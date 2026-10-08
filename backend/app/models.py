"""SQLModel = SQLAlchemy table + Pydantic model in one class."""
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Student(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = "anonymous"
    is_simulated: bool = False
    created_at: datetime = Field(default_factory=_now)


class Mastery(SQLModel, table=True):
    """Current BKT belief P(known) per (student, concept)."""
    student_id: int = Field(foreign_key="student.id", primary_key=True)
    concept_id: str = Field(primary_key=True)
    p_known: float
    updated_at: datetime = Field(default_factory=_now)


class Attempt(SQLModel, table=True):
    """Append-only answer log; mastery can be recomputed from it."""
    id: int | None = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="student.id", index=True)
    concept_id: str = Field(index=True)
    question_id: str
    answer: str
    correct: bool
    created_at: datetime = Field(default_factory=_now)


class TransferProblem(SQLModel, table=True):
    """A generated problem. The answer is NOT stored: it is rebuilt from (template_id, seed)."""
    id: int | None = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="student.id", index=True)
    template_id: str
    concept_id: str
    seed: str
    stem: str  # the text the student saw (template wording or LLM re-wording)
    unit: str
    hints_used: int = 0
    submissions: int = 0
    solved: bool = False
    counted: bool = False  # mastery already updated for this problem
    created_at: datetime = Field(default_factory=_now)
