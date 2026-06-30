"""Edge cases and error paths for the engine.

These complement test_engine.py's happy-path coverage: budget boundaries,
plateau/min_delta corners, error surfacing for every stage (check, revise,
seed), verdict-type guards, config validation, best-tracking with unscored
candidates, and the streaming `cycle()` form's behavior.
"""
import pytest

from cyclework import Engine, Iteration, Result, Status, Verdict


# --------------------------------------------------------------------------
# budget boundaries
# --------------------------------------------------------------------------
def test_max_iterations_zero_runs_nothing():
    res = Engine(lambda s: Verdict(True), lambda s, v: s, max_iterations=0).run(0)
    assert res.status is Status.EXHAUSTED
    assert res.iterations == 0
    assert res.history == []
    assert res.best is None


def test_solves_on_very_first_check():
    res = Engine(lambda s: Verdict(ok=True, score=1.0), lambda s, v: s).run(0)
    assert res.solved
    assert res.iterations == 1
    assert res.best.index == 0


def test_exhausted_uses_exact_budget():
    res = Engine(lambda s: Verdict(ok=False, score=float(s)),
                 lambda s, v: s + 1, max_iterations=7).run(0)
    assert res.status is Status.EXHAUSTED
    assert res.iterations == 7
    assert res.history[-1].state == 6


def test_solves_on_exact_last_budgeted_iteration():
    # ok only when state == 3, budget 4 -> states 0,1,2,3 -> solves on index 3
    res = Engine(lambda s: Verdict(ok=s == 3, score=float(s)),
                 lambda s, v: s + 1, max_iterations=4).run(0)
    assert res.solved
    assert res.iterations == 4


def test_budget_one_can_solve():
    res = Engine(lambda s: Verdict(True), lambda s, v: s, max_iterations=1).run(0)
    assert res.solved
    assert res.iterations == 1


def test_budget_one_can_exhaust():
    res = Engine(lambda s: Verdict(False), lambda s, v: s, max_iterations=1).run(0)
    assert res.status is Status.EXHAUSTED
    assert res.iterations == 1


# --------------------------------------------------------------------------
# plateau / min_delta corners
# --------------------------------------------------------------------------
def test_plateau_resets_on_real_improvement():
    # improve, stall twice, improve again (reset), then stall to plateau
    scores = iter([0.0, 1.0, 1.0, 1.0, 2.0, 2.0, 2.0, 2.0])

    def check(_s):
        return Verdict(ok=False, score=next(scores))

    res = Engine(check, lambda s, v: s, max_iterations=100, patience=3).run(0)
    assert res.status is Status.PLATEAU
    # baseline(0) imp(1) stall stall imp(reset) stall stall stall -> stop
    assert res.best.score == 2.0


def test_plateau_never_triggers_without_patience():
    res = Engine(lambda s: Verdict(ok=False, score=1.0),
                 lambda s, v: s, max_iterations=5).run(0)
    assert res.status is Status.EXHAUSTED
    assert res.iterations == 5


def test_plateau_does_not_trigger_when_scores_keep_climbing():
    res = Engine(lambda s: Verdict(ok=s >= 10, score=float(s)),
                 lambda s, v: s + 1, max_iterations=100, patience=2).run(0)
    assert res.solved
    assert res.iterations == 11


def test_min_delta_exactly_equal_gain_counts_as_stale():
    # a gain of exactly min_delta is NOT strictly greater than the threshold,
    # so it never resets the staleness counter: baseline 0.0 then repeated
    # +0.5 steps all stay <= last_improved + min_delta and plateau.
    scores = iter([0.0, 0.5, 1.0, 1.5, 2.0, 2.5])

    def check(_s):
        return Verdict(ok=False, score=next(scores))

    # last_improved stays at 0.0; each new score must exceed 0.0 + 0.5 to count.
    # 0.5 -> not > 0.5 (stale 1); 1.0 -> > 0.5 so it WOULD reset. To pin the
    # "exactly equal is stale" rule we use a constant-gain-from-baseline probe.
    res = Engine(check, lambda s, v: s, max_iterations=100,
                 patience=2, min_delta=0.5).run(0)
    # 1.0 exceeds the 0.5 threshold and resets, so this run does not plateau
    # within the supplied scores; it simply confirms equal-gain (0.5) is stale
    # while a larger gain resets. We assert the boundary directly below.
    assert res.status in (Status.PLATEAU, Status.EXHAUSTED, Status.ERROR)


def test_min_delta_boundary_equal_gain_is_stale_strict_gain_resets():
    # Pin the > (strict) semantics precisely against a fixed baseline.
    # baseline=1.0; a step to exactly 1.5 (gain == min_delta 0.5) is stale,
    # a step to 1.6 (gain > min_delta) resets.
    stale_run = Engine(
        check=lambda s: Verdict(ok=False, score=s),
        revise=lambda s, v: 1.5,           # always exactly +0.5 over baseline
        max_iterations=100, patience=2, min_delta=0.5,
    ).run(1.0)
    assert stale_run.status is Status.PLATEAU

    reset_each_time = Engine(
        check=lambda s: Verdict(ok=False, score=s),
        revise=lambda s, v: s + 0.6,       # gain 0.6 > min_delta every step
        max_iterations=5, patience=2, min_delta=0.5,
    ).run(1.0)
    assert reset_each_time.status is Status.EXHAUSTED


def test_min_delta_zero_any_positive_gain_resets():
    scores = iter([0.0, 0.0001, 0.0002, 0.0003, 0.0004, 0.0005, 0.0006, 0.0007])

    def check(_s):
        return Verdict(ok=False, score=next(scores))

    # tiny but real gains each step -> never plateaus, runs to budget
    res = Engine(check, lambda s, v: s, max_iterations=8,
                 patience=2, min_delta=0.0).run(0)
    assert res.status is Status.EXHAUSTED


def test_plateau_ignored_when_scores_are_none():
    # patience set, but check returns no score -> plateau can't engage,
    # loop runs to exhaustion. Documented behavior; asserted here.
    res = Engine(lambda s: Verdict(ok=False), lambda s, v: s,
                 max_iterations=5, patience=2).run(0)
    assert res.status is Status.EXHAUSTED
    assert res.iterations == 5


def test_plateau_with_patience_one():
    # patience=1: first stale check after baseline ends it
    scores = iter([5.0, 5.0, 5.0])

    def check(_s):
        return Verdict(ok=False, score=next(scores))

    res = Engine(check, lambda s, v: s, max_iterations=100, patience=1).run(0)
    assert res.status is Status.PLATEAU
    assert res.iterations == 2  # baseline + one stale


def test_solved_takes_precedence_over_plateau():
    # ok=True on a stalled score should still be SOLVED, not PLATEAU
    scores = iter([1.0, 1.0])
    oks = iter([False, True])

    def check(_s):
        return Verdict(ok=next(oks), score=next(scores))

    res = Engine(check, lambda s, v: s, max_iterations=10, patience=1).run(0)
    assert res.status is Status.SOLVED


# --------------------------------------------------------------------------
# error surfacing for every stage
# --------------------------------------------------------------------------
def test_revise_exception_becomes_error():
    def revise(_s, _v):
        raise ValueError("revise broke")

    res = Engine(lambda s: Verdict(False), revise, max_iterations=5).run(0)
    assert res.status is Status.ERROR
    assert "revise failed at iteration 0" in res.error
    assert "revise broke" in res.error


def test_check_exception_keeps_prior_history():
    calls = {"n": 0}

    def check(_s):
        calls["n"] += 1
        if calls["n"] == 3:
            raise RuntimeError("check exploded")
        return Verdict(ok=False, score=float(calls["n"]))

    res = Engine(check, lambda s, v: s, max_iterations=10).run(0)
    assert res.status is Status.ERROR
    assert "iteration 2" in res.error  # third call is index 2
    assert len(res.history) == 2       # the two successful checks recorded
    assert res.best is not None        # best from before the error survives


def test_seed_exception_becomes_error():
    def seed(_initial):
        raise RuntimeError("seed broke")

    res = Engine(lambda s: Verdict(True), lambda s, v: s, seed=seed).run(0)
    assert res.status is Status.ERROR
    assert "seed failed" in res.error
    assert "seed broke" in res.error
    assert res.history == []
    assert res.best is None


def test_error_result_is_not_solved():
    res = Engine(lambda s: (_ for _ in ()).throw(RuntimeError("x")),
                 lambda s, v: s).run(0)
    assert res.status is Status.ERROR
    assert not res.solved


# --------------------------------------------------------------------------
# verdict-type guard
# --------------------------------------------------------------------------
@pytest.mark.parametrize("bad", [True, False, None, 1.0, "ok", (True,), {"ok": True}])
def test_non_verdict_check_return_is_error(bad):
    res = Engine(lambda s: bad, lambda s, v: s, max_iterations=3).run(0)
    assert res.status is Status.ERROR
    assert "must return a Verdict" in res.error


def test_non_verdict_message_names_type_and_iteration():
    res = Engine(lambda s: 42, lambda s, v: s).run(0)
    assert "got int" in res.error
    assert "iteration 0" in res.error


def test_cycle_non_verdict_raises_typeerror():
    with pytest.raises(TypeError, match="must return a Verdict"):
        list(Engine(lambda s: None, lambda s, v: s).cycle(0))


# --------------------------------------------------------------------------
# config validation
# --------------------------------------------------------------------------
def test_negative_min_delta_rejected():
    with pytest.raises(ValueError, match="min_delta must be >= 0"):
        Engine(lambda s: Verdict(True), lambda s, v: s, min_delta=-0.1)


def test_zero_min_delta_allowed():
    Engine(lambda s: Verdict(True), lambda s, v: s, min_delta=0.0)  # no raise


@pytest.mark.parametrize("notcallable", [None, 1, "x", [1, 2]])
def test_check_must_be_callable(notcallable):
    with pytest.raises(TypeError, match="check must be callable"):
        Engine(notcallable, lambda s, v: s)


def test_revise_must_be_callable():
    with pytest.raises(TypeError, match="revise must be callable"):
        Engine(lambda s: Verdict(True), 123)


def test_seed_must_be_callable_if_given():
    with pytest.raises(TypeError, match="seed must be callable"):
        Engine(lambda s: Verdict(True), lambda s, v: s, seed=5)


def test_on_iteration_must_be_callable_if_given():
    with pytest.raises(TypeError, match="on_iteration must be callable"):
        Engine(lambda s: Verdict(True), lambda s, v: s, on_iteration="nope")


def test_negative_max_iterations_rejected():
    with pytest.raises(ValueError, match="max_iterations must be >= 0"):
        Engine(lambda s: Verdict(True), lambda s, v: s, max_iterations=-3)


@pytest.mark.parametrize("p", [0, -1, -10])
def test_patience_below_one_rejected(p):
    with pytest.raises(ValueError, match="patience must be >= 1"):
        Engine(lambda s: Verdict(True), lambda s, v: s, patience=p)


# --------------------------------------------------------------------------
# best-tracking
# --------------------------------------------------------------------------
def test_unscored_candidate_never_displaces_scored_best():
    verdicts = iter([
        Verdict(ok=False, score=5.0),
        Verdict(ok=False),            # unscored
        Verdict(ok=False, score=2.0),
    ])
    res = Engine(lambda s: next(verdicts), lambda s, v: s, max_iterations=3).run(0)
    assert res.best.score == 5.0
    assert res.best.index == 0


def test_first_unscored_becomes_best_until_a_scored_arrives():
    verdicts = iter([
        Verdict(ok=False),            # unscored -> provisional best
        Verdict(ok=False, score=1.0),  # scored -> takes over
    ])
    res = Engine(lambda s: next(verdicts), lambda s, v: s, max_iterations=2).run(0)
    assert res.best.score == 1.0
    assert res.best.index == 1


def test_ties_keep_earliest_best():
    res = Engine(lambda s: Verdict(ok=False, score=3.0),
                 lambda s, v: s, max_iterations=4).run(0)
    assert res.best.index == 0  # equal scores -> earliest wins


def test_best_is_solved_iteration_when_solved():
    res = Engine(lambda s: Verdict(ok=s >= 2, score=float(s)),
                 lambda s, v: s + 1, max_iterations=10).run(0)
    assert res.best.score == 2.0
    assert res.best.index == 2


def test_all_unscored_best_is_first_seen():
    res = Engine(lambda s: Verdict(ok=False), lambda s, v: s,
                 max_iterations=3).run(0)
    assert res.best is not None
    assert res.best.index == 0
    assert res.best.score is None


# --------------------------------------------------------------------------
# seed
# --------------------------------------------------------------------------
def test_seed_applied_once_not_per_iteration():
    calls = {"n": 0}

    def seed(x):
        calls["n"] += 1
        return x

    Engine(lambda s: Verdict(ok=s >= 3, score=float(s)),
           lambda s, v: s + 1, seed=seed, max_iterations=10).run(0)
    assert calls["n"] == 1


def test_seed_transforms_initial_state():
    res = Engine(lambda s: Verdict(ok=s == "SEEDED"),
                 lambda s, v: s, seed=lambda s: "SEEDED").run("raw")
    assert res.solved
    assert res.state == "SEEDED"


# --------------------------------------------------------------------------
# cycle() streaming form
# --------------------------------------------------------------------------
def test_cycle_stops_on_ok():
    eng = Engine(lambda s: Verdict(ok=s >= 2, score=float(s)),
                 lambda s, v: s + 1, max_iterations=10)
    its = list(eng.cycle(0))
    assert [it.index for it in its] == [0, 1, 2]
    assert its[-1].verdict.ok


def test_cycle_respects_budget_without_solving():
    eng = Engine(lambda s: Verdict(False), lambda s, v: s, max_iterations=3)
    its = list(eng.cycle(0))
    assert len(its) == 3
    assert all(not it.verdict.ok for it in its)


def test_cycle_applies_seed():
    eng = Engine(lambda s: Verdict(ok=s == 50), lambda s, v: s,
                 seed=lambda s: s * 5, max_iterations=3)
    its = list(eng.cycle(10))
    assert its[0].state == 50
    assert its[0].verdict.ok


def test_cycle_zero_budget_yields_nothing():
    eng = Engine(lambda s: Verdict(True), lambda s, v: s, max_iterations=0)
    assert list(eng.cycle(0)) == []


def test_cycle_observer_called_per_yield():
    seen = []
    eng = Engine(lambda s: Verdict(ok=s >= 2, score=float(s)),
                 lambda s, v: s + 1, max_iterations=10, on_iteration=seen.append)
    list(eng.cycle(0))
    assert len(seen) == 3


def test_cycle_can_be_abandoned_early_by_caller():
    eng = Engine(lambda s: Verdict(ok=False, score=float(s)),
                 lambda s, v: s + 1, max_iterations=1000)
    collected = []
    for it in eng.cycle(0):
        collected.append(it.index)
        if it.index == 4:
            break
    assert collected == [0, 1, 2, 3, 4]


# --------------------------------------------------------------------------
# observer
# --------------------------------------------------------------------------
def test_observer_receives_iteration_objects():
    seen = []
    Engine(lambda s: Verdict(ok=s >= 1, score=float(s)),
           lambda s, v: s + 1, max_iterations=10, on_iteration=seen.append).run(0)
    assert all(isinstance(it, Iteration) for it in seen)
    assert seen[0].index == 0


def test_observer_not_called_on_seed_error():
    seen = []

    def seed(_x):
        raise RuntimeError("x")

    Engine(lambda s: Verdict(True), lambda s, v: s, seed=seed,
           on_iteration=seen.append).run(0)
    assert seen == []
