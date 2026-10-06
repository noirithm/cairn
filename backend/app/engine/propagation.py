"""Prerequisite propagation: a wrong answer is also (weaker) evidence that prerequisites are shaky."""
from ..graph import ConceptGraph
from .bkt import bayes_update, bkt_update, params_for

# Fraction of a path's strength that becomes evidence. Hand-set, not fitted.
PROPAGATION_DAMPING = 0.5


def evidence_strengths(graph: ConceptGraph, concept_id: str) -> dict[str, float]:
    """Weight in (0, 1] per ancestor: product of edge strengths on the strongest path."""
    w = {concept_id: 1.0}
    # Reverse topological order: every dependent of a node is processed before the node itself.
    for node in reversed(graph.topo_order()):
        if node not in w:
            continue
        for prereq in graph.g.predecessors(node):
            via = w[node] * graph.g[prereq][node]["strength"]
            w[prereq] = max(w.get(prereq, 0.0), via)
    return w


def update_mastery(graph: ConceptGraph, mastery: dict[str, float],
                   concept_id: str, correct: bool) -> dict[str, float]:
    """Pure function: returns a new mastery dict and never mutates the input."""
    params = params_for(concept_id)
    new = dict(mastery)
    new[concept_id] = bkt_update(mastery[concept_id], correct, params)
    if correct:
        return new
    for ancestor, w in evidence_strengths(graph, concept_id).items():
        if ancestor == concept_id:
            continue
        s = w * PROPAGATION_DAMPING
        # Interpolate from "uninformative" (0.5 / 0.5) toward the full wrong-answer likelihoods.
        like_known = 0.5 + s * (params.p_slip - 0.5)
        like_unknown = 0.5 + s * ((1 - params.p_guess) - 0.5)
        new[ancestor] = bayes_update(mastery[ancestor], like_known, like_unknown)
    return new
