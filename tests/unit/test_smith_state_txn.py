"""State transaction: merges stage, commit applies -- a run that dies leaves state.json untouched."""
import json
from argparse import Namespace

import smith_memory as sm
import smith_state as ss


def _base(tmp_path, state=None):
    base, rd = tmp_path / "base", tmp_path / "base" / "runs" / "r1"
    rd.mkdir(parents=True)
    (base / "state.json").write_text(json.dumps(state or {"thesis": {}, "data_cache": {}, "keep": 1}))
    return base, rd


def _raw(base):
    return json.loads((base / "state.json").read_text())


def test_stage_leaves_state_json_untouched_and_overlay_sees_it(tmp_path):
    base, rd = _base(tmp_path)
    before = (base / "state.json").read_bytes()
    st = ss.load_state(str(base), str(rd))
    st["cycle_position"] = {"position": "mid"}
    ss.stage_state(str(base), str(rd), st, by="test")
    assert (base / "state.json").read_bytes() == before
    assert ss.load_state(str(base), str(rd))["cycle_position"] == {"position": "mid"}
    assert "cycle_position" not in ss.load_state(str(base))


def test_stages_accumulate_across_waves(tmp_path):
    base, rd = _base(tmp_path)
    st = ss.load_state(str(base), str(rd)); st["a"] = 1
    ss.stage_state(str(base), str(rd), st, by="wave1")
    st = ss.load_state(str(base), str(rd)); st["b"] = 2
    ss.stage_state(str(base), str(rd), st, by="wave2")
    patch = ss.load_patch(str(rd))
    assert patch["set"] == {"a": 1, "b": 2}
    assert [s["by"] for s in patch["staged_by"]] == ["wave1", "wave2"]


def test_commit_preserves_keys_other_writers_changed_meanwhile(tmp_path):
    base, rd = _base(tmp_path)
    st = ss.load_state(str(base), str(rd)); st["thesis"] = {"NVDA": "intact"}; del st["keep"]
    ss.stage_state(str(base), str(rd), st, by="merge")
    raw = _raw(base); raw["dashboard_last_synced_ts"] = "2026-09-14"   # sync-decisions, mid-run
    (base / "state.json").write_text(json.dumps(raw))
    out = ss.commit_state(str(base), str(rd), persist_safe=True)
    final = _raw(base)
    assert final["thesis"] == {"NVDA": "intact"}
    assert final["dashboard_last_synced_ts"] == "2026-09-14"
    assert "keep" not in final and out["unset"] == ["keep"]
    assert final["latest_run_dir"] == "runs/r1" and final["ts"].endswith("Z")
    assert not (rd / ss.PENDING).exists() and (rd / ss.COMMITTED).exists()


def test_second_commit_changes_nothing_but_the_stamp(tmp_path):
    base, rd = _base(tmp_path)
    st = ss.load_state(str(base), str(rd)); st["x"] = 1
    ss.stage_state(str(base), str(rd), st, by="t")
    ss.commit_state(str(base), str(rd), persist_safe=True)
    first = _raw(base)
    out = ss.commit_state(str(base), str(rd), persist_safe=True)
    second = _raw(base)
    assert out["committed"] is False and out["keys"] == []
    first.pop("ts"); second.pop("ts")
    assert first == second


def test_unsafe_price_snapshot_withholds_price_keys(tmp_path):
    base, rd = _base(tmp_path, {"us": {"value_usd": 1}, "thesis": {}})
    (rd / "compute_book.json").write_text(json.dumps({"persist_safe": False}))
    st = ss.load_state(str(base), str(rd))
    st["us"] = {"value_usd": 999}; st["thesis"] = {"AMD": "watch"}
    ss.stage_state(str(base), str(rd), st, by="t")
    out = ss.commit_state(str(base), str(rd))                # auto -> reads compute_book.json
    final = _raw(base)
    assert out["withheld"] == ["us"] and final["us"] == {"value_usd": 1}
    assert final["thesis"] == {"AMD": "watch"}


def test_merge_tails_stages_and_does_not_advance_the_committed_watermark(tmp_path):
    base, rd = _base(tmp_path, {"thesis": {}, "data_cache": {}, "news_watermark": "2026-09-01"})
    (rd / "out_cycle.json").write_text(json.dumps(
        {"cycle_position": "mid", "confidence": "high", "falsifier": "capex guide cut"}))
    (rd / "out_watchlist.json").write_text("{}")
    before = (base / "state.json").read_bytes()
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        sm.cmd_merge_tails(Namespace(base_dir=str(base), run_dir=str(rd), today="2026-09-14",
                                     agents="cycle,watchlist"))
    emitted = json.loads(buf.getvalue())
    assert emitted["written"] is False and "cycle_position" in emitted["staged"]["staged_keys"]
    assert (base / "state.json").read_bytes() == before          # a run dying here loses nothing
    assert ss.load_state(str(base), str(rd))["news_watermark"] == "2026-09-14"
    ss.commit_state(str(base), str(rd), persist_safe=True)
    final = _raw(base)
    assert final["cycle_position"]["position"] == "mid" and final["news_watermark"] == "2026-09-14"


def test_uncommitted_runs_are_discoverable(tmp_path):
    base, rd = _base(tmp_path)
    st = ss.load_state(str(base), str(rd)); st["x"] = 1
    ss.stage_state(str(base), str(rd), st, by="t")
    assert ss.uncommitted_runs(str(base)) == ["r1"]
