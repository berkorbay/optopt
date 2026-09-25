"""Figures for the tutorials, generated from the run traces and derived tables (the committed PNGs come from the paper's
runs; to regenerate them, re-run the jobs first so that traces/ exists).

  python tutorials/make_figures.py      -> tutorials/figures/*.png
Palette: validated categorical order (blue, orange, aqua, yellow, magenta, green) on a light surface; three slots sit
below 3:1 contrast, so every figure carries direct labels and every tutorial shows the numbers as a table as well.
"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from optopt.paths import WORK as ROOT  # the workspace (cwd or $OPTOPT_HOME)
from optopt.analysis.metrics import dual_steps, incumbent_steps, primal_gap  # noqa: E402

OUT = ROOT / "tutorials/figures"
OUT.mkdir(parents=True, exist_ok=True)
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
SURF, INK, INK2 = "#fcfcfb", "#0b0b0b", "#52514e"
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "axes.edgecolor": INK2, "axes.labelcolor": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "grid.color": "#e6e5e1", "grid.linewidth": 0.6,
                     "lines.linewidth": 2})


def trace(path):
    return json.loads(Path(path).read_text())


def steps_xy(steps, T):
    xs, ys = [], []
    for t, v in steps:
        if t > T:
            break
        xs.append(t)
        ys.append(v)
    return xs, ys


def fig_trajectory():
    """Incumbent and bound over time: SCIP default vs separation off on one instance (B2, seed 0)."""
    inst, T = "h80x6320d", 120
    fig, ax = plt.subplots(figsize=(7, 3.6))
    for i, (arm, lab) in enumerate((("C:D", "SCIP default"), ("C:NOC", "separation off"))):
        t = trace(ROOT / f"traces/raw/b2_scip/{inst}__{arm}__s0.json")
        px, py = steps_xy(incumbent_steps(t), T)
        dx, dy = steps_xy(dual_steps(t), T)
        if px:
            ax.step(px + [T], py + [py[-1]], where="post", color=C[i], label=f"{lab}: incumbent")
        if dx:
            ax.step(dx + [T], dy + [dy[-1]], where="post", color=C[i], linestyle="--", linewidth=1.2, label=f"{lab}: bound")
    ax.set_xlabel("wall-clock seconds")
    ax.set_ylabel("objective (minimise)")
    ax.set_title(f"MIPLIB {inst}: incumbent (solid) and bound (dashed)", loc="left", fontsize=10, color=INK)
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    ax.set_xlim(0, T)
    fig.tight_layout()
    fig.savefig(OUT / "01_trajectory.png", dpi=150)
    plt.close(fig)


def fig_primal_integral():
    """The primal gap step function and its integral (shaded) for one run."""
    inst, T = "h80x6320d", 120
    t = trace(ROOT / f"traces/raw/b2_scip/{inst}__C:D__s0.json")
    from optopt.analysis.build_runs import solu
    ref = solu()[inst]  # MIPLIB 2017 published optimum
    st = [(0.0, None)] + [(tt, v) for tt, v in incumbent_steps(t) if tt < T]
    xs, gs = [], []
    for i, (tt, v) in enumerate(st):
        xs.append(tt)
        gs.append(primal_gap(v, ref, 1))
    xs.append(T)
    gs.append(gs[-1])
    fig, ax = plt.subplots(figsize=(7, 3.2))
    ax.step(xs, gs, where="post", color=C[0])
    ax.fill_between(xs, gs, step="post", color=C[0], alpha=0.18, linewidth=0)
    area = sum(gs[i] * (xs[i + 1] - xs[i]) for i in range(len(xs) - 1)) / T
    ax.text(T * 0.55, 0.6, f"shaded area / T = P({T}) = {area:.3f}", color=INK, fontsize=9)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("wall-clock seconds")
    ax.set_ylabel("primal gap γ(t)")
    ax.set_title("Primal integral: the average gap over the budget (1 before the first solution)", loc="left",
                 fontsize=10, color=INK)
    fig.tight_layout()
    fig.savefig(OUT / "02_primal_integral.png", dpi=150)
    plt.close(fig)
    return area


def fig_headroom():
    """Best fixed strategy vs per-instance oracle, per family (Track A)."""
    port = pd.read_csv(ROOT / "datasets/portfolio_table.csv")
    rows = [("miplib", 60, "MIPLIB"), ("ml4co_item_placement", 30, "item placement"),
            ("ml4co_load_balancing", 30, "load balancing"), ("pglib_uc", 60, "unit commitment")]
    fig, ax = plt.subplots(figsize=(7, 3.4))
    x = np.arange(len(rows))
    w = 0.36
    for k, (col, lab, color) in enumerate((("sbs_cost", "best fixed strategy", C[0]), ("vbs_cost", "per-instance oracle", C[1]))):
        vals = [port[(port.family == f) & (port["T"] == T)][col].iloc[0] for f, T, _ in rows]
        bars = ax.bar(x + (k - 0.5) * w, vals, w - 0.03, color=color, label=lab)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.01, f"{v:.2f}", ha="center", fontsize=8, color=INK)
    ax.set_xticks(x, [r[2] for r in rows])
    ax.set_ylabel("mean primal integral P (lower is better)")
    ax.set_title("Headroom: what choosing per instance could gain over one fixed strategy", loc="left", fontsize=10, color=INK)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "03_headroom.png", dpi=150)
    plt.close(fig)


def fig_decomposition():
    """Choosing vs switching vs run-level (B2)."""
    r = json.load(open(ROOT / "datasets/b2_decomposition.json"))
    parts = [("static_selection", "choose the right static setting", C[0]), ("dynamic_increment", "switch during the solve", C[1]),
             ("run_level", "run-level (hindsight only)", C[2])]
    fig, ax = plt.subplots(figsize=(7, 3.2))
    for i, m in enumerate(("P", "PDI")):
        left = 0.0
        for key, lab, color in parts:
            v = max(0.0, r[m][key])
            ax.barh(i, v, left=left, color=color, height=0.5, edgecolor=SURF, linewidth=2, label=lab if i == 0 else None)
            if v > 1.5:
                ax.text(left + v / 2, i, f"{v:.1f}", ha="center", va="center", fontsize=8, color=INK)
            left += v
    ax.set_yticks([0, 1], ["primal integral", "primal-dual integral"])
    ax.set_xlabel("gain over the best single static setting (percent / points)")
    ax.set_title("Where the headroom lives inside SCIP (45 MIPLIB instances, 120 s)", loc="left", fontsize=10, color=INK)
    ax.legend(frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.28), ncol=3)
    fig.tight_layout()
    fig.savefig(OUT / "04_decomposition.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_bandit():
    """Which setting the bandit agent was in over time, on one item-placement run."""
    runs = sorted((ROOT / "traces/raw/pilot_e2").glob("item_placement*__A:bandit5__s0.json"))
    t = trace(runs[0])
    names = ["D", "NOC", "PSC", "INF", "HOFF", "HEU"]
    labels = {"D": "default", "NOC": "separation off", "PSC": "pseudo-cost branching", "INF": "inference branching",
              "HOFF": "heuristics off", "HEU": "aggressive heuristics"}
    cur, last, segs = "D", 0.0, []
    for tt, act, _ in t["extra"]["agent_log"]:
        segs.append((last, tt, cur))
        last = tt
        if act and act[0] == "set":
            cur = act[1]
    segs.append((last, 120.0, cur))
    fig, ax = plt.subplots(figsize=(7, 2.8))
    for a, b, s in segs:
        ax.barh(names.index(s), b - a, left=a, color=C[names.index(s)], height=0.6, edgecolor=SURF, linewidth=1)
    ax.set_yticks(range(len(names)), [labels[n] for n in names])
    ax.set_xlabel("wall-clock seconds")
    ax.set_title(f"Bandit agent (5 s decisions) on {runs[0].name.split('__')[0]}", loc="left", fontsize=10, color=INK)
    ax.set_xlim(0, 120)
    fig.tight_layout()
    fig.savefig(OUT / "05_bandit.png", dpi=150)
    plt.close(fig)


def fig_parallel():
    r = json.load(open(ROOT / "datasets/b2_seeds_analysis.json"))
    ks = [1, 2, 3, 5]
    fig, ax = plt.subplots(figsize=(6, 3.0))
    for i, (m, lab) in enumerate((("P", "primal integral"), ("PDI", "primal-dual integral"))):
        ys = [r[m]["parallel"][str(k)]["gain_pct"] for k in ks]
        ax.plot(ks, ys, marker="o", markersize=5, color=C[i], label=lab)
        ax.text(ks[-1] + 0.1, ys[-1], lab, fontsize=8, color=INK, va="center")
    ax.set_xticks(ks)
    ax.set_xlabel("copies of SCIP running in parallel (different seeds)")
    ax.set_ylabel("gain over one copy (%)")
    ax.set_xlim(0.8, 6.6)
    ax.set_title("Parallel copies: diminishing returns", loc="left", fontsize=10, color=INK)
    fig.tight_layout()
    fig.savefig(OUT / "06_parallel.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    fig_trajectory()
    a = fig_primal_integral()
    fig_headroom()
    fig_decomposition()
    fig_bandit()
    fig_parallel()
    print("figures written; example P =", round(a, 3))
