#include <Wire.h>
#include <U8g2lib.h>
#include <Servo.h>
#include <string.h>
#include <stdlib.h>

// ============================================================
// EMU v3.0 — CUTE / EXPRESSIVE DESK COMPANION FACE ENGINE
// Target: Arduino Uno + SSD1306 128x64 I2C OLED + 1x SG90
//
// OLED: 0x3C, SDA=A4, SCL=A5
// Servo: D6
//
// Serial commands:
//   EXPR HAPPY
//   EXPR SAD
//   EXPR ANGRY
//   EXPR SURPRISED
//   EXPR ANXIOUS
//   EXPR CONFUSED
//   EXPR CURIOUS
//   EXPR SLEEPY
//   EXPR TIRED
//   EXPR ALERT
//   EXPR CONCERNED
//   EXPR LISTENING
//   EXPR PROCESSING
//   EXPR EXCITED
//   EXPR EMBARRASSED
//   EXPR PRIVACY
//   EXPR TALKING
//   EXPR NEUTRAL
//
//   MOUTH TALK
//   MOUTH STOP
//   LOOK -100 20
//   SERVO 90
//   ANIM WIGGLE
//   ANIM NOD
//   GESTURE WAVE|NOD|SHUFFLE|GENTLE_ATTENTION|ACKNOWLEDGE
//   ANIM HEART
//   ANIM SPARKLE
//   ANIM SURPRISE
//   ANIM SLEEP
//   ANIM WAKE
// ============================================================

U8G2_SSD1306_128X64_NONAME_2_HW_I2C u8g2(U8G2_R0, U8X8_PIN_NONE);
Servo headServo;

#define SERVO_PIN 6
#define SERVO_CENTER 90
#define SERVO_MIN 55
#define SERVO_MAX 125

enum Expression {
  NEUTRAL, HAPPY, SAD, ANGRY, SURPRISED, ANXIOUS, CONFUSED,
  CURIOUS, SLEEPY, TIRED, ALERT, CONCERNED, LISTENING,
  PROCESSING, EXCITED, EMBARRASSED, PRIVACY, TALKING
};

Expression expression = NEUTRAL;

// ---------------------------
// Timing
// ---------------------------
const uint16_t FRAME_TIME = 50;       // 20 FPS, stable on Uno
const uint16_t BLINK_MIN = 2400;
const uint16_t BLINK_MAX = 6500;

unsigned long lastFrame = 0;
unsigned long lastBlink = 0;
unsigned long blinkStart = 0;
unsigned long nextBlink = 3400;
unsigned long lastWander = 0;
unsigned long nextWander = 2200;
unsigned long lastIdleMotion = 0;
unsigned long effectUntil = 0;

bool blinking = false;
bool talking = false;
bool servoEnabled = true;

uint8_t blinkPhase = 0;                // 0=open, 1=closing, 2=opening
uint8_t blinkOpen = 255;               // 255=open, 0=closed
bool doubleBlinkPending = false;

// ---------------------------
// Integer pupil animation
// ---------------------------
int8_t pupilX = 0;
int8_t pupilY = 0;
int8_t targetPupilX = 0;
int8_t targetPupilY = 0;

// ---------------------------
// Servo
// ---------------------------
int8_t headAngle = SERVO_CENTER;
int8_t targetHeadAngle = SERVO_CENTER;

// ---------------------------
// Idle/effect state
// ---------------------------
enum Effect {
  EFFECT_NONE,
  EFFECT_WIGGLE,
  EFFECT_NOD,
  EFFECT_HEART,
  EFFECT_SPARKLE,
  EFFECT_SURPRISE,
  EFFECT_WAKE
};

Effect effect = EFFECT_NONE;
unsigned long effectStart = 0;

// ---------------------------
// Serial
// ---------------------------
char commandBuffer[40];
uint8_t commandLength = 0;

// ============================================================
// Small helpers
// ============================================================

int clampInt(int v, int lo, int hi) {
  if (v < lo) return lo;
  if (v > hi) return hi;
  return v;
}

int approach(int current, int target, int amount) {
  if (current < target) {
    current += amount;
    if (current > target) current = target;
  } else if (current > target) {
    current -= amount;
    if (current < target) current = target;
  }
  return current;
}

// Integer easing. 0..255 -> smooth-ish 0..255.
uint8_t easeOut(uint8_t x) {
  uint16_t inv = 255 - x;
  uint16_t y = 255 - ((uint32_t)inv * inv / 255);
  return (uint8_t)y;
}

// ============================================================
// Organic eye geometry
//
// Instead of sqrt()/floating point ellipses, each eye is built
// from integer scanlines. This is deterministic and SRAM-light.
// ============================================================

// Half widths for a soft almond eye, 17 scanlines.
// y=-8..+8
const uint8_t EYE_ALMOND[17] PROGMEM = {
  2, 6, 9, 12, 14, 15, 16, 17, 17,
  17,
  17, 16, 15, 14, 12, 9, 6
};

// Rounder/wider eye for surprise/alert.
const uint8_t EYE_ROUND[17] PROGMEM = {
  7, 10, 13, 15, 16, 17, 18, 18, 18,
  18,
  18, 18, 17, 16, 15, 13, 10
};

// Sleepy compressed eye.
const uint8_t EYE_SLEEPY[9] PROGMEM = {
  9, 14, 16, 17, 17, 17, 16, 14, 9
};

void drawEyeScanlines(int cx, int cy, int scaleY, const uint8_t *shape) {
  // scaleY: 8 means native 17-line eye.
  // For this renderer we keep the scanline height native and
  // deform it vertically by skipping/duplicating edge lines.
  for (int i = -8; i <= 8; i++) {
    int idx = i + 8;
    uint8_t half = pgm_read_byte(&shape[idx]);
    int y = cy + i;

    if (half > 0) {
      u8g2.drawHLine(cx - half, y, half * 2 + 1);
    }
  }
}

// ============================================================
// Eye layers
// ============================================================

void drawUpperLid(int cx, int cy, int halfW, int lidY, int slope, bool heavy) {
  // Curved-ish upper lid made from connected integer segments.
  int leftX = cx - halfW;
  int rightX = cx + halfW;

  if (heavy) {
    u8g2.drawLine(leftX, lidY + 2, cx - 8, lidY - 1);
    u8g2.drawLine(cx - 8, lidY - 1, cx, lidY - 2);
    u8g2.drawLine(cx, lidY - 2, cx + 8, lidY - 1);
    u8g2.drawLine(cx + 8, lidY - 1, rightX, lidY + 2);
  } else {
    u8g2.drawLine(leftX, lidY + slope, cx - 8, lidY);
    u8g2.drawLine(cx - 8, lidY, cx, lidY - 1);
    u8g2.drawLine(cx, lidY - 1, cx + 8, lidY);
    u8g2.drawLine(cx + 8, lidY, rightX, lidY + slope);
  }
}

void drawLowerLid(int cx, int cy, int halfW, int y, bool smileCurve) {
  int leftX = cx - halfW;
  int rightX = cx + halfW;

  if (smileCurve) {
    u8g2.drawLine(leftX, y - 1, cx - 9, y + 2);
    u8g2.drawLine(cx - 9, y + 2, cx, y + 3);
    u8g2.drawLine(cx, y + 3, cx + 9, y + 2);
    u8g2.drawLine(cx + 9, y + 2, rightX, y - 1);
  } else {
    u8g2.drawLine(leftX, y, cx - 8, y + 1);
    u8g2.drawLine(cx - 8, y + 1, cx, y + 1);
    u8g2.drawLine(cx, y + 1, cx + 8, y + 1);
    u8g2.drawLine(cx + 8, y + 1, rightX, y);
  }
}

void drawPupil(int px, int py, uint8_t radius, bool sparkle) {
  u8g2.setDrawColor(0);
  u8g2.drawDisc(px, py, radius);

  u8g2.setDrawColor(1);

  // Main catchlight.
  if (radius >= 4) {
    u8g2.drawDisc(px - 2, py - 2, 1);
  }

  // Tiny secondary glint makes the eyes feel less like buttons.
  if (sparkle && radius >= 5) {
    u8g2.drawPixel(px + 2, py + 2);
  }
}

void drawOrganicEye(
  int cx,
  int cy,
  int pupilDx,
  int pupilDy,
  uint8_t openness,
  bool happyEye,
  bool angryEye,
  bool sadEye,
  bool roundEye,
  bool sparkle
) {
  // Openness 0..255.
  // We render the white eye first, then black lids cover it.
  const uint8_t *shape = roundEye ? EYE_ROUND : EYE_ALMOND;

  u8g2.setDrawColor(1);

  for (int i = -8; i <= 8; i++) {
    // Compress top/bottom toward the center as the eye closes.
    int scaled = (i * openness) / 255;
    int y = cy + scaled;
    uint8_t half = pgm_read_byte(&shape[i + 8]);

    // Slight expression deformation.
    if (happyEye && abs(i) > 5) half -= (half > 2 ? 2 : 0);
    if (sadEye && i < -2) half -= (half > 3 ? 2 : 0);

    if (half > 0) {
      u8g2.drawHLine(cx - half, y, half * 2 + 1);
    }
  }

  // At a full close, make the eyelid a clean expressive line.
  if (openness < 35) {
    u8g2.setDrawColor(1);
    if (happyEye) {
      drawLowerLid(cx, cy, 15, cy, true);
    } else {
      u8g2.drawLine(cx - 15, cy, cx - 6, cy - 1);
      u8g2.drawLine(cx - 6, cy - 1, cx, cy);
      u8g2.drawLine(cx, cy, cx + 6, cy - 1);
      u8g2.drawLine(cx + 6, cy - 1, cx + 15, cy);
    }
    return;
  }

  // Pupil size is emotion-sensitive.
  uint8_t radius = 4;
  if (expression == SURPRISED) radius = 3;
  if (expression == ALERT) radius = 4;
  if (expression == EXCITED) radius = 4;
  if (expression == SLEEPY) radius = 3;

  // Keep pupil within eye.
  int px = cx + pupilDx;
  int py = cy + pupilDy;

  drawPupil(px, py, radius, sparkle);

  // Upper/lower lid design.
  if (happyEye) {
    // Happy eyes are crescent-like, with the upper edge still
    // readable as an eye rather than a plain line.
    u8g2.setDrawColor(0);
    drawUpperLid(cx, cy, 17, cy - 5, 1, true);
    u8g2.setDrawColor(1);
  }

  if (angryEye) {
    u8g2.setDrawColor(0);
    // Diagonal inner brow/lid pressure.
    u8g2.drawLine(cx - 17, cy - 5, cx - 4, cy - 2);
    u8g2.drawLine(cx - 4, cy - 2, cx + 17, cy - 1);
    u8g2.setDrawColor(1);
  }

  if (sadEye) {
    u8g2.setDrawColor(0);
    drawLowerLid(cx, cy, 16, cy + 6, false);
    u8g2.setDrawColor(1);
  }
}

// ============================================================
// Brows
// ============================================================

void drawBrow(int x1, int y1, int x2, int y2, bool thick) {
  u8g2.drawLine(x1, y1, x2, y2);
  if (thick) u8g2.drawLine(x1, y1 + 1, x2, y2 + 1);
}

void drawBrows() {
  switch (expression) {
    case ANGRY:
      drawBrow(22, 14, 52, 21, true);
      drawBrow(106, 14, 76, 21, true);
      break;

    case SAD:
    case CONCERNED:
      drawBrow(22, 20, 50, 13, false);
      drawBrow(106, 20, 78, 13, false);
      break;

    case SURPRISED:
      drawBrow(22, 9, 52, 7, false);
      drawBrow(106, 9, 76, 7, false);
      break;

    case CURIOUS:
      drawBrow(22, 12, 52, 7, true);
      drawBrow(77, 15, 106, 15, false);
      break;

    case CONFUSED:
      drawBrow(22, 10, 51, 15, false);
      drawBrow(77, 15, 106, 10, false);
      break;

    case ALERT:
      drawBrow(22, 8, 52, 8, true);
      drawBrow(76, 8, 106, 8, true);
      break;

    case EMBARRASSED:
      drawBrow(25, 17, 50, 15, false);
      drawBrow(103, 17, 78, 15, false);
      break;

    default:
      break;
  }
}

// ============================================================
// Cheeks / blush
// ============================================================

void drawCheeks() {
  if (expression != HAPPY &&
      expression != EXCITED &&
      expression != EMBARRASSED) return;

  // Small pixel blush marks, deliberately subtle on 128x64.
  u8g2.drawHLine(15, 45, 7);
  u8g2.drawHLine(17, 47, 5);

  u8g2.drawHLine(106, 45, 7);
  u8g2.drawHLine(108, 47, 5);
}

// ============================================================
// Mouth engine
// ============================================================

void drawSmile() {
  u8g2.drawLine(53, 52, 58, 56);
  u8g2.drawLine(58, 56, 64, 58);
  u8g2.drawLine(64, 58, 70, 56);
  u8g2.drawLine(70, 56, 75, 52);
}

void drawFrown() {
  u8g2.drawLine(54, 57, 59, 54);
  u8g2.drawLine(59, 54, 64, 53);
  u8g2.drawLine(64, 53, 69, 54);
  u8g2.drawLine(69, 54, 74, 57);
}

void drawMouth() {
  const int cx = 64;
  const int cy = 54;

  if (talking) {
    uint8_t phase = (millis() / 85) % 6;

    if (phase == 0) {
      u8g2.drawRBox(58, 52, 12, 4, 2);
    } else if (phase == 1) {
      u8g2.drawRBox(55, 50, 18, 8, 3);
    } else if (phase == 2) {
      u8g2.drawRBox(58, 49, 12, 11, 4);
    } else if (phase == 3) {
      u8g2.drawRBox(54, 52, 20, 6, 3);
    } else if (phase == 4) {
      u8g2.drawRBox(57, 50, 14, 8, 3);
    } else {
      u8g2.drawRBox(59, 52, 10, 4, 2);
    }
    return;
  }

  switch (expression) {
    case HAPPY:
    case EXCITED:
      drawSmile();
      break;

    case SAD:
    case CONCERNED:
      drawFrown();
      break;

    case SURPRISED:
      u8g2.drawCircle(cx, cy, 5);
      break;

    case ANGRY:
      u8g2.drawRBox(56, 52, 16, 4, 2);
      break;

    case ANXIOUS:
      u8g2.drawLine(54, 53, 74, 53);
      u8g2.drawLine(57, 57, 71, 57);
      break;

    case CONFUSED:
      u8g2.drawLine(57, 56, 62, 52);
      u8g2.drawLine(62, 52, 68, 56);
      u8g2.drawLine(68, 56, 72, 53);
      break;

    case SLEEPY:
      u8g2.drawLine(58, 55, 70, 55);
      break;

    case TIRED:
      u8g2.drawLine(56, 54, 72, 54);
      break;

    case LISTENING:
      u8g2.drawLine(55, 54, 73, 54);
      break;

    case PROCESSING:
      u8g2.drawDisc(64, 54, 2);
      break;

    case PRIVACY:
      u8g2.drawLine(54, 54, 74, 54);
      break;

    case EMBARRASSED:
      u8g2.drawLine(57, 54, 71, 54);
      break;

    default:
      u8g2.drawLine(57, 54, 71, 54);
      break;
  }
}

// ============================================================
// Special effects
// ============================================================

void drawHeart(int cx, int cy) {
  u8g2.drawDisc(cx - 3, cy - 1, 3);
  u8g2.drawDisc(cx + 3, cy - 1, 3);
  u8g2.drawLine(cx - 6, cy, cx, cy + 7);
  u8g2.drawLine(cx + 6, cy, cx, cy + 7);
}

void drawSparkle(int cx, int cy, uint8_t size) {
  u8g2.drawVLine(cx, cy - size, size * 2 + 1);
  u8g2.drawHLine(cx - size, cy, size * 2 + 1);
  if (size >= 2) {
    u8g2.drawPixel(cx - 1, cy - 1);
    u8g2.drawPixel(cx + 1, cy + 1);
  }
}

void drawEffect() {
  if (effect == EFFECT_NONE) return;

  unsigned long age = millis() - effectStart;

  if (effect == EFFECT_HEART) {
    if (age < 1000) {
      drawHeart(64, 20);
      drawHeart(64, 39);
    }
  } else if (effect == EFFECT_SPARKLE) {
    if (age < 900) {
      drawSparkle(17, 17, 3);
      drawSparkle(111, 16, 2);
      drawSparkle(13, 34, 1);
      drawSparkle(115, 36, 1);
    }
  } else if (effect == EFFECT_SURPRISE) {
    if (age < 500) {
      drawSparkle(18, 18, 2);
      drawSparkle(110, 18, 2);
    }
  } else if (effect == EFFECT_WAKE) {
    if (age < 800) {
      drawSparkle(64, 8, 2);
    }
  }
}

// ============================================================
// Face geometry
// ============================================================

void getFaceParams(
  uint8_t &open,
  bool &happyEye,
  bool &angryEye,
  bool &sadEye,
  bool &roundEye
) {
  open = 255;
  happyEye = false;
  angryEye = false;
  sadEye = false;
  roundEye = false;

  switch (expression) {
    case HAPPY:
      open = 175;
      happyEye = true;
      break;

    case SAD:
      open = 190;
      sadEye = true;
      break;

    case ANGRY:
      open = 180;
      angryEye = true;
      break;

    case SURPRISED:
      open = 255;
      roundEye = true;
      break;

    case ANXIOUS:
      open = 240;
      break;

    case CONFUSED:
      open = 220;
      break;

    case CURIOUS:
      open = 245;
      break;

    case SLEEPY:
      open = 95;
      break;

    case TIRED:
      open = 130;
      break;

    case ALERT:
      open = 255;
      roundEye = true;
      break;

    case CONCERNED:
      open = 185;
      sadEye = true;
      break;

    case LISTENING:
      open = 215;
      break;

    case PROCESSING:
      open = 210;
      break;

    case EXCITED:
      open = 255;
      roundEye = true;
      break;

    case EMBARRASSED:
      open = 145;
      happyEye = true;
      break;

    case TALKING:
      open = 225;
      break;

    default:
      break;
  }

  if (blinking) {
    open = (uint8_t)((uint16_t)open * blinkOpen / 255);
  }
}

void drawPrivacyFace() {
  // Privacy is deliberately distinct from a normal expression.
  u8g2.drawFrame(24, 17, 33, 24);
  u8g2.drawFrame(71, 17, 33, 24);

  // Pixelated "camera off" feeling.
  u8g2.drawLine(29, 22, 52, 35);
  u8g2.drawLine(52, 22, 29, 35);
  u8g2.drawLine(76, 22, 99, 35);
  u8g2.drawLine(99, 22, 76, 35);

  u8g2.drawLine(55, 54, 73, 54);
}

void drawFace() {
  uint8_t open;
  bool happyEye, angryEye, sadEye, roundEye;
  getFaceParams(open, happyEye, angryEye, sadEye, roundEye);

  if (expression == PRIVACY) {
    drawPrivacyFace();
    drawEffect();
    return;
  }

  int leftY = 29;
  int rightY = 29;

  // A little asymmetry is much more alive than perfect symmetry.
  if (expression == CURIOUS) {
    leftY = 28;
    rightY = 30;
  } else if (expression == CONFUSED) {
    leftY = 30;
    rightY = 28;
  } else if (expression == HAPPY || expression == EMBARRASSED) {
    leftY = 28;
    rightY = 28;
  } else if (expression == SLEEPY) {
    leftY = 31;
    rightY = 31;
  }

  // Subtle idle "breathing" of the face.
  int micro = 0;
  if (!talking && expression != PROCESSING) {
    micro = ((millis() / 700) % 2);
  }

  int leftPX = pupilX;
  int rightPX = pupilX;
  int leftPY = pupilY + micro;
  int rightPY = pupilY + micro;

  // Curious/confused asymmetry.
  if (expression == CURIOUS) rightPX += 1;
  if (expression == CONFUSED) leftPX -= 1;

  bool sparkle = (expression == HAPPY ||
                  expression == EXCITED ||
                  expression == CURIOUS ||
                  expression == ALERT);

  drawOrganicEye(
    40, leftY,
    leftPX, leftPY,
    open,
    happyEye, angryEye, sadEye, roundEye, sparkle
  );

  drawOrganicEye(
    88, rightY,
    rightPX, rightPY,
    open,
    happyEye, angryEye, sadEye, roundEye, sparkle
  );

  drawBrows();
  drawCheeks();
  drawMouth();
  drawEffect();
}

// ============================================================
// Blink engine
// ============================================================

void startBlink(bool doubleBlink) {
  blinking = true;
  blinkStart = millis();
  blinkPhase = 1;
  blinkOpen = 255;
  doubleBlinkPending = doubleBlink;
}

void updateBlink() {
  unsigned long now = millis();

  if (!blinking) {
    if (now - lastBlink >= nextBlink) {
      bool doDouble = (random(0, 10) == 0);
      startBlink(doDouble);
      lastBlink = now;
      nextBlink = random(BLINK_MIN, BLINK_MAX);
    }
    return;
  }

  unsigned long elapsed = now - blinkStart;

  if (elapsed < 70) {
    blinkPhase = 1;
    blinkOpen = 255 - (uint8_t)map(elapsed, 0, 70, 0, 255);
  } else if (elapsed < 145) {
    blinkPhase = 2;
    blinkOpen = (uint8_t)map(elapsed, 70, 145, 0, 255);
  } else {
    blinking = false;
    blinkOpen = 255;

    if (doubleBlinkPending) {
      doubleBlinkPending = false;
      blinkStart = now + 80;
      // Start the second blink on the next update.
      blinking = true;
    }
  }
}

// ============================================================
// Pupil / attention engine
// ============================================================

void setLookTarget(int x, int y) {
  targetPupilX = (int8_t)map(clampInt(x, -100, 100), -100, 100, -6, 6);
  targetPupilY = (int8_t)map(clampInt(y, -100, 100), -100, 100, -4, 4);
}

void updatePupils() {
  pupilX = (int8_t)approach(pupilX, targetPupilX, 1);
  pupilY = (int8_t)approach(pupilY, targetPupilY, 1);

  unsigned long now = millis();

  if (!talking && expression != PROCESSING) {
    if (now - lastWander >= nextWander) {
      lastWander = now;
      nextWander = random(1700, 4200);

      int choice = random(0, 10);

      if (choice < 6) {
        setLookTarget(random(-45, 46), random(-30, 31));
      } else if (choice < 8) {
        setLookTarget(random(-85, 86), random(-20, 21));
      } else {
        // Briefly look toward center again.
        setLookTarget(0, random(-10, 11));
      }
    }
  }

  // Processing: tiny searching motion.
  if (expression == PROCESSING && now - lastWander >= 650) {
    lastWander = now;
    setLookTarget(random(-45, 46), random(-20, 21));
  }
}

// ============================================================
// Head micro-motion
// ============================================================

void updateHead() {
  if (!servoEnabled) return;

  unsigned long now = millis();

  // Slow follow of requested target.
  if (headAngle < targetHeadAngle) headAngle++;
  else if (headAngle > targetHeadAngle) headAngle--;

  headAngle = clampInt(headAngle, SERVO_MIN, SERVO_MAX);
  headServo.write(headAngle);

  // Very subtle idle motion around center.
  if (now - lastIdleMotion > 4200 &&
      expression != PROCESSING &&
      expression != PRIVACY) {
    lastIdleMotion = now;

    int8_t offset = random(-4, 5);
    targetHeadAngle = clampInt(SERVO_CENTER + offset, SERVO_MIN, SERVO_MAX);
  }

  if (effect == EFFECT_WIGGLE) {
    unsigned long age = now - effectStart;

    if (age < 160) targetHeadAngle = 82;
    else if (age < 320) targetHeadAngle = 98;
    else if (age < 480) targetHeadAngle = 84;
    else if (age < 640) targetHeadAngle = 96;
    else {
      targetHeadAngle = SERVO_CENTER;
      effect = EFFECT_NONE;
    }
  } else if (effect == EFFECT_NOD) {
    unsigned long age = now - effectStart;

    if (age < 150) targetHeadAngle = 84;
    else if (age < 300) targetHeadAngle = 96;
    else if (age < 450) targetHeadAngle = 86;
    else if (age < 600) targetHeadAngle = 94;
    else {
      targetHeadAngle = SERVO_CENTER;
      effect = EFFECT_NONE;
    }
  }
}

// ============================================================
// Effects
// ============================================================

void triggerEffect(Effect e, uint16_t duration) {
  effect = e;
  effectStart = millis();
  effectUntil = effectStart + duration;
}

void updateEffects() {
  if (effect != EFFECT_NONE && millis() > effectUntil) {
    effect = EFFECT_NONE;
  }
}

// ============================================================
// Serial command parser
// ============================================================

void setExpressionByName(const char *name) {
  if (!strcmp(name, "NEUTRAL")) expression = NEUTRAL;
  else if (!strcmp(name, "HAPPY")) expression = HAPPY;
  else if (!strcmp(name, "SAD")) expression = SAD;
  else if (!strcmp(name, "ANGRY")) expression = ANGRY;
  else if (!strcmp(name, "SURPRISED")) expression = SURPRISED;
  else if (!strcmp(name, "ANXIOUS")) expression = ANXIOUS;
  else if (!strcmp(name, "CONFUSED")) expression = CONFUSED;
  else if (!strcmp(name, "CURIOUS")) expression = CURIOUS;
  else if (!strcmp(name, "SLEEPY")) expression = SLEEPY;
  else if (!strcmp(name, "TIRED")) expression = TIRED;
  else if (!strcmp(name, "ALERT")) expression = ALERT;
  else if (!strcmp(name, "CONCERNED")) expression = CONCERNED;
  else if (!strcmp(name, "LISTENING")) expression = LISTENING;
  else if (!strcmp(name, "PROCESSING")) expression = PROCESSING;
  else if (!strcmp(name, "EXCITED")) expression = EXCITED;
  else if (!strcmp(name, "EMBARRASSED")) expression = EMBARRASSED;
  else if (!strcmp(name, "PRIVACY")) expression = PRIVACY;
  else if (!strcmp(name, "TALKING")) expression = TALKING;
}

void processCommand(char *cmd) {
  char *token = strtok(cmd, " ");
  if (!token) return;

  if (!strcmp(token, "EXPR")) {
    char *name = strtok(NULL, " ");
    if (name) {
      setExpressionByName(name);
      Serial.print(F("EXPR OK: "));
      Serial.println(name);
    }
    return;
  }

  if (!strcmp(token, "MOUTH")) {
    char *state = strtok(NULL, " ");
    if (!state) return;

    if (!strcmp(state, "TALK")) {
      talking = true;
    } else if (!strcmp(state, "STOP")) {
      talking = false;
    }
    return;
  }

  if (!strcmp(token, "LOOK")) {
    char *xs = strtok(NULL, " ");
    char *ys = strtok(NULL, " ");

    if (xs && ys) {
      setLookTarget(atoi(xs), atoi(ys));
    }
    return;
  }

  if (!strcmp(token, "SERVO")) {
    char *as = strtok(NULL, " ");
    if (as) {
      targetHeadAngle = clampInt(atoi(as), SERVO_MIN, SERVO_MAX);
    }
    return;
  }

  if (!strcmp(token, "GESTURE")) {
    char *name = strtok(NULL, " ");
    if (!name) return;

    if (!strcmp(name, "WAVE") ||
        !strcmp(name, "ACKNOWLEDGE") ||
        !strcmp(name, "SHUFFLE")) {
      triggerEffect(EFFECT_WIGGLE, 750);
    } else if (!strcmp(name, "NOD")) {
      triggerEffect(EFFECT_NOD, 700);
    } else if (!strcmp(name, "GENTLE_ATTENTION")) {
      triggerEffect(EFFECT_SPARKLE, 900);
    }
    return;
  }

  if (!strcmp(token, "ANIM")) {
    char *name = strtok(NULL, " ");
    if (!name) return;

    if (!strcmp(name, "WIGGLE")) {
      triggerEffect(EFFECT_WIGGLE, 750);
    } else if (!strcmp(name, "NOD")) {
      triggerEffect(EFFECT_NOD, 700);
    } else if (!strcmp(name, "HEART")) {
      triggerEffect(EFFECT_HEART, 1000);
    } else if (!strcmp(name, "SPARKLE")) {
      triggerEffect(EFFECT_SPARKLE, 900);
    } else if (!strcmp(name, "SURPRISE")) {
      triggerEffect(EFFECT_SURPRISE, 500);
      startBlink(false);
    } else if (!strcmp(name, "WAKE")) {
      triggerEffect(EFFECT_WAKE, 800);
      setExpressionByName("ALERT");
    } else if (!strcmp(name, "SLEEP")) {
      setExpressionByName("SLEEPY");
    }
    return;
  }

  if (!strcmp(token, "BLINK")) {
    startBlink(false);
    return;
  }

  if (!strcmp(token, "DOUBLEBLINK")) {
    startBlink(true);
    return;
  }

  if (!strcmp(token, "CENTER")) {
    setLookTarget(0, 0);
    targetHeadAngle = SERVO_CENTER;
    return;
  }

  if (!strcmp(token, "SERVOOFF")) {
    servoEnabled = false;
    headServo.detach();
    return;
  }

  if (!strcmp(token, "SERVON")) {
    if (!servoEnabled) {
      headServo.attach(SERVO_PIN);
      servoEnabled = true;
    }
    targetHeadAngle = SERVO_CENTER;
    return;
  }
}

void pollSerial() {
  while (Serial.available()) {
    char c = Serial.read();

    if (c == '\n') {
      commandBuffer[commandLength] = '\0';
      processCommand(commandBuffer);
      commandLength = 0;
    } else if (c != '\r') {
      if (commandLength < sizeof(commandBuffer) - 1) {
        commandBuffer[commandLength++] = c;
      } else {
        commandLength = 0;
      }
    }
  }
}

// ============================================================
// Boot / diagnostics
// ============================================================

void bootScreen() {
  u8g2.firstPage();
  do {
    u8g2.setFont(u8g2_font_ncenB08_tr);
    u8g2.drawStr(48, 20, "EMU");
    u8g2.drawStr(33, 34, "booting");
    u8g2.drawDisc(28, 48, 2);
    u8g2.drawDisc(100, 48, 2);
  } while (u8g2.nextPage());

  delay(700);

  u8g2.firstPage();
  do {
    u8g2.setFont(u8g2_font_5x7_tr);
    u8g2.drawStr(39, 25, "FACE ONLINE");
    u8g2.drawStr(29, 38, "READY");
  } while (u8g2.nextPage());

  delay(500);
}

void setup() {
  Serial.begin(9600);
  Wire.begin();

  // U8g2 page buffer is intentionally used for Uno SRAM safety.
  u8g2.setBusClock(400000);
  u8g2.begin();

  if (servoEnabled) {
    headServo.attach(SERVO_PIN);
    headServo.write(SERVO_CENTER);
  }

  randomSeed(analogRead(A0));

  lastBlink = millis();
  nextBlink = 3400;
  lastWander = millis();
  lastIdleMotion = millis();

  bootScreen();

  Serial.println(F("OLED OK"));
  Serial.println(F("EMU READY"));
}

void loop() {
  pollSerial();

  unsigned long now = millis();

  updateBlink();
  updatePupils();
  updateHead();
  updateEffects();

  if (now - lastFrame >= FRAME_TIME) {
    lastFrame = now;

    u8g2.firstPage();
    do {
      drawFace();
    } while (u8g2.nextPage());
  }
}
