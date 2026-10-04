# Form-Posture-Analysis

MediaPipe + OpenCV ile egzersiz formu ve statik postür analizi. Girdi: canlı webcam, video veya fotoğraf.

## Kurulum
Python 3.10+ ve MediaPipe 1.x (Tasks API) gerekir.

    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt

Pose modeli (~9 MB) `models/` altına indirilmelidir:

    mkdir models
    curl -L -o models/pose_landmarker_full.task https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task

## Kullanım

    python -m posture_analysis --mode squat --source webcam
    python -m posture_analysis --mode sitting --source video.mp4 --output outputs/out.mp4
    python -m posture_analysis --mode sitting --source foto.jpg --output outputs/out.jpg

Modlar: `squat` (diz/gövde açısı), `sitting` (boyun/gövde eğimi). Çıkış: `q`, `Esc` veya pencereyi kapat (X).

## Yapı
- `posture_analysis/angles.py` – saf geometri (test edilebilir)
- `posture_analysis/rules.py` – mod bazlı kurallar ve geri bildirim
- `posture_analysis/pose.py` – MediaPipe sarmalayıcı
- `posture_analysis/sources.py` – webcam/video/foto girdi
- `posture_analysis/cli.py` – komut satırı ve çizim
