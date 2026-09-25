"""Solution exchange between two concurrently running solvers (SCIP on a CPU core, cuOpt on the GPU).

Each side posts its new incumbents to a mailbox file and polls the other side's file. Vectors travel in SCIP's own
variable order: SCIP writes its variable names once (before its clock starts) and the partner, which parses the file
anyway, maps its own order onto SCIP's. SCIP therefore never parses the file twice or loads the cuOpt library — an
earlier version did, and that cost SCIP ~0.7 s of the pair's wall clock (found 2026-09-24 00:27).
Writes are atomic (write to a temp file, then os.replace), so a reader never sees a half-written vector.
"""
from __future__ import annotations

import os
import time

import numpy as np


class Mailbox:
    def __init__(self, d: str, me: str, other: str, send: bool = True, recv: bool = True, names=None):
        """names: this side's variable names, for a partner (non-SCIP) side; vectors are converted to/from SCIP order."""
        self.d, self.me, self.other, self.send, self.recv = d, me, other, send, recv
        self.names, self.perm = names, None
        self.seq, self.seen_mtime = 0, 0.0
        self.log = []  # (t_epoch, "post"/"recv", obj)
        self.received = []  # objective values injected from the partner (cuOpt side)

    def _path(self, who):
        return os.path.join(self.d, f"{who}.npz")

    def echo(self, obj: float) -> bool:
        """True if obj is a partner solution we injected ourselves — posting it back would only echo it."""
        return any(abs(obj - r) <= 1e-9 * max(1.0, abs(r)) for r in self.received)

    def write_order(self, names):
        """SCIP side: publish SCIP's variable order once."""
        tmp = os.path.join(self.d, ".order.tmp.npy")
        np.save(tmp, np.asarray(names))
        os.replace(tmp, os.path.join(self.d, "scip_order.npy"))

    def _perm(self):
        """Partner side: perm[k] = index in our order of SCIP's k-th variable (None until SCIP has published)."""
        if self.names is None:
            return None
        if self.perm is None:
            p = os.path.join(self.d, "scip_order.npy")
            if not os.path.exists(p):
                return None
            pos = {str(n): j for j, n in enumerate(self.names)}
            self.perm = np.array([pos[str(n)] for n in np.load(p)])
        return self.perm

    def post(self, x, obj: float):
        if not self.send:
            return
        if self.names is not None:  # partner side: convert to SCIP order
            perm = self._perm()
            if perm is None:
                return
            x = np.asarray(x, dtype=np.float64)[perm]
        self.seq += 1
        tmp = os.path.join(self.d, f".{self.me}.{self.seq}.tmp.npz")
        np.savez(tmp, x=np.asarray(x, dtype=np.float64), obj=float(obj), seq=self.seq, t=time.time())
        os.replace(tmp, self._path(self.me))
        self.log.append((time.time(), "post", float(obj)))

    def poll(self):
        """Return (x, obj) if the other side posted something new since the last poll, else None."""
        if not self.recv:
            return None
        p = self._path(self.other)
        try:
            mt = os.stat(p).st_mtime_ns
        except FileNotFoundError:
            return None
        if mt == self.seen_mtime:
            return None
        self.seen_mtime = mt
        try:
            with np.load(p) as z:
                x, obj = z["x"].copy(), float(z["obj"])
        except (OSError, ValueError, KeyError):  # replaced while reading — take it next poll
            self.seen_mtime = 0.0
            return None
        if self.names is not None:  # partner side: convert from SCIP order to ours
            perm = self._perm()
            if perm is None:
                return None
            y = np.zeros(len(self.names))
            y[perm] = x
            x = y
        self.log.append((time.time(), "recv", obj))
        return x, obj


