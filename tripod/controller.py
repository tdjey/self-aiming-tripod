import math

LEFT, STOP, RIGHT = -1, 0, 1


def pixel_to_deg(x, width, hfov):
    f = (width / 2) / math.tan(math.radians(hfov / 2))
    return math.degrees(math.atan((x - width / 2) / f))


def deg_to_pixel(angle, width, hfov):
    f = (width / 2) / math.tan(math.radians(hfov / 2))
    return width / 2 + f * math.tan(math.radians(angle))


def sign(x):
    return RIGHT if x > 0 else LEFT


class AlphaBeta:
    def __init__(self, alpha, beta):
        self.alpha = alpha
        self.beta = beta
        self.reset()

    def reset(self):
        self.x = None
        self.v = 0.0
        self.t = 0.0

    def update(self, x, t, freeze_speed=False):
        if self.x is None:
            self.x = x
            self.t = t
            return
        dt = t - self.t
        self.t = t
        if freeze_speed:
            self.v = 0.0
            self.x += self.alpha * (x - self.x)
            return
        pred = self.x + self.v * dt
        r = x - pred
        self.x = pred + self.alpha * r
        if dt > 0:
            self.v += self.beta * r / dt


class Controller:
    def __init__(self, cfg):
        self.cfg = cfg
        self.filt = AlphaBeta(cfg.alpha, cfg.beta)
        self.reset()

    def reset(self):
        self.filt.reset()
        self.cmd = STOP
        self.settle_until = 0.0
        self.last_seen = None
        self.going_out_since = None

    def predicted(self):
        return self.filt.x + self.filt.v * self.cfg.predict_time

    def update(self, angle, t):
        if angle is None:
            return self.on_lost(t)
        self.last_seen = t

        # пока камера крутится, скорость человека в кадре врёт
        moving = self.cmd != STOP or t < self.settle_until
        self.filt.update(angle, t, freeze_speed=moving)
        x = self.filt.x

        if self.cmd != STOP:
            if abs(x) < self.cfg.stop_deg or x * self.cmd < 0:
                self.stop(t)
            return self.cmd

        if t < self.settle_until:
            return STOP

        if abs(x) > self.cfg.edge_deg:
            self.cmd = sign(x)
            return self.cmd

        # идёт к краю: прогноз должен держаться какое-то время, иначе дрожание
        # бокса или взмах рукой тоже выглядят как движение
        pred = self.predicted()
        if abs(x) > self.cfg.warn_deg and abs(pred) > self.cfg.edge_deg and pred * x > 0:
            if self.going_out_since is None:
                self.going_out_since = t
            if t - self.going_out_since >= self.cfg.confirm_time:
                self.cmd = sign(x)
        else:
            self.going_out_since = None
        return self.cmd

    def on_lost(self, t):
        if self.last_seen is None:
            return STOP
        gone = t - self.last_seen
        x = self.filt.x

        if gone > self.cfg.lost_hold:
            self.reset()
            self.settle_until = t + self.cfg.settle_time
        elif abs(x) > self.cfg.edge_deg:
            # ушёл за край, докручиваем в ту сторону
            self.cmd = sign(x)
        elif gone > self.cfg.blink_time and self.cmd != STOP:
            self.stop(t)
        return self.cmd

    def stop(self, t):
        self.cmd = STOP
        self.going_out_since = None
        self.settle_until = t + self.cfg.settle_time
