"""Run identity: a hash of everything that defines a run, stored in its trace, so an existing trace is only reused
for the same configuration (review 2026-09-24: output names are instance/strategy/seed only)."""
import hashlib
import json

import optopt
from optopt.portfolio.strategies import STRATEGIES


def config_hash(instance: str, strategy: str, budget: float, seed: int) -> str:
    spec = {"instance": str(instance), "strategy": strategy, "definition": STRATEGIES[strategy],
            "budget": float(budget), "seed": int(seed)}
    return hashlib.sha256(json.dumps(spec, sort_keys=True, default=str).encode()).hexdigest()[:16]


def version() -> str:
    return optopt.__version__
