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
