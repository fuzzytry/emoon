from context.models import VisionObservation,SemanticObservation,VocalObservation,EmotionState
SCENARIOS={
"PERSON_ENTERS":[{"vision":VisionObservation(face_detected=True,face_x=.5,face_y=.5,tracking_confidence=.9)}],
"PERSON_HAPPY":[{"vision":VisionObservation(face_detected=True,expression=EmotionState.HAPPY,expression_confidence=.75),"semantic":SemanticObservation(text="Hey, I'm back."),"vocal":VocalObservation(estimated_emotion=EmotionState.HAPPY,estimated_confidence=.7)}],
"PERSON_SAD":[{"vision":VisionObservation(face_detected=True,expression=EmotionState.SAD,expression_confidence=.6),"semantic":SemanticObservation(text="I've had a terrible day."),"vocal":VocalObservation(estimated_emotion=EmotionState.SAD,estimated_confidence=.65)}],
"PERSON_TIRED":[{"vision":VisionObservation(face_detected=True,expression=EmotionState.TIRED,expression_confidence=.55),"semantic":SemanticObservation(text="I'm exhausted."),"vocal":VocalObservation(estimated_emotion=EmotionState.TIRED,estimated_confidence=.6)}],
"PRIVACY":[{"vision":VisionObservation(face_detected=True),"privacy":True}],"PERSON_LEAVES":[{"vision":VisionObservation(face_detected=False)}]}
