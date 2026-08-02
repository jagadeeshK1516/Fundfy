"""Base tool abstraction for the Fundfy agent."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

from fundfy.tools.schemas import ToolResult


class BaseTool(ABC):
    """Abstract base class for all agent tools."""

    name: str
    description: str
    args_schema: type[BaseModel]

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with the given arguments.

        Returns:
            ToolResult with success/failure status and data.
        """
        ...

    def to_openai_function(self) -> dict[str, Any]:
        """Return the OpenAI function-calling schema dict for this tool."""
        schema = self.args_schema.model_json_schema()
        # Remove title and description from top-level schema (OpenAI expects clean properties)
        parameters = {
            "type": "object",
            "properties": schema.get("properties", {}),
            "required": schema.get("required", []),
        }
        return {
            "name": self.name,
            "description": self.description,
            "parameters": parameters,
        }
