"""Scenario 17 - search engineers: keep the best from a non-converging search.

Not every search converges - sometimes you explore a noisy landscape, never hit
a perfect answer, and just want the best candidate you stumbled on. Because
cyclework tracks `best` (the highest-scoring iteration) independently of where
the loop stops, a search that exhausts its budget or plateaus still hands back
its best find - and the trace shows the whole exploration.

This demo runs a bounded hill-climb over a deceptive 1-D function with a local
trap, never solves exactly, and shows the engine returning the best point seen
even though the final point is worse.
"""
import math

from _common import Engine, Status, Verdict, rule, show_summary


def main() -> None:
    rule("BEST-OF NON-CONVERGENT  -  return the best find, not the last step")

    # a bumpy function with a clear global max near x = 6.0 that we sample
    # along a fixed schedule (no real convergence, just exploration).
    def f(x):
        return math.sin(x) + 0.4 * math.sin(3 * x) - 0.02 * (x - 6) ** 2

    xs = iter([0.0, 1.5, 3.0, 4.5, 6.0, 7.5, 9.0, 10.5, 12.0, 1.0])

    def check(_state):
        try:
            x = next(xs)
        except StopIteration:
            x = 0.0
        score = f(x)
        # never "ok" - this is a search, not a solve; we want best-of.
        return Verdict(ok=False, score=score, detail={"x": x})

    def revise(state, _v):
        return state  # the schedule lives in the check; state is a placeholder

    res = Engine(check, revise, max_iterations=10).run(None)

    print("\nSampled a bumpy landscape; the loop never declares success:\n")
    for it in res.history:
        x = it.verdict.detail["x"]
        marker = "  <-- best so far" if it is res.best else ""
        print(f"   [{it.index:>2}] x={x:5.2f}  f(x)={it.score:+.4f}{marker}")

    print()
    show_summary(res)
    bx = res.best.verdict.detail["x"]
    print(f"\n   status={res.status.value}: never solved, but best find is "
          f"x={bx:.2f} with f(x)={res.best.score:+.4f}")
    assert res.status is Status.EXHAUSTED

    print(
        "\n`best` is tracked independently of the stopping point, so a search "
        "that runs out of budget still returns the best thing it ever saw."
    )


if __name__ == "__main__":
    main()
