import logging
import cv2

from context.fusion import FusionEngine
from intelligence.decision import DecisionEngine
from expression.behavior import BehaviorEngine
from hardware.robot import Robot
from perception.vision import VisionProvider
from perception.speech import SpeechProvider
from perception.voice_emotion import analyze as analyze_prosody
from output.tts import TTSEngine
from config.settings import settings

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("emu.live")


def run_live():
    fusion = FusionEngine()
    decision = DecisionEngine()
    behavior = BehaviorEngine()
    robot = Robot()
    tts = TTSEngine()

    vision = VisionProvider(camera_device=settings.camera_device)
    speech = SpeechProvider(stt_model=settings.stt_model)
    speech.start()

    privacy_active = settings.privacy_default
    logger.info("EMU live mode running. Press 'q' in the camera window to quit.")

    try:
        while True:
            vision_obs, frame = vision.read()
            speech_obs, semantic_obs, audio = speech.poll()

            vocal_obs = None
            if audio is not None:
                vocal_obs = analyze_prosody(
                    audio, speech_obs.duration or 0,
                    len(semantic_obs.text.split()) if semantic_obs else 0,
                )

            ctx = fusion.fuse(
                vision=vision_obs, speech=speech_obs, semantic=semantic_obs,
                vocal=vocal_obs, privacy_active=privacy_active,
                robot_connected=robot.connected,
            )

            # Reflexive pupil tracking — independent of the decision engine,
            # runs every frame a face is visible so the eyes feel alive even
            # when nothing conversational is happening.
            if vision_obs.face_detected and vision_obs.face_x is not None:
                look_x = (vision_obs.face_x - 0.5) * 2   # -1..1, mirrored feel natural
                look_y = (vision_obs.face_y - 0.5) * 2
                robot.send([RobotCommand("look", {"x": round(look_x, 2), "y": round(look_y, 2)})])

            if semantic_obs and semantic_obs.text:
                logger.info("HEARD: %r", semantic_obs.text)
                if tts.is_speaking:
                    tts.stop()  # user started talking over EMU — stop and listen
                intent = decision.decide(ctx)
                logger.info("DECISION: %s -> %r", intent.intent.value, intent.speech)
                commands = behavior.render(intent)
                robot.send(commands)
                tts.speak(intent.speech)
                fusion.history.add("user", ctx.last_utterance, ctx.emotion)
                fusion.history.add("emu", intent.speech, intent.emotion)

            if frame is not None:
                cv2.putText(frame, f"State: {ctx.interaction_state.value}", (20, frame.shape[0] - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                cv2.imshow("EMU — live perception", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == ord("p"):
                privacy_active = not privacy_active
                logger.info("Privacy toggled: %s", privacy_active)

    finally:
        vision.close()
        speech.stop()
        robot.close()
        cv2.destroyAllWindows()
