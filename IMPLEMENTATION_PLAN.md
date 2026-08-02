# Fundfy AI Business Execution Platform — Implementation Plan

## Architecture Decisions

1. **Framework:** FastAPI — async-native, excellent for streaming LLM responses, lightweight, well-supported.
2. **RAG Stack:** LangChain + ChromaDB. LangChain provides the orchestration glue (chains, retrievers, memory); ChromaDB is zero-config, file-based, no external service needed for local dev, and sufficient for MVP. Embeddings via OpenAI `text-embedding-3-small`.
3. **LLM:** OpenAI GPT-4o via `langchain-openai`, configurable via env var so swapping models later is trivial.
4. **Structured Storage:** SQLite via SQLAlchemy (async with aiosqlite). Lightweight for MVP; schema is portable to PostgreSQL later.
5. **Project layout:** Single Python package `fundfy/` with sub-packages per domain (core, memory, orchestrator, intelligence, documents, communication). One entry point (`fundfy/main.py`).
6. **Dependency management:** `pyproject.toml` with pip/uv install. No Poetry — keeps tooling simple.
7. **Testing:** pytest + pytest-asyncio. Tests live in `tests/` mirroring `fundfy/` structure.
8. **Python version:** 3.11 via pyenv (`.python-version` file in repo root).

---

## Implementation Plan

- [ ] 1. **Bootstrap project skeleton and dependencies**
      Create the repo structure, `pyproject.toml` with all dependencies, `.python-version`, `.env.example`, `.gitignore`, and empty `__init__.py` files for every package so imports resolve.
      Files:
        - `pyproject.toml`
        - `.python-version` (contents: `3.11.15`)
        - `.env.example` (OPENAI_API_KEY, DATABASE_URL, CHROMA_PERSIST_DIR)
        - `.gitignore`
        - `fundfy/__init__.py`
        - `fundfy/main.py` (minimal FastAPI app with `/health` endpoint)
        - `fundfy/config.py` (pydantic-settings `Settings` class loading from env)
        - `fundfy/core/__init__.py`
        - `fundfy/memory/__init__.py`
        - `fundfy/orchestrator/__init__.py`
        - `fundfy/intelligence/__init__.py`
        - `fundfy/documents/__init__.py`
        - `fundfy/communication/__init__.py`
        - `tests/__init__.py`
        - `tests/test_health.py` (hits `/health`, expects 200)
      Verify: `cd /projects/sandbox/Fundfy && pyenv local 3.11.15 && pip install -e ".[dev]" && pytest tests/test_health.py -v` — test passes, server starts.

- [ ] 2. **Database models and migrations setup**
      Define SQLAlchemy async models for core business entities: `Founder`, `Business`, `Conversation`, `Message`, `Document`, `WorkstreamTask`. Create a `fundfy/db.py` with engine/session factory and an `alembic`-free init script (`fundfy/db_init.py`) that creates tables on first run (sufficient for MVP; Alembic can come later).
      Files:
        - `fundfy/db.py` (async engine, session maker, `init_db()` function)
        - `fundfy/models/__init__.py`
        - `fundfy/models/founder.py` (Founder: id, name, email, created_at)
        - `fundfy/models/business.py` (Business: id, founder_id, name, industry, stage, goals_json, created_at)
        - `fundfy/models/conversation.py` (Conversation: id, founder_id, title, created_at; Message: id, conversation_id, role, content, timestamp)
        - `fundfy/models/document.py` (Document: id, business_id, doc_type, title, content_text, metadata_json, created_at)
        - `fundfy/models/workstream.py` (WorkstreamTask: id, business_id, type, status, params_json, result_json, created_at, updated_at)
        - `tests/test_db.py` (creates in-memory SQLite, calls init_db, inserts a founder, asserts round-trip)
      Verify: `pytest tests/test_db.py -v` — passes.

- [ ] 3. **Business Memory Engine — vector store integration**
      Implement the RAG memory layer. A `MemoryEngine` class wraps ChromaDB: ingest text (with metadata tags like source_type, business_id), embed via OpenAI, and retrieve top-k relevant chunks given a query. Uses LangChain's `Chroma` vectorstore wrapper and `RecursiveCharacterTextSplitter` for chunking.
      Files:
        - `fundfy/memory/engine.py` (class `MemoryEngine` with methods: `ingest(text, metadata)`, `query(question, filters, k=5) -> list[Document]`, `ingest_document(doc_id)`)
        - `fundfy/memory/embeddings.py` (factory function returning `OpenAIEmbeddings` configured from settings)
        - `tests/test_memory.py` (unit test using a temporary ChromaDB directory: ingest 3 short texts, query, assert relevant chunk returned; mock OpenAI embeddings with a deterministic fake)
      Verify: `pytest tests/test_memory.py -v` — passes.

- [ ] 4. **Core AI Agent — single conversational chain with RAG retrieval**
      Build the central `FundfyAgent` class. Before every response it: (a) retrieves relevant context from MemoryEngine, (b) constructs a system prompt with business context + retrieved chunks, (c) calls the LLM, (d) persists the exchange in DB and memory. Uses LangChain's `ChatOpenAI` + `ConversationBufferWindowMemory` (last 20 messages window) + custom retrieval step.
      Files:
        - `fundfy/core/agent.py` (class `FundfyAgent` with `async chat(founder_id, message) -> str`)
        - `fundfy/core/prompts.py` (system prompt templates: SYSTEM_PROMPT, CONTEXT_INJECTION_TEMPLATE)
        - `tests/test_agent.py` (mock LLM + mock memory engine, assert agent returns response string incorporating retrieved context)
      Verify: `pytest tests/test_agent.py -v` — passes.

- [ ] 5. **Execution Orchestrator — workstream decomposition and dispatch**
      Implement the orchestrator that takes a founder's objective and breaks it into parallel tasks. Uses an LLM call with a structured output (JSON) to produce a list of workstream tasks, then dispatches them asynchronously. Each task type maps to a handler function.
      Files:
        - `fundfy/orchestrator/planner.py` (class `ExecutionPlanner` with `async plan(objective, business_context) -> list[WorkstreamTask]` — calls LLM with planning prompt, parses JSON)
        - `fundfy/orchestrator/dispatcher.py` (class `Dispatcher` with `async execute(tasks) -> list[TaskResult]` — runs handlers concurrently via `asyncio.gather`)
        - `fundfy/orchestrator/handlers/__init__.py`
        - `fundfy/orchestrator/handlers/base.py` (abstract `BaseHandler` with `async run(task) -> TaskResult`)
        - `tests/test_orchestrator.py` (mock LLM returns a known JSON plan, dispatcher executes dummy handlers, asserts all tasks complete)
      Verify: `pytest tests/test_orchestrator.py -v` — passes.

- [ ] 6. **Intelligence Layer — market research, validation, competitor analysis**
      Implement handler classes for intelligence workstreams. Each handler: retrieves relevant memory, calls LLM with a domain-specific prompt, returns structured findings, and ingests results back into memory.
      Files:
        - `fundfy/intelligence/__init__.py`
        - `fundfy/intelligence/market_research.py` (class `MarketResearchHandler(BaseHandler)` — prompt for market sizing, trends, TAM/SAM/SOM)
        - `fundfy/intelligence/competitor_analysis.py` (class `CompetitorAnalysisHandler(BaseHandler)` — prompt for competitor landscape, positioning)
        - `fundfy/intelligence/idea_validation.py` (class `IdeaValidationHandler(BaseHandler)` — prompt for feasibility, risks, opportunities)
        - `fundfy/intelligence/financial_reasoning.py` (class `FinancialReasoningHandler(BaseHandler)` — prompt for revenue models, unit economics)
        - `fundfy/orchestrator/handlers/registry.py` (maps task type strings to handler classes)
        - `tests/test_intelligence.py` (mock LLM, run each handler with sample input, assert structured output returned)
      Verify: `pytest tests/test_intelligence.py -v` — passes.

- [ ] 7. **Document Generation Engine — templates and LLM-powered writing**
      Implement document generation handlers. Each takes business context from memory, generates a full document via LLM (using long-form prompts with section outlines), persists to DB and memory.
      Files:
        - `fundfy/documents/generator.py` (class `DocumentGenerator` with `async generate(doc_type, business_id) -> Document`)
        - `fundfy/documents/templates.py` (prompt templates per doc type: BUSINESS_PLAN, EXECUTIVE_SUMMARY, PITCH_DECK_OUTLINE, PRD, BRD, SOP, FINANCIAL_MODEL, DPR, COMPANY_PROFILE)
        - `fundfy/documents/handlers.py` (class `DocumentGenerationHandler(BaseHandler)` — delegates to DocumentGenerator)
        - `tests/test_documents.py` (mock LLM, generate a business plan, assert document saved with correct type and non-empty content)
      Verify: `pytest tests/test_documents.py -v` — passes.

- [ ] 8. **Founder Communication — conversational interface, mock interviews, pitch practice**
      Implement specialized conversation modes: free chat (default), mock investor interview, pitch practice, Q&A rehearsal. Each mode adjusts the system prompt and evaluation criteria.
      Files:
        - `fundfy/communication/modes.py` (enum `ConversationMode`: CHAT, MOCK_INTERVIEW, PITCH_PRACTICE, QA_REHEARSAL)
        - `fundfy/communication/prompts.py` (mode-specific system prompts and scoring rubrics)
        - `fundfy/communication/session.py` (class `CommunicationSession` extending agent behavior with mode switching and feedback generation)
        - `tests/test_communication.py` (mock LLM, start a mock interview session, send a message, assert response includes interviewer-style follow-up)
      Verify: `pytest tests/test_communication.py -v` — passes.

- [ ] 9. **REST API — endpoints for all platform capabilities**
      Wire everything together via FastAPI routes. Endpoints: chat, create business profile, trigger execution plan, get documents, list workstreams, switch conversation mode. Include request/response Pydantic schemas.
      Files:
        - `fundfy/api/__init__.py`
        - `fundfy/api/schemas.py` (Pydantic models: ChatRequest, ChatResponse, BusinessCreate, BusinessResponse, ExecutionRequest, DocumentResponse, WorkstreamResponse)
        - `fundfy/api/routes_chat.py` (POST `/api/chat` — main conversational endpoint)
        - `fundfy/api/routes_business.py` (POST `/api/business`, GET `/api/business/{id}`)
        - `fundfy/api/routes_execution.py` (POST `/api/execute` — trigger orchestrator, GET `/api/workstreams/{business_id}`)
        - `fundfy/api/routes_documents.py` (POST `/api/documents/generate`, GET `/api/documents/{id}`, GET `/api/documents?business_id=X`)
        - `fundfy/api/routes_communication.py` (POST `/api/communication/session` — start/switch mode)
        - `fundfy/main.py` (updated: include all routers, add startup event for db init)
        - `tests/test_api.py` (use `httpx.AsyncClient` with FastAPI test client: test chat endpoint returns 200, test business creation, test document listing)
      Verify: `pytest tests/test_api.py -v` — passes.

- [ ] 10. **Integration wiring, dependency injection, and app startup**
       Create a dependency injection container so routes get the agent, memory engine, orchestrator, etc. properly initialized. Add lifespan events to initialize DB and ChromaDB on startup. Add CORS middleware for future frontend.
       Files:
         - `fundfy/dependencies.py` (functions: `get_memory_engine()`, `get_agent()`, `get_orchestrator()`, `get_document_generator()` — all using FastAPI `Depends`)
         - `fundfy/main.py` (updated: add lifespan context manager, CORS middleware, wire dependencies)
         - `tests/test_integration.py` (end-to-end test: create business, send chat message, trigger execution, verify workstream created — all with mocked LLM)
       Verify: `pytest tests/ -v` — all tests pass. Then `uvicorn fundfy.main:app --host 0.0.0.0 --port 8000 &` and `curl http://localhost:8000/health` returns 200.

- [ ] 11. **README and developer documentation**
       Write a README with: project description, architecture overview, setup instructions (pyenv, install, env vars), how to run, API endpoint reference, and contribution notes.
       Files:
         - `README.md`
       Verify: File exists and is valid markdown (no broken formatting). `pip install -e ".[dev]" && pytest tests/ -v` still passes (no regressions from any accidental file changes).
