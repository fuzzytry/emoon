"""
Live microphone perception: Silero VAD (streaming, decides when someone is
actually talking) gates faster-whisper (only transcribes real utterances,
not silence — avoids wasting compute and Whisper's known hallucination-
on-silence behavior).
"""
import logging
import numpy as np
import sounddevice as sd
import torch
from silero_vad import load_silero_vad, VADIterator
from faster_whisper import WhisperModel

from context.models import SpeechObservation, SemanticObservation

logger = logging.getLogger("emu.speech")

SAMPLE_RATE = 16000
WINDOW_SAMPLES = 1536  # per Silero VAD's own streaming example


class SpeechProvider:
    def __init__(self, stt_model: str = "small.en"):
        self.vad_model = load_silero_vad(onnx=True)
        self.vad_iterator = VADIterator(self.vad_model, sampling_rate=SAMPLE_RATE)
        self.whisper = WhisperModel(stt_model, device="cpu", compute_type="int8")

        self._buffer: list[np.ndarray] = []
        self._speaking = False
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE, channels=1, dtype="float32",
            blocksize=WINDOW_SAMPLES, callback=self._on_audio,
        )
        self._pending_utterance: np.ndarray | None = None

    def _on_audio(self, indata, frames, time_info, status):
        if status:
            logger.warning("audio input status: %s", status)
        chunk = indata[:, 0].copy()
        chunk_t = torch.from_numpy(chunk)
        vad_result = self.vad_iterator(chunk_t, return_seconds=True)

        if self._speaking:
            self._buffer.append(chunk)

        if vad_result and "start" in vad_result:
            self._speaking = True
            self._buffer = [chunk]
        elif vad_result and "end" in vad_result and self._speaking:
            self._speaking = False
            self._pending_utterance = np.concatenate(self._buffer) if self._buffer else None
            self._buffer = []

    def start(self):
        self._stream.start()

    def stop(self):
        self._stream.stop()
        self._stream.close()

    def poll(self) -> tuple[SpeechObservation, SemanticObservation | None, np.ndarray | None]:
        """Call this regularly from the main loop (non-blocking). Returns
        speech state always; SemanticObservation + raw audio only when an
        utterance just finished and was transcribed."""
        speech_obs = SpeechObservation(speaking=self._speaking)

        if self._pending_utterance is not None:
            audio = self._pending_utterance
            self._pending_utterance = None
            speech_obs.speech_ended = True
            speech_obs.duration = round(len(audio) / SAMPLE_RATE, 2)
            speech_obs.audio_energy = float(np.sqrt(np.mean(audio ** 2)))

            segments, info = self.whisper.transcribe(audio, language="en")
            text = " ".join(seg.text.strip() for seg in segments).strip()
            semantic = SemanticObservation(
                text=text,
                stt_confidence=round(float(getattr(info, "language_probability", 0.0)), 2),
            )
            return speech_obs, semantic, audio

        return speech_obs, None, None
