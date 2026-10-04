from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..deps import get_db, get_graph
from ..models import Mastery, Student
from ..schemas import GraphOut, NodeOut, SessionOut

router = APIRouter()

P_INIT = 0.3  # placeholder prior; Day 2 replaces it with per-concept BKT P(L0)


@router.post("/sessions", response_model=SessionOut)
def create_session(db: Session = Depends(get_db), graph=Depends(get_graph)):
    student = Student()
    db.add(student)
    db.commit()
    db.refresh(student)
    db.add_all(
        Mastery(student_id=student.id, concept_id=cid, p_known=P_INIT)
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
