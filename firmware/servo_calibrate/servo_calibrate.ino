#include <Servo.h>

// Подбор крайних положений головки через Serial Monitor (115200, "Новая строка").
//   +       на 10 мкс в одну сторону (+++++ = на 50)
//   -       на 10 мкс в другую
//   1600    поехать в 1600 мкс
// Серва едет плавно, чтобы можно было успеть выдернуть питание.

const int SERVO_PIN = 9;
const int SAFE_MIN = 500;
const int SAFE_MAX = 2500;
// шаг за раз должен быть больше мёртвой зоны сервы (~5 мкс), иначе она дёргается
const float SPEED = 400;  // мкс/с

Servo servo;
float pos = 1500;
int target = 1500;
unsigned long lastTick = 0;
bool reported = true;

char buf[12];
byte len = 0;

void setup() {
  Serial.begin(115200);
  servo.writeMicroseconds(1500);
  servo.attach(SERVO_PIN);
  Serial.println("calibrate: + / - / number in us");
  Serial.println("pos 1500");
}

void handleLine() {
  buf[len] = 0;
  if (len > 0 && buf[0] >= '0' && buf[0] <= '9') {
    target = atoi(buf);
  } else {
    for (byte i = 0; i < len; i++) {
      if (buf[i] == '+') target += 10;
      if (buf[i] == '-') target -= 10;
    }
  }
  target = constrain(target, SAFE_MIN, SAFE_MAX);
  reported = false;
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (len > 0)
        handleLine();
      len = 0;
    } else if (len < sizeof(buf) - 1) {
      buf[len++] = c;
    }
  }

  unsigned long now = millis();
  if (now - lastTick >= 40) {
    float step = SPEED * (now - lastTick) / 1000.0;
    lastTick = now;
    if (fabs(target - pos) <= step)
      pos = target;
    else
      pos += target > pos ? step : -step;
    servo.writeMicroseconds((int)pos);
  }

  if (!reported && pos == target) {
    Serial.print("pos ");
    Serial.println(target);
    reported = true;
  }
}
