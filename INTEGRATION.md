# EMU Integration Notes

## Architecture

PC:
camera -> face tracking/emotion -> fusion -> decision/LLM -> TTS

Arduino:
serial commands -> OLED face / pupils / mouth / head servo

The PC does not stream animation frames. It sends state changes such as
`EXPR HAPPY`, `LOOK 20 -10`, and `MOUTH TALK`.

## Verified OLED path

The SSD1306 was independently verified on the Uno:

- I2C scanner finds `0x3C`
- minimal OLED initialization succeeds
- minimal OLED + one-servo initialization succeeds

The full firmware therefore initializes the OLED first, keeps the default I2C
clock, and currently allocates only one Servo object. This avoids unnecessary
SRAM pressure on the Uno's 2 KB SRAM.

## Current actuator limitation

Only the head SG90 is physically installed. The protocol still reserves the
future servo channels, but `sketch.ino` only drives channel 0 today. Future
PCA9685 hardware should replace the Uno's direct multi-servo approach rather
than adding five Servo objects to the Uno.

## Emotion mapping

Camera/user emotion is mapped to display expressions:

- NEUTRAL -> NEUTRAL
- HAPPY -> HAPPY
- SAD -> SAD
- EXCITED -> EXCITED
- TIRED -> TIRED
- ANGRY -> ANGRY
- SURPRISED -> SURPRISED
- CONFUSED -> CONFUSED
- STRESSED -> ANXIOUS
- ANXIOUS -> ANXIOUS
- FOCUSED -> ALERT
- BORED -> SLEEPY

The live loop throttles expression changes to prevent noisy camera
classification from making the OLED flicker.

## TTS / mouth

When `TTSEngine.is_speaking` becomes true:

    MOUTH TALK

When speech finishes:

    MOUTH STOP

This is approximate talking animation, not true phoneme-level lip sync.


## Python -> V3 firmware integration

The Python protocol has been aligned with the current single-servo V3 firmware:

- `expression` -> `EXPR NAME`
- `look` -> `LOOK x y`
- `mouth` -> `MOUTH TALK|STOP`
- `head` -> `SERVO degrees`
- current channel-0 servo -> `SERVO degrees`
- high-level gestures are translated to firmware animations:
  - WAVE/ACKNOWLEDGE/SHUFFLE -> `ANIM WIGGLE`
  - NOD -> `ANIM NOD`
  - GENTLE_ATTENTION -> `ANIM SPARKLE`

The Arduino remains responsible for all frame-by-frame animation. Python does
not stream OLED frames.

### TTS lifecycle

`TTSEngine.is_speaking` drives:

    MOUTH TALK
    MOUTH STOP

This is intentionally asynchronous: TTS runs in its own thread while the live
loop continues polling camera, serial and animation state.

### First live test

1. Flash `sketch.ino`.
2. Confirm Serial Monitor prints `OLED OK` and `EMU READY`.
3. Close Serial Monitor.
4. Set `EMU_SERIAL_PORT` in `config/.env` to the actual Arduino COM port.
5. Run `python main.py --live`.
6. Look at the camera and speak.

Expected behavior:
- face emotion changes -> OLED expression changes
- face position changes -> pupils look toward it
- microphone speech -> LISTENING
- LLM processing -> PROCESSING
- TTS -> animated mouth
- privacy (`p`) -> PRIVACY
