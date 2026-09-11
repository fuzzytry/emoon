"""Robot command gateway. Every command is validated before serial output."""
import logging
from context.models import RobotCommand
from hardware.protocol import validate, InvalidCommandError
from hardware.serial import connect
from config.settings import settings

logger = logging.getLogger("emu.robot")


class Robot:
    def __init__(self):
        self._link = connect(settings.serial_port, settings.serial_baud)
        self.connected = bool(getattr(self._link, "connected", False))

    def send(self, commands: list[RobotCommand]) -> None:
        for cmd in commands:
            try:
                line = validate(cmd).to_wire_line()
                if line:
                    self._link.send(line)
                    logger.info("SENT: %s", line)
            except (InvalidCommandError, KeyError, TypeError, ValueError) as exc:
                logger.error("REJECTED %s: %s", cmd, exc)

    def close(self) -> None:
        self._link.close()
