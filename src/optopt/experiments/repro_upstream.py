"""Minimal reproductions for possible upstream bug reports (nothing is posted from here)."""
import json, sys, time


if __name__ == "__main__":
    sys.path.insert(0, ".")
    out = {}
    from optopt.paths import DATA
    M = str(DATA / "miplib/inst") + "/"
    import highspy
    h = highspy.Highs(); h.setOptionValue("output_flag", False); h.setOptionValue("threads", 1); h.setOptionValue("time_limit", 60.0)
    h = highspy.Highs(); h.setOptionValue("output_flag", False); h.setOptionValue("threads", 1); h.setOptionValue("time_limit", 60.0)
    h = highspy.Highs(); h.setOptionValue("output_flag", False); h.setOptionValue("threads", 1); h.setOptionValue("time_limit", 60.0)
    h = highspy.Highs(); h.setOptionValue("output_flag", False); h.setOptionValue("threads", 1); h.setOptionValue("time_limit", 60.0)
    h.readModel(M + "s100.mps.gz"); t = time.time(); h.run(); w = time.time() - t
    h.readModel(M + "s100.mps.gz"); t = time.time(); h.run(); w = time.time() - t
    h.readModel(M + "s100.mps.gz"); t = time.time(); h.run(); w = time.time() - t
    h.readModel(M + "s100.mps.gz"); t = time.time(); h.run(); w = time.time() - t
    out["highs_s100"] = dict(version=h.version(), time_limit=60, wall=round(w, 1), status=h.modelStatusToString(h.getModelStatus()))
    print(out, flush=True)
    from cuopt.linear_programming import ParseMps, Solve, SolverSettings
    import cuopt
    for name, params in (("sorrell3", {"mip_cut_passes": 0, "mip_hyper_heuristic_rins_time_limit": 10.0}), ("uccase12", {}),
                         ("dano3_3", {"mip_cut_passes": 0, "mip_hyper_heuristic_rins_time_limit": 10.0})):
        dm = ParseMps(M + name + ".mps.gz"); s = SolverSettings()
        s.set_parameter("time_limit", 60.0); s.set_parameter("log_to_console", False); s.set_parameter("num_cpu_threads", 3)
        for k, v in params.items(): s.set_parameter(k, v)
        t = time.time(); sol = Solve(dm, s); w = time.time() - t
        out[f"cuopt_{name}"] = dict(version=cuopt.__version__, params=params, time_limit=60, wall=round(w, 1),
                                    status=int(sol.get_termination_status()), objective=sol.get_primal_objective())
        print(out[f"cuopt_{name}"], flush=True)
    json.dump(out, open("traces/repro/upstream_repro.json", "w"), indent=1, default=str)
    print("REPRO-DONE", flush=True)
