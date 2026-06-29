"""Scenario 1 - teams building AI / LLM agents.

The "keep trying until it passes" loop at the heart of every self-correcting
agent is usually a `while` buried in a function: you cannot tell afterward
whether it solved, gave up, or just stopped improving, and the path it took is
gone. cyclework makes that loop a first-class object.

Here we stub the "model" as a deterministic code generator that fixes exactly
the one problem the checker (a fake test suite + linter) complains about. No
network, no real LLM - but the control flow is precisely what you would wrap a
real model call in: check -> feedback -> revise.
"""
from _common import Engine, Verdict, rule, show_summary, show_trace


# A pretend code artifact the "agent" is refining toward passing checks.
# Each key is a defect the artifact currently has.
START = {"syntax_error": True, "failing_test": True, "lint_warnings": 3, "todo": True}


def check(artifact: dict) -> Verdict:
    """Stand-in for 'run the tests + linter and report the first blocker'.

    `score` = negative count of remaining defects (higher is better, 0 = clean).
    `feedback` names the single most important thing to fix next - exactly the
    string you would feed back into a real model's next prompt.
    """
    defects = (
        (1 if artifact["syntax_error"] else 0)
        + (1 if artifact["failing_test"] else 0)
        + artifact["lint_warnings"]
        + (1 if artifact["todo"] else 0)
    )
    score = -float(defects)
    if artifact["syntax_error"]:
        return Verdict.failed("fix syntax error before anything else", score=score, fix="syntax_error")
    if artifact["failing_test"]:
        return Verdict.failed("test_login is red - make it pass", score=score, fix="failing_test")
    if artifact["lint_warnings"] > 0:
        return Verdict.failed(f"{artifact['lint_warnings']} lint warning(s) left", score=score, fix="lint")
    if artifact["todo"]:
        return Verdict.failed("resolve the remaining TODO", score=score, fix="todo")
    return Verdict.passed(score=0.0)


def revise(artifact: dict, v: Verdict) -> dict:
    """Apply exactly the fix the verdict asked for (what a model would emit)."""
    nxt = dict(artifact)
    fix = v.detail.get("fix")
    if fix == "syntax_error":
        nxt["syntax_error"] = False
    elif fix == "failing_test":
        nxt["failing_test"] = False
    elif fix == "lint":
        nxt["lint_warnings"] -= 1
    elif fix == "todo":
        nxt["todo"] = False
    return nxt


def _fmt(a: dict) -> str:
    on = [k for k, val in a.items() if val and val != 0]
    return "{" + ", ".join(on) + "}" if on else "{clean}"


def main() -> None:
    rule("AGENT RETRY LOOP  -  self-correcting generation, made inspectable")
    print("\nTask: refine a code artifact until tests + linter are clean.")
    print("Each cycle: check reports ONE blocker -> revise fixes exactly it.\n")

    # max_iterations is the budget - a real agent caps model calls the same way.
    engine = Engine(check, revise, max_iterations=20)
    res = engine.run(START)

    show_trace(res, fmt_state=_fmt)
    print()
    show_summary(res)

    print(
        "\nThe loop ended SOLVED, and the full trace above is the audit trail: "
        "every model 'turn', what it was told, and what it changed."
    )


if __name__ == "__main__":
    main()
