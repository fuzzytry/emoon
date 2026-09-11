import argparse,logging
from simulation.simulator import Simulator
def main():
 p=argparse.ArgumentParser(description='EMU - AI companion robot'); p.add_argument('--simulate',action='store_true'); p.add_argument('--scenario'); p.add_argument('--live',action='store_true'); a=p.parse_args(); logging.basicConfig(level=logging.INFO,format='%(message)s')
 if a.simulate:
  s=Simulator(); s.run_scenario(a.scenario) if a.scenario else s.run_all(); s.robot.close()
 elif a.live:
  from live_loop import run_live; run_live()
 else:p.print_help()
if __name__=='__main__':main()
