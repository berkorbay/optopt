"""LLM agents for the main experiment (D-004), with and without Laya as a tool.

The agent is called from inside SCIP (solvers/scip.py, event handler) — first right after the solve starts, then every
`interval` seconds — and every second it spends waiting for the model is charged to the run's wall-clock budget.
Backends:
  local  : Ornith-1.5-35B-A3B (NVFP4, vLLM on 127.0.0.1:8094, thinking off) — the box's own chat model
  gpt    : OpenAI GPT-6 Luna, reasoning effort low, ChatGPT Plus through agents/gpt_bridge.py (127.0.0.1:8112)
Laya as a tool: at the first decision the agent asks the Laya service (agents/laya_service.py, fine-tuned on 60 ML4CO
training instances) for the probability that each setting is best, and shows the answer to the LLM.
The prompt carries only public-instance features (the same 62-feature text Laya and LightGBM see) and solver state.
"""
import json
import re
import time
import urllib.request
from pathlib import Path

from .base import Agent

from optopt.paths import WORK as ROOT  # the workspace (cwd or $OPTOPT_HOME)
SETTINGS = {
    "D": "SCIP default settings",
    "NOC": "cutting-plane separation off",
    "PSC": "pseudo-cost branching",
    "INF": "inference branching",
    "HOFF": "primal heuristics off",
    "HEU": "aggressive primal heuristics",
}
SYSTEM = (
    "You control the mixed-integer programming solver SCIP while it runs. Goal: find good feasible solutions as early "
    "as possible within the wall-clock budget. The score is the primal integral: the average relative gap between the "
    "current best solution and the best known solution over the budget (1 before the first solution); lower is better. "
    "Every second you spend deciding is charged to the budget. At each call choose exactly one action and reply with "
    'JSON only, no other text: {"action": "keep"} or {"action": "set:<SETTING>"} or {"action": "restart"}. '
    "Settings: " + "; ".join(f"{k} = {v}" for k, v in SETTINGS.items()) + ". Changing the setting keeps the search tree; "
    "restart discards the tree but keeps the solutions found so far.")


def _post(url, body, timeout):
    req = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())


def _fmt(x):
    return "none" if x is None else f"{x:.6g}"


class LLMAgent(Agent):
    first_at = 0.0

    def __init__(self, backend="local", laya_tool=False, interval=20.0, first_only=False):
        """first_only: make the first decision and never call the model again (separates the opening move from
        later steering — timing-matched control requested by the 2026-09-24 review)."""
        self.backend, self.laya_tool, self.interval, self.first_only = backend, laya_tool, interval, first_only
        if first_only:
            self.interval = 1e9
        self.name = f"llm-{backend}" + ("+laya" if laya_tool else "")
        self.instance, self.desc, self.laya_probs = None, None, None
        self.note = None
        if backend == "local":
            m = json.loads(urllib.request.urlopen("http://127.0.0.1:8094/v1/models", timeout=10).read())
            self.model = m["data"][0]["id"]
        # instance description from precomputed features (same input as Laya / LightGBM), loaded before the clock
        import pandas as pd

        from optopt.analysis.build_runs import stem
        from optopt.policies.laya import state_text
        self._F = pd.read_parquet(ROOT / "datasets/features.parquet").assign(
            name=lambda d: d["instance"].map(stem)).set_index("name")
        self._state_text = state_text

    def reset(self, budget):
        super().reset(budget)
        self.laya_probs = None
        self.desc = self._state_text(self._F.loc[self.instance].to_dict(), budget) if self.instance in self._F.index else "unknown"

    def _ask(self, user, timeout):
        if self.backend == "local":
            r = _post("http://127.0.0.1:8094/v1/chat/completions",
                      {"model": self.model, "temperature": 0, "max_tokens": 60,
                       "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]}, timeout)
            return r["choices"][0]["message"]["content"] or ""
        r = _post("http://127.0.0.1:8112/ask", {"system": SYSTEM, "user": user, "effort": "low", "timeout": timeout},
                  timeout + 5)
        if "error" in r:
            raise RuntimeError(r["error"])
        return r["text"]

    def decide(self, st):
        remaining = st["budget"] - st["t"]
        if remaining < 3:
            return None
        if self.laya_tool and self.laya_probs is None:
            try:
                self.laya_probs = _post("http://127.0.0.1:8111/choose", {"instance": self.instance, "budget": st["budget"]},
                                        5)["probs"]
            except Exception as e:  # noqa: BLE001 — the tool failing is part of the run
                self.laya_probs = {"error": str(e)[:80]}
        hist = "; ".join(f"t={h[0]:.0f}s {h[1] or 'keep'}" for h in st["history"][-6:]) or "none yet"
        user = (f"Problem: {self.desc}\nTime used {st['t']:.0f} of {st['budget']:.0f} s. Current setting: {st['setting']}. "
                f"Solutions found: {st['n_inc']}" + (f" (last {st['inc_age']:.0f} s ago)" if st["n_inc"] else "") +
                f". Best solution value {_fmt(st['primal'])}, dual bound {_fmt(st['dual'])}, primal-dual gap "
                f"{100 * st['pd_gap']:.2f}%. Nodes {st['nodes']} ({st['node_rate']:.0f} per s recently). "
                f"Your earlier decisions: {hist}.")
        if self.laya_tool and self.laya_probs and "error" not in self.laya_probs:
            user += (" Tool result — Laya, a small model trained on 60 similar instances, estimates the probability that "
                     "each setting is best for this problem: " +
                     ", ".join(f"{k} {v:.2f}" for k, v in sorted(self.laya_probs.items(), key=lambda kv: -kv[1])) + ".")
        try:
            txt = self._ask(user, timeout=max(2.0, min(30.0, remaining - 2)))
        except Exception as e:  # noqa: BLE001
            self.note = f"error: {str(e)[:120]}"
            return None
        self.note = txt[:200]
        m = re.search(r"\{.*?\}", txt, re.S)
        try:
            a = json.loads(m.group(0))["action"] if m else ""
        except (json.JSONDecodeError, KeyError, TypeError):
            a = ""
        a = str(a).strip()
        if a.lower() == "restart":
            return ("restart",)
        # accept "set:HEU", "set HEU" and a bare "HEU" (the local model sometimes drops the prefix; the intent is clear)
        m2 = re.fullmatch(r"(?:set\s*[:_\-\s]\s*)?([A-Za-z]+)", a)
        s = m2.group(1).upper() if m2 else ""
        if s in SETTINGS:
            return None if s == st["setting"] else ("set", s)
        return None


class LayaAgent(Agent):
    """Laya as the agent: at the first decision, ask the Laya service and switch to its most probable setting; then
    keep it (Laya was trained on static instance features, so later calls would give the same answer)."""
    first_at = 0.0
    name = "laya"

    def __init__(self):
        self.interval, self.instance, self.done, self.note = 1e9, None, False, None

    def reset(self, budget):
        super().reset(budget)
        self.done = False

    def decide(self, st):
        if self.done:
            return None
        self.done = True
        try:
            p = _post("http://127.0.0.1:8111/choose", {"instance": self.instance, "budget": st["budget"]}, 5)["probs"]
        except Exception as e:  # noqa: BLE001
            self.note = f"error: {str(e)[:120]}"
            return None
        best = max(p, key=p.get)
        self.note = json.dumps(p)
        return None if best == st["setting"] else ("set", best)


class FixedAgent(Agent):
    """Applies one fixed setting through the agent callback at the first eligible solver event, exactly where the
    learned agents make their first move. Compared with the same setting configured before presolve (C:<setting>),
    it isolates the effect of WHEN a setting is applied; compared with the learned agents, the effect of WHICH setting
    they choose (timing-matched control, review 2026-09-24)."""
    first_at = 0.0
    name = "fixed"

    def __init__(self, setting="HEU", at=0.0):
        self.setting, self.interval, self.instance, self.done, self.note = setting, 1e9, None, False, None
        self.first_at = float(at)  # 0: first eligible event (after presolve); >0: first event after `at` seconds

    def reset(self, budget):
        super().reset(budget)
        self.done = False

    def decide(self, st):
        if self.done:
            return None
        self.done = True
        return None if st["setting"] == self.setting else ("set", self.setting)

