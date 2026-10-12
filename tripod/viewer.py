import cv2

from tripod.controller import LEFT, RIGHT, deg_to_pixel

GRAY = (160, 160, 160)
GREEN = (0, 220, 0)
YELLOW = (0, 220, 220)
RED = (0, 0, 230)


def draw_zone(img, angle, cfg, color):
    h, w = img.shape[:2]
    for a in (-angle, angle):
        x = int(deg_to_pixel(a, w, cfg.hfov))
        cv2.line(img, (x, 0), (x, h), color, 1)


def draw(img, boxes, target, controller, cmd, cfg, info):
    h, w = img.shape[:2]
    draw_zone(img, cfg.stop_deg, cfg, GREEN)
    draw_zone(img, cfg.warn_deg, cfg, YELLOW)
    draw_zone(img, cfg.edge_deg, cfg, RED)
    cv2.line(img, (0, int(cfg.max_box_top * h)), (w, int(cfg.max_box_top * h)), GRAY, 1)

    for b in boxes:
        cv2.rectangle(img, (int(b[0]), int(b[1])), (int(b[2]), int(b[3])), GRAY, 1)
    if target is not None:
        cv2.rectangle(img, (int(target[0]), int(target[1])), (int(target[2]), int(target[3])), GREEN, 2)

    if controller.filt.x is not None:
        x = int(deg_to_pixel(controller.filt.x, w, cfg.hfov))
        px = int(deg_to_pixel(controller.predicted(), w, cfg.hfov))
        y = h // 2
        cv2.circle(img, (x, y), 6, GREEN, -1)
        cv2.arrowedLine(img, (x, y), (px, y), YELLOW, 2)

    if cmd == LEFT:
        text, color = "<<< LEFT", RED
    elif cmd == RIGHT:
        text, color = "RIGHT >>>", RED
    else:
        text, color = "STOP", GREEN
    size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 2.5, 6)[0]
    cv2.putText(img, text, ((w - size[0]) // 2, 90), cv2.FONT_HERSHEY_SIMPLEX, 2.5, color, 6)

    cv2.putText(img, info, (10, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
