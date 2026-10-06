from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..deps import get_db, get_graph
from ..engine.bkt import params_for
from ..engine.propagation import update_mastery
from ..models import Attempt, Mastery, Student
from ..schemas import AnswerIn, GraphOut, MasteryOut, NodeOut, SessionOut

router = APIRouter()


@router.post("/sessions", response_model=SessionOut)
def create_session(db: Session = Depends(get_db), graph=Depends(get_graph)):
    student = Student()
    db.add(student)
    db.commit()
    db.refresh(student)
    db.add_all(
        Mastery(student_id=student.id, concept_id=cid, p_known=params_for(cid).p_init)
        for cid in graph.topo_order()
    )
    db.commit()
    return SessionOut(session_id=student.id)


@router.get("/sessions/{session_id}/graph", response_model=GraphOut)
def session_graph(session_id: int, db: Session = Depends(get_db), graph=Depends(get_graph)):
    """Everything the React Flow viewer needs: nodes with mastery, plus edges."""
    if db.get(Student, session_id) is None:
        raise HTTPException(status_code=404, detail="unknown session")
    rows = db.exec(select(Mastery).where(Mastery.student_id == session_id)).all()
    mastery = {r.concept_id: r.p_known for r in rows}
    nodes = [
        NodeOut(id=c.id, name=c.name, section=c.section, p_known=mastery[c.id])
        for c in graph.data.concepts
    ]
    return GraphOut(unit=graph.data.unit, nodes=nodes, edges=graph.data.edges)


@router.post("/sessions/{session_id}/answers", response_model=MasteryOut)
def submit_answer(session_id: int, body: AnswerIn,
                  db: Session = Depends(get_db), graph=Depends(get_graph)):
    if db.get(Student, session_id) is None:
        raise HTTPException(status_code=404, detail="unknown session")
    if body.concept_id not in graph.g:
        raise HTTPException(status_code=422, detail="unknown concept")
    rows = db.exec(select(Mastery).where(Mastery.student_id == session_id)).all()
    before = {r.concept_id: r.p_known for r in rows}
    after = update_mastery(graph, before, body.concept_id, body.correct)
    for r in rows:
        if after[r.concept_id] != r.p_known:
            r.p_known = after[r.concept_id]
            r.updated_at = datetime.now(timezone.utc)
            db.add(r)
    db.add(Attempt(student_id=session_id, concept_id=body.concept_id,
                   question_id=body.question_id, answer=body.answer, correct=body.correct))
    db.commit()
    return MasteryOut(mastery=after)
