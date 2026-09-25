"""Track B · B2 sequential go/no-go gate (all arms, instances in blocks, early stop on the confidence interval).

Racing arms is the wrong tool for a headroom gate — an arm that is bad on average can be the per-instance winner.
Instead every arm runs on every instance, but instances come in blocks ordered by how strongly they separated
strategies in Track A (independent prior data). After each block (from `--min-inst` on) we compute the held-out
SWITCHING increment (static oracle -> full oracle, optopt.analysis.decomp) with a bootstrap 95 % interval over
instances, and stop when
    upper bound < gate   → NO-GO (futility)      or      lower bound > gate   → GO.
This is an allocation heuristic (repeated looks, not a sequentially valid test); the reported numbers come from the
final sample (optopt.analysis.b2_decomp). History: the run on 2026-09-23 gated on the TOTAL headroom (static choice +
switching), which can say GO when only the static choice matters; the reported decomposition was always separate.

Each block is run by optopt.experiments.pool (pinned X925 lanes, hard per-run memory cap, resource record).
Progress: datasets/b2_gate_progress.jsonl ; final: datasets/b2_gate.json ; log: traces/b2_gate.log
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from optopt.paths import WORK as ROOT  # the workspace (cwd or $OPTOPT_HOME)
from optopt.analysis.build_runs import solu, stem  # noqa: E402
from optopt.analysis.metrics import primal_dual_integral, primal_integral  # noqa: E402
from optopt.analysis.decomp import bootstrap, decompose  # noqa: E402
from optopt.portfolio.strategies import B2_ARMS, B2_STATIC  # noqa: E402

ARMS = list(B2_ARMS)
SET = "b2_scip"


def log(msg):
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    with open(ROOT / "traces/b2_gate.log", "a") as f:
        f.write(line + "\n")


def instance_order():
    b0 = pd.read_csv(ROOT / "datasets/b0_meanP.csv", index_col=0).index.tolist()  # the 45 non-trivial instances
    prior = pd.read_parquet(ROOT / "datasets/runs.parquet")
    prior = prior[(prior["set"] == "miplib") & (prior["seed"] == 0)].pivot_table(index="name", columns="strategy",
                                                                               values="pi@30").dropna()
    spread = (prior.max(axis=1) - prior.min(axis=1)).sort_values(ascending=False)
    order = [n for n in spread.index if n in b0]
    return order + [n for n in b0 if n not in order]


def costs(metric, T, names):
    ref = solu()
    rows = []
    for f in (ROOT / "traces/raw" / SET).glob("*.json"):
        t = json.loads(f.read_text())
        n = stem(t["instance"])
        if n not in names:
            continue
        err = bool(t.get("error"))
        c = 1.0 if err else (primal_integral(t, ref.get(n), T) if metric == "P" else primal_dual_integral(t, T))
        rows.append((n, t["strategy"], t["seed"], c))
    df = pd.DataFrame(rows, columns=["name", "arm", "seed", "c"])
    return {s: df[df.seed == s].pivot_table(index="name", columns="arm", values="c").reindex(columns=ARMS)
            for s in (0, 1)}


def evaluate(names, T, metric):
    """Allocation heuristic for B2 (how many instances to run), on the SWITCHING increment — not the total headroom,
    which also contains the value of choosing the static setting (review 2026-09-24). Repeated bootstrap looks are not
    a sequentially valid test; the reported B2 numbers come from analysis/b2_decomp.py on the final sample."""
    P = costs(metric, T, names)
    common = P[0].dropna().index.intersection(P[1].dropna().index)
    A, B = P[0].loc[common], P[1].loc[common]
    d = decompose(A, B, B2_STATIC, ARMS)
    ci = bootstrap(A, B, B2_STATIC, ARMS, n=1000, seed=0, keys=("switching_pct", "total_pct"))
    means = ((A + B) / 2).mean().round(4).to_dict()
    return dict(n=len(common), switching_pct=d["switching_pct"], lo=ci["switching_pct"][0], hi=ci["switching_pct"][1],
                total_pct=d["total_pct"], total_ci=ci["total_pct"], best_static=d["best_static"],
                best_static_cost=d["best_static_cost"], arm_means=means)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=float, default=120)
    ap.add_argument("--block", type=int, default=5)
    ap.add_argument("--min-inst", type=int, default=15)
    ap.add_argument("--gate", type=float, default=15.0)
    ap.add_argument("--pin", default="5,6,7,8,9,15,16,17,18,19")
    ap.add_argument("--mem-cap-gb", type=float, default=9)
    ap.add_argument("--deadline", default="16:40", help="HH:MM — no new block starts after this")
    a = ap.parse_args()
    order = instance_order()
    log(f"B2 gate start: {len(order)} instances, {len(ARMS)} arms x 2 seeds, {a.budget:.0f} s, gate {a.gate} %")
    done, verdict = [], "INCONCLUSIVE (ran out of instances)"
    for i in range(0, len(order), a.block):
        if time.strftime("%H:%M") >= a.deadline:
            verdict = "INCONCLUSIVE (deadline)"
            break
        blk = order[i:i + a.block]
        jf = ROOT / f"jobs/b2_block{i // a.block:02d}.jsonl"
        with open(jf, "w") as f:
            for n in blk:
                f.write(json.dumps(dict(set=SET, instance=f"data/miplib/inst/{n}.mps.gz",
                                        strategies=ARMS, seeds=[0, 1], budget=a.budget)) + "\n")
        log(f"block {i // a.block}: {blk}")
        r = subprocess.run([sys.executable, "-m", "optopt.experiments.pool", str(jf), "--only", "cpu",
                            "--pin", a.pin, "--mem-cap-gb", str(a.mem_cap_gb), "--min-avail-gb", "20"],
                           capture_output=True, text=True)
        if r.returncode != 0:
            log(f"runner refused/failed: {r.stdout[-300:]} {r.stderr[-300:]}")
            verdict = "ABORTED (runner)"
            break
        done += blk
        rec = {"t": time.strftime("%H:%M:%S"), "instances": len(done)}
        for metric in ("P", "PDI"):
            rec[metric] = evaluate(done, a.budget, metric)
        with open(ROOT / "datasets/b2_gate_progress.jsonl", "a") as f:
            f.write(json.dumps(rec, default=str) + "\n")
        p = rec["P"]
        log(f"after {p['n']} inst: switching P {p['switching_pct']:+.1f}% [{p['lo']:+.1f}, {p['hi']:+.1f}]  "
            f"PDI {rec['PDI']['switching_pct']:+.1f}% [{rec['PDI']['lo']:+.1f}, {rec['PDI']['hi']:+.1f}]  best static {p['best_static']}")
        if len(done) >= a.min_inst:
            his = max(rec["P"]["hi"], rec["PDI"]["hi"])
            los = max(rec["P"]["lo"], rec["PDI"]["lo"])
            if his < a.gate:
                verdict = "NO-GO (upper bound below gate on both metrics)"
                break
            if los > a.gate:
                verdict = "GO (lower bound above gate)"
                break
    final = {"verdict": verdict, "instances": done, "budget": a.budget, "gate_pct": a.gate}
    json.dump(final, open(ROOT / "datasets/b2_gate.json", "w"), indent=1)
    log(f"VERDICT: {verdict}")


if __name__ == "__main__":
    main()
