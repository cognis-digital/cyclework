import math

from cyclework.examples import fixed_point, refine_slug, sqrt_newton


def test_sqrt_newton_converges():
    res = sqrt_newton(2.0)
    assert res.solved
    assert abs(res.state - math.sqrt(2.0)) < 1e-9
    # Newton doubles precision each step; should be quick
    assert res.iterations < 12


def test_sqrt_newton_zero():
    res = sqrt_newton(0.0)
    assert res.solved
    assert abs(res.state) < 1e-6


def test_fixed_point_cosine():
    # the Dottie number: fixed point of cos(x)
    res = fixed_point(math.cos, 1.0)
    assert res.solved
    assert abs(math.cos(res.state) - res.state) < 1e-9


def test_refine_slug_full_pipeline():
    res = refine_slug("  Hello,  World!!  ")
    assert res.solved
    assert res.state == "hello-world"


def test_refine_slug_truncates():
    res = refine_slug("a b c d e f g h i j k l m n o p q r s t u v", max_len=10)
    assert res.solved
    assert len(res.state) <= 10
    assert not res.state.endswith("-")


def test_refine_slug_already_clean_is_one_pass():
    res = refine_slug("already-clean")
    assert res.solved
    assert res.iterations == 1
