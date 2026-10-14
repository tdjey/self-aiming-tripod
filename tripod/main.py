import argparse
import time

import cv2

from tripod.camera import Camera
from tripod.config import Config
from tripod.controller import Controller, pixel_to_deg
from tripod.detector import Detector
from tripod.link import ManualLink, SerialLink
from tripod.tracker import Tracker, center_x
from tripod.viewer import draw


def parse_args():
    p = argparse.ArgumentParser(description="auto tracking tripod")
    p.add_argument("--port", help="arduino port, without it only shows the direction")
    p.add_argument("--camera", help="part of camera name")
    p.add_argument("--hfov", type=float, help="camera horizontal field of view")
    return p.parse_args()


def main():
    args = parse_args()
    cfg = Config()
    if args.camera:
        cfg.camera_name = args.camera
    if args.hfov:
        cfg.hfov = args.hfov

    camera = Camera(cfg.camera_name, cfg.width, cfg.height)
    detector = Detector(cfg.model, cfg.device, cfg.conf, cfg.imgsz)
    tracker = Tracker(cfg)
    controller = Controller(cfg)
    link = SerialLink(args.port, cfg) if args.port else ManualLink()

    frame_id = 0
    fps = 0.0
    last = time.monotonic()
    try:
        while True:
            frame, stamp, frame_id = camera.read(frame_id)
            if frame is None:
                # кадров нет - не держим старую команду поворота
                now = time.monotonic()
                link.send(controller.update(None, now), now)
                link.poll()
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
                continue

            h, w = frame.shape[:2]
            t0 = time.monotonic()
            boxes = detector.detect(frame)
            infer_ms = (time.monotonic() - t0) * 1000

            target = tracker.update(boxes, h)
            if tracker.new_target:
                controller.reset()
            angle = None
            if target is not None:
                angle = pixel_to_deg(center_x(target), w, cfg.hfov)
            cmd = controller.update(angle, stamp)
            link.send(cmd, stamp)
            link.poll()

            now = time.monotonic()
            fps = 0.9 * fps + 0.1 / max(now - last, 1e-6)
            last = now
            info = "fps %.0f  infer %.0f ms  people %d" % (fps, infer_ms, len(boxes))
            if link.at_limit:
                info += "  LIMIT"
            draw(frame, boxes, target, controller, cmd, cfg, info)
            cv2.imshow("tripod", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == ord("r"):
                tracker.reset()
                controller.reset()
    finally:
        link.close()
        camera.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
