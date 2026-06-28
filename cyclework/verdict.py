"""The result of checking a candidate.

A `Verdict` answers three things about a candidate state:
  * `ok`       — is this good enough to stop? (the only required field)
  * `score`    — an optional quality number; higher is better. Used for
                 convergence/plateau detection and for tracking the best
                 candidate seen so far.
  * `feedback` — optional, free-form information passed to the next revise
                 step (an error message, a diff, a gradient hint, anything).

Keeping the verdict separate from the revise step lets the engine reason about
progress (via `score`) without knowing anything about the problem domain.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class Verdict:
    ok: bool
    score: Optional[float] = None
    feedback: str = ""
    detail: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def passed(cls, score: Optional[float] = None, **detail: Any) -> "Verdict":
        return cls(ok=True, score=score, detail=detail)

    @classmethod
    def failed(cls, feedback: str = "", score: Optional[float] = None, **detail: Any) -> "Verdict":
        return cls(ok=False, score=score, feedback=feedback, detail=detail)
