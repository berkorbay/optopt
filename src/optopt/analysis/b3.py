"""B3 (night 2026-09-23/24): does switching pay at a longer budget? Same 12 arms as B2 plus the online bandit, on the
20 top-headroom MIPLIB instances of the five-seed study, 300 s, two seeds, one run per Cortex-X925 core.

Decomposition exactly as analysis/b2_decomp.py (choose on one seed, score on the other, both directions averaged):
  static choice = gain of the per-instance best static setting over the best single static setting
  switching increment = further gain when the schedules may be chosen too
Compared with B2 at 120 s on the SAME 20 instances. Bootstrap CIs over instances. Writes datasets/b3_results.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from optopt.paths import WORK as ROOT  # the workspace (cwd or $OPTOPT_HOME)
from optopt.analysis.build_runs import solu, stem  # noqa: E402
from optopt.analysis.metrics import primal_dual_integral, primal_integral  # noqa: E402
from optopt.analysis.decomp import decompose  # noqa: E402
from optopt.portfolio.strategies import B2_ARMS, B2_STATIC  # noqa: E402
from optopt.analysis.stats import by_instance  # noqa: E402

ARMS = list(B2_ARMS)


def costs(set_name, metric, T, names=None, arms=ARMS):
    ref = solu()
    rows = []
    for f in (ROOT / "traces/raw" / set_name).glob("*.json"):
        t = json.loads(f.read_text())
        n = stem(t["instance"])
        if names is not None and n not in names:
            continue
        c = 1.0 if t.get("error") else (primal_integral(t, ref.get(n), T) if metric == "P" else primal_dual_integral(t, T))
        rows.append((n, t["strategy"], t["seed"], c))
    df = pd.DataFrame(rows, columns=["name", "arm", "seed", "c"])
    return {s: df[df.seed == s].pivot_table(index="name", columns="arm", values="c").reindex(columns=arms)
            for s in (0, 1)}


def dec(A, B):
    d = decompose(A, B, B2_STATIC, ARMS)
    d = by_instance(d)  # instance-level paired differences (review 2026-09-24)
    return d["static_pct"], d["switching_pct"]


def decomposition(set_name, T, names=None, B=2000):
    out = {}
    rng = np.random.default_rng(0)
    for metric in ("P", "PDI"):
        P = costs(set_name, metric, T, names)
        c = P[0][ARMS].dropna().index.intersection(P[1][ARMS].dropna().index)
        A0, B0 = P[0].loc[c], P[1].loc[c]
        st, sw = dec(A0, B0)
        boots = []
        for _ in range(B):
            i = rng.integers(len(c), size=len(c))
            boots.append(dec(A0.iloc[i], B0.iloc[i]))
        boots = np.array(boots)
        out[metric] = {"n": int(len(c)), "static_choice_pct": st, "switching_pct": sw,
                       "ci_static": np.percentile(boots[:, 0], [2.5, 97.5]).tolist(),
                       "ci_switching": np.percentile(boots[:, 1], [2.5, 97.5]).tolist(),
                       "arm_means": {a: float((A0[a].mean() + B0[a].mean()) / 2) for a in ARMS}}
    return out, sorted(c)


def main():
    b3, names = decomposition("b3_scip300", 300)
    b2 = decomposition("b2_scip", 120, set(names))[0]
    res = {"B3_300s": b3, "B2_120s_same_instances": b2, "instances": names}
    # online bandit (5 s) vs default and vs the best single static setting, both seeds pooled
    for metric in ("P", "PDI"):
        P = costs("b3_scip300", metric, 300, arms=ARMS + ["A:bandit5"])
        df = pd.concat([P[0], P[1]]).dropna(subset=["A:bandit5", "C:D"])
        best = df[B2_STATIC].mean().idxmin()
        for base in ("C:D", best):
            d = df["A:bandit5"] - df[base]
            d = by_instance(d)  # instance-level paired differences (review 2026-09-24)
            res.setdefault("bandit", {}).setdefault(metric, {})[f"vs {base}"] = {
                "n_runs": int(len(df)), "bandit": float(df["A:bandit5"].mean()), base: float(df[base].mean()),
                "gain_pct": float(100 * (df[base].mean() - df["A:bandit5"].mean()) / df[base].mean()),
                "p": float(stats.wilcoxon(d).pvalue) if (d != 0).any() else 1.0}
    json.dump(res, open(ROOT / "datasets/b3_results.json", "w"), indent=1)
    for k in ("B3_300s", "B2_120s_same_instances"):
        for m in ("P", "PDI"):
            r = res[k][m]
            print(f"{k:24s} {m:3s} n={r['n']:2d} static {r['static_choice_pct']:+.1f}% {np.round(r['ci_static'],1)}"
                  f"  switching {r['switching_pct']:+.1f}% {np.round(r['ci_switching'],1)}")
    print(json.dumps(res["bandit"], indent=1))


if __name__ == "__main__":
    main()
