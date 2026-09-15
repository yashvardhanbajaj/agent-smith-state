"""smith_math.py draft-specs (added 2026-09-15, efficiency pass item 5): script-drafts the
strategist's proposal specs from compute_triggers.json's already-sized live candidates."""
import json
from argparse import Namespace

import smith_math as m


def _row(**kw):
    base = {"ticker": "MU", "trigger_type": "oversold_reversion", "direction": "BUY",
            "vote": "live", "suggested_size_usd": 500.0, "size_wanted_usd": 500.0,
            "clamped_by": None, "price_usd": 100.0, "stop_price_usd": 90.0,
            "reasons": ["RSI14 30 < 35"], "blockers": []}
    base.update(kw)
    return base


class TestDraftProposalSpecs:
    def test_drafts_a_single_leg_live_candidate(self):
        triggers = {"oversold_reversion": [_row()]}
        specs, skipped = m._draft_proposal_specs(triggers, open_keys=set())
        assert len(specs) == 1 and not skipped
        s = specs[0]
        assert s["ticker"] == "MU" and s["direction"] == "BUY" and s["size_usd"] == 500.0
        assert s["trigger_type"] == "oversold_reversion" and s["stop_price_usd"] == 90.0
        assert s["rationale"] is None and s["evidence_quality"] is None

    def test_skips_shadow_votes(self):
        triggers = {"oversold_reversion": [_row(vote="shadow")]}
        specs, skipped = m._draft_proposal_specs(triggers, open_keys=set())
        assert specs == [] and skipped == []

    def test_skips_a_ticker_already_open_under_the_same_trigger_type(self):
        triggers = {"oversold_reversion": [_row()]}
        specs, skipped = m._draft_proposal_specs(triggers, open_keys={("MU", "oversold_reversion")})
        assert specs == [] and "MU/oversold_reversion already open" in skipped[0]

    def test_a_different_trigger_type_on_the_same_ticker_is_not_deduped(self):
        triggers = {"catalyst_threat": [_row(trigger_type="catalyst_threat", direction="TRIM")]}
        specs, skipped = m._draft_proposal_specs(triggers, open_keys={("MU", "oversold_reversion")})
        assert len(specs) == 1 and not skipped

    def test_drafts_both_legs_of_a_paired_trigger_sharing_pair_id(self):
        triggers = {"cluster_rotation": [{
            "trigger_type": "cluster_rotation", "vote": "live", "pair_id": "cr-GEV-BE",
            "sell_leg": {"ticker": "GEV", "direction": "SELL", "suggested_size_usd": 600.0,
                        "reasons": ["laggard"]},
            "buy_leg": {"ticker": "BE", "direction": "BUY", "suggested_size_usd": 600.0,
                       "reasons": ["performer"]}}]}
        specs, skipped = m._draft_proposal_specs(triggers, open_keys=set())
        assert len(specs) == 2 and not skipped
        by_role = {s["pair_role"]: s for s in specs}
        assert by_role["sell"]["ticker"] == "GEV" and by_role["buy"]["ticker"] == "BE"
        assert by_role["sell"]["pair_id"] == by_role["buy"]["pair_id"] == "cr-GEV-BE"

    def test_skips_a_pair_when_either_leg_is_already_open(self):
        triggers = {"cluster_rotation": [{
            "trigger_type": "cluster_rotation", "vote": "live", "pair_id": "cr-GEV-BE",
            "sell_leg": {"ticker": "GEV", "direction": "SELL", "suggested_size_usd": 600.0},
            "buy_leg": {"ticker": "BE", "direction": "BUY", "suggested_size_usd": 600.0}}]}
        specs, skipped = m._draft_proposal_specs(triggers, open_keys={("BE", "cluster_rotation")})
        assert specs == [] and len(skipped) == 1


class TestDraftStressAnchorAndScorecardQuote:
    def test_stress_anchor_pulls_from_market_inputs_and_fomc_cache(self):
        anchor = m._draft_stress_anchor({"us10y": 4.5, "vix": 18.2, "dxy": 101.0},
                                        {"rate_pct": 3.63, "stance": "hawkish"})
        assert anchor == {"us10y_pct": 4.5, "vix": 18.2, "dxy": 101.0,
                          "fed_rate_pct": 3.63, "fed_stance": "hawkish"}

    def test_stress_anchor_tolerates_missing_inputs(self):
        assert m._draft_stress_anchor(None, None) == {"us10y_pct": None, "vix": None, "dxy": None,
                                                       "fed_rate_pct": None, "fed_stance": None}

    def test_scorecard_quote_formats_overall_and_by_direction(self):
        scorecard = {"as_of": "2026-09-15", "overall_accuracy_30d": 30.6,
                    "overall": {"n": 62, "worked": 19, "missed": 34, "neutral": 9},
                    "by_direction": {"BUY": {"accuracy_pct": 36.4, "n": 22}}}
        quote = m._draft_scorecard_quote(scorecard)
        assert "n=62" in quote and "30.6%" in quote and "BUY 36.4% (n=22)" in quote

    def test_scorecard_quote_none_when_absent(self):
        assert m._draft_scorecard_quote(None) is None
        assert m._draft_scorecard_quote({}) is None


class TestCmdDraftSpecsWritesFile(object):
    def test_end_to_end_writes_proposal_specs_json(self, tmp_path):
        run_dir = tmp_path / "run"
        run_dir.mkdir()
        (run_dir / "compute_triggers.json").write_text(json.dumps(
            {"as_of": "2026-09-15", "oversold_reversion": [_row()]}))
        (run_dir / "market_inputs.json").write_text(json.dumps({"us10y": 4.5, "vix": 18.0, "dxy": 100.0}))
        (tmp_path / "proposals.json").write_text(json.dumps(
            {"proposals": [], "scorecard": {"as_of": "2026-09-14", "overall_accuracy_30d": 40.0,
                                            "overall": {"n": 5, "worked": 2, "missed": 2, "neutral": 1},
                                            "by_direction": {}}}))
        (tmp_path / "state.json").write_text(json.dumps({"fomc_cache": {"rate_pct": 3.63, "stance": "hawkish"}}))
        m.cmd_draft_specs(Namespace(base_dir=str(tmp_path), run_dir=str(run_dir)))
        written = json.loads((run_dir / "proposal_specs.json").read_text())
        assert len(written["proposal_specs"]) == 1
        assert written["proposal_specs"][0]["ticker"] == "MU"
        assert written["stress_table_anchor"]["fed_rate_pct"] == 3.63
        assert "n=5" in written["scorecard_quote"]
