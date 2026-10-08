import os

from .base import LLMClient


def from_env() -> LLMClient | None:
    """CAIRN_LLM = none (default) | anthropic | ollama. `none` means templates only."""
    provider = os.getenv("CAIRN_LLM", "none").lower()
    if provider == "none":
        return None
    if provider == "anthropic":
        from .anthropic_client import AnthropicClient
        return AnthropicClient()
    if provider == "ollama":
        from .ollama_client import OllamaClient
        return OllamaClient()
    raise ValueError(f"unknown CAIRN_LLM={provider!r} (use none, anthropic or ollama)")
