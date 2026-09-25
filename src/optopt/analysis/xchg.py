"""Night 2026-09-23/24: live CPU||GPU pair with and without solution exchange, and SCIP + evolutionary partner.

All arms are scored on the PAIR's wall clock: t = 0 at the launch of both processes (reading the file counts), T = 60 s.
Reference value: the MIPLIB 2017 published optimum / best known (solu.txt), primal gap rule of analysis/metrics.py.
  portfolio P : best incumbent of either process over time (what a user of the pair gets)
  scip P      : SCIP's own trajectory, which includes every partner solution it accepted
Arms: race / g2c / both (SCIP || cuOpt), solo (SCIP alone), scip2 (SCIP || SCIP other seed), ea0 / ea20 (SCIP + EA).
Writes datasets/xchg_results.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

from optopt.paths import WORK as ROOT  # the workspace (cwd or $OPTOPT_HOME)
from optopt.analysis.build_runs import solu  # noqa: E402
from optopt.analysis.metrics import primal_integral  # noqa: E402

T = 60.0
# which run of the SCIP||cuOpt arms to score: "xchg" (2026-09-23 night, injection from an event handler) or "xheur"
# (2026-09-24, injection through a SCIP heuristic plugin); `python analysis/xchg.py xheur`
PAIR_SET = "xchg"


def shifted(tr, launch):
    if tr is None or tr.get("error") or "events" not in tr:
        return []
    off = (tr.get("extra") or {}).get("t0_epoch", launch) - launch
    return [dict(e, t=e["t"] + off) for e in tr["events"] if e.get("kind") == "incumbent" and e.get("primal") is not None]


def ea_events(rec, launch):
    """EA posts (feasible by its own check; SCIP re-checks what it accepts)."""
    if rec is None:
        return []
    return [{"t": t - launch, "primal": o, "kind": "incumbent"} for t, k, o in rec.get("xchg_log", []) if k == "post"]


def load(p):
    try:
        return json.loads(Path(p).read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def main():
    ref = solu()
    # an arm is taken from the requested session (PAIR_SET) when that session ran it; otherwise from the night's
    # EA/solo session ("xea"). Same-session comparisons are preferred: sessions differ by ~1-3 % (review 2026-09-24).
    by_set = {}
    for line in open(ROOT / "traces/raw/xchg_launch.jsonl"):
        r = json.loads(line)
        by_set.setdefault(r.get("set", "xchg"), {})[(r["arm"], r["instance"])] = r["launch_epoch"]
    own = by_set.get(PAIR_SET, {})
    launches = {k: (PAIR_SET, v) for k, v in own.items()}
    own_arms = {a for a, _ in own}
    for k, v in by_set.get("xea", {}).items():
        if k[0] not in own_arms:
            launches[k] = ("xea", v)
    rows = {}
    for (arm, inst), (pre, launch) in launches.items():
        d = ROOT / "traces/raw" / f"{pre}_{arm}"
        s = load(d / f"{inst}__scip__s0.json") or load(d / f"{inst}__cpu__s0.json")
        p = load(d / f"{inst}__partner__s0.json")
        if inst not in ref:
            continue
        crashed = s is None  # SCIP died without writing its trace (native crash): SCIP scores 1, the partner stands alone
        if crashed:
            s = {"sense": (p or {}).get("sense", 1), "events": [], "error": "no trace (process died)"}
        sense = s.get("sense", 1)
        se = shifted(s, launch)
        pe = ea_events(p, launch) if arm.startswith("ea") else shifted(p, launch)
        rows.setdefault(arm, {})[inst] = {
            "scip": primal_integral({"sense": sense, "events": se}, ref[inst], T),
            "partner": primal_integral({"sense": sense, "events": pe}, ref[inst], T) if p is not None else None,
            "portfolio": primal_integral({"sense": sense, "events": se + pe}, ref[inst], T),
            "injected": len(((s.get("extra") or {}).get("xchg_injected")) or []),
            "scip_crashed": crashed,
        }
    out = {"n": {a: len(v) for a, v in rows.items()}, "mean": {}, "paired": {}}
    for a, v in rows.items():
        out["mean"][a] = {k: float(np.nanmean([r[k] for r in v.values() if r[k] is not None])) for k in ("scip", "portfolio")}
        out["mean"][a]["injected_instances"] = int(sum(r["injected"] > 0 for r in v.values()))
        out["mean"][a]["scip_crashed"] = int(sum(r["scip_crashed"] for r in v.values()))

    def paired(a, b, key_a, key_b):
        common = sorted(set(rows.get(a, {})) & set(rows.get(b, {})))
        if len(common) < 5:
            return None
        x = np.array([rows[a][i][key_a] for i in common])
        y = np.array([rows[b][i][key_b] for i in common])
        d = x - y
        return {"n": len(common), f"{a}.{key_a}": float(x.mean()), f"{b}.{key_b}": float(y.mean()),
                "gain_pct": float(100 * (y.mean() - x.mean()) / y.mean()) if y.mean() > 0 else None,
                "p": float(stats.wilcoxon(d).pvalue) if (d != 0).any() else 1.0,
                "better/worse": [int((d < -1e-9).sum()), int((d > 1e-9).sum())]}
    for a, b, ka, kb in [("g2c", "race", "portfolio", "portfolio"), ("both", "race", "portfolio", "portfolio"),
                         ("g2c", "race", "scip", "scip"), ("race", "solo", "portfolio", "scip"),
                         ("scip2", "solo", "portfolio", "scip"), ("ea0", "solo", "scip", "scip"),
                         ("ea20", "solo", "scip", "scip"), ("ea20", "ea0", "scip", "scip"),
                         ("ea20", "scip2", "scip", "portfolio"), ("ea0", "scip2", "scip", "portfolio"),
                         ("hrace", "hsolo", "portfolio", "scip"), ("hrace", "race", "portfolio", "portfolio"),
                         ("race", "hsolo", "portfolio", "scip")]:
        r = paired(a, b, ka, kb)
        if r:
            out["paired"][f"{a}.{ka} vs {b}.{kb}"] = r
    json.dump({"summary": out, "rows": rows}, open(ROOT / f"datasets/{PAIR_SET}_results.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    PAIR_SET = sys.argv[1] if len(sys.argv) > 1 else "xchg"
    main()
