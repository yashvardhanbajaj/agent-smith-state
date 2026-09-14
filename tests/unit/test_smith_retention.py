"""Phase 5 retention: flags, data_quality, data_cache, proposal text, trade notes. Archive, never delete."""
import contextlib
import importlib.util
import io
import json
import os
from argparse import Namespace

import smith_memory as sm

MIG = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "migrations", "m2026_09_open_flags.py")


def _base(tmp_path, state, proposals=None, trades=None):
    (tmp_path / "state.json").write_text(json.dumps(state))
    (tmp_path / "proposals.json").write_text(json.dumps({"proposals": proposals or []}))
    if trades is not None:
        (tmp_path / "trades.json").write_text(json.dumps({"trades": trades}))
    return tmp_path


def _compact(base, today="2026-09-14", mode="full", write=True):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        sm.cmd_compact(Namespace(base_dir=str(base), holdings=None, today=today, write=write, mode=mode))
    return json.loads(buf.getvalue())


def _j(p):
    return json.loads(p.read_text())


HELD = [{"ticker": "MU"}, {"ticker": "NVDA"}]


def test_flags_close_when_old_and_every_ticker_exited(tmp_path):
    flags = [{"ticker": "BX", "opened": "2026-08-01", "flag": "exited"},
             {"ticker": "MU", "opened": "2026-07-01", "flag": "held name"},
             {"ticker": "IREN", "opened": "2026-07-01", "flag": "decision", "kind": "user_decision"},
             {"ticker": "__BOOK__", "opened": "2026-07-01", "flag": "book-level"},
             {"ticker": "ORCL/MU", "opened": "2026-07-01", "flag": "mixed"},
             {"ticker": "HOOD", "opened": "2026-09-10", "flag": "recent"},
             {"ticker": "X", "flag": "closed by hand", "closed_on": "2026-09-13"}]
    base = _base(tmp_path, {"holdings": HELD, "open_flags": flags})
    _compact(base, mode="cheap")
    kept = {f["ticker"] for f in _j(base / "state.json")["open_flags"]}
    assert kept == {"MU", "IREN", "__BOOK__", "ORCL/MU", "HOOD"}
    arch = _j(base / "flags-archive.json")["open_flags"]
    assert {f["ticker"] for f in arch} == {"BX", "X"} and arch[0]["closed_reason"].startswith("auto")


def test_data_quality_expires_dated_notes_only(tmp_path):
    dq = ["old 2026-09-01 note", "fresh 2026-09-12 note", "undated note", {"text": "x", "as_of": "2026-08-01"}]
    base = _base(tmp_path, {"holdings": HELD, "data_quality": dq})
    _compact(base, mode="cheap")
    assert _j(base / "state.json")["data_quality"] == ["fresh 2026-09-12 note", "undated note"]
    assert len(_j(base / "flags-archive.json")["data_quality"]) == 2


def test_cache_prunes_only_after_the_unheld_clock_runs_out_and_protects_live_references(tmp_path):
    dc = {"betas": {"MU": {"value": 1}, "ORCL": {"value": 1}, "AMD": {"value": 1}, "as_of": "2026-09-01"},
          "atr20": {"values_pct": {"MU": 3.0, "ORCL": 4.0, "AMD": 5.0}, "as_of": "2026-09-01"}}
    props = [{"id": "P-1", "ticker": "AMD", "status": "open"}]
    base = _base(tmp_path, {"holdings": HELD, "data_cache": dc}, proposals=props)
    _compact(base, today="2026-09-01", mode="cheap")
    st = _j(base / "state.json")
    assert st["data_cache"]["unheld_since"] == {"ORCL": "2026-09-01"}      # AMD has an open proposal
    assert "ORCL" in st["data_cache"]["betas"]                            # clock started, nothing pruned
    _compact(base, today="2026-10-05", mode="cheap")
    st = _j(base / "state.json")
    assert "ORCL" not in st["data_cache"]["betas"] and "ORCL" not in st["data_cache"]["atr20"]["values_pct"]
    assert "AMD" in st["data_cache"]["betas"] and "MU" in st["data_cache"]["betas"]
    assert st["data_cache"]["betas"]["as_of"] == "2026-09-01"
    arc = _j(base / "exited-holdings-archive.json")
    assert arc["data_cache.betas"]["ORCL"] == {"value": 1} and arc["data_cache.atr20.values_pct"]["ORCL"] == 4.0


def test_a_ticker_that_returns_is_unstamped(tmp_path):
    base = _base(tmp_path, {"holdings": HELD, "data_cache": {"betas": {"ORCL": {"value": 1}},
                                                          "unheld_since": {"ORCL": "2026-08-01"}}})
    st = _j(base / "state.json"); st["holdings"].append({"ticker": "ORCL"}); (base / "state.json").write_text(json.dumps(st))
    _compact(base, mode="cheap")
    st = _j(base / "state.json")
    assert "ORCL" in st["data_cache"]["betas"] and "ORCL" not in st["data_cache"]["unheld_since"]


def test_unscorable_superseded_rows_archive_immediately_open_rows_never(tmp_path):
    props = [{"id": "P-1", "status": "superseded", "ticker": "MU", "date": "2026-09-10"},
             {"id": "P-2", "status": "superseded", "ticker": "MU", "price_at_proposal": 100, "date": "2026-09-10"},
             {"id": "P-3", "status": "open", "ticker": "NVDA", "date": "2026-05-01"}]
    base = _base(tmp_path, {"holdings": HELD}, proposals=props)
    _compact(base)
    assert [p["id"] for p in _j(base / "proposals.json")["proposals"]] == ["P-2", "P-3"]
    assert [p["id"] for p in _j(base / "proposals-archive.json")["proposals"]] == ["P-1"]


def test_terminal_text_is_clipped_to_a_sidecar_open_text_is_not(tmp_path):
    long = "x" * 2000
    props = [{"id": "P-1", "status": "auto_retired", "ticker": "MU", "price_at_proposal": 1,
              "date": "2026-09-10", "rationale": long, "history": [{"n": i, "t": long[:200]} for i in range(12)]},
             {"id": "P-2", "status": "open", "ticker": "NVDA", "rationale": long}]
    base = _base(tmp_path, {"holdings": HELD}, proposals=props)
    _compact(base)
    rows = {p["id"]: p for p in _j(base / "proposals.json")["proposals"]}
    assert len(rows["P-1"]["rationale"]) == sm.TEXT_CLIP_CHARS + 1 and len(rows["P-1"]["history"]) == 3
    assert rows["P-1"]["text_archived"] and rows["P-2"]["rationale"] == long
    side = _j(base / "proposals-text-archive.json")["texts"]["P-1"]
    assert side["rationale"] == long and len(side["history"]) == 12
    out = _compact(base)
    assert not [m for m in out["moves"] if m.get("text_clipped_rows")]      # idempotent


def test_trade_notes_clip_to_sidecar_and_cheap_mode_leaves_them(tmp_path):
    trades = [{"ticker": "MU", "date": "2026-09-01", "qty": 1, "price_usd": 100, "message_id": "m1", "notes": "n" * 900},
              {"ticker": "MU", "date": "2026-09-02", "qty": 1, "price_usd": 101, "notes": "short"}]
    base = _base(tmp_path, {"holdings": HELD}, trades=trades)
    _compact(base, mode="cheap")
    assert len(_j(base / "trades.json")["trades"][0]["notes"]) == 900
    _compact(base)
    t = _j(base / "trades.json")["trades"]
    assert len(t[0]["notes"]) == sm.NOTES_CLIP_CHARS + 1 and t[0]["notes_archived"] == "m1" and t[1]["notes"] == "short"
    assert _j(base / "trades-notes-archive.json")["notes"]["m1"] == "n" * 900


def test_dry_run_writes_nothing(tmp_path):
    base = _base(tmp_path, {"holdings": HELD, "open_flags": [{"ticker": "BX", "opened": "2026-07-01"}]})
    before = (base / "state.json").read_bytes()
    out = _compact(base, mode="cheap", write=False)
    assert out["dry_run"] and out["moves"] and (base / "state.json").read_bytes() == before
    assert not (base / "flags-archive.json").exists()


def test_open_flags_migration_matches_by_ticker_and_date(tmp_path):
    spec = importlib.util.spec_from_file_location("mig", MIG)
    mig = importlib.util.module_from_spec(spec); spec.loader.exec_module(mig)
    state = {"open_flags": [{"ticker": "TER", "opened": "2026-08-19", "flag": "dust"},
                            {"ticker": "IREN", "flag": "keep on watchlist 2026-08-03"},
                            {"ticker": "BX", "opened": "2026-08-17", "flag": "exited"},
                            {"ticker": "NEW", "opened": "2026-09-13", "flag": "added after approval"}],
             "data_quality": ["a", "b"], "preferences": {"hide": []}}
    archive = {}
    out = mig.migrate(state, archive)
    assert {f["ticker"] for f in state["open_flags"]} == {"TER", "NEW"}
    assert state["open_flags"][0]["kind"] == "user_decision" and out["unmatched_left_open"] == [("NEW", "2026-09-13")]
    assert state["preferences"]["standing_decisions"][0]["ticker"] == "IREN"
    assert state["data_quality"] == [] and len(archive["open_flags"]) == 2 and archive["data_quality"] == ["a", "b"]
