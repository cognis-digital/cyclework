"""Scenario 20 - numerical engineers: two root-finders, one engine.

The same problem - find a root of a continuous function - can be refined by very
different strategies. Newton's method uses the derivative and converges fast but
can diverge; bisection only needs a sign-bracketing interval and converges
slowly but unconditionally. Both are propose/check/revise loops; cyclework lets
you express each as a check/revise pair and compare their traces head to head.

This demo finds the root of f(x) = x^3 - x - 2 (~1.5214) with both methods and
prints how many iterations each took to the same tolerance.
"""
from _common import Engine, Status, Verdict, rule


def f(x):
    return x ** 3 - x - 2


def fprime(x):
    return 3 * x ** 2 - 1


def newton(x0, tol=1e-12, max_iterations=50):
    def check(x):
        err = abs(f(x))
        return Verdict(ok=err <= tol, score=-err, detail={"err": err})

    def revise(x, _v):
        d = fprime(x)
        return x - f(x) / d if d != 0 else x + 1e-3

    return Engine(check, revise, max_iterations=max_iterations).run(x0)


def bisection(lo, hi, tol=1e-12, max_iterations=200):
    # state is the bracket (lo, hi); the midpoint is the candidate root
    def check(state):
        lo, hi = state
        mid = (lo + hi) / 2
        err = abs(f(mid))
        return Verdict(ok=(hi - lo) / 2 <= tol or err <= tol,
                       score=-err, detail={"mid": mid, "err": err})

    def revise(state, _v):
        lo, hi = state
        mid = (lo + hi) / 2
        # keep the half that still brackets the sign change
        if f(lo) * f(mid) <= 0:
            return (lo, mid)
        return (mid, hi)

    return Engine(check, revise, max_iterations=max_iterations).run((lo, hi))


def main() -> None:
    rule("NEWTON vs BISECTION  -  two strategies, one refinement engine")
    print("\nFind a root of f(x) = x^3 - x - 2  (true root ~ 1.52137971).\n")

    res_n = newton(1.5)
    root_n = res_n.state
    print(f"Newton    : root = {root_n:.12f}  status={res_n.status.value}  "
          f"iterations={res_n.iterations}")
    assert res_n.status is Status.SOLVED

    res_b = bisection(1.0, 2.0)
    root_b = (res_b.state[0] + res_b.state[1]) / 2
    print(f"Bisection : root = {root_b:.12f}  status={res_b.status.value}  "
          f"iterations={res_b.iterations}")
    assert res_b.status is Status.SOLVED

    print(f"\nBoth agree to < 1e-6: {abs(root_n - root_b) < 1e-6}")
    print(f"Newton needed {res_n.iterations} iterations; bisection "
          f"{res_b.iterations} - same engine, the check/revise pair encodes "
          f"the whole strategy.")

    print(
        "\nThe engine is strategy-agnostic: change only how a candidate is "
        "scored and revised, and the same loop runs an entirely different method."
    )


if __name__ == "__main__":
    main()
