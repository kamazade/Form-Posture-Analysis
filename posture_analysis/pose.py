import cv2
import mediapipe as mp


class PoseEstimator:
    def __init__(self, static: bool = False):
        self._mp_pose = mp.solutions.pose
        self._draw = mp.solutions.drawing_utils
        self._pose = self._mp_pose.Pose(static_image_mode=static)

    def process(self, frame_bgr):
        """(landmark listesi [(x, y, visibility)] | None, ham sonuç) döndürür; x,y normalize."""
        res = self._pose.process(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
        if not res.pose_landmarks:
            return None, res
        return [(p.x, p.y, p.visibility) for p in res.pose_landmarks.landmark], res

    def draw(self, frame, res):
        if res.pose_landmarks:
            self._draw.draw_landmarks(frame, res.pose_landmarks, self._mp_pose.POSE_CONNECTIONS)
