from random import Random
from types import SimpleNamespace

from app.content import Content
from app.engine.diagnosis import diagnosed_id, replay_belief
from app.graph import ConceptGraph
from app.main import DATA_DIR
from app.simulation import check_prevalence, simulate_student

GRAPH = ConceptGraph.load(DATA_DIR / "graph.json")
CONTENT = Content.load(DATA_DIR, set(GRAPH.g.nodes))


def test_prevalence_names_real_misconceptions():
    check_prevalence(CONTENT)  # raises if the table names an unknown id


def test_simulation_is_deterministic():
    assert simulate_student(GRAPH, CONTENT, Random(1)) == simulate_student(GRAPH, CONTENT, Random(1))


def test_simulated_students_follow_the_selector_and_never_repeat():
    rng = Random(3)
    for _ in range(20):
        r = simulate_student(GRAPH, CONTENT, rng)
        ids = [a[0] for a in r.attempts]
        assert 5 <= len(ids) <= 8 and len(set(ids)) == len(ids)
        assert len(r.held) <= 2


def test_hidden_misconceptions_are_mostly_recovered():
    rng = Random(7)
    with_held = hits = 0
    for _ in range(30):
        r = simulate_student(GRAPH, CONTENT, rng)
        if not r.held:
            continue
        with_held += 1
        attempts = [SimpleNamespace(question_id=q, answer=o) for q, _, o, _ in r.attempts]
        if diagnosed_id(replay_belief(CONTENT, attempts)) in r.held:
            hits += 1
    assert with_held >= 20 and hits / with_held >= 0.5  # about 17 of 29 with seed 7
