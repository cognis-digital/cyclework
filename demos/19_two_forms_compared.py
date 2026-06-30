"""Scenario 19 - API tour: run() vs cycle() on the same problem.

cyclework exposes the loop two ways, and which you reach for is a real design
choice. `run()` is the batch form: it owns the loop, traps stage errors, detects
plateaus, and returns a complete `Result` you inspect afterward. `cycle()` is the
streaming form: it yields each `Iteration` as it happens so the *caller* owns the
loop - free to throttle, log live, or stop on an external condition the engine
knows nothing about.

This demo drives the identical check/revise pair through both forms and contrasts
what each gives you: a final Result you query vs a live stream you steer.
"""
from _common import Engine, Verdict, rule, show_summary


def make_engine():
    # converge x toward 10 by halving the gap; score = -distance
    def check(x):
        return Verdict(ok=abs(x - 10) < 1e-9, score=-abs(x - 10))

    def revise(x, _v):
        return x + (10 - x) / 2

    return Engine(check, revise, max_iterations=60)


def main() -> None:
    rule("TWO FORMS COMPARED  -  run() vs cycle() on one problem")
    print("\nConverge x -> 10 by halving the gap. Same check/revise, two APIs.\n")

    # --- run(): batch, returns a Result ----------------------------------
    print("1) run() - engine owns the loop, returns a Result to inspect:\n")
    res = make_engine().run(0.0)
    print(f"   final state = {res.state:.9f}")
    show_summary(res)
    print(f"   the whole path is in res.history ({len(res.history)} iterations); "
          f"plateaus and errors are handled for you.")

    # --- cycle(): streaming, caller owns the loop ------------------------
    print("\n2) cycle() - caller owns the loop, stops on its own condition:\n")
    seen = 0
    last = None
    for it in make_engine().cycle(0.0):
        seen += 1
        last = it.state
        if it.state >= 9.9:               # external stop the engine never knew about
            print(f"   caller stops at iteration {it.index}: x={it.state:.6f} "
                  f"(>= 9.9 is good enough for us)")
            break
    print(f"   streamed {seen} iterations; final seen state = {last:.6f}")

    print(
        "\nReach for run() when you want the engine to manage the loop and hand "
        "you a complete, inspectable Result; reach for cycle() when the caller "
        "needs to watch or steer it live."
    )


if __name__ == "__main__":
    main()
