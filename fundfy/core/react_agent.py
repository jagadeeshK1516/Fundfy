"""ReAct agent loop — Reason + Act pattern with tool execution."""

import json
from dataclasses import dataclass, field
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from fundfy.tools.base import BaseTool

REACT_SYSTEM_PROMPT = """You are Fundfy AI, an autonomous business execution agent. You help founders build, validate, and grow their businesses.

You have access to the following tools:

{tool_descriptions}

When you need to use a tool, respond with a function call. When you have gathered enough information to provide a final answer, respond with your analysis directly (no function call).

Guidelines:
- Break complex tasks into steps and use tools systematically
- Use web_search for current market data, competitors, and trends
- Use save_to_memory to persist important findings for future use
- Use query_memory to check what's already been researched
- Be thorough but efficient — avoid redundant tool calls
- Provide actionable, specific recommendations in your final answer
"""


@dataclass
class AgentResponse:
    """Response from the ReAct agent."""

    response: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    steps: int = 0
    checkpoints: list[dict[str, Any]] = field(default_factory=list)


class ReActAgent:
    """Custom ReAct agent loop with checkpointing."""

    def __init__(
        self,
        llm: Any,
        tools: dict[str, BaseTool],
        memory_engine: Any = None,
        max_iterations: int = 10,
    ):
        self._llm = llm
        self._tools = tools
        self._memory = memory_engine
        self._max_iterations = max_iterations

    def _build_tool_descriptions(self) -> str:
        """Build tool descriptions for the system prompt."""
        descriptions = []
        for tool in self._tools.values():
            schema = tool.args_schema.model_json_schema()
            props = schema.get("properties", {})
            params = ", ".join(f"{k}: {v.get('type', 'any')}" for k, v in props.items())
            descriptions.append(f"- {tool.name}({params}): {tool.description}")
        return "\n".join(descriptions)

    def _get_function_schemas(self) -> list[dict[str, Any]]:
        """Get OpenAI function-calling schemas for all tools."""
        return [tool.to_openai_function() for tool in self._tools.values()]

    async def run(self, founder_id: str, objective: str) -> AgentResponse:
        """Execute the ReAct loop for an objective.

        Args:
            founder_id: The founder's ID.
            objective: The task/question to accomplish.

        Returns:
            AgentResponse with the final answer and execution trace.
        """
        tool_descriptions = self._build_tool_descriptions()
        system_prompt = REACT_SYSTEM_PROMPT.format(tool_descriptions=tool_descriptions)
        function_schemas = self._get_function_schemas()

        messages: list[Any] = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Founder ID: {founder_id}\n\nObjective: {objective}"),
        ]

        tool_calls_log: list[dict[str, Any]] = []
        checkpoints: list[dict[str, Any]] = []
        steps = 0

        for iteration in range(self._max_iterations):
            steps = iteration + 1

            # Call LLM with function schemas
            response = await self._call_llm(messages, function_schemas)

            # Check if the LLM wants to call a function
            function_call = self._extract_function_call(response)

            if function_call is None:
                # No function call — this is the final answer
                final_text = response.content if hasattr(response, "content") else str(response)
                return AgentResponse(
                    response=final_text,
                    tool_calls=tool_calls_log,
                    steps=steps,
                    checkpoints=checkpoints,
                )

            # Execute the tool
            tool_name = function_call["name"]
            tool_args = function_call["arguments"]

            tool = self._tools.get(tool_name)
            if not tool:
                # Tool not found — add error observation
                observation = f"Error: Tool '{tool_name}' not found."
                messages.append(AIMessage(content="", additional_kwargs={"function_call": {"name": tool_name, "arguments": json.dumps(tool_args)}}))
                messages.append(HumanMessage(content=f"Tool result: {observation}"))
                checkpoints.append({
                    "step": steps,
                    "tool": tool_name,
                    "status": "failed",
                    "summary": observation,
                })
                continue

            try:
                result = await tool.execute(**tool_args)
                observation = json.dumps(result.model_dump(), default=str)
                status = "completed" if result.success else "failed"
                summary = (
                    f"Success: {_summarize_data(result.data)}"
                    if result.success
                    else f"Error: {result.error}"
                )
            except Exception as e:
                observation = json.dumps({"success": False, "error": str(e)})
                status = "failed"
                summary = f"Exception: {str(e)}"

            # Log the tool call
            tool_call_record = {
                "tool": tool_name,
                "args": tool_args,
                "result_summary": summary,
                "success": status == "completed",
            }
            tool_calls_log.append(tool_call_record)

            # Add checkpoint
            checkpoints.append({
                "step": steps,
                "tool": tool_name,
                "status": status,
                "summary": summary,
            })

            # Add the function call and observation to messages
            messages.append(AIMessage(content="", additional_kwargs={"function_call": {"name": tool_name, "arguments": json.dumps(tool_args)}}))
            messages.append(HumanMessage(content=f"Tool '{tool_name}' result:\n{observation}"))

        # Max iterations reached — return what we have
        return AgentResponse(
            response="I reached the maximum number of steps. Here's what I found so far based on the tools I used.",
            tool_calls=tool_calls_log,
            steps=steps,
            checkpoints=checkpoints,
        )

    async def _call_llm(self, messages: list[Any], function_schemas: list[dict]) -> Any:
        """Call the LLM with function-calling support."""
        # Use bind to attach functions to the LLM call
        if function_schemas:
            bound_llm = self._llm.bind(functions=function_schemas)
            return await bound_llm.ainvoke(messages)
        return await self._llm.ainvoke(messages)

    def _extract_function_call(self, response: Any) -> dict[str, Any] | None:
        """Extract a function call from the LLM response, if present."""
        # Check additional_kwargs for function_call
        if hasattr(response, "additional_kwargs"):
            fc = response.additional_kwargs.get("function_call")
            if fc:
                name = fc.get("name", "")
                args_str = fc.get("arguments", "{}")
                try:
                    arguments = json.loads(args_str)
                except (json.JSONDecodeError, TypeError):
                    arguments = {}
                return {"name": name, "arguments": arguments}

        # Check tool_calls attribute (newer LangChain format)
        if hasattr(response, "tool_calls") and response.tool_calls:
            tc = response.tool_calls[0]
            if isinstance(tc, dict):
                return {"name": tc.get("name", ""), "arguments": tc.get("args", {})}
            # LangChain ToolCall object
            if hasattr(tc, "name"):
                return {"name": tc.name, "arguments": tc.get("args", {})}

        return None


def _summarize_data(data: Any) -> str:
    """Create a brief summary of tool result data."""
    if data is None:
        return "No data"
    if isinstance(data, list):
        return f"Found {len(data)} results"
    if isinstance(data, dict):
        if "content" in data:
            content = str(data["content"])
            return f"{content[:100]}..." if len(content) > 100 else content
        if "analysis" in data:
            return "Analysis completed"
        if "file_path" in data:
            return f"Generated file: {data.get('file_name', 'unknown')}"
        return f"Dict with keys: {list(data.keys())}"
    return str(data)[:100]
