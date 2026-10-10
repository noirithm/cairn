from fastapi.testclient import TestClient

from app.main import create_app
from app.seed import seed_simulated_students


def _client(seed=True):
    return TestClient(create_app("sqlite://", llm_factory=lambda: None, seed_demo=seed))


def test_empty_class_without_seeding():
    with _client(seed=False) as c:
        h = c.get("/teacher/heatmap").json()
        assert h["n_students"] == 0 and h["cells"] == [] and h["students"] == []
        assert len(h["stats"]) == 7 and len(h["concepts"]) == 14


def test_heatmap_with_seeded_students():
    with _client() as c:
        h = c.get("/teacher/heatmap").json()
        assert h["n_students"] == 30
        assert len(h["cells"]) == 30
        assert all(len(row) == len(h["misconceptions"]) for row in h["cells"])
        assert all(0 <= v <= 1 for row in h["cells"] for v in row)
        assert all(s["is_simulated"] for s in h["students"])
        counts = [s["diagnosed_count"] for s in h["stats"]]
        assert counts == sorted(counts, reverse=True) and counts[0] >= 5
        flags = [s["diagnosed"] is None for s in h["students"]]
        assert flags == sorted(flags)  # diagnosed students come first
        assert all(0 < x["mean_p_known"] < 1 for x in h["concepts"])


def test_real_student_joins_the_class_after_answering():
    with _client() as c:
        sid = c.post("/sessions").json()["session_id"]
        assert c.get("/teacher/heatmap").json()["n_students"] == 30  # no attempts yet
        r = c.post(f"/sessions/{sid}/answers", json={"question_id": "q_puck_ice", "option_id": "b"})
        assert r.status_code == 200
        h = c.get("/teacher/heatmap").json()
        assert h["n_students"] == 31
        assert [s["is_simulated"] for s in h["students"]].count(False) == 1


def test_seeding_is_idempotent_and_reset_rebuilds():
    with _client() as c:
        st = c.app.state
        assert seed_simulated_students(st.engine, st.graph, st.content) == {}
        assert c.get("/teacher/heatmap").json()["n_students"] == 30
        again = seed_simulated_students(st.engine, st.graph, st.content, n=10, reset=True)
        assert len(again) == 10
        assert c.get("/teacher/heatmap").json()["n_students"] == 10
