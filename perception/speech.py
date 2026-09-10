"""
Live microphone perception: Silero VAD (streaming, decides when someone is
actually talking) gates faster-whisper. FIXED from last version:
- window size corrected to 512 samples (was 1536 — wrong for Silero's
  16kHz streaming requirement, likely the actual cause of "nothing heard")
- explicit input device selection (was silently using system default,
  which is a common Windows multi-device gotcha)
- thread-safe handoff via a Lock (audio callback runs on its own thread)
- periodic debug logging of raw audio level so you can SEE the mic is
  capturing before worrying about VAD/STT at all
"""
import logging
import threading
import numpy as np
import sounddevice as sd
import torch
from silero_vad import load_silero_vad, VADIterator
from faster_whisper import WhisperModel

from context.models import SpeechObservation, SemanticObservation

logger = logging.getLogger("emu.speech")

SAMPLE_RATE = 16000
WINDOW_SAMPLES = 512  # REQUIRED exact value for Silero VAD streaming at 16kHz


def list_audio_devices():
    """Run this standalone to find your mic's device index:
        python -c "from perception.speech import list_audio_devices; list_audio_devices()"
    """
    print(sd.query_devices())


class SpeechProvider:
    def __init__(self, stt_model: str = "small.en", input_device=None):
        self.vad_model = load_silero_vad(onnx=True)
        self.vad_iterator = VADIterator(self.vad_model, sampling_rate=SAMPLE_RATE)
        self.whisper = WhisperModel(stt_model, device="cpu", compute_type="int8")

        self._lock = threading.Lock()
        self._buffer: list[np.ndarray] = []
        self._speaking = False
        self._pending_utterance: np.ndarray | None = None

        self._last_level_log = 0
        self._callback_count = 0

        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE, channels=1, dtype="float32",
            blocksize=WINDOW_SAMPLES, device=input_device,
            callback=self._on_audio,
        )
        logger.info("Using input device: %s", sd.query_devices(input_device or sd.default.device[0])["name"])

    def _on_audio(self, indata, frames, time_info, status):
        if status:
            logger.warning("audio input status: %s", status)
        chunk = indata[:, 0].copy()
        self._callback_count += 1

        # Debug: prove audio is actually being captured, roughly once/sec.
        # 16000 samples/sec / 512 per chunk ~= 31 chunks/sec.
        if self._callback_count % 31 == 0:
            peak = float(np.max(np.abs(chunk)))
            logger.info("[mic level] peak=%.3f  %s", peak, "SOUND DETECTED" if peak > 0.02 else "(quiet)")

        chunk_t = torch.from_numpy(chunk)
        vad_result = self.vad_iterator(chunk_t, return_seconds=True)

        with self._lock:
            if self._speaking:
                self._buffer.append(chunk)
            if vad_result and "start" in vad_result:
                self._speaking = True
                self._buffer = [chunk]
                logger.info("[VAD] speech START")
            elif vad_result and "end" in vad_result and self._speaking:
                self._speaking = False
                self._pending_utterance = np.concatenate(self._buffer) if self._buffer else None
                self._buffer = []
                logger.info("[VAD] speech END")

    def start(self):
        self._stream.start()

    def stop(self):
        self._stream.stop()
        self._stream.close()

    def poll(self) -> tuple[SpeechObservation, SemanticObservation | None, np.ndarray | None]:
        with self._lock:
            speaking_now = self._speaking
            pending = self._pending_utterance
            self._pending_utterance = None

        speech_obs = SpeechObservation(speaking=speaking_now)

        if pending is not None:
            speech_obs.speech_ended = True
            speech_obs.duration = round(len(pending) / SAMPLE_RATE, 2)
            speech_obs.audio_energy = float(np.sqrt(np.mean(pending ** 2)))

            try:
                segments, info = self.whisper.transcribe(pending, language="en")
                text = " ".join(seg.text.strip() for seg in segments).strip()
            except Exception as e:
                logger.error("Whisper transcription failed: %s", e)
                text = ""

            logger.info("[STT] transcribed: %r", text)
            semantic = SemanticObservation(
                text=text,
                stt_confidence=round(float(getattr(info, "language_probability", 0.0)), 2) if text else 0.0,
            )
            return speech_obs, semantic, pending

        return speech_obs, None, None
