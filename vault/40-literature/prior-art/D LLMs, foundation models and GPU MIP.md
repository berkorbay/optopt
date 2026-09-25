# Prior art D: LLMs, foundation models, small encoder routers, GPU MIP, HiGHS+ML, theses

Sweep date: 2026-09-23. Question: **has anyone used a learned, neural, foundation or language model to do
the solver-side job we do, i.e. choose or adjust a MIP solver's configuration or strategy?**

**How this was checked.** Only legal sources were used: arXiv abstract and HTML pages (fetched one at a time),
the Semantic Scholar batch API for metadata, Crossref for DOIs and licences, conference pages (ICLR, ICML/PMLR,
NeurIPS, IJCAI), university repositories and GitHub. The OpenAlex search was used at the start, but the network's shared free daily
budget ran out partway through (`Rate limit exceeded`, no key used), and later Semantic Scholar searches got
HTTP 429. So open-access status is taken from Crossref, Semantic Scholar's `openAccessPdf`, and the
venue's own OA policy. OpenReview pages returned a browser challenge, so no OpenReview decision could be read. No
paywalled PDF was opened.

**What "Evidence" means in the table.** *HTML full text* = the arXiv HTML full text was read (via
a summarising fetch, not line by line). *abstract* = the arXiv abstract page. *metadata* = S2 or Crossref record
plus search-engine snippets. **Confidence** refers to what the table claims about the paper: Confirmed = seen on
the paper's own page. Strong evidence = seen in its metadata and several consistent secondary sources. Likely =
only one secondary source.

## 1. Table

| # | Paper (short title, first author) | Year | Venue | DOI or URL | Access | Legal copy | Evidence read | Problem | Solver | ML / model | Solver intervention | Similarity | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | LLMs for Cold-Start Cutting Plane Separator Configuration, Lawless | 2024 arXiv / 2025 | CPAIOR 2025, LNCS | 10.1007/978-3-031-95976-9_4 | paywalled; preprint available | [arXiv:2412.12038](https://arxiv.org/abs/2412.12038) (v2 2025-09-24) | abstract + HTML v1 | Choose which cutting-plane separators to enable, per problem family, starting from a text description of the problem | SCIP and Gurobi | LLM (generative) prompted with problem description + separator summaries, outputs ensembled/clustered into a small portfolio | **Yes, configuration before solve** (separator on/off) | **very close** | Confirmed |
| 2 | GRIMIP: instance-specific configuration of MIP solvers using LLMs, Luo | 2026 | arXiv (OpenReview forum exists, venue/decision not readable) | [arXiv:2606.23299](https://arxiv.org/abs/2606.23299) | preprint available | arXiv | abstract + HTML v1 | Per-instance hyperparameter configuration | Gurobi 11.0.1, single thread | LLM (DeepSeek-V3.2-Exp main; GPT-4, Qwen3, gpt-oss-20b also) as the **probabilistic surrogate in Bayesian optimisation** (predicts mean and std), plus LLM "Automated Space Selection" pruning of the parameter set; ~10–12 solver evaluations per instance | **Yes, configuration before solve**, found by repeated solves of the same instance | **very close**: uses **PDI**, **ML4CO Item Placement and Load Balancing**, **MIPLIB**, all of which we use too | Confirmed |
| 3 | Multi-task Representation Learning for MILP, Cai | 2024 arXiv / 2025 | CPAIOR 2025, LNCS | 10.1007/978-3-031-95973-8_9 | paywalled; preprint available | [arXiv:2412.14409](https://arxiv.org/abs/2412.14409) | abstract | One embedding model for several MILP tasks | Gurobi and SCIP | Learned (graph-based) multi-task instance embeddings | Yes: branching + **solver configuration**, across two solvers | **very close** on "one learned model, several solvers, configuration" (not a language model) | Confirmed |
| 4 | Towards Foundation Models for MILP (MILP-Evolve), Li (Sirui) | 2024 arXiv / 2025 | ICLR 2025 | [arXiv:2410.08288](https://arxiv.org/abs/2410.08288); [ICLR page](https://iclr.cc/virtual/2025/poster/30856) | open | arXiv; code [microsoft/MILP-Evolve](https://github.com/microsoft/MILP-Evolve) | metadata + abstract (via secondary) | Train one model across many MILP classes; the LLM (GPT-4) *generates* the classes | not verified from the abstract (learning-to-branch task) | GNN with attention; LLM used only for data generation and a text–MILP alignment task | Yes, via learned branching (one of three tasks); no configuration | related | Strong evidence |
| 5 | MILP-Evo: closed-loop automatic design of MILP solvers, Nie | 2026 | arXiv | [arXiv:2607.18252](https://arxiv.org/abs/2607.18252) | preprint available | arXiv | abstract | Design cut selector + branching rule as code | SCIP (PySCIPOpt callbacks) | LLM program evolution with measured solver feedback | Yes, **replaces components** with evolved code (offline design) | related | Confirmed |
| 6 | LLM4Branch: LLM for discovering branching policies, Hou | 2026 | ICML 2026 (per arXiv comment, camera-ready pending) | [arXiv:2605.10401](https://arxiv.org/abs/2605.10401) | preprint available | arXiv | abstract | Branching policy as a program: LLM skeleton + parameters tuned by zeroth-order search | not named in the abstract; compared against CPU- and GPU-based approaches | LLM program synthesis | Yes, branching (offline design) | related | Confirmed |
| 7 | DHEvo: data–algorithm co-evolution of MILP heuristics, Zhang | 2025 | arXiv | [arXiv:2507.15615](https://arxiv.org/abs/2507.15615) | preprint available | arXiv | abstract | Evolve heuristics together with a representative instance subset, for generalisation within a class | not stated in the abstract | LLM heuristic evolution | Yes, heuristic code (offline) | related | Confirmed |
| 8 | EvoCut: strengthening IPs via evolution-guided LLMs, Yazdani | 2025 | arXiv | [arXiv:2508.11850](https://arxiv.org/abs/2508.11850) | preprint available | arXiv | metadata + snippet | Generate "acceleration cuts" for a MILP model | not verified | Multi-agent LLM + evolutionary search | Changes the model's constraints, not solver settings | background | Strong evidence |
| 9 | Agentic MIP Research: constraint handler generation, Xu (Liding) | 2026 | arXiv | [arXiv:2605.09186](https://arxiv.org/abs/2605.09186) | preprint available | arXiv | abstract | LLM agents generate, verify and benchmark SCIP constraint-handler plugins | SCIP (MIPLIB 2017) | LLM agents in a solver-aware sandbox harness | Yes, new plugin code (research automation, offline) | related: "an LLM agent operating a solver", but for development work, not live tuning | Confirmed |
| 10 | FunSearch: discoveries from program search with LLMs, Romera-Paredes | 2023 online / 2024 | Nature | 10.1038/s41586-023-06924-6 | open (hybrid OA per OpenAlex) | publisher | metadata | LLM + evaluator program search (cap set, bin packing heuristics) | none (not a MIP solver) | LLM program search | No | background | Strong evidence |
| 11 | Evolution of Heuristics (EoH), Liu (Fei) | 2024 | ICML 2024 (PMLR 235) | [arXiv:2401.02051](https://arxiv.org/abs/2401.02051) | open | arXiv / PMLR | metadata | LLM automatic heuristic design | none | LLM + evolution of "thoughts" and code | No | background | Strong evidence |
| 12 | ReEvo: LLMs as hyper-heuristics with reflective evolution, Ye | 2024 | NeurIPS 2024 | [arXiv:2402.01145](https://arxiv.org/abs/2402.01145) | open | arXiv | metadata | LLM heuristic generation for CO | none | LLM hyper-heuristic | No | background | Strong evidence |
| 13 | HeurAgenix: LLMs for complex CO, Yang (Xianliang) | 2025 | arXiv | [arXiv:2506.15196](https://arxiv.org/abs/2506.15196) | preprint available | arXiv | abstract | Evolve a pool of heuristics, then **select a heuristic online from the current state** | none (problem-specific heuristics; the benchmarks were not verified) | Selector is "a state-of-the-art LLM **or a fine-tuned lightweight model**" with a dual-reward fine-tuning | Online heuristic selection inside its own search, not a MIP solver | related: a small fine-tuned model choosing strategies online from a state description is close to our Track B | Confirmed |
| 14 | AutoSAT: optimise SAT solvers via LLMs, Sun (Yi-Wen) | 2024 arXiv / 2026 | JAIR | 10.1613/jair.1.20499 | open (JAIR) | [JAIR](https://www.jair.org/index.php/jair/article/view/20499); [arXiv:2402.10705](https://arxiv.org/abs/2402.10705) | metadata + snippet | LLM rewrites heuristics inside a CDCL solver (EasySAT); compared with MiniSat/Kissat and their parameter-tuned variants | SAT (EasySAT) | LLM code generation + hill climbing / (1+1)-EA | Yes, heuristic code (offline) | related (SAT, not MIP) | Strong evidence |
| 15 | Discovering heuristics in a complex SAT solver with LLMs (AutoModSAT), Sun (Yi-Wen) | 2025 arXiv / 2026 | Nature Communications | 10.1038/s41467-026-74949-2 | open | [arXiv:2507.22876](https://arxiv.org/abs/2507.22876); [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC13507263/) | metadata + snippet | Same line of work, scaled to a modularised complex solver | SAT | LLM code generation + prompt optimisation + presearch | Yes, heuristic code (offline) | related | Strong evidence |
| 16 | OptiMUS: scalable optimisation modelling with (MI)LP solvers and LLMs, AhmadiTeshnizi | 2024 | ICML 2024 | [arXiv:2402.10172](https://arxiv.org/abs/2402.10172) (also 2310.06116, OptiMUS-0.3 2407.19633) | open | arXiv | metadata | Natural language → MILP formulation + solver code, debugging from solver feedback | Gurobi-type solver calls (formulation only) | LLM agents | **No**: writes the model, never touches solver settings | background | Strong evidence |
| 17 | LLM-Enhanced Algorithm Selection (AS-LLM), Wu (Xingyu) | 2024 | IJCAI 2024 | 10.24963/ijcai.2024/579 | open | [IJCAI PDF](https://www.ijcai.org/proceedings/2024/0579.pdf); [arXiv:2311.13184](https://arxiv.org/abs/2311.13184) | metadata + snippet | Algorithm selection with LLM-derived **algorithm** representations (from code) fused with problem features | generic AS benchmarks | LLM embeddings + similarity module | No solver intervention; selection only | related | Strong evidence |
| 18 | ZeroFolio: algorithm selection with zero domain knowledge via text embeddings, Szeider | 2026 | arXiv | [arXiv:2604.19753](https://arxiv.org/abs/2604.19753) | preprint available | arXiv | abstract + HTML | Per-instance AS on 11 ASlib scenarios **including MIP-2016** (218 instances, 5 algorithms) | ASlib MIP-2016 (solver names not given in the paper) | **Frozen** pretrained text embeddings (Gemini-embedding, text-embedding-3-large, Qwen3-embedding-8b) of the raw instance file (10k chars, shuffled lines) + weighted kNN | Selection before solve | **very close** to "text encoder as selector"; differs: frozen embedding, raw file text, no solver state, no calibration, no GPU solver | Confirmed |
| 19 | Synthesizing Feature Extractors: agentic AS, Xia | 2026 | arXiv | [arXiv:2608.17170](https://arxiv.org/abs/2608.17170) | preprint available | arXiv | abstract | LLM agent writes feature-extractor code for CSP AS; beats mzn2feat **and transformer features** | 5 CP solvers, 3 domains | LLM agentic code synthesis | Selection before solve | related | Confirmed |
| 20 | Automatic Feature Learning for Essence (car sequencing), Pellegrino | 2024 | arXiv (venue not verified) | [arXiv:2409.15158](https://arxiv.org/abs/2409.15158) | open (CC BY) | arXiv | abstract | Choose model + solver combination per instance | CP/SAT back-ends via Essence | Language model features learned from the high-level instance text | Selection before solve | related (text-encoder AS for constraint solvers) | Confirmed |
| 21 | RouteLLM: learning to route LLMs from preference data, Ong | 2024 arXiv / 2025 | ICLR 2025 | [arXiv:2406.18665](https://arxiv.org/abs/2406.18665); [ICLR PDF](https://proceedings.iclr.cc/paper_files/paper/2025/file/5503a7c69d48a2f86fc00b3dc09de686-Paper-Conference.pdf) | open | ICLR proceedings | metadata + snippet | Route queries between a strong and a weak LLM | none | Routers incl. a BERT classifier | none | background (architectural precedent for an encoder router) | Strong evidence |
| 22 | GPU-Accelerated Primal Heuristics for MIP, Çördük | 2025 | NeurIPS 2025 | [arXiv:2510.20499](https://arxiv.org/abs/2510.20499); [NeurIPS page](https://neurips.cc/virtual/2025/133391) | open | arXiv / OpenReview PDF | metadata + snippet | GPU PDLP as approximate LP, probing cache, GPU FP/FJ/fix-and-propagate; 221 feasible on MIPLIB 2017 presolved | **cuOpt** | none | Is the solver (heuristics) | background (mechanism behind our cuOpt arms) | Strong evidence |
| 23 | PDLP: practical large-scale LP with PDHG, Applegate | 2021 | NeurIPS 2021 | [arXiv:2106.04756](https://arxiv.org/abs/2106.04756) | open | NeurIPS proceedings | metadata | First-order LP | PDLP (OR-Tools) | none | none | background | Strong evidence |
| 24 | cuPDLP.jl: GPU restarted PDHG for LP, Lu (Haihao) | 2023 arXiv / 2025 | Operations Research | 10.1287/opre.2024.1069 | paywalled; preprint available | [arXiv:2311.12180](https://arxiv.org/abs/2311.12180) | metadata (Crossref + S2) | GPU LP | cuPDLP | none | none | background | Strong evidence |
| 25 | Overview of GPU-based first-order methods for LP, Lu (Haihao) | 2025 | arXiv | [arXiv:2506.02174](https://arxiv.org/abs/2506.02174) | preprint available | arXiv | metadata + snippet | Survey of GPU FOMs (PDLP, cuPDLP, cuPDLPx) | several | none | none | background | Strong evidence |
| 26 | CHAP: a hybrid GPU-CPU heuristic for MIP, Tjusila | 2026 | arXiv | [arXiv:2605.05086](https://arxiv.org/abs/2605.05086) | preprint available | arXiv | abstract | GPU tabu search + cuPDLPx LP on the GPU; FP, fix-and-propagate and CPU tabu search on the CPU; **shared solution pool**; 47/50 on the 2026 Land–Doig competition set vs Gurobi 44, cuOpt 43 | own framework; compared against cuOpt, Gurobi | **none** (no learning) | Is a solver component | related (CPU+GPU cooperation, no learning) | Confirmed |
| 27 | Using a MIP Solver as a PDHG-Based MIP Heuristic, Rothberg | 2026 | arXiv | [arXiv:2607.14483](https://arxiv.org/abs/2607.14483) | preprint available | arXiv | abstract | Replace the LP solver inside a MIP solver's heuristics with low-accuracy PDHG | a "modern MIP solver" (not named in the abstract) | none | Internal LP swap | background | Confirmed |
| 28 | Race, Exchange, Improve (ReXi), Mexi | 2026 | arXiv | [arXiv:2609.05954](https://arxiv.org/abs/2609.05954) | preprint available | arXiv | abstract + HTML | Parallel portfolio racing with solution exchange for a fast primal; MIPFEAS benchmark, **primal integral** | 10 SCIP settings + LP-free local search + LNS workers; inside SCIP and standalone | **none**: fixed assignment, no adaptive selection | Parallel racing of fixed settings | related: same metric and the same "run copies / race settings" idea as our C4, with no learned selector | Confirmed |
| 29 | Parameter tuning with generalization guarantees for GPU LP, Prasad | 2026 | arXiv | [arXiv:2606.08638](https://arxiv.org/abs/2606.08638) | preprint available | arXiv | abstract | Data-driven tuning of (cu)PDLP step size, primal weight, etc.; sample-complexity bounds | (cu)PDLP | data-driven algorithm design (learning theory) | Parameter choice before solve (LP only) | related: **the only "learning on top of a GPU solver's parameters" item found** | Confirmed |
| 30 | PDHG-Unrolled L2O for large-scale LP (PDHG-Net), Li (Bingheng) | 2024 | ICML 2024, PMLR 235:29164–29180 | [PMLR](https://proceedings.mlr.press/v235/li24ce.html); [arXiv:2406.01908](https://arxiv.org/abs/2406.01908) | open | PMLR | metadata + snippet | Neural warm start, then PDLP polishes | PDLP | Unrolled PDHG network | Warm start (LP) | background | Strong evidence |
| 31 | learning-to-configure-optimization-solvers (GitHub), "Jors Academy" | 2026 (repo created 2026-09-17) | GitHub, no paper | [repo](https://github.com/jorsacademy/learning-to-configure-optimization-solvers) | open (MIT) | GitHub | README + GitHub API | Per-instance choice among six **HiGHS** configurations from cheap static features, scored by regret | **HiGHS** | Random-forest runtime regression | Configuration before solve | related: the only "ML with HiGHS" item found; weak provenance (anonymous, 0 stars, synthetic set cover) | Confirmed (exists), Unknown (quality) |
| 32 | LLMs for Combinatorial Optimization: A Systematic Review, Da Ros | 2025 arXiv / 2026 | ACM Computing Surveys 58(11), art. 272 | 10.1145/3801961 | open (S2 lists publisher OA link) | [ACM](https://dl.acm.org/doi/10.1145/3801961); [arXiv:2507.03637](https://arxiv.org/abs/2507.03637) | metadata + snippet | PRISMA review, 103 studies | — | survey | — | background (positioning) | Strong evidence |
| 33 | ML-augmented branch and bound for MILP (survey), Scavuzzo | 2024 | Mathematical Programming | 10.1007/s10107-024-02130-y | open (hybrid OA, Springer) | [Springer](https://link.springer.com/article/10.1007/s10107-024-02130-y); [arXiv:2402.05501](https://arxiv.org/abs/2402.05501) | metadata + snippet | Survey: branching, cuts, node selection, heuristics, **configuration** | mainly SCIP | survey | — | background | Strong evidence |
| 34 | Machine learning algorithms in MIP (PhD thesis), Zarpellon | 2020 | PhD, Polytechnique Montréal (adv. A. Lodi) | [PolyPublie 5332](https://publications.polymtl.ca/5332/) | open | [PDF](https://publications.polymtl.ca/5332/1/2020_Zarpellon,_Giulia.pdf) | repository record | Learned branching and related B&B decisions | SCIP / CPLEX-era work | various | In-solver | background (thesis) | Strong evidence |
| 35 | Algorithmic Configuration by Learning and Optimization (PhD thesis), Iommazzo | 2021 | PhD, École Polytechnique + Univ. Pisa (NNT 2021IPPAX105) | [LIX PDF](https://www.lix.polytechnique.fr/Labo/Gabriele.Iommazzo/phd_thesis_iommazzo.pdf) | open | LIX / depositolegale.it | repository record + snippet | Per-instance solver configuration: learn a performance function, then optimise over configurations with a MP formulation | CPLEX (per his hydro-UC papers; not re-verified here) | ML performance model + MP | Configuration before solve | related (thesis on exactly the configuration problem) | Strong evidence |
| 36 | Cutting Plane Selection for MILP (PhD thesis), Turner (Mark-Ruben) | defended 2023-12-01 | PhD, TU Berlin (adv. T. Koch) | [DepositOnce](https://depositonce.tu-berlin.de/items/8caa0d04-146d-4ec2-b69a-766687ca16b5); [ZIB OPUS](https://opus4.kobv.de/opus4-zib/frontdoor/index/index/docId/9326) | open | DepositOnce | ZIB news + repository record | Cut selection incl. adaptive/learned scoring parameters | SCIP | learned cut-selector parameters (per his adaptive cut selection papers) | In-solver parameters | background (thesis) | Strong evidence |

Counts: 36 entries. **Open (venue OA, OA proceedings, open repository or open GitHub): 19. Preprint available only (arXiv): 14. Publisher paywalled but a legal
preprint exists: 3** (#1, #3, #24). **Paywalled with no legal copy: 0.**

## 2. Paywalled items without a legal copy

Moved to [[Paywalled research]], the single home for paywalled works (disclaimer, evidence, what to request).

## 3. Closest prior art to our project

**An LLM configuring a MIP solver. Two direct precedents, both single-solver and both generative LLMs:**

1. **GRIMIP (Luo et al., arXiv 2606.23299, 2026) is the closest and must be cited and set apart explicitly.**
   It configures Gurobi per instance and reports **PDI** on **ML4CO Item Placement, ML4CO Load Balancing and
   MIPLIB**, which overlaps heavily with our instance sets and our secondary metric. Differences: (a) one solver
   (Gurobi), not a portfolio across HiGHS/SCIP/cuOpt; (b) configuration is found by **~10–12 solver evaluations of
   the same instance** (LLM-as-BO-surrogate). That is per-instance tuning by repeated solves, not a single
   prediction made inside one wall-clock budget. (c) A large hosted/open LLM, not a 421M encoder with calibrated
   outputs. (d) No mid-solve switching. Their "over 40 % PDI reduction on hard sets" is measured against
   defaults/tuners **after** the tuning solves, so it is not comparable to our one-shot numbers.
2. **Lawless et al. (CPAIOR 2025)**: cold-start separator configuration for SCIP and Gurobi from a text
   description of the problem family. It is per family, not per instance, and covers separators only. It has no trace training and no calibration.

**One learned model configuring more than one MIP solver:**
3. **Cai, Huang & Dilkina (CPAIOR 2025)**: one multi-task embedding used for branching **and configuration**
   on Gurobi and SCIP. It is the nearest thing to "one learned selector across solvers" we found. It is a graph
   embedding, not a language model, it does not include a GPU solver, and it does not choose between solvers.

**A small or frozen text encoder as an algorithm selector:**
4. **ZeroFolio (Szeider, 2026)**: frozen pretrained text embeddings of the raw instance file + kNN beat
   RF-on-features in 9/11 ASlib scenarios, **MIP-2016 included**. It is the closest precedent for "a text encoder
   selects the solver". Differences: frozen large embedding APIs, no fine-tuning, no solver-state text, argmax kNN (no
   calibrated probabilities), selection only. Related: Pellegrino et al. (2024, language-model features for Essence
   model+solver choice) and Xia et al. (2026, LLM-synthesised feature extractors that beat transformer features).
   RouteLLM remains the architectural precedent for a BERT-class router.
5. **HeurAgenix (Yang et al., 2025)**: an online selector that picks a heuristic from the current search state,
   and which may be **a fine-tuned lightweight model** instead of an LLM. This is conceptually the closest thing to
   Laya-as-Track-B-controller, but it works inside its own CO heuristics framework, not a MIP solver.

**CPU+GPU solver cooperation with learning: nothing found.** cuOpt itself (Çördük et al.: GPU heuristics, CPU
dual bound), CHAP (a GPU+CPU shared pool) and ReXi (parallel racing of SCIP settings, scored by primal integral)
are all hand-designed. The only learning on top of a GPU solver is Prasad & Sharma (PDLP LP parameters, with
theory) and PDHG-Net (a neural warm start for PDLP). **Learned selection or scheduling between a CPU B&C solver and a GPU
heuristic solver, which is our HiGHS‖cuOpt finding (C4), has no precedent in this sweep.**

**LLM agents operating a solver live: none found for MIP tuning within a single wall-clock budget.** The agentic
work either writes code offline (MILP-Evo, LLM4Branch, DHEvo, Agentic MIP Research, EvoCut, AutoSAT) or writes the model
(OptiMUS). GRIMIP is iterative, but across repeated solves.

**Not found:** any work where a BERT-class or ModernBERT-class encoder, fine-tuned or not, chooses or tunes MIP
solver settings. Any learned selector over a portfolio that contains a GPU MIP solver. Any HiGHS-specific learning
paper (only an anonymous GitHub benchmark, #31).

## 4. Candidates to request from authors or through a library (do NOT contact anyone)

Moved to [[Paywalled research]], the single home for paywalled works (disclaimer, evidence, what to request).

## Bib keys to add if cited (not yet in `paper/refs.bib`)

`luo2026grimip` and `lawless2025llm` are already in Related work §9. New candidates: `cai2025multitask`,
`szeider2026zerofolio`, `yang2025heuragenix`, `li2025foundation` (MILP-Evolve), `mexi2026rexi`, `tjusila2026chap`,
`prasad2026pdlptuning`, `nie2026milpevo`, `hou2026llm4branch`.
