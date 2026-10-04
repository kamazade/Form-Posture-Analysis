from dataclasses import dataclass, field

from .angles import angle_between, angle_from_vertical

# MediaPipe Pose landmark indeksleri
EAR, SHOULDER, HIP, KNEE, ANKLE = 7, 11, 23, 25, 27  # sol taraf
R_SHOULDER = 12

# Omuz genisligi / govde uzunlugu bu degerin ustundeyse kisi kameraya donuk;
# 2B govde egimi bu durumda anlamsiz oldugu icin olculmez.
FRONTAL_RATIO = 0.8


@dataclass
class Feedback:
    metrics: dict = field(default_factory=dict)
    issues: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.issues


def _pt(lm, i):
    return (lm[i][0], lm[i][1])


def _is_frontal(lm, aspect) -> bool:
    """aspect = kare genisligi / yuksekligi (landmark'lar normalize oldugu icin)."""
    sw = abs(lm[SHOULDER][0] - lm[R_SHOULDER][0]) * aspect
    tl = ((lm[SHOULDER][0] - lm[HIP][0]) * aspect) ** 2 + (lm[SHOULDER][1] - lm[HIP][1]) ** 2
    return tl > 0 and sw / tl**0.5 > FRONTAL_RATIO


def analyze_squat(lm, aspect: float = 1.0) -> Feedback:
    # Derin cokus (diz ~40-50 derece) gecerli bir squat; "cok derin" kurali yok.
    knee = angle_between(_pt(lm, HIP), _pt(lm, KNEE), _pt(lm, ANKLE))
    fb = Feedback(metrics={"knee": knee})
    if not _is_frontal(lm, aspect):
        torso = angle_from_vertical(_pt(lm, SHOULDER), _pt(lm, HIP))
        fb.metrics["torso_lean"] = torso
        if torso > 50:
            fb.issues.append("Govde fazla one egik")
    return fb


def analyze_sitting(lm, aspect: float = 1.0) -> Feedback:
    neck = angle_from_vertical(_pt(lm, EAR), _pt(lm, SHOULDER))
    torso = angle_from_vertical(_pt(lm, SHOULDER), _pt(lm, HIP))
    fb = Feedback(metrics={"neck_tilt": neck, "torso_lean": torso})
    if neck > 30:
        fb.issues.append("Bas one dusmus")
    if torso > 20:
        fb.issues.append("Sirt kamburlasmis")
    return fb


MODES = {"squat": analyze_squat, "sitting": analyze_sitting}
