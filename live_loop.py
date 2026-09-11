import logging,time,cv2
from context.fusion import FusionEngine
from context.models import RobotCommand,EmotionState
from intelligence.decision import DecisionEngine
from expression.behavior import BehaviorEngine
from hardware.robot import Robot
from perception.vision import VisionProvider
from perception.speech import SpeechProvider
from perception.voice_emotion import analyze as analyze_prosody
from output.tts import TTSEngine
from config.settings import settings
logging.basicConfig(level=logging.INFO,format="%(message)s"); logger=logging.getLogger("emu.live")
EMOTION_TO_EXPRESSION={EmotionState.NEUTRAL:"NEUTRAL",EmotionState.HAPPY:"HAPPY",EmotionState.SAD:"SAD",EmotionState.EXCITED:"EXCITED",EmotionState.TIRED:"TIRED",EmotionState.ANGRY:"ANGRY",EmotionState.SURPRISED:"SURPRISED",EmotionState.CONFUSED:"CONFUSED",EmotionState.STRESSED:"ANXIOUS",EmotionState.ANXIOUS:"ANXIOUS",EmotionState.FOCUSED:"ALERT",EmotionState.BORED:"SLEEPY"}
MIN_CONF=.52; EXPR_HOLDOFF=.20; LOOK_INTERVAL=.08; LOOK_EPS=.035
def run_live():
 fusion=FusionEngine(); decision=DecisionEngine(); behavior=BehaviorEngine(); robot=Robot(); tts=TTSEngine()
 vision=VisionProvider(camera_device=settings.camera_device); speech=SpeechProvider(stt_model=settings.stt_model,input_device=(None if settings.mic_device in {"","default"} else int(settings.mic_device) if settings.mic_device.isdigit() else settings.mic_device)); speech.start()
 privacy=settings.privacy_default; last_expr=None; last_expr_at=0.; last_look=(None,None); last_look_at=0.; last_mouth=False
 def expr(name,force=False):
  nonlocal last_expr,last_expr_at
  now=time.monotonic()
  if force or (name!=last_expr and now-last_expr_at>=EXPR_HOLDOFF): robot.send([RobotCommand("expression",{"name":name})]); last_expr=name; last_expr_at=now
 try:
  while True:
   vo,frame=vision.read(); so,sem,audio=speech.poll(); vocal=analyze_prosody(audio,so.duration or 0,len(sem.text.split()) if sem else 0) if audio is not None else None
   ctx=fusion.fuse(vision=vo,speech=so,semantic=sem,vocal=vocal,privacy_active=privacy,robot_connected=robot.connected)
   if privacy:
    expr("PRIVACY",True)
   elif ctx.interaction_state.value == "PROCESSING":
    expr("PROCESSING")
   elif ctx.emotion_confidence >= MIN_CONF:
    expr(EMOTION_TO_EXPRESSION.get(ctx.emotion,"NEUTRAL"))
   elif so.speaking:
    expr("LISTENING")
   else:
    expr("NEUTRAL")
   if vo.face_detected and vo.face_x is not None and vo.face_y is not None:
    x=max(-1,min(1,(vo.face_x-.5)*2)); y=max(-1,min(1,(vo.face_y-.5)*2)); now=time.monotonic()
    if now-last_look_at>=LOOK_INTERVAL and (last_look[0] is None or abs(x-last_look[0])>=LOOK_EPS or abs(y-last_look[1])>=LOOK_EPS): robot.send([RobotCommand("look",{"x":round(x,2),"y":round(y,2)})]); last_look=(x,y); last_look_at=now
   speaking=tts.is_speaking
   if speaking!=last_mouth: robot.send([RobotCommand("mouth",{"state":"TALK" if speaking else "STOP"})]); last_mouth=speaking
   if sem and sem.text:
    logger.info("HEARD: %r",sem.text)
    if tts.is_speaking: tts.stop(); robot.send([RobotCommand("mouth",{"state":"STOP"})]); last_mouth=False
    intent=decision.decide(ctx); logger.info("DECISION: %s -> %r",intent.intent.value,intent.speech); robot.send(behavior.render(intent)); expr(intent.expression.value,True); tts.speak(intent.speech); fusion.history.add("user",ctx.last_utterance,ctx.emotion); fusion.history.add("emu",intent.speech,intent.emotion)
   if frame is not None: cv2.putText(frame,f"State: {ctx.interaction_state.value} | Emotion: {ctx.emotion.value} {ctx.emotion_confidence:.2f}",(20,frame.shape[0]-20),cv2.FONT_HERSHEY_SIMPLEX,.45,(255,255,255),1); cv2.imshow("EMU - live perception",frame)
   key=cv2.waitKey(1)&0xFF
   if key==ord('q'): break
   if key==ord('p'): privacy=not privacy; expr("PRIVACY" if privacy else "NEUTRAL",True)
 finally:
  try: robot.send([RobotCommand("mouth",{"state":"STOP"})])
  except Exception: pass
  vision.close(); speech.stop(); robot.close(); cv2.destroyAllWindows()
