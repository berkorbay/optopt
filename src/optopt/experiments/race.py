"""Racing (F-Race style) over candidate settings, with instances ordered by how well they discriminate.

Two modes:
  --replay <cost.csv>  : replay a race on an already-complete cost table (rows = instances, cols = arms) and report
                         how many runs it needed and whether it reached the same verdict as the exhaustive grid.
  (live mode is the next step: same loop, but each block launches experiments/00_baseline.py for the survivors.)

Procedure (Birattari et al. 2002, F-Race; López-Ibáñez et al. 2016, irace):
  1. order instances: most discriminating first (spread of prior costs across arms), trivial/hopeless last
  2. run all surviving arms on the next block of `block` instances
  3. after >= `min_inst` instances: Friedman test over survivors; if significant, drop every arm whose mean rank is
     worse than the leader's by more than the Nemenyi critical difference (paired, per instance)
  4. the reference arm (default) is never dropped, so the final comparison is always "winner vs default"
"""
from __future__ import annotations

import argparse
import math

import numpy as np
import pandas as pd
from scipy import stats

# Nemenyi q_alpha (alpha=0.05) for k = 2..12 (Demšar 2006, Table 5a)
Q05 = {2: 1.960, 3: 2.343, 4: 2.569, 5: 2.728, 6: 2.850, 7: 2.949, 8: 3.031, 9: 3.102, 10: 3.164, 11: 3.219, 12: 3.268}


def discriminating_order(C: pd.DataFrame) -> list:
    spread = C.max(axis=1) - C.min(axis=1)
    return list(spread.sort_values(ascending=False).index)


def race(C: pd.DataFrame, order, block=5, min_inst=10, reference="B:D", alpha=0.05):
    alive = list(C.columns)
    seen, runs, log = [], 0, []
    for i in range(0, len(order), block):
        blk = order[i:i + block]
        seen += blk
        runs += len(blk) * len(alive)
        if len(seen) < min_inst or len(alive) <= 2:
            continue
        sub = C.loc[seen, alive]
        if sub.shape[1] < 3:
            continue
        p = stats.friedmanchisquare(*[sub[c].to_numpy() for c in alive]).pvalue
        if p >= alpha:
            continue
        ranks = sub.rank(axis=1).mean()
        k, n = len(alive), len(seen)
        cd = Q05.get(k, 3.3) * math.sqrt(k * (k + 1) / (6 * n))
        best = ranks.min()
        drop = [a for a in alive if ranks[a] - best > cd and a != reference]
        if drop:
            alive = [a for a in alive if a not in drop]
            log.append((len(seen), p, drop))
    return alive, runs, log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay", required=True)
    ap.add_argument("--block", type=int, default=5)
    ap.add_argument("--min-inst", type=int, default=10)
    ap.add_argument("--order-from", default="datasets/runs.parquet",
                    help="independent prior runs (Track A) used to rank instances by discriminativeness")
    a = ap.parse_args()
    C = pd.read_csv(a.replay, index_col=0).dropna()
    exhaustive_runs = C.size
    exhaustive_best = C.mean().idxmin()
    # discriminativeness from INDEPENDENT prior data (Track A strategies on the same instances), not from C itself
    prior = pd.read_parquet(a.order_from)
    prior = prior[(prior["set"] == "miplib") & (prior["seed"] == 0)].pivot_table(index="name", columns="strategy",
                                                                               values="pi@30")
    prior_order = [n for n in discriminating_order(prior.dropna()) if n in C.index]
    prior_order += [n for n in C.index if n not in prior_order]
    for label, order in (("prior-discriminating", prior_order),
                         ("oracle-order (circular)", discriminating_order(C)),
                         ("random order", list(np.random.default_rng(0).permutation(C.index)))):
        alive, runs, log = race(C, order, a.block, a.min_inst)
        final_best = C[alive].mean().idxmin()
        print(f"{label:22s} runs {runs:4d}/{exhaustive_runs} ({100 * runs / exhaustive_runs:.0f}%), survivors {alive}, "
              f"winner {final_best} (exhaustive winner {exhaustive_best})")
        for n, p, d in log:
            print(f"    after {n:3d} inst  p={p:.3g}  dropped {d}")


if __name__ == "__main__":
    main()
