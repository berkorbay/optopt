"""Workspace paths round-trip with an external data directory; traces are strict JSON (review 2026-09-24)."""
import json
import os
import subprocess
import sys


def test_rel_resolve_round_trip_with_external_data(tmp_path):
    ext = tmp_path / "elsewhere"
    code = ("from optopt.paths import rel, resolve, DATA; p = DATA / 'miplib/inst/x.mps.gz'; "
            "assert rel(p) == 'data/miplib/inst/x.mps.gz', rel(p); assert resolve(rel(p)) == p; print('ok')")
    env = dict(os.environ, OPTOPT_DATA=str(ext), OPTOPT_HOME=str(tmp_path / "ws"))
    out = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True)
    assert out.stdout.strip() == "ok", out.stderr


def test_trace_json_has_no_nonfinite_numbers():
    from optopt.solvers.common import Trace
    t = Trace(instance="x", solver="scip", strategy="S0", seed=0, budget=1.0, sense=1)
    t.final_primal = float("inf")
    t.extra = {"a": [float("nan"), 1.0], "b": {"c": float("-inf")}}
    d = json.loads(t.to_json())            # strict parsers accept it
    assert d["final_primal"] is None and d["extra"]["a"] == [None, 1.0] and d["extra"]["b"]["c"] is None
