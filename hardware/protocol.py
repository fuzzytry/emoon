"""
Command schema + validation. This is layer 1 of two-layer safety — the
Arduino performs its own independent clamping too, so a bug here can't
alone produce an unsafe physical command.
"""
import time
import uuid
from dataclasses import dataclass, field
from context.models import RobotCommand

PROTOCOL_VERSION = 1
VALID_TYPES = {"expression", "gesture", "servo", "system", "speech"}
VALID_EXPRESSIONS = {"NEUTRAL", "HAPPY", "CURIOUS", "SURPRISED", "SLEEPY",
                      "ALERT", "CONFUSED", "LISTENING", "PROCESSING", "PRIVACY", "CONCERNED"}
VALID_GESTURES = {"WAVE", "NOD", "SHUFFLE", "GENTLE_ATTENTION"}
SERVO_CHANNEL_RANGE = range(0, 5)
SERVO_DEG_RANGE = range(0, 181)


class InvalidCommandError(ValueError):
    pass


@dataclass
class CommandEnvelope:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    timestamp: float = field(default_factory=time.time)
    version: int = PROTOCOL_VERSION
    type: str = ""
    payload: dict = field(default_factory=dict)

    def to_json_line(self) -> str:
        import json
        return json.dumps({
            "id": self.id, "ts": round(self.timestamp, 3), "v": self.version,
            "type": self.type, "payload": self.payload,
        })


def validate(cmd: RobotCommand) -> CommandEnvelope:
    if cmd.type not in VALID_TYPES:
        raise InvalidCommandError(f"unknown command type: {cmd.type}")

    if cmd.type == "expression":
        name = cmd.payload.get("name")
        if name not in VALID_EXPRESSIONS:
            raise InvalidCommandError(f"invalid expression: {name}")

    elif cmd.type == "gesture":
        name = cmd.payload.get("name")
        if name not in VALID_GESTURES:
            raise InvalidCommandError(f"invalid gesture: {name}")

    elif cmd.type == "servo":
        ch = cmd.payload.get("channel")
        deg = cmd.payload.get("deg")
        if ch not in SERVO_CHANNEL_RANGE:
            raise InvalidCommandError(f"channel {ch} out of range")
        if deg not in SERVO_DEG_RANGE:
            raise InvalidCommandError(f"deg {deg} out of range")

    elif cmd.type == "head":
        target = cmd.payload.get("target")
        if target is not None and not (-30 <= target <= 30):
            raise InvalidCommandError(f"head target {target} out of ±30 range")

    return CommandEnvelope(type=cmd.type, payload=cmd.payload)
