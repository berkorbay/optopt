"""Property-based tests for analysis/metrics.py (issue #26)."""
import math

from hypothesis import assume, given, settings
from hypothesis import strategies as st

from optopt.analysis.metrics import gap, incumbent_steps, primal_dual_integral, primal_integral, time_to_target

T = 30.0
times = st.floats(min_value=0.0, max_value=60.0, allow_nan=False)
objs = st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False)
events = st.lists(st.tuples(times, objs), max_size=25)


def trace(evs, sense=1, duals=None):
    out = [{"t": t, "primal": p, "dual": None} for t, p in evs]
    for t, d in duals or []:
        out.append({"t": t, "primal": None, "dual": d})
    return {"sense": sense, "events": out}


@given(objs, objs)
def test_gap_in_unit_interval(a, b):
    g = gap(a, b)
    assert 0.0 <= g <= 1.0


@given(events, objs, st.sampled_from([1, -1]))
def test_primal_integral_in_unit_interval(evs, ref, sense):
    p = primal_integral(trace(evs, sense), ref, T)
    assert 0.0 <= p <= 1.0 + 1e-12


@given(events, st.sampled_from([1, -1]))
def test_incumbents_monotone(evs, sense):
    steps = incumbent_steps(trace(evs, sense))
    vals = [v for _, v in steps]
    assert all(sense * b <= sense * a for a, b in zip(vals, vals[1:]))
    ts = [t for t, _ in steps]
    assert ts == sorted(ts)


@given(events, objs)
def test_events_after_budget_do_not_matter(evs, ref):
    inside = [(t, p) for t, p in evs if t < T]
    assert math.isclose(primal_integral(trace(evs), ref, T), primal_integral(trace(inside), ref, T), abs_tol=1e-12)


@given(events, objs, times, objs)
def test_adding_the_optimum_never_hurts(evs, ref, t_new, _):
    """Adding an incumbent equal to the reference at any time never increases the primal integral."""
    base = primal_integral(trace(evs), ref, T)
    more = primal_integral(trace(evs + [(t_new, ref)]), ref, T)
    assert more <= base + 1e-12


@given(events, objs)
def test_earlier_is_better(evs, ref):
    """Shifting every VALID event earlier (same values) never increases the primal integral."""
    evs = [(t, p) for t, p in evs if p >= ref]  # minimisation: valid incumbents are not below the optimum
    assume(evs)
    earlier = [(t / 2, p) for t, p in evs]
    assert primal_integral(trace(earlier), ref, T) <= primal_integral(trace(evs), ref, T) + 1e-12


@given(events, objs)
def test_target_time_consistent(evs, ref):
    evs = [(t, p) for t, p in evs if p >= ref]  # valid incumbents only (impossible ones are scored as invalid)
    tt = time_to_target(trace(evs), ref, T)
    if math.isfinite(tt):
        assert 0.0 <= tt <= T
        best_by_tt = [v for t, v in incumbent_steps(trace(evs)) if t <= tt][-1]
        from optopt.analysis.metrics import primal_gap
        assert primal_gap(best_by_tt, ref, 1) <= 0.01


@settings(max_examples=200)
@given(events, st.lists(st.tuples(times, objs), max_size=10))
def test_pdi_in_unit_interval(evs, duals):
    p = primal_dual_integral(trace(evs, 1, duals), T)
    assert 0.0 <= p <= 1.0 + 1e-12


@given(objs, st.floats(min_value=0, max_value=1e-5))
def test_within_tolerance_below_ref_is_zero_gap(ref, eps):
    from optopt.analysis.metrics import primal_gap
    assert primal_gap(ref - eps * max(1.0, abs(ref)), ref, 1) == 0.0


def test_impossible_incumbent_is_invalid():
    from optopt.analysis.metrics import primal_gap
    assert primal_gap(0.0, 576.34, 1) == 1.0      # the cuOpt/dano3_3 case
    assert primal_gap(900.0, 576.34, -1) == 1.0   # maximisation: above the optimum is impossible
