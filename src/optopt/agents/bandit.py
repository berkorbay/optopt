"""Online bandit agent (baseline, no training): UCB1 over SCIP's static settings, in the spirit of Hendel et al.'s
bandit-based adaptive behaviour in SCIP. Each interval is a pull of the current setting; reward = relative
reduction of the primal-dual gap during the interval + 0.5 if a new incumbent was found."""
import math

from .base import Agent

SETTINGS = ["D", "NOC", "PSC", "INF", "HOFF", "HEU"]


class BanditAgent(Agent):
    name = "bandit"

    def __init__(self, interval=10.0, c=0.5, start="D", prior_file=None):
        self.interval, self.c, self.start, self.prior_file = interval, c, start, prior_file
        self.instance = None

    def reset(self, budget):
        super().reset(budget)
        self.n = {s: 0 for s in SETTINGS}
        self.r = {s: 0.0 for s in SETTINGS}
        self.prev = None
        self.first = None
        if self.prior_file and self.instance:  # diagnosis prior: predicted setting starts with an optimistic pull
            import json
            from optopt.paths import resolve
            pred = json.load(open(resolve(self.prior_file))).get(self.instance)
            if pred in SETTINGS:
                self.n[pred], self.r[pred] = 1, 1.0
                self.first = pred

    def decide(self, st):
        if self.first is not None and st["setting"] != self.first and self.prev is None:
            self.prev = (st["pd_gap"], st["n_inc"], self.first)
            return ("set", self.first)
        if self.prev is not None:
            g0, inc0, s0 = self.prev
            rew = max(0.0, (g0 - st["pd_gap"]) / max(g0, 1e-9)) + (0.5 if st["n_inc"] > inc0 else 0.0)
            self.n[s0] += 1
            self.r[s0] += rew
        total = sum(self.n.values()) + 1
        untried = [s for s in SETTINGS if self.n[s] == 0]
        nxt = untried[0] if untried else max(
            SETTINGS, key=lambda s: self.r[s] / self.n[s] + self.c * math.sqrt(math.log(total) / self.n[s]))
        self.prev = (st["pd_gap"], st["n_inc"], nxt)
        return None if nxt == st["setting"] else ("set", nxt)
