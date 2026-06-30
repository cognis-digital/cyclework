"""Scenario 10 - algorithm explorers: bounded iteration with a hard budget.

Some loops are not guaranteed to terminate (or you simply do not want them to
run forever). The Collatz sequence is the classic example: iterate
n -> n/2 (even) or 3n+1 (odd) and you *conjecture* it reaches 1, but you cannot
prove it for every start. cyclework turns that into a safe, bounded experiment:
set a budget, run, and read back whether it solved or exhausted - never a hang.

This demo runs Collatz from several starts under a fixed budget and reports the
stopping time (number of steps to reach 1) or EXHAUSTED if the budget ran out.
"""
from _common import Engine, Status, Verdict, rule


def collatz_steps(start: int, max_iterations: int = 1000):
    def check(n: int) -> Verdict:
        # score = -n so 'closer to 1' reads as higher; ok when we hit 1
        return Verdict(ok=n == 1, score=-float(n))

    def revise(n: int, _v: Verdict) -> int:
        return n // 2 if n % 2 == 0 else 3 * n + 1

    return Engine(check, revise, max_iterations=max_iterations).run(start)


def main() -> None:
    rule("COLLATZ & BUDGET  -  unprovable loops made safe by a hard cap")
    print("\nIterate n -> n/2 (even) / 3n+1 (odd) until it reaches 1.")
    print("A budget guarantees termination even where the math does not.\n")

    for start in [1, 6, 27, 97, 871]:
        res = collatz_steps(start, max_iterations=500)
        steps = res.iterations - 1  # checks include the starting n
        if res.status is Status.SOLVED:
            print(f"   start={start:<5} reached 1 in {steps:>3} steps")
        else:
            print(f"   start={start:<5} {res.status.value} after {steps} steps "
                  f"(min value seen = {int(-res.best.score)})")

    print("\nNow with a deliberately tiny budget so it cannot finish:")
    res = collatz_steps(27, max_iterations=10)
    print(f"   start=27 budget=10 -> status={res.status.value}, "
          f"reached n={res.state} (not yet 1).")

    print(
        "\nThe budget is the safety rail: the loop always returns, and the "
        "status tells you whether it got there or simply ran out of room."
    )


if __name__ == "__main__":
    main()
