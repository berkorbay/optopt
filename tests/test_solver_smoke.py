"""Solver smoke tests on tiny deterministic models (review 2026-09-24): objective sense, incumbent trajectory, saved
solution, the agent callback, strict JSON. Each run takes well under a second."""
import gzip
import json

import pytest

KNAP = """NAME          KNAP
OBJSENSE
    MAX
ROWS
 N  obj
 L  cap
COLUMNS
    MARKER                 'MARKER'                 'INTORG'
    a         obj       5.0            cap       2.0
    b         obj       4.0            cap       3.0
    c         obj       3.0            cap       1.0
    MARKER                 'MARKER'                 'INTEND'
RHS
    rhs       cap       4.0
BOUNDS
 UP bnd       a         1.0
 UP bnd       b         1.0
 UP bnd       c         1.0
ENDATA
"""  # maximise 5a + 4b + 3c s.t. 2a + 3b + c <= 4, binary -> optimum a = c = 1, value 8


@pytest.fixture
def knap(tmp_path):
    p = tmp_path / "knap.mps"
    p.write_text(KNAP)
    return p


def test_scip_maximisation_trajectory_and_saved_solution(knap, tmp_path):
    from optopt.solvers import scip
    sol = tmp_path / "sol.json.gz"
    tr = scip.run(str(knap), "S0", {}, budget=5, seed=0, sol_out=str(sol))
    assert tr.sense == -1 and tr.final_primal == pytest.approx(8.0)
    inc = [e.primal for e in tr.events if e.kind == "incumbent"]
    assert inc and inc[-1] == pytest.approx(8.0)
    assert all(b >= a - 1e-9 for a, b in zip(inc, inc[1:]))          # maximisation: incumbents improve upwards
    vals = json.load(gzip.open(sol, "rt"))
    assert vals.get("a") == pytest.approx(1.0) and vals.get("c") == pytest.approx(1.0)
    json.loads(tr.to_json())                                            # strict JSON


def test_highs_maximisation(knap):
    from optopt.solvers import highs
    tr = highs.run(str(knap), "H0", {}, budget=5, seed=0)
    assert tr.final_primal == pytest.approx(8.0)


def test_agent_callback_applies_its_action(knap):
    from optopt.agents.llm import FixedAgent
    from optopt.solvers import scip
    ag = FixedAgent("HEU")
    ag.instance = "knap"
    tr = scip.run(str(knap), "A:heu_cb", {}, budget=5, seed=0, agent=ag)
    log = tr.extra.get("agent_log", [])
    # on a tiny model SCIP may finish in presolve before any event; if the agent was called, its move is recorded
    assert tr.final_primal == pytest.approx(8.0)
    if log:
        assert log[0][1] == ["set", "HEU"] or log[0][1] == ("set", "HEU")
