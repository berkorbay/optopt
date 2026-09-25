# Policies and evaluation

Code: `experiments/01_selection.py` (all non-Laya policies + scoring), `experiments/02_laya.py`,
`policies/laya.py`, `policies/rules.py`.

Policies: random (expected), best default solver (train), best fixed strategy (train), hand rules
(pre-registered 00:52, before results), LightGBM (per-strategy cost regressors → argmin), MLP (64-64, soft
targets), Laya zero-shot, MIP-Laya (full fine-tune with soft targets), oracle.

**Scoring** (ASlib convention): SBS = hindsight single best strategy on the test instances; VBS = oracle.
Closed gap = (SBS − policy)/(SBS − VBS); 95 % bootstrap CI over test instances. Also time-to-target sgm (PAR2).

**Folds.** *Pooled*: one policy for all families, 5 folds, every instance tested once (ML4CO train always in
training; MIPLIB by instance; UC by base system). *LOFO*: train on three families, test on the fourth.

**Why both.** Pooled answers "does selection work when the family has been seen"; LOFO answers the spec's
reusability question — does the policy transfer to an unseen problem family.

**Laya input** (`state_text`): ~260 tokens of rounded, worded features; question = six-way choice with a
one-line description per strategy. Model context is 512 tokens with 192 for the question, so ≤ ~320 for state.
