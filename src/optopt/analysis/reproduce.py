"""Regenerate every derived table from the committed traces and check that nothing changed.

    optopt reproduce            # in a workspace (a clone of the repository); needs no instances and no GPU

Runs the deterministic analysis chain (all numbers in the paper come from it), then compares every file under
datasets/ and paper/generated/ with its state before the run: text files byte for byte, parquet files by content. Exit code 1 if
any step fails or any output changed; 2 if there are no trajectories (unpack the release archive or re-run the jobs).
Steps that train Laya (GPU, not bit-reproducible) are not re-run; their stored predictions
(datasets/laya_preds.json, datasets/laya_diag.json) are inputs here. Exit code 1 if any step fails or any output changed.
"""
import hashlib
import io
import runpy
import sys
import time
from contextlib import redirect_stderr, redirect_stdout

import pandas as pd

from optopt.paths import WORK

STEPS = [  # (module, argv) in dependency order
    ("optopt.analysis.build_runs", []),
    ("optopt.analysis.pairs", []),
    ("optopt.experiments.selection", ["--laya", "datasets/laya_preds.json"]),
    ("optopt.analysis.reports", []),
    ("optopt.analysis.b0", []),
    ("optopt.analysis.b1", []),
    ("optopt.analysis.b2_decomp", []),
    ("optopt.analysis.b3", []),
    ("optopt.analysis.pilot_e", []),
    ("optopt.analysis.pilot_e2", []),
    ("optopt.analysis.diag", []),
    ("optopt.analysis.agents_llm", []),
    ("optopt.analysis.agents_llm", ["--latex"]),
    ("optopt.analysis.xchg", ["xchg"]),
    ("optopt.analysis.xchg", ["xheur"]),
    ("optopt.analysis.xchg", ["xhighs"]),
    ("optopt.analysis.xchg", ["xsame"]),
    ("optopt.analysis.timing_ctrl", []),
    ("optopt.analysis.timing_mech", []),
    ("optopt.analysis.main_tables", []),
    ("optopt.analysis.references", []),
    ("optopt.analysis.solcheck_coverage", []),
]
WATCH = ["datasets", "paper/generated"]


def snapshot():
    out = {}
    for d in WATCH:
        for f in sorted((WORK / d).rglob("*")):
            if not f.is_file():
                continue
            key = str(f.relative_to(WORK))
            if f.suffix == ".parquet":
                df = pd.read_parquet(f)
                out[key] = hashlib.sha256(pd.util.hash_pandas_object(df, index=True).values.tobytes()
                                          + str(list(df.columns)).encode()).hexdigest()
            else:
                out[key] = hashlib.sha256(f.read_bytes()).hexdigest()
    return out


def main():
    if not any((WORK / "traces/raw").glob("*/*.json")):
        print("No run trajectories in traces/raw/. They are not committed. To re-analyse the published study, unpack the\n"
              "release archive of the original traces into the workspace; for a new replication, re-run the experiments\n"
              "(optopt pool jobs/<set>.jsonl, optopt pair jobs/miplib.jsonl). See README, Reproducibility.")
        return 2
    before = snapshot()
    failed = []
    for mod, argv in STEPS:
        t = time.time()
        sys.argv = [mod] + argv
        buf = io.StringIO()
        try:
            with redirect_stdout(buf), redirect_stderr(buf):
                runpy.run_module(mod, run_name="__main__", alter_sys=True)
            status = "ok"
        except SystemExit as e:
            status = "ok" if not e.code else f"exit {e.code}"
        except Exception as e:  # noqa: BLE001 — report and continue, the comparison still runs
            status = f"FAILED {type(e).__name__}: {e}"
        print(f"{mod} {' '.join(argv)}: {status} ({time.time() - t:.0f} s)", flush=True)
        if status != "ok":
            failed.append(f"{mod} {' '.join(argv)}".strip())
    after = snapshot()
    changed = sorted(k for k in before if k in after and before[k] != after[k])
    added = sorted(set(after) - set(before))
    print(f"\n{len(before)} derived files checked; changed {len(changed)}, new {len(added)}")
    for k in changed:
        print("  changed:", k)
    for k in added:
        print("  new:", k)
    anc_ok = (WORK / "AGENTS.md").read_bytes() == (WORK / "paper/anc/AGENTS.md").read_bytes()
    print("companion file paper/anc/AGENTS.md identical to AGENTS.md:", anc_ok)
    for f in failed:
        print("  FAILED step:", f)
    return 1 if (changed or not anc_ok or failed) else 0


if __name__ == "__main__":
    sys.exit(main())
