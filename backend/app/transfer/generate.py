"""Generate a transfer problem and verify its answer with SymPy before anyone sees it."""
from dataclasses import dataclass
from random import Random

import sympy

from .templates import TEMPLATES_BY_ID, Template


@dataclass(frozen=True)
class Problem:
    template_id: str
    concept_id: str
    unit: str
    seed: str
    stem: str
    answer: sympy.Expr
    answer_float: float
    hints: list[str]
    traps: dict[str, float]  # misconception id -> the wrong value that signals it


def solve(t: Template, p: dict):
    eqs, unknowns, target = t.equations(p)
    sols = sympy.solve(eqs, unknowns, dict=True)
    if len(sols) != 1 or target not in sols[0]:
        raise ValueError(f"{t.id}: expected exactly one solution, got {sols}")
    return eqs, sols[0], target


def verify(t: Template, p: dict, answer) -> bool:
    """Three independent checks on a candidate answer."""
    eqs, sol, target = solve(t, p)
    trial = {**sol, target: answer}
    # 1. Substitute back: every governing equation must hold exactly.
    for e in eqs:
        if sympy.simplify(e.lhs.subs(trial) - e.rhs.subs(trial)) != 0:
            return False
    # 2. Agree with a separate plain-Python derivation.
    cf = t.closed_form(p)
    if abs(float(answer) - cf) > 1e-9 * max(1.0, abs(cf)):
        return False
    # 3. Physically sensible (positive normal force, friction below its limit, ...).
    return t.check(p, trial)


def build_problem(template_id: str, seed: str) -> Problem:
    """Deterministic: the same (template, seed) always rebuilds the same verified problem."""
    t = TEMPLATES_BY_ID[template_id]
    p = t.sample(Random(seed))
    _, sol, target = solve(t, p)
    answer = sol[target]
    if not verify(t, p, answer):
        raise ValueError(f"{t.id}: answer failed verification for seed {seed}")
    return Problem(
        template_id=t.id, concept_id=t.concept_id, unit=t.unit, seed=seed, stem=t.stem(p),
        answer=answer, answer_float=float(answer), hints=t.hints(p),
        traps={k: float(v) for k, v in t.traps(p).items()},
    )


def generate(t: Template, seed_base: str, tries: int = 20) -> Problem:
    """Try seeds seed_base:0, seed_base:1, ... until one verifies. Never returns an unverified problem."""
    last = None
    for i in range(tries):
        try:
            return build_problem(t.id, f"{seed_base}:{i}")
        except ValueError as e:
            last = e
    raise RuntimeError(f"could not generate a verified {t.id} problem: {last}")
