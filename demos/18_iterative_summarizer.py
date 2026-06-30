"""Scenario 18 - content engineers: shrink text to fit, one edit per cycle.

"Make this fit in N characters without butchering it" is a refinement loop: the
check scores how far over budget you are, the revise applies the gentlest edit
that still helps (drop filler, trim trailing detail). cyclework runs it with a
budget and a trace so you can see *which* edits fired to hit the target.

This is a deterministic, dependency-free stand-in for the kind of length-bounded
rewriting an LLM does - same control flow (check length -> revise -> recheck),
no model required.
"""
import re

from _common import Engine, Verdict, rule, show_trace


FILLER = ["really", "very", "just", "actually", "basically", "simply",
          "in order to", "at this point in time", "due to the fact that"]


def fit(text: str, limit: int):
    def check(s: str) -> Verdict:
        over = len(s) - limit
        score = -float(max(over, 0))      # 0 when within budget
        if over <= 0:
            return Verdict.passed(score=0.0)
        # decide the gentlest available edit
        if any(w in s.lower() for w in FILLER):
            return Verdict.failed(f"{over} over - drop filler", score=score, fix="filler")
        if "  " in s or s != s.strip():
            return Verdict.failed(f"{over} over - squeeze spaces", score=score, fix="space")
        return Verdict.failed(f"{over} over - trim tail", score=score, fix="trim")

    def revise(s: str, v: Verdict) -> str:
        fix = v.detail["fix"]
        if fix == "filler":
            out = s
            for w in FILLER:
                out = re.sub(rf"\b{re.escape(w)}\b ?", "", out, flags=re.IGNORECASE)
            return re.sub(r"\s{2,}", " ", out).strip()
        if fix == "space":
            return re.sub(r"\s{2,}", " ", s).strip()
        # last resort: trim to the last word boundary under the limit
        cut = s[:limit].rsplit(" ", 1)[0]
        return cut.rstrip(",.;: ")

    return Engine(check, revise, max_iterations=20).run(text)


def main() -> None:
    rule("ITERATIVE SUMMARIZER  -  fit text to a budget, gentlest edit first")
    text = ("This is really just a very simple summary that is, "
            "basically, actually too long in order to fit nicely.")
    print(f"\noriginal ({len(text)} chars): {text!r}\n")

    for limit in [80, 50, 30]:
        res = fit(text, limit)
        print(f"target <= {limit}:")
        show_trace(res, fmt_state=lambda s: f"{len(s)}c {s!r}")
        print(f"   => ({len(res.state)} chars) {res.state!r}  "
              f"[{res.status.value}]")
        assert len(res.state) <= limit
        print()

    print("Length-bounded rewriting is propose/check/revise: score the overflow, "
          "apply the least-destructive edit, recheck.")


if __name__ == "__main__":
    main()
