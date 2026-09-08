"""
Mandatory simulation mode — runs the ENTIRE real pipeline (fusion, decision,
expression, robot protocol) against scripted fake perception, with zero
hardware, zero camera/mic, and zero API keys required (MockLLM by default).
"""
import logging
from context.fusion import FusionEngine
from intelligence.decision import DecisionEngine
from expression.behavior import BehaviorEngine
from hardware.robot import Robot
from simulation.scenarios import SCENARIOS

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("emu.simulator")


class Simulator:
    def __init__(self):
        self.fusion = FusionEngine()
        self.decision = DecisionEngine()
        self.behavior = BehaviorEngine()
        self.robot = Robot()

    def run_scenario(self, name: str) -> None:
        if name not in SCENARIOS:
            logger.error("Unknown scenario: %s", name)
            return
        logger.info("\n========== SCENARIO: %s ==========", name)
        for step in SCENARIOS[name]:
            ctx = self.fusion.fuse(
                vision=step.get("vision"),
                speech=step.get("speech"),
                semantic=step.get("semantic"),
                vocal=step.get("vocal"),
                privacy_active=step.get("privacy", False),
                robot_connected=self.robot.connected,
            )
            logger.info("PERCEPTION -> FUSION: emotion=%s conf=%.2f state=%s",
                        ctx.emotion.value, ctx.emotion_confidence, ctx.interaction_state.value)

            intent = self.decision.decide(ctx)
            logger.info("DECISION: intent=%s speech=%r expression=%s",
                        intent.intent.value, intent.speech, intent.expression.value)

            commands = self.behavior.render(intent)
            self.robot.send(commands)

            if intent.speech:
                self.fusion.history.add("user", ctx.last_utterance, ctx.emotion)
                self.fusion.history.add("emu", intent.speech, intent.emotion)

    def run_all(self) -> None:
        for name in SCENARIOS:
            self.run_scenario(name)
        self.robot.close()
