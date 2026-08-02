"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fundfy.api.routes_chat import router as chat_router
from fundfy.api.routes_business import router as business_router
from fundfy.api.routes_execution import router as execution_router
from fundfy.api.routes_documents import router as documents_router
from fundfy.api.routes_communication import router as communication_router
from fundfy.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Initialize database
    from fundfy.db import init_db
    await init_db()

    # Initialize dependencies
    from fundfy.memory.engine import MemoryEngine
    from fundfy.core.agent import FundfyAgent
    from fundfy.orchestrator.planner import ExecutionPlanner
    from fundfy.orchestrator.dispatcher import Dispatcher
    from fundfy.orchestrator.handlers.registry import create_handlers
    from fundfy.documents.generator import DocumentGenerator
    from fundfy.dependencies import init_dependencies

    memory_engine = MemoryEngine()
    agent = FundfyAgent(memory_engine=memory_engine)
    planner = ExecutionPlanner()
    handlers = create_handlers(memory_engine=memory_engine)
    dispatcher = Dispatcher(handlers=handlers)
    document_generator = DocumentGenerator(memory_engine=memory_engine)

    init_dependencies(
        memory_engine=memory_engine,
        agent=agent,
        planner=planner,
        dispatcher=dispatcher,
        document_generator=document_generator,
        llm=agent._llm,
    )

    yield


app = FastAPI(
    title="Fundfy AI Business Execution Platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router)
app.include_router(business_router)
app.include_router(execution_router)
app.include_router(documents_router)
app.include_router(communication_router)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
