from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..content import CORRECT
from ..deps import get_content, get_db, get_graph
from ..engine.diagnosis import DIAGNOSIS_THRESHOLD, entropy, replay_belief, update_belief
from ..engine.propagation import update_mastery
from ..engine.selector import expected_information_gain, pick_next
from ..models import Attempt, Mastery, Student
from ..schemas import (AnswerIn, AnswerOut, DiagnosisEntry, DiagnosisOut, NextQuestionOut,
                       OptionOut, QuestionOut)

router = APIRouter()


def _require_student(db: Session, session_id: int) -> None:
    if db.get(Student, session_id) is None:
        raise HTTPException(status_code=404, detail="unknown session")


def _attempts(db: Session, session_id: int):
    stmt = select(Attempt).where(Attempt.student_id == session_id).order_by(Attempt.id)
    return db.exec(stmt).all()


def _entries(content, belief: dict[str, float]) -> list[DiagnosisEntry]:
    entries = [
        DiagnosisEntry(
            id=h, name=content.hypothesis_name(h), p=p,
            explanation=None if h == CORRECT else content.misconceptions[h].explanation,
        )
        for h, p in belief.items()
    ]
    return sorted(entries, key=lambda e: e.p, reverse=True)


@router.get("/sessions/{session_id}/next-question", response_model=NextQuestionOut)
def next_question(session_id: int, db: Session = Depends(get_db), content=Depends(get_content)):
    _require_student(db, session_id)
    attempts = _attempts(db, session_id)
    belief = replay_belief(content, attempts)
    asked = {a.question_id for a in attempts}
    q = pick_next(belief, list(content.questions.values()), asked)
    if q is None:
        return NextQuestionOut(question=None)
    return NextQuestionOut(
        question=QuestionOut(
            id=q.id, concept_id=q.concept_id, prompt=q.prompt,
            options=[OptionOut(id=o.id, text=o.text) for o in q.options],
        ),
        expected_gain=expected_information_gain(belief, q),
    )


@router.post("/sessions/{session_id}/answers", response_model=AnswerOut)
def submit_answer(session_id: int, body: AnswerIn, db: Session = Depends(get_db),
                  graph=Depends(get_graph), content=Depends(get_content)):
    _require_student(db, session_id)
    q = content.questions.get(body.question_id)
    if q is None:
        raise HTTPException(status_code=404, detail="unknown question")
    option = next((o for o in q.options if o.id == body.option_id), None)
    if option is None:
        raise HTTPException(status_code=422, detail="unknown option")
    attempts = _attempts(db, session_id)
    if any(a.question_id == q.id for a in attempts):
        raise HTTPException(status_code=409, detail="question already answered")

    # Grading is server-side: the client only says which option was picked.
    rows = db.exec(select(Mastery).where(Mastery.student_id == session_id)).all()
    before = {r.concept_id: r.p_known for r in rows}
    after = update_mastery(graph, before, q.concept_id, option.correct)
    for r in rows:
        if after[r.concept_id] != r.p_known:
            r.p_known = after[r.concept_id]
            r.updated_at = datetime.now(timezone.utc)
            db.add(r)
    db.add(Attempt(student_id=session_id, concept_id=q.concept_id, question_id=q.id,
                   answer=option.id, correct=option.correct))
    db.commit()

    belief = update_belief(replay_belief(content, attempts), q, option.id)
    entries = _entries(content, belief)
    top = entries[0]
    diagnosed = top if top.id != CORRECT and top.p >= DIAGNOSIS_THRESHOLD else None
    return AnswerOut(correct=option.correct, explanation=q.explanation, mastery=after,
                     diagnosis=entries, diagnosed=diagnosed)


@router.get("/sessions/{session_id}/diagnosis", response_model=DiagnosisOut)
def diagnosis(session_id: int, db: Session = Depends(get_db), content=Depends(get_content)):
    _require_student(db, session_id)
    belief = replay_belief(content, _attempts(db, session_id))
    return DiagnosisOut(diagnosis=_entries(content, belief), entropy=entropy(belief))
