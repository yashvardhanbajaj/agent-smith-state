"""Open-proposal re-check (smith_validity.py, added 2026-09-19).

Built after P-346 (Trim MU) still read HIGH three sessions after the user had bought MU, the
strategist had recommended retiring it, and MU had beaten SMH by 4.5pp. Each test pins one of the
checks that would have told the dashboard so -- and the one rule that must never bend: this
module never edits or dismisses a proposal.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import smith_validity as sv


def setup(tmp_path, proposal, trades=(), triggers=None, retire=None, thesis=None, earnings=None):
    base = tmp_path
    rd = base / "runs" / "r"
    rd.mkdir(parents=True)
    (base / "state.json").write_text(json.dumps({
        "latest_run_dir": "runs/r", "thesis": thesis or {},
        "data_cache": {"earnings_calendar": earnings or {}}}))
    (base / "proposals.json").write_text(json.dumps({"proposals": [proposal]}))
    (base / "trades.json").write_text(json.dumps({"trades": list(trades)}))
    (rd / "compute_triggers.json").write_text(json.dumps(triggers or {}))
    (rd / "market_inputs.json").write_text(json.dumps({"smh": 573.0}))
    (rd / "holdings.json").write_text(json.dumps({"holdings_inr": [
        {"ticker": "MU", "qty": 2.0, "price_usd": 1017.75, "weight_pct": 6.0},
        {"ticker": "TSM", "qty": 7, "price_usd": 433.36, "weight_pct": 9.0}]}))
    if retire:
        (rd / "out_strategist.json").write_text(json.dumps(
            {"stale_proposal_retirements": {"retire_open_now": retire}}))
    return str(base)


P346 = {"id": "P-346", "ticker": "MU", "direction_bucket": "TRIM", "size_usd": 186.0,
        "price_at_proposal": 929.46, "benchmark_price_at_proposal": 545.56, "date": "2026-09-16",
        "status": "open", "priority": "HIGH", "trigger_type": "catalyst_threat",
        "retires_when": "MU no longer appears in a structural-threat factor catalyst"}


def rows(base):
    return {r["id"]: r for r in sv.check_all(base, today="2026-09-19")["rows"]}


def test_the_p346_case_reads_retire_with_every_reason(tmp_path):
    base = setup(tmp_path, P346,
                 trades=[{"ticker": "MU", "date": "2026-09-18", "qty_change": 1.0}],
                 triggers={"catalyst_threat": [{"ticker": "MU"}]},
                 retire=[{"id": "P-346", "reason": "Contradicted by the user's own +1 MU buy"}])
    r = rows(base)["P-346"]
    assert r["verdict"] == "retire" and r["effective_priority"] == "RETIRE"
    assert r["priority"] == "HIGH"                              # the stored value is untouched
    assert any("opposite of this proposal" in x for x in r["retire_because"])
    assert any("strategist recommends" in x for x in r["retire_because"])
    assert r["since"]["agree_pp"] < -4                          # MU beat SMH: against a trim
    assert r["after_trade"]["pct_of_position"] == 9.1
    assert r["after_trade"]["weight_after"] < r["after_trade"]["weight_before"]


def test_same_direction_trade_means_already_acted_on_not_contradicted(tmp_path):
    buy = dict(P346, direction_bucket="BUY", id="P-9")
    base = setup(tmp_path, buy, trades=[{"ticker": "MU", "date": "2026-09-18", "qty_change": 1.0}])
    r = rows(base)["P-9"]
    assert r["verdict"] == "retire" and r["acted_on"] and not r["contradicting_trades"]
    assert "already acted on" in r["retire_because"][0]


def test_a_trade_before_the_proposal_is_not_evidence_about_it(tmp_path):
    base = setup(tmp_path, P346, trades=[{"ticker": "MU", "date": "2026-09-10", "qty_change": 1.0}],
                 triggers={"catalyst_threat": [{"ticker": "MU"}]})
    assert not rows(base)["P-346"]["contradicting_trades"]


def test_trigger_gone_alone_is_reported_not_judged(tmp_path):
    """Phase 5 ownership split. "The trigger no longer fires on this ticker" is an objective,
    ticker-level fact, so cmd_proposals owns it (trigger_no_longer_fires -> auto_retired, and where it
    deliberately keeps a row open, e.g. a catalyst trim whose position is still over cap, validity must
    not second-guess that design). smith_validity still SHOWS the fact and that its drop-off condition
    is met; it only judges the compound built on it (see the next test)."""
    p = dict(P346, price_at_proposal=1017.75, benchmark_price_at_proposal=573.0)  # flat vs SMH
    base = setup(tmp_path, p, triggers={"catalyst_threat": [{"ticker": "TSM"}]})
    r = rows(base)["P-346"]
    assert r["trigger_state"] == "not_firing" and r["drops_off_met"] is True
    assert r["verdict"] == "valid" and r["effective_priority"] == "HIGH"
    assert r["weakened_conditions"] == [] and r["retire_conditions"] == []


def test_a_clean_live_proposal_stays_valid(tmp_path):
    p = dict(P346, price_at_proposal=1017.75, benchmark_price_at_proposal=573.0)
    base = setup(tmp_path, p, triggers={"catalyst_threat": [{"ticker": "MU"}]},
                 thesis={"MU": {"status": "watch"}})
    r = rows(base)["P-346"]
    assert r["verdict"] == "valid" and r["effective_priority"] == "HIGH"


def test_paired_trigger_rows_are_read(tmp_path):
    p = dict(P346, trigger_type="cluster_rotation", price_at_proposal=1017.75,
             benchmark_price_at_proposal=573.0)
    base = setup(tmp_path, p, triggers={"cluster_rotation": [
        {"sell": {"t": "MU"}, "buy": {"t": "TSM"}}]})
    assert rows(base)["P-346"]["trigger_state"] == "firing"


def test_earnings_soon_is_listed_against(tmp_path):
    p = dict(P346, price_at_proposal=1017.75, benchmark_price_at_proposal=573.0)
    base = setup(tmp_path, p, triggers={"catalyst_threat": [{"ticker": "MU"}]},
                 earnings={"MU": {"date": "2026-10-01"}})
    r = rows(base)["P-346"]
    assert r["earnings"] == "2026-10-01"
    assert any("earnings 2026-10-01" in x for x in r["against"])


def test_nothing_is_ever_written_to_proposals(tmp_path):
    base = setup(tmp_path, P346, retire=[{"id": "P-346", "reason": "x"}])
    before = Path(base, "proposals.json").read_text()
    sv.check_all(base, today="2026-09-19")
    assert Path(base, "proposals.json").read_text() == before


def test_session_age_counts_weekdays_not_calendar_days():
    from datetime import date
    assert sv._sessions_between(date(2026, 9, 16), date(2026, 9, 19)) == 2   # Wed -> Sat: Thu, Fri
    assert sv._sessions_between(date(2026, 9, 18), date(2026, 9, 21)) == 1   # Fri -> Mon


def test_tickers_in_reads_paired_rotation_legs():
    """Paired rotation rows nest tickers under sell_leg/buy_leg, not sell/buy.

    Regression for 2026-09-20: reading only `sell`/`buy` returned an empty set for every
    profit_rotation / cluster_rotation row, so a proposal the rotation trigger had just
    produced was scored `not_firing` on its own creating run and demoted on the dashboard.
    """
    row = {"pair_id": "cluster_rotation-GLW-LITE", "trigger_type": "cluster_rotation",
           "sell_leg": {"ticker": "GLW", "direction": "SELL", "suggested_size_usd": 135.09},
           "buy_leg": {"ticker": "LITE", "direction": "BUY", "suggested_size_usd": 135.09}}
    assert sv._tickers_in(row) == {"GLW", "LITE"}


def test_tickers_in_still_reads_flat_and_legacy_shapes():
    """The legacy `sell`/`buy` shape and plain single-ticker rows keep working."""
    assert sv._tickers_in({"ticker": "MU"}) == {"MU"}
    assert sv._tickers_in({"sell": {"ticker": "A"}, "buy": {"ticker": "B"}}) == {"A", "B"}
    assert sv._tickers_in("not a dict") == set()


def test_accepted_by_user_is_rechecked():
    """An acceptance is agreement with the reasoning at the time, not a standing order to
    execute later -- so it gets re-checked like any open card (user correction, 2026-09-20)."""
    assert "accepted_by_user" in sv.RECHECKED_STATUSES
    assert "open" in sv.RECHECKED_STATUSES
    # explicitly NOT re-checked: these are "not now" states, not agreed positions
    assert "deferred" not in sv.RECHECKED_STATUSES
    assert "watch" not in sv.RECHECKED_STATUSES
