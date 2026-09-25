"""Traces -> datasets/runs.parquet: one row per (instance, strategy, seed) with the metrics of analysis/metrics.py.

Reference objective per instance: the MIPLIB published value (=opt= or =best=) when available, otherwise the best
primal value found by ANY run on that instance (all strategies, all seeds). The latter makes "gap" relative to
the best-known, which is the standard for time-to-good-solution comparisons but means a family's oracle gap is
0 by construction on at least one strategy.
"""
import json
import math
import sys
from pathlib import Path

import pandas as pd

from optopt.paths import WORK as ROOT  # the workspace (cwd or $OPTOPT_HOME)
from optopt.analysis.metrics import summarize  # noqa: E402


def solu():
    """MIPLIB 2017 published optima / best known values (=opt= / =best= lines of the official .solu file, shipped with
    the package as optopt/references/miplib2017.solu)."""
    from importlib.resources import files
    ref = {}
    for line in files("optopt.references").joinpath("miplib2017.solu").read_text().splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[0] in ("=opt=", "=best="):
            ref[parts[1]] = float(parts[2])
    return ref


def stem(p):
    n = Path(p).name
    for ext in (".mps.gz", ".mps"):
        if n.endswith(ext):
            return n[: -len(ext)]
    return n


def load(sets=None):
    traces = []
    track_a = {"miplib", "miplib300", "ml4co_item_placement", "ml4co_load_balancing", "pglib_uc"}
    for f in (ROOT / "traces/raw").glob("*/*.json"):
        if f.parent.name not in (sets or track_a):  # cross-solver (Track A) sets only; Track B has its own scripts
            continue
        try:
            t = json.loads(f.read_text())
        except json.JSONDecodeError:
            continue
        t["set"] = f.parent.name
        traces.append(t)
    return traces


def main():
    traces = load()
    published = solu()
    best = {}
    for t in traces:
        s = t.get("sense", 1) or 1
        for e in t.get("events", []):
            p = e.get("primal")
            if p is None:
                continue
            k = t["instance"]
            if k not in best or s * p < s * best[k]:
                best[k] = p
    # MIPLIB instances must use the published reference: a missing one is an error, never a silent switch to the
    # best observed run (review 2026-09-24). Other families (ML4CO, PGLib-UC) have no published optima by design.
    missing = sorted({stem(t["instance"]) for t in traces if t["set"].startswith("miplib")} - set(published))
    if missing:
        raise SystemExit(f"no published MIPLIB reference for {len(missing)} instance(s), e.g. {missing[:5]} — "
                         "the reference file shipped with optopt is incomplete; refusing to fall back silently")
    rows = []
    for t in traces:
        inst = t["instance"]
        ref = published.get(stem(inst), best.get(inst))
        T = float(t["budget"])
        r = dict(set=t["set"], instance=inst, name=stem(inst), strategy=t["strategy"], solver=t.get("solver"),
                 seed=t.get("seed", 0), budget=T, ref=ref, ref_source="published" if stem(inst) in published else "best-run",
                 status=t.get("status"), error=t.get("error"), solve_wall=t.get("solve_wall"),
                 read_time=t.get("read_time"), nodes=t.get("nodes"), final_primal=t.get("final_primal"),
                 final_dual=t.get("final_dual"))
        if t.get("error"):
            r.update(pi=1.0, pdi=1.0, t_first=math.inf, t_target=math.inf, t_target_5pct=math.inf, incumbents=0,
                     final_gap=1.0)
            for c in (5, 10, 15, 30):
                if c < T:
                    r[f"pi@{c}"], r[f"t_target@{c}"] = 1.0, math.inf
        else:
            r.update(summarize(t, ref, T))
            for c in (5, 10, 15, 30):
                if c < T:
                    sub = summarize(t, ref, c)
                    r[f"pi@{c}"], r[f"t_target@{c}"] = sub["pi"], sub["t_target"]
        r[f"pi@{int(T)}"], r[f"t_target@{int(T)}"] = r["pi"], r["t_target"]
        rows.append(r)
    df = pd.DataFrame(rows)
    # the 300 s screening re-uses MIPLIB instance paths: keep it out of the selection table
    df[df["set"] == "miplib300"].to_parquet(ROOT / "datasets/runs300.parquet")
    df = df[df["set"] != "miplib300"]
    df.to_parquet(ROOT / "datasets/runs.parquet")
    print(df.groupby(["set", "strategy"]).agg(n=("pi", "size"), pi=("pi", "mean"), err=("error", lambda x: x.notna().sum())))


if __name__ == "__main__":
    main()
