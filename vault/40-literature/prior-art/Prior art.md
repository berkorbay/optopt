# Prior art

> Paywalled works we could not read legally live in [[Paywalled research]] only.

## The question
Not "has someone used Laya with SCIP, HiGHS or cuOpt?", but **"has someone used a learned / neural / foundation model to
perform the same solver-side function we want Laya to perform?"** — choosing or adjusting solver configuration and strategy,
per instance or during the solve, across solvers.

## Evidence classes
| class | meaning |
|---|---|
| **Confirmed** | method described in accessible full text or code |
| **Strong evidence** | abstract plus citing papers clearly describe the method |
| **Likely** | metadata strongly suggests similarity, implementation unclear |
| **Unknown** | insufficient public information |

## Search protocol (Berk, 2026-09-23)
1. Exact title + DOI in Google Scholar / Semantic Scholar / OpenAlex / Crossref.
2. Legal open copies: Unpaywall-style OA status (via OpenAlex), institutional repositories, author pages, arXiv, HAL,
   Zenodo, OSF, CORE, BASE, SSRN.
3. Exact-title searches (+ "pdf", "manuscript", "preprint").
4. Abstract and metadata first: question, method, data/problem class, solver/model, claimed contribution, keywords.
5. The paper's references (older, often open work). 6. Papers that **cite** it — they often describe it concretely.
7. Concept queries (learning to branch, neural diving, learned cuts, LLM + MILP, GNN + MILP, RL in branch-and-bound, …).
8. Solver-specific queries (SCIP, HiGHS, cuOpt, Gurobi, CPLEX). 9. Classify by solver intervention point.
10. Citation graphs (references, citing works, same authors / group). 11. Theses and dissertations.
12. Conference / workshop / tech-report versions. 13. Code repositories. 14. Talks and slides.
15. Benchmark anchors (MIPLIB, ML4CO, Ecole, set cover, auctions, facility location, independent set).
16. Do not over-infer from abstracts — use the evidence classes. 17. For important papers: library access (e.g. BSB,
Fernleihe, SUBITO) or an author request. 18. Ask authors when necessary — **only Berk sends such requests.**
Rules for agents: no shadow libraries, no paywalled downloads, no personal email in API calls, no contact with authors.

## Sweeps
| theme | file |
|---|---|
| A · branching and node selection | [[A branching and node selection]] |
| B · primal heuristics, diving, LNS, warm starts | [[B primal heuristics and LNS]] |
| C · configuration, selection, portfolios, dynamic control, cuts, presolve | [[C configuration, selection and dynamic control]] |
| D · LLMs, foundation models, GPU MIP, theses | [[D LLMs, foundation models and GPU MIP]] |
| E · novelty re-check (cross-solver selection, encoders, static vs dynamic) | [[E novelty re-check 2026-09-23]] |

## Synthesis (2026-09-23, from sweeps A–D: 159 works)

**Answer to the key question.** Yes, in part. Learned or online models already perform *each* solver-side function we
give Laya, but always one at a time and always inside one solver:
- per-instance static configuration (Hydra-MIP, ISAC, Valentin 2022, BenLOC, Lawless 2025, GRIMIP);
- mid-solve switching of one component (DASH for branching; Hendel's solving phases, hand-crafted);
- online bandits steering SCIP heuristics (Hendel 2019, Chmiela 2023, Balans).

What we did **not** find (corrected by the re-check [[E novelty re-check 2026-09-23]]):
1. ~~a learned selector across different MIP solvers~~ — **exists**: ASlib MIP-2016 (CBC, CPLEX, Gurobi, SCIP, Xpress),
   OASC 2017, ZeroFolio 2026. Still not found: a GPU MIP solver in the portfolio, and selection scored by the primal integral;
2. a pretrained encoder (BERT/ModernBERT class) fine-tuned to choose MIP settings (Pellegrino et al. 2025 trains a BERT
   architecture from scratch over solvers incl. CPLEX; ZeroFolio uses frozen embeddings);
3. an explicit decomposition of the gain into *static choice* and *switching*, with held-out seeds, for MIP (Vermetten et al.
   2020 did it for black-box optimisation — cite as the template);
4. an agent tuning a solver live within a single wall-clock budget that charges its own thinking time.

Items 1 and 2 are negative search results. The arXiv API was blocked and OpenAlex rate-limited during sweep C, so
**the paper must not say "first"** until the cross-solver queries are re-run on OpenAlex or Semantic Scholar.

### Closest prior art (Berk's table format)
| Paper | Year | Accessible evidence | Problem | Solver | ML/model | Solver intervention | Similarity to our idea | Confidence |
|---|---|---|---|---|---|---|---|---|
| DASH, Di Liberto, Kadioglu, Leo, Malitsky (EJOR 248(3)) | 2016 | arXiv 1307.4689 full text | heterogeneous MIP | CPLEX 12.5 | feature clustering + GGA | **switches branching heuristic at nodes** (to depth 10) | very close; **contrary result** (switching beats per-instance selection, PAR10 643 vs 892) | Confirmed |
| Hendel, Exploiting solving phases (OR Proc. 2015); Berthold, Hendel, Koch (OMS 33(3)) | 2017/18 | ZIB OPUS preprints | MIPLIB | SCIP | none (phase criteria) | **switches SCIP settings by solving phase** | very close, hand-crafted version of our schedules | Strong evidence |
| Balans, Cai, Kadioglu, Dilkina (IJCAI) / ParBalans (arXiv 2508.06736) | 2025 | open proceedings + code | MIP | on top of a MIP solver | bandit | online choice of LNS neighbourhoods; parallel configs | very close to our bandit agent and to C4; **adaptive beats best single neighbourhood** | Confirmed |
| Hendel, Miltenberger, Witzig; Chmiela et al. | 2019/2023 | open | MIP | SCIP | bandit | heuristic selection during the solve | same mechanism as our bandit, finer grain | Confirmed |
| Hydra-MIP / MIPzilla, Xu et al. | 2011 | full text | MIP | CPLEX only | cost-sensitive forests | per-instance choice of configuration | very close (static), single solver | Confirmed |
| BenLOC, Li et al. | 2025 | open | MIP | COPT | trees, GNN | per-instance configuration | very close; **agrees with C2** (gains < 5 %, trees beat deep models) | Confirmed |
| Lawless et al. (CPAIOR, LNCS) | 2025 | arXiv 2412.12038 v1 | MILP | SCIP, Gurobi | generative LLM, text | separator configuration before the solve, per family | very close (text + foundation model) | Confirmed |
| GRIMIP, Luo et al. | 2026 | arXiv 2606.23299 | MIPLIB, ML4CO IP/LB | Gurobi | LLM as BO surrogate, ~10 solves per instance | per-instance parameters | **closest**: same sets and PDI; but tuning by repeated solves, one solver | Strong evidence |
| Cai, Huang, Dilkina (CPAIOR, LNCS) | 2025 | arXiv 2412.14409 abstract | MILP | Gurobi and SCIP | multi-task graph embedding | branching + configuration of each solver | nearest "one model, two solvers"; never chooses between solvers | Strong evidence |
| ZeroFolio, Szeider | 2026 | arXiv 2604.19753 | ASlib incl. MIP-2016 | ASlib portfolio | frozen text embeddings + kNN | selection before the solve | closest "text encoder as selector"; no fine-tuning, no solver state | Confirmed |
| ReXi, Mexi & Rehfeldt | 2026 | arXiv 2609.05954 | MIPFEAS, primal integral | 10 SCIP settings | none | parallel racing with exchange (−69 % primal integral) | anticipates C4 (parallel copies); CPU, one solver | Confirmed |
| cuOpt, Çördük et al.; CHAP, Tjusila | 2025/26 | open | MIP | cuOpt; own GPU+CPU | none | GPU heuristics beside CPU B&B | CPU+GPU cooperation, hand-designed | Confirmed |

### Tensions the paper must address
- **DASH vs C3.** Its metric is time to optimality (PAR10), ours the primal integral at 30–120 s. It uses CPLEX 12.5
  and switches only the branching heuristic, at nodes near the root. Our C3 therefore holds only for *whole-setting
  switches in SCIP at short budgets, measured by time to good solutions*. It is not a general claim.
- **Balans vs C3.** Its gain from adaptivity is at the granularity of LNS neighbourhoods inside ALNS, not of solver
  emphasis settings. The bandit mechanism is the same as ours, so our bandit is not new; the decomposition is.
- **ReXi, ParBalans, Carvajal 2014, FiberSCIP racing vs C4.** Running copies and keeping the winner is established.
  Our contribution there is a *measurement* (a CPU HiGHS ‖ GPU cuOpt pair captures 80 % of the cross-solver oracle
  headroom), not a method.
- **BenLOC agrees with C2.** Cite it as independent support.

### Paywalled works and what to request
Moved to [[Paywalled research]], the single home for paywalled works (disclaimer, evidence, what to request).

### Still to do
- Re-run cross-solver algorithm-selection queries (OpenAlex / Semantic Scholar) before any novelty wording.
- Read GRIMIP's appendix and ZeroFolio's MIP-2016 numbers in full (both open).
