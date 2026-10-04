# Form-Posture-Analysis

MediaPipe + OpenCV ile egzersiz formu ve statik postür analizi. Girdi: canlı webcam, video veya fotoğraf.

## Kurulum
MediaPipe henüz tüm Python sürümlerini desteklemez; Python 3.10–3.12 önerilir.

    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt

## Kullanım

    python -m posture_analysis --mode squat --source webcam
    python -m posture_analysis --mode sitting --source video.mp4 --output outputs/out.mp4
    python -m posture_analysis --mode sitting --source foto.jpg --output outputs/out.jpg

Modlar: `squat` (diz/gövde açısı), `sitting` (boyun/gövde eğimi). Çıkış: `q`.

## Yapı
- `posture_analysis/angles.py` – saf geometri (test edilebilir)
- `posture_analysis/rules.py` – mod bazlı kurallar ve geri bildirim
- `posture_analysis/pose.py` – MediaPipe sarmalayıcı
- `posture_analysis/sources.py` – webcam/video/foto girdi
- `posture_analysis/cli.py` – komut satırı ve çizim
