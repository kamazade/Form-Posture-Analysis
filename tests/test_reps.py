from posture_analysis.reps import RepTracker


def run(knees, torsos=None):
    t = RepTracker(smooth=1)
    for i, k in enumerate(knees):
        m = {"knee": k}
        if torsos is not None:
            m["torso_lean"] = torsos[i]
        t.update(i, m)
    t.finish(len(knees))
    return t.reps


def squat(bottom, n=10):
    down = [175 - (175 - bottom) * i / n for i in range(n + 1)]
    return down + down[::-1][1:]


def test_two_reps_grouped_separately():
    reps = run([175] * 5 + squat(50) + [175] * 5 + squat(60) + [175] * 5)
    assert [r.index for r in reps] == [1, 2]
    assert reps[0].min_knee == 50 and reps[1].min_knee == 60


def test_shallow_rep_flagged():
    reps = run([175] + squat(120) + [175])
    assert len(reps) == 1 and any("yeterince" in i for i in reps[0].issues)


def test_leaning_rep_flagged_and_good_rep_ok():
    k = squat(50)
    reps = run(k + [175] * 3 + k, [10] * len(k) + [0] * 3 + [65] * len(k))
    assert reps[0].ok
    assert not reps[1].ok and "govde" in reps[1].issues[0]


def test_frontal_rep_has_no_torso_verdict():
    reps = run([175] + squat(50) + [175])
    assert reps[0].peak_torso is None and reps[0].ok


def test_jitter_below_min_frames_ignored():
    assert run([175, 100, 175, 175]) == []


def test_wide_stance_flagged():
    t = RepTracker(smooth=1)
    for i in range(30):
        t.update(i, {"knee": 175, "stance": 1.5})
    for i, k in enumerate(squat(50)):
        t.update(30 + i, {"knee": k, "stance": 1.5})
    t.finish(100)
    assert any("bacaklar" in x for x in t.reps[0].issues)


def test_lateral_event_without_knee_bend_becomes_own_entry():
    t = RepTracker(smooth=1)
    for i in range(10):
        t.update(i, {"knee": 175})
    for i in range(10, 25):
        t.update(i, {"knee": 150, "shoulder_tilt": 18, "trunk_shift": 30})
    t.update(25, {"knee": 175})
    assert len(t.reps) == 1 and "yana egilme" in t.reps[0].issues[0]


def test_short_lateral_blip_ignored():
    t = RepTracker(smooth=1)
    for i in range(3):
        t.update(i, {"knee": 175, "shoulder_tilt": 18, "trunk_shift": 30})
    t.update(3, {"knee": 175})
    assert t.reps == []


def test_standing_shoulder_tilt_is_not_a_movement():
    t = RepTracker(smooth=1)
    for i in range(30):
        t.update(i, {"knee": 168, "shoulder_tilt": 30, "trunk_shift": 40})
    t.update(30, {"knee": 175})
    assert t.reps == []


def _sway_rep(amp):
    t = RepTracker(smooth=1)
    k = squat(50, 20)
    for i, kn in enumerate(k):
        t.update(i, {"knee": kn, "hip_offset": amp * (1 if (i // 4) % 2 else -1)})
    t.finish(len(k))
    return t.reps[0]


def test_hip_sway_flagged_when_large():
    rep = _sway_rep(20)
    assert rep.sway == 40 and any("kalca" in x for x in rep.issues)


def test_small_hip_sway_ok():
    assert _sway_rep(5).ok
