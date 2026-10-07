"""Pick the next question by expected information gain (EIG), in bits.

EIG(q) = H(belief) - sum over options a of P(a) * H(belief after seeing a)
"""
from .diagnosis import entropy, update_belief


def expected_information_gain(belief: dict[str, float], question) -> float:
    expected_after = 0.0
    for opt in question.options:
        p_answer = sum(p * question.p_option_given(h, opt.id) for h, p in belief.items())
        expected_after += p_answer * entropy(update_belief(belief, question, opt.id))
    return entropy(belief) - expected_after


def pick_next(belief: dict[str, float], questions, asked: set[str]):
    """Highest-EIG unasked question; ties go to the smallest id. None when the bank is used up."""
    candidates = sorted((q for q in questions if q.id not in asked), key=lambda q: q.id)
    if not candidates:
        return None
    scored = [(expected_information_gain(belief, q), q) for q in candidates]
    return max(scored, key=lambda t: t[0])[1]  # max keeps the first of equal scores
