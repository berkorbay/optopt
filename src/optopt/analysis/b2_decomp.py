"""B2 decomposition (static choice / switching increment / run-level) with bootstrap CIs, the five-seed analysis and
parallel copies. Writes datasets/b2_decomposition.json and datasets/b2_seeds_analysis.json, paper table_b2.tex."""
import itertools
import json
import sys
from pathlib import Path

import numpy as np

from optopt.paths import WORK as ROOT  # the workspace (cwd or $OPTOPT_HOME)
from optopt.analysis.build_runs import solu, stem  # noqa: E402
from optopt.analysis.metrics import primal_dual_integral, primal_integral  # noqa: E402
from optopt.analysis.switch_sim import load  # noqa: E402
from optopt.portfolio.strategies import B2_STATIC  # noqa: E402

from optopt.analysis.decomp import decompose  # noqa: E402
from optopt.experiments import b2_gate as g  # noqa: E402
ARMS = g.ARMS


def decomposition():
    rng = np.random.default_rng(0)
    res = {}
    for metric in ("P", "PDI"):
        P = g.costs(metric, 120, g.instance_order())
        c = P[0].dropna().index.intersection(P[1].dropna().index)
        A0, B0 = P[0].loc[c], P[1].loc[c]

        def dec(A, B):
            d = decompose(A, B, B2_STATIC, ARMS)
            return [d["static_pct"], d["switching_pct"], d["total_pct"], d["run_level_pct"]]

        pt = dec(A0, B0)
        boot = np.array([dec(A0.iloc[i], B0.iloc[i]) for i in [rng.integers(0, len(c), len(c)) for _ in range(1000)]])
        ci = np.percentile(boot, [2.5, 97.5], axis=0)
        keys = ["static_selection", "dynamic_increment", "total", "run_level"]
        res[metric] = dict(n=len(c), **dict(zip(keys, pt)), ci={k: [float(ci[0][i]), float(ci[1][i])] for i, k in enumerate(keys)},
                           same_winner_both_seeds=float((A0.idxmin(axis=1) == B0.idxmin(axis=1)).mean()),
                           best_static=((A0 + B0) / 2)[B2_STATIC].mean().idxmin(), arm_means=((A0 + B0) / 2).mean().round(4).to_dict())
    json.dump(res, open(ROOT / "datasets/b2_decomposition.json", "w"), indent=1)
    return res


def seeds():
    runs, ref, T = load(), solu(), 120
    # the instances that were actually run with five seeds (jobs/b2_seeds.jsonl), not a re-derived ranking: the ranking
    # moved when runs.parquet was re-scored after the SCIP recorder correction, and 3 of its new top 20 have no extra seeds
    top = [stem(json.loads(line)["instance"]) for line in open(ROOT / "jobs/b2_seeds.jsonl")]
    SEEDS = [0, 1, 2, 3, 4]

    def cost(evs, sense, n, m):
        tr = {"sense": sense, "events": evs}
        return primal_dual_integral(tr, T) if m == "PDI" else primal_integral(tr, ref.get(n), T)
    out = {}
    for m in ("P", "PDI"):
        C = {}
        for n in top:
            rr = {(a, sd): runs.get((n, a, sd)) for a in B2_STATIC for sd in SEEDS}
            if any(v is None or v.get("error") for v in rr.values()):
                continue
            sense = rr[(B2_STATIC[0], 0)].get("sense", 1)
            C[n] = {a: np.array([cost(rr[(a, sd)]["events"], sense, n, m) for sd in SEEDS]) for a in B2_STATIC}
            C[n]["_ev"] = {a: [rr[(a, sd)]["events"] for sd in SEEDS] for a in B2_STATIC}
            C[n]["_s"] = sense
        names = list(C)
        mean_w = {n: min(B2_STATIC, key=lambda a: C[n][a].mean()) for n in names}
        agree = np.mean([min(B2_STATIC, key=lambda a: C[n][a][sd]) == mean_w[n] for n in names for sd in range(5)])
        best_a = min(B2_STATIC, key=lambda a: np.mean([C[n][a].mean() for n in names]))
        base = np.mean([C[n][best_a].mean() for n in names])
        par = {}
        for k in (1, 2, 3, 5):
            par[k] = float(np.mean([np.mean([cost(sum((C[n]["_ev"][best_a][i] for i in sub), []), C[n]["_s"], n, m)
                                             for sub in itertools.combinations(range(5), k)]) for n in names]))
        inst_or = np.mean([C[n][mean_w[n]].mean() for n in names])
        out[m] = dict(n=len(names), best_static=best_a, best_static_cost=float(base),
                      instance_oracle_pct=float(100 * (base - inst_or) / base),
                      per_seed_winner_matches_mean_winner=float(agree),
                      seed_sd=float(np.mean([C[n][a].std() for n in names for a in B2_STATIC])),
                      between_setting_sd=float(np.mean([np.std([C[n][a].mean() for a in B2_STATIC]) for n in names])),
                      parallel={str(k): {"cost": v, "gain_pct": float(100 * (base - v) / base)} for k, v in par.items()})
    json.dump(out, open(ROOT / "datasets/b2_seeds_analysis.json", "w"), indent=1)
    return out


def table(r):
    L = [r"\begin{table}[t]\centering\small", r"\resizebox{\linewidth}{!}{\begin{tabular}{lrrrrr}", r"\toprule",
         r"& static choice & switching, on top & run-level (hindsight) & same winner & best static \\", r"\midrule"]
    nm = {"P": r"primal integral $P(120)$", "PDI": r"primal-dual integral PDI$(120)$"}
    for m in ("P", "PDI"):
        d, c = r[m], r[m]["ci"]
        L.append(f"{nm[m]} & {d['static_selection']:+.1f}\\% [{c['static_selection'][0]:+.1f}, {c['static_selection'][1]:+.1f}] & "
                 f"{d['dynamic_increment']:+.1f}\\% [{c['dynamic_increment'][0]:+.1f}, {c['dynamic_increment'][1]:+.1f}] & "
                 f"{d['run_level']:.1f} pts & {100 * d['same_winner_both_seeds']:.0f}\\% & {d['best_static'].replace('C:', '')} \\\\")
    L += [r"\bottomrule", r"\end{tabular}}", rf"\caption{{Choosing versus switching inside SCIP: SCIP~10 with six static settings "
          rf"(default, separation off, pseudo-cost branching, inference branching, heuristics off, aggressive heuristics) and six "
          rf"mid-solve schedules (restart at 25\,\% or after a 20\,\% stall, branching switches, heuristic bursts), {r['P']['n']} MIPLIB "
          rf"instances, 120\,s, two seeds, one run per Cortex-X925 core. Gains are over the best single static setting; choices made "
          rf"on one seed and scored on the other; 95\,\% bootstrap intervals. Run-level: additional gain of an oracle that sees the "
          rf"run itself.}}\label{{tab:b2}}", r"\end{table}"]
    (ROOT / "paper/generated/table_b2.tex").write_text("\n".join(L))


if __name__ == "__main__":
    r = decomposition()
    table(r)
    s_ = seeds()
    for m in ("P", "PDI"):
        d = r[m]
        print(f"{m}: static {d['static_selection']:+.1f}% switching {d['dynamic_increment']:+.1f}% "
              f"{[round(x, 1) for x in d['ci']['dynamic_increment']]} run-level {d['run_level']:.1f} same-winner "
              f"{100 * d['same_winner_both_seeds']:.0f}% best {d['best_static']} | 5-seed inst-oracle {s_[m]['instance_oracle_pct']:+.1f}% "
              f"winner-stable {100 * s_[m]['per_seed_winner_matches_mean_winner']:.0f}% parallel "
              f"{ {k: round(v['gain_pct'], 1) for k, v in s_[m]['parallel'].items()} }")
