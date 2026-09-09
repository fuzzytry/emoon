"""
Prosody features via librosa — the lighter, more honest tier we chose over
a full speech-emotion classifier (see architecture discussion). Measurable,
interpretable signals: pitch, energy, speaking rate.
"""
import numpy as np
import librosa
from context.models import VocalObservation, EmotionState

SAMPLE_RATE = 16000


def analyze(audio: np.ndarray, duration_s: float, word_count: int) -> VocalObservation:
    obs = VocalObservation()
    if audio is None or len(audio) < SAMPLE_RATE // 2:
        return obs

    rms = float(np.sqrt(np.mean(audio ** 2)))
    obs.energy_level = round(min(1.0, rms * 8), 2)  # rough normalization

    try:
        f0, voiced_flag, _ = librosa.pyin(
            audio, fmin=librosa.note_to_hz("C2"), fmax=librosa.note_to_hz("C7"),
            sr=SAMPLE_RATE,
        )
        f0_voiced = f0[voiced_flag] if voiced_flag is not None else np.array([])
    except Exception:
        f0_voiced = np.array([])

    rate_wpm = (word_count / duration_s) * 60 if duration_s > 0 and word_count > 0 else None

    # Deliberately coarse, explainable heuristic — NOT a trained classifier.
    # High energy + fast rate reads as EXCITED; low energy + slow reads as
    # TIRED/SAD. This is exactly the kind of estimate that should carry a
    # visible, modest confidence rather than a confident label.
    if obs.energy_level and obs.energy_level > 0.6 and rate_wpm and rate_wpm > 160:
        obs.estimated_emotion = EmotionState.EXCITED
        obs.estimated_confidence = 0.45
    elif obs.energy_level and obs.energy_level < 0.2:
        obs.estimated_emotion = EmotionState.TIRED
        obs.estimated_confidence = 0.4
    else:
        obs.estimated_emotion = EmotionState.NEUTRAL
        obs.estimated_confidence = 0.3

    return obs
