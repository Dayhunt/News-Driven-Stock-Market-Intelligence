# scheduler.py
"""
Runs the CrewAI pipeline every 10 minutes.
Execute from the project root:
    python scheduler.py
"""

import sys, os, time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from crew.crew_pipeline import run_pipeline


def main():
    print("⏰  Scheduler started.")
    print(f"    CWD : {os.getcwd()}")
    print(f"    First run : {datetime.now().strftime('%H:%M:%S')}\n")

    while True:
        try:
            run_pipeline()
        except Exception as e:
            print(f"❌ Pipeline crashed: {e}")

        print(f"\n⏳  Next run in 10 min …  ({datetime.now().strftime('%H:%M:%S')})\n")
        time.sleep(600)


if __name__ == "__main__":
    main()
