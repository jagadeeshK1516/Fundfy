# Phase A Implementation Plan — Autonomous Agent with Real Tool-Use

## Prerequisites & Environment Note

The project targets Python 3.11 (`requires-python = ">=3.11"`). Ensure the build/test environment uses Python 3.11+. The existing test command is `pytest tests/` with `asyncio_mode = "auto"`.

---

## Implementation Plan

- [ ] 1. Add Phase A dependencies to `pyproject.toml` and update `fundfy/config.py` with new settings.
      Add `tavily-python`, `beautifulsoup4`, `python-pptx`, `python-docx`, `reportlab`, and `langchain-core` (for tool abstractions) to the `[project.dependencies]` list. In `fundfy/config.py`, add optional env-var settings: `tavily_api_key: str = ""`, `generated_files_dir: str = "./generated_files"`. Update `.env.example` with `TAVILY_API_KEY=` and `GENERATED_FILES_DIR=./generated_files`.
      Files: `pyproject.toml`, `fundfy/config.py`, `.env.example`
      Verify: `pip install -e ".[dev]"` completes without errors (on Python 3.11).

- [ ] 2. Create the tool base class and Pydantic schemas for structured tool I/O in a new `fundfy/tools/` package.
      Create `fundfy/tools/__init__.py`, `fundfy/tools/base.py` (defines `BaseTool` ABC with `name`, `description`, `args_schema: type[BaseModel]`, and `async execute(self, **kwargs) -> ToolResult`), and `fundfy/tools/schemas.py` (Pydantic models for structured extraction: `CompetitorProfile`, `MarketData`, `InvestorProfile`, `GrantOpportunity`, `ToolResult` with fields `success: bool`, `data: Any`, `error: str | None`). The `BaseTool` must expose a `to_openai_function()` method that returns the JSON-schema dict LangChain/OpenAI function-calling expects, derived from `args_schema`.
      Files: `fundfy/tools/__init__.py`, `fundfy/tools/base.py`, `fundfy/tools/schemas.py`
      Verify: `python -c "from fundfy.tools.base import BaseTool; from fundfy.tools.schemas import ToolResult, CompetitorProfile"` succeeds.

- [ ] 3. Implement `web_search` tool using Tavily API.
      Create `fundfy/tools/web_search.py`. Class `WebSearchTool(BaseTool)` with `name="web_search"`, accepts `query: str` and optional `max_results: int = 5`. Uses `tavily-python` client (`TavilyClient`) to call `client.search(query, max_results=max_results)`. Returns `ToolResult` with list of `{title, url, content}` dicts. Falls back gracefully if `TAVILY_API_KEY` is empty (returns error result). Register in `fundfy/tools/__init__.py`.
      Files: `fundfy/tools/web_search.py`
      Verify: `pytest tests/test_tools.py::test_web_search_tool` passes (new test, next step).

- [ ] 4. Implement `web_scrape` tool using httpx + BeautifulSoup.
      Create `fundfy/tools/web_scrape.py`. Class `WebScrapeTool(BaseTool)` with `name="web_scrape"`, accepts `url: str`. Uses `httpx.AsyncClient` to GET the URL (timeout 15s), then `BeautifulSoup` to extract main text content (strip scripts/styles, extract `<article>` or `<main>` or `<body>` text). Returns `ToolResult` with `{url, content, title}`. Truncate content to 8000 chars to fit in LLM context.
      Files: `fundfy/tools/web_scrape.py`
      Verify: `pytest tests/test_tools.py::test_web_scrape_tool` passes.

- [ ] 5. Implement memory tools: `save_to_memory` and `query_memory`.
      Create `fundfy/tools/memory_tools.py`. `SaveToMemoryTool(BaseTool)` accepts `content: str`, `metadata: dict | None`. Calls `MemoryEngine.ingest(content, metadata)`. `QueryMemoryTool(BaseTool)` accepts `query: str`, `k: int = 5`. Calls `MemoryEngine.query(query, k=k)` and returns page_content + metadata for each result. Both tools require a `memory_engine` instance passed at construction.
      Files: `fundfy/tools/memory_tools.py`
      Verify: `pytest tests/test_tools.py::test_memory_tools` passes.

- [ ] 6. Implement `generate_document` tool that produces real file exports (PDF, DOCX, PPTX, Markdown).
      Create `fundfy/tools/document_tool.py`. Class `GenerateDocumentTool(BaseTool)` accepts `doc_type: str`, `business_id: str`, `content: str | None`, `format: str` (one of `"pdf"`, `"docx"`, `"pptx"`, `"markdown"`, default `"markdown"`). Logic: (a) if `content` is not provided, call the existing `DocumentGenerator.generate()` to produce text content; (b) convert to the requested format using helper functions in a new `fundfy/tools/exporters.py`. Exporters: `export_pdf(title, content) -> filepath` (using `reportlab`), `export_docx(title, content) -> filepath` (using `python-docx`), `export_pptx(title, slides_content) -> filepath` (using `python-pptx` — splits content by `##` headings into slides), `export_markdown(title, content) -> filepath`. Files are saved to `settings.generated_files_dir/{uuid}.{ext}`. Returns `ToolResult` with `{file_path, file_name, format, doc_type}`.
      Files: `fundfy/tools/document_tool.py`, `fundfy/tools/exporters.py`
      Verify: `pytest tests/test_tools.py::test_generate_document_tool` passes.

- [ ] 7. Implement workstream tools: `create_workstream` and `update_workstream`.
      Create `fundfy/tools/workstream_tools.py`. `CreateWorkstreamTool(BaseTool)` accepts `business_id: str`, `title: str`, `steps: list[str]`. Creates an in-memory workstream record (dict with `id`, `business_id`, `title`, `steps` list of `{index, description, status}`, `created_at`) stored in a module-level dict (consistent with the current pattern in routes_execution.py). Returns `ToolResult` with workstream id. `UpdateWorkstreamTool(BaseTool)` accepts `workstream_id: str`, `step_index: int`, `status: str`, `result_summary: str | None`. Updates the step's status.
      Files: `fundfy/tools/workstream_tools.py`
      Verify: `pytest tests/test_tools.py::test_workstream_tools` passes.

- [ ] 8. Implement `draft_email` tool.
      Create `fundfy/tools/email_tool.py`. Class `DraftEmailTool(BaseTool)` accepts `email_type: str` (one of `"investor_outreach"`, `"grant_cover_letter"`, `"introduction_request"`, `"follow_up"`), `recipient_context: str`, `business_context: str`. Uses the shared LLM with a mode-specific system prompt to draft the email. Returns `ToolResult` with `{subject, body, email_type, recipient_context}`. Stores drafts in a module-level list for retrieval.
      Files: `fundfy/tools/email_tool.py`
      Verify: `pytest tests/test_tools.py::test_draft_email_tool` passes.

- [ ] 9. Implement `analyze_financials` tool.
      Create `fundfy/tools/financial_tool.py`. Class `AnalyzeFinancialsTool(BaseTool)` accepts `business_context: str`, `analysis_type: str` (e.g., `"unit_economics"`, `"projections"`, `"break_even"`). Delegates to the existing `FinancialReasoningHandler` logic (reuses its prompt) but returns structured `ToolResult`. Uses the shared LLM.
      Files: `fundfy/tools/financial_tool.py`
      Verify: `pytest tests/test_tools.py::test_analyze_financials_tool` passes.

- [ ] 10. Implement `search_grants` and `search_investors` tools (composite tools using web_search + structured extraction).
       Create `fundfy/tools/research_tools.py`. `SearchGrantsTool(BaseTool)` accepts `query: str`, `industry: str | None`. Internally calls `WebSearchTool.execute(query=f"grants for {query} startups {industry}")`, then uses the LLM with a Pydantic output schema to extract a list of `GrantOpportunity` objects from the search results. Similarly `SearchInvestorsTool(BaseTool)` accepts `query: str`, `stage: str | None`, `industry: str | None`. Both return `ToolResult` with structured list of extracted objects. They require `llm` and `web_search_tool` at construction.
       Files: `fundfy/tools/research_tools.py`
       Verify: `pytest tests/test_tools.py::test_search_grants_tool` and `test_search_investors_tool` pass.

- [ ] 11. Create the tool registry that assembles all tools with their dependencies.
       Create `fundfy/tools/registry.py`. Function `create_tool_registry(llm, memory_engine, document_generator) -> dict[str, BaseTool]` that instantiates all 11 tools and returns them keyed by `tool.name`. This is the single point where tools get their dependencies injected.
       Files: `fundfy/tools/registry.py`
       Verify: `python -c "from fundfy.tools.registry import create_tool_registry"` succeeds.

- [ ] 12. Implement the ReAct agent loop in `fundfy/core/react_agent.py`.
       Create `fundfy/core/react_agent.py` with class `ReActAgent`. Constructor accepts `llm`, `tools: dict[str, BaseTool]`, `memory_engine`, `max_iterations: int = 10`. Core method: `async run(self, founder_id: str, objective: str) -> AgentResponse`. The loop: (a) Build messages with system prompt (including tool descriptions), conversation history, and accumulated thought/action/observation trace. (b) Call LLM with OpenAI function-calling (pass tool schemas as `functions` parameter). (c) If LLM returns a function_call, parse tool name + args, execute the tool, append observation. (d) If LLM returns plain content (no function_call), that's the final answer. (e) Repeat up to `max_iterations`. Define `AgentResponse` dataclass: `response: str`, `tool_calls: list[dict]` (log of each tool invocation with name, args, result summary), `steps: int`. Use LangChain's `ChatOpenAI` with `model_kwargs={"functions": [...]}` or the newer `.bind_tools()` API depending on langchain version — decision: use `.bind(functions=tool_schemas)` since langchain-openai supports it and doesn't require the full LangChain agent executor (gives us control over the loop).
       Files: `fundfy/core/react_agent.py`
       Verify: `pytest tests/test_react_agent.py` passes (new test file, next step).

- [ ] 13. Write comprehensive unit tests for all tools and the ReAct agent.
       Create `tests/test_tools.py` with mocked external calls (httpx for scraping, Tavily client for search, LLM for email/financials/research). Each tool gets at least one happy-path and one error-path test. Create `tests/test_react_agent.py` testing: (a) single-tool invocation, (b) multi-step chain (mock LLM returns function_call then observation then final answer), (c) max_iterations guard. All external I/O is mocked.
       Files: `tests/test_tools.py`, `tests/test_react_agent.py`
       Verify: `pytest tests/test_tools.py tests/test_react_agent.py -v` — all tests pass.

- [ ] 14. Upgrade `FundfyAgent` to delegate to `ReActAgent` for complex queries while preserving simple chat for basic messages.
       Modify `fundfy/core/agent.py`. Add a `_react_agent: ReActAgent` attribute initialized with tools from the registry. Modify the `chat()` method: after retrieving context, include a short classifier prompt that asks the LLM "Does this message require tool use (research, document generation, execution) or is it a simple conversational reply? Answer TOOL_USE or CHAT_ONLY." If TOOL_USE → delegate to `self._react_agent.run(founder_id, message)` and return the `AgentResponse.response`. If CHAT_ONLY → proceed with existing RAG-only path. This keeps backward compatibility for simple Q&A. Also add a new method `async execute(self, founder_id: str, objective: str) -> AgentResponse` that always uses the ReAct loop (for the `/api/execute` endpoint upgrade later).
       Files: `fundfy/core/agent.py`
       Verify: `pytest tests/test_agent.py` — existing tests still pass (mock LLM returns "CHAT_ONLY" for classifier call, then the normal response).

- [ ] 15. Update `ChatResponse` schema and `/api/chat` to return enriched responses with tool-call metadata.
       Modify `fundfy/api/schemas.py`: add optional fields to `ChatResponse`: `tool_calls: list[dict] | None = None`, `steps: int | None = None`, `files: list[dict] | None = None` (for generated file references). Update `fundfy/api/routes_chat.py` to check if the response came from the ReAct agent (has tool_calls) and include them. The frontend already only reads `.response` so this is additive/backward-compatible.
       Files: `fundfy/api/schemas.py`, `fundfy/api/routes_chat.py`
       Verify: `pytest tests/test_api.py` — existing API tests still pass.

- [ ] 16. Add a file download endpoint for generated documents.
       Create endpoint `GET /api/files/{file_id}` in a new `fundfy/api/routes_files.py`. Serves the file from `settings.generated_files_dir` using `FileResponse`. Add the router to `fundfy/main.py`. Also add `GET /api/files` (query by `business_id`) to list generated files.
       Files: `fundfy/api/routes_files.py`, `fundfy/main.py`
       Verify: `pytest tests/test_api.py::test_file_download_endpoint` passes (new test that creates a temp file and downloads it).

- [ ] 17. Update application startup in `fundfy/main.py` to initialize the tool registry and pass it to the agent.
       In the `lifespan` function, after creating `memory_engine` and `document_generator`, call `create_tool_registry(llm, memory_engine, document_generator)` and pass the resulting tools dict to `FundfyAgent`. Update `FundfyAgent.__init__` signature to accept optional `tools: dict[str, BaseTool] | None`. Update `init_dependencies` to store the registry if other routes need tool access.
       Files: `fundfy/main.py`, `fundfy/core/agent.py` (minor signature update), `fundfy/dependencies.py`
       Verify: `pytest tests/test_integration.py` — integration test still passes (tools default to empty dict when not provided in tests).

- [ ] 18. Add execution checkpoint tracking to the ReAct agent loop.
       Modify `fundfy/core/react_agent.py`: during the loop, after each tool call, emit a checkpoint dict `{step: int, tool: str, status: "completed"|"failed", summary: str}` into a list on the `AgentResponse`. Add field `checkpoints: list[dict]` to `AgentResponse`. Update `ChatResponse` schema with optional `checkpoints: list[dict] | None = None`. This allows the frontend to display "Step 1/5: Searching for competitors... ✓ Found 8 results".
       Files: `fundfy/core/react_agent.py`, `fundfy/api/schemas.py`
       Verify: `pytest tests/test_react_agent.py` — checkpoint data is present in responses from multi-step tests.

- [ ] 19. Ensure all existing tests pass and add a full integration test for the ReAct agent path.
       Add `tests/test_react_integration.py`: an end-to-end test that hits `POST /api/chat` with a message like "Research my competitors in the CRM space" and verifies: (a) response includes tool_calls with at least one web_search call, (b) checkpoints are present, (c) the final response text is non-empty. Mock Tavily and LLM. Run the full test suite to confirm nothing is broken.
       Files: `tests/test_react_integration.py`
       Verify: `pytest tests/ -v` — all tests pass, including old and new.

- [ ] 20. Create `generated_files/` directory with a `.gitkeep` and add it to `.gitignore` (exclude actual generated files but keep the dir).
       Add `generated_files/` directory. Add `generated_files/*` and `!generated_files/.gitkeep` to `.gitignore`.
       Files: `generated_files/.gitkeep`, `.gitignore`
       Verify: `ls generated_files/.gitkeep` exists; `git status` shows the gitkeep tracked.

---

## Architecture Decisions (for implementer reference)

1. **No LangChain AgentExecutor** — We implement our own ReAct loop for full control over iteration, checkpointing, and error handling. LangChain's `AgentExecutor` is opaque and hard to add checkpointing to. We still use LangChain's `ChatOpenAI` and its function-calling `.bind(functions=...)` method.

2. **Tool routing via classifier** — Rather than always running the ReAct loop (expensive), a lightweight classifier prompt decides if the message needs tools. This preserves fast simple-chat UX.

3. **Module-level state stores for workstreams/files** — The existing code uses in-memory dicts (`_workstreams`, `_documents`, `_businesses`). We follow the same pattern for consistency. A future phase can migrate to the SQLAlchemy DB.

4. **Tavily as primary web search** — Tavily is purpose-built for AI agents, returns clean content, and has a free tier. No fallback to SerpAPI in Phase A to avoid complexity; if `TAVILY_API_KEY` is empty, the tool returns a graceful error.

5. **Exporters as simple functions** — PDF/DOCX/PPTX generation is done by pure helper functions in `exporters.py`, not classes. This keeps them testable and composable.

6. **Structured extraction via LLM** — For `search_grants` and `search_investors`, we use the LLM with a Pydantic schema prompt to extract structured data from raw web search results, rather than writing brittle scrapers.

7. **Backward compatibility** — `ChatResponse` gets new optional fields. The frontend reads `.response` which remains the same. Existing tests mock the LLM so the classifier returns "CHAT_ONLY" by default, keeping them passing without changes.
