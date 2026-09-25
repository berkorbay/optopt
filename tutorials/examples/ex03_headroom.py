"""Example 3 — best fixed strategy, per-instance oracle and headroom, from the paper's own runs (no solver needed).

  python tutorials/examples/ex03_headroom.py
"""
import pandas as pd

from common import ROOT

runs = pd.read_parquet(ROOT / "datasets/runs.parquet")
runs = runs[(runs["seed"] == 0) & (runs["set"] == "miplib")]
P = runs.pivot_table(index="name", columns="strategy", values="pi@60").dropna()
means = P.mean().sort_values()
print("mean P(60) per strategy (lower is better):\n", means.round(3).to_string())
sbs = means.index[0]
oracle = P.min(axis=1).mean()
print(f"\nsingle best strategy: {sbs} ({means.iloc[0]:.3f});  per-instance oracle: {oracle:.3f};  "
      f"headroom {100 * (means.iloc[0] - oracle) / means.iloc[0]:.0f} %")
print("\nhow often each strategy is the per-instance winner:\n", P.idxmin(axis=1).value_counts().to_string())
