import argparse
from pathlib import Path

import cv2

from .pose import PoseEstimator
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
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    for frame in frames(args.source):
        lm, res = estimator.process(frame)
        if lm:
            estimator.draw(frame, res)
            overlay(frame, analyze(lm))
        else:
            cv2.putText(frame, "Kisi bulunamadi", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)

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
            elif cv2.waitKey(1) & 0xFF == ord("q"):
                break
    if writer:
        writer.release()
    cv2.destroyAllWindows()
