"""
Cron replacement for the Anthropic-hosted scheduled-tasks mechanism.
Fires orchestrator.py as a fresh subprocess daily at 2:30pm IST - the same
time the Claude Code scheduled task fires today - so behavior is directly
comparable during the cutover.

Runs each sweep as a subprocess (not an in-process function call) so a
crash in one day's run can't corrupt the scheduler process itself, and so
the run gets a clean environment every time.

Run as a long-lived process (e.g. via launchd/systemd, or just `nohup ... &`):
    ./.venv/bin/python scheduler.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler

HERE = Path(__file__).parent
PYTHON = HERE / ".venv" / "bin" / "python"
ORCHESTRATOR = HERE / "orchestrator.py"


def run_sweep_subprocess() -> None:
    print(f"=== Firing sweep at scheduled time ===", flush=True)
    result = subprocess.run(
        [str(PYTHON), str(ORCHESTRATOR)],
        cwd=str(HERE),
        capture_output=False,  # let output stream straight to this process's logs
    )
    if result.returncode != 0:
        print(f"Sweep exited with code {result.returncode}", file=sys.stderr, flush=True)


def main() -> None:
    scheduler = BlockingScheduler(timezone="Asia/Kolkata")
    scheduler.add_job(
        run_sweep_subprocess,
        trigger="cron",
        hour=14,
        minute=30,
        id="agent-smith-daily-quick-sweep",
        misfire_grace_time=3600,  # if the machine was asleep, still fire within 1h
    )
    print("Scheduler started - daily sweep at 14:30 Asia/Kolkata. Ctrl+C to stop.")
    scheduler.start()


if __name__ == "__main__":
    main()
