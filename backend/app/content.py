"""Offline-built content: misconception taxonomy and question bank (JSON in data/)."""
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field, model_validator

CORRECT = "correct"  # hypothesis id meaning "no misconception"


class Misconception(BaseModel):
    id: str = Field(pattern=r"^m_[a-z0-9_]+$")
    name: str
    concept_id: str
    description: str
    explanation: str  # targeted explanation shown when this misconception is diagnosed


class Option(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9]+$")
    text: str
    correct: bool = False


class Question(BaseModel):
    id: str = Field(pattern=r"^q_[a-z0-9_]+$")
    concept_id: str
    prompt: str
    options: list[Option] = Field(min_length=2)
    # hypothesis id -> {option id -> P(option | hypothesis)}. Hand-set by the author.
    # A hypothesis not listed answers like the CORRECT row.
    likelihoods: dict[str, dict[str, float]]
    explanation: str

    @model_validator(mode="after")
    def check(self):
        ids = [o.id for o in self.options]
        if len(ids) != len(set(ids)):
            raise ValueError(f"{self.id}: duplicate option ids")
        correct = [o.id for o in self.options if o.correct]
        if len(correct) != 1:
            raise ValueError(f"{self.id}: need exactly one correct option")
        if CORRECT not in self.likelihoods:
            raise ValueError(f"{self.id}: missing '{CORRECT}' likelihoods")
        for h, row in self.likelihoods.items():
            if set(row) != set(ids):
                raise ValueError(f"{self.id}/{h}: row must cover exactly the option ids")
            if any(not 0 < p <= 1 for p in row.values()):
                raise ValueError(f"{self.id}/{h}: probabilities must be in (0, 1]")
            if abs(sum(row.values()) - 1) > 1e-6:
                raise ValueError(f"{self.id}/{h}: row must sum to 1")
        row = self.likelihoods[CORRECT]
        if max(row, key=row.get) != correct[0]:
            raise ValueError(f"{self.id}: a correct student must most likely pick the correct option")
        return self

    def p_option_given(self, hypothesis: str, option_id: str) -> float:
        return self.likelihoods.get(hypothesis, self.likelihoods[CORRECT])[option_id]


class MisconceptionFile(BaseModel):
    misconceptions: list[Misconception]


class QuestionFile(BaseModel):
    questions: list[Question]


@dataclass
class Content:
    misconceptions: dict[str, Misconception]
    questions: dict[str, Question]

    @classmethod
    def load(cls, data_dir: Path, concept_ids: set[str]) -> "Content":
        mf = MisconceptionFile.model_validate_json((data_dir / "misconceptions.json").read_text())
        qf = QuestionFile.model_validate_json((data_dir / "questions.json").read_text())
        mis = {m.id: m for m in mf.misconceptions}
        qs = {q.id: q for q in qf.questions}
        if len(mis) != len(mf.misconceptions):
            raise ValueError("duplicate misconception ids")
        if len(qs) != len(qf.questions):
            raise ValueError("duplicate question ids")
        for m in mis.values():
            if m.concept_id not in concept_ids:
                raise ValueError(f"{m.id}: unknown concept {m.concept_id}")
        for q in qs.values():
            if q.concept_id not in concept_ids:
                raise ValueError(f"{q.id}: unknown concept {q.concept_id}")
            unknown = set(q.likelihoods) - set(mis) - {CORRECT}
            if unknown:
                raise ValueError(f"{q.id}: unknown hypotheses {sorted(unknown)}")
        return cls(mis, qs)

    def hypothesis_name(self, h: str) -> str:
        return "No misconception" if h == CORRECT else self.misconceptions[h].name
