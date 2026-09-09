"""Ties Intent + Behavior library into the final list of RobotCommands
sent downstream — this is the single place that turns a decision into
actual output commands."""
from context.models import Intent, RobotCommand
from expression.choreography import BEHAVIOR_LIBRARY
from expression.gestures import GESTURE_COMMANDS


class BehaviorEngine:
    def render(self, intent: Intent) -> list[RobotCommand]:
        behavior = BEHAVIOR_LIBRARY[intent.expression]
        commands: list[RobotCommand] = [
            RobotCommand("expression", {"name": behavior.expression.value}),
            RobotCommand("system", {"lighting": behavior.lighting.value}),
        ]
        if intent.head_target_deg is not None:
            commands.append(RobotCommand("head", {"target": intent.head_target_deg}))
        commands.extend(GESTURE_COMMANDS.get(intent.gesture, []))
        return commands
