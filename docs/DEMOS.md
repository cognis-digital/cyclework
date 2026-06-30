# Demos

Twenty runnable scenarios in [`../demos/`](../demos/), each targeting a
different audience or facet of the engine. Every scenario drives the **real**
cyclework API (`Engine`, `Verdict`, the `Result`/`Iteration` trace), touches no
network, prints narrated output, and exits 0 — so they double as smoke tests of
the public surface.

```bash
python demos/run_all.py               # all twenty, end to end
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
| 6 | [`06_error_recovery.py`](../demos/06_error_recovery.py) | Resilience engineers | Stage failures (check / revise / seed) surfaced as `Status.ERROR` with a named message, preserving the partial trace and the best pre-failure candidate. |
| 7 | [`07_gradient_descent.py`](../demos/07_gradient_descent.py) | ML / optimization engineers | Gradient descent on a quadratic across three learning rates (converge / exhaust / oscillate); the best point is always retained. |
| 8 | [`08_text_normalizer.py`](../demos/08_text_normalizer.py) | Data-cleaning engineers | A richer multi-rule normalizer (product codes): the check ranks violations, revise repairs the top one, the trace shows which rules fired. |
| 9 | [`09_misuse_guards.py`](../demos/09_misuse_guards.py) | Library users | Clear errors over cryptic tracebacks: a non-`Verdict` return becomes a named ERROR; bad config raises `TypeError`/`ValueError` at construction. |
| 10 | [`10_collatz_and_budget.py`](../demos/10_collatz_and_budget.py) | Algorithm explorers | A not-provably-terminating loop (Collatz) made safe by a hard budget: SOLVED with a stopping time, or EXHAUSTED — never a hang. |
| 11 | [`11_seed_preprocessing.py`](../demos/11_seed_preprocessing.py) | Pipeline authors | `seed(initial)` canonicalizes input once before the loop, with the same honest ERROR handling when the seed itself fails. |
| 12 | [`12_plateau_early_stop.py`](../demos/12_plateau_early_stop.py) | Training-loop owners | Early stopping: `patience`/`min_delta` decide when a flattening learning curve is a plateau; the best epoch is kept. |
| 13 | [`13_streaming_audit_log.py`](../demos/13_streaming_audit_log.py) | Compliance / audit engineers | The trace as an audit log: `on_iteration` streams a structured record per step; `Result.summary()` is the final attestation. |
| 14 | [`14_state_is_anything.py`](../demos/14_state_is_anything.py) | Generalists | One engine over four state types — number, list (bubble sort), dict, (x,y) tuple — showing the loop's shape is independent of the data. |
| 15 | [`15_retry_with_backoff.py`](../demos/15_retry_with_backoff.py) | Reliability engineers | Retry-with-backoff as a bounded loop: the candidate carries attempt count + computed backoff; SOLVED on recovery, EXHAUSTED past budget. |
| 16 | [`16_constraint_repair.py`](../demos/16_constraint_repair.py) | Config / scheduling engineers | Constraint repair: a booking nudged until every rule holds; `patience` stops a repair that can never converge. |
| 17 | [`17_best_of_nonconvergent.py`](../demos/17_best_of_nonconvergent.py) | Search engineers | A bumpy search that never "solves": `best` is tracked independently of the stopping point, so the best find is still returned. |
| 18 | [`18_iterative_summarizer.py`](../demos/18_iterative_summarizer.py) | Content engineers | Length-bounded rewriting: fit text to a budget by applying the gentlest helpful edit first — same control flow an LLM rewrite uses. |
| 19 | [`19_two_forms_compared.py`](../demos/19_two_forms_compared.py) | API tour | `run()` (batch Result) vs `cycle()` (caller-owned stream) on one problem, and when to reach for each. |
| 20 | [`20_newton_vs_bisection.py`](../demos/20_newton_vs_bisection.py) | Numerical engineers | Two root-finders (Newton, bisection) as different check/revise pairs on one engine — the strategy lives entirely in those two functions. |

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
`pytest`, alongside the unit tests for the engine, the data model, and the
examples (136 tests in total).
