"""Inspectable history of a run.

Every iteration is recorded as an `Iteration` (the candidate, its verdict, and
the wall-clock-independent step index). A `Result` bundles the final outcome
with the full trace and the best candidate seen, so a caller can not only get
the answer but explain how it was reached — which is the whole point of making
the loop a first-class object rather than a `while` buried in a function.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional

from .verdict import Verdict


class Status(str, Enum):
    SOLVED = "solved"          # a verdict came back ok=True
    PLATEAU = "plateau"        # score stopped improving (patience exhausted)
    EXHAUSTED = "exhausted"    # hit max_iterations without solving
    ERROR = "error"            # a stage raised and the run was aborted


@dataclass
class Iteration:
    index: int
    state: Any
    verdict: Verdict

    @property
    def score(self) -> Optional[float]:
        return self.verdict.score


@dataclass
class Result:
    status: Status
    state: Any                          # final candidate
    iterations: int
    history: List[Iteration] = field(default_factory=list)
    best: Optional[Iteration] = None    # highest-scoring iteration seen
    error: Optional[str] = None

    @property
    def solved(self) -> bool:
        return self.status is Status.SOLVED

    def summary(self) -> dict:
        return {
            "status": self.status.value,
            "iterations": self.iterations,
            "solved": self.solved,
            "final_score": self.history[-1].score if self.history else None,
            "best_score": self.best.score if self.best else None,
            "error": self.error,
        }
