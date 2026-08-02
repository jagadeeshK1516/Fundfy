"""Test Execution Orchestrator — planner and dispatcher."""

import json
from typing import Any
from unittest.mock import AsyncMock

import pytest
from langchain_core.messages import AIMessage

from fundfy.orchestrator.planner import ExecutionPlanner
from fundfy.orchestrator.dispatcher import Dispatcher
from fundfy.orchestrator.handlers.base import BaseHandler, TaskResult


class DummyHandler(BaseHandler):
    """Dummy handler that always succeeds."""

    async def run(self, task: dict[str, Any]) -> TaskResult:
        return TaskResult(
            task_id=task.get("title", "dummy"),
            task_type=task.get("type", "dummy"),
            status="completed",
            result={"message": "Task completed successfully"},
        )


@pytest.mark.asyncio
async def test_planner_parses_llm_json():
    """Planner calls LLM and parses JSON task list."""
    plan_json = json.dumps([
        {"type": "market_research", "title": "Analyze SaaS market", "params": {"industry": "SaaS"}},
        {"type": "competitor_analysis", "title": "Find competitors", "params": {"market": "CRM"}},
    ])

    mock_llm = AsyncMock()
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content=plan_json))

    planner = ExecutionPlanner(llm=mock_llm)
    tasks = await planner.plan("Launch a CRM product", "B2B SaaS startup")

    assert len(tasks) == 2
    assert tasks[0]["type"] == "market_research"
    assert tasks[1]["type"] == "competitor_analysis"


@pytest.mark.asyncio
async def test_dispatcher_executes_all_tasks():
    """Dispatcher runs all tasks concurrently and returns results."""
    dispatcher = Dispatcher()
    dispatcher.register_handler("market_research", DummyHandler())
    dispatcher.register_handler("competitor_analysis", DummyHandler())

    tasks = [
        {"type": "market_research", "title": "Research market", "params": {}},
        {"type": "competitor_analysis", "title": "Analyze competitors", "params": {}},
    ]

    results = await dispatcher.execute(tasks)

    assert len(results) == 2
    assert all(r.status == "completed" for r in results)


@pytest.mark.asyncio
async def test_dispatcher_handles_missing_handler():
    """Dispatcher returns failed result for unregistered task types."""
    dispatcher = Dispatcher()

    tasks = [{"type": "unknown_type", "title": "Unknown task", "params": {}}]
    results = await dispatcher.execute(tasks)

    assert len(results) == 1
    assert results[0].status == "failed"
    assert "No handler registered" in results[0].error
