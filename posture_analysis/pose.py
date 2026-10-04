from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision

DEFAULT_MODEL = Path(__file__).resolve().parent.parent / "models" / "pose_landmarker_full.task"


class PoseEstimator:
    def __init__(self, static: bool = False, model_path: Path = DEFAULT_MODEL):
        if not Path(model_path).exists():
            raise FileNotFoundError(
                f"Model bulunamadi: {model_path} (README'deki indirme adimina bak)"
            )
        # Yerel kutuphane Windows'ta ASCII disi yollari (or. 'Masaüstü') acamaz; bellekten yukle.
        model_bytes = Path(model_path).read_bytes()
        self._static = static
        mode = vision.RunningMode.IMAGE if static else vision.RunningMode.VIDEO
        options = vision.PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_buffer=model_bytes), running_mode=mode
        )
        self._landmarker = vision.PoseLandmarker.create_from_options(options)
        self._ts_ms = 0

    def process(self, frame_bgr):
        """(landmark listesi [(x, y, visibility)] | None, ham landmark) döndürür; x,y normalize."""
        img = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
        if self._static:
            res = self._landmarker.detect(img)
        else:
            self._ts_ms += 33  # monoton artan zaman damgası
            res = self._landmarker.detect_for_video(img, self._ts_ms)
        if not res.pose_landmarks:
            return None, None
        pts = res.pose_landmarks[0]
        return [(p.x, p.y, p.visibility) for p in pts], pts

    def draw(self, frame, pts):
        if pts is None:
            return
        h, w = frame.shape[:2]
        xy = [(int(p.x * w), int(p.y * h)) for p in pts]
        for c in vision.PoseLandmarksConnections.POSE_LANDMARKS:
            cv2.line(frame, xy[c.start], xy[c.end], (0, 255, 0), 2)
        for x, y in xy:
            cv2.circle(frame, (x, y), 3, (0, 0, 255), -1)
