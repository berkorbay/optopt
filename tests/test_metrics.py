import math

from optopt.analysis.metrics import gap, primal_dual_integral, primal_integral, time_to_first, time_to_target


def tr(events, sense=1):
    return {"sense": sense, "events": events}


def ev(t, p=None, d=None):
    return {"t": t, "primal": p, "dual": d}


def test_gap_definition():
    assert gap(None, 1) == 1
    assert gap(5, 5) == 0
    assert gap(-1, 1) == 1
    assert math.isclose(gap(110, 100), 10 / 110)


def test_primal_integral_step():
    # no incumbent for 2 s (gap 1), then 110 vs ref 100 until 6 s, then optimal
    t = tr([ev(2, 110), ev(6, 100)])
    expect = (2 * 1 + 4 * (10 / 110) + 4 * 0) / 10
    assert math.isclose(primal_integral(t, 100, 10), expect)


def test_integral_cuts_at_budget():
    t = tr([ev(2, 110), ev(12, 100)])
    assert math.isclose(primal_integral(t, 100, 10), (2 + 8 * 10 / 110) / 10)


def test_maximisation_monotone():
    # a worse later incumbent must not count (max problem: larger is better)
    t = tr([ev(1, 90), ev(2, 80), ev(3, 100)], sense=-1)
    assert math.isclose(primal_integral(t, 100, 4), (1 + 2 * (10 / 100) + 0) / 4)


def test_times():
    t = tr([ev(1.5, 120), ev(4, 100.5)])
    assert time_to_first(t, 10) == 1.5
    assert time_to_target(t, 100, 10) == 4
    assert time_to_target(t, 100, 3) == math.inf


def test_pdi():
    t = tr([ev(1, 110, 90), ev(5, 100, 100)])
    g = gap(110, 90)
    assert math.isclose(primal_dual_integral(t, 10), (1 + 4 * g) / 10)
