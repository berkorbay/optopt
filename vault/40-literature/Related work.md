---
tags: [literature, related-work]
updated: 2026-09-23
bib: paper/refs.bib
---

# Related work

> Prior-art sweep (159 works, novelty verdict): [[Prior art]]. † = paywalled, no legal copy, described in [[Paywalled research]] only.

Project question: can a small non-autoregressive decision model (Laya, 421M params) trained on
optimization traces learn a reusable control policy across HiGHS, SCIP and NVIDIA cuOpt that
improves time-to-good-solution over fixed solver strategies? First milestone: per-instance
selection among 6 strategies (HiGHS default / heuristic-heavy, SCIP default / aggressive
heuristics, cuOpt default / primal-focused), scored against best-fixed and a per-instance
oracle, with LightGBM and MLP baselines.

Every entry below is in `paper/refs.bib` and was checked on 2026-09-23 against Crossref,
OpenAlex, a publisher page, PMLR/OpenReview or the arXiv abstract page. Where a detail such
as a page range could not be confirmed, the bib entry leaves it out.

---

## 1. Algorithm selection and portfolios

Choosing which algorithm to run on a given instance has been a formal problem since Rice
(1976): you have instance features, a set of algorithms and a performance measure, and you
want a map from features to algorithm. SATzilla made this work at competition level for SAT
with learned runtime models. Later systems replaced the regression step with clustering
(ISAC†), nearest neighbours (CPHydra†) or automatically tuned selectors (AutoFolio). ASlib then
fixed the evaluation protocol that everyone uses: compare against the single best solver and
the virtual best solver (the per-instance oracle), and report the fraction of that gap you
close. For MIP specifically, Hydra-MIP combined configuration and selection on CPLEX. Our
milestone is exactly this problem. What is different is a portfolio that spans three solvers,
one of them GPU-based, and a small pretrained text encoder as the selector.

- [rice1976algorithm]: the formal definition our milestone instantiates (features → strategy → time-to-good-solution).
- [gomes2001portfolios]: why a portfolio of differently behaving solvers beats any single one on heavy-tailed runtimes.
- [xu2008satzilla]: the reference design: empirical hardness models per solver, pick the argmin. Our LightGBM baseline is essentially this.
- CPHydra and ISAC are paywalled with no legal copy: see [[Paywalled research]].
- [xu2010hydra], [xu2011hydramip]: build the portfolio by configuration, then select. Hydra-MIP is the closest MIP precedent for "selection over solver strategies".
- [lindauer2015autofolio]: the selector's own hyperparameters matter a lot, so our baselines need a fair tuning budget.
- [bischl2016aslib]: evaluation standard: single best vs virtual best, gap closed, PAR10. We should report in these terms.
- [kotthoff2014survey], [kerschke2019survey]: surveys for positioning. Both note that per-instance selection gains depend on how complementary the portfolio is.

## 2. Algorithm configuration and runtime prediction

Configuration tunes the parameters of one solver, usually for a whole instance distribution.
ParamILS and SMAC showed large speedups on CPLEX, Gurobi and lpsolve MIP parameters. Hutter
et al. (2014) is the main reference on predicting solver runtime from instance features, which
is what a regression-based selector does internally. Our six strategies are, in effect, a tiny
hand-made configuration space. These papers explain why it helps to widen that space later
and how to do it.

- [hutter2009paramils], [hutter2011smac]: standard configurators. A tuned single strategy per solver is a stronger "best fixed" baseline than defaults.
- [hutter2010mipconfig]: configuration of MIP solvers specifically, with large gains over defaults. Sets expectations for what fixed-strategy tuning alone buys.
- [hutter2014runtime]: runtime prediction methods and MIP instance features. A direct source for our hand-crafted feature set and for the LightGBM baseline design.
- [schede2022survey]: survey of configuration methods, including per-instance configuration.
- [gleixner2021miplib]: MIPLIB 2017 benchmark and "collection" sets, instance feature clustering, and solvability status. Our instance pool and features should follow it.

## 3. Learned components inside MIP solvers

Since 2016 the field has mostly used ML to replace one decision *inside* a single solver,
usually SCIP: which variable to branch on, which cuts to add, which heuristics to run and
when, which neighbourhood to search. Branching was first (Khalil 2016; Alvarez 2017; Gasse
2019's GCNN imitating strong branching). Neural Diving and Neural Branching (Nair et al.
2020) moved it to production scale. Learned large neighbourhood search (Song 2020, Sonnerat
2021, Huang 2023) is the line most focused on primal performance, i.e. time-to-good-solution.
Cut selection (Tang 2020, Paulus 2022, Wang 2023) and separator configuration (Li 2023) show
that learned *configuration* decisions pay off too. These methods need deep solver hooks,
usually SCIP callbacks, and are trained per solver and often per instance family. Our
approach takes the opposite design point: coarse decisions made from outside the solver,
shared across solvers.

- [khalil2016learning]: learning to branch, online ranking. Shows a learned policy can replace an expensive expert rule.
- [alvarez2017strong]: regression imitation of strong branching. Same idea, earlier offline form.
- [gasse2019exact]: bipartite-graph GCNN for branching. The standard learned MIP representation and the default architecture a reviewer will ask about.
- [nair2020solving]: Neural Diving + Neural Branching at scale. The "big learned solver component" contrast to our small external selector.
- [khalil2017heuristics]: learning *when to run* primal heuristics in tree search. The closest in-solver analogue of our "heuristic-heavy vs default" choice.
- [chmiela2021learning]: learned heuristic schedules in SCIP. Also targets primal performance and uses the primal integral.
- [hendel2022alns]: bandit-based adaptive LNS in SCIP, i.e. online algorithm selection among heuristics during a solve. The online counterpart of our offline selection.
- [song2020general], [sonnerat2021learning], [huang2023searching]: learned LNS. Their anytime/primal-gap curves are the metric family we adopt.
- [liu2022localbranching]: learning local-branching neighbourhood size. Another primal-side learned control knob.
- [tang2020rl], [paulus2022learning], [wang2023learning]: learned cut selection (RL, imitation, hierarchical sequence model).
- [li2023separators]: learned per-instance separator *configuration* in SCIP. Configuration-level decisions of the kind we make, at a finer grain.
- [bengio2021ml]: taxonomy: "ML alongside the solver" (configuration, selection) vs "ML inside the solver". We sit in the first class.
- [scavuzzo2024ml]: recent survey of ML-augmented branch-and-bound, organised by solver component. Its open issues (generalisation across distributions, integration cost) are our motivation.

## 4. ML4CO competition and tooling

The NeurIPS 2021 ML4CO competition had three tasks on SCIP via Ecole: primal (find good
solutions fast, scored by primal integral), dual (tight bounds), and configuration (choose
SCIP parameters per instance). The configuration task is the nearest public precedent for our
milestone, but it was single-solver and per-dataset: entries such as Valentin et al. trained
a GNN per benchmark.

- [gasse2022ml4co]: competition report. Its primal-task metric (primal integral with time limit) and configuration task are direct templates for our evaluation.
- [prouvost2020ecole]: gym-style SCIP control interface. Shows what "solver as environment" costs in engineering and why we stay at the parameter/strategy level for three solvers.
- [valentin2022instance]: GNN predicting a SCIP configuration per instance (3rd overall in ML4CO config). A single-solver, per-instance baseline to cite against.

## 5. Learned solver configuration and learning to optimize

Several recent works learn *per-instance* MIP configurations. Iommazzo et al. learn
instance→configuration→performance and then optimise over configurations; tellingly, their
case study is a hydro unit-commitment problem on CPLEX. MIP-GNN feeds a GNN's predictions into
a solver's guidance. Hosny & Reda retrieve configurations from similar past instances.
BenLOC (2025) is a benchmark and toolkit for exactly this task. Its main message is that
dataset choice, features and baselines decide whether a learned configurator looks good,
and that classical ML baselines are hard to beat. That supports our choice to lead with
LightGBM/MLP baselines and to make Laya earn its place.

- [iommazzo2020learning]: per-instance MP solver configuration, validated on unit commitment. The closest domain precedent.
- [khalil2022mipgnn]: GNN-guided solver decisions (branching/heuristics) from a single trained model. A "one learned model steering the solver" precedent, single solver.
- [hosny2023automatic]: metric-learning retrieval of configurations. A strong, simple k-NN-style baseline design.
- [li2025benloc]: benchmark for learning to configure MIP optimizers. Adopt its baseline and bias-control protocol where it applies.
- [chen2022l2o]: L2O primer and benchmark (continuous optimisation). Useful for framing "learning to optimize" terminology, less for MIP specifics.

## 6. The solvers in our portfolio

HiGHS is the leading open-source LP/MIP solver. Its dual simplex is described in Huangfu &
Hall. The MIP branch-and-cut has no journal paper, so we cite the software. SCIP is the
standard research MIP framework and the substrate of nearly all section-3 work; the 9.0 and
10.0 suite reports document its heuristics and parameters. cuOpt is NVIDIA's open-source GPU
optimizer. Its LP side descends from PDLP (restarted primal-dual hybrid gradient; Applegate
et al.) and cuPDLP (Lu & Yang). Its MIP side leans on GPU primal heuristics (Çördük et al.
2025: GPU PDLP as an approximate LP solver, bulk fix-and-propagate, feasibility pump and
local search), which build on CPU heuristics such as Feasibility Jump. The practical point
for us: cuOpt is primal-heuristic-strong and bound-weak by design, while HiGHS and SCIP are
classical branch-and-cut. So the portfolio is genuinely complementary on time-to-good-solution,
which is what makes selection worthwhile.

- [huangfu2018parallelizing]: HiGHS dual simplex core.
- [highs]: HiGHS software. Cite the release used; MIP solver by Gottwald.
- [bolusani2024scip9], [hojny2025scip10]: SCIP suite reports. Parameter emphasis settings behind our "aggressive heuristics" strategy.
- [applegate2021pdlp]: PDLP, the first-order LP method under cuOpt's LP.
- [lu2025cupdlp]: GPU PDLP. Why a GPU LP solver can win on very large, loosely structured LPs.
- [luteberget2023fj]: Feasibility Jump. LP-free MIP heuristic that GPU heuristics build on.
- [corduk2025gpu]: cuOpt's GPU primal heuristics. The mechanism behind the "cuOpt primal-focused" strategy.
- [cuopt]: cuOpt software. Cite the release used.

## 7. How to measure "time to a good solution"

Time-to-optimal ignores what an operator gets while waiting. Berthold's primal integral
integrates the primal gap over time, so it rewards finding good solutions early. It became
the ML4CO primal metric and is the natural target for our selector. Lodi & Tramontani show
that MIP runtimes vary a lot under changes that should not matter (random seed, row order,
platform)†. A per-instance oracle computed from one seed therefore overstates the achievable
gain. We need several seeds per (instance, strategy) and should report the oracle with its
own variance.

- [berthold2013primal]: primal integral definition. Primary metric (plus time-to-gap thresholds).
- Lodi & Tramontani (variability) is paywalled with no legal copy: see [[Paywalled research]]. It is why we use multi-seed labels and a variance-aware oracle.
- [gleixner2021miplib]: MIPLIB's benchmark rules (time limits, solvability status) for instance selection.

## 8. Unit commitment as a test domain

Unit commitment (UC) is a MIP family with real operational deadlines, so time-to-good-solution
matters in practice. Knueven, Ostrowski & Watson compare UC formulations and show that
formulation choice alone changes solve time by large factors. PGLib-UC provides the standard
open instances (CA, FERC, RTS-GMLC) in JSON. Xavier, Qiu & Ahmed learn from historical
solves of similar UC instances to warm-start and prune the model, with large speedups. That
is instance-family learning inside one solver. Iommazzo et al. (section 5) configure CPLEX for
hydro UC.

- [knueven2020uc]: formulation study and reference formulation for our UC instances. Also a reminder that formulation choice confounds solver-strategy comparisons.
- [pglibuc]: instance source (CC BY). Our UC instances should come from here.
- [xavier2020uc]: learning for security-constrained UC. The strong domain-specific baseline that our general selector does *not* try to beat on its own terms.

## 9. LLMs and foundation models for optimization control; small decision models

LLM work on optimization is mostly about *modelling*: turning text into a MILP (OptiMUS) or
searching program space for heuristics (FunSearch). Two recent papers use LLMs to *configure*
MIP solvers. Lawless et al. (CPAIOR 2025) use an LLM to pick SCIP separator settings
cold-start from a problem description. GRIMIP (2026) combines LLM reasoning with Bayesian
optimisation for instance-specific configuration. Both call large autoregressive models,
and both configure one solver. Da Ros et al. review about 100 LLM-for-CO studies. On the model
side, RouteLLM shows that a small BERT-class classifier can make routing decisions between
expensive back-ends from preference data. That is the closest ML analogue to using Laya
(ModernBERT-large encoder + decision head) as a solver router. Laya's training uses strictly
proper scoring rules (Gneiting & Raftery) and needs temperature calibration (Guo et al.).
That matters for us because calibrated strategy probabilities allow hedging (running two
strategies) or deferring to a default.

- [ahmaditeshnizi2024optimus]: LLM formulation agent. Contrast: we control solving, not modelling.
- [romeraparedes2024funsearch]: LLM program search for heuristics. Contrast: offline heuristic *design* vs online *selection*.
- [lawless2025llm]: LLM cold-start separator configuration (SCIP). Closest LLM precedent. Single solver, generative model, no training on traces.
- [luo2026grimip]: LLM + BO instance-specific MIP configuration. Recent, arXiv-only; same caveats.
- [daros2025llmco]: systematic review of LLMs for CO, for positioning.
- [ong2024routellm]: small BERT classifier as a router between back-ends. Architectural precedent for an encoder-based selector.
- [warner2025modernbert]: Laya's English backbone.
- [marone2025mmbert]: backbone of the multilingual Laya checkpoint (not needed for us).
- [gneiting2007scoring]: strictly proper scoring rules. Laya's RLCD reward.
- [guo2017calibration]: temperature scaling. Laya ships over-confident, and its card says to refit temperatures.
- [shao2024deepseekmath]: GRPO. Laya's RLCD update is described as "GRPO-style" (group-mean baseline).
- [laya2026]: the model card itself (no paper exists). See [[Laya]].

---

## Laya model card summary

Everything here comes from the Hugging Face card and the code files in the repo
(`rl_agent_api.py`, `rl_common.py`, `rl_agent_config.json`), read 2026-09-23. Details: [[Laya]].

- **What it is:** "Multilingual, non-autoregressive System 1 decision model." You give it a
  *state* (text or JSON) and *typed questions*. It returns typed answers with probabilities
  in one forward pass. It never generates text.
- **Architecture (root checkpoint):** ModernBERT-large encoder (395M, bidirectional, fully
  fine-tuned) plus a decision head trained from scratch: 2 transformer layers, an
  option-marker scorer and an act/escalate head. **421M total.** Each answer option gets its
  own `[MASK]` token, and the scores are softmaxed over that question's options, so the answer
  set is defined at request time. Context 512 tokens (`head_max_len` 192 for the question and
  options, about 320 left for the state). Sibling checkpoints: `laya-multilingual` (mmBERT-base,
  322M, 1024 ctx) and `laya-typed-decisions` (fine-tuned, 1024 ctx).
- **Question types / API:** `choice` (returns `choice`, `probabilities` per option,
  `confidence`), `score` (ordinal: expected level `score`, `probabilities`, `legend`),
  `noul` (binary probability). Each answer also carries `rl_agent.act_probability` from the act
  head. Entry points: `laya.load(...).predict(state, questions)` or
  `RLAgent(model_dir).system_one(state, questions)`. The request shape is "Jev-compatible".
  Note that the API names are `choice`/`score`/`noul`, not "choices/scores".
- **Training, "RLCD" (Reinforcement Learning for Calibrated Decisions):** the policy outputs a
  distribution, exploration adds Gaussian noise to logits, and the reward is a strictly proper
  scoring rule (log + spherical, plus ranked probability score for ordinal questions). Updates
  are REINFORCE with a group-mean baseline ("GRPO-style"). Multi-turn uses TD(λ=1.0).
- **Honest limits stated on the card:** base checkpoints are near chance zero-shot on their
  typed-decisions benchmark (0.362). "A fast base to specialise, not a zero-shot decision
  engine." The model ships over-confident, so refit temperatures per (type, option count). Ordinal
  `score` is the weakest question type.
- **Licence:** Apache-2.0. Repo created 2026-09-18. There is no paper; the card and GitHub are
  the only sources.

---

## What is novel here (and what is not)

**Not novel, and we should say so plainly:**
- Per-instance algorithm selection with a portfolio and an oracle is 50 years old in concept
  and 15+ years old in practice (SATzilla, Hydra-MIP, ASlib's protocol).
- Using ML to speed up MIP solving is an established field with surveys (Bengio et al. 2021;
  Scavuzzo et al. 2024), a NeurIPS competition (ML4CO) and a configuration benchmark (BenLOC).
- Per-instance MIP configuration, including GNN-based and LLM-based variants, exists, and it
  has been tried on unit commitment specifically (Iommazzo et al.).
- Primal integral as the metric for "good solutions early" is standard.

**Plausibly novel:**
- **One selector across three different solvers**, including a GPU first-order/heuristic
  solver (cuOpt) next to two CPU branch-and-cut solvers. Almost all learned MIP work is
  single-solver, usually SCIP. The portfolio's complementarity comes from solver
  *architecture*, not from parameter tweaks.
- **A small, pretrained, general-purpose decision model** (a text encoder with typed,
  calibrated outputs) as the selector, instead of a GNN or GBDT trained from scratch per
  task. The questions are whether it matches LightGBM on the milestone, and whether the
  *same* model can later take on other control questions (time-limit split, when to switch
  solver, whether to hedge) without new architecture.
- **Calibrated probabilities used for decisions**: hedging (run the top two strategies in
  parallel when uncertain) or deferring to the best-fixed strategy. Selectors in the ASlib
  tradition mostly output an argmax.
- **Trained on optimisation traces**, i.e. anytime primal-bound curves, not only final runtimes.

**The risk to state up front:** BenLOC and the ASlib literature both find that tuned
tree-based baselines are hard to beat on tabular instance features. If LightGBM already
closes most of the best-fixed→oracle gap, then Laya's contribution has to be generality
(multiple tasks and solvers with one model) or calibration, not raw selection accuracy.

---

## Track B (in-solver dynamic control) — prior art

- [he2014learning] Imitation-learns an adaptive node-search order for LP-based branch and bound on MIP (compared against SCIP and Gurobi). The earliest learned node-selection control; it replaces one component with a learned per-node policy, whereas we switch among SCIP's existing node selectors mid-solve.
- [labassi2022nodes] A siamese GNN that compares pairs of open nodes, trained to imitate a diving oracle, used as SCIP's node comparator. Same control point (node selection) at node granularity; our model makes coarser, occasional strategy switches rather than ranking every node.
- [anderson2019restarts] Online tree-size estimation from search progress, used to decide whether to restart a MIP solve (implemented in SCIP). The direct precedent for the "restart" action; their decision rule is a hand-set threshold on the estimate, where ours would be learned jointly with the other knobs.
- [hendel2019bandits] Multi-armed bandits choose, adaptively during a solve, among SCIP's LNS heuristics and diving heuristics. Closest precedent for learned mid-solve control of heuristic effort, but online per-instance bandits with no offline-trained model and no node-selection, cut or restart actions.
- [mattick2024node] Reinforcement learning of node selection with a GNN over the whole B&B tree state, in SCIP (TMLR 2024). Shows node selection can be learned with RL on tree-state features; again a per-node replacement rather than a small switcher over existing strategies.
- [chmiela2023online] Online bandit learning that controls two heuristic classes (LNS and diving) at once with a single agent during a SCIP solve. Another data point that adaptive heuristic effort helps; like Hendel et al. it adapts within one instance instead of transferring a trained controller across instances.
