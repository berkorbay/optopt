"""Correct SCIP incumbent values recorded before the 2026-09-23 19:30 recorder fix.

At SCIP's BESTSOLFOUND event, getPrimalbound() still returns the PREVIOUS incumbent's objective, so the old recorder
stored, at the time of incumbent k, the value of incumbent k-1 (None for the first). Because every new best solution
fires its own event, the sequence is recoverable exactly:
    true value of incumbent k  = value recorded at incumbent event k+1      (k < last)
    true value of the last one = the run's final primal bound (final_primal)
Verified on a fresh run with the fixed recorder (identical sequence). Sample events (NODESOLVED) were read after the
update and are already correct. HiGHS and cuOpt callbacks report the new solution's own objective — not affected.

The original value is kept as `primal_recorded` on every changed event; the trace gets
extra.incumbent_values_corrected = true so the correction is never applied twice. Traces recorded with the fixed
recorder carry extra.incumbent_values_exact = true and are skipped.

  python analysis/fix_scip_traces.py [--dry-run]
"""
import argparse
import json
from pathlib import Path

from optopt.paths import WORK as ROOT  # the workspace (cwd or $OPTOPT_HOME)


def correct(t):
    ex = t.get("extra") or {}
    if t.get("solver") != "scip" or ex.get("incumbent_values_exact") or ex.get("incumbent_values_corrected") or t.get("error"):
        return False
    ev = t.get("events", [])
    order = sorted(range(len(ev)), key=lambda i: ev[i]["t"])
    inc = [i for i in order if ev[i].get("kind") == "incumbent"]
    if not inc:
        return False
    recorded = [ev[i].get("primal") for i in inc]
    for k, i in enumerate(inc):
        true = recorded[k + 1] if k + 1 < len(inc) else t.get("final_primal")
        ev[i]["primal_recorded"] = ev[i].get("primal")
        ev[i]["primal"] = true
    ex["incumbent_values_corrected"] = True
    t["extra"] = ex
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    n_changed = n_scip = 0
    per_set = {}
    for f in sorted((ROOT / "traces/raw").glob("*/*.json")):
        try:
            t = json.loads(f.read_text())
        except json.JSONDecodeError:
            continue
        if t.get("solver") != "scip":
            continue
        n_scip += 1
        if correct(t):
            n_changed += 1
            per_set[f.parent.name] = per_set.get(f.parent.name, 0) + 1
            if not a.dry_run:
                tmp = f.with_suffix(".json.tmp")
                tmp.write_text(json.dumps(t))
                tmp.replace(f)
    print(f"SCIP traces {n_scip}, corrected {n_changed} ({'dry run' if a.dry_run else 'written'}): {per_set}")


if __name__ == "__main__":
    main()
