import pytest

from app.content import CORRECT, Content, Question
from app.graph import ConceptGraph
from app.main import DATA_DIR


def _q(**over):
    base = dict(
        id="q_t", concept_id="newton_1", prompt="p", explanation="e",
        options=[{"id": "a", "text": "A", "correct": True}, {"id": "b", "text": "B"}],
        likelihoods={CORRECT: {"a": 0.8, "b": 0.2}},
    )
    base.update(over)
    return Question(**base)


def _content():
    g = ConceptGraph.load(DATA_DIR / "graph.json")
    return Content.load(DATA_DIR, set(g.g.nodes))


def test_real_content_loads_and_validates():
    c = _content()
    assert len(c.misconceptions) == 7 and len(c.questions) == 8


def test_every_misconception_has_a_question():
    c = _content()
    for m in c.misconceptions:
        assert any(m in q.likelihoods for q in c.questions.values()), m


def test_row_must_sum_to_one():
    with pytest.raises(ValueError):
        _q(likelihoods={CORRECT: {"a": 0.7, "b": 0.2}})


def test_correct_row_must_favor_correct_option():
    with pytest.raises(ValueError):
        _q(likelihoods={CORRECT: {"a": 0.3, "b": 0.7}})


def test_exactly_one_correct_option():
    with pytest.raises(ValueError):
        _q(options=[{"id": "a", "text": "A", "correct": True}, {"id": "b", "text": "B", "correct": True}])


def test_zero_probability_rejected():
    with pytest.raises(ValueError):
        _q(likelihoods={CORRECT: {"a": 1.0, "b": 0.0}})


def test_content_must_reference_known_concepts():
    with pytest.raises(ValueError):
        Content.load(DATA_DIR, {"newton_1"})
