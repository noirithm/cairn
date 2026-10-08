import json
import re

import pytest
from sympy import Integer, Rational

from app.content import Content
from app.graph import ConceptGraph
from app.llm.base import LLMClient, LLMError
from app.main import DATA_DIR
from app.transfer.generate import build_problem, generate, solve, verify
from app.transfer.phrase import Phrased, phrase
from app.transfer.templates import TEMPLATES, TEMPLATES_BY_ID

I = Integer


class FakeLLM(LLMClient):
    def __init__(self, replies):
        self.replies, self.calls = list(replies), 0

    def _complete(self, system, user):
        self.calls += 1
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


def _answer(tid, **p):
    _, sol, target = solve(TEMPLATES_BY_ID[tid], p)
    return sol[target]


def _tension_problem():
    return generate(TEMPLATES_BY_ID["t_tension"], "phrase")


def test_all_templates_generate_verified_problems():
    for t in TEMPLATES:
        for i in range(100):
            assert generate(t, f"s{i}").answer_float is not None


def test_known_answers():
    assert _answer("t_net_accel", m=I(5), F1=I(45), F2=I(20)) == 5
    assert _answer("t_normal", m=I(10), P=I(20), dir="down") == 118
    assert _answer("t_normal", m=I(10), P=I(20), dir="up") == 78
    assert _answer("t_friction_static", m=I(20), mu=Rational(1, 2), F=I(40)) == 40
    assert _answer("t_friction_kinetic", m=I(10), mu=Rational(3, 10), F=I(50)) == Rational(103, 50)
    assert _answer("t_incline", m=I(3), theta=I(30)) == Rational(49, 10)
    assert _answer("t_tension", m1=I(2), m2=I(3), F=I(30)) == 18
    assert _answer("t_weight", m=I(60), g=Rational(8, 5), planet="the Moon") == 96
    static = TEMPLATES_BY_ID["t_friction_static"]
    assert static.traps(dict(m=I(20), mu=Rational(1, 2), F=I(40)))["m_friction_always_mu_n"] == 98


def test_verify_rejects_wrong_answers():
    t, p = TEMPLATES_BY_ID["t_normal"], dict(m=I(10), P=I(20), dir="down")
    assert verify(t, p, I(118))
    assert not verify(t, p, I(119))
    assert not verify(t, p, I(98))  # the "N = mg" trap value


def test_generation_is_deterministic_and_varied():
    assert build_problem("t_tension", "x:1") == build_problem("t_tension", "x:1")
    assert len({build_problem("t_tension", f"v{i}").stem for i in range(40)}) > 5


def test_every_template_has_three_hints():
    for t in TEMPLATES:
        assert len(generate(t, "h").hints) == 3


def test_traps_match_taxonomy():
    g = ConceptGraph.load(DATA_DIR / "graph.json")
    content = Content.load(DATA_DIR, set(g.g.nodes))
    for t in TEMPLATES:
        for i in range(10):
            for mid in generate(t, f"t{i}").traps:
                assert mid in content.misconceptions


def test_template_concepts():
    assert {t.concept_id for t in TEMPLATES} == {
        "newton_2", "weight", "normal", "friction", "incline", "tension"}


def test_phrase_keeps_numbers():
    problem = _tension_problem()
    reply = json.dumps({"text": problem.stem.replace("block", "cart")})
    text, source = phrase(problem.stem, FakeLLM([reply]))
    assert source == "llm" and "cart" in text


def test_phrase_falls_back_on_changed_numbers():
    problem = _tension_problem()
    reply = json.dumps({"text": re.sub(r"\d+", "999", problem.stem, count=1)})
    assert phrase(problem.stem, FakeLLM([reply])) == (problem.stem, "template")


def test_phrase_falls_back_on_llm_error_or_no_llm():
    problem = _tension_problem()
    assert phrase(problem.stem, FakeLLM([RuntimeError("boom")])) == (problem.stem, "template")
    assert phrase(problem.stem, None) == (problem.stem, "template")


def test_complete_json_retries_then_succeeds():
    problem = _tension_problem()
    good = json.dumps({"text": problem.stem})
    llm = FakeLLM(["not json at all", good])
    text, source = phrase(problem.stem, llm)
    assert source == "llm" and llm.calls == 2


def test_complete_json_gives_up():
    with pytest.raises(LLMError):
        FakeLLM(["x", "x", "x"]).complete_json("s", "u", Phrased)
