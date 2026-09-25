---
tags: [literature, prior-art, theme-C]
updated: 2026-09-23
scope: algorithm/solver selection and portfolios, instance-specific configuration, dynamic (mid-solve) configuration, learned cuts/separators, learned presolve/decomposition, performance variability
---

# Prior art C: configuration, selection and dynamic control of MIP solvers

Sweep done 2026-09-23 for the question "has anyone used a learned, neural or foundation model to do the
same solver-side job as our work?" Our job here means: choose a static configuration per instance, switch
settings during the solve, choose across solvers, or run parallel copies.

**How it was checked.** OpenAlex worked for the first queries and then ran out of free budget on this
IP. arXiv's API is blocked from this box (HTTP 403, see the autoresearch memory). The rest came from
Crossref metadata, arXiv abstract pages opened one at a time with a web fetcher, publisher and
proceedings pages, author homepages, optimization-online, and GitHub. No shadow library was used, no
paywalled PDF was opened, and no one was contacted. One full text was read: Hydra-MIP, the authors'
own UBC PDF. Everything else was judged from abstracts, landing pages or the HTML version of an
open preprint.

**Access classes.** *open*: the version of record is free. *preprint available*: the version of
record is paywalled but a legal preprint or author copy exists. *paywalled-no-legal-copy*: no legal
free copy was found.
**Confidence.** *Confirmed*: the metadata and the claim were checked against the primary source this
session, or the bib entry was already verified in [[Related work]]. *Strong evidence*: the abstract
or landing page of the primary source was read. *Likely*: the information comes only from secondary
sources, such as citing papers or search snippets. *Unknown*: not established.

Keys in `[brackets]` already exist in `paper/refs.bib`. Every other entry is new and would need a
bib entry before it is cited.

## 1. Table

| # | Paper (short title, first author) | Year | Venue | DOI or URL | Access | Legal copy link | Accessible evidence | Problem | Solver | ML / model | Solver intervention | Similarity | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **(1) Selection and portfolios** |||||||||||||| 
| 1 | SATzilla, Xu `[xu2008satzilla]` | 2008 | JAIR 32 | 10.1613/jair.2490 | open | https://doi.org/10.1613/jair.2490 | full text (OA) | SAT | SAT solvers | empirical hardness models (ridge regression) → argmin | per-instance solver selection, pre-solvers | background (template for our LightGBM selector) | Confirmed |
| 2 | Hydra-MIP, Xu | 2011 | RCRA workshop @ IJCAI 2011 | https://www.cs.ubc.ca/~hoos/Publ/XuEtAl11.pdf | open | same | **full text read** | MIP (CL, REG, RCW, ISAC sets) | CPLEX only | cost-sensitive decision forests (pairwise) for selection; ParamILS builds the portfolio | per-instance choice among CPLEX configurations ("MIPzilla" = SATzilla-style portfolio of CPLEX configs) | **very close** (static per-instance selection); single solver | Confirmed |
| 3 | ISAC, Kadioglu `[kadioglu2010isac]` | 2010 | ECAI 2010 (FAIA 215) | 10.3233/978-1-60750-606-5-751 | paywalled-no-legal-copy | — | metadata; citing surveys | SAT/MIP | incl. CPLEX (per citing work) | clustering (g-means) of normalised features, one tuned config per cluster | per-instance configuration via cluster | related | Likely |
| 4 | Algorithm selection and scheduling (3S), Kadioglu | 2011 | CP 2011, LNCS 6876 | 10.1007/978-3-642-23786-7_35 | paywalled-no-legal-copy | — | Crossref metadata; citing papers | SAT (portfolio scheduling) | SAT solvers | k-NN selection + a static schedule computed by IP | schedule of short runs, then one selected solver | related (pre-schedule vs. our parallel copies) | Likely |
| 5 | ASlib, Bischl `[bischl2016aslib]` | 2016 | Artificial Intelligence 237 | 10.1016/j.artint.2016.04.003 | preprint available | https://arxiv.org/abs/1506.02465 | verified in [[Open access audit]] | AS benchmarking | many | — | evaluation protocol (SBS, VBS, gap closed) | background (our "closed gap" metric) | Confirmed |
| 6 | Using diversification, communication and parallelism, Carvajal | 2014 | Oper. Res. Letters 42(2) | 10.1016/j.orl.2013.12.012 | paywalled-no-legal-copy | — | Crossref; abstract via search snippets | MILP (MIPLIB 2010) | one MILP solver, multiple configurations | none | parallel B&B trees with different configurations that share information | **very close** to our parallel copies (no learning) | Strong evidence |
| 7 | Exploiting erraticism in search, Fischetti | 2014 | Operations Research 62(1) | 10.1287/opre.2013.1231 | preprint available | http://www.dei.unipd.it/~fisch/papers/exploiting_erraticism_in_search.pdf (author page) | abstract (RePEc/INFORMS); search snippet | MIP | not verified | none (rule-based "bet") | **bet-and-run**: several short randomized runs, bet on the most promising, finish only that one | **very close**: the non-learned form of "choose early, don't switch" plus seed copies | Strong evidence |
| 8 | FiberSCIP, Shinano | 2018 | INFORMS J. Computing 30(1) | 10.1287/ijoc.2017.0762 | preprint available | https://optimization-online.org/2017/04/5944/ | Crossref; optimization-online landing | MIP | SCIP (shared-memory UG) | none | **racing ramp-up**: every thread solves the root with a different setting, the winner's tree is continued | **very close** (race-then-commit across settings) | Strong evidence |
| 9 | Race, Exchange, Improve (ReXi), Mexi | 2026 | arXiv 2609.05954 | https://arxiv.org/abs/2609.05954 | open | same | abstract + HTML full text (via fetcher) | MIP primal (MIPFEAS benchmark, primal integral) | 10 SCIP settings racing; external tool ReXi | none | portfolio racing with solution and bound exchange; primal integral cut by 69 % from 1 to 10 threads; no GPU, no HiGHS, no cuOpt in the portfolio | **very close** to our parallel-copies result, CPU and one solver only | Confirmed |
| 10 | CHAP hybrid GPU-CPU heuristic, Tjusila | 2026 | arXiv 2605.05086 | https://arxiv.org/abs/2605.05086 | open | same | abstract | MIP primal (Land-Doig MIP competition 2026) | own GPU tabu search + cuPDLPx; CPU fix-and-propagate and feasibility pump; compared with Gurobi and cuOpt | none (fixed collaborative portfolio, shared pool) | GPU+CPU heuristic portfolio sharing solutions | related (the closest **GPU+CPU portfolio**; heuristics, not whole solvers, and nothing learned) | Strong evidence |
| 11 | GPU-accelerated primal heuristics (cuOpt), Çördük `[corduk2025gpu]` | 2025 | arXiv 2510.20499 | 10.48550/arXiv.2510.20499 | open | https://arxiv.org/abs/2510.20499 | verified in [[Related work]] | MIP primal | cuOpt | none | GPU heuristics run concurrently with CPU B&B inside cuOpt | background (one of our arms) | Confirmed |
| **(2) Instance-specific configuration** |||||||||||||| 
| 12 | Automated configuration of MIP solvers, Hutter `[hutter2010mipconfig]` | 2010 | CPAIOR 2010, LNCS | 10.1007/978-3-642-13520-0_23 | preprint available | https://www.cs.ubc.ca/~hutter/papers/10-CPAIOR-MIP-Config.pdf | verified in [[Open access audit]] | MIP | CPLEX, Gurobi, lpsolve | ParamILS (per distribution) | one tuned static configuration per instance set | related (per-set, not per-instance) | Confirmed |
| 13 | Learning to configure MP solvers by MP, Iommazzo `[iommazzo2020learning]` | 2020 | LION 14, LNCS | 10.1007/978-3-030-53552-0_34 | preprint available | https://arxiv.org/abs/2401.05041 | verified in [[Related work]] | MP (hydro UC case) | CPLEX | learned performance map + optimisation over configurations | per-instance configuration | very close (single solver) | Confirmed |
| 14 | ML4CO competition report, Gasse `[gasse2022ml4co]` | 2022 | NeurIPS 2021 Comp. Track, PMLR 176 | https://arxiv.org/abs/2203.02433 | open | same | verified in [[Related work]] | MILP (item placement, load balancing, anonymous) | SCIP via Ecole | participants' own (GNN, trees, ...) | **configuration task**: pick SCIP parameters per instance, scored by primal-dual integral | **very close**: same datasets as our ML4CO sets, single solver | Confirmed |
| 15 | Instance-wise algorithm configuration with GNNs, Valentin `[valentin2022instance]` | 2022 | arXiv 2202.04910 | 10.48550/arXiv.2202.04910 | open | https://arxiv.org/abs/2202.04910 | verified in [[Related work]] | ML4CO config task | SCIP | GNN predicting per-configuration performance | per-instance SCIP config (3rd overall in ML4CO config) | **very close** (learned per-instance static choice; one solver) | Confirmed |
| 16 | Automatic MILP solver configuration by learning problem similarities, Hosny | 2023 | Annals of Operations Research | 10.1007/s10479-023-05508-x | preprint available | https://arxiv.org/abs/2307.00670 | abstract | MILP | one MILP solver (not named in the abstract) | deep metric learning, then nearest-neighbour configuration | per-instance configuration (costs up to 38 % better than prior approaches) | very close (single solver) | Strong evidence |
| 17 | BenLOC, Li `[li2025benloc]` | 2025 | arXiv 2506.02752 | 10.48550/arXiv.2506.02752 | open | https://arxiv.org/abs/2506.02752 | abstract + HTML full text (via fetcher) | MIP config benchmark (5 datasets incl. MIPLIB 2017, load balancing) | **COPT** only | LightGBM/RF vs GNN/deep models | per-instance choice among default + top-3 of 25 configurations (cut/heuristic levels, strong branching) | **very close**. Finding matches ours: gains over per-dataset best under 5 %; deep models lose to trees | Strong evidence |
| 18 | Multi-task representation learning for MILP, Cai | 2025 | LNCS (Springer, 2025; conference not confirmed) | 10.1007/978-3-031-95973-8_9 | preprint available | https://arxiv.org/abs/2412.14409 | abstract | MILP (3 benchmarks) | **Gurobi and SCIP** | shared GNN embedding, multi-task | branching and solver configuration, **one embedding for both solvers** (separate heads/tasks) | **very close**: the nearest "one model across solvers", but it configures each solver separately and never chooses between them | Strong evidence |
| 19 | LLMs for cold-start separator configuration, Lawless `[lawless2025llm]` | 2025 | CPAIOR 2025, LNCS | 10.1007/978-3-031-95976-9_4 | preprint available | https://arxiv.org/abs/2412.12038 | verified in [[Related work]] | MILP | SCIP | LLM (autoregressive, zero-shot) from the problem description | per-instance/family separator configuration | **very close** (text input, foundation model; one solver, one module) | Confirmed |
| 20 | GRIMIP, Luo `[luo2026grimip]` | 2026 | arXiv 2606.23299 | https://arxiv.org/abs/2606.23299 | open | same | abstract | MIP (MIPLIB and 6 other benchmarks) | not named in the abstract | LLM as the surrogate inside Bayesian optimisation | per-instance hyperparameters; reports >40 % lower primal-dual integral on hard instances | **very close** (foundation model; needs search runs per instance) | Strong evidence |
| 21 | Online algorithm configuration for MILP re-optimization with LLM guidance (anonymous) | 2025 or 2026 (venue unknown) | OpenReview submission | https://openreview.net/forum?id=xbyebbS1ZF | open (OpenReview) | same (the page is behind a browser check; content comes from a search snippet) | search-engine abstract only | MILP re-optimization (MIP Workshop 2023 benchmark) | SCIP and Gurobi | LLM proposes a small portfolio, then **multi-armed bandit** picks across a sequence of instances | configuration (primal hints, root/non-root cuts) chosen online across related instances; up to 54 % lower time | **very close** to our LLM-portfolio + bandit idea, but it adapts *between* instances, not within one | Likely |
| 22 | OptVerse AI solver, Li | 2024 | arXiv 2401.05960 | https://arxiv.org/abs/2401.05960 | open | same | abstract | LP/MILP (commercial) | Huawei OptVerse | parameter tuning, GCN initial basis, RL presolve, RL cut selection | ML inside a production solver | related (industrial precedent of learned solver-side decisions) | Strong evidence |
| 23 | Towards foundation models for MILP (MILP-Evolve), Li | 2025 | ICLR 2025 | https://arxiv.org/abs/2410.08288 | open | same | abstract; venue from the official GitHub README | MILP | SCIP-based tasks | GNN foundation model trained on LLM-generated classes | integrality-gap prediction, learning to branch, language alignment; **no configuration task** | related (a "foundation model for MILP" that does *not* choose configurations) | Strong evidence |
| 24 | Learning a classification of MIQPs, Bonami | 2018 | CPAIOR 2018, LNCS 10848 | 10.1007/978-3-319-93031-2_43 | preprint available | GERAD G-2017-106 (https://www.gerad.ca/fr/papers/G-2017-106), linked from PolyPublie 64112 | Crossref; repository record; abstract snippets | MIQP | CPLEX | supervised classifiers | per-instance **linearize or not** decision; follow-up OR 2022 (10.1287/opre.2022.2267) is titled "...in CPLEX" | related (a learned per-instance solver-side switch, deployed) | Strong evidence |
| 25 | Learning to scale MIPs, Berthold | 2021 | AAAI-21 | 10.1609/aaai.v35i5.16482 | open | https://ojs.aaai.org/index.php/AAAI/article/view/16482 | abstract | MIP numerics | FICO Xpress | random forest / linear regression | per-instance choice between standard and Curtis-Reid scaling; "used by default since release 8.9" | related (a learned static choice shipped as a solver default) | Confirmed |
| 26 | Learning to use local cuts, Berthold | 2025 | Math. Prog. Computation | 10.1007/s12532-025-00278-y | preprint available | https://arxiv.org/abs/2206.11618 | abstract; OpenAlex OA record | MIP | FICO Xpress | regression forest | per-instance decision: generate cuts in the tree (local) or at the root only | related | Strong evidence |
| **(3) Dynamic / online configuration during the solve** |||||||||||||| 
| 27 | DASH: dynamic approach for switching heuristics, Di Liberto | 2016 | EJOR 249(3) | 10.1016/j.ejor.2015.08.018 | preprint available | https://arxiv.org/abs/1307.4689 | abstract (arXiv); search snippets | MIP | MIP B&B (solver not named in the abstract) | g-means clustering of subproblem features, offline assignment of branching heuristic per cluster | **switches branching heuristic at nodes during search**; reports "significant gains over pure algorithm selection" | **very close**, and its result points the other way from our C3 (switching adds only ~2 %) | Strong evidence |
| 28 | Dynamic algorithm configuration, Biedenkapp | 2020 | ECAI 2020 (FAIA 325) | 10.3233/FAIA200122 | open | https://ecai2020.eu/papers/1237_paper.pdf | Crossref; search | general (toy/benchmarks) | — | RL (contextual MDP) | per-step parameter control | background (the DAC framing of our C3) | Strong evidence |
| 29 | Adaptive algorithmic behavior via bandits, Hendel `[hendel2019bandits]` | 2019 | OR Proceedings 2018 | 10.1007/978-3-030-18500-8_64 | preprint available | https://opus4.kobv.de/opus4-zib/frontdoor/index/index/docId/6956 (ZIB-Report 18-36) | verified in [[Related work]] | MIP | SCIP | multi-armed bandits | online selection among heuristics during a solve | **very close** to our online UCB agent (heuristic level, not whole settings) | Confirmed |
| 30 | Adaptive LNS for MIP, Hendel `[hendel2022alns]` | 2022 | Math. Prog. Computation 14 | 10.1007/s12532-021-00209-7 | open (CC BY) | same | verified in [[Open access audit]] | MIP | SCIP | bandits (UCB, EXP3, ε-greedy) | chooses LNS neighbourhoods online within a solve | **very close** (same bandit family as our agent) | Confirmed |
| 31 | Learning to run heuristics in tree search, Khalil `[khalil2017heuristics]` | 2017 | IJCAI 2017 | 10.24963/ijcai.2017/92 | open | same | verified in [[Related work]] | MIP | CPLEX | logistic-regression-type classifier per node | decides at each node whether to run a primal heuristic | related | Confirmed |
| 32 | Learning to schedule heuristics in B&B, Chmiela `[chmiela2021learning]` | 2021 | NeurIPS 2021 | https://arxiv.org/abs/2103.10294 | open | same | verified in [[Related work]] | MIP (primal integral) | SCIP | learned schedule (offline, per distribution) | heuristic (diving) schedule | related | Confirmed |
| 33 | Online learning for scheduling MIP heuristics, Chmiela `[chmiela2023online]` | 2023 | CPAIOR 2023, LNCS | 10.1007/978-3-031-33271-5_8 | preprint available | https://arxiv.org/abs/2304.03755 | abstract | MIP (MIPLIB 2017) | SCIP | multi-armed bandit, one agent over LNS + diving | online, **within a single solve**; about 4 % faster on hard instances | **very close** to our in-loop bandit | Strong evidence |
| 34 | Clairvoyant restarts, Anderson `[anderson2019restarts]` | 2019 | AAAI-19 | 10.1609/aaai.v33i01.33011427 | open | same | OpenAlex OA record; search | MIP | SCIP | online tree-size estimation | **restart decision** mid-solve | related (the "restarts" action in our switching experiment) | Strong evidence |
| 35 | Estimating the size of B&B trees, Hendel | 2022 | INFORMS J. Computing 34(2) | 10.1287/ijoc.2021.1103 | preprint available | https://optimization-online.org/2020/04/7722/ (also ZIB-Report 20-02) | Crossref; optimization-online landing; search | MIP | SCIP 7 | progress measures, double-exponential smoothing, random forest | tree-size estimate that drives restarts and progress reports | related | Strong evidence |
| **(4) Learned cuts and separator configuration** |||||||||||||| 
| 36 | Learning cut selection via hierarchical sequence model (HEM), Wang `[wang2023learning]` | 2023 | ICLR 2023 | https://openreview.net/forum?id=Zob4P9bRNcK | open | https://arxiv.org/abs/2302.00244 | verified in [[Related work]] | MILP | SCIP (+ Huawei solver) | RL, hierarchical pointer/sequence model | which cuts to add, how many, in what order | related | Confirmed |
| 37 | Adaptive cut selection in MILP, Turner | 2023 | Open J. Math. Optimization 4 | 10.5802/ojmo.25 | open | https://ojmo.centre-mersenne.org/articles/OJMO_2023__4__A5_0/ | landing page; search | MILP (MIPLIB 2017) | SCIP | learned per-instance cut-scoring parameters (model details not verified) | per-instance cut-selector parameters | related (per-instance parameter choice inside one module) | Likely |
| 38 | Learning to configure separators, Li `[li2023separators]` | 2023 | NeurIPS 2023 | 10.52202/075280-2622 | open | https://arxiv.org/abs/2311.05650 | verified in [[Related work]] | MILP | SCIP | restricted configuration space, then k-NN/GNN predictor of improvement over default | per-instance separator on/off configuration | **very close** in design (small learned menu, pick per instance) | Confirmed |
| 39 | Sample complexity of tree search configuration, Balcan | 2021 | NeurIPS 2021 | https://proceedings.neurips.cc/paper_files/paper/2021/hash/210b7ec74fc9cec6fb8388dbbdaf23f7-Abstract.html | open | https://arxiv.org/abs/2106.04033 | proceedings page; search | IP theory | B&C | learning theory | distribution-level cut/tree-search parameter learning, generalisation bounds | background | Strong evidence |
| **(5) Learned presolve and decomposition** |||||||||||||| 
| 40 | Learning when to use a decomposition, Kruber | 2017 | CPAIOR 2017, LNCS 10335 | 10.1007/978-3-319-59776-8_16 | paywalled-no-legal-copy | — | Crossref; citing papers (e.g. arXiv 2310.07068) | MIP | GCG (Likely) | supervised classifier (model not verified) | per-instance: apply Dantzig-Wolfe or not, and which decomposition | related (learned per-instance algorithm choice at t = 0) | Likely |
| 41 | L2P-MIP: learning to presolve, Liu | 2024 | ICLR 2024 | https://proceedings.iclr.cc/paper_files/paper/2024/hash/1e6e0c2edb159b2ad2f9419b898f56d3-Abstract-Conference.html | open | https://openreview.net/pdf?id=McfYbKnpT8 | proceedings abstract; search | MIP | SCIP | simulated annealing labels + neural net imitator | per-instance presolver priority/time/round (42 parameters) | related (per-instance configuration of one phase; labels from search, like ours from runs) | Strong evidence |
| **(6) Variability and benchmarking methodology** |||||||||||||| 
| 42 | Performance variability in MIP, Lodi `[lodi2013variability]` | 2013 | INFORMS TutORials | 10.1287/educ.2013.0112 | paywalled-no-legal-copy | — | metadata; citing works | MIP | CPLEX and others | — | seed/permutation variability | background (our seed protocol, C4) | Confirmed (metadata) |
| 43 | Improving B&C by random sampling, Fischetti | 2016 | Math. Prog. Computation 8 | 10.1007/s12532-015-0096-0 | preprint available | https://www.dei.unipd.it/~salvagni/pdf/ksample.pdf (co-author page) | Crossref; abstract snippets; co-author page | MIP | not verified | none | uses several root LP bases/random runs to stabilise and improve B&C | related (exploiting variability with copies, like our C4) | Strong evidence |
| 44 | Measuring the impact of primal heuristics, Berthold `[berthold2013primal]` | 2013 | Oper. Res. Letters 41(6) | 10.1016/j.orl.2013.08.007 | preprint available | https://opus4.kobv.de/opus4-zib/frontdoor/index/index/docId/1788 | verified in [[Open access audit]] | metric | SCIP | — | primal integral | background (our metric P(T)) | Confirmed |

44 entries: 23 open, 16 preprint available, 5 paywalled-no-legal-copy.

## 2. Paywalled items without a legal copy (not read in full)

Moved to [[Paywalled research]], the single home for paywalled works (disclaimer, evidence, what to request).

## 3. Closest prior art to our project

**Per-instance static configuration selection with a learned model.** This is well established.
Hydra-MIP and MIPzilla (2011) chose among CPLEX configurations with cost-sensitive forests. ISAC did
the same with clusters. Valentin et al. used a GNN for the SCIP configuration task in ML4CO (2022). Hosny
& Reda used metric learning and nearest neighbours (2023). Li et al. predict separator configurations
per instance (NeurIPS 2023). Liu et al. do the same for presolve (L2P-MIP, 2024). BenLOC (2025)
benchmarks the task on COPT, and FICO ships two such learned static choices as Xpress defaults
(scaling, local cuts). The foundation-model versions are Lawless et al. (LLM, cold start, text input,
SCIP separators) and GRIMIP (LLM surrogate inside Bayesian optimisation). **All of them configure a
single solver.** BenLOC's headline finding is that learned gains over the per-dataset best are under
5 % and that trees beat deep models. That is independent confirmation of our C2 (selectors capture at
most a quarter of the headroom; LightGBM is competitive with Laya). We add nothing new on the
*existence* of learned per-instance selection. What we add is a measured oracle headroom (25–41 %)
alongside how little of it the selectors capture, plus a small non-autoregressive text encoder with
calibrated probabilities as the selector.

**Mid-solve (dynamic) configuration with RL or bandits.** Also established, but always at a finer
grain than whole settings. DASH (EJOR 2016) switches the branching heuristic at nodes using clustering.
It reports *significant* gains over static selection, which is the opposite of our C3, and a reviewer
will ask about it. Hendel's bandits (2019, 2022 ALNS) and Chmiela et al. 2023 run bandits over
heuristics inside one SCIP solve. Khalil 2017 and Chmiela 2021 learn when to run heuristics. Anderson
2019 and Hendel 2022 decide restarts from tree-size estimates. The LLM + bandit re-optimization paper
adapts configurations *between* related instances. The generic DAC framework (Biedenkapp 2020) has,
as far as this sweep found, no published MIP application that switches whole emphasis settings mid-solve.
What we add: a controlled decomposition of *static choice* vs. *switching* with seeds, showing that
switching adds about 2 %. We also show that a bandit acting on whole settings mostly rediscovers the
best static setting. We found no prior paper that makes that decomposition explicitly.

**Cross-solver selection.** This is thin. MIPzilla, despite the name, is CPLEX configurations only
(checked in the full text). Cai, Huang & Dilkina (2025) learn one embedding usable for both Gurobi and
SCIP, but they configure each solver; they do not choose between them. The anonymous re-optimization
paper evaluates on SCIP and Gurobi separately. Hutter 2010 tunes CPLEX, Gurobi and lpsolve separately.
**We found no published learned per-instance selector across different MIP solvers**, let alone one
spanning an open CPU solver, SCIP and a GPU solver. This is our clearest novelty, but it rests on a
negative search result. arXiv API search was unavailable and OpenAlex ran out of budget mid-sweep, so it
should be re-checked before the paper claims "first".

**CPU+GPU portfolios.** cuOpt itself runs GPU heuristics concurrently with CPU branch-and-bound
(Çördük 2025). CHAP (2026) is a fixed GPU+CPU heuristic portfolio with a shared pool. ReXi (Mexi &
Rehfeldt, Sept 2026) races 10 SCIP settings with exchange and cuts the primal integral by 69 %, on CPU
only and with no learning. FiberSCIP's racing ramp-up, Fischetti & Monaci's bet-and-run and Carvajal
et al. are the older forms of "run copies, keep the winner". None of them pairs two independent
solvers, CPU HiGHS with GPU cuOpt. What we add: the measurement that a 2-way CPU‖GPU pair captures
80 % of the oracle headroom. That is a portfolio result, not a learning result, and it is closely
anticipated by the racing literature. Frame it as a measurement.

## 4. Candidates to request from authors / via library (do not contact anyone)

Moved to [[Paywalled research]], the single home for paywalled works (disclaimer, evidence, what to request).

## Gaps in this sweep

- arXiv API blocked (403) and the OpenAlex daily budget exhausted early, so recall on 2025–2026
  preprints relies on web search. Before claiming novelty on cross-solver selection, re-run
  "algorithm selection" + MIP/MILP + solver-name queries on OpenAlex or Semantic Scholar.
- The anonymous OpenReview paper (row 21) could not be opened; its authors, venue and year are
  unknown.
