# EMU 🤖
## Emotion-Aware AI Desk Companion

EMU is a small AI desk companion combining computer vision, emotion recognition, speech, local AI and physical expression.

**PC = brain. Arduino = body.**

### Current stack
- Webcam + MediaPipe face tracking
- HSEmotion facial emotion recognition
- Silero VAD + faster-whisper STT
- Ollama/LiteLLM decision layer
- Kokoro TTS
- USB serial to Arduino Uno
- SSD1306 128x64 expressive OLED
- Pupil tracking + animated mouth
- Servo control + simulation mode

### Run
```bash
pip install -r requirements.txt
python main.py --simulate
python main.py --live
```

Set `config/.env` from `.env.example`; configure the Arduino COM port and Ollama model there.

### Serial protocol
`EXPR`, `LOOK`, `MOUTH`, `SERVO`, `GESTURE` are intentionally flat text commands so the Uno stays lightweight.
