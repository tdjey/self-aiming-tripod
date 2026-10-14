import time

from tripod.controller import STOP

# Mac -> Arduino:  "T 1500" уставка в мкс, "S" плавно затормозить
# Arduino -> Mac:  "READY" после старта, "A 1500" позиция, "L" уставка упёрлась в лимит


def format_target(us):
    return "T %d\n" % int(round(us))


def parse_line(line):
    parts = line.strip().split()
    if len(parts) == 1 and parts[0] in ("READY", "L"):
        return parts[0], None
    if len(parts) == 2 and parts[0] == "A":
        try:
            return "A", float(parts[1])
        except ValueError:
            return None
    return None


class ManualLink:
    at_limit = False

    def send(self, cmd, t):
        pass

    def poll(self):
        pass

    def close(self):
        pass


class SerialLink:
    def __init__(self, port, cfg):
        import serial

        self.cfg = cfg
        self.ser = serial.Serial(port, 115200, timeout=0)
        self.buf = b""
        self.pos = None
        self.at_limit = False
        self.target = None
        self.last_t = None

        deadline = time.monotonic() + 4
        while self.pos is None and time.monotonic() < deadline:
            self.poll()
            time.sleep(0.05)
        if self.pos is None:
            raise RuntimeError("no answer from arduino on %s" % port)

    def send(self, cmd, t):
        dt = 0.0 if self.last_t is None else min(t - self.last_t, 0.1)
        self.last_t = t
        if cmd == STOP or self.target is None or self.at_limit:
            self.target = self.pos
        if cmd == STOP:
            self.ser.write(b"S\n")
            return
        self.target += cmd * self.cfg.servo_dir * self.cfg.servo_speed * dt
        self.ser.write(format_target(self.target).encode())

    def poll(self):
        self.buf += self.ser.read(256)
        while b"\n" in self.buf:
            line, self.buf = self.buf.split(b"\n", 1)
            msg = parse_line(line.decode(errors="ignore"))
            if msg is None:
                continue
            kind, value = msg
            if kind == "A":
                self.pos = value
                self.at_limit = False
            elif kind == "L":
                self.at_limit = True
        if len(self.buf) > 1024:
            self.buf = b""

    def close(self):
        self.ser.close()
