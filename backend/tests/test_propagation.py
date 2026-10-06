import pytest

from app.engine.propagation import evidence_strengths, update_mastery
from app.graph import ConceptGraph
from app.main import DATA_DIR
from app.schemas import Concept, Edge, GraphFile


def make_graph(ids, edges):
    return ConceptGraph(GraphFile(
        unit="t", source="t",
        concepts=[Concept(id=i, name=i, description="d", section="0") for i in ids],
        edges=[Edge(prereq=a, dependent=b, strength=s) for a, b, s in edges],
    ))


def test_strength_multiplies_along_chain():
    g = make_graph("abc", [("a", "b", 0.8), ("b", "c", 0.5)])
    assert evidence_strengths(g, "c") == pytest.approx({"c": 1.0, "b": 0.5, "a": 0.4})


def test_strongest_path_wins():
    g = make_graph("abd", [("a", "b", 0.5), ("b", "d", 0.5), ("a", "d", 0.6)])
    assert evidence_strengths(g, "d")["a"] == pytest.approx(0.6)


def test_wrong_answer_lowers_closer_prereqs_more():
    g = make_graph("abc", [("a", "b", 0.8), ("b", "c", 0.5)])
    before = {"a": 0.5, "b": 0.5, "c": 0.5}
    after = update_mastery(g, before, "c", correct=False)
    assert after["c"] < 0.5 and after["b"] < 0.5 and after["a"] < 0.5
    assert before["b"] - after["b"] > before["a"] - after["a"]


def test_descendants_and_unrelated_untouched():
    g = make_graph("abcx", [("a", "b", 0.8), ("b", "c", 0.5)])
    before = {k: 0.5 for k in "abcx"}
    after = update_mastery(g, before, "b", correct=False)
    assert after["c"] == before["c"] and after["x"] == before["x"]


def test_correct_answer_changes_only_that_concept():
    g = make_graph("abc", [("a", "b", 0.8), ("b", "c", 0.5)])
    before = {k: 0.5 for k in "abc"}
    after = update_mastery(g, before, "c", correct=True)
    assert after["c"] > 0.5
    assert after["a"] == 0.5 and after["b"] == 0.5


def test_input_not_mutated():
    g = make_graph("ab", [("a", "b", 0.8)])
    before = {"a": 0.5, "b": 0.5}
    snapshot = dict(before)
    update_mastery(g, before, "b", correct=False)
    assert before == snapshot


def test_toy_numeric_example():
    # strength 1.0 -> s = 0.5; like_known = 0.3, like_unknown = 0.65; p=0.3 -> 0.09/0.545
    g = make_graph("ab", [("a", "b", 1.0)])
    after = update_mastery(g, {"a": 0.3, "b": 0.3}, "b", correct=False)
    assert after["a"] == pytest.approx(0.165138, abs=1e-5)
    assert after["b"] == pytest.approx(0.193220, abs=1e-5)


def test_real_graph_changed_set_is_concept_plus_ancestors():
    g = ConceptGraph.load(DATA_DIR / "graph.json")
    before = {c: 0.5 for c in g.g.nodes}
    after = update_mastery(g, before, "incline", correct=False)
    changed = {c for c in before if after[c] != before[c]}
    assert changed == g.all_prerequisites("incline") | {"incline"}


def test_real_graph_worked_example():
    g = ConceptGraph.load(DATA_DIR / "graph.json")
    before = {c: 0.3 for c in g.g.nodes}
    after = update_mastery(g, before, "newton_2", correct=False)
    assert after["net_force"] == pytest.approx(0.1776, abs=1e-4)
    assert after["vectors"] == pytest.approx(0.2006, abs=1e-4)
    assert after["newton_2"] == pytest.approx(0.1932, abs=1e-4)
