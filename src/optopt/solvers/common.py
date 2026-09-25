"""Shared trace format for all solver wrappers.

A run produces a `Trace`: a list of events (time since solve start, primal bound, dual bound, nodes, ...) and a
final record. All objectives are reported in the problem's own sense; `sense` is +1 for minimisation, -1 for
maximisation, so `sense * obj` is always "smaller is better".
"""
from __future__ import annotations

import json
import math
import time
from dataclasses import asdict, dataclass, field

INF = float("inf")


@dataclass
class Event:
    t: float
    primal: float | None  # incumbent objective (None = no incumbent yet)
    dual: float | None  # best bound
    nodes: int | None = None
    lp_iters: int | None = None
    kind: str = "sample"  # "incumbent" | "sample" | "final"


@dataclass
class Trace:
    instance: str
    solver: str
    strategy: str
    seed: int
    budget: float
    sense: int = 1
    events: list[Event] = field(default_factory=list)
    status: str = ""
    read_time: float = 0.0
    solve_wall: float = 0.0
    final_primal: float | None = None
    final_dual: float | None = None
    nodes: int | None = None
    lp_iters: int | None = None
    incumbent_count: int = 0
    error: str | None = None
    extra: dict = field(default_factory=dict)

    def add(self, ev: Event, min_dt: float = 0.5):
        """Keep every incumbent; throttle plain samples to one per `min_dt` seconds."""
        if ev.kind == "incumbent":
            self.incumbent_count += 1
            self.events.append(ev)
            return
        last = next((e for e in reversed(self.events) if e.kind == "sample"), None)
        if last is None or ev.t - last.t >= min_dt:
            self.events.append(ev)

    def to_json(self) -> str:
        """Strict JSON: non-finite floats anywhere in the trace become null (never the non-standard Infinity/NaN)."""
        return json.dumps(_finite_tree(asdict(self)), allow_nan=False, default=_clean)


def _clean(x):
    if isinstance(x, float) and not math.isfinite(x):
        return None
    return str(x)


def finite(x, big=1e19):
    if x is None:
        return None
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(x) or abs(x) >= big:
        return None
    return x


class Clock:
    def __init__(self):
        self.t0 = time.perf_counter()

    def __call__(self) -> float:
        return time.perf_counter() - self.t0


def _finite_tree(o):
    if isinstance(o, float):
        return o if math.isfinite(o) else None
    if isinstance(o, dict):
        return {k: _finite_tree(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_finite_tree(v) for v in o]
    return o


def _store_solution(sol_out, names, values, tr):
    """Write the final incumbent (nonzeros, by variable name) for the independent checker; never fails the run."""
    if not sol_out:
        return
    try:
        import gzip
        import json as _json
        with gzip.open(sol_out, "wt") as fh:
            _json.dump({str(n): float(v) for n, v in zip(names, values) if v != 0.0}, fh)
        from optopt.paths import rel
        tr.extra["sol_file"] = rel(sol_out)
    except Exception as e:  # noqa: BLE001 — storing is a side product; record why it failed
        tr.extra["sol_store_error"] = f"{type(e).__name__}: {e}"[:200]
