import argparse
from pathlib import Path

import cv2

from .pose import PoseEstimator
from .reps import RepTracker
from .rules import MODES
from .sources import frames, is_image


def overlay(frame, fb):
    y = 25
    for k, v in fb.metrics.items():
        cv2.putText(frame, f"{k}: {v:.0f}", (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        y += 25
    for issue in fb.issues:
        cv2.putText(frame, issue, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        y += 28


def overlay_reps(frame, reps, last_n=3):
    h = frame.shape[0]
    for k, rep in enumerate(reps[-last_n:][::-1]):
        color = (0, 200, 0) if rep.ok else (0, 0, 255)
        cv2.putText(frame, rep.summary(), (10, h - 15 - 28 * k), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)


def main():
    p = argparse.ArgumentParser(prog="posture_analysis")
    p.add_argument("--mode", choices=MODES, required=True)
    p.add_argument("--source", default="webcam", help="webcam | video | foto yolu")
    p.add_argument("--output", help="Cikti dosyasi (video veya foto)")
    p.add_argument("--no-display", action="store_true")
    args = p.parse_args()

    analyze = MODES[args.mode]
    estimator = PoseEstimator(static=is_image(args.source))
    writer = None
    tracker = RepTracker() if args.mode == "squat" and not is_image(args.source) else None
    n = 0
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    for n, frame in enumerate(frames(args.source)):
        lm, pts = estimator.process(frame)
        if lm:
            estimator.draw(frame, pts)
            fb = analyze(lm, frame.shape[1] / frame.shape[0])
            overlay(frame, fb)
            if tracker:
                rep = tracker.update(n, fb.metrics)
                if rep:
                    print(rep.summary())
        else:
            cv2.putText(frame, "Kisi bulunamadi", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)

        if tracker:
            overlay_reps(frame, tracker.reps)

        if args.output:
            if is_image(args.output):
                cv2.imwrite(args.output, frame)
            else:
                if writer is None:
                    h, w = frame.shape[:2]
                    writer = cv2.VideoWriter(args.output, cv2.VideoWriter_fourcc(*"mp4v"), 30, (w, h))
                writer.write(frame)
        if not args.no_display:
            cv2.imshow("Posture Analysis", frame)
            if is_image(args.source):
                cv2.waitKey(0)
            else:
                key = cv2.waitKey(1) & 0xFF
                closed = cv2.getWindowProperty("Posture Analysis", cv2.WND_PROP_VISIBLE) < 1
                if key in (ord("q"), 27) or closed:  # q, Esc veya pencere kapatma (X)
                    break
    if tracker:
        if tracker.finish(n):
            print(tracker.reps[-1].summary())
    if writer:
        writer.release()
    cv2.destroyAllWindows()
