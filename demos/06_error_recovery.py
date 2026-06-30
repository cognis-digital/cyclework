"""Scenario 6 - resilience engineers: failures are first-class outcomes.

Real refinement stages fail: a model endpoint times out, a `revise` hits a
divide-by-zero, a `seed` preprocessor chokes on bad input. cyclework does not
let those escape as raw tracebacks - it surfaces them as `Status.ERROR` with a
message naming the stage and iteration, and it preserves the trace and the best
candidate seen *before* the failure, so the caller can still recover something.

This demo triggers a failure in each of the three stages (check, revise, seed)
and shows the engine naming the stage, keeping the partial history, and handing
back the best pre-failure candidate.
"""
from _common import Engine, Verdict, rule, show_summary, show_trace


def main() -> None:
    rule("ERROR RECOVERY  -  stage failures become inspectable outcomes")

    # --- a check that explodes part-way through ---------------------------
    print("\n1) check() raises on the 3rd call - history before it survives:\n")
    calls = {"n": 0}

    def flaky_check(s):
        calls["n"] += 1
        if calls["n"] == 3:
            raise RuntimeError("scoring service 503")
        return Verdict(ok=False, score=float(s))

    res = Engine(flaky_check, lambda s, v: s + 1, max_iterations=10).run(0)
    show_trace(res, fmt_state=str)
    show_summary(res)
    print(f"   -> {len(res.history)} good iterations kept; best score "
          f"{res.best.score} from before the failure.")

    # --- a revise that divides by zero ------------------------------------
    print("\n2) revise() raises - the engine names the stage and iteration:\n")

    def bad_revise(s, v):
        return 1 / 0  # noqa: B018

    res = Engine(lambda s: Verdict(ok=False, score=1.0), bad_revise,
                 max_iterations=5).run(10)
    show_summary(res)

    # --- a seed that fails before the loop even starts --------------------
    print("\n3) seed() raises before any iteration - clean ERROR, empty trace:\n")

    def bad_seed(_x):
        raise ValueError("could not parse initial input")

    res = Engine(lambda s: Verdict(True), lambda s, v: s,
                 seed=bad_seed).run("garbage")
    show_summary(res)
    print(f"   -> history length {len(res.history)} (nothing ran), "
          f"status named the failure instead of crashing the caller.")

    print(
        "\nEvery stage failure is a value you can branch on (res.status, "
        "res.error), not an exception that takes down the whole pipeline."
    )


if __name__ == "__main__":
    main()
