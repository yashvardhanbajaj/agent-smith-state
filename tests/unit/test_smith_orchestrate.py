"""dispatch-plan, triggers-diff, postflight."""
import json
import os
from argparse import Namespace

import pytest

import smith_orchestrate as so
import smith_state as ss

CALM_MI = {"us10y_change_pts": 0.01, "vix": 15.0, "smh_change_pct": 0.5,
           "asia": {"kospi_change_pct": 0.2, "taiex_change_pct": -0.4}, "spx": 7600.0, "ndx": 26000.0, "smh": 570.0}


def _run(tmp_path, mi=None, triggers=None, session=None, state=None, ladder=None, freshness=None,
         held=("MU", "NVDA"), ledger_rows=(), name="2026-09-14-0900Z"):
    base = tmp_path / "base"
    rd = base / "runs" / name
    rd.mkdir(parents=True, exist_ok=True)
    (rd / "market_inputs.json").write_text(json.dumps(mi if mi is not None else CALM_MI))
    (rd / "compute_triggers.json").write_text(json.dumps(triggers or {"correction_state": "none"}))
    (rd / "compute_session.json").write_text(json.dumps(session or {"gate_classification": "STABILIZING",
                                                                    "cluster_moves_pct": {}}))
    (rd / "holdings.json").write_text(json.dumps({"usdinr": 95.0, "holdings_inr": [
        {"ticker": t, "qty": 1, "weight_pct": 100 / len(held)} for t in held]}))
    if ladder is not None:
        (rd / "compute_ladder.json").write_text(json.dumps(ladder))
    if freshness is not None:
        (rd / "compute_freshness.json").write_text(json.dumps(freshness))
    (base / "state.json").write_text(json.dumps(state or {"data_cache": {}}))
    hdr = "ts,mode,value_usd,usdinr,wallet_usd,spx,ndx,smh,smh_asof,est_net_flows_usd,external_flow_usd,value_trust,notes\r\n"
    (base / "ledger.csv").write_text(hdr + "".join(r + "\r\n" for r in ledger_rows))
    return base, rd


def _plan(base, rd, mode="quick", asks=(), today="2026-09-14"):
    return so.dispatch_plan(str(base), str(rd), mode, asks, today)


# --- dispatch-plan -------------------------------------------------------------------------------
def test_calm_quick_run_is_signals_and_strategist_only(tmp_path):
    p = _plan(*_run(tmp_path))
    assert set(p["agents"]) == {"signals", "strategist"}
    assert "thesis" in p["skipped"] and "watchlist" in p["skipped"]


def test_thesis_fires_only_for_a_live_trigger_on_a_held_name(tmp_path):
    p = _plan(*_run(tmp_path, triggers={"oversold_reversion": [{"ticker": "AMD"}]}))
    assert "thesis" not in p["agents"]
    p = _plan(*_run(tmp_path, triggers={"catalyst_threat": [{"ticker": "MU"}]}))
    assert "thesis" in p["agents"] and p["agents"]["thesis"]["wave"] == 2


@pytest.mark.parametrize("patch,fires", [
    ({"us10y_change_pts": 0.119}, False), ({"us10y_change_pts": -0.12}, True),
    ({"vix": 21.9}, False), ({"vix": 22.0}, True),
])
def test_macro_trigger_boundaries(tmp_path, patch, fires):
    p = _plan(*_run(tmp_path, mi=dict(CALM_MI, **patch)))
    assert ("scout" in p["agents"]) is fires
    if fires:
        assert p["agents"]["scout"]["mode"] == "macro_only"


@pytest.mark.parametrize("mi_patch,session,fires", [
    ({"smh_change_pct": -2.9}, None, False), ({"smh_change_pct": -3.0}, None, True),
    ({"asia": {"kospi_change_pct": -3.26}}, None, True),
    ({}, {"gate_classification": "ESCALATING", "cluster_moves_pct": {}}, True),
    ({}, {"gate_classification": "AMBIGUOUS", "cluster_moves_pct": {"AI Memory/Storage": 4.0}}, True),
])
def test_catalyst_trigger(tmp_path, mi_patch, session, fires):
    p = _plan(*_run(tmp_path, mi=dict(CALM_MI, **mi_patch), session=session))
    assert ("catalyst" in p["agents"]) is fires


def test_rebound_and_earnings_verify_fire_in_any_mode(tmp_path):
    state = {"data_cache": {"earnings_facts": {"MU": {"status": "PENDING", "reported_date": "2026-09-13"},
                                               "NVDA": {"status": "PENDING", "reported_date": "2026-09-20"}}}}
    p = _plan(*_run(tmp_path, triggers={"correction_state": "correction"}, state=state))
    assert "rebound" in p["agents"]
    assert p["agents"]["earnings"]["mode"] == "verify_only" and p["agents"]["earnings"]["tickers"] == ["MU"]
    assert "thesis" in p["agents"]


def test_deep_roster_and_monthly_stagger(tmp_path):
    base, rd = _run(tmp_path, ladder={"dispatch_selected": ["cluster_semis", "cluster_optics",
                                                            "cluster_memory", "cluster_power"]})
    p = _plan(base, rd, "deep")
    assert {"signals", "thesis", "watchlist", "catalyst", "scout", "cycle", "strategist"} <= set(p["agents"])
    assert p["agents"]["scout"]["mode"] == "full" and "quality" not in p["agents"]
    clusters = [k for k in p["agents"] if k.startswith("cluster_")]
    assert len(clusters) == 3 and p["agents"]["cluster_semis"]["agent"] == "smith-cluster"
    base, rd = _run(tmp_path / "b", ledger_rows=["2026-09-07T03:00:00+00:00,deep,1,95,1,1,1,,,,,ok,x"])
    p = _plan(base, rd, "deep")
    assert "quality" in p["agents"] and "cycle" not in p["agents"]


def test_quick_never_dispatches_clusters(tmp_path):
    p = _plan(*_run(tmp_path, ladder={"dispatch_selected": ["cluster_semis"]}))
    assert not [k for k in p["agents"] if k.startswith("cluster_")]


def test_deep_earnings_window_counts_trading_days(tmp_path):
    state = {"data_cache": {"earnings_calendar": {"MU": {"date": "2026-09-21"}, "NVDA": {"date": "2026-09-22"}}}}
    p = _plan(*_run(tmp_path, state=state), "deep")                 # Mon 09-14 -> Mon 09-21 = 5 trading days
    assert "MU 2026-09-21" in p["agents"]["earnings"]["reasons"][0]
    assert "NVDA" not in p["agents"]["earnings"]["reasons"][0]


# --- triggers-diff ---------------------------------------------------------------------------------
def _sig_run(base, name, pairs, cash, gate):
    rd = base / "runs" / name
    rd.mkdir(parents=True, exist_ok=True)
    trig = {}
    for fam, t in pairs:
        trig.setdefault(fam, []).append({"ticker": t})
    (rd / "compute_triggers.json").write_text(json.dumps(trig))
    (rd / "compute_drift.json").write_text(json.dumps({"cash_pct": cash, "cash_band_pct": [5, 15]}))
    (rd / "compute_session.json").write_text(json.dumps({"gate_classification": gate}))
    return rd


def _diff(base, cur):
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        so.cmd_triggers_diff(Namespace(base_dir=str(base), run_dir=str(cur), prev=None))
    return json.loads(buf.getvalue())


def test_triggers_diff(tmp_path):
    base = tmp_path
    _sig_run(base, "2026-09-10-0331", [("oversold_reversion", "MU")], 22.5, "STABILIZING")
    _sig_run(base, "2026-09-13-0900Z", [("oversold_reversion", "MU")], 20.0, "STABILIZING")
    same = _sig_run(base, "2026-09-14-0900Z", [("oversold_reversion", "MU")], 21.0, "STABILIZING")
    d = _diff(base, same)
    assert d["changed"] is False and d["prev"].endswith("2026-09-13-0900Z")
    added = _sig_run(base, "2026-09-14-1000Z", [("oversold_reversion", "MU"), ("catalyst_threat", "NVDA")], 21.0, "STABILIZING")
    assert _diff(base, added)["added"] == [["catalyst_threat", "NVDA"]]
    cash = _sig_run(base, "2026-09-14-1100Z", [("oversold_reversion", "MU")], 12.0, "STABILIZING")
    assert "cash band above -> inside" in _diff(base, cash)["reasons"]
    gate = _sig_run(base, "2026-09-14-1200Z", [("oversold_reversion", "MU")], 12.0, "ESCALATING")
    assert any(r.startswith("gate") for r in _diff(base, gate)["reasons"])


# --- postflight --------------------------------------------------------------------------------------
def _pf(base, rd, phase, mode="quick", **kw):
    d = dict(base_dir=str(base), run_dir=str(rd), phase=phase, mode=mode, today="2026-09-14", run_id=None,
             summary="test run", briefing_file=None, external_flow_usd=None, no_ledger=False,
             no_decisions=True, no_git=True, keep_runs=10)
    d.update(kw)
    return so.postflight_commit(Namespace(**d)) if phase == "commit" else so.postflight_close(Namespace(**d))


def _pf_base(tmp_path, persist_safe=True):
    base, rd = _run(tmp_path, held=("MU",))
    (rd / "compute_book.json").write_text(json.dumps({"value_usd": 1000.0, "wallet_usd": 50.0, "pnl_pct": 3.0,
                                                      "count": 1, "persist_safe": persist_safe}))
    (rd / "compute_journal.json").write_text(json.dumps({
        "journal_updates": [{"date": "2026-09-01", "ticker": "MU", "bucket": "BREAKOUT", "verdict": "worked",
                             "outcome_7d_pct": 4.0, "_verdict_7d": "worked"}],
        "bucket_hit_rates": {"BREAKOUT": 0.5}}))
    (rd / "compute_triggers.json").write_text(json.dumps({"shadow_new": [
        {"ticker": "MU", "trigger_type": "laggard_rotation", "price_at_flag": 100}]}))
    (base / "journal.json").write_text(json.dumps({"entries": [
        {"date": "2026-09-01", "ticker": "MU", "bucket": "BREAKOUT", "verdict": "open"}]}))
    return base, rd


def test_postflight_commit_persists_everything_once(tmp_path):
    base, rd = _pf_base(tmp_path)
    out = _pf(base, rd, "commit")
    st = json.loads((base / "state.json").read_text())
    assert st["us"]["value_usd"] == 1000.0 and st["holdings"] == [{"ticker": "MU", "qty": 1, "weight_pct": 100.0}]
    assert st["data_cache"]["last_seen"]["MU"] == "2026-09-14" and st["ts"].endswith("Z")
    e = json.loads((base / "journal.json").read_text())
    assert e["entries"][0]["verdict"] == "worked" and "_verdict_7d" not in e["entries"][0]
    assert e["bucket_hit_rates"] == {"BREAKOUT": 0.5}
    assert json.loads((base / "trigger_journal.json").read_text())["entries"][0]["scored"] is False
    assert out["ledger"].get("appended") is True
    assert len((base / "ledger.csv").read_text().strip().splitlines()) == 2
    again = _pf(base, rd, "commit")                     # idempotent journals
    assert again["trigger_journal_added"] == 0


def test_postflight_commit_refuses_ledger_and_price_keys_when_unsafe(tmp_path):
    base, rd = _pf_base(tmp_path, persist_safe=False)
    out = _pf(base, rd, "commit")
    assert out["ledger"] == "skipped: persist_safe false"
    assert "us" not in json.loads((base / "state.json").read_text())


def test_postflight_close_prunes_releases_and_keeps_current(tmp_path):
    base, rd = _run(tmp_path, name="2026-09-01-0900Z")        # the OLDEST dir is the current run
    for i in range(2, 14):
        (base / "runs" / f"2026-09-{i:02d}-0900Z").mkdir()
    ss.lock_acquire(str(base), "me", run_dir=str(rd))
    out = _pf(base, rd, "close", run_id="me")
    left = sorted(os.listdir(base / "runs"))
    assert "2026-09-01-0900Z" in left and len(left) == 11
    assert out["lock"]["released"] and "git" not in out
