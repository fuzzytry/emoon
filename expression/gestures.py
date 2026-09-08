"""
Semantic gestures decoupled from actuator geometry — "WAVE" is a concept,
the hardware layer decides how it's actually achieved with whatever servo
count/geometry the physical robot ends up with. This is what lets the
5-servo config evolve without touching this file.
"""
from context.models import GestureType, RobotCommand

GESTURE_COMMANDS: dict[GestureType, list[RobotCommand]] = {
    GestureType.NONE: [],
    GestureType.WAVE: [RobotCommand("gesture", {"name": "WAVE"})],
    GestureType.NOD: [RobotCommand("gesture", {"name": "NOD"})],
    GestureType.SHUFFLE: [RobotCommand("gesture", {"name": "SHUFFLE"})],
    GestureType.ACKNOWLEDGE: [RobotCommand("gesture", {"name": "NOD"})],
    GestureType.GENTLE_ATTENTION: [RobotCommand("gesture", {"name": "NOD"})],
}
