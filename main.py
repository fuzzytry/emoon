"""
EMU entry point.

    python main.py --simulate                 # run all scripted scenarios
    python main.py --simulate --scenario PERSON_SAD
    python main.py --live                     # run live perception mode
"""
import argparse
import logging
from simulation.simulator import Simulator


def main():
    parser = argparse.ArgumentParser(description="EMU — AI companion robot")
    parser.add_argument("--simulate", action="store_true", help="run in simulation mode (no hardware needed)")
    parser.add_argument("--scenario", type=str, default=None, help="run a single named scenario instead of all")
    parser.add_argument("--live", action="store_true", help="run in live perception mode (camera + microphone)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if args.simulate:
        sim = Simulator()
        if args.scenario:
            sim.run_scenario(args.scenario)
            sim.robot.close()
        else:
            sim.run_all()
    elif args.live:
        from live_loop import run_live
        run_live()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
