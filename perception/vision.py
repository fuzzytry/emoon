"""
Live webcam perception: MediaPipe Face Landmarker for detection/pose,
HSEmotion for expression classification. Also drives the live analytics
window you asked for — face box + per-emotion percentage bars drawn
directly on the camera feed.
"""
import time
import logging
import numpy as np
import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision as mp_vision
from mediapipe.tasks.python import BaseOptions
from hsemotion_onnx.facial_emotions import HSEmotionRecognizer

from context.models import VisionObservation, EmotionState

logger = logging.getLogger("emu.vision")

# HSEmotion's 8 output classes mapped onto EMU's broader EmotionState set.
# This is a deliberate, lossy mapping — documented here so it's a visible
# decision, not a silent guess.
HSEMOTION_TO_EMU = {
    "Anger": EmotionState.ANGRY,
    "Contempt": EmotionState.CONFUSED,
    "Disgust": EmotionState.ANGRY,
    "Fear": EmotionState.ANXIOUS,
    "Happiness": EmotionState.HAPPY,
    "Neutral": EmotionState.NEUTRAL,
    "Sadness": EmotionState.SAD,
    "Surprise": EmotionState.SURPRISED,
}

_MODEL_FILE_HINT = (
    "MediaPipe needs a Face Landmarker .task model file. Download it once from "
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task "
    "and save it as perception/face_landmarker.task"
)


class VisionProvider:
    def __init__(self, camera_device: int = 0, model_path: str = "perception/face_landmarker.task"):
        self.cap = cv2.VideoCapture(camera_device)
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open camera device {camera_device}")

        try:
            options = mp_vision.FaceLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=model_path),
                output_facial_transformation_matrixes=True,
                num_faces=1,
                running_mode=mp_vision.RunningMode.VIDEO,
            )
            self.landmarker = mp_vision.FaceLandmarker.create_from_options(options)
        except Exception as e:
            raise RuntimeError(f"{_MODEL_FILE_HINT}\nOriginal error: {e}")

        self.emotion_model = HSEmotionRecognizer(model_name="enet_b0_8_best_afew")
        self._frame_idx = 0

    def _extract_face_crop(self, frame_rgb, landmarks, w, h) -> np.ndarray:
        xs = [lm.x * w for lm in landmarks]
        ys = [lm.y * h for lm in landmarks]
        x1, x2 = max(0, int(min(xs)) - 10), min(w, int(max(xs)) + 10)
        y1, y2 = max(0, int(min(ys)) - 10), min(h, int(max(ys)) + 10)
        return frame_rgb[y1:y2, x1:x2], (x1, y1, x2, y2)

    def _yaw_pitch_from_matrix(self, matrix) -> tuple[float, float]:
        # 4x4 transformation matrix -> approximate yaw/pitch in degrees.
        # Standard rotation-matrix decomposition; sufficient precision for
        # "look left/right/up/down" behavior, not aerospace-grade.
        m = np.array(matrix).reshape(4, 4)[:3, :3]
        yaw = np.degrees(np.arctan2(-m[2, 0], np.sqrt(m[2, 1] ** 2 + m[2, 2] ** 2)))
        pitch = np.degrees(np.arctan2(m[2, 1], m[2, 2]))
        return float(yaw), float(pitch)

    def read(self) -> tuple[VisionObservation, np.ndarray]:
        """Returns (observation, annotated_bgr_frame_for_display)."""
        ok, frame_bgr = self.cap.read()
        if not ok:
            return VisionObservation(face_detected=False), None

        h, w = frame_bgr.shape[:2]
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

        timestamp_ms = int(time.time() * 1000)
        result = self.landmarker.detect_for_video(mp_image, timestamp_ms)
        self._frame_idx += 1

        obs = VisionObservation()
        if not result.face_landmarks:
            cv2.putText(frame_bgr, "No face detected", (20, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            return obs, frame_bgr

        landmarks = result.face_landmarks[0]
        crop, (x1, y1, x2, y2) = self._extract_face_crop(frame_rgb, landmarks, w, h)

        obs.face_detected = True
        obs.face_count = len(result.face_landmarks)
        obs.face_x = round((x1 + x2) / 2 / w, 3)
        obs.face_y = round((y1 + y2) / 2 / h, 3)
        obs.face_size = round((x2 - x1) * (y2 - y1) / (w * h), 3)
        obs.tracking_confidence = 0.9  # MediaPipe doesn't expose a direct
                                        # per-face confidence in this API;
                                        # presence of landmarks stands in.

        if result.facial_transformation_matrixes:
            yaw, pitch = self._yaw_pitch_from_matrix(result.facial_transformation_matrixes[0])
            obs.head_yaw, obs.head_pitch = round(yaw, 1), round(pitch, 1)

        scores_by_label = {}
        if crop.size > 0:
            emotion_label, scores = self.emotion_model.predict_emotions(crop, logits=False)
            labels = ["Anger", "Contempt", "Disgust", "Fear", "Happiness", "Neutral", "Sadness", "Surprise"]
            scores_by_label = dict(zip(labels, scores))
            top_conf = float(max(scores))
            obs.expression = HSEMOTION_TO_EMU.get(emotion_label, EmotionState.NEUTRAL)
            obs.expression_confidence = round(top_conf, 2)

        # ---- draw live analytics overlay ----
        cv2.rectangle(frame_bgr, (x1, y1), (x2, y2), (0, 200, 0), 2)
        bar_x, bar_y = 20, 20
        for i, (label, score) in enumerate(scores_by_label.items()):
            y = bar_y + i * 22
            bar_w = int(score * 150)
            cv2.rectangle(frame_bgr, (bar_x + 90, y), (bar_x + 90 + bar_w, y + 16), (0, 180, 255), -1)
            cv2.putText(frame_bgr, f"{label} {score*100:.0f}%", (bar_x, y + 13),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

        return obs, frame_bgr

    def close(self):
        self.cap.release()
