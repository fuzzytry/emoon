# EMU — Phase 1 (software skeleton + simulation mode)

## What's built
Data models, multimodal context fusion, LLM decision engine (provider-agnostic
via LiteLLM, mock mode by default), expression/behavior/choreography engine,
two-layer-validated hardware protocol, and a full simulation mode that runs
the entire pipeline with zero hardware and zero API keys.

## What's NOT built yet (Phase 2)
Live camera (MediaPipe + HSEmotion), live microphone (Silero VAD + faster-whisper),
speech-emotion/prosody, and TTS (Kokoro). These involve library APIs I have not
personally executed and want to verify incrementally rather than ship unverified
— see the architecture discussion in this project's chat history for why.

## Setup
    python -m venv venv
    source venv/bin/activate   # or venv\Scripts\activate on Windows
    pip install -r requirements.txt
    cp config/.env.example config/.env

## Run
    python main.py --simulate
    python main.py --simulate --scenario PERSON_SAD

This runs every scripted scenario through the REAL fusion → decision →
expression → robot-command pipeline and prints each stage's output. No
physical robot is required — commands are logged as
`[NO ROBOT CONNECTED] would send: ...` unless `EMU_SERIAL_PORT` is set in `.env`.

## Known limitations (be exact about these — do not overstate what's done)
- Emotion fusion in context/fusion.py is intentionally simple (max-confidence
  candidate + EMA) — a placeholder for real tuning once Phase 2 provides
  actual camera/mic noise characteristics to tune against.
- MockLLM produces keyword-matched canned responses, not real reasoning —
  set EMU_USE_MOCK_LLM=false and configure a real provider to test actual
  LLM behavior.
- No pytest test suite yet — deliberately deferred until you've confirmed
  this actually runs on your machine, so tests verify real behavior rather
  than my guess at it.
