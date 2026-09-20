#!/usr/bin/env python3
"""
Agent Smith deterministic compute layer.

Moves arithmetic that sub-agents were doing with an LLM (currency conversion,
weights, concentration, drawdown, journal scoring, drift-vs-policy, a Fear/Greed
composite) into plain Python. Sub-agents are for judgment and external data
gathering; this script is for math. Stdlib only, no pip deps.

Subcommands emit one compact JSON object to stdout. On any error, emit
{"error": "..."} to stdout and exit 1 -- the orchestrator treats that as a
signal to note the gap in data_quality and let the relevant sub-agent
compute that section inline, same as any other sub-agent failure.

Usage -- PREFER THE PIPELINE. It runs every per-run stage below in dependency order and
fails loudly instead of letting a stage emit silent zeros (see cmd_pipeline for the incident
that motivated it):

  smith_math.py pipeline    --base-dir DIR --run-dir DIR [--today YYYY-MM-DD] [--lots lots.json]

Per-run stages (all run by `pipeline`; invoke individually only to debug one):
  book        --base-dir DIR --run-dir DIR [--lots lots.json]   value/weights/concentration/drawdown
  risk        --base-dir DIR --run-dir DIR                      ATR caps, open risk   (needs book)
  drift       --base-dir DIR --run-dir DIR                      cluster/cash/AI-capex (needs book)
  journal     --base-dir DIR --run-dir DIR [--today ...]        signal hit-rate scoring
  attribution --base-dir DIR --run-dir DIR                      FX / flow / residual decomposition
  rotation    --base-dir DIR --run-dir DIR                      accumulate/trim buckets (needs risk)
  sentiment   --base-dir DIR --market-inputs market_inputs.json Fear/Greed composite
  derisk      --base-dir DIR --run-dir DIR [--today ...]        fragility queue (needs risk+sentiment)
  triggers    --base-dir DIR --run-dir DIR [--today ...]        oversold/overbought/ratchet triggers

Stages the pipeline deliberately does NOT run (each needs something it cannot supply itself):
  score       --base-dir DIR --prices-json P.json [--run-dir R] [--rebase-scorecard] [--today ...] [--dry-run]
              proposal outcome scoring, 30d/90d. Needs prices -> run with --prices-json /dev/null
              first and it will NAME the tickers it wants.
  stops       --base-dir DIR --prices-json P.json [--today ...] stop-loss efficacy; same price rule
  proposals   --base-dir DIR --run-dir DIR [--today ...]        lifecycle/dedup/priority; run AFTER
                                                                the strategist appends this run
  dismiss     --base-dir DIR --id P-### [--reason "..."]        user-invoked, terminal
  validate    --base-dir DIR                                    policy sanity check, not per-run
"""
import argparse
import json
import math
import os
import re
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smith_risk
import smith_conviction
import smith_ticket
from smith_core import *  # noqa: F401,F403
from smith_core import load_json, emit, fail, clamp
from smith_ledger import (cmd_lots, cmd_history, cmd_universe, cmd_ledger_parse,
                          cmd_ledger_apply, cmd_bookcalc, cmd_taxcalc)
import smith_valuation
import smith_perf
from smith_correlation import cmd_correlation
from smith_comms import cmd_comms_route, cmd_comms_status
from smith_validity import cmd_validity
from smith_valuation import cmd_valuation
from smith_memory import cmd_compact, cmd_gaps, cmd_validate, cmd_slices, validate_policy, cmd_append_ledger, cmd_merge_tails, cmd_freshness, cmd_report, cmd_runs, cmd_crosscheck
from smith_lifecycle import (cmd_proposals, cmd_score, cmd_stops, cmd_dismiss, cmd_add_proposal,
                             cmd_score_shadow_journal, dismiss_proposal_core)
from smith_learning import (load_store as learn_load_store, write_store as learn_write_store,
                            record_observation, user_force_approve,
                            cmd_learn_status, cmd_learn_lessons, cmd_learn_add_lesson,
                            cmd_learn_revealed_preference, cmd_learn_priority_params,
                            cmd_learn_stop_calibration, cmd_usage_audit,
                            cmd_usage_report)
# explicit: `from x import *` does NOT export underscore-prefixed names
from smith_core import _prior_run_prices
from smith_ledger import _avg_cost_from_lots, _months_between, policy_ltcg_months, months_until_ltcg
from smith_lifecycle import _proposal_parse_date
from smith_ledger import cmd_trade_rationale  # noqa: E402
import smith_marketdata  # noqa: E402
from smith_marketdata import cmd_indicators, cmd_normalize_bars, cmd_session_gate  # noqa: E402
from smith_orchestrate import cmd_dispatch_plan, cmd_triggers_diff, cmd_postflight  # noqa: E402
from smith_perf import cmd_perf  # noqa: E402
from smith_runlife import (cmd_lock, cmd_commit_state, cmd_health,  # noqa: E402
                           cmd_memory_summary, cmd_preflight, cmd_abort)



                          # (see cmd_score: a corrupt $305.87 TSM anchor produced a phantom -39%)














# ---------------------------------------------------------------------------
# build-holdings
# ---------------------------------------------------------------------------
def cmd_build_holdings(args):
    """Build holdings.json mechanically from a raw networth_holdings(US_STOCK) dump, instead of
    the orchestrator hand-writing it in an inline Python snippet every run.

    ADDED 2026-09-10 after a run where hand-construction cost most of a sweep's wall-clock and
    produced two real defects in a row: (1) day_chg_pct was left null on all 31 rows because the
    inline script never wired up the field, silently starving compute_buckets.json's STRONG
    DOWNTREND/UPTREND classification of real data until a user-flagged anomaly (VRT -9.6% with
    no bucket fired) forced a second full pipeline run to find it; (2) two tickers absent from
    the live pull (FSLR, VST) were guessed to be a snapshot pagination glitch and silently
    carried forward at last-known qty -- WRONG, both had been legitimately stopped out days
    earlier, and the guess was only caught because it happened to also break persist-safety
    checks downstream. Both defects share one root cause: there was no deterministic builder, so
    every run re-derived the transformation by hand and both mistakes were free to recur (the
    2026-09-09 run made the identical "carried forward" guess for the identical tickers).

    THE RULE THIS ENFORCES: the row set in holdings.json is EXACTLY the row set the snapshot
    returned. A ticker present in state.json's prior holdings but absent from this run's
    snapshot is NEVER carried forward and NEVER silently dropped -- it is named in
    `dropped_since_last_run` and the caller MUST resolve it via the ledger pipeline (SKILL.md's
    LEDGER trigger: search transaction-confirmation emails, `ledger-parse` / `ledger-apply`) or
    an explicit user confirmation, never a guess about API flakiness.

    Input:
      --snapshot-json   raw networth_holdings(US_STOCK) `result` payload (parsed JSON): expects
                        top-level `holdings` (list of {investment_code, investment, total_units,
                        invested_value_usd, current_value_usd, one_day_change_usd,
                        holding_percent}) and `asset_summary.total_value_usd`.
      --live-quotes-json  optional flat {"TICKER": price} or {"TICKER": {"price":..,
                        "changePct":..}} map (e.g. yfinance get_stock_price, format=json). When a
                        ticker has a live quote, its price and day_chg_pct are taken from THIS,
                        not from the snapshot's own (measured unreliable -- see G94's sibling
                        finding that INDmoney's one_day_change_percentage read -0.11% for a name
                        that had actually moved -9.6% intraday) one_day_change fields. A ticker
                        with no live quote keeps the snapshot's own day-change as a fallback,
                        degraded rather than dropped, and is named in `no_live_quote`.
      --usdinr          required.
      --wallet-usd       US_STOCK_WALLET current_value in USD (from networth_snapshot).
      --aggregate-usd    optional: the snapshot's own asset_summary.total_value_usd, kept
                        SEPARATE from the row-level sum so cmd_book's G3 divergence check still
                        has real teeth. Defaults to the row-level sum (no distinct check) if
                        omitted.
      --market-session, --gate-classification, --gate-reason  strings, written through as-is.
      --macro-json      optional path to market_inputs.json; merged into macro_strip verbatim.
      --benchmarks-json  optional flat {"smh": 574.29, ...}.
      --run-dir         required; writes <run-dir>/holdings.json.
      --base-dir        required; reads state.json for prior-holdings drop detection only.
    """
    snap = load_json(args.snapshot_json)
    if not snap or "holdings" not in snap:
        fail(f"--snapshot-json does not look like a networth_holdings result (no 'holdings' key): {args.snapshot_json}")
    live_quotes_raw = load_json(args.live_quotes_json, default={}) if args.live_quotes_json else {}
    usdinr = args.usdinr
    state = load_json(os.path.join(args.base_dir, "state.json"), default={}) or {}

    def _live_for(ticker):
        v = live_quotes_raw.get(ticker)
        if v is None:
            return None, None
        if isinstance(v, dict):
            return v.get("price"), v.get("changePct")
        return v, None  # bare price, no change% available

    rows, no_live_quote = [], []
    for h in snap["holdings"]:
        ticker = h.get("investment_code")
        if not ticker:
            continue
        qty = h.get("total_units") or 0.0
        invested_usd = h.get("invested_value_usd") or 0.0
        current_usd = h.get("current_value_usd") or 0.0
        live_price, live_chg_pct = _live_for(ticker)
        if live_price is not None and qty:
            current_usd = qty * live_price
        if live_chg_pct is not None:
            day_chg_pct = round(live_chg_pct * 100, 4)
        else:
            no_live_quote.append(ticker)
            # degrade to the snapshot's own day-change, not to null -- a partial live-quote
            # fetch should not silently blank out every OTHER row's bucket classification too
            one_day_change_usd = h.get("one_day_change_usd")
            day_chg_pct = (round(100.0 * one_day_change_usd / (current_usd - one_day_change_usd), 4)
                          if one_day_change_usd is not None and current_usd != one_day_change_usd
                          else None)
        rows.append({
            "ticker": ticker, "name": h.get("investment") or ticker, "qty": qty,
            "market_value_inr": round(current_usd * usdinr, 4),
            "invested_inr": round(invested_usd * usdinr, 4),
            "weight_pct": None,  # filled below, after the full row set is known
            "pnl_pct": (round(100.0 * (current_usd - invested_usd) / invested_usd, 4)
                       if invested_usd else None),
            "price_usd": round(current_usd / qty, 4) if qty else None,
            "day_chg_pct": day_chg_pct,
            "market_cap": h.get("market_cap", "large"),
            "live_price_usd": round(live_price, 4) if live_price is not None else (
                round(current_usd / qty, 4) if qty else None),
        })

    total_val_usd = sum(r["market_value_inr"] for r in rows) / usdinr
    for r in rows:
        r["weight_pct"] = round(100.0 * (r["market_value_inr"] / usdinr) / total_val_usd, 4) if total_val_usd else 0.0

    live_quotes_out = {t: (v.get("price") if isinstance(v, dict) else v)
                       for t, v in live_quotes_raw.items()}
    for r in rows:
        live_quotes_out.setdefault(r["ticker"], r["live_price_usd"])

    # DROP DETECTION -- the whole point of this rewrite. Never guess; always name.
    prior_tickers = {h.get("ticker") for h in (state.get("holdings") or []) if h.get("ticker")}
    current_tickers = {r["ticker"] for r in rows}
    dropped = sorted(prior_tickers - current_tickers)

    # QTY CHANGES, emitted HERE (added 2026-09-14) so the ledger pipeline can record this run's
    # fills BEFORE `pipeline` runs. Until now the only qty diff came out of `book`, i.e. after
    # the lots/book/triggers stages had already been computed from the previous trades.json.
    prior_qty = {h.get("ticker"): float(h.get("qty") or 0) for h in (state.get("holdings") or [])
                 if h.get("ticker")}
    qty_changes = []
    for t in sorted(current_tickers | prior_tickers):
        now_q = next((float(r["qty"] or 0) for r in rows if r["ticker"] == t), 0.0)
        was_q = prior_qty.get(t, 0.0)
        if abs(now_q - was_q) > 1e-6:
            qty_changes.append({"ticker": t, "prior_qty": was_q, "qty": now_q,
                                "qty_diff": round(now_q - was_q, 6)})

    wallet_usd = args.wallet_usd or 0.0
    invested_total_usd = sum(h.get("invested_value_usd") or 0.0 for h in snap["holdings"])
    snap_agg = (snap.get("asset_summary") or {}).get("total_value_usd")
    if args.aggregate_usd is not None:
        aggregate_usd, aggregate_source = args.aggregate_usd, "cli"
    elif snap_agg is not None:
        aggregate_usd, aggregate_source = snap_agg, "snapshot"
    else:
        # No independent aggregate: cmd_book's G3 divergence check would compare the rows with
        # themselves. Say so instead of letting a toothless check read as a passed one.
        aggregate_usd, aggregate_source = total_val_usd, "rows (no independent aggregate)"

    holdings_doc = {
        "ts": args.ts or iso_utc(),
        "usdinr": usdinr,
        "market_session": args.market_session,
        "gate_classification": args.gate_classification,
        "gate_reason": args.gate_reason,
        "holdings_inr": rows,
        "live_quotes": live_quotes_out,
        "totals": {
            "current_value_inr_from_snapshot": round(total_val_usd * usdinr, 4),
            "invested_inr": round(invested_total_usd * usdinr, 4),
            "wallet_inr": round(wallet_usd * usdinr, 4),
            "aggregate_value_inr": round(aggregate_usd * usdinr, 4),
            "rows_sum_inr": round(sum(r["market_value_inr"] for r in rows), 4),
            "pnl_pct": (round(100.0 * (total_val_usd * usdinr - invested_total_usd * usdinr) / (invested_total_usd * usdinr), 4)
                       if invested_total_usd else None),
            "count": len(rows),
        },
        "macro_strip": load_json(args.macro_json, default={}) if args.macro_json else {},
        "benchmarks": load_json(args.benchmarks_json, default={}) if args.benchmarks_json else {},
        "dropped_since_last_run": dropped,
        "qty_changes": qty_changes,
        "aggregate_source": aggregate_source,
        "no_live_quote": sorted(set(no_live_quote)),
    }
    if dropped:
        holdings_doc["price_overlay_note"] = (
            f"dropped_since_last_run={dropped}: present in the prior run's holdings, absent from "
            f"this snapshot. NOT carried forward, NOT assumed sold -- resolve via the LEDGER "
            f"trigger (search transaction-confirmation emails / ledger-parse) before writing a "
            f"briefing that treats these as exits.")

    out_path = os.path.join(args.run_dir, "holdings.json")
    atomic_write_json(out_path, holdings_doc)

    emit({"written": out_path, "rows": len(rows), "total_value_usd": round(total_val_usd, 2),
          "dropped_since_last_run": dropped, "no_live_quote": sorted(set(no_live_quote)),
          "qty_changes": qty_changes, "aggregate_source": aggregate_source,
          "next_step": ("qty_changes non-empty: run the LEDGER pipeline (ledger-parse -> "
                        "ledger-apply) BEFORE `pipeline`" if qty_changes else None),
          "weights_sum_check": round(sum(r["weight_pct"] for r in rows), 4)})


# ---------------------------------------------------------------------------
# book
# ---------------------------------------------------------------------------
USDINR_PLAUSIBLE = (70.0, 120.0)
WEIGHTS_SUM_TOLERANCE_PCT = 0.5
BOOK_MOVE_TOLERANCE_PCT = 15.0


def _last_ledger_row(base_dir):
    import csv
    try:
        with open(os.path.join(base_dir, "ledger.csv"), newline="") as fh:
            rows = list(csv.DictReader(fh))
    except OSError:
        return None
    return rows[-1] if rows else None


def cmd_book(args):
    holdings = load_json(os.path.join(args.run_dir, "holdings.json"))
    state = load_json(os.path.join(args.base_dir, "state.json"), default={})
    lots = load_json(args.lots, default={}) if args.lots else load_json(
        os.path.join(args.base_dir, "lots.json"), default={})

    usdinr = holdings["usdinr"]
    rows = holdings["holdings_inr"]
    totals = holdings["totals"]

    # FIXED 2026-07-28 (G3): reconcile the row-level sum against whatever aggregate figure the
    # snapshot reported. INDmoney's aggregate US_STOCK endpoint lags the per-name feed -- observed
    # 12.2% divergence on 2026-07-27 and 4.1% on 2026-07-28. Persisting an aggregate that disagrees
    # with the rows silently corrupts every downstream weight, so the divergence is measured here and
    # persist_safe is flipped false above a 3% tolerance. The orchestrator must not write state.json
    # or append a ledger row when persist_safe is false.
    row_sum_inr = sum(r.get("market_value_inr", 0) for r in rows)
    snapshot_inr = totals["current_value_inr_from_snapshot"]
    aggregate_inr = totals.get("aggregate_value_inr")
    recon = {"row_sum_inr": round(row_sum_inr, 2), "snapshot_inr": round(snapshot_inr, 2),
             "aggregate_inr": round(aggregate_inr, 2) if aggregate_inr else None,
             "tolerance_pct": 3.0}
    persist_safe = True
    for label, other in (("snapshot", snapshot_inr), ("aggregate", aggregate_inr)):
        if not other or not row_sum_inr:
            continue
        div = abs(other - row_sum_inr) / row_sum_inr * 100
        recon[f"{label}_divergence_pct"] = round(div, 3)
        if div > recon["tolerance_pct"]:
            persist_safe = False
            recon.setdefault("breaches", []).append(
                f"{label} differs from row-level sum by {div:.2f}% (tolerance 3%) -- G3 pattern")
    recon["persist_safe"] = persist_safe

    # ADDED 2026-08-07 (G32): when rows and aggregate disagree, say WHICH ONE IS WRONG.
    # Until now the script only reported *that* they diverged and blocked the persist, leaving the
    # orchestrator to guess. The guess has direction risk: G3 was aggregate-lags-rows, but the three
    # 2026-07-29/30 recurrences were the OPPOSITE (rows stale up to 79.5% on a name, aggregate live
    # and within 0.22% of a from-scratch reconstruction). Defaulting to either source is wrong half
    # the time. This script is stdlib-only and cannot fetch quotes, so the orchestrator passes what
    # it already pulled in step 2.5/2.5b as holdings.json["live_quotes"] = {TICKER: price_usd}, and
    # the arbitration is done here deterministically instead of by narrative judgement.
    live_quotes = holdings.get("live_quotes") or {}
    if live_quotes and row_sum_inr:
        priced, unpriced, live_sum_inr = [], [], 0.0
        for r in rows:
            px, qty = live_quotes.get(r["ticker"]), r.get("qty")
            if px and qty:
                live_sum_inr += qty * px * usdinr
                priced.append(r["ticker"])
            else:
                unpriced.append(r["ticker"])
        coverage = len(priced) / len(rows) * 100 if rows else 0.0
        arb = {"live_sum_inr": round(live_sum_inr, 2), "coverage_pct": round(coverage, 1),
               "unpriced": unpriced}
        if coverage >= 90.0 and live_sum_inr:
            d_rows = abs(row_sum_inr - live_sum_inr) / live_sum_inr * 100
            arb["rows_vs_live_pct"] = round(d_rows, 3)
            if aggregate_inr:
                d_agg = abs(aggregate_inr - live_sum_inr) / live_sum_inr * 100
                arb["aggregate_vs_live_pct"] = round(d_agg, 3)
                # whichever source tracks live is the trustworthy one
                if abs(d_rows - d_agg) < 1.0:
                    if max(d_rows, d_agg) <= recon["tolerance_pct"]:
                        arb["verdict"] = "both_agree_with_live"
                        arb["note"] = "rows and aggregate both track live within tolerance -- healthy"
                    else:
                        arb["verdict"] = "inconclusive"
                        arb["note"] = ("rows and aggregate are about equally far from live -- the "
                                       "divergence is not a one-sided stale feed; investigate "
                                       "before persisting")
                elif d_rows < d_agg:
                    arb["verdict"] = "aggregate_stale"
                    arb["trust"] = "rows"
                else:
                    arb["verdict"] = "rows_stale"
                    arb["trust"] = "aggregate"
            else:
                arb["verdict"] = "rows_only_checked"
                arb["trust"] = "rows" if d_rows <= 3.0 else "neither"
        else:
            arb["verdict"] = "insufficient_coverage"
            arb["note"] = (f"live quotes cover only {coverage:.0f}% of rows (need >=90%) -- "
                           "not enough to arbitrate; no direction inferred")
        recon["live_arbitration"] = arb
        # A confident arbitration turns a blocked persist into a usable one, but ONLY by telling the
        # orchestrator which source to rebuild from -- it never silently re-enables the write.
        if not persist_safe and arb.get("trust") in ("rows", "aggregate"):
            recon.setdefault("breaches", []).append(
                f"ARBITRATED: {arb['verdict']} -- rebuild holdings.json from '{arb['trust']}' "
                f"(or from live quotes directly) and re-run; persist stays blocked until the "
                f"row-vs-aggregate divergence is actually resolved, not merely explained")

    value_usd = round(totals["current_value_inr_from_snapshot"] / usdinr, 2)
    wallet_usd = round(totals.get("wallet_inr", 0) / usdinr, 2)
    total_book_usd = value_usd + wallet_usd
    count = totals.get("count", len(rows))
    pnl_pct = totals.get("pnl_pct")

    prior_us = state.get("us", {})
    prior_usdinr = prior_us.get("usdinr") or state.get("usdinr")
    usdinr_drift_pct = None
    if prior_usdinr:
        usdinr_drift_pct = round((usdinr - prior_usdinr) / prior_usdinr * 100, 3)

    positions = []
    for r in rows:
        w = r["weight_pct"]
        price_usd = None
        if r.get("qty"):
            price_usd = round(r["market_value_inr"] / r["qty"] / usdinr, 4)
        positions.append({
            "ticker": r["ticker"], "weight_pct": round(w, 3),
            "market_value_usd": round(r["market_value_inr"] / usdinr, 2),
            "qty": r.get("qty"), "price_usd": price_usd,
            "day_chg_pct": r.get("day_chg_pct"),
            "market_cap": r.get("market_cap", ""),
        })
    positions.sort(key=lambda p: -p["weight_pct"])

    top3 = [{"ticker": p["ticker"], "weight_pct": p["weight_pct"]} for p in positions[:3]]
    top5_pct = round(sum(p["weight_pct"] for p in positions[:5]), 3)

    # Weighted day-change (added 2026-08-06, dashboard feature review): holdings.json's
    # day_chg_pct is OPTIONAL per position -- an orchestrator fetching from a source without
    # per-name day-change (e.g. a refresher using only INDmoney's row-level market_value, no
    # yfinance overlay) simply omits it, and this degrades to None rather than a wrong number.
    # Weight is renormalized to only the positions that DO carry a day_chg_pct, so a partial
    # supply doesn't silently understate the true day move.
    dchg_weight = sum(p["weight_pct"] for p in positions if p.get("day_chg_pct") is not None)
    day_chg_pct_weighted = (
        round(sum(p["weight_pct"] * p["day_chg_pct"] for p in positions if p.get("day_chg_pct") is not None)
              / dchg_weight, 3)
        if dchg_weight else None)
    top10_pct = round(sum(p["weight_pct"] for p in positions[:10]), 3)

    data_cache = state.get("data_cache", {})
    betas_cache = data_cache.get("betas", {})
    beta_missing = []
    weighted_beta_sum = 0.0
    risk_rows = []
    for p in positions:
        b = betas_cache.get(p["ticker"])
        if b is None:
            b = 1.0
            beta_missing.append(p["ticker"])
        elif isinstance(b, dict):
            b = b.get("value")
            if b is None:
                b = 1.0
                beta_missing.append(p["ticker"])
        contrib = (p["weight_pct"] / 100.0) * b
        weighted_beta_sum += contrib
        risk_rows.append({"ticker": p["ticker"], "weight_pct": p["weight_pct"], "beta": b, "risk_contrib": contrib})

    portfolio_beta = round(weighted_beta_sum, 3)
    total_risk = sum(r["risk_contrib"] for r in risk_rows) or 1.0
    for r in risk_rows:
        r["risk_pct"] = round(r["risk_contrib"] / total_risk * 100, 2)
        del r["risk_contrib"]
    risk_rows.sort(key=lambda r: -r["risk_pct"])
    risk_concentration = risk_rows[:5]

    # Extract benchmark betas (TIER 2.5: SOX/SMH primary, SPX secondary)
    bench_betas = data_cache.get("benchmark_betas", {})
    sox_beta = bench_betas.get("SOX", {}).get("value")
    smh_beta = bench_betas.get("SMH", {}).get("value")
    spx_beta = bench_betas.get("SPX", {}).get("value")
    primary_benchmark = {
        "benchmark": "SOX/SMH",
        "primary_beta": sox_beta or smh_beta,
        "peer_etf": "SMH",
        "secondary_spx_beta": spx_beta,
        "note": "SOX is the true factor; SPX beta is misleading. Use SOX/SMH for all sizing/stress decisions."
    }

    over_cap = []  # populated by caller against policy; report raw >10% here as a generic flag
    over_10pct = [{"ticker": p["ticker"], "weight_pct": p["weight_pct"]} for p in positions if p["weight_pct"] > 10]

    # FIXED 2026-07-26: drawdown must be measured on TOTAL BOOK (equity+cash), not equity alone.
    # Equity-only peak/drawdown conflates market loss with deliberate cash conversion -- a move
    # from equity into cash (e.g. the 07-24 de-risking) reads as an enormous equity "drawdown"
    # even though total book barely moved. This is the same denominator-mixing defect as G28,
    # just in the drawdown path instead of the cluster-target path. peak_total_book_usd is
    # tracked alongside (not instead of) the legacy peak_value_usd field for backward visibility.
    peak_value_usd = max(prior_us.get("peak_value_usd", value_usd), value_usd)  # legacy, equity-only -- kept for continuity, not used for drawdown_pct below
    prior_peak_total_book = prior_us.get("peak_total_book_usd")
    if prior_peak_total_book is None:
        # bootstrap: no prior peak recorded -- try to reconstruct from prior_us if it predates this fix,
        # otherwise seed from today's total_book_usd (first observation becomes the peak)
        prior_peak_total_book = (prior_us.get("value_usd", 0) or 0) + (prior_us.get("wallet_usd", 0) or 0)
    peak_total_book_usd = max(prior_peak_total_book, total_book_usd) if prior_peak_total_book else total_book_usd
    drawdown_pct = round((total_book_usd - peak_total_book_usd) / peak_total_book_usd * 100, 3) if peak_total_book_usd else 0.0

    wallet_pct = round(wallet_usd / total_book_usd * 100, 3) if total_book_usd else 0.0

    market_cap_alloc = {}
    for p in positions:
        mc = p["market_cap"] or "Unclassified"
        market_cap_alloc[mc] = round(market_cap_alloc.get(mc, 0) + p["weight_pct"], 3)

    ltcg_flags = []
    ltcg_boundary_months = policy_ltcg_months(load_json(os.path.join(args.base_dir, "policy.json"), default={}))
    today = desk_today()
    lots = dict(smith_risk.data_entries(lots, value_type=list))   # one canonical filter (2026-08-16)
    if lots:
        for ticker, lot_list in lots.items():
            for lot in lot_list:
                try:
                    lot_date = datetime.strptime(lot["date"], "%Y-%m-%d").date()
                except (KeyError, ValueError, TypeError):
                    continue
                months_to_ltcg = months_until_ltcg(lot_date, today, ltcg_boundary_months)
                if months_to_ltcg <= 6:
                    ltcg_flags.append({
                        "ticker": ticker, "qty": lot.get("qty"),
                        "months_to_ltcg": months_to_ltcg,
                        "note": "past LTCG boundary" if months_to_ltcg <= 0 else "approaching LTCG boundary",
                    })

    # rough net-flow estimate vs prior state holdings (qty deltas x current price)
    # FIXED 2026-07-26: now catches full exits and new entries, not just qty changes on common holdings
    prior_holdings = {h["ticker"]: h for h in state.get("holdings", [])}
    current_holdings = {p["ticker"]: p for p in positions}
    est_net_flows_usd = 0.0
    qty_changes = []

    # track qty changes on existing positions
    for p in positions:
        prior = prior_holdings.get(p["ticker"])
        if prior is None:
            continue
        prior_qty = prior.get("qty")
        if prior_qty is None or p["qty"] is None:
            continue
        qty_diff = p["qty"] - prior_qty
        if abs(qty_diff) < 1e-6:
            continue
        ratio = p["qty"] / prior_qty if prior_qty else None
        is_split_like = ratio is not None and abs(ratio - round(ratio)) < 0.02 and round(ratio) != 1
        qty_changes.append({
            "ticker": p["ticker"], "prior_qty": prior_qty, "current_qty": p["qty"],
            "ratio": round(ratio, 4) if ratio else None,
            "likely_corporate_action": bool(is_split_like),
        })
        if not is_split_like and p["price_usd"]:
            est_net_flows_usd += qty_diff * p["price_usd"]

    # FIXED 2026-08-07 (G41): the two loops below append to qty_changes but historically never
    # touched est_net_flows_usd, so only qty changes on CONTINUING holdings were counted as flow.
    # Verified against the 2026-08-03 run: est_net_flows_usd read $810.37, which is exactly the
    # TSM +2sh add and nothing else -- the four new entries (META/AMZN/BABA/QBTS, ~$1,678 out)
    # and IREN's full exit (~$360 in) were both silently dropped into
    # compute_attribution.json's residual_market_move_usd, misattributing cash movement as
    # market performance. New entries are exactly priceable (they're in `positions`); exits are
    # not (the row is gone), so exit proceeds fall back to the LAST KNOWN price from the prior
    # run's compute_book.json and are labelled as such -- never estimated or interpolated.
    _prior_run_prices._current = args.run_dir
    prior_prices = _prior_run_prices(args.base_dir, state.get("last_run_dir"), state)

    flow_components = {"adds_trims_usd": round(est_net_flows_usd, 2), "new_entries_usd": 0.0,
                       "exits_usd": 0.0, "exits_unpriced": [], "exit_price_basis": "last_known_price_prior_run"}

    # track full exits (in prior, not in current) -- proceeds are a cash INFLOW (negative net flow)
    for prior in state.get("holdings", []):
        if prior["ticker"] not in current_holdings:
            exit_qty = prior.get("qty") or 0.0
            exit_px = prior_prices.get(prior["ticker"])
            entry = {
                "ticker": prior["ticker"], "prior_qty": prior.get("qty"), "current_qty": 0.0,
                "ratio": 0.0, "likely_corporate_action": False,
            }
            if exit_px and exit_qty:
                proceeds = exit_qty * exit_px
                est_net_flows_usd -= proceeds
                flow_components["exits_usd"] = round(flow_components["exits_usd"] - proceeds, 2)
                entry["est_proceeds_usd"] = round(proceeds, 2)
                entry["price_basis"] = "last_known_price_prior_run"
            else:
                flow_components["exits_unpriced"].append(prior["ticker"])
            qty_changes.append(entry)

    # track new entries (in current, not in prior) -- purchases are a cash OUTFLOW (positive net flow)
    for p in positions:
        if p["ticker"] not in prior_holdings:
            entry = {
                "ticker": p["ticker"], "prior_qty": 0.0, "current_qty": p["qty"],
                "ratio": None, "likely_corporate_action": False,
            }
            if p["price_usd"] and p["qty"]:
                cost = p["qty"] * p["price_usd"]
                est_net_flows_usd += cost
                flow_components["new_entries_usd"] = round(flow_components["new_entries_usd"] + cost, 2)
                entry["est_cost_usd"] = round(cost, 2)
            qty_changes.append(entry)

    # load trade rationales from trades.json if present (FIXED 1.2: 2026-07-26)
    #
    # FIXED 2026-08-15 (found by smith-ledger). The prior implementation built a bare
    # ticker -> reason map by LAST-WRITE-WINS over the entire trade history, with no date and
    # no direction check:
    #     for trade in trades: trade_reasons[trade["ticker"]] = trade["reason"]
    # So any ticker whose newest fill was not yet recorded in trades.json inherited the reason
    # of its most recent PRIOR, unrelated trade. On this run that stamped four positions
    # OPENING from zero (IREN, VRT, BE, GLW) with "stop-loss" -- each name's previous exit --
    # and labelled a genuine AMAT stop-loss sale "deploy-excess-cash". A position opening
    # cannot be a stop-loss; the label was not merely stale, it was categorically impossible,
    # and it fed the briefing and the strategist's context.
    #
    # Two guards now, both cheap:
    #   1. DIRECTION must agree. A qty increase only accepts a buy-side row, a decrease only a
    #      sell-side row. This alone kills the impossible-label class.
    #   2. RECENCY. Only rows dated at/after the previous run's timestamp can explain a change
    #      observed since that run. Older rows describe a different event.
    # No match -> emit "UNMATCHED" rather than borrowing someone else's reason. An honest gap
    # is recoverable; a confident wrong label is what actually did damage.
    trades = load_json(os.path.join(args.base_dir, "trades.json"), default={})
    prior_ts = _proposal_parse_date((state.get("ts") or "")[:10])

    def _sign_of(trade):
        """+1 buy-side, -1 sell-side, 0 unknown. qty_change is authoritative; the action verb
        is the fallback because action strings have drifted (add/entry/buy, trim/exit/sell)."""
        q = trade.get("qty_change")
        if isinstance(q, (int, float)) and q:
            return 1 if q > 0 else -1
        verb = str(trade.get("action", "")).strip().lower()
        if verb.startswith(("buy", "add", "entry", "re-entry", "initiate")):
            return 1
        if verb.startswith(("sell", "trim", "exit", "reduce", "close")):
            return -1
        return 0

    for qc in qty_changes:
        # Direction of the observed change. NOTE cmd_book's rows carry prior_qty/current_qty
        # (cmd_attribution's carry qty_diff) -- derive from whichever is present rather than
        # assuming one shape. Getting this wrong silently defaults every row to "sell", which
        # is how the first cut of this fix still mislabelled six buys as UNMATCHED.
        if qc.get("qty_diff") is not None:
            delta = qc["qty_diff"]
        else:
            delta = (qc.get("current_qty") or 0) - (qc.get("prior_qty") or 0)
        want = 1 if delta > 0 else -1
        best, best_d = None, None
        for trade in trades.get("trades", []):
            if trade.get("ticker") != qc["ticker"]:
                continue
            if trade.get("type") == "corporate_action":
                continue  # a conversion/split is not a trade and has no rationale to capture
            if _sign_of(trade) != want:
                continue
            d = _proposal_parse_date(trade.get("date", ""))
            if prior_ts and d and d < prior_ts:
                continue  # predates this window -- describes a different event
            if best_d is None or (d and d >= best_d):
                best, best_d = trade, d
        qc["trade_reason"] = (best.get("reason", "UNCAPTURED") if best else "UNMATCHED")
        if best_d:
            qc["trade_reason_date"] = str(best_d)

    # SANITY GATE, in code (moved from SKILL.md prose 2026-09-14 -- it was placed before the data
    # it checks existed and was applied by eye). Each failure is a named breach.
    rows_weighted = [r.get("weight_pct") for r in rows]
    if rows and all(isinstance(w, (int, float)) for w in rows_weighted):
        wsum = sum(rows_weighted)
        recon["weights_sum_pct"] = round(wsum, 3)
        if abs(wsum - 100.0) > WEIGHTS_SUM_TOLERANCE_PCT:
            persist_safe = False
            recon.setdefault("breaches", []).append(
                f"row weights sum to {wsum:.2f}% (tolerance 100 +/- {WEIGHTS_SUM_TOLERANCE_PCT})")
    if not (USDINR_PLAUSIBLE[0] <= usdinr <= USDINR_PLAUSIBLE[1]):
        persist_safe = False
        recon.setdefault("breaches", []).append(
            f"USD/INR {usdinr} outside the plausible band {USDINR_PLAUSIBLE[0]}-{USDINR_PLAUSIBLE[1]}")
    prev_row = _last_ledger_row(args.base_dir)
    try:
        prev_total = (float(prev_row["value_usd"]) + float(prev_row.get("wallet_usd") or 0)
                      if prev_row and prev_row.get("value_trust", "ok") == "ok" else None)
    except (TypeError, ValueError, KeyError):
        prev_total = None
    if prev_total:
        move = 100.0 * (total_book_usd - prev_total) / prev_total
        recon["total_book_move_vs_last_row_pct"] = round(move, 3)
        if abs(move) > BOOK_MOVE_TOLERANCE_PCT and not qty_changes:
            persist_safe = False
            recon.setdefault("breaches", []).append(
                f"total book moved {move:+.1f}% since the last ledger row with no qty change to "
                f"explain it (tolerance {BOOK_MOVE_TOLERANCE_PCT}%) -- a stale or partial snapshot")
    recon["persist_safe"] = persist_safe

    data_quality = []
    if not recon["persist_safe"]:
        data_quality.append("PERSIST BLOCKED (G3): " + "; ".join(recon.get("breaches", [])))
    if beta_missing:
        data_quality.append(f"betas defaulted to 1.0 for {len(beta_missing)} names (no data_cache entry): {', '.join(beta_missing[:8])}{'...' if len(beta_missing) > 8 else ''}")
    if not lots:
        data_quality.append("lots.json absent/empty -- LTCG flags unavailable (standing gap)")
    if flow_components["exits_unpriced"]:
        data_quality.append(
            "est_net_flows_usd EXCLUDES proceeds for fully-exited "
            f"{', '.join(flow_components['exits_unpriced'])} -- no last-known price in the prior run's "
            "compute_book.json, and an exit price is never estimated (G41)")

    emit({
        "value_usd": value_usd, "pnl_pct": pnl_pct, "day_chg_pct_weighted": day_chg_pct_weighted,
        "count": count,
        "usdinr": usdinr, "usdinr_drift_pct": usdinr_drift_pct,
        "top3": top3, "top5_pct": top5_pct, "top10_pct": top10_pct,
        "over_10pct": over_10pct, "beta": portfolio_beta, "primary_benchmark": primary_benchmark,
        "risk_concentration": risk_concentration,
        "peak_value_usd": round(peak_value_usd, 2),
        "peak_total_book_usd": round(peak_total_book_usd, 2),
        "total_book_usd": round(total_book_usd, 2),
        "drawdown_pct": drawdown_pct,
        "drawdown_basis": "total_book",
        "wallet_usd": wallet_usd, "wallet_pct": wallet_pct,
        "ltcg_flags": ltcg_flags,
        "market_cap_allocation": market_cap_alloc,
        "reconciliation": recon,
        "persist_safe": persist_safe,
        "qty_changes": qty_changes, "est_net_flows_usd": round(est_net_flows_usd, 2),
        "flow_components": flow_components,
        "positions": positions,
        "data_quality": data_quality,
    })


# ---------------------------------------------------------------------------
# risk -- ATR-based per-name stop/cap/headroom (G34: was hand-authored once,
# never in scripts/; formula lives in smith_risk.py, shared with the treemap)
# ---------------------------------------------------------------------------
def cmd_risk(args):
    book = load_json(os.path.join(args.run_dir, "compute_book.json"))
    state = load_json(os.path.join(args.base_dir, "state.json"), default={})
    policy = load_json(os.path.join(args.base_dir, "policy.json"), default={})

    total_book_usd = book.get("total_book_usd")
    sector_map = state.get("sector_map", {})
    atr_cache = state.get("data_cache", {}).get("atr20", {}).get("values_pct", {})
    betas_cache = state.get("data_cache", {}).get("betas", {})

    # The measured mid-tier stop multiple, offered as an ADVISORY learned_stop on each mid-vol
    # position (Phase 3): reachable for the first time. Never changes a stop, cap or size.
    learning_store = load_json(os.path.join(args.base_dir, "learning.json"), default={}) or {}
    missing_atr, missing_beta = [], []
    rows = []
    agg_open_risk_usd = 0.0
    for p in book.get("positions", []):
        ticker = p["ticker"]
        atr_pct = atr_cache.get(ticker)
        if atr_pct is None:
            missing_atr.append(ticker)
        beta_entry = betas_cache.get(ticker)
        beta = beta_entry.get("value") if isinstance(beta_entry, dict) else beta_entry
        if beta is None:
            missing_beta.append(ticker)

        r = smith_risk.stop_and_cap(atr_pct, p.get("price_usd"), p.get("qty"), total_book_usd, policy,
                                    learned_multiple=smith_risk.learned_stop_multiple_for(atr_pct, learning_store))
        r["ticker"] = ticker
        r["cluster"] = sector_map.get(ticker, "Unclassified")
        r["beta"] = beta
        rows.append(r)
        if r["position_open_risk_usd"]:
            agg_open_risk_usd += r["position_open_risk_usd"]

    agg_cap_pct = (policy.get("stop_loss_framework", {}) or {}).get("aggregate_open_risk_cap_pct_of_book",
                   policy.get("aggregate_open_risk_cap_pct_of_book"))
    agg_open_risk_pct = round(agg_open_risk_usd / total_book_usd * 100, 3) if total_book_usd else None

    data_quality = []
    if missing_atr:
        data_quality.append(f"ATR20 missing for {len(missing_atr)} held names (no data_cache entry): "
                             f"{', '.join(missing_atr)} -- stop/cap/headroom left null, never estimated")
    if missing_beta:
        data_quality.append(f"beta missing for {len(missing_beta)} held names: {', '.join(missing_beta)}")

    emit({
        "total_book_usd": total_book_usd,
        "positions": rows,
        "aggregate_open_risk_usd": round(agg_open_risk_usd, 2),
        "aggregate_open_risk_pct": agg_open_risk_pct,
        "aggregate_open_risk_cap_pct": agg_cap_pct,
        "aggregate_over_cap": bool(agg_cap_pct is not None and agg_open_risk_pct is not None
                                    and agg_open_risk_pct > agg_cap_pct),
        "missing_atr": missing_atr, "missing_beta": missing_beta,
        "data_quality": data_quality,
    })


# ---------------------------------------------------------------------------
# journal
# ---------------------------------------------------------------------------
def cmd_journal(args):
    journal = load_json(os.path.join(args.base_dir, "journal.json"), default={"entries": []})
    holdings = load_json(os.path.join(args.run_dir, "holdings.json"))
    usdinr = holdings["usdinr"]
    price_by_ticker = {}
    for r in holdings["holdings_inr"]:
        if r.get("qty"):
            price_by_ticker[r["ticker"]] = r["market_value_inr"] / r["qty"] / usdinr

    # Injected prices for EXITED tickers (added 2026-08-25, self-learning Phase 1). Without
    # this, an entry for a ticker no longer held can never price -- current_price stays None
    # forever, verdict stays "open" forever. Original hypothesis going in was that this biases
    # every hit rate optimistic (losers get excluded); VERIFIED WRONG on first real backfill
    # (16 tickers, 14 newly-scoreable entries): TARGET GAP moved 23.1%->36.8% (n=13->19) as
    # excluded WINNERS like IREN +10.8%, LITE +15.2%, ORCL +17.8% (x2), DLR +4.5% came back in,
    # while MOMENTUM+VOLUME stayed flat at 0% (n=7->11). The real defect isn't a uniform
    # direction, it's that EXCLUSION ITSELF is non-random -- an exited name got there via a
    # stop-out or a deliberate exit, which correlates with volatile price action in EITHER
    # direction, not uniformly bad. Corrected as a lesson (see learn-add-lesson); don't assume
    # a direction when reasoning about this fix elsewhere. Injected values win on collision (an
    # explicit fetch is fresher than a snapshot derived from this run's holdings), matching
    # cmd_score/cmd_stops' existing --prices-json contract exactly, including the same
    # probe-with-{} discovery idiom.
    injected = {}
    if args.prices_json:
        injected = load_json(args.prices_json, default={})
    price_by_ticker = {**price_by_ticker, **injected}

    today = resolve_today(args.today)

    prior_by_key = {}
    for e in journal.get("entries", []):
        prior_by_key[(e.get("date"), e.get("ticker"), e.get("bucket"))] = e

    updates = []
    bucket_scores = {}  # bucket -> [worked/failed/neutral bools at 30d]
    name_bucket_scores = {}  # (ticker,bucket) -> list of (verdict, n) pairs -- see grade() below
    bucket_scores_7d = {}  # same, at 7d -- interim read, see bucket_hit_rates_7d below
    # bucket -> {"worked": [signed_pct, ...], "failed": [signed_pct, ...]} -- added 2026-09-07
    # for the Kelly-informed track_record_multiplier tilt (smith_conviction.py). bucket_scores
    # above only ever counted win/loss, never MAGNITUDE, so a signal that wins small and loses
    # big looked identical to one that wins big and loses small -- this is the payoff-ratio
    # data Kelly's formula needs and the plain hit-rate tilt structurally can't use.
    bucket_score_magnitudes = {}
    needs_price = set()  # tickers with an open entry and no price -- surfaced so the caller
                         # knows exactly which exited names to fetch and re-run with

    for e in journal.get("entries", []):
        try:
            flag_date = datetime.strptime(e["date"], "%Y-%m-%d").date()
        except (KeyError, ValueError):
            continue
        days_old = (today - flag_date).days
        key = (e.get("date"), e.get("ticker"), e.get("bucket"))
        prior = prior_by_key.get(key, {})

        # LOCK ON FIRST SCORE (added 2026-08-25, fixes the "no scoring window" defect): once an
        # outcome has been scored, it is NEVER recomputed against a later price. Before this
        # fix, outcome_30d_pct always compared flag price to TODAY's price regardless of
        # days_old -- a 44-day-old entry got scored on a 44-day move and labelled "30d" anyway,
        # because cmd_journal rebuilds bucket_scores from scratch every run with no memory of
        # what price it scored against last time. Locking means the number an entry is scored
        # on is fixed at (approximately) the day it first crosses the 7d/30d line, not whatever
        # day this command happens to run again.
        out = {"date": e["date"], "ticker": e["ticker"], "bucket": e["bucket"],
               "days_old": days_old,
               "outcome_7d_pct": prior.get("outcome_7d_pct"),
               "outcome_30d_pct": prior.get("outcome_30d_pct"),
               "verdict": prior.get("verdict", "open")}
        already_locked_30d = prior.get("outcome_30d_pct") is not None
        already_locked_7d = prior.get("outcome_7d_pct") is not None

        # MIGRATION BACKFILL (2026-08-25): entries locked before `_verdict_7d` existed as a
        # field have outcome_7d_pct set but no cached verdict label. The pct is already locked
        # -- re-deriving the LABEL from it is not a new price read, just recovering information
        # that was always computable from what's already stored, so this is a one-time backfill
        # rather than a re-score. Runs exactly once per entry: after this, _verdict_7d exists
        # and the branch below never re-enters this path for that entry again.
        if already_locked_7d and not prior.get("_verdict_7d"):
            d7 = BUCKET_DIRECTION.get(e["bucket"])
            if d7 is not None and prior.get("outcome_7d_pct") is not None:
                s7 = prior["outcome_7d_pct"] if d7 == "up" else -prior["outcome_7d_pct"]
                prior = dict(prior)  # don't mutate the loaded journal in place
                prior["_verdict_7d"] = ("worked" if s7 > VERDICT_THRESHOLD_PCT
                                        else "failed" if s7 < -VERDICT_THRESHOLD_PCT else "neutral")

        current_price = price_by_ticker.get(e["ticker"])
        if current_price is None or not e.get("price_at_flag"):
            if out["verdict"] == "open":
                needs_price.add(e["ticker"])
            # Still re-tally anything ALREADY locked, regardless of whether this run can price
            # the ticker -- an entry locked while the name was still held (e.g. its 7d verdict)
            # must keep counting even after the name later exits and this run can't re-price it.
            if prior.get("_verdict_7d"):
                out["_verdict_7d"] = prior["_verdict_7d"]
                bucket_scores_7d.setdefault(e["bucket"], []).append(prior["_verdict_7d"])
            if out["verdict"] in ("worked", "failed", "neutral", "n/a"):
                bucket_scores.setdefault(e["bucket"], []).append(out["verdict"])
                name_bucket_scores.setdefault((e["ticker"], e["bucket"]), []).append(out["verdict"])
                if out["verdict"] in ("worked", "failed") and out.get("outcome_30d_pct") is not None:
                    _dir = BUCKET_DIRECTION.get(e["bucket"])
                    if _dir is not None:
                        _signed = out["outcome_30d_pct"] if _dir == "up" else -out["outcome_30d_pct"]
                        bucket_score_magnitudes.setdefault(e["bucket"], {"worked": [], "failed": []})[out["verdict"]].append(_signed)
            updates.append(out)
            continue

        pct_move = round((current_price - e["price_at_flag"]) / e["price_at_flag"] * 100, 3)

        if days_old >= 7 and not already_locked_7d:
            out["outcome_7d_pct"] = pct_move
            direction_7d = BUCKET_DIRECTION.get(e["bucket"])
            if direction_7d is not None:
                signed_7d = pct_move if direction_7d == "up" else -pct_move
                v7 = ("worked" if signed_7d > VERDICT_THRESHOLD_PCT
                      else "failed" if signed_7d < -VERDICT_THRESHOLD_PCT else "neutral")
                out["_v7_locked_this_run"] = v7  # consumed just below, not persisted
        if days_old >= 30 and not already_locked_30d:
            out["outcome_30d_pct"] = pct_move
            direction = BUCKET_DIRECTION.get(e["bucket"])
            if direction is None:
                out["verdict"] = "n/a"
            else:
                signed = pct_move if direction == "up" else -pct_move
                if signed > VERDICT_THRESHOLD_PCT:
                    out["verdict"] = "worked"
                elif signed < -VERDICT_THRESHOLD_PCT:
                    out["verdict"] = "failed"
                else:
                    out["verdict"] = "neutral"

        # 7d interim verdict (added 2026-08-06, locking added 2026-08-25): kept in a SEPARATE
        # dict (bucket_scores_7d, never bucket_scores) so it can never contaminate the
        # validated 30d hit rate.
        v7_for_tally = out.pop("_v7_locked_this_run", None) or (
            prior.get("_verdict_7d") if already_locked_7d else None)
        if v7_for_tally:
            out["_verdict_7d"] = v7_for_tally  # persisted so future runs can re-tally without price
            bucket_scores_7d.setdefault(e["bucket"], []).append(v7_for_tally)

        if out["verdict"] in ("worked", "failed", "neutral", "n/a"):
            bucket_scores.setdefault(e["bucket"], []).append(out["verdict"])
            name_bucket_scores.setdefault((e["ticker"], e["bucket"]), []).append(out["verdict"])
            if out["verdict"] in ("worked", "failed") and out.get("outcome_30d_pct") is not None:
                _dir = BUCKET_DIRECTION.get(e["bucket"])
                if _dir is not None:
                    _signed = out["outcome_30d_pct"] if _dir == "up" else -out["outcome_30d_pct"]
                    bucket_score_magnitudes.setdefault(e["bucket"], {"worked": [], "failed": []})[out["verdict"]].append(_signed)
        updates.append(out)

    bucket_hit_rates = {}
    for bucket, verdicts in bucket_scores.items():
        scored = [v for v in verdicts if v in ("worked", "failed")]
        if scored:
            row = {
                "n": len(scored),
                "hit_rate_pct": round(sum(1 for v in scored if v == "worked") / len(scored) * 100, 1),
            }
            # payoff_ratio (added 2026-09-07): avg |magnitude| of worked / avg |magnitude| of
            # failed, both direction-adjusted 30d moves. None (never a made-up 1.0) unless
            # BOTH sides have at least one scored entry -- a bucket that has never lost has no
            # observed loss magnitude to divide by, and "infinite payoff ratio" is not a real
            # number to hand to Kelly's formula.
            mags = bucket_score_magnitudes.get(bucket, {"worked": [], "failed": []})
            if mags["worked"] and mags["failed"]:
                avg_win = sum(mags["worked"]) / len(mags["worked"])
                avg_loss = abs(sum(mags["failed"]) / len(mags["failed"]))
                if avg_loss > 0:
                    row["payoff_ratio"] = round(avg_win / avg_loss, 3)
            bucket_hit_rates[bucket] = row

    bucket_hit_rates_7d = {}
    for bucket, verdicts in bucket_scores_7d.items():
        scored = [v for v in verdicts if v in ("worked", "failed")]
        if len(scored) >= 3:  # same n>=3 floor as bucket_hit_rates -- don't publish on n=1
            bucket_hit_rates_7d[bucket] = {
                "n": len(scored),
                "hit_rate_pct": round(sum(1 for v in scored if v == "worked") / len(scored) * 100, 1),
                "interim": True,
            }

    def grade(hit_rate_pct):
        if hit_rate_pct >= 70:
            return "A"
        if hit_rate_pct >= 50:
            return "B"
        if hit_rate_pct >= 30:
            return "C"
        return "F"

    # name_bucket_grades (rebuilt 2026-08-25): the old n>=3-per-(ticker,bucket) gate was
    # structurally unreachable at this journaling cadence -- audited 2026-08-25, the 48 matured
    # entries at the time formed 45 distinct pairs and the MAXIMUM count on any single pair was
    # 2. A gate that nothing can ever clear isn't caution, it's a permanently-false claim
    # ("34/34 ungraded") dressed as a measurement. Fixed by reporting every pair that has AT
    # LEAST ONE scored entry, with its n stated alongside the grade -- "low_confidence": true
    # below n=3 is the honest version of the old binary gate: visible and usable, but never
    # mistaken for a validated statistic. A pair with ZERO scored entries is omitted entirely
    # (never "ungraded"), because there is a real difference between "not enough data yet" and
    # "measured, but on a thin sample" and the old single bucket collapsed both into one lie.
    name_bucket_grades = {}
    for (ticker, bucket), verdicts in name_bucket_scores.items():
        scored = [v for v in verdicts if v in ("worked", "failed")]
        if not scored:
            continue
        hr = sum(1 for v in scored if v == "worked") / len(scored) * 100
        name_bucket_grades.setdefault(ticker, {})[bucket] = {
            "grade": grade(hr), "n": len(scored), "hit_rate_pct": round(hr, 1),
            "low_confidence": len(scored) < 3,
        }

    dq = [] if price_by_ticker else ["no current prices available -- all entries left open"]
    if needs_price:
        dq.append(f"{len(needs_price)} ticker(s) have an open journal entry and no price -- "
                  f"likely exited positions, unreachable via holdings.json: "
                  f"{', '.join(sorted(needs_price)[:12])}. Re-run with --prices-json to score "
                  f"them (probe with an empty {{}} first to confirm this list).")

    pending_30d = [e for e in updates if 14 <= e.get("days_old", 0) < 30 and e.get("verdict") == "open"]
    if pending_30d:
        dq.append(f"{len(pending_30d)} entries in 14-30d window; hit-rate scoring begins once they cross 30d")

    emit({
        "journal_updates": updates,
        "bucket_hit_rates": bucket_hit_rates,
        "bucket_hit_rates_7d": bucket_hit_rates_7d,
        "name_bucket_grades": name_bucket_grades,
        "data_quality": dq,
    })


# ---------------------------------------------------------------------------
# attribution
# ---------------------------------------------------------------------------
def _rolling_windows(run_dir, holdings, ledger_path):
    """attribution.rolling (was a stub that always returned null windows until 2026-09-14).
    Primary basis: today's holdings at today's equity weights vs SMH over trailing sessions, from
    the run's bars.json (flow-free). A realized time-weighted return is added per window only
    where the ledger records external flows for every row -- never inferred."""
    import csv
    import smith_marketdata as md
    bars = load_json(os.path.join(run_dir, "bars.json"), default=None)
    rows_ledger = []
    if os.path.exists(ledger_path):
        with open(ledger_path, newline="") as fh:
            rows_ledger = list(csv.DictReader(fh))
    if not isinstance(bars, dict) or not bars.get(md.BENCHMARK):
        return {"note": "no SMH bars in this run (smith_fetch bars section) -- rolling windows not computed",
                "_ledger_rows": len(rows_ledger)}
    weights = {r.get("ticker"): r.get("market_value_inr") for r in (holdings.get("holdings_inr") or [])
               if r.get("ticker") and isinstance(r.get("market_value_inr"), (int, float))}
    out = md.rolling_constant_mix(bars, weights)
    bench = {str(x["d"])[:10]: float(x["c"]) for x in bars[md.BENCHMARK] if isinstance(x.get("c"), (int, float))}
    for key, w in out.items():
        if w.get("from"):
            w.update(md.realized_twr(rows_ledger, w["from"], w["to"], bench))
    as_of = next((w.get("to") for w in out.values() if w.get("to")), None)
    out.update({"basis": "current_holdings_constant_mix", "benchmark": md.BENCHMARK, "as_of": as_of,
                "basis_label": ("trailing windows: current holdings at current weights vs SMH. Not a "
                                "realized return (trades, wallet cash and deposits excluded) and "
                                "flattered by hindsight: it prices the names you kept"),
                "_ledger_rows": len(rows_ledger)})
    return out


def cmd_attribution(args):
    holdings = load_json(os.path.join(args.run_dir, "holdings.json"))
    state = load_json(os.path.join(args.base_dir, "state.json"), default={})
    ledger_path = os.path.join(args.base_dir, "ledger.csv")

    usdinr = holdings["usdinr"]
    totals = holdings["totals"]
    value_usd = totals["current_value_inr_from_snapshot"] / usdinr

    prior_us = state.get("us", {})
    prior_value_usd = prior_us.get("value_usd")
    prior_usdinr = prior_us.get("usdinr") or state.get("usdinr")

    result = {"value_delta_usd": None, "fx_effect_usd": None, "flow_usd": None,
              "residual_market_move_usd": None, "qty_changes": [], "data_quality": []}

    if prior_value_usd is None or prior_usdinr is None:
        result["data_quality"].append("no prior state -- this is a first-run baseline, attribution not computable")
        emit(result)
        return

    value_delta = value_usd - prior_value_usd
    value_inr_current = totals["current_value_inr_from_snapshot"]
    value_at_prior_fx = value_inr_current / prior_usdinr
    value_at_current_fx = value_inr_current / usdinr
    fx_effect = value_at_current_fx - value_at_prior_fx

    # FIXED 2026-08-07 (G41): this loop used to `continue` past any ticker absent from prior
    # holdings, so a brand-new position's purchase cost never reached flow_usd, and full exits
    # (absent from `rows` entirely) were never visited at all. Both leaked into `residual`,
    # which the briefing reports as "market move" -- so cash movement was being narrated as
    # performance. Verified on the 2026-08-03 book: flow read $810.37 when true flow was
    # $2,093.66, overstating residual market move by ~$1,283 on a $40k book.
    prior_holdings = {h["ticker"]: h for h in state.get("holdings", [])}
    rows = {r["ticker"]: r for r in holdings["holdings_inr"]}
    flow_usd = 0.0
    qty_changes = []
    flow_components = {"adds_trims_usd": 0.0, "new_entries_usd": 0.0, "exits_usd": 0.0,
                       "exits_unpriced": [], "exit_price_basis": "last_known_price_prior_run"}

    for ticker, r in rows.items():
        prior = prior_holdings.get(ticker)
        if not r.get("qty"):
            continue
        price_usd = r["market_value_inr"] / r["qty"] / usdinr
        if prior is None:
            # brand-new position: full cost is a cash outflow
            cost = r["qty"] * price_usd
            flow_usd += cost
            flow_components["new_entries_usd"] = round(flow_components["new_entries_usd"] + cost, 2)
            qty_changes.append({"ticker": ticker, "qty_diff": round(r["qty"], 6),
                                "likely_corporate_action": False, "new_entry": True,
                                "est_cost_usd": round(cost, 2)})
            continue
        if prior.get("qty") is None:
            continue
        qty_diff = r["qty"] - prior["qty"]
        if abs(qty_diff) < 1e-6:
            continue
        ratio = r["qty"] / prior["qty"] if prior["qty"] else None
        is_split_like = ratio is not None and abs(ratio - round(ratio)) < 0.02 and round(ratio) != 1
        entry = {"ticker": ticker, "qty_diff": round(qty_diff, 6), "likely_corporate_action": bool(is_split_like)}
        qty_changes.append(entry)
        if not is_split_like:
            flow_usd += qty_diff * price_usd
            flow_components["adds_trims_usd"] = round(
                flow_components["adds_trims_usd"] + qty_diff * price_usd, 2)

    # full exits: gone from `rows`, so priced off the prior run's last-known price, never estimated
    _prior_run_prices._current = args.run_dir
    prior_prices = _prior_run_prices(args.base_dir, state.get("last_run_dir"), state)
    for ticker, prior in prior_holdings.items():
        if ticker in rows:
            continue
        exit_qty = prior.get("qty") or 0.0
        exit_px = prior_prices.get(ticker)
        entry = {"ticker": ticker, "qty_diff": round(-exit_qty, 6),
                 "likely_corporate_action": False, "full_exit": True}
        if exit_px and exit_qty:
            proceeds = exit_qty * exit_px
            flow_usd -= proceeds
            flow_components["exits_usd"] = round(flow_components["exits_usd"] - proceeds, 2)
            entry["est_proceeds_usd"] = round(proceeds, 2)
            entry["price_basis"] = "last_known_price_prior_run"
        else:
            flow_components["exits_unpriced"].append(ticker)
        qty_changes.append(entry)

    if flow_components["exits_unpriced"]:
        result["data_quality"].append(
            "flow_usd EXCLUDES proceeds for fully-exited "
            f"{', '.join(flow_components['exits_unpriced'])} -- no last-known price available; "
            "residual_market_move_usd absorbs it and is overstated by that amount (G41)")

    residual = value_delta - fx_effect - flow_usd

    result.update({
        "value_delta_usd": round(value_delta, 2),
        "fx_effect_usd": round(fx_effect, 2),
        "flow_usd": round(flow_usd, 2),
        "residual_market_move_usd": round(residual, 2),
        "qty_changes": qty_changes,
        "flow_components": flow_components,
    })

    result["rolling"] = _rolling_windows(args.run_dir, holdings, ledger_path)
    result["ledger_rows_available"] = result["rolling"].pop("_ledger_rows", 0)

    # REALIZED return, from the position-level reconstruction (added 2026-09-19). `rolling` above
    # is survivorship-biased by construction and must never be the headline on its own: it priced
    # today's 27 survivors back 12 months and reported +46.76pp of excess while the reconstructed
    # book, which includes the 121 positions stopped out and never re-entered, shows the opposite
    # sign. Both are emitted, and `realized` is the one the briefing leads with.
    result["realized"] = _realized_block(args.base_dir)

    emit(result)


def _realized_block(base_dir):
    """Attach smith_perf's reconstruction if its price history exists, else say why not.

    Never fabricates: a missing perf_bars.json degrades to an explicit reason, because a silent
    fallback to the constant-mix number is exactly the confusion this block exists to end.
    """
    bars = load_json(os.path.join(base_dir, "perf_bars.json"), default=None)
    if not bars:
        return {"available": False,
                "reason": "perf_bars.json missing -- run `smith_fetch.py perf-bars --base-dir .`"}
    trades = (load_json(os.path.join(base_dir, "trades.json"), default={}) or {}).get("trades", [])
    if not trades:
        return {"available": False, "reason": "trades.json has no trades"}
    recon = smith_perf.reconstruct(trades, bars)
    if recon.get("error") or not recon.get("series"):
        return {"available": False, "reason": recon.get("error") or "empty reconstruction"}
    series = recon["series"]
    material = [r for r in series if r["value_usd"] >= 10000.0]
    return {"available": True,
            "full_history": smith_perf.chain(series, bars),
            "material_capital": smith_perf.chain(material, bars) if material else None,
            "material_floor_usd": 10000.0,
            "money_weighted": smith_perf.selection_cost(series, bars),
            "basis": "trades.json rebuilt daily and priced at closes; includes exited names",
            "note": "TWR equal-weights the sub-$5K months, so full_history overstates the damage; "
                    "material_capital and money_weighted describe the capital that mattered."}




























def cmd_drift(args):
    holdings = load_json(os.path.join(args.run_dir, "holdings.json"))
    state = load_json(os.path.join(args.base_dir, "state.json"), default={})
    policy = load_json(os.path.join(args.base_dir, "policy.json"), default=None)

    if policy is None:
        emit({"policy_present": False, "note": "no policy.json -- strategist must bootstrap a draft"})
        return

    policy_defects = validate_policy(policy)

    usdinr = holdings["usdinr"]
    rows = holdings["holdings_inr"]
    totals = holdings["totals"]
    value_usd = totals["current_value_inr_from_snapshot"] / usdinr
    wallet_usd = totals.get("wallet_inr", 0) / usdinr
    total_book_usd = value_usd + wallet_usd

    sector_map = state.get("sector_map", {})
    cluster_actual = {}
    for r in rows:
        cluster = sector_map.get(r["ticker"], "Unclassified")
        cluster_actual[cluster] = cluster_actual.get(cluster, 0) + r["weight_pct"]

    cluster_targets = policy.get("cluster_targets", {})
    cluster_table = []
    for cluster, target in cluster_targets.items():
        actual = round(cluster_actual.get(cluster, 0.0), 3)
        lo, hi = target.get("band_pct", [None, None])
        breach = (lo is not None and actual < lo) or (hi is not None and actual > hi)
        cluster_table.append({
            "cluster": cluster, "actual_pct": actual, "target_pct": target.get("target_pct"),
            "band_pct": target.get("band_pct"), "drift_pt": round(actual - target.get("target_pct", 0), 3),
            "breach": breach,
        })
    unpoliced_pct = 0.0
    unpoliced_clusters = []
    for cluster, actual in cluster_actual.items():
        if cluster not in cluster_targets:
            unpoliced_pct += actual
            unpoliced_clusters.append(cluster)
            cluster_table.append({"cluster": cluster, "actual_pct": round(actual, 3),
                                   "target_pct": None, "band_pct": None, "drift_pt": None,
                                   "breach": False, "note": "no policy target for this cluster"})
    # SURFACE THE HOLE AS A NUMBER (added 2026-08-30). A reader had to notice `target_pct: null`
    # on individual rows and add them up to discover that 8% of equity could not breach anything;
    # nobody did, for weeks. A cluster with no policy target is not merely untargeted, it is
    # UNPOLICEABLE -- breach is False by construction however far it drifts.
    unpoliced_pct = round(unpoliced_pct, 3)

    # ADDED 2026-07-28: conditional cluster denominator. Cluster weights on INVESTED EQUITY are the
    # right measure of concentration inside the deployed sleeve, but while a large cash balance is
    # being rebuilt they overstate real risk -- a shrunken equity base makes every cluster look
    # oversized and manufactures breaches the risk framework forbids curing. When cash sits above the
    # NORMAL band top, breach-testing switches to a total-book basis. Both figures are always emitted
    # so neither is silently lost. User-raised and accepted 2026-07-28.
    cash_pct_pre = (wallet_usd / total_book_usd * 100) if total_book_usd else 0.0
    _regs = policy.get("cash_regimes") or {}
    _norm = (_regs.get("normal") or {}).get("band_pct") or policy.get("cash_band_pct") or [0, 100]
    equity_share_pre = (value_usd / total_book_usd) if total_book_usd else 1.0
    _cond = policy.get("cluster_denominator_conditional", {}).get("enabled", False)
    use_total_book = bool(_cond and _norm[1] is not None and cash_pct_pre > _norm[1])
    cluster_basis = "total_book" if use_total_book else "invested_equity"
    # The two denominators answer different questions, so they govern different edges of the band:
    #   CEILING ("am I over-exposed to this factor?") -> TOTAL BOOK when cash is elevated. Idle cash is
    #     genuinely uncorrelated, so memory at 19% of a half-invested sleeve is only 10% of the wealth
    #     actually at risk. This is the edge the user asked to relax.
    #   FLOOR ("is the invested portfolio the right shape?") -> ALWAYS INVESTED EQUITY. A floor is a
    #     statement about portfolio construction, and "you must hold 10% of TOTAL BOOK in Power" is
    #     incoherent while deliberately sitting on 48% cash -- it would fire on every cluster at once.
    # Testing both edges on one denominator is what broke in the first cut of this change: switching
    # wholesale to total book halved every reading and manufactured five phantom floor breaches.
    for c in cluster_table:
        c["actual_pct_of_equity"] = c["actual_pct"]
        c["actual_pct_of_total_book"] = round(c["actual_pct"] * equity_share_pre, 3)
        # band_pct is None for a cluster with no policy target (e.g. a brand-new holding not yet
        # assigned a sector_map cluster) -- there's no band to test against, so skip the breach
        # test rather than crash the whole subcommand (was a real bug, hit 2026-07-29 by BE).
        if c["band_pct"] is None:
            c["breach"] = False
            c["breach_edge"] = None
            c["ceiling_tested_on"] = None
            c["floor_tested_on"] = None
            c["actual_pct"] = c["actual_pct_of_equity"]
            continue
        _lo, _hi = c["band_pct"]
        ceil_val = c["actual_pct_of_total_book"] if use_total_book else c["actual_pct_of_equity"]
        floor_val = c["actual_pct_of_equity"]
        over = ceil_val > _hi
        under = floor_val < _lo
        c["breach"] = bool(over or under)
        c["breach_edge"] = "over" if over else ("under" if under else None)
        c["ceiling_tested_on"] = "total_book" if use_total_book else "invested_equity"
        c["floor_tested_on"] = "invested_equity"
        c["actual_pct"] = c["actual_pct_of_equity"]
        c["drift_pt"] = round(c["actual_pct_of_equity"] - c["target_pct"], 3)

    # CLUSTER CEILING ROOM IN DOLLARS (added 2026-09-08). smith_conviction.clamp_size has taken a
    # `cluster_room_usd` argument since it was written, and EVERY caller passes None -- so "never
    # push a cluster over its ceiling", which that function's own docstring promises, has never
    # actually been enforced on a single sized buy. Nothing computed the number. This is the only
    # place that can: the band, the denominator switch and both bases all live here.
    #
    # Which denominator, and why the arithmetic differs between them:
    #   total_book basis -- a cash-funded buy moves dollars from wallet to equity, so total book
    #     is UNCHANGED and the room is exactly linear: (hi - actual_of_total_book)% of total book.
    #   invested_equity basis -- a cash-funded buy grows the numerator AND the denominator, so the
    #     exact solve is X = (hi/100*E - c) / (1 - hi/100), which is LARGER than the linear figure.
    #     The linear figure is used deliberately: it under-states available room, and a sizing
    #     clamp that errs small is the correct direction to err.
    # A cluster with no band cannot be over a ceiling it doesn't have -- None, not zero, so
    # clamp_size treats it as non-binding rather than as "no room" (unknown != a reason to block).
    for c in cluster_table:
        band = c.get("band_pct")
        hi = band[1] if band else None
        if hi is None:
            c["cluster_room_usd"] = None
            c["cluster_room_basis"] = None
            continue
        if c.get("ceiling_tested_on") == "total_book":
            room = (hi - c["actual_pct_of_total_book"]) / 100.0 * total_book_usd
        else:
            room = (hi - c["actual_pct_of_equity"]) / 100.0 * value_usd
        c["cluster_room_usd"] = round(max(0.0, room), 2)
        c["cluster_room_basis"] = c.get("ceiling_tested_on")

    max_single = policy.get("max_single_position_pct")
    position_breaches = []
    for r in rows:
        if max_single is not None and r["weight_pct"] > max_single:
            position_breaches.append({"ticker": r["ticker"], "actual_pct": round(r["weight_pct"], 3),
                                       "cap_pct": max_single, "drift_pt": round(r["weight_pct"] - max_single, 3)})

    # FIXED 2026-07-28 (G28): two-regime cash band. The user runs a tight, large-quantum stop
    # discipline on a maximally-correlated book, which structurally converts equity to cash in single
    # sessions (07-24: cash to 45.8%; 07-28: to 60.5%). A single [5,15] band declared a severe breach
    # on every such day that could NOT be cured without violating the position-risk framework -- a
    # false alarm that trains the reader to ignore a real control. policy.cash_regimes lets the band
    # widen while a stop-out is recent, and the ceiling above it is still a genuine breach.
    cash_pct = round(wallet_usd / total_book_usd * 100, 3) if total_book_usd else 0.0
    regimes = policy.get("cash_regimes") or {}
    cash_regime = "normal"
    regime_reason = "no cash_regimes block in policy; using cash_band_pct"
    if regimes:
        window = (regimes.get("post_stop_event") or {}).get("window_sessions", 15)
        normal_ceiling = ((regimes.get("normal") or {}).get("band_pct") or [None, None])[1]
        last_stop = state.get("last_stop_event_date")
        sessions_since = None
        if last_stop:
            try:
                d0 = datetime.strptime(last_stop, "%Y-%m-%d").date()
                today_d = resolve_today(getattr(args, "today", None))
                sessions_since = int((today_d - d0).days * 5 / 7)  # calendar->trading-day approximation
            except ValueError:
                sessions_since = None
        in_window = sessions_since is not None and sessions_since <= window
        # FIXED 2026-07-30: the regime must persist through the whole window unless cash has
        # genuinely re-entered the NORMAL band's own ceiling -- re-testing the wider band's entry
        # trigger (trigger_cash_pct, 20%) every run instead flips the regime back to "normal" the
        # moment cash dips just under 20%, well before it's anywhere near the tight [5,15]% band's
        # actual ceiling, manufacturing exactly the false-alarm breach this two-regime system exists
        # to prevent (the G28 problem, recurring one level down). Found when a same-day partial
        # redeployment took cash from 20.5% to 19.1% and instantly produced a spurious ceiling breach.
        # trigger_cash_pct's real job is deciding whether a stop-out was severe enough to SET
        # last_stop_event_date in the first place -- that happens elsewhere, not in this persistence
        # check, so it plays no further role here.
        if in_window and (normal_ceiling is None or cash_pct > normal_ceiling):
            cash_regime = "post_stop_event"
            regime_reason = (f"stop-out on {last_stop}, ~{sessions_since} sessions ago (window {window}), "
                              + (f"cash {cash_pct}% has not yet re-entered the normal band (<= {normal_ceiling}%)"
                                 if normal_ceiling is not None else
                                 "no normal-band ceiling configured to test re-entry against"))
        elif in_window:
            regime_reason = f"stop-out {sessions_since} sessions ago but cash {cash_pct}% has re-entered the normal band (<= {normal_ceiling}%)"
        else:
            regime_reason = f"no stop-out within {window} sessions (last: {last_stop or 'none recorded'})"
    band_src = (regimes.get(cash_regime) or {}).get("band_pct") if regimes else None
    cash_band = band_src or policy.get("cash_band_pct", [None, None])
    cash_breach = (cash_band[0] is not None and cash_pct < cash_band[0]) or \
                  (cash_band[1] is not None and cash_pct > cash_band[1])
    normal_band = (regimes.get("normal") or {}).get("band_pct") or policy.get("cash_band_pct", [None, None])
    cash_breach_vs_normal = (normal_band[1] is not None and cash_pct > normal_band[1]) or \
                            (normal_band[0] is not None and cash_pct < normal_band[0])

    # AI-capex exposure is reported on BOTH bases: cluster weights are equity-denominated, so the
    # equity figure measures concentration *within the invested sleeve*, while the total-book figure
    # measures portfolio-level single-factor exposure (idle cash genuinely is uncorrelated -- on
    # 2026-07-24 every held name fell while cash and defensives did not). The two answer different
    # questions and can disagree about a breach; the cap is tested against whichever basis the policy
    # declares, and both numbers are emitted so the other is never silently lost.
    ai_clusters = policy.get("ai_capex_clusters", DEFAULT_AI_CAPEX_CLUSTERS)
    ai_capex_pct_equity = round(sum(cluster_actual.get(c, 0) for c in ai_clusters), 3)
    equity_share = (value_usd / total_book_usd) if total_book_usd else 0.0
    ai_capex_pct_total_book = round(ai_capex_pct_equity * equity_share, 3)

    ai_cap = policy.get("max_ai_capex_factor_pct")
    ai_denom = policy.get("ai_capex_denominator", "invested_equity")
    ai_capex_pct = ai_capex_pct_total_book if ai_denom == "total_book" else ai_capex_pct_equity
    ai_capex_breach = ai_cap is not None and ai_capex_pct > ai_cap

    # FIXED 2026-07-26: drawdown (and therefore the risk-off status and drawdown_trim_ladder trigger
    # below) must be measured on TOTAL BOOK, not equity alone -- see identical fix + rationale in
    # cmd_book(). A cash conversion (07-24: $18k moved from equity to wallet) must never itself read
    # as a drawdown; only an actual loss in total_book_usd should.
    prior_us = state.get("us", {})
    prior_peak_total_book = prior_us.get("peak_total_book_usd")
    if prior_peak_total_book is None:
        prior_peak_total_book = (prior_us.get("value_usd", 0) or 0) + (prior_us.get("wallet_usd", 0) or 0)
    peak_total_book_usd = max(prior_peak_total_book, total_book_usd) if prior_peak_total_book else total_book_usd
    drawdown_pct = round((total_book_usd - peak_total_book_usd) / peak_total_book_usd * 100, 3) if peak_total_book_usd else 0.0
    warn = policy.get("drawdown_warn_pct", 15)
    risk_off = policy.get("drawdown_risk_off_pct", 25)
    if abs(drawdown_pct) >= risk_off:
        risk_off_status = "risk_off"
    elif abs(drawdown_pct) >= warn:
        risk_off_status = "warn"
    else:
        risk_off_status = "normal"

    # Check drawdown trim ladder (TIER 2.3: sell-discipline framework, 2026-07-26)
    drawdown_action = None
    trim_ladder = policy.get("drawdown_trim_ladder", [])
    for rung in sorted(trim_ladder, key=lambda r: r.get("drawdown_pct", 0)):
        if abs(drawdown_pct) >= abs(rung.get("drawdown_pct", 0)):
            drawdown_action = rung

    output = {
        "policy_present": True, "policy_confirmed": policy.get("confirmed", False),
        "policy_defects": policy_defects,
        "policy_valid": not policy_defects,
        "cluster_target_denominator": "split: ceiling=%s, floor=invested_equity" % cluster_basis,
        "cluster_denominator_declared": policy.get("cluster_target_denominator", "UNDECLARED"),
        "cluster_denominator_switched": use_total_book,
        "cluster_denominator_reason": (
            "cash %.1f%% is above the normal band top %s%% -- cluster CEILINGS tested on total book, floors still on invested equity"
            % (cash_pct_pre, _norm[1]) if use_total_book else
            "cash %.1f%% within the normal band -- cluster breaches tested on invested equity"
            % cash_pct_pre),
        "cluster_table": sorted(cluster_table, key=lambda c: c["breach"], reverse=True),
        "unpoliced_pct_of_equity": unpoliced_pct,
        "unpoliced_clusters": sorted(unpoliced_clusters),
        "position_breaches": position_breaches,
        "cash_pct": cash_pct, "cash_band_pct": cash_band, "cash_breach": cash_breach,
        "cash_regime": cash_regime, "cash_regime_reason": regime_reason,
        "cash_band_normal_pct": normal_band, "cash_breach_vs_normal": cash_breach_vs_normal,
        "cash_pct_denominator": "total_book",
        "ai_capex_pct": ai_capex_pct, "ai_capex_cap_pct": ai_cap, "ai_capex_breach": ai_capex_breach,
        "ai_capex_denominator": ai_denom,
        "ai_capex_pct_of_equity": ai_capex_pct_equity,
        "ai_capex_pct_of_total_book": ai_capex_pct_total_book,
        "total_book_usd": round(total_book_usd, 2),
        # Added 2026-09-08 alongside cluster_room_usd: consumers previously had to back this out
        # of total_book_usd and cash_pct to know the denominator the equity-basis figures use.
        "invested_equity_usd": round(value_usd, 2),
        "peak_total_book_usd": round(peak_total_book_usd, 2),
        "drawdown_pct": drawdown_pct, "drawdown_basis": "total_book", "risk_off_status": risk_off_status,
        "drawdown_action": drawdown_action,
    }

    emit(output)


# ---------------------------------------------------------------------------
# rotation -- accumulate/rotate-out/trim-risk-cap classification per ticker.
# Needs risk (compute_risk.json) to have run first in this run-dir.
# ---------------------------------------------------------------------------
def cmd_rotation(args):
    state = load_json(os.path.join(args.base_dir, "state.json"), default={})
    # default=None returns None on a missing file (smith_core._NO_DEFAULT); the guard below is
    # what a hand-run `rotation` before `risk` hits. cmd_pipeline asserts the input first, so
    # this path only shows up in the per-stage invocation SKILL.md documents.
    risk = load_json(os.path.join(args.run_dir, "compute_risk.json"), default=None)
    polarity_table_json = {k: sorted(v) for k, v in smith_risk.SIGNAL_POLARITY.items()}

    if risk is None:
        emit({"tickers": {}, "polarity_table": polarity_table_json,
              "data_quality": ["compute_risk.json not found in run-dir -- run `risk` before `rotation`"]})
        return

    signal_history = state.get("signal_history", {})
    thesis = state.get("thesis", {})
    risk_by_ticker = {r["ticker"]: r for r in risk.get("positions", [])}
    # RSI cache, for the "not yet overbought" exemption below -- same threshold/cache the LIVE
    # overbought_distribution trigger uses (RSI_OVERBOUGHT, cmd_triggers), so a name reads
    # identically whether the desk is looking at it via triggers or via rotation.
    rsi_cache = (state.get("data_cache", {}).get("rsi14", {}) or {}).get("values", {})

    tickers = {}
    dq = []
    for ticker, r in risk_by_ticker.items():
        # ONE canonical reader for both entry shapes -- see smith_risk.thesis_status (2026-08-16).
        thesis_status = smith_risk.thesis_status(thesis.get(ticker))
        polarity = smith_risk.classify_signal_polarity(signal_history.get(ticker, []))
        over_cap = bool(r.get("over_cap"))
        rsi = rsi_cache.get(ticker)
        overbought = rsi is not None and rsi > RSI_OVERBOUGHT
        bucket = smith_risk.rotation_bucket(over_cap, thesis_status, polarity["net"], overbought)
        # A name that WOULD be exempted (strong + over_cap) but has no RSI to check the
        # overbought leg with falls back to the pre-2026-09-07 behavior (trim_risk_cap wins,
        # via rotation_bucket's own overbought=False default) -- surfaced here so that's a
        # visible data gap, not a silent one.
        ts_l = (thesis_status or "").strip().lower()
        if over_cap and ts_l == "strengthening" and polarity["net"] > 0 and rsi is None:
            dq.append(f"{ticker}: strengthening + net-bullish + over cap, but no RSI14 cached -- "
                      f"cannot check the overbought exemption, defaulted to trim_risk_cap")
        tickers[ticker] = {
            "cluster": r.get("cluster"), "thesis_status": thesis_status,
            "net_signal": polarity["net"], "bullish_buckets": polarity["bullish"],
            "bearish_buckets": polarity["bearish"],
            "headroom_usd": r.get("headroom_usd"), "over_cap": over_cap,
            "cap_multiple": r.get("cap_multiple"), "bucket": bucket,
            "rsi14": rsi, "overbought": overbought,
        }

    emit({"tickers": tickers, "polarity_table": polarity_table_json, "data_quality": dq})


# ---------------------------------------------------------------------------
# ladder -- the DETERMINISTIC half of the cluster substitution ladder.
# Needs risk + drift + rotation to have run first in this run-dir.
# ---------------------------------------------------------------------------
# WHY THIS EXISTS (added 2026-09-08). Within a cluster every name shares one tailwind, so the
# question that moves money is not "is NVDA's story intact?" -- smith-thesis owns that, per name
# -- but "given the same tailwind, which of these ten captures the most of it?". Nothing in the
# fleet owned that comparative question, and the one place it leaked into behaviour,
# _trigger_cluster_rotation, answered it with `rel_pp` from data_cache.rel_strength_1m.
#
# That number is ALWAYS SMH-relative, for the whole book. data_cache.rel_strength_1m_peer is
# null, so GEV/VRT/BE/FSLR and MSFT/GOOG/NBIS/IREN have been ranked against a semiconductor ETF.
# For an INTRA-cluster comparison the fix is not a better external benchmark -- it is to stop
# using one. rel_intra_pp measures each member against its OWN CLUSTER'S mean return, which is
# benchmark-free by construction and is precisely what "who is winning inside this cluster"
# means. It sidesteps the empty peer cache entirely.
#
# This stage computes only what a script can honestly compute: intra-cluster relative strength,
# dispersion, redundancy CANDIDATES, cluster room, and the dispatch gate. The ranking rationale,
# the margin-pool read, the bench and the cluster thesis are judgment and belong to smith-cluster.


def _ladder_slug(cluster, playbook):
    """Stable, collision-free agent-key suffix for a cluster. The playbook may override for
    readability (`memory` reads better than `ai_memory_storage` in a dispatch line); the derived
    form is the fallback so Phase 1 works before any playbook exists, and so a cluster added to
    sector_map without a playbook entry is still dispatchable rather than silently unreachable."""
    slug = (playbook or {}).get("slug")
    if slug:
        return re.sub(r"[^a-z0-9_]", "", str(slug).strip().lower())
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", cluster.lower())).strip("_")


def _stdev(xs):
    if len(xs) < 2:
        return 0.0
    mean = sum(xs) / len(xs)
    return math.sqrt(sum((x - mean) ** 2 for x in xs) / (len(xs) - 1))


def _ladder_track_record(prior_ladder, abs_ret, today):
    """Score the PREVIOUS ladder before it is replaced: did the name it called the leader
    actually beat the name it called the laggard?

    This is the whole reason a judgment layer is allowed to touch a trigger. A ranking that is
    never checked becomes a confident-nonsense generator, and this book already has the
    machinery (journal scoring, signal hit-rates) that says so. The measurement is deliberately
    crude -- one pairwise call per cluster per refresh, on the same 1-month return window every
    other price comparison here uses -- because a crude falsifiable score beats a sophisticated
    unfalsifiable one. Returns None when the prior ladder or either name's return is missing;
    an unscoreable call is NOT a wrong call and must not be recorded as one.
    """
    if not prior_ladder:
        return None
    leader, laggard = prior_ladder.get("leader"), prior_ladder.get("laggard")
    if not leader or not laggard or leader == laggard:
        return None
    lead_r, lag_r = abs_ret.get(leader), abs_ret.get(laggard)
    if lead_r is None or lag_r is None:
        return {"scored": False, "reason": f"no 1m return cached for {leader if lead_r is None else laggard}"}
    return {"scored": True, "as_of": today.isoformat(), "ladder_as_of": prior_ladder.get("as_of"),
            "leader": leader, "laggard": laggard,
            "leader_return_1m_pct": lead_r, "laggard_return_1m_pct": lag_r,
            "spread_pp": round(lead_r - lag_r, 2), "correct": bool(lead_r > lag_r),
            "ladder_confidence_at_call": prior_ladder.get("confidence")}


def _ladder_reopen_reasons(c, prior, catalysts, track):
    """Why a ladder younger than LADDER_FRESH_SKIP_DAYS must still be rebuilt (added 2026-09-15).
    Four events, each a fact rather than a price move: a structural catalyst first seen after the
    ladder on one of its members; a member reporting inside LADDER_EARNINGS_WINDOW_DAYS; the
    ladder's own leader-over-laggard call currently scoring wrong; a held member the ladder never
    ranked. Anything else waits for the ladder to age past the window."""
    reasons = []
    members = {m["ticker"] for m in c.get("members") or []}
    as_of = _parse_as_of(prior.get("as_of"))
    rows = catalysts.get("catalysts") if isinstance(catalysts, dict) else catalysts
    for cat in rows or []:
        if not isinstance(cat, dict) or cat.get("horizon") != "structural":
            continue
        seen = _parse_as_of(cat.get("first_seen") or cat.get("date"))
        hit = members & set(cat.get("affects") or [])
        if hit and seen and (as_of is None or seen > as_of):
            reasons.append(f"structural catalyst first seen {seen} on {', '.join(sorted(hit))}: "
                           f"{str(cat.get('headline') or '')[:90]}")
    soon = [m["ticker"] for m in c.get("members") or []
            if m.get("days_to_earnings") is not None and 0 <= m["days_to_earnings"] <= LADDER_EARNINGS_WINDOW_DAYS]
    if soon:
        reasons.append(f"{', '.join(soon)} reports within {LADDER_EARNINGS_WINDOW_DAYS}d")
    if isinstance(track, dict) and track.get("scored") and track.get("correct") is False:
        reasons.append(f"the current ladder's call ({track.get('leader')} over {track.get('laggard')}) "
                       f"is scoring wrong ({track.get('spread_pp')}pp)")
    ranked = {(r.get("t") or r.get("ticker")) for r in (prior.get("ranking") or []) if isinstance(r, dict)}
    ranked |= {(r.get("ticker") or r.get("t")) for r in (prior.get("unranked") or []) if isinstance(r, dict)}
    if ranked:
        missing = sorted(members - ranked)
        if missing:
            reasons.append(f"held member(s) not on the ladder: {', '.join(missing)}")
    return reasons


def cmd_ladder(args):
    # `default=None` means "return None if absent" -- see the _NO_DEFAULT sentinel in
    # smith_core.load_json. Until 2026-09-08 it raised instead, so the `if risk is None`
    # guard below was unreachable and the stage crashed rather than degrading.
    risk = load_json(os.path.join(args.run_dir, "compute_risk.json"), default=None)
    drift = load_json(os.path.join(args.run_dir, "compute_drift.json"), default={})
    rotation = load_json(os.path.join(args.run_dir, "compute_rotation.json"), default={})
    state = load_json(os.path.join(args.base_dir, "state.json"), default={})
    policy = load_json(os.path.join(args.base_dir, "policy.json"), default={})

    if risk is None:
        emit({"clusters": {}, "dispatch": [], "dispatch_selected": [],
              "data_quality": ["compute_risk.json not found in run-dir -- run `risk` before `ladder`"]})
        return

    today = resolve_today(args.today)
    dq = []
    dc = state.get("data_cache", {}) or {}
    thesis = state.get("thesis", {}) or {}
    playbooks = policy.get("cluster_playbooks", {}) or {}
    prior_ladders = state.get("cluster_ladders", {}) or {}
    rot_by_ticker = rotation.get("tickers", {}) or {}
    cluster_rows = {c.get("cluster"): c for c in (drift.get("cluster_table") or [])}

    rel_cache = dc.get("rel_strength_1m", {}) or {}
    abs_ret = rel_cache.get("values_abs_pct", {}) or {}
    rel_smh = rel_cache.get("values_pp", {}) or {}
    rel_as_of = _parse_as_of(rel_cache.get("as_of"))
    rel_age = (today - rel_as_of).days if rel_as_of else None
    rel_usable = bool(abs_ret) and rel_age is not None and rel_age <= TRIGGER_CACHE_MAX_AGE_DAYS
    if not rel_usable:
        dq.append(f"rel_strength_1m.values_abs_pct unusable (age={rel_age}d, n={len(abs_ret)}) -- "
                  f"rel_intra_pp and dispersion cannot be computed, so every cluster reads as "
                  f"zero-dispersion and the gate falls back to staleness alone. Not estimated.")

    atr_vals = (dc.get("atr20", {}) or {}).get("values_pct", {}) or {}
    rsi_vals = (dc.get("rsi14", {}) or {}).get("values", {}) or {}
    ecal = dc.get("earnings_calendar", {}) or {}
    equity_usd = drift.get("invested_equity_usd") or risk.get("total_book_usd") or 0.0

    # --- group held positions by cluster ------------------------------------
    by_cluster = {}
    for r in risk.get("positions", []):
        by_cluster.setdefault(r.get("cluster") or "Unclassified", []).append(r)

    clusters, track_record = {}, {}
    for cluster, positions in sorted(by_cluster.items()):
        pb = playbooks.get(cluster) or {}
        slug = _ladder_slug(cluster, pb)
        rets = {r["ticker"]: abs_ret[r["ticker"]] for r in positions if r["ticker"] in abs_ret}
        missing = sorted(r["ticker"] for r in positions if r["ticker"] not in abs_ret)
        # EQUAL-weighted, not value-weighted. The question is "which NAME is winning", and a
        # value-weighted mean lets the largest holding define the bar it is then measured
        # against -- an over-sized laggard would drag the mean down until it looked like a
        # leader. Equal weight treats every member as one candidate for the cluster's dollar,
        # which is what a substitution ladder is choosing between.
        mean_ret = round(sum(rets.values()) / len(rets), 3) if rets else None
        # None, not 0.0, when the cache covers fewer than two members. A single covered name has
        # no dispersion -- reporting 0.0 would say "this cluster moves as one block", which is a
        # finding, and a missing measurement must never be dressed as one.
        dispersion = round(_stdev(list(rets.values())), 3) if len(rets) >= 2 else None

        members = []
        for r in positions:
            t = r["ticker"]
            ret = abs_ret.get(t)
            ed = (ecal.get(t) or {}).get("date")
            days_to_earnings = None
            if ed:
                try:
                    days_to_earnings = (date.fromisoformat(ed) - today).days
                except ValueError:
                    dq.append(f"{t}: unparseable earnings_calendar date {ed!r} -- ignored")
            members.append({
                "ticker": t, "held": True,
                "market_value_usd": r.get("market_value_usd"),
                "weight_pct": (round(r["market_value_usd"] / equity_usd * 100, 3)
                               if equity_usd and r.get("market_value_usd") is not None else None),
                "abs_return_1m_pct": ret,
                "rel_intra_pp": (round(ret - mean_ret, 3) if ret is not None and mean_ret is not None else None),
                "rel_smh_pp": rel_smh.get(t),
                "atr20_pct": atr_vals.get(t) or r.get("atr20_pct"),
                "rsi14": rsi_vals.get(t),
                "thesis_status": smith_risk.thesis_status(thesis.get(t)),
                "over_cap": bool(r.get("over_cap")),
                "headroom_usd": r.get("headroom_usd"),
                "cap_multiple": r.get("cap_multiple"),
                "rotation_bucket": (rot_by_ticker.get(t) or {}).get("bucket"),
                "earnings_date": ed, "days_to_earnings": days_to_earnings,
            })
        members.sort(key=lambda m: (m["rel_intra_pp"] is None, -(m["rel_intra_pp"] or 0)))
        ranked = [m for m in members if m["rel_intra_pp"] is not None]

        # --- redundancy CANDIDATES (a screen, never a finding) ----------------
        redundancy = []
        for i, a in enumerate(ranked):
            for b in ranked[i + 1:]:
                if a["atr20_pct"] is None or b["atr20_pct"] is None:
                    continue
                rgap = abs(a["rel_intra_pp"] - b["rel_intra_pp"])
                agap = abs(a["atr20_pct"] - b["atr20_pct"])
                if rgap <= LADDER_REDUNDANCY_RETURN_GAP_PP and agap <= LADDER_REDUNDANCY_ATR_GAP_PCT:
                    redundancy.append({"pair": [a["ticker"], b["ticker"]],
                                       "return_gap_pp": round(rgap, 3), "atr_gap_pct": round(agap, 3),
                                       "note": "moves and volatility are near-identical -- CANDIDATE "
                                               "only; the same-bet call is a business judgment "
                                               "(customer, product, node), not this arithmetic"})

        # A ranking that cannot see a third of its cluster is a partial ranking, and the agent
        # must be told so it reports one rather than a confident ordering of whoever happened to
        # be cached. This bites hardest on the names that matter: on 2026-09-08 the live
        # cluster_rotation buy leg (LITE) had no 1-month return at all.
        if missing and len(positions) >= LADDER_MIN_MEMBERS:
            cov = 100.0 * len(rets) / len(positions)
            if cov < LADDER_MIN_COVERAGE_PCT:
                dq.append(f"{cluster}: 1-month returns cover only {cov:.0f}% of members "
                          f"({', '.join(missing)} missing) -- the ladder for this cluster is a "
                          f"PARTIAL ranking; refresh rel_strength_1m before trusting its ends")

        prior = prior_ladders.get(cluster) or {}
        ladder_as_of = _parse_as_of(prior.get("as_of"))
        ladder_age = (today - ladder_as_of).days if ladder_as_of else None
        ladder_stale = ladder_age is None or ladder_age > LADDER_TTL_DAYS
        tr = _ladder_track_record(prior, abs_ret, today)
        if tr:
            track_record[cluster] = tr

        drow = cluster_rows.get(cluster) or {}
        ineligible = []
        if len(positions) < LADDER_MIN_MEMBERS:
            ineligible.append(f"only {len(positions)} held name(s), below LADDER_MIN_MEMBERS={LADDER_MIN_MEMBERS}")
        if len([m for m in members if not m["over_cap"]]) < 2:
            ineligible.append("fewer than 2 members are under their ATR cap -- nothing to rotate into")

        clusters[cluster] = {
            "slug": slug, "playbook_present": bool(pb),
            "differentiators": pb.get("differentiators", []),
            "read_throughs": pb.get("read_throughs", []),
            "external_feed": pb.get("external_feed"),
            "member_count": len(positions),
            "return_coverage": {"with_return": len(rets), "total": len(positions), "missing": missing},
            "mean_return_1m_pct": mean_ret, "dispersion_pp": dispersion,
            "members": members,
            # A "leader" needs somebody to lead. With one covered member both ends would be the
            # same ticker, which reads as a ranking and is not one.
            "leader_by_price": ranked[0]["ticker"] if len(ranked) >= 2 else None,
            "laggard_by_price": ranked[-1]["ticker"] if len(ranked) >= 2 else None,
            "redundancy_candidates": redundancy,
            "cluster_room_usd": drow.get("cluster_room_usd"),
            "actual_pct_of_equity": drow.get("actual_pct_of_equity"),
            "band_pct": drow.get("band_pct"), "breach": bool(drow.get("breach")),
            "breach_edge": drow.get("breach_edge"),
            "prior_ladder": {"present": bool(prior), "as_of": prior.get("as_of"),
                             "age_days": ladder_age, "stale": ladder_stale,
                             "confidence": prior.get("confidence"),
                             "leader": prior.get("leader"), "laggard": prior.get("laggard")},
            "eligible": not ineligible, "ineligible_reasons": ineligible,
        }

    # --- dispatch gate ------------------------------------------------------
    # Scores WHY a cluster is worth an agent this run, not how good it looks. A cluster nobody
    # has ranked in three weeks scores above one whose ladder is a week old and whose members
    # are moving as a block -- the gate spends attention on where the ranking is most likely to
    # be both wrong and consequential.
    live_rotation_clusters = set()
    trig = load_json(os.path.join(args.run_dir, "compute_triggers.json"), default={})
    for pair in (trig.get("cluster_rotation") or []):
        if pair.get("cluster"):
            live_rotation_clusters.add(pair["cluster"])

    dispatch, skipped_fresh = [], []
    for cluster, c in clusters.items():
        if not c["eligible"]:
            continue
        score, reasons = 0, []
        # FRESH-LADDER SKIP (2026-09-15): see LADDER_FRESH_SKIP_DAYS and _ladder_reopen_reasons.
        age = c["prior_ladder"]["age_days"]
        if age is not None and age < LADDER_FRESH_SKIP_DAYS:
            reopen = _ladder_reopen_reasons(c, prior_ladders.get(cluster) or {},
                                            state.get("factor_catalysts"), track_record.get(cluster))
            if not reopen:
                skipped_fresh.append({"cluster": cluster, "agent": f"cluster_{c['slug']}", "age_days": age,
                                      "reason": (f"ladder is {age}d old (< {LADDER_FRESH_SKIP_DAYS}d) with no "
                                                 "structural catalyst, member earnings, wrong-scoring call or "
                                                 "unranked member since -- reuse it")})
                continue
            score += 2
            reasons.append("fresh ladder reopened: " + "; ".join(reopen))
        if c["prior_ladder"]["stale"]:
            score += 3
            age = c["prior_ladder"]["age_days"]
            reasons.append(f"no ladder yet" if age is None else
                           f"ladder is {age}d old (TTL {LADDER_TTL_DAYS}d)")
        if c["dispersion_pp"] is not None and c["dispersion_pp"] >= LADDER_DISPERSION_MIN_PP:
            score += 2
            reasons.append(f"dispersion {c['dispersion_pp']}pp -- a real contest, not a block move")
        if cluster in live_rotation_clusters:
            score += 2
            reasons.append("a live cluster_rotation pair is already proposed here")
        if c["breach"]:
            score += 2
            reasons.append(f"cluster is outside its policy band ({c['breach_edge']})")
        soon = [m["ticker"] for m in c["members"]
                if m["days_to_earnings"] is not None and 0 <= m["days_to_earnings"] <= LADDER_EARNINGS_WINDOW_DAYS]
        if soon:
            score += 1
            reasons.append(f"{', '.join(soon)} reports within {LADDER_EARNINGS_WINDOW_DAYS}d")
        if c["redundancy_candidates"]:
            score += 1
            reasons.append(f"{len(c['redundancy_candidates'])} redundancy candidate pair(s) to judge")
        dispatch.append({"cluster": cluster, "slug": c["slug"], "agent": f"cluster_{c['slug']}",
                         "priority_score": score, "reasons": reasons})

    # Round-robin cursor breaks ties so a permanently-quiet cluster still gets refreshed. Ties
    # are ordered by how long since that cluster was LAST DISPATCHED, oldest first -- the same
    # cursor idea as watchlist_scan_cursor, which rotates a list nobody would otherwise finish.
    cursor = state.get("cluster_scan_cursor", {}) or {}

    def _last_seen(row):
        d = _parse_as_of(cursor.get(row["cluster"]))
        return (today - d).days if d else 10 ** 6

    # Tie-break order: how long since this cluster was last looked at (the round-robin), then
    # dispersion (a 12pp contest deserves attention before a 6pp one), then name for determinism.
    dispatch.sort(key=lambda r: (-r["priority_score"], -_last_seen(r),
                                 -(clusters[r["cluster"]]["dispersion_pp"] or 0), r["cluster"]))
    selected = dispatch[:LADDER_MAX_DISPATCH]
    for row in dispatch:
        row["last_dispatched"] = cursor.get(row["cluster"])
        row["selected"] = row in selected

    if not clusters:
        dq.append("no held positions grouped into clusters -- check state.sector_map coverage")
    unclassified = clusters.get("Unclassified")
    if unclassified:
        dq.append(f"{unclassified['member_count']} held name(s) are Unclassified in sector_map "
                  f"and cannot be ranked against a cluster: "
                  f"{', '.join(m['ticker'] for m in unclassified['members'])}")

    emit({
        "as_of": today.isoformat(),
        "return_basis": {"source": "data_cache.rel_strength_1m.values_abs_pct",
                         "as_of": rel_cache.get("as_of"), "age_days": rel_age, "usable": rel_usable,
                         "note": "rel_intra_pp is measured against the cluster's own equal-weighted "
                                 "mean return, NOT against SMH -- benchmark-free by construction"},
        "ttl_days": LADDER_TTL_DAYS, "max_dispatch": LADDER_MAX_DISPATCH,
        "clusters": clusters,
        "dispatch": dispatch,
        "dispatch_selected": [r["agent"] for r in selected],
        "dispatch_selected_clusters": [r["cluster"] for r in selected],
        "skipped_fresh": skipped_fresh, "fresh_skip_days": LADDER_FRESH_SKIP_DAYS,
        "track_record": track_record,
        "data_quality": dq,
    })


# ---------------------------------------------------------------------------
# sentiment
# ---------------------------------------------------------------------------
def cmd_sentiment(args):
    mi = load_json(args.market_inputs)
    state = load_json(os.path.join(args.base_dir, "state.json"), default={})
    prior_sentiment = state.get("sentiment", {})

    vix = mi["vix"]
    vix_lo, vix_hi = mi.get("vix_52w_range", [10, 40])
    vix_norm = clamp((vix - vix_lo) / (vix_hi - vix_lo) * 100) if vix_hi > vix_lo else 50
    c_vix = 100 - vix_norm

    spx = mi["spx"]
    spx_125dma = mi.get("spx_125dma")
    c_ma = clamp(50 + (spx - spx_125dma) / spx_125dma * 100 * 5) if spx_125dma else 50

    c_rsi = clamp(mi.get("ndx_rsi14", 50))

    spx_52w_high = mi.get("spx_52w_high")
    pct_off_high = (spx_52w_high - spx) / spx_52w_high * 100 if spx_52w_high else 0
    c_high = clamp(100 - pct_off_high * 4)

    yield_chg_bps = mi.get("us10y_chg_1m_bps", 0)
    c_yield = clamp(50 + yield_chg_bps / 2)

    components = {"vix": round(c_vix, 1), "ma125": round(c_ma, 1), "rsi14": round(c_rsi, 1),
                  "pct_off_52w_high": round(c_high, 1), "yield_trend": round(c_yield, 1)}
    score = round(sum(components.values()) / len(components), 1)

    prior_band = prior_sentiment.get("band")
    if score >= 75:
        band = "extreme_greed"
    elif score >= 55:
        band = "greed"
    elif score > 45:
        band = "neutral"
    elif score > 25:
        band = "fear"
    else:
        band = "extreme_fear"

    # hysteresis: if prior band was extreme, require crossing 70/30 (not 75/25) to exit
    if prior_band == "extreme_greed" and score >= 70:
        band = "extreme_greed"
    if prior_band == "extreme_fear" and score <= 30:
        band = "extreme_fear"

    action_hint = None
    if band == "extreme_greed":
        action_hint = "propose profit-booking on overweight/breach names"
    elif band == "extreme_fear":
        action_hint = "propose deploying wallet cash into diversifier bench"

    emit({
        "score": score, "band": band, "components": components,
        "action_hint": action_hint, "prior_band": prior_band,
        "note": "proxy composite, not CNN's Fear & Greed Index -- equal-weighted VIX-range/125dma/RSI14/52wk-high/yield-trend",
    })




























def cmd_merge_prices(args):
    """Merge one or more fetched price JSON files into the single flat {"TICKER":price_usd}
    map `score`/`stops` (and `build-holdings`' --live-quotes-json) expect.

    ADDED 2026-09-10, alongside `build-holdings` (G95) and its follow-up lesson: the prices-json
    fed to `score`/`stops` cannot be fetched BY the script (no network, by design), but the
    MERGING of several fetch rounds into one file was still being hand-written in inline Python
    every run -- three separate `python3 << EOF ... json.dump(...)` blocks in a single sweep on
    2026-09-10, each one a fresh chance to fat-finger a key or silently drop a ticker. This
    command removes that specific manual step; it does not and cannot remove the FETCH itself.

    Each --input file may be in EITHER shape and both are handled without the caller pre-flattening:
      - a flat map already: {"TICKER": 123.45, ...}
      - raw yfinance get_stock_price(format=json) output: {"TICKER": {"price": 123.45,
        "changePct": ..., ...other fields...}, ...} -- only `.price` is extracted.
    Later --input files win on a key collision (last one wins, so pass the freshest fetch last).
    A value that is neither a number nor a dict-with-price is skipped and named in `skipped`,
    never silently coerced.
    """
    merged, skipped, sources = {}, [], {}
    for path in args.inputs:
        data = load_json(path, default=None)
        if not isinstance(data, dict):
            fail(f"--input {path} is not a JSON object")
        for ticker, v in data.items():
            price = v.get("price") if isinstance(v, dict) else v
            if isinstance(price, (int, float)):
                merged[ticker] = price
                sources[ticker] = os.path.basename(path)
            else:
                skipped.append({"ticker": ticker, "file": os.path.basename(path), "value": v})
    with open(args.out, "w") as f:
        json.dump(merged, f, indent=2)
    emit({"written": args.out, "tickers": len(merged), "skipped": skipped,
          "inputs": [os.path.basename(p) for p in args.inputs]})


def cmd_maxpain(args):
    """Max-pain and put/call OI ratio from an options chain (G18).

    G18 was opened when a SPY/QQQ pull returned near-zero/null open interest across nearly
    every strike. Re-probed 2026-08-16: OI is now populated across the full chain, so the
    blocker is gone and the number is computable again. It lives here rather than in an agent
    because it is pure arithmetic over a table -- exactly what COMPUTE-FIRST reserves for the
    script.

    Max pain = the strike at which the aggregate intrinsic value owed to option HOLDERS is
    smallest, i.e. where the most contracts expire worthless:
        pain(K) = SUM_calls OI_c * max(0, K - strike_c) + SUM_puts OI_p * max(0, strike_p - K)
    evaluated at every listed strike; the minimum wins.

    Takes a saved chain file because this script is offline by design -- the orchestrator does
    the MCP fetch and hands the JSON over, the same contract every other compute uses.
    """
    chain = load_json(args.chain)
    spot = chain.get("underlyingPrice")
    out, dq = {}, []
    if chain.get("_truncated"):
        dq.append("chain JSON carries _truncated: true -- strikes were dropped by the fetch, so "
                  "max-pain is computed over a PARTIAL book and may be wrong. Re-fetch per-expiry "
                  "with a wider strike_range before trusting it.")
    for expiry, legs in (chain.get("data") or {}).items():
        calls = [(c.get("strike"), c.get("openInterest") or 0) for c in (legs.get("calls") or [])
                 if c.get("strike") is not None]
        puts = [(p.get("strike"), p.get("openInterest") or 0) for p in (legs.get("puts") or [])
                if p.get("strike") is not None]
        # Volume PCR too (added 2026-09-06): smith-macro reports pcr_vol alongside pcr_oi, and
        # was computing BOTH by hand from the raw chain while this command already did the
        # harder one. They answer different questions -- OI is standing positioning, volume is
        # today's flow -- so both are emitted, never blended.
        call_vol = sum((c.get("volume") or 0) for c in (legs.get("calls") or []))
        put_vol = sum((p.get("volume") or 0) for p in (legs.get("puts") or []))
        if not calls or not puts:
            dq.append(f"{expiry}: missing a full call or put leg -- skipped, never half-computed")
            continue
        call_oi, put_oi = sum(o for _, o in calls), sum(o for _, o in puts)
        if call_oi == 0 and put_oi == 0:
            dq.append(f"{expiry}: open interest is zero across every strike -- this is the original "
                      "G18 signature. Reported as null rather than as a max-pain of 0.")
            out[expiry] = {"max_pain": None, "pcr_oi": None, "note": "no open interest"}
            continue
        strikes = sorted({s for s, _ in calls} | {s for s, _ in puts})
        pain = {K: sum(o * max(0.0, K - s) for s, o in calls)
                   + sum(o * max(0.0, s - K) for s, o in puts) for K in strikes}
        best = min(pain, key=pain.get)
        # A minimum sitting at the edge of the listed range usually means the range, not the
        # market, picked it -- flag rather than report a boundary artifact as a real level.
        edge = best in (strikes[0], strikes[-1])
        if edge:
            dq.append(f"{expiry}: max-pain landed on the {'lowest' if best == strikes[0] else 'highest'} "
                      f"listed strike ({best}) -- that is a truncated-chain artifact, not a level.")
        out[expiry] = {
            "max_pain": best, "pain_at_max_pain": round(pain[best], 0),
            "pcr_oi": round(put_oi / call_oi, 3) if call_oi else None,
            "pcr_vol": round(put_vol / call_vol, 3) if call_vol else None,
            "call_oi": call_oi, "put_oi": put_oi,
            "call_vol": call_vol, "put_vol": put_vol,
            "strikes_used": len(strikes), "strike_range": [strikes[0], strikes[-1]],
            "spot_vs_max_pain_pct": (round((spot - best) / best * 100, 2)
                                     if spot and best else None),
            "boundary_artifact": edge,
        }
    emit({"symbol": args.symbol, "underlying_price": spot, "expiries": out,
          "data_quality": dq,
          "note": ("pcr_oi is put/call OPEN INTEREST (standing positioning); pcr_vol is today's "
                   "FLOW. Different questions -- report both, never blend them. Max-pain is a "
                   "gravity heuristic, not a forecast -- it moves as OI shifts and is least "
                   "meaningful far from expiry.")})






def cmd_pipeline(args):
    """Run the compute stages in dependency order and FAIL LOUDLY on a broken one.

    WHY THIS EXISTS (added 2026-08-15). The deep review that day invoked the stages by hand,
    in a shell loop, and got the order wrong: `rotation` ran while `compute_risk.json` was
    still absent because `risk` had failed on an argument-order mistake a moment earlier.
    rotation did not error. It exited 0 and wrote a file containing ZERO tickers. Nothing
    downstream complained. The only reason it surfaced at all was that the dashboard's
    section-count diff showed "Rotation analysis" had vanished from the published page --
    i.e. the desk found a silent data failure by noticing a hole in an HTML file.

    That is the wrong control. Stages have real dependencies (rotation needs risk; derisk
    needs risk AND sentiment; proposals needs drift, risk, book, derisk, rotation), and a
    stage whose input is missing should stop the run, not quietly emit an empty result that
    every consumer then treats as fact. An empty rotation table is indistinguishable from
    "no rotation candidates" unless something checks.

    So: one ordered runner, each stage's inputs asserted present BEFORE it runs, each output
    checked non-trivially-empty AFTER, and the first genuine failure aborts with the stage
    named. Stages the orchestrator legitimately cannot run yet (score and stops need prices
    it must fetch first) are skipped with a reason rather than failed.
    """
    import subprocess  # local: the rest of this file is deliberately network- and shell-free

    run_dir, base = args.run_dir, args.base_dir
    here = os.path.abspath(__file__)

    def out(name):
        return os.path.join(run_dir, f"compute_{name}.json")

    # (stage, required input files, "emptiness" probe on its own output)
    STAGES = [
        # `indicators` runs FIRST (added 2026-09-14): it turns smith_fetch's bars.json into the
        # ATR20/RSI14/rel-strength/ret_5d/52w/beta caches that book, risk, buckets, derisk,
        # triggers and ladder read. No bars.json -> it reports skipped and every cache stays as
        # it was (freshness then says how old).
        ("indicators",  [],                                          lambda d: d.get("skipped") or d.get("tickers") is not None),
        ("freshness",   [],                                          lambda d: d.get("artefacts")),
        # `lots` runs BEFORE book, which consumes lots.json for its LTCG/basis work. Added to
        # the pipeline 2026-08-31: the engine was trusted and adopted, but nothing re-ran it,
        # so the lots spine drifted from trades.json until a human remembered. Writes only when
        # the rebuild reconciles cleanly against broker quantities (see cmd_lots).
        ("lots",        ["holdings.json"],                          lambda d: d.get("total_lots")),
        ("book",        ["holdings.json"],                          lambda d: d.get("value_usd")),
        ("universe",    ["holdings.json"],                          lambda d: d.get("total")),
        ("risk",        ["compute_book.json"],                      lambda d: d.get("positions")),
        ("drift",       ["compute_book.json", "holdings.json"],     lambda d: d.get("cluster_table")),
        ("journal",     ["holdings.json"],                          lambda d: "journal_updates" in d),
        ("attribution", ["holdings.json"],                          lambda d: "value_delta_usd" in d),
        ("rotation",    ["compute_risk.json"],                      lambda d: d.get("tickers")),
        ("buckets",     ["holdings.json"],                          lambda d: d.get("tickers") is not None),
        ("sentiment",   ["market_inputs.json"],                     lambda d: d.get("score") is not None),
        ("derisk",      ["compute_risk.json", "compute_sentiment.json", "compute_book.json"],
                                                                    lambda d: d.get("queue")),
        # `correlation` runs BEFORE triggers (moved 2026-09-20, Phase 3): the heat budget reads
        # compute_correlation.json's average pairwise correlation, and while this stage ran after
        # triggers the file never existed in a fresh run dir -- every run would have fallen back
        # to the conservative bound and the measured correlation could never matter. It needs only
        # compute_risk and holdings, both present here. It stays DEGRADABLE: no perf_bars.json just
        # means the budget takes its conservative bound (rho = 1), never that the sweep fails.
        # It depends on perf_bars.json rather than the run's own bars.json, because it must price
        # names the book no longer holds -- exited positions are the whole point of a year-long
        # realized-return series.
        ("correlation", ["compute_risk.json", "holdings.json"],     lambda d: d.get("diversification")),
        ("triggers",    ["compute_risk.json", "compute_book.json"], lambda d: "correction_state" in d),
        # `ladder` runs LAST, after triggers, deliberately: its dispatch gate reads
        # compute_triggers.json to score a cluster higher when a rotation pair is already
        # proposed there. It is a GATE, not a data dependency -- a missing triggers file
        # degrades the score by 2 points, it does not fail the stage.
        ("ladder",      ["compute_risk.json"],                      lambda d: d.get("clusters") is not None),
        # `perf` depends on perf_bars.json rather than the run's own bars.json, because it must
        # price names the book no longer holds. Degradable: no perf_bars.json just means the
        # section is absent, never that the sweep fails. (`correlation` moved ahead of `triggers`.)
        ("perf",        [],                                          lambda d: d.get("twr")),
    ]

    stage_names = [st[0] for st in STAGES]
    wanted = set(stage_names)
    if getattr(args, "stages", None):
        wanted = {x.strip() for x in args.stages.split(",") if x.strip()}
        unknown = sorted(wanted - set(stage_names))
        if unknown:
            fail(f"--stages names unknown stage(s): {', '.join(unknown)}")
    if getattr(args, "from_stage", None):
        if args.from_stage not in stage_names:
            fail(f"--from {args.from_stage!r} is not a stage; stages: {', '.join(stage_names)}")
        wanted &= set(stage_names[stage_names.index(args.from_stage):])

    # A stage in DEGRADABLE never stops the run: `sentiment` only sets proposal urgency, and a
    # yfinance outage (no or partial market_inputs.json) used to abort the pipeline before
    # derisk/triggers/ladder -- a whole run with no proposals because one mood gauge was missing.
    # It writes an explicit degraded payload instead, which derisk reads as the neutral band.
    DEGRADABLE = {"sentiment", "correlation", "perf"}

    def degrade(name, reason):
        atomic_write_json(out(name), {"degraded": True, "reason": reason,
                                      "score": None, "band": None, "components": {}})
        results.append({"stage": name, "status": "DEGRADED", "note": reason})
        degraded.append(name)

    results, failed, degraded = [], None, []
    for name, needs, probe in STAGES:
        if name not in wanted:
            continue
        # Run-scoped inputs are read from the run dir only -- accepting a same-named file in the
        # base dir let this check pass on a file no stage would ever read.
        missing = [n for n in needs if not os.path.exists(os.path.join(run_dir, n))]
        if missing:
            reason = f"required input(s) absent: {', '.join(missing)}"
            if name in DEGRADABLE:
                degrade(name, reason)
                continue
            results.append({"stage": name, "status": "BLOCKED", "missing_inputs": missing})
            failed = (name, reason)
            break

        cmd = [sys.executable, here, name, "--base-dir", base]
        if name == "sentiment":
            cmd += ["--market-inputs", os.path.join(run_dir, "market_inputs.json")]
        else:
            cmd += ["--run-dir", run_dir]
        if name in ("journal", "derisk", "triggers", "buckets", "ladder", "indicators") and args.today:
            cmd += ["--today", args.today]
        if name == "book" and args.lots:
            cmd += ["--lots", args.lots]
        if name == "lots":
            # cmd_lots takes --holdings, not --run-dir; strip the run-dir the loop added.
            cmd = [c for c in cmd if c not in ("--run-dir", run_dir)]
            cmd += ["--holdings", os.path.join(run_dir, "holdings.json"), "--write-if-clean"]

        proc = subprocess.run(cmd, capture_output=True, text=True)
        payload, parse_error = None, None
        if (proc.stdout or "").strip():
            try:
                payload = json.loads(proc.stdout)
            except ValueError:
                parse_error = "stdout was not valid JSON"
        # fail() prints {"error": ...} to STDOUT and exits 1 -- read the reason from there, not
        # from stderr, or every failure reads "exited 1" with nothing to act on.
        err = payload.get("error") if isinstance(payload, dict) else None
        if proc.returncode != 0 or err or parse_error or payload is None:
            reason = err or parse_error or (f"exited {proc.returncode}" if proc.returncode
                                            else "emitted nothing")
            if name in DEGRADABLE:
                degrade(name, reason)
                continue
            results.append({"stage": name, "status": "FAILED", "exit": proc.returncode,
                            "error": reason, "stderr": (proc.stderr or "")[-400:]})
            failed = (name, reason)
            break
        # THE CHECK THAT WOULD HAVE CAUGHT 2026-08-15: exit 0 is not success if the payload is
        # hollow. Probe BEFORE writing, so a hollow result never lands where later stages, slices
        # or the dashboard would read it as real; keep it beside the run for inspection instead.
        if not probe(payload):
            if os.path.exists(out(name)):
                os.remove(out(name))
            atomic_write_json(os.path.join(run_dir, f"compute_{name}.rejected.json"), payload)
            results.append({"stage": name, "status": "EMPTY",
                            "note": "ran cleanly but produced an empty result -- treated as a "
                                    "failure, not as 'nothing to report'; kept as "
                                    f"compute_{name}.rejected.json"})
            failed = (name, "produced an empty result despite exiting 0")
            break
        atomic_write_json(out(name), payload)
        if name == "lots" and payload.get("write_blocked"):
            results.append({"stage": name, "status": "DEGRADED",
                            "note": "lots.json NOT rebuilt (book/derisk/triggers read the "
                                    "previous one): " + str(payload["write_blocked"])})
            degraded.append(name)
            continue
        results.append({"stage": name, "status": "ok"})

    # latest_run_dir: stamped HERE, by the only code that always knows which run dir it just
    # populated. Added 2026-08-31 after `validate` reported a 13.183% aggregate-risk breach that
    # had ALREADY been resolved -- it was grading runs/2026-08-29-0816 while two later runs sat
    # on disk, because `state.last_run_dir` is hand-written at PERSIST and had been missed twice.
    #
    # This is a NEW field, not a repair of `last_run_dir`, and the distinction is load-bearing:
    # `last_run_dir` means "the PREVIOUS run" to `_prior_run_prices`, which needs the run before
    # this one to price full exits and carries an explicit self-reference guard for the case
    # where it points at the current run. `validate` and the dashboard read the same key meaning
    # "the LATEST run". One field, two contradictory contracts -- so the fix is to give the
    # latest-run readers a field that actually means that, not to redefine one out from under
    # the other. Written only on a successful pipeline, so a failed run never advances it.
    if not failed:
        try:
            st_path = os.path.join(base, "state.json")
            st = load_json(st_path, default=None)
            if isinstance(st, dict):
                rel = os.path.relpath(os.path.realpath(run_dir), os.path.realpath(base))
                if st.get("latest_run_dir") != rel:
                    st["latest_run_dir"] = rel
                    safe_write(st_path, st)
        except (OSError, ValueError):
            pass  # a stamp failure must never take down a completed pipeline

    emit({"run_dir": run_dir,
          "stages": results,
          "completed": [r["stage"] for r in results if r["status"] == "ok"],
          "failed_at": failed[0] if failed else None,
          "reason": failed[1] if failed else None,
          "ok": failed is None,
          "degraded": degraded,
          "not_run_here": ["score", "stops", "proposals", "validate"],
          "note": ("score and stops need prices the orchestrator must fetch first; proposals "
                   "runs after the strategist has appended this run's proposals; validate is a "
                   "policy check, not a per-run compute. Run those explicitly.")})
    if failed:
        sys.exit(1)




def cmd_derisk(args):
    risk = load_json(os.path.join(args.run_dir, "compute_risk.json"))
    book = load_json(os.path.join(args.run_dir, "compute_book.json"))
    sent = load_json(os.path.join(args.run_dir, "compute_sentiment.json"), default={})
    state = load_json(os.path.join(args.base_dir, "state.json"), default={})
    policy = load_json(os.path.join(args.base_dir, "policy.json"), default={})
    lots = load_json(os.path.join(args.base_dir, "lots.json"), default={})

    today = resolve_today(args.today)
    ltcg_months = policy_ltcg_months(policy)
    dust_floor = dust_usd(policy)   # smith_core.dust_usd: the ONE dust number (also smith_ticket's MIN_POSITION_USD)

    rel_cache = state.get("data_cache", {}).get("rel_strength_1m", {}) or {}
    rel_vals = rel_cache.get("values_pp", {}) or {}
    abs_vals = rel_cache.get("values_abs_pct", {}) or {}
    sector_map = state.get("sector_map", {})
    thesis = state.get("thesis", {})
    signal_history = state.get("signal_history", {})
    rsi_cache = (state.get("data_cache", {}).get("rsi14", {}) or {}).get("values", {})

    agg_risk = risk.get("aggregate_open_risk_usd") or 0.0
    positions = risk.get("positions", [])
    dq, missing_rel, no_rsi_for_strong = [], [], []

    raw = []
    for p in positions:
        t = p["ticker"]
        mv = p.get("market_value_usd") or 0.0
        open_risk = p.get("position_open_risk_usd")
        cap_x = p.get("cap_multiple")

        # --- fragility -------------------------------------------------
        # STRONG-NAME CAP EXEMPTION (2026-09-07, user request: "check the de-risk queue for the
        # same fix" as rotation_bucket's over_cap exemption). cap_x amplifies fragility -- a
        # position 1.5x over its ATR cap scores 1.5x the raw risk-share, which is the queue's
        # dominant term. That's right for a name that's over cap AND weak; it overstates the
        # case for a name that's over cap because it's WINNING (strengthening thesis, net-
        # bullish signal) and not yet overbought -- exactly the situation rotation_bucket now
        # exempts from Trim -- risk cap for the same reason. Both panels should read the same
        # name the same way. The cap multiplier is floored at 1.0 (no amplification, but the
        # underlying risk-share fragility still counts in full -- real exposure is never
        # hidden) for a strong, not-yet-overbought name; a name with no RSI cached keeps the
        # OLD behavior (full cap_x applies) and is reported in data_quality, same fallback
        # rotation_bucket uses.
        t_status_pre = smith_risk.thesis_status(thesis.get(t))
        polarity_pre = smith_risk.classify_signal_polarity(signal_history.get(t, []))
        strong = (t_status_pre or "").strip().lower() == "strengthening" and polarity_pre["net"] > 0
        rsi_pre = rsi_cache.get(t)
        overbought_pre = rsi_pre is not None and rsi_pre > RSI_OVERBOUGHT
        if strong and cap_x and cap_x > 1.0 and rsi_pre is None:
            no_rsi_for_strong.append(t)
        cap_x_for_frag = (1.0 if (strong and not overbought_pre and rsi_pre is not None)
                          else cap_x)

        if open_risk is None or not agg_risk:
            frag_raw, frag_note = None, "no open-risk figure (ATR missing upstream)"
        else:
            risk_share = open_risk / agg_risk * 100.0
            frag_raw = risk_share * max(cap_x_for_frag or 1.0, 1.0)
            frag_note = None

        # --- stretch (relative to SMH AND absolutely up) ----------------
        # Both gates required. Beating a benchmark that is itself down just
        # means "fell less" -- there is no gain to give back, so it is not a
        # trim candidate. (2026-07-31: 9 names cleared rel>0 while sitting
        # -2.5% to -17% absolute; only CEG/AVGO were genuinely up.)
        rel_pp = rel_vals.get(t)
        abs_pct = abs_vals.get(t)
        if rel_pp is None:
            missing_rel.append(t)
            stretch_raw = None
        elif abs_pct is not None and abs_pct <= 0:
            stretch_raw = 0.0
        else:
            stretch_raw = max(rel_pp, 0.0)

        # --- friction --------------------------------------------------
        friction, fr_reasons = 0.0, []
        tlots = lots.get(t) or []
        oldest = None       # FIFO sells the oldest lot first
        unknown_date_qty = 0.0
        for lot in tlots:
            if lot.get("date"):
                m = _months_between(lot["date"], today)
                if m is not None and (oldest is None or m > oldest):
                    oldest = m
            else:
                unknown_date_qty += lot.get("qty") or 0.0
        if oldest is not None:
            to_ltcg = ltcg_months - oldest
            if to_ltcg <= 0:
                pass                                    # already long-term, free to trim
            elif to_ltcg <= LTCG_DEFER_WINDOW_MONTHS:
                f = 100.0 * (LTCG_DEFER_WINDOW_MONTHS - to_ltcg) / LTCG_DEFER_WINDOW_MONTHS
                friction += f
                fr_reasons.append(f"{to_ltcg:.1f}mo to LTCG boundary")
        if unknown_date_qty > 0:
            friction += 25.0
            fr_reasons.append("lot date unknown (predates email history, G1)")
        if mv < dust_floor:
            friction += 30.0
            fr_reasons.append(f"position below ${dust_floor:g} dust threshold")
        friction = clamp(friction)

        cap_exempt = cap_x_for_frag != cap_x and bool(cap_x) and cap_x > 1.0

        raw.append({"ticker": t, "market_value_usd": round(mv, 2),
                    "cluster": sector_map.get(t), "thesis_status": t_status_pre,
                    "cap_multiple": cap_x, "atr20_pct": p.get("atr20_pct"),
                    "stop_price_usd": p.get("stop_price_usd"),
                    "risk_share_pct": round(open_risk / agg_risk * 100.0, 2) if (open_risk and agg_risk) else None,
                    "rel_strength_1m_pp": rel_pp, "abs_return_1m_pct": abs_pct,
                    "_frag_raw": frag_raw, "_stretch_raw": stretch_raw,
                    "friction_score": round(friction, 1),
                    "friction_reasons": fr_reasons, "_frag_note": frag_note,
                    "cap_exempt": cap_exempt, "rsi14": rsi_pre, "overbought": overbought_pre})

    # normalise fragility / stretch to 0-100 across the book
    fmax = max([r["_frag_raw"] for r in raw if r["_frag_raw"] is not None] or [0]) or 1.0
    smax = max([r["_stretch_raw"] for r in raw if r["_stretch_raw"] is not None] or [0])
    band = (sent.get("band") or "neutral").lower()
    urgency = BAND_URGENCY.get(band, 1.0)

    rows = []
    for r in raw:
        frag = round(r["_frag_raw"] / fmax * 100.0, 1) if r["_frag_raw"] is not None else None
        if r["_stretch_raw"] is None:
            stretch = None
        elif smax <= 0:
            stretch = 0.0
        else:
            stretch = round(r["_stretch_raw"] / smax * 100.0, 1)
        if frag is None:
            score = None
        else:
            # Friction (LTCG proximity / unknown lot dates / dust threshold) is deliberately
            # excluded from the score itself (removed 2026-09-06, user request) -- it still
            # computes and displays per-row as a cost-of-acting annotation, but no longer
            # discounts a name's ranked fragility. A name that's genuinely fragile stays ranked
            # on fragility alone; friction is read alongside the rank, not baked into it.
            score = frag * (1.0 + (stretch or 0.0) / 100.0) * urgency
            score = round(score, 1)
        r.pop("_frag_raw"); r.pop("_stretch_raw")
        note = r.pop("_frag_note")
        if note:
            dq.append(f"{r['ticker']}: {note}")
        rows.append({**r, "fragility_score": frag, "stretch_score": stretch, "derisk_score": score,
                     "sentiment_band": band, "urgency_multiplier": urgency})

    rows.sort(key=lambda x: -(x["derisk_score"] or -1))
    for i, r in enumerate(rows, 1):
        r["rank"] = i

    stretched = [r["ticker"] for r in rows
                 if (r["rel_strength_1m_pp"] or 0) > 0 and (r["abs_return_1m_pct"] or 0) > 0]
    beat_but_down = [r["ticker"] for r in rows
                     if (r["rel_strength_1m_pp"] or 0) > 0 and (r["abs_return_1m_pct"] or 0) <= 0]
    top = [r for r in rows if r["derisk_score"] is not None][:5]

    caveat = (f" ({len(beat_but_down)} more beat SMH but are still down absolutely -- fell less, "
              f"nothing to give back, deliberately not counted as stretched.)") if beat_but_down else ""
    if not stretched:
        queue_state = "no_stretch"
        headline = ("Nothing is stretched -- no holding is both ahead of SMH and up on the month. "
                    "Queue is ordered by fragility alone: a sizing reference, not a sell signal." + caveat)
    elif len(stretched) <= 3:
        queue_state = "narrow_stretch"
        headline = (f"Only {len(stretched)} name(s) both ahead of SMH and actually up ({', '.join(stretched)}). "
                    "Selective single-name profit-taking, not a book-wide de-risking event." + caveat)
    else:
        queue_state = "broad_stretch"
        headline = (f"{len(stretched)} names both ahead of SMH and up on the month -- broad strength. "
                    "This is the regime the queue is built for; work the top of it." + caveat)

    if missing_rel:
        dq.append(f"rel_strength_1m missing for {len(missing_rel)} name(s): {', '.join(missing_rel[:8])}"
                  f"{'...' if len(missing_rel) > 8 else ''} -- stretch scored as null, never estimated")
    if not rel_vals:
        dq.append("rel_strength_1m cache absent entirely -- queue is fragility-only this run")
    if no_rsi_for_strong:
        dq.append(f"{', '.join(no_rsi_for_strong)}: strengthening + net-bullish + over ATR cap, but "
                  f"no RSI14 cached -- cannot check the overbought exemption, cap multiplier applied "
                  f"in full (same fallback rotation_bucket uses)")

    emit({
        "as_of": today.isoformat(),
        "benchmark": rel_cache.get("benchmark", "SMH"),
        "benchmark_return_1m_pct": rel_cache.get("benchmark_return_1m_pct"),
        "rel_strength_as_of": rel_cache.get("as_of"),
        "sentiment_band": band, "urgency_multiplier": urgency,
        "ltcg_months": ltcg_months,
        "queue_state": queue_state, "headline": headline,
        "names_stretched": stretched,
        "names_beat_benchmark_but_down": beat_but_down,
        "aggregate_open_risk_pct": risk.get("aggregate_open_risk_pct"),
        "aggregate_open_risk_cap_pct": risk.get("aggregate_open_risk_cap_pct"),
        "queue": rows,
        "shadow_new": [{"date": today.isoformat(), "ticker": r["ticker"], "rank": r["rank"],
                        "derisk_score": r["derisk_score"], "queue_state": queue_state,
                        "price_at_flag": (round(r["market_value_usd"] / q, 4)
                                          if (q := next((h.get("qty") for h in state.get("holdings", [])
                                                         if h.get("ticker") == r["ticker"]), None)) else None),
                        "scored": False}
                       for r in top],
        "data_quality": dq,
    })


# ---------------------------------------------------------------------------
# triggers
# ---------------------------------------------------------------------------
def _parse_as_of(raw):
    """Cache as_of dates are not always bare ISO strings -- atr20's carries a trailing note
    ("2026-08-10 (partial refresh: INTC added...)"). Take the leading date, ignore the prose."""
    if not raw or not isinstance(raw, str):
        return None
    try:
        return date.fromisoformat(raw.strip()[:10])
    except ValueError:
        return None




def _rebound_screen(book, risk, policy, dc, universe, thesis, today,
                    rel_usable=True, rel_age=None, support=None):
    """Measure whether the book is in a broad correction, and if so which names have fallen
    far enough — and are volatile enough — to be worth watching for a relief rally.

    THE VOLATILITY TENSION, stated because it is the whole design question here. The user wants
    HIGH-volatility names: they fall hardest in a broad selloff and bounce hardest on the
    relief, which is what makes the trade worth taking. But this desk's own signal doctrine
    normalises moves by each name's ATR precisely so that a big move on a loud name is not
    mistaken for a real dislocation — and applying that here would de-select exactly the names
    the mandate is about.

    Both readings are kept, and neither is allowed to silently win. Selection and ranking
    follow the mandate (fall depth x volatility, both positive). `fall_atr_mult` is computed
    and reported ALONGSIDE, so a candidate whose 20% fall is only 1.3 of its own average daily
    ranges is visibly ordinary rather than dressed up as a dislocation. The screen picks the
    candidate; the normaliser tells you how unusual it actually is.
    """
    warn = abs(policy.get("drawdown_warn_pct") or 15.0)
    dd = book.get("drawdown_pct")
    rel = dc.get("rel_strength_1m", {}) or {}
    abs_1m = rel.get("values_abs_pct", {}) or {}
    bench_1m = rel.get("benchmark_return_1m_pct")
    # 5-day is the primary window: a selloff resolves in about a week, and a 1-month lookback
    # straddles the rally that preceded it, so a name down 18% in five days can read flat.
    r5 = dc.get("ret_5d", {}) or {}
    fall_5d = r5.get("values_pct", {}) or {}
    bench_5d = r5.get("benchmark_return_pct")

    def _fall(t):
        """(value, window_label, threshold). 5-day where available, 1-month as a LABELLED
        fallback -- never silently mixed, since the two are not comparable magnitudes."""
        if fall_5d.get(t) is not None:
            return fall_5d[t], "5d", REBOUND_MIN_FALL_PCT
        if abs_1m.get(t) is not None:
            return abs_1m[t], "1m_fallback", REBOUND_MIN_FALL_PCT_1M_FALLBACK
        return None, None, None
    atr = (dc.get("atr20", {}) or {}).get("values_pct", {}) or {}
    held = [r["ticker"] for r in risk.get("positions", [])]

    fallen = [t for t in held if (_fall(t)[0] is not None
                                  and _fall(t)[0] <= REBOUND_BREADTH_FALL_PCT)]
    breadth = (len(fallen) / len(held)) if held else 0.0

    reasons = []
    state = "none"

    def worse(a, b):
        return CORRECTION_STATES.index(a) > CORRECTION_STATES.index(b)

    def bump(to, why):
        nonlocal state
        if worse(to, state):
            state = to
        reasons.append(why)

    if dd is not None:
        if dd <= -warn * REBOUND_DEEP_FRACTION_OF_WARN:
            bump("deep_correction", f"book drawdown {dd:.2f}% at or past the policy warn line ({-warn:.0f}%)")
        elif dd <= -warn * REBOUND_CORRECTION_FRACTION_OF_WARN:
            bump("correction", f"book drawdown {dd:.2f}% past half the policy warn line ({-warn/2:.1f}%)")
        elif dd <= -warn * REBOUND_PULLBACK_FRACTION_OF_WARN:
            bump("pullback", f"book drawdown {dd:.2f}% past a quarter of the policy warn line ({-warn/4:.1f}%)")
    if bench_5d is not None:
        # A benchmark that fell this far in a WEEK is the case this screen exists for.
        if bench_5d <= REBOUND_BENCH_1M_CORRECTION_PCT:
            bump("correction", f"benchmark 5d {bench_5d:.2f}% at or past {REBOUND_BENCH_1M_CORRECTION_PCT}%")
        elif bench_5d <= REBOUND_BENCH_1M_PULLBACK_PCT:
            bump("pullback", f"benchmark 5d {bench_5d:.2f}% at or past {REBOUND_BENCH_1M_PULLBACK_PCT}%")
    elif bench_1m is not None:
        if bench_1m <= REBOUND_BENCH_1M_CORRECTION_PCT:
            bump("correction", f"benchmark 1m {bench_1m:.2f}% at or past {REBOUND_BENCH_1M_CORRECTION_PCT}%")
        elif bench_1m <= REBOUND_BENCH_1M_PULLBACK_PCT:
            bump("pullback", f"benchmark 1m {bench_1m:.2f}% at or past {REBOUND_BENCH_1M_PULLBACK_PCT}%")
    if held and breadth >= REBOUND_BREADTH_SHARE:
        bump("correction", f"breadth: {len(fallen)}/{len(held)} held names down "
                           f"{REBOUND_BREADTH_FALL_PCT}%+ over 1m ({breadth:.0%})")

    # THE SCREEN IS ONLY AS CURRENT AS ITS FALL DATA. Every `fall_pct` here comes from the
    # rel_strength_1m cache, so a stale cache means the 1-month window PREDATES the very selloff
    # this screen exists to find -- and the failure is silent: it returns a short, plausible
    # candidate list rather than an error. Measured on 2026-08-30 the cache was 18 days old with
    # a benchmark 1m of +0.73%, i.e. a flat window, while the book sat 7.9% below its peak. Note
    # that the correction STATE was still detected correctly, because the book-drawdown route
    # reads live prices; it is the per-name candidate screen that degrades.
    stale_warning = None
    if not rel_usable:
        stale_warning = (f"REBOUND CANDIDATES ARE PROVISIONAL: rel_strength_1m is "
                         f"{rel_age if rel_age is not None else 'unknown'}d old, so every "
                         f"fall figure below measures a window that may predate this correction "
                         f"entirely. Breadth and the benchmark route are equally affected. The "
                         f"correction STATE is still sound -- it was reached on live book "
                         f"drawdown. Refresh the cache and re-run before sizing anything.")
    out = {"correction_state": state, "reasons": reasons,
           "inputs_usable": bool(rel_usable), "rel_cache_age_days": rel_age,
           "stale_warning": stale_warning,
           "book_drawdown_pct": dd, "benchmark_1m_pct": bench_1m,
           "breadth_fallen_share": round(breadth, 3),
           "policy_warn_pct": -warn, "candidates": [], "considered": 0,
           "excluded": {"thesis_blocked": [], "too_quiet": [], "not_fallen_enough": [], "no_data": []}}
    if state == "none":
        out["note"] = "No broad correction by any of the three routes -- no rebound screen run."
        return out

    # THE CANDIDATE POOL IS THE UNIVERSE, NOT THE HOLDINGS. A name exited during the selloff is
    # exactly the kind of candidate this is for, and it was structurally invisible before.
    pool = [r for r in (universe.get("tickers") or [])
            if r.get("tier") in ("T1_HELD", "T2_ALUMNI", "T4_WATCHLIST") and not r.get("suppressed")]
    for row in pool:
        t = row["ticker"]
        fall, window, min_fall = _fall(t)
        a = atr.get(t)
        if fall is None or a is None:
            out["excluded"]["no_data"].append(t)
            continue
        out["considered"] += 1
        if fall > min_fall:
            out["excluded"]["not_fallen_enough"].append(t)
            continue
        if a < REBOUND_MIN_ATR_PCT:
            # Not a rejection of the name, only of the TRADE: a low-vol name that fell this far
            # is a different (and slower) thesis than a relief-rally bounce.
            out["excluded"]["too_quiet"].append(t)
            continue
        status = smith_risk.thesis_status(thesis.get(t))
        if status is not None and status not in HEALTHY_THESIS:
            # Same falling-knife gate oversold_reversion already uses: a technical dip on an
            # intact thesis is a setup; a dip alongside a broken one is a knife.
            out["excluded"]["thesis_blocked"].append(f"{t} ({status})")
            continue
        sup = (support or {}).get(t) or {}
        out["candidates"].append({
            "ticker": t, "tier": row["tier"], "cluster": row.get("cluster"),
            "fall_pct": round(fall, 2), "fall_window": window, "atr20_pct": round(a, 2),
            "thesis_status": status,
            "thesis_known": status is not None,
            "support_level": sup.get("nearest_support"),
            "support_label": sup.get("nearest_support_label"),
            "support_distance_pct": sup.get("nearest_support_distance_pct"),
            # Depth of fall in units of the name's own daily range -- the honest counterweight.
            # ATR20 is a DAILY range; comparing a multi-day fall against it directly
            # would overstate the dislocation. Scale by sqrt(window) -- 5d expected
            # range is about 2.24x the daily one.
            "fall_atr_mult": round(abs(fall) / (a * (5 ** 0.5 if window == "5d" else 21 ** 0.5)), 2),
            "rebound_score": round(abs(fall) * (a / 10.0), 1),
            "window": window,
            "last_held_date": row.get("last_held_date"),
        })
    out["candidates"].sort(key=lambda c: -c["rebound_score"])
    ordinary = [c["ticker"] for c in out["candidates"] if c["fall_atr_mult"] < 1.5]
    if ordinary:
        out["note"] = (f"CONTEXT, not a veto: {', '.join(ordinary)} fell less than 1.5x their own "
                       f"average daily range -- loud names being loud, not obvious dislocations. "
                       f"Ranked on the mandate (fall x volatility) regardless; weigh this when sizing.")
    unknown = [c["ticker"] for c in out["candidates"] if not c["thesis_known"]]
    if unknown:
        out["thesis_gap"] = (f"{len(unknown)} candidate(s) have NO thesis entry and so passed the "
                             f"falling-knife gate unexamined rather than on the evidence "
                             f"({', '.join(unknown[:8])}). state.thesis is seeded from current "
                             f"holdings, so alumni and watchlist names are absent by construction.")
    return out


# ---------------------------------------------------------------------------
# cmd_triggers helpers -- one function per lettered trigger section, extracted
# 2026-09-02 so each is independently readable and callable. This is a MECHANICAL
# extraction (each function's body is the original inline block, unchanged) verified
# byte-identical against a golden-master fixture (tests/golden/triggers_case1.json) --
# see tests/verify_triggers.sh. Every function takes its inputs as explicit named
# parameters (no hidden closure over cmd_triggers' locals) and appends its result
# directly to the caller-supplied output list(s), matching the original code's own
# side-effecting style so the diff against the original block is minimal and auditable.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# RISK-SIZED SELLS (Phase 2, 2026-09-20) -- shared helpers for every trigger below
# ---------------------------------------------------------------------------
def _compact_materiality(m):
    """The parts of a smith_ticket.materiality verdict worth persisting on every sized row."""
    if not m:
        return None
    out = {k: m.get(k) for k in ("ok", "floor_usd", "binding_term", "shortfall_usd")}
    if m.get("exempt"):
        out["exempt"] = m["exempt"]
    return out


def _no_sizing():
    """A sizing context with no book -- every risk-sized sell reports size None with a reason
    rather than an estimate. Only reached when a caller omits the context."""
    return smith_ticket.sizing_context(0.0, {}, {})


def _size_sell(family, ticker, mv, sizing, severity_r=None):
    """Size one sell leg of `family` in risk dollars and package the row fields.

    Returns {"fields": {...merged into the row...}, "res": smith_ticket.size_sell_leg's result}.
    `legacy_size_usd` is the OLD market-value-fraction number, carried for one release so the
    golden diff shows what changed per family (smith_core.LEGACY_SELL_FRACTION)."""
    sev = SEVERITY_R[family] if severity_r is None else severity_r
    res = smith_ticket.size_sell_leg(sev, mv, (sizing["stop_pct_by_ticker"] or {}).get(ticker), sizing)
    size = res["size_usd"]
    fields = {"suggested_size_usd": size,
              "legacy_size_usd": round(mv * LEGACY_SELL_FRACTION[family], 2) if family in LEGACY_SELL_FRACTION else None,
              "severity_r": sev, "stop_pct": res["stop_pct"],
              "risk_removed_usd": res["risk_removed_usd"], "sell_action": res["action"],
              "trim_fraction": round(size / mv, 4) if (size and mv) else None,
              "sizing_note": res["sizing_note"], "materiality": _compact_materiality(res["materiality"])}
    return {"fields": fields, "res": res}


def _apply_sell_verdict(row, sized):
    """Fold the materiality / exit-or-hold verdict into a row. A sub-floor ticket is neither
    shrunk nor dropped: a LIVE row is demoted to vote "below_materiality" (shadow rows keep their
    vote -- their job is to be scored, and the verdict rides along in `materiality`)."""
    res = sized["res"]
    row.setdefault("blockers", [])
    if res["vote_hint"] == "below_materiality":
        m = res["materiality"] or {}
        row["materiality_shortfall_usd"] = m.get("shortfall_usd")
        if row.get("vote") == "live":
            row["vote"] = "below_materiality"
        row["blockers"].append(
            (f"below materiality: ${(res['size_usd'] or 0):,.2f} vs a ${m.get('floor_usd', 0):,.2f} floor "
             f"({m.get('binding_term')}) -- emitted, not shrunk to the floor and not dropped"
             if res["action"] != "hold" else f"not a trim candidate: {res['sizing_note'].split('; ')[-1]}"))
    elif res["vote_hint"] == smith_ticket.UNSIZED:
        row["blockers"].append(res["sizing_note"])
    return row


def _pair_sizing(sizing, total_book, policy, conviction_by_ticker):
    """The caller's sizing context, or one rebuilt from what a pair trigger already has (book,
    policy and each name's ATR in conviction_by_ticker) so it can be called standalone."""
    if sizing is not None:
        return sizing
    stops = {t: smith_ticket.stop_pct_from_atr((c or {}).get("atr_pct"))
             for t, c in (conviction_by_ticker or {}).items()}
    return smith_ticket.sizing_context(total_book, policy, stops)


def _apply_pair_notes(row, sold):
    """Blockers a paired row must carry so the strategist reads WHY a leg is what it is."""
    row.setdefault("blockers", [])
    sell = sold["res"]
    if sell["vote_hint"] == "below_materiality":
        row["blockers"].append("sell leg: " + sell["sizing_note"].split("; ")[-1])
    if row.get("materiality_legs_below"):
        row["blockers"].append(
            f"below materiality ({'+'.join(row['materiality_legs_below'])} leg): the pair is emitted "
            f"but not proposed -- short by ${row['materiality_shortfall_usd']:,.2f}. Not shrunk to the "
            f"floor and not dropped: this is what a ticket too small to act on looks like.")
    rr = row.get("rotation_risk") or {}
    freed = rr.get("r_freed_usd") or 0.0
    if freed and abs(rr.get("heat_delta_final_usd") or 0.0) > 0.05 * freed:
        row["blockers"].append(
            f"not risk-flat: the sell frees ${freed:,.2f} of risk and the buy re-takes "
            f"${rr['buy_risk_final_usd']:,.2f} (bound by {rr.get('bound_by')}); the difference goes to "
            f"cash, not into the book")
    return row


def _cluster_room_for(cluster_rows, cluster):
    """Standing cluster-ceiling room in dollars for `cluster` (cmd_drift's cluster_room_usd), or
    None when the cluster is unknown / has no policy band -- clamp_size treats None as
    non-binding ("unknown != a reason to block"). Every buy site passes THIS instead of a bare
    None: clamp_size promised "never push a cluster over its ceiling" and four of its six call
    sites never enforced it."""
    if not cluster or not cluster_rows:
        return None
    return (cluster_rows.get(cluster) or {}).get("cluster_room_usd")


def _buy_leg_verdict(size, ticker, sizing):
    """Materiality verdict for a BUY of `size` dollars, or None when it is not a ticket."""
    stop = (sizing["stop_pct_by_ticker"] or {}).get(ticker)
    if not size or not stop or not sizing["r_base_usd"]:
        return None
    fee = size * sizing["fee_pct"] / 100.0
    return smith_ticket.materiality(size, stop, sizing["total_book_usd"], sizing["r_base_usd"],
                                    fee, sizing["materiality"])


def _apply_buy_materiality(row, sizing, size_key="suggested_size_usd"):
    """Attach a materiality verdict to a single-leg BUY row -- ANNOTATE ONLY, never demote.

    Sells and rotation legs are demoted to vote "below_materiality" (that is the $56 fix). A
    single-leg buy is deliberately NOT: the desk's standing complaint is zero fresh buy ideas while
    cash sits above its band, most single-leg buys are FIRST TRANCHES (smith_conviction's
    STAGE_FRACTION 0.5) that sit just under the floor by construction (AMAT's $504.51 tranche vs a
    $543 floor on the live 2026-09-20 run), and the floors are still unconfirmed. Demoting them
    would cure the small-ticket problem by deepening the buy drought. So the verdict rides along in
    `materiality` / `materiality_shortfall_usd` with an advisory blocker, and the vote is
    untouched until the user signs the floors and decides buys should be held to them."""
    m = _buy_leg_verdict(row.get(size_key), row.get("ticker"), sizing)
    if m is None:
        return row
    row["materiality"] = _compact_materiality(m)
    if not m["ok"]:
        row["materiality_shortfall_usd"] = m["shortfall_usd"]
        row.setdefault("blockers", []).append(
            f"below the materiality floor (advisory for single-leg buys): ${row[size_key]:,.2f} vs "
            f"${m['floor_usd']:,.2f} ({m['binding_term']}); vote unchanged -- buys are annotated, not "
            f"demoted, until the floors are confirmed")
    return row


def _rotation_buy_leg(sell_size, sell_ticker, buy_t, buy_conv, buy_r_ticket, cluster_room, sizing):
    """Risk-conserving buy leg of a rotation: smith_ticket.rotation_legs, then every existing
    clamp, with the binding constraint NAMED. Returns (size, clamped_by, legs)."""
    st = sizing["stop_pct_by_ticker"] or {}
    legs = smith_ticket.rotation_legs(sell_size, st.get(sell_ticker), buy_r_ticket, st.get(buy_t))
    size, clamped_by = smith_conviction.clamp_size(legs["buy_size_usd"], buy_conv["headroom_usd"],
                                                   cluster_room, None)
    if clamped_by is None and size and size < legs["buy_uncapped_usd"] - 0.01:
        clamped_by = ("buy R_ticket (its own conviction tranche)" if legs["bound_by"] == "buy_r_ticket"
                      else "risk freed by the sell leg")
    elif clamped_by is None and size and legs["bound_by"] == "r_freed":
        clamped_by = "risk freed by the sell leg"
    legs = dict(legs, buy_size_final_usd=size,
                buy_risk_final_usd=round((size or 0.0) * (st.get(buy_t) or 0.0) / 100.0, 2))
    legs["heat_delta_final_usd"] = round(legs["buy_risk_final_usd"] - legs["r_freed_usd"], 2)
    return size, clamped_by, legs


def _pair_verdict(row, sell_res, buy_size, buy_ticker, sizing):
    """Pair-level materiality: BOTH legs must be tickets worth taking. Either leg sub-floor demotes
    a LIVE pair together (the legs retire together, so they may not vote separately)."""
    bm = _buy_leg_verdict(buy_size, buy_ticker, sizing)
    row["buy_leg"]["materiality"] = _compact_materiality(bm)
    row["sell_leg"]["materiality"] = _compact_materiality(sell_res["res"]["materiality"])
    short = []
    if sell_res["res"]["vote_hint"] == "below_materiality":
        short.append(("sell", (sell_res["res"]["materiality"] or {}).get("shortfall_usd")))
    if bm is not None and not bm["ok"]:
        short.append(("buy", bm["shortfall_usd"]))
    if not short:
        return row
    row["materiality_shortfall_usd"] = max((v or 0.0) for _, v in short)
    row["materiality_legs_below"] = [k for k, _ in short]
    if row.get("vote") == "live":
        row["vote"] = "below_materiality"
    return row


def _trigger_oversold_reversion(base, ticker, status, healthy, rsi_usable, rsi, over_cap,
                                 headroom, max_single, fundamental_headwind, oversold, dq):
    """Section A: oversold_reversion (BUY, live)."""
    if rsi_usable and rsi is not None and rsi < RSI_OVERSOLD and healthy \
            and not over_cap and (headroom or 0) > 0 and not fundamental_headwind:
        size = min(headroom, max_single) if max_single else 0.0
        oversold.append({**base, "trigger_type": "oversold_reversion", "direction": "BUY",
                         "vote": "live",
                         "headroom_usd": round(headroom, 2),
                         "suggested_size_usd": round(size, 2),
                         "retires_when": f"{ticker} RSI14 recovers above {RSI_OVERSOLD_EXIT:g} "
                                         "(setup consumed) or its thesis leaves intact/strengthening",
                         "reasons": [f"RSI14 {rsi:.1f} < {RSI_OVERSOLD:g} (oversold)",
                                     f"thesis {status} -- technical dip, not a fundamental break",
                                     f"within ATR risk cap with ${headroom:,.0f} headroom"],
                         "blockers": ([] if size > 0 else
                                      ["no deployable cash above the band ceiling -- setup valid, "
                                       "funding is not"])})
    elif rsi_usable and rsi is not None and rsi < RSI_OVERSOLD and not healthy:
        dq.append(f"{ticker} is oversold (RSI {rsi:.1f}) but thesis is '{status}' -- deliberately "
                  "not a bounce candidate (falling knife, not a dip)")


def _trigger_overbought_distribution(base, ticker, rsi_usable, rsi, rel_usable, abs_pct, mv,
                                     sector_map, cluster_rows, rel_vals, risk_by_ticker, thesis,
                                     overbought, sizing=None):
    """Section B: overbought_distribution (TRIM, live). Deliberately INDEPENDENT of over_cap:
    booking profit on a name that ran is the point, and gating it on a risk-cap breach is
    precisely what made every trim an ATR trim.

    SIZED IN RISK (2026-09-20): SEVERITY_R["overbought_distribution"] of the position's own open risk -- see
    smith_core's SEVERITY_R block."""
    sizing = sizing or _no_sizing()
    if rsi_usable and rsi is not None and rsi > RSI_OVERBOUGHT:
        genuinely_up = (abs_pct is not None and abs_pct > 0) if rel_usable else None
        if genuinely_up is not False:
            sized = _size_sell("overbought_distribution", ticker, mv, sizing)
            reasons = [f"RSI14 {rsi:.1f} > {RSI_OVERBOUGHT:g} (overbought)"]
            if genuinely_up:
                reasons.append(f"up {abs_pct:+.1f}% on the month -- real gain to protect")
            blockers = []
            if genuinely_up is None:
                blockers.append("1m return unavailable (stale rel_strength) -- 'genuinely up' "
                                "gate unverified, confirm the position is actually in profit")
            # CLUSTER TENSION (added 2026-08-12). The trim itself stays cap-independent and
            # cluster-independent -- "this name ran, book some" is a valid standalone reason and
            # gating it on cluster state would recreate the ATR-only monoculture in a new form.
            # But a trim of a name whose cluster is UNDER its floor makes that underweight worse,
            # and the G56 family of bugs is exactly this: a cluster figure cited in the wrong
            # direction. Found live on 2026-08-12 -- MSFT tripped overbought while
            # Compute/Hyperscaler sat 7.74pt UNDER floor. So: flag it, never silently allow a
            # downstream proposal to cite the cluster as support, and name the intra-cluster
            # rotation that resolves it (sell the extended name, buy the lagging one in the SAME
            # cluster -> books the gain, leaves the cluster weight untouched).
            cl_row = cluster_rows.get(sector_map.get(ticker)) if cluster_rows else None
            cl_drift = cl_row.get("drift_pt") if cl_row else None
            cluster_tension = cl_drift is not None and cl_drift < 0
            rotation_targets = []
            if cluster_tension:
                # G63: only recommend an intra-cluster rotation if a target actually EXISTS.
                # Found live 2026-08-13 on MSFT -- Compute/Hyperscaler was 10.40pt under floor,
                # yet all three members (MSFT/AMZN/ORCL) were stretched, so the advice sent the
                # reader hunting for a trade that was not there. Eligible = same cluster, not
                # this ticker, negative 1m relative strength (genuinely hasn't run), inside its
                # own ATR cap, and thesis not broken.
                my_cluster = sector_map.get(ticker)
                for ot, orow in risk_by_ticker.items():
                    if ot == ticker or sector_map.get(ot) != my_cluster:
                        continue
                    orel = rel_vals.get(ot)
                    if orel is None or orel >= 0 or orow.get("over_cap"):
                        continue
                    if smith_risk.thesis_status(thesis.get(ot)) == "broken":
                        continue
                    rotation_targets.append({"ticker": ot, "rel_pp": round(orel, 2),
                                             "headroom_usd": orow.get("headroom_usd")})
                rotation_targets.sort(key=lambda x: x["rel_pp"])
                base_msg = (f"cluster {my_cluster} is {cl_drift:+.2f}pt UNDER its floor -- this "
                            f"trim deepens an existing underweight. The stretch reason stands on "
                            f"its own, but do NOT cite the cluster as support (G56).")
                if rotation_targets:
                    tgt = ", ".join(f"{t['ticker']} ({t['rel_pp']:+.1f}pp, "
                                    f"${(t['headroom_usd'] or 0):,.0f} headroom)"
                                    for t in rotation_targets[:3])
                    blockers.append(f"{base_msg} Resolve it as an INTRA-CLUSTER ROTATION into: "
                                    f"{tgt} -- books the gain and leaves the cluster weight "
                                    f"unchanged.")
                else:
                    blockers.append(f"{base_msg} NO intra-cluster rotation is available: every "
                                    f"other name in {my_cluster} has already run (none has "
                                    f"negative 1m relative strength while inside its ATR cap). "
                                    f"So the real choice is trim-anyway and accept a deeper "
                                    f"underweight, or leave it -- there is no third option this "
                                    f"run. Do not go looking for one.")
            overbought.append(_apply_sell_verdict({**base, "trigger_type": "overbought_distribution",
                               "direction": "TRIM", "vote": "live",
                               **sized["fields"],
                               "over_cap_independent": True,
                               "cluster_tension": cluster_tension,
                               "cluster_drift_pt": cl_drift,
                               "rotation_targets": rotation_targets,
                               "retires_when": f"{ticker} RSI14 falls below {RSI_OVERBOUGHT_EXIT:g} "
                                               "or it is no longer up on the month",
                               "reasons": reasons, "blockers": blockers}, sized))


def _trigger_laggard_rotation(base, ticker, rel_usable, laggard_set, healthy, over_cap, headroom,
                              status, rel_pp, rel_cache, max_single, fundamental_headwind, laggard):
    """Section C: laggard_rotation (BUY, shadow)."""
    if rel_usable and ticker in laggard_set and healthy and not over_cap \
            and (headroom or 0) > 0 and not fundamental_headwind:
        laggard.append({**base, "trigger_type": "laggard_rotation", "direction": "BUY",
                        "vote": "shadow",
                        "headroom_usd": round(headroom, 2),
                        "suggested_size_usd": round(min(headroom, max_single), 2) if max_single else 0.0,
                        "reasons": [f"bottom-quartile 1m relative strength ({rel_pp:+.1f}pp vs "
                                    f"{rel_cache.get('benchmark', 'SMH')}) -- has not run yet",
                                    f"thesis {status}", "within ATR risk cap"],
                        # Same honesty as oversold_reversion: a $0 size means the SETUP is valid and
                        # the FUNDING is not. Without this the row rendered "$0" with no explanation,
                        # which reads as "the screen found nothing worth sizing" -- the opposite of
                        # what it means. It is also the normal state once cash re-enters its band,
                        # so it will be seen often; a rotation pair funds it from a sell leg instead.
                        "blockers": ([] if max_single else
                                     ["no deployable cash above the band ceiling -- setup valid, "
                                      "funding is not; fund it from a sell leg (rotation pair) "
                                      "rather than from the wallet"])})


def _trigger_catalyst_threat(base, ticker, mv, catalyst_threats_by_ticker, rotation_by_ticker,
                             status, catalyst_threat, sizing=None):
    """Section F: catalyst_threat (TRIM, live). Deliberately independent of over_cap/cluster/cash,
    same discipline as overbought_distribution -- a structural threat is a reason to trim on its
    own, not something that should wait for a volatility-budget breach to also be true.

    SIZED IN RISK (2026-09-20): SEVERITY_R["catalyst_threat"]. The $37.58 SKHY trim this used to
    emit on a $188 stub is now a full exit or nothing (smith_ticket.exit_or_hold)."""
    sizing = sizing or _no_sizing()
    cats = catalyst_threats_by_ticker.get(ticker)
    if cats:
        sized = _size_sell("catalyst_threat", ticker, mv, sizing)
        # A carried-forward catalyst is labelled as such in the reason line (2026-09-08).
        # It is NOT downweighted: a structural threat that no one re-reported this week is
        # still a structural threat -- the label exists so the strategist can see the
        # evidence's age, not so the trigger can quietly discount it.
        reasons = [f"{c.get('headline', '')} ({c.get('date', '')}) -- {c.get('magnitude', '')}"
                   + (f" [carried forward, last confirmed {c.get('last_confirmed') or c.get('date')}]"
                      if c.get("carried_forward") else "")
                   for c in cats]
        blockers = []
        # TENSION, not suppression (same idiom as overbought_distribution's cluster_tension
        # check above): a name can simultaneously carry a strengthening thesis/accumulate
        # rotation signal AND a real, dated financing/structural threat -- those are not the
        # same question, and letting the accumulate signal silently veto the catalyst would
        # recreate exactly the gap this trigger exists to close (AVGO, 2026-08-17: rotation
        # said accumulate on a strengthening thesis while a $370bn bond-downgrade tail risk
        # went unscored). Surface both, let the strategist weigh them.
        rtk_here = rotation_by_ticker.get(ticker, {})
        if rtk_here.get("bucket") == "accumulate" and status in HEALTHY_THESIS:
            blockers.append(f"{ticker} is simultaneously in rotation's accumulate bucket on a "
                            f"{status} thesis -- the catalyst threat and the accumulate signal "
                            "are answering different questions (financing-structure risk vs. "
                            "operating fundamentals); this does not cancel the trigger, but "
                            "size and priority are a judgement call, not a formula")
        read_through = sorted({p for c in cats for p in (c.get("read_through") or [])})
        catalyst_threat.append(_apply_sell_verdict({**base, "trigger_type": "catalyst_threat", "direction": "TRIM",
                                "vote": "live",
                                # which EVENT(s) drive this row -- the dashboard groups by event,
                                # so three events read as three lines, not ten trims
                                "events": [f"{c.get('headline', '')[:90]} ({c.get('date', '')})" for c in cats],
                                "read_through": read_through,
                                **sized["fields"],
                                "over_cap_independent": True,
                                "catalyst_sources": [c.get("source") for c in cats],
                                "retires_when": f"{ticker} no longer appears in a "
                                                "structural-threat factor catalyst",
                                "reasons": reasons, "blockers": blockers}, sized))


def _trigger_thesis_break(base, ticker, status, mv, thesis, thesis_break, sizing=None):
    """Section G: thesis_break (TRIM, live). A broken thesis has nothing to do with cost basis,
    so this is its own top-level check, not chained onto the ratchet/ladder logic -- it must
    fire even when lots.json has no entry for this ticker. LIVE from day one; see the
    constants-file note (the "why live from day one" comment in smith_core.py above
    FUNDAMENTAL_HEADWIND_BUCKETS).

    SIZED IN RISK (2026-09-20): SEVERITY_R["thesis_break"] (40% of open risk); exit_or_hold turns a
    trim that would leave a stub into a full exit and says so."""
    sizing = sizing or _no_sizing()
    if status == "broken":
        ev_for, ev_against, verified = smith_risk.thesis_evidence(thesis.get(ticker))
        thesis_line = smith_risk.thesis_text(thesis.get(ticker))
        sized = _size_sell("thesis_break", ticker, mv, sizing)
        reasons = ([thesis_line] if thesis_line else []) + \
                  [f"broken -- {c.get('claim', '')} ({c.get('date', '')}, {c.get('source', '')})"
                   for c in (ev_against or [])[:3]]
        blockers = []
        if not ev_against:
            blockers.append(f"{ticker} marked broken with no evidence_against recorded -- "
                            "sizing proceeds anyway (a status flip is itself the signal) but "
                            "flag for the next smith-thesis touch to backfill the evidence")
        thesis_break.append(_apply_sell_verdict({**base, "trigger_type": "thesis_break", "direction": "TRIM",
                             "vote": "live",
                             **sized["fields"],
                             "over_cap_independent": True,
                             "evidence_verified": verified,
                             "retires_when": f"{ticker}'s thesis is no longer 'broken'",
                             "reasons": reasons, "blockers": blockers}, sized))


def _trigger_ratchet_and_ladder(base, ticker, r, mv, price, rsi, lots, laggard_set, ratchet,
                                ladder, dq, sizing=None):
    """Sections D/E: profit_ratchet + scale_out_ladder (both shadow). Share the same avg-cost
    precompute, so extracted as one function rather than two -- forcing them apart would mean
    computing avg_cost/priced_qty/unpriced_qty twice for no benefit.

    Each ladder rung sells SEVERITY_R["scale_out_ladder"] of risk (was a third of market value per
    rung); every rung is the same size because the risk it removes is the same."""
    sizing = sizing or _no_sizing()
    avg_cost, priced_qty, unpriced_qty = _avg_cost_from_lots(lots.get(ticker))
    if avg_cost and price:
        gain_pct = (price - avg_cost) / avg_cost * 100.0
        stop = r.get("stop_price_usd")
        basis_note = ([f"{unpriced_qty:g} share(s) have no known cost (G1 synthetic lot) -- "
                       "average is over the priced portion only"] if unpriced_qty else [])
        if gain_pct >= RATCHET_MIN_GAIN_PCT and stop is not None and stop < avg_cost:
            ratchet.append({**base, "trigger_type": "profit_ratchet", "direction": "STOP_RAISE",
                            "vote": "shadow",
                            "avg_cost_usd": round(avg_cost, 4), "gain_pct": round(gain_pct, 2),
                            "current_stop_usd": round(stop, 4),
                            "suggested_stop_usd": round(avg_cost, 4),
                            "gain_at_risk_usd": round((avg_cost - stop) * (priced_qty or 0), 2),
                            "reasons": [f"up {gain_pct:+.1f}% vs a ${avg_cost:,.2f} basis",
                                        f"stop sits at ${stop:,.2f}, BELOW breakeven -- a "
                                        "retracement turns this winner into a realised loss"],
                            "blockers": basis_note})
        sized = _size_sell("scale_out_ladder", ticker, mv, sizing)
        legacy_slice = round(mv * LEGACY_SELL_FRACTION["scale_out_ladder"], 2)
        tiers = [{"gain_pct": t, "triggered": gain_pct >= t,
                  "slice_usd": sized["fields"]["suggested_size_usd"],
                  "legacy_slice_usd": legacy_slice} for t in LADDER_TIERS_PCT]
        if any(t["triggered"] for t in tiers):
            hit = [t for t in tiers if t["triggered"]]
            rungs = ", ".join("+%g%%" % t["gain_pct"] for t in hit)
            ladder.append(_apply_sell_verdict({**base, "trigger_type": "scale_out_ladder", "direction": "TRIM",
                           "vote": "shadow",
                           "avg_cost_usd": round(avg_cost, 4), "gain_pct": round(gain_pct, 2),
                           "tiers": tiers,
                           **sized["fields"],
                           "reasons": [f"up {gain_pct:+.1f}% vs basis -- "
                                       f"{len(hit)} of {len(tiers)} scale-out rung(s) reached "
                                       f"({rungs})"],
                           "blockers": list(basis_note)}, sized))
    elif ticker in laggard_set or (rsi is not None and rsi > RSI_OVERBOUGHT):
        if not lots.get(ticker):
            dq.append(f"{ticker} has no lots.json entry -- profit_ratchet/scale_out_ladder "
                      "cannot be computed (no cost basis)")


def _trigger_conviction_held(base, ticker, r, mv, price, rsi, rel_pp, rsi_usable, healthy,
                             over_cap, headroom, thesis, signal_history, atr_vals, total_book,
                             policy, deployable_for_ideas, build_ctx, conviction_by_ticker,
                             catalyst_threats_by_ticker, lots, trend_entry, trend_breakdown,
                             conviction_average, conviction_exit, dq, sizing=None, cluster_rows=None):
    """Sections H/I/J/K: the four conviction-driven triggers on currently-HELD tickers (added
    2026-08-24). Kept as one function, not four -- all of H/I/J/K share the SAME conv/ctx/
    buckets/polarity computed once per ticker, and splitting them apart would mean either
    recomputing that shared state four times or threading it through four call sites, neither
    of which is safer than the original single pass. Also populates conviction_by_ticker,
    consumed later by the O/P rotation-pairing pass -- that population must happen here
    regardless of which of H/I/J/K (if any) actually fires.

    2026-09-20: trend_breakdown / conviction_exit sell in RISK (SEVERITY_R), and the two buys
    (trend_entry / conviction_average) now pass their cluster's REAL ceiling room to clamp_size
    instead of None."""
    sizing = sizing or _no_sizing()
    cluster_room = _cluster_room_for(cluster_rows, r.get("cluster"))
    buckets = signal_history.get(ticker) or []
    ctx = build_ctx(ticker, thesis.get(ticker), buckets, price, rsi, rel_pp, ticker)
    conv = smith_conviction.score_conviction(ctx)
    conviction_by_ticker[ticker] = {**conv, "cluster": r.get("cluster"), "rel_pp": rel_pp,
                                    "over_cap": over_cap, "headroom_usd": headroom,
                                    "market_value_usd": mv, "price": price, "atr_pct": atr_vals.get(ticker)}
    polarity = smith_risk.classify_signal_polarity(buckets)

    # --- H. trend_entry (BUY, live) -- ORGANISING RULE: price extended/rising + thesis
    # strong -> hold or add on strength. Fires on a genuine breakout/uptrend bucket, not on
    # RSI alone (RSI-based entries are oversold_reversion's job) -- this is the direct fix
    # for "NEW TAILWINDS drives zero logic today": a bullish trend bucket now scores
    # conviction UP and, past the bar, becomes an add.
    if healthy and {"BREAKOUT", "STRONG UPTREND"} & set(buckets) and not over_cap \
            and conv["conviction_tier"] not in ("none",) and (headroom or 0) > 0:
        atr_pct = atr_vals.get(ticker)
        pmax = (smith_conviction.policy_max_position_usd(atr_pct, price, total_book, policy)
                if atr_pct and price else None)
        target, wanted = ((None, None) if not pmax else
                          smith_conviction.conviction_size(conv["conviction_tier_pct"], pmax["max_position_usd"]))
        size_final, clamped_by = smith_conviction.clamp_size(wanted, headroom, cluster_room, deployable_for_ideas)
        trend_entry.append({**base, "trigger_type": "trend_entry", "direction": "BUY", "vote": "live",
                           "conviction_score": conv["conviction_score"], "conviction_tier": conv["conviction_tier"],
                           "size_wanted_usd": wanted, "suggested_size_usd": size_final, "clamped_by": clamped_by,
                           "stop_price_usd": pmax.get("stop_price_usd") if pmax else None,
                           "retires_when": f"{ticker} no longer carries BREAKOUT/STRONG UPTREND or thesis leaves intact/strengthening",
                           "reasons": conv["conviction_reasons"], "blockers": []})

    # --- I. trend_breakdown (TRIM/SELL, live) -- price falling + thesis weak -> exit the
    # breakdown. Mirror of H on the bearish side.
    if not healthy and {"BREAKDOWN", "STRONG DOWNTREND"} & set(buckets):
        sized = _size_sell("trend_breakdown", ticker, mv, sizing)
        trend_breakdown.append(_apply_sell_verdict({**base, "trigger_type": "trend_breakdown", "direction": "TRIM", "vote": "live",
                               "conviction_score": conv["conviction_score"], "conviction_tier": conv["conviction_tier"],
                               **sized["fields"], "over_cap_independent": True,
                               "retires_when": f"{ticker} no longer carries BREAKDOWN/STRONG DOWNTREND or thesis recovers",
                               "reasons": conv["conviction_reasons"], "blockers": []}, sized))

    # --- J. conviction_average (BUY, live) -- ORGANISING RULE: price lagging/fallen + thesis
    # strong -> average down. Requires the BLENDED entry to stay ABOVE the current stop --
    # per user decision, this trigger REFUSES the add rather than quietly widen the stop.
    # Fair-value anchor = technical support, proxied as price - 2xATR (same fallback rule
    # smith-rebound already uses live) since no persisted moving-average support level exists.
    atr_pct = atr_vals.get(ticker)
    # Gate is "not none", not "medium+" -- the tier already scales size (conviction_tier_pct),
    # so requiring medium+ here was a redundant second restriction on top of that scaling,
    # and it starved every candidate whose only available input was an unverified thesis
    # (the common case -- 22 of 33 in this book) since that alone lands in "low", not "medium".
    if healthy and atr_pct and price and conv["conviction_tier"] != "none" and not over_cap:
        # 1x ATR, not 2x -- 2x ATR is literally the STOP distance (policy's own
        # stop_distance_pct = max(2*atr_pct, 3.0)), so using it as a "support" level made
        # this trigger require price to have fallen almost all the way to its own stop
        # before ever registering as a dip -- confirmed live: GLW needed to fall to ~$115
        # from $145 (2x ATR) when smith-rebound's own live moving-average support sat at
        # $140.23, a ~3.5% dip. 1x ATR is a rougher compute-only proxy for that same idea
        # (no persisted moving-average level exists to read directly) and should be
        # superseded by a live-dispatched agent's real support number when one is available.
        support = price * (1 - atr_pct / 100.0)
        avg_cost_h, priced_qty_h, _ = _avg_cost_from_lots(lots.get(ticker))
        stop_now = r.get("stop_price_usd")
        # Gate on genuine drawdown vs COST BASIS, not proximity to the ATR-support proxy --
        # tried the proxy first and it required price within 1x ATR of support, which for a
        # book running 9-15% ATR20 names meant "has fallen almost to its own support zone",
        # rarely true for a name merely off its highs. "Price below what you paid" is a
        # directly-measurable, defensible reading of "drawdown beyond fair price" (fair
        # price = your own entry), and `support` is still carried on the row as context for
        # where a real technical floor roughly sits, just not the gating test.
        if avg_cost_h and priced_qty_h and stop_now is not None and price < avg_cost_h:
            pmax = smith_conviction.policy_max_position_usd(atr_pct, price, total_book, policy)
            target, wanted = smith_conviction.conviction_size(conv["conviction_tier_pct"], pmax["max_position_usd"])
            size_final, clamped_by = smith_conviction.clamp_size(wanted, headroom, cluster_room, deployable_for_ideas)
            add_qty = (size_final / price) if (size_final and price) else 0.0
            blended = ((avg_cost_h * priced_qty_h) + (price * add_qty)) / (priced_qty_h + add_qty) if add_qty else avg_cost_h
            if blended > stop_now:
                conviction_average.append({**base, "trigger_type": "conviction_average", "direction": "BUY",
                                          "vote": "live", "conviction_score": conv["conviction_score"],
                                          "conviction_tier": conv["conviction_tier"],
                                          "support_usd": round(support, 4), "size_wanted_usd": wanted,
                                          "suggested_size_usd": size_final, "clamped_by": clamped_by,
                                          "blended_entry_usd": round(blended, 4), "current_stop_usd": round(stop_now, 4),
                                          # `stop_price_usd` is the name _draft_leg_spec and the
                                          # proposal row read; this row emitted only
                                          # `current_stop_usd`, so every conviction_average
                                          # draft leg went out with stop_price_usd=None.
                                          "stop_price_usd": round(stop_now, 4),
                                          "retires_when": f"{ticker} recovers above its support level or thesis leaves intact/strengthening",
                                          "reasons": conv["conviction_reasons"], "blockers": []})
            else:
                dq.append(f"{ticker}: conviction_average setup found but blended entry ${blended:.2f} "
                          f"would sit below the current stop ${stop_now:.2f} -- refused per standing rule, "
                          "not sized")

    # --- K. conviction_exit (SELL, live) -- convergence of negatives, not the word 'broken'.
    # There are 0 broken theses in this book; a broken-keyed exit could never fire. Counts
    # how many of {thesis, catalyst, trend, technical} independently read negative and exits
    # only when at least 3 agree -- one bad signal alone never triggers this.
    neg_count = sum([
        1 if smith_risk.thesis_status(thesis.get(ticker)) == "watch" else 0,
        1 if catalyst_threats_by_ticker.get(ticker) else 0,
        1 if polarity["net"] < 0 else 0,
        1 if (rsi_usable and rsi is not None and rsi > RSI_OVERBOUGHT and polarity["net"] <= 0) else 0,
    ])
    if smith_conviction.convergence_exit_score(neg_count) and not over_cap:
        # convergence of negatives is the strongest sell signal this engine has -> the heaviest rung
        # of SEVERITY_R (50% of the position's open risk)
        sized = _size_sell("conviction_exit", ticker, mv, sizing)
        reasons = list(conv["conviction_reasons"])
        reasons.insert(0, f"{neg_count} independent negative signals converged (thesis/catalyst/trend/technical)")
        conviction_exit.append(_apply_sell_verdict({**base, "trigger_type": "conviction_exit", "direction": "SELL", "vote": "live",
                               "conviction_score": conv["conviction_score"], "negative_signal_count": neg_count,
                               **sized["fields"], "over_cap_independent": True,
                               "retires_when": f"fewer than 3 of {ticker}'s independent negative signals remain",
                               "reasons": reasons, "blockers": []}, sized))


def _trigger_entry_setup_scan(watchlist_setups, risk_by_ticker, state, signal_history, thesis,
                              factor_catalysts, earnings_facts, mention_counts, track_record_for,
                              atr_vals, sector_map, entry_setup, total_book=None, policy=None,
                              deployable_for_ideas=None, market_prices=None, cluster_rows=None):
    """Section L: entry_setup (BUY) -- smith-watchlist's setups, persisted to state.json
    this run for the first time (previously had NO code path into proposals at all -- 9 setups
    found on 2026-08-24, 1 reached a proposal, hand-written narrative only).

    SIZING (added 2026-09-20). `size_final = None` was initialised here and never assigned, so
    entry_setup could not size on ANY input: the 2026-09-20 run had IONQ/QBTS/BABA with a usable
    ATR and empty blockers yet `suggested_size_usd: null`. It now mirrors `reentry`'s three
    lines. Price comes from the setup row's own `price_usd` (smith-watchlist has it when it
    computes upside/pos); when the row lacks one, or ATR is missing, size stays None WITH a
    blocker -- a missing input is never estimated.

    THESIS GATE (same date, and it must ship WITH the sizing). The four live candidates that
    day (IONQ/QBTS/RGTI/BABA) all had `thesis_status: null` and cleared the 'low' conviction
    floor by 0.6-0.8 points on valuation + RSI alone. Sizing them live would cure the buy
    drought by lowering quality. A setup with no state.thesis entry therefore votes `shadow`
    (logged, never a ticket) with a blocker naming the missing thesis, until smith-thesis has
    actually examined the name.

    PRICE (2026-09-20, Phase 2 prerequisite). Setup rows carry no price, and the four candidates
    were in NEITHER live_quotes.json nor bars.json, so the sizing above stayed inert on the live
    run. smith_fetch now fetches candidate names; this reads `market_prices` (live quote, else the
    last daily close) when the row lacks `price_usd`. A price is NEVER back-derived from an
    analyst target and an upside percentage -- that would invent the input the sizing depends on."""
    market_prices = market_prices or {}
    for row in watchlist_setups:
        ticker = row.get("ticker")
        if not ticker or ticker in risk_by_ticker:
            continue
        if smith_risk.is_watchlist_suppressed(state, ticker):
            continue  # user clicked "Not interested" on the dashboard -- see smith_risk's reader
        # watchlist_setups' `pos` (0-1 within the 52-week range) is real technical signal that
        # was going unused here -- reused as an RSI-scale proxy (pos*100) so a name near its
        # 52wk low reads as oversold-ish, same as a genuine RSI would. Not a substitute for a
        # real RSI, but a documented, defensible reuse of a number the desk already computed
        # rather than leaving the technical component at a flat 0 for every watchlist name.
        pos = row.get("pos")
        buckets_for_ticker = signal_history.get(ticker) or []
        ctx = {"ticker": ticker, "thesis_entry": thesis.get(ticker), "factor_catalysts": factor_catalysts,
               "buckets": buckets_for_ticker, "upside_pct": row.get("upside_pct"),
               "earnings_fact": earnings_facts.get(ticker),
               "rsi": (pos * 100 if pos is not None else None), "rsi_usable": pos is not None,
               "rel_pp": None, "rel_usable": False, "mention_count": mention_counts.get(ticker, 0),
               "track_record": track_record_for(buckets_for_ticker)}
        conv = smith_conviction.score_conviction(ctx)
        if conv["conviction_tier"] == "none":
            continue
        atr_pct = atr_vals.get(ticker)
        price = row.get("price_usd")
        price_source = "setup_row" if price else None
        if not price and market_prices.get(ticker):
            price, price_source = market_prices[ticker]["price"], market_prices[ticker]["source"]
        blockers = []
        if not atr_pct:
            blockers.append(f"no live ATR for {ticker} this run -- setup valid, sizing needs a fetch")
        if not price:
            blockers.append(f"no price_usd on {ticker}'s watchlist setup row and none in "
                            "live_quotes.json/bars.json -- sizing needs a fetched price")
        pmax = (smith_conviction.policy_max_position_usd(atr_pct, price, total_book, policy)
                if (atr_pct and price) else None)
        target, wanted = ((None, None) if not pmax else
                          smith_conviction.conviction_size(conv["conviction_tier_pct"], pmax["max_position_usd"]))
        size_final, clamped_by = ((None, None) if wanted is None else
                                  smith_conviction.clamp_size(
                                      wanted, None, _cluster_room_for(cluster_rows, sector_map.get(ticker)),
                                      deployable_for_ideas))
        vote = "live"
        if thesis.get(ticker) is None:
            vote = "shadow"
            blockers.append(f"no state.thesis entry for {ticker} -- entry_setup may not vote live "
                            "on valuation + RSI alone; smith-thesis must examine it first")
        entry_setup.append({"ticker": ticker, "cluster": sector_map.get(ticker), "thesis_status": conv["thesis_status"],
                            "watchlist_type": row.get("type"), "upside_pct": row.get("upside_pct"),
                            "price_usd": price, "price_source": price_source,
                            "trigger_type": "entry_setup", "direction": "BUY", "vote": vote,
                            "conviction_score": conv["conviction_score"], "conviction_tier": conv["conviction_tier"],
                            "size_wanted_usd": wanted, "suggested_size_usd": size_final, "clamped_by": clamped_by,
                            "stop_price_usd": pmax.get("stop_price_usd") if pmax else None,
                            "retires_when": f"{ticker} drops off the watchlist setups list or conviction falls to 'none'",
                            "reasons": conv["conviction_reasons"], "blockers": blockers})


def _trigger_reentry_scan(trades, recently_exited, signal_history, thesis, factor_catalysts,
                          earnings_facts, upside_pct_for, rsi_vals, rsi_usable, rel_vals,
                          rel_usable, mention_counts, track_record_for, atr_vals, total_book,
                          policy, deployable_for_ideas, sector_map, reentry, reentry_no_thesis,
                          reentry_judged_out, cluster_rows=None):
    """Section M: reentry (BUY, live) -- the direct fix for "an exited name has no headroom row,
    so the engine sizes its re-entry at $0": recently_exited tickers, priced from the last known
    fill (trades.json), sized via policy_max_position_usd at qty=0 (works for unheld names by
    construction -- see smith_conviction's module note). Appends ticker names into
    reentry_no_thesis/reentry_judged_out (both caller-supplied lists) for the G72-shaped
    dq message the caller writes after this returns."""
    last_exit_price = {}
    for tr in sorted(trades.get("trades", []), key=lambda r: r.get("date") or ""):
        # Chronological, so the LAST priced fill wins -- and keyed on the ticker being in the
        # pool rather than on the row carrying an "exit" label, since the universe finds exits
        # that were never labelled one.
        if tr.get("ticker") in recently_exited and tr.get("price_at_trade"):
            last_exit_price[tr["ticker"]] = tr.get("price_at_trade")
    for ticker, exit_date in recently_exited.items():
        price = last_exit_price.get(ticker)
        buckets_for_ticker = signal_history.get(ticker) or []
        ctx = {"ticker": ticker, "thesis_entry": thesis.get(ticker), "factor_catalysts": factor_catalysts,
               "buckets": buckets_for_ticker, "upside_pct": upside_pct_for(ticker, price),
               "earnings_fact": earnings_facts.get(ticker), "rsi": rsi_vals.get(ticker), "rsi_usable": rsi_usable,
               "rel_pp": rel_vals.get(ticker), "rel_usable": rel_usable, "mention_count": mention_counts.get(ticker, 0),
               "track_record": track_record_for(buckets_for_ticker)}
        conv = smith_conviction.score_conviction(ctx)
        if conv["conviction_tier"] == "none" or conv["thesis_status"] not in ("intact", "strengthening"):
            # exited-and-still-weak is not a re-entry case, it's confirmation the exit was right.
            # BUT distinguish "judged and rejected" from "could not be judged": state.thesis is
            # seeded from CURRENT holdings, so an alumnus usually has NO thesis entry at all and
            # fails this gate for absence of evidence rather than on the evidence. That is the
            # G72 shape again -- a name is silent in a file that cannot represent it. Count both
            # so the gap is visible instead of looking like "no candidates today".
            (reentry_no_thesis if thesis.get(ticker) is None else reentry_judged_out).append(ticker)
            continue
        atr_pct = atr_vals.get(ticker)
        pmax = smith_conviction.policy_max_position_usd(atr_pct, price, total_book, policy) if (atr_pct and price) else None
        target, wanted = ((None, None) if not pmax else
                          smith_conviction.conviction_size(conv["conviction_tier_pct"], pmax["max_position_usd"]))
        size_final, clamped_by = smith_conviction.clamp_size(
            wanted, None, _cluster_room_for(cluster_rows, sector_map.get(ticker)), deployable_for_ideas)
        reentry.append({"ticker": ticker, "cluster": sector_map.get(ticker), "thesis_status": conv["thesis_status"],
                        "exited_on": exit_date.isoformat(), "price_usd": price,
                        "trigger_type": "reentry", "direction": "BUY", "vote": "live",
                        "conviction_score": conv["conviction_score"], "conviction_tier": conv["conviction_tier"],
                        "size_wanted_usd": wanted, "suggested_size_usd": size_final, "clamped_by": clamped_by,
                        "stop_price_usd": pmax.get("stop_price_usd") if pmax else None,
                        "retires_when": f"{ticker}'s thesis leaves intact/strengthening",
                        "reasons": [f"exited {exit_date.isoformat()} at ${price:.2f}" if price else f"exited {exit_date.isoformat()}"]
                                  + conv["conviction_reasons"],
                        "blockers": ([] if pmax else [f"no live ATR for {ticker} -- exit price is last-known, not live"])})


def _trigger_bench_diversifier_scan(diversifier_candidates, risk_by_ticker, state, mention_counts,
                                    track_record_for, atr_vals, total_book, policy,
                                    deployable_for_ideas, bench_diversifier, market_prices=None,
                                    cluster_rows=None, sector_map=None):
    """Section N: bench_diversifier (BUY, live) -- smith-scout's diversifier bench, sized for the
    first time. VST's 63.9% modelled upside had never once been referenced by any proposal.
    Honest limit: these names carry no thesis, no factor_catalysts, and no pos/RSI proxy in
    this book (unlike watchlist_setups), so valuation is often the ONLY component available --
    rarely enough alone to clear even "low" tier. This trigger firing empty on a given run is
    not a bug; it means the compute-only pass genuinely has too little independently-verified
    information on these names, not that the bench isn't worth reading (it still renders on
    the dashboard regardless of whether it clears the bar to become a sized proposal)."""
    for ticker, dv in diversifier_candidates.items():
        if not dv.get("clean_diversifier") or dv.get("status") == "stale" or ticker in risk_by_ticker:
            continue
        if smith_risk.is_watchlist_suppressed(state, ticker):
            continue  # shares the watchlist suppression list -- see smith_risk's reader
        price = dv.get("price_usd") or ((market_prices or {}).get(ticker) or {}).get("price")
        # buckets stays [] genuinely -- these names carry no signal history in this book (see
        # the comment above), so track_record_for([]) correctly returns None rather than
        # faking a bucket to look up. Wired for consistency with the other 8 triggers rather
        # than left as a hardcoded None, in case a diversifier candidate later gains signal
        # coverage without anyone remembering to revisit this site.
        ctx = {"ticker": ticker, "thesis_entry": None, "factor_catalysts": [],
               "buckets": [], "upside_pct": dv.get("upside_pct"), "earnings_fact": None,
               "rsi": None, "rsi_usable": False, "rel_pp": None, "rel_usable": False,
               "mention_count": mention_counts.get(ticker, 0), "track_record": track_record_for([])}
        conv = smith_conviction.score_conviction(ctx)
        if conv["conviction_tier"] == "none":
            continue
        atr_pct = atr_vals.get(ticker)
        pmax = smith_conviction.policy_max_position_usd(atr_pct, price, total_book, policy) if (atr_pct and price) else None
        target, wanted = ((None, None) if not pmax else
                          smith_conviction.conviction_size(conv["conviction_tier_pct"], pmax["max_position_usd"]))
        # A clean diversifier is by definition outside the AI-capex clusters, so it usually has no
        # sector_map entry and therefore no ceiling to breach -- None is the honest answer there;
        # if the name HAS been classified into a banded cluster the real room is passed.
        size_final, clamped_by = smith_conviction.clamp_size(
            wanted, None, _cluster_room_for(cluster_rows, (sector_map or {}).get(ticker)),
            deployable_for_ideas)
        bench_diversifier.append({"ticker": ticker, "cluster": None, "thesis_status": None,
                                  "price_usd": price, "trigger_type": "bench_diversifier", "direction": "BUY",
                                  "vote": "live", "conviction_score": conv["conviction_score"],
                                  "conviction_tier": conv["conviction_tier"], "size_wanted_usd": wanted,
                                  "suggested_size_usd": size_final, "clamped_by": clamped_by,
                                  "stop_price_usd": pmax.get("stop_price_usd") if pmax else None,
                                  "retires_when": f"{ticker} leaves the diversifier bench or its upside falls below 10%",
                                  "reasons": conv["conviction_reasons"],
                                  "blockers": ([] if pmax else [f"no live ATR for {ticker} this run"])})


def _pair_cluster_room_usd(cluster_rows, sell_cluster, buy_cluster, sell_size):
    """Cluster ceiling room available to the BUY leg of a PAIRED rotation, in dollars.

    Added 2026-09-08 with cmd_drift's cluster_room_usd. The subtlety that makes this a function
    rather than a dict lookup: a rotation is a SWAP, and when both legs sit in the same cluster
    the sale creates the very room the purchase consumes -- net cluster weight change is ~zero.
    Clamping such a buy to the cluster's standing room would zero the buy leg of any rotation
    inside an already-full cluster and silently convert it into a naked sell, which is the exact
    opposite of what a rotation trigger is for. So the sale's proceeds are added back when, and
    only when, the legs share a cluster.

    Returns None (non-binding, clamp_size's documented "unknown != a reason to block") when the
    buy cluster has no policy band or drift didn't run.
    """
    row = (cluster_rows or {}).get(buy_cluster) or {}
    room = row.get("cluster_room_usd")
    if room is None:
        return None
    if sell_cluster and buy_cluster and sell_cluster == buy_cluster:
        room += max(0.0, sell_size or 0.0)
    return round(max(0.0, room), 2)


def _trigger_cluster_bench_rotation(cluster_ladders, conviction_by_ticker, thesis,
                                    risk_by_ticker, today, cluster_bench_rotation, sizing=None):
    """Section Q: cluster_bench_rotation (PAIRED, SHADOW). Sell the ladder's laggard, buy a name
    the book does NOT own.

    WHY THIS IS SEPARATE FROM cluster_rotation, and why it is shadow. Often the honest answer to
    "rotate the laggard into what?" is a name outside the book -- a ladder that can only
    recommend from what is already held is choosing the best of a set nobody re-examined. But
    this is the one trigger that introduces a never-held name on a single agent's judgment, with
    no price history in the journal, no thesis entry, no lot, and no track record of this desk
    ever having been right about it. Every other live trigger either acts on a name the book
    knows or is corroborated by a second source. So it logs `price_at_flag` and is scored at
    7/30d first, exactly like laggard_rotation did before it earned a vote -- the standing "a
    new signal class earns its vote before it gets one" rule.

    The SELL leg still has to clear the same bars as a live rotation: fresh ladder, real
    authority, held, not over cap, and a thesis the authority level permits selling. A shadow
    vote is not a licence to relax the sell side; the shadow-ness is entirely about the buy.

    The sell leg is risk-sized (SEVERITY_R["cluster_bench_rotation"]); the buy stays unsized (a
    never-held name has no ticket until it earns a vote).
    """
    sizing = _pair_sizing(sizing, 0.0, {}, conviction_by_ticker)
    for cluster, entry in (cluster_ladders or {}).items():
        bench = [b for b in (entry.get("bench") or []) if isinstance(b, dict) and b.get("ticker")]
        if not bench:
            continue
        authority, eff_conf, _ = smith_risk.ladder_authority(
            entry, today, ttl_days=LADDER_TTL_DAYS, min_scored=LADDER_MIN_SCORED_CALLS)
        if authority not in ("rank", "full"):
            continue
        here = [t for t, c in conviction_by_ticker.items() if c["cluster"] == cluster]
        picked = _cluster_rotation_legs_from_ladder(entry, here, conviction_by_ticker,
                                                    thesis, authority)
        if not picked:
            continue
        sell_t = picked[0]
        # Never propose buying something already held -- that is cluster_rotation's job and it
        # is LIVE. A bench entry naming a holding is a stale ladder, not an idea.
        cand = next((b for b in bench if b["ticker"] not in risk_by_ticker), None)
        if not cand:
            continue
        buy_t = cand["ticker"]
        sell_mv = conviction_by_ticker[sell_t]["market_value_usd"]
        sold = _size_sell("cluster_bench_rotation", sell_t, sell_mv, sizing)
        sell_size = sold["fields"]["suggested_size_usd"]
        row = {
            "pair_id": f"cluster_bench_rotation-{sell_t}-{buy_t}",
            "trigger_type": "cluster_bench_rotation", "vote": "shadow", "cluster": cluster,
            "ladder_as_of": entry.get("as_of"), "ladder_confidence": eff_conf,
            "ladder_authority": authority,
            "sell_leg": {"ticker": sell_t, "direction": "SELL", **sold["fields"],
                         "reasons": [picked[2]]},
            "buy_leg": {"ticker": buy_t, "direction": "BUY", "suggested_size_usd": None,
                        "price_usd": cand.get("price_usd"),
                        "reasons": [f"cluster bench: better than {cand.get('why_better_than') or sell_t}",
                                    f"entry condition: {cand.get('entry_condition') or 'none stated'}"],
                        "blockers": ["SHADOW -- a never-held name on one agent's judgment, with no "
                                     "journal history and no thesis entry. Scored at 7/30d before "
                                     "it can be sized."]},
            "retires_when": (f"EITHER {cluster}'s ladder drops {buy_t} from its bench "
                             f"OR {sell_t} leaves the bottom of that ladder")}
        row["sell_leg"]["materiality"] = _compact_materiality(sold["res"]["materiality"])
        cluster_bench_rotation.append(row)


def _trigger_cluster_consolidation(cluster_ladders, conviction_by_ticker, risk_by_ticker,
                                   today, cluster_consolidation, sizing=None, cluster_rows=None):
    """Section R: cluster_consolidation (PAIRED, SHADOW). Two holdings that are ONE bet -- same
    customer, same product, same process step -- collapsed into the better of the two.

    This is the only rotation on this list that does not change factor exposure at all. It
    shortens the tail: three expressions of one WFE trade carry three sets of idiosyncratic
    risk for one thesis. Shadow because "these are the same bet" is a business judgment with no
    numeric proof available here -- cmd_ladder can only screen for near-identical move and
    volatility, which is a resemblance, not a cause, and no return series is cached to compute
    a real correlation from.

    Only acts on pairs the agent explicitly marked `verdict: "redundant"`. A candidate the agent
    looked at and called `distinct` is a judgment already made, not an unanswered question.

    The sell leg stays a FULL EXIT of the dropped name (no severity: consolidation is not a trim).
    The buy leg is now risk-conserving (smith_ticket.rotation_legs) rather than dollar-matched, and
    passes the kept name's ATR headroom and cluster room through clamp_size.
    """
    sizing = _pair_sizing(sizing, 0.0, {}, conviction_by_ticker)
    for cluster, entry in (cluster_ladders or {}).items():
        authority, eff_conf, _ = smith_risk.ladder_authority(
            entry, today, ttl_days=LADDER_TTL_DAYS, min_scored=LADDER_MIN_SCORED_CALLS)
        if authority not in ("rank", "full"):
            continue
        for rp in (entry.get("redundant_pairs") or []):
            if not isinstance(rp, dict) or rp.get("verdict") != "redundant":
                continue
            keep, drop = rp.get("keep"), rp.get("drop")
            pair = rp.get("pair") or []
            if not keep or not drop:
                # Infer the drop side only when the pair names exactly two and one is `keep`.
                # Guessing which of three names to sell is not a gap worth filling silently.
                others = [t for t in pair if t != keep]
                drop = others[0] if keep and len(pair) == 2 and others else None
            if not keep or not drop or keep == drop:
                continue
            if keep not in conviction_by_ticker or drop not in conviction_by_ticker:
                continue
            if conviction_by_ticker[keep]["over_cap"]:
                continue
            drop_mv = conviction_by_ticker[drop]["market_value_usd"]
            st = sizing["stop_pct_by_ticker"] or {}
            keep_conv = conviction_by_ticker[keep]
            room = _pair_cluster_room_usd(cluster_rows, conviction_by_ticker[drop]["cluster"],
                                          keep_conv["cluster"], drop_mv)
            buy_size, buy_clamped, legs = _rotation_buy_leg(drop_mv, drop, keep, keep_conv, None, room, sizing)
            drop_risk = round(drop_mv * (st.get(drop) or 0.0) / 100.0, 2) if st.get(drop) else None
            row = ({
                "pair_id": f"cluster_consolidation-{drop}-{keep}",
                "trigger_type": "cluster_consolidation", "vote": "shadow", "cluster": cluster,
                "ladder_as_of": entry.get("as_of"), "ladder_confidence": eff_conf,
                "ladder_authority": authority,
                "sell_leg": {"ticker": drop, "direction": "SELL",
                             "suggested_size_usd": round(drop_mv, 2),
                             "legacy_size_usd": round(drop_mv, 2), "sell_action": "full_exit",
                             "risk_removed_usd": drop_risk,
                             "market_value_usd": round(drop_mv, 2),
                             "reasons": [f"same bet as {keep}: {rp.get('same_bet_because') or 'agent verdict'}"]},
                "buy_leg": {"ticker": keep, "direction": "BUY",
                            "suggested_size_usd": buy_size, "clamped_by": buy_clamped,
                            "legacy_size_usd": round(drop_mv, 2),
                            "reasons": [f"the better expression of the {cluster} bet {keep} and "
                                        f"{drop} both make"],
                            "blockers": ["SHADOW -- 'same bet' is a business judgment with no "
                                         "numeric proof available here; the script can only "
                                         "screen for resemblance, never for cause."]},
                "rotation_risk": legs,
                "retires_when": (f"EITHER {cluster}'s ladder stops calling {keep}/{drop} "
                                 f"redundant OR that ladder goes stale")})
            row["buy_leg"]["materiality"] = _compact_materiality(_buy_leg_verdict(buy_size, keep, sizing))
            cluster_consolidation.append(row)


def _trigger_profit_rotation(names_stretched, conviction_by_ticker, thesis, total_book, policy,
                             profit_rotation, cluster_rows=None, sizing=None):
    """Section O: profit_rotation (PAIRED, live). ORGANISING RULE -- sell an EXTENDED name whose
    thesis is WEAK (book profit), buy a LAGGARD whose thesis is STRONG (yet to rally). This is
    "sell what ran, buy what hasn't", scoped by thesis so it never contradicts cluster_rotation.
    One row per rotation idea, never two independently-scored legs -- 19 rotation pairs were
    attempted all-time before this and 0 survived, because the old pairing scored each leg
    separately and one half died. Both legs retire TOGETHER (see cmd_proposals's paired
    retirement rule).

    RISK-SIZED (2026-09-20). The sell leg removes SEVERITY_R["profit_rotation"] of risk; the buy
    leg is what that risk buys in the LAGGARD (smith_ticket.rotation_legs), capped by the laggard's
    own conviction ticket and then by every existing clamp, with the binding one named in
    `clamped_by`. `rotation_risk` on the row reports risk freed / redeployed / left over, so a
    rotation that quietly de-risks (its buy ticket is smaller than the risk freed) says so instead
    of looking flat."""
    sizing = _pair_sizing(sizing, total_book, policy, conviction_by_ticker)
    sell_candidates = [t for t in names_stretched if t in conviction_by_ticker
                       and smith_risk.thesis_status(thesis.get(t)) == "watch"
                       and not conviction_by_ticker[t]["over_cap"]]
    buy_candidates = [t for t in conviction_by_ticker
                      if conviction_by_ticker[t]["conviction_tier"] != "none"
                      and smith_risk.thesis_status(thesis.get(t)) in ("intact", "strengthening")
                      and (conviction_by_ticker[t]["rel_pp"] or 0) < 0
                      and not conviction_by_ticker[t]["over_cap"]]
    used_buys = set()
    for sell_t in sorted(sell_candidates, key=lambda t: -conviction_by_ticker[t]["market_value_usd"]):
        cands = [t for t in buy_candidates if t not in used_buys and t != sell_t]
        if not cands:
            continue
        buy_t = max(cands, key=lambda t: conviction_by_ticker[t]["conviction_score"])
        used_buys.add(buy_t)
        pair_id = f"profit_rotation-{sell_t}-{buy_t}"
        sell_mv = conviction_by_ticker[sell_t]["market_value_usd"]
        sold = _size_sell("profit_rotation", sell_t, sell_mv, sizing)
        sell_size = sold["fields"]["suggested_size_usd"] or 0.0
        legacy_sell = sold["fields"]["legacy_size_usd"]
        buy_conv = conviction_by_ticker[buy_t]
        atr_pct = buy_conv["atr_pct"]
        pmax = (smith_conviction.policy_max_position_usd(atr_pct, buy_conv["price"], total_book, policy)
                if atr_pct and buy_conv["price"] else None)
        target, wanted = ((None, None) if not pmax else
                          smith_conviction.conviction_size(buy_conv["conviction_tier_pct"], pmax["max_position_usd"]))
        # buy leg is funded from the sell leg, never sized past the smaller of the two --
        # sizing past the sell proceeds or the buy's own headroom creates a fresh breach.
        # cluster_room added 2026-09-08 -- profit_rotation pairs are frequently CROSS-cluster
        # (sell the stretched name wherever it sits, buy the best laggard anywhere), which is
        # precisely the case where a buy can push its cluster through the ceiling. Same-cluster
        # pairs get the sale's proceeds credited back; see _pair_cluster_room_usd.
        cluster_room = _pair_cluster_room_usd(cluster_rows, conviction_by_ticker[sell_t]["cluster"],
                                              buy_conv["cluster"], sell_size)
        buy_stop = (sizing["stop_pct_by_ticker"] or {}).get(buy_t)
        # the buy's OWN ticket: the risk its conviction-sized tranche (`wanted`) would take. No
        # conviction sizing -> no ticket -> zero buy, exactly as `min(wanted or 0, ...)` behaved.
        buy_r_ticket = (wanted * buy_stop / 100.0) if (wanted is not None and buy_stop) else 0.0
        buy_size, clamped_by, legs = _rotation_buy_leg(sell_size, sell_t, buy_t, buy_conv, buy_r_ticket,
                                                       cluster_room, sizing)
        legacy_buy, _ = smith_conviction.clamp_size(
            min(wanted or 0, legacy_sell), buy_conv["headroom_usd"],
            _pair_cluster_room_usd(cluster_rows, conviction_by_ticker[sell_t]["cluster"],
                                   buy_conv["cluster"], legacy_sell), None)
        row = {
            "pair_id": pair_id, "trigger_type": "profit_rotation", "vote": "live",
            "sell_leg": {"ticker": sell_t, "direction": "SELL", **sold["fields"],
                        "market_value_usd": round(sell_mv, 2),
                        "reasons": [f"stretched (in names_stretched) with a watch thesis -- real profit to book"]},
            "buy_leg": {"ticker": buy_t, "direction": "BUY", "suggested_size_usd": buy_size, "clamped_by": clamped_by,
                       "legacy_size_usd": legacy_buy,
                       "conviction_score": buy_conv["conviction_score"],
                       "reasons": [f"laggard ({buy_conv['rel_pp']:+.1f}pp) with a {smith_risk.thesis_status(thesis.get(buy_t))} thesis -- yet to rally"]},
            "rotation_risk": legs,
            "retires_when": f"EITHER {sell_t} drops out of the stretched cohort OR {buy_t}'s thesis leaves intact/strengthening"}
        profit_rotation.append(_apply_pair_notes(_pair_verdict(row, sold, buy_size, buy_t, sizing), sold))


def _cluster_rotation_legs_from_ladder(entry, tickers_here, conviction_by_ticker, thesis, authority):
    """Pick the sell and buy legs from the AGENT'S ranking rather than from a price delta.

    Returns (sell_t, buy_t, sell_reason, buy_reason) or None when the ladder cannot name a
    usable pair -- in which case the caller falls back to the price rule, which is a genuine
    fallback and not a degraded version of this one.

    Only HELD, non-over-cap members are eligible on either leg; a ladder ranks the bench too,
    and buying a bench name is a different trigger (it introduces a name the book has never
    owned, on agent judgment alone) that must earn its own vote separately.

    The sell leg is taken from the BOTTOM THIRD of the ranking, not simply "last". With ten
    names in AI Semis/Fabs the difference between rank 9 and rank 10 is inside the agent's own
    resolution; insisting on the exact last name would make the pair hostage to a distinction
    the ladder cannot actually make. Among the bottom third, the largest position is sold --
    that is where dead money actually costs something.
    """
    ranking = [r for r in (entry.get("ranking") or []) if r.get("ticker")]
    if len(ranking) < 2:
        return None
    order = {r["ticker"]: r.get("rank") or (i + 1) for i, r in enumerate(ranking)}
    reads = {r["ticker"]: r for r in ranking}
    eligible = [t for t in tickers_here
                if t in order and not conviction_by_ticker[t]["over_cap"]]
    if len(eligible) < 2:
        return None
    by_rank = sorted(eligible, key=lambda t: order[t])
    cutoff = by_rank[max(1, int(len(by_rank) * 2 / 3)):] or by_rank[-1:]

    # THE THESIS GATE, and the one thing `full` authority buys. `watch` keeps cluster_rotation
    # from ever selling a name the desk still believes in -- which also means it can never
    # rotate an INTACT laggard, the most common real case in a book with 16 strengthening,
    # 16 watch and 0 broken. Lifting it lets a ladder sell something no other agent flagged,
    # so it costs `high` confidence.
    ok_to_sell = ((lambda st: st != "strengthening") if authority == "full"
                  else (lambda st: st == "watch"))
    sells = [t for t in cutoff if ok_to_sell(smith_risk.thesis_status(thesis.get(t)))]
    buys = [t for t in by_rank[:max(1, len(by_rank) // 3)]
            if smith_risk.thesis_status(thesis.get(t)) in ("intact", "strengthening")]
    if not sells or not buys:
        return None
    sell_t = max(sells, key=lambda t: conviction_by_ticker[t]["market_value_usd"])
    buy_t = min(buys, key=lambda t: order[t])
    if sell_t == buy_t:
        return None

    def _differentiator(t):
        dr = ((reads.get(t) or {}).get("differentiator_reads") or [{}])[0]
        axis, read = dr.get("axis"), dr.get("read")
        return f"{axis} -- {read}" if axis and read else None

    def _rank_line(t, side):
        return f"cluster ladder ranks {t} #{order[t]} of {len(ranking)} ({side})"

    def _why_buy(t):
        """The buy leg quotes `differentiator_reads` -- the agent's case FOR the rank. On this
        leg that argument and the trade point the same way."""
        d = _differentiator(t)
        base = _rank_line(t, "leader")
        return f"{base}: {d}" if d else base

    def _why_sell(t):
        """The sell leg must quote `case_against` -- the BEAR case the agent is required to
        supply for every rank (G58). Quoting `differentiator_reads` here produced rationales
        that argued against their own trade ("sell AMD because it is gaining share"), because
        that field is the case FOR the rank, not against the name.

        State the rank, then the bear case. Fall back to the differentiator read only when no
        `case_against` was supplied, and label the fallback so a reader can tell which of the
        two they are looking at -- an unlabelled fallback reintroduces the same contradiction
        silently.
        """
        base = _rank_line(t, "laggard")
        against = ((reads.get(t) or {}).get("case_against") or "").strip()
        if against:
            return f"{base}. Case against: {against}"
        d = _differentiator(t)
        if d:
            return (f"{base}. NO case_against SUPPLIED -- what follows is the agent's case FOR "
                    f"its rank, not against the name: {d}")
        return f"{base}. No case_against supplied."

    return sell_t, buy_t, _why_sell(sell_t), _why_buy(buy_t)


def _trigger_cluster_rotation(conviction_by_ticker, thesis, cluster_rotation, cluster_rows=None,
                              cluster_ladders=None, today=None, sizing=None):
    """Section P: cluster_rotation (PAIRED, live). ORGANISING RULE -- within the SAME cluster,
    sell the laggard, buy the performer. This is the opposite price/thesis pairing from
    profit_rotation and is why the two do not contradict -- same price state (laggard), opposite
    thesis, opposite action.

    TWO WAYS TO RANK (2026-09-08). Where a fresh, confident cluster ladder exists, the ordering
    comes from smith-cluster's FUNDAMENTAL ranking. Otherwise it comes from `rel_pp`, exactly as
    before. The fallback is retained deliberately rather than made conditional-on-nothing: a
    cluster the round-robin has not reached, or one whose ladder is failing its own track
    record, must still be able to produce a rotation on the evidence that is actually available.

    Why `rel_pp` was never good enough on its own: it is ALWAYS SMH-relative for the whole book,
    and `data_cache.rel_strength_1m_peer` is null, so power and hyperscaler names were ranked
    against a semiconductor ETF. On the live 2026-09-07 book that put AVGO last in optics on a
    -13.31pp reading while it was in fact +5.19pp ahead of its own cluster -- and an open
    proposal was selling it.

    RISK-SIZED (2026-09-20): sell leg = SEVERITY_R["cluster_rotation"] of risk; buy leg = the risk
    that frees, in the performer (no ticket of its own -- this pair never conviction-sized its
    buy), then headroom / cluster room. See _trigger_profit_rotation for `rotation_risk`.
    """
    sizing = _pair_sizing(sizing, 0.0, {}, conviction_by_ticker)
    by_cluster = {}
    for t, c in conviction_by_ticker.items():
        by_cluster.setdefault(c["cluster"], []).append(t)
    for cluster, tickers_here in by_cluster.items():
        if not cluster or len(tickers_here) < 2:
            continue
        entry = (cluster_ladders or {}).get(cluster)
        authority, eff_conf, auth_reasons = smith_risk.ladder_authority(
            entry, today or desk_today(), ttl_days=LADDER_TTL_DAYS,
            min_scored=LADDER_MIN_SCORED_CALLS) if entry else ("none", None, [])
        picked = (_cluster_rotation_legs_from_ladder(
            entry, tickers_here, conviction_by_ticker, thesis, authority)
            if authority in ("rank", "full") else None)

        if picked:
            sell_t, buy_t, sell_why, buy_why = picked
            ladder_driven = True
        else:
            laggard_weak = [t for t in tickers_here if (conviction_by_ticker[t]["rel_pp"] or 0) < 0
                            and smith_risk.thesis_status(thesis.get(t)) == "watch"
                            and not conviction_by_ticker[t]["over_cap"]]
            performer_strong = [t for t in tickers_here if (conviction_by_ticker[t]["rel_pp"] or 0) > 0
                                and smith_risk.thesis_status(thesis.get(t)) in ("intact", "strengthening")
                                and not conviction_by_ticker[t]["over_cap"]]
            if not laggard_weak or not performer_strong:
                continue
            sell_t = min(laggard_weak, key=lambda t: conviction_by_ticker[t]["rel_pp"] or 0)
            buy_t = max(performer_strong, key=lambda t: conviction_by_ticker[t]["conviction_score"])
            if sell_t == buy_t:
                continue
            ladder_driven = False
            sell_why = (f"laggard within {cluster} ({conviction_by_ticker[sell_t]['rel_pp']:+.1f}pp), "
                        f"watch thesis -- dead money in this cluster")
            buy_why = (f"performer within {cluster} ({conviction_by_ticker[buy_t]['rel_pp']:+.1f}pp), "
                       f"{smith_risk.thesis_status(thesis.get(buy_t))} thesis")
        sell_mv = conviction_by_ticker[sell_t]["market_value_usd"]
        sold = _size_sell("cluster_rotation", sell_t, sell_mv, sizing)
        sell_size = sold["fields"]["suggested_size_usd"] or 0.0
        legacy_sell = sold["fields"]["legacy_size_usd"]
        buy_conv = conviction_by_ticker[buy_t]
        # Always a same-cluster pair, so the sale funds its own room -- this is effectively
        # non-binding by construction and is passed for consistency and for the case where a
        # cluster is so far over its ceiling that even the swap leaves it breached.
        cluster_room = _pair_cluster_room_usd(cluster_rows, cluster, cluster, sell_size)
        buy_size, clamped_by, legs = _rotation_buy_leg(sell_size, sell_t, buy_t, buy_conv, None,
                                                       cluster_room, sizing)
        legacy_buy, _ = smith_conviction.clamp_size(
            legacy_sell, buy_conv["headroom_usd"],
            _pair_cluster_room_usd(cluster_rows, cluster, cluster, legacy_sell), None)
        # The retirement condition must name what the pair was actually BUILT on, or the
        # lifecycle pass revalidates a ladder-driven pair against a price fact nobody used.
        retires = (f"EITHER {cluster}'s ladder no longer ranks {buy_t} above {sell_t} "
                   f"OR that ladder goes stale (>{LADDER_TTL_DAYS}d)" if ladder_driven else
                   f"EITHER {sell_t}'s thesis strengthens OR {buy_t} is no longer the "
                   f"cluster's relative-strength leader")
        row = {
            "pair_id": f"cluster_rotation-{sell_t}-{buy_t}", "trigger_type": "cluster_rotation", "vote": "live",
            "cluster": cluster,
            "ladder_driven": ladder_driven,
            "ladder_as_of": (entry or {}).get("as_of") if ladder_driven else None,
            "ladder_confidence": eff_conf if ladder_driven else None,
            "ladder_authority": authority,
            "ladder_authority_reasons": auth_reasons,
            "sell_leg": {"ticker": sell_t, "direction": "SELL", **sold["fields"],
                        "reasons": [sell_why]},
            "buy_leg": {"ticker": buy_t, "direction": "BUY", "suggested_size_usd": buy_size, "clamped_by": clamped_by,
                       "legacy_size_usd": legacy_buy,
                       "conviction_score": buy_conv["conviction_score"],
                       "reasons": [buy_why]},
            "rotation_risk": legs,
            "retires_when": retires}
        cluster_rotation.append(_apply_pair_notes(_pair_verdict(row, sold, buy_size, buy_t, sizing), sold))



# ---------------------------------------------------------------------------
# BUCKETS (added 2026-09-06) -- the deterministic half of smith-signals
# ---------------------------------------------------------------------------
# WHY THIS EXISTS. smith-signals was the largest agent in the fleet: 144,878 tokens and 22 tool
# calls on the 2026-09-06 deep run, and it runs on EVERY sweep including quick. Most of what it
# returned was not judgment -- STRONG UPTREND is a day-move divided by ATR20, PEER LEADER is a
# cached relative-strength number over a cached dispersion, TARGET GAP is price against a cached
# analyst target. All three inputs already sit in state.data_cache, which the script owns. An
# LLM re-deriving them each run is precisely what COMPUTE-FIRST exists to stop.
#
# THIS SUPERSEDES A DOCUMENTED CARVE-OUT, deliberately. SKILL.md's COMPUTE-FIRST section listed
# smith-signals' `pos` and `relative_strength_1m` as "judgment-layer calculations the script
# deliberately doesn't own". That carve-out was written before agent cost was measured. It is now
# measured -- cost is nearly flat at 75K-145K per agent regardless of what the agent does, so
# arithmetic left in an agent is arithmetic bought at LLM prices, every run, forever.
#
# WHAT IS NOT MOVED, and why. The pos-based buckets (BREAKOUT, BREAKDOWN, OVERSOLD BOUNCE,
# OVERBOUGHT PULLBACK, and the pos legs of STRONG UPTREND/DOWNTREND) need a 52-week high/low
# range that NOTHING currently caches -- smith-signals fetches it per run and it dies with the
# run. They are reported as `deferred_pos_buckets` with the reason, not silently dropped, and
# they light up automatically the moment `data_cache.wk52` exists (see WK52_NOTE). Pretending to
# compute them from data the script does not have is exactly the guardrail this file enforces
# everywhere else.
#
# News, catalysts, the "with catalyst" leg of MOMENTUM+VOLUME, and every judgment about whether
# a flag MEANS anything stay with the agent. This computes the arithmetic and hands it over.

WK52_NOTE = ("data_cache.wk52 does not exist. Add it as {TICKER: {'high': x, 'low': y, "
             "'as_of': d}} with a 7-day TTL and the pos-based buckets compute here "
             "automatically -- no further code change is needed.")


def _strong_move_threshold(atr20_pct):
    """clamp(1.5 x ATR20, 2.0, 12.0) -- the floor stops a very quiet name flagging on noise,
    the ceiling stops a very loud one being effectively unflaggable. Thresholds identical to
    smith-signals.md task 10; this is a move of the same arithmetic, not a redefinition."""
    return clamp(1.5 * atr20_pct, 2.0, 12.0)


def _rel_sigma(rel_pp, atr20_pct):
    """1-month peer-relative move in units of the name's own expected dispersion.
    Denominator max(2.3 x ATR20, 5.0); the 2.3 is derived in smith-signals.md task 10 and is
    reproduced there rather than re-derived here."""
    return rel_pp / max(2.3 * atr20_pct, 5.0)


def cmd_buckets(args):
    rd = args.run_dir
    holdings = load_json(os.path.join(rd, "holdings.json"), default={})
    state = load_json(os.path.join(args.base_dir, "state.json"), default={})
    dc = state.get("data_cache", {}) or {}
    atr = (dc.get("atr20") or {}).get("values_pct", {}) or {}
    rel = (dc.get("rel_strength_1m") or {}).get("values_pp", {}) or {}
    targets = dc.get("analyst_targets", {}) or {}
    wk52 = dc.get("wk52") or {}
    peer_map = state.get("peer_map", {}) or {}
    # rel_strength_1m above is ALWAYS SMH-relative for the whole book. Added 2026-09-07: prefer
    # a peer_map-aware reading, when cached, for any ticker whose true peer isn't SMH -- before
    # this, smith-signals recomputed the same BE/GEV/VRT-vs-XLU, MSFT/NBIS-vs-XLK override from
    # a fresh fetch on EVERY dispatch (quick or deep, no TTL gate at all), because the compute
    # layer had nowhere to cache the answer and hand it back next run. See FRESHNESS's
    # data_cache.rel_strength_1m_peer entry.
    rel_peer_cache = dc.get("rel_strength_1m_peer") or {}
    rel_peer = rel_peer_cache.get("values_pp", {}) or {}
    rel_peer_etf = rel_peer_cache.get("peer_etf", {}) or {}

    rows, unnormalized, sigmas, stale_peer_fallback = {}, [], [], []
    for h in holdings.get("holdings_inr", []):
        t = h.get("ticker")
        price = h.get("live_price_usd")
        day = h.get("day_chg_pct")
        a = atr.get(t)
        buckets, why = [], {}

        # --- volatility-normalized move buckets -------------------------------------
        if isinstance(a, (int, float)) and a > 0:
            thr = _strong_move_threshold(a)
            norm = True
        else:
            # GUARDRAIL (smith-signals.md task 10): never estimate a missing ATR and never skip
            # the name -- fall back to the legacy absolute threshold and TAG it.
            thr, norm = 4.0, False
            unnormalized.append(t)
        if isinstance(day, (int, float)):
            mult = round(day / a, 2) if norm else None
            why["day_atr_mult"] = mult
            why["threshold_pct"] = round(thr, 2)
            if day >= thr:
                buckets.append("STRONG UPTREND")
            elif day <= -thr:
                buckets.append("STRONG DOWNTREND")
            if abs(day) >= thr:
                # the volume/catalyst leg is the AGENT's call; this is the magnitude leg only
                buckets.append("MOMENTUM+VOLUME?")

        # --- peer-relative ----------------------------------------------------------
        # Prefer the cached peer_map-aware reading over the SMH-default one whenever this
        # ticker's true peer isn't SMH and a fresh cache entry exists for it -- see the
        # rel_peer_cache setup above. benchmark_used records which one actually applied, so a
        # reader (and the agent, when the cache is stale/missing and it falls back to a fresh
        # override) always knows without guessing.
        true_peer = (peer_map.get(t) or {}).get("peer_etf")
        r, benchmark_used = rel.get(t), "SMH"
        if true_peer and true_peer != "SMH" and t in rel_peer:
            r, benchmark_used = rel_peer.get(t), rel_peer_etf.get(t, true_peer)
        elif true_peer and true_peer != "SMH":
            stale_peer_fallback.append(t)
        if isinstance(r, (int, float)) and isinstance(a, (int, float)) and a > 0:
            sig = round(_rel_sigma(r, a), 2)
            why["rel_sigma"] = sig
            why["rel_strength_1m_pp"] = r
            why["peer_benchmark_used"] = benchmark_used
            sigmas.append(sig)
            if sig >= 1.0:
                buckets.append("PEER LEADER")
            elif sig <= -1.0:
                buckets.append("PEER LAGGARD")
            elif r <= -25:
                # KNOWN BLIND SPOT: genuinely deteriorating AND highly volatile -> wide
                # denominator swallows real underperformance. Context line, never a flag.
                why["blind_spot_note"] = (
                    f"{t} {r:+.1f}pp vs benchmark but only {sig:+.2f} sigma on a {a:.1f}% ATR "
                    f"-- inside its own noise, not flagged; thesis/derisk own this one")

        # --- target gap -------------------------------------------------------------
        tg = (targets.get(t) or {}).get("mean_target_usd")
        if isinstance(tg, (int, float)) and isinstance(price, (int, float)) and price > 0:
            up = round((tg - price) / price * 100, 1)
            why["upside_pct"] = up
            why["analyst_target"] = tg
            if abs(up) >= 15:
                buckets.append("TARGET GAP")

        # --- pos-based, only if a 52-week range is actually available ----------------
        w = wk52.get(t) or {}
        hi, lo = w.get("high"), w.get("low")
        if all(isinstance(x, (int, float)) for x in (hi, lo, price)) and hi > lo:
            pos = round((price - lo) / (hi - lo), 3)
            why["pos"] = pos
            if pos >= 0.95:
                buckets.append("BREAKOUT")
            if pos <= 0.06:
                buckets.append("BREAKDOWN")
            if pos >= 0.80 and "STRONG UPTREND" not in buckets:
                buckets.append("STRONG UPTREND")
            if pos <= 0.22 and "STRONG DOWNTREND" not in buckets:
                buckets.append("STRONG DOWNTREND")
            if pos <= 0.30:
                buckets.append("OVERSOLD BOUNCE?")
            if pos >= 0.85:
                buckets.append("OVERBOUGHT PULLBACK?")

        if buckets or why:
            rows[t] = {"buckets": sorted(set(buckets)), "normalized": norm, **why}

    sd = None
    if len(sigmas) > 1:
        m = sum(sigmas) / len(sigmas)
        sd = round((sum((x - m) ** 2 for x in sigmas) / (len(sigmas) - 1)) ** 0.5, 3)

    dq = []
    if unnormalized:
        dq.append(f"atr20 missing/zero for {len(unnormalized)} ticker(s): "
                  f"{','.join(sorted(unnormalized))} -- fell back to the legacy absolute "
                  f"4% threshold and tagged them normalized:false, per the task-10 guardrail.")
    if not wk52:
        dq.append("pos-based buckets NOT computed: " + WK52_NOTE)
    if sd is not None and not (0.8 <= sd <= 1.3):
        dq.append(f"SELF-CALIBRATION: SD(rel_sigma)={sd} is outside the 0.8-1.3 band a correctly "
                  f"scaled measure should show. {'Denominator too wide, bucket under-firing' if sd < 0.8 else 'Denominator too narrow, bucket over-firing'}. "
                  f"REPORT this, never silently retune the constant -- that is the user's call.")
    if stale_peer_fallback:
        dq.append(f"{len(stale_peer_fallback)} ticker(s) have a non-SMH true peer in peer_map "
                  f"but no fresh data_cache.rel_strength_1m_peer entry, so PEER LEADER/LAGGARD "
                  f"fell back to the SMH-default reading this run: {','.join(sorted(stale_peer_fallback))}. "
                  f"smith-signals should refresh these (task 9, cache-check-first) on its next dispatch.")

    out = {"as_of": args.today, "tickers": rows,
           "suffixed_buckets_need_agent_confirmation": [
               "MOMENTUM+VOLUME? -- magnitude leg only; the agent confirms volume/catalyst",
               "OVERSOLD BOUNCE? -- pos leg only; the agent confirms positive news/upgrade",
               "OVERBOUGHT PULLBACK? -- pos leg only; the agent confirms negatives/above-target"],
           "deferred_pos_buckets": (not wk52),
           "rel_sigma_sd": sd, "unnormalized_tickers": sorted(unnormalized),
           "stale_peer_fallback_tickers": sorted(stale_peer_fallback),
           "peer_benchmark_caveat": (
               "PEER LEADER/LAGGARD prefers a cached peer_map-aware reading (data_cache."
               "rel_strength_1m_peer, added 2026-09-07) for any ticker whose true peer isn't "
               "SMH -- check each row's `peer_benchmark_used` field to see which one applied. "
               "Falls back to the SMH-default reading (data_cache.rel_strength_1m) only when "
               "that cache is missing or stale for a ticker, named in `stale_peer_fallback_"
               "tickers` -- those are the only names still needing an agent override this run."),
           "data_quality": dq,
           "note": ("Deterministic bucket arithmetic, moved out of smith-signals 2026-09-06. "
                    "A '?' suffix means the script computed the measurable leg and the agent "
                    "owns the remaining judgment leg -- it is NOT a fired bucket. News, "
                    "catalysts, and whether any flag MEANS anything remain the agent's.")}
    # emit only -- cmd_pipeline captures stdout and writes compute_buckets.json itself,
    # same contract as every other stage. Writing the file here too would produce two
    # writers for one artefact, which is how they drift.
    emit(out)

def _bucket_expectancy_r(hr):
    """Per-trade expectancy in R for one bucket hit-rate row: p * payoff - (1 - p).

    payoff_ratio is None when the bucket has never lost; it then defaults to 1.0 (an honest
    "unknown, assume symmetric") rather than infinity, so an unbeaten small-n bucket is not
    ranked above a proven one."""
    p = float(hr.get("hit_rate_pct") or 0.0) / 100.0
    payoff = hr.get("payoff_ratio")
    payoff = 1.0 if payoff is None else float(payoff)
    return p * payoff - (1.0 - p)


def worst_bullish_track_record(bullish, hit_rates_30d, hit_rates_7d):
    """The LOWEST-expectancy bullish bucket with data, as a track_record dict (or None).

    Prefers the validated 30d table; falls back to the interim 7d table only when no bullish
    bucket has a 30d reading (same preference the reader always had). Ties resolve to the
    smaller n, then the name, so the pick is deterministic."""
    for table, interim in ((hit_rates_30d, False), (hit_rates_7d, True)):
        cands = [(b, table[b]) for b in bullish if table.get(b) and table[b].get("n")]
        if cands:
            b, hr = min(cands, key=lambda c: (_bucket_expectancy_r(c[1]), c[1]["n"], c[0]))
            return {"hit_rate_pct": hr["hit_rate_pct"], "n": hr["n"], "interim": interim,
                    "payoff_ratio": hr.get("payoff_ratio")}   # None if never lost -- fine
    return None


# ---------------------------------------------------------------------------
# PORTFOLIO HEAT BUDGET POST-PASS (Phase 3, 2026-09-20)
# ---------------------------------------------------------------------------
# WHY A POST-PASS. A budget is shared by every ticket of the run, so it cannot be spent inside the
# per-ticker trigger loop, which sees one name at a time. cmd_triggers sizes every candidate as
# before; this pass then sees them ALL at once, in smith_ticket.allocate_heat, and writes the
# result back onto the rows. The motivating incident: policy records the 10% aggregate-open-risk
# cap breached at 13.028% and 11.947% while sizing carried on at the full per-position formula.
_HEAT_SINGLE_FAMILIES = ("oversold_reversion", "trend_entry", "conviction_average", "entry_setup",
                         "reentry", "bench_diversifier")
_HEAT_PAIR_FAMILIES = ("profit_rotation", "cluster_rotation")
_HEAT_SELL_FAMILIES = ("overbought_distribution", "catalyst_threat", "thesis_break",
                       "trend_breakdown", "conviction_exit")
_HEAT_FIELDS = ("risk_usd", "book_heat_before_usd", "book_heat_after_usd", "heat_room_remaining_usd")


def _floor_usd_for(ticker, sizing):
    """The materiality floor (dollars) a BUY of `ticker` must clear -- it does not depend on size."""
    m = _buy_leg_verdict(1.0, ticker, sizing)
    return m["floor_usd"] if m else 0.0


def _stamp_heat_fields(target, d):
    for k in _HEAT_FIELDS:
        target[k] = d.get(k)


def _apply_heat_budget(fams, pair_fams, sell_fams, risk, drift, policy, corr, today, sizing,
                       sector_map, dq, atr_vals=None, learning_store=None):
    """Run smith_ticket.allocate_heat over every live buy candidate and write the outcome back.

    `fams` / `pair_fams` / `sell_fams` map trigger name -> row list (mutated in place). Returns the
    `heat_budget` block published in compute_triggers.json (`{"enabled": False, ...}` when policy
    carries no aggregate cap, in which case no row is touched). Every buy row and every rotation
    buy leg gains risk_usd / book_heat_before_usd / book_heat_after_usd / heat_room_remaining_usd;
    a shrunk row names its clamp in clamped_by; a ticket that does not fit is emitted with vote
    "deferred", deferred_by and would_be_size_usd -- never dropped.
    """
    cap_pct = risk.get("aggregate_open_risk_cap_pct")
    if cap_pct is None:
        dq.append("heat budget DISABLED: policy carries no aggregate_open_risk_cap_pct_of_book")
        return {"enabled": False, "reason": "no aggregate_open_risk_cap_pct_of_book in policy"}
    hp = smith_ticket.heat_policy(policy.get("heat_budget"))
    total_book = risk.get("total_book_usd") or sizing["total_book_usd"]
    corr_read = smith_ticket.correlation_read(corr, today)
    budget = smith_ticket.heat_budget(risk.get("aggregate_open_risk_usd"), total_book, cap_pct,
                                      corr_read, hp["heat_floor"])
    if not hp["confirmed"]:
        dq.append("policy.heat_budget is UNCONFIRMED (confirmed:false) -- the engine uses a %.0f%% floor "
                  "on the aggregate-risk cap at full correlation and the cluster sub-budget %s, but the "
                  "user has not signed them; treat every deferred/heat_room verdict as provisional."
                  % (hp["heat_floor"] * 100, "ON" if hp["cluster_sub_budget"] else "OFF"))
    if not corr_read["measured"]:
        dq.append(f"heat budget uses the CONSERVATIVE bound: {corr_read['reason']} -- correlation is "
                  f"treated as 1.0 (budget = cap x {hp['heat_floor']:g}); no diversification credit "
                  "is assumed that was not measured.")

    st = sizing["stop_pct_by_ticker"] or {}
    positions = risk.get("positions") or []
    mv_by = {p["ticker"]: (p.get("market_value_usd") or 0.0) for p in positions}
    e_usd = (drift or {}).get("invested_equity_usd")
    ai_clusters = set(policy.get("ai_capex_clusters") or [])
    cl_rows = {c.get("cluster"): c for c in ((drift or {}).get("cluster_table") or [])}

    def cluster_of(row, ticker):
        return row.get("cluster") or sector_map.get(ticker)

    # ---- candidates ----------------------------------------------------------------------------
    cands, index = [], {}
    for fam in _HEAT_SINGLE_FAMILIES:
        for row in fams.get(fam, []):
            t, stop, size = row.get("ticker"), st.get(row.get("ticker")), row.get("suggested_size_usd")
            if row.get("vote") != "live" or not size or size <= 0 or not stop:
                continue
            cid = f"{fam}:{t}"
            cl = cluster_of(row, t)
            cands.append({"id": cid, "kind": "single", "ticker": t, "score": row.get("conviction_score"),
                          "size_usd": size, "stop_pct": stop, "floor_usd": _floor_usd_for(t, sizing),
                          "cluster": cl, "is_ai": cl in ai_clusters})
            index[cid] = ("single", row)
    for fam in _HEAT_PAIR_FAMILIES:
        for row in pair_fams.get(fam, []):
            b, sl = row["buy_leg"], row["sell_leg"]
            stop, size = st.get(b["ticker"]), b.get("suggested_size_usd")
            if row.get("vote") != "live" or not size or size <= 0 or not stop:
                continue
            bcl = cluster_of(b, b["ticker"])
            scl = cluster_of(sl, sl["ticker"])
            cid = row["pair_id"]
            cands.append({"id": cid, "kind": "pair", "ticker": b["ticker"], "score": b.get("conviction_score"),
                          "size_usd": size, "stop_pct": stop, "floor_usd": _floor_usd_for(b["ticker"], sizing),
                          "cluster": bcl, "is_ai": bcl in ai_clusters,
                          "freed_risk_usd": sl.get("risk_removed_usd") or 0.0,
                          "sell_size_usd": sl.get("suggested_size_usd") or 0.0,
                          "sell_cluster": scl, "sell_is_ai": scl in ai_clusters})
            index[cid] = ("pair", row)

    # ---- credit: standalone sells -- OFF by default, a proposed sell has not freed anything -------
    # Per ticker, never more than the risk the position actually carries: two sell rows on one name
    # (a catalyst trim AND a rotation's sell leg) cannot free more than R_open between them.
    ropen_by = {p["ticker"]: (p.get("position_open_risk_usd") or 0.0) for p in positions}
    pair_freed_by = {}
    for fam in _HEAT_PAIR_FAMILIES:
        for row in pair_fams.get(fam, []):
            if row.get("vote") == "live":
                t = row["sell_leg"]["ticker"]
                pair_freed_by[t] = pair_freed_by.get(t, 0.0) + (row["sell_leg"].get("risk_removed_usd") or 0.0)
    sold_by, credit_rows = {}, []
    for fam in _HEAT_SELL_FAMILIES:
        for row in sell_fams.get(fam, []):
            if row.get("vote") == "live" and row.get("sell_action") in ("trim", "full_exit") \
                    and (row.get("risk_removed_usd") or 0) > 0:
                sold_by[row["ticker"]] = sold_by.get(row["ticker"], 0.0) + row["risk_removed_usd"]
                credit_rows.append(f"{fam}:{row.get('ticker')}")
    credit = sum(min(v, max(0.0, ropen_by.get(t, 0.0) - pair_freed_by.get(t, 0.0)))
                 for t, v in sold_by.items())
    if not STANDALONE_SELL_CREDIT_ENABLED:
        # see smith_core.STANDALONE_SELL_CREDIT_ENABLED: a proposed sell has not freed anything yet
        credit, credit_rows = 0.0, []

    # ---- static rooms: single position, AI capex, cluster risk -----------------------------------
    rooms = {"single_position_usd": {}, "ai_capex_usd": None, "cluster_risk_usd": {}}
    max_single = policy.get("max_single_position_pct")
    if max_single is not None and e_usd:
        for c in cands:
            rooms["single_position_usd"][c["ticker"]] = smith_ticket.cash_funded_room(
                max_single / 100.0, mv_by.get(c["ticker"], 0.0), e_usd, True)
    ai_cap = policy.get("max_ai_capex_factor_pct")
    ai_denom = policy.get("ai_capex_denominator", "invested_equity")
    ai_num = ai_den = None
    if ai_cap is not None and drift:
        if ai_denom == "total_book" and drift.get("ai_capex_pct_of_total_book") is not None:
            ai_num, ai_den = drift["ai_capex_pct_of_total_book"] / 100.0 * total_book, total_book
        elif e_usd and drift.get("ai_capex_pct_of_equity") is not None:
            ai_num, ai_den = drift["ai_capex_pct_of_equity"] / 100.0 * e_usd, e_usd
        if ai_den:
            rooms["ai_capex_usd"] = smith_ticket.cash_funded_room(ai_cap / 100.0, ai_num, ai_den,
                                                                  ai_denom != "total_book")
    cluster_max, cluster_open = {}, {}
    if hp["cluster_sub_budget"]:
        for p in positions:
            cluster_open[p.get("cluster")] = cluster_open.get(p.get("cluster"), 0.0) + (p.get("position_open_risk_usd") or 0.0)
        # sorted: a set's iteration order varies with hash randomisation and would make the published
        # block (and every golden master) differ byte-for-byte between identical runs
        for cl in sorted({c["cluster"] for c in cands if c["cluster"]}
                         | {c.get("sell_cluster") for c in cands if c.get("sell_cluster")}):
            row = cl_rows.get(cl) or {}
            band = row.get("band_pct")
            mx = smith_ticket.cluster_risk_max_usd(budget["h_eff_max_usd"], band[1] if band else None,
                                                   row.get("ceiling_tested_on"), total_book, e_usd)
            if mx is not None:
                cluster_max[cl] = mx
                rooms["cluster_risk_usd"][cl] = max(0.0, mx - cluster_open.get(cl, 0.0))

    res = smith_ticket.allocate_heat(cands, budget, rooms, credit)
    dec = res["decisions"]

    # ---- write back ----------------------------------------------------------------------------
    for cid, (kind, row) in index.items():
        d = dec[cid]
        tgt = row if kind == "single" else row["buy_leg"]
        ticker = tgt["ticker"]
        _stamp_heat_fields(tgt, d)
        tgt["heat_status"] = d["status"]
        if d["status"] == "deferred":
            row["vote"] = "deferred"
            row["deferred_by"] = HEAT_DEFER_LABEL
            row["deferred_reason"] = d["deferred_reason"]
            row["would_be_size_usd"] = d["would_be_size_usd"]
            row["size_pre_heat_usd"] = d["size_pre_heat_usd"]
            row.setdefault("blockers", []).append(
                f"DEFERRED by the {HEAT_DEFER_LABEL}: {d['deferred_reason']}. Would-be size "
                f"${d['would_be_size_usd']:,.2f} (risk ${d['risk_usd']:,.2f}); emitted, not proposed, "
                "so the desk sees the queue.")
            continue
        new = d["size_usd"]
        old = tgt.get("suggested_size_usd") or 0.0
        if new is not None and new < old - 0.005:
            tgt["size_pre_heat_usd"] = round(old, 2)
            tgt["suggested_size_usd"] = new
            if d["clamped_by"]:
                tgt["clamped_by"] = d["clamped_by"]
            row.setdefault("blockers", []).append(
                f"shrunk by {d['clamped_by']}: ${old:,.2f} -> ${new:,.2f}")
        if kind == "pair":
            rr = row.get("rotation_risk") or {}
            stop = st.get(ticker) or 0.0
            rr["buy_size_final_usd"] = new
            rr["buy_risk_final_usd"] = round((new or 0.0) * stop / 100.0, 2)
            rr["heat_delta_final_usd"] = round(rr["buy_risk_final_usd"] - (rr.get("r_freed_usd") or 0.0), 2)
            if d["status"] == "below_materiality":
                bm = _buy_leg_verdict(new, ticker, sizing)
                row["buy_leg"]["materiality"] = _compact_materiality(bm)
                row["materiality_shortfall_usd"] = (bm or {}).get("shortfall_usd")
                row["materiality_legs_below"] = sorted(set((row.get("materiality_legs_below") or []) + ["buy"]))
                row["vote"] = "below_materiality"
                row.setdefault("blockers", []).append(
                    f"below materiality after {d['clamped_by']}: the buy leg shrank to ${new:,.2f} -- the pair "
                    "neither consumes nor frees heat")
            else:
                row["buy_leg"]["materiality"] = _compact_materiality(_buy_leg_verdict(new, ticker, sizing))

    # ---- rows that were not allocated still carry their risk ------------------------------------
    for fam in list(_HEAT_SINGLE_FAMILIES):
        for row in fams.get(fam, []):
            if "risk_usd" not in row:
                sz, stp = row.get("suggested_size_usd"), st.get(row.get("ticker"))
                row["risk_usd"] = round(sz * stp / 100.0, 2) if (sz and stp) else None
                row["heat_status"] = f"not_allocated ({row.get('vote')})"
    for fam in _HEAT_PAIR_FAMILIES:
        for row in pair_fams.get(fam, []):
            b = row["buy_leg"]
            if "risk_usd" not in b:
                sz, stp = b.get("suggested_size_usd"), st.get(b["ticker"])
                b["risk_usd"] = round(sz * stp / 100.0, 2) if (sz and stp) else None
                b["heat_status"] = f"not_allocated ({row.get('vote')})"

    # ---- learned_stop: make the advisory block reachable and surfaced on BUY rows -----------------
    lm_any = False
    for fam in _HEAT_SINGLE_FAMILIES:
        for row in fams.get(fam, []):
            atr = (atr_vals or {}).get(row.get("ticker"))
            lm = smith_risk.learned_stop_multiple_for(atr, learning_store)
            px = row.get("price_usd")
            if lm and px:
                ls = smith_conviction.policy_max_position_usd(atr, px, total_book, policy,
                                                               learned_multiple=lm).get("learned_stop")
                if ls:
                    row["learned_stop"] = ls
                    lm_any = True

    defers = [{"id": k, "would_be_size_usd": v["would_be_size_usd"], "risk_usd": v["risk_usd"],
               "reason": v["deferred_reason"]} for k, v in dec.items() if v["status"] == "deferred"]
    alloc = [{"id": k, "size_usd": v["size_usd"], "risk_usd": v["risk_usd"], "net_risk_usd": v["net_risk_usd"],
              "clamped_by": v["clamped_by"]} for k, v in dec.items() if v["status"] in ("fit", "clamped")]
    if defers:
        dq.append("DEFERRED by the portfolio heat budget (emitted, not proposed): " + "; ".join(
            f"{x['id']} would-be ${x['would_be_size_usd']:,.2f} (risk ${x['risk_usd']:,.2f})" for x in defers))
    return {"enabled": True, **budget,
            "confirmed": hp["confirmed"], "cluster_sub_budget": hp["cluster_sub_budget"],
            "correlation": {k: corr_read[k] for k in ("rho", "measured", "as_of", "window_to", "age_days", "reason")},
            "sell_credit_usd": res["credit_usd"], "sell_credit_from": credit_rows if not budget["over_cap"] else [],
            "r_available_usd": round(budget["r_free_usd"] + res["credit_usd"], 2),
            "r_remaining_after_allocation_usd": res["remaining_usd"],
            "book_heat_after_allocation_usd": res["h_after_usd"],
            "ordering_key": "smith_ticket.allocation_priority (conviction_score desc; Phase 4 swaps in EV per marginal risk)",
            "allocated": alloc, "deferred": defers,
            "rooms": {"single_position_pct": max_single, "ai_capex_cap_pct": ai_cap, "ai_capex_denominator": ai_denom,
                      "ai_capex_room_usd": (None if rooms["ai_capex_usd"] is None else round(rooms["ai_capex_usd"], 2)),
                      "cluster_risk_max_usd": cluster_max,
                      "cluster_risk_open_usd": {k: round(v, 2) for k, v in cluster_open.items()}},
            "learned_stop_surfaced": lm_any}


def cmd_triggers(args):
    """Deterministic candidate generation for the seven non-ATR proposal triggers.

    This does NOT create proposals -- it hands the strategist typed, pre-screened candidate lists
    so it no longer has to invent non-ATR ideas from narrative judgment. Same compute-first
    contract as every other subcommand: every gate is a number from a compute file or a cache,
    never a prose reading.

    Inputs split two ways, and the distinction is deliberate:

      REQUIRED -- compute_risk.json and compute_book.json are loaded with no default, so their
                  absence stops the stage rather than yielding a confidently empty answer. There
                  is no held-position universe and no price without them, so every trigger here
                  would return "no candidates" for a book that in fact has plenty. In a pipeline
                  run cmd_pipeline's STAGES registry asserts both first and BLOCKS by name.
      OPTIONAL -- drift, rotation, state, lots, policy and the state caches (rsi14, rel_strength,
                  atr20) all default to empty and degrade to an empty candidate list plus a
                  data_quality line rather than an estimate. See rsi_usable / rel_usable below,
                  and the cluster-tension note, for what that degradation looks like per gate.

    vote=="live"   (oversold_reversion, overbought_distribution, catalyst_threat, thesis_break)
                   may become sized proposals now.
    vote=="shadow" (laggard_rotation, profit_ratchet, scale_out_ladder) are logged with
                   price_at_flag and scored at 7/30d first -- the same "a new signal class earns
                   its vote before it gets one" rule the de-risk queue (2.9c) runs under. The
                   RSI-based live triggers are exempted because OVERSOLD BOUNCE already carries a
                   measured record in this book's own journal; catalyst_threat and thesis_break
                   (added 2026-08-17) are exempted for a different reason -- they consume findings
                   that are already evidence-graded and sourced by smith-catalyst/smith-thesis
                   before they ever reach here, not a newly invented statistical heuristic with no
                   track record. See the "why live from day one" comment in smith_core.py.
    """
    risk = load_json(os.path.join(args.run_dir, "compute_risk.json"))
    book = load_json(os.path.join(args.run_dir, "compute_book.json"))
    drift = load_json(os.path.join(args.run_dir, "compute_drift.json"), default={})
    rotation = load_json(os.path.join(args.run_dir, "compute_rotation.json"), default={})
    # STAGED state (2026-09-19): identical to state.json during the normal pipeline -- nothing is
    # staged yet when triggers first runs -- but after a desk-round REVISION (smith_comms) the
    # re-run must see the analysts' corrected verdicts and narrowed catalyst mappings, or it
    # keeps firing the very threats they just withdrew.
    from smith_state import load_state as _load_staged
    state = _load_staged(args.base_dir, args.run_dir) or {}
    lots = load_json(os.path.join(args.base_dir, "lots.json"), default={})
    policy = load_json(os.path.join(args.base_dir, "policy.json"), default={})
    # Cluster state, for the overbought cluster-tension check further down. Both default to empty so
    # a missing/failed drift step degrades to "no tension detected" rather than raising -- consistent
    # with how rsi_usable / rel_usable degrade elsewhere in this function.
    cluster_rows = {c.get("cluster"): c for c in (drift.get("cluster_table") or [])}
    sector_map = state.get("sector_map", {}) or {}

    today = resolve_today(args.today)
    dc = state.get("data_cache", {}) or {}
    thesis = state.get("thesis", {}) or {}
    rotation_by_ticker = rotation.get("tickers", {}) or {}
    risk_by_ticker = {r["ticker"]: r for r in risk.get("positions", [])}
    price_by_ticker = {p["ticker"]: p.get("price_usd") for p in book.get("positions", [])}
    dq = []

    # --- technical caches, with an explicit staleness gate ----------------------
    rsi_cache = dc.get("rsi14", {}) or {}
    rsi_vals = rsi_cache.get("values", {}) or {}
    rsi_as_of = _parse_as_of(rsi_cache.get("as_of"))
    rsi_age = (today - rsi_as_of).days if rsi_as_of else None
    rsi_usable = bool(rsi_vals) and rsi_age is not None and rsi_age <= TRIGGER_CACHE_MAX_AGE_DAYS
    held_tickers = [r["ticker"] for r in risk.get("positions", [])]
    rsi_missing = sorted(t for t in held_tickers if t not in rsi_vals)
    rsi_coverage_pct = round(100.0 * (len(held_tickers) - len(rsi_missing)) / len(held_tickers), 1) \
        if held_tickers else None
    if rsi_usable and rsi_coverage_pct is not None and rsi_coverage_pct < TRIGGER_CACHE_MIN_COVERAGE_PCT:
        dq.append(f"rsi14 is fresh but covers only {rsi_coverage_pct}% of held names "
                  f"({len(rsi_missing)} missing: {', '.join(rsi_missing[:8])}) -- RSI triggers "
                  f"cannot fire on a name the cache cannot see, so partial coverage shrinks the "
                  f"candidate set exactly like staleness does. Refresh the missing names.")
    if not rsi_vals:
        dq.append("rsi14 cache absent -- oversold_reversion and overbought_distribution cannot be "
                  "computed this run (never estimated); seed it from the same daily bars ATR20 uses")
    elif not rsi_usable:
        dq.append(f"rsi14 cache is {rsi_age}d old (max {TRIGGER_CACHE_MAX_AGE_DAYS}d for a live "
                  f"trigger) -- RSI-based triggers suppressed this run rather than fired on stale data")

    rel_cache = dc.get("rel_strength_1m", {}) or {}
    rel_vals = rel_cache.get("values_pp", {}) or {}
    abs_vals = rel_cache.get("values_abs_pct", {}) or {}
    rel_as_of = _parse_as_of(rel_cache.get("as_of"))
    rel_age = (today - rel_as_of).days if rel_as_of else None
    rel_usable = bool(rel_vals) and rel_age is not None and rel_age <= TRIGGER_CACHE_MAX_AGE_DAYS
    rel_missing = sorted(t for t in held_tickers if t not in rel_vals)
    rel_coverage_pct = round(100.0 * (len(held_tickers) - len(rel_missing)) / len(held_tickers), 1) \
        if held_tickers else None
    if rel_usable and rel_coverage_pct is not None and rel_coverage_pct < TRIGGER_CACHE_MIN_COVERAGE_PCT:
        dq.append(f"rel_strength_1m is fresh but covers only {rel_coverage_pct}% of held names "
                  f"({len(rel_missing)} missing: {', '.join(rel_missing[:8])}) -- these names are "
                  f"invisible to laggard_rotation and to overbought's 'genuinely up' gate.")
    if not rel_usable:
        dq.append(f"rel_strength_1m unusable (age={rel_age}d, n={len(rel_vals)}) -- laggard_rotation "
                  "suppressed and overbought_distribution's 'genuinely up' gate degrades to price-only")

    # --- deployable cash: only the excess over the normal band's top ------------
    # Sizing a buy off total cash would recommend spending the liquidity floor itself. The
    # deployable figure is the overshoot, which is what the drift table already flags as the
    # live problem when cash_breach_vs_normal fires on the high side.
    total_book = book.get("total_book_usd") or 0.0
    cash_usd = book.get("wallet_usd") or 0.0
    # BUG FIXED 2026-08-24: this used to prefer cash_band_normal_pct, which cmd_drift always
    # sets to the static [5,15] band regardless of regime -- cash_band_pct is the one cmd_drift
    # actually regime-adjusts (post_stop_event -> [5,40] per policy.json, confirmed live: cash
    # sat at 30.37% today, a stop-cascade day, and this `or` order meant deployable read $0
    # against a genuinely available $6,292 of post-stop-event headroom). cash_band_pct first.
    band = drift.get("cash_band_pct") or drift.get("cash_band_normal_pct") or [None, None]
    if band[1] is not None and total_book:
        deployable = max(0.0, cash_usd - (band[1] / 100.0 * total_book))
    else:
        deployable = 0.0
    max_single = deployable * MAX_SINGLE_DEPLOY_FRACTION if deployable else 0.0

    # Separate, WIDER pool for conviction-driven ideas (added 2026-08-24). `deployable` above is
    # "cash ABOVE THE CEILING" -- built for the old force-deploy-the-overflow mechanism, and it
    # is genuinely $0 whenever cash sits inside its tolerated band (post_stop_event's own
    # `glide` note: "Redeployment is NEVER forced by the calendar"). But a conviction-driven idea
    # is an opportunistic redeployment, not a forced one -- it should be able to draw on any cash
    # down to the FLOOR, same as a human would read "I have $12k, I need to keep 5% liquid,
    # everything else is available if a good idea shows up." Confirmed live: post-cascade cash
    # sat at 30.37% (inside the tolerated [5,40] post_stop_event band), so `deployable` read $0
    # while $10,384 genuinely sat available above the 5% floor -- exactly the gap that sized
    # smith-rebound's real $4,600 of redeploy ideas down to $0 in the old engine.
    floor_pct = band[0] if band[0] is not None else 5.0
    deployable_for_ideas = max(0.0, cash_usd - (floor_pct / 100.0 * total_book)) if total_book else 0.0

    oversold, overbought, laggard, ratchet, ladder, catalyst_threat, thesis_break = [], [], [], [], [], [], []
    trend_entry, trend_breakdown, conviction_average, conviction_exit = [], [], [], []
    entry_setup, reentry, bench_diversifier = [], [], []
    profit_rotation, cluster_rotation = [], []
    cluster_bench_rotation, cluster_consolidation = [], []
    conviction_by_ticker = {}  # populated in the main loop, consumed by the rotation-pairing pass

    rel_ranked = sorted((t for t in risk_by_ticker if rel_vals.get(t) is not None),
                        key=lambda t: rel_vals[t])
    laggard_cut = int(len(rel_ranked) * LAGGARD_PCTILE / 100.0) if rel_ranked else 0
    laggard_set = set(rel_ranked[:max(laggard_cut, 1)]) if rel_ranked else set()

    # catalyst_threat precompute (added 2026-08-17): only a structural, threat-classified catalyst
    # counts -- "noise"/"mechanical" horizon threats are exactly the Friday-drop-with-no-cause class
    # smith-catalyst itself distinguishes, and a "ambiguous" direction is not a threat by definition.
    # Keyed by ticker so the per-ticker loop below can just look itself up, same shape as every
    # other precomputed map here (rel_vals, laggard_set, etc).
    # 2026-09-08: read through `smith_risk.live_catalysts` rather than the raw array, so an
    # entry that has aged out past its own horizon stops driving triggers even though the
    # carry-forward merge keeps it in state until the next scan can retire it explicitly.
    # ONE READER for the freshness rule -- the dashboard goes through the same helper.
    factor_catalysts = smith_risk.live_catalysts(state, today, include_suppressed=True)
    # DEDUP + BREADTH (2026-09-19, see smith_risk): near-duplicate reports of one event count
    # once, and a threat touching most of the book becomes ONE book-level factor_threat row
    # instead of a 20% trim of every name it lists -- on 2026-09-19 a single essay entry
    # listing 26 of 27 holdings produced 26 of the 27 live TRIMs ($6,746).
    _equity = sum(float(r.get("market_value_usd") or 0) for r in risk.get("positions", []))
    _weights = ({r["ticker"]: float(r.get("market_value_usd") or 0) / _equity * 100
                 for r in risk.get("positions", [])} if _equity else {})
    catalyst_threats_by_ticker = {}
    factor_threat = []
    for cat in smith_risk.dedupe_catalysts(factor_catalysts):
        if cat.get("direction") != "threat" or cat.get("horizon") != "structural":
            continue
        if smith_risk.is_broad_catalyst(cat, _weights, held=held_tickers):
            names, pct = smith_risk.catalyst_breadth(cat, _weights, held=held_tickers)
            factor_threat.append({
                "trigger_type": "factor_threat", "direction": "BOOK", "vote": "live",
                "headline": cat.get("headline"), "date": cat.get("date"),
                "magnitude": cat.get("magnitude"), "source": cat.get("source"),
                "held_names": sorted(names), "held_count": len(names), "equity_pct": pct,
                "duplicates_folded": len(cat.get("duplicates") or []),
                "reasons": [f"touches {len(names)} held names ({pct:.0f}% of equity) -- a "
                            f"threat to the whole factor is answered by gross exposure and "
                            f"cash, not by trimming each name the same fraction"],
                "suggested_size_usd": None})
            continue
        # COMPANY-SPECIFIC EVENTS TRIM ONLY THE COMPANY (2026-09-19). When the headline names a
        # held company -- "Corning (GLW) ... ATM program", "GE Vernova (GEV) initiated Sell" --
        # the event is about THAT company. Its peers in `affects` are read-through (same-session
        # sympathy selling), not a structural threat of their own: a Street-low Sell on GEV is not
        # a reason to trim VRT, nor Corning's dilution a reason to trim Lumentum. They ride along
        # on the named company's row as `read_through` instead of becoming live trims.
        named = [t for t in held_tickers
                 if re.search(rf"(?<![A-Za-z]){re.escape(t)}(?![A-Za-z])", str(cat.get("headline") or ""))
                 and t in (cat.get("affects") or [])]
        if named:
            peers = [t for t in (cat.get("affects") or []) if t not in named and t in held_tickers]
            for t in named:
                catalyst_threats_by_ticker.setdefault(t, []).append(dict(cat, read_through=peers))
            continue
        for t in (cat.get("affects") or []):
            catalyst_threats_by_ticker.setdefault(t, []).append(cat)

    # ------------------------------------------------------------------------------------------
    # CONVICTION-TRIGGER PRECOMPUTE (added 2026-08-24) -- everything the nine conviction triggers
    # below need, gathered once, same "typed data, never a re-read of prose" discipline as above.
    # ------------------------------------------------------------------------------------------
    derisk = load_json(os.path.join(args.run_dir, "compute_derisk.json"), default={})
    names_stretched = set(derisk.get("names_stretched") or [])
    signal_history = state.get("signal_history", {}) or {}
    signal_history_as_of = state.get("signal_history_as_of", {}) or {}
    watchlist_setups = state.get("watchlist_setups", []) or []
    diversifier_candidates = state.get("diversifier_candidates", {}) or {}
    earnings_facts = dc.get("earnings_facts", {}) or {}
    atr_vals = (dc.get("atr20", {}) or {}).get("values_pct", {}) or {}

    # RISK-SIZING CONTEXT (Phase 2, 2026-09-20): R_base, the materiality floors, the one dust
    # number and every name's stop distance, gathered once. Held names take the stop cmd_risk
    # already published (smith_risk.stop_and_cap's own figure); everyone else derives it from the
    # ATR cache by the identical rule. A name with neither has NO stop and therefore no risk-sized
    # ticket -- never an estimate.
    _stop_by_ticker = {t: smith_ticket.stop_pct_from_atr(a) for t, a in atr_vals.items() if a}
    for _t, _r in risk_by_ticker.items():
        if _r.get("stop_distance_pct"):
            _stop_by_ticker[_t] = _r["stop_distance_pct"]
    sizing = smith_ticket.sizing_context(total_book, policy, _stop_by_ticker)
    if not sizing["materiality"]["confirmed"]:
        dq.append("policy.trade_materiality is UNCONFIRMED (confirmed:false) -- the engine uses these "
                  "floors (min ticket $%g / %g%% of book / %gR, dust $%g) but the user has not signed "
                  "them; treat every below_materiality verdict as provisional."
                  % (sizing["materiality"]["min_ticket_usd"], sizing["materiality"]["min_ticket_pct_of_book"],
                     sizing["materiality"]["min_ticket_r"], sizing["min_position_usd"]))

    # PRICES FOR NAMES THE BOOK DOES NOT HOLD (Phase 2 prerequisite): live quote first, else the
    # last daily close in bars.json. Both files are written by smith_fetch, which now fetches the
    # watchlist-setup / diversifier / cluster-bench names too. Never derived from target+upside.
    market_prices = {}
    _bars_for_px = load_json(os.path.join(args.run_dir, "bars.json"), default={}) or {}
    for _t, _rows in _bars_for_px.items():
        _closes = [b.get("c") for b in (_rows or []) if isinstance(b, dict) and b.get("c")]
        if _closes:
            market_prices[_t] = {"price": round(float(_closes[-1]), 4), "source": "bars.json last close"}
    for _t, _q in (load_json(os.path.join(args.run_dir, "live_quotes.json"), default={}) or {}).items():
        _px = _q.get("price") if isinstance(_q, dict) else _q
        if _px:
            market_prices[_t] = {"price": round(float(_px), 4), "source": "live_quotes.json"}

    # analyst_targets (added 2026-08-24, closes the standing gap: data_cache.analyst_targets has
    # been empty since it was reserved -- the real numbers live scattered in journal.json's
    # per-flag analyst_target field instead). Derive a per-ticker proxy from the MOST RECENT
    # journal entry that carries one, rather than leaving valuation_component blind. This is a
    # read of already-computed numbers, not a new fetch or an estimate.
    journal = load_json(os.path.join(args.base_dir, "journal.json"), default={})
    target_by_ticker = {}
    for e in journal.get("entries", []) or []:
        tgt = e.get("analyst_target")
        if tgt is None:
            continue
        prior = target_by_ticker.get(e["ticker"])
        if prior is None or (e.get("date") or "") >= prior[0]:
            target_by_ticker[e["ticker"]] = (e.get("date", ""), tgt)

    def upside_pct_for(ticker, price):
        if price:
            t = target_by_ticker.get(ticker)
            if t:
                return (t[1] - price) / price * 100.0
            dv = diversifier_candidates.get(ticker)
            if dv and dv.get("upside_pct") is not None:
                return dv["upside_pct"]
        return None

    # corroboration: how many independent Stage-1 surfaces named this ticker as of TODAY.
    # Direct fix for the user-reported gap -- SKHY was named by both rebound and thesis the same
    # run and got zero proposals because nothing counted it. Built from persisted, timestamped
    # state only (never ephemeral per-run agent prose this script cannot see).
    mention_counts = {}

    def _bump(t):
        mention_counts[t] = mention_counts.get(t, 0) + 1

    for t, stamp in signal_history_as_of.items():
        if stamp == today.isoformat() and signal_history.get(t):
            _bump(t)
    for cat in factor_catalysts:
        for t in (cat.get("affects") or []):
            _bump(t)
    for row in watchlist_setups:
        _bump(row.get("ticker"))
    for t in diversifier_candidates:
        _bump(t)
    for t, entry in thesis.items():
        if isinstance(entry, dict) and entry.get("verified_on") == today.isoformat():
            _bump(t)

    # EVER-EXITED tickers -- the `reentry` candidate pool. Sourced from compute_universe.json's
    # T2_ALUMNI tier when present, falling back to a trades.json scan.
    #
    # REWRITTEN 2026-08-30, and both changes matter:
    #
    # (a) The pool was scoped to names exited in the last "20 trading days" -- which the code
    #     computed as 20 CALENDAR days, so it was really about fourteen. Either way it made 35
    #     of the 70 tickers this book has ever traded permanently invisible to the proposal
    #     engine: an alumnus went stale roughly three weeks after exit and could never be
    #     proposed again, however good it later looked. The window is gone. It was carrying a
    #     job it was never needed for -- the conviction + thesis gate a few lines below already
    #     rejects "exited and still weak", which is the actual thing worth filtering. A time
    #     limit filtered on WHEN rather than on WHETHER THE CASE IS GOOD NOW. `exited_on`
    #     survives as CONTEXT for the rationale, never as an eligibility gate.
    #
    # (b) The pool keyed on `action == "exit"`. SKILL.md 2.9 already warns that `action`
    #     strings have drifted inconsistently across trades.json's history and that `qty_diff`
    #     is the unambiguous signal; the universe derives membership from quantity math
    #     instead of a label, so it sees exits that were never labelled as such.
    trades = load_json(os.path.join(args.base_dir, "trades.json"), default={"trades": []})
    universe = load_json(os.path.join(args.run_dir, "compute_universe.json"), default={})
    recently_exited = {}
    alumni_rows = [r for r in (universe.get("tickers") or [])
                   if r.get("tier") == "T2_ALUMNI" and not r.get("suppressed")]
    if alumni_rows:
        for r in alumni_rows:
            if r["ticker"] in risk_by_ticker:
                continue  # already re-entered
            try:
                recently_exited[r["ticker"]] = date.fromisoformat(r.get("last_held_date") or "")
            except (ValueError, TypeError):
                continue
    else:
        dq.append("compute_universe.json absent or empty -- reentry fell back to a trades.json "
                  "action=='exit' scan. Run `universe` before `triggers` for full alumni coverage.")
        for tr in trades.get("trades", []):
            if tr.get("action") != "exit" or tr.get("ticker") in risk_by_ticker:
                continue
            try:
                d = date.fromisoformat(tr.get("date", ""))
            except ValueError:
                continue
            prior = recently_exited.get(tr["ticker"])
            if prior is None or d > prior:
                recently_exited[tr["ticker"]] = d

    def _track_record_for(buckets):
        """Track record: use the measured hit rate of whichever bullish bucket this ticker
        carries, if any -- same source cmd_proposals already reads for signal_conviction.
        Extracted 2026-08-25 (self-learning Phase 1) so entry_setup/reentry/bench_diversifier
        can share it too -- those three were passing track_record: None outright, a dead
        track_record_multiplier call for 3 of the 9 conviction triggers, found in the same
        audit that found trigger_journal.json's 0-scored gate. Not everything gets a track
        record (bench_diversifier has no buckets to read at all), and that's fine -- None is
        the correct, honest answer there, not a bug to route around.

        Prefers the VALIDATED 30d bucket_hit_rates over the interim 7d table (added 2026-08-25,
        Phase 3 -- "feed the reconnected track_record_multiplier" from the now-unbiased data
        Phase 1 fixed). Both tables read from journal.json, which Phase 1's exited-ticker price
        injection has already de-biased for entries locked with a real price; the 30d table is
        simply the higher-confidence one when it has data, since it requires the full 30-day
        maturation window per VERDICT_THRESHOLD_PCT rather than the 7-day interim proxy. Falls
        back to 7d only when a bucket has no 30d-matured reading yet."""
        polarity = smith_risk.classify_signal_polarity(buckets)
        # WORST bullish bucket, not the first enumerated (2026-09-20). The loop used to `break`
        # on the first bullish bucket with data, so a name carrying MOMENTUM+VOLUME (20% hit,
        # n=15) alongside OVERSOLD BOUNCE (66.7%, n=3) got whichever the classifier listed first.
        # A sizing multiplier should be conservative about a name's evidence.
        tr = worst_bullish_track_record(polarity["bullish"], journal.get("bucket_hit_rates", {}),
                                        journal.get("bucket_hit_rates_7d", {}))
        return tr

    def build_ctx(ticker, thesis_entry, buckets, price, rsi_val, rel_val, earnings_fact_ticker):
        """One shared context-builder for every conviction trigger, so all nine score the exact
        same way off the exact same inputs -- divergent scoring per trigger type is how the old
        engine's five inconsistent thesis-status readers happened (see smith_risk.py's ONE FIELD
        ONE READER note); this is that discipline applied to conviction."""
        tr = _track_record_for(buckets)
        return {
            "ticker": ticker, "thesis_entry": thesis_entry, "factor_catalysts": factor_catalysts,
            "buckets": buckets, "upside_pct": upside_pct_for(ticker, price),
            "earnings_fact": earnings_facts.get(ticker), "rsi": rsi_val, "rsi_usable": rsi_usable,
            "rel_pp": rel_val, "rel_usable": rel_usable, "mention_count": mention_counts.get(ticker, 0),
            "track_record": tr,
        }

    for ticker, r in risk_by_ticker.items():
        status = smith_risk.thesis_status(thesis.get(ticker))
        rtk = rotation_by_ticker.get(ticker, {})
        bearish = set(rtk.get("bearish_buckets") or [])
        mv = r.get("market_value_usd") or 0.0
        price = price_by_ticker.get(ticker)
        over_cap = bool(r.get("over_cap"))
        headroom = r.get("headroom_usd")
        rsi = rsi_vals.get(ticker)
        rel_pp = rel_vals.get(ticker)
        abs_pct = abs_vals.get(ticker)
        healthy = status in HEALTHY_THESIS
        fundamental_headwind = bool(bearish & FUNDAMENTAL_HEADWIND_BUCKETS)
        # G62: a signal_history bucket carries NO timestamp, so a news-flow flag can outlive the
        # news indefinitely and silently veto a live trigger. Found 2026-08-12: META was resolved
        # WATCH->INTACT by smith-thesis against a verified source, was the book's only oversold
        # name, and still produced zero oversold_reversion candidates because a NEW HEADWINDS entry
        # from an earlier run kept tripping this veto -- and the only agent that can clear that
        # entry (smith-signals) had failed that run. A fresher, source-verified judgement lost to a
        # stale unverifiable one.
        # Fix: a thesis entry that is BOTH explicitly verified against a source AND re-verified
        # within THESIS_OVERRIDES_STALE_BUCKET_DAYS outranks the bucket. Deliberately narrow --
        # `verified: "unverified"` (the normal state) does NOT override anything, so this cannot
        # become a blanket bypass. The bucket is still reported, just no longer decisive.
        thesis_override = False
        if fundamental_headwind:
            stamp = _parse_as_of((state.get("signal_history_as_of") or {}).get(ticker))
            age = (today - stamp).days if stamp else None
            if age is None or age > HEADWIND_BUCKET_MAX_AGE_DAYS:
                fundamental_headwind = False
                dq.append(
                    f"{ticker}: {sorted(bearish & FUNDAMENTAL_HEADWIND_BUCKETS)} bucket DECAYED "
                    + (f"-- last refreshed {age}d ago, past the "
                       f"{HEADWIND_BUCKET_MAX_AGE_DAYS}d limit" if age is not None
                       else "-- no refresh stamp, so its age cannot be established")
                    + " (G62). smith-signals rewrites buckets wholesale each run, so an unrefreshed "
                      "bucket means that agent has not confirmed the headwind recently. Reported as "
                      "context; no longer decisive.")
        if fundamental_headwind and healthy:
            te = thesis.get(ticker)
            if isinstance(te, dict) and te.get("verified") in ("primary", "secondary"):
                von = _parse_as_of(te.get("verified_on"))
                if von and (today - von).days <= THESIS_OVERRIDES_STALE_BUCKET_DAYS:
                    thesis_override = True
                    fundamental_headwind = False
                    dq.append(f"{ticker}: stale {sorted(bearish & FUNDAMENTAL_HEADWIND_BUCKETS)} "
                              f"bucket OVERRIDDEN by a {te['verified']}-verified thesis re-checked "
                              f"{(today - von).days}d ago ({te.get('verified_on')}) -- G62. The "
                              f"bucket stands as context; it is no longer decisive.")
        base = {"ticker": ticker, "cluster": r.get("cluster"), "thesis_status": status,
                "rsi14": rsi, "rel_strength_1m_pp": rel_pp, "abs_return_1m_pct": abs_pct,
                "price_usd": price, "market_value_usd": round(mv, 2)}

        # --- A. oversold_reversion (BUY, live) ---------------------------------
        _trigger_oversold_reversion(base, ticker, status, healthy, rsi_usable, rsi, over_cap,
                                    headroom, max_single, fundamental_headwind, oversold, dq)

        # --- B. overbought_distribution (TRIM, live) ---------------------------
        _trigger_overbought_distribution(base, ticker, rsi_usable, rsi, rel_usable, abs_pct, mv,
                                         sector_map, cluster_rows, rel_vals, risk_by_ticker,
                                         thesis, overbought, sizing)

        # --- C. laggard_rotation (BUY, shadow) --------------------------------
        _trigger_laggard_rotation(base, ticker, rel_usable, laggard_set, healthy, over_cap,
                                  headroom, status, rel_pp, rel_cache, max_single,
                                  fundamental_headwind, laggard)

        # --- D/E. profit_ratchet + scale_out_ladder (shadow) -------------------
        _trigger_ratchet_and_ladder(base, ticker, r, mv, price, rsi, lots, laggard_set, ratchet,
                                    ladder, dq, sizing)

        # --- F. catalyst_threat (TRIM, live) ------------------------------------
        _trigger_catalyst_threat(base, ticker, mv, catalyst_threats_by_ticker, rotation_by_ticker,
                                 status, catalyst_threat, sizing)

        # --- G. thesis_break (TRIM, live) ---------------------------------------
        _trigger_thesis_break(base, ticker, status, mv, thesis, thesis_break, sizing)

        # --- H/I/J/K. conviction-driven triggers on HELD tickers (added 2026-08-24) -----------
        _trigger_conviction_held(base, ticker, r, mv, price, rsi, rel_pp, rsi_usable, healthy,
                                 over_cap, headroom, thesis, signal_history, atr_vals, total_book,
                                 policy, deployable_for_ideas, build_ctx, conviction_by_ticker,
                                 catalyst_threats_by_ticker, lots, trend_entry, trend_breakdown,
                                 conviction_average, conviction_exit, dq, sizing, cluster_rows)

    # --- L. entry_setup (BUY, live) --------------------------------------------------------
    _trigger_entry_setup_scan(watchlist_setups, risk_by_ticker, state, signal_history, thesis,
                              factor_catalysts, earnings_facts, mention_counts, _track_record_for,
                              atr_vals, sector_map, entry_setup, total_book, policy,
                              deployable_for_ideas, market_prices, cluster_rows)

    # --- M. reentry (BUY, live) -----------------------------------------------------------
    _reentry_no_thesis, _reentry_judged_out = [], []
    _trigger_reentry_scan(trades, recently_exited, signal_history, thesis, factor_catalysts,
                          earnings_facts, upside_pct_for, rsi_vals, rsi_usable, rel_vals,
                          rel_usable, mention_counts, _track_record_for, atr_vals, total_book,
                          policy, deployable_for_ideas, sector_map, reentry, _reentry_no_thesis,
                          _reentry_judged_out, cluster_rows)

    # --- N. bench_diversifier (BUY, live) --------------------------------------------------
    _trigger_bench_diversifier_scan(diversifier_candidates, risk_by_ticker, state, mention_counts,
                                    _track_record_for, atr_vals, total_book, policy,
                                    deployable_for_ideas, bench_diversifier, market_prices,
                                    cluster_rows, sector_map)

    # --- O/P. profit_rotation + cluster_rotation (PAIRED, live) ---------------------------
    _trigger_profit_rotation(names_stretched, conviction_by_ticker, thesis, total_book, policy,
                             profit_rotation, cluster_rows, sizing)
    _cluster_ladders = state.get("cluster_ladders") or {}
    _trigger_cluster_rotation(conviction_by_ticker, thesis, cluster_rotation, cluster_rows,
                              _cluster_ladders, today, sizing)

    # --- Q/R. cluster_bench_rotation + cluster_consolidation (PAIRED, SHADOW) --------------
    _trigger_cluster_bench_rotation(_cluster_ladders, conviction_by_ticker, thesis,
                                    risk_by_ticker, today, cluster_bench_rotation, sizing)
    _trigger_cluster_consolidation(_cluster_ladders, conviction_by_ticker, risk_by_ticker,
                                   today, cluster_consolidation, sizing, cluster_rows)

    # --- PORTFOLIO HEAT BUDGET (Phase 3): one post-pass over EVERY live buy candidate, after all
    # triggers have sized theirs and before the materiality annotation below reads the final sizes.
    _heat = _apply_heat_budget(
        {"oversold_reversion": oversold, "trend_entry": trend_entry, "conviction_average": conviction_average,
         "entry_setup": entry_setup, "reentry": reentry, "bench_diversifier": bench_diversifier},
        {"profit_rotation": profit_rotation, "cluster_rotation": cluster_rotation},
        {"overbought_distribution": overbought, "catalyst_threat": catalyst_threat,
         "thesis_break": thesis_break, "trend_breakdown": trend_breakdown, "conviction_exit": conviction_exit},
        risk, drift, policy, load_json(os.path.join(args.run_dir, "compute_correlation.json"), default={}),
        today, sizing, sector_map, dq, atr_vals,
        load_json(os.path.join(args.base_dir, "learning.json"), default={}) or {})

    # --- materiality on the single-leg BUYS: annotate only (sells and rotation legs carry their own
    # verdict and ARE demoted). Unfunded rows (size 0/None) are not tickets and are skipped.
    for _fam in (oversold, laggard, trend_entry, conviction_average, entry_setup, reentry,
                 bench_diversifier):
        for _row in _fam:
            _apply_buy_materiality(_row, sizing)
    _below = [(fam, r) for fam, rows in (
        ("oversold_reversion", oversold), ("overbought_distribution", overbought),
        ("catalyst_threat", catalyst_threat), ("thesis_break", thesis_break),
        ("trend_entry", trend_entry), ("trend_breakdown", trend_breakdown),
        ("conviction_average", conviction_average), ("conviction_exit", conviction_exit),
        ("entry_setup", entry_setup), ("reentry", reentry), ("bench_diversifier", bench_diversifier),
        ("profit_rotation", profit_rotation), ("cluster_rotation", cluster_rotation))
        for r in rows if r.get("vote") == "below_materiality"]
    if _below:
        dq.append("below_materiality (emitted, not proposed -- too small to act on): " + "; ".join(
            f"{fam} {r.get('ticker') or r.get('pair_id')} short ${r.get('materiality_shortfall_usd') or 0:,.0f}"
            for fam, r in _below)
            + ". Many of these are stubs: a book that generates tickets this small needs consolidating.")
    _sell_rows = [(fam, r.get("ticker"), r) for fam, rows in (
        ("overbought_distribution", overbought), ("catalyst_threat", catalyst_threat),
        ("thesis_break", thesis_break), ("trend_breakdown", trend_breakdown),
        ("conviction_exit", conviction_exit), ("scale_out_ladder", ladder)) for r in rows] + [
        (fam, r["sell_leg"]["ticker"], r["sell_leg"]) for fam, rows in (
            ("profit_rotation", profit_rotation), ("cluster_rotation", cluster_rotation),
            ("cluster_bench_rotation", cluster_bench_rotation)) for r in rows]
    if _sell_rows:
        dq.append("risk-sized sell legs, legacy -> new (family ticker: legacy$ -> new$ [action]; "
                  "risk removed): " + "; ".join(
            f"{fam} {t}: {l.get('legacy_size_usd')} -> {l.get('suggested_size_usd')} "
            f"[{l.get('sell_action')}] risk ${l.get('risk_removed_usd')}"
            for fam, t, l in _sell_rows))

    oversold.sort(key=lambda x: x["rsi14"])
    overbought.sort(key=lambda x: -x["rsi14"])
    laggard.sort(key=lambda x: x["rel_strength_1m_pp"])
    ratchet.sort(key=lambda x: -(x["gain_at_risk_usd"] or 0))
    ladder.sort(key=lambda x: -x["gain_pct"])
    catalyst_threat.sort(key=lambda x: -(x.get("market_value_usd") or 0))
    thesis_break.sort(key=lambda x: -(x.get("market_value_usd") or 0))

    trend_entry.sort(key=lambda x: -(x.get("conviction_score") or 0))
    trend_breakdown.sort(key=lambda x: -(x.get("conviction_score") or 0))
    conviction_average.sort(key=lambda x: -(x.get("conviction_score") or 0))
    conviction_exit.sort(key=lambda x: -(x.get("negative_signal_count") or 0))
    entry_setup.sort(key=lambda x: -(x.get("conviction_score") or 0))
    _rebound_pool = [r["ticker"] for r in (universe.get("tickers") or [])
                     if r.get("tier") in ("T1_HELD", "T2_ALUMNI", "T4_WATCHLIST") and not r.get("suppressed")]
    _rebound_bars = load_json(os.path.join(args.run_dir, "bars.json"), default={}) or {}
    _rebound_support = smith_marketdata.support_levels(_rebound_bars, _rebound_pool) if _rebound_bars else {}
    rebound = _rebound_screen(book, risk, policy, dc, universe, thesis, today,
                              rel_usable=rel_usable, rel_age=rel_age, support=_rebound_support)

    if rebound.get("stale_warning"):
        dq.append(rebound["stale_warning"])
    if rebound["correction_state"] != "none":
        dq.append(f"correction_state={rebound['correction_state']} "
                  f"({'; '.join(rebound['reasons'])}) -- dispatch smith-rebound this run.")

    if _reentry_no_thesis:
        dq.append(f"reentry: {len(_reentry_no_thesis)} alumni could not be JUDGED at all -- no "
                  f"state.thesis entry exists for them ({', '.join(sorted(_reentry_no_thesis)[:10])}"
                  f"{'...' if len(_reentry_no_thesis) > 10 else ''}). state.thesis is seeded from "
                  f"CURRENT holdings, so an exited name is absent by construction and fails the "
                  f"conviction gate for lack of evidence, not on the evidence. These are not "
                  f"rejected candidates; they are unexamined ones.")
    if _reentry_judged_out:
        dq.append(f"reentry: {len(_reentry_judged_out)} alumni judged and rejected on a real "
                  f"thesis/conviction read ({', '.join(sorted(_reentry_judged_out)[:10])}).")
    reentry.sort(key=lambda x: -(x.get("conviction_score") or 0))
    bench_diversifier.sort(key=lambda x: -(x.get("conviction_score") or 0))

    def _n_live(rows):
        return sum(1 for r in rows if r.get("vote") == "live")

    live_counts = {"oversold_reversion": _n_live(oversold), "overbought_distribution": _n_live(overbought),
                   "catalyst_threat": _n_live(catalyst_threat), "thesis_break": _n_live(thesis_break),
                   "trend_entry": _n_live(trend_entry), "trend_breakdown": _n_live(trend_breakdown),
                   "conviction_average": _n_live(conviction_average), "conviction_exit": _n_live(conviction_exit),
                   "entry_setup": _n_live(entry_setup),
                   "reentry": _n_live(reentry), "bench_diversifier": _n_live(bench_diversifier),
                   "profit_rotation": _n_live(profit_rotation), "cluster_rotation": _n_live(cluster_rotation),
                   "factor_threat": len(factor_threat)}
    below_materiality_counts = {fam: n for fam, n in (
        ("oversold_reversion", sum(1 for r in oversold if r.get("vote") == "below_materiality")),
        ("overbought_distribution", sum(1 for r in overbought if r.get("vote") == "below_materiality")),
        ("catalyst_threat", sum(1 for r in catalyst_threat if r.get("vote") == "below_materiality")),
        ("thesis_break", sum(1 for r in thesis_break if r.get("vote") == "below_materiality")),
        ("trend_entry", sum(1 for r in trend_entry if r.get("vote") == "below_materiality")),
        ("trend_breakdown", sum(1 for r in trend_breakdown if r.get("vote") == "below_materiality")),
        ("conviction_average", sum(1 for r in conviction_average if r.get("vote") == "below_materiality")),
        ("conviction_exit", sum(1 for r in conviction_exit if r.get("vote") == "below_materiality")),
        ("entry_setup", sum(1 for r in entry_setup if r.get("vote") == "below_materiality")),
        ("reentry", sum(1 for r in reentry if r.get("vote") == "below_materiality")),
        ("bench_diversifier", sum(1 for r in bench_diversifier if r.get("vote") == "below_materiality")),
        ("profit_rotation", sum(1 for r in profit_rotation if r.get("vote") == "below_materiality")),
        ("cluster_rotation", sum(1 for r in cluster_rotation if r.get("vote") == "below_materiality"))) if n}
    shadow_counts = {"entry_setup": sum(1 for r in entry_setup if r.get("vote") == "shadow"),
                     "laggard_rotation": len(laggard), "profit_ratchet": len(ratchet),
                     "scale_out_ladder": len(ladder),
                     "cluster_bench_rotation": len(cluster_bench_rotation),
                     "cluster_consolidation": len(cluster_consolidation)}

    # Shadow entries mirror cmd_derisk's shadow_new contract: price_at_flag now, scored later.
    shadow_new = [{"date": today.isoformat(), "ticker": c["ticker"],
                   "trigger_type": c["trigger_type"], "price_at_flag": c.get("price_usd"),
                   "rsi14": c.get("rsi14"), "gain_pct": c.get("gain_pct"),
                   "rel_strength_1m_pp": c.get("rel_strength_1m_pp"), "scored": False}
                  for c in laggard + ratchet + ladder]
    # Paired shadow triggers log their BUY leg -- that is the half whose vote is being tested
    # (the sell leg has already cleared the same bars a live rotation's sell leg does).
    shadow_new += [{"date": today.isoformat(), "ticker": p["buy_leg"]["ticker"],
                    "trigger_type": p["trigger_type"],
                    "price_at_flag": (p["buy_leg"].get("price_usd")
                                      or price_by_ticker.get(p["buy_leg"]["ticker"])),
                    "rsi14": None, "gain_pct": None, "rel_strength_1m_pp": None,
                    "pair_id": p["pair_id"], "scored": False}
                   for p in cluster_bench_rotation + cluster_consolidation]

    emit({
        "as_of": today.isoformat(),
        "rsi_as_of": rsi_cache.get("as_of"), "rsi_age_days": rsi_age, "rsi_usable": rsi_usable, "rsi_coverage_pct": rsi_coverage_pct,
        "rsi_missing": rsi_missing,
        "rel_as_of": rel_cache.get("as_of"), "rel_age_days": rel_age, "rel_usable": rel_usable, "rel_coverage_pct": rel_coverage_pct,
        "rel_missing": rel_missing,
        "deployable_cash_usd": round(deployable, 2),
        "max_single_deploy_usd": round(max_single, 2),
        "thresholds": {"rsi_oversold": RSI_OVERSOLD, "rsi_overbought": RSI_OVERBOUGHT,
                       "laggard_pctile": LAGGARD_PCTILE, "ratchet_min_gain_pct": RATCHET_MIN_GAIN_PCT,
                       "ladder_tiers_pct": LADDER_TIERS_PCT,
                       # WHAT A TRIM MEANS (Phase 2): a downstream reader can size-check any row
                       # without reading source. Sells are RISK dollars: size = severity_r x r_base_usd
                       # / (stop_pct/100), clamped to the position.
                       "sizing": {
                           "currency": "risk_dollars",
                           "r_base_usd": round(sizing["r_base_usd"], 2),
                           "r_base_rule": "policy.stop_loss_framework.risk_per_position_pct_of_book x total book",
                           "stop_pct_rule": "max(2 x atr20_pct, 3.0)",
                           "size_usd_rule": "min(severity_r x market value, market value); i.e. risk_removed = severity_r x R_open, R_open = mv x stop_pct/100",
                           "severity_unit": "fraction of the position's OWN open risk (R_base is the unit for entries and trim_risk_cap only)",
                           "severity_r": dict(SEVERITY_R),
                           "severity_r_computed": {
                               "trim_risk_cap": "(R_open - R_base) / R_base -- trims exactly to the ATR cap",
                               "cluster_consolidation": "full exit of the dropped name"},
                           "exit_or_hold": {"trim_to_exit_fraction": TRIM_TO_EXIT_FRACTION,
                                            "min_position_usd": sizing["min_position_usd"],
                                            "rule": "residual < min_position or trim > 60% -> full exit; "
                                                    "a position already < min_position is never partially trimmed"},
                           "rotation_buy_rule": "buy = min(buy R_ticket, R_freed) / buy stop, then headroom / "
                                                "cluster room / deployable cash; rotation_risk names the bound",
                           "materiality": {**sizing["materiality"],
                                           "rule": "ticket >= max(min_ticket_usd, min_ticket_pct_of_book% x book, "
                                                   "min_ticket_r x r_base / stop, fee_cover_mult x round-trip fee); "
                                                   "sub-floor -> vote below_materiality; full exits exempt"},
                           "round_trip_fee_pct": sizing["fee_pct"],
                           "heat_budget": {
                               "rule": "H_eff_max = H_max x (heat_floor + (1 - heat_floor) x (1 - rho)); R_free = max(0, H_eff_max - H); "
                                       "H = aggregate_open_risk_usd, H_max = aggregate_open_risk_cap_pct_of_book x total book",
                               "heat_floor": _heat.get("heat_floor"), "cluster_sub_budget": _heat.get("cluster_sub_budget"),
                               "unmeasured_correlation": "rho treated as 1.0 (conservative bound), never as 0",
                               "allocation": "pairs first (net = buy risk - the risk their own sell frees), then singles greedily by "
                                             "smith_ticket.allocation_priority; a partial fit is sized to the remaining room only if it "
                                             "still clears materiality, else the ticket is DEFERRED (vote 'deferred', never dropped)",
                               "over_cap": "H > H_eff_max -> zero new net-risk buys; sells and net<=0 rotations still emit; no sell credit is taken",
                               "sell_credit": "OFF: a proposed standalone sell has not freed anything (STANDALONE_SELL_CREDIT_ENABLED); only a rotation's own sell leg offsets its own buy",
                               "static_clamps": ["single_position", "ai_capex", "cluster_risk_budget"]},
                           "legacy_fractions_for_one_release": {k: round(v, 4) for k, v in LEGACY_SELL_FRACTION.items()},
                       }},
        "deployable_cash_for_ideas_usd": round(deployable_for_ideas, 2),
        "live_counts": live_counts, "shadow_counts": shadow_counts,
        "below_materiality_counts": below_materiality_counts,
        "heat_budget": _heat,
        "deferred_counts": {fam: n for fam, n in (
            (fam, sum(1 for r in rows if r.get("vote") == "deferred")) for fam, rows in (
                ("oversold_reversion", oversold), ("trend_entry", trend_entry),
                ("conviction_average", conviction_average), ("entry_setup", entry_setup),
                ("reentry", reentry), ("bench_diversifier", bench_diversifier),
                ("profit_rotation", profit_rotation), ("cluster_rotation", cluster_rotation))) if n},
        "oversold_reversion": oversold, "overbought_distribution": overbought,
        "catalyst_threat": catalyst_threat, "thesis_break": thesis_break,
        "factor_threat": factor_threat,
        "trend_entry": trend_entry, "trend_breakdown": trend_breakdown,
        "conviction_average": conviction_average, "conviction_exit": conviction_exit,
        "entry_setup": entry_setup, "reentry": reentry, "bench_diversifier": bench_diversifier,
        "rebound": rebound, "correction_state": rebound["correction_state"],
        "profit_rotation": profit_rotation, "cluster_rotation": cluster_rotation,
        "cluster_bench_rotation": cluster_bench_rotation,
        "cluster_consolidation": cluster_consolidation,
        "laggard_rotation": laggard, "profit_ratchet": ratchet, "scale_out_ladder": ladder,
        "shadow_new": shadow_new,
        # Published for cmd_proposals' retirement pass so it tests RSI-triggered proposals against
        # the SAME gated numbers this subcommand used, rather than re-reading the cache and
        # possibly disagreeing about staleness. Empty when rsi_usable is false -- the retirement
        # pass then cannot test the condition and keeps the proposal open, the safe direction.
        "rsi_values": (rsi_vals if rsi_usable else {}),
        "abs_return_1m_pct_values": (abs_vals if rel_usable else {}),
        "data_quality": dq,
    })


# ---------------------------------------------------------------------------
# draft-specs -- script-drafted strategist proposal specs (added 2026-09-15,
# efficiency pass item 5: "the triggers already size every candidate; let a script draft the
# specs and the fixed sections, leaving the strategist to accept, reject and explain")
# ---------------------------------------------------------------------------
_DRAFT_SINGLE_LEG_KEYS = ("oversold_reversion", "overbought_distribution", "catalyst_threat",
                          "thesis_break", "trend_entry", "trend_breakdown", "conviction_average",
                          "conviction_exit", "entry_setup", "reentry", "bench_diversifier")
_DRAFT_PAIRED_KEYS = ("profit_rotation", "cluster_rotation")


def _draft_leg_spec(ticker, trigger_type, direction, row, pair_id=None, pair_role=None):
    return {"direction": direction, "ticker": ticker, "trigger_type": trigger_type,
            "pair_id": pair_id, "pair_role": pair_role,
            "size_usd": row.get("suggested_size_usd"),
            "size_wanted_usd": row.get("size_wanted_usd"), "clamped_by": row.get("clamped_by"),
            "price_at_proposal": row.get("price_usd"), "stop_price_usd": row.get("stop_price_usd"),
            "draft_reasons": row.get("reasons"), "blockers": row.get("blockers"),
            # Left for the strategist to write -- this is judgment, never scripted:
            "rationale": None, "evidence_quality": None}


def _draft_proposal_specs(triggers, open_keys):
    specs, skipped = [], []
    for key in _DRAFT_SINGLE_LEG_KEYS:
        for row in triggers.get(key) or []:
            if row.get("vote") != "live":
                continue
            ticker, ttype = row.get("ticker"), row.get("trigger_type", key)
            if (ticker, ttype) in open_keys:
                skipped.append(f"{ticker}/{ttype} already open")
                continue
            specs.append(_draft_leg_spec(ticker, ttype, row.get("direction"), row))
    for key in _DRAFT_PAIRED_KEYS:
        for row in triggers.get(key) or []:
            if row.get("vote") != "live":
                continue
            sell, buy = row.get("sell_leg") or {}, row.get("buy_leg") or {}
            ttype, pair_id = row.get("trigger_type", key), row.get("pair_id")
            sk, bk = (sell.get("ticker"), ttype), (buy.get("ticker"), ttype)
            if sk in open_keys or bk in open_keys:
                skipped.append(f"pair {pair_id} already open ({sell.get('ticker')}/{buy.get('ticker')})")
                continue
            specs.append(_draft_leg_spec(sell.get("ticker"), ttype, sell.get("direction"),
                                         sell, pair_id=pair_id, pair_role="sell"))
            specs.append(_draft_leg_spec(buy.get("ticker"), ttype, buy.get("direction"),
                                         buy, pair_id=pair_id, pair_role="buy"))
    return specs, skipped


def _draft_stress_anchor(market_inputs, fomc_cache):
    mi, fc = market_inputs or {}, fomc_cache or {}
    return {"us10y_pct": mi.get("us10y"), "vix": mi.get("vix"), "dxy": mi.get("dxy"),
            "fed_rate_pct": fc.get("rate_pct"), "fed_stance": fc.get("stance")}


def _draft_scorecard_quote(scorecard):
    if not scorecard:
        return None
    o = scorecard.get("overall") or {}
    parts = [f"Stored scorecard (as_of {scorecard.get('as_of')}, n={o.get('n')}): "
             f"overall {scorecard.get('overall_accuracy_30d')}% "
             f"({o.get('worked')}/{o.get('missed')}/{o.get('neutral')} worked/missed/neutral)"]
    for label, d in (scorecard.get("by_direction") or {}).items():
        parts.append(f"{label} {d.get('accuracy_pct')}% (n={d.get('n')})")
    return "; ".join(parts)


def cmd_draft_specs(args):
    """Drafts the strategist's proposal specs from compute_triggers.json's already-sized/-scored
    live candidates, plus the stress table's anchor block and a pre-formatted scorecard quote --
    the mechanical two-thirds of TASK 2/4/6 that was previously hand-written in the strategist's
    32-minute, 42-call pass. Judgment (rationale, evidence_quality, accept/reject, scenario
    mechanism/impact estimates, scorecard INTERPRETATION) stays the strategist's -- this only
    drafts the arithmetic fields the trigger rows already carry."""
    triggers = load_json(os.path.join(args.run_dir, "compute_triggers.json"), default={})
    props = load_json(os.path.join(args.base_dir, "proposals.json"), default={})
    market_inputs = load_json(os.path.join(args.run_dir, "market_inputs.json"), default={})
    state = load_json(os.path.join(args.base_dir, "state.json"), default={})
    open_keys = {(pr.get("ticker"), pr.get("trigger_type"))
                 for pr in (props.get("proposals") or [])
                 if pr.get("status") in ("open", "accepted_by_user")}
    specs, skipped = _draft_proposal_specs(triggers, open_keys)
    out = {"as_of": triggers.get("as_of"), "proposal_specs": specs, "skipped_already_open": skipped,
           "stress_table_anchor": _draft_stress_anchor(market_inputs, state.get("fomc_cache")),
           "scorecard_quote": _draft_scorecard_quote(props.get("scorecard"))}
    atomic_write_json(os.path.join(args.run_dir, "proposal_specs.json"), out)
    emit(out)


# ---------------------------------------------------------------------------
# sync-decisions -- reconciles the interactive dashboard's button clicks
# ---------------------------------------------------------------------------
# Added 2026-08-25. Lives HERE, not in smith_lifecycle.py (where cmd_dismiss/cmd_proposals
# live), because smith_learning.py already imports from smith_lifecycle
# (_proposal_parse_date) -- putting this in smith_lifecycle and importing smith_learning from
# it would be circular. smith_math.py already imports both, so it's the natural home for
# anything that needs to reach across both modules, same reasoning as every other
# cross-cutting CLI command in this file.
#
# THE BRIDGE THIS CLOSES: no capability lets a published page write to this Mac's filesystem
# (checked against the real contract before designing anything -- only downloads/mcp/self
# exist). `self.publish` lets the page durably hold data (by republishing itself) until a
# future Agent Smith run fetches the live artifact and reconciles it here. That fetch is the
# orchestrator's job (WebFetch, per SKILL.md's new step 1.7); parsing and applying what it
# finds is this function's job -- deterministic, never eyeballed.

_DECISIONS_BLOB_RE = re.compile(
    r'<script type="application/json" id="smith-decisions">(.*?)</script>', re.S)


def _extract_decisions(html):
    """Pull the decisions[] array out of fetched dashboard HTML. Returns [] (never raises) if
    the tag is missing or unparseable -- a malformed/absent blob means 'nothing to reconcile',
    not 'crash the run'. A freshly-built dashboard always ships this tag empty, so its absence
    from an OLDER cached fetch is also a legitimate empty case, not just a parse failure."""
    m = _DECISIONS_BLOB_RE.search(html)
    if not m:
        return []
    try:
        parsed = json.loads(m.group(1))
    except ValueError:
        return []
    return parsed if isinstance(parsed, list) else []


def _decisions_from_records_file(path):
    """Reads the decisions[] array from a JSON file the orchestrator wrote after an
    `Artifact action:"read_db"` call against the dashboard's `decisions` collection (added
    2026-09-16, replacing the WebFetch-the-whole-page path -- see `--records-file` below).
    Each record's `id` (the db document id) is harmless extra data to the per-decision loop,
    which only reads the fields it already knows. Malformed/absent -> [], same contract as
    `_extract_decisions`."""
    try:
        with open(path) as f:
            parsed = json.load(f)
    except (OSError, ValueError):
        return []
    return parsed if isinstance(parsed, list) else []


def cmd_sync_decisions(args):
    if getattr(args, "records_file", None):
        decisions = _decisions_from_records_file(args.records_file)
    else:
        with open(args.html_file) as f:
            html = f.read()
        decisions = _extract_decisions(html)
    today = str(resolve_today(args.today))

    import copy
    _lock = file_lock(args.base_dir)
    _lock.__enter__()                  # held from load to write: no concurrent writer lands between
    p_path = os.path.join(args.base_dir, "proposals.json")
    s_path = os.path.join(args.base_dir, "state.json")
    proposals_store = load_json(p_path, default={"proposals": [], "scorecard": {}})
    state = load_json(s_path, default={})
    props = proposals_store.get("proposals", [])

    reconciled, skipped, errors = [], [], []
    proposals_dirty = False
    state_dirty = False

    def prop_by_id(pid):
        return next((p for p in props if p.get("id") == pid), None)

    for d in decisions:
        surface = d.get("surface")
        element_id = d.get("element_id")
        decision = d.get("decision")
        reason = d.get("reason") or None
        # A decision that raises halfway must not leave half its edits behind (2026-09-14):
        # snapshot, and restore on failure. Decision volume per sync is tiny.
        _snap = (copy.deepcopy(props), copy.deepcopy(state), proposals_dirty, state_dirty)
        try:
            if surface == "proposal":
                pr = prop_by_id(element_id)
                if pr is None:
                    skipped.append({"surface": surface, "element_id": element_id, "why": "no such proposal"})
                    continue
                if decision == "reject":
                    if pr.get("status") != "open":
                        skipped.append({"surface": surface, "element_id": element_id, "why": f"already {pr.get('status')}"})
                        continue
                    dismiss_proposal_core(props, element_id, reason, actor="user (dashboard)")
                    proposals_dirty = True
                elif decision == "retire":
                    # RETIRE (added 2026-09-19) is not Reject. It is the user confirming the
                    # DESK's own recommendation to withdraw its proposal (smith_validity verdict
                    # `retire`) -- so it is recorded as dismissed_by_desk, which the scorecard
                    # counts as a strategist miss. Filing it as a user override would hide the
                    # desk's own stale calls inside the exclusion meant for the user's taste.
                    if pr.get("status") != "open":
                        skipped.append({"surface": surface, "element_id": element_id, "why": f"already {pr.get('status')}"})
                        continue
                    dismiss_proposal_core(props, element_id,
                                          reason or "desk recommended retirement; confirmed on the dashboard",
                                          actor="desk (retire recommendation, confirmed by user)")
                    proposals_dirty = True
                elif decision == "accept":
                    if pr.get("status") != "open":
                        skipped.append({"surface": surface, "element_id": element_id, "why": f"already {pr.get('status')}"})
                        continue
                    # Deliberately NOT "executed"/"fulfilled"/"filled" -- those mean a
                    # ledger-confirmed fill. A button click is a stated intent, never proof of
                    # a trade; conflating the two would let an unconfirmed click into
                    # outcome-scoring's SCOREABLE set.
                    pr["status"] = "accepted_by_user"
                    pr["accepted_on"] = today
                    pr["accepted_reason"] = reason
                    proposals_dirty = True
                elif decision == "hold":
                    if pr.get("status") != "open":
                        skipped.append({"surface": surface, "element_id": element_id, "why": f"already {pr.get('status')}"})
                        continue
                    # Same-day dedup: the decisions blob is CUMULATIVE -- every republish of
                    # the page carries every decision ever made on it, so a Hold is re-presented
                    # to this code on each sync. Accept/reject are naturally idempotent because
                    # they reach a terminal status that the skip-check sees; hold deliberately
                    # is NOT terminal (the proposal stays open), so nothing stopped it appending
                    # a duplicate date every run. P-178 read "held 2x" on 2026-08-31 from a
                    # single click.
                    holds = pr.setdefault("held_on", [])
                    if today in holds:
                        # Already applied today. Report it as SKIPPED, not reconciled, and fall
                        # through to `continue` so no observation is logged: the dedup below
                        # kept proposals.json correct, but the caller still recorded a fresh
                        # `dashboard.decision.proposal` observation into learning.json on every
                        # sync of the same cumulative blob (found 2026-08-31, P-178 logged
                        # twice). That substrate measures revealed preference and engagement
                        # rate, so duplicate holds would inflate the hold count and bias any
                        # calibration built on it -- a quieter version of the same bug, one
                        # layer down. record_observation is right to never mutate a prior
                        # observation; the fix belongs here, in not recording an event this
                        # sync did not actually apply.
                        skipped.append({"surface": surface, "element_id": element_id,
                                        "why": f"already held on {today}"})
                        continue
                    holds.append(today)
                    pr["held_reason"] = reason
                    proposals_dirty = True
                else:
                    skipped.append({"surface": surface, "element_id": element_id, "why": f"unknown decision {decision!r}"})
                    continue
                record_observation(args.base_dir, "dashboard.decision.proposal",
                                   {"element_id": element_id, "decision": decision, "reason": reason,
                                    "ticker": pr.get("ticker"), "trigger_type": pr.get("trigger_type")},
                                   today=today, write=True)
                reconciled.append({"surface": surface, "element_id": element_id, "decision": decision})

            elif surface == "auto_retired_proposal":
                pr = prop_by_id(element_id)
                if pr is None or pr.get("status") != "auto_retired":
                    skipped.append({"surface": surface, "element_id": element_id, "why": "not auto_retired"})
                    continue
                if decision == "revive":
                    pr["status"] = "open"
                    pr["retired_reason"] = None
                    pr["revived_by_user_on"] = today
                    proposals_dirty = True
                    record_observation(args.base_dir, "dashboard.decision.auto_retired_proposal",
                                       {"element_id": element_id, "decision": decision, "reason": reason,
                                        "ticker": pr.get("ticker")}, today=today, write=True)
                    reconciled.append({"surface": surface, "element_id": element_id, "decision": decision})
                else:
                    skipped.append({"surface": surface, "element_id": element_id, "why": f"unknown decision {decision!r}"})

            elif surface == "watchlist":
                ticker = element_id
                if decision == "not_interested":
                    state.setdefault("watchlist_suppressed", {})[ticker] = {"date": today, "reason": reason}
                    state_dirty = True
                elif decision == "watch_closely":
                    state.setdefault("watchlist_priority", {})[ticker] = {"date": today, "reason": reason}
                    state_dirty = True
                else:
                    skipped.append({"surface": surface, "element_id": element_id, "why": f"unknown decision {decision!r}"})
                    continue
                record_observation(args.base_dir, "dashboard.decision.watchlist",
                                   {"ticker": ticker, "decision": decision, "reason": reason},
                                   today=today, write=True)
                reconciled.append({"surface": surface, "element_id": element_id, "decision": decision})

            elif surface == "diversifier":
                ticker = element_id
                if decision != "not_interested":
                    skipped.append({"surface": surface, "element_id": element_id, "why": f"unknown decision {decision!r}"})
                    continue
                state.setdefault("watchlist_suppressed", {})[ticker] = {"date": today, "reason": reason}
                state_dirty = True
                record_observation(args.base_dir, "dashboard.decision.diversifier",
                                   {"ticker": ticker, "decision": decision, "reason": reason},
                                   today=today, write=True)
                reconciled.append({"surface": surface, "element_id": element_id, "decision": decision})

            elif surface == "derisk":
                ticker = element_id
                if decision != "disagree":
                    skipped.append({"surface": surface, "element_id": element_id, "why": f"unknown decision {decision!r}"})
                    continue
                # Never removes the ticker from the queue -- cmd_derisk reports the override
                # ALONGSIDE its own computed score (smith_risk.derisk_override_for), never
                # instead of it. A real risk signal is never suppressed, only annotated.
                state.setdefault("derisk_overrides", {})[ticker] = {"date": today, "reason": reason}
                state_dirty = True
                record_observation(args.base_dir, "dashboard.decision.derisk",
                                   {"ticker": ticker, "decision": decision, "reason": reason},
                                   today=today, write=True)
                reconciled.append({"surface": surface, "element_id": element_id, "decision": decision})

            elif surface == "gap":
                gap_id = element_id
                gaps = state.get("known_gaps") or []
                g = next((x for x in gaps if x.get("id") == gap_id), None)
                if g is None or decision != "resolve":
                    skipped.append({"surface": surface, "element_id": element_id, "why": "no such open gap or unknown decision"})
                    continue
                # Found live during testing (2026-08-25, fixture picked G18): a gap carrying a
                # `user_decision` field already has a standing directive attached by a real
                # interactive session (e.g. G18's own "confirmed LEAVE AS wont_fix... do not
                # re-open, do not re-evaluate sources"). A dashboard click must never silently
                # override that -- Mark Resolved is meant for ordinary gaps, not ones a prior
                # conversation already reasoned through explicitly.
                if g.get("user_decision"):
                    skipped.append({"surface": surface, "element_id": element_id,
                                    "why": "gap carries a standing user_decision -- resolve it "
                                    "in chat, not via a dashboard click, so the standing "
                                    "directive is reviewed rather than silently overwritten"})
                    continue
                g["status"] = "closed"
                g["resolution"] = reason or "closed via dashboard"
                g["closed_by"] = "user (dashboard)"
                g["closed"] = today
                state_dirty = True
                reconciled.append({"surface": surface, "element_id": element_id, "decision": decision})
                # no learning observation -- pure convenience, not a preference signal

            elif surface == "learning_param":
                param_id = element_id
                if decision == "approve":
                    res = user_force_approve(args.base_dir, param_id, today=today,
                                             why=("user-approved via dashboard" + (f": {reason}" if reason else "")),
                                             write=True)
                    if res is None:
                        skipped.append({"surface": surface, "element_id": element_id,
                                        "why": "parameter is no longer in escalated state -- stale click, not applied"})
                        continue
                    reconciled.append({"surface": surface, "element_id": element_id, "decision": decision, "result": res})
                elif decision == "defer":
                    # Doing nothing IS deferring -- re-surfaces next run since it's still escalated.
                    reconciled.append({"surface": surface, "element_id": element_id, "decision": decision})
                else:
                    skipped.append({"surface": surface, "element_id": element_id, "why": f"unknown decision {decision!r}"})

            elif surface == "thesis":
                ticker = element_id
                thesis_map = state.get("thesis", {})
                entry = thesis_map.get(ticker)
                if entry is None or not isinstance(entry, dict):
                    skipped.append({"surface": surface, "element_id": element_id, "why": "no thesis entry to act on"})
                    continue
                if decision == "confirm":
                    # Never bumps `verified` -- a click is not a primary source. Logged as an
                    # observation only; the thesis entry itself is untouched.
                    record_observation(args.base_dir, "dashboard.decision.thesis",
                                       {"ticker": ticker, "decision": decision, "reason": reason,
                                        "status_at_confirm": entry.get("status")},
                                       today=today, write=True)
                    reconciled.append({"surface": surface, "element_id": element_id, "decision": decision})
                elif decision == "override":
                    if not reason:
                        skipped.append({"surface": surface, "element_id": element_id,
                                        "why": "override requires a reason, none supplied"})
                        continue
                    new_status = d.get("new_status")
                    if new_status not in smith_risk.KNOWN_STATUSES:
                        skipped.append({"surface": surface, "element_id": element_id,
                                        "why": f"override new_status {new_status!r} not a known thesis status"})
                        continue
                    entry.setdefault("evidence_for" if new_status in ("strengthening", "intact") else "evidence_against",
                                     []).append({"claim": reason, "date": today, "source": "user (dashboard override)"})
                    entry["status"] = new_status
                    # `user_stated` is a real, distinct evidence tier -- it can move a status
                    # (a human's own judgment is real signal), but it never masquerades as a
                    # primary/secondary source check.
                    entry["verified"] = "user_stated"
                    entry["verified_against"] = "user override via dashboard"
                    entry["verified_on"] = today
                    thesis_map[ticker] = entry
                    state["thesis"] = thesis_map
                    state_dirty = True
                    record_observation(args.base_dir, "dashboard.decision.thesis",
                                       {"ticker": ticker, "decision": decision, "reason": reason,
                                        "new_status": new_status}, today=today, write=True)
                    reconciled.append({"surface": surface, "element_id": element_id, "decision": decision})
                else:
                    skipped.append({"surface": surface, "element_id": element_id, "why": f"unknown decision {decision!r}"})

            elif surface == "catalyst":
                if decision != "priced_in":
                    skipped.append({"surface": surface, "element_id": element_id, "why": f"unknown decision {decision!r}"})
                    continue
                headline, cat_date = d.get("headline"), d.get("date")
                state.setdefault("catalyst_suppressed", []).append(
                    {"headline": headline, "date": cat_date, "suppressed_on": today, "reason": reason})
                state_dirty = True
                reconciled.append({"surface": surface, "element_id": element_id, "decision": decision})
                # no learning observation -- decluttering, not a preference signal

            else:
                skipped.append({"surface": surface, "element_id": element_id, "why": f"unknown surface {surface!r}"})
        except Exception as e:
            props[:] = _snap[0]
            state.clear()
            state.update(_snap[1])
            proposals_dirty, state_dirty = _snap[2], _snap[3]
            errors.append({"surface": surface, "element_id": element_id, "error": str(e),
                           "rolled_back": True})

    try:
        if proposals_dirty:
            proposals_store["proposals"] = props
            safe_write(p_path, proposals_store)
    # Stamp every sync attempt, decisions or not -- this is what lets the orchestrator gate
    # §1.7's expensive WebFetch to at most once/day on quick runs (added 2026-09-14) instead of
    # fetching the full live dashboard page on every single sweep to check for a click that,
    # historically, is present on roughly 1 run in 25.
        # Only a CLEAN sync is stamped: a decision that errored stays in the live page, and an
        # unstamped sync is what makes the next run fetch and retry it.
        if not errors:
            state["dashboard_last_synced_ts"] = str(resolve_today(args.today))
            state_dirty = True
        if state_dirty:
            safe_write(s_path, state)
    finally:
        _lock.__exit__(None, None, None)
    # learning.json observations and the learning_param approve write themselves individually
    # above (record_observation/user_force_approve both write=True) -- each is a single small
    # append, and decision volume per run is small enough that per-decision writes cost nothing
    # worth batching for.

    emit({"decisions_found": len(decisions), "reconciled": reconciled, "skipped": skipped,
          "errors": errors, "ok": not errors,
          "proposals_written": proposals_dirty, "state_written": state_dirty})


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    for name in ("book", "journal", "attribution", "drift", "risk", "rotation", "derisk",
                 "triggers", "buckets", "ladder"):
        sp = sub.add_parser(name)
        sp.add_argument("--base-dir", default=DEFAULT_BASE)
        sp.add_argument("--run-dir", required=True, help="this run's directory containing holdings.json")
        if name == "book":
            sp.add_argument("--lots", default=None)
        if name in ("journal", "derisk", "triggers", "buckets", "ladder"):
            sp.add_argument("--today", default=None)
        if name == "journal":
            sp.add_argument("--prices-json", default=None,
                            help='optional {"TICKER":price_usd} for tickers with an open '
                                 '(unscored) journal entry whose ticker is no longer held -- '
                                 'without this, an exited ticker can never price and stays '
                                 'verdict:"open" forever (survivorship bias). Omit for the '
                                 'normal pipeline call; supply on a separate pass once tickers '
                                 'needing a price are known (same probe-with-{} idiom as score/stops).')

    sp = sub.add_parser("build-holdings",
                        help="build holdings.json mechanically from a raw networth_holdings dump "
                             "-- see cmd_build_holdings' own docstring for why this replaced "
                             "hand-written per-run Python")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--run-dir", required=True)
    sp.add_argument("--snapshot-json", required=True,
                    help="raw networth_holdings(US_STOCK) result, parsed JSON")
    sp.add_argument("--live-quotes-json", default=None,
                    help='optional {"TICKER":price} or {"TICKER":{"price":..,"changePct":..}}')
    sp.add_argument("--usdinr", type=float, required=True)
    sp.add_argument("--wallet-usd", type=float, default=0.0)
    sp.add_argument("--aggregate-usd", type=float, default=None,
                    help="the snapshot's own asset_summary.total_value_usd, kept separate from "
                         "the row sum so cmd_book's G3 divergence check has real teeth")
    sp.add_argument("--market-session", default=None,
                    help="optional: `session-gate --write-holdings` fills market_session and the gate afterwards")
    sp.add_argument("--gate-classification", default=None)
    sp.add_argument("--gate-reason", default=None)
    sp.add_argument("--macro-json", default=None)
    sp.add_argument("--benchmarks-json", default=None)
    sp.add_argument("--ts", default=None)

    sp = sub.add_parser("sentiment")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--market-inputs", required=True)

    # No --run-dir: this checks policy.json's internal consistency only, so it can be run
    # standalone (e.g. right after editing the policy) without a live run directory.
    sp = sub.add_parser("validate")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)

    sp = sub.add_parser("report", help="write the dated daily or weekly report to reports/")
    sp.add_argument("--kind", choices=("daily", "weekly"), required=True)
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--run-dir", default=None)
    sp.add_argument("--today", default=None)

    sp = sub.add_parser("runs",
                        help="expected-vs-actual scheduled runs -- a run is evidenced by a run dir PLUS a ledger row, never by session metadata")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--days", type=int, default=10)
    sp.add_argument("--today", default=None)
    sp.add_argument("--declare-outage", default=None, metavar="FROM:TO",
                    help="record a period the desk could not have run for an external reason "
                         "(host unavailable, account blocked, machine off). Requires --reason. "
                         "The days stay visible in the report; they stop counting as defects.")
    sp.add_argument("--reason", default=None, help="why the desk could not run; required with --declare-outage")

    sp = sub.add_parser("freshness",
                        help="age every artefact in smith_core.FRESHNESS: fresh|stale|dark|unstamped|missing")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--run-dir", default=None, help="if given, also writes compute_freshness.json there")
    sp.add_argument("--today", default=None)

    sp = sub.add_parser("proposals")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--run-dir", required=True, help="this run's directory containing compute_drift.json and holdings.json")
    sp.add_argument("--today", default=None, help="reference date for expiry (YYYY-MM-DD); default today")

    sp = sub.add_parser("dismiss")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--id", required=True, help="stable proposal id, e.g. P-014")
    sp.add_argument("--reason", default=None, help="optional free-text note on why it was dismissed")
    sp.add_argument("--by", choices=("user", "desk"), default="user",
                    help="who dismissed it. 'user' (default) is a revealed preference, excluded "
                         "from the scorecard as a user override. 'desk' means the orchestrator "
                         "withdrew its OWN proposal -- not a user preference, and counted "
                         "separately as a strategist miss rather than hidden.")

    sp = sub.add_parser("add-proposal", help="the only sanctioned way to append new proposals -- builds `action` from ticker+direction so it can't be a bare direction word")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--proposals-json", required=True, help="path to a JSON array of proposal specs (see cmd_add_proposal docstring)")
    sp.add_argument("--run-dir", default=None, help="check price_at_proposal / SMH anchor against this run's quotes (replaced when >3%% off)")
    sp.add_argument("--today", default=None)

    sp = sub.add_parser("append-ledger", help="the only sanctioned way to append a ledger.csv row -- short summary in the CSV, full narrative in a separate briefing file")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--ts", default=None, help="default: now, from the script clock (never hand-type it)")
    sp.add_argument("--mode", required=True, choices=["quick", "deep"])
    sp.add_argument("--value-usd", required=True, type=float)
    sp.add_argument("--usdinr", required=True, type=float)
    sp.add_argument("--wallet-usd", required=True, type=float)
    sp.add_argument("--spx", required=True, type=float)
    sp.add_argument("--ndx", required=True, type=float)
    sp.add_argument("--smh", type=float, default=None)
    sp.add_argument("--smh-asof", default=None)
    sp.add_argument("--est-net-flows-usd", default=None)
    sp.add_argument("--external-flow-usd", default=None)
    sp.add_argument("--value-trust", default="ok")
    sp.add_argument("--summary", required=True, help=f"short one-liner, max {300} chars -- full narrative goes in --briefing-file")
    sp.add_argument("--briefing-file", default=None, help="path to the full run narrative (e.g. runs/<ts>/briefing.md); the ledger notes cell stores a pointer to it, not the text itself")

    sp = sub.add_parser("trade-rationale", help="attach a reason to trades ledger-apply already recorded -- the only way a reason reaches trades.json")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--ticker", default=None)
    sp.add_argument("--date", default=None, help="trade date YYYY-MM-DD")
    sp.add_argument("--side", default=None, choices=["buy", "sell"])
    sp.add_argument("--message-id", default=None)
    sp.add_argument("--reason", required=True)
    sp.add_argument("--notes", default=None)
    sp.add_argument("--overwrite", action="store_true", help="replace a reason that is already captured")

    sp = sub.add_parser("dispatch-plan", help="which sub-agents run this sweep, in which wave, and why")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--run-dir", required=True)
    sp.add_argument("--mode", choices=("quick", "deep"), required=True)
    sp.add_argument("--ask", action="append", default=[],
                    choices=("full", "thesis", "watchlist", "why", "quality", "cycle"),
                    help="an explicit user ask that forces an agent (repeatable)")
    sp.add_argument("--today", default=None)

    sp = sub.add_parser("triggers-diff", help="priced-refresh materiality gate vs the previous run")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--run-dir", required=True)
    sp.add_argument("--prev", default=None, help="default: newest other run dir with compute_triggers.json")

    sp = sub.add_parser("postflight", help="PERSIST as code: --phase commit (state/journals/ledger/reports) then --phase close (compact/prune/git/lock)")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--run-dir", required=True)
    sp.add_argument("--phase", choices=("commit", "close"), required=True)
    sp.add_argument("--mode", choices=("quick", "deep", "priced", "refresher", "holiday"), required=True)
    sp.add_argument("--today", default=None)
    sp.add_argument("--run-id", default=None)
    sp.add_argument("--summary", default="", help="<=300-char ledger one-liner")
    sp.add_argument("--briefing-file", default=None)
    sp.add_argument("--external-flow-usd", default=None)
    sp.add_argument("--no-ledger", action="store_true")
    sp.add_argument("--no-decisions", action="store_true")
    sp.add_argument("--no-git", action="store_true")
    sp.add_argument("--keep-runs", type=int, default=10)

    sp = sub.add_parser("indicators", help="ATR20/RSI14/ret_5d/rel strength/52w/beta caches from bars.json (script-owned)")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--run-dir", required=True)
    sp.add_argument("--bars", default=None, help="default: <run-dir>/bars.json")
    sp.add_argument("--today", default=None)

    sp = sub.add_parser("normalize-bars", help="MCP fallback: convert saved get_stock_history output into bars.json")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--run-dir", required=True)
    sp.add_argument("--mcp-files", nargs="+", required=True)
    sp.add_argument("--out", default=None)

    sp = sub.add_parser("session-gate", help="market_session (DST/holidays/early close) + GATE v2, computed")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--run-dir", required=True)
    sp.add_argument("--now", default=None, help="ISO timestamp override (tests/replays)")
    sp.add_argument("--write-holdings", action="store_true")

    sp = sub.add_parser("lock", help="script-owned run lock: acquire|heartbeat|release|status")
    sp.add_argument("action", choices=("acquire", "heartbeat", "release", "status"))
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--run-id", default=None)
    sp.add_argument("--run-dir", default=None)
    sp.add_argument("--mode", default=None)
    sp.add_argument("--force", action="store_true")

    sp = sub.add_parser("commit-state", help="apply this run's staged state patch to state.json")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--run-dir", required=True)
    sp.add_argument("--persist-safe", choices=("auto", "true", "false"), default="auto",
                    help="auto = read compute_book.json's persist_safe")

    sp = sub.add_parser("health", help="missed runs, stale lock, uncommitted state, mirror drift")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--notify", action="store_true", help="macOS notification when not ok")

    sp = sub.add_parser("memory-summary", help="~5KB digest of the memory of record")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)

    sp = sub.add_parser("preflight", help="lock + health + validate + freshness + lessons + memory summary")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--mode", required=True)
    sp.add_argument("--run-id", default=None)
    sp.add_argument("--run-dir", default=None)
    sp.add_argument("--today", default=None)

    sp = sub.add_parser("abort", help="end a run that cannot proceed: discard staged state, stub report, release lock")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--run-dir", default=None)
    sp.add_argument("--run-id", default=None)
    sp.add_argument("--reason", required=True)
    sp.add_argument("--kind", choices=("connector", "host", "data", "other"), default="other")
    sp.add_argument("--today", default=None)

    sp = sub.add_parser("merge-tails", help="fold Stage-1 sub-agent out_<agent>.json files into state.json per the declarative MERGE_RULES table")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--run-dir", required=True)
    sp.add_argument("--today", default=None)
    sp.add_argument("--agents", default=None, help="comma-separated agent names to merge (default: every agent MERGE_RULES knows how to merge)")
    sp.add_argument("--revision", action="store_true",
                    help="re-merge after a desk-round REVISION (smith_comms): skips the side "
                         "effects that must happen once per run -- shifting stress_table_prev, "
                         "appending a ladder's track-record score, recording its learning "
                         "observation")

    sp = sub.add_parser("stops")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--prices-json", required=True, help='{"TICKER":price_usd} for tickers with an unscored stop')
    sp.add_argument("--today", default=None)
    sp.add_argument("--out", default=None, help="default: base_dir/stops_analysis.json")
    sp.add_argument("--force", action="store_true",
                    help="allow overwriting stops_analysis.json with FEWER scored stops than it "
                         "already holds (normally refused -- see the regression guard in cmd_stops)")

    sp = sub.add_parser("lots", help="rebuild lots.json from trades.json by FIFO, honouring corporate actions")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--holdings", default=None,
                    help="a run's holdings.json, to reconcile lot sums against broker quantities")
    sp.add_argument("--write", action="store_true", help="write lots.json (default: dry run)")
    sp.add_argument("--write-if-clean", action="store_true",
                    help="write lots.json ONLY if the rebuild reconciles cleanly against the "
                         "--holdings broker quantities (no mismatches, orphans or phantom "
                         "shorts). Requires --holdings. This is what the pipeline uses.")

    sp = sub.add_parser("maxpain", help="max-pain + put/call OI ratio from a saved options chain (G18)")
    sp.add_argument("--chain", required=True, help="JSON chain file: {underlyingPrice, data:{expiry:{calls,puts}}}")
    sp.add_argument("--symbol", default=None)

    sp = sub.add_parser("merge-prices",
                        help="merge several fetched price JSON files (flat or raw yfinance "
                             "shape) into the one flat {TICKER:price} map score/stops/"
                             "build-holdings expect -- replaces hand-written merge Python")
    sp.add_argument("--inputs", required=True, nargs="+",
                    help="one or more JSON file paths, space-separated; last wins on a key collision")
    sp.add_argument("--out", required=True)

    sp = sub.add_parser("slices", help="render per-agent data embeds from the declared table")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--run-dir", required=True)
    sp.add_argument("--mode", default="deep")
    sp.add_argument("--today", default=None)
    sp.add_argument("--agents", default=None, help="comma-separated; default = all")

    sp = sub.add_parser("draft-specs", help="script-draft the strategist's proposal specs from compute_triggers.json's sized live candidates")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--run-dir", required=True)

    sp = sub.add_parser("gaps", help="look up known_gaps across BOTH state.json and the archive")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--id", default=None, help="exact gap id, e.g. G44")
    sp.add_argument("--query", default=None,
                    help="free-text precedent search (BM25-ranked, not substring) across both files")
    sp.add_argument("--top", type=int, default=8, help="max ranked results for --query (default 8)")
    sp.add_argument("--open-only", action="store_true")

    sp = sub.add_parser("compact", help="enforce RETENTION: archive resolved history out of the hot files")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--holdings", default=None, help="a run's holdings.json, to know which tickers are live")
    sp.add_argument("--today", default=None)
    sp.add_argument("--write", action="store_true", help="apply (default: dry run)")
    sp.add_argument("--mode", choices=("cheap", "full"), default="full",
                    help="cheap: gaps, flags, data_quality, data_cache (every run); full: + proposals, journals, trade notes (deep runs)")

    sp = sub.add_parser("universe",
                        help="the candidate set: held + ever-held + peers + watchlist + discovery")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--run-dir", default=None, help="uses holdings.json for T1; falls back to lots.json")
    sp.add_argument("--today", default=None)

    sp = sub.add_parser("history", help="authoritative was-this-ever-held lookup for a ticker (G72)")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--ticker", required=True, help="one ticker, or a comma-separated list")

    sp = sub.add_parser("pipeline", help="run all per-run computes in dependency order, failing loudly")
    sp.add_argument("--stages", default=None, help="comma-separated subset of stages to run")
    sp.add_argument("--from", dest="from_stage", default=None,
                    help="resume from this stage (e.g. after ledger-apply: --from lots)")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--run-dir", required=True)
    sp.add_argument("--today", default=None)
    sp.add_argument("--lots", default=None)

    sp = sub.add_parser("score", help="score past proposals on price outcome (30d/90d)")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--prices-json", required=True,
                    help='{"TICKER":price_usd} for tickers with a closed, unscored proposal. '
                         'Run with /dev/null first to have the tool NAME which tickers it needs.')
    sp.add_argument("--today", default=None)
    sp.add_argument("--run-dir", default=None,
                    help="optional: read the SMH benchmark price from RUN_DIR/market_inputs.json "
                         "when --prices-json lacks it, so alpha grading is reachable")
    sp.add_argument("--rebase-scorecard", action="store_true",
                    help="one-time: permit the scored_count to shrink when a definitional fix "
                         "explains it (superseded no longer scored, HOLD unscoreable); a larger "
                         "drop is still refused as the empty-prices probe")
    sp.add_argument("--dry-run", action="store_true",
                    help="compute and print the scorecard without writing proposals.json")

    sp = sub.add_parser("score-shadow-journal",
                        help="score trigger_journal.json or derisk_journal.json at 7d/30d")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--file", required=True, choices=["trigger_journal.json", "derisk_journal.json"])
    sp.add_argument("--prices-json", default=None,
                    help='{"TICKER":price_usd}. Omit or probe with an empty {} first to see '
                         'which tickers are needed.')
    sp.add_argument("--today", default=None)
    sp.add_argument("--dry-run", action="store_true")

    sp = sub.add_parser("learn-status", help="report every learning.json parameter's state/n")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)

    sp = sub.add_parser("learn-lessons", help="list recorded lessons (corrections/dead ends)")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--kind", default=None, choices=["correction", "calibration", "dead_end"])

    sp = sub.add_parser("learn-add-lesson", help="record a lesson into learning.json")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--kind", required=True, choices=["correction", "calibration", "dead_end"])
    sp.add_argument("--text", required=True)
    sp.add_argument("--evidence", default=None)
    sp.add_argument("--source-run", default=None)
    sp.add_argument("--supersedes", default=None, help="lesson id (L-###) this one corrects")
    sp.add_argument("--today", default=None)

    sp = sub.add_parser("ledger-parse",
                        help="deterministically parse INDmoney BUY/SELL confirmations from "
                             "search_threads output; fetch bodies ONLY for what it lists")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--threads-file", required=True,
                    help="raw search_threads JSON (a dict, or a list of pages)")
    sp.add_argument("--bodies-file", default=None,
                    help="optional get_thread results for rows a prior run put in needs_body; "
                         "bodies win over snippets on conflict")
    sp.add_argument("--today", default=None)

    sp = sub.add_parser("crosscheck",
                        help="detect conflicts BETWEEN this run's sub-agent outputs; run AFTER "
                             "WAVE 2 (interpreters) has merged and BEFORE WAVE 3 (strategist) "
                             "dispatches -- this help contradicted cmd_crosscheck's own "
                             "docstring until 2026-09-08; the docstring is right, and explains "
                             "why the earlier timing left 4 of 5 rules structurally inert")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--run-dir", required=True)
    sp.add_argument("--today", default=None)

    sp = sub.add_parser("bookcalc",
                        help="dividends/ex-dates, LTCG window and risk-weighted concentration "
                             "-- the arithmetic half of smith-book")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--run-dir", required=True)
    sp.add_argument("--summary-file", default=None,
                    help="yfinance get_stock_summary payload; the SAME call that populates "
                         "data_cache.wk52, so it is free on a run that refreshes wk52")
    sp.add_argument("--ex-window-days", type=int, default=30)
    sp.add_argument("--today", default=None)

    sp = sub.add_parser("taxcalc",
                        help="FIFO-vs-HIFO lot sequencing for open trims + loss-harvest "
                             "candidates -- the arithmetic half of smith-tax")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--run-dir", required=True)
    sp.add_argument("--material-usd", type=float, default=5.0,
                    help="tax delta below which FIFO-vs-HIFO is not worth complicating execution")
    sp.add_argument("--today", default=None)

    sp = sub.add_parser("perf",
                        help="REALIZED return: rebuilds the book from trades.json + daily closes "
                             "and reports TWR vs SMH plus the dollar cost of selection. This is "
                             "the survivorship-free number rolling_constant_mix cannot produce.")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--run-dir", default=None, help="writes compute_perf.json here when given")
    sp.add_argument("--bars", default=None, help="default: <base-dir>/perf_bars.json")
    sp.add_argument("--bench", default=smith_perf.BENCH)
    sp.add_argument("--since", default=None, help="YYYY-MM-DD; trim the chain's start")
    sp.add_argument("--until", default=None)
    sp.add_argument("--min-book", type=float, default=smith_perf.MIN_BOOK_USD,
                    help="exclude sessions whose PRIOR book is below this (denominator stability)")
    sp.add_argument("--material-book", type=float, default=10000.0,
                    help="second chain restricted to sessions at or above this book value")
    sp.add_argument("--full", action="store_true", help="include the per-month table")
    sp.add_argument("--today", default=None)

    sp = sub.add_parser("comms-route",
                        help="one DESK ROUND: harvest asks/tells/answers from every agent tail, "
                             "open debates from crosscheck conflicts, apply revisions, and say who "
                             "must be resumed or newly dispatched. Repeat until converged.")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--run-dir", required=True)
    sp.add_argument("--today", default=None)
    sp.add_argument("--max-rounds", type=int, default=6)
    sp.add_argument("--include-low", action="store_true",
                    help="also debate low-severity crosscheck findings")

    sp = sub.add_parser("validity",
                        help="re-check every OPEN proposal against today: trigger still firing, "
                             "alpha since proposed, your contradicting trades, the strategist's "
                             "retire list, thesis direction, desk debates. Advisory -- never "
                             "edits or dismisses a proposal.")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--run-dir", default=None)
    sp.add_argument("--today", default=None)

    sp = sub.add_parser("comms-status", help="the desk conversation digest for this run")
    sp.add_argument("--run-dir", required=True)
    sp.add_argument("--full", action="store_true")

    sp = sub.add_parser("correlation",
                        help="realised correlation: effective number of bets, whether the "
                             "diversification credit on the stop sum is earned, and whether "
                             "policy's named clusters are real risk buckets or just labels")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--run-dir", required=True)
    sp.add_argument("--lookback", type=int, default=250)
    sp.add_argument("--min-obs", type=int, default=40)
    sp.add_argument("--top", type=int, default=12)
    sp.add_argument("--full", action="store_true", help="include the full matrix")
    sp.add_argument("--today", default=None)

    sp = sub.add_parser("valuation",
                        help="reverse-DCF, ROIC-vs-WACC and forensic (Beneish/Altman) checks "
                             "from agent-fetched FMP statement data")
    sp.add_argument("--run-dir", required=True)
    sp.add_argument("--statements-json", required=True,
                    help="ticker-keyed JSON; see smith_valuation.py's module docstring for shape")
    sp.add_argument("--today", default=None)
    sp.add_argument("--terminal-growth-pct", type=float, default=smith_valuation.TERMINAL_GROWTH_PCT_DEFAULT)
    sp.add_argument("--forecast-years", type=int, default=smith_valuation.FORECAST_YEARS_DEFAULT)
    sp.add_argument("--stretch-gap-pp", type=float, default=smith_valuation.REVERSE_DCF_STRETCH_GAP_PP_DEFAULT)
    sp.add_argument("--market-risk-premium-pct", type=float, default=smith_valuation.MARKET_RISK_PREMIUM_PCT_DEFAULT)

    sp = sub.add_parser("ledger-apply",
                        help="append parsed confirmations to trades.json (idempotent on "
                             "message_id); dry run unless --write")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--parsed-file", required=True,
                    help="ledger-parse output, or a bare list of its `parsed` rows")
    sp.add_argument("--write", action="store_true")

    sp = sub.add_parser("usage-report",
                        help="log AND audit EVERY dispatched agent's usage in one call -- the "
                             "batched replacement for a per-agent usage-log/usage-audit loop")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--run-id", required=True)
    sp.add_argument("--mode", required=True, choices=["quick", "deep"])
    sp.add_argument("--usage-file", required=True,
                    help='JSON list of {"agent","tokens","tool_calls","duration_s"} -- one entry '
                         'per dispatched agent. Raises on a malformed row rather than skipping '
                         'it: a silently partial cost figure is worse than none.')
    sp.add_argument("--today", default=None)

    sp = sub.add_parser("usage-audit",
                        help="flag this run's agent usage as an outlier vs its own trailing "
                             "history or stated budget, and auto-log a correction lesson if so")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--agent", required=True)
    sp.add_argument("--run-id", required=True)
    sp.add_argument("--tokens", required=True, type=int)
    sp.add_argument("--tool-calls", default=None, type=int)
    sp.add_argument("--duration-s", default=None, type=float)
    sp.add_argument("--today", default=None)

    sp = sub.add_parser("learn-revealed-preference",
                        help="period-keyed acted/dismissed/ignored profile + engagement rate")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)

    sp = sub.add_parser("learn-priority-params",
                        help="list the priority scorer's named literals (Phase 2, not yet wired)")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)

    sp = sub.add_parser("learn-stop-calibration",
                        help="per-volatility-tier read on stop distance at a fixed 30-session "
                             "horizon -- escalation only, never auto-applies")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--record", action="store_true",
                    help="feed each scored mid-tier stop into learning.json and promote the "
                         "stops.atr_multiple.mid parameter's state (idempotent per stop)")
    sp.add_argument("--run-dir", default=None)
    sp.add_argument("--today", default=None)

    sp = sub.add_parser("sync-decisions",
                        help="reconcile the interactive dashboard's accumulated button clicks")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    src = sp.add_mutually_exclusive_group(required=True)
    src.add_argument("--records-file",
                     help="JSON array from Artifact action:read_db against the dashboard's "
                          "decisions collection, saved to disk (the current path, added "
                          "2026-09-16 -- replaces the whole-page WebFetch)")
    src.add_argument("--html-file", help="LEGACY: fetched dashboard HTML (WebFetch output saved "
                                         "to disk) from before decisions moved to the db capability")
    sp.add_argument("--today", default=None)

    args = p.parse_args()
    # Every run-scoped command refreshes the heartbeat of the lock its run holds. Best effort:
    # a heartbeat failure must never fail the command it rides on.
    if getattr(args, "run_dir", None) and args.cmd not in ("lock", "preflight", "abort", "postflight"):
        try:
            import smith_state
            smith_state.lock_heartbeat(getattr(args, "base_dir", DEFAULT_BASE), run_dir=args.run_dir)
        except Exception:  # noqa: BLE001
            pass
    try:
        {"build-holdings": cmd_build_holdings, "merge-prices": cmd_merge_prices,
         "book": cmd_book, "journal": cmd_journal, "attribution": cmd_attribution,
         "drift": cmd_drift, "risk": cmd_risk, "rotation": cmd_rotation, "derisk": cmd_derisk,
         "triggers": cmd_triggers, "buckets": cmd_buckets, "ladder": cmd_ladder,
         "draft-specs": cmd_draft_specs,
         "score": cmd_score,
         "pipeline": cmd_pipeline, "lots": cmd_lots,
         "history": cmd_history, "universe": cmd_universe, "maxpain": cmd_maxpain, "compact": cmd_compact, "gaps": cmd_gaps, "slices": cmd_slices,
         "sentiment": cmd_sentiment, "validate": cmd_validate, "proposals": cmd_proposals,
         "freshness": cmd_freshness, "report": cmd_report, "runs": cmd_runs,
         "dismiss": cmd_dismiss, "add-proposal": cmd_add_proposal,
         "append-ledger": cmd_append_ledger, "merge-tails": cmd_merge_tails, "stops": cmd_stops,
         "score-shadow-journal": cmd_score_shadow_journal, "learn-status": cmd_learn_status,
         "learn-lessons": cmd_learn_lessons, "learn-add-lesson": cmd_learn_add_lesson,
         "learn-revealed-preference": cmd_learn_revealed_preference,
         "learn-priority-params": cmd_learn_priority_params,
         "learn-stop-calibration": cmd_learn_stop_calibration,
         "usage-audit": cmd_usage_audit,
         "usage-report": cmd_usage_report, "ledger-parse": cmd_ledger_parse, "ledger-apply": cmd_ledger_apply,
         "crosscheck": cmd_crosscheck, "bookcalc": cmd_bookcalc, "taxcalc": cmd_taxcalc,
         "valuation": cmd_valuation, "perf": cmd_perf, "correlation": cmd_correlation, "comms-route": cmd_comms_route, "validity": cmd_validity, "comms-status": cmd_comms_status,
         "sync-decisions": cmd_sync_decisions,
         "trade-rationale": cmd_trade_rationale, "indicators": cmd_indicators,
         "dispatch-plan": cmd_dispatch_plan, "triggers-diff": cmd_triggers_diff, "postflight": cmd_postflight,
         "normalize-bars": cmd_normalize_bars, "session-gate": cmd_session_gate, "lock": cmd_lock, "commit-state": cmd_commit_state, "health": cmd_health,
         "memory-summary": cmd_memory_summary, "preflight": cmd_preflight, "abort": cmd_abort}[args.cmd](args)
    except Exception as e:  # noqa: BLE001 -- deliberate: any failure degrades gracefully
        fail(f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
