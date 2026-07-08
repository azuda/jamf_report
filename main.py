# main.py
# Cross-platform entrypoint: runs the full report pipeline in order.
# Works on macOS and Windows — invoked by run.sh (launchd) or run.ps1 (Task Scheduler).

import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

SCRIPTS = [
  "query_jamf.py",
  "computer_report.py",
  "device_report.py",
  "upload.py",
]

def main():
  print(f"Script start @ {datetime.now()}", flush=True)

  for script in SCRIPTS:
    result = subprocess.run([sys.executable, script], cwd=PROJECT_ROOT)
    if result.returncode != 0:
      # stop the pipeline — uploading stale/partial data is worse than skipping a day
      print(f"{script} exited with code {result.returncode}, aborting", file=sys.stderr, flush=True)
      sys.exit(result.returncode)

  print(f"\nScript end @ {datetime.now()}", flush=True)

if __name__ == "__main__":
  main()
