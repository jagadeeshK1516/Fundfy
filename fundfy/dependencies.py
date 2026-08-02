"""Dependency injection for FastAPI routes."""

from typing import Any

from fundfy.core.agent import FundfyAgent
from fundfy.documents.generator import DocumentGenerator
from fundfy.memory.engine import MemoryEngine
from fundfy.orchestrator.dispatcher import Dispatcher
from fundfy.orchestrator.planner import ExecutionPlanner

# Global instances (initialized at startup)
_memory_engine: MemoryEngine | None = None
_agent: FundfyAgent | None = None
_planner: ExecutionPlanner | None = None
_dispatcher: Dispatcher | None = None
_document_generator: DocumentGenerator | None = None
_llm: Any = None


def init_dependencies(
    memory_engine: MemoryEngine | None = None,
    agent: FundfyAgent | None = None,
    planner: ExecutionPlanner | None = None,
    dispatcher: Dispatcher | None = None,
    document_generator: DocumentGenerator | None = None,
    llm: Any = None,
):
    """Initialize global dependencies."""
    global _memory_engine, _agent, _planner, _dispatcher, _document_generator, _llm
    _memory_engine = memory_engine
    _agent = agent
    _planner = planner
    _dispatcher = dispatcher
    _document_generator = document_generator
    _llm = llm


def get_memory_engine() -> MemoryEngine:
    """Get the memory engine instance."""
    if _memory_engine is None:
        raise RuntimeError("Memory engine not initialized. Call init_dependencies first.")
    return _memory_engine


def get_agent() -> FundfyAgent:
    """Get the agent instance."""
    if _agent is None:
        raise RuntimeError("Agent not initialized. Call init_dependencies first.")
    return _agent


def get_orchestrator() -> tuple[ExecutionPlanner, Dispatcher]:
    """Get the orchestrator (planner + dispatcher)."""
    if _planner is None or _dispatcher is None:
        raise RuntimeError("Orchestrator not initialized. Call init_dependencies first.")
    return _planner, _dispatcher


def get_document_generator() -> DocumentGenerator:
    """Get the document generator instance."""
    if _document_generator is None:
        raise RuntimeError("Document generator not initialized. Call init_dependencies first.")
    return _document_generator


def get_agent_llm() -> Any:
    """Get the shared LLM instance."""
    return _llm
