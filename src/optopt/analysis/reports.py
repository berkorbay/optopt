"""Generate paper tables/figures and vault result notes from datasets/*.parquet|csv.

  python analysis/reports.py
Writes paper/generated/*.tex, paper/figures/*.pdf|png, vault/30-results/*.md, datasets/key_numbers.json.
Prose in the paper is written by hand around these tables; this script only produces numbers.
"""
from __future__ import annotations
import json
import math
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from optopt.paths import WORK as ROOT  # the workspace (cwd or $OPTOPT_HOME)
from optopt.portfolio.strategies import MILESTONE as S  # noqa: E402
GEN = ROOT / "paper/generated"
FIG = ROOT / "paper/figures"
RES = ROOT / "vault/30-results"


def tex_escape(s):
    return str(s).replace("_", r"\_").replace("%", r"\%").replace("&", r"\&")


def flow_table(raw, none, piv, nstrat):
    """Attempted, with a solution from some strategy, and scored instances per family (PGLib-UC per power system)."""
    real = nstrat[nstrat >= len(S)].index  # run with all six strategies (other run sets add CPU-only instances)
    idx = real.to_frame(index=False)
    idx["group"] = [f if f != "pglib_uc" else f"pglib_uc:{str(i).split('/')[-1].split('__')[0]}" for f, i in real]
    idx["solved"] = [not bool(none[k]) for k in real]
    idx["scored"] = [k in piv.index for k in real]
    g = idx.groupby("group").agg(attempted=("solved", "size"), solved=("solved", "sum"), scored=("scored", "sum"))
    names = {"miplib": "MIPLIB 2017", "ml4co_item_placement": "ML4CO item placement",
             "ml4co_load_balancing": "ML4CO load balancing"}
    L = [r"\begin{table}[h]\centering\small", r"\begin{tabular}{lrrr}", r"\toprule",
         r"family (system) & attempted & some strategy finds a solution & scored \\", r"\midrule"]
    for k, r in g.iterrows():
        lab = names.get(k, "PGLib-UC, " + k.split(":")[1].upper().replace("_", "-") if k.startswith("pglib") else k)
        L.append(f"{lab} & {r.attempted} & {r.solved} & {r.scored} \\\\")
    L += [r"\midrule", f"all & {g.attempted.sum()} & {g.solved.sum()} & {g.scored.sum()} \\\\", r"\bottomrule",
          r"\end{tabular}", r"\caption{Instances in the cross-solver grid, run with all six strategies (one seed, 30\\,s view). An instance is scored on "
          r"the conditional cohort when it has a reference value, which requires some strategy to find a solution; in the "
          r"full cohort the unsolved instances score $P=1$ for every strategy. MIPLIB instances always have a published "
          r"reference, so its unsolved instances are scored in both.}\label{tab:flow}", r"\end{table}"]
    (GEN / "table_flow.tex").write_text("\n".join(L))


def portfolio_table(runs, key):
    """Mean cost per family x strategy at each budget, + SBS, VBS, headroom, win shares."""
    r0 = runs[runs["seed"] == 0]
    rows, md = [], []
    for T in (10, 30, 60):
        col = f"pi@{T}"
        if col not in r0:
            continue
        sub = r0[r0["budget"] >= T]
        raw = sub.pivot_table(index=["set", "instance"], columns="strategy", values=col, aggfunc="first", dropna=False)
        # Full cohort: an instance where no strategy finds any solution has no reference value, but by the metric's
        # definition every strategy scores P = 1 on it (review 2026-09-24: 23 PGLib-UC FERC cases). The conditional
        # cohort (some strategy finds a solution) is the one selectors are trained and evaluated on.
        none = sub.groupby(["set", "instance"])["incumbents"].max().fillna(0).eq(0)
        full = raw.copy()
        full.loc[none[none].index.intersection(full.index)] = full.loc[none[none].index.intersection(full.index)].fillna(1.0)
        full = full.dropna()[[s for s in S if s in raw.columns]]
        piv = raw.dropna()
        piv = piv[[s for s in S if s in piv.columns]]
        if T == 30:
            flow_table(raw, none, piv, sub.groupby(["set", "instance"])["strategy"].nunique())
        if piv.shape[1] < len(S):
            continue
        for fam in sorted(piv.index.get_level_values(0).unique()) + ["ALL"]:
            p = piv if fam == "ALL" else piv.loc[fam]
            pf = full if fam == "ALL" else full.loc[fam]
            sbs_all, vbs_all = pf.mean().min(), pf.min(axis=1).mean()
            means = p.mean()
            sbs = means.idxmin()
            vbs = p.min(axis=1).mean()
            best = p.eq(p.min(axis=1), axis=0)
            wins = (best.div(best.sum(axis=1), axis=0)).sum() / len(p)
            rows.append(dict(T=T, family=fam, n=len(p), **{s: means[s] for s in S}, sbs=sbs, sbs_cost=means.min(),
                             vbs_cost=vbs, headroom_pct=100 * (means.min() - vbs) / means.min() if means.min() > 0 else 0,
                             n_all=len(pf), sbs_cost_all=sbs_all, vbs_cost_all=vbs_all,
                             headroom_all_pct=100 * (sbs_all - vbs_all) / sbs_all if sbs_all > 0 else 0,
                             **{f"win_{s}": wins[s] for s in S}))
    df = pd.DataFrame(rows)
    df.to_csv(ROOT / "datasets/portfolio_table.csv", index=False)
    # LaTeX
    lines = [r"\begin{table}[t]\centering\small", r"\setlength{\tabcolsep}{4pt}",
             r"\resizebox{\linewidth}{!}{\begin{tabular}{llr" + "r" * len(S) + "rrr}", r"\toprule",
             r"$T$ & family & $n$ & " + " & ".join(S) + r" & SBS & VBS & headroom \\", r"\midrule"]
    for T, g in df.groupby("T"):
        for _, r in g.iterrows():
            cells = []
            for s in S:
                v = f"{r[s]:.3f}"
                cells.append(r"\textbf{" + v + "}" if s == r["sbs"] else v)
            lines.append(f"{T} & {FAM_NAME[r['family']]} & {r['n']} & " + " & ".join(cells) +
                         f" & {r['sbs']} & {r['vbs_cost']:.3f} & {r['headroom_pct']:.0f}\\% \\\\")
        lines.append(r"\midrule")
    lines[-1] = r"\bottomrule"
    lines += [r"\end{tabular}}", r"\caption{Mean normalised primal integral $P(T)$ (lower is better) per strategy, "
              r"seed 0. Bold: single best strategy (SBS) of the family. VBS: per-instance oracle. Headroom: "
              r"$(\mathrm{SBS}-\mathrm{VBS})/\mathrm{SBS}$.}\label{tab:portfolio-results}", r"\end{table}"]
    (GEN / "table_portfolio.tex").write_text("\n".join(lines))
    key["portfolio"] = df.to_dict("records")
    return df


def selection_tables(key):
    p = ROOT / "datasets/selection_results.csv"
    if not p.exists():
        return None
    df = pd.read_csv(p)
    key["selection"] = df.to_dict("records")
    out = []
    for scheme in ("pooled", "lofo"):
        for T in sorted(df["T"].unique()):
            g = df[(df["scheme"] == scheme) & (df["T"] == T) & (df["family"] == "ALL")]
            if g.empty:
                continue
            g = g.set_index("policy")
            lines = [r"\begin{table}[t]\centering\small", r"\begin{tabular}{lrrrr}", r"\toprule",
                     r"policy & cost $P(T)$ & closed gap [95\% CI] & TTT sgm (s) & reached 1\% \\", r"\midrule"]
            for pol in POL_ORDER:
                if pol not in g.index:
                    continue
                r = g.loc[pol]
                cg = "" if pd.isna(r["closed_gap"]) else f"{r['closed_gap']:+.2f} [{r['closed_gap_lo']:+.2f}, {r['closed_gap_hi']:+.2f}]"
                lines.append(f"{POL_NAME[pol]} & {r['cost']:.3f} & {cg} & {r['ttt_sgm']:.1f} & {100 * r['reached_target']:.0f}\\% \\\\")
            n = int(g["n"].iloc[0])
            sbs = g["sbs"].iloc[0]
            lines += [r"\bottomrule", r"\end{tabular}",
                      rf"\caption{{Strategy selection, {'pooled 5-fold' if scheme == 'pooled' else 'leave-one-family-out'} "
                      rf"evaluation, $T={T}$\,s, $n={n}$ test instances. Closed gap is relative to the hindsight single best "
                      rf"strategy on the same instances ({sbs}; 0 = SBS, 1 = oracle). TTT: time to 1\% primal gap, "
                      rf"censored at $2T$, shifted geometric mean.}}\label{{tab:sel-{scheme}-{T}}}", r"\end{table}"]
            name = f"table_selection_{scheme}_{T}.tex"
            (GEN / name).write_text("\n".join(lines))
            out.append(name)
    # per-family closed gap (pooled)
    fams = [f for f in df["family"].unique() if f != "ALL"]
    lines = [r"\begin{table}[t]\centering\small", r"\resizebox{\linewidth}{!}{\begin{tabular}{ll" + "r" * len(fams) + "}", r"\toprule",
             r"$T$ & policy & " + " & ".join(FAM_NAME[f] for f in fams) + r" \\", r"\midrule"]
    for T in sorted(df["T"].unique()):
        g = df[(df["scheme"] == "pooled") & (df["T"] == T)]
        for pol in ["best-fixed(train)", "rules", "lightgbm", "mlp", "laya-zeroshot", "mip-laya"]:
            cells = []
            for f in fams:
                x = g[(g["family"] == f) & (g["policy"] == pol)]
                cells.append("--" if x.empty or pd.isna(x["closed_gap"].iloc[0]) else f"{x['closed_gap'].iloc[0]:+.2f}")
            if all(c == "--" for c in cells):
                continue
            lines.append(f"{T} & {POL_NAME[pol]} & " + " & ".join(cells) + r" \\")
        hr = []
        for f in fams:
            x = g[(g["family"] == f) & (g["policy"] == "oracle")]
            hr.append("--" if x.empty else f"{x['headroom_pct'].iloc[0]:.0f}\\%")
        lines.append(f"{T} & \\emph{{oracle headroom}} & " + " & ".join(hr) + r" \\")
        lines.append(r"\midrule")
    lines[-1] = r"\bottomrule"
    lines += [r"\end{tabular}}", r"\caption{Closed gap per family, pooled policy (one model for all families). "
              r"Headroom = oracle improvement over the family's hindsight SBS. Where the headroom is small (PGLib-UC at 10\,s: "
              r"1\%) closed-gap values are ratios of tiny differences and very large in magnitude; read them with the "
              r"headroom row.}\label{tab:sel-family}", r"\end{table}"]
    (GEN / "table_selection_family.tex").write_text("\n".join(lines))
    return out


def variance(runs, key):
    v = runs[runs["name"].isin(runs[runs["seed"] > 0]["name"].unique())]
    if v.empty or v["seed"].nunique() < 2:
        return None
    rows = []
    for (name, strat), g in v.groupby(["name", "strategy"]):
        if len(g) < 2:
            continue
        rows.append(dict(name=name, strategy=strat, n=len(g), mean=g["pi"].mean(), sd=g["pi"].std(),
                         rng=g["pi"].max() - g["pi"].min()))
    d = pd.DataFrame(rows)
    # oracle stability: per seed, which strategy wins among those with that seed
    stab = []
    multi = sorted(set(v[v["seed"] > 0]["strategy"]))  # strategies that have extra seeds (CPU only tonight)
    for name, g in v.groupby("name"):
        g = g[g["strategy"].isin(multi)]
        seeds = sorted(set(g["seed"]))
        winners = {}
        for sd in seeds:
            gg = g[g["seed"] == sd].set_index("strategy")["pi"]
            if len(gg) == len(multi):
                winners[sd] = gg.idxmin()
        mean_pi = g.groupby("strategy")["pi"].mean()
        if winners:
            stab.append(dict(name=name, seed0=winners.get(0), mean_winner=mean_pi.idxmin(),
                             agree=np.mean([w == mean_pi.idxmin() for w in winners.values()]),
                             seed0_regret=float(mean_pi.get(winners.get(0), np.nan) - mean_pi.min()) if 0 in winners else np.nan))
    st = pd.DataFrame(stab)
    # noise inflation of a single-seed oracle (leave-one-seed-out), same four strategies
    vv = v[v["strategy"].isin(multi)]
    res = []
    for sd in sorted(vv["seed"].unique()):
        a = vv[vv["seed"] == sd].pivot_table(index="name", columns="strategy", values="pi")[multi].dropna()
        o = vv[vv["seed"] != sd].pivot_table(index="name", columns="strategy", values="pi", aggfunc="mean")[multi].loc[a.index]
        c = a.to_numpy().argmin(1)
        res.append((a.min(axis=1).mean(), o.to_numpy()[np.arange(len(a)), c].mean(), o.mean().min(), o.min(axis=1).mean()))
    own, real, sbs_o, true_o = np.mean(res, 0)
    key["noise_inflation"] = dict(apparent_pct=100 * (sbs_o - own) / sbs_o, realised_pct=100 * (sbs_o - real) / sbs_o,
                                  true_pct=100 * (sbs_o - true_o) / sbs_o)
    agg = d.groupby("strategy").agg(mean_sd=("sd", "mean"), median_sd=("sd", "median"), max_range=("rng", "max"))
    key["variance"] = dict(per_strategy=agg.reset_index().to_dict("records"), oracle_stability=st.to_dict("records"))
    lines = [r"\begin{table}[t]\centering\small", r"\begin{tabular}{lrrr}", r"\toprule",
             r"strategy & mean s.d. of $P(60)$ & median s.d. & max range \\", r"\midrule"]
    for s, r in agg.iterrows():
        lines.append(f"{s} & {r['mean_sd']:.3f} & {r['median_sd']:.3f} & {r['max_range']:.3f} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}",
              rf"\caption{{Run-to-run variability across seeds on the {d['name'].nunique()}-instance MIPLIB variance subset "
              rf"(HiGHS and SCIP strategies, seeds 0--4; cuOpt extra seeds were cut for time). Among these four strategies the "
              rf"per-seed winner equals the seed-averaged winner "
              rf"on {100 * st['agree'].mean() if len(st) else float('nan'):.0f}\% of (instance, seed) pairs. A single-seed oracle "
              rf"appears {key['noise_inflation']['apparent_pct']:.1f}\% better than the SBS on its own seed and realises "
              rf"{key['noise_inflation']['realised_pct']:.1f}\% on held-out seeds (true seed-mean oracle: "
              rf"{key['noise_inflation']['true_pct']:.1f}\%).}}\label{{tab:variance}}",
              r"\end{table}"]
    (GEN / "table_variance.tex").write_text("\n".join(lines))
    return agg, st


def contention(key):
    p = ROOT / "datasets/contention.jsonl"
    if not p.exists():
        return None
    d = pd.DataFrame([json.loads(l) for l in open(p)])
    lat = [json.loads(l) for l in open(ROOT / "datasets/contention_laya.jsonl")] if (ROOT / "datasets/contention_laya.jsonl").exists() else []
    base = d[d["cond"] == "A"].groupby("instance")["pi"].mean()
    d["pi_rel"] = d.apply(lambda r: r["pi"] - base.get(r["instance"], np.nan), axis=1)

    def smi_col(rows, i):
        vals = []
        for s in rows:
            try:
                x = s.split(",")[i].strip()
                vals.append(float(x))
            except (ValueError, IndexError):
                pass
        return np.mean(vals) if vals else np.nan
    d["gpu_util"] = d["smi"].apply(lambda r: smi_col(r, 0))
    d["sm_clock"] = d["smi"].apply(lambda r: smi_col(r, 3))
    d["power"] = d["smi"].apply(lambda r: smi_col(r, 4))
    agg = d.groupby("cond").agg(n=("pi", "size"), pi=("pi", "mean"), dpi=("pi_rel", "mean"), dpi_sd=("pi_rel", "std"),
                                nodes=("nodes", "median"), util=("gpu_util", "mean"), clock=("sm_clock", "mean"),
                                power=("power", "mean"), t_first=("t_first", "median"))
    L = {}
    for rec in lat:
        L.setdefault(rec["mode"], []).extend(rec["lat_ms"])
    latrows = {m: dict(n=len(v), median=float(np.median(v)), p90=float(np.percentile(v, 90))) for m, v in L.items() if v}
    key["contention"] = dict(table=agg.reset_index().to_dict("records"), laya_latency=latrows)
    names = {"A": "A: cuOpt alone", "B": "B: + Laya loaded, idle", "C": "C: + Laya every 5 s", "D": "D: + Laya continuous"}
    lines = [r"\begin{table}[t]\centering\small", r"\begin{tabular}{lrrrrrr}", r"\toprule",
             r"condition & runs & $P(30)$ & $\Delta P$ vs A & GPU util & SM MHz & Laya ms (med/p90) \\", r"\midrule"]
    for c, r in agg.iterrows():
        lr = latrows.get(c)
        ls = f"{lr['median']:.0f} / {lr['p90']:.0f}" if lr else "--"
        lines.append(f"{names[c]} & {int(r['n'])} & {r['pi']:.3f} & {r['dpi']:+.3f} $\\pm$ {r['dpi_sd']:.3f} & "
                     f"{r['util']:.0f}\\% & {r['clock']:.0f} & {ls} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}",
              r"\caption{GPU contention between cuOpt (C0, 30\,s) and Laya inference on the shared GB10 GPU. "
              r"$\Delta P$: paired difference in primal integral against condition A on the same instance "
              r"(mean $\pm$ s.d. over instances and repetitions).}\label{tab:contention}", r"\end{table}"]
    (GEN / "table_contention.tex").write_text("\n".join(lines))
    return agg, latrows


def figures(runs, port):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
    cols = {"H0": "#4C78A8", "H1": "#9ECAE9", "S0": "#F58518", "S1": "#FFBF79", "C0": "#54A24B", "C1": "#88D27A"}
    # Fig 1: mean P(T) per strategy per family, with VBS marker
    g = port[port["T"] == 30] if (port["T"] == 30).any() else port
    fams = [f for f in g["family"] if f != "ALL"] + ["ALL"]
    fig, ax = plt.subplots(figsize=(7, 2.8))
    w = 0.12
    x = np.arange(len(fams))
    for i, s in enumerate(S):
        ax.bar(x + (i - 2.5) * w, [g[g["family"] == f][s].iloc[0] for f in fams], w, label=s, color=cols[s])
    ax.scatter(x, [g[g["family"] == f]["vbs_cost"].iloc[0] for f in fams], marker="_", s=900, color="black",
               label="oracle", zorder=5)
    ax.set_xticks(x, [FAM_NAME[f] for f in fams], rotation=0, fontsize=7)
    ax.set_ylabel(f"mean $P({int(g['T'].iloc[0])})$ (lower better)")
    ax.legend(ncol=7, fontsize=7, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.18))
    fig.tight_layout()
    fig.savefig(FIG / "portfolio.pdf")
    fig.savefig(FIG / "portfolio.png", dpi=150)
    plt.close(fig)
    # Fig 2: closed gap per policy, pooled, all T
    p = ROOT / "datasets/selection_results.csv"
    if p.exists():
        df = pd.read_csv(p)
        df = df[(df["scheme"] == "pooled") & (df["family"] == "ALL")]
        pols = [q for q in POL_ORDER if q in set(df["policy"]) and q != "oracle"]
        Ts = sorted(df["T"].unique())
        fig, ax = plt.subplots(figsize=(7, 2.6))
        w = 0.8 / len(Ts)
        for k, T in enumerate(Ts):
            gg = df[df["T"] == T].set_index("policy")
            y = [gg.loc[q, "closed_gap"] if q in gg.index else np.nan for q in pols]
            lo = [gg.loc[q, "closed_gap"] - gg.loc[q, "closed_gap_lo"] if q in gg.index else 0 for q in pols]
            hi = [gg.loc[q, "closed_gap_hi"] - gg.loc[q, "closed_gap"] if q in gg.index else 0 for q in pols]
            ax.bar(np.arange(len(pols)) + (k - (len(Ts) - 1) / 2) * w, y, w, yerr=[lo, hi], capsize=2,
                   label=f"T={T}s", color=["#bbbbbb", "#777777", "#333333"][k % 3])
        ax.axhline(0, color="black", lw=0.8)
        ax.axhline(1, color="black", lw=0.8, ls="--")
        ax.set_xticks(np.arange(len(pols)), [POL_NAME[q] for q in pols], rotation=20, ha="right", fontsize=7)
        ax.set_ylabel("closed gap (0=SBS, 1=oracle)")
        ax.set_ylim(max(-1.5, ax.get_ylim()[0]), 1.1)
        ax.legend(frameon=False, fontsize=7)
        fig.tight_layout()
        fig.savefig(FIG / "closed_gap.pdf")
        fig.savefig(FIG / "closed_gap.png", dpi=150)
        plt.close(fig)


def overhead(key):
    """Spec §23: policy overhead = feature extraction + inference, as % of the budget."""
    f = pd.read_parquet(ROOT / "datasets/features.parquet")
    lat = None
    p = ROOT / "datasets/laya_latency.json"
    if p.exists():
        lat = json.load(open(p))
    rows = []
    for fam, g in f.groupby("set"):
        rows.append(dict(family=fam, n=len(g), feat_med_ms=1000 * g["feat_time"].median(),
                         feat_p90_ms=1000 * g["feat_time"].quantile(0.9), feat_max_ms=1000 * g["feat_time"].max()))
    d = pd.DataFrame(rows)
    key["overhead"] = dict(features=d.to_dict("records"), laya=lat)
    lm = lat["single_median_ms"] if lat else float("nan")
    lines = [r"\begin{table}[t]\centering\small", r"\begin{tabular}{lrrrrr}", r"\toprule",
             r"family & $n$ & features med (ms) & p90 (ms) & max (ms) & overhead (own budget) \\", r"\midrule"]
    for _, r in d.iterrows():
        B = 30000 if r["family"].startswith("ml4co") else 60000
        tot = (r["feat_p90_ms"] + (lm if lat else 0)) / B * 100
        lines.append(f"{FAM_NAME[r['family']]} & {r['n']} & {r['feat_med_ms']:.0f} & {r['feat_p90_ms']:.0f} & "
                     f"{r['feat_max_ms']:.0f} & {tot:.2f}\\% \\\\")
    cap = (f"Laya adds {lm:.0f}\\,ms per decision (median of {lat.get('n', 50)} decisions, one question, batch 1)." if lat
           else "Laya latency not yet measured.")
    lines += [r"\bottomrule", r"\end{tabular}", r"\caption{Policy overhead: static feature extraction "
              r"(HiGHS reader + NumPy, single thread) plus one Laya decision, as a share of the family's budget "
              r"(30\,s ML4CO, 60\,s MIPLIB and PGLib-UC), using the p90 extraction time. Extraction time is dominated by "
              r"parsing the MPS file, which the chosen solver repeats; a controller that handed its parsed model to the "
              r"solver would pay only the NumPy part. " + cap + r"}\label{tab:overhead}", r"\end{table}"]
    (GEN / "table_overhead.tex").write_text("\n".join(lines))
    return d


def bands(runs, key):
    """Appendix: spec SHORT/MEDIUM/HARD bands from the 300 s HiGHS/SCIP default screening, headroom per band."""
    p = ROOT / "datasets/runs300.parquet"
    if not p.exists():
        return None
    r3 = pd.read_parquet(p)
    solved = r3["status"].str.lower().str.contains("optimal")
    r3["t_solve"] = np.where(solved, r3["solve_wall"], np.inf)
    best = r3.pivot_table(index="name", columns="strategy", values="t_solve", aggfunc="min").min(axis=1)
    labels = ["trivial ($<$5\\,s)", "SHORT (5--30\\,s)", "MEDIUM (30--120\\,s)", "HARD (120--300\\,s)", "unsolved in 300\\,s"]
    band = pd.cut(best, [-1, 5, 30, 120, 300, np.inf], labels=labels)
    r0 = runs[(runs["set"] == "miplib") & (runs["seed"] == 0)]
    piv = r0.pivot_table(index="name", columns="strategy", values="pi@60")[S]
    lines = [r"\begin{table}[t]\centering\small", r"\begin{tabular}{lr" + "r" * len(S) + "rr}", r"\toprule",
             r"band & $n$ & " + " & ".join(S) + r" & VBS & headroom \\", r"\midrule"]
    rows = []
    for b in labels:
        names = band[band == b].index.intersection(piv.index)
        if len(names) == 0:
            continue
        p_ = piv.loc[names]
        m = p_.mean()
        vbs = p_.min(axis=1).mean()
        hr = 100 * (m.min() - vbs) / m.min() if m.min() > 0 else 0.0
        rows.append(dict(band=b, n=len(names), **m.to_dict(), vbs=vbs, headroom=hr))
        cells = [(r"\textbf{%.3f}" % m[s_]) if s_ == m.idxmin() else "%.3f" % m[s_] for s_ in S]
        lines.append(f"{b} & {len(names)} & " + " & ".join(cells) + f" & {vbs:.3f} & {hr:.0f}\\% \\\\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\caption{MIPLIB subset by the spec's difficulty bands (time to "
              r"optimality of the faster of HiGHS and SCIP defaults in a 300\,s run, 12 concurrent CPU runs). Entries: "
              r"mean $P(60)$ per strategy (bold = best), oracle, headroom over the band's best fixed strategy.}"
              r"\label{tab:bands}", r"\end{table}"]
    (GEN / "table_bands.tex").write_text("\n".join(lines))
    key["bands"] = rows
    return rows


def main():
    runs = pd.read_parquet(ROOT / "datasets/runs.parquet")
    key = {}
    bands(runs, key)
    overhead(key)
    port = portfolio_table(runs, key)
    selection_tables(key)
    variance(runs, key)
    contention(key)
    figures(runs, port)
    json.dump(key, open(ROOT / "datasets/key_numbers.json", "w"), indent=1, default=float)
    print(port[["T", "family", "n", "sbs", "sbs_cost", "vbs_cost", "headroom_pct"]].round(3).to_string(index=False))


if __name__ == "__main__":
    for d in (GEN, FIG, RES):
        d.mkdir(parents=True, exist_ok=True)
    FAM_NAME = {"miplib": "MIPLIB 2017", "ml4co_item_placement": "ML4CO item placement",
                "ml4co_load_balancing": "ML4CO load balancing", "pglib_uc": "PGLib-UC", "ALL": "All (pooled)"}
    POL_ORDER = ["random(expected)", "best-default-solver(train)", "best-fixed(train)", "rules", "lightgbm", "mlp",
                 "laya-zeroshot", "mip-laya", "oracle"]
    POL_NAME = {"random(expected)": "Random (expected)", "best-default-solver(train)": "Best default solver",
                "best-fixed(train)": "Best fixed strategy", "rules": "Hand rules", "lightgbm": "LightGBM", "mlp": "MLP",
                "laya-zeroshot": "Laya zero-shot", "mip-laya": "MIP-Laya (fine-tuned)", "oracle": "Oracle (VBS)"}
    main()
