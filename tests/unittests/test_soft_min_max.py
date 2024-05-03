import pytest
from mimosa.common import soft_min, soft_max, soft_switch


@pytest.mark.parametrize(
    "x, scale",
    [(1, None), (-1, None), (10, None), (-10, None), (0.02, 0.01), (-0.02, 0.01)],
)
def test_soft_switch(x, scale):
    value = soft_switch(x) if scale is None else soft_switch(x, scale)
    assert 0 < value < 1

    # For (relatively) large positive values, switch should be almost 1
    if x > 0:
        assert value == pytest.approx(1, abs=0.03)

    # For (relatively) large negative values, switch should be almost 0
    if x < 0:
        assert value == pytest.approx(0, abs=0.03)


def test_soft_min_positive():
    """For (relatively) large positive values, soft_min should be almost x"""
    for x in [1, 10, 100]:
        assert soft_min(x) == pytest.approx(x, 0.03)


def test_soft_min_negative():
    """For (relatively) large negative values, soft_min should be almost 0"""
    for x in [-1, -10, -100]:
        value = soft_min(x)
        assert value == pytest.approx(0, abs=0.03)
        assert value > 0


def test_soft_max_positive():
    """For values larger than maxval, soft_max should be almost maxval"""
    assert soft_max(1, 0) == pytest.approx(0, abs=0.02)
    assert soft_max(10, 5) == pytest.approx(5, 0.02)
    assert soft_max(0.02, 0.005, 0.01) == pytest.approx(0.005, 0.02)


def test_soft_max_negative():
    """For values smaller than maxval, soft_max should be almost x"""
    assert soft_max(-1, 0) == pytest.approx(-1, 0.02)
    assert soft_max(-10, -5) == pytest.approx(-10, 0.02)
    assert soft_max(-0.02, -0.005, 0.01) == pytest.approx(-0.02, 0.02)
