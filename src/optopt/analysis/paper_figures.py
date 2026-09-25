"""The paper's illustrative figures.

    python -m optopt.analysis.paper_figures      -> paper/figures/fig_primal_integral.pdf, fig_decomposition.pdf

Figure 1 needs the B2 trajectories of one MIPLIB instance (traces/raw/b2_scip); Figure 2 reads the derived tables only.
Palette: the validated categorical order used in the tutorials (blue, orange); every value is also printed on the figure.
"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from optopt.analysis.build_runs import solu  # noqa: E402
from optopt.analysis.metrics import incumbent_steps, primal_gap, primal_integral  # noqa: E402
from optopt.paths import WORK as ROOT  # noqa: E402

OUT = ROOT / "paper/figures"
BLUE, ORANGE, INK, INK2, GRID = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#e6e5e1"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.color": GRID, "grid.linewidth": 0.6, "lines.linewidth": 1.8, "pdf.fonttype": 42})
META = {"CreationDate": None, "ModDate": None}  # reproducible PDF bytes


def gap_curve(tr, ref, T):
    """Primal gap as a step function over [0, T]: 1 before the first incumbent."""
    sense = tr.get("sense", 1)
    xs, ys = [0.0], [1.0]
    for t, v in incumbent_steps(tr):
        if t >= T:
            break
        xs.append(t)
        ys.append(primal_gap(v, ref, sense))
    xs.append(T)
    ys.append(ys[-1])
    return xs, ys


def fig_primal_integral(inst="h80x6320d", T=120):
    ref = solu()[inst]
    fig, ax = plt.subplots(figsize=(6.2, 2.6))
    for arm, lab, color, ytext in (("C:D", "SCIP default", BLUE, 0.67), ("C:NOC", "separation off", ORANGE, 0.12)):
        tr = json.loads((ROOT / f"traces/raw/b2_scip/{inst}__{arm}__s0.json").read_text())
        xs, ys = gap_curve(tr, ref, T)
        P = primal_integral(tr, ref, T)
        ax.step(xs, ys, where="post", color=color)
        ax.fill_between(xs, ys, step="post", color=color, alpha=0.15, linewidth=0)
        ax.text(18, ytext, f"{lab}: $P({T}) = {P:.3f}$", color=INK, fontsize=9)
    ax.set_xlim(0, T)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("wall-clock seconds")
    ax.set_ylabel(r"primal gap $\gamma(t)$")
    fig.tight_layout()
    fig.savefig(OUT / "fig_primal_integral.pdf", metadata=META)
    plt.close(fig)


def fig_decomposition():
    b2 = json.loads((ROOT / "datasets/b2_decomposition.json").read_text())
    b3 = json.loads((ROOT / "datasets/b3_results.json").read_text())["B3_300s"]
    rows = [("primal integral, 120 s (45 instances)", b2["P"]["static_selection"], b2["P"]["dynamic_increment"],
             b2["P"]["ci"]["static_selection"], b2["P"]["ci"]["dynamic_increment"]),
            ("primal integral, 300 s (20 instances)", b3["P"]["static_choice_pct"], b3["P"]["switching_pct"],
             b3["P"]["ci_static"], b3["P"]["ci_switching"]),
            ("primal-dual integral, 120 s", b2["PDI"]["static_selection"], b2["PDI"]["dynamic_increment"],
             b2["PDI"]["ci"]["static_selection"], b2["PDI"]["ci"]["dynamic_increment"]),
            ("primal-dual integral, 300 s", b3["PDI"]["static_choice_pct"], b3["PDI"]["switching_pct"],
             b3["PDI"]["ci_static"], b3["PDI"]["ci_switching"])]
    fig, ax = plt.subplots(figsize=(6.2, 2.5))
    h = 0.36
    for i, (lab, s, w, cs, cw) in enumerate(rows):
        y = len(rows) - 1 - i
        for dy, v, ci, color, name in ((h / 2, s, cs, BLUE, "choosing the right setting at the start"),
                                       (-h / 2, w, cw, ORANGE, "the six switching schedules, on top")):
            ax.barh(y + dy, v, h * 0.92, color=color, label=name if i == 0 else None)
            ax.errorbar(v, y + dy, xerr=[[v - ci[0]], [ci[1] - v]], fmt="none", ecolor=INK2, elinewidth=0.9, capsize=2)
            ax.text(ci[1] + 0.4, y + dy, f"{v:+.1f} %", va="center", fontsize=8, color=INK)
    ax.set_yticks(range(len(rows)), [r[0] for r in rows][::-1])
    ax.axvline(0, color=INK2, linewidth=0.8)
    ax.set_xlim(-3, 42)
    ax.set_xlabel("gain over the best single SCIP setting (%)")
    ax.legend(frameon=False, fontsize=8, loc="lower center", bbox_to_anchor=(0.3, 1.0), ncol=2)
    fig.tight_layout()
    fig.savefig(OUT / "fig_decomposition.pdf", metadata=META, bbox_inches="tight")
    plt.close(fig)


def fig_social_card(inst="h80x6320d", T=120):
    """1200 x 630 link-preview image for the project site (Open Graph / X), from the Figure 1 runs."""
    ref = solu()[inst]
    fig = plt.figure(figsize=(12, 6.3), dpi=100)
    fig.patch.set_facecolor("#fcfcfb")
    fig.text(0.05, 0.80, "Optimizing the Optimizers", fontsize=33, fontweight="bold", color=INK, va="top")
    fig.text(0.05, 0.655, "Measuring learned control of MIP solvers\non a single DGX Spark", fontsize=20, color=INK,
             va="top", linespacing=1.3)
    fig.text(0.05, 0.40, "HiGHS \u00b7 SCIP \u00b7 cuOpt  |  8,000+ runs  |  code, data, tutorials", fontsize=14,
             color=INK2, va="top")
    fig.text(0.05, 0.12, "Berk Orbay  \u00b7  berkorbay.github.io/optopt", fontsize=15, color=INK2, va="bottom")
    ax = fig.add_axes([0.67, 0.20, 0.29, 0.52])
    for arm, lab, color, ytext in (("C:D", "SCIP default", BLUE, 0.70), ("C:NOC", "separation off", ORANGE, 0.14)):
        tr = json.loads((ROOT / f"traces/raw/b2_scip/{inst}__{arm}__s0.json").read_text())
        xs, ys = gap_curve(tr, ref, T)
        ax.step(xs, ys, where="post", color=color, linewidth=2.4)
        ax.fill_between(xs, ys, step="post", color=color, alpha=0.15, linewidth=0)
        ax.text(10, ytext, f"{lab}", color=INK, fontsize=11)
    ax.set_xlim(0, T)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("seconds", fontsize=11)
    ax.set_ylabel("gap to best known", fontsize=11)
    ax.set_facecolor("#fcfcfb")
    ax.set_title("same solver, two settings", fontsize=12, color=INK2, loc="left")
    out = ROOT / "docs/social-card.png"
    fig.savefig(out, dpi=100, facecolor=fig.get_facecolor(), metadata={"Software": None})
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    fig_decomposition()
    if (ROOT / "traces/raw/b2_scip").exists():
        fig_primal_integral()
        fig_social_card()
    else:
        print("traces/raw/b2_scip not present: Figure 1 kept as committed (re-run jobs/b2_*.jsonl to regenerate)")


if __name__ == "__main__":
    main()
