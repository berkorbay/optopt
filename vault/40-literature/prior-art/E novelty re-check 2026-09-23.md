---
tags: [literature, prior-art, novelty]
updated: 2026-09-23
scope: re-check of the three novelty claims left open by sweeps A–D (see [[Prior art]], [[C configuration, selection and dynamic control]])
---

# E: novelty re-check, 2026-09-23 (evening)

**Claims tested.**
(a) No published work uses a learned per-instance selector that chooses **between different MIP solvers**, as opposed to
configuring one solver.
(b) No BERT/ModernBERT-class small encoder has been fine-tuned to choose MIP solver settings.
(c) No published work splits solver-control gain into static per-instance choice and mid-solve switching.

**Short answer.** (a) is **false as worded**. A published learned cross-solver MIP selector has existed since 2017 (ASlib
MIP-2016 and OASC 2017), and in 2026 a text-embedding version followed (ZeroFolio). Mixed-paradigm portfolios with MIP
back-ends go back to 2014. A narrower claim survives. (b) survives, but only with its qualifiers. (c) survives for MIP. Its
conceptual template exists for continuous black-box optimisation and must be cited. Details in §3.

## 1. How the search was run, and what was blocked

| source | status this session |
|---|---|
| OpenAlex API | **blocked**: HTTP 429 "Insufficient budget … shared by everyone on your network's IP address", `retry-after` 11 318 s (resets at midnight UTC). No OpenAlex query ran, so there was no OpenAlex citation-graph walk either. |
| Semantic Scholar `/paper/search` (relevance) | **blocked**: 429 on every attempt. It gave up after 12 back-off retries (~13 min) on the first query. |
| Semantic Scholar `/paper/search/bulk` | **worked**: 12 boolean queries (below), abstracts included |
| Semantic Scholar `/paper/{id}/citations` | worked for 4 of 5 seeds. DASH (arXiv 1307.4689) stayed 429. |
| DBLP search API | refused (429 / connection closed) |
| Crossref | reachable (one probe). Not needed for discovery. |
| WebSearch | ~38 queries (list below) |
| Primary documents read | ASlib `MIP-2016` scenario files on GitHub (`coseal/aslib_data`: `description.txt`, `readme.txt`, `algorithm_runs.arff`); the same for `CSP-Minizinc-Time-2016` and `CSP-MZN-2013`; OASC 2017 setup paper (PMLR v79, open PDF); the AS competitions 2015/2017 report (open arXiv PDF 1805.01214); Amadini et al. LION 2014 (author copy, unibo.it); Pezo et al. C&OR 2024 (author copy, hochbaum.ieor.berkeley.edu); Pellegrino et al. CP 2025 (LIPIcs, CC BY); SMT-Select CP 2026 landing page (LIPIcs, CC BY); Hurley et al. slides (open PDF via semanticscholar.org); ZIB OPUS record of Georges et al. 2018 |
| arXiv | no `curl` to arxiv.org from the box. A handful of single abstract/HTML pages were opened through the web-fetch tool, as in sweep C (2604.19753 HTML; abstracts of 2311.13184, 2608.07040, 2608.17170, 2512.13374, 2504.16918, 2309.03924, 1706.08627; PDF 1805.01214). |

No shadow library was used. No paywall was bypassed. No one was contacted. No personal data went into any API call.

### Semantic Scholar bulk queries (total hits)
| id | query | hits |
|---|---|---|
| q1 | `"algorithm selection" + (MIP \| MILP \| "mixed integer" \| "integer programming")` | 42 |
| q2 | `("solver selection" \| "selecting solvers" \| "select the solver" \| "choose the solver") + ("integer programming" \| MIP \| MILP \| "linear programming")` | 41 |
| q3 | `(Gurobi + CPLEX + SCIP) + (selection \| selector \| portfolio) + (learning \| learned \| neural)` | 0 |
| q4 | `portfolio + ("per-instance" \| "instance-specific") + (MIP \| MILP \| "mixed integer")` | 3 |
| q5 | `"MIP-2016"` | 1 |
| q6 | `(GPU \| PDLP \| cuOpt \| cuPDLP) + (MILP \| "mixed integer" \| "linear programming") + (selection \| portfolio)` | 33 |
| q7 | `(LLM \| "language model") + ("solver selection" \| "choose solver" \| "select solver" \| "selecting a solver")` | 16 |
| q8 | `(MiniZinc \| "sunny-cp" \| SUNNY) + portfolio` | 48 |
| q9 | `(BERT \| ModernBERT \| RoBERTa \| "text encoder" \| "text embeddings") + ("algorithm selection" \| "algorithm configuration" \| "solver configuration")` | 7 |
| q10 | `("dynamic algorithm selection" \| "dynamic algorithm configuration" \| "online algorithm selection") + (switching \| static)` | 30 |
| q11 | `("algorithm selection" \| "solver selection") + (HiGHS \| Gurobi \| CPLEX \| Xpress)` | 887 (loose match; filtered by title/abstract keywords to ~120 and screened) |
| q12 | `"algorithm portfolio" + ("integer programming" \| MIP \| MILP)` | 10 |

Citation walks (S2 `citations`). ZeroFolio 2604.19753: 0 citing papers indexed. Cai/Huang/Dilkina 2412.14409: 8, none of
them a cross-solver selector. Pezo 2309.03924: 3, none relevant. Pellegrino CP 2025: 5 (ZeroFolio, SMT-Select, Xia et al.
2608.17170, Da Ros et al. 2512.13374, an NK-landscape study), all listed below.

### WebSearch queries (hit lists screened by hand; the tool gives no totals)
MIP solver selection Gurobi/CPLEX/SCIP; ASlib MIP-2016 algorithms; sunny-cp + Gurobi/CPLEX back-ends; "MIP-2016" results;
OASC 2017 "Mira"; learned PDLP vs simplex/barrier selection; LLM agent selects solver Gurobi/SCIP/HiGHS; "solver
selection" MIP GNN; BERT fine-tuned algorithm selection; "algorithm selection" MIPLIB Mittelmann; CPU vs GPU (cuOpt)
per-instance predictor; LLM optimisation benchmarks "which solver"; "MILP solver selection" 2025–26; algorithm selection
Gurobi/SCIP/HiGHS portfolio; dynamic vs static algorithm selection (Vermetten, BBOB); MINLP solver selection; empirical
hardness models for CPLEX/Gurobi/SCIP/lp_solve; fine-tuned LM predicts Gurobi parameters; ModernBERT/RoBERTa/DeBERTa
algorithm selection; LLaMoCo; LLM-enhanced algorithm selection (IJCAI 2024); ZeroFolio MIP-2016; instance space analysis
for MIP; LLM solver recommendation; exact-vs-heuristic selection; RL dynamic SCIP configuration; cuOpt/PDLP portfolio; LP
algorithm prediction; MIP-2016 + neural; Amadini COP portfolios; "Feature-Based Algorithm Selection for MIP"; Pezo PBO
portfolio; Hurley multi-language portfolio; SMT-Select encoder; LLM solver routing; MiniZinc Challenge portfolios 2023–25;
AS for MIP-based NN verification.

## 2. Table

Evidence: *Confirmed* means accessible full text, code or data was read. *Strong evidence* means the abstract or landing
page was read, plus consistent secondary sources. *Likely* means metadata or snippets only. *Unknown* means not
established.

| # | Paper | Year | Accessible evidence | Problem | Solver(s) | ML/model | Intervention | Similarity to our claims | Confidence |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **ASlib scenario MIP-2016** (R.-D. Bergdoll; in ASlib, `coseal/aslib_data`) | 2016/17 | scenario files read: `algorithm_runs.arff` has 218 instances × {**CBC, CPLEX, Gurobi, SCIP-cpx, XPRESS**}; readme: "PAR10 performances of modern solvers on the solvable instances of MIPLIB2010 … runtime data directly taken from the '12 threads' table of H. Mittelmann's evaluations"; 143 MIP features (UBC EPM code) | MIPLIB 2010, time to optimality (PAR10, cutoff 7200 s) | 5 different MIP solvers | benchmark for any AS method | per-instance choice **between MIP solvers** before the solve | **direct precedent for (a)**. Runtimes are Mittelmann's, not self-run. No GPU solver, no anytime metric, 218 instances | Confirmed |
| 2 | **OASC 2017** setup: Lindauer, van Rijn, Kotthoff (PMLR 79); results: "The algorithm selection competitions 2015 and 2017", AIJ 272 (2019), arXiv 1805.01214 | 2017/19 | both open PDFs read. Table 1 lists MIP-2016 as "Mira", 5 algorithms, VBS/SBS speedup 11. Table E.9 remaining gap on Mira: ASAP.v3 0.491, ASAP.v2 0.495, AS-RF 0.505, Sunny-fkvar 0.568, *Zilla 0.967, AS-ASL 1.407, Sunny-autok 1.014, *Zilla dyn-sched 2.337. Table 5: MIP-2016 average remaining gap 0.56, best 0.49 | as #1 | as #1 | ASAP (pre-schedule + RF), *Zilla (pairwise cost-sensitive forests), Sunny (k-NN), RF/ASlib baselines | learned per-instance selection among CBC/CPLEX/Gurobi/SCIP/Xpress, scored on held-out test instances | **direct precedent for (a)**: 8 learned selectors, the best closing ~51 % of the SBS→VBS gap. Several do worse than the single best solver, which fits our C2 | Confirmed |
| 3 | **ZeroFolio**, Szeider (AutoML 2026), arXiv 2604.19753 | 2026 | HTML full text via fetcher. Frozen Gemini-embedding-2 (also Gemini-001, text-embedding-3-large, Qwen3-embedding-8B), "without fine-tuning"; raw instance file (incl. MPS) → embedding → weighted k-NN. MIP-2016 row: SBS 3008, RF 3258, tuned RF 1973, ZeroFolio 2512, VBS 282 (PAR10); gap closed ZeroFolio 18 %, RF −9 % | MIP-2016 (and 10 other ASlib scenarios) | CBC/CPLEX/Gurobi/SCIP/Xpress | frozen text embeddings + k-NN | selection between MIP solvers from **raw MPS text** | **precedent for (a) with a text encoder**, and closest to (b). Differences: frozen, not fine-tuned; embeddings, not a classifier; runtime metric; no GPU solver | Confirmed |
| 4 | SUNNY / sunny-cp, Amadini, Gabbrielli, Mauro (TPLP 2014; SAC 2015; "SUNNY-CP and the MiniZinc Challenge", TPLP 2018, arXiv 1706.08627) | 2014–18 | abstracts; the sunny-cp documented portfolio includes G12/Gurobi, G12/CBC and (2020 portfolio) CPLEX, per the search snippets and MiniZinc challenge descriptions | MiniZinc CSP/COP models | CP, SAT/LCG and **MIP back-ends** (Gurobi, CBC, CPLEX) | k-NN → per-instance solver schedule | selection and scheduling across solver paradigms, MIP solvers included | precedent for "learned choice that includes MIP solvers". Inputs are CP models, not MIP instances, and the MIP solvers are one paradigm among many | Strong evidence |
| 5 | ASlib CSP-Minizinc-Time-2016 / -Obj-2016 (Bergdoll), used in OASC 2017 | 2016/17 | scenario file read: 20 solvers including **MZN/Cbc, MZN/CPLEX, MZN/Gurobi, MZN/SCIP** (OASC used an 8-solver subset; its composition was not checked) | MiniZinc Challenge 2016 | CP + MIP back-ends | any AS method | as #4 | as #4 | Confirmed (data); Unknown whether the MIP back-ends are in the OASC 8 |
| 6 | Amadini, Gabbrielli, Mauro, "Portfolio approaches for constraint optimization problems" (LION 2014 → AMAI 2016) | 2014/16 | LION author copy read: universe of 12 MiniZinc 2012 solvers incl. **G12/MIP**; 4977 COPs; anytime **score** from the best objective found by time *t*; the "area under val(s,i,t)" is named but not used | COPs in MiniZinc | CP + one MIP back-end | SATzilla-, 3S-, CPHydra- and SUNNY-style selectors | per-instance selection under an **anytime quality metric** | closest older precedent for "anytime metric + cross-paradigm selection incl. a MIP solver" | Confirmed (LION version) |
| 7 | Pellegrino, Akgün, Dang, Kiziltan, Miguel, "Transformer-Based Feature Learning for Algorithm Selection in Combinatorial Optimisation" (CP 2025, LIPIcs 340, CC BY) | 2025 | full text read: encoder "based on the BERT-base-uncased architecture … since we do not employ a pre-trained model"; 2048 tokens; learned features → AS; algorithms = Essence Prime model × {Kissat, Chuffed, **CPLEX**, OR-Tools CP-SAT} | 3 Essence problem classes | SAT, CP, **MIP (CPLEX)**, CP-SAT | BERT-architecture encoder **trained from scratch** on instance text | per-instance model+solver choice | **closest to (b)**: BERT-class encoder, instance text in, solver choice out, CPLEX in the portfolio. Differences: not pretrained or fine-tuned, not MIP instances, no settings/strategies, no GPU | Confirmed |
| 8 | Hurley, O'Sullivan, Allouche, Katsirelos, Schiex, Zytnicki, de Givry, "Multi-language evaluation of exact solvers in graphical model discrete optimization" (Constraints 21(3)) | 2016 | the authors' slides (open PDF) read: portfolio over toulbar2, **CPLEX (two 0/1-LP encodings)**, DAOOPT, MaxHS; selectors M5P, J48, RF and k-means reach 2279–2298 solved vs VBS 2321 and toulbar2 2220 | graphical-model optimisation (MRF/WCSP) | incl. CPLEX as a 0/1 ILP solver | trees, RF, clustering | per-instance choice across solver languages | cross-paradigm precedent with CPLEX as a candidate. Instances are not native MIPs | Strong evidence (slides; article not read) |
| 9 | Pezo, Hochbaum, Godoy, Asín-Achá, "Automatic algorithm selection for Pseudo-Boolean optimization with given computational time limits" (C&OR 2024, 10.1016/j.cor.2024.106836; arXiv 2309.03924) | 2023/24 | author copy read: portfolio NaPS, two OpenWBO, LS-PBO, RoundingSat, **Gurobi**, Clasp; RF/GB/k-NN/CNN; **time limit is an input** (anytime selection); also "p-PBO_MS" runs the top-p predicted solvers in equal time shares | PBO (0-1 programs) | PB/MaxSAT solvers + **Gurobi (MIP)** | random forest (chosen), GB, k-NN, CNN | per-instance, per-budget solver choice; also splits the budget over top-p solvers | **close to our framing**: anytime selection across heterogeneous solvers incl. a MIP solver, plus a "run several" variant (our C4). Differences: PBO, one MIP solver, no GPU, quality at the deadline rather than a primal integral | Confirmed |
| 10 | Hutter, Xu, Hoos, Leyton-Brown, "Algorithm runtime prediction: methods & evaluation" (AIJ 206, 2014; arXiv 1211.0906) | 2014 | abstract (S2). Solver list from memory of the paper: CPLEX, Gurobi, SCIP, lp_solve; not re-read this session | MIP (plus SAT, TSP) | several MIP solvers | RF and other EPMs | runtime prediction per solver, stated as the basis for portfolio selection | background for (a): per-solver models, no selector evaluated across MIP solvers in the abstract | Likely (solver list) |
| 11 | Georges et al., "Feature-based algorithm selection for mixed integer programming" (ZIB-Report 18-17, OPUS 6836) | 2018 | OPUS landing page: "treat different parameter settings of the MIP solver SCIP as different algorithms to choose from" | MIP | **SCIP only** | feature-based AS | per-instance choice of SCIP setting | not (a). **New to our bibliography and very close to our SCIP static-choice arm**; add to [[C configuration, selection and dynamic control]] | Strong evidence |
| 12 | Vermetten, Wang, Bäck, Doerr, "Towards dynamic algorithm selection for numerical black-box optimization: investigating BBOB as a use case" (GECCO 2020; arXiv 2006.06586; HAL hal-02871952) | 2020 | abstract and snippets: compares the static per-function VBS with single-switch dynamic selection; switching can beat the static VBS | continuous BBO (BBOB) | CMA-ES variants / BBOB algorithms | none (oracle analysis) | theoretical static-vs-switch split | **conceptual template for (c)** outside MIP; the result goes the other way from our C3 | Strong evidence |
| 13 | Kostovska et al., "Per-run algorithm selection with warm-starting using trajectory-based features" (PPSN 2022, 2204.09483); "To switch or not to switch" (2023, 2302.09075) | 2022/23 | titles and abstracts (S2) | BBO | BBO algorithms | trajectory features, RF | predict whether a mid-run switch pays | related to (c), not MIP | Strong evidence |
| 14 | DASH, Di Liberto et al. (EJOR 2016; arXiv 1307.4689) | 2016 | already in sweep C | MIP | CPLEX | clustering + GGA | branching-heuristic switching vs pure selection | the only MIP comparison of switching against static selection. Branching heuristic only, PAR10, no seed protocol; opposite result to our C3 | Confirmed (sweep C) |
| 15 | SMT-Select, Lu, Sarnighausen-Cahn, Chen, Gurfinkel, Manea, Ganesh (CP 2026, LIPIcs, CC BY) and FoIKS 2026 (LNCS) companion | 2026 | landing page: AST graph + Sentence-BERT (`all-mpnet-base-v2`) text of a natural-language context → solver selection; fine-tuning not stated | SMT | SMT solvers | GNN + sentence encoder | per-instance selection | analogue of (b) in SMT; no MIP | Strong evidence (CP 2026); Likely (FoIKS) |
| 16 | Wu et al., "Large Language Model-Enhanced Algorithm Selection" (IJCAI 2024, 10.24963/ijcai.2024/579; arXiv 2311.13184) | 2024 | abstract and secondary description (ZeroFolio): LLM embeds **algorithm source code**; instance side uses hand-crafted ASlib features | ASlib scenarios (MIP-2016 inclusion not verified) | ASlib portfolios | pretrained LLM (model not verified) | per-instance selection | related to (b): a language model on the algorithm side, not the instance side | Likely |
| 17 | Xia, Ansótegui, Szeider, "Synthesizing Feature Extractors: An Agentic Approach for Algorithm Selection" (arXiv 2608.17170) | 2026 | abstract: LLM agents write feature extractors; 5-solver portfolio (names not in the abstract); VRP, car sequencing, error-correcting codes | CSP/COP | not verified | LLM-written features + standard AS | per-instance selection | related (LLM in the AS pipeline). Whether a MIP solver is in the portfolio is **Unknown** | Likely |
| 18 | Da Ros, Di Gaspero, Roitero (arXiv 2512.13374) | 2025/26 | abstract: frozen open-weight LLM hidden states (3B–120B) as instance features for per-instance AS | CO benchmarks (not MIP per the abstract) | not stated | frozen LLM probing | selection | related to (b); frozen, not fine-tuned | Likely |
| 19 | OptimAI, Thind, Sun, Liang, Yang (arXiv 2504.16918) | 2025/26 | abstract, plus a search snippet saying a decider/planner ranks strategies incl. OR-Tools, SCIP, Gurobi | NL → optimisation model | Gurobi, SCIP, OR-Tools | prompted LLM (not trained for selection) | per-problem strategy/solver choice | weak (a)-type: prompted, not learned, and not measured as a selector | Likely |
| 20 | König et al., "Speeding up neural network robustness verification via algorithm configuration and an optimised MILP solver portfolio" (Machine Learning 111, 2022; Leiden repository copy) | 2022 | abstract via search: parallel portfolio of **configurations of one MIP solver**; per-instance AS left as future work | MIP-based NN verification | one MIP solver (Gurobi, per the MIPVerify/Venus back-end; not verified) | configurator | parallel config portfolio | related to C4, not (a) | Strong evidence |
| 21 | Kuş, Akgün, Dang, Miguel, "Frugal algorithm selection" (CP 2024; JAIR 2026) | 2024/26 | abstracts | CP / combinatorial | Essence pipelines (portfolio incl. CPLEX not checked) | active learning for AS labels | cheaper selector training | methodology only | Likely |

Searched and screened out as not relevant to (a)–(c): LLaMoCo (fine-tuned CodeGen-350M generates optimiser code for
continuous problems); OptiDSL 2608.07040 (solver library behind a DSL; its selection mechanism is not in the abstract);
GPU-PDLP parameter tuning 2606.08638 (one solver); CHAP, ReXi and cuOpt (already in sweep C, not learned); Cheng et al.
NeurIPS 2024 (neural net picks a cut per instance, one solver); Vilas Boas et al. ITOR 2021 (decision trees over CBC LP
settings, one solver); Select-then-Solve 2604.06753 (LLM reasoning paradigms, not solvers).

## 3. Verdicts

### (a) Learned per-instance selection *between different MIP solvers*: **precedent exists. Do not claim it.**
- **Direct precedents.** The ASlib **MIP-2016** scenario (CBC, CPLEX, Gurobi, SCIP, Xpress on 218 MIPLIB 2010 instances,
  Mittelmann's runtimes) was one of the 11 OASC 2017 scenarios. Eight learned selectors were scored on it (best remaining
  gap 0.49, i.e. ~51 % of SBS→VBS closed; VBS is 11× faster than SBS). ZeroFolio (2026) reran it with frozen text
  embeddings of the MPS files (18 % gap closed). Every ASlib-wide selector paper since 2017 has this scenario available,
  and some (Run2Survive 2007.02816, Tornede et al. 2109.06234) turned up on a "MIP-2016" query; their use of it is *Likely*,
  not verified.
- **Mixed-paradigm precedents with MIP back-ends.** SUNNY/sunny-cp and Amadini et al. (MiniZinc, with G12/MIP, CBC,
  Gurobi, CPLEX back-ends), Hurley et al. 2016 (CPLEX vs toulbar2 etc.), Pellegrino et al. 2025 (CPLEX among four
  solvers), and Pezo et al. 2024 (Gurobi vs PB solvers, **anytime**, time limit as an input, plus a top-p split).
- **How close.** MIP-2016 and OASC are exactly "a learned selector choosing among MIP solvers on MIP instances". They
  differ from us only in scale and metric: 218 instances, time-to-optimality PAR10, a borrowed runtime table, CPU
  solvers only. Pezo et al. is the nearest on metric (anytime quality under a budget), but for PBO.
- **What survives (no precedent found).** (i) A portfolio that includes a **GPU MIP solver** (cuOpt/PDLP-based) next to
  CPU solvers, with a learned selector over it. Nothing was found in S2 q6, the WebSearch GPU queries or the citation
  walks. (ii) Cross-solver selection scored on the **primal integral** at short wall-clock budgets, with self-run,
  held-out-seed labels on MIPLIB 2017 + ML4CO + UC. Suggested wording: *"Learned selection among MIP solvers has been
  benchmarked before (ASlib MIP-2016, OASC 2017; ZeroFolio 2026) on time to optimality with CPU solvers. We are not aware
  of prior work that includes a GPU MIP solver in the portfolio or scores the choice by the primal integral."* Keep
  "not aware" rather than "first": OpenAlex could not be queried this session.

### (b) BERT/ModernBERT-class encoder fine-tuned to choose MIP settings: **no precedent found, but with qualifiers.**
- The nearest works each lack one element:
  - Pellegrino et al. CP 2025 has a BERT-base *architecture* on instance text choosing among solvers incl. CPLEX, but it
    is **trained from scratch**, on Essence rather than MIP, and picks model and solver rather than settings.
  - ZeroFolio uses **frozen** embeddings of MPS text, with k-NN, on MIP-2016.
  - SMT-Select uses Sentence-BERT for SMT.
  - Lawless et al. 2025 uses a **generative** LLM to configure SCIP separators.
  - AS-LLM (IJCAI 2024) is a language model on the algorithm side.
- Defensible claim: *a pretrained non-autoregressive encoder, fine-tuned end-to-end with calibrated probabilities, as a
  per-instance selector of MIP solver settings and strategies.* Pellegrino et al. and ZeroFolio must be cited next to it.
  Dropping "pretrained/fine-tuned" or "MIP" from the claim makes it false.

### (c) Decomposing gain into static per-instance choice vs mid-solve switching: **no MIP precedent found; cite the template.**
- In MIP, DASH is the only work found that compares dynamic switching with pure per-instance selection. It uses the
  branching heuristic only, PAR10, no seed protocol, and finds the opposite result. Hendel's solving phases are
  hand-crafted and do not report the split.
- Outside MIP, Vermetten et al. 2020 (BBOB) splits the oracle into static VBS vs single-switch dynamic selection, and
  Kostovska et al. 2022/23 learn when switching pays. That is the conceptual precedent for our decomposition. The paper
  should say *"following the static-vs-dynamic oracle comparison of Vermetten et al. for black-box optimisation, we
  measure the split for MIP solver control, with held-out seeds"*. It should not present the decomposition idea as new.

### Action items
- Add rows 1–3, 6–9, 11, 12 to [[Related work]] / `refs.bib` (all have legal open copies). MIP-2016 is cited via ASlib
  plus Lindauer et al. 2019.
- Fix [[Prior art]] synthesis item 1 ("a learned selector across different MIP solvers" → "…including a GPU solver, scored
  by the primal integral").
- Re-run the OpenAlex queries after the midnight-UTC budget reset (or with a free API key, which only Berk can create), to
  close the remaining recall gap on 2025–26 preprints.

## Paywalled
Moved to [[Paywalled research]] (Amadini 2016 AMAI, Lu 2026 FoIKS, Hurley 2016 Constraints).
