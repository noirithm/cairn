import os

import httpx

from .base import LLMClient


class OllamaClient(LLMClient):
    def __init__(self, model: str | None = None, host: str | None = None):
        self._model = model or os.getenv("CAIRN_LLM_MODEL", "llama3.1")
        self._host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")

    def _complete(self, system: str, user: str) -> str:
        r = httpx.post(
            f"{self._host}/api/chat", timeout=60,
            json={"model": self._model, "stream": False, "format": "json",
                  "messages": [{"role": "system", "content": system},
                               {"role": "user", "content": user}]},
        )
        r.raise_for_status()
        return r.json()["message"]["content"]
