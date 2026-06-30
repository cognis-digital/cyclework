"""Run every demo scenario end to end.

    python demos/run_all.py

Each scenario is independent, uses only the real cyclework API, touches no
network, and exits 0 - so this doubles as a smoke test of the public surface.
On a cp1252 console, run with PYTHONUTF8=1.
"""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SCENARIOS = [
    "01_agent_retry_loop",
    "02_numeric_solvers",
    "03_plateau_and_budget",
    "04_feedback_refiner",
    "05_streaming_observability",
    "06_error_recovery",
    "07_gradient_descent",
    "08_text_normalizer",
    "09_misuse_guards",
    "10_collatz_and_budget",
    "11_seed_preprocessing",
    "12_plateau_early_stop",
    "13_streaming_audit_log",
    "14_state_is_anything",
    "15_retry_with_backoff",
    "16_constraint_repair",
    "17_best_of_nonconvergent",
    "18_iterative_summarizer",
    "19_two_forms_compared",
    "20_newton_vs_bisection",
]


def main() -> None:
    for name in SCENARIOS:
        mod = importlib.import_module(name)
        mod.main()
    print("\n" + "=" * 70)
    print("  All demo scenarios completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()
