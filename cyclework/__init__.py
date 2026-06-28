"""cyclework — a small engine for iterative refinement loops.

A surprising amount of useful work has the same shape: produce a candidate,
check it against a goal, and use what the check told you to produce a better
candidate — repeating until the candidate is good enough, stops improving, or
you run out of budget. Optimizers, solvers, retry-with-feedback agent loops,
and self-correcting generators are all this loop.

cyclework makes that loop a first-class, inspectable object. You supply two
functions — how to *check* a candidate and how to *revise* it given feedback —
and the engine runs the cycle, detects convergence and plateaus, enforces a
budget, and hands back a full trace of what happened on every iteration.

It is deliberately tiny, dependency-free, and domain-agnostic: the candidate
("state") can be a number, a string, a dict, an AST — anything.
"""

from .verdict import Verdict
from .trace import Iteration, Result, Status
from .engine import Engine

__version__ = "0.1.0"
__all__ = ["Engine", "Verdict", "Result", "Iteration", "Status", "__version__"]
