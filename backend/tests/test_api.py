from fastapi.testclient import TestClient

from app.engine.bkt import params_for
from app.main import create_app


def _mastery(client, sid):
    nodes = client.get(f"/sessions/{sid}/graph").json()["nodes"]
    return {n["id"]: n["p_known"] for n in nodes}


def test_session_graph_flow():
    # `with` is required so the lifespan (DB + graph load) runs.
    with TestClient(create_app("sqlite://")) as client:
        assert client.get("/health").json() == {"status": "ok"}
        sid = client.post("/sessions").json()["session_id"]
        body = client.get(f"/sessions/{sid}/graph").json()
        assert len(body["nodes"]) == 14
        assert len(body["edges"]) == 25
        for n in body["nodes"]:
            assert abs(n["p_known"] - params_for(n["id"]).p_init) < 1e-9


def test_unknown_session_404():
    with TestClient(create_app("sqlite://")) as client:
        assert client.get("/sessions/999/graph").status_code == 404
        r = client.post("/sessions/999/answers", json={"concept_id": "newton_2", "correct": True})
        assert r.status_code == 404


def test_unknown_concept_422():
    with TestClient(create_app("sqlite://")) as client:
        sid = client.post("/sessions").json()["session_id"]
        r = client.post(f"/sessions/{sid}/answers", json={"concept_id": "nope", "correct": True})
        assert r.status_code == 422


def test_wrong_answer_lowers_prereqs_not_descendants():
    with TestClient(create_app("sqlite://")) as client:
        sid = client.post("/sessions").json()["session_id"]
        before = _mastery(client, sid)
        r = client.post(f"/sessions/{sid}/answers", json={"concept_id": "newton_2", "correct": False})
        assert r.status_code == 200
        after = _mastery(client, sid)  # persisted, not just returned
        for c in ("newton_2", "net_force", "kinematics", "mass_inertia", "force", "vectors"):
            assert after[c] < before[c]
        for c in ("weight", "friction", "incline", "newton_1"):
            assert after[c] == before[c]


def test_correct_answer_raises_only_that_concept():
    with TestClient(create_app("sqlite://")) as client:
        sid = client.post("/sessions").json()["session_id"]
        before = _mastery(client, sid)
        client.post(f"/sessions/{sid}/answers", json={"concept_id": "newton_2", "correct": True})
        after = _mastery(client, sid)
        assert after["newton_2"] > before["newton_2"]
        assert all(after[c] == before[c] for c in before if c != "newton_2")
