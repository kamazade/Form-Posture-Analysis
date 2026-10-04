from collections import deque
from dataclasses import dataclass, field
from statistics import median


@dataclass
class Rep:
    index: int
    start: int
    end: int
    min_knee: float
    peak_torso: float | None  # None: tekrar boyunca yan gorunum yoktu
    issues: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.issues

    def summary(self) -> str:
        torso = "olculemedi (on gorunum)" if self.peak_torso is None else f"{self.peak_torso:.0f}"
        verdict = "dogru" if self.ok else "; ".join(self.issues)
        return f"Tekrar {self.index}: {verdict} [diz min {self.min_knee:.0f}, govde tepe {torso}]"


class RepTracker:
    """Diz acisindan tekrar sinirlarini bulur; sayim degil, tekrar basina analiz icindir.

    Esikler (derece):
      down/up: tekrarin basladigi/bittigi diz acisi (histerezis).
      max_torso: tekrar boyunca tepe govde egimi bunu asarsa 'one cok egik'
                 (form1 max 45, form2 p10 50 verisinden).
      max_depth_knee: en derin diz acisi bunu asmazsa 'yeterince inmedi'
                 (ayarlanmadi; ornek videolar hep cok derindi).
    """

    def __init__(self, down=130, up=160, min_frames=6, smooth=5, max_torso=47, max_depth_knee=100):
        self.down, self.up, self.min_frames = down, up, min_frames
        self.max_torso, self.max_depth_knee = max_torso, max_depth_knee
        self._knees = deque(maxlen=smooth)
        self._torsos = deque(maxlen=smooth)
        self._cur = None
        self.reps: list[Rep] = []

    def update(self, frame: int, metrics: dict) -> Rep | None:
        """Kare metriklerini ver; bir tekrar bittiyse Rep dondurur."""
        self._knees.append(metrics["knee"])
        knee = median(self._knees)
        torso = None
        if "torso_lean" in metrics:
            self._torsos.append(metrics["torso_lean"])
            torso = median(self._torsos)
        if self._cur is None:
            if knee < self.down:
                self._cur = {"start": frame, "min_knee": knee, "peak_torso": torso}
            return None
        c = self._cur
        c["min_knee"] = min(c["min_knee"], knee)
        if torso is not None:
            c["peak_torso"] = torso if c["peak_torso"] is None else max(c["peak_torso"], torso)
        if knee > self.up:
            return self._close(frame)
        return None

    def finish(self, frame: int) -> Rep | None:
        """Video bitince acik kalan tekrari kapatir."""
        return self._close(frame) if self._cur else None

    def _close(self, frame: int) -> Rep | None:
        c, self._cur = self._cur, None
        if frame - c["start"] < self.min_frames:
            return None
        rep = Rep(len(self.reps) + 1, c["start"], frame, c["min_knee"], c["peak_torso"])
        if rep.min_knee > self.max_depth_knee:
            rep.issues.append(f"yeterince inmedi (diz {rep.min_knee:.0f})")
        if rep.peak_torso is not None and rep.peak_torso > self.max_torso:
            rep.issues.append(f"govde one cok egik ({rep.peak_torso:.0f})")
        self.reps.append(rep)
        return rep
