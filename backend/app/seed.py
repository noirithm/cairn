"""Seed simulated students (idempotent). CLI: uv run python -m app.seed [--n 30] [--seed 7] [--reset]"""
from random import Random

from sqlmodel import Session, col, select

from .models import Attempt, Mastery, Student
from .simulation import check_prevalence, simulate_student


def seed_simulated_students(engine, graph, content, n: int = 30, seed: int = 7,
                            reset: bool = False) -> dict[int, list[str]]:
    """Create simulated students once. Returns {student_id: hidden misconceptions},
    or {} if they already exist (unless reset=True, which rebuilds them)."""
    check_prevalence(content)
    with Session(engine) as db:
        existing = db.exec(select(Student).where(col(Student.is_simulated).is_(True))).all()
        if existing and not reset:
            return {}
        for s in existing:
            for model in (Attempt, Mastery):
                for row in db.exec(select(model).where(model.student_id == s.id)).all():
                    db.delete(row)
            db.delete(s)
        db.commit()

        rng = Random(seed)
        hidden: dict[int, list[str]] = {}
        for i in range(n):
            result = simulate_student(graph, content, rng)
            student = Student(name=f"Sim {i + 1:02d}", is_simulated=True)
            db.add(student)
            db.commit()
            db.refresh(student)
            db.add_all(
                Attempt(student_id=student.id, concept_id=cid, question_id=qid, answer=oid,
                        correct=ok)
                for qid, cid, oid, ok in result.attempts
            )
            db.add_all(
                Mastery(student_id=student.id, concept_id=cid, p_known=p)
                for cid, p in result.mastery.items()
            )
            db.commit()
            hidden[student.id] = result.held
        return hidden


def main() -> None:
    import argparse

    from .content import Content
    from .database import init_db, make_engine
    from .graph import ConceptGraph
    from .main import DATA_DIR  # imported here to avoid a circular import

    ap = argparse.ArgumentParser(description="Seed simulated students for the teacher view")
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--reset", action="store_true")
    args = ap.parse_args()

    engine = make_engine()
    init_db(engine)
    graph = ConceptGraph.load(DATA_DIR / "graph.json")
    content = Content.load(DATA_DIR, set(graph.g.nodes))
    created = seed_simulated_students(engine, graph, content, args.n, args.seed, args.reset)
    print(f"created {len(created)} simulated students" if created
          else "simulated students already exist (use --reset to rebuild)")


if __name__ == "__main__":
    main()
