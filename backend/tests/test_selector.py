from math import log2
from types import SimpleNamespace

import pytest

from app.content import CORRECT, Question
from app.engine.diagnosis import entropy, initial_belief, replay_belief, update_belief
from app.engine.selector import expected_information_gain, pick_next


def make_q(qid, rows):
    return Question(
        id=qid, concept_id="newton_1", prompt="p", explanation="e",
        options=[{"id": "a", "text": "A", "correct": True}, {"id": "b", "text": "B"},
                 {"id": "c", "text": "C"}],
        likelihoods={CORRECT: rows[0], "m_a": rows[1], "m_b": rows[2]},
    )


ROWS_1 = [{"a": 0.8, "b": 0.1, "c": 0.1}, {"a": 0.1, "b": 0.8, "c": 0.1}, {"a": 0.1, "b": 0.1, "c": 0.8}]
ROWS_2 = [{"a": 0.8, "b": 0.1, "c": 0.1}, {"a": 0.1, "b": 0.45, "c": 0.45}, {"a": 0.1, "b": 0.45, "c": 0.45}]
Q1 = make_q("q_one", ROWS_1)
Q2 = make_q("q_two", ROWS_2)
UNIFORM = {CORRECT: 1 / 3, "m_a": 1 / 3, "m_b": 1 / 3}


def test_entropy_uniform():
    assert entropy(UNIFORM) == pytest.approx(log2(3))


def test_initial_belief_sums_to_one():
    b = initial_belief(["m_a", "m_b"])
    assert sum(b.values()) == pytest.approx(1) and b[CORRECT] == 0.4


def test_update_belief_matches_lesson_example():
    post = update_belief(UNIFORM, Q1, "b")
    assert post == pytest.approx({CORRECT: 0.1, "m_a": 0.8, "m_b": 0.1})


def test_eig_matches_lesson_numbers():
    assert expected_information_gain(UNIFORM, Q1) == pytest.approx(0.663, abs=1e-3)
    assert expected_information_gain(UNIFORM, Q2) == pytest.approx(0.365, abs=1e-3)


def test_uninformative_question_has_zero_gain():
    flat = {"a": 0.5, "b": 0.3, "c": 0.2}
    q = make_q("q_flat", [flat, flat, flat])
    assert expected_information_gain(UNIFORM, q) == pytest.approx(0, abs=1e-9)


def test_pick_next_prefers_informative_and_skips_asked():
    assert pick_next(UNIFORM, [Q2, Q1], set()).id == "q_one"
    assert pick_next(UNIFORM, [Q1, Q2], {"q_one"}).id == "q_two"


def test_pick_next_none_when_exhausted():
    assert pick_next(UNIFORM, [Q1], {"q_one"}) is None


def test_tie_break_is_smallest_id():
    qa, qb = make_q("q_a", ROWS_1), make_q("q_b", ROWS_1)
    assert pick_next(UNIFORM, [qb, qa], set()).id == "q_a"


def test_replay_belief_ignores_unknown_questions():
    content = SimpleNamespace(misconceptions={"m_a": None, "m_b": None}, questions={"q_one": Q1})
    attempts = [SimpleNamespace(question_id="manual", answer="a"),
                SimpleNamespace(question_id="q_one", answer="b")]
    expected = update_belief(initial_belief(["m_a", "m_b"]), Q1, "b")
    assert replay_belief(content, attempts) == pytest.approx(expected)
