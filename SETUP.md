# EMU Setup

## Current verified hardware

- Arduino Uno
- SSD1306 128x64 I2C OLED at address `0x3C`
- One SG90 head servo on D6
- USB connection to the PC

The OLED was independently verified with an I2C scanner (`0x3C`) and a minimal
OLED + one-servo sketch before using the full EMU firmware.

## Arduino

1. Open `sketch.ino` in Arduino IDE.
2. Select **Arduino Uno**.
3. Select the correct COM port.
4. Install:
   - Adafruit GFX Library
   - Adafruit SSD1306
   - Servo (normally bundled with the AVR Arduino core)
5. Upload.
6. Close Serial Monitor before running Python.

Expected boot output:

    OLED OK
    EMU READY

Expected OLED boot sequence:

    EMU
    EMU READY
    [animated face]

## Python

Create `config/.env` from `config/.env.example`.

Set the actual Arduino COM port, for example:

    EMU_SERIAL_PORT=COM5
    EMU_SERIAL_BAUD=9600

The serial wrapper waits briefly after opening the port because an Arduino Uno
normally resets when its USB serial port is opened.

Run:

    python main.py --live

Use `q` in the camera window to quit and `p` to toggle privacy.

## Ollama

The default configuration targets:

    ollama/llama3.2
    http://localhost:11434

If Ollama is unavailable, EMU falls back to a deterministic local response.

## Protocol

    EXPR HAPPY
    EXPR SAD
    EXPR ANGRY
    LOOK 20 -10
    MOUTH TALK
    MOUTH STOP
    SERVO 95
    GESTURE NOD
    ANIM HEART
    ANIM SPARKLE

Python sends semantic state changes. The Arduino owns face animation, blinking,
pupil easing, and mouth animation.
