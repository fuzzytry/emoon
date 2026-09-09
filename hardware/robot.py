"""High-level Robot interface — this is what the rest of the app calls."""
import logging
from context.models import RobotCommand
from hardware.protocol import validate, InvalidCommandError
from hardware.serial import connect
from config.settings import settings

logger = logging.getLogger("emu.robot")


class Robot:
    def __init__(self):
        self._link = connect(settings.serial_port, settings.serial_baud)
        self.connected = not isinstance(self._link, type(connect("", 0)))  # NullSerialLink check

    def send(self, commands: list[RobotCommand]) -> None:
        for cmd in commands:
            try:
                envelope = validate(cmd)
                line = envelope.to_wire_line()
                if line:
                    self._link.send(line)
                    logger.info("SENT: %s", line)
            except InvalidCommandError as e:
                logger.error("REJECTED unsafe command %s: %s", cmd, e)

    def close(self) -> None:
        self._link.close()
