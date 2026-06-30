"""Scenario 11 - pipeline authors: the seed normalizes input before the loop.

A refinement loop often wants its starting candidate in a canonical form first:
parse a string into a number, clamp into a valid range, decompress, validate.
cyclework's optional `seed(initial) -> state` runs exactly once, before the
first check - and (unlike a bare preprocess) a failing seed is surfaced as a
clean `Status.ERROR`, not a stray exception.

This demo uses a seed to parse and clamp messy user input into a number the
loop can refine, and also shows a seed that rejects bad input cleanly.
"""
from _common import Engine, Status, Verdict, rule, show_summary


def parse_and_clamp(raw: str):
    """Seed turns a string into a float clamped to [0, 100]; loop counts to 100."""

    def seed(s: str) -> float:
        val = float(s.strip())          # raises ValueError on garbage -> ERROR
        return max(0.0, min(100.0, val))

    def check(x: float) -> Verdict:
        return Verdict(ok=x >= 100.0, score=x)

    def revise(x: float, _v: Verdict) -> float:
        return x + 25.0

    return Engine(check, revise, seed=seed, max_iterations=20).run(raw)


def main() -> None:
    rule("SEED PREPROCESSING  -  canonicalize input once, before the loop")
    print("\nSeed parses a string and clamps it to [0,100]; the loop climbs to 100.\n")

    for raw in ["  10 ", "-50", "200", "62.5"]:
        res = parse_and_clamp(raw)
        print(f"   input={raw!r:<8} seeded+ran -> state={res.state}  "
              f"status={res.status.value}  iterations={res.iterations}")

    print("\nA seed that cannot parse its input fails as a clean ERROR:\n")
    res = parse_and_clamp("not-a-number")
    show_summary(res)

    print(
        "\nThe seed is the loop's front door: one-time normalization, with the "
        "same honest error handling as every other stage."
    )


if __name__ == "__main__":
    main()
