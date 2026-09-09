"""
EMU entry point.

    python main.py --simulate                 # run all scripted scenarios
    python main.py --simulate --scenario PERSON_SAD

Real camera/mic mode is NOT implemented yet (Phase 2) — running without
--simulate raises a clear error rather than pretending to process a live
camera feed that doesn't exist in this build.
"""
import argparse
import logging
from simulation.simulator import Simulator


def main():
    parser = argparse.ArgumentParser(description="EMU — AI companion robot")
    parser.add_argument("--simulate", action="store_true", help="run in simulation mode (no hardware needed)")
    parser.add_argument("--scenario", type=str, default=None, help="run a single named scenario instead of all")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if args.simulate:
        sim = Simulator()
        if args.scenario:
            sim.run_scenario(args.scenario)
            sim.robot.close()
        else:
            sim.run_all()
    else:
        raise NotImplementedError(
            "Live camera/mic perception is Phase 2 and isn't built yet in this "
            "delivery. Run with --simulate to test the fusion/decision/expression "
            "pipeline right now."
        )


if __name__ == "__main__":
    main()

    else:
        from live_loop import run_live
        run_live()
