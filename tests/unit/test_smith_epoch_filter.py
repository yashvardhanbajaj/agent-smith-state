"""EVIDENCE WINDOW, every path (user instruction 2026-09-21).

"Don't use the earlier proposal hit data as the actual performance data in the current redesign,
as earlier proposals were too broken" -- then, told the signal-bucket hit rates were not
epoch-filtered: "correct this and any similar older hit-rate issue in the new proposal engine."

Phase 4 filtered the proposal scorecard and the trigger-journal reader. These tests pin every OTHER
path by which a pre-ENGINE_EPOCH outcome could change a size, a priority, a vote, a retirement or a
gate: signal-bucket rates and name grades (cmd_journal), the Kelly conviction tilt, the bucket
priority penalty/reward, signal_conviction retirement, cluster-ladder authority, the phase4.readiness
counter, the shadow-journal hit rates and the reporting surfaces. The effect is meant to be large --
every one of them goes INERT until post-epoch outcomes mature -- and nothing here softens that.
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
from argparse import Namespace
from contextlib import redirect_stdout
from datetime import date

import pytest

import smith_conviction
import smith_core
import smith_edge
import smith_learning
import smith_lifecycle as sl
import smith_math
import smith_memory as sm
import smith_risk

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EPOCH = smith_core.ENGINE_EPOCH                      # 2026-09-21 in production
LEGACY, POST = "2026-08-01", "2026-09-25"
TODAY = "2026-10-30"                                  # every fixture below is >30d old by then
BUCKET = "MOMENTUM+VOLUME"                            # direction "up": a fall is a failure


# ------------------------------------------------------------------------------------- helpers
def _locked(day, ticker, bucket=BUCKET, verdict="failed", pct=-10.0):
    """A journal entry already scored and LOCKED at 7d and 30d (the shape cmd_journal persists)."""
    return {"date": day, "ticker": ticker, "bucket": bucket, "price_at_flag": 100.0,
            "outcome_7d_pct": pct, "outcome_30d_pct": pct, "verdict": verdict, "_verdict_7d": verdict}


def _run_journal(tmp_path, entries, prices_held=True):
    """Run the real cmd_journal against a temp base/run dir; returns its emitted JSON."""
    base, rd = tmp_path / "base", tmp_path / "run"
    base.mkdir(exist_ok=True)
    rd.mkdir(exist_ok=True)
    (base / "journal.json").write_text(json.dumps({"schema_version": 1, "entries": entries}))
    held = [{"ticker": "ZZZ", "qty": 1, "market_value_inr": 100.0}] if prices_held else []
    (rd / "holdings.json").write_text(json.dumps({"usdinr": 1.0, "holdings_inr": held}))
    buf = io.StringIO()
    with redirect_stdout(buf):
        smith_math.cmd_journal(Namespace(base_dir=str(base), run_dir=str(rd), today=TODAY,
                                         prices_json=None))
    return json.loads(buf.getvalue())


def _thirty_losers(day):
    return [_locked(day, f"T{i:02d}") for i in range(30)]


# ---------------------------------------------------- 1. signal-bucket rates (cmd_journal)
class TestJournalPublishesOnlyPostEpochRates:
    def test_thirty_perfectly_losing_legacy_firings_publish_nothing(self, tmp_path):
        out = _run_journal(tmp_path, _thirty_losers(LEGACY))
        assert out["bucket_hit_rates"] == {}
        assert out["bucket_hit_rates_7d"] == {}
        assert out["name_bucket_grades"] == {}
        assert out["legacy_entries_excluded"] == 30
        assert out[smith_edge.BUCKET_RATES_EPOCH_KEY] == EPOCH
        assert EPOCH in out["bucket_rates_window"]

    def test_the_same_entries_dated_post_epoch_are_evaluated_normally(self, tmp_path):
        out = _run_journal(tmp_path, _thirty_losers(POST))
        assert out["bucket_hit_rates"][BUCKET] == {"n": 30, "hit_rate_pct": 0.0}
        assert out["bucket_hit_rates_7d"][BUCKET]["n"] == 30
        assert out["legacy_entries_excluded"] == 0

    def test_moving_the_epoch_moves_the_verdict_on_the_same_entries(self, tmp_path, monkeypatch):
        entries = _thirty_losers(LEGACY)
        assert _run_journal(tmp_path, entries)["bucket_hit_rates"] == {}
        monkeypatch.setattr(smith_core, "ENGINE_EPOCH", "2026-01-01")
        out = _run_journal(tmp_path, entries)
        assert out["bucket_hit_rates"][BUCKET]["n"] == 30
        assert out[smith_edge.BUCKET_RATES_EPOCH_KEY] == "2026-01-01"

    def test_a_mixed_journal_counts_only_post_epoch_and_n_proves_it(self, tmp_path):
        entries = ([_locked(LEGACY, f"L{i}") for i in range(10)]                       # 10 legacy losers
                   + [_locked(POST, f"P{i}", verdict="worked", pct=8.0) for i in range(4)])  # 4 post winners
        out = _run_journal(tmp_path, entries)
        assert out["bucket_hit_rates"][BUCKET] == {"n": 4, "hit_rate_pct": 100.0}
        assert out["bucket_hit_rates_7d"][BUCKET]["n"] == 4
        assert out["legacy_entries_excluded"] == 10
        # per-name grades: a legacy-only name is absent, a post-epoch name is graded
        assert "L0" not in out["name_bucket_grades"]
        assert out["name_bucket_grades"]["P0"][BUCKET]["grade"] == "A"

    def test_payoff_ratio_uses_only_post_epoch_magnitudes(self, tmp_path):
        entries = ([_locked(LEGACY, f"L{i}", pct=-40.0) for i in range(5)]
                   + [_locked(POST, "W0", "MOMENTUM+VOLUME", "worked", 9.0),
                      _locked(POST, "W1", "MOMENTUM+VOLUME", "worked", 11.0),
                      _locked(POST, "F0", "MOMENTUM+VOLUME", "failed", -5.0)])
        row = _run_journal(tmp_path, entries)["bucket_hit_rates"][BUCKET]
        assert row["n"] == 3 and row["payoff_ratio"] == 2.0    # 10 / 5, the -40s never enter

    def test_below_the_sample_floor_nothing_is_published(self, tmp_path):
        few = [_locked(POST, f"P{i}") for i in range(smith_core.BUCKET_RATE_MIN_N - 1)]
        out = _run_journal(tmp_path, few)
        assert out["bucket_hit_rates"] == {} and out["bucket_hit_rates_7d"] == {}


class TestJournalLockingIsUndisturbed:
    def test_a_legacy_unscored_entry_is_still_scored_and_locked_but_never_tallied(self, tmp_path):
        open_legacy = {"date": LEGACY, "ticker": "ZZZ", "bucket": BUCKET, "price_at_flag": 200.0,
                       "verdict": "open"}                     # ZZZ is held at $100: -50%
        out = _run_journal(tmp_path, [open_legacy])
        upd = out["journal_updates"][0]
        assert upd["outcome_30d_pct"] == -50.0 and upd["verdict"] == "failed"     # scored and locked
        assert upd["outcome_7d_pct"] == -50.0 and upd["_verdict_7d"] == "failed"
        assert out["bucket_hit_rates"] == {} and out["legacy_entries_excluded"] == 1

    def test_a_locked_score_never_moves_when_the_price_does(self, tmp_path):
        e = _locked(POST, "ZZZ", verdict="worked", pct=+7.0)      # locked at +7%; ZZZ now prices at -50%
        e["price_at_flag"] = 200.0
        out = _run_journal(tmp_path, [e])
        assert out["journal_updates"][0]["outcome_30d_pct"] == 7.0
        assert out["journal_updates"][0]["verdict"] == "worked"


# ------------------------------------------- 2. the ONE reader refuses an unstamped table
class TestAdmissibleTables:
    LEGACY_TABLES = {"bucket_hit_rates": {BUCKET: {"n": 15, "hit_rate_pct": 20.0}},
                     "bucket_hit_rates_7d": {BUCKET: {"n": 14, "hit_rate_pct": 14.3}},
                     "name_bucket_grades": {"NVDA": {BUCKET: {"grade": "F", "n": 2, "hit_rate_pct": 0.0,
                                                              "low_confidence": True}}}}

    def test_a_journal_persisted_before_the_filter_reads_as_empty(self):
        got = smith_edge.admissible_bucket_tables(self.LEGACY_TABLES)          # no stamp
        assert got == {"bucket_hit_rates": {}, "bucket_hit_rates_7d": {}, "name_bucket_grades": {}}

    def test_a_table_stamped_under_a_different_epoch_is_legacy(self):
        j = {**self.LEGACY_TABLES, smith_edge.BUCKET_RATES_EPOCH_KEY: "2026-01-01"}
        assert smith_edge.admissible_bucket_tables(j)["bucket_hit_rates"] == {}

    def test_a_current_stamp_admits_rows_at_or_above_the_floor_only(self):
        j = {smith_edge.BUCKET_RATES_EPOCH_KEY: EPOCH,
             "bucket_hit_rates": {"A": {"n": 3, "hit_rate_pct": 33.3}, "B": {"n": 2, "hit_rate_pct": 100.0}}}
        assert set(smith_edge.admissible_bucket_tables(j)["bucket_hit_rates"]) == {"A"}

    def test_epoch_can_be_overridden_per_call(self):
        j = {**self.LEGACY_TABLES, smith_edge.BUCKET_RATES_EPOCH_KEY: "2026-01-01"}
        assert smith_edge.admissible_bucket_tables(j, epoch="2026-01-01")["bucket_hit_rates"]


# ---------------------------------- 3. Kelly conviction tilt / 4. priority / 5. retirement
class TestNoPostEpochRecordMeansNoEffect:
    EMPTY = smith_edge.admissible_bucket_tables({"bucket_hit_rates": {BUCKET: {"n": 15, "hit_rate_pct": 20.0}}})

    def test_kelly_tilt_is_one_and_the_reason_quotes_no_legacy_number(self):
        tr = smith_math.worst_bullish_track_record([BUCKET], self.EMPTY["bucket_hit_rates"],
                                                   self.EMPTY["bucket_hit_rates_7d"])
        assert tr is None
        mult, why = smith_conviction.track_record_multiplier(None, 0, window=smith_edge.evidence_window())
        assert mult == 1.0
        assert "no post-epoch track record" in why and EPOCH in why
        assert not re.search(r"\d+%", why)                                    # no rate quoted

    def test_below_the_floor_is_no_tilt_even_with_a_rate(self):
        mult, why = smith_conviction.track_record_multiplier(0.0, 2, payoff_ratio=None, window="since x")
        assert mult == 1.0 and "no post-epoch track record" in why

    def test_score_conviction_states_it_and_does_not_tilt(self):
        ctx = {"ticker": "AAA", "thesis_entry": {"status": "intact"}, "buckets": [BUCKET],
               "track_record": {"hit_rate_pct": None, "n": 0, "payoff_ratio": None,
                                "window": smith_edge.evidence_window()}}
        out = smith_conviction.score_conviction(ctx)
        assert out["conviction_score"] == out["conviction_raw_pre_tilt"]
        assert any("no post-epoch track record" in r for r in out["conviction_reasons"])

    def test_a_post_epoch_record_still_tilts_and_names_its_window(self):
        mult, why = smith_conviction.track_record_multiplier(20.0, 20, payoff_ratio=0.5,
                                                             window=smith_edge.evidence_window())
        assert mult < 1.0 and EPOCH in why

    def test_bucket_penalty_needs_admitted_rows(self):
        assert smith_edge.bucket_adjustment(self.EMPTY, [BUCKET]) == (0, None)
        assert smith_edge.bucket_rate(self.EMPTY, BUCKET) is None
        admitted = {"bucket_hit_rates": {BUCKET: {"n": 30, "hit_rate_pct": 0.0}}}
        pts, why = smith_edge.bucket_adjustment(admitted, [BUCKET])
        assert pts == -smith_core.BUCKET_PENALTY_POINTS and EPOCH in why      # labelled window

    def test_bucket_rate_labels_window_and_enforces_the_floor(self):
        r = smith_edge.bucket_rate({"bucket_hit_rates": {"X": {"n": 3, "hit_rate_pct": 66.7}}}, "X")
        assert r["window"] == "since " + EPOCH
        assert smith_edge.bucket_rate({"bucket_hit_rates": {"X": {"n": 2, "hit_rate_pct": 100.0}}}, "X") is None

    @staticmethod
    def _retire(hit_rates_30d, hit_rates_7d=None):
        from conftest import make_proposal
        pr = make_proposal(ticker="AAA", action="Buy AAA", direction_bucket="BUY", trigger_type="signal_conviction",
                           trigger_bucket=BUCKET, date="2026-09-25")
        sl._check_condition_based_retirement(
            pr, today_date=date(2026, 9, 26), risk_by_ticker={}, directional_breach=lambda *a: None,
            current_tickers=set(), drift={}, trig_rsi={}, trig_abs={}, trigger_live_sets={}, state_thesis={},
            derisk={}, cluster_breach=lambda *a: None,
            rotation_by_ticker={"AAA": {"bullish_buckets": [BUCKET]}}, hit_rates_7d=hit_rates_7d or {},
            parse_date=sl._proposal_parse_date, hold_max_age_days=2, hit_rates_30d=hit_rates_30d)
        return pr

    def test_signal_conviction_is_not_retired_on_absent_or_legacy_evidence(self):
        """No admissible rate (nothing matured since the epoch, or a legacy table read as empty) must
        KEEP the proposal open: absence of evidence is not evidence. Before 2026-09-21 a missing or
        legacy rate decided this."""
        pr = self._retire(self.EMPTY["bucket_hit_rates"])
        assert pr["status"] == "open"

    def test_signal_conviction_retires_on_a_falling_post_epoch_rate_and_names_the_window(self):
        pr = self._retire({BUCKET: {"n": 12, "hit_rate_pct": 40.0}})
        assert pr["status"] == "auto_retired" and EPOCH in pr["retired_reason"]

    def test_signal_conviction_stays_open_on_a_healthy_post_epoch_rate(self):
        assert self._retire({BUCKET: {"n": 12, "hit_rate_pct": 70.0}})["status"] == "open"

    def test_signal_conviction_is_retired_when_the_bucket_itself_is_gone(self):
        from conftest import make_proposal
        pr = make_proposal(ticker="AAA", action="Buy AAA", direction_bucket="BUY", trigger_type="signal_conviction",
                           trigger_bucket=BUCKET, date="2026-09-25")
        sl._check_condition_based_retirement(
            pr, today_date=date(2026, 9, 26), risk_by_ticker={}, directional_breach=lambda *a: None,
            current_tickers=set(), drift={}, trig_rsi={}, trig_abs={}, trigger_live_sets={}, state_thesis={},
            derisk={}, cluster_breach=lambda *a: None, rotation_by_ticker={"AAA": {"bullish_buckets": []}},
            hit_rates_7d={}, parse_date=sl._proposal_parse_date, hold_max_age_days=2, hit_rates_30d={})
        assert pr["status"] == "auto_retired"


# --------------------------------------------------------------- 6. cluster-ladder authority
def _ladder(conf, calls, as_of="2026-09-20"):
    return {"as_of": as_of, "confidence": conf, "leader": "A", "laggard": "B", "track_record": calls}


def _call(correct, day):
    return {"scored": True, "correct": correct, "ladder_as_of": day, "as_of": day}


class TestLadderAuthorityEpoch:
    TODAY = date(2026, 9, 21)

    @pytest.mark.parametrize("conf,expected", [("high", "full"), ("medium", "rank"), ("low", "none"), ("", "none")])
    def test_only_pre_epoch_calls_equal_no_calls_at_every_confidence(self, conf, expected):
        losing_legacy = [_call(False, "2026-09-08")] * 8            # 0/8: withdrawn before the filter
        with_calls = smith_risk.ladder_authority(_ladder(conf, losing_legacy), self.TODAY)
        with_none = smith_risk.ladder_authority(_ladder(conf, []), self.TODAY)
        assert with_calls[0] == with_none[0] == expected            # NOT stripped, NOT granted
        assert with_calls[1] == with_none[1]

    def test_the_filter_never_withdraws_authority_from_a_medium_ladder(self):
        auth = smith_risk.ladder_authority(_ladder("medium", [_call(False, "2026-09-08")] * 20), self.TODAY)
        assert auth[0] == "rank"                                    # rotation candidates still generated

    def test_legacy_calls_are_reported_as_set_aside_not_counted(self):
        _, _, why = smith_risk.ladder_authority(_ladder("medium", [_call(False, "2026-09-08")] * 3), self.TODAY)
        assert any("predate the engine epoch" in w for w in why)
        assert not any("ladder track record" in w for w in why)

    def test_post_epoch_calls_behave_normally_and_withdraw_on_a_failing_sample(self):
        bad = [_call(False, POST)] * 5 + [_call(True, POST)]
        auth, conf, why = smith_risk.ladder_authority(_ladder("high", bad), self.TODAY)
        assert (auth, conf) == ("none", "low") and "since " + EPOCH in why[0] or "below coin-flip" in why[0]

    def test_a_small_post_epoch_sample_is_reported_not_acted_on(self):
        auth, _, why = smith_risk.ladder_authority(_ladder("high", [_call(False, POST)] * 2), self.TODAY)
        assert auth == "full" and any("below the sample bar" in w for w in why)

    def test_mixed_calls_count_only_the_post_epoch_ones(self):
        calls = [_call(False, "2026-09-08")] * 10 + [_call(True, POST)] * 2
        _, _, why = smith_risk.ladder_authority(_ladder("high", calls), self.TODAY)
        assert any("2/2" in w for w in why)

    def test_an_undated_call_cannot_be_admitted(self):
        auth = smith_risk.ladder_authority(_ladder("high", [{"scored": True, "correct": False}] * 8), self.TODAY)
        assert auth[0] == "full"

    def test_epoch_moves_with_the_argument(self):
        calls = [_call(False, "2026-09-08")] * 6
        assert smith_risk.ladder_authority(_ladder("high", calls), self.TODAY, epoch="2026-09-01")[0] == "none"

    def test_no_cluster_rotation_is_lost_as_an_artefact_end_to_end(self, tmp_path):
        """cmd_triggers on the ladder fixture: poison every ladder with 8 WRONG pre-epoch calls and the
        ladder-driven cluster_rotation candidates are byte-identical; poison with 8 wrong POST-epoch
        calls and they legitimately disappear (proving the filter, not the fixture, decides)."""
        src = os.path.join(ROOT, "tests", "fixtures", "triggers_case2_ladder")

        def run(day):
            dst = tmp_path / f"case_{day}"
            shutil.copytree(src, dst)
            st = json.loads((dst / "base" / "state.json").read_text())
            for entry in st["cluster_ladders"].values():
                entry["track_record"] = [_call(False, day) for _ in range(8)] if day else []
            (dst / "base" / "state.json").write_text(json.dumps(st))
            res = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "smith_math.py"), "triggers",
                                  "--base-dir", str(dst / "base"), "--run-dir", str(dst / "rundir"),
                                  "--today", "2026-09-01"], capture_output=True, text=True, check=True)
            return [(r["sell_leg"]["ticker"], r["buy_leg"]["ticker"], r["ladder_authority"])
                    for r in json.loads(res.stdout)["cluster_rotation"]]

        baseline = run(None)
        assert baseline, "fixture must produce ladder-driven rotations"
        assert run("2026-09-08") == baseline                        # legacy losers: no effect at all
        assert run("2026-09-25") != baseline                        # admissible losers: authority withdrawn


# ------------------------------------------------------ 7. the phase4.readiness counter
class TestReadinessCountsOnlyPostEpoch:
    def _store(self, tmp_path, rows, archive=()):
        (tmp_path / "proposals.json").write_text(json.dumps({"proposals": rows}))
        (tmp_path / "proposals-archive.json").write_text(json.dumps({"proposals": list(archive)}))

    def test_legacy_graded_rows_do_not_count_and_are_reported_as_excluded(self, tmp_path):
        self._store(tmp_path,
                    [{"id": "P-1", "outcome_verdict": "worked", "date": "2026-09-10"},
                     {"id": "P-2", "outcome_verdict": "missed", "date": "2026-09-20"},
                     {"id": "P-363", "outcome_verdict": "worked", "date": POST}],
                    [{"id": "P-9", "outcome_verdict": "missed", "date": "2026-08-01"}])
        c = smith_learning.scored_proposal_counts(str(tmp_path))
        assert c["scored"] == 1 and c["worked"] == 1 and c["missed"] == 0
        assert c["legacy_excluded"] == 3 and c["counted_since"] == EPOCH

    def test_all_legacy_reads_zero(self, tmp_path):
        self._store(tmp_path, [{"id": f"P-{i}", "outcome_verdict": "worked", "date": "2026-09-01"} for i in range(22)])
        assert smith_learning.update_phase4_readiness(str(tmp_path))["scored"] == 0
        p = smith_learning.load_store(str(tmp_path))["parameters"]["phase4.readiness"]
        assert p["current"] == 0 and p["legacy_excluded"] == 22 and p["n_gate"] == 100

    def test_an_undated_row_is_not_admissible(self, tmp_path):
        self._store(tmp_path, [{"id": "P-1", "outcome_verdict": "worked"}])
        assert smith_learning.scored_proposal_counts(str(tmp_path))["scored"] == 0

    def test_validator_uses_the_same_counter(self, tmp_path):
        self._store(tmp_path, [{"id": "P-1", "outcome_verdict": "worked", "date": "2026-09-01"}])
        (tmp_path / "learning.json").write_text(json.dumps(
            {"observations": [], "lessons": [], "parameters": {"phase4.readiness": {"current": 1}}}))
        assert any("LEARNING COUNTER" in d for d in sm.validate_learning_schema(str(tmp_path)))
        (tmp_path / "learning.json").write_text(json.dumps(
            {"observations": [], "lessons": [], "parameters": {"phase4.readiness": {"current": 0}}}))
        assert not any("LEARNING COUNTER" in d for d in sm.validate_learning_schema(str(tmp_path)))

    def test_ladder_observations_recorded_only_for_post_epoch_calls(self):
        src = open(os.path.join(ROOT, "scripts", "smith_memory.py")).read()
        assert 'smith_edge.post_epoch(_sc.get("ladder_as_of"))' in src


# ------------------------------------------------- shadow-journal hit rates (trigger_journal.json)
class TestShadowJournalPublishesPostEpochOnly:
    def test_hit_rate_by_key_excludes_legacy_and_keeps_it_labelled(self, tmp_path):
        rows = [{"date": LEGACY, "ticker": "A", "trigger_type": "laggard_rotation", "price_at_flag": 100.0,
                 "scored": True, "verdict": "failed", "outcome_pct": -9.0},
                {"date": POST, "ticker": "B", "trigger_type": "laggard_rotation", "price_at_flag": 100.0,
                 "scored": True, "verdict": "worked", "outcome_pct": 9.0}]
        (tmp_path / "trigger_journal.json").write_text(json.dumps({"entries": rows}))
        buf = io.StringIO()
        with redirect_stdout(buf):
            sl.cmd_score_shadow_journal(Namespace(base_dir=str(tmp_path), file="trigger_journal.json",
                                                  prices_json=None, today=TODAY, dry_run=False))
        out = json.loads(buf.getvalue())
        assert out["hit_rate"] == {"n": 1, "hit_rate_pct": 100.0}
        assert out["hit_rate_by_key"] == {"laggard_rotation": {"n": 1, "hit_rate_pct": 100.0}}
        assert out["legacy_hit_rate"] == {"n": 1, "hit_rate_pct": 0.0}
        stored = json.loads((tmp_path / "trigger_journal.json").read_text())
        assert "LEGACY" in stored["legacy_note"] and stored["evidence_window"] == "since " + EPOCH


# ------------------------------------------------------------------------ 8. reporting surfaces
class TestReportingNeverPresentsALegacyRateAsCurrent:
    def _base(self, tmp_path, journal, scorecard):
        base = tmp_path
        (base / "ledger.csv").write_text("ts,mode,value_usd\n2026-09-20T09:07:00Z,quick,1\n")
        (base / "state.json").write_text("{}")
        (base / "journal.json").write_text(json.dumps(journal))
        (base / "proposals.json").write_text(json.dumps({"proposals": [], "scorecard": scorecard}))
        return sm._report_weekly(str(base), None, date(2026, 9, 21), {}, [])

    LEGACY_JOURNAL = {"bucket_hit_rates": {"MOMENTUM+VOLUME": {"n": 15, "hit_rate_pct": 20.0},
                                           "TARGET GAP": {"n": 19, "hit_rate_pct": 36.8}}}
    LEGACY_SCORECARD = {"overall": {"n": 88, "accuracy_pct": 27.3, "worked": 24, "missed": 64},
                        "by_direction": {"BUY": {"n": 40, "accuracy_pct": 25.0}}}

    def test_the_weak_bucket_line_cannot_survive_on_legacy_data(self, tmp_path):
        text = self._base(tmp_path, self.LEGACY_JOURNAL, self.LEGACY_SCORECARD)
        assert "Below the strategist's own de-emphasis line" not in text
        assert "MOMENTUM+VOLUME" not in text and "TARGET GAP" not in text
        assert "since " + EPOCH in text and "No signal fired since" in text

    def test_a_stamped_post_epoch_table_is_shown_with_its_window(self, tmp_path):
        j = {smith_edge.BUCKET_RATES_EPOCH_KEY: EPOCH,
             "bucket_hit_rates": {BUCKET: {"n": 6, "hit_rate_pct": 16.7}}}
        text = self._base(tmp_path, j, {})
        assert f"| {BUCKET} | 16.7% | 6 |" in text and "signals fired since " + EPOCH in text
        assert "Below the strategist's own de-emphasis line" in text

    def test_the_flat_legacy_scorecard_is_labelled_history_and_never_the_headline(self, tmp_path):
        text = self._base(tmp_path, {}, self.LEGACY_SCORECARD)
        assert "CURRENT engine" in text and "n=0" in text
        line = next(l for l in text.splitlines() if "27.3%" in l)
        assert "LEGACY-ENGINE HISTORY" in line and "not current performance" in line
        assert "Scorecard (all-time" not in text

    def test_dashboard_track_payload_reads_the_admitted_view(self):
        import smith_dashboard as sd
        src = open(os.path.join(ROOT, "scripts", "smith_dashboard.py")).read()
        assert "smith_edge.admissible_bucket_tables(journal)" in src
        assert 'journal.get("bucket_hit_rates")' not in src

    def test_runlife_summary_drops_the_legacy_flat_accuracy_scalars(self):
        src = open(os.path.join(ROOT, "scripts", "smith_runlife.py")).read()
        assert '_accuracy_30d' in src and "current_engine_scored_rows" in src


# ------------------------------------------------------------------------------ 9. the guard
class TestNoConsumerBypassesTheEpochFilter:
    """A grep-style guard so a FUTURE consumer cannot silently read an unfiltered table. Every
    script that names one of these tables may do so only through the epoch-filtered path or as the
    single producer/persister. If you add a reader, route it through smith_edge.admissible_bucket_tables
    (or smith_risk.ladder_authority / smith_learning.scored_proposal_counts) rather than editing this list."""
    SCRIPTS = os.path.join(ROOT, "scripts")

    # file -> why it is allowed to mention the raw table name
    RAW_ALLOWED = {
        "smith_math.py": "cmd_journal is the PRODUCER (tallies post-epoch only); the reader in cmd_triggers "
                         "goes through smith_edge.admissible_bucket_tables",
        "smith_edge.py": "THE reader (admissible_bucket_tables / bucket_rate / bucket_adjustment)",
        "smith_orchestrate.py": "persists cmd_journal's stamped output verbatim (the stamp travels with it)",
        "smith_lifecycle.py": "reads through smith_edge.admissible_bucket_tables in cmd_proposals",
        "smith_dashboard.py": "reads through smith_edge.admissible_bucket_tables",
        "smith_memory.py": "weekly report reads through smith_edge.admissible_bucket_tables; retention "
                           "prose mentions the names",
    }
    NAMES = ("bucket_hit_rates", "name_bucket_grades")

    def _src(self, name):
        return open(os.path.join(self.SCRIPTS, name)).read()

    def test_no_unlisted_module_reads_the_bucket_tables(self):
        offenders = []
        for f in sorted(os.listdir(self.SCRIPTS)):
            if not f.endswith(".py"):
                continue
            if any(n in self._src(f) for n in self.NAMES) and f not in self.RAW_ALLOWED:
                offenders.append(f)
        assert not offenders, f"new reader(s) of the raw bucket tables, route through smith_edge: {offenders}"

    def test_every_allowed_reader_actually_goes_through_the_filter(self):
        for f in ("smith_math.py", "smith_lifecycle.py", "smith_dashboard.py", "smith_memory.py"):
            assert "admissible_bucket_tables(" in self._src(f), f

    def test_no_raw_journal_table_reads_outside_the_producer_and_the_reader(self):
        pat = re.compile(r'journal(?:_doc)?\.get\(\s*["\'](bucket_hit_rates(?:_7d)?|name_bucket_grades)["\']')
        bad = {f: pat.findall(self._src(f)) for f in os.listdir(self.SCRIPTS)
               if f.endswith(".py") and pat.search(self._src(f)) and f != "smith_edge.py"}
        assert not bad, bad

    def test_ladder_track_record_is_only_counted_inside_ladder_authority(self):
        for f in sorted(os.listdir(self.SCRIPTS)):
            if not f.endswith(".py") or f == "smith_risk.py":
                continue
            src = self._src(f)
            assert not re.search(r'\.get\(["\']track_record["\']\)[^\n]*scored', src), f
            assert 'entry["track_record"] if' not in src

    def test_scored_proposal_counts_is_epoch_filtered_at_its_definition(self):
        src = self._src("smith_learning.py")
        body = src[src.index("def scored_proposal_counts"):src.index("def update_phase4_readiness")]
        assert "post_epoch" in body

    def test_smith_edge_docstring_no_longer_claims_bucket_rates_are_exempt(self):
        assert "epoch exclusion does not apply." not in self._src("smith_edge.py")
