"""Regression tests for the primal-dual integral (bug found by the 2026-09-24 repository review: change times were
rounded to 1e-6 s and then looked up at the rounded time, so updates whose time rounded down were missed)."""
import math
import random

import pytest

from optopt.analysis.metrics import dual_steps, gap, incumbent_steps, primal_dual_integral


def ev(t, primal=None, dual=None):
    return {"t": t, "primal": primal, "dual": dual}


def test_update_whose_time_rounds_down_is_seen():
    tr = {"events": [ev(1.0000004, 100, 100)]}
    assert primal_dual_integral(tr, 10) == pytest.approx(1.0000004 / 10)


def test_update_whose_time_rounds_up_is_seen():
    tr = {"events": [ev(1.0000006, 100, 100)]}
    assert primal_dual_integral(tr, 10) == pytest.approx(1.0000006 / 10)


def test_lone_closing_event():
    tr = {"events": [ev(5.0, 10, 10)]}
    assert primal_dual_integral(tr, 10) == pytest.approx(0.5)


def test_simultaneous_primal_and_dual_updates():
    tr = {"events": [ev(2.0, 100, None), ev(2.0, None, 50), ev(6.0, None, 100)]}
    # gap 1 until 2 s, then |100-50|/100 = 0.5 until 6 s, then 0
    assert primal_dual_integral(tr, 10) == pytest.approx((2 * 1 + 4 * 0.5) / 10)


def test_updates_at_and_after_the_budget_are_ignored():
    tr = {"events": [ev(10.0, 100, 100), ev(12.0, 100, 100)]}
    assert primal_dual_integral(tr, 10) == pytest.approx(1.0)
    tr = {"events": [ev(9.999999, 100, 100)]}
    assert primal_dual_integral(tr, 10) == pytest.approx(0.9999999)


def _brute_force(tr, T, n=200_000):
    """Independent reference: midpoint rule on a fine grid over the step functions."""
    ps, ds = incumbent_steps(tr), dual_steps(tr)

    def at(steps, t):
        v = None
        for s, x in steps:
            if s <= t:
                v = x
            else:
                break
        return v
    h = T / n
    return sum(gap(at(ps, (i + 0.5) * h), at(ds, (i + 0.5) * h)) for i in range(n)) * h / T


@pytest.mark.parametrize("seed", range(5))
def test_random_traces_match_brute_force(seed):
    rng = random.Random(seed)
    T = 10.0
    events, p, d = [], None, None
    for t in sorted(rng.uniform(0, 12) for _ in range(12)):
        if rng.random() < 0.5:
            p = (p if p is not None else 200.0) - rng.uniform(0, 20)
            events.append(ev(t, p, None))
        else:
            d = (d if d is not None else 0.0) + rng.uniform(0, 20)
            events.append(ev(t + rng.choice([0.0, 4e-7, -4e-7]), None, min(d, p) if p is not None else d))
    tr = {"events": events}
    ref = _brute_force(tr, T)
    assert math.isclose(primal_dual_integral(tr, T), ref, abs_tol=2e-4)
