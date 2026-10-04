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
    reps = run(k + [175] * 3 + k, [10] * len(k) + [0] * 3 + [55] * len(k))
    assert reps[0].ok
    assert not reps[1].ok and "govde" in reps[1].issues[0]


def test_frontal_rep_has_no_torso_verdict():
    reps = run([175] + squat(50) + [175])
    assert reps[0].peak_torso is None and reps[0].ok


def test_jitter_below_min_frames_ignored():
    assert run([175, 100, 175, 175]) == []
