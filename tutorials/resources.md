# Reading list: MIP, solver control, and learning to choose

A reading list for people learning the background to this project. Every entry was checked on 2026-09-23 against
Crossref, OpenAlex, DataCite (arXiv), the publisher's page or the author's own page. Links marked **(open)** go to a free,
legal copy that was opened and checked. **(paywalled)** means the publisher's copy is behind a subscription and no free
copy was verified; a university library will usually have it.

## (a) Integer programming foundations

### Books

- **Wolsey, L. A. *Integer Programming*, 2nd ed. Wiley, 2020.** doi:[10.1002/9781119606475](https://doi.org/10.1002/9781119606475) (paywalled)
  — The shortest route to a working understanding of formulations, relaxations, branch-and-bound and cutting planes. Start here.
- **Nemhauser, G. L. & Wolsey, L. A. *Integer and Combinatorial Optimization*. Wiley, 1988.** doi:[10.1002/9781118627372](https://doi.org/10.1002/9781118627372) (paywalled)
  — The standard reference on polyhedral theory and valid inequalities; dense, use it for depth after Wolsey.
- **Conforti, M., Cornuéjols, G. & Zambelli, G. *Integer Programming*. Graduate Texts in Mathematics, Springer, 2014.** doi:[10.1007/978-3-319-11008-0](https://doi.org/10.1007/978-3-319-11008-0) (paywalled)
  — A modern, rigorous graduate text; the best treatment of cutting-plane theory (Gomory, split, lift-and-project).
- **Schrijver, A. *Theory of Linear and Integer Programming*. Wiley, 1986.** ISBN 978-0-471-98232-6. [Publisher page](https://www.wiley.com/en-us/Theory+of+Linear+and+Integer+Programming-p-9780471982326) (paywalled)
  — The theory reference (complexity, polyhedra, total unimodularity) with extensive historical notes.
- **Bertsimas, D. & Tsitsiklis, J. N. *Introduction to Linear Optimization*. Athena Scientific, 1997.** ISBN 978-1-886529-19-9. [Publisher page](http://www.athenasc.com/linoptbook.html) (paywalled)
  — Linear programming done well: simplex, duality, sensitivity; the LP relaxation is the engine inside every MIP solver.

### Papers

- **Dantzig, G., Fulkerson, R. & Johnson, S. "Solution of a Large-Scale Traveling-Salesman Problem." *Journal of the Operations Research Society of America* 2(4):393–410, 1954.** doi:[10.1287/opre.2.4.393](https://doi.org/10.1287/opre.2.4.393) (paywalled)
  — The first cutting-plane computation: a 49-city TSP solved by adding inequalities as they were needed.
- **Gomory, R. E. "Outline of an Algorithm for Integer Solutions to Linear Programs." *Bulletin of the AMS* 64(5):275–278, 1958.** doi:[10.1090/S0002-9904-1958-10224-4](https://doi.org/10.1090/S0002-9904-1958-10224-4) — [AMS PDF](https://www.ams.org/bull/1958-64-05/S0002-9904-1958-10224-4/S0002-9904-1958-10224-4.pdf) (open)
  — Four pages that introduced general-purpose cutting planes; Gomory cuts are still in every solver.
- **Land, A. H. & Doig, A. G. "An Automatic Method of Solving Discrete Programming Problems." *Econometrica* 28(3):497–520, 1960.** doi:[10.2307/1910129](https://doi.org/10.2307/1910129) (paywalled)
  — The origin of branch-and-bound, the tree search that every modern MIP solver runs.
- **Achterberg, T. *Constraint Integer Programming*. PhD thesis, TU Berlin, 2007.** doi:[10.14279/depositonce-1634](https://doi.org/10.14279/depositonce-1634) (open)
  — The design document of SCIP: branching, node selection, conflict analysis and the plugin architecture this project controls.
- **Lodi, A. "Mixed Integer Programming Computation." In *50 Years of Integer Programming 1958–2008*, Springer, 2010, pp. 619–645.** doi:[10.1007/978-3-540-68279-0_16](https://doi.org/10.1007/978-3-540-68279-0_16) (paywalled)
  — A survey of which solver components (presolve, cuts, heuristics, branching) actually made MIP practical.
- **Koch, T., Achterberg, T., Andersen, E., et al. "MIPLIB 2010." *Mathematical Programming Computation* 3(2):103–163, 2011.** doi:[10.1007/s12532-011-0025-9](https://doi.org/10.1007/s12532-011-0025-9) (paywalled)
  — How a benchmark library is built and why instance selection matters.
- **Gleixner, A., Hendel, G., Gamrath, G., et al. "MIPLIB 2017: Data-Driven Compilation of the 6th Mixed-Integer Programming Library." *Mathematical Programming Computation* 13(3):443–490, 2021.** doi:[10.1007/s12532-020-00194-3](https://doi.org/10.1007/s12532-020-00194-3) — [Springer, CC BY 4.0](https://link.springer.com/article/10.1007/s12532-020-00194-3) (open)
  — The benchmark set used in this project; read the sections on instance features and the benchmark-set selection.
- **Bixby, R. E. "A Brief History of Linear and Mixed-Integer Programming Computation." *Documenta Mathematica*, Extra Volume: Optimization Stories, 2012, pp. 107–121.** doi:[10.4171/dms/6/16](https://doi.org/10.4171/dms/6/16) — [EMS Press](https://ems.press/books/dms/251/4927) (open)
  — A first-hand account of how LP and MIP solvers became millions of times faster, and how much of that came from algorithms rather than hardware.
- **Achterberg, T. & Wunderling, R. "Mixed Integer Programming: Analyzing 12 Years of Progress." In *Facets of Combinatorial Optimization*, Springer, 2013, pp. 449–481.** doi:[10.1007/978-3-642-38189-8_18](https://doi.org/10.1007/978-3-642-38189-8_18) (paywalled)
  — Measures, component by component, what each CPLEX feature is worth; the model for an ablation study of a solver.

## (b) Solvers and benchmarking

- **The SCIP Optimization Suite 9.0** (Bolusani, S., Besançon, M., Bestuzheva, K., et al.), 2024. [arXiv:2402.17702](https://arxiv.org/abs/2402.17702) (open)
  and **The SCIP Optimization Suite 10.0** (Hojny, C., Besançon, M., Bestuzheva, K., et al.), 2025. [arXiv:2511.18580](https://arxiv.org/abs/2511.18580) (open)
  — The release reports of the solver we control; each lists what changed and what it is worth on benchmarks. Project site: [scipopt.org](https://www.scipopt.org/).
- **Huangfu, Q. & Hall, J. A. J. "Parallelizing the Dual Revised Simplex Method." *Mathematical Programming Computation* 10(1):119–142, 2018.** doi:[10.1007/s12532-017-0130-5](https://doi.org/10.1007/s12532-017-0130-5) — [Springer, CC BY 4.0](https://link.springer.com/article/10.1007/s12532-017-0130-5) (open)
  — The LP engine inside HiGHS. The HiGHS MIP solver itself has no journal paper; see [highs.dev](https://highs.dev/) (open).
- **NVIDIA cuOpt documentation.** [docs.nvidia.com/cuopt](https://docs.nvidia.com/cuopt/) (open)
  — The GPU solver in our portfolio: its PDLP-based LP and GPU primal heuristics for MILP.
- **Lodi, A. & Tramontani, A. "Performance Variability in Mixed-Integer Programming." In *Theory Driven by Influential Applications*, INFORMS TutORials in Operations Research, 2013, pp. 1–12.** doi:[10.1287/educ.2013.0112](https://doi.org/10.1287/educ.2013.0112) (paywalled; no free copy verified)
  — Why a solver's runtime changes when you permute rows or change a seed, and why one run per instance can mislead. Essential before reading any benchmark table, including ours.
- **Berthold, T. "Measuring the Impact of Primal Heuristics." *Operations Research Letters* 41(6):611–614, 2013.** doi:[10.1016/j.orl.2013.08.007](https://doi.org/10.1016/j.orl.2013.08.007) — [ZIB-Report 13-17](https://opus4.kobv.de/opus4-zib/frontdoor/index/index/docId/1788) (open)
  — Defines the primal integral, the main metric in this project: it rewards finding good solutions early, not only proving optimality.
- **Mittelmann, H. D. Benchmarks for Optimization Software.** [plato.asu.edu/bench.html](https://plato.asu.edu/bench.html) (open)
  — Long-running independent comparisons of LP/MIP solvers; useful for seeing how solvers rank and how the ranking moves.

## (c) Machine learning for combinatorial optimization

- **Bengio, Y., Lodi, A. & Prouvost, A. "Machine Learning for Combinatorial Optimization: A Methodological Tour d'Horizon." *European Journal of Operational Research* 290(2):405–421, 2021.** doi:[10.1016/j.ejor.2020.07.063](https://doi.org/10.1016/j.ejor.2020.07.063) — [arXiv:1811.06128](https://arxiv.org/abs/1811.06128) (open)
  — The map of the field: learning to imitate expensive decisions vs. learning from experience, and where ML can sit in a solver.
- **Scavuzzo, L., Aardal, K., Lodi, A. & Yorke-Smith, N. "Machine Learning Augmented Branch and Bound for Mixed Integer Linear Programming." *Mathematical Programming* 217:123–166, 2026 (online 2024).** doi:[10.1007/s10107-024-02130-y](https://doi.org/10.1007/s10107-024-02130-y) — [arXiv:2402.05501](https://arxiv.org/abs/2402.05501) (open; the journal version is also CC BY)
  — A recent survey of learned components inside branch-and-bound: branching, node selection, cuts and heuristics.
- **Khalil, E. B., Le Bodic, P., Song, L., Nemhauser, G. & Dilkina, B. "Learning to Branch in Mixed Integer Programming." AAAI 2016.** doi:[10.1609/aaai.v30i1.10080](https://doi.org/10.1609/aaai.v30i1.10080) (open)
  — An early learned branching rule, trained on the fly for each instance.
- **Khalil, E. B., Dilkina, B., Nemhauser, G. L., Ahmed, S. & Shao, Y. "Learning to Run Heuristics in Tree Search." IJCAI 2017, pp. 659–666.** doi:[10.24963/ijcai.2017/92](https://doi.org/10.24963/ijcai.2017/92) (open)
  — Learns when to run a primal heuristic at a node: an in-solver control decision, close to this project's Track B.
- **Gasse, M., Chételat, D., Ferroni, N., Charlin, L. & Lodi, A. "Exact Combinatorial Optimization with Graph Convolutional Neural Networks." NeurIPS 2019.** [arXiv:1906.01629](https://arxiv.org/abs/1906.01629) (open)
  — Introduced the bipartite variable–constraint graph representation of a MIP that most later work uses.
- **Nair, V., Bartunov, S., Gimeno, F., et al. "Solving Mixed Integer Programs Using Neural Networks." 2020.** [arXiv:2012.13349](https://arxiv.org/abs/2012.13349) (open)
  — Learned branching and learned diving at industrial scale; shows what large training budgets buy.
- **Gasse, M., Cappart, Q., et al. "The Machine Learning for Combinatorial Optimization Competition (ML4CO): Results and Insights." NeurIPS 2021 Competitions and Demonstrations Track, PMLR 176:220–231, 2022.** [arXiv:2203.02433](https://arxiv.org/abs/2203.02433) (open). Competition page: [ecole.ai/2021/ml4co-competition](https://www.ecole.ai/2021/ml4co-competition/) (open)
  — Source of the item-placement and load-balancing instances we use; the "configuration" task is our problem in a competition setting.
- **Prouvost, A., Dumouchelle, J., Scavuzzo, L., Gasse, M., Chételat, D. & Lodi, A. "Ecole: A Gym-like Library for Machine Learning in Combinatorial Optimization Solvers." 2020.** [arXiv:2011.06069](https://arxiv.org/abs/2011.06069) (open). Project: [ecole.ai](https://www.ecole.ai/) (open)
  — How to expose SCIP's decisions as a reinforcement-learning environment.

## (d) Algorithm selection and configuration

- **Rice, J. R. "The Algorithm Selection Problem." *Advances in Computers* 15:65–118, 1976.** doi:[10.1016/S0065-2458(08)60520-3](https://doi.org/10.1016/S0065-2458(08)60520-3) (paywalled) — the 1975 Purdue technical report of the same title: [docs.lib.purdue.edu/cstech/99](https://docs.lib.purdue.edu/cstech/99/) (open)
  — The founding formulation: problem space, feature space, algorithm space, performance space. Our per-instance selector is exactly this.
- **Gomes, C. P. & Selman, B. "Algorithm Portfolios." *Artificial Intelligence* 126(1–2):43–62, 2001.** doi:[10.1016/S0004-3702(00)00081-3](https://doi.org/10.1016/S0004-3702(00)00081-3) — [Elsevier open archive](https://www.sciencedirect.com/science/article/pii/S0004370200000813) (open)
  — Why running several algorithms in parallel beats picking one when runtimes are heavy-tailed; the idea behind our parallel-copies results.
- **Birattari, M., Stützle, T., Paquete, L. & Varrentrapp, K. "A Racing Algorithm for Configuring Metaheuristics." GECCO 2002, Morgan Kaufmann, pp. 11–18.** [Author copy](https://eden.dei.uc.pt/~paquete/papers/gecco2002.pdf) (open)
  — F-Race: evaluate candidate configurations on instances one at a time and drop the losers early with a statistical test.
- **Xu, L., Hutter, F., Hoos, H. H. & Leyton-Brown, K. "SATzilla: Portfolio-based Algorithm Selection for SAT." *JAIR* 32:565–606, 2008.** doi:[10.1613/jair.2490](https://doi.org/10.1613/jair.2490) (open)
  — The system that made per-instance selection win competitions; its feature and runtime-model design is still the template.
- **Hutter, F., Hoos, H. H., Leyton-Brown, K. & Stützle, T. "ParamILS: An Automatic Algorithm Configuration Framework." *JAIR* 36:267–306, 2009.** doi:[10.1613/jair.2861](https://doi.org/10.1613/jair.2861) (open)
  — Local search in parameter space; together with the next two entries, the standard way to tune a solver offline.
- **Hutter, F., Hoos, H. H. & Leyton-Brown, K. "Automated Configuration of Mixed Integer Programming Solvers." CPAIOR 2010, LNCS, pp. 186–202.** doi:[10.1007/978-3-642-13520-0_23](https://doi.org/10.1007/978-3-642-13520-0_23) — [author copy](https://www.cs.ubc.ca/~hutter/papers/10-CPAIOR-MIP-Config.pdf) (open)
  — Offline tuning of CPLEX, Gurobi and lpsolve: large speed-ups from parameters alone.
- **Hutter, F., Hoos, H. H. & Leyton-Brown, K. "Sequential Model-Based Optimization for General Algorithm Configuration." LION 5, LNCS, 2011, pp. 507–523.** doi:[10.1007/978-3-642-25566-3_40](https://doi.org/10.1007/978-3-642-25566-3_40) — [author copy](https://www.cs.ubc.ca/labs/algorithms/Projects/SMAC/papers/11-LION5-SMAC.pdf) (open)
  — SMAC: Bayesian optimisation with random forests for configuration.
- **López-Ibáñez, M., Dubois-Lacoste, J., Pérez Cáceres, L., Birattari, M. & Stützle, T. "The irace Package: Iterated Racing for Automatic Algorithm Configuration." *Operations Research Perspectives* 3:43–58, 2016.** doi:[10.1016/j.orp.2016.09.002](https://doi.org/10.1016/j.orp.2016.09.002) (open; open-access journal)
  — The practical successor to F-Race, with a widely used R package.
- **Kotthoff, L. "Algorithm Selection for Combinatorial Search Problems: A Survey."** *AI Magazine* 35(3):48–60, 2014, doi:[10.1609/aimag.v35i3.2460](https://doi.org/10.1609/aimag.v35i3.2460); extended version in *Data Mining and Constraint Programming*, LNCS, Springer, 2016, pp. 149–190, doi:[10.1007/978-3-319-50137-6_7](https://doi.org/10.1007/978-3-319-50137-6_7). [arXiv:1210.7959](https://arxiv.org/abs/1210.7959) (open)
  — A readable survey of selector designs: classification, regression, pairwise models, schedules.
- **Bischl, B., Kerschke, P., Kotthoff, L., et al. "ASlib: A Benchmark Library for Algorithm Selection." *Artificial Intelligence* 237:41–58, 2016.** doi:[10.1016/j.artint.2016.04.003](https://doi.org/10.1016/j.artint.2016.04.003) — [arXiv:1506.02465](https://arxiv.org/abs/1506.02465) (open)
  — How to report selectors fairly: the virtual best solver, the single best solver and the closed-gap measure we use.
- **Kerschke, P., Hoos, H. H., Neumann, F. & Trautmann, H. "Automated Algorithm Selection: Survey and Perspectives." *Evolutionary Computation* 27(1):3–45, 2019.** doi:[10.1162/evco_a_00242](https://doi.org/10.1162/evco_a_00242) — [arXiv:1811.11597](https://arxiv.org/abs/1811.11597) (open)
  — The most complete recent survey, covering continuous as well as discrete problems.

## (e) Bandits and online learning

- **Auer, P., Cesa-Bianchi, N. & Fischer, P. "Finite-time Analysis of the Multiarmed Bandit Problem." *Machine Learning* 47(2–3):235–256, 2002.** doi:[10.1023/A:1013689704352](https://doi.org/10.1023/A:1013689704352) — [Springer PDF](https://link.springer.com/content/pdf/10.1023/A:1013689704352.pdf) (open; free on the publisher site)
  — UCB1, the index policy behind the online bandit agent in this project.
- **Lattimore, T. & Szepesvári, C. *Bandit Algorithms*. Cambridge University Press, 2020.** doi:[10.1017/9781108571401](https://doi.org/10.1017/9781108571401) — [free online edition (PDF)](https://tor-lattimore.com/downloads/book/book.pdf) (open)
  — The modern textbook; the free edition matches the print one apart from corrected typos.
- **Sutton, R. S. & Barto, A. G. *Reinforcement Learning: An Introduction*, 2nd ed. MIT Press, 2018.** — [book page with full PDF](http://incompleteideas.net/book/the-book-2nd.html) (open)
  — The standard introduction to RL; chapter 2 covers bandits, later chapters the sequential control setting of in-solver decisions.

## (f) Free courses

- **MIT OpenCourseWare 15.083J "Integer Programming and Combinatorial Optimization"** (Fall 2009; Bertsimas, Schulz). [ocw.mit.edu](https://ocw.mit.edu/courses/15-083j-integer-programming-and-combinatorial-optimization-fall-2009/) (open)
  — Graduate lecture notes on formulations, polyhedra, cuts and branch-and-bound.
- **MIT OpenCourseWare 6.251J "Introduction to Mathematical Programming"** (Fall 2009; Bertsimas). [ocw.mit.edu](https://ocw.mit.edu/courses/6-251j-introduction-to-mathematical-programming-fall-2009/) (open)
  — The LP course that pairs with Bertsimas & Tsitsiklis.
