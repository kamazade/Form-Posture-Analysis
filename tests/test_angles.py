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


def _lm(**pts):
    lm = [(0.0, 0.0, 1.0)] * 33
    for k, v in pts.items():
        lm[int(k[1:])] = (*v, 1.0)
    return lm


def test_squat_deep_is_not_flagged():
    from posture_analysis.rules import analyze_squat
    # kalca-diz-ayak bilegi ~45 derece, govde dik, yandan gorunum (omuzlar ust uste)
    lm = _lm(p11=(0.5, 0.3), p12=(0.5, 0.3), p23=(0.5, 0.6), p25=(0.7, 0.6), p27=(0.5, 0.75))
    fb = analyze_squat(lm, 16 / 9)
    assert fb.ok and fb.metrics["knee"] < 60


def test_squat_torso_skipped_when_frontal():
    from posture_analysis.rules import analyze_squat
    lm = _lm(p11=(0.4, 0.3), p12=(0.6, 0.3), p23=(0.45, 0.6), p25=(0.45, 0.8), p27=(0.45, 0.95))
    assert "torso_lean" not in analyze_squat(lm, 16 / 9).metrics


def test_aspect_scales_x_for_angles():
    from posture_analysis.rules import analyze_squat
    # normalize koordinatta 45 derece gorunen govde, 16:9 karede gercekte ~60 dereceye yakin egimlidir
    lm = _lm(p11=(0.6, 0.4), p12=(0.6, 0.4), p23=(0.5, 0.6), p25=(0.5, 0.8), p27=(0.5, 0.95))
    sq = analyze_squat(lm, 1.0).metrics["torso_lean"]
    wide = analyze_squat(lm, 16 / 9).metrics["torso_lean"]
    assert wide > sq + 10
