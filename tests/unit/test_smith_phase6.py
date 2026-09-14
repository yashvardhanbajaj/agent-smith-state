"""Phase 6 (2026-09-14): health surfacing, the launchd watchdog, and retired code staying retired."""
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
from argparse import Namespace
from datetime import date, datetime, timezone

import pytest

import smith_dashboard as sd
import smith_math
import smith_memory as sm
import smith_runlife as rl

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FIXTURE = os.path.join(ROOT, "tests", "fixtures", "dashboard_case1", "base")


def _ledger(base, stamps):
    with open(os.path.join(base, "ledger.csv"), "w") as fh:
        fh.write("ts,mode,value_usd\n")
        for ts in stamps:
            fh.write(f"{ts},quick,1\n")


def test_todays_missing_run_is_a_problem_only_after_the_watchdog_hour(tmp_path, monkeypatch):
    monkeypatch.setattr(rl, "_mirror_status", lambda base: {"checked": False})
    base = str(tmp_path)
    os.makedirs(os.path.join(base, "runs", "2026-09-11-0907Z"))
    _ledger(base, ["2026-09-11T09:07:00Z"])
    # Monday 2026-09-14: 08:00Z is 13:30 IST (before the daily), 10:45Z is 16:15 IST (after).
    early = rl.health(base, now=datetime(2026, 9, 14, 8, 0, tzinfo=timezone.utc))
    late = rl.health(base, now=datetime(2026, 9, 14, 10, 45, tzinfo=timezone.utc))
    assert not any("today" in p for p in early["problems"])
    assert any("today's scheduled run" in p for p in late["problems"])


def test_cmd_health_writes_the_snapshot_the_dashboard_reads(tmp_path, monkeypatch):
    monkeypatch.setattr(rl, "_mirror_status", lambda base: {"checked": False})
    base = str(tmp_path)
    _ledger(base, [])
    with contextlib.redirect_stdout(io.StringIO()):
        rl.cmd_health(Namespace(base_dir=base, notify=False))
    snap = json.load(open(os.path.join(base, "health.json")))
    assert set(snap) >= {"ok", "headline", "problems", "as_of"}


def test_dashboard_payload_carries_health(tmp_path):
    base = str(tmp_path / "base")
    shutil.copytree(FIXTURE, base)
    assert sd.build_payload(base)["health"] == {"available": False}
    with open(os.path.join(base, "health.json"), "w") as fh:
        json.dump({"ok": False, "headline": "Health: 1 problem(s)", "problems": ["x"],
                   "as_of": "2026-09-14T10:30:00Z", "missed_runs": []}, fh)
    h = sd.build_payload(base)["health"]
    assert h["available"] and h["ok"] is False and h["problems"] == ["x"]
    assert "health" in sd.REQUIRED_KEYS


def test_weekly_report_names_missed_runs(tmp_path):
    base = str(tmp_path)
    os.makedirs(os.path.join(base, "runs", "2026-09-14-0907Z"))
    _ledger(base, ["2026-09-14T09:07:00Z"])
    with open(os.path.join(base, "state.json"), "w") as fh:
        json.dump({}, fh)
    text = sm._report_weekly(base, None, date(2026, 9, 18), {}, [])
    assert "## Missed runs" in text
    assert "2026-09-15" in text and "MISSING" in text


def test_launchd_template_lints_and_targets_weekdays_at_16():
    tpl = os.path.join(ROOT, "scripts", "launchd", "com.agentsmith.health.plist.template")
    body = open(tpl).read()
    assert body.count("<key>Hour</key><integer>16</integer>") == 5
    assert "health --base-dir . --notify" in body
    if sys.platform == "darwin" and shutil.which("plutil"):
        assert subprocess.run(["plutil", "-lint", tpl], capture_output=True).returncode == 0


def test_retired_code_stays_retired():
    for f in ("smith_charts.py", "smith_evidence_audit.py"):
        assert not os.path.exists(os.path.join(ROOT, "scripts", f))
        assert os.path.exists(os.path.join(ROOT, "archive", "scripts-retired-2026-09", f))
    src = open(os.path.join(ROOT, "scripts", "smith_math.py")).read()
    assert '"usage-log"' not in src and "cmd_usage_log" not in src
    import smith_learning
    assert not hasattr(smith_learning, "_today") and not hasattr(smith_learning, "cmd_usage_log")


def test_monday_without_a_deep_row_is_flagged_the_same_day_after_the_watchdog_hour(tmp_path, monkeypatch):
    monkeypatch.setattr(rl, "_mirror_status", lambda base: {"checked": False})
    base = str(tmp_path)
    os.makedirs(os.path.join(base, "runs", "2026-09-14-0907Z"))
    _ledger(base, ["2026-09-11T09:07:00Z", "2026-09-14T09:07:00Z"])   # Monday: a quick row only
    early = rl.health(base, now=datetime(2026, 9, 14, 8, 0, tzinfo=timezone.utc))
    late = rl.health(base, now=datetime(2026, 9, 14, 10, 45, tzinfo=timezone.utc))
    assert not any("weekly" in p for p in early["problems"])
    assert any("weekly deep run" in p for p in late["problems"])
    with open(os.path.join(base, "ledger.csv"), "a") as fh:
        fh.write("2026-09-14T09:40:00Z,deep,1\n")
    done = rl.health(base, now=datetime(2026, 9, 14, 10, 45, tzinfo=timezone.utc))
    assert not any("weekly" in p for p in done["problems"])
