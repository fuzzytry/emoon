import time
import numpy as np
import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision as mp_vision
from mediapipe.tasks.python import BaseOptions
from hsemotion_onnx.facial_emotions import HSEmotionRecognizer
from context.models import VisionObservation, EmotionState
HSEMOTION_TO_EMU={"Anger":EmotionState.ANGRY,"Contempt":EmotionState.CONFUSED,"Disgust":EmotionState.ANGRY,"Fear":EmotionState.ANXIOUS,"Happiness":EmotionState.HAPPY,"Neutral":EmotionState.NEUTRAL,"Sadness":EmotionState.SAD,"Surprise":EmotionState.SURPRISED}
class VisionProvider:
 def __init__(self,camera_device=0,model_path="perception/face_landmarker.task"):
  self.cap=cv2.VideoCapture(camera_device)
  if not self.cap.isOpened():raise RuntimeError(f"Could not open camera device {camera_device}")
  options=mp_vision.FaceLandmarkerOptions(base_options=BaseOptions(model_asset_path=model_path),output_facial_transformation_matrixes=True,num_faces=1,running_mode=mp_vision.RunningMode.VIDEO)
  self.landmarker=mp_vision.FaceLandmarker.create_from_options(options); self.emotion_model=HSEmotionRecognizer(model_name="enet_b0_8_best_afew")
 def _extract(self,frame,landmarks,w,h):
  xs=[lm.x*w for lm in landmarks]; ys=[lm.y*h for lm in landmarks]; x1,x2=max(0,int(min(xs))-10),min(w,int(max(xs))+10); y1,y2=max(0,int(min(ys))-10),min(h,int(max(ys))+10); return frame[y1:y2,x1:x2],(x1,y1,x2,y2)
 def _angles(self,matrix):
  m=np.array(matrix).reshape(4,4)[:3,:3]; yaw=np.degrees(np.arctan2(-m[2,0],np.sqrt(m[2,1]**2+m[2,2]**2))); pitch=np.degrees(np.arctan2(m[2,1],m[2,2])); return float(yaw),float(pitch)
 def read(self):
  ok,frame=cv2.VideoCapture.read(self.cap)
  if not ok:return VisionObservation(face_detected=False),None
  h,w=frame.shape[:2]; rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB); result=self.landmarker.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB,data=rgb),int(time.time()*1000)); obs=VisionObservation()
  if not result.face_landmarks:return obs,frame
  crop,(x1,y1,x2,y2)=self._extract(rgb,result.face_landmarks[0],w,h); obs.face_detected=True; obs.face_count=1; obs.face_x=((x1+x2)/2)/w; obs.face_y=((y1+y2)/2)/h; obs.face_size=((x2-x1)*(y2-y1))/(w*h); obs.tracking_confidence=.9
  if result.facial_transformation_matrixes:obs.head_yaw,obs.head_pitch=self._angles(result.facial_transformation_matrixes[0])
  if crop.size:
   label,scores=self.emotion_model.predict_emotions(crop,logits=False); obs.expression=HSEMOTION_TO_EMU.get(label,EmotionState.NEUTRAL); obs.expression_confidence=round(float(max(scores)),2)
  cv2.rectangle(frame,(x1,y1),(x2,y2),(0,200,0),2); return obs,frame
 def close(self):self.cap.release()
