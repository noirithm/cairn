import pytest

from app.graph import ConceptGraph
from app.main import DATA_DIR
from app.schemas import Concept, Edge, GraphFile


def _file(ids, edges):
    return GraphFile(
        unit="t", source="t",
        concepts=[Concept(id=i, name=i, description="d", section="0") for i in ids],
        edges=[Edge(prereq=a, dependent=b, strength=0.5) for a, b in edges],
    )


def test_real_graph_loads_and_is_acyclic():
    g = ConceptGraph.load(DATA_DIR / "graph.json")
    assert len(g.data.concepts) == 14


def test_topo_order_puts_prereqs_first():
    g = ConceptGraph.load(DATA_DIR / "graph.json")
    pos = {c: i for i, c in enumerate(g.topo_order())}
    for e in g.data.edges:
        assert pos[e.prereq] < pos[e.dependent]


def test_transitive_prerequisites():
    g = ConceptGraph.load(DATA_DIR / "graph.json")
    assert {"vectors", "force", "net_force", "fbd", "normal"} <= g.all_prerequisites("incline")
    assert g.prerequisites("vectors") == []


def test_cycle_rejected():
    with pytest.raises(ValueError, match="cycle"):
        ConceptGraph(_file(["a", "b"], [("a", "b"), ("b", "a")]))


def test_unknown_edge_reference_rejected():
    with pytest.raises(ValueError):
        _file(["a"], [("a", "zzz")])
