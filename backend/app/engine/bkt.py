"""Bayesian Knowledge Tracing (Corbett & Anderson, 1995), hand-written.

Hidden state per concept: does the student know it? We track P(known).
  p_init    P(L0)  knew it before any practice
  p_transit P(T)   learns it after each practice opportunity
  p_slip    P(S)   knows it but answers wrong anyway
  p_guess   P(G)   doesn't know it but answers right anyway
"""
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class BKTParams:
    p_init: float = 0.3
    p_transit: float = 0.15
    p_slip: float = 0.1
    p_guess: float = 0.2

    def __post_init__(self):
        for name, value in vars(self).items():
            if not 0 < value < 1:
                raise ValueError(f"{name} must be in (0, 1), got {value}")
        if self.p_slip + self.p_guess >= 1:
            raise ValueError("p_slip + p_guess must be < 1")


def bayes_update(p: float, like_if_known: float, like_if_unknown: float) -> float:
    """P(known | observation), given the prior and the observation's likelihood in each state."""
    num = p * like_if_known
    return num / (num + (1 - p) * like_if_unknown)


def bkt_update(p: float, correct: bool, params: BKTParams) -> float:
    # Step 1: evidence from the answer.
    if correct:
        posterior = bayes_update(p, 1 - params.p_slip, params.p_guess)
    else:
        posterior = bayes_update(p, params.p_slip, 1 - params.p_guess)
    # Step 2: the student may have learned from this opportunity.
    return posterior + (1 - posterior) * params.p_transit


DEFAULT_PARAMS = BKTParams()

# Foundational concepts are more likely known before the unit starts.
_P_INIT_OVERRIDES = {"vectors": 0.5, "kinematics": 0.5, "force": 0.5, "mass_inertia": 0.4}


def params_for(concept_id: str) -> BKTParams:
    if concept_id in _P_INIT_OVERRIDES:
        return replace(DEFAULT_PARAMS, p_init=_P_INIT_OVERRIDES[concept_id])
    return DEFAULT_PARAMS
