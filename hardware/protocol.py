"""Flat-token serial protocol shared by Python and the Arduino firmware."""
import time
from dataclasses import dataclass, field
from context.models import RobotCommand

VALID_TYPES = {"expression", "gesture", "servo", "system", "head", "look", "mouth"}
VALID_EXPRESSIONS = {
    "NEUTRAL", "HAPPY", "SAD", "CURIOUS", "SURPRISED", "SLEEPY", "TIRED",
    "ALERT", "CONFUSED", "ANXIOUS", "LISTENING", "PROCESSING", "EXCITED",
    "EMBARRASSED", "PRIVACY", "CONCERNED", "ANGRY", "TALKING",
}
VALID_GESTURES = {"WAVE", "NOD", "SHUFFLE", "GENTLE_ATTENTION", "ACKNOWLEDGE"}


class InvalidCommandError(ValueError):
    pass


@dataclass
class CommandEnvelope:
    timestamp: float = field(default_factory=time.time)
    type: str = ""
    payload: dict = field(default_factory=dict)

    def to_wire_line(self) -> str:
        if self.type == "expression":
            return f"EXPR {self.payload['name']}"
        if self.type == "gesture":
            # Current Uno firmware has one physical head servo. Translate
            # high-level gestures into firmware-native animations.
            name = str(self.payload["name"]).upper()
            if name in {"WAVE", "ACKNOWLEDGE"}:
                return "ANIM WIGGLE"
            if name == "NOD":
                return "ANIM NOD"
            if name == "GENTLE_ATTENTION":
                return "ANIM SPARKLE"
            if name == "SHUFFLE":
                return "ANIM WIGGLE"
            return ""
        if self.type == "servo":
            channel = int(self.payload["channel"])
            deg = int(self.payload["deg"])
            # V3 currently has only the head SG90 on channel 0.
            if channel != 0:
                return ""
            return f"SERVO {deg}"
        if self.type == "head":
            target = max(-30, min(30, int(self.payload.get("target", 0))))
            return f"SERVO {90 + target}"
        if self.type == "look":
            x = max(-1.0, min(1.0, float(self.payload["x"])))
            y = max(-1.0, min(1.0, float(self.payload["y"])))
            return f"LOOK {round(x * 100):d} {round(y * 100):d}"
        if self.type == "mouth":
            return f"MOUTH {str(self.payload['state']).upper()}"
        return ""  # system/lighting is intentionally local-only


def validate(cmd: RobotCommand) -> CommandEnvelope:
    if cmd.type not in VALID_TYPES:
        raise InvalidCommandError(f"unknown command type: {cmd.type}")

    if cmd.type == "expression":
        name = str(cmd.payload.get("name", ""))
        if name not in VALID_EXPRESSIONS:
            raise InvalidCommandError(f"invalid expression: {name}")

    elif cmd.type == "gesture":
        name = str(cmd.payload.get("name", ""))
        if name not in VALID_GESTURES:
            raise InvalidCommandError(f"invalid gesture: {name}")

    elif cmd.type == "mouth":
        state = str(cmd.payload.get("state", "")).upper()
        if state not in {"TALK", "STOP"}:
            raise InvalidCommandError(f"invalid mouth state: {state}")
        cmd.payload["state"] = state

    elif cmd.type == "servo":
        channel = cmd.payload.get("channel")
        deg = cmd.payload.get("deg")
        if not isinstance(channel, int) or not 0 <= channel <= 4:
            raise InvalidCommandError(f"invalid servo channel: {channel}")
        if not isinstance(deg, int) or not 0 <= deg <= 180:
            raise InvalidCommandError(f"invalid servo degrees: {deg}")

    elif cmd.type == "look":
        try:
            x = float(cmd.payload["x"])
            y = float(cmd.payload["y"])
        except (KeyError, TypeError, ValueError) as exc:
            raise InvalidCommandError("look requires numeric x and y") from exc
        if not -1.0 <= x <= 1.0 or not -1.0 <= y <= 1.0:
            raise InvalidCommandError(f"look offset out of range: {x},{y}")

    return CommandEnvelope(type=cmd.type, payload=cmd.payload)
