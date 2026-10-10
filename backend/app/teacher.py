"""Class-level aggregation for the teacher view. Pure: no database, no FastAPI."""
from .engine.diagnosis import diagnosed_id, replay_belief


def _mean(xs) -> float:
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


def build_heatmap(students, attempts_by, mastery_by, content, graph) -> dict:
    """Students x misconceptions matrix of posterior probabilities, plus class-level summaries.

    Only students with at least one attempt count. Beliefs are replayed from the attempt log,
    exactly as for a live student.
    """
    cols = list(content.misconceptions)
    index = {m: i for i, m in enumerate(cols)}
    rows = []
    for s in students:
        attempts = attempts_by.get(s.id)
        if not attempts:
            continue
        belief = replay_belief(content, attempts)
        rows.append((s, belief, diagnosed_id(belief)))
    # Group students who share a diagnosis so the heatmap shows blocks.
    rows.sort(key=lambda r: (r[2] is None, index.get(r[2], 0), r[0].id))

    stats = [
        {
            "misconception_id": m,
            "name": content.misconceptions[m].name,
            "concept_id": content.misconceptions[m].concept_id,
            "mean_p": _mean(b[m] for _, b, _ in rows),
            "diagnosed_count": sum(1 for _, _, d in rows if d == m),
        }
        for m in cols
    ]
    stats.sort(key=lambda s: (-s["diagnosed_count"], -s["mean_p"], s["misconception_id"]))

    concepts = [
        {
            "concept_id": c.id,
            "name": c.name,
            "mean_p_known": _mean(mastery_by[s.id][c.id] for s, _, _ in rows
                                  if c.id in mastery_by.get(s.id, {})),
        }
        for c in graph.data.concepts
    ]
    return {
        "n_students": len(rows),
        "misconceptions": [{"id": m, "name": content.misconceptions[m].name,
                            "concept_id": content.misconceptions[m].concept_id} for m in cols],
        "students": [{"id": s.id, "name": s.name, "is_simulated": s.is_simulated,
                      "answered": len(attempts_by[s.id]), "diagnosed": d} for s, _, d in rows],
        "cells": [[b[m] for m in cols] for _, b, _ in rows],
        "stats": stats,
        "concepts": concepts,
    }
