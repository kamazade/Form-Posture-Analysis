from pathlib import Path

import cv2

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".bmp"}


def is_image(source: str) -> bool:
    return Path(source).suffix.lower() in IMAGE_EXT


def frames(source: str):
    """source: 'webcam' | video yolu | foto yolu. Kareleri (BGR) üretir."""
    if is_image(source):
        img = cv2.imread(source)
        if img is None:
            raise FileNotFoundError(source)
        yield img
        return
    cap = cv2.VideoCapture(0 if source == "webcam" else source)
    if not cap.isOpened():
        raise RuntimeError(f"Kaynak acilamadi: {source}")
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            yield frame
    finally:
        cap.release()
