from dataclasses import dataclass, field

from .angles import angle_between, angle_from_vertical

# MediaPipe Pose landmark indeksleri
EAR, SHOULDER, HIP, KNEE, ANKLE = 7, 11, 23, 25, 27  # sol taraf


@dataclass
class Feedback:
    metrics: dict = field(default_factory=dict)
    issues: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.issues


def _pt(lm, i):
    return (lm[i][0], lm[i][1])


def analyze_squat(lm) -> Feedback:
    knee = angle_between(_pt(lm, HIP), _pt(lm, KNEE), _pt(lm, ANKLE))
    torso = angle_from_vertical(_pt(lm, SHOULDER), _pt(lm, HIP))
    fb = Feedback(metrics={"knee": knee, "torso_lean": torso})
    if torso > 55:
        fb.issues.append("Govde fazla one egik")
    if knee < 70:
        fb.issues.append("Cok derin cokuyorsun")
    return fb


def analyze_sitting(lm) -> Feedback:
    neck = angle_from_vertical(_pt(lm, EAR), _pt(lm, SHOULDER))
    torso = angle_from_vertical(_pt(lm, SHOULDER), _pt(lm, HIP))
    fb = Feedback(metrics={"neck_tilt": neck, "torso_lean": torso})
    if neck > 30:
        fb.issues.append("Bas one dusmus")
    if torso > 20:
        fb.issues.append("Sirt kamburlasmis")
    return fb


MODES = {"squat": analyze_squat, "sitting": analyze_sitting}
