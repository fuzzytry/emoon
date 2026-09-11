"""Kokoro TTS — provider-independent interface (generate/play/stop/queue/
speaking-state). Adds explicit lifecycle logging and defensive audio-type
handling per the "do not silently swallow errors" requirement."""
import logging
import threading
import numpy as np
import sounddevice as sd
from kokoro import KPipeline

logger = logging.getLogger("emu.tts")
SAMPLE_RATE = 24000


class TTSEngine:
    def __init__(self, lang_code: str = "a", voice: str = "af_heart", output_device=None):
        self.pipeline = KPipeline(lang_code=lang_code)
        self.voice = voice
        self.output_device = output_device
        self._speaking = threading.Event()
        self._stop_flag = threading.Event()
        self._lock = threading.Lock()
        logger.info("[TTS] initialized, output device: %s",
                    sd.query_devices(output_device)["name"] if output_device is not None
                    else sd.query_devices(sd.default.device[1])["name"])

    @property
    def is_speaking(self) -> bool:
        return self._speaking.is_set()

    def stop(self):
        self._stop_flag.set()
        sd.stop()

    def speak(self, text: str, blocking: bool = False):
        if not text:
            logger.warning("[TTS] speak() called with empty text — nothing to say")
            return
        if blocking:
            self._speak_now(text)
        else:
            threading.Thread(target=self._speak_now, args=(text,), daemon=True).start()

    def _speak_now(self, text: str):
        with self._lock:
            self._stop_flag.clear()
            self._speaking.set()
            logger.info("[TTS] starting: %r", text)
            try:
                chunk_count = 0
                for _, _, audio in self.pipeline(text, voice=self.voice):
                    if self._stop_flag.is_set():
                        logger.info("[TTS] interrupted mid-speech")
                        break
                    # Kokoro may yield a torch.Tensor — sounddevice needs numpy.
                    audio_np = audio.numpy() if hasattr(audio, "numpy") else np.asarray(audio, dtype=np.float32)
                    chunk_count += 1
                    logger.info("[TTS] speaking chunk %d (%d samples, device=%s)",
                                chunk_count, len(audio_np), self.output_device)
                    sd.play(audio_np, SAMPLE_RATE, device=self.output_device)
                    sd.wait()
                logger.info("[TTS] finished (%d chunks played)", chunk_count)
            except Exception as e:
                logger.error("[TTS] error: %s", e, exc_info=True)
            finally:
                self._speaking.clear()
