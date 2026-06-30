"""Edge cases for the worked examples in cyclework.examples.

Convergence corners (perfect squares, large/small inputs), error paths
(negative sqrt), budget-bounded non-convergence (diverging fixed points),
and the slug refiner's individual rules and idempotence.
"""
import math

import pytest

from cyclework import Status
from cyclework.examples import fixed_point, refine_slug, sqrt_newton


# --------------------------------------------------------------------------
# sqrt_newton
# --------------------------------------------------------------------------
def test_sqrt_perfect_square():
    res = sqrt_newton(144.0)
    assert res.solved
    assert abs(res.state - 12.0) < 1e-9


def test_sqrt_one():
    res = sqrt_newton(1.0)
    assert res.solved
    assert abs(res.state - 1.0) < 1e-9


def test_sqrt_of_one_is_immediate():
    # seed is max(n, 1.0) = 1.0; 1*1 == 1 so it solves on the first check
    res = sqrt_newton(1.0)
    assert res.iterations == 1


def test_sqrt_large_number():
    res = sqrt_newton(1e12)
    assert res.solved
    assert abs(res.state - 1e6) < 1e-3


def test_sqrt_small_number():
    res = sqrt_newton(1e-6)
    assert res.solved
    assert abs(res.state - 1e-3) < 1e-6


def test_sqrt_negative_raises():
    with pytest.raises(ValueError, match="non-negative"):
        sqrt_newton(-4.0)


def test_sqrt_doubles_precision_quickly():
    res = sqrt_newton(2.0, max_iterations=50)
    assert res.iterations < 12


def test_sqrt_tight_budget_can_exhaust():
    # one Newton step is not enough to hit a 1e-12 tolerance from seed
    res = sqrt_newton(2.0, max_iterations=2)
    assert res.status is Status.EXHAUSTED
    # but the best candidate is already a decent approximation
    assert abs(res.best.state - math.sqrt(2.0)) < 0.1


# --------------------------------------------------------------------------
# fixed_point
# --------------------------------------------------------------------------
def test_fixed_point_cos():
    res = fixed_point(math.cos, 1.0)
    assert res.solved
    assert abs(math.cos(res.state) - res.state) < 1e-9


def test_fixed_point_already_at_solution():
    # f(x) = x for the identity-ish map: x -> x/2 + 1 has fixed point 2
    res = fixed_point(lambda x: x / 2 + 1, 2.0)
    assert res.solved
    assert res.iterations == 1
    assert abs(res.state - 2.0) < 1e-12


def test_fixed_point_contraction_converges():
    # x -> (x + 4/x)/2 converges to sqrt(4) = 2
    res = fixed_point(lambda x: (x + 4 / x) / 2, 3.0)
    assert res.solved
    assert abs(res.state - 2.0) < 1e-9


def test_fixed_point_divergent_exhausts():
    # x -> 2x + 1 has fixed point -1 but iterating from 1 diverges
    res = fixed_point(lambda x: 2 * x + 1, 1.0, max_iterations=20)
    assert res.status is Status.EXHAUSTED
    assert not res.solved


def test_fixed_point_error_propagates_as_error_status():
    # f raises -> engine surfaces ERROR rather than crashing
    def f(x):
        raise ZeroDivisionError("bad map")

    res = fixed_point(f, 1.0)
    assert res.status is Status.ERROR
    assert "bad map" in res.error


# --------------------------------------------------------------------------
# refine_slug — full pipeline & individual rules
# --------------------------------------------------------------------------
def test_slug_full_messy_input():
    res = refine_slug("  Hello,  World!!  ")
    assert res.solved
    assert res.state == "hello-world"


def test_slug_already_clean_one_pass():
    res = refine_slug("already-clean")
    assert res.solved
    assert res.iterations == 1


def test_slug_only_uppercase():
    res = refine_slug("HELLO")
    assert res.state == "hello"


def test_slug_only_needs_trim():
    res = refine_slug("clean-already   ")
    assert res.solved
    assert res.state == "clean-already"


def test_slug_collapses_multiple_dashes():
    res = refine_slug("Cognis Digital --- Accountable AI")
    assert res.solved
    assert "--" not in res.state
    assert not res.state.startswith("-")
    assert not res.state.endswith("-")


def test_slug_strips_symbols():
    res = refine_slug("c@#$%plus+plus")
    assert res.solved
    assert all(c.isalnum() or c == "-" for c in res.state)


def test_slug_truncates_to_max_len():
    res = refine_slug("a b c d e f g h i j k l m n o p q r s t u v", max_len=10)
    assert res.solved
    assert len(res.state) <= 10
    assert not res.state.endswith("-")


def test_slug_empty_string_is_already_valid():
    res = refine_slug("")
    assert res.solved
    assert res.state == ""


def test_slug_is_idempotent():
    once = refine_slug("Hello, World!").state
    twice = refine_slug(once).state
    assert once == twice
    assert refine_slug(once).iterations == 1


def test_slug_unicode_symbols_removed():
    res = refine_slug("café déjà vu")
    assert res.solved
    assert all(c.isalnum() or c == "-" for c in res.state)
