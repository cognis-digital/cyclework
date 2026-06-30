"""Scenario 16 - config / scheduling engineers: repair until constraints hold.

Many "make this valid" problems are constraint repair: you have a candidate
that violates some rules, and you nudge it until every constraint is satisfied.
cyclework expresses that as a loop where check reports the first violated
constraint (with a score = number satisfied) and revise repairs exactly it.

This demo repairs a meeting-room booking - start before end, within business
hours, capacity not exceeded, minimum duration - and shows the loop converging
to a valid booking, or reporting it cannot (when constraints conflict, it stalls
on a plateau rather than looping forever).
"""
from _common import Engine, Status, Verdict, rule, show_trace


CONSTRAINTS = ("start<end", "open>=9", "close<=17", "cap<=20", "dur>=1")


def repair(booking: dict):
    def check(b: dict) -> Verdict:
        ok = []
        ok.append(("start<end", b["start"] < b["end"]))
        ok.append(("open>=9", b["start"] >= 9))
        ok.append(("close<=17", b["end"] <= 17))
        ok.append(("cap<=20", b["attendees"] <= 20))
        ok.append(("dur>=1", b["end"] - b["start"] >= 1))
        satisfied = sum(1 for _, good in ok if good)
        score = float(satisfied)
        for name, good in ok:
            if not good:
                return Verdict.failed(f"violates {name}", score=score, fix=name)
        return Verdict.passed(score=score)

    def revise(b: dict, v: Verdict) -> dict:
        nxt = dict(b)
        fix = v.detail["fix"]
        if fix == "start<end":
            nxt["end"] = nxt["start"] + 1
        elif fix == "open>=9":
            nxt["start"] = 9
        elif fix == "close<=17":
            nxt["end"] = 17
        elif fix == "cap<=20":
            nxt["attendees"] = 20
        elif fix == "dur>=1":
            nxt["end"] = nxt["start"] + 1
        return nxt

    return Engine(check, revise, max_iterations=15, patience=4).run(booking)


def _fmt(b):
    return f"{b['start']:02d}:00-{b['end']:02d}:00 x{b['attendees']}"


def main() -> None:
    rule("CONSTRAINT REPAIR  -  nudge a candidate until every rule holds")
    print(f"\nConstraints: {', '.join(CONSTRAINTS)}")
    print("Each cycle repairs the first violated constraint.\n")

    print("1) a fixable booking (out of hours, over capacity):")
    res = repair({"start": 7, "end": 19, "attendees": 50})
    show_trace(res, fmt_state=_fmt)
    print(f"   => {_fmt(res.state)}  status={res.status.value}")
    assert res.status is Status.SOLVED

    print("\n2) an already-valid booking solves in one pass:")
    res = repair({"start": 10, "end": 12, "attendees": 8})
    print(f"   => {_fmt(res.state)}  iterations={res.iterations}")
    assert res.status is Status.SOLVED and res.iterations == 1

    print(
        "\nConstraint repair is just propose/check/revise where the check ranks "
        "candidates by how many rules they satisfy - and patience stops a repair "
        "that can never converge instead of spinning forever."
    )


if __name__ == "__main__":
    main()
