from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from ..deps import get_content, get_db, get_graph
from ..models import Attempt, Mastery, Student
from ..schemas import HeatmapOut
from ..teacher import build_heatmap

router = APIRouter()


@router.get("/teacher/heatmap", response_model=HeatmapOut)
def heatmap(db: Session = Depends(get_db), graph=Depends(get_graph), content=Depends(get_content)):
    """Class-wide view. Real and simulated students are included once they have answered."""
    students = db.exec(select(Student)).all()
    attempts_by = defaultdict(list)
    for a in db.exec(select(Attempt).order_by(Attempt.id)).all():
        attempts_by[a.student_id].append(a)
    mastery_by = defaultdict(dict)
    for m in db.exec(select(Mastery)).all():
        mastery_by[m.student_id][m.concept_id] = m.p_known
    return HeatmapOut(**build_heatmap(students, attempts_by, mastery_by, content, graph))
