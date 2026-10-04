from dataclasses import dataclass, field

import numpy as np

from .angles import angle_between, angle_from_vertical

# MediaPipe Pose landmark indeksleri
EAR, SHOULDER, HIP, KNEE, ANKLE = 7, 11, 23, 25, 27  # sol taraf
R_SHOULDER = 12

# Omuz genisligi / govde uzunlugu bu degerin ustundeyse kisi kameraya donuk;
# 2B govde egimi bu durumda anlamsiz oldugu icin olculmez.
FRONTAL_RATIO = 0.8

# Govde one egimi (3B, derece) bunu asarsa hata. Etiketli tekrarlarda dogrular en cok 56,
# one egik tekrarlar 58-62 cikti (dar marj).
MAX_TORSO = 57


@dataclass
class Feedback:
    metrics: dict = field(default_factory=dict)
    issues: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.issues


def _pt(lm, i, aspect=1.0):
    # Landmark'lar normalize (x/genislik, y/yukseklik); aci icin piksel orani gerekir.
    return (lm[i][0] * aspect, lm[i][1])


def _is_frontal(lm, aspect) -> bool:
    """aspect = kare genisligi / yuksekligi (landmark'lar normalize oldugu icin)."""
    sw = abs(lm[SHOULDER][0] - lm[R_SHOULDER][0]) * aspect
    tl = ((lm[SHOULDER][0] - lm[HIP][0]) * aspect) ** 2 + (lm[SHOULDER][1] - lm[HIP][1]) ** 2
    return tl > 0 and sw / tl**0.5 > FRONTAL_RATIO


def lateral_metrics(lm, aspect) -> dict:
    """Kameraya yari/tam donukken yana egilme gostergeleri; yan gorunumde bos dondurur.

    shoulder_tilt: omuz hattinin yataydan egimi (derece)
    trunk_shift: omuz merkezinin kalca merkezine gore yan kaymasi (govde boyu yuzdesi)
    hip_offset: kalca merkezinin ayak bilekleri ortasina gore yan konumu (govde boyu yuzdesi)
    """
    p = lambda i: np.array(_pt(lm, i, aspect))
    ms, mh = (p(SHOULDER) + p(R_SHOULDER)) / 2, (p(HIP) + p(HIP + 1)) / 2
    tl = np.linalg.norm(ms - mh)
    sw, hw = abs(p(SHOULDER)[0] - p(R_SHOULDER)[0]), abs(p(HIP)[0] - p(HIP + 1)[0])
    if tl == 0 or sw / tl <= 0.4 or hw / tl <= 0.25:
        return {}
    d = p(SHOULDER) - p(R_SHOULDER)
    tilt = abs((np.degrees(np.arctan2(d[1], d[0])) + 90) % 180 - 90)
    base = (p(ANKLE) + p(ANKLE + 1)) / 2
    return {
        "shoulder_tilt": float(tilt),
        "trunk_shift": float(abs(ms[0] - mh[0]) / tl * 100),
        "hip_offset": float((mh[0] - base[0]) / tl * 100),
    }


def torso_lean_3d(world) -> float:
    """Govdenin vucut cercevesinde (kalca ekseni) one/arkaya egimi, derece; kamera acisindan bagimsiz.

    world: MediaPipe 3B dunya landmark'lari [(x, y, z)], y asagi dogru.
    """
    w = np.asarray(world, dtype=float)
    trunk = (w[SHOULDER] + w[R_SHOULDER]) / 2 - (w[HIP] + w[HIP + 1]) / 2
    side = w[HIP] - w[HIP + 1]
    side[1] = 0.0
    n = np.linalg.norm(side)
    if n == 0:
        return 0.0
    forward = np.cross(side / n, [0.0, 1.0, 0.0])
    return float(abs(np.degrees(np.arctan2(trunk @ forward, -trunk[1]))))


def stance_ratio(world) -> float:
    """Ayak bilekleri arasi mesafe / omuz genisligi (3B)."""
    w = np.asarray(world, dtype=float)
    sw = np.linalg.norm(w[SHOULDER] - w[R_SHOULDER])
    return float(np.linalg.norm(w[ANKLE] - w[ANKLE + 1]) / sw) if sw else 0.0


def analyze_squat(lm, aspect: float = 1.0, world=None) -> Feedback:
    # Derin cokus (diz ~40-50 derece) gecerli bir squat; "cok derin" kurali yok.
    knee = angle_between(_pt(lm, HIP, aspect), _pt(lm, KNEE, aspect), _pt(lm, ANKLE, aspect))
    fb = Feedback(metrics={"knee": knee})
    torso = None
    if world is not None:
        torso = torso_lean_3d(world)
        fb.metrics["stance"] = stance_ratio(world)
    elif not _is_frontal(lm, aspect):  # 3B yoksa: 2B, yalniz yan gorunumde anlamli
        torso = angle_from_vertical(_pt(lm, SHOULDER, aspect), _pt(lm, HIP, aspect))
    fb.metrics.update(lateral_metrics(lm, aspect))
    if torso is not None:
        fb.metrics["torso_lean"] = torso
        if torso > MAX_TORSO:
            fb.issues.append("Govde fazla one egik")
    return fb


def analyze_sitting(lm, aspect: float = 1.0, world=None) -> Feedback:
    neck = angle_from_vertical(_pt(lm, EAR, aspect), _pt(lm, SHOULDER, aspect))
    torso = angle_from_vertical(_pt(lm, SHOULDER, aspect), _pt(lm, HIP, aspect))
    fb = Feedback(metrics={"neck_tilt": neck, "torso_lean": torso})
    if neck > 30:
        fb.issues.append("Bas one dusmus")
    if torso > 20:
        fb.issues.append("Sirt kamburlasmis")
    return fb


MODES = {"squat": analyze_squat, "sitting": analyze_sitting}
