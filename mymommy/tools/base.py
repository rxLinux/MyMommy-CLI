from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseTool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        pass

    def get_schema(self) -> Dict[str, Any]:
        """Returns the JSON schema for the tool (for LLM function calling)."""
        # This is a simplified version; in a real scenario, we'd use Pydantic 
        # or introspect the execute method.
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self._parameters_schema()
        }

    @abstractmethod
    def _parameters_schema(self) -> Dict[str, Any]:
        pass
