"""Pydantic schemas: the validation boundary for graph files and API payloads."""
from pydantic import BaseModel, Field, model_validator


class Concept(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9_]+$")
    name: str
    description: str
    section: str


class Edge(BaseModel):
    prereq: str
    dependent: str
    # How strongly failing `dependent` implicates `prereq` (Day 2 propagation).
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


class SessionOut(BaseModel):
    session_id: int


class NodeOut(BaseModel):
    id: str
    name: str
    section: str
    p_known: float


class GraphOut(BaseModel):
    unit: str
    nodes: list[NodeOut]
    edges: list[Edge]
