"""Small pyserial wrapper with an explicit connected state."""
import logging
import time

logger = logging.getLogger("emu.serial")


class SerialLink:
    connected = True

    def __init__(self, port: str, baud: int):
        import serial
        self._serial = serial.Serial(port, baud, timeout=0.1)
        # Opening a Uno serial port commonly resets the board. Give firmware
        # time to boot before the first command so EXPR/LOOK are not lost.
        time.sleep(2.0)
        self._serial.reset_input_buffer()

    def send(self, line: str) -> None:
        self._serial.write((line + "\n").encode("ascii"))
        self._serial.flush()

    def close(self) -> None:
        if self._serial.is_open:
            self._serial.close()


class NullSerialLink:
    connected = False

    def send(self, line: str) -> None:
        logger.info("[NO ROBOT] %s", line)

    def close(self) -> None:
        pass


def connect(port: str, baud: int):
    if not port:
        logger.info("No serial port configured; using NullSerialLink")
        return NullSerialLink()
    try:
        link = SerialLink(port, baud)
        logger.info("Serial connected: %s @ %d", port, baud)
        return link
    except Exception as exc:
        logger.error("Serial open failed for %s: %s", port, exc)
        return NullSerialLink()
