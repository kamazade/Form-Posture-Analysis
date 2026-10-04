import pytest

from posture_analysis.angles import angle_between, angle_from_vertical


def test_right_angle():
    assert angle_between((1, 0), (0, 0), (0, 1)) == pytest.approx(90)


def test_straight_line():
    assert angle_between((-1, 0), (0, 0), (1, 0)) == pytest.approx(180)


def test_vertical_upright():
    # y aşağı: üst nokta daha küçük y
    assert angle_from_vertical((0, 0), (0, 1)) == pytest.approx(0)


def test_vertical_leaning_45():
    assert angle_from_vertical((1, 0), (0, 1)) == pytest.approx(45)
