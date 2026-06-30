"""Scenario 8 - data-cleaning engineers: a multi-rule normalizer.

The bundled slug refiner fixes one rule per cycle; here we build a richer
normalizer for free-text product codes from the same primitives - each cycle
the check reports the highest-priority violation and revise applies exactly
that fix. The point: a "clean this messy field" pipeline is a refinement loop,
and the trace tells you *which* rules fired, in what order, for any input.
"""
import re

from _common import Engine, Verdict, rule, show_summary, show_trace


def normalize_code(raw: str):
    """Normalize a product code: uppercase, A-Z0-9 and single dashes, <= 16."""
    MAX = 16

    def check(s: str) -> Verdict:
        n = sum(c not in "-" for c in s)
        score = float(n)  # prefer candidates closer to a valid form
        if s != s.strip():
            return Verdict.failed("has surrounding whitespace", score=score, fix="trim")
        if s != s.upper():
            return Verdict.failed("not uppercase", score=score, fix="upper")
        if re.search(r"\s", s):
            return Verdict.failed("internal whitespace", score=score, fix="space")
        if re.search(r"[^A-Z0-9-]", s):
            return Verdict.failed("illegal characters", score=score, fix="strip")
        if "--" in s or s.startswith("-") or s.endswith("-"):
            return Verdict.failed("dash noise", score=score, fix="dash")
        if len(s) > MAX:
            return Verdict.failed("too long", score=score, fix="trunc")
        return Verdict.passed(score=score)

    def revise(s: str, v: Verdict) -> str:
        fix = v.detail.get("fix")
        if fix == "trim":
            return s.strip()
        if fix == "upper":
            return s.upper()
        if fix == "space":
            return re.sub(r"\s+", "-", s)
        if fix == "strip":
            return re.sub(r"[^A-Z0-9-]", "", s)
        if fix == "dash":
            return re.sub(r"-+", "-", s).strip("-")
        if fix == "trunc":
            return s[:MAX].rstrip("-")
        return s

    return Engine(check, revise, max_iterations=25).run(raw)


CASES = [
    "  sku 12 / abc!!  ",
    "Widget---Pro---2026",
    "VALID-CODE-01",
    "this-is-a-really-long-product-code-that-overflows",
]


def main() -> None:
    rule("TEXT NORMALIZER  -  multi-rule cleaning, one fix per cycle")
    print("\nNormalize free-text product codes to UPPER / [A-Z0-9-] / <=16 chars.")
    print("Each cycle names the top violation; the trace shows which rules fired.\n")

    for raw in CASES:
        print(f"input: {raw!r}")
        res = normalize_code(raw)
        show_trace(res, fmt_state=repr)
        print(f"   => {res.state!r}")
        show_summary(res)
        print()

    print("The same propose/check/revise shape scales to any rule set you can "
          "rank by priority.")


if __name__ == "__main__":
    main()
