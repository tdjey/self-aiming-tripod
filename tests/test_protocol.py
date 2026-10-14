import sys
import types

from tripod.config import Config
from tripod.controller import RIGHT
from tripod.link import SerialLink, format_target, parse_line


def test_format():
    assert format_target(1500) == "T 1500\n"
    assert format_target(1499.6) == "T 1500\n"


def test_parse():
    assert parse_line("READY\r\n") == ("READY", None)
    assert parse_line("A 1234") == ("A", 1234.0)
    assert parse_line("L") == ("L", None)


def test_parse_garbage():
    for line in ("", "A", "A abc", "X 10", "A 1 2", "READY 1"):
        assert parse_line(line) is None


class FakeSerial:
    def __init__(self, *args, **kwargs):
        self.incoming = [b"READY\nA 1750\n"]
        self.sent = []

    def read(self, n):
        return self.incoming.pop(0) if self.incoming else b""

    def write(self, data):
        self.sent.append(data)

    def close(self):
        pass


def test_right_turns_camera_right(monkeypatch):
    monkeypatch.setitem(sys.modules, "serial", types.SimpleNamespace(Serial=FakeSerial))
    link = SerialLink("fake", Config())
    link.send(RIGHT, 0.0)
    link.send(RIGHT, 0.1)
    assert link.target < 1750
