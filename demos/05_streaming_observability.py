"""Scenario 5 - observability / platform engineers.

A long-running loop should not be a black box until it returns. cyclework gives
you two ways to watch it live: the `on_iteration` callback (wire it to a logger,
a metrics sink, or a progress bar) and the `Engine.cycle()` generator form,
which yields each `Iteration` as it happens so you can stream, throttle, or stop
early from the outside.

This demo wires an observer that emits a live progress bar, then re-runs the
same loop as a generator and stops it from the caller side once 'good enough'.
"""
from _common import Engine, Verdict, rule


def main() -> None:
    rule("STREAMING & OBSERVABILITY  -  watch the loop while it runs")

    # gradient-descent-flavoured loop: minimize (x-7)^2, score = -loss
    target = 7.0

    def check(x):
        loss = (x - target) ** 2
        return Verdict(ok=loss <= 1e-6, score=-loss, detail={"loss": loss})

    def revise(x, _v):
        return x + 0.3 * (target - x)  # step toward target

    # --- 1) on_iteration observer: a live progress bar --------------------
    print("\n1) on_iteration callback -> live progress (score climbs toward 0):\n")

    def bar(it):
        # score is -loss in [-inf, 0]; map to a 0..30 bar by closeness
        loss = it.verdict.detail["loss"]
        filled = max(0, min(30, int(30 * (1 - min(loss / 50.0, 1.0)))))
        print(f"   [{it.index:>2}] |{'#' * filled}{'.' * (30 - filled)}| "
              f"state={it.state:7.4f}  loss={loss:.4f}")

    res = Engine(check, revise, max_iterations=40, on_iteration=bar).run(0.0)
    print(f"\n   final: state={res.state:.6f}  status={res.status.value}  "
          f"iterations={res.iterations}")

    # --- 2) cycle() generator: stop early from the caller side ------------
    print("\n2) Engine.cycle() generator -> caller decides when to stop:\n")
    engine = Engine(check, revise, max_iterations=40)
    for it in engine.cycle(0.0):
        print(f"   yielded iteration {it.index}: state={it.state:.4f}")
        if it.state >= 6.5:  # external stopping rule, no engine change needed
            print("   caller says: close enough, breaking out of the stream.")
            break

    print(
        "\nThe loop is observable both ways: push (on_iteration) for fire-and-"
        "forget sinks, pull (cycle) when the caller owns the stopping decision."
    )


if __name__ == "__main__":
    main()
