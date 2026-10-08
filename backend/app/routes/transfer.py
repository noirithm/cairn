from datetime import datetime, timezone
from random import Random

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..deps import get_content, get_db, get_graph, get_llm
from ..engine.propagation import update_mastery
from ..models import Mastery, Student, TransferProblem
from ..schemas import (HintOut, TransferAnswerIn, TransferIn, TransferOut, TransferResultOut,
                       TrapOut)
from ..transfer.generate import build_problem, generate
from ..transfer.phrase import phrase
from ..transfer.templates import TEMPLATES, fmt, templates_for

router = APIRouter()
REL_TOLERANCE = 0.01  # 1% relative tolerance on numeric answers


def _close(value: float, target: float) -> bool:
    return abs(value - target) <= max(REL_TOLERANCE * abs(target), 1e-6)


def _require_student(db: Session, session_id: int) -> None:
    if db.get(Student, session_id) is None:
        raise HTTPException(status_code=404, detail="unknown session")


def _problem_row(db: Session, session_id: int, problem_id: int) -> TransferProblem:
    row = db.get(TransferProblem, problem_id)
    if row is None or row.student_id != session_id:
        raise HTTPException(status_code=404, detail="unknown problem")
    return row


def _mastery_rows(db: Session, session_id: int):
    return db.exec(select(Mastery).where(Mastery.student_id == session_id)).all()


@router.post("/sessions/{session_id}/transfer", response_model=TransferOut)
def create_transfer(session_id: int, body: TransferIn | None = None,
                    db: Session = Depends(get_db), llm=Depends(get_llm)):
    _require_student(db, session_id)
    mastery = {r.concept_id: r.p_known for r in _mastery_rows(db, session_id)}
    available = sorted({t.concept_id for t in TEMPLATES})
    concept_id = body.concept_id if body else None
    if concept_id is None:
        concept_id = min(available, key=lambda c: mastery[c])  # weakest; ties -> smallest id
    elif concept_id not in available:
        raise HTTPException(status_code=422, detail="no transfer problems for this concept")

    n_prev = len(db.exec(select(TransferProblem)
                         .where(TransferProblem.student_id == session_id)).all())
    seed_base = f"{session_id}:{n_prev}"
    template = Random(seed_base).choice(templates_for(concept_id))
    problem = generate(template, seed_base)  # verified with SymPy before it exists
    text, source = phrase(problem.stem, llm)

    row = TransferProblem(student_id=session_id, template_id=problem.template_id,
                          concept_id=concept_id, seed=problem.seed, stem=text, unit=problem.unit)
    db.add(row)
    db.commit()
    db.refresh(row)
    return TransferOut(problem_id=row.id, concept_id=concept_id, text=text, unit=problem.unit,
                       hints_available=len(problem.hints), phrased_by=source)


@router.post("/sessions/{session_id}/transfer/{problem_id}/hint", response_model=HintOut)
def next_hint(session_id: int, problem_id: int, db: Session = Depends(get_db)):
    _require_student(db, session_id)
    row = _problem_row(db, session_id, problem_id)
    problem = build_problem(row.template_id, row.seed)
    if row.hints_used >= len(problem.hints):
        raise HTTPException(status_code=409, detail="no more hints")
    text = problem.hints[row.hints_used]
    row.hints_used += 1
    db.add(row)
    db.commit()
    return HintOut(level=row.hints_used, text=text, remaining=len(problem.hints) - row.hints_used)


@router.post("/sessions/{session_id}/transfer/{problem_id}/answer",
             response_model=TransferResultOut)
def answer(session_id: int, problem_id: int, body: TransferAnswerIn,
           db: Session = Depends(get_db), graph=Depends(get_graph), content=Depends(get_content)):
    _require_student(db, session_id)
    row = _problem_row(db, session_id, problem_id)
    problem = build_problem(row.template_id, row.seed)
    correct = _close(body.value, problem.answer_float)

    rows = _mastery_rows(db, session_id)
    before = {r.concept_id: r.p_known for r in rows}
    after = before
    if not row.counted:  # mastery moves once per problem, on the first submission
        if not (correct and row.hints_used >= 2):  # heavy hint support counts as no evidence
            after = update_mastery(graph, before, row.concept_id, correct)
            for r in rows:
                if after[r.concept_id] != r.p_known:
                    r.p_known = after[r.concept_id]
                    r.updated_at = datetime.now(timezone.utc)
                    db.add(r)
        row.counted = True
    row.submissions += 1
    row.solved = row.solved or correct
    db.add(row)
    db.commit()

    trap = None
    if not correct:
        for mid, value in problem.traps.items():
            if _close(body.value, value):
                m = content.misconceptions[mid]
                trap = TrapOut(misconception_id=mid, name=m.name, explanation=m.explanation)
                break
    solution = (f"{problem.hints[1]} Answer: {fmt(problem.answer)} {problem.unit}."
                if correct else None)
    return TransferResultOut(correct=correct, mastery_updated=after is not before,
                             hints_used=row.hints_used, mastery=after, solution=solution, trap=trap)
