"""Fixtures for the independent solution checker (review 2026-09-24): feasible, infeasible, objective mismatch, unknown
variable, missing model, tolerance boundary — and determinism on repeated checks of the same model (the cached-array
bug found on 2026-09-24)."""
import gzip
import json

import pytest

MPS = """NAME          TINY
ROWS
 N  obj
 L  c1
 G  c2
COLUMNS
    MARKER                 'MARKER'                 'INTORG'
    x         obj       1.0            c1        1.0
    x         c2        1.0
    MARKER                 'MARKER'                 'INTEND'
    y         obj       2.0            c1        1.0
RHS
    rhs       c1        4.0            c2        1.0
BOUNDS
 UP bnd       x         3.0
 UP bnd       y         3.0
ENDATA
"""


@pytest.fixture
def model(tmp_path):
    p = tmp_path / "tiny.mps"
    p.write_text(MPS)
    return p


def _check(tmp_path, model, values, reported, name="s"):
    from optopt.analysis.check_solutions import check
    sol = tmp_path / f"{name}.json.gz"
    with gzip.open(sol, "wt") as f:
        json.dump(values, f)
    tr = tmp_path / f"{name}.json"
    tr.write_text(json.dumps({"instance": str(model), "strategy": "S0", "seed": 0, "final_primal": reported}))
    return check((str(sol), str(tr)))


def test_feasible(tmp_path, model):
    r = _check(tmp_path, model, {"x": 1.0, "y": 0.5}, 2.0)
    assert r["feasible"]


def test_infeasible_row(tmp_path, model):
    r = _check(tmp_path, model, {"x": 3.0, "y": 2.0}, 7.0)      # x + y = 5 > 4
    assert not r["feasible"] and r["worst_row_rel"] > 1e-6


def test_integrality(tmp_path, model):
    r = _check(tmp_path, model, {"x": 1.5, "y": 0.0}, 1.5)
    assert not r["feasible"] and r["worst_int"] > 1e-6


def test_objective_mismatch(tmp_path, model):
    r = _check(tmp_path, model, {"x": 1.0, "y": 0.0}, 5.0)
    assert not r["feasible"] and r["obj_rel_err"] > 1e-6


def test_unknown_variable(tmp_path, model):
    r = _check(tmp_path, model, {"x": 1.0, "z": 1.0}, 1.0)
    assert not r["feasible"] and r["unknown_vars"] == 1


def test_tolerance_boundary(tmp_path, model):
    assert _check(tmp_path, model, {"x": 1.0, "y": 3.0000009}, 7.0000018)["feasible"]          # within 1e-6 · |rhs|
    assert not _check(tmp_path, model, {"x": 1.0, "y": 3.00002}, 7.00004, "b")["feasible"]


def test_missing_model(tmp_path):
    with pytest.raises(Exception):
        _check(tmp_path, tmp_path / "does_not_exist.mps", {"x": 1.0}, 1.0)


def test_repeated_checks_are_deterministic(tmp_path, model):
    verdicts = [_check(tmp_path, model, v, obj, f"r{i}")["feasible"]
                for i, (v, obj) in enumerate([({"x": 1.0, "y": 0.5}, 2.0), ({"x": 3.0, "y": 2.0}, 7.0)] * 3)]
    assert verdicts == [True, False] * 3
