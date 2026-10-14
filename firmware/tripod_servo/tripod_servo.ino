#include <Servo.h>

// MIN_US/MAX_US - крайние положения головки (края доски), подбираются на месте.
// Заодно они не дают четырёхзвеннику дойти до мёртвой точки.
const int SERVO_PIN = 9;
const float MIN_US = 1100;   // камера смотрит вправо
const float MAX_US = 2400;   // камера смотрит влево
const float CENTER_US = 1750;
const float MAX_SPEED = 400;   // мкс/с
const float MAX_ACCEL = 1500;  // мкс/с^2
const unsigned long WATCHDOG_MS = 300;
const unsigned long REPORT_MS = 50;

Servo servo;
float pos = CENTER_US;
float vel = 0;
float target = CENTER_US;
unsigned long lastCmd = 0;
unsigned long lastTick = 0;
unsigned long lastReport = 0;
bool limitHit = false;

char buf[16];
byte len = 0;
bool overflow = false;

void setup() {
  Serial.begin(115200);
  // если сначала attach, серва рванёт в центр на полной скорости
  servo.writeMicroseconds(CENTER_US);
  servo.attach(SERVO_PIN);
  lastTick = millis();
  Serial.println("READY");
}

void brake() {
  target = constrain(pos + vel * fabs(vel) / (2 * MAX_ACCEL), MIN_US, MAX_US);
}

void handleLine() {
  if (len == 1 && buf[0] == 'S') {
    limitHit = false;
    brake();
    lastCmd = millis();
    return;
  }
  if (len < 3 || buf[0] != 'T' || buf[1] != ' ')
    return;
  long v = atol(buf + 2);
  // atol на мусоре вернёт 0, такое не должно уводить серву в лимит
  if (v < 500 || v > 2500)
    return;
  limitHit = v < MIN_US || v > MAX_US;
  target = constrain(v, MIN_US, MAX_US);
  lastCmd = millis();
}

void readSerial() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\r')
      continue;
    if (c == '\n') {
      buf[len] = 0;
      if (!overflow)
        handleLine();
      len = 0;
      overflow = false;
    } else if (len < sizeof(buf) - 1) {
      buf[len++] = c;
    } else {
      overflow = true;
    }
  }
}

void move(float dt) {
  float err = target - pos;
  // максимальная скорость, с которой ещё успеваем затормозить к уставке
  float vmax = min(sqrt(2 * MAX_ACCEL * fabs(err)), MAX_SPEED);
  float want = err > 0 ? vmax : -vmax;
  float dv = constrain(want - vel, -MAX_ACCEL * dt, MAX_ACCEL * dt);
  vel += dv;
  pos += vel * dt;
  if (fabs(err) < 1 && fabs(vel) < 10) {
    pos = target;
    vel = 0;
  }
  pos = constrain(pos, MIN_US, MAX_US);
}

void loop() {
  readSerial();

  unsigned long now = millis();
  if (now - lastCmd > WATCHDOG_MS)
    brake();

  float dt = (now - lastTick) / 1000.0;
  // серва всё равно принимает импульс раз в 20 мс
  if (dt >= 0.02) {
    lastTick = now;
    move(dt);
    servo.writeMicroseconds((int)pos);
  }

  if (now - lastReport >= REPORT_MS) {
    lastReport = now;
    Serial.print("A ");
    Serial.println((int)pos);
    if (limitHit)
      Serial.println("L");
  }
}
