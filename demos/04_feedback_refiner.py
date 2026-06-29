"""Scenario 4 - data / content engineers building self-correcting pipelines.

The defining feature of a retry-with-feedback loop is that the *check* doesn't
just say pass/fail - it hands the next *revise* the information it needs to do
better. cyclework carries that on `Verdict.feedback` (and `Verdict.detail`).

The bundled `refine_slug` example normalizes arbitrary text into a URL slug one
rule at a time: each cycle, check names the first rule the candidate breaks and
revise applies exactly that fix. We run it and print the path, so you can watch
the feedback steer each step.
"""
from _common import rule, show_summary, show_trace
from cyclework.examples import refine_slug


CASES = [
    "  Hello,  World!!  ",
    "Cognis Digital --- Accountable AI",
    "already-clean",
]


def main() -> None:
    rule("FEEDBACK REFINER  -  the verdict steers the next revision")
    print("\nNormalize messy text into a URL slug, one rule per cycle.")
    print("Watch `feedback` name the fix that revise then applies.\n")

    for raw in CASES:
        print(f"input: {raw!r}")
        res = refine_slug(raw)
        show_trace(res, fmt_state=repr)
        print(f"   => {res.state!r}")
        show_summary(res)
        print()

    print(
        "Each candidate is built from the previous one PLUS the verdict's "
        "feedback - the exact contract a self-correcting generator runs on."
    )


if __name__ == "__main__":
    main()
