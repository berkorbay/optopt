"""Laya as a strategy-selection policy: zero-shot and fine-tuned ("MIP-Laya").

Laya (convaiinnovations/laya) is a ModernBERT-large encoder with a 2-layer decision head. A request is a
*state* (text, ≤ ~320 tokens here) plus a *choice question* whose options each get a [MASK] marker; the head
scores the markers in one forward pass. We use the checkpoint's own code (rl_common.py in the model dir) for
the sequence layout and the model, so zero-shot inference is exactly the published model.

Fine-tuning: full fine-tune of encoder + head with soft targets P(a) ∝ exp(-β·cost_a) (spec §12),
cross-entropy on the choice logits. No other change to the architecture.
"""
from __future__ import annotations

import json
import math
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch

from optopt.paths import MODELS  # noqa: E402

MODEL_DIR = Path(os.environ.get("LAYA_DIR", MODELS / "laya"))
sys.path.insert(0, str(MODEL_DIR))
from rl_common import QTYPES, build_model, build_sequence, collate_items  # noqa: E402

OPTIONS = {
    "H0": "HiGHS default, CPU",
    "H1": "HiGHS with heavy primal heuristics, CPU",
    "S0": "SCIP default, CPU",
    "S1": "SCIP with aggressive primal heuristics, CPU",
    "C0": "NVIDIA cuOpt default, GPU",
    "C1": "NVIDIA cuOpt primal-focused without cuts, GPU",
}
INSTRUCTIONS = ("Which mixed-integer programming solver strategy will reach the best solution fastest "
                "within the time budget for this problem?")


def state_text(f: dict, budget: float) -> str:
    """Compact, human-readable state; numbers rounded so the tokenizer sees few tokens."""
    def pct(x):
        return f"{100 * x:.0f}%"
    return (
        f"time budget {budget:.0f} s. "
        f"size: {10 ** f['log_rows']:.0f} rows, {10 ** f['log_cols']:.0f} columns, {10 ** f['log_nnz']:.0f} nonzeros, "
        f"density {f['density']:.2g}. "
        f"variables: {pct(f['frac_bin'])} binary, {pct(f['frac_int'])} general integer, {pct(f['frac_cont'])} continuous. "
        f"constraints: {pct(f['frac_eq'])} equality, {pct(f['frac_le'])} less-or-equal, {pct(f['frac_ge'])} greater-or-equal, "
        f"{pct(f['frac_setlike_rows'])} set partitioning or packing, {pct(f['frac_knapsack_rows'])} knapsack. "
        f"objective: {'maximize' if f['maximize'] else 'minimize'}, {pct(f['frac_obj_nonzero'])} of columns have cost, "
        f"{pct(f['frac_obj_on_int'])} of costs on integer columns, cost dynamic range {f['obj_dynrange']:.1f} decades. "
        f"matrix: {pct(f['frac_unit_coef'])} unit coefficients, {pct(f['frac_int_coef'])} integer coefficients, "
        f"coefficient range {f['coef_dynrange']:.1f} decades, row coefficient spread median {f['rowspread_q50']:.1f} decades, "
        f"right-hand-side range {f['rhs_dynrange']:.1f} decades. "
        f"column degree median {10 ** f['coldeg_q50'] - 1:.0f}, max {10 ** f['coldeg_max'] - 1:.0f}; "
        f"row degree median {10 ** f['rowdeg_q50'] - 1:.0f}, max {10 ** f['rowdeg_max'] - 1:.0f}."
    )


class Laya:
    def __init__(self, device="cuda", load_weights=True, options=None, instructions=None):
        from safetensors.torch import load_file
        from transformers import AutoTokenizer
        self.cfg = json.load(open(MODEL_DIR / "rl_agent_config.json"))
        self.device = torch.device(device)
        self.tok = AutoTokenizer.from_pretrained(MODEL_DIR / "tokenizer")
        self.model = build_model(self.cfg, encoder_dir=str(MODEL_DIR / "encoder"))
        if load_weights:
            self.model.load_state_dict(load_file(MODEL_DIR / "model.safetensors"), strict=True)
        self.model.encoder.config.reference_compile = False
        self.model.to(self.device).eval()
        opts = dict(options or OPTIONS)  # other choice sets (e.g. SCIP settings) keep the same question format
        self.keys = list(opts)
        self.q = {"t": "choice", "ins": instructions or INSTRUCTIONS, "crit": opts}
        self._init_state = {k: v.detach().clone() for k, v in self.model.state_dict().items()}

    def reset(self):
        self.model.load_state_dict(self._init_state)

    def encode(self, texts, targets=None):
        items = []
        for i, s in enumerate(texts):
            seq, markers = build_sequence(self.tok, s, self.q, self.cfg["max_len"], self.cfg["head_max_len"])
            assert len(markers) == len(self.keys), "options truncated"
            tgt = list(targets[i]) if targets is not None else [0.0] * len(markers)
            items.append({"ids": seq, "markers": markers, "qtype": QTYPES["choice"], "target": tgt, "label": -1,
                          "episode": 0, "ep_step": 0, "ep_len": 1, "src": "mip"})
        return items

    def _forward(self, items):
        b = collate_items([items], self.tok.pad_token_id)
        with torch.autocast(device_type="cuda", dtype=torch.bfloat16, enabled=self.device.type == "cuda"):
            logits, _ = self.model(b["input_ids"].to(self.device), b["attention_mask"].to(self.device),
                                   b["marker_pos"].to(self.device), b["marker_mask"].to(self.device),
                                   b["qtype"].to(self.device))
        return logits.float(), b

    @torch.no_grad()
    def predict(self, texts, batch=32):
        self.model.eval()
        out = []
        for i in range(0, len(texts), batch):
            logits, _ = self._forward(self.encode(texts[i:i + batch]))
            out.append(torch.softmax(logits[:, :len(self.keys)], -1).cpu().numpy())
        return np.concatenate(out) if out else np.zeros((0, len(self.keys)))

    def finetune(self, texts, soft, epochs=8, batch=16, lr_enc=2e-5, lr_head=1e-4, seed=0, log=None):
        torch.manual_seed(seed)
        rng = np.random.default_rng(seed)
        enc = [p for n, p in self.model.named_parameters() if n.startswith("encoder.")]
        head = [p for n, p in self.model.named_parameters() if not n.startswith("encoder.")]
        opt = torch.optim.AdamW([{"params": enc, "lr": lr_enc}, {"params": head, "lr": lr_head}], weight_decay=0.01)
        items = self.encode(texts, soft)
        steps = epochs * math.ceil(len(items) / batch)
        sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=[lr_enc, lr_head], total_steps=steps, pct_start=0.1)
        self.model.train()
        t0 = time.time()
        for ep in range(epochs):
            order = rng.permutation(len(items))
            tot = 0.0
            for i in range(0, len(items), batch):
                sel = [items[j] for j in order[i:i + batch]]
                logits, b = self._forward(sel)
                k = len(self.keys)
                tgt = b["target"][:, :k].to(self.device)
                loss = -(tgt * torch.log_softmax(logits[:, :k], -1)).sum(-1).mean()
                opt.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                opt.step()
                sched.step()
                tot += loss.item() * len(sel)
            if log:
                log(f"  epoch {ep + 1}/{epochs} loss {tot / len(items):.4f} ({time.time() - t0:.0f}s)")
        self.model.eval()
