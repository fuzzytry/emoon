from context.models import Intent,RobotCommand
from expression.choreography import BEHAVIOR_LIBRARY
from expression.gestures import GESTURE_COMMANDS
class BehaviorEngine:
    def render(self,intent:Intent)->list[RobotCommand]:
        behavior=BEHAVIOR_LIBRARY.get(intent.expression,BEHAVIOR_LIBRARY[next(iter(BEHAVIOR_LIBRARY))])
        commands=[RobotCommand("expression",{"name":behavior.expression.value}),RobotCommand("system",{"lighting":behavior.lighting.value})]
        if intent.head_target_deg is not None: commands.append(RobotCommand("head",{"target":intent.head_target_deg}))
        elif behavior.head_target_deg: commands.append(RobotCommand("head",{"target":behavior.head_target_deg}))
        commands.extend(GESTURE_COMMANDS.get(intent.gesture,[])); return commands
