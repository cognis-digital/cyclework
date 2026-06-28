"""The refinement engine.

You give it two functions:

    check(state)          -> Verdict        # how good is this candidate?
    revise(state, verdict) -> new_state      # produce a better candidate

and it runs the cycle:

    seed? -> [ check -> (stop?) -> revise ]*

stopping when a verdict is `ok`, when the score plateaus (no improvement of at
least `min_delta` for `patience` checks), or when `max_iterations` is reached.
A stage raising an exception aborts cleanly with `Status.ERROR` and the trace
collected so far.

Convention: `score` is higher-is-better. For a "lower is better" objective
(an error/cost), return its negation as the score.
"""

from __future__ import annotations

from typing import Any, Callable, Iterator, Optional

from .trace import Iteration, Result, Status
from .verdict import Verdict

CheckFn = Callable[[Any], Verdict]
ReviseFn = Callable[[Any, Verdict], Any]
SeedFn = Callable[[Any], Any]
ObserverFn = Callable[[Iteration], None]


class Engine:
    def __init__(
        self,
        check: CheckFn,
        revise: ReviseFn,
        *,
        max_iterations: int = 25,
        patience: Optional[int] = None,
        min_delta: float = 0.0,
        seed: Optional[SeedFn] = None,
        on_iteration: Optional[ObserverFn] = None,
    ):
        if max_iterations < 0:
            raise ValueError("max_iterations must be >= 0")
        if patience is not None and patience < 1:
            raise ValueError("patience must be >= 1")
        self.check = check
        self.revise = revise
        self.max_iterations = max_iterations
        self.patience = patience
        self.min_delta = min_delta
        self.seed = seed
        self.on_iteration = on_iteration

    # ---- streaming form: yields each iteration as it happens -------------
    def cycle(self, initial: Any) -> Iterator[Iteration]:
        state = self.seed(initial) if self.seed else initial
        for i in range(self.max_iterations):
            verdict = self.check(state)
            it = Iteration(index=i, state=state, verdict=verdict)
            if self.on_iteration:
                self.on_iteration(it)
            yield it
            if verdict.ok:
                return
            state = self.revise(state, verdict)

    # ---- batch form: runs to completion, returns a Result ----------------
    def run(self, initial: Any) -> Result:
        history: list[Iteration] = []
        best: Optional[Iteration] = None
        status = Status.EXHAUSTED
        last_improved: Optional[float] = None
        stale = 0
        state = self.seed(initial) if self.seed else initial

        for i in range(self.max_iterations):
            try:
                verdict = self.check(state)
            except Exception as e:  # noqa: BLE001 - surface stage errors as ERROR status
                return Result(Status.ERROR, state, len(history), history, best,
                              error=f"check failed at iteration {i}: {e}")

            it = Iteration(index=i, state=state, verdict=verdict)
            history.append(it)
            best = _better(best, it)
            if self.on_iteration:
                self.on_iteration(it)

            if verdict.ok:
                status = Status.SOLVED
                break

            # plateau detection on score (higher is better)
            if self.patience is not None and verdict.score is not None:
                if last_improved is None or verdict.score > last_improved + self.min_delta:
                    last_improved = verdict.score
                    stale = 0
                else:
                    stale += 1
                    if stale >= self.patience:
                        status = Status.PLATEAU
                        break

            try:
                state = self.revise(state, verdict)
            except Exception as e:  # noqa: BLE001
                return Result(Status.ERROR, state, len(history), history, best,
                              error=f"revise failed at iteration {i}: {e}")

        return Result(status, state, len(history), history, best)


def _better(current: Optional[Iteration], candidate: Iteration) -> Iteration:
    """Keep the higher-scoring iteration; unscored candidates never displace
    a scored best, but become best if nothing better exists yet."""
    if current is None:
        return candidate
    cs, ks = current.score, candidate.score
    if ks is None:
        return current
    if cs is None or ks > cs:
        return candidate
    return current
