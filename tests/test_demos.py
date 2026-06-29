"""Smoke tests for the runnable demo scenarios.

Each demo drives the real public API, touches no network, and must exit 0.
We import them as modules and assert main() runs cleanly. The demos directory
is added to sys.path the same way run_all.py does it.
"""
import importlib
import io
import os
import sys
from contextlib import redirect_stdout

import pytest

DEMOS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "demos")
sys.path.insert(0, DEMOS_DIR)

SCENARIOS = [
    "01_agent_retry_loop",
    "02_numeric_solvers",
    "03_plateau_and_budget",
    "04_feedback_refiner",
    "05_streaming_observability",
]


@pytest.mark.parametrize("name", SCENARIOS)
def test_demo_runs_and_produces_output(name):
    mod = importlib.import_module(name)
    buf = io.StringIO()
    with redirect_stdout(buf):
        mod.main()  # must not raise -> exit 0 equivalent
    out = buf.getvalue()
    assert out.strip(), f"{name} produced no output"


def test_run_all_executes_every_scenario():
    run_all = importlib.import_module("run_all")
    assert run_all.SCENARIOS == SCENARIOS
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_all.main()
    assert "All demo scenarios completed." in buf.getvalue()


def test_agent_retry_loop_solves():
    from _common import Status  # noqa: WPS433
    mod = importlib.import_module("01_agent_retry_loop")
    res = mod.Engine(mod.check, mod.revise, max_iterations=20).run(mod.START)
    assert res.status is Status.SOLVED
    assert res.state == {
        "syntax_error": False, "failing_test": False,
        "lint_warnings": 0, "todo": False,
    }
