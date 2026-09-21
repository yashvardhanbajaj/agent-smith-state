"""A catalyst revision may arrive as a CHANGE-SET -- {"catalysts": {"added", "changed": [{"match", ...}], "retired"}}.

Found 2026-09-21: `_overlay` replaced the tail's `catalysts` LIST with that dict and the next `merge-tails`
died on `dict(x)` over a string. `_catalyst_changeset` normalises it into the list shapes the revision
path reads; `added` entries must survive hydration (which only revises EXISTING items)."""
import json
import os

import smith_comms as C

CXMT = "CXMT HBM3E: small-scale/trial production confirmed again 09-20 (qualification samples)"
SUMMIT = "Trump-Xi summit in Washington Thursday 09-24"
NEW = "Oracle-leased Project Jupiter datacentre loans quoted at 89-91c"


def _run(tmp_path, monkeypatch, patch):
    base = {"catalysts": [{"headline": SUMMIT, "date": "2026-09-21", "affects": ["TSM", "TER"]}],
            "retired_catalysts": []}
    (tmp_path / "out_catalyst.json").write_text(json.dumps(base))
    carried = [{"headline": CXMT, "date": "2026-09-20", "affects": ["MU", "AMAT", "TER"]}]
    monkeypatch.setattr(C, "_state", lambda run_dir: {"factor_catalysts": {"catalysts": carried}})
    rec = C.apply_revision(str(tmp_path), "catalyst", {"catalysts": patch}, "M1", 1)
    return rec, json.loads((tmp_path / "out_catalyst.json").read_text())


def test_changed_by_match_prefix_and_substring(tmp_path, monkeypatch):
    rec, out = _run(tmp_path, monkeypatch, {"changed": [
        {"match": "Trump-Xi summit in Washington", "affects": ["TSM"], "note": "TER withdrawn"},
        {"match": "small-scale/trial production confirmed", "affects": ["MU"]}]})
    assert rec["applied"], rec
    assert isinstance(out["catalysts"], list)
    by = {c["headline"]: c for c in out["catalysts"]}
    assert by[SUMMIT]["affects"] == ["TSM"] and by[SUMMIT]["revision_note"] == "TER withdrawn"
    assert by[CXMT]["affects"] == ["MU"] and by[CXMT]["date"] == "2026-09-20"   # hydrated from carried, not a stub


def test_added_entry_survives_hydration(tmp_path, monkeypatch):
    rec, out = _run(tmp_path, monkeypatch, {"added": [{"headline": NEW, "date": "2026-09-18", "affects": ["ORCL"]}]})
    assert rec["applied"], rec
    assert any(c["headline"] == NEW for c in out["catalysts"])


def test_retired_resolves_and_unmatched_change_is_dropped(tmp_path, monkeypatch):
    rec, out = _run(tmp_path, monkeypatch, {
        "retired": [{"headline": "small-scale/trial production confirmed", "reason": "dup"}],
        "changed": [{"match": "no such catalyst anywhere", "affects": []}]})
    assert all("no such catalyst" not in c["headline"] for c in out["catalysts"])
    assert any(r.get("headline") == CXMT for r in out.get("retired_catalysts") or [])   # resolved to the full carried headline
    assert any("dropped" in h for h in (rec.get("hydration") or []))                   # and the unmatched change said so


def test_ir_verified_earnings_date_beats_feed_date():
    """MU (2026-09-21): company IR said 09-30 after the close; yfinance's 10-01 was the reaction session and sat in the
    calendar as 'confirmed'. The IR date must land in the calendar cache and survive a later feed-sourced merge."""
    import smith_memory as M
    st = {"data_cache": {"earnings_calendar": {"MU": {"date": "2026-10-01", "confirmed": True, "source": "yfinance"}}}}
    M._merge_earnings({"earnings_facts_updates": {"MU": {"reported_date": "2026-09-30", "timing": "after_close",
                      "first_reaction_session": "2026-10-01", "date_source": "Micron IR press release 2026-08-26"}}}, st, "2026-09-21")
    assert st["data_cache"]["earnings_calendar"]["MU"]["date"] == "2026-09-30"
    M._merge_watchlist({"earnings_calendar_updates": {"MU": {"date": "2026-10-01", "confirmed": True, "source": "yfinance"}}}, st, "2026-09-22")
    assert st["data_cache"]["earnings_calendar"]["MU"]["date"] == "2026-09-30"          # not put back
    M._merge_watchlist({"earnings_calendar_updates": {"AMD": {"date": "2026-11-04", "confirmed": True, "source": "yfinance"}}}, st, "2026-09-22")
    assert st["data_cache"]["earnings_calendar"]["AMD"]["date"] == "2026-11-04"         # other names still update
