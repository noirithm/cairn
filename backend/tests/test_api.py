from fastapi.testclient import TestClient

from app.content import Content
from app.engine.bkt import params_for
from app.graph import ConceptGraph
from app.main import DATA_DIR, create_app

GRAPH = ConceptGraph.load(DATA_DIR / "graph.json")
CONTENT = Content.load(DATA_DIR, set(GRAPH.g.nodes))


def _new(client):
    return client.post("/sessions").json()["session_id"]


def _mastery(client, sid):
    nodes = client.get(f"/sessions/{sid}/graph").json()["nodes"]
    return {n["id"]: n["p_known"] for n in nodes}


def _answer(client, sid, qid, oid):
    return client.post(f"/sessions/{sid}/answers", json={"question_id": qid, "option_id": oid})


def _correct_option(qid):
    return next(o.id for o in CONTENT.questions[qid].options if o.correct)


def test_session_graph_flow():
    # `with` is required so the lifespan (DB + graph + content load) runs.
    with TestClient(create_app("sqlite://")) as client:
        assert client.get("/health").json() == {"status": "ok"}
        sid = _new(client)
        body = client.get(f"/sessions/{sid}/graph").json()
        assert len(body["nodes"]) == 14 and len(body["edges"]) == 25
        for n in body["nodes"]:
            assert abs(n["p_known"] - params_for(n["id"]).p_init) < 1e-9


def test_unknown_session_404():
    with TestClient(create_app("sqlite://")) as client:
        assert client.get("/sessions/999/graph").status_code == 404
        assert client.get("/sessions/999/next-question").status_code == 404
        assert client.get("/sessions/999/diagnosis").status_code == 404
        assert _answer(client, 999, "q_puck_ice", "a").status_code == 404


def test_next_question_hides_the_answer():
    with TestClient(create_app("sqlite://")) as client:
        sid = _new(client)
        body = client.get(f"/sessions/{sid}/next-question").json()
        q = body["question"]
        assert q["id"] in CONTENT.questions
        assert all(set(o) == {"id", "text"} for o in q["options"])
        assert body["expected_gain"] > 0


def test_wrong_answers_update_mastery_and_diagnose():
    with TestClient(create_app("sqlite://")) as client:
        sid = _new(client)
        before = _mastery(client, sid)
        r = _answer(client, sid, "q_puck_ice", "b")
        assert r.status_code == 200
        body = r.json()
        assert body["correct"] is False and body["explanation"]
        after = _mastery(client, sid)
        for c in ("newton_1", "mass_inertia", "net_force", "force", "vectors"):
            assert after[c] < before[c]
        for c in ("newton_2", "weight", "friction"):
            assert after[c] == before[c]
        assert body["diagnosed"] is None  # one wrong answer is not enough
        probs = [e["p"] for e in body["diagnosis"]]
        assert abs(sum(probs) - 1) < 1e-9 and probs == sorted(probs, reverse=True)

        r2 = _answer(client, sid, "q_skydiver_terminal", "b").json()
        assert r2["diagnosed"]["id"] == "m_motion_needs_force"
        assert r2["diagnosed"]["explanation"]
        d = client.get(f"/sessions/{sid}/diagnosis").json()
        assert d["diagnosis"][0]["id"] == "m_motion_needs_force"


def test_duplicate_answer_409():
    with TestClient(create_app("sqlite://")) as client:
        sid = _new(client)
        assert _answer(client, sid, "q_puck_ice", "a").status_code == 200
        assert _answer(client, sid, "q_puck_ice", "a").status_code == 409


def test_unknown_question_and_option():
    with TestClient(create_app("sqlite://")) as client:
        sid = _new(client)
        assert _answer(client, sid, "q_nope", "a").status_code == 404
        assert _answer(client, sid, "q_puck_ice", "z").status_code == 422


def test_full_quiz_follows_selector_to_the_end():
    with TestClient(create_app("sqlite://")) as client:
        sid = _new(client)
        seen = []
        for _ in range(len(CONTENT.questions)):
            q = client.get(f"/sessions/{sid}/next-question").json()["question"]
            assert q is not None and q["id"] not in seen
            seen.append(q["id"])
            assert _answer(client, sid, q["id"], _correct_option(q["id"])).status_code == 200
        assert client.get(f"/sessions/{sid}/next-question").json()["question"] is None
        d = client.get(f"/sessions/{sid}/diagnosis").json()
        assert d["diagnosis"][0]["id"] == "correct"
