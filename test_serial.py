"""Quick hardware smoke test for EMU V3.
Run after setting EMU_SERIAL_PORT in config/.env:
    python test_serial.py
"""
import time
from config.settings import settings
from hardware.robot import Robot
from context.models import RobotCommand

if not settings.serial_port:
    raise SystemExit("Set EMU_SERIAL_PORT in config/.env first.")

robot = Robot()
print("Connected:", robot.connected)
if not robot.connected:
    raise SystemExit("Could not connect to Arduino.")

sequence = [
    RobotCommand("expression", {"name": "HAPPY"}),
    RobotCommand("look", {"x": -0.8, "y": 0.0}),
]
robot.send(sequence); time.sleep(1.0)

robot.send([RobotCommand("look", {"x": 0.8, "y": 0.0})]); time.sleep(1.0)
robot.send([RobotCommand("look", {"x": 0.0, "y": 0.0})]); time.sleep(.5)

robot.send([RobotCommand("expression", {"name": "SURPRISED"})])
time.sleep(.4)
robot.send([RobotCommand("expression", {"name": "HAPPY"})])
robot.send([RobotCommand("gesture", {"name": "WAVE"})])
time.sleep(1.0)

robot.send([RobotCommand("expression", {"name": "TALKING"})])
robot.send([RobotCommand("mouth", {"state": "TALK"})])
time.sleep(2.0)
robot.send([RobotCommand("mouth", {"state": "STOP"})])
robot.send([RobotCommand("expression", {"name": "NEUTRAL"})])
robot.close()
print("Smoke test complete.")
