"""
Command schema + validation, wire-compatible with the flat-token Arduino
parser already built and tested in this project (EXPR/GESTURE/SERVO
lines) — NOT nested JSON. This was corrected after checking against the
actual firmware rather than inventing a new protocol Arduino can't read.
"""
import time
import logging
from dataclasses import dataclass, field
from context.models import RobotCommand

logger = logging.getLogger("emu.protocol")

VALID_TYPES = {"expression", "gesture", "servo", "system", "head"}
VALID_EXPRESSIONS = {"NEUTRAL", "HAPPY", "CURIOUS", "SURPRISED", "SLEEPY",
                      "ALERT", "CONFUSED", "LISTENING", "PROCESSING", "PRIVACY", "CONCERNED"}
VALID_GESTURES = {"WAVE", "NOD", "SHUFFLE", "GENTLE_ATTENTION"}
SERVO_CHANNEL_RANGE = range(0, 5)
SERVO_DEG_RANGE = range(0, 181)


class InvalidCommandError(ValueError):
    pass


@dataclass
class CommandEnvelope:
    timestamp: float = field(default_factory=time.time)
    type: str = ""
    payload: dict = field(default_factory=dict)

    def to_wire_line(self) -> str:
        """Flat-token format matching the Arduino sketch's actual parser."""
        if self.type == "expression":
            return f"EXPR {self.payload['name']}"
        if self.type == "gesture":
            return f"GESTURE {self.payload['name']}"
        if self.type == "servo":
            return f"SERVO {self.payload['channel']} {self.payload['deg']}"
        if self.type == "head":
            # Arduino head channel is 0; map ±30deg target to 60-120 range,
            # matching servos[0]'s min/max in the firmware.
            deg = 90 + int(self.payload.get("target", 0))
            return f"SERVO 0 {deg}"
        if self.type == "system":
            return ""  # lighting-only commands: no Arduino equivalent yet
                       # (NeoPixel ring was dropped in the simplified build —
                       # this is a silent no-op by design, not a bug)
        return ""


def validate(cmd: RobotCommand) -> CommandEnvelope:
    if cmd.type not in VALID_TYPES:
        raise InvalidCommandError(f"unknown command type: {cmd.type}")
    if cmd.type == "expression" and cmd.payload.get("name") not in VALID_EXPRESSIONS:
        raise InvalidCommandError(f"invalid expression: {cmd.payload.get('name')}")
    if cmd.type == "gesture" and cmd.payload.get("name") not in VALID_GESTURES:
        raise InvalidCommandError(f"invalid gesture: {cmd.payload.get('name')}")
    if cmd.type == "servo":
        if cmd.payload.get("channel") not in SERVO_CHANNEL_RANGE:
            raise InvalidCommandError(f"channel {cmd.payload.get('channel')} out of range")
        if cmd.payload.get("deg") not in SERVO_DEG_RANGE:
            raise InvalidCommandError(f"deg {cmd.payload.get('deg')} out of range")
    return CommandEnvelope(type=cmd.type, payload=cmd.payload)
