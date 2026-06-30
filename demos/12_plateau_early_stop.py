"""Scenario 12 - training-loop owners: stop early when learning stalls.

You rarely want to burn the full budget once a loop has stopped improving.
With `patience` and `min_delta`, cyclework detects a plateau - N consecutive
checks that fail to improve the score by at least min_delta - and stops, handing
back the best candidate it saw. This is the same early-stopping you would wire
into a training loop, but as a property of the engine.

This demo models a noisy learning curve that climbs, then flattens, and shows
how patience/min_delta change *when* the engine calls it quits - and that the
best epoch is always retained regardless of where it stopped.
"""
from _common import Engine, Status, Verdict, rule


# a hand-built "learning curve": fast early gains, then it flattens out.
CURVE = [0.10, 0.45, 0.70, 0.82, 0.88, 0.905, 0.915, 0.920, 0.922, 0.923,
         0.9235, 0.9237, 0.9238, 0.92385, 0.92386]


def run(patience: int, min_delta: float):
    scores = iter(CURVE)

    def check(_s):
        try:
            return Verdict(ok=False, score=next(scores))
        except StopIteration:
            return Verdict(ok=False, score=CURVE[-1])

    return Engine(check, lambda s, v: s, max_iterations=len(CURVE),
                  patience=patience, min_delta=min_delta).run(0)


def main() -> None:
    rule("PLATEAU EARLY-STOP  -  quit when learning flattens, keep the best")
    print("\nA learning curve that climbs then flattens. patience/min_delta")
    print("decide how long to wait before declaring a plateau.\n")

    for patience, min_delta in [(2, 0.01), (3, 0.01), (2, 0.05), (5, 0.0)]:
        res = run(patience, min_delta)
        stopped = res.iterations
        tag = res.status.value
        print(f"   patience={patience} min_delta={min_delta:<5} -> "
              f"stopped after {stopped:>2} epochs ({tag}); "
              f"best score {res.best.score:.5f} at epoch {res.best.index}")

    print("\nTighter min_delta / smaller patience -> stops sooner. In every "
          "case the best epoch is retained, not whatever the last one was.")

    # show that without patience it would run the whole budget
    res = run(patience=1, min_delta=10.0)  # impossible gain -> immediate plateau
    assert res.status is Status.PLATEAU


if __name__ == "__main__":
    main()
