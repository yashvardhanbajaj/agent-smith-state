"""Unit tests for the 9 functions extracted from cmd_proposals (smith_lifecycle.py) in the
2026-09 god-function refactor.
"""
from datetime import date

from conftest import make_proposal

import smith_lifecycle as sl


def breach(edge, drift_pt=5.0):
    def _b(cluster, bucket):
        return {"breach_edge": edge, "drift_pt": drift_pt}
    return _b


# ---------------------------------------------------------------------------
# _assign_stable_proposal_ids
# ---------------------------------------------------------------------------

class TestAssignStableProposalIds:
    def test_assigns_sequential_ids_to_new_proposals(self):
        props = [make_proposal(id=""), make_proposal(id="")]
        sl._assign_stable_proposal_ids(props)
        assert props[0]["id"] == "P-001"
        assert props[1]["id"] == "P-002"

    def test_never_reassigns_or_reuses_an_existing_id(self):
        props = [make_proposal(id="P-005"), make_proposal(id="")]
        sl._assign_stable_proposal_ids(props)
        assert props[0]["id"] == "P-005"
        assert props[1]["id"] == "P-006"  # continues from the max seen, not from 1


# ---------------------------------------------------------------------------
# _backfill_proposal_ticker_and_bucket
# ---------------------------------------------------------------------------

class TestBackfillProposalTickerAndBucket:
    def test_backfills_missing_ticker_from_action_text(self):
        props = [make_proposal(ticker=None, action="Trim CEG (rotation funding leg)")]
        del props[0]["ticker"]
        sl._backfill_proposal_ticker_and_bucket(props, sl._proposal_infer_ticker, sl._proposal_direction)
        assert props[0]["ticker"] == "CEG"
        assert "backfilled" in props[0]["note"]

    def test_sets_direction_bucket_from_action(self):
        props = [make_proposal(action="Buy NVDA", direction_bucket=None)]
        del props[0]["direction_bucket"]
        sl._backfill_proposal_ticker_and_bucket(props, sl._proposal_infer_ticker, sl._proposal_direction)
        assert props[0]["direction_bucket"] == "BUY"

    def test_does_not_overwrite_existing_ticker(self):
        props = [make_proposal(ticker="AAA", action="Trim BBB")]
        sl._backfill_proposal_ticker_and_bucket(props, sl._proposal_infer_ticker, sl._proposal_direction)
        assert props[0]["ticker"] == "AAA"


# ---------------------------------------------------------------------------
# _dedupe_expire_void_proposals
# ---------------------------------------------------------------------------

class TestDedupeExpireVoidProposals:
    def test_merges_two_open_proposals_for_the_same_ticker_direction(self):
        props = [
            make_proposal(id="P-001", ticker="AAA", action="Trim AAA", date="2026-08-20T09:00",
                          direction_bucket="TRIM"),
            make_proposal(id="P-002", ticker="AAA", action="Trim AAA more", date="2026-08-22T09:00",
                          direction_bucket="TRIM"),
        ]
        to_supersede = sl._dedupe_expire_void_proposals(
            props, today_date=date(2026, 8, 22), current_tickers={"AAA"},
            direction=sl._proposal_direction, parse_date=sl._proposal_parse_date,
            parse_datetime=sl._proposal_parse_datetime)
        assert to_supersede == {0}  # the earlier occurrence loses to the fresher one
        assert props[1]["repeat_count"] == 2
        assert len(props[1]["history"]) == 1

    def test_expires_a_proposal_older_than_seven_days(self):
        props = [make_proposal(date="2026-08-01T09:00", ticker="AAA")]
        to_supersede = sl._dedupe_expire_void_proposals(
            props, today_date=date(2026, 8, 20), current_tickers={"AAA"},
            direction=sl._proposal_direction, parse_date=sl._proposal_parse_date,
            parse_datetime=sl._proposal_parse_datetime)
        assert to_supersede == {0}
        assert "auto-expired" in props[0]["note"]

    def test_voids_a_trim_whose_position_has_been_exited(self):
        props = [make_proposal(date="2026-08-20T09:00", ticker="AAA", direction_bucket="TRIM")]
        to_supersede = sl._dedupe_expire_void_proposals(
            props, today_date=date(2026, 8, 20), current_tickers=set(),  # AAA no longer held
            direction=sl._proposal_direction, parse_date=sl._proposal_parse_date,
            parse_datetime=sl._proposal_parse_datetime)
        assert to_supersede == {0}
        assert "auto-voided" in props[0]["note"]

    def test_a_fresh_buy_for_an_unheld_ticker_is_not_voided(self):
        props = [make_proposal(date="2026-08-20T09:00", ticker="ZZZ", action="Buy ZZZ",
                               direction_bucket="BUY")]
        to_supersede = sl._dedupe_expire_void_proposals(
            props, today_date=date(2026, 8, 20), current_tickers=set(),
            direction=sl._proposal_direction, parse_date=sl._proposal_parse_date,
            parse_datetime=sl._proposal_parse_datetime)
        assert to_supersede == set()

    def test_closed_proposals_are_untouched(self):
        props = [make_proposal(status="dismissed_by_user", date="2026-01-01T09:00", ticker="AAA")]
        to_supersede = sl._dedupe_expire_void_proposals(
            props, today_date=date(2026, 8, 20), current_tickers=set(),
            direction=sl._proposal_direction, parse_date=sl._proposal_parse_date,
            parse_datetime=sl._proposal_parse_datetime)
        assert to_supersede == set()


# ---------------------------------------------------------------------------
# _classify_voided_proposals
# ---------------------------------------------------------------------------

class TestClassifyVoidedProposals:
    def test_marks_superseded_and_splits_today_vs_stale(self):
        props = [
            make_proposal(id="P-001", date="2026-08-20T09:00"),  # created today
            make_proposal(id="P-002", date="2026-08-01T09:00"),  # stale
        ]
        voided_today, voided_stale, warnings = sl._classify_voided_proposals(
            props, to_supersede={0, 1}, today_date=date(2026, 8, 20))
        assert props[0]["status"] == "superseded"
        assert props[1]["status"] == "superseded"
        assert len(voided_today) == 1 and len(voided_stale) == 1
        assert any("G60" in w for w in warnings)

    def test_no_g60_warning_when_nothing_voided_today(self):
        props = [make_proposal(id="P-001", date="2026-08-01T09:00")]
        voided_today, voided_stale, warnings = sl._classify_voided_proposals(
            props, to_supersede={0}, today_date=date(2026, 8, 20))
        assert voided_today == []
        assert warnings == []


# ---------------------------------------------------------------------------
# _score_proposal_priority
# ---------------------------------------------------------------------------

class TestScoreProposalPriority:
    def test_over_cap_position_scores_plus_two(self, no_breach):
        pr = make_proposal(ticker="AAA", direction_bucket="TRIM")
        risk_by_ticker = {"AAA": {"cluster": "Compute", "over_cap": True, "cap_multiple": 1.4}}
        sl._score_proposal_priority(
            pr, risk_by_ticker, no_breach, cash_short=False, cash_excess=False,
            cash_pct=10.0, cash_band=[5, 15], stretch_by_ticker={}, derisk={},
            rotation_by_ticker={}, hit_rates_7d={}, trigger_live_sets={}, trigger_rows={},
            trigger_pairs={}, state_sector_map={}, cluster_breach={}, total_book_usd=100000.0)
        assert pr["priority_score"] == 2
        assert pr["priority"] == "MEDIUM"
        assert any("ATR risk cap" in r for r in pr["priority_reasons"])

    def test_no_signals_scores_a_discretionary_buy_negative(self, no_breach):
        pr = make_proposal(ticker="ZZZ", action="Buy ZZZ", direction_bucket="BUY")
        sl._score_proposal_priority(
            pr, {}, no_breach, cash_short=False, cash_excess=False, cash_pct=10.0,
            cash_band=[5, 15], stretch_by_ticker={}, derisk={}, rotation_by_ticker={},
            hit_rates_7d={}, trigger_live_sets={}, trigger_rows={}, trigger_pairs={},
            state_sector_map={}, cluster_breach={}, total_book_usd=100000.0)
        assert pr["priority_score"] == -1
        assert pr["priority"] == "LOW"
        assert "discretionary add" in pr["priority_reasons"][-1]

    def test_live_trigger_exempts_high_from_the_medium_cap(self, no_breach):
        pr = make_proposal(ticker="AAA", direction_bucket="TRIM", trigger_type="thesis_break")
        risk_by_ticker = {"AAA": {"cluster": "Compute", "over_cap": True, "cap_multiple": 1.4}}
        trigger_live_sets = {"thesis_break": {"AAA"}}
        trigger_rows = {"thesis_break": {"AAA": {"reasons": ["broken thesis"]}}}
        sl._score_proposal_priority(
            pr, risk_by_ticker, no_breach, cash_short=False, cash_excess=False,
            cash_pct=10.0, cash_band=[5, 15], stretch_by_ticker={}, derisk={},
            rotation_by_ticker={}, hit_rates_7d={}, trigger_live_sets=trigger_live_sets,
            trigger_rows=trigger_rows, trigger_pairs={}, state_sector_map={}, cluster_breach={},
            total_book_usd=100000.0)
        # over_cap (+2) + live trigger (+3) = 5 -> HIGH, and a live trigger means it's NOT capped
        assert pr["priority_score"] == 5
        assert pr["priority"] == "HIGH"

    def test_high_without_a_live_trigger_is_capped_to_medium(self, no_breach):
        pr = make_proposal(ticker="AAA", direction_bucket="TRIM", repeat_count=2)
        risk_by_ticker = {"AAA": {"cluster": "Compute", "over_cap": True, "cap_multiple": 1.4}}
        sl._score_proposal_priority(
            pr, risk_by_ticker, breach("over"), cash_short=True, cash_excess=False,
            cash_pct=2.0, cash_band=[5, 15], stretch_by_ticker={}, derisk={},
            rotation_by_ticker={}, hit_rates_7d={}, trigger_live_sets={}, trigger_rows={},
            trigger_pairs={}, state_sector_map={}, cluster_breach={}, total_book_usd=100000.0)
        # over_cap(+2) + directional cluster breach(+2) + cash short(+2) + repeat(+1) = 7 -> would
        # be HIGH on raw score, but no live trigger caps it to MEDIUM.
        assert pr["priority_score"] == 7
        assert pr["priority"] == "MEDIUM"
        assert any("capped at MEDIUM" in r for r in pr["priority_reasons"])

    def test_honest_sizing_computes_cure_pct_on_a_trim(self, no_breach):
        pr = make_proposal(ticker="AAA", direction_bucket="TRIM", size_usd=100.0)
        risk_by_ticker = {"AAA": {"cluster": "Compute", "over_cap": True, "cap_multiple": 1.4,
                                  "headroom_usd": -1000.0}}
        sl._score_proposal_priority(
            pr, risk_by_ticker, no_breach, cash_short=False, cash_excess=False,
            cash_pct=10.0, cash_band=[5, 15], stretch_by_ticker={}, derisk={},
            rotation_by_ticker={}, hit_rates_7d={}, trigger_live_sets={}, trigger_rows={},
            trigger_pairs={}, state_sector_map={}, cluster_breach={}, total_book_usd=100000.0)
        assert pr["full_cure_usd"] == 1000.0
        assert pr["cure_basis"] == "risk cap"
        assert pr["cure_pct"] == 10.0
        assert "tranche_note" in pr


# ---------------------------------------------------------------------------
# _check_condition_based_retirement
# ---------------------------------------------------------------------------

class TestCheckConditionBasedRetirement:
    def test_overbought_distribution_retires_once_rsi_cools(self, no_breach):
        pr = make_proposal(ticker="AAA", direction_bucket="TRIM", trigger_type="overbought_distribution")
        result = sl._check_condition_based_retirement(
            pr, today_date=date(2026, 8, 20), risk_by_ticker={}, directional_breach=no_breach,
            current_tickers={"AAA"}, drift={}, trig_rsi={"AAA": 55.0}, trig_abs={"AAA": 5.0},
            trigger_live_sets={}, state_thesis={}, derisk={}, cluster_breach={},
            rotation_by_ticker={}, hit_rates_7d={}, parse_date=sl._proposal_parse_date,
            hold_max_age_days=2)
        assert result is not None
        assert pr["status"] == "auto_retired"
        assert "RSI14 has cooled" in pr["retired_reason"]

    def test_overbought_distribution_stays_open_while_rsi_still_hot(self, no_breach):
        pr = make_proposal(ticker="AAA", direction_bucket="TRIM", trigger_type="overbought_distribution")
        result = sl._check_condition_based_retirement(
            pr, today_date=date(2026, 8, 20), risk_by_ticker={}, directional_breach=no_breach,
            current_tickers={"AAA"}, drift={}, trig_rsi={"AAA": 75.0}, trig_abs={"AAA": 5.0},
            trigger_live_sets={}, state_thesis={}, derisk={}, cluster_breach={},
            rotation_by_ticker={}, hit_rates_7d={}, parse_date=sl._proposal_parse_date,
            hold_max_age_days=2)
        assert result is None
        assert pr["status"] == "open"

    def test_stale_rsi_cache_keeps_it_open_rather_than_guessing(self, no_breach):
        pr = make_proposal(ticker="AAA", direction_bucket="TRIM", trigger_type="overbought_distribution")
        result = sl._check_condition_based_retirement(
            pr, today_date=date(2026, 8, 20), risk_by_ticker={}, directional_breach=no_breach,
            current_tickers={"AAA"}, drift={}, trig_rsi={}, trig_abs={},
            trigger_live_sets={}, state_thesis={}, derisk={}, cluster_breach={},
            rotation_by_ticker={}, hit_rates_7d={}, parse_date=sl._proposal_parse_date,
            hold_max_age_days=2)
        assert result is None

    def test_generic_trim_retires_when_neither_trigger_is_live(self, no_breach):
        pr = make_proposal(ticker="AAA", direction_bucket="TRIM")
        result = sl._check_condition_based_retirement(
            pr, today_date=date(2026, 8, 20), risk_by_ticker={"AAA": {"over_cap": False}},
            directional_breach=no_breach, current_tickers={"AAA"}, drift={}, trig_rsi={},
            trig_abs={}, trigger_live_sets={}, state_thesis={}, derisk={}, cluster_breach={},
            rotation_by_ticker={}, hit_rates_7d={}, parse_date=sl._proposal_parse_date,
            hold_max_age_days=2)
        assert result is not None
        assert "neither trigger is live" in pr["retired_reason"]

    def test_generic_trim_stays_open_while_over_cap(self, no_breach):
        pr = make_proposal(ticker="AAA", direction_bucket="TRIM")
        result = sl._check_condition_based_retirement(
            pr, today_date=date(2026, 8, 20), risk_by_ticker={"AAA": {"over_cap": True}},
            directional_breach=no_breach, current_tickers={"AAA"}, drift={}, trig_rsi={},
            trig_abs={}, trigger_live_sets={}, state_thesis={}, derisk={}, cluster_breach={},
            rotation_by_ticker={}, hit_rates_7d={}, parse_date=sl._proposal_parse_date,
            hold_max_age_days=2)
        assert result is None

    def test_buy_retires_once_the_position_is_initiated(self, no_breach):
        pr = make_proposal(ticker="ZZZ", action="Initiate ZZZ", direction_bucket="BUY")
        result = sl._check_condition_based_retirement(
            pr, today_date=date(2026, 8, 20), risk_by_ticker={}, directional_breach=no_breach,
            current_tickers={"ZZZ"}, drift={}, trig_rsi={}, trig_abs={},
            trigger_live_sets={}, state_thesis={}, derisk={}, cluster_breach={},
            rotation_by_ticker={}, hit_rates_7d={}, parse_date=sl._proposal_parse_date,
            hold_max_age_days=2)
        assert result is not None
        assert "already exists" in pr["retired_reason"]

    def test_stop_hold_never_expires_on_age_alone(self, no_breach):
        pr = make_proposal(ticker="AAA", action="Set hard stop on AAA @ $10", direction_bucket="HOLD",
                           date="2026-01-01T09:00")
        result = sl._check_condition_based_retirement(
            pr, today_date=date(2026, 8, 20), risk_by_ticker={}, directional_breach=no_breach,
            current_tickers={"AAA"}, drift={}, trig_rsi={}, trig_abs={},
            trigger_live_sets={}, state_thesis={}, derisk={}, cluster_breach={},
            rotation_by_ticker={}, hit_rates_7d={}, parse_date=sl._proposal_parse_date,
            hold_max_age_days=2)
        assert result is None

    def test_ordinary_hold_expires_after_max_age(self, no_breach):
        pr = make_proposal(ticker="AAA", action="Hold fire on AAA until Q print", direction_bucket="HOLD",
                           date="2026-01-01T09:00")
        result = sl._check_condition_based_retirement(
            pr, today_date=date(2026, 8, 20), risk_by_ticker={}, directional_breach=no_breach,
            current_tickers={"AAA"}, drift={}, trig_rsi={}, trig_abs={},
            trigger_live_sets={}, state_thesis={}, derisk={}, cluster_breach={},
            rotation_by_ticker={}, hit_rates_7d={}, parse_date=sl._proposal_parse_date,
            hold_max_age_days=2)
        assert result is not None
        assert "time-bound" in pr["retired_reason"]

    def test_restatement_backstop_fires_at_three_repeats(self, no_breach):
        pr = make_proposal(ticker="AAA", direction_bucket="TRIM", repeat_count=3)
        result = sl._check_condition_based_retirement(
            pr, today_date=date(2026, 8, 20), risk_by_ticker={"AAA": {"over_cap": True}},
            directional_breach=no_breach, current_tickers={"AAA"}, drift={}, trig_rsi={},
            trig_abs={}, trigger_live_sets={}, state_thesis={}, derisk={}, cluster_breach={},
            rotation_by_ticker={}, hit_rates_7d={}, parse_date=sl._proposal_parse_date,
            hold_max_age_days=2)
        # over_cap alone would keep it open, but the 3x-restatement backstop overrides that.
        assert result is not None
        assert "0-for-17" in pr["retired_reason"]

    def test_paired_rotation_leg_is_never_retired_here(self, no_breach):
        pr = make_proposal(ticker="AAA", direction_bucket="SELL", trigger_type="profit_rotation",
                           pair_id="profit_rotation-AAA-BBB")
        result = sl._check_condition_based_retirement(
            pr, today_date=date(2026, 8, 20), risk_by_ticker={"AAA": {"over_cap": False}},
            directional_breach=no_breach, current_tickers={"AAA"}, drift={}, trig_rsi={},
            trig_abs={}, trigger_live_sets={}, state_thesis={}, derisk={}, cluster_breach={},
            rotation_by_ticker={}, hit_rates_7d={}, parse_date=sl._proposal_parse_date,
            hold_max_age_days=2)
        assert result is None  # handled entirely by _retire_orphaned_rotation_legs instead


# ---------------------------------------------------------------------------
# _retire_orphaned_rotation_legs
# ---------------------------------------------------------------------------

class TestRetireOrphanedRotationLegs:
    def test_retires_a_leg_whose_pair_is_no_longer_live(self):
        props = [make_proposal(id="P-001", ticker="AAA", direction_bucket="SELL",
                               pair_id="profit_rotation-AAA-BBB")]
        retired = []
        sl._retire_orphaned_rotation_legs(props, trigger_pairs={}, today_date=date(2026, 8, 20),
                                          retired=retired)
        assert props[0]["status"] == "auto_retired"
        assert len(retired) == 1

    def test_keeps_both_legs_open_while_the_pair_is_still_live(self):
        props = [
            make_proposal(id="P-001", ticker="AAA", direction_bucket="SELL",
                          pair_id="profit_rotation-AAA-BBB"),
            make_proposal(id="P-002", ticker="BBB", direction_bucket="BUY",
                          pair_id="profit_rotation-AAA-BBB"),
        ]
        retired = []
        sl._retire_orphaned_rotation_legs(
            props, trigger_pairs={"profit_rotation-AAA-BBB": {}}, today_date=date(2026, 8, 20),
            retired=retired)
        assert props[0]["status"] == "open" and props[1]["status"] == "open"
        assert retired == []

    def test_none_trigger_pairs_is_a_no_op(self):
        props = [make_proposal(id="P-001", pair_id="profit_rotation-AAA-BBB")]
        retired = []
        sl._retire_orphaned_rotation_legs(props, trigger_pairs=None, today_date=date(2026, 8, 20),
                                          retired=retired)
        assert props[0]["status"] == "open"


# ---------------------------------------------------------------------------
# _apply_live_rejustification
# ---------------------------------------------------------------------------

class TestApplyLiveRejustification:
    def test_flags_large_price_drift_since_proposal(self, no_breach):
        pr = make_proposal(ticker="AAA", price_at_proposal=100.0)
        sl._apply_live_rejustification(pr, {"AAA": 115.0}, {}, no_breach, date(2026, 8, 20))
        assert pr["price_drift_pct"] == 15.0
        assert any("re-size before acting" in f for f in pr["review_flags"])

    def test_small_price_drift_is_not_flagged(self, no_breach):
        pr = make_proposal(ticker="AAA", price_at_proposal=100.0)
        sl._apply_live_rejustification(pr, {"AAA": 103.0}, {}, no_breach, date(2026, 8, 20))
        assert pr["review_flags"] == []

    def test_unverified_evidence_only_is_flagged_g58(self, no_breach):
        pr = make_proposal(ticker="AAA", evidence_quality={"verified": 0, "unverified": 2, "computed": 0})
        sl._apply_live_rejustification(pr, {}, {}, no_breach, date(2026, 8, 20))
        assert any("G58" in f for f in pr["review_flags"])

    def test_no_priority_reasons_gets_the_honest_default(self, no_breach):
        pr = make_proposal(ticker="AAA", priority_reasons=[])
        sl._apply_live_rejustification(pr, {}, {}, no_breach, date(2026, 8, 20))
        assert pr["still_valid_because"] == ["no active structural trigger -- kept open on the strategist's judgement, not a breach"]

    def test_retires_when_matches_trigger_type(self, no_breach):
        pr = make_proposal(ticker="AAA", trigger_type="oversold_reversion")
        sl._apply_live_rejustification(pr, {}, {}, no_breach, date(2026, 8, 20))
        assert "RSI14 recovers above" in pr["retires_when"]

    def test_retires_when_none_for_a_trim_with_no_live_conditions(self, no_breach):
        pr = make_proposal(ticker="AAA", direction_bucket="TRIM")
        sl._apply_live_rejustification(pr, {}, {"AAA": {"over_cap": False}}, no_breach, date(2026, 8, 20))
        assert pr["retires_when"] is None


# ---------------------------------------------------------------------------
# _compute_stacking_warnings
# ---------------------------------------------------------------------------

class TestComputeStackingWarnings:
    def test_flags_a_sell_stack_above_the_warn_threshold(self):
        props = [
            make_proposal(id="P-164", ticker="MSFT", status="accepted_by_user",
                          direction_bucket="SELL", size_usd=437.92),
            make_proposal(id="P-201", ticker="MSFT", status="open",
                          direction_bucket="SELL", size_usd=305.96),
        ]
        risk_by_ticker = {"MSFT": {"market_value_usd": 1019.88}}
        warnings = sl._compute_stacking_warnings(props, risk_by_ticker)
        assert len(warnings) == 1
        w = warnings[0]
        assert w["severity"] == "high"
        assert w["combined_pct_of_position"] == round(100.0 * 743.88 / 1019.88, 1)
        assert props[1]["stacks_on"]["accepted_id"] == "P-164"

    def test_no_stack_when_sides_differ(self):
        props = [
            make_proposal(id="P-001", ticker="AAA", status="accepted_by_user",
                          direction_bucket="SELL", size_usd=100.0),
            make_proposal(id="P-002", ticker="AAA", status="open",
                          direction_bucket="BUY", size_usd=100.0),
        ]
        warnings = sl._compute_stacking_warnings(props, {"AAA": {"market_value_usd": 1000.0}})
        assert warnings == []

    def test_stale_stacks_on_field_is_cleared_each_run(self):
        props = [make_proposal(id="P-001", ticker="AAA", status="open", direction_bucket="SELL",
                               stacks_on={"accepted_id": "P-000"})]
        sl._compute_stacking_warnings(props, {})
        assert "stacks_on" not in props[0]

    def test_no_accepted_proposals_produces_no_warnings(self):
        props = [make_proposal(id="P-001", ticker="AAA", status="open", direction_bucket="SELL")]
        warnings = sl._compute_stacking_warnings(props, {"AAA": {"market_value_usd": 1000.0}})
        assert warnings == []
