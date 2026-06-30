"""Scenario 14 - generalists: the candidate "state" can be anything.

cyclework is domain-agnostic - the state it refines is whatever you make it: a
number, a string, a dict, a list, a tuple, even a small data structure. The
engine never inspects the state; it only passes it to your check and revise.

This demo runs the *same* engine pattern over four wildly different state types
- a number, a list being sorted by bubble passes, a dict being filled in, and a
tuple representing a 2-D point walking to a target - to make the point that the
loop's shape is independent of the data.
"""
from _common import Engine, Verdict, rule, show_summary


def run_number():
    return Engine(lambda n: Verdict(ok=n >= 16, score=float(n)),
                  lambda n, v: n * 2, max_iterations=10).run(1)


def run_list_sort():
    def check(lst):
        sorted_pairs = sum(1 for a, b in zip(lst, lst[1:]) if a <= b)
        ok = lst == sorted(lst)
        return Verdict(ok=ok, score=float(sorted_pairs))

    def revise(lst, _v):  # one bubble pass
        out = list(lst)
        for i in range(len(out) - 1):
            if out[i] > out[i + 1]:
                out[i], out[i + 1] = out[i + 1], out[i]
        return out

    return Engine(check, revise, max_iterations=20).run([5, 1, 4, 2, 8, 3])


def run_dict_fill():
    need = ("name", "email", "plan")

    def check(d):
        missing = [k for k in need if k not in d]
        if missing:
            return Verdict.failed(f"need {missing[0]}", score=float(len(d)), fix=missing[0])
        return Verdict.passed(score=float(len(d)))

    def revise(d, v):
        return {**d, v.detail["fix"]: "<set>"}

    return Engine(check, revise, max_iterations=10).run({})


def run_point_walk():
    target = (3, 4)

    def check(p):
        dist = abs(p[0] - target[0]) + abs(p[1] - target[1])
        return Verdict(ok=dist == 0, score=-float(dist))

    def revise(p, _v):
        x = p[0] + (1 if p[0] < target[0] else -1 if p[0] > target[0] else 0)
        y = p[1] + (1 if p[1] < target[1] else -1 if p[1] > target[1] else 0)
        return (x, y)

    return Engine(check, revise, max_iterations=20).run((0, 0))


def main() -> None:
    rule("STATE IS ANYTHING  -  one engine, four candidate types")
    print("\nThe engine never looks inside the state. Number, list, dict, tuple -")
    print("same propose/check/revise loop, four totally different problems.\n")

    print("1) number doubling to >= 16:")
    r = run_number()
    print(f"   -> {r.state}")
    show_summary(r)

    print("\n2) list sorted by bubble passes:")
    r = run_list_sort()
    print(f"   -> {r.state}")
    show_summary(r)

    print("\n3) dict filled field by field:")
    r = run_dict_fill()
    print(f"   -> {r.state}")
    show_summary(r)

    print("\n4) (x,y) point walking to (3,4):")
    r = run_point_walk()
    print(f"   -> {r.state}")
    show_summary(r)

    print(
        "\nThe loop's shape is independent of the data. If you can score a "
        "candidate and produce a better one, cyclework can drive it."
    )


if __name__ == "__main__":
    main()
