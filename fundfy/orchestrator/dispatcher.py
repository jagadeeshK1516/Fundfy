"""Dispatcher — runs workstream tasks concurrently."""

import asyncio
from typing import Any

from fundfy.orchestrator.handlers.base import BaseHandler, TaskResult


class Dispatcher:
    """Dispatches workstream tasks to handlers and executes concurrently."""

    def __init__(self, handlers: dict[str, BaseHandler] | None = None):
        self._handlers = handlers or {}

    def register_handler(self, task_type: str, handler: BaseHandler):
        """Register a handler for a given task type."""
        self._handlers[task_type] = handler

    async def execute(self, tasks: list[dict[str, Any]]) -> list[TaskResult]:
        """Execute a list of tasks concurrently via asyncio.gather.

        Args:
            tasks: List of task dictionaries with at least 'type' and 'params'.

        Returns:
            List of TaskResult objects.
        """

        async def run_task(task: dict[str, Any]) -> TaskResult:
            task_type = task.get("type", "unknown")
            task_id = task.get("id", task.get("title", "unknown"))
            handler = self._handlers.get(task_type)

            if not handler:
                return TaskResult(
                    task_id=task_id,
                    task_type=task_type,
                    status="failed",
                    error=f"No handler registered for type: {task_type}",
                )

            try:
                result = await handler.run(task)
                return result
            except Exception as e:
                return TaskResult(
                    task_id=task_id,
                    task_type=task_type,
                    status="failed",
                    error=str(e),
                )

        results = await asyncio.gather(*[run_task(t) for t in tasks])
        return list(results)
