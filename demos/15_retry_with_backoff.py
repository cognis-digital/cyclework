"""Scenario 15 - reliability engineers: retry-with-backoff as a loop.

"Call a flaky service, and if it fails, wait longer and try again, up to N
times" is a refinement loop in disguise: the candidate is the attempt-state
(attempt count + current backoff), the check is "did the call succeed?", and
revise computes the next backoff. cyclework gives it a budget, a trace of every
attempt, and an honest terminal status (SOLVED vs EXHAUSTED) - no hidden while.

No real sleeping or network here: the "service" is a deterministic stub that
fails a fixed number of times, so the demo is fast and exit-0. The backoff is
*computed and recorded*, not actually slept on.
"""
from _common import Engine, Status, Verdict, rule, show_trace


def run_retry(fails_before_success: int, max_attempts: int = 8):
    """state = {attempt, backoff_s}. Succeeds once attempt > fails_before_success."""

    def check(state):
        attempt = state["attempt"]
        succeeded = attempt > fails_before_success
        if succeeded:
            return Verdict.passed(score=float(attempt))
        return Verdict.failed(
            f"attempt {attempt} failed; backing off {state['backoff_s']:.1f}s",
            score=float(attempt),
        )

    def revise(state, _v):
        # exponential backoff, capped at 30s - computed, not slept
        return {
            "attempt": state["attempt"] + 1,
            "backoff_s": min(state["backoff_s"] * 2, 30.0),
        }

    return Engine(check, revise, max_iterations=max_attempts).run(
        {"attempt": 1, "backoff_s": 0.5}
    )


def _fmt(s):
    return f"attempt={s['attempt']} backoff={s['backoff_s']:.1f}s"


def main() -> None:
    rule("RETRY WITH BACKOFF  -  flaky-call retries as a bounded loop")
    print("\nCall a stub that fails K times then succeeds. The candidate carries")
    print("the attempt count and the (computed) backoff; the budget caps retries.\n")

    print("1) service recovers on the 4th attempt (within budget):")
    res = run_retry(fails_before_success=3, max_attempts=8)
    show_trace(res, fmt_state=_fmt)
    print(f"   => {res.status.value} after {res.iterations} attempts\n")
    assert res.status is Status.SOLVED

    print("2) service stays down longer than the budget allows:")
    res = run_retry(fails_before_success=20, max_attempts=5)
    show_trace(res, fmt_state=_fmt)
    print(f"   => {res.status.value} after exhausting {res.iterations} attempts")
    assert res.status is Status.EXHAUSTED

    print(
        "\nThe retry policy is data (attempt + backoff) refined by a loop with a "
        "hard budget - and every attempt is in the trace for post-mortems."
    )


if __name__ == "__main__":
    main()
