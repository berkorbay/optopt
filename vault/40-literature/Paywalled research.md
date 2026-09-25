---
tags: [literature, paywalled]
updated: 2026-09-23
---

# Paywalled research

> **Disclaimer.** The works below are behind publisher paywalls and **we have not read them in full**. No legal free
> copy was found (preprint, accepted manuscript, repository or author copy, thesis, earlier conference version). They are
> listed because they matter for this research. Each was found either through accessible papers that cite or describe it,
> or judged relevant from its public abstract and metadata. What we say about each one is limited to what those sources
> state; the evidence class says how far that goes. Nothing here was obtained by bypassing a paywall.

This is the **only** place for paywalled literature. Every other note, the paper body and the tutorials point here.
If a legal free copy turns up later, the work moves out of this note into [[Related work]] with the link.
Search protocol and evidence classes: [[Prior art]]. Paper counterpart: appendix subsection *Paywalled research*
(`app:paywalled`).

| class | meaning |
|---|---|
| **Strong evidence** | abstract plus citing papers clearly describe the method |
| **Likely** | metadata strongly suggests it; the implementation is unclear |
| **Unknown** | not enough public information |

## Cited in the paper (appendix `app:paywalled` only)
| Paper | Year | DOI | Why it matters to us | Evidence | Known from |
|---|---|---|---|---|---|
| ISAC — Kadioglu, Malitsky, Sellmann, Tierney (ECAI, FAIA 215) | 2010 | 10.3233/978-1-60750-606-5-751 | per-instance configuration: cluster features (g-means), tune one configuration per cluster (GGA), assign a new instance to its nearest cluster; CPLEX among its targets | Strong evidence | Hydra-MIP full text (reuses "the six configurations found by GGA"); algorithm-selection surveys |
| 3S, Algorithm Selection and Scheduling — Kadioglu, Malitsky, Sabharwal, Samulowitz, Sellmann (CP, LNCS 6876) | 2011 | 10.1007/978-3-642-23786-7_35 | k-NN selection plus a fixed pre-schedule of short solver runs computed by an integer program; evaluated on SAT; close to our parallel copies, but sequential | Strong evidence | Crossref metadata, citing literature |
| Carvajal, Ahmed, Nemhauser, Furman, Goel, Shao (ORL 42(2)) | 2014 | 10.1016/j.orl.2013.12.012 | differently configured copies of one MILP solver run in parallel and share information; gains on MIPLIB 2010; nothing learned | Strong evidence | publisher abstract as quoted by search results |
| Kruber, Lübbecke, Parmentier (CPAIOR, LNCS) | 2017 | 10.1007/978-3-319-59776-8_16 | supervised learning decides per instance whether a Dantzig-Wolfe reformulation in GCG pays off, and which decomposition to use | Likely | Crossref; one citing paper (arXiv 2310.07068, snippet only) |
| Bonami, Lodi, Zarpellon (CPAIOR, LNCS 10848) | 2018 | 10.1007/978-3-319-93031-2_43 | learned per-instance strategy choice inside CPLEX (linearise a convex MIQP or not) | Strong evidence | Springer abstract; the authors' later journal version (Optimization Online preprint). GERAD G-2017-106 exists, PolyPublie copy staff-only |
| Lodi & Zarpellon, On learning and branching: a survey (TOP 25(2)) | 2017 | 10.1007/s11750-017-0451-6 | the reference survey of learning for variable and node selection | Strong evidence | Springer abstract; cited as the reference survey by Scavuzzo et al. 2022/2024 (open) |
| Lodi & Tramontani, Performance variability in MIP (INFORMS TutORials) | 2013 | 10.1287/educ.2013.0112 | the standard account of run-to-run variability under seeds and permutations; behind our multi-seed oracle and parallel copies | Strong evidence | citing literature. OpenAlex tags it "gold", but INFORMS blocks automated access and Crossref has no licence — not confirmed |
| Achterberg & Berthold, Hybrid branching (CPAIOR, LNCS) | 2009 | 10.1007/978-3-642-01929-6_23 | SCIP's non-learned combination of pseudocost, inference, conflict and cutoff scores | Strong evidence | Crossref, ZIB talk slides, citing work (arXiv 2306.06050) |

## Listed here only (background, not cited)
| Paper | Year | DOI | Relevance | Evidence | Known from |
|---|---|---|---|---|---|
| O'Mahony et al., CPHydra (AICS) | 2008 | — | k-NN / case-based selection with scheduling | Strong evidence | algorithm-selection surveys; only a ResearchGate listing, no verified copy |
| Lin et al., T-BranT (Knowledge-Based Systems) | 2022 | 10.1016/j.knosys.2022.109455 | transformer branching policy (attention across candidates, tree-encoded history), imitation on MIPLIB/CORAL, SCIP | Strong evidence | ScienceDirect abstract; official GitHub repository |
| Wang, Blackley, Tang, RAIL (DASFAA, LNCS) | 2022 | 10.1007/978-3-031-00126-0_51 | RL + generative adversarial imitation learning for a B&B search policy. A 2025 ASOC follow-up (10.1016/j.asoc.2025.112690) is paywalled too, abstract not retrieved | Likely | Springer abstract |
| Masti & Bemporad (ECC) | 2019 | 10.23919/ecc.2019.8795808 | learned binary warm starts for a purpose-built B&B in repeated MPC solves | Likely | IEEE Xplore abstract via a search listing |
| Amadini, Gabbrielli, Mauro, Portfolio approaches for constraint optimization problems (Annals of Math. and AI) | 2016 | 10.1007/s10472-015-9459-5 | journal version of the LION 2014 study (anytime-scored COP portfolios with a MIP back-end); the LION author copy was read, the journal version not | Strong evidence | LION 2014 author copy; abstract |
| Lu et al., Learning SMT algorithm selection with high-level natural-language descriptions (FoIKS, LNCS) | 2026 | 10.1007/978-3-032-21540-6_23 | text encoder for solver selection (SMT); its open CP 2026 sibling covers the method | Likely | Semantic Scholar metadata; CP 2026 paper |
| Hurley et al., Multi-language evaluation of exact solvers in graphical model discrete optimization (Constraints 21(3)) | 2016 | 10.1007/s10601-016-9245-y | CPLEX inside a learned cross-language portfolio; a HAL record (hal-02633083) exists but whether it holds the full text was not checked — move out if it does | Strong evidence | authors' open slides; metadata |

## Paywalled at the publisher, read through a legal copy (not in this list's scope)
DASH (EJOR; arXiv 1307.4689), Hendel's solving phases (OR Proc.; ZIB OPUS), Berthold, Hendel & Koch (OMS; ZIB-Report 16-78),
Lawless et al. and Cai, Huang & Dilkina (CPAIOR 2025; arXiv), Rice 1976 (Advances in Computers; the 1975 Purdue technical
report), and the rest recorded in [[Open access audit]]. Where the version of record might differ, that is noted there.
Malitsky's book chapter on DASH (*Instance-Specific Algorithm Configuration*, Springer 2014, 10.1007/978-3-319-11230-5_8)
was not read; its content is covered by the DASH preprint.

## Worth obtaining legally
Library, BSB, Fernleihe, SUBITO, or an author request. **Only Berk sends such requests; agents contact no one.**
1. DASH, EJOR version of record — the strongest result against "don't switch"; check for experiments beyond the 2013 preprint.
2. ISAC (2010) and 3S (2011) — the per-instance and schedule precedents.
3. Carvajal et al. 2014 — the exact configurations used in the diversification, for C4.
4. Bonami, Lodi, Zarpellon 2018 and the 2022 Operations Research follow-up (10.1287/opre.2022.2267) — features and labelling.
5. Lodi & Tramontani 2013 — variability, behind C4.
6. Lower priority: Kruber 2017, Lodi & Zarpellon 2017 (with its comments and rejoinder), Hybrid branching 2009, the
   Lawless and Cai camera-ready versions, GRIMIP's OpenReview thread.
