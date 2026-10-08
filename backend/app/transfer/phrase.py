"""Optional LLM re-wording of a problem. The LLM never sees the answer, and every number it
returns must match the original stem exactly, or we silently use the template wording."""
import re
from collections import Counter

from pydantic import BaseModel, Field

from ..llm.base import LLMClient

SYSTEM = (
    "You rewrite physics word problems into a new everyday context. Rules: keep every number "
    "exactly as written, using digits; do not add, remove or change any number; ask for the same "
    "quantity in the same units; do not solve the problem or give hints. "
    'Reply with only JSON: {"text": "<the rewritten problem>"}'
)


class Phrased(BaseModel):
    text: str = Field(min_length=20, max_length=700)


def numbers_in(text: str) -> Counter:
    return Counter(re.findall(r"\d+(?:\.\d+)?", text))


def phrase(stem: str, llm: LLMClient | None) -> tuple[str, str]:
    """Returns (text, source) where source is 'llm' or 'template'."""
    if llm is None:
        return stem, "template"
    try:
        out = llm.complete_json(SYSTEM, f"Problem:\n{stem}", Phrased)
    except Exception:  # any LLM failure (network, schema, key) must degrade to the template
        return stem, "template"
    if numbers_in(out.text) != numbers_in(stem):
        return stem, "template"
    return out.text, "llm"
