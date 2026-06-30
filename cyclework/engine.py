"""The refinement engine.

You give it two functions:

    check(state)          -> Verdict        # how good is this candidate?
    revise(state, verdict) -> new_state      # produce a better candidate

and it runs the cycle:

    seed? -> [ check -> (stop?) -> revise ]*

stopping when a verdict is `ok`, when the score plateaus (no improvement of at
least `min_delta` for `patience` checks), or when `max_iterations` is reached.
Any stage (`seed`, `check`, `revise`) that raises — or a `check` that returns
something other than a `Verdict` — aborts cleanly with `Status.ERROR`, a message
naming the stage and iteration, and the trace collected so far. Constructor
arguments are validated up front (callable stages; non-negative budget/min_delta;
patience >= 1).

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
        if min_delta < 0:
            raise ValueError("min_delta must be >= 0")
        if not callable(check):
            raise TypeError("check must be callable: check(state) -> Verdict")
        if not callable(revise):
            raise TypeError("revise must be callable: revise(state, verdict) -> state")
        if seed is not None and not callable(seed):
            raise TypeError("seed must be callable: seed(initial) -> state")
        if on_iteration is not None and not callable(on_iteration):
            raise TypeError("on_iteration must be callable: on_iteration(iteration) -> None")
        self.check = check
        self.revise = revise
        self.max_iterations = max_iterations
        self.patience = patience
        self.min_delta = min_delta
        self.seed = seed
        self.on_iteration = on_iteration

    # ---- streaming form: yields each iteration as it happens -------------
    def cycle(self, initial: Any) -> Iterator[Iteration]:
        """Yield each `Iteration` as it happens.

        Unlike `run()`, the streaming form does not trap stage exceptions or
        detect plateaus — the caller owns the loop and can stop early or wrap
        it as it sees fit. A `check` that returns something other than a
        `Verdict` still raises a clear `TypeError`.
        """
        state = self.seed(initial) if self.seed else initial
        for i in range(self.max_iterations):
            verdict = _as_verdict(self.check(state), "check", i)
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

        # the seed is a stage too: surface its failures as ERROR, just like
        # check/revise, rather than letting them escape the engine.
        if self.seed is not None:
            try:
                state = self.seed(initial)
            except Exception as e:  # noqa: BLE001 - surface seed errors as ERROR status
                return Result(Status.ERROR, initial, 0, history, best,
                              error=f"seed failed: {e}")
        else:
            state = initial

        for i in range(self.max_iterations):
            try:
                verdict = _as_verdict(self.check(state), "check", i)
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


def _as_verdict(value: Any, stage: str, index: int) -> Verdict:
    """Guard that a stage returned a `Verdict`.

    Returning a bare bool/tuple/None from `check` is the single most common
    misuse; without this guard it surfaces deep in the engine as a cryptic
    `AttributeError`. Here it becomes an actionable `TypeError` naming the
    stage and iteration.
    """
    if not isinstance(value, Verdict):
        raise TypeError(
            f"{stage} must return a Verdict at iteration {index}, "
            f"got {type(value).__name__}: {value!r}. "
            f"Use Verdict(ok=...), Verdict.passed(...), or Verdict.failed(...)."
        )
    return value


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
