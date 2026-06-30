"""Scenario 7 - ML / optimization engineers: descent as a refinement loop.

Gradient descent is the archetypal "propose, check, revise" loop: the check
scores how low the loss is, the revise steps downhill. Because cyclework tracks
the best candidate seen, a descent that overshoots and bounces still hands back
its lowest-loss point - not wherever it happened to stop.

This demo minimizes a 1-D quadratic with three learning rates - one that
converges smoothly, one that converges slowly (and exhausts its budget), and
one so large it oscillates - and shows the engine naming each outcome while
always recovering the best point.
"""
from _common import Engine, Status, Verdict, rule, show_summary


def descend(lr: float, max_iterations: int = 60):
    """Minimize f(x) = (x - 3)^2. score = -loss (higher is better)."""
    target = 3.0

    def check(x):
        loss = (x - target) ** 2
        return Verdict(ok=loss <= 1e-9, score=-loss, detail={"loss": loss})

    def revise(x, _v):
        grad = 2 * (x - target)      # df/dx
        return x - lr * grad

    return Engine(check, revise, max_iterations=max_iterations).run(0.0)


def main() -> None:
    rule("GRADIENT DESCENT  -  minimize a quadratic, keep the best point")
    print("\nMinimize f(x) = (x - 3)^2 from x0 = 0, varying the learning rate.\n")

    for lr, label in [(0.3, "well-tuned"), (0.02, "too small"), (1.05, "too large")]:
        res = descend(lr)
        best_x = res.best.state
        best_loss = res.best.verdict.detail["loss"]
        print(f"lr={lr:<5} ({label}):")
        print(f"   status={res.status.value:<9} iterations={res.iterations:<3} "
              f"best_x={best_x:.6f}  best_loss={best_loss:.3e}")
        if res.status is Status.SOLVED:
            print("   -> converged to the minimum.")
        elif res.status is Status.EXHAUSTED:
            print("   -> ran out of budget; best point so far is still usable.")
        print()

    print("Verbose summary of the well-tuned run:")
    show_summary(descend(0.3))

    print(
        "\nSame engine, three regimes. The loop never loses the best candidate, "
        "so even a non-converging run returns something you can use."
    )


if __name__ == "__main__":
    main()
