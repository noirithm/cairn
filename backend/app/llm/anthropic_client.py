import os

from .base import LLMClient


class AnthropicClient(LLMClient):
    def __init__(self, model: str | None = None):
        import anthropic  # lazy: only needed when this provider is selected

        self._client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
        self._model = model or os.getenv("CAIRN_LLM_MODEL", "claude-haiku-4-5-20251001")

    def _complete(self, system: str, user: str) -> str:
        msg = self._client.messages.create(
            model=self._model, max_tokens=600, system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in msg.content if b.type == "text")
