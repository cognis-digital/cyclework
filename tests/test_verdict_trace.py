"""Tests for the Verdict, Iteration, and Result data model.

The data model is the engine's public contract — the trace a caller inspects
after a run. These tests pin down the constructors, the convenience factories,
immutability, and the summary/explanation surface.
"""
import dataclasses

import pytest

from cyclework import Iteration, Result, Status, Verdict


# --------------------------------------------------------------------------
# Verdict
# --------------------------------------------------------------------------
def test_verdict_minimal_only_requires_ok():
    v = Verdict(ok=True)
    assert v.ok is True
    assert v.score is None
    assert v.feedback == ""
    assert v.detail == {}


def test_verdict_passed_factory():
    v = Verdict.passed(score=1.5, note="great")
    assert v.ok is True
    assert v.score == 1.5
    assert v.detail == {"note": "great"}


def test_verdict_passed_without_score():
    v = Verdict.passed()
    assert v.ok is True
    assert v.score is None


def test_verdict_failed_factory():
    v = Verdict.failed("try again", score=-2.0, fix="syntax")
    assert v.ok is False
    assert v.feedback == "try again"
    assert v.score == -2.0
    assert v.detail == {"fix": "syntax"}


def test_verdict_failed_defaults():
    v = Verdict.failed()
    assert v.ok is False
    assert v.feedback == ""
    assert v.score is None
    assert v.detail == {}


def test_verdict_is_frozen():
    v = Verdict(ok=True)
    with pytest.raises(dataclasses.FrozenInstanceError):
        v.ok = False


def test_verdict_detail_is_independent_per_instance():
    a = Verdict.failed(fix="x")
    b = Verdict.failed(fix="y")
    assert a.detail == {"fix": "x"}
    assert b.detail == {"fix": "y"}


def test_verdict_positional_ok():
    assert Verdict(True).ok is True
    assert Verdict(False).ok is False


# --------------------------------------------------------------------------
# Iteration
# --------------------------------------------------------------------------
def test_iteration_score_proxies_verdict():
    it = Iteration(index=0, state="s", verdict=Verdict(ok=False, score=3.0))
    assert it.score == 3.0


def test_iteration_score_none_when_verdict_unscored():
    it = Iteration(index=0, state="s", verdict=Verdict(ok=True))
    assert it.score is None


def test_iteration_holds_state():
    obj = {"k": 1}
    it = Iteration(index=2, state=obj, verdict=Verdict(ok=True))
    assert it.state is obj
    assert it.index == 2


# --------------------------------------------------------------------------
# Result
# --------------------------------------------------------------------------
def test_result_solved_property():
    assert Result(Status.SOLVED, 0, 1).solved is True
    assert Result(Status.PLATEAU, 0, 1).solved is False
    assert Result(Status.EXHAUSTED, 0, 1).solved is False
    assert Result(Status.ERROR, 0, 1).solved is False


def test_result_summary_empty_history():
    r = Result(Status.EXHAUSTED, None, 0)
    s = r.summary()
    assert s["status"] == "exhausted"
    assert s["iterations"] == 0
    assert s["solved"] is False
    assert s["final_score"] is None
    assert s["best_score"] is None
    assert s["error"] is None


def test_result_summary_with_history_and_best():
    h = [
        Iteration(0, "a", Verdict(ok=False, score=1.0)),
        Iteration(1, "b", Verdict(ok=True, score=5.0)),
    ]
    r = Result(Status.SOLVED, "b", 2, history=h, best=h[1])
    s = r.summary()
    assert s["final_score"] == 5.0
    assert s["best_score"] == 5.0
    assert s["solved"] is True


def test_result_summary_carries_error():
    r = Result(Status.ERROR, 0, 1, error="boom at iteration 0")
    assert r.summary()["error"] == "boom at iteration 0"


def test_result_history_defaults_to_empty_list():
    r = Result(Status.EXHAUSTED, 0, 0)
    assert r.history == []
    assert r.best is None


# --------------------------------------------------------------------------
# Status enum
# --------------------------------------------------------------------------
def test_status_is_str_enum():
    assert Status.SOLVED == "solved"
    assert Status.PLATEAU.value == "plateau"
    assert {Status.SOLVED, Status.ERROR} == {Status.SOLVED, Status.ERROR}


def test_all_statuses_distinct():
    vals = {s.value for s in Status}
    assert vals == {"solved", "plateau", "exhausted", "error"}
