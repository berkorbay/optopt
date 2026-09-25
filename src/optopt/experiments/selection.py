"""Phases 1-2 (+ Laya from phase 4): per-instance strategy selection vs single best strategy vs oracle.

Terminology (algorithm-selection standard):
  SBS  single best strategy — lowest mean cost on the evaluation instances in hindsight (an upper bound for any
       fixed strategy); "best fixed (train)" is the fixed strategy a practitioner would pick from training data.
  VBS  virtual best = per-instance oracle.
  closed gap = (SBS - policy) / (SBS - VBS): the fraction of the oracle headroom a policy captures.

Cost = normalised primal integral P(T)/T in [0,1] (lower is better); T ∈ {10, 30, 60} where the budget allows.
Secondary: time-to-target (1 % primal gap), censored runs counted as 2T (PAR2), shifted geometric mean.

Folds: one pooled policy is trained across ALL families; each instance is tested exactly once.
  ML4CO: the official train split is always training data; valid instances are spread across the 5 folds.
  MIPLIB: 5-fold by instance. PGLib-UC: by base system (ca / ferc / rts_gmlc), so no system is on both sides.
A second scheme, leave-one-family-out (LOFO), tests transfer to an unseen family.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from optopt.paths import WORK as ROOT  # the workspace (cwd or $OPTOPT_HOME)
from optopt.analysis.metrics import shifted_geomean  # noqa: E402
from optopt.policies import rules  # noqa: E402
from optopt.portfolio.strategies import MILESTONE  # noqa: E402

S = MILESTONE
RNG = np.random.default_rng(20260923)


def family(row):
    return row["set"]


def assign_folds(inst: pd.DataFrame, k=5) -> pd.Series:
    fold = pd.Series(-1, index=inst.index)
    for fam, g in inst.groupby("set"):
        if fam.startswith("ml4co"):
            te = g[g["split"] == "valid"].index
            fold[te] = np.arange(len(te)) % k
        elif fam == "pglib_uc":
            systems = sorted(g["name"].str.split("__").str[0].unique())
            fold[g.index] = g["name"].str.split("__").str[0].map({s: i % k for i, s in enumerate(systems)})
        else:  # fixed per-family permutation, independent of call order
            perm = np.random.default_rng(1234).permutation(len(g))
            fold[g.index] = perm % k
    return fold


# ------------------------------------------------------------------ policies: (Xtr, Ctr, Xte, ftr, fte) -> idx
def p_best_fixed(Xtr, Ctr, Xte, **_):
    return np.full(len(Xte), int(np.argmin(Ctr.mean(0))))


def p_best_default(Xtr, Ctr, Xte, **_):
    d = [S.index(s) for s in ("H0", "S0", "C0")]
    return np.full(len(Xte), d[int(np.argmin(Ctr[:, d].mean(0)))])


def p_rules(Xtr, Ctr, Xte, fte=None, **_):
    return np.array([S.index(rules.choose(f)) for f in fte])


def p_lgbm(Xtr, Ctr, Xte, **_):
    import lightgbm as lgb
    preds = []
    for j in range(Ctr.shape[1]):
        m = lgb.LGBMRegressor(n_estimators=300, learning_rate=0.03, num_leaves=15, min_child_samples=5,
                              subsample=0.8, subsample_freq=1, colsample_bytree=0.8, verbose=-1, random_state=j, n_jobs=1)
        m.fit(Xtr, Ctr[:, j])
        preds.append(m.predict(Xte))
    return np.argmin(np.stack(preds, 1), 1)


def soft_targets(C, beta):
    z = -beta * C
    z -= z.max(1, keepdims=True)
    p = np.exp(z)
    return p / p.sum(1, keepdims=True)


def p_mlp(Xtr, Ctr, Xte, beta=20.0, epochs=400, seed=0, **_):
    import torch
    torch.set_num_threads(1)
    torch.manual_seed(seed)
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-6
    xt = torch.tensor((Xtr - mu) / sd, dtype=torch.float32)
    xe = torch.tensor((Xte - mu) / sd, dtype=torch.float32)
    yt = torch.tensor(soft_targets(Ctr, beta), dtype=torch.float32)
    net = torch.nn.Sequential(torch.nn.Linear(xt.shape[1], 64), torch.nn.ReLU(), torch.nn.Dropout(0.1),
                              torch.nn.Linear(64, 64), torch.nn.ReLU(), torch.nn.Linear(64, yt.shape[1]))
    opt = torch.optim.AdamW(net.parameters(), lr=3e-3, weight_decay=1e-2)
    for _ in range(epochs):
        net.train()
        opt.zero_grad()
        loss = -(yt * torch.log_softmax(net(xt), 1)).sum(1).mean()
        loss.backward()
        opt.step()
    net.eval()
    with torch.no_grad():
        return net(xe).argmax(1).numpy()


POLICIES = {"best-fixed(train)": p_best_fixed, "best-default-solver(train)": p_best_default, "rules": p_rules,
            "lightgbm": p_lgbm, "mlp": p_mlp}


# ------------------------------------------------------------------ evaluation
def load(T):
    runs = pd.read_parquet(ROOT / "datasets/runs.parquet")
    runs = runs[runs["seed"] == 0]
    col = f"pi@{T}"
    if col not in runs:
        return None
    runs = runs[runs["budget"] >= T]
    C = runs.pivot_table(index="instance", columns="strategy", values=col, aggfunc="first")
    TT = runs.pivot_table(index="instance", columns="strategy", values=f"t_target@{T}", aggfunc="first")
    C = C.dropna()
    C = C[[s for s in S if s in C.columns]]
    if C.shape[1] < len(S):
        return None
    feats = pd.read_parquet(ROOT / "datasets/features.parquet").set_index("instance")
    inst = feats.loc[feats.index.intersection(C.index)].copy()
    C, TT = C.loc[inst.index], TT.loc[inst.index][S]
    meta = runs.drop_duplicates("instance").set_index("instance").loc[inst.index, ["set", "name"]]
    inst["set"], inst["name"] = meta["set"], meta["name"]
    return inst, C, TT


def feature_matrix(inst):
    cols = [c for c in inst.columns if c not in ("set", "split", "name", "feat_time") and inst[c].dtype.kind in "fi"]
    return inst[cols].to_numpy(float), cols


def run_scheme(inst, C, scheme, extra_preds=None):
    X, cols = feature_matrix(inst)
    Cm = C.to_numpy()
    fdicts = inst[cols].to_dict("records")
    if scheme == "pooled":
        fold = assign_folds(inst).to_numpy()
        splits = [(np.where(fold != k)[0], np.where(fold == k)[0]) for k in range(5)]
    else:  # LOFO
        fams = inst["set"].to_numpy()
        splits = [(np.where(fams != f)[0], np.where(fams == f)[0]) for f in sorted(set(fams))]
    choice = {p: np.full(len(inst), -1) for p in POLICIES}
    for tr, te in splits:
        if len(te) == 0 or len(tr) == 0:
            continue
        for name, fn in POLICIES.items():
            choice[name][te] = fn(X[tr], Cm[tr], X[te], fte=[fdicts[i] for i in te])
    choice["oracle"] = Cm.argmin(1)
    choice["random(expected)"] = None
    if extra_preds:
        for name, pred in extra_preds.items():
            idx = inst.index.map(lambda i: pred.get(i, -1)).to_numpy()
            if (idx >= 0).any():
                choice[name] = idx
    tested = np.zeros(len(inst), bool)
    for _, te in splits:
        tested[te] = True
    return choice, tested


def cost_of(choice, Cm):
    if choice is None:
        return Cm.mean(1)
    out = np.full(len(Cm), np.nan)
    ok = choice >= 0
    out[ok] = Cm[np.where(ok)[0], choice[ok]]
    return out


def paired_selectors(Cm, a, b, tested, n_boot=2000, seed=0):
    """Fine-tuned Laya vs LightGBM on the same test instances (review 2026-09-24): paired Wilcoxon on per-instance costs
    and a bootstrap interval of the difference in closed gap, predictions held fixed (no retraining)."""
    from scipy import stats
    ca, cb = cost_of(a, Cm), cost_of(b, Cm)
    m = tested & ~np.isnan(ca) & ~np.isnan(cb)
    ca, cb, C = ca[m], cb[m], Cm[m]
    sbs_j = int(np.argmin(C.mean(0)))

    def gap(ix):
        s, v = C[ix, sbs_j].mean(), C[ix].min(1).mean()
        return ((s - ca[ix].mean()) - (s - cb[ix].mean())) / (s - v) if s - v > 1e-9 else np.nan
    rng = np.random.default_rng(seed)
    boot = [gap(rng.integers(0, len(ca), len(ca))) for _ in range(n_boot)]
    d = cb - ca
    return {"n": int(m.sum()), "closed_gap_diff": float(gap(np.arange(len(ca)))),
            "ci95": [float(x) for x in np.nanpercentile(boot, [2.5, 97.5])],
            "p_wilcoxon": float(stats.wilcoxon(d).pvalue) if (d != 0).any() else 1.0,
            "laya_better/worse": [int((d > 1e-12).sum()), int((d < -1e-12).sum())]}


def summarise(inst, C, TT, choice, tested, T, label):
    Cm, TTm = C.to_numpy(), TT.to_numpy()
    rows = []
    for fam in ["ALL"] + sorted(inst["set"].unique()):
        m = tested & ((inst["set"] == fam).to_numpy() if fam != "ALL" else True)
        if m.sum() == 0:
            continue
        sbs_j = int(np.argmin(Cm[m].mean(0)))
        sbs = Cm[m, sbs_j].mean()
        vbs = Cm[m].min(1).mean()
        for pol, ch in choice.items():
            c = cost_of(ch, Cm)[m]
            valid = ~np.isnan(c)
            if valid.sum() == 0:
                continue
            if ch is None:
                tt = np.nanmean(np.where(np.isinf(TTm[m]), 2 * T, TTm[m]), 1)
            else:
                idx = np.where(m)[0]
                tt = np.array([TTm[i, ch[i]] if ch[i] >= 0 else np.nan for i in idx])
                tt = np.where(np.isinf(tt), 2 * T, tt)
            # bootstrap CI of closed gap
            n = valid.sum()
            cg = []
            for _ in range(500):
                b = RNG.integers(0, n, n)
                cc, sb, vb = c[valid][b].mean(), Cm[m][valid][b][:, sbs_j].mean(), Cm[m][valid][b].min(1).mean()
                cg.append((sb - cc) / (sb - vb) if sb - vb > 1e-9 else np.nan)
            rows.append(dict(scheme=label, T=T, family=fam, policy=pol, n=int(n), cost=float(np.nanmean(c)),
                             sbs=S[sbs_j], sbs_cost=float(sbs), vbs_cost=float(vbs),
                             headroom_pct=float(100 * (sbs - vbs) / sbs) if sbs > 0 else 0.0,
                             closed_gap=float((sbs - np.nanmean(c)) / (sbs - vbs)) if sbs - vbs > 1e-9 else float("nan"),
                             closed_gap_lo=float(np.nanpercentile(cg, 2.5)) if len(cg) else np.nan,
                             closed_gap_hi=float(np.nanpercentile(cg, 97.5)) if len(cg) else np.nan,
                             ttt_sgm=float(shifted_geomean([x for x in tt if not np.isnan(x)])),
                             reached_target=float(np.mean(tt < T)),
                             choice_dist=json.dumps({S[k]: int((ch[m] == k).sum()) for k in range(len(S))}) if ch is not None else ""))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--budgets", default="10,30,60")
    ap.add_argument("--laya", nargs="*", default=[], help="prediction json files {name: {instance: idx}}")
    a = ap.parse_args()
    extra = {}
    for f in a.laya:
        extra.update(json.load(open(f)))
    all_rows, paired = [], {}
    for T in [int(x) for x in a.budgets.split(",")]:
        d = load(T)
        if d is None:
            continue
        inst, C, TT = d
        for scheme in ("pooled", "lofo"):
            ex = {k.split("|")[1]: v for k, v in extra.items() if k.startswith(f"{scheme}@{T}|")}
            choice, tested = run_scheme(inst, C, scheme, ex)
            all_rows += summarise(inst, C, TT, choice, tested, T, scheme)
            if "mip-laya" in choice and "lightgbm" in choice:
                paired[f"{scheme}@{T}"] = paired_selectors(C.to_numpy(), choice["mip-laya"], choice["lightgbm"], tested)
    (ROOT / "datasets/selection_paired.json").write_text(json.dumps(paired, indent=1))
    df = pd.DataFrame(all_rows)
    df.to_csv(ROOT / "datasets/selection_results.csv", index=False)
    show = df[df["family"] == "ALL"][["scheme", "T", "policy", "n", "cost", "closed_gap", "closed_gap_lo", "closed_gap_hi",
                                     "headroom_pct", "ttt_sgm", "reached_target"]]
    with pd.option_context("display.width", 200, "display.max_rows", 200):
        print(show.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
