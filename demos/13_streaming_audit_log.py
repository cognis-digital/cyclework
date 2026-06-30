"""Scenario 13 - compliance / audit engineers: the trace IS the audit log.

When a self-correcting system makes a decision, "it worked" is not enough - you
need a record of every step: what each candidate was, how it scored, what the
checker said, and why the loop stopped. cyclework records all of that, and the
`on_iteration` hook lets you stream it to an audit sink as it happens.

This demo wires an observer that appends a structured record per iteration to an
in-memory "audit log", runs a refinement, then prints the log and a final
attestation built from `Result.summary()` - the kind of artifact you would
hand a reviewer.
"""
import json

from _common import Engine, Verdict, rule


def main() -> None:
    rule("STREAMING AUDIT LOG  -  every step recorded as it happens")
    print("\nA review loop scores a 'document' and revises it until it passes.")
    print("An on_iteration observer streams a structured record per step.\n")

    audit_log = []

    def observer(it):
        audit_log.append({
            "step": it.index,
            "candidate": dict(it.state),
            "score": it.score,
            "passed": it.verdict.ok,
            "note": it.verdict.feedback or None,
        })

    # the "document" gains required sections one at a time
    START = {"has_title": False, "has_summary": False, "has_signoff": False}

    def check(doc):
        missing = [k for k, v in doc.items() if not v]
        score = -float(len(missing))
        if missing:
            return Verdict.failed(f"missing: {missing[0]}", score=score, fix=missing[0])
        return Verdict.passed(score=0.0)

    def revise(doc, v):
        nxt = dict(doc)
        nxt[v.detail["fix"]] = True
        return nxt

    res = Engine(check, revise, max_iterations=10, on_iteration=observer).run(START)

    print("   --- streamed audit log -------------------------------------")
    for rec in audit_log:
        print("   " + json.dumps(rec, sort_keys=True))

    print("\n   --- final attestation --------------------------------------")
    print("   " + json.dumps(res.summary(), sort_keys=True))
    print(f"\n   Decision: {'APPROVED' if res.solved else 'NOT APPROVED'} "
          f"after {res.iterations} reviewed revisions.")

    print(
        "\nThe loop is no longer a black box: the audit log reconstructs every "
        "decision, and the attestation summarizes the outcome for a reviewer."
    )


if __name__ == "__main__":
    main()
