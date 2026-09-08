"""
pyserial wrapper. A NullSerialLink stands in automatically when no port is
configured, so the rest of the codebase never branches on "do we have
hardware" — it just calls .send() either way."""
import logging

logger = logging.getLogger("emu.serial")


class SerialLink:
    def __init__(self, port: str, baud: int):
        import serial  # pyserial — only imported when actually needed
        self._serial = serial.Serial(port, baud, timeout=1)

    def send(self, line: str) -> None:
        self._serial.write((line + "\n").encode())

    def close(self) -> None:
        self._serial.close()


class NullSerialLink:
    """No physical robot connected — commands are logged, not sent."""
    def send(self, line: str) -> None:
        logger.info("[NO ROBOT CONNECTED] would send: %s", line)

    def close(self) -> None:
        pass


def connect(port: str, baud: int):
    if not port:
        logger.info("No serial port configured — running with NullSerialLink")
        return NullSerialLink()
    try:
        return SerialLink(port, baud)
    except Exception as e:
        logger.error("Failed to open serial port %s (%s) — falling back to NullSerialLink", port, e)
        return NullSerialLink()
