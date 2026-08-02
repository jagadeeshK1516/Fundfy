"""Handler registry — maps task type strings to handler classes."""

from typing import Any

from fundfy.orchestrator.handlers.base import BaseHandler
from fundfy.intelligence.market_research import MarketResearchHandler
from fundfy.intelligence.competitor_analysis import CompetitorAnalysisHandler
from fundfy.intelligence.idea_validation import IdeaValidationHandler
from fundfy.intelligence.financial_reasoning import FinancialReasoningHandler


HANDLER_REGISTRY: dict[str, type[BaseHandler]] = {
    "market_research": MarketResearchHandler,
    "competitor_analysis": CompetitorAnalysisHandler,
    "idea_validation": IdeaValidationHandler,
    "financial_reasoning": FinancialReasoningHandler,
}


def create_handlers(llm: Any = None, memory_engine: Any = None) -> dict[str, BaseHandler]:
    """Instantiate all registered handlers with shared dependencies.

    Args:
        llm: The LLM instance to use.
        memory_engine: The memory engine instance.

    Returns:
        Dictionary mapping task type to handler instance.
    """
    return {
        task_type: handler_cls(llm=llm, memory_engine=memory_engine)
        for task_type, handler_cls in HANDLER_REGISTRY.items()
    }
