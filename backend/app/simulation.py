"""Simulated students for the teacher view.

They answer through the SAME engine as real students (adaptive selector, BKT, propagation),
so the heatmap exercises the real pipeline. Caveat: their answers are drawn from the same
likelihood tables the engine assumes, so recovering their hidden misconceptions shows the
pipeline works, not that those tables match real students.
"""
from dataclasses import dataclass
from random import Random

from .content import CORRECT
from .engine.bkt import params_for
from .engine.diagnosis import initial_belief, update_belief
from .engine.propagation import update_mastery
from .engine.selector import pick_next

# Chance a simulated student holds each misconception. A hand-set classroom prior, not data.
PREVALENCE = {
    "m_motion_needs_force": 0.45,
    "m_normal_equals_weight": 0.35,
    "m_bigger_pushes_harder": 0.30,
    "m_mass_weight_same": 0.25,
    "m_force_prop_velocity": 0.20,
    "m_friction_always_mu_n": 0.20,
    "m_third_law_same_object": 0.12,
}
MAX_HELD = 2


@dataclass
class SimResult:
    held: list[str]  # hidden truth; never stored in the database
    attempts: list[tuple[str, str, str, bool]]  # (question_id, concept_id, option_id, correct)
    mastery: dict[str, float]


def check_prevalence(content) -> None:
    unknown = set(PREVALENCE) - set(content.misconceptions)
    if unknown:
        raise ValueError(f"PREVALENCE names unknown misconceptions: {sorted(unknown)}")


def sample_held(rng: Random) -> list[str]:
    return [m for m, p in PREVALENCE.items() if rng.random() < p][:MAX_HELD]


def sample_option(question, held: list[str], rng: Random) -> str:
    """Answer like the first held misconception that this question tests, else like a correct student."""
    hypothesis = next((h for h in held if h in question.likelihoods), CORRECT)
    ids = [o.id for o in question.options]
    weights = [question.p_option_given(hypothesis, i) for i in ids]
    return rng.choices(ids, weights=weights)[0]


def simulate_student(graph, content, rng: Random) -> SimResult:
    held = sample_held(rng)
    mastery = {cid: params_for(cid).p_init for cid in graph.topo_order()}
    belief = initial_belief(content.misconceptions)
    asked: set[str] = set()
    attempts: list[tuple[str, str, str, bool]] = []
    for _ in range(rng.randint(5, 8)):
        q = pick_next(belief, list(content.questions.values()), asked)
        if q is None:
            break
        option_id = sample_option(q, held, rng)
        correct = next(o.correct for o in q.options if o.id == option_id)
        mastery = update_mastery(graph, mastery, q.concept_id, correct)
        belief = update_belief(belief, q, option_id)
        asked.add(q.id)
        attempts.append((q.id, q.concept_id, option_id, correct))
    return SimResult(held, attempts, mastery)
