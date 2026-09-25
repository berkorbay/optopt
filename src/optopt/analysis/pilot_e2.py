"""Pilot set 2 (30 further held-out ML4CO instances (validation split) x 2 seeds, 120 s): default, bandit (10 s / 5 s), fixed HEU / NOC from t=0.
Writes datasets/pilot_e2_static.json (reference = best value found by any run in the set)."""
import json
import sys
from pathlib import Path
import pandas as pd
from scipy import stats
from optopt.paths import WORK as ROOT  # the workspace (cwd or $OPTOPT_HOME)
from optopt.analysis.build_runs import stem  # noqa: E402
from optopt.analysis.metrics import primal_dual_integral, primal_integral  # noqa: E402
from optopt.analysis.stats import by_instance  # noqa: E402


if __name__ == "__main__":
    ARMS = ["A:default", "C:HEU", "C:NOC", "A:bandit", "A:bandit5"]
    runs = {}
    for f in (ROOT / "traces/raw/pilot_e2").glob("*.json"):
        t = json.loads(f.read_text())
        if "instance" in t:
            runs[(stem(t["instance"]), t["strategy"], t["seed"])] = t
    best = {}
    for (n, _, _), t in runs.items():
        for e in t["events"]:
            p = e.get("primal")
            if p is not None and (n not in best or p < best[n]):
                best[n] = p
    rows = [dict(name=n, fam=("item" if n.startswith("item") else "load"), arm=a, seed=s, T=T,
                 P=primal_integral(t, best.get(n), T), PDI=primal_dual_integral(t, T))
            for (n, a, s), t in runs.items() if a in ARMS for T in (60, 120)]
    df = pd.DataFrame(rows)
    res = {}
    for T in (60, 120):
        for m in ("P", "PDI"):
            for fam in ("item", "load", "ALL"):
                sub = df[(df["T"] == T) & ((df.fam == fam) if fam != "ALL" else True)]
                piv = sub.pivot_table(index=["name", "seed"], columns="arm", values=m).reindex(columns=ARMS).dropna()
                means = piv.mean()
                bst = min(["C:HEU", "C:NOC", "A:default"], key=lambda a: means[a])
                out = dict(n=int(len(piv)), means=means.round(4).to_dict(), best_static=bst)
                for a in ("A:bandit", "A:bandit5"):
                    d = piv[a] - piv["A:default"]
                    d = by_instance(d)  # instance-level paired differences (review 2026-09-24)
                    out[f"{a}_vs_default_pct"] = float(100 * (means["A:default"] - means[a]) / means["A:default"])
                    out[f"{a}_vs_default_p"] = float(stats.wilcoxon(d).pvalue) if (d != 0).any() else 1.0
                d = piv["A:bandit5"] - piv[bst]
                d = by_instance(d)  # instance-level paired differences (review 2026-09-24)
                out["bandit5_vs_best_static_pct"] = float(100 * (means[bst] - means["A:bandit5"]) / means[bst])
                out["bandit5_vs_best_static_p"] = float(stats.wilcoxon(d).pvalue) if (d != 0).any() else 1.0
                res[f"{m}@{T}|{fam}"] = out
                print(f"{m}@{T} {fam:4s} n={len(piv)} " + " ".join(f"{a.split(':')[1]}={means[a]:.4f}" for a in ARMS) +
                      f" | bandit5 vs default {out['A:bandit5_vs_default_pct']:+.1f}% (p={out['A:bandit5_vs_default_p']:.2g})"
                      f" | bandit5 vs best static ({bst.split(':')[1]}) {out['bandit5_vs_best_static_pct']:+.1f}% (p={out['bandit5_vs_best_static_p']:.2g})")
    json.dump(res, open(ROOT / "datasets/pilot_e2_static.json", "w"), indent=1)
