import logging
from context.fusion import FusionEngine
from intelligence.decision import DecisionEngine
from expression.behavior import BehaviorEngine
from hardware.robot import Robot
from simulation.scenarios import SCENARIOS
logger=logging.getLogger('emu.simulator')
class Simulator:
 def __init__(self):self.fusion=FusionEngine();self.decision=DecisionEngine();self.behavior=BehaviorEngine();self.robot=Robot()
 def run_scenario(self,name):
  for step in SCENARIOS.get(name,[]):
   ctx=self.fusion.fuse(vision=step.get('vision'),speech=step.get('speech'),semantic=step.get('semantic'),vocal=step.get('vocal'),privacy_active=step.get('privacy',False),robot_connected=self.robot.connected); intent=self.decision.decide(ctx); self.robot.send(self.behavior.render(intent))
 def run_all(self):
  for n in SCENARIOS:self.run_scenario(n)
  self.robot.close()
