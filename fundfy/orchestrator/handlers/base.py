"""Base handler for workstream tasks."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class TaskResult:
    """Result of a workstream task execution."""

    task_id: str
    task_type: str
    status: str  # "completed", "failed"
    result: dict[str, Any] | None = None
    error: str | None = None


class BaseHandler(ABC):
    """Abstract base handler for workstream tasks."""

    @abstractmethod
    async def run(self, task: dict[str, Any]) -> TaskResult:
        """Execute the task and return a result.

        Args:
            task: Dictionary containing task parameters.

        Returns:
            TaskResult with execution outcome.
        """
        ...
