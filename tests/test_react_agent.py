"""Tests for the ReAct agent loop."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage

from fundfy.core.react_agent import ReActAgent
from fundfy.tools.base import BaseTool
from fundfy.tools.schemas import ToolResult
from pydantic import BaseModel


class MockToolArgs(BaseModel):
    """Mock tool arguments."""

    query: str


class MockTool(BaseTool):
    """Mock tool for testing."""

    name = "mock_search"
    description = "A mock search tool for testing."
    args_schema = MockToolArgs

    def __init__(self):
        self._execute_mock = AsyncMock(return_value=ToolResult(
            success=True, data=[{"title": "Result 1", "content": "Test content"}]
        ))

    async def execute(self, **kwargs):
        return await self._execute_mock(**kwargs)


def _make_function_call_response(name: str, arguments: dict) -> AIMessage:
    """Create a mock AIMessage with a function call."""
    return AIMessage(
        content="",
        additional_kwargs={
            "function_call": {
                "name": name,
                "arguments": json.dumps(arguments),
            }
        },
    )


def _make_text_response(text: str) -> AIMessage:
    """Create a mock AIMessage with plain text (final answer)."""
    return AIMessage(content=text)


@pytest.mark.asyncio
async def test_react_single_tool_invocation():
    """ReAct agent calls a tool then returns final answer."""
    mock_tool = MockTool()
    tools = {"mock_search": mock_tool}

    # LLM: first call returns function_call, second returns final answer
    mock_llm = MagicMock()
    bound_mock = AsyncMock()
    bound_mock.ainvoke = AsyncMock(side_effect=[
        _make_function_call_response("mock_search", {"query": "AI startups"}),
        _make_text_response("Based on my research, here are the top AI startups..."),
    ])
    mock_llm.bind = MagicMock(return_value=bound_mock)

    agent = ReActAgent(llm=mock_llm, tools=tools, max_iterations=5)
    response = await agent.run("founder-1", "Research AI startups")

    assert response.response == "Based on my research, here are the top AI startups..."
    assert len(response.tool_calls) == 1
    assert response.tool_calls[0]["tool"] == "mock_search"
    assert response.tool_calls[0]["success"] is True
    assert response.steps == 2


@pytest.mark.asyncio
async def test_react_multi_step_chain():
    """ReAct agent performs multiple tool calls before final answer."""
    mock_tool = MockTool()
    tools = {"mock_search": mock_tool}

    mock_llm = MagicMock()
    bound_mock = AsyncMock()
    bound_mock.ainvoke = AsyncMock(side_effect=[
        _make_function_call_response("mock_search", {"query": "market size"}),
        _make_function_call_response("mock_search", {"query": "competitors"}),
        _make_text_response("The market is $5B with 3 major competitors."),
    ])
    mock_llm.bind = MagicMock(return_value=bound_mock)

    agent = ReActAgent(llm=mock_llm, tools=tools, max_iterations=5)
    response = await agent.run("founder-1", "Analyze the market")

    assert response.response == "The market is $5B with 3 major competitors."
    assert len(response.tool_calls) == 2
    assert response.steps == 3


@pytest.mark.asyncio
async def test_react_max_iterations_guard():
    """ReAct agent stops after max iterations."""
    mock_tool = MockTool()
    tools = {"mock_search": mock_tool}

    # LLM always returns function calls (never a final answer)
    mock_llm = MagicMock()
    bound_mock = AsyncMock()
    bound_mock.ainvoke = AsyncMock(
        return_value=_make_function_call_response("mock_search", {"query": "endless search"})
    )
    mock_llm.bind = MagicMock(return_value=bound_mock)

    agent = ReActAgent(llm=mock_llm, tools=tools, max_iterations=3)
    response = await agent.run("founder-1", "Search forever")

    assert response.steps == 3
    assert len(response.tool_calls) == 3
    assert "maximum" in response.response.lower()


@pytest.mark.asyncio
async def test_react_tool_not_found():
    """ReAct agent handles calls to non-existent tools gracefully."""
    tools = {}  # No tools registered

    mock_llm = MagicMock()
    # When no function schemas, _call_llm uses self._llm.ainvoke directly
    mock_llm.ainvoke = AsyncMock(side_effect=[
        _make_function_call_response("nonexistent_tool", {"query": "test"}),
        _make_text_response("I couldn't find that tool, but here's my answer."),
    ])

    agent = ReActAgent(llm=mock_llm, tools=tools, max_iterations=5)
    response = await agent.run("founder-1", "Do something")

    assert "answer" in response.response.lower()
    assert len(response.checkpoints) == 1
    assert response.checkpoints[0]["status"] == "failed"


@pytest.mark.asyncio
async def test_react_checkpoints_present():
    """ReAct agent includes checkpoints in response."""
    mock_tool = MockTool()
    tools = {"mock_search": mock_tool}

    mock_llm = MagicMock()
    bound_mock = AsyncMock()
    bound_mock.ainvoke = AsyncMock(side_effect=[
        _make_function_call_response("mock_search", {"query": "test"}),
        _make_text_response("Done."),
    ])
    mock_llm.bind = MagicMock(return_value=bound_mock)

    agent = ReActAgent(llm=mock_llm, tools=tools, max_iterations=5)
    response = await agent.run("founder-1", "Quick search")

    assert len(response.checkpoints) == 1
    assert response.checkpoints[0]["tool"] == "mock_search"
    assert response.checkpoints[0]["status"] == "completed"
    assert response.checkpoints[0]["step"] == 1


@pytest.mark.asyncio
async def test_react_immediate_answer():
    """ReAct agent returns immediately if LLM gives text without function call."""
    tools = {"mock_search": MockTool()}

    mock_llm = MagicMock()
    bound_mock = AsyncMock()
    bound_mock.ainvoke = AsyncMock(
        return_value=_make_text_response("I can answer this directly without tools.")
    )
    mock_llm.bind = MagicMock(return_value=bound_mock)

    agent = ReActAgent(llm=mock_llm, tools=tools, max_iterations=5)
    response = await agent.run("founder-1", "What is 2+2?")

    assert response.response == "I can answer this directly without tools."
    assert len(response.tool_calls) == 0
    assert response.steps == 1
