from fastapi.testclient import TestClient
from sqlmodel import Session

from app.main import create_app
from app.models import TransferProblem
from app.transfer.generate import build_problem


def _client():
    return TestClient(create_app("sqlite://", llm_factory=lambda: None))


def _new(c):
    return c.post("/sessions").json()["session_id"]


def _mastery(c, sid):
    return {n["id"]: n["p_known"] for n in c.get(f"/sessions/{sid}/graph").json()["nodes"]}


def _make(c, sid, concept=None):
    return c.post(f"/sessions/{sid}/transfer", json={"concept_id": concept} if concept else None)


def _answer(c, sid, pid, value):
    return c.post(f"/sessions/{sid}/transfer/{pid}/answer", json={"value": value})


def _built(c, pid):
    with Session(c.app.state.engine) as db:
        row = db.get(TransferProblem, pid)
        return build_problem(row.template_id, row.seed)


def test_transfer_flow_hides_answer_and_updates_mastery_once():
    with _client() as c:
        sid = _new(c)
        r = _make(c, sid, "normal")
        assert r.status_code == 200
        body = r.json()
        assert set(body) == {"problem_id", "concept_id", "text", "unit", "hints_available",
                             "phrased_by"}
        assert body["concept_id"] == "normal" and body["phrased_by"] == "template"
        pid = body["problem_id"]
        problem = _built(c, pid)

        before = _mastery(c, sid)
        wrong = _answer(c, sid, pid, problem.answer_float + 7).json()
        assert wrong["correct"] is False and wrong["mastery_updated"] is True
        assert wrong["solution"] is None
        mid = _mastery(c, sid)
        assert mid["normal"] < before["normal"]

        right = _answer(c, sid, pid, problem.answer_float).json()
        assert right["correct"] is True and right["mastery_updated"] is False
        assert right["solution"]
        assert _mastery(c, sid) == mid  # second submission does not move mastery again


def test_hint_ladder_then_409_and_hint_assisted_success_is_neutral():
    with _client() as c:
        sid = _new(c)
        pid = _make(c, sid, "tension").json()["problem_id"]
        for level in (1, 2, 3):
            r = c.post(f"/sessions/{sid}/transfer/{pid}/hint")
            assert r.status_code == 200
            assert r.json()["level"] == level and r.json()["remaining"] == 3 - level
        assert c.post(f"/sessions/{sid}/transfer/{pid}/hint").status_code == 409
        before = _mastery(c, sid)
        r = _answer(c, sid, pid, _built(c, pid).answer_float).json()
        assert r["correct"] is True and r["mastery_updated"] is False
        assert _mastery(c, sid) == before


def test_trap_answer_returns_misconception_feedback():
    with _client() as c:
        sid = _new(c)
        pid = _make(c, sid, "weight").json()["problem_id"]
        trap_value = _built(c, pid).traps["m_mass_weight_same"]
        r = _answer(c, sid, pid, trap_value).json()
        assert r["correct"] is False
        assert r["trap"]["misconception_id"] == "m_mass_weight_same"
        assert r["trap"]["explanation"]


def test_default_concept_is_weakest_with_templates():
    with _client() as c:
        sid = _new(c)
        assert _make(c, sid).json()["concept_id"] == "friction"  # all tied at 0.3 -> smallest id
        r = c.post(f"/sessions/{sid}/answers",
                   json={"question_id": "q_crate_static", "option_id": "a"})
        assert r.status_code == 200  # friction mastery goes up
        assert _make(c, sid).json()["concept_id"] == "incline"


def test_unknown_session_problem_and_concept():
    with _client() as c:
        assert _make(c, 999).status_code == 404
        sid, other = _new(c), _new(c)
        pid = _make(c, sid, "normal").json()["problem_id"]
        assert _answer(c, sid, 999, 1.0).status_code == 404
        assert _answer(c, other, pid, 1.0).status_code == 404  # someone else's problem
        assert _make(c, sid, "vectors").status_code == 422  # no template for this concept
