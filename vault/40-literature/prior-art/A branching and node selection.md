# Prior art A — learned branching and node selection in MIP

Sweep date 2026-09-23. Question asked of each work: does a learned model perform the same **solver-side function**
as our project (choosing or adjusting a MIP solver's configuration/strategy per instance or during the solve), not
"does it use Laya".

**Sources and rules.** OpenAlex (until its shared daily budget ran out mid-sweep), Crossref metadata, arXiv abstract
pages (one at a time), AAAI/OpenReview/NeurIPS proceedings pages, Optimization Online, institutional repositories,
GitHub. No shadow libraries, no paywalled PDFs. "Read" below means what was actually opened in this sweep. Full text
was read for two works (DASH arXiv preprint, Hendel et al. Optimization Online preprint); everything else was judged
from abstracts, proceedings pages and metadata. Solver names not stated in an abstract are marked "(not verified)".

**Confidence scale.** Confirmed = method read in accessible full text or code. Strong evidence = abstract/proceedings
page states the method. Likely = metadata/snippets only. Unknown = could not verify.

## 1. Table

| # | Paper (short title, first author) | Year | Venue | DOI or URL | Access | Legal copy link | Accessible evidence | Problem | Solver | ML/model | Solver intervention | Similarity | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | DASH: Dynamic Approach for Switching Heuristics — Di Liberto | 2016 (arXiv 2013) | European J. Operational Research | 10.1016/j.ejor.2015.08.018 | preprint available | https://arxiv.org/abs/1307.4689 | arXiv full text (preprint) | heterogeneous MIP | CPLEX 12.5 (branch callback, single core) | subproblem features (40), g-means clustering, GGA tuner assigns a heuristic per cluster | **switches branching heuristic during the solve** (every 3rd node, up to depth 10) among 6 heuristics; compared with ISAC per-instance selection | **very close** | Confirmed |
| 2 | Non-Model-Based Search Guidance for Set Partitioning — Kadioglu | 2012 | AAAI-12 | 10.1609/aaai.v26i1.8141 | open | https://ojs.aaai.org/index.php/AAAI/article/view/8141 | AAAI abstract page | set partitioning | CPLEX (compared vs its dynamic search) | feature-based, clustering-style (DASH precursor) | dynamic choice of branching heuristic per subproblem | **very close** | Strong evidence |
| 3 | Adaptive Algorithmic Behavior … Using Bandit Algorithms — Hendel | 2019 | Operations Research Proceedings 2018 (Springer) | 10.1007/978-3-030-18500-8_64 | preprint available | https://optimization-online.org/2018/07/6725/ | Optimization Online full text | MIP (MIPLIB-type) | SCIP 6.0 pre-release | multi-armed bandits (UCB, Exp.3, ε-greedy/greedy) with designed rewards | online selection among LNS heuristics, diving heuristics, simplex pricers **during the solve**; reports e.g. +6 % (UCB) / +14 % (greedy) LP throughput for pricing, ~8 % speed-up on hard instances for adaptive diving | **very close** (online bandit inside SCIP; not branching) | Confirmed |
| 4 | Online Learning for Scheduling MIP Heuristics — Chmiela | 2023 | CPAIOR 2023 (LNCS) | 10.1007/978-3-031-33271-5_8 | preprint available | https://arxiv.org/abs/2304.03755 | arXiv abstract | MIPLIB 2017 | SCIP (not verified from abstract; MIPLIB benchmark stated) | single bandit agent | controls LNS and diving heuristics online | **very close** (bandit agent in the solve; primal side) | Strong evidence |
| 5 | Influence branching for learning to solve MIPs online — Strang | 2025 | arXiv (MIP Workshop 2025 computational competition) | https://arxiv.org/abs/2510.04273 | open | https://arxiv.org/abs/2510.04273 | arXiv abstract | MIP reoptimisation series | SCIP | Thompson sampling over graph representations/hyper-parameters | chooses a branching heuristic's configuration online across a stream of instances | **very close** (bandit configuring branching) | Strong evidence |
| 6 | Learning to Branch — Balcan | 2018 | ICML 2018 (PMLR) | https://arxiv.org/abs/1803.10150 | open | https://arxiv.org/abs/1803.10150 | arXiv abstract | IP / CSP tree search | (not verified) | learns a weighting of branching scoring rules per distribution, with sample-complexity bounds | sets a branching **parameter** per instance distribution (a configuration choice) | related (configuration of branching, static) | Strong evidence |
| 7 | A Classifier to Decide on the Linearization of MIQPs in CPLEX — Bonami | 2022 | Operations Research 70(6) | 10.1287/opre.2022.2267 | preprint available | https://optimization-online.org/2020/03/7662/ | search-result abstract + OO landing | convex MIQP | CPLEX 12.10 (deployed) | supervised classifier on instance features | chooses a solver strategy (linearise or not) per instance; first end-to-end ML in a commercial solver | **very close** (learned per-instance strategy choice inside a solver; not branching) | Strong evidence |
| 8 | Learning a Classification of MIQP Problems — Bonami | 2018 | CPAIOR 2018 (LNCS 10848) | 10.1007/978-3-319-93031-2_43 | paywalled-no-legal-copy | — (GERAD tech report G-2017-106 exists; PolyPublie copy staff-only) | Crossref metadata + search abstract | convex MIQP | CPLEX | classifier | per-instance method choice | very close (earlier version of #7) | Strong evidence |
| 9 | Learning to Select Branching Rules in DPLL — Lagoudakis | 2001 | Electronic Notes in Discrete Mathematics 9 (SAT 2001) | https://www.sciencedirect.com/science/article/abs/pii/S1571065304003324 | preprint available | https://dias.library.tuc.gr/view/60669?locale=en | abstract (search snippets, repository record) | SAT | DPLL solver (RLSAT) | RL value function over branching rules | selects **which branching rule at each node** | related (SAT, same "choose among existing rules during search" shape) | Strong evidence |
| 10 | Learning to Branch in MIP — Khalil | 2016 | AAAI-16 | 10.1609/aaai.v30i1.10080 | open | https://doi.org/10.1609/aaai.v30i1.10080 | Crossref/OpenAlex metadata; abstract known from repo notes | MIPLIB | CPLEX (not verified in this sweep) | online learning-to-rank per instance | replaces variable selection by a ranking imitating strong branching, learned during the solve | related | Strong evidence |
| 11 | ML-Based Approximation of Strong Branching — Alvarez | 2017 | INFORMS J. Computing 29(1) | 10.1287/ijoc.2016.0723 | preprint available | https://orbi.uliege.be/handle/2268/198561 | OpenAlex/Crossref metadata; ORBi submitted manuscript listed | MIP | (not verified) | supervised regression imitating strong-branching scores (model type not verified) | replaces variable selection | related | Strong evidence |
| 12 | Exact Combinatorial Optimization with GCNNs — Gasse | 2019 | NeurIPS 2019 | https://arxiv.org/abs/1906.01629 | open | https://arxiv.org/abs/1906.01629 | OpenAlex metadata; repo notes | set cover, comb. auction, capacitated facility location, max independent set | SCIP | GCNN on variable–constraint bipartite graph, imitation of strong branching | replaces variable selection | related (canonical representation) | Strong evidence |
| 13 | Hybrid Models for Learning to Branch — Gupta | 2020 | NeurIPS 2020 | https://arxiv.org/abs/2006.15212 | open | https://arxiv.org/abs/2006.15212 | arXiv abstract | Ecole-style benchmarks | SCIP (not verified in abstract) | GNN at root + cheap MLP at nodes (CPU-only) | replaces variable selection; up to 26 % faster than CPU baselines | related (cost-of-inference argument, like our C6) | Strong evidence |
| 14 | Lookback for Learning to Branch — Gupta | 2022 | TMLR | https://arxiv.org/abs/2206.14987 | open | https://arxiv.org/abs/2206.14987 | arXiv abstract | standard benchmarks | (not verified) | GNN + target smoothing + parent-as-target regulariser; model selection on solve time | replaces variable selection | background | Strong evidence |
| 15 | Parameterizing B&B Search Trees to Learn Branching Policies — Zarpellon | 2021 | AAAI-21 | 10.1609/aaai.v35i5.16512 | open | https://arxiv.org/abs/2002.05120 | arXiv abstract | heterogeneous MIPLIB | SCIP (not verified) | imitation learning with explicit tree-state parameterisation | variable selection that generalises across instances | related (cross-instance generalisation, as our unseen-family test) | Strong evidence |
| 16 | Solving MIPs Using Neural Networks (Neural Branching) — Nair | 2020 | arXiv | 10.48550/arxiv.2012.13349 | open | https://arxiv.org/abs/2012.13349 | OpenAlex metadata; repo notes | MIPLIB + industrial | SCIP | GNN imitating full strong branching (ADMM expert) + Neural Diving | replaces variable selection (and primal heuristic) | background (large learned component) | Strong evidence |
| 17 | RL for Variable Selection in B&B (FMSTS) — Etheve | 2020 | CPAIOR 2020 (LNCS 12296) | 10.1007/978-3-030-58942-4_12 | preprint available | https://arxiv.org/abs/2005.10026 | search abstract; OpenAlex OA record | problem-specific real-world MIPs | (not verified) | RL minimising sub-tree size | replaces variable selection | background | Strong evidence |
| 18 | Improving Learning to Branch via RL — Sun | 2020 | NeurIPS 2020 Workshop LMCA | https://openreview.net/forum?id=M_KwRsbhi5e | open | https://openreview.net/pdf?id=z4D7-PTxTb | search abstract | NP-hard benchmark families | (not verified) | RL (novelty-search ES), argues SB is a poor expert | replaces variable selection | background | Strong evidence |
| 19 | Learning to Branch with Tree MDPs — Scavuzzo | 2022 | NeurIPS 2022 | https://arxiv.org/abs/2205.11107 | open | https://arxiv.org/abs/2205.11107 | arXiv abstract | Ecole benchmarks | SCIP (Ecole; not verified in abstract) | RL on tree MDPs (tree policy gradient) | replaces variable selection | background | Strong evidence |
| 20 | Branch Ranking (offline RL) — Huang | 2022 | ECML-PKDD 2022 (LNCS) | 10.1007/978-3-031-26419-1_23 | preprint available | https://arxiv.org/abs/2207.13701 | search abstract | MIP classes | (not verified) | offline ranking-based policy learning | replaces variable selection | background | Strong evidence |
| 21 | RL for B&B using Retrospective Trajectories — Parsonson | 2023 | AAAI-23 | 10.1609/aaai.v37i4.25521 | open | https://arxiv.org/abs/2205.14345 | OpenAlex metadata; title | benchmark CO | (not verified) | RL | replaces variable selection | background | Likely |
| 22 | SORREL — Feng | 2025 | AAAI-25 | 10.1609/aaai.v39i11.33219 | open | https://arxiv.org/abs/2412.15534 | OpenAlex metadata; title | benchmark MILPs | (not verified) | RL guided by suboptimal demonstrations | replaces variable selection | background | Likely |
| 23 | Planning in B&B: Model-Based RL (PlanB&B) — Strang | 2026 | AAAI-26 | 10.1609/aaai.v40i30.39759 | open | https://arxiv.org/abs/2511.09219 | AAAI abstract page | four standard MILP benchmarks | (not verified) | model-based RL with learned B&B dynamics | replaces variable selection | background | Strong evidence |
| 24 | Rethinking Branching … Deep Symbolic Discovery (Symb4CO) — Kuang | 2024 | ICLR 2024 | https://openreview.net/forum?id=jKhNBulNMh | open | https://openreview.net/forum?id=jKhNBulNMh | search abstract | branching benchmarks | (not verified) | large network searches for small symbolic branching formulas, CPU deployment | replaces variable selection with a compiled symbolic rule | related (small/cheap policy argument) | Strong evidence |
| 25 | CAMBranch — Lin | 2024 | arXiv (2402.03647) | 10.48550/arxiv.2402.03647 | open | https://arxiv.org/abs/2402.03647 | OpenAlex metadata; title | MILP benchmarks | (not verified) | contrastive learning with augmented MILPs | replaces variable selection | background | Likely |
| 26 | Rethinking the Capacity of GNNs for Branching — Chen | 2024 | arXiv (2402.07099) | https://arxiv.org/abs/2402.07099 | open | https://arxiv.org/abs/2402.07099 | arXiv abstract | theory | — | MP-GNN vs 2-FGNN expressivity for SB scores | none (theory) | background (limits of graph features) | Strong evidence |
| 27 | Towards Foundation Models for MILP — Li | 2024 | arXiv (2410.08288) | https://arxiv.org/abs/2410.08288 | open | https://arxiv.org/abs/2410.08288 | arXiv abstract | MILP-Evolve generated classes, MIPLIB | (not verified) | one model trained across many LLM-generated MILP classes; tasks: gap prediction, learning to branch, language alignment | variable selection (among tasks) | **related — nearest "foundation model" framing** | Strong evidence |
| 28 | LLM4Branch — Hou | 2026 | arXiv (2605.10401), ICML 2026 per authors | https://arxiv.org/abs/2605.10401 | open | https://arxiv.org/abs/2605.10401 | arXiv abstract | standard MILP benchmarks | (not verified) | LLM writes a branching program skeleton; parameters tuned zeroth-order on end-to-end feedback | replaces variable selection (LLM offline, not in the loop) | related | Strong evidence |
| 29 | MILP-Evo — Nie | 2026 | arXiv (2607.18252) | https://arxiv.org/abs/2607.18252 | open | https://arxiv.org/abs/2607.18252 | arXiv abstract | multiple benchmark families | SCIP | LLM-driven program evolution | designs cut-selection + branching components | background | Strong evidence |
| 30 | Learning to Search in B&B — He | 2014 | NeurIPS 2014 (NIPS 27) | https://papers.nips.cc/paper/2014 | open | NeurIPS proceedings (volume 27) | search abstract; repo notes | MIP | SCIP (compared with SCIP, Gurobi per repo notes) | imitation learning of node selection + pruning | replaces node selection/pruning | related (node-selection control point) | Strong evidence |
| 31 | Learning to Search via Retrospective Imitation — Song | 2018 | arXiv (1804.00846) | 10.48550/arxiv.1804.00846 | open | https://arxiv.org/abs/1804.00846 | OpenAlex metadata; title | combinatorial search incl. MIP | (not verified) | retrospective imitation | node selection / search policy | background | Likely |
| 32 | Learning to Compare Nodes with GNNs — Labassi | 2022 | NeurIPS 2022 | https://arxiv.org/abs/2210.16934 | open | https://arxiv.org/abs/2210.16934 | arXiv abstract; code https://github.com/ds4dm/learn2comparenodes | three benchmarks | SCIP | siamese GNN imitating a diving oracle | replaces node comparator | related | Strong evidence |
| 33 | RL for Node Selection in B&B — Mattick | 2024 | TMLR | https://openreview.net/forum?id=0ez68a5UqI | open | https://arxiv.org/abs/2310.00112 | arXiv abstract | trained on TSP, tested broadly | SCIP (per repo notes) | RL + GNN over the whole tree | replaces node selection | related | Strong evidence |
| 34 | Learning Search Approximation: Node Selection in SCIP — Yilmaz | 2021 | AI (MDPI) 2(2) | 10.3390/ai2020010 | open | https://doi.org/10.3390/ai2020010 | OpenAlex metadata (gold OA); title | MIP | SCIP | learned node selection | replaces node selection | related | Likely |
| 35 | Learning to Select Nodes with Sufficient Tree Representation (TRGNN) — Zhang | 2025 | ICLR 2025 | https://openreview.net/forum?id=gyvYKLEm8t | open | https://openreview.net/forum?id=gyvYKLEm8t | search abstract | MILP | (not verified) | tripartite graph + RL GNN | replaces node selection | background | Strong evidence |
| 36 | Learning efficient B&B for MILP — Du | 2025 | Applied Soft Computing | 10.1016/j.asoc.2025.112863 | preprint available | SSRN preprint (abstract id 4944657) | search abstract | MILP categories | (not verified) | one GNN for both node and variable selection, imitation of expert policies | replaces both decisions | related (joint control) | Strong evidence |
| 37 | Hybrid Branching — Achterberg | 2009 | CPAIOR 2009 (LNCS) | 10.1007/978-3-642-01929-6_23 | paywalled-no-legal-copy | — (only ZIB talk slides seen) | Crossref metadata; search snippet | MIP | SCIP | none (hand-designed) | combines several branching scores in one rule | background (non-learned baseline for "mixing strategies") | Likely |
| 38 | On learning and branching: a survey — Lodi | 2017 | TOP 25 | 10.1007/s11750-017-0451-6 | paywalled-no-legal-copy | — | Crossref metadata; search abstract | survey | — | survey | variable + node selection | background | Strong evidence |
| 39 | Learning to branch with Tree-aware Branching Transformers (T-BranT) — Lin | 2022 | Knowledge-Based Systems | 10.1016/j.knosys.2022.109455 | paywalled-no-legal-copy (code open) | code only: https://github.com/linjc16/TBranT | ScienceDirect abstract via search; GitHub README | MIPLIB 3/2010/2017, CORAL | SCIP (per README) | transformer over candidates + binary-tree encoding of branching history, imitation | replaces variable selection on heterogeneous instances | related (transformer; heterogeneous sets) | Strong evidence |
| 40 | GAIL to Search in B&B (RAIL) — Wang | 2022 | DASFAA 2022 (LNCS) | 10.1007/978-3-031-00126-0_51 | paywalled-no-legal-copy | — | Crossref metadata; publisher abstract via search | B&B search | (not verified) | RL + generative adversarial imitation | search policy in B&B | background | Likely |
| 41 | ML-augmented B&B for MILP (survey) — Scavuzzo | 2024 | Mathematical Programming 217 | 10.1007/s10107-024-02130-y | open | https://arxiv.org/abs/2402.05501 | OpenAlex (hybrid OA); repo notes | survey | — | survey by solver component | all components | background | Strong evidence |

Counts: 41 entries — **open 27**, **preprint available (closed venue, legal copy) 9**, **paywalled-no-legal-copy 5**
(#8, #37–#40; #8 has a later journal version with an open preprint, #7). By confidence: Confirmed 2, Strong
evidence 32, Likely 7, Unknown 0.

## 2. Paywalled items without a legal copy (NOT read in full)

Moved to [[Paywalled research]], the single home for paywalled works (disclaimer, evidence, what to request).

## 3. Closest prior art to our project

Almost all learned-branching and learned-node-selection work (#10–#36) does a **different** solver-side function
from ours: it *replaces one decision rule* (variable scoring, node comparison) with a learned per-node policy, usually
a GNN on the bipartite graph imitating strong branching or trained by RL, inside SCIP, on one problem family at a
time. It does not choose among the solver's existing configurations, and it never spans solvers.

The works that do **our** function — a learned or online model choosing among a solver's *existing* strategies,
per instance or during the solve — are few:
- **DASH (#1) and its precursor Kadioglu et al. 2012 (#2)** are the direct precedent for "switch strategy mid-solve":
  CPLEX 12.5, six branching heuristics, switching every 3rd node down to depth 10 via feature clustering. Unlike our
  C3 finding (+2 % from switching over a static choice), DASH reports a *large* gain over per-instance selection
  (PAR10 643 vs 892 for the filtered ISAC selector; mean 241 vs 289 s). The difference in metric (time to optimality vs
  our primal integral), era (CPLEX 12.5) and action set (branching heuristics only) should be discussed explicitly —
  it is the strongest contrary result to our "choose, don't switch" claim.
- **Hendel, Miltenberger, Witzig 2019 (#3), Chmiela et al. 2023 (#4) and Strang et al. 2025 (#5)** are the precedent
  for our online bandit agent: bandits inside SCIP selecting LNS/diving heuristics and pricers (#3, #4) or tuning a
  branching heuristic across a stream (#5). Our bandit acts at a coarser level (whole emphasis/setting bundles) and we
  add the static-vs-switching decomposition, but "an online bandit steering SCIP during the solve" is not new.
- **Bonami, Lodi, Zarpellon (#7, #8)**: a learned per-instance *strategy choice* deployed in a commercial solver
  (CPLEX linearise-or-not). Closest to our "learned selector from static features".
- **Balcan et al. 2018 (#6)**: learns a branching *parameter* per distribution — configuration, but static.
- **Lagoudakis & Littman 2001 (#9)**: RL choosing among existing branching rules at each node, in SAT — the oldest
  instance of the idea.
- **Li et al. 2024 (#27)**: the nearest "foundation model for MILP" framing (one model across many problem classes),
  but its model makes branching decisions and gap predictions, not configuration choices; LLM4Branch (#28) and
  MILP-Evo (#29) use LLMs offline to write solver components, not to choose settings.

Nothing found in this theme uses **one small learned model to choose configurations across several different solvers
(CPU and GPU)**, or a text-input encoder with calibrated choice probabilities for that purpose. Cross-solver selection
is algorithm-selection territory (covered by other themes).

## 4. Candidates to request from authors / via library (do not contact)

Moved to [[Paywalled research]], the single home for paywalled works (disclaimer, evidence, what to request).
