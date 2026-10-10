"""Belief over hypotheses: CORRECT (no misconception) plus each taxonomy misconception.

Pure functions, like update_mastery: the selector calls them for "what if" questions.
"""
from math import log2

from ..content import CORRECT

P_CORRECT_PRIOR = 0.4
DIAGNOSIS_THRESHOLD = 0.5  # a misconception counts as diagnosed once its posterior passes this


def initial_belief(misconception_ids) -> dict[str, float]:
    ids = list(misconception_ids)
    belief = {CORRECT: P_CORRECT_PRIOR}
    for m in ids:
        belief[m] = (1 - P_CORRECT_PRIOR) / len(ids)
    return belief


def entropy(belief: dict[str, float]) -> float:
    """Shannon entropy in bits: how unsure we are which hypothesis is true."""
    return -sum(p * log2(p) for p in belief.values() if p > 0)


def update_belief(belief: dict[str, float], question, option_id: str) -> dict[str, float]:
    """Bayes: P(h | answer) is proportional to P(answer | h) * P(h). Returns a new dict."""
    unnorm = {h: p * question.p_option_given(h, option_id) for h, p in belief.items()}
    z = sum(unnorm.values())
    return {h: v / z for h, v in unnorm.items()}


def replay_belief(content, attempts) -> dict[str, float]:
    """Rebuild the belief from the append-only attempt log (no extra table needed)."""
    belief = initial_belief(content.misconceptions)
    for a in attempts:
        q = content.questions.get(a.question_id)
        if q is None:  # row from an older bank; ignore
            continue
        belief = update_belief(belief, q, a.answer)
    return belief


def diagnosed_id(belief: dict[str, float]) -> str | None:
    """Id of the diagnosed misconception, or None (top hypothesis is CORRECT or under the threshold)."""
    top = max(belief, key=belief.get)
    return top if top != CORRECT and belief[top] >= DIAGNOSIS_THRESHOLD else None
