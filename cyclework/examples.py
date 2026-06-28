"""Worked examples — each is a real use of the engine, exercised by the tests.

They span the range the loop is good at: a numeric solver (Newton), a generic
fixed-point iterator, and a feedback-driven text refiner where the verdict's
`feedback` actively steers the next revision.
"""

from __future__ import annotations

import re
from typing import Callable

from .engine import Engine
from .trace import Result
from .verdict import Verdict


def sqrt_newton(n: float, tol: float = 1e-12, max_iterations: int = 50) -> Result:
    """Square root via Newton's method, expressed as a refinement loop.

    check: error = |x^2 - n|; ok when error <= tol; score = -error (higher is
    better). revise: one Newton step x' = (x + n/x) / 2.
    """
    if n < 0:
        raise ValueError("n must be non-negative")

    def check(x: float) -> Verdict:
        err = abs(x * x - n)
        return Verdict(ok=err <= tol, score=-err, detail={"error": err})

    def revise(x: float, _v: Verdict) -> float:
        return (x + n / x) / 2 if x != 0 else 1.0

    engine = Engine(check, revise, max_iterations=max_iterations)
    return engine.run(max(n, 1.0))


def fixed_point(f: Callable[[float], float], x0: float, tol: float = 1e-10,
                max_iterations: int = 200) -> Result:
    """Find x such that x == f(x), by iterating x <- f(x)."""

    def check(x: float) -> Verdict:
        gap = abs(f(x) - x)
        return Verdict(ok=gap <= tol, score=-gap, detail={"gap": gap})

    def revise(x: float, _v: Verdict) -> float:
        return f(x)

    return Engine(check, revise, max_iterations=max_iterations).run(x0)


def refine_slug(text: str, max_len: int = 40) -> Result:
    """Turn arbitrary text into a clean url slug, one fix per cycle.

    Demonstrates feedback-driven revision: `check` reports the first rule the
    candidate violates, and `revise` applies exactly the fix that rule asks
    for. The loop converges when no rule is violated.
    """

    def check(s: str) -> Verdict:
        if s != s.strip():
            return Verdict.failed("trim", fix="trim")
        if s != s.lower():
            return Verdict.failed("lowercase", fix="lower")
        if re.search(r"\s", s):
            return Verdict.failed("spaces->dashes", fix="dash")
        if re.search(r"[^a-z0-9-]", s):
            return Verdict.failed("strip-symbols", fix="symbols")
        if "--" in s or s.startswith("-") or s.endswith("-"):
            return Verdict.failed("collapse-dashes", fix="collapse")
        if len(s) > max_len:
            return Verdict.failed("too-long", fix="truncate")
        return Verdict.passed()

    def revise(s: str, v: Verdict) -> str:
        fix = v.detail.get("fix")
        if fix == "trim":
            return s.strip()
        if fix == "lower":
            return s.lower()
        if fix == "dash":
            return re.sub(r"\s+", "-", s)
        if fix == "symbols":
            return re.sub(r"[^a-z0-9-]", "", s)
        if fix == "collapse":
            return re.sub(r"-+", "-", s).strip("-")
        if fix == "truncate":
            return s[:max_len].rstrip("-")
        return s

    return Engine(check, revise, max_iterations=20).run(text)
