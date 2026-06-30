"""Scenario 9 - library users: the engine fails loudly, not cryptically.

The most common way to misuse a propose/check/revise engine is to have `check`
return a bare bool (or None, or a tuple) instead of a `Verdict`. Without a
guard that surfaces deep inside the loop as a baffling AttributeError. cyclework
catches it at the boundary and tells you exactly what went wrong, where.

This demo deliberately misconfigures the engine in several ways and shows the
clear error each one produces - config validation up front (TypeError /
ValueError) and a wrong return type surfaced as a named ERROR result.
"""
from _common import Engine, Verdict, rule


def main() -> None:
    rule("MISUSE GUARDS  -  clear errors beat cryptic tracebacks")

    print("\n1) check returns a bare bool instead of a Verdict:\n")
    res = Engine(lambda s: s >= 3, lambda s, v: s + 1, max_iterations=5).run(0)
    print(f"   status={res.status.value}")
    print(f"   error: {res.error}")

    print("\n2) check returns None (forgot to return at all):\n")
    res = Engine(lambda s: None, lambda s, v: s).run(0)
    print(f"   status={res.status.value}")
    print(f"   error: {res.error}")

    print("\n3) constructor validation - caught immediately, before any run:\n")
    for label, thunk in [
        ("max_iterations=-1", lambda: Engine(lambda s: Verdict(True), lambda s, v: s, max_iterations=-1)),
        ("patience=0", lambda: Engine(lambda s: Verdict(True), lambda s, v: s, patience=0)),
        ("min_delta=-0.5", lambda: Engine(lambda s: Verdict(True), lambda s, v: s, min_delta=-0.5)),
        ("check not callable", lambda: Engine(123, lambda s, v: s)),
        ("revise not callable", lambda: Engine(lambda s: Verdict(True), "nope")),
        ("seed not callable", lambda: Engine(lambda s: Verdict(True), lambda s, v: s, seed=7)),
    ]:
        try:
            thunk()
            print(f"   {label:<22} -> (no error - unexpected!)")
        except (ValueError, TypeError) as e:
            print(f"   {label:<22} -> {type(e).__name__}: {e}")

    print(
        "\nMisconfiguration is caught at construction; a wrong return type is "
        "surfaced as a named ERROR result you can branch on - never a surprise "
        "AttributeError ten frames deep."
    )


if __name__ == "__main__":
    main()
