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
    stance: float | None = None  # ayakta ayak mesafesi / omuz genisligi

    @property
    def ok(self) -> bool:
        return not self.issues

    def summary(self) -> str:
        torso = "-" if self.peak_torso is None else f"{self.peak_torso:.0f}"
        verdict = "dogru" if self.ok else "; ".join(self.issues)
        return f"Tekrar {self.index}: {verdict} [diz min {self.min_knee:.0f}, govde tepe {torso}]"


class RepTracker:
    """Diz acisindan tekrar sinirlarini bulur; sayim degil, tekrar basina analiz icindir.

    Esikler (derece):
      down/up: tekrarin basladigi/bittigi diz acisi (histerezis).
      max_torso: tekrar boyunca tepe govde egimi (3B) bunu asarsa 'one cok egik'
                 (etiketli dogrular en cok 56, one egikler 58-62).
      max_stance: tekrar oncesi ayakta ayak mesafesi / omuz genisligi bunu asarsa
                 'bacaklar cok acik' (yanlis 1.47, dogrular en cok 1.24).
      lat_*: omuz egimi >= lat_tilt VE omuz merkezi kaymasi >= lat_shift (govde boyu %),
                 en az lat_frames kare surerse 'yana egilme'. Dizler az bukuldugunde
                 tekrar sayilmayabilecegi icin ayri bir hareket olarak da eklenir.
      max_depth_knee: en derin diz acisi bunu asmazsa 'yeterince inmedi'
                 (ayarlanmadi; ornek videolar hep cok derindi).
    """

    def __init__(self, down=130, up=160, min_frames=6, smooth=5, max_torso=57, max_depth_knee=100, max_stance=1.35,
                 lat_tilt=14, lat_shift=20, lat_frames=8):
        self.down, self.up, self.min_frames = down, up, min_frames
        self.max_torso, self.max_depth_knee, self.max_stance = max_torso, max_depth_knee, max_stance
        self.lat_tilt, self.lat_shift, self.lat_frames = lat_tilt, lat_shift, lat_frames
        self._lat = None
        self._stance = deque(maxlen=40)  # ayakta iken son stance degerleri
        self._knees = deque(maxlen=smooth)
        self._torsos = deque(maxlen=smooth)
        self._cur = None
        self.reps: list[Rep] = []

    def update(self, frame: int, metrics: dict) -> Rep | None:
        """Kare metriklerini ver; bir tekrar/hareket bittiyse Rep dondurur."""
        lat = self._lateral_step(frame, metrics)
        return self._knee_step(frame, metrics) or lat

    def _lateral_step(self, frame: int, metrics: dict) -> Rep | None:
        flag = (
            metrics.get("shoulder_tilt", 0) >= self.lat_tilt
            and metrics.get("trunk_shift", 0) >= self.lat_shift
        )
        if flag:
            r = self._lat or {"start": frame, "n": 0, "tilt": 0.0, "shift": 0.0, "min_knee": metrics["knee"]}
            r["n"] += 1
            r["tilt"], r["shift"] = max(r["tilt"], metrics["shoulder_tilt"]), max(r["shift"], metrics["trunk_shift"])
            r["min_knee"] = min(r["min_knee"], metrics["knee"])
            self._lat = r
            return None
        return self._close_lateral(frame)

    def _close_lateral(self, frame: int) -> Rep | None:
        r, self._lat = self._lat, None
        if r is None or r["n"] < self.lat_frames:
            return None
        msg = f"yana egilme (omuz {r['tilt']:.0f} derece, kayma %{r['shift']:.0f})"
        if self._cur is not None:  # squat sirasinda: o tekrara ekle
            self._cur["lateral"] = msg
            return None
        rep = Rep(len(self.reps) + 1, r["start"], frame, r["min_knee"], None, [msg])
        self.reps.append(rep)
        return rep

    def _knee_step(self, frame: int, metrics: dict) -> Rep | None:
        self._knees.append(metrics["knee"])
        knee = median(self._knees)
        torso = None
        if "torso_lean" in metrics:
            self._torsos.append(metrics["torso_lean"])
            torso = median(self._torsos)
        if self._cur is None:
            if knee < self.down:
                stance = median(self._stance) if self._stance else None
                self._cur = {"start": frame, "min_knee": knee, "peak_torso": torso, "stance": stance}
            elif knee > self.up and "stance" in metrics:
                self._stance.append(metrics["stance"])
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
        lat = self._close_lateral(frame)
        return (self._close(frame) if self._cur else None) or lat

    def _close(self, frame: int) -> Rep | None:
        c, self._cur = self._cur, None
        if frame - c["start"] < self.min_frames:
            return None
        rep = Rep(len(self.reps) + 1, c["start"], frame, c["min_knee"], c["peak_torso"], stance=c["stance"])
        if rep.min_knee > self.max_depth_knee:
            rep.issues.append(f"yeterince inmedi (diz {rep.min_knee:.0f})")
        if rep.stance is not None and rep.stance > self.max_stance:
            rep.issues.append(f"bacaklar cok acik ({rep.stance:.2f}x omuz)")
        if rep.peak_torso is not None and rep.peak_torso > self.max_torso:
            rep.issues.append(f"govde one cok egik ({rep.peak_torso:.0f})")
        if c.get("lateral"):
            rep.issues.append(c["lateral"])
        self.reps.append(rep)
        return rep
