# EMU V3

### An expressive AI desk companion robot

EMU is a small, expressive desktop companion designed to combine **AI, computer vision, voice interaction, emotional expression, and physical movement** into a single character.

The idea is simple:

> **The computer is EMU's brain. The robot is EMU's body.**

EMU does not try to be a humanoid robot. It is intentionally small, stationary, expressive, and personality-driven.

---

## What is EMU?

EMU is a purpose-built AI companion that can:

- Listen to the user through a microphone
- Convert speech to text
- Analyze voice characteristics
- Detect facial expressions and interaction context
- Generate conversational responses using an LLM
- Speak responses using text-to-speech
- Animate an OLED face
- Blink and move its pupils
- Change expressions based on interaction
- Move a servo for physical expression
- Perform gestures and animations
- Operate as a virtual desktop companion even without the physical robot

The physical robot is controlled by an Arduino, while the heavy AI processing runs on the connected computer.

---

# Architecture

```text
                     ┌──────────────────────┐
                     │       USER           │
                     │  Voice / Face / PC   │
                     └──────────┬───────────┘
                                │
                ┌───────────────┴───────────────┐
                │                               │
                ▼                               ▼
        ┌───────────────┐               ┌───────────────┐
        │  Microphone   │               │    Camera     │
        └───────┬───────┘               └───────┬───────┘
                │                               │
                ▼                               ▼
        ┌───────────────┐               ┌───────────────┐
        │   Speech /    │               │ Vision /      │
        │     STT       │               │ Emotion       │
        └───────┬───────┘               └───────┬───────┘
                │                               │
                └───────────────┬───────────────┘
                                ▼
                       ┌─────────────────┐
                       │ Context Fusion  │
                       └────────┬────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   AI Decision   │
                       │      / LLM      │
                       └────────┬────────┘
                                │
                 ┌──────────────┴──────────────┐
                 ▼                             ▼
        ┌─────────────────┐           ┌─────────────────┐
        │       TTS       │           │    Behavior     │
        │  Kokoro / Audio │           │   Expression    │
        └────────┬────────┘           └────────┬────────┘
                 │                             │
                 └──────────────┬──────────────┘
                                ▼
                       ┌─────────────────┐
                       │    Arduino     │
                       │   Body Control │
                       └────────┬────────┘
                                │
                  ┌─────────────┴─────────────┐
                  ▼                           ▼
             ┌─────────┐                ┌──────────┐
             │  OLED   │                │  Servo   │
             │  Face   │                │ Movement │
             └─────────┘                └──────────┘
	  
V3 Features
Expressive OLED Face

EMU V3 uses an OLED display to render a custom animated face.

The face includes:

Organic eyes
Moving pupils
Catchlights
Eyelids
Blinking
Double blinking
Blush
Mouth animation
Looking/searching behavior
Processing animation
Expression-specific eye shapes
Small organic micro-movements

The goal is to avoid the typical robotic, and instead make the face feel alive.
