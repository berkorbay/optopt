"""The switching increment must not include the value of choosing the static setting (review 2026-09-24)."""
import numpy as np
import pandas as pd

from optopt.analysis.decomp import bootstrap, decompose

STATIC, ARMS = ["S1", "S2"], ["S1", "S2", "SW"]


def _frames(n=40):
    # half the instances prefer S1, half S2 (large static value); the schedule SW is never better than the best static
    rows = []
    for i in range(n):
        good, bad = (0.1, 0.6) if i % 2 == 0 else (0.6, 0.1)
        rows.append({"S1": good, "S2": bad, "SW": min(good, bad) + 0.05})
    df = pd.DataFrame(rows)
    return df, df.copy()


def test_large_static_zero_switching():
    A, B = _frames()
    d = decompose(A, B, STATIC, ARMS)
    assert d["static_pct"] > 50
    assert abs(d["switching_pct"]) < 1e-9
    assert d["total_pct"] == d["static_pct"] + d["switching_pct"]


def test_gate_on_switching_says_no_go():
    A, B = _frames()
    ci = bootstrap(A, B, STATIC, ARMS, n=200, keys=("switching_pct", "total_pct"))
    gate = 15.0
    assert ci["switching_pct"][1] < gate          # NO-GO on switching
    assert ci["total_pct"][0] > gate              # the old total-headroom gate would have said GO


def test_switching_detected_when_present():
    A, B = _frames()
    A["SW"], B["SW"] = 0.02, 0.02                  # the schedule beats every static setting everywhere
    d = decompose(A, B, STATIC, ARMS)
    assert d["switching_pct"] > 10
