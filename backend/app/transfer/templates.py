"""Parametric transfer-problem templates. Each template carries its own physics:

  sample(rng)        exact parameters (SymPy numbers)
  stem(p)            the problem text (deterministic; the LLM may only re-word it)
  equations(p)       governing equations in SymPy
  closed_form(p)     an independent plain-Python derivation (floats)
  check(p, sol)      physical sanity (e.g. normal force > 0)
  hints(p)           three-step hint ladder
  traps(p)           wrong answers that signal a taxonomy misconception

The LLM never sees the answer, and never touches any of this.
"""
import math
from dataclasses import dataclass, field
from random import Random
from typing import Any, Callable

from sympy import Eq, Integer, Rational, Symbol, pi, sin

G = Rational(49, 5)  # 9.8 m/s^2, exact so SymPy stays exact


def fmt(x) -> str:
    """Human-friendly number: 5 -> '5', 49/5 -> '9.8'."""
    return f"{float(x):g}"


@dataclass(frozen=True)
class Template:
    id: str
    concept_id: str
    unit: str
    sample: Callable[[Random], dict[str, Any]]
    stem: Callable[[dict], str]
    equations: Callable[[dict], tuple[list, list, Symbol]]
    closed_form: Callable[[dict], float]
    check: Callable[[dict, dict], bool]
    hints: Callable[[dict], list[str]]
    traps: Callable[[dict], dict[str, Any]] = field(default=lambda p: {})


def _ints(r: Random, values) -> Integer:
    return Integer(r.choice(values))


# ---- newton_2: net force -> acceleration ---------------------------------
def _net_sample(r):
    m, f2 = _ints(r, [2, 3, 4, 5, 6, 8]), _ints(r, [10, 15, 20, 25])
    return {"m": m, "F1": f2 + _ints(r, [10, 15, 20, 25, 30]), "F2": f2}


def _net_eq(p):
    a = Symbol("a")
    return [Eq(p["F1"] - p["F2"], p["m"] * a)], [a], a


NET_ACCEL = Template(
    id="t_net_accel", concept_id="newton_2", unit="m/s²",
    sample=_net_sample,
    stem=lambda p: (f"A {fmt(p['m'])} kg sled on frictionless ice is pulled to the right with "
                    f"{fmt(p['F1'])} N and to the left with {fmt(p['F2'])} N. What is its "
                    f"acceleration in m/s², taking right as positive?"),
    equations=_net_eq,
    closed_form=lambda p: (float(p["F1"]) - float(p["F2"])) / float(p["m"]),
    check=lambda p, sol: bool(sol[Symbol("a")] > 0),
    hints=lambda p: [
        "Forces on one object add as vectors, so combine them before using F = ma.",
        "Net force = (force to the right) - (force to the left), and net force = m·a.",
        f"a = ({fmt(p['F1'])} - {fmt(p['F2'])}) / {fmt(p['m'])}",
    ],
)


# ---- weight: W = m g on another world ------------------------------------
PLANETS = [("Mars", Rational(37, 10)), ("the Moon", Rational(8, 5)),
           ("Jupiter", Rational(124, 5)), ("Venus", Rational(89, 10))]


def _weight_sample(r):
    name, g = r.choice(PLANETS)
    return {"m": _ints(r, [45, 50, 55, 60, 65, 70, 75, 80]), "g": g, "planet": name}


WEIGHT = Template(
    id="t_weight", concept_id="weight", unit="N",
    sample=_weight_sample,
    stem=lambda p: (f"A student has a mass of {fmt(p['m'])} kg. What is her weight on {p['planet']}, "
                    f"where g = {fmt(p['g'])} m/s²? Give your answer in newtons."),
    equations=lambda p: ([Eq(Symbol("W"), p["m"] * p["g"])], [Symbol("W")], Symbol("W")),
    closed_form=lambda p: float(p["m"]) * float(p["g"]),
    check=lambda p, sol: bool(sol[Symbol("W")] > 0),
    hints=lambda p: [
        "Weight is the gravitational force on an object, not its mass.",
        "Weight = mass × the local g.",
        f"W = {fmt(p['m'])} × {fmt(p['g'])}",
    ],
    traps=lambda p: {"m_mass_weight_same": p["m"]},
)


# ---- normal: N from a vertical balance -----------------------------------
def _normal_sample(r):
    m, d = _ints(r, [4, 6, 8, 10, 12]), r.choice(["down", "up"])
    P = _ints(r, [10, 15, 20, 25, 30, 40] if d == "down" else [10, 15, 20, 25])
    return {"m": m, "P": P, "dir": d}


def _normal_eq(p):
    N = Symbol("N")
    sign = 1 if p["dir"] == "down" else -1  # push down adds to N, pull up subtracts
    return [Eq(N - sign * p["P"] - p["m"] * G, 0)], [N], N


def _normal_stem(p):
    force = ("You push straight down on it with" if p["dir"] == "down"
             else "A rope pulls straight up on it with")
    tail = "" if p["dir"] == "down" else ", not enough to lift it"
    return (f"A {fmt(p['m'])} kg box rests on a horizontal floor. {force} {fmt(p['P'])} N{tail}. "
            f"Taking g = 9.8 m/s², what is the normal force from the floor, in newtons?")


NORMAL = Template(
    id="t_normal", concept_id="normal", unit="N",
    sample=_normal_sample, stem=_normal_stem, equations=_normal_eq,
    closed_form=lambda p: float(p["m"]) * 9.8 + (1 if p["dir"] == "down" else -1) * float(p["P"]),
    check=lambda p, sol: bool(sol[Symbol("N")] > 0),
    hints=lambda p: [
        "Draw a free-body diagram of the box and mark every force on it.",
        "The box does not accelerate vertically, so the forces up equal the forces down.",
        f"N = {fmt(p['m'])} × 9.8 {'+' if p['dir'] == 'down' else '-'} {fmt(p['P'])}",
    ],
    traps=lambda p: {"m_normal_equals_weight": p["m"] * G},
)


# ---- friction (static): friction matches the push ------------------------
def _static_sample(r):
    m, mu = _ints(r, [10, 15, 20, 25]), r.choice([Rational(2, 5), Rational(1, 2), Rational(3, 5)])
    kmax = int(Rational(4, 5) * mu * m * G / 5)  # keep the push safely below the static limit
    return {"m": m, "mu": mu, "F": Integer(5 * r.randint(2, kmax))}


STATIC = Template(
    id="t_friction_static", concept_id="friction", unit="N",
    sample=_static_sample,
    stem=lambda p: (f"A {fmt(p['m'])} kg crate rests on a horizontal floor. The coefficient of static "
                    f"friction is {fmt(p['mu'])}. You push horizontally with {fmt(p['F'])} N and the "
                    f"crate does not move. Taking g = 9.8 m/s², what is the friction force on the "
                    f"crate, in newtons?"),
    equations=lambda p: ([Eq(Symbol("f") - p["F"], 0)], [Symbol("f")], Symbol("f")),
    closed_form=lambda p: float(p["F"]),
    check=lambda p, sol: bool(0 < sol[Symbol("f")] <= p["mu"] * p["m"] * G),
    hints=lambda p: [
        "The crate is not moving, so its acceleration is zero.",
        "Friction here is static: it adjusts to exactly balance the push. It is not automatically mu·N.",
        f"The most static friction could give is mu_s·N = {fmt(p['mu'])} × {fmt(p['m'])} × 9.8; "
        f"your push is below that, so the crate stays put.",
    ],
    traps=lambda p: {"m_friction_always_mu_n": p["mu"] * p["m"] * G},
)


# ---- friction (kinetic): two equations, two unknowns ---------------------
def _kinetic_sample(r):
    m = _ints(r, [10, 15, 20, 25])
    mu = r.choice([Rational(1, 5), Rational(3, 10), Rational(2, 5)])
    F = Integer(5 * (int(Rational(3, 2) * mu * m * G / 5) + 1))  # comfortably above kinetic friction
    return {"m": m, "mu": mu, "F": F}


def _kinetic_eq(p):
    N, a = Symbol("N"), Symbol("a")
    return [Eq(N, p["m"] * G), Eq(p["F"] - p["mu"] * N, p["m"] * a)], [N, a], a


KINETIC = Template(
    id="t_friction_kinetic", concept_id="friction", unit="m/s²",
    sample=_kinetic_sample,
    stem=lambda p: (f"A {fmt(p['m'])} kg crate slides on a horizontal floor with kinetic friction "
                    f"coefficient {fmt(p['mu'])}. You push it horizontally with {fmt(p['F'])} N. "
                    f"Taking g = 9.8 m/s², what is its acceleration, in m/s²?"),
    equations=_kinetic_eq,
    closed_form=lambda p: (float(p["F"]) - float(p["mu"]) * float(p["m"]) * 9.8) / float(p["m"]),
    check=lambda p, sol: bool(sol[Symbol("a")] > 0),
    hints=lambda p: [
        "Find the normal force first: vertically the crate does not accelerate.",
        "Kinetic friction is mu_k·N, opposing the motion. Then net force = F - mu_k·N = m·a.",
        f"a = ({fmt(p['F'])} - {fmt(p['mu'])} × {fmt(p['m'])} × 9.8) / {fmt(p['m'])}",
    ],
)


# ---- incline: frictionless ramp ------------------------------------------
INCLINE = Template(
    id="t_incline", concept_id="incline", unit="m/s²",
    sample=lambda r: {"m": _ints(r, [2, 3, 5]), "theta": _ints(r, [30, 45, 60])},
    stem=lambda p: (f"A {fmt(p['m'])} kg block slides down a frictionless ramp inclined at "
                    f"{fmt(p['theta'])}° above the horizontal. Taking g = 9.8 m/s², what is its "
                    f"acceleration down the ramp, in m/s²?"),
    equations=lambda p: ([Eq(p["m"] * Symbol("a"), p["m"] * G * sin(pi * p["theta"] / 180))],
                         [Symbol("a")], Symbol("a")),
    closed_form=lambda p: 9.8 * math.sin(math.radians(float(p["theta"]))),
    check=lambda p, sol: bool(sol[Symbol("a")] > 0),
    hints=lambda p: [
        "Resolve the weight into components along the ramp and perpendicular to it.",
        "Along the ramp the only force is m·g·sin(theta), so m·g·sin(theta) = m·a. The mass cancels.",
        f"a = 9.8 × sin({fmt(p['theta'])}°)",
    ],
)


# ---- tension: two blocks on a rope ---------------------------------------
def _tension_eq(p):
    a, T = Symbol("a"), Symbol("T")
    return [Eq(p["F"] - T, p["m1"] * a), Eq(T, p["m2"] * a)], [a, T], T


TENSION = Template(
    id="t_tension", concept_id="tension", unit="N",
    sample=lambda r: {"m1": _ints(r, [2, 3, 4, 5]), "m2": _ints(r, [2, 3, 4, 5, 6]),
                      "F": _ints(r, [20, 30, 40, 50])},
    stem=lambda p: (f"On a frictionless table, a {fmt(p['m1'])} kg block is pulled by a horizontal force "
                    f"of {fmt(p['F'])} N. A rope connects it to a {fmt(p['m2'])} kg block trailing "
                    f"behind it. What is the tension in the rope, in newtons?"),
    equations=_tension_eq,
    closed_form=lambda p: float(p["F"]) * float(p["m2"]) / (float(p["m1"]) + float(p["m2"])),
    check=lambda p, sol: bool(0 < sol[Symbol("T")] < p["F"]),
    hints=lambda p: [
        "Draw a separate free-body diagram for each block.",
        "Front block: F - T = m1·a. Trailing block: T = m2·a. Both blocks share the same a.",
        f"Adding the two equations gives F = (m1 + m2)·a, so a = {fmt(p['F'])} / "
        f"({fmt(p['m1'])} + {fmt(p['m2'])}); then T = {fmt(p['m2'])} × a",
    ],
)


TEMPLATES = [NET_ACCEL, WEIGHT, NORMAL, STATIC, KINETIC, INCLINE, TENSION]
TEMPLATES_BY_ID = {t.id: t for t in TEMPLATES}


def templates_for(concept_id: str) -> list[Template]:
    return [t for t in TEMPLATES if t.concept_id == concept_id]
