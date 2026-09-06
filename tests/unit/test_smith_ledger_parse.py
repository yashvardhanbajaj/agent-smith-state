"""Deterministic parsing of INDmoney confirmation emails (added 2026-09-06).

smith-ledger cost 107,874 tokens and 24 tool calls to record SEVEN fills. Almost none of it was
judgment: the confirmations are a rigid template and extracting Shares/Price/Order Type from one
is regex work. These tests pin the parser AND the two properties that make replacing an LLM with
a regex safe here -- the arithmetic self-check, and failing closed on an ambiguous ticker.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import smith_ledger as sl


def msg(subject, snippet, mid="m1", date="2026-09-03T14:00:00Z"):
    return {"threads": [{"id": mid, "messages": [
        {"id": mid, "threadId": mid, "date": date, "internalDate": "1", "subject": subject,
         "snippet": snippet}]}]}


def run(tmp_path, payload, tmap, aliases=None, bodies=None):
    (tmp_path / "state.json").write_text(json.dumps(
        {"data_cache": {"ticker_map": tmap, "ticker_map_email_aliases": aliases or {}}}))
    (tmp_path / "t.json").write_text(json.dumps(payload))
    bf = None
    if bodies is not None:
        (tmp_path / "b.json").write_text(json.dumps(bodies))
        bf = str(tmp_path / "b.json")

    class A:
        base_dir, threads_file, bodies_file, today = str(tmp_path), str(tmp_path / "t.json"), bf, "2026-09-06"
    out = {}
    orig = sl.emit
    sl.emit = lambda d: out.update(d)
    try:
        sl.cmd_ledger_parse(A())
    finally:
        sl.emit = orig
    return out


SELL = ("SELL order of Corning Inc. for $279.64 is successful",
        "Your SELL order for Corning Inc. is successful. Ticker: Corning Inc. "
        "Amount: $279.64 Price: $139.82 Shares: 2 Order Type: stop US a/c")


class TestTickerIntegrity:
    def test_ambiguous_name_resolves_to_nothing_not_a_guess(self, tmp_path):
        """THE safety case. ticker_map holds BOTH Alphabet share classes, so an email saying
        'Alphabet Inc.' prefix-matches GOOG and GOOGL. It must resolve to neither."""
        out = run(tmp_path, msg("BUY order of Alphabet Inc. for $100 is successful",
                                "Your BUY order for Alphabet Inc. is successful. "
                                "Ticker: Alphabet Inc. Amount: $100.30 Price: $100.0 "
                                "Shares: 1 Order Type: Market"),
                  {"Alphabet Inc. Class C Capital Stock": "GOOG",
                   "Alphabet Inc. Class A Common Stock": "GOOGL"})
        assert out["parsed_count"] == 0
        assert len(out["unresolved_ticker"]) == 1
        assert "ambiguous_prefix" in out["unresolved_ticker"][0]["reason"]
        assert out["dispatch_agent"] is True

    def test_unique_prefix_resolves_and_is_labelled_and_suggested_as_an_alias(self, tmp_path):
        out = run(tmp_path, msg(*SELL), {"Corning Incorporated": "GLW"})
        assert out["parsed"][0]["ticker"] == "GLW"
        assert out["parsed"][0]["ticker_resolved_by"] == "unique_prefix"
        assert out["alias_suggestions"] == {"Corning Inc.": "GLW"}

    def test_a_confirmed_alias_beats_prefix_matching(self, tmp_path):
        out = run(tmp_path, msg(*SELL), {"Corning Incorporated": "GLW"},
                  aliases={"Corning Inc.": "GLW"})
        assert out["parsed"][0]["ticker_resolved_by"] == "alias"


class TestArithmeticSelfCheck:
    def test_a_row_whose_numbers_do_not_reconcile_is_a_parse_failure_not_a_trade(self, tmp_path):
        """Amount == Shares x Price plus a known fee (0.30% buy / 0.00% sell). Three
        independently extracted numbers reconciling is WHY a regex may be trusted here."""
        out = run(tmp_path, msg("SELL order of Corning Inc. for $279.64 is successful",
                                "Your SELL order for Corning Inc. is successful. "
                                "Ticker: Corning Inc. Amount: $999.99 Price: $139.82 "
                                "Shares: 2 Order Type: stop"),
                  {"Corning Incorporated": "GLW"})
        assert out["parsed_count"] == 0
        assert out["failed_validation"][0]["ticker"] == "GLW"
        assert out["dispatch_agent"] is True

    def test_buy_fee_of_030_pct_is_accepted(self, tmp_path):
        out = run(tmp_path, msg("BUY order of Amphenol Corporation for $831.23 is successful",
                                "Your BUY order for Amphenol Corporation is successful. "
                                "Ticker: Amphenol Corporation Amount: $831.23 Price: $82.88 "
                                "Shares: 10 Order Type: Market US"),
                  {"Amphenol Corporation": "APH"})
        assert out["parsed_count"] == 1
        assert round(out["parsed"][0]["implied_fee_pct"], 2) == 0.29


class TestSnippetSufficiency:
    def test_a_complete_snippet_needs_no_body_fetch(self, tmp_path):
        out = run(tmp_path, msg(*SELL), {"Corning Incorporated": "GLW"})
        assert out["needs_body_count"] == 0
        assert out["parsed_count"] == 1

    def test_a_truncated_snippet_is_listed_for_a_body_fetch_not_guessed(self, tmp_path):
        """AMD, live 2026-09-04: the long company name pushed the fixed-length snippet past
        Shares:. Never derive quantity from Amount/Price (G80) -- ask for the body."""
        out = run(tmp_path, msg("BUY order of Advanced Micro Devices Inc. for $469.88 is successful",
                                "Your BUY order for Advanced Micro Devices Inc. is successful. "
                                "Ticker: Advanced Micro Devices Inc. Amount: $469.88 Price: $468.48"),
                  {"Advanced Micro Devices Inc. Common Stock": "AMD"})
        assert out["parsed_count"] == 0
        assert out["needs_body_count"] == 1
        assert "shares" in out["needs_body"][0]["missing"]
        assert out["dispatch_agent"] is False        # a body fetch is routine, not an exception

    def test_body_supersedes_a_truncated_snippet(self, tmp_path):
        thin = msg("BUY order of Advanced Micro Devices Inc. for $469.88 is successful",
                   "Ticker: Advanced Micro Devices Inc. Amount: $469.88 Price: $468.48")
        body = {"threads": [{"id": "m1", "messages": [{
            "id": "m1", "threadId": "m1", "date": "2026-09-04T13:53:05Z", "internalDate": "2",
            "subject": "BUY order of Advanced Micro Devices Inc. for $469.88 is successful",
            "plaintextBody": "Ticker: Advanced Micro Devices Inc. Amount: $469.88 "
                             "Price: $468.48 Shares: 1.0003 Order Type: Market US"}]}]}
        out = run(tmp_path, thin, {"Advanced Micro Devices Inc. Common Stock": "AMD"}, bodies=body)
        assert out["parsed_count"] == 1
        assert out["parsed"][0]["extracted_from"] == "body"
        assert out["needs_body_count"] == 0


class TestLedgerRules:
    def test_cancelled_notifications_are_excluded(self, tmp_path):
        out = run(tmp_path, msg("SELL order of Corning Inc. is cancelled",
                                "Your SELL order for Corning Inc. is cancelled."),
                  {"Corning Incorporated": "GLW"})
        assert out["parsed_count"] == 0
        assert len(out["excluded_cancelled"]) == 1

    def test_only_a_literal_stop_sets_a_reason(self, tmp_path):
        stop = run(tmp_path, msg(*SELL), {"Corning Incorporated": "GLW"})
        assert stop["parsed"][0]["reason"] == "stop-loss"
        mkt = run(tmp_path, msg("SELL order of Corning Inc. for $279.64 is successful",
                                "Ticker: Corning Inc. Amount: $279.64 Price: $139.82 "
                                "Shares: 2 Order Type: Market US"),
                  {"Corning Incorporated": "GLW"})
        assert mkt["parsed"][0]["reason"] == "UNCAPTURED"   # market says what, never why

    def test_two_fills_on_one_ticker_stay_two_rows(self, tmp_path):
        """One order = one row. The G64 NVDA failure was exactly this collapse."""
        p = {"threads": [
            {"id": "a", "messages": [{"id": "a", "threadId": "a", "date": "2026-09-03T13:31:49Z",
              "internalDate": "1", "subject": "SELL order of Corning Inc. for $425.55 is successful",
              "snippet": "Ticker: Corning Inc. Amount: $425.55 Price: $141.85 Shares: 3 Order Type: stop"}]},
            {"id": "b", "messages": [{"id": "b", "threadId": "b", "date": "2026-09-03T13:33:18Z",
              "internalDate": "2", "subject": "SELL order of Corning Inc. for $279.64 is successful",
              "snippet": "Ticker: Corning Inc. Amount: $279.64 Price: $139.82 Shares: 2 Order Type: stop"}]}]}
        out = run(tmp_path, p, {"Corning Incorporated": "GLW"})
        assert out["parsed_count"] == 2
        assert sorted(r["qty"] for r in out["parsed"]) == [2.0, 3.0]
