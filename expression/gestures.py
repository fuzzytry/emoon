from context.models import RobotCommand,GestureType
GESTURE_COMMANDS={
 GestureType.NONE:[],
 GestureType.WAVE:[RobotCommand("gesture",{"name":"WAVE"})],
 GestureType.NOD:[RobotCommand("gesture",{"name":"NOD"})],
 GestureType.SHUFFLE:[RobotCommand("gesture",{"name":"SHUFFLE"})],
 GestureType.GENTLE_ATTENTION:[RobotCommand("gesture",{"name":"GENTLE_ATTENTION"})],
 GestureType.ACKNOWLEDGE:[RobotCommand("gesture",{"name":"ACKNOWLEDGE"})],
}
