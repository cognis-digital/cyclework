"""Scenario 2 - scientific / numerical engineers.

Root-finding, fixed points, and successive approximation are *the* canonical
refinement loops. cyclework ships them as worked examples (`cyclework.examples`)
that are nothing but the engine with a domain-specific check/revise pair - the
same object you would use for an agent loop, applied to math.

This demo runs the bundled solvers and then builds one inline to show there is
no magic: a check that scores how close we are, a revise that steps closer.
"""
import math

from _common import Engine, Verdict, rule, show_summary
from cyclework.examples import fixed_point, sqrt_newton


def main() -> None:
    rule("NUMERIC SOLVERS  -  convergence as a first-class loop")

    print("\n1) Newton's method for sqrt, expressed as check/revise:\n")
    res = sqrt_newton(2.0)
    print(f"   sqrt(2) -> {res.state!r}")
    print(f"   math.sqrt(2) = {math.sqrt(2.0)!r}")
    print(f"   agreement to < 1e-9: {abs(res.state - math.sqrt(2.0)) < 1e-9}")
    show_summary(res)

    print("\n2) Fixed point of cos(x) (the 'Dottie number'):\n")
    res = fixed_point(math.cos, 1.0)
    print(f"   x where cos(x) == x -> {res.state!r}")
    print(f"   residual |cos(x) - x| = {abs(math.cos(res.state) - res.state):.2e}")
    show_summary(res)

    print("\n3) Built inline - geometric series sum_{k>=0} 0.5^k -> 2.0:\n")
    # check: how far is the running partial sum from the analytic limit 2.0?
    # revise: add the next term. score = -error, so 'higher is better'.
    def check(state):
        partial, _term = state
        err = abs(partial - 2.0)
        return Verdict(ok=err <= 1e-9, score=-err, detail={"error": err})

    def revise(state, _v):
        partial, term = state
        nxt = term * 0.5
        return (partial + nxt, nxt)

    # seed: partial=1.0 (the k=0 term), next term=1.0 so revise adds 0.5, ...
    res = Engine(check, revise, max_iterations=60).run((1.0, 1.0))
    print(f"   partial sum -> {res.state[0]!r}  (analytic limit = 2.0)")
    show_summary(res)

    print(
        "\nThree different problems, one engine. The 'solver' is just a "
        "check that scores closeness and a revise that steps closer."
    )


if __name__ == "__main__":
    main()
