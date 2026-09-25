---
tags: [literature, model, laya]
updated: 2026-09-23
source: https://huggingface.co/convaiinnovations/laya
bib: laya2026
---

# Laya (convaiinnovations/laya)

Source: the Hugging Face model card plus the text files in the repo (`README.md`,
`rl_agent_api.py`, `rl_common.py`, `rl_agent_config.json`, `eval/results.md`), read
2026-09-23. Repo created 2026-09-18, last modified 2026-09-20. **There is no paper.** The
card, the GitHub repo (https://github.com/NandhaKishorM/laya) and a Dev.to write-up are the
only sources. Quotes are from the card. Numbers are the vendor's own, measured on a T4. Weights
were **not** downloaded for this note.

## What the card says it is

> "Multilingual, non-autoregressive System 1 decision model. Give it a **state** (text,
> email, ticket, or JSON) and **typed questions**; it returns typed answers with
> mathematically calibrated probabilities in a single forward pass (~33 ms) across 100+
> languages."

> "It never generates text, so there is nothing to parse and nothing to hallucinate."

Tags: classification, routing, scoring, guardrails, moderation, reinforcement-learning.
Pipeline tag `text-classification`. Library `transformers`. **Licence Apache-2.0**
(commercial use allowed).

## Checkpoints (one repo, three subfolders)

| checkpoint | backbone | params | context | note |
|---|---|---|---|---|
| root `convaiinnovations/laya` | ModernBERT-large | 421M | 512 | English; ~808 MB |
| `subfolder="multilingual"` | mmBERT-base | 322M | 1024 (encoder up to 8k) | ~647 MB, ~2.2x faster |
| `subfolder="typed-decisions"` | ModernBERT-large | 421M | 1024 | fine-tuned on the 4 typed-decisions workflows |

For us: the root (English) checkpoint, or `typed-decisions` if its 1024-token context
is needed for a richer instance description.

## Architecture

- "ModernBERT-large (395M, bidirectional, fully fine-tuned) + a decision head trained from
  scratch: 2 transformer layers, an option-marker scorer, and an act/escalate head. 421M total."
- **Option markers:** "Every option is scored at its own `[MASK]` token, then softmaxed over
  that question's options. The answer space is defined at request time, so new schemas need
  no retraining."
- A question-type embedding (choice / score / noul) is added to every token before the head.
- **Act head:** takes the pooled `[CLS]` state plus four summary features of the answer
  distribution (top-1 prob, top1 − top2 margin, normalised entropy, option count / 255) and
  outputs act vs escalate. Config: `act_costs: {escalate: 0.5}`, `cost_wrong_act: 3.0`.
- All questions in one call are answered in one batched forward pass.

## Input format (from `rl_common.build_sequence`)

```
[CLS] "<type> question: <instructions>" [SEP] [MASK] opt0 [MASK] opt1 ... [SEP] <state> [SEP]
```

- `state` is a string, or a dict that is serialised with `json.dumps(ensure_ascii=False)`.
- Option text: `choice` → `"key"` or `"key: description"`; `score` → `"level i: text"`;
  `noul` → `"false: ..."` / `"true: ..."` (so `p[1]` is the noul probability).
- Each option text is capped at 48 tokens. If the options overflow `head_max_len`, every
  option is shrunk evenly (to at least 4 tokens).
- Budgets (root): `max_len 512`, `head_max_len 192`, so **about 320 tokens are left for the
  state**. The state is truncated from the right, or from the left for multi-turn training.
  The API raises an error if the options do not fit.

## API (`rl_agent_api.py`, "Jev-compatible")

```python
agent = laya.load("convaiinnovations/laya")          # or RLAgent(model_dir)
out = agent.predict(state, questions)                # RLAgent.system_one(state, questions)
questions = {
  "strategy": {"type": "choice",
               "instructions": "...",
               "criteria": {"highs_default": "...", "scip_aggr_heur": "...", ...}},  # dict or list
  "urgency":  {"type": "score", "instructions": "...", "criteria": ["low", "mid", "high"]},
  "flag":     {"type": "noul",  "instructions": "..."}
}
```

Returned per question:
- `choice`: `{"choice": key, "probabilities": {key: p}, "confidence": c, "rl_agent": {"act_probability": a}}`
- `score`: `{"score": E[level], "legend": {...}, "probabilities": {...}, "confidence": c, ...}`
- `noul`: `{"noul": p_true, ...}`
- plus `usage.input_tokens` and `output_tokens: 0`.

Probabilities are temperature-scaled at inference: `temperature_by_options` is keyed by
bucket (`choice:2`, `choice:3-5`, `choice:6-10`, `choice:11+`, `score:3-5`, `noul:2`), with a
per-type fallback. In the shipped root config `choice:6-10` = **1.00** (effectively uncalibrated)
and `choice:11+` = 0.10. **Our 6-way strategy question falls in `choice:6-10`, so we must refit
that temperature on our own validation data.**

A `Router` (`pip install laya`) picks the English or multilingual checkpoint by script
detection. We do not need it.

Operational note from the card: if `laya.load()` hangs, run with `USE_TF=0`.

## Training: RLCD

> "RLCD (Reinforcement Learning for Calibrated Decisions). The policy reports a
> distribution; exploration adds zero-mean Gaussian noise to the logits; the reward is a
> strictly proper scoring rule (log + spherical, plus ranked probability score for ordinal
> questions). Expected reward is maximised only by reporting honest probabilities. Updates
> are REINFORCE with a group-mean baseline (GRPO-style). Multi-turn conversations use
> TD(λ=1.0) over prefix slices."

From `rl_common.proper_reward`: reward = log score (floored at −9.21) + 0.5 × spherical
score, minus 1.0 × RPS for `score` questions. The **target may be soft** (a distribution),
not just one-hot. Shipped root config: 7,313 updates, 1 epoch, 1.96 h, fine-tuned from a
prior checkpoint, bf16.

## Vendor-reported results worth knowing

- typed-decisions (2,000 decisions): fine-tuned checkpoint 0.766 accuracy. **Base root
  checkpoint 0.362, below the 0.461 majority-class baseline.** "Laya is a fast base to
  specialise, not a zero-shot decision engine."
- In-task eval (root): accuracy 0.753, ECE 0.030. Zero-shot held-out task families:
  accuracy 0.651, ECE 0.204.
- Over-confident as shipped. Temperature refit moves mean ECE 0.466 → 0.081.
- Weak on high-cardinality choices (Banking77, 77 labels: 0.425) because options share the
  `head_max_len` budget. Ordinal `score` is the weakest primitive (SST-5 0.372).
- Latency (T4): 39.5 ms for one question on the root checkpoint, 38.4 ms p50 in `eval/results.md`.

## Implications for fine-tuning it on solver traces

1. **Zero-shot is not an option.** The card itself says the capability comes from
   fine-tuning. Plan a supervised warm start or an RLCD fine-tune on our traces. A
   fine-tuning notebook is linked from the card
   (`notebooks/laya_finetune_typed_decisions_2xT4_kaggle.ipynb` in the GitHub repo).
2. **Frame strategy selection as one `choice` question with 6 options.** Option text can
   carry a short description of each strategy ("cuOpt primal-focused: GPU heuristics,
   PDLP LP"), within 48 tokens each and about 192 in total. That fits.
3. **The state must fit in about 320 tokens.** Serialise a compact JSON of instance features
   (size, density, integrality mix, constraint-type counts, LP-relaxation stats, family tag),
   with rounded numbers. Text encoders tokenise digits poorly, so we should test bucketed or
   rounded features against raw ones. Or use the 1024-context `typed-decisions` checkpoint.
4. **Use soft targets.** RLCD accepts a target distribution. A softmin over per-strategy
   primal integrals (averaged over seeds) encodes "several strategies are near-tied",
   which is common in MIP portfolios, and it fits the proper-scoring reward.
5. **Refit the temperature for the `choice:6-10` bucket** before any calibration claim,
   using a held-out split.
6. **The act/escalate head maps naturally onto "defer to best-fixed"** or "hedge with two
   strategies". It needs its own reward/cost definition if we use it.
7. **Baselines on equal footing:** LightGBM/MLP get the same numeric features. Laya gets them
   as text. Report whether any gain survives when Laya's text state holds only information
   the tabular baselines also have.
8. Licence (Apache-2.0) permits fine-tuning and publishing derived weights. Per the Spark
   rules, the weights download needs Berk's go-ahead first.
