import random

from tripod.config import Config
from tripod.controller import LEFT, RIGHT, STOP, Controller, deg_to_pixel, pixel_to_deg

FPS = 30


def run(angles, cfg=None):
    ctrl = Controller(cfg or Config())
    return [ctrl.update(a, i / FPS) for i, a in enumerate(angles)]


def noisy(base, n, amp=3.0, seed=0):
    rnd = random.Random(seed)
    return [base + rnd.uniform(-amp, amp) for _ in range(n)]


def test_pixel_deg():
    for x in (0, 300, 640, 1000, 1279):
        assert abs(deg_to_pixel(pixel_to_deg(x, 1280, 70), 1280, 70) - x) < 1e-6
    assert pixel_to_deg(640, 1280, 70) == 0
    assert abs(pixel_to_deg(1280, 1280, 70) - 35) < 1e-6


def test_quiet_cases():
    cases = {
        "center": [0.0] * 90,
        "jitter near center": noisy(8, 300),
        "standing at the board": [18.0] * 150,
        "walking back to center": [20 - 15 * i / FPS for i in range(60)],
        "lost in the middle": [2.0] * 10 + [None] * 30,
    }
    for name, angles in cases.items():
        assert RIGHT not in run(angles) and LEFT not in run(angles), name


def test_jitter_in_warn_zone():
    # раньше тут штатив дёргался почти каждый кадр: скорость считалась по одному кадру
    for seed in range(5):
        for base in (16, 18, 20):
            assert set(run(noisy(base, 300, seed=seed))) == {STOP}, (base, seed)


def test_raised_hand():
    # центр бокса сдвинулся на пару градусов и вернулся
    angles = [18.0] * 30 + [20.0] * 10 + [18.0] * 30
    assert set(run(angles)) == {STOP}


def test_at_edge():
    assert run([30.0] * 30)[-1] == RIGHT
    assert run([-30.0] * 30)[-1] == LEFT


def test_walking_out_turns_before_edge():
    cfg = Config()
    for speed in (10, 20):
        angles = [speed * i / FPS for i in range(150)]
        first = run(angles, cfg).index(RIGHT)
        assert angles[first] < cfg.edge_deg - 2, speed


def test_stops_when_centered():
    angles = [30.0] * 10 + [30 - 3 * i for i in range(11)] + [0.0] * 20
    cmds = run(angles)
    assert RIGHT in cmds
    assert cmds[-1] == STOP


def test_lost_at_edge():
    cfg = Config()
    angles = [30.0] * 10 + [None] * int(FPS * (cfg.lost_hold + 0.5))
    cmds = run(angles, cfg)
    assert cmds[15] == RIGHT
    assert cmds[-1] == STOP
