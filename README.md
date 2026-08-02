# Fundfy AI Business Execution Platform

An AI-native business execution platform agent that helps founders build, validate, and scale their businesses using RAG (Retrieval-Augmented Generation).

## Architecture Overview

```
fundfy/
├── main.py              # FastAPI app entry point
├── config.py            # Pydantic-settings configuration
├── db.py                # Async SQLAlchemy engine/session
├── dependencies.py      # Dependency injection container
├── models/              # SQLAlchemy async models
│   ├── founder.py       # Founder entity
│   ├── business.py      # Business entity
│   ├── conversation.py  # Conversation & Message
│   ├── document.py      # Generated documents
│   └── workstream.py    # Workstream tasks
├── memory/              # RAG memory layer
│   ├── engine.py        # ChromaDB vector store wrapper
│   └── embeddings.py    # OpenAI embeddings factory
├── core/                # AI agent
│   ├── agent.py         # FundfyAgent (RAG + LLM)
│   └── prompts.py       # System prompt templates
├── orchestrator/        # Execution orchestrator
│   ├── planner.py       # LLM-based task decomposition
│   ├── dispatcher.py    # Async concurrent dispatch
│   └── handlers/        # Task type handlers
│       ├── base.py      # Abstract BaseHandler
│       └── registry.py  # Handler registry
├── intelligence/        # Intelligence workstreams
│   ├── market_research.py
│   ├── competitor_analysis.py
│   ├── idea_validation.py
│   └── financial_reasoning.py
├── documents/           # Document generation
│   ├── generator.py     # LLM-powered document writer
│   ├── templates.py     # Prompt templates per doc type
│   └── handlers.py      # Orchestrator handler
├── communication/       # Founder communication
│   ├── modes.py         # ConversationMode enum
│   ├── prompts.py       # Mode-specific prompts
│   └── session.py       # Communication session manager
└── api/                 # REST API
    ├── schemas.py       # Pydantic request/response models
    ├── routes_chat.py   # POST /api/chat
    ├── routes_business.py       # Business CRUD
    ├── routes_execution.py      # Execution orchestrator
    ├── routes_documents.py      # Document generation
    └── routes_communication.py  # Communication sessions
```

## Tech Stack

- **Framework:** FastAPI (async)
- **RAG:** LangChain + ChromaDB
- **LLM:** OpenAI GPT-4o via `langchain-openai`
- **Embeddings:** OpenAI `text-embedding-3-small`
- **Database:** SQLite via async SQLAlchemy + aiosqlite
- **Testing:** pytest + pytest-asyncio

## Setup

### Prerequisites

- Python 3.11 (via pyenv)
- pip

### Installation

```bash
# Set Python version
pyenv local 3.11.15

# Install in development mode
pip install -e ".[dev]"
```

### Environment Variables

Copy `.env.example` to `.env` and set your values:

```bash
cp .env.example .env
```

Required variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | `sk-test-key` |
| `DATABASE_URL` | SQLAlchemy async database URL | `sqlite+aiosqlite:///./fundfy.db` |
| `CHROMA_PERSIST_DIR` | ChromaDB persistence directory | `./chroma_data` |

## Running

```bash
# Start the server
uvicorn fundfy.main:app --host 0.0.0.0 --port 8000

# With auto-reload for development
uvicorn fundfy.main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoint Reference

### Health Check
- `GET /health` — Returns `{"status": "healthy"}`

### Chat
- `POST /api/chat` — Main conversational endpoint
  - Body: `{"founder_id": "...", "message": "..."}`
  - Returns: `{"response": "...", "founder_id": "..."}`

### Business
- `POST /api/business` — Create a business profile
  - Body: `{"founder_id": "...", "name": "...", "industry": "...", "stage": "..."}`
- `GET /api/business/{id}` — Get business details

### Execution
- `POST /api/execute` — Trigger execution orchestrator
  - Body: `{"business_id": "...", "objective": "...", "context": "..."}`
- `GET /api/workstreams/{business_id}` — List workstream tasks

### Documents
- `POST /api/documents/generate` — Generate a document
  - Body: `{"business_id": "...", "doc_type": "...", "context": "..."}`
  - Supported types: `business_plan`, `executive_summary`, `pitch_deck`, `prd`, `brd`, `sop`, `financial_model`, `dpr`, `company_profile`
- `GET /api/documents/{id}` — Get a document
- `GET /api/documents?business_id=X` — List documents for a business

### Communication
- `POST /api/communication/session` — Start/continue a session
  - Body: `{"founder_id": "...", "mode": "chat|mock_interview|pitch_practice|qa_rehearsal", "message": "..."}`

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_agent.py -v
```

All tests use mocked LLM/embedding calls and do not require actual API keys.

## Contributing

1. Follow the existing package structure for new modules
2. Add tests for all new functionality
3. Mock external API calls in tests
4. Use async patterns consistently
