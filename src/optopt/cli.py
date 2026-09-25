"""`optopt <command> [args]` — thin dispatcher to the library's runnable modules. Run it inside a workspace
(or set OPTOPT_HOME); see optopt.paths.

  optopt run INSTANCE STRATEGY --budget S --out FILE     one solver run -> trace JSON
  optopt pool jobs/<file>.jsonl --pin 5,6 --mem-cap-gb 8  pinned, memory-capped pool of runs
  optopt pair jobs/miplib.jsonl --arms race,g2c           SCIP || cuOpt / evolutionary partner, with exchange
  optopt jobs miplib|ml4co|uc                             build job files from data/
  optopt check traces/sol/<set>                           independent solution checker (exact arithmetic)
  optopt analyse <module> [args]                          any optopt.analysis module, e.g. `optopt analyse b3`
  optopt experiment <module> [args]                       any optopt.experiments module, e.g. `selection`
  optopt reproduce                                        regenerate every derived table from traces/ and compare
  optopt fetch miplib|pglib|ml4co                         get the public instance sets into data/
"""
import runpy
import sys

COMMANDS = {
    "run": "optopt.experiments.run_one",
    "pool": "optopt.experiments.pool",
    "pair": "optopt.experiments.xchg_pair",
    "jobs": "optopt.experiments.make_jobs",
    "check": "optopt.analysis.check_solutions",
    "reproduce": "optopt.analysis.reproduce",
    "fetch": "optopt.benchmarks.fetch",
}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd in ("analyse", "analyze", "experiment"):
        if not rest:
            print(f"usage: optopt {cmd} <module> [args]")
            return 2
        mod = f"optopt.{'analysis' if cmd != 'experiment' else 'experiments'}.{rest[0]}"
        rest = rest[1:]
    elif cmd in COMMANDS:
        mod = COMMANDS[cmd]
    else:
        print(f"unknown command {cmd!r}\n{__doc__}")
        return 2
    sys.argv = [mod] + rest
    runpy.run_module(mod, run_name="__main__", alter_sys=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
