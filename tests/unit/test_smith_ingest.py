"""Ingest writers: build-holdings, book sanity gate, append-ledger, sync-decisions, trade-rationale."""
import contextlib
import io
import json
from argparse import Namespace
from datetime import datetime, timedelta, timezone

import pytest

import smith_ledger as sl
import smith_math as smm
import smith_memory as sm


def _emit(fn, args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fn(args)
    return json.loads(buf.getvalue().strip().splitlines()[-1])


def _holdings(tmp_path, prior, usdinr=88.0, ledger_rows=()):
    base, rd = tmp_path, tmp_path / "r"
    rd.mkdir(exist_ok=True)
    (base / "state.json").write_text(json.dumps({"holdings": prior}))
    if ledger_rows:
        (base / "ledger.csv").write_text(
            "ts,mode,value_usd,usdinr,wallet_usd,spx,ndx,smh,smh_asof,est_net_flows_usd,"
            "external_flow_usd,value_trust,notes\r\n" + "".join(r + "\r\n" for r in ledger_rows))
    snap = {"asset_summary": {"total_value_usd": 1900.0}, "holdings": [
        {"investment_code": "MU", "investment": "Micron", "total_units": 12,
         "invested_value_usd": 1000, "current_value_usd": 1300, "one_day_change_usd": 10},
        {"investment_code": "NVDA", "investment": "Nvidia", "total_units": 3,
         "invested_value_usd": 500, "current_value_usd": 600, "one_day_change_usd": 5}]}
    (tmp_path / "snap.json").write_text(json.dumps(snap))
    args = Namespace(base_dir=str(base), run_dir=str(rd), snapshot_json=str(tmp_path / "snap.json"),
                     live_quotes_json=None, usdinr=usdinr, wallet_usd=100.0, aggregate_usd=None,
                     market_session="pre-open", gate_classification="CALM", gate_reason="",
                     macro_json=None, benchmarks_json=None, ts=None)
    return _emit(smm.cmd_build_holdings, args), base, rd


def test_build_holdings_emits_qty_changes_and_aggregate_source(tmp_path):
    out, base, rd = _holdings(tmp_path, [{"ticker": "MU", "qty": 10}, {"ticker": "FSLR", "qty": 5}])
    assert {q["ticker"]: q["qty_diff"] for q in out["qty_changes"]} == {"MU": 2.0, "NVDA": 3.0, "FSLR": -5.0}
    assert out["aggregate_source"] == "snapshot" and out["next_step"]
    assert json.loads((rd / "holdings.json").read_text())["qty_changes"]


def _book(base, rd):
    return _emit(smm.cmd_book, Namespace(base_dir=str(base), run_dir=str(rd), lots=None))


def test_book_gate_flags_an_implausible_fx_rate(tmp_path):
    _, base, rd = _holdings(tmp_path, [{"ticker": "MU", "qty": 12}, {"ticker": "NVDA", "qty": 3}],
                            usdinr=150.0)
    out = _book(base, rd)
    assert out["persist_safe"] is False
    assert any("USD/INR" in b for b in out["reconciliation"]["breaches"])


def test_book_gate_flags_an_unexplained_total_book_jump(tmp_path):
    _, base, rd = _holdings(tmp_path, [{"ticker": "MU", "qty": 12}, {"ticker": "NVDA", "qty": 3}],
                            ledger_rows=["2026-09-13T09:00:00+00:00,quick,5000,88,0,1,1,,,,,ok,x"])
    out = _book(base, rd)
    assert out["persist_safe"] is False
    assert any("moved" in b for b in out["reconciliation"]["breaches"])


def test_book_gate_accepts_a_move_explained_by_qty_changes(tmp_path):
    _, base, rd = _holdings(tmp_path, [{"ticker": "MU", "qty": 30}],
                            ledger_rows=["2026-09-13T09:00:00+00:00,quick,5000,88,0,1,1,,,,,ok,x"])
    out = _book(base, rd)
    assert not any("moved" in b for b in out["reconciliation"].get("breaches", []))


def _ledger_args(base, **kw):
    d = dict(base_dir=str(base), ts=None, mode="quick", value_usd=1.0, usdinr=88.0, wallet_usd=1.0,
             spx=1.0, ndx=1.0, smh=None, smh_asof=None, est_net_flows_usd=None,
             external_flow_usd=None, value_trust="ok", summary="ok", briefing_file=None)
    d.update(kw)
    return Namespace(**d)


def test_append_ledger_stamps_from_the_script_clock(tmp_path):
    out = _emit(sm.cmd_append_ledger, _ledger_args(tmp_path))
    written = datetime.fromisoformat(out["ts"])
    assert abs((datetime.now(timezone.utc) - written).total_seconds()) < 120
    raw = (tmp_path / "ledger.csv").read_bytes()
    assert raw.startswith(b"ts,mode") and raw.endswith(b"\r\n") and raw.count(b"\r\n") == 2


def test_append_ledger_refuses_a_future_timestamp(tmp_path):
    future = (datetime.now(timezone.utc) + timedelta(hours=10)).isoformat(timespec="seconds")
    with pytest.raises(SystemExit):
        _emit(sm.cmd_append_ledger, _ledger_args(tmp_path, ts=future))
    assert not (tmp_path / "ledger.csv").exists()


def test_sync_decisions_rolls_back_a_failing_decision_and_does_not_stamp(tmp_path, monkeypatch):
    (tmp_path / "proposals.json").write_text(json.dumps({"proposals": [{"id": "P-1", "status": "open"}],
                                                        "scorecard": {}}))
    (tmp_path / "state.json").write_text(json.dumps({"k": 1}))
    (tmp_path / "page.html").write_text("<html></html>")
    monkeypatch.setattr(smm, "_extract_decisions", lambda html: [
        {"surface": "catalyst", "element_id": "c1", "decision": "priced_in",
         "headline": "h", "date": "2026-09-13"},
        {"surface": "proposal", "element_id": "P-1", "decision": "reject", "reason": "no"}])

    def boom(props, pid, reason, actor=None):
        props[0]["status"] = "dismissed_by_user"
        raise RuntimeError("mid-edit failure")

    monkeypatch.setattr(smm, "dismiss_proposal_core", boom)
    out = _emit(smm.cmd_sync_decisions, Namespace(base_dir=str(tmp_path),
                                                  html_file=str(tmp_path / "page.html"),
                                                  today="2026-09-14"))
    assert out["ok"] is False and out["errors"][0]["rolled_back"]
    assert json.loads((tmp_path / "proposals.json").read_text())["proposals"][0]["status"] == "open"
    st = json.loads((tmp_path / "state.json").read_text())
    assert st["catalyst_suppressed"][0]["headline"] == "h"
    assert "dashboard_last_synced_ts" not in st


def test_sync_decisions_reads_records_file_the_same_way_as_html(tmp_path):
    # records-file (added 2026-09-16, replaces WebFetching the whole dashboard page) feeds the
    # same per-decision loop as --html-file -- prove it reconciles a proposal reject identically.
    (tmp_path / "proposals.json").write_text(json.dumps({"proposals": [{"id": "P-1", "status": "open"}],
                                                        "scorecard": {}}))
    (tmp_path / "state.json").write_text(json.dumps({"k": 1}))
    records = tmp_path / "records.json"
    records.write_text(json.dumps([
        {"id": "abc123", "surface": "proposal", "element_id": "P-1", "decision": "reject",
         "reason": "no longer relevant"}]))
    out = _emit(smm.cmd_sync_decisions, Namespace(base_dir=str(tmp_path),
                                                  records_file=str(records), html_file=None,
                                                  today="2026-09-16"))
    assert out["ok"] is True
    assert json.loads((tmp_path / "proposals.json").read_text())["proposals"][0]["status"] == "dismissed_by_user"


def test_decisions_from_records_file_tolerates_missing_or_malformed(tmp_path):
    assert smm._decisions_from_records_file(str(tmp_path / "nope.json")) == []
    bad = tmp_path / "bad.json"
    bad.write_text("not json")
    assert smm._decisions_from_records_file(str(bad)) == []
    not_a_list = tmp_path / "obj.json"
    not_a_list.write_text(json.dumps({"surface": "x"}))
    assert smm._decisions_from_records_file(str(not_a_list)) == []


def _trades(tmp_path):
    (tmp_path / "trades.json").write_text(json.dumps({"trades": [
        {"ticker": "MU", "date": "2026-09-10", "qty_change": 2, "reason": "UNCAPTURED",
         "message_id": "m1", "price_source": "email_confirmed"},
        {"ticker": "MU", "date": "2026-09-10", "qty_change": -1, "reason": "stop-loss",
         "message_id": "m2", "price_source": "email_confirmed"}]}))


def _tr_args(tmp_path, **kw):
    d = dict(base_dir=str(tmp_path), ticker="mu", date="2026-09-10", side=None, message_id=None,
             reason="dollar-cost-averaging", notes="weekly DCA", overwrite=False)
    d.update(kw)
    return Namespace(**d)


def test_trade_rationale_updates_only_uncaptured_rows(tmp_path):
    _trades(tmp_path)
    out = _emit(sl.cmd_trade_rationale, _tr_args(tmp_path))
    t = json.loads((tmp_path / "trades.json").read_text())["trades"]
    assert out["updated"] == 1
    assert t[0]["reason"] == "dollar-cost-averaging" and t[0]["notes"] == "weekly DCA"
    assert t[1]["reason"] == "stop-loss"


def test_trade_rationale_refuses_when_nothing_matches_and_writes_nothing(tmp_path):
    _trades(tmp_path)
    before = (tmp_path / "trades.json").read_bytes()
    with pytest.raises(SystemExit):
        _emit(sl.cmd_trade_rationale, _tr_args(tmp_path, date="2026-01-01"))
    assert (tmp_path / "trades.json").read_bytes() == before


def test_validate_flags_trades_without_provenance(tmp_path):
    (tmp_path / "trades.json").write_text(json.dumps({"trades": [{"ticker": "X", "date": "2026-01-02"}]}))
    assert "TRADE PROVENANCE" in sm.validate_trade_provenance(str(tmp_path))[0]


def test_retire_decision_is_recorded_as_the_desks_withdrawal_not_a_user_override(tmp_path):
    # Retire confirms the DESK's own recommendation (smith_validity verdict), so it must land as
    # dismissed_by_desk -- counted as a strategist miss -- never as the user's taste.
    (tmp_path / "proposals.json").write_text(json.dumps({"proposals": [
        {"id": "P-346", "status": "open"}, {"id": "P-2", "status": "open"}], "scorecard": {}}))
    (tmp_path / "state.json").write_text(json.dumps({"k": 1}))
    records = tmp_path / "records.json"
    records.write_text(json.dumps([
        {"id": "a", "surface": "proposal", "element_id": "P-346", "decision": "retire"},
        {"id": "b", "surface": "proposal", "element_id": "P-2", "decision": "reject"}]))
    out = _emit(smm.cmd_sync_decisions, Namespace(base_dir=str(tmp_path), records_file=str(records),
                                                  html_file=None, today="2026-09-19"))
    assert out["ok"] is True
    props = {p["id"]: p for p in json.loads((tmp_path / "proposals.json").read_text())["proposals"]}
    assert props["P-346"]["status"] == "dismissed_by_desk"
    assert props["P-346"]["dismiss_reason"]
    assert props["P-2"]["status"] == "dismissed_by_user"
