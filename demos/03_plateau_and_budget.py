"""Scenario 3 - SREs, ML engineers, anyone running loops in production.

A loop in production needs honest stopping. "It finished" is not enough - you
need to know *why* it finished: did it solve, did it stop improving (plateau),
or did it run out of budget (exhausted)? And when it gives up, you want the
best candidate it ever saw, not the last one.

This demo drives the engine into each of the four terminal states - SOLVED,
PLATEAU, EXHAUSTED, ERROR - on purpose, so you can see the engine name each one
and recover the best result even from a non-success.
"""
from _common import Engine, Status, Verdict, rule, show_summary


def main() -> None:
    rule("PLATEAU & BUDGET  -  honest stopping with the best candidate kept")

    # --- SOLVED: a verdict comes back ok=True -----------------------------
    print("\nSOLVED  - climb to 5, stop the moment ok=True:")
    res = Engine(
        check=lambda s: Verdict(ok=s >= 5, score=float(s)),
        revise=lambda s, v: s + 1,
        max_iterations=50,
    ).run(0)
    assert res.status is Status.SOLVED
    show_summary(res)

    # --- PLATEAU: score stops improving for `patience` checks -------------
    print("\nPLATEAU - score creeps then stalls; patience=3 calls it:")
    # gains shrink below min_delta, so improvements stop 'counting' as progress
    scores = iter([0.0, 0.5, 0.8, 0.85, 0.86, 0.865, 0.866, 0.8665, 0.8666])
    res = Engine(
        check=lambda s: Verdict(ok=False, score=next(scores)),
        revise=lambda s, v: s,
        max_iterations=50,
        patience=3,
        min_delta=0.1,
    ).run("x")
    assert res.status is Status.PLATEAU
    show_summary(res)
    print(f"   best candidate kept from iteration #{res.best.index} "
          f"(score {res.best.score}), not the last stalled one.")

    # --- EXHAUSTED: budget runs out before solving ------------------------
    print("\nEXHAUSTED - target never reached inside a 4-iteration budget:")
    res = Engine(
        check=lambda s: Verdict(ok=s >= 1000, score=float(s)),
        revise=lambda s, v: s + 1,
        max_iterations=4,
    ).run(0)
    assert res.status is Status.EXHAUSTED
    show_summary(res)

    # --- ERROR: a stage raises; abort cleanly with the trace so far -------
    print("\nERROR   - a check raises; the run aborts cleanly, trace preserved:")
    def boom(_s):
        raise RuntimeError("model endpoint unreachable")
    res = Engine(boom, revise=lambda s, v: s, max_iterations=5).run(0)
    assert res.status is Status.ERROR
    show_summary(res)

    print(
        "\nFour outcomes, four named statuses. Production code branches on "
        "res.status and always has res.best to fall back on."
    )


if __name__ == "__main__":
    main()
