"""Paired comparisons at the level the claims are about: instances (review 2026-09-24).

Seeds of the same instance are not independent draws of new instances, so paired differences are first averaged
within each instance; the Wilcoxon signed-rank test and a bootstrap interval (resampling instances) are computed on
those instance-level differences. All comparisons reported this way are exploratory unless a primary contrast was
fixed in advance (the paper states which).
"""
import numpy as np
from scipy import stats


def paired_instance(piv, a, base, n_boot=2000, seed=0):
    """piv: DataFrame indexed by (instance, seed), columns = arms, values = cost (lower is better)."""
    pair = piv[[a, base]].dropna()
    inst = pair.groupby(level=0).mean()
    d = (inst[a] - inst[base]).to_numpy()
    gain = 100 * (inst[base].mean() - inst[a].mean()) / inst[base].mean()
    rng = np.random.default_rng(seed)
    idx = [rng.integers(0, len(inst), len(inst)) for _ in range(n_boot)]
    boot = [100 * (inst[base].to_numpy()[i].mean() - inst[a].to_numpy()[i].mean()) / inst[base].to_numpy()[i].mean()
            for i in idx]
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return {"n_instances": int(len(inst)), "n_runs": int(len(pair)), "gain_pct": float(gain),
            "ci95": [float(lo), float(hi)], "p": float(stats.wilcoxon(d).pvalue) if (d != 0).any() else 1.0,
            "better/worse": [int((d < -1e-9).sum()), int((d > 1e-9).sum())]}


def by_instance(d):
    """Average a paired-difference Series over seeds within each instance (index level 0 = instance name)."""
    import pandas as pd
    if isinstance(d, pd.Series) and d.index.nlevels > 1:
        return d.groupby(level=0).mean()
    if isinstance(d, pd.Series) and d.index.has_duplicates:
        return d.groupby(level=0).mean()
    return d
