// ============================================================
// EMU firmware — expression executor with pupil tracking.
// Pupils shift toward LOOK x/y on top of the current expression
// shape; expressions/gestures still come from EXPR/GESTURE/SERVO.
// ============================================================
#include <Wire.h>
#include <Servo.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_W 128
#define SCREEN_H 64

enum EyeState { EYE_NEUTRAL, EYE_HAPPY, EYE_SURPRISED, EYE_BLINK, EYE_CURIOUS,
                EYE_SLEEPY, EYE_CONFUSED, EYE_PRIVACY, EYE_CONCERNED, EYE_ANGRY };

Adafruit_SSD1306 display(SCREEN_W, SCREEN_H, &Wire, -1);

#define CH_HEAD 0
#define CH_ARM_L 1
#define CH_ARM_R 2
#define CH_LEG_L 3
#define CH_LEG_R 4
const int servoPins[5] = {6, 7, 8, 9, 10};
Servo myServo[5];

struct ServoState { int minDeg, maxDeg, homeDeg, current; };
ServoState servos[5] = {
  {60,120,90,90}, {30,150,90,90}, {30,150,90,90}, {75,105,90,90}, {75,105,90,90}
};

void servoWriteDeg(uint8_t ch, int deg) {
  deg = constrain(deg, servos[ch].minDeg, servos[ch].maxDeg);
  servos[ch].current = deg;
  myServo[ch].write(deg);
}
void servoMoveSmooth(uint8_t ch, int toDeg, int steps, int stepDelayMs) {
  int from = servos[ch].current;
  for (int i = 0; i <= steps; i++) { servoWriteDeg(ch, from + (toDeg-from)*i/steps); delay(stepDelayMs); }
}
void allServosHome() { for (int i=0;i<5;i++) servoWriteDeg(i, servos[i].homeDeg); }

void gestureWave() {
  for (int i = 0; i < 2; i++) { servoMoveSmooth(CH_ARM_R, 140, 4, 20); servoMoveSmooth(CH_ARM_R, 60, 5, 20); }
  servoMoveSmooth(CH_ARM_R, 90, 4, 20);
}
void gestureNod() {
  servoMoveSmooth(CH_HEAD, 108, 5, 20); servoMoveSmooth(CH_HEAD, 75, 6, 20); servoMoveSmooth(CH_HEAD, 90, 5, 20);
}
void gestureShuffle() {
  for (int i = 0; i < 3; i++) {
    servoWriteDeg(CH_LEG_L, 100); servoWriteDeg(CH_LEG_R, 80); delay(150);
    servoWriteDeg(CH_LEG_L, 80);  servoWriteDeg(CH_LEG_R, 100); delay(150);
  }
  servoWriteDeg(CH_LEG_L, 90); servoWriteDeg(CH_LEG_R, 90);
}
void gestureGentleAttention() {
  servoMoveSmooth(CH_HEAD, 105, 5, 20); servoMoveSmooth(CH_ARM_L, 75, 4, 20);
}

EyeState currentEye = EYE_NEUTRAL;
int pupilX = 0, pupilY = 0;       // current rendered pupil offset, pixels
int targetPupilX = 0, targetPupilY = 0; // where LOOK wants it to go

// Which expressions get a tracking pupil drawn on top — shapes like BLINK,
// SLEEPY, PRIVACY, ANGRY don't get one, it would look wrong on those.
bool eyeSupportsPupil(EyeState st) {
  return st == EYE_NEUTRAL || st == EYE_HAPPY || st == EYE_SURPRISED ||
         st == EYE_CURIOUS || st == EYE_CONFUSED || st == EYE_CONCERNED;
}

void drawEyes(EyeState st) {
  display.clearDisplay();
  int cx1=40, cx2=88, cy=32;
  switch (st) {
    case EYE_NEUTRAL:   display.fillCircle(cx1,cy,14,SSD1306_WHITE); display.fillCircle(cx2,cy,14,SSD1306_WHITE); break;
    case EYE_HAPPY:      display.fillRoundRect(cx1-14,cy,28,14,6,SSD1306_WHITE); display.fillRoundRect(cx2-14,cy,28,14,6,SSD1306_WHITE); break;
    case EYE_SURPRISED:  display.fillCircle(cx1,cy,18,SSD1306_WHITE); display.fillCircle(cx2,cy,18,SSD1306_WHITE); break;
    case EYE_BLINK:      display.fillRect(cx1-14,cy-2,28,4,SSD1306_WHITE); display.fillRect(cx2-14,cy-2,28,4,SSD1306_WHITE); break;
    case EYE_CURIOUS:    display.fillCircle(cx1-3,cy,14,SSD1306_WHITE); display.fillCircle(cx2+3,cy,14,SSD1306_WHITE); break;
    case EYE_SLEEPY:     display.fillRoundRect(cx1-14,cy+3,28,7,3,SSD1306_WHITE); display.fillRoundRect(cx2-14,cy+3,28,7,3,SSD1306_WHITE); break;
    case EYE_CONFUSED:   display.drawCircle(cx1,cy,14,SSD1306_WHITE); display.fillCircle(cx2,cy,14,SSD1306_WHITE); break;
    case EYE_PRIVACY:    display.drawRect(cx1-14,cy-10,28,20,SSD1306_WHITE); display.drawRect(cx2-14,cy-10,28,20,SSD1306_WHITE); break;
    case EYE_CONCERNED:  display.fillRoundRect(cx1-14,cy-2,28,10,4,SSD1306_WHITE); display.fillRoundRect(cx2-14,cy-2,28,10,4,SSD1306_WHITE); break;
    case EYE_ANGRY:
      display.fillRoundRect(cx1-12, cy-4, 24, 10, 3, SSD1306_WHITE);
      display.fillRoundRect(cx2-12, cy-4, 24, 10, 3, SSD1306_WHITE);
      display.drawLine(cx1-14, cy-8, cx1+8, cy-2, SSD1306_WHITE);
      display.drawLine(cx2+14, cy-8, cx2-8, cy-2, SSD1306_WHITE);
      break;
  }
  if (eyeSupportsPupil(st)) {
    display.fillCircle(cx1 + pupilX, cy + pupilY, 4, SSD1306_BLACK);
    display.fillCircle(cx2 + pupilX, cy + pupilY, 4, SSD1306_BLACK);
  }
  display.display();
}

// Eased blink: closes and reopens over a few frames instead of one
// instant static frame — noticeably smoother.
void blinkOnce() {
  EyeState prev = currentEye;
  for (int i = 0; i < 2; i++) { drawEyes(EYE_BLINK); delay(35); }
  drawEyes(prev);
}

char cmdBuf[48];
uint8_t cmdLen = 0;
unsigned long lastCommandMs = 0;

void handleCommand(char* line) {
  lastCommandMs = millis();
  char* tok = strtok(line, " ");
  if (!tok) return;

  if (!strcmp(tok, "EXPR")) {
    char* name = strtok(NULL, " ");
    if (!name) return;
    if      (!strcmp(name, "HAPPY"))     currentEye = EYE_HAPPY;
    else if (!strcmp(name, "SURPRISED")) currentEye = EYE_SURPRISED;
    else if (!strcmp(name, "CURIOUS"))   currentEye = EYE_CURIOUS;
    else if (!strcmp(name, "SLEEPY"))    currentEye = EYE_SLEEPY;
    else if (!strcmp(name, "ALERT"))     currentEye = EYE_SURPRISED;
    else if (!strcmp(name, "CONFUSED"))  currentEye = EYE_CONFUSED;
    else if (!strcmp(name, "PRIVACY"))   currentEye = EYE_PRIVACY;
    else if (!strcmp(name, "CONCERNED")) currentEye = EYE_CONCERNED;
    else if (!strcmp(name, "ANGRY"))     currentEye = EYE_ANGRY;
    else                                  currentEye = EYE_NEUTRAL;
    drawEyes(currentEye);
  }
  else if (!strcmp(tok, "GESTURE")) {
    char* name = strtok(NULL, " ");
    if (!name) return;
    if      (!strcmp(name, "WAVE"))             gestureWave();
    else if (!strcmp(name, "NOD"))              gestureNod();
    else if (!strcmp(name, "SHUFFLE"))          gestureShuffle();
    else if (!strcmp(name, "GENTLE_ATTENTION")) gestureGentleAttention();
  }
  else if (!strcmp(tok, "SERVO")) {
    char* chStr = strtok(NULL, " ");
    char* degStr = strtok(NULL, " ");
    if (chStr && degStr) {
      int ch = atoi(chStr), deg = atoi(degStr);
      if (ch >= 0 && ch < 5) servoWriteDeg(ch, deg);
    }
  }
  else if (!strcmp(tok, "LOOK")) {
    char* xStr = strtok(NULL, " ");
    char* yStr = strtok(NULL, " ");
    if (xStr && yStr) {
      // incoming range -100..100 -> pixel offset -5..5 (keeps pupil inside eye shape)
      targetPupilX = constrain(atoi(xStr), -100, 100) * 5 / 100;
      targetPupilY = constrain(atoi(yStr), -100, 100) * 5 / 100;
    }
  }
}

void pollSerial() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') { cmdBuf[cmdLen] = '\0'; handleCommand(cmdBuf); cmdLen = 0; }
    else if (cmdLen < sizeof(cmdBuf)-1) cmdBuf[cmdLen++] = c;
  }
}

unsigned long lastBlink = 0;
unsigned long lastPupilUpdate = 0;

void setup() {
  Serial.begin(9600);
  Wire.begin();
  for (int i = 0; i < 5; i++) myServo[i].attach(servoPins[i]);
  bool oledOK = display.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  Serial.println(oledOK ? "OLED OK" : "OLED FAULT");
  allServosHome();
  drawEyes(EYE_NEUTRAL);
  lastCommandMs = millis();
  Serial.println("EMU READY");
}

void loop() {
  pollSerial();

  // Smooth pupil easing toward target, independent of command rate —
  // this is what makes the tracking look fluid instead of snapping.
  if (millis() - lastPupilUpdate > 40) {
    lastPupilUpdate = millis();
    bool moved = false;
    if (pupilX != targetPupilX) { pupilX += (targetPupilX > pupilX) ? 1 : -1; moved = true; }
    if (pupilY != targetPupilY) { pupilY += (targetPupilY > pupilY) ? 1 : -1; moved = true; }
    if (moved && eyeSupportsPupil(currentEye)) drawEyes(currentEye);
  }

  if (currentEye == EYE_NEUTRAL && millis() - lastBlink > 4000) {
    blinkOnce(); lastBlink = millis();
  }
}
