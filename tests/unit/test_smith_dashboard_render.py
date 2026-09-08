"""Unit tests for the 24 _render_* panel functions extracted from smith_dashboard.py's build()
in the 2026-09 god-function refactor. These are HTML string builders -- the golden-master
harness (tests/verify_dashboard.sh) already proves the refactor changed nothing end-to-end;
these are lighter, targeted smoke tests: absent data renders nothing (or a stated-empty note),
minimal populated data renders without raising and contains the ticker/expected text.
"""
import smith_dashboard as sd
import smith_risk


def joined(out):
    return "".join(out)


# ---------------------------------------------------------------------------

class TestAcceptedAwaitingExecution:
    def test_empty_props_renders_nothing(self):
        assert sd._render_accepted_awaiting_execution({"proposals": []}) == []

    def test_accepted_proposal_renders_a_panel(self):
        props = {"proposals": [{"id": "P-001", "ticker": "AAA", "action": "Sell AAA",
                                "status": "accepted_by_user", "size_usd": 500.0,
                                "direction_bucket": "SELL"}]}
        html = joined(sd._render_accepted_awaiting_execution(props))
        assert "Accepted" in html and "P-001" in html and "AAA" in html


class TestIdeasAndHousekeeping:
    def test_no_open_proposals_and_no_breaches_renders_nothing(self):
        out = sd._render_ideas_and_housekeeping({"proposals": []}, {}, {}, False, 10.0, [5, 15])
        assert out == []

    def test_open_idea_proposal_renders_in_ideas_panel(self):
        props = {"proposals": [{"id": "P-001", "ticker": "AAA", "action": "Buy AAA",
                                "status": "open", "direction_bucket": "BUY",
                                "proposal_class": "idea", "conviction_score": 55,
                                "priority_score": 3, "size_usd": 400.0}]}
        html = joined(sd._render_ideas_and_housekeeping(props, {}, {}, False, 10.0, [5, 15]))
        assert "Ideas" in html and "AAA" in html

    def test_position_cap_breach_renders_housekeeping_row(self):
        state = {"holdings": [{"ticker": "AAA", "weight_pct": 20.0}]}
        html = joined(sd._render_ideas_and_housekeeping({"proposals": []}, {"max_single_position_pct": 12},
                                                         state, False, 10.0, [5, 15]))
        assert "Risk housekeeping" in html and "AAA" in html


class TestFactorCatalysts:
    def test_no_catalysts_renders_nothing(self):
        assert sd._render_factor_catalysts({}) == []

    def test_a_catalyst_renders_headline_and_affected_tickers(self):
        state = {"factor_catalysts": [{"headline": "Supply glut", "direction": "threat",
                                       "magnitude": "large", "affects": ["AAA"],
                                       "date": "2026-08-01"}]}
        html = joined(sd._render_factor_catalysts(state))
        assert "Supply glut" in html and "AAA" in html


class TestTradeTriggers:
    def test_no_triggers_renders_nothing(self):
        assert sd._render_trade_triggers({}) == []

    def test_oversold_reversion_row_renders(self):
        triggers = {"live_counts": {"oversold_reversion": 1},
                   "oversold_reversion": [{"ticker": "AAA", "cluster": "Compute", "rsi14": 30.0,
                                           "suggested_size_usd": 200.0, "reasons": ["oversold"],
                                           "blockers": [], "vote": "live"}]}
        html = joined(sd._render_trade_triggers(triggers))
        assert "AAA" in html and "OVERSOLD" in html


class TestFactorThemes:
    def test_no_themes_renders_nothing(self):
        assert sd._render_factor_themes({}) == []

    def test_a_theme_renders(self):
        state = {"factor_themes": {"themes": [{"name": "AI capex", "watch": "hyperscaler guides",
                                                "maps_to": ["AAA"]}]}}
        html = joined(sd._render_factor_themes(state))
        assert "AI capex" in html


class TestDiversifierBench:
    def test_no_active_candidates_renders_nothing(self):
        assert sd._render_diversifier_bench({}) == []

    def test_active_candidate_renders_a_chip(self):
        state = {"diversifier_candidates": {"ZZZ": {"status": "active", "clean_diversifier": True,
                                                     "upside_pct": 20.0, "target_usd": 50.0,
                                                     "thesis": "cheap"}}}
        html = joined(sd._render_diversifier_bench(state))
        assert "ZZZ" in html


class TestRotationAnalysis:
    def test_no_tickers_renders_nothing(self):
        assert sd._render_rotation_analysis({}) == []

    def test_accumulate_bucket_renders(self):
        rotation = {"tickers": {"AAA": {"bucket": "accumulate", "net_signal": 2,
                                        "bullish_buckets": ["BREAKOUT"], "bearish_buckets": [],
                                        "cluster": "Compute", "thesis_status": "intact"}}}
        html = joined(sd._render_rotation_analysis(rotation))
        assert "AAA" in html and "Accumulate" in html


class TestClusters:
    def test_no_cluster_table_renders_nothing(self):
        assert sd._render_clusters({}, {}, set(), {}, smith_risk.thesis_status, {}) == []

    def test_a_cluster_row_renders_with_its_member(self):
        drift = {"cluster_table": [{"cluster": "Compute", "band_pct": [10, 30],
                                    "actual_pct_of_equity": 20.0, "actual_pct_of_total_book": 18.0,
                                    "target_pct": 20.0, "breach": False}]}
        state = {"holdings": [{"ticker": "AAA", "weight_pct": 20.0, "qty": 10}],
                 "sector_map": {"AAA": "Compute"}}
        risk_by_ticker = {"AAA": {"market_value_usd": 1000.0}}
        html = joined(sd._render_clusters(drift, state, {"AAA"}, risk_by_ticker,
                                          smith_risk.thesis_status, {"AAA": "Compute"}))
        assert "Compute" in html and "AAA" in html


class TestStopLossEfficacy:
    def test_no_overall_stats_renders_nothing(self):
        assert sd._render_stop_loss_efficacy({}) == []

    def test_overall_stats_render_summary(self):
        stops = {"overall": {"count": 5, "win_rate_pct": 60.0, "net_dollar_impact": -100.0,
                             "avg_move_pct": 2.0}, "by_cohort": {}, "stops": [],
                 "as_of": "2026-08-20"}
        html = joined(sd._render_stop_loss_efficacy(stops))
        assert "Stop-loss efficacy" in html


class TestTheReadAndMacro:
    def test_no_session_text_renders_nothing(self):
        assert sd._render_the_read_and_macro({}, {}, {}, {}) == []

    def test_session_text_renders(self):
        narr = {"session_read": "Futures flat into the print."}
        html = joined(sd._render_the_read_and_macro(narr, {}, {}, {}))
        assert "Futures flat" in html


class TestSentimentSessionGrid:
    def test_no_data_renders_nothing(self):
        assert sd._render_sentiment_session_grid({}, {}) == []

    def test_sentiment_score_renders_the_gauge(self):
        state = {"sentiment": {"score": 55.0, "components": {"vix": "neutral"}}}
        html = joined(sd._render_sentiment_session_grid(state, {}))
        assert "Sentiment gauge" in html


class TestWeekAhead:
    def test_always_renders_the_calendar_panel(self):
        html = joined(sd._render_week_ahead({}, "2026-08-20T09:00"))
        assert "The week ahead" in html

    def test_earnings_calendar_entry_renders(self):
        state = {"data_cache": {"earnings_calendar": {"AAA": {"date": "2026-08-20", "confirmed": True}}}}
        html = joined(sd._render_week_ahead(state, "2026-08-20T09:00"))
        assert "AAA" in html


class TestWatchlistSetups:
    def test_no_setups_renders_nothing(self):
        assert sd._render_watchlist_setups({}) == []

    def test_a_setup_renders(self):
        state = {"watchlist_setups": [{"ticker": "ZZZ", "type": "breakout", "upside_pct": 20.0, "pos": 0.5}]}
        html = joined(sd._render_watchlist_setups(state))
        assert "ZZZ" in html


class TestDerisksQueue:
    def test_no_queue_renders_nothing(self):
        assert sd._render_derisk_queue({}, {}) == []

    def test_a_queue_row_renders(self):
        derisk = {"queue": [{"rank": 1, "ticker": "AAA", "derisk_score": 50.0,
                             "fragility_score": 10.0, "stretch_score": 5.0, "friction_score": 5.0,
                             "abs_return_1m_pct": 2.0, "rel_strength_1m_pp": 1.0,
                             "cap_multiple": 1.1, "market_value_usd": 1000.0,
                             "friction_reasons": []}],
                 "queue_state": "no_stretch", "headline": "book is calm",
                 "sentiment_band": "neutral", "urgency_multiplier": 1.0}
        html = joined(sd._render_derisk_queue(derisk, {}))
        assert "AAA" in html and "De-risk queue" in html


class TestRiskCapAndLtcg:
    def test_no_breaches_or_lots_renders_nothing(self, tmp_path):
        assert sd._render_risk_cap_and_ltcg({}, {}, str(tmp_path)) == []

    def test_over_cap_position_renders_breach_row(self, tmp_path):
        risk = {"positions": [{"ticker": "AAA", "over_cap": True, "market_value_usd": 2000.0,
                               "max_position_usd": 1000.0, "cap_multiple": 2.0,
                               "headroom_usd": -1000.0}]}
        html = joined(sd._render_risk_cap_and_ltcg(risk, {}, str(tmp_path)))
        assert "Risk-cap breaches" in html and "AAA" in html


class TestPositionsTable:
    def test_no_holdings_renders_nothing(self):
        assert sd._render_positions_table({}, {}, {}, {}, {}) == []

    def test_a_holding_renders_a_row(self):
        state = {"holdings": [{"ticker": "AAA", "qty": 10, "weight_pct": 15.0}]}
        risk_by_ticker = {"AAA": {"market_value_usd": 1000.0, "atr20_pct": 8.0, "beta": 1.2,
                                  "stop_distance_pct": 16.0, "stop_price_usd": 84.0,
                                  "max_position_usd": 1200.0, "headroom_usd": 200.0}}
        html = joined(sd._render_positions_table(state, risk_by_ticker, {"AAA": "Compute"}, {}, {}))
        assert "AAA" in html and "Positions" in html


class TestThesisMap:
    def test_no_thesis_renders_nothing(self):
        out = sd._render_thesis_map({}, set(), {}, smith_risk.thesis_status,
                                    smith_risk.thesis_text, smith_risk.thesis_evidence)
        assert out == []

    def test_held_ticker_thesis_renders_grouped_by_status(self):
        state = {"thesis": {"AAA": "strong demand|strengthening"}}
        html = joined(sd._render_thesis_map(state, {"AAA"}, {"AAA": "Compute"},
                                            smith_risk.thesis_status, smith_risk.thesis_text,
                                            smith_risk.thesis_evidence))
        assert "AAA" in html and "Thesis map" in html

    def test_exited_ticker_is_excluded_from_held_count(self):
        # only tickers passed in held_tickers should render -- this mirrors build()'s own
        # pre-filter (state.thesis carries every ticker ever analysed, not just current holdings)
        state = {"thesis": {"AAA": "x|strengthening", "ZZZ": "y|watch"}}
        html = joined(sd._render_thesis_map({"thesis": {"AAA": state["thesis"]["AAA"]}}, {"AAA"},
                                            {}, smith_risk.thesis_status, smith_risk.thesis_text,
                                            smith_risk.thesis_evidence))
        assert "ZZZ" not in html


class TestSignalHistory:
    def test_no_signal_history_renders_nothing(self):
        assert sd._render_signal_history({}, set()) == []

    def test_bullish_bucket_renders(self):
        state = {"signal_history": {"AAA": ["BREAKOUT"]}}
        html = joined(sd._render_signal_history(state, {"AAA"}))
        assert "AAA" in html and "Bullish" in html

    def test_exited_ticker_is_struck_through(self):
        state = {"signal_history": {"AAA": ["BREAKOUT"]}}
        html = joined(sd._render_signal_history(state, set()))  # AAA no longer held
        assert 'class="tick g gone"' in html


class TestOpenGaps:
    def test_no_gaps_renders_nothing(self):
        assert sd._render_open_gaps({}) == []

    def test_open_gap_renders(self):
        state = {"known_gaps": [{"id": "G99", "status": "open", "description": "missing beta"}]}
        html = joined(sd._render_open_gaps(state))
        assert "G99" in html

    def test_closed_gap_is_excluded(self):
        state = {"known_gaps": [{"id": "G99", "status": "closed", "description": "fixed"}]}
        assert sd._render_open_gaps(state) == []


class TestRetiredRecent:
    def test_no_retired_proposals_renders_nothing(self):
        assert sd._render_retired_recent({"proposals": []}) == []

    def test_auto_retired_proposal_renders(self):
        props = {"proposals": [{"id": "P-001", "status": "auto_retired", "action": "Trim AAA",
                                "retired_on": "2026-08-19", "retired_reason": "cap cleared"}]}
        html = joined(sd._render_retired_recent(props))
        assert "P-001" in html


class TestExecutionLog:
    def test_no_trades_renders_nothing(self):
        assert sd._render_execution_log({}) == []

    def test_a_trade_renders(self):
        trades = {"trades": [{"date": "2026-08-19", "action": "TRIM", "ticker": "AAA",
                              "qty_change": -5, "price_at_trade": 100.0, "reason": "risk-cap"}]}
        html = joined(sd._render_execution_log(trades))
        assert "AAA" in html and "Execution log" in html


class TestDataQuality:
    def test_no_caveats_renders_nothing(self):
        assert sd._render_data_quality({}, {}, {}, {}, {}) == []

    def test_a_caveat_renders(self):
        state = {"data_quality": ["rsi14 cache stale"]}
        html = joined(sd._render_data_quality(state, {}, {}, {}, {}))
        assert "rsi14 cache stale" in html

    def test_caveats_are_pooled_from_every_compute_source(self):
        book_compute = {"data_quality": ["book caveat"]}
        html = joined(sd._render_data_quality({}, book_compute, {}, {}, {}))
        assert "book caveat" in html


class TestSelfLearning:
    def test_no_learning_data_renders_nothing(self, tmp_path):
        assert sd._render_self_learning(str(tmp_path)) == []

    def test_lessons_render_when_present(self, tmp_path, monkeypatch):
        import json
        (tmp_path / "learning.json").write_text(json.dumps(
            {"lessons": [{"kind": "correction", "date": "2026-08-19", "text": "avoid double-counting"}]}))
        html = joined(sd._render_self_learning(str(tmp_path)))
        assert "Self-learning" in html and "correction" in html


class TestHistoricalCharts:
    def test_no_charts_renders_nothing(self):
        assert sd._render_historical_charts({}, {}) == []

    def test_a_chart_renders_the_collapsed_panel(self):
        ch = {"bookvalue": {"svg": "<svg></svg>", "legend": [], "note": ""}}
        html = joined(sd._render_historical_charts(ch, {"max_single_position_pct": 12}))
        assert "Historical charts" in html


# ---------------------------------------------------------------------------
# _render_cluster_ladders (added 2026-09-08)
# ---------------------------------------------------------------------------

def _ladder_state(**kw):
    L = {"as_of": "2026-09-08", "confidence": "high", "leader": "COHR", "laggard": "APH",
         "cluster_thesis": {"status": "strengthening", "innings": "early"},
         "margin_pool": {"moving_toward": "laser/EML supply"},
         "ranking": [
             {"rank": 1, "ticker": "COHR", "held": True, "verdict": "leader",
              "differentiator_reads": [{"axis": "1.6T timing", "read": "qualified at two hyperscalers"}]},
             {"rank": 2, "ticker": "APH", "held": True, "verdict": "laggard",
              "differentiator_reads": []}]}
    L.update(kw)
    return {"cluster_ladders": {"AI Networking/Optics": L},
            "thesis": {"COHR": "lasers|strengthening", "APH": "connectors|strengthening"}}


LADDER_FILE = {"clusters": {"AI Networking/Optics": {"members": [
    {"ticker": "COHR", "rel_intra_pp": 6.0}, {"ticker": "APH", "rel_intra_pp": -9.0}]}}}


class TestClusterLadders:
    def test_no_ladders_renders_nothing(self):
        """Absence is not a finding. A ladder panel built from an empty map would read as
        'no cluster has a winner', which is a claim nobody made."""
        assert sd._render_cluster_ladders({}, {}, smith_risk.thesis_status) == []
        assert sd._render_cluster_ladders({"cluster_ladders": {}}, {}, smith_risk.thesis_status) == []

    def test_a_ladder_with_no_ranking_renders_nothing(self):
        assert sd._render_cluster_ladders(_ladder_state(ranking=[]), {},
                                          smith_risk.thesis_status) == []

    def test_a_populated_ladder_renders_its_order_and_rationale(self):
        html = joined(sd._render_cluster_ladders(_ladder_state(), LADDER_FILE,
                                                 smith_risk.thesis_status))
        assert "Cluster ladders" in html
        assert "COHR" in html and "APH" in html
        assert "qualified at two hyperscalers" in html      # the WHY, not just the order
        assert "1.6T timing" in html                        # the axis it was ranked on
        assert "early innings" in html

    def test_rel_intra_pp_comes_from_the_compute_file_not_the_agent(self):
        """The deterministic number sits beside each rank precisely so a ranking that merely
        restates price is visible as such at a glance."""
        html = joined(sd._render_cluster_ladders(_ladder_state(), LADDER_FILE,
                                                 smith_risk.thesis_status))
        assert "+6.0 pp" in html and "-9.0 pp" in html

    def test_a_missing_compute_ladder_degrades_to_a_dash(self):
        html = joined(sd._render_cluster_ladders(_ladder_state(), {}, smith_risk.thesis_status))
        assert " pp</span>" not in html      # no fabricated number where the cache is silent
        assert "COHR" in html                 # the ranking itself still renders

    def test_a_rank_contradicting_the_thesis_is_flagged(self):
        """A laggard the desk still calls strengthening is the most informative cell here --
        flag it rather than leaving it to be noticed."""
        html = joined(sd._render_cluster_ladders(_ladder_state(), LADDER_FILE,
                                                 smith_risk.thesis_status))
        assert "vs thesis" in html                          # APH: laggard on a strengthening thesis

    def test_an_agreeing_rank_is_not_flagged(self):
        st = _ladder_state()
        st["thesis"]["APH"] = "connectors|watch"
        html = joined(sd._render_cluster_ladders(st, LADDER_FILE, smith_risk.thesis_status))
        assert "vs thesis" not in html

    def test_the_track_record_is_never_shown_without_its_denominator(self):
        st = _ladder_state(track_record=[{"scored": True, "correct": True},
                                         {"scored": True, "correct": False},
                                         {"scored": False}])
        html = joined(sd._render_cluster_ladders(st, LADDER_FILE, smith_risk.thesis_status))
        assert "ladder calls 1/2" in html                   # unscoreable calls are not wrong calls

    def test_bench_names_are_marked_and_not_mistaken_for_holdings(self):
        st = _ladder_state(bench=[{"ticker": "LITE", "why_better_than": "APH",
                                   "entry_condition": "below $110"}])
        html = joined(sd._render_cluster_ladders(st, LADDER_FILE, smith_risk.thesis_status))
        assert "LITE" in html and "bench" in html and "better than APH" in html

    def test_a_redundant_pair_verdict_surfaces_but_a_distinct_one_does_not(self):
        redundant = _ladder_state(redundant_pairs=[
            {"pair": ["AVGO", "MRVL"], "verdict": "redundant", "keep": "AVGO"}])
        distinct = _ladder_state(redundant_pairs=[
            {"pair": ["AVGO", "MRVL"], "verdict": "distinct", "keep": "AVGO"}])
        assert "are one bet" in joined(sd._render_cluster_ladders(
            redundant, LADDER_FILE, smith_risk.thesis_status))
        assert "are one bet" not in joined(sd._render_cluster_ladders(
            distinct, LADDER_FILE, smith_risk.thesis_status))

    def test_confidence_is_shown_because_it_gates_trigger_authority(self):
        for conf in ("high", "medium", "low"):
            html = joined(sd._render_cluster_ladders(_ladder_state(confidence=conf),
                                                     LADDER_FILE, smith_risk.thesis_status))
            assert conf in html

    def test_a_legacy_string_thesis_entry_reads_as_a_status_not_as_its_whole_text(self):
        st = _ladder_state()
        st["thesis"]["COHR"] = "a very long legacy thesis sentence|watch"
        html = joined(sd._render_cluster_ladders(st, LADDER_FILE, smith_risk.thesis_status))
        assert "a very long legacy thesis sentence" not in html
