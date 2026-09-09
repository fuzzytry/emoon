"""Kokoro TTS — provider-independent interface (generate/play/stop/queue/
speaking-state), so swapping providers later doesn't touch calling code."""
import logging
import threading
import numpy as np
import sounddevice as sd
from kokoro import KPipeline

logger = logging.getLogger("emu.tts")
SAMPLE_RATE = 24000


class TTSEngine:
    def __init__(self, lang_code: str = "a", voice: str = "af_heart"):
        self.pipeline = KPipeline(lang_code=lang_code)
        self.voice = voice
        self._speaking = threading.Event()
        self._stop_flag = threading.Event()
        self._lock = threading.Lock()

    @property
    def is_speaking(self) -> bool:
        return self._speaking.is_set()

    def stop(self):
        """Interrupt speech immediately — used when the user starts talking
        over EMU (section 18's interruption requirement)."""
        self._stop_flag.set()
        sd.stop()

    def speak(self, text: str, blocking: bool = False):
        if not text:
            return
        if blocking:
            self._speak_now(text)
        else:
            threading.Thread(target=self._speak_now, args=(text,), daemon=True).start()

    def _speak_now(self, text: str):
        with self._lock:
            self._stop_flag.clear()
            self._speaking.set()
            try:
                for _, _, audio in self.pipeline(text, voice=self.voice):
                    if self._stop_flag.is_set():
                        break
                    sd.play(audio, SAMPLE_RATE)
                    sd.wait()
            except Exception as e:
                logger.error("TTS playback failed: %s", e)
            finally:
                self._speaking.clear()
