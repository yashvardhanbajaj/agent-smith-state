"""Script-owned run lock: exclusive, heartbeat-aged, steals recorded, release checked."""
import json
from datetime import datetime, timedelta, timezone

import smith_state as ss

T0 = datetime(2026, 9, 14, 9, 0, tzinfo=timezone.utc)


def test_second_run_is_refused_while_the_first_is_fresh(tmp_path):
    b = str(tmp_path)
    assert ss.lock_acquire(b, "run-a", "quick", "runs/a", now=T0)["acquired"]
    r = ss.lock_acquire(b, "run-b", "deep", now=T0 + timedelta(minutes=40))
    assert r["acquired"] is False and r["holder"]["run_id"] == "run-a"


def test_same_run_reacquires(tmp_path):
    b = str(tmp_path)
    ss.lock_acquire(b, "run-a", now=T0)
    assert ss.lock_acquire(b, "run-a", now=T0)["reentrant"]


def test_heartbeat_keeps_a_long_run_alive_and_its_absence_lets_a_steal_happen(tmp_path):
    b = str(tmp_path)
    ss.lock_acquire(b, "run-a", run_dir="runs/a", now=T0)
    ss.lock_heartbeat(b, run_dir="/x/runs/a", now=T0 + timedelta(minutes=40))
    assert not ss.lock_acquire(b, "run-b", now=T0 + timedelta(minutes=80))["acquired"]
    r = ss.lock_acquire(b, "run-b", now=T0 + timedelta(minutes=90))       # 50 min silent
    assert r["acquired"] and r["stolen"]
    assert r["lock"]["steals"][-1]["from_run_id"] == "run-a"


def test_hard_ceiling_steals_even_with_heartbeats(tmp_path):
    b = str(tmp_path)
    ss.lock_acquire(b, "run-a", run_dir="runs/a", now=T0)
    ss.lock_heartbeat(b, run_id="run-a", now=T0 + timedelta(minutes=155))
    assert ss.lock_acquire(b, "run-b", now=T0 + timedelta(minutes=156))["acquired"]


def test_heartbeat_never_touches_another_runs_lock(tmp_path):
    b = str(tmp_path)
    ss.lock_acquire(b, "run-a", run_dir="runs/a", now=T0)
    assert ss.lock_heartbeat(b, run_dir="runs/zzz", now=T0)["refreshed"] is False


def test_release_checks_ownership(tmp_path):
    b = str(tmp_path)
    ss.lock_acquire(b, "run-a", now=T0)
    assert ss.lock_release(b, "run-b")["released"] is False
    assert ss.lock_release(b, "run-a")["released"]
    assert ss.lock_status(b)["held"] is False


def test_legacy_running_file_is_honoured_then_stolen_when_stale(tmp_path):
    b = str(tmp_path)
    (tmp_path / ".running").write_text("2026-09-14T08:30:00+00:00")
    assert not ss.lock_acquire(b, "run-a", now=T0)["acquired"]
    r = ss.lock_acquire(b, "run-a", now=T0 + timedelta(hours=3))
    assert r["acquired"] and not (tmp_path / ".running").exists()
    assert json.loads((tmp_path / ".smith.lock").read_text())["steals"][0]["kind"] == "legacy"
