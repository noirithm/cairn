from fastapi.testclient import TestClient

from app.main import create_app


def test_session_graph_flow():
    # `with` is required so the lifespan (DB + graph load) runs.
    with TestClient(create_app("sqlite://")) as client:
        assert client.get("/health").json() == {"status": "ok"}
        sid = client.post("/sessions").json()["session_id"]
        body = client.get(f"/sessions/{sid}/graph").json()
        assert len(body["nodes"]) == 14
        assert all(n["p_known"] == 0.3 for n in body["nodes"])
        assert len(body["edges"]) == 25


def test_unknown_session_404():
    with TestClient(create_app("sqlite://")) as client:
        assert client.get("/sessions/999/graph").status_code == 404
