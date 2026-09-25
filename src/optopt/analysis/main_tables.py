"""Compact main-body tables of the paper (headroom, selection, agent, parallel) from datasets/."""
import json
from pathlib import Path
import pandas as pd
from optopt.paths import WORK as ROOT  # the workspace (cwd or $OPTOPT_HOME)
G = ROOT / "paper/generated"


if __name__ == "__main__":
    names = {"miplib": "MIPLIB 2017", "ml4co_item_placement": "ML4CO item placement", "ml4co_load_balancing": "ML4CO load balancing",
             "pglib_uc": "PGLib-UC", "ALL": "Pooled"}
    port = pd.read_csv(ROOT / "datasets/portfolio_table.csv")
    L = [r"\begin{table}[t]\centering\small", r"\begin{tabular}{lrrlrrrr}", r"\toprule",
         r" & \multicolumn{2}{c}{instances} & & & \multicolumn{2}{c}{oracle headroom} \\",
         r"family & all & some sol. & budget & best fixed & $P$ (all) & all & some sol. \\", r"\midrule"]
    for fam, T in (("miplib", 60), ("ml4co_item_placement", 30), ("ml4co_load_balancing", 30), ("pglib_uc", 60), ("ALL", 30)):
        r = port[(port.family == fam) & (port["T"] == T)].iloc[0]
        L.append(f"{names[fam]} & {int(r.n_all)} & {int(r.n)} & {T}\\,s & {r.sbs} & {r.sbs_cost_all:.3f} & "
                 f"{r.headroom_all_pct:.0f}\\% & {r.headroom_pct:.0f}\\% \\\\")
    L += [r"\bottomrule", r"\end{tabular}", r"\caption{Headroom across HiGHS, SCIP and cuOpt (six strategies, Table~\ref{tab:portfolio}): normalised primal integral $P$ of the best fixed strategy and the improvement a per-instance oracle would achieve, one seed. \emph{All}: every attempted instance, with $P=1$ for every strategy where none finds a solution (23 PGLib-UC cases, all from the FERC system). \emph{Some sol.}: instances where at least one strategy finds a solution; the selectors of Section~\ref{sec:predict} are trained and evaluated on this cohort. On a five-seed MIPLIB subset about 80\,\% of the single-seed headroom repeats (Appendix~\ref{app:trackA}).}\label{tab:headroom}", r"\end{table}"]
    (G / "main_headroom.tex").write_text("\n".join(L))
    sel = pd.read_csv(ROOT / "datasets/selection_results.csv")
    pols = [("best-fixed(train)", "Best fixed, chosen on training data"), ("lightgbm", "LightGBM"), ("mlp", "MLP"), ("laya-zeroshot", "Laya, zero-shot"),
            ("mip-laya", "Laya, fine-tuned"), ("oracle", "Oracle")]
    L = [r"\begin{table}[t]\centering\small", r"\begin{tabular}{lrrrr}", r"\toprule", r"& \multicolumn{2}{c}{seen families (pooled)} & \multicolumn{2}{c}{unseen family (LOFO)} \\",
         r"policy & 10\,s & 30\,s & 10\,s & 30\,s \\", r"\midrule"]
    for p, nm in pols:
        cells = []
        for sch in ("pooled", "lofo"):
            for T in (10, 30):
                x = sel[(sel.scheme == sch) & (sel["T"] == T) & (sel.family == "ALL") & (sel.policy == p)]
                cells.append("--" if x.empty else f"{x.closed_gap.iloc[0]:+.2f}")
        L.append(f"{nm} & " + " & ".join(cells) + r" \\")
    _pos = sel[(sel.family == "ALL") & sel.scheme.isin(["pooled", "lofo"]) & sel["T"].isin([10, 30]) & (sel.closed_gap > 0)
               & (sel.closed_gap_lo > 0) & ~sel.policy.isin(["oracle", "best-fixed(train)"])]
    _names = {"lightgbm": "LightGBM", "mlp": "MLP", "mip-laya": "the fine-tuned Laya", "laya-zeroshot": "zero-shot Laya"}
    excl = ("Positive closed gaps whose 95\\,\\% interval excludes zero: " + "; ".join(
        f"{_names.get(r.policy, r.policy)}, {'seen' if r.scheme == 'pooled' else 'unseen'} families, {r.T}\\,s "
        f"([{r.closed_gap_lo:.2f}, {r.closed_gap_hi:.2f}])" for r in _pos.itertuples())) if len(_pos) else \
        "No positive closed gap has a 95\\,\\% interval that excludes zero"
    L += [r"\bottomrule", r"\end{tabular}", r"\caption{Selecting a strategy before the solve from 62 static instance features: closed gap between the hindsight single best strategy (0) and the oracle (1); one model for all families, 163 instances with grouped cross-validation (seen families) and 313 with leave-one-family-out (unseen family), all from the cohort where some strategy finds a solution (one FERC unit-commitment case). The hindsight single best defines 0; the best fixed strategy chosen on the training folds can score below it. Intervals resample test instances with the fitted models held fixed; they do not cover retraining or other folds. " + excl + r"; intervals, per-family results and time-to-target are in Appendix~\ref{app:trackA}.}\label{tab:selection}", r"\end{table}"]
    (G / "main_selection.tex").write_text("\n".join(L))
    e1 = json.load(open(ROOT / "datasets/pilot_e.json"))
    e2 = json.load(open(ROOT / "datasets/pilot_e2_static.json"))
    f = lambda v: f"{v:.3f}"  # noqa: E731
    L = [r"\begin{table}[t]\centering\small", r"\setlength{\tabcolsep}{4pt}\begin{tabular}{lrrrrrr}", r"\toprule",
         r" & & \multicolumn{2}{c}{agents} & \multicolumn{2}{c}{fixed from $t=0$} & 2 copies \\ instances $\times$ seeds & default & bandit & rules & aggr.\ heur. & sep.\ off & (2 cores) \\", r"\midrule"]
    m = e1["P@120|ML4CO"]["means"]
    L.append(f"ML4CO, set 1 ($20\\times2$) & {f(m['A:default'])} & {f(m['A:bandit'])} & {f(m['A:rules'])} & -- & -- & {f(m['2x default (2 cores)'])} \\\\")
    m = e1["P@120|MIPLIB"]["means"]
    L.append(f"MIPLIB ($15\\times2$) & {f(m['A:default'])} & {f(m['A:bandit'])} & {f(m['A:rules'])} & -- & -- & {f(m['2x default (2 cores)'])} \\\\")
    for fam, lab in (("item", "ML4CO set 2, item placement ($15\\times2$)"), ("load", "ML4CO set 2, load balancing ($15\\times2$)")):
        m = e2[f"P@120|{fam}"]["means"]
        L.append(f"{lab} & {f(m['A:default'])} & {f(m['A:bandit5'])} & -- & {f(m['C:HEU'])} & {f(m['C:NOC'])} & -- \\\\")
    L += [r"\bottomrule", r"\end{tabular}", r"\caption{Agent in the loop: primal integral $P(120)$ (lower is better) of agents that start from SCIP's defaults in a fixed slice (one Cortex-X925 core, 9\,GiB, 120\,s wall clock including every agent decision). ML4CO instances are held out, from the validation split. Set 1: bandit deciding every 10\,s; set 2: every 5\,s. Significance tests in Appendix~\ref{app:agents}.}\label{tab:agent}", r"\end{table}"]
    (G / "main_agent.tex").write_text("\n".join(L))
    seeds = json.load(open(ROOT / "datasets/b2_seeds_analysis.json"))
    pairs = pd.read_csv(ROOT / "datasets/pairs.csv")
    S = ["H0", "H1", "S0", "S1", "C0", "C1"]
    sbs = pairs[S].mean().min()
    pair = pairs["H1||C0"].mean()
    orc = pairs[S].min(axis=1).mean()
    L = [r"\begin{table}[t]\centering\small", r"\begin{tabular}{llrr}", r"\toprule", r"setting & portfolio & $P$ gain & PDI gain \\", r"\midrule",
         f"HiGHS/SCIP/cuOpt study, pooled ({len(pairs)} inst.) & HiGHS (1 thread) $\\|$ cuOpt (GPU) & {100 * (sbs - pair) / sbs:.0f}\\,\\% & -- \\\\"]
    for k in ("2", "3", "5"):
        L.append(f"SCIP, 20 MIPLIB inst., 120\\,s & {k} copies of the best setting & {seeds['P']['parallel'][k]['gain_pct']:.0f}\\% & {seeds['PDI']['parallel'][k]['gain_pct']:.0f}\\% \\\\")
    L += [r"\bottomrule", r"\end{tabular}", rf"\caption{{Parallel portfolios, computed exactly from recorded trajectories: best incumbent (and bound) of runs executed side by side, against the best single strategy. HiGHS$\|$cuOpt captures {100 * (sbs - pair) / (sbs - orc):.0f}\,\% of the cross-solver oracle headroom; SCIP copies differ only in the random seed.}}\label{{tab:parallel}}", r"\end{table}"]
    (G / "main_parallel.tex").write_text("\n".join(L))
    print("pair share of headroom", round(100 * (sbs - pair) / (sbs - orc), 1), "pair gain", round(100 * (sbs - pair) / sbs, 1))
