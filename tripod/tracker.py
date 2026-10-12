def center_x(box):
    return (box[0] + box[2]) / 2


def height(box):
    return box[3] - box[1]


def iou(a, b):
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    if w <= 0 or h <= 0:
        return 0.0
    inter = w * h
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    return inter / (area_a + area_b - inter)


class Tracker:
    def __init__(self, cfg):
        self.cfg = cfg
        self.reset()

    def reset(self):
        self.box = None
        self.missed = 0
        self.new_target = False

    def update(self, boxes, frame_h):
        self.new_target = False
        boxes = [b for b in boxes if b[1] < self.cfg.max_box_top * frame_h]

        if self.box is None:
            if not boxes:
                return None
            # лектор стоит, поэтому его бокс обычно самый высокий
            self.box = max(boxes, key=height)
            self.missed = 0
            self.new_target = True
            return self.box

        best = self.match(boxes)
        if best is None:
            self.missed += 1
            if self.missed > self.cfg.max_missed:
                self.reset()
            return None

        self.box = best
        self.missed = 0
        return best

    def match(self, boxes):
        if not boxes:
            return None
        best = max(boxes, key=lambda b: iou(b, self.box))
        if iou(best, self.box) >= self.cfg.min_iou:
            return best
        if self.missed > 0:
            return None

        # при повороте камеры бокс может уехать сильно, тогда ищем ближайший по x
        # среди людей похожего роста, чтобы не перескочить на соседа
        cx = center_x(self.box)
        h = height(self.box)
        similar = [b for b in boxes if 0.7 < height(b) / h < 1.4]
        if not similar:
            return None
        best = min(similar, key=lambda b: abs(center_x(b) - cx))
        if abs(center_x(best) - cx) < self.cfg.max_jump * (self.box[2] - self.box[0]):
            return best
        return None
