"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fundfy.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # 1. Setup logging
    from fundfy.logging import setup_logging
    setup_logging()

    # 2. Initialize Redis
    from fundfy.redis import init_redis, close_redis
    await init_redis()

    # 3. Initialize database
    from fundfy.db import init_db
    await init_db()

    # 4. Initialize dependencies
    from fundfy.memory.engine import MemoryEngine
    from fundfy.core.agent import FundfyAgent
    from fundfy.orchestrator.planner import ExecutionPlanner
    from fundfy.orchestrator.dispatcher import Dispatcher
    from fundfy.orchestrator.handlers.registry import create_handlers
    from fundfy.documents.generator import DocumentGenerator
    from fundfy.tools.registry import create_tool_registry
    from fundfy.dependencies import init_dependencies

    memory_engine = MemoryEngine()
    document_generator = DocumentGenerator(memory_engine=memory_engine)

    # Create a temporary agent to get the LLM instance
    temp_agent = FundfyAgent(memory_engine=memory_engine)
    llm = temp_agent._llm

    # Create tool registry
    tool_registry = create_tool_registry(
        llm=llm,
        memory_engine=memory_engine,
        document_generator=document_generator,
    )

    # Create the real agent with tools
    agent = FundfyAgent(memory_engine=memory_engine, llm=llm, tools=tool_registry)
    planner = ExecutionPlanner()
    handlers = create_handlers(memory_engine=memory_engine)
    dispatcher = Dispatcher(handlers=handlers)

    init_dependencies(
        memory_engine=memory_engine,
        agent=agent,
        planner=planner,
        dispatcher=dispatcher,
        document_generator=document_generator,
        llm=llm,
    )

    yield

    # Shutdown
    await close_redis()


app = FastAPI(
    title="Fundfy AI Business Execution Platform",
    version="0.2.0",
    lifespan=lifespan,
)

# Middleware ordering: RequestID -> Logging -> RateLimit -> Auth -> CORS
# (added in reverse order since Starlette processes them in stack order)

# CORS middleware (outermost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth middleware
from fundfy.auth.middleware import AuthMiddleware  # noqa: E402
app.add_middleware(AuthMiddleware)

# Rate limit middleware
from fundfy.middleware.rate_limit import RateLimitMiddleware  # noqa: E402
app.add_middleware(RateLimitMiddleware)

# Logging middleware
from fundfy.middleware.logging import LoggingMiddleware  # noqa: E402
app.add_middleware(LoggingMiddleware)

# Request ID middleware (innermost to response, outermost to request)
from fundfy.middleware.request_id import RequestIDMiddleware  # noqa: E402
app.add_middleware(RequestIDMiddleware)

# Include routers
from fundfy.api.routes_chat import router as chat_router  # noqa: E402
from fundfy.api.routes_business import router as business_router  # noqa: E402
from fundfy.api.routes_execution import router as execution_router  # noqa: E402
from fundfy.api.routes_documents import router as documents_router  # noqa: E402
from fundfy.api.routes_communication import router as communication_router  # noqa: E402
from fundfy.api.routes_files import router as files_router  # noqa: E402
from fundfy.api.routes_auth import router as auth_router  # noqa: E402
from fundfy.api.routes_jobs import router as jobs_router  # noqa: E402
from fundfy.api.routes_health import router as health_router  # noqa: E402
from fundfy.api.routes_integrations import router as integrations_router  # noqa: E402
from fundfy.api.routes_crm import router as crm_router  # noqa: E402
from fundfy.api.routes_notifications import router as notifications_router  # noqa: E402

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(business_router)
app.include_router(execution_router)
app.include_router(documents_router)
app.include_router(communication_router)
app.include_router(files_router)
app.include_router(jobs_router)
app.include_router(integrations_router)
app.include_router(crm_router)
app.include_router(notifications_router)
