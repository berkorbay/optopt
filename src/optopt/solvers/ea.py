"""A small evolutionary algorithm that runs beside SCIP and exchanges solutions with it (solvers/xchg.py).

Population rule (Berk, 2026-09-23): most of the population is feasible; up to a fraction `rho` may be INFEASIBLE, but
only individuals whose objective beats the best feasible one ("super-optimal"). Infeasible survivors are pruned by
increasing infeasibility: the closer to feasible, the more likely to survive (rank-based survival probability).

Individuals are full vectors in the canonical (MPS) variable order. Offspring = uniform crossover on the integer
variables + mutation, then repair:
  - integer part: greedy moves that reduce total row violation (bounded number of steps);
  - continuous part (mixed problems): an LP with the integer variables fixed (HiGHS), which also gives the exact
    objective of the repaired point.
Feasible improvements are posted to SCIP, which checks every solution itself (trySol) before accepting it.
SCIP's incumbents are pulled into the population as they appear. Everything runs on the wall clock of the pair.
"""
from __future__ import annotations

import time

import numpy as np
import scipy.sparse as sp

TOL = 1e-6


class Problem:
    def __init__(self, path: str):
        from cuopt.linear_programming import ParseMps
        from optopt.paths import resolve  # instance paths are repository-relative
        dm = ParseMps(str(resolve(path)))
        self.names = [str(v) for v in dm.get_variable_names()]
        n = len(self.names)
        self.A = sp.csr_matrix((dm.get_constraint_matrix_values(), dm.get_constraint_matrix_indices(),
                                dm.get_constraint_matrix_offsets()), shape=(len(dm.get_constraint_lower_bounds()), n))
        self.AT = self.A.T.tocsr()
        self.rl = np.asarray(dm.get_constraint_lower_bounds(), float)
        self.ru = np.asarray(dm.get_constraint_upper_bounds(), float)
        self.lb = np.asarray(dm.get_variable_lower_bounds(), float)
        self.ub = np.asarray(dm.get_variable_upper_bounds(), float)
        self.isint = np.asarray([t != "C" for t in dm.get_variable_types()])
        self.s = -1.0 if dm.get_sense() else 1.0  # minimise s * c.x
        self.c = np.asarray(dm.get_objective_coefficients(), float)
        self.off = float(dm.get_objective_offset())
        rn = np.sqrt(np.asarray(self.A.multiply(self.A).sum(1)).ravel())
        self.rn = np.where(rn > 0, rn, 1.0)
        self.n, self.m = n, self.A.shape[0]
        self.ints = np.flatnonzero(self.isint)
        self.conts = np.flatnonzero(~self.isint)
        self._lp = None

    def obj(self, x):  # user-sense objective
        return float(self.c @ x + self.off)

    def viol(self, x, act=None):
        act = self.A @ x if act is None else act
        r = np.maximum(self.rl - act, 0) + np.maximum(act - self.ru, 0)
        return float((r / self.rn).sum() + (np.maximum(self.lb - x, 0) + np.maximum(x - self.ub, 0)).sum())

    def is_feasible(self, x, tol=1e-6):
        """Per-row check in SCIP's style: every row and bound within tol relative to its magnitude, integers integral.
        (The first version compared the SUM of normalised violations with tol * rows — far too loose on large
        instances: 26 of 176 posts on 2026-09-24 claimed objectives better than the known optimum.)"""
        act = self.A @ x
        if np.any(act < self.rl - tol * np.maximum(1.0, np.abs(self.rl))) or \
                np.any(act > self.ru + tol * np.maximum(1.0, np.abs(self.ru))):
            return False
        if np.any(x < self.lb - tol * np.maximum(1.0, np.abs(self.lb))) or \
                np.any(x > self.ub + tol * np.maximum(1.0, np.abs(self.ub))):
            return False
        xi = x[self.ints]
        return bool(np.all(np.abs(xi - np.round(xi)) <= tol))

    def repair_int(self, x, rng, steps=60):
        """Greedy: pick a violated row, move the integer variable in it that most reduces total violation."""
        act = self.A @ x
        for _ in range(steps):
            r = np.maximum(self.rl - act, 0) + np.maximum(act - self.ru, 0)
            bad = np.flatnonzero(r > TOL)
            if len(bad) == 0:
                break
            i = bad[rng.integers(len(bad))]
            lo, hi = self.A.indptr[i], self.A.indptr[i + 1]
            cols, vals = self.A.indices[lo:hi], self.A.data[lo:hi]
            need = 1.0 if act[i] < self.rl[i] - TOL else -1.0
            best, bj, bd = None, None, 0.0
            for j, a in zip(cols, vals):
                if not self.isint[j]:
                    continue
                d = need * np.sign(a)
                nv = x[j] + d
                if nv < self.lb[j] - TOL or nv > self.ub[j] + TOL:
                    continue
                clo, chi = self.AT.indptr[j], self.AT.indptr[j + 1]
                rows, cv = self.AT.indices[clo:chi], self.AT.data[clo:chi]
                old = np.maximum(self.rl[rows] - act[rows], 0) + np.maximum(act[rows] - self.ru[rows], 0)
                na = act[rows] + cv * d
                new = np.maximum(self.rl[rows] - na, 0) + np.maximum(na - self.ru[rows], 0)
                gain = ((old - new) / self.rn[rows]).sum() - 1e-9 * self.s * self.c[j] * d
                if best is None or gain > best:
                    best, bj, bd = gain, j, d
            if bj is None or best <= 0:
                continue
            clo, chi = self.AT.indptr[bj], self.AT.indptr[bj + 1]
            act[self.AT.indices[clo:chi]] += self.AT.data[clo:chi] * bd
            x[bj] += bd
        return x

    def repair_lp(self, x):
        """Fix integers, solve the LP over the continuous variables. Returns x (continuous part optimal) or None."""
        if len(self.conts) == 0:
            return x, True
        import highspy
        if self._lp is None:
            h = highspy.Highs()
            h.setOptionValue("output_flag", False)
            h.setOptionValue("threads", 1)
            lp = highspy.HighsLp()
            lp.num_col_, lp.num_row_ = self.n, self.m
            lp.col_cost_ = self.s * self.c
            lp.col_lower_, lp.col_upper_ = self.lb.copy(), self.ub.copy()
            lp.row_lower_, lp.row_upper_ = self.rl, self.ru
            csc = self.A.tocsc()
            lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
            lp.a_matrix_.start_, lp.a_matrix_.index_, lp.a_matrix_.value_ = csc.indptr, csc.indices, csc.data
            h.passModel(lp)
            self._lp = h
        h = self._lp
        xi = np.round(x[self.ints])
        h.changeColsBounds(len(self.ints), self.ints.astype(np.int32), xi, xi)
        h.setOptionValue("time_limit", 2.0)
        h.run()
        st = h.getModelStatus()
        if st == highspy.HighsModelStatus.kOptimal:
            return np.asarray(h.getSolution().col_value, float), True
        if st != highspy.HighsModelStatus.kInfeasible:
            return None, False
        # LP-infeasible integer assignment: take the least-infeasible continuous completion, so the child gets an
        # honest (infeasibility, objective) pair for the population rule
        h.feasibilityRelaxation(1.0, 1.0, 1.0)
        y = np.asarray(h.getSolution().col_value, float)
        h.clearSolver()
        return (y, False) if len(y) == self.n else (None, False)


def run(path: str, budget: float, xchg, seed: int = 0, rho: float = 0.2, pop: int = 40, tr_extra: dict | None = None):
    """Loop until the budget elapses (wall clock from call). Posts feasible improvements via xchg."""
    t0 = time.time()
    rng = np.random.default_rng(seed)
    P = Problem(path)
    xchg.names = P.names
    feas, infeas = [], []  # lists of (key, x): feas key = s*obj ; infeas key = viol (with s*obj stored)
    best_posted = np.inf
    stats = dict(gens=0, offspring=0, feas_new=0, posted=0, infeas_kept_max=0, lp_repairs=0, recv=0, read_s=time.time() - t0)

    def add_feasible(x, f, own=True):
        nonlocal best_posted
        k = P.s * f
        if any(abs(k - kk) <= 1e-9 * max(1, abs(k)) for kk, _ in feas):
            return
        feas.append((k, x))
        feas.sort(key=lambda z: z[0])
        del feas[max(1, int(round(pop * (1 - rho)))):]
        if k < best_posted - 1e-9 * max(1, abs(k)):
            best_posted = k
            if own:  # never echo SCIP's own solutions back to it
                xchg.post(x, f)
                stats["posted"] += 1

    def survive_infeasible():
        """Keep up to rho*pop super-optimal infeasible individuals; closer to feasible = more likely to survive."""
        if not feas:
            return
        bf = feas[0][0]
        cand = [z for z in infeas if z[2] < bf]  # (viol, x, s*obj)
        cand.sort(key=lambda z: z[0])
        cap = int(round(rho * pop))
        if len(cand) > cap:
            ranks = np.arange(len(cand))
            p = np.exp(-ranks / max(1.0, cap / 2))  # survival probability falls with the infeasibility rank
            keep = rng.random(len(cand)) < p / p.max()
            keep[:1] = True
            cand = [c for c, k in zip(cand, keep) if k][:cap]
        infeas[:] = cand
        stats["infeas_kept_max"] = max(stats["infeas_kept_max"], len(infeas))

    while time.time() - t0 < budget:
        got = xchg.poll()
        if got is not None:
            x, f = got
            add_feasible(np.asarray(x, float), f, own=False)
            stats["recv"] += 1
        if not feas:
            time.sleep(0.05)
            continue
        stats["gens"] += 1
        parents = [x for _, x in feas] + [x for _, x, _ in infeas]
        for _ in range(8):
            if time.time() - t0 >= budget:
                break
            a = parents[rng.integers(len(parents))]
            b = parents[rng.integers(len(parents))]
            child = a.copy()
            mask = rng.random(len(P.ints)) < 0.5
            child[P.ints[mask]] = b[P.ints[mask]]
            k = max(1, int(0.01 * len(P.ints)))
            mj = P.ints[rng.integers(len(P.ints), size=k)]
            child[mj] = np.clip(child[mj] + rng.choice([-1.0, 1.0], size=k), P.lb[mj], P.ub[mj])
            child = P.repair_int(child, rng)
            stats["offspring"] += 1
            if len(P.conts):  # mixed problem: integers are the genes, the LP decodes the continuous part
                y, ok = P.repair_lp(child)
                stats["lp_repairs"] += 1
                if y is not None:
                    child = y
                    if not ok:
                        stats["lp_relaxed"] = stats.get("lp_relaxed", 0) + 1
            v = P.viol(child)
            f = P.obj(child)
            if P.is_feasible(child):
                if P.s * f < feas[0][0] + 1e-12 or len(feas) < pop * (1 - rho):
                    stats["feas_new"] += 1
                    add_feasible(child, f)
            else:
                infeas.append((v, child, P.s * f))
                stats["infeas_seen"] = stats.get("infeas_seen", 0) + 1
                if P.s * f < feas[0][0]:
                    stats["superopt_seen"] = stats.get("superopt_seen", 0) + 1
        survive_infeasible()
    if tr_extra is not None:
        tr_extra.update({"ea": stats})
    return stats
