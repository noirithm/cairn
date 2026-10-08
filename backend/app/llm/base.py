"""Provider-agnostic LLM interface. The model only ever produces JSON that must pass a Pydantic schema."""
from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    pass


def _json_slice(raw: str) -> str:
    """Models sometimes wrap JSON in prose or code fences; keep the outermost {...}."""
    start, end = raw.find("{"), raw.rfind("}")
    return raw[start:end + 1] if start != -1 and end > start else raw


class LLMClient(ABC):
    @abstractmethod
    def _complete(self, system: str, user: str) -> str:
        """One raw model call. Adapters implement only this."""

    def complete_json(self, system: str, user: str, schema: type[T], max_retries: int = 2) -> T:
        """Call, validate against `schema`, and retry (telling the model what was wrong) on failure."""
        error = ""
        for _ in range(max_retries + 1):
            prompt = user if not error else (
                f"{user}\n\nYour previous reply was invalid ({error}). Reply with only the JSON object.")
            raw = self._complete(system, prompt)
            try:
                return schema.model_validate_json(_json_slice(raw))
            except ValidationError as e:
                error = str(e).replace("\n", " ")[:300]
        raise LLMError(f"no valid {schema.__name__} after {max_retries + 1} attempts: {error}")
