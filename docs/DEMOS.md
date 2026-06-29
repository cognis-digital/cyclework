# Demos

Five runnable scenarios in [`../demos/`](../demos/), each targeting a different
audience. Every scenario drives the **real** cyclework API (`Engine`,
`Verdict`, the `Result`/`Iteration` trace), touches no network, prints narrated
output, and exits 0 — so they double as smoke tests of the public surface.

```bash
python demos/run_all.py               # all five, end to end
python demos/02_numeric_solvers.py    # or just one
```

On a Windows / cp1252 console, run with `PYTHONUTF8=1` so the output encodes
cleanly.

| # | Demo | Audience | Shows |
|---|------|----------|-------|
| 1 | [`01_agent_retry_loop.py`](../demos/01_agent_retry_loop.py) | AI / LLM agent builders | A self-correcting "fix until tests pass" loop as a first-class, inspectable object — check reports one blocker, revise fixes exactly it, and the full trace is the audit trail. |
| 2 | [`02_numeric_solvers.py`](../demos/02_numeric_solvers.py) | Scientific / numerical engineers | Convergence as a refinement loop: Newton's sqrt, the `cos(x)` fixed point, and a geometric series built inline — three problems, one engine. |
| 3 | [`03_plateau_and_budget.py`](../demos/03_plateau_and_budget.py) | SREs / production loop owners | Honest stopping: the engine driven into all four terminal states (SOLVED / PLATEAU / EXHAUSTED / ERROR) on purpose, always keeping the best candidate seen. |
| 4 | [`04_feedback_refiner.py`](../demos/04_feedback_refiner.py) | Data / content pipeline engineers | Feedback-driven revision: `Verdict.feedback` names the first broken rule and `revise` applies exactly that fix, normalizing messy text into a URL slug one cycle at a time. |
| 5 | [`05_streaming_observability.py`](../demos/05_streaming_observability.py) | Observability / platform engineers | Watching a loop live: the `on_iteration` push callback (a live progress bar) and the `Engine.cycle()` pull generator that lets the caller stop early. |

## The shape they share

Every demo is the same loop with a different `check`/`revise` pair:

1. **`check(state) -> Verdict`** — score the candidate, decide if it's good
   enough, and (optionally) hand feedback to the next step.
2. **`revise(state, verdict) -> state`** — produce the next candidate, using
   the feedback when there is some.
3. The engine records each step, detects convergence/plateau, enforces the
   budget, and returns a `Result` with the full trace.

---

Each demo prints clear, narrated output and exits 0, so they double as smoke
tests — [`tests/test_demos.py`](../tests/test_demos.py) runs every one under
`pytest`, alongside the unit tests for the engine and examples.
