"""Concept graph: validated JSON -> NetworkX DiGraph. Edge direction: prereq -> dependent.
Cycles are rejected at load: Day 2 propagation would loop forever on A -> B -> A."""
from pathlib import Path

import networkx as nx

from .schemas import GraphFile


class ConceptGraph:
    def __init__(self, data: GraphFile):
        g = nx.DiGraph()
        for c in data.concepts:
            g.add_node(c.id)
        for e in data.edges:
            g.add_edge(e.prereq, e.dependent, strength=e.strength)
        if not nx.is_directed_acyclic_graph(g):
            raise ValueError(f"prerequisite graph has a cycle: {nx.find_cycle(g)}")
        self.g = g
        self.data = data

    @classmethod
    def load(cls, path: Path) -> "ConceptGraph":
        return cls(GraphFile.model_validate_json(Path(path).read_text()))

    def prerequisites(self, concept_id: str) -> list[str]:
        return list(self.g.predecessors(concept_id))

    def all_prerequisites(self, concept_id: str) -> set[str]:
        return nx.ancestors(self.g, concept_id)

    def topo_order(self) -> list[str]:
        return list(nx.topological_sort(self.g))
