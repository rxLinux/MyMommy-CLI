import ollama
from typing import List, Dict, Any, Generator
from mymommy.models.base import BaseModelProvider
from mymommy.config.settings import settings

class OllamaProvider(BaseModelProvider):
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.DEFAULT_MODEL
        self.client = ollama.Client(host=settings.OLLAMA_BASE_URL)

    def generate(self, prompt: str, system_prompt: str = None) -> str:
        response = self.client.generate(
            model=self.model_name,
            prompt=prompt,
            system=system_prompt
        )
        return response['response']

    def stream_generate(self, prompt: str, system_prompt: str = None) -> Generator[str, None, None]:
        stream = self.client.generate(
            model=self.model_name,
            prompt=prompt,
            system=system_prompt,
            stream=True
        )
        for chunk in stream:
            yield chunk['response']

    def chat(self, messages: List[Dict[str, str]]) -> str:
        response = self.client.chat(
            model=self.model_name,
            messages=messages
        )
        return response['message']['content']

    def stream_chat(self, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        stream = self.client.chat(
            model=self.model_name,
            messages=messages,
            stream=True
        )
        for chunk in stream:
            yield chunk['message']['content']
