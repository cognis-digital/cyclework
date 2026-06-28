from cyclework import Engine, Status, Verdict


def test_solves_when_check_ok():
    # count up to 5; ok when state == 5
    eng = Engine(
        check=lambda s: Verdict(ok=s >= 5, score=float(s)),
        revise=lambda s, v: s + 1,
        max_iterations=10,
    )
    res = eng.run(0)
    assert res.solved
    assert res.status is Status.SOLVED
    assert res.state == 5
    assert res.iterations == 6  # states 0,1,2,3,4,5


def test_exhausted_when_never_ok():
    eng = Engine(
        check=lambda s: Verdict(ok=False, score=float(s)),
        revise=lambda s, v: s + 1,
        max_iterations=4,
    )
    res = eng.run(0)
    assert res.status is Status.EXHAUSTED
    assert res.iterations == 4
    assert not res.solved


def test_plateau_detection():
    # score never improves; patience=3 should stop after 3 stale checks
    eng = Engine(
        check=lambda s: Verdict(ok=False, score=1.0),
        revise=lambda s, v: s,
        max_iterations=100,
        patience=3,
    )
    res = eng.run("x")
    assert res.status is Status.PLATEAU
    # first scored sets baseline (stale=0), then 3 stale -> stop at 4 records
    assert res.iterations == 4


def test_min_delta_counts_small_gains_as_stale():
    scores = iter([0.0, 0.1, 0.15, 0.18, 0.19, 0.195])

    def check(_s):
        return Verdict(ok=False, score=next(scores))

    eng = Engine(check, revise=lambda s, v: s, max_iterations=100,
                 patience=2, min_delta=0.2)
    res = eng.run(0)
    # every gain is < 0.2, so improvements never "count"; plateau quickly
    assert res.status is Status.PLATEAU


def test_best_tracks_highest_score():
    scores = iter([1.0, 5.0, 3.0, 2.0])

    def check(_s):
        return Verdict(ok=False, score=next(scores))

    eng = Engine(check, revise=lambda s, v: s, max_iterations=4)
    res = eng.run(0)
    assert res.best is not None
    assert res.best.score == 5.0
    assert res.best.index == 1


def test_error_status_on_stage_exception():
    def check(_s):
        raise RuntimeError("boom")

    res = Engine(check, revise=lambda s, v: s, max_iterations=5).run(0)
    assert res.status is Status.ERROR
    assert "boom" in (res.error or "")


def test_seed_preprocesses_initial():
    eng = Engine(
        check=lambda s: Verdict(ok=s == 100, score=float(s)),
        revise=lambda s, v: s + 1,
        seed=lambda s: s * 10,
        max_iterations=5,
    )
    res = eng.run(10)  # seed -> 100, immediately ok
    assert res.solved
    assert res.iterations == 1


def test_feedback_passed_to_revise():
    seen = []

    def check(s):
        return Verdict(ok=s == "DONE", feedback="next")

    def revise(s, v):
        seen.append(v.feedback)
        return "DONE"

    Engine(check, revise, max_iterations=3).run("start")
    assert seen == ["next"]


def test_cycle_streams_iterations():
    eng = Engine(
        check=lambda s: Verdict(ok=s >= 3, score=float(s)),
        revise=lambda s, v: s + 1,
        max_iterations=10,
    )
    indices = [it.index for it in eng.cycle(0)]
    assert indices == [0, 1, 2, 3]


def test_observer_hook_called():
    calls = []
    eng = Engine(
        check=lambda s: Verdict(ok=s >= 2, score=float(s)),
        revise=lambda s, v: s + 1,
        max_iterations=10,
        on_iteration=calls.append,
    )
    eng.run(0)
    assert len(calls) == 3


def test_invalid_config():
    import pytest
    with pytest.raises(ValueError):
        Engine(lambda s: Verdict(True), lambda s, v: s, max_iterations=-1)
    with pytest.raises(ValueError):
        Engine(lambda s: Verdict(True), lambda s, v: s, patience=0)
