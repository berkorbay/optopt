"""Held-out decomposition of configuration headroom (one implementation, used by the B2 gate, the B2 report and B3).

Given two cost matrices A, B (rows = instances, columns = arms; one per seed), choose on one seed and score on the
other, both directions averaged:
  best single static    the static arm with the lowest mean cost on the choosing seed
  static oracle         per instance, the static arm that was best on the choosing seed
  full oracle           per instance, the best arm of ALL arms (static + schedules) on the choosing seed
Percentages are relative to the best single static cost on the scoring seed:
  static_pct     = best single static -> static oracle     (value of choosing the static setting per instance)
  switching_pct  = static oracle -> full oracle             (what switching adds on top of the right static choice)
  total_pct      = best single static -> full oracle        (the two together; NOT a measure of switching)
  run_level_pct  = full oracle -> per-run best in hindsight (only reachable with hindsight or parallel copies)
"""
import numpy as np


def decompose(A, B, static, arms, idx=None):
    if idx is not None:
        A, B = A.iloc[idx], B.iloc[idx]
    v = []
    for ch, sc in ((A, B), (B, A)):
        st = ch[static].mean().idxmin()
        bs = sc[st].mean()
        so = sc[static].to_numpy()[np.arange(len(sc)), ch[static].to_numpy().argmin(1)].mean()
        fo = sc[arms].to_numpy()[np.arange(len(sc)), ch[arms].to_numpy().argmin(1)].mean()
        v.append((bs, so, fo, sc[arms].min(axis=1).mean(), st))
    bs, so, fo, same = np.mean([x[:4] for x in v], 0)
    return {"static_pct": 100 * (bs - so) / bs, "switching_pct": 100 * (so - fo) / bs,
            "total_pct": 100 * (bs - fo) / bs, "run_level_pct": 100 * (fo - same) / bs,
            "best_static": [x[4] for x in v], "best_static_cost": bs}


def bootstrap(A, B, static, arms, n=1000, seed=0, keys=("static_pct", "switching_pct", "total_pct", "run_level_pct")):
    rng = np.random.default_rng(seed)
    boot = np.array([[decompose(A, B, static, arms, rng.integers(0, len(A), len(A)))[k] for k in keys] for _ in range(n)])
    lo, hi = np.percentile(boot, [2.5, 97.5], axis=0)
    return {k: [float(lo[i]), float(hi[i])] for i, k in enumerate(keys)}
