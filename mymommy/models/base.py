from abc import ABC, abstractmethod
from typing import List, Dict, Any, Generator

class BaseModelProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = None) -> str:
        pass

    @abstractmethod
    def stream_generate(self, prompt: str, system_prompt: str = None) -> Generator[str, None, None]:
        pass

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]]) -> str:
        pass

    @abstractmethod
    def stream_chat(self, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        pass
