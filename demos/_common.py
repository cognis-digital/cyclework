"""Shared helpers for the demo scenarios.

Every demo here drives the *real* cyclework API — `Engine`, `Verdict`, the
`Result`/`Iteration` trace — with no network, no external deps, and exit 0.
They double as narrated smoke tests of the public surface.
"""
from __future__ import annotations

import os
import sys

# allow `python demos/NN_name.py` from anywhere
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cyclework import Engine, Iteration, Result, Status, Verdict  # noqa: E402,F401

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def rule(title: str) -> None:
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def show_summary(res: Result) -> None:
    """Print a run's outcome the way an operator would read it."""
    s = res.summary()
    print(
        f"   -> status={s['status']}  iterations={s['iterations']}  "
        f"solved={s['solved']}  final_score={_fmt(s['final_score'])}  "
        f"best_score={_fmt(s['best_score'])}"
    )
    if res.error:
        print(f"   -> error: {res.error}")


def show_trace(res: Result, fmt_state=str, limit: int = 12) -> None:
    """Print the per-iteration path the loop took (the inspectable history)."""
    rows = res.history[:limit]
    for it in rows:
        v = it.verdict
        mark = "OK " if v.ok else "..."
        fb = f"  feedback={v.feedback!r}" if v.feedback else ""
        print(
            f"   [{it.index:>2}] {mark} score={_fmt(it.score):>10}  "
            f"state={fmt_state(it.state)}{fb}"
        )
    if len(res.history) > limit:
        print(f"   ... ({len(res.history) - limit} more iterations)")


def _fmt(x) -> str:
    if x is None:
        return "None"
    if isinstance(x, float):
        return f"{x:.6g}"
    return str(x)
