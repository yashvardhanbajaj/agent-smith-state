"""health / memory-summary / preflight / abort."""
import io
import contextlib
import json
from argparse import Namespace
from datetime import datetime, timedelta, timezone

import smith_runlife as rl
import smith_state as ss


def _base(tmp_path, ledger_rows=()):
    base = tmp_path / "base"
    (base / "runs").mkdir(parents=True)
    (base / "state.json").write_text(json.dumps({"known_gaps": [], "open_flags": []}))
    (base / "policy.json").write_text(json.dumps({"confirmed": True, "as_of": "2026-09-08"}))
    lines = ["ts,mode,value_usd,wallet_usd,value_trust,notes"] + list(ledger_rows)
    (base / "ledger.csv").write_text("\n".join(lines) + "\n")
    return base


def _emit(fn, **kw):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fn(Namespace(**kw))
    return json.loads(buf.getvalue().strip().splitlines()[-1])


def test_health_flags_missed_runs_stale_lock_and_uncommitted_state(tmp_path, monkeypatch):
    monkeypatch.setenv("SMITH_LIVE_SKILL_DIR", str(tmp_path / "nope"))
    base = _base(tmp_path)
    rd = base / "runs" / "2026-09-11-0900Z"
    rd.mkdir()
    st = ss.load_state(str(base), str(rd)); st["x"] = 1
    ss.stage_state(str(base), str(rd), st, by="t")
    (base / ".smith.lock").write_text(json.dumps({"run_id": "old", "acquired_utc": "2026-09-13T00:00:00Z",
                                                  "heartbeat_utc": "2026-09-13T00:00:00Z"}))
    h = rl.health(str(base), now=datetime(2026, 9, 14, 10, 30, tzinfo=timezone.utc))
    text = " ".join(h["problems"])
    assert not h["ok"]
    assert "scheduled run(s)" in text and "stale smith run lock" in text
    assert "uncommitted staged state" in text and "no ledger row" in text


def test_health_catches_a_future_ledger_stamp(tmp_path, monkeypatch):
    monkeypatch.setenv("SMITH_LIVE_SKILL_DIR", str(tmp_path / "nope"))
    base = _base(tmp_path, ["2026-09-14T19:07:00+00:00,quick,1,1,ok,"])
    h = rl.health(str(base), now=datetime(2026, 9, 14, 7, 0, tzinfo=timezone.utc))
    assert any("FUTURE" in p for p in h["problems"])


def test_mirror_drift_is_reported(tmp_path, monkeypatch):
    base = _base(tmp_path)
    live, agents = tmp_path / "live", tmp_path / "agents"
    live.mkdir(); agents.mkdir()
    (base / "skill").mkdir(); (base / "skill" / "agents").mkdir()
    (live / "SKILL.md").write_text("new"); (base / "skill" / "SKILL.md").write_text("old")
    monkeypatch.setenv("SMITH_LIVE_SKILL_DIR", str(live))
    monkeypatch.setenv("SMITH_LIVE_AGENTS_DIR", str(agents))
    m = rl._mirror_status(str(base))
    assert m["stale"] and m["differs"] == ["SKILL.md"]


def test_memory_summary_is_small_and_lists_only_open_proposals(tmp_path):
    base = _base(tmp_path, ["2026-09-13T09:00:00Z,quick,40000,1500,ok,fine"])
    props = [{"id": f"P-{i}", "status": "superseded", "rationale": "x" * 2000} for i in range(200)]
    props += [{"id": "P-900", "status": "open", "action": "Buy MU", "size_usd": 300},
              {"id": "P-901", "status": "deferred", "action": "Trim NVDA"}]
    (base / "proposals.json").write_text(json.dumps({"proposals": props, "scorecard": {"hit_rate": 0.29}}))
    s = rl.memory_summary(str(base))
    assert [p["id"] for p in s["open_proposals"]] == ["P-900", "P-901"]
    assert len(json.dumps(s)) < 8000


def test_preflight_refuses_when_another_run_holds_the_lock(tmp_path, monkeypatch):
    monkeypatch.setenv("SMITH_LIVE_SKILL_DIR", str(tmp_path / "nope"))
    base = _base(tmp_path)
    ss.lock_acquire(str(base), "other-run")
    out = _emit(rl.cmd_preflight, base_dir=str(base), mode="quick", run_id="me", run_dir=None, today=None)
    assert out["proceed"] is False


def test_preflight_proceeds_and_reports(tmp_path, monkeypatch):
    monkeypatch.setenv("SMITH_LIVE_SKILL_DIR", str(tmp_path / "nope"))
    base = _base(tmp_path)
    out = _emit(rl.cmd_preflight, base_dir=str(base), mode="quick", run_id="me", run_dir=None, today=None)
    assert out["proceed"] and out["lock"]["acquired"]
    assert {"health", "validate", "freshness", "lessons", "memory"} <= set(out)
    assert ss.lock_status(str(base))["holder"]["run_id"] == "me"


def test_abort_discards_staged_state_stubs_report_declares_outage_and_unlocks(tmp_path):
    base = _base(tmp_path)
    rd = base / "runs" / "2026-09-14-0900Z"
    rd.mkdir()
    ss.lock_acquire(str(base), "me", run_dir=str(rd))
    st = ss.load_state(str(base), str(rd)); st["thesis"] = {"MU": "broken"}
    ss.stage_state(str(base), str(rd), st, by="t")
    before = json.loads((base / "state.json").read_text())
    out = _emit(rl.cmd_abort, base_dir=str(base), run_dir=str(rd), run_id=None,
                reason="INDmoney connector unavailable", kind="connector", today="2026-09-14")
    after = json.loads((base / "state.json").read_text())
    assert out["discarded_pending"] and (rd / "ABORTED.json").exists()
    assert out["lock"]["released"] and not ss.lock_status(str(base))["held"]
    assert (base / "reports" / "daily" / "2026-09-14.md").exists()
    assert after.get("run_outages") and "thesis" not in after
    assert {k: v for k, v in after.items() if k != "run_outages"} == before
