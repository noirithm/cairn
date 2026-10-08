"""Pydantic schemas: the validation boundary for graph files and API payloads."""
from pydantic import BaseModel, Field, model_validator


class Concept(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9_]+$")
    name: str
    description: str
    section: str  # OpenStax section reference


class Edge(BaseModel):
    prereq: str
    dependent: str
    # How strongly failing `dependent` implicates `prereq` (propagation weight).
    strength: float = Field(gt=0, le=1)


class GraphFile(BaseModel):
    unit: str
    source: str
    concepts: list[Concept]
    edges: list[Edge]

    @model_validator(mode="after")
    def check_references(self):
        ids = [c.id for c in self.concepts]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate concept ids")
        known = set(ids)
        for e in self.edges:
            if e.prereq not in known or e.dependent not in known:
                raise ValueError(f"edge references unknown concept: {e.prereq} -> {e.dependent}")
            if e.prereq == e.dependent:
                raise ValueError(f"self-loop on {e.prereq}")
        return self


# ---- API response shapes ----
class SessionOut(BaseModel):
    session_id: int


class NodeOut(BaseModel):
    id: str
    name: str
    section: str
    p_known: float  # belief the student knows this concept (0-1)


class GraphOut(BaseModel):
    unit: str
    nodes: list[NodeOut]
    edges: list[Edge]


class OptionOut(BaseModel):  # note: no `correct` flag, the client must not see the answer
    id: str
    text: str


class QuestionOut(BaseModel):
    id: str
    concept_id: str
    prompt: str
    options: list[OptionOut]


class NextQuestionOut(BaseModel):
    question: QuestionOut | None  # None once the bank is used up
    expected_gain: float = 0.0  # bits of information this question is expected to give


class AnswerIn(BaseModel):
    question_id: str
    option_id: str


class DiagnosisEntry(BaseModel):
    id: str
    name: str
    p: float
    explanation: str | None = None  # targeted explanation (misconceptions only)


class AnswerOut(BaseModel):
    correct: bool
    explanation: str
    mastery: dict[str, float]
    diagnosis: list[DiagnosisEntry]  # all hypotheses, most likely first
    diagnosed: DiagnosisEntry | None = None  # set once a misconception passes the threshold


class DiagnosisOut(BaseModel):
    diagnosis: list[DiagnosisEntry]
    entropy: float


class TransferIn(BaseModel):
    concept_id: str | None = None  # omitted -> the weakest concept that has transfer problems


class TransferOut(BaseModel):
    problem_id: int
    concept_id: str
    text: str
    unit: str
    hints_available: int
    phrased_by: str  # "template" or "llm"


class HintOut(BaseModel):
    level: int
    text: str
    remaining: int


class TransferAnswerIn(BaseModel):
    value: float


class TrapOut(BaseModel):
    misconception_id: str
    name: str
    explanation: str


class TransferResultOut(BaseModel):
    correct: bool
    mastery_updated: bool
    hints_used: int
    mastery: dict[str, float]
    solution: str | None = None  # only revealed once the answer is correct
    trap: TrapOut | None = None  # set when a wrong answer matches a known misconception
