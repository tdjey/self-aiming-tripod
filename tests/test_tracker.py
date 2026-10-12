from tripod.config import Config
from tripod.tracker import Tracker

H = 720
LECTURER = [600, 100, 700, 600]


def shifted(box, dx):
    return [box[0] + dx, box[1], box[2] + dx, box[3]]


def test_ignores_audience():
    tr = Tracker(Config())
    head = [100, 550, 300, 720]
    assert tr.update([head, LECTURER], H) == LECTURER
    assert tr.new_target


def test_follows_lecturer_with_neighbour():
    tr = Tracker(Config())
    other = [900, 150, 980, 560]
    tr.update([LECTURER, other], H)
    for dx in range(0, 200, 10):
        assert tr.update([other, shifted(LECTURER, dx)], H) == shifted(LECTURER, dx)
    assert not tr.new_target


def test_no_jump_to_short_neighbour():
    tr = Tracker(Config())
    tr.update([LECTURER], H)
    # лектора не нашли, рядом кто-то сидящий в первом ряду
    sitting = [720, 330, 820, 600]
    assert tr.update([sitting], H) is None


def test_reacquire_after_long_loss():
    cfg = Config()
    tr = Tracker(cfg)
    tr.update([LECTURER], H)
    for _ in range(cfg.max_missed + 1):
        tr.update([], H)
    far = [100, 120, 190, 610]
    assert tr.update([far], H) == far
    assert tr.new_target
