"""Hand-written agent from today's component results (B1/B2): start with separation off (best static on P);
if no incumbent by 10 s, restart once; if the bound has not moved for 2 intervals after 30 s, switch to inference
branching (best static on PDI)."""
from .base import Agent


class RulesAgent(Agent):
    name = "rules"

    def __init__(self, interval=5.0):
        self.interval = interval

    def reset(self, budget):
        super().reset(budget)
        self.restarted = False
        self.duals = []

    def decide(self, st):
        self.duals.append(st["dual"])
        if st["setting"] == "D" and st["t"] < self.interval * 1.5:
            return ("set", "NOC")
        if not self.restarted and st["n_inc"] == 0 and st["t"] >= 10:
            self.restarted = True
            return ("restart",)
        if st["t"] >= 30 and len(self.duals) >= 3 and self.duals[-1] == self.duals[-3] and st["setting"] != "INF":
            return ("set", "INF")
        return None
