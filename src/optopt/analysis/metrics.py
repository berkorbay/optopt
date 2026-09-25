"""Trajectory metrics (spec §7).

All functions take a trace dict (as written by optopt.experiments.run_one) and a reference objective `ref` in the
problem's own sense. Definitions follow Berthold (2013), "Measuring the impact of primal heuristics":

  primal gap  γ(t) = 1                              if no incumbent at t, or incumbent and ref differ in sign
                   = 0                              if |inc| = |ref| = 0
                   = |inc - ref| / max(|inc|,|ref|) otherwise
  primal integral  P(T) = ∫_0^T γ(t) dt   — reported normalised, P(T)/T ∈ [0, 1]

The primal-dual integral uses the same gap with the current dual bound in place of `ref`.
Every metric is cut at the budget T, so a solver that overruns its time limit gains nothing from the overrun.
"""
from __future__ import annotations

import math

CHECKPOINTS = (5, 10, 15, 30, 60)


def gap(a: float | None, b: float | None) -> float:
    if a is None or b is None:
        return 1.0
    if a == b:
        return 0.0
    if a * b < 0:
        return 1.0
    return min(1.0, abs(a - b) / max(abs(a), abs(b)))


BEYOND_REF_TOL = 1e-4


def primal_gap(v: float | None, ref: float | None, sense: int = 1) -> float:
    """Berthold gap, with two cases his definition assumes away (found by the property tests, 2026-09-23):
    an incumbent better than the reference by <= BEYOND_REF_TOL (relative) is solver tolerance -> gap 0;
    better by more than that is impossible against a proven optimum -> treated as invalid, gap 1."""
    if v is None or ref is None:
        return 1.0
    d = sense * (v - ref)
    if d < 0:
        return 0.0 if -d / max(1.0, abs(ref)) <= BEYOND_REF_TOL else 1.0
    return gap(v, ref)


def incumbent_steps(tr: dict) -> list[tuple[float, float]]:
    """Monotone (t, best-so-far) incumbent steps in the problem's sense."""
    sense = tr.get("sense", 1) or 1
    steps, best = [], None
    for e in sorted(tr.get("events", []), key=lambda e: e["t"]):
        p = e.get("primal")
        if p is None:
            continue
        if best is None or sense * p < sense * best - 1e-12 * max(1.0, abs(best)):
            best = p
            steps.append((e["t"], p))
    return steps


def dual_steps(tr: dict) -> list[tuple[float, float]]:
    sense = tr.get("sense", 1) or 1
    steps, best = [], None
    for e in sorted(tr.get("events", []), key=lambda e: e["t"]):
        d = e.get("dual")
        if d is None:
            continue
        if best is None or sense * d > sense * best:
            best = d
            steps.append((e["t"], d))
    return steps


def value_at(steps, t):
    v = None
    for s, x in steps:
        if s <= t:
            v = x
        else:
            break
    return v


def primal_integral(tr: dict, ref: float | None, T: float) -> float:
    """Normalised primal integral P(T)/T in [0, 1]."""
    if ref is None:
        return float("nan")
    sense = tr.get("sense", 1) or 1
    steps = [(t, v) for t, v in incumbent_steps(tr) if t < T]
    area, t_prev, g_prev = 0.0, 0.0, 1.0
    for t, v in steps:
        area += g_prev * (t - t_prev)
        t_prev, g_prev = t, primal_gap(v, ref, sense)
    area += g_prev * (T - t_prev)
    return area / T


def primal_dual_integral(tr: dict, T: float) -> float:
    """Normalised primal-dual integral PDI(T)/T in [0, 1]: the relative primal-dual gap integrated over [0, T].

    Primal and dual updates are merged on their exact timestamps; simultaneous updates are applied together.
    (Until 2026-09-24 the change times were rounded to 1e-6 s and the step values then looked up at the rounded
    time, so a change whose time rounded down was missed until the next event or for the rest of the budget —
    found by an external repository review.)
    """
    changes: dict[float, dict] = {}
    for t, v in incumbent_steps(tr):
        if t < T:
            changes.setdefault(t, {})["p"] = v
    for t, v in dual_steps(tr):
        if t < T:
            changes.setdefault(t, {})["d"] = v
    p = d = None
    area, t_prev = 0.0, 0.0
    for t in sorted(changes):
        area += gap(p, d) * (t - t_prev)
        c = changes[t]
        p, d = c.get("p", p), c.get("d", d)
        t_prev = t
    area += gap(p, d) * (T - t_prev)
    return area / T


def time_to_first(tr: dict, T: float) -> float:
    s = incumbent_steps(tr)
    return s[0][0] if s and s[0][0] <= T else math.inf


def time_to_target(tr: dict, ref: float | None, T: float, tol: float = 0.01) -> float:
    """First time the incumbent is within `tol` relative primal gap of ref; inf if never within T."""
    if ref is None:
        return math.inf
    sense = tr.get("sense", 1) or 1
    for t, v in incumbent_steps(tr):
        if t > T:
            break
        if primal_gap(v, ref, sense) <= tol:
            return t
    return math.inf


def gap_at(tr: dict, ref: float | None, t: float) -> float:
    return primal_gap(value_at(incumbent_steps(tr), t), ref, tr.get("sense", 1) or 1)


def summarize(tr: dict, ref: float | None, T: float) -> dict:
    out = {
        "pi": primal_integral(tr, ref, T),
        "pdi": primal_dual_integral(tr, T),
        "t_first": time_to_first(tr, T),
        "t_target": time_to_target(tr, ref, T),
        "t_target_5pct": time_to_target(tr, ref, T, 0.05),
        "incumbents": len([s for s in incumbent_steps(tr) if s[0] <= T]),
        "final_gap": gap_at(tr, ref, T),
    }
    for c in CHECKPOINTS:
        if c <= T:
            out[f"gap@{c}"] = gap_at(tr, ref, c)
    return out


def shifted_geomean(xs, shift=1.0):
    xs = [x for x in xs if x is not None and not math.isnan(x)]
    if not xs:
        return float("nan")
    return math.exp(sum(math.log(x + shift) for x in xs) / len(xs)) - shift
