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
  score       --base-dir DIR --prices-json P.json [--today ...] [--dry-run]
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
from smith_core import *  # noqa: F401,F403
from smith_core import load_json, emit, fail, clamp
from smith_ledger import cmd_lots, cmd_history
from smith_memory import cmd_compact, cmd_gaps, cmd_validate, cmd_slices, validate_policy
from smith_lifecycle import cmd_proposals, cmd_score, cmd_stops, cmd_dismiss
# explicit: `from x import *` does NOT export underscore-prefixed names
from smith_core import _prior_run_prices
from smith_ledger import _avg_cost_from_lots, _months_between
from smith_lifecycle import _proposal_parse_date



                          # (see cmd_score: a corrupt $305.87 TSM anchor produced a phantom -39%)














# ---------------------------------------------------------------------------
# book
# ---------------------------------------------------------------------------
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
    ltcg_boundary_months = load_json(os.path.join(args.base_dir, "policy.json"), default={}).get("ltcg_boundary_months", 24)
    today = date.today()
    lots = dict(smith_risk.data_entries(lots, value_type=list))   # one canonical filter (2026-08-16)
    if lots:
        for ticker, lot_list in lots.items():
            for lot in lot_list:
                try:
                    lot_date = datetime.strptime(lot["date"], "%Y-%m-%d").date()
                except (KeyError, ValueError, TypeError):
                    continue
                months_held = (today.year - lot_date.year) * 12 + (today.month - lot_date.month)
                months_to_ltcg = ltcg_boundary_months - months_held
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

        r = smith_risk.stop_and_cap(atr_pct, p.get("price_usd"), p.get("qty"), total_book_usd, policy)
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

    today = datetime.strptime(args.today, "%Y-%m-%d").date() if args.today else date.today()

    updates = []
    bucket_scores = {}  # bucket -> [worked/failed/neutral bools at 30d]
    name_bucket_scores = {}  # (ticker,bucket) -> list
    bucket_scores_7d = {}  # same, at 7d -- interim read, see bucket_hit_rates_7d below

    for e in journal.get("entries", []):
        try:
            flag_date = datetime.strptime(e["date"], "%Y-%m-%d").date()
        except (KeyError, ValueError):
            continue
        days_old = (today - flag_date).days
        current_price = price_by_ticker.get(e["ticker"])
        out = {"date": e["date"], "ticker": e["ticker"], "bucket": e["bucket"],
               "days_old": days_old, "outcome_7d_pct": None, "outcome_30d_pct": None,
               "verdict": "open"}
        if current_price is None or not e.get("price_at_flag"):
            out["verdict"] = "open"
            updates.append(out)
            continue
        pct_move = round((current_price - e["price_at_flag"]) / e["price_at_flag"] * 100, 3)
        if days_old >= 7:
            out["outcome_7d_pct"] = pct_move
            # 7d interim verdict (added 2026-08-06, rotation-proposal feature review): same
            # direction-aware signed-move logic as the 30d verdict below, just usable 23 days
            # sooner. Kept in a SEPARATE dict (bucket_scores_7d, never bucket_scores) so it can
            # never contaminate the validated 30d hit rate -- proposal scoring may read the 7d
            # number, but it must always be visibly labelled interim/lower-confidence, never
            # presented as the same thing as a matured 30d verdict.
            direction_7d = BUCKET_DIRECTION.get(e["bucket"])
            if direction_7d is not None:
                signed_7d = pct_move if direction_7d == "up" else -pct_move
                v7 = ("worked" if signed_7d > VERDICT_THRESHOLD_PCT
                      else "failed" if signed_7d < -VERDICT_THRESHOLD_PCT else "neutral")
                bucket_scores_7d.setdefault(e["bucket"], []).append(v7)
        if days_old >= 30:
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
            bucket_scores.setdefault(e["bucket"], []).append(out["verdict"])
            name_bucket_scores.setdefault((e["ticker"], e["bucket"]), []).append(out["verdict"])
        updates.append(out)

    bucket_hit_rates = {}
    for bucket, verdicts in bucket_scores.items():
        scored = [v for v in verdicts if v in ("worked", "failed")]
        if scored:
            bucket_hit_rates[bucket] = {
                "n": len(scored),
                "hit_rate_pct": round(sum(1 for v in scored if v == "worked") / len(scored) * 100, 1),
            }

    bucket_hit_rates_7d = {}
    for bucket, verdicts in bucket_scores_7d.items():
        scored = [v for v in verdicts if v in ("worked", "failed")]
        if len(scored) >= 3:  # same n>=3 floor as name_bucket_grades below -- don't grade on n=1
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

    name_bucket_grades = {}
    for (ticker, bucket), verdicts in name_bucket_scores.items():
        scored = [v for v in verdicts if v in ("worked", "failed")]
        name_bucket_grades.setdefault(ticker, {})
        if len(scored) >= 3:
            hr = sum(1 for v in scored if v == "worked") / len(scored) * 100
            name_bucket_grades[ticker][bucket] = grade(hr)
        else:
            name_bucket_grades[ticker][bucket] = "ungraded"

    dq = [] if price_by_ticker else ["no current prices available -- all entries left open"]

    # Flag entries in the 30-day window (approaching scoring threshold, 1.5: 2026-07-26)
    today = date.today()
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

    if os.path.exists(ledger_path):
        with open(ledger_path) as f:
            lines = [l.strip() for l in f if l.strip()]
        if len(lines) > 1:
            header = lines[0].split(",")
            rows_ledger = [dict(zip(header, l.split(","))) for l in lines[1:]]
            result["ledger_rows_available"] = len(rows_ledger)
            result["rolling"] = {"1m": None, "3m": None, "6m": None, "12m": None,
                                  "note": f"only {len(rows_ledger)} ledger row(s) -- rolling windows need more history"}
        else:
            result["rolling"] = {"note": "ledger has no rows yet"}
    else:
        result["rolling"] = {"note": "ledger.csv not found"}

    emit(result)




























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
    for cluster, actual in cluster_actual.items():
        if cluster not in cluster_targets:
            cluster_table.append({"cluster": cluster, "actual_pct": round(actual, 3),
                                   "target_pct": None, "band_pct": None, "drift_pt": None,
                                   "breach": False, "note": "no policy target for this cluster"})

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
                today_d = datetime.strptime(args.today, "%Y-%m-%d").date() if getattr(args, "today", None) else date.today()
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
    risk = load_json(os.path.join(args.run_dir, "compute_risk.json"), default=None)
    polarity_table_json = {k: sorted(v) for k, v in smith_risk.SIGNAL_POLARITY.items()}

    if risk is None:
        emit({"tickers": {}, "polarity_table": polarity_table_json,
              "data_quality": ["compute_risk.json not found in run-dir -- run `risk` before `rotation`"]})
        return

    signal_history = state.get("signal_history", {})
    thesis = state.get("thesis", {})
    risk_by_ticker = {r["ticker"]: r for r in risk.get("positions", [])}

    tickers = {}
    for ticker, r in risk_by_ticker.items():
        # ONE canonical reader for both entry shapes -- see smith_risk.thesis_status (2026-08-16).
        thesis_status = smith_risk.thesis_status(thesis.get(ticker))
        polarity = smith_risk.classify_signal_polarity(signal_history.get(ticker, []))
        over_cap = bool(r.get("over_cap"))
        bucket = smith_risk.rotation_bucket(over_cap, thesis_status, polarity["net"])
        tickers[ticker] = {
            "cluster": r.get("cluster"), "thesis_status": thesis_status,
            "net_signal": polarity["net"], "bullish_buckets": polarity["bullish"],
            "bearish_buckets": polarity["bearish"],
            "headroom_usd": r.get("headroom_usd"), "over_cap": over_cap,
            "cap_multiple": r.get("cap_multiple"), "bucket": bucket,
        }

    emit({"tickers": tickers, "polarity_table": polarity_table_json, "data_quality": []})


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
            "call_oi": call_oi, "put_oi": put_oi,
            "strikes_used": len(strikes), "strike_range": [strikes[0], strikes[-1]],
            "spot_vs_max_pain_pct": (round((spot - best) / best * 100, 2)
                                     if spot and best else None),
            "boundary_artifact": edge,
        }
    emit({"symbol": args.symbol, "underlying_price": spot, "expiries": out,
          "data_quality": dq,
          "note": ("pcr_oi is put/call OPEN INTEREST (positioning), not volume. Max-pain is a "
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
        ("book",        ["holdings.json"],                          lambda d: d.get("value_usd")),
        ("risk",        ["compute_book.json"],                      lambda d: d.get("positions")),
        ("drift",       ["compute_book.json"],                      lambda d: d.get("cluster_table")),
        ("journal",     ["holdings.json"],                          lambda d: True),
        ("attribution", ["holdings.json"],                          lambda d: True),
        ("rotation",    ["compute_risk.json"],                      lambda d: d.get("tickers")),
        ("sentiment",   ["market_inputs.json"],                     lambda d: d.get("score") is not None),
        ("derisk",      ["compute_risk.json", "compute_sentiment.json"], lambda d: d.get("queue")),
        ("triggers",    ["compute_risk.json", "compute_book.json"], lambda d: True),
    ]

    results, failed = [], None
    for name, needs, probe in STAGES:
        missing = [n for n in needs
                   if not os.path.exists(os.path.join(run_dir, n))
                   and not os.path.exists(os.path.join(base, n))]
        if missing:
            results.append({"stage": name, "status": "BLOCKED", "missing_inputs": missing})
            failed = failed or (name, f"required input(s) absent: {', '.join(missing)}")
            break

        cmd = [sys.executable, here, name, "--base-dir", base]
        if name == "sentiment":
            cmd += ["--market-inputs", os.path.join(run_dir, "market_inputs.json")]
        else:
            cmd += ["--run-dir", run_dir]
        if name in ("journal", "derisk", "triggers") and args.today:
            cmd += ["--today", args.today]
        if name == "book" and args.lots:
            cmd += ["--lots", args.lots]

        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            results.append({"stage": name, "status": "FAILED", "exit": proc.returncode,
                            "stderr": (proc.stderr or "")[-400:]})
            failed = (name, f"exited {proc.returncode}")
            break
        try:
            payload = json.loads(proc.stdout)
        except ValueError:
            results.append({"stage": name, "status": "FAILED", "note": "stdout was not valid JSON"})
            failed = (name, "emitted non-JSON stdout")
            break
        if isinstance(payload, dict) and payload.get("error"):
            results.append({"stage": name, "status": "FAILED", "note": payload["error"]})
            failed = (name, payload["error"])
            break
        with open(out(name), "w") as fh:
            json.dump(payload, fh, indent=2)
        # THE CHECK THAT WOULD HAVE CAUGHT 2026-08-15: exit 0 is not success if the payload
        # is hollow. A stage that ran but produced nothing is a failure wearing a green light.
        if not probe(payload):
            results.append({"stage": name, "status": "EMPTY",
                            "note": "ran cleanly but produced an empty result -- treated as a "
                                    "failure, not as 'nothing to report'"})
            failed = (name, "produced an empty result despite exiting 0")
            break
        results.append({"stage": name, "status": "ok"})

    emit({"run_dir": run_dir,
          "stages": results,
          "completed": [r["stage"] for r in results if r["status"] == "ok"],
          "failed_at": failed[0] if failed else None,
          "reason": failed[1] if failed else None,
          "ok": failed is None,
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

    today = date.fromisoformat(args.today) if args.today else date.today()
    ltcg_months = (policy.get("mandate") or {}).get("ltcg_months", LTCG_MONTHS_DEFAULT)
    dust_usd = (policy.get("mandate") or {}).get("dust_position_usd", DUST_USD_DEFAULT)

    rel_cache = state.get("data_cache", {}).get("rel_strength_1m", {}) or {}
    rel_vals = rel_cache.get("values_pp", {}) or {}
    abs_vals = rel_cache.get("values_abs_pct", {}) or {}
    sector_map = state.get("sector_map", {})
    thesis = state.get("thesis", {})

    agg_risk = risk.get("aggregate_open_risk_usd") or 0.0
    positions = risk.get("positions", [])
    dq, missing_rel = [], []

    raw = []
    for p in positions:
        t = p["ticker"]
        mv = p.get("market_value_usd") or 0.0
        open_risk = p.get("position_open_risk_usd")
        cap_x = p.get("cap_multiple")

        # --- fragility -------------------------------------------------
        if open_risk is None or not agg_risk:
            frag_raw, frag_note = None, "no open-risk figure (ATR missing upstream)"
        else:
            risk_share = open_risk / agg_risk * 100.0
            frag_raw = risk_share * max(cap_x or 1.0, 1.0)
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
        if mv < dust_usd:
            friction += 30.0
            fr_reasons.append(f"position below ${dust_usd:g} dust threshold")
        friction = clamp(friction)

        t_status = smith_risk.thesis_status(thesis.get(t))

        raw.append({"ticker": t, "market_value_usd": round(mv, 2),
                    "cluster": sector_map.get(t), "thesis_status": t_status,
                    "cap_multiple": cap_x, "atr20_pct": p.get("atr20_pct"),
                    "stop_price_usd": p.get("stop_price_usd"),
                    "risk_share_pct": round(open_risk / agg_risk * 100.0, 2) if (open_risk and agg_risk) else None,
                    "rel_strength_1m_pp": rel_pp, "abs_return_1m_pct": abs_pct,
                    "_frag_raw": frag_raw, "_stretch_raw": stretch_raw,
                    "friction_score": round(friction, 1),
                    "friction_reasons": fr_reasons, "_frag_note": frag_note})

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
            score = frag * (1.0 + (stretch or 0.0) / 100.0) * (1.0 - r["friction_score"] / 200.0) * urgency
            score = round(score, 1)
        r.pop("_frag_raw"); r.pop("_stretch_raw")
        note = r.pop("_frag_note")
        if note:
            dq.append(f"{r['ticker']}: {note}")
        rows.append({**r, "fragility_score": frag, "stretch_score": stretch, "derisk_score": score})

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




def cmd_triggers(args):
    """Deterministic candidate generation for the five non-ATR proposal triggers.

    This does NOT create proposals -- it hands the strategist typed, pre-screened candidate lists
    so it no longer has to invent non-ATR ideas from narrative judgment. Same compute-first
    contract as every other subcommand: every gate is a number from a compute file or a cache,
    never a prose reading, and a missing input yields an empty list plus a data_quality line
    rather than an estimate.

    vote=="live"   (oversold_reversion, overbought_distribution) may become sized proposals now.
    vote=="shadow" (laggard_rotation, profit_ratchet, scale_out_ladder) are logged with
                   price_at_flag and scored at 7/30d first -- the same "a new signal class earns
                   its vote before it gets one" rule the de-risk queue (2.9c) runs under. The two
                   live triggers are exempted because OVERSOLD BOUNCE already carries a measured
                   record in this book's own journal; the other three are genuinely unmeasured.
    """
    risk = load_json(os.path.join(args.run_dir, "compute_risk.json"))
    book = load_json(os.path.join(args.run_dir, "compute_book.json"))
    drift = load_json(os.path.join(args.run_dir, "compute_drift.json"), default={})
    rotation = load_json(os.path.join(args.run_dir, "compute_rotation.json"), default={})
    state = load_json(os.path.join(args.base_dir, "state.json"), default={})
    lots = load_json(os.path.join(args.base_dir, "lots.json"), default={})
    # Cluster state, for the overbought cluster-tension check further down. Both default to empty so
    # a missing/failed drift step degrades to "no tension detected" rather than raising -- consistent
    # with how rsi_usable / rel_usable degrade elsewhere in this function.
    cluster_rows = {c.get("cluster"): c for c in (drift.get("cluster_table") or [])}
    sector_map = state.get("sector_map", {}) or {}

    today = date.fromisoformat(args.today) if args.today else date.today()
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
    if not rel_usable:
        dq.append(f"rel_strength_1m unusable (age={rel_age}d, n={len(rel_vals)}) -- laggard_rotation "
                  "suppressed and overbought_distribution's 'genuinely up' gate degrades to price-only")

    # --- deployable cash: only the excess over the normal band's top ------------
    # Sizing a buy off total cash would recommend spending the liquidity floor itself. The
    # deployable figure is the overshoot, which is what the drift table already flags as the
    # live problem when cash_breach_vs_normal fires on the high side.
    total_book = book.get("total_book_usd") or 0.0
    cash_usd = book.get("wallet_usd") or 0.0
    band = drift.get("cash_band_normal_pct") or drift.get("cash_band_pct") or [None, None]
    if band[1] is not None and total_book:
        deployable = max(0.0, cash_usd - (band[1] / 100.0 * total_book))
    else:
        deployable = 0.0
    max_single = deployable * MAX_SINGLE_DEPLOY_FRACTION if deployable else 0.0

    oversold, overbought, laggard, ratchet, ladder = [], [], [], [], []

    rel_ranked = sorted((t for t in risk_by_ticker if rel_vals.get(t) is not None),
                        key=lambda t: rel_vals[t])
    laggard_cut = int(len(rel_ranked) * LAGGARD_PCTILE / 100.0) if rel_ranked else 0
    laggard_set = set(rel_ranked[:max(laggard_cut, 1)]) if rel_ranked else set()

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

        # --- B. overbought_distribution (TRIM, live) ---------------------------
        # Deliberately INDEPENDENT of over_cap: booking profit on a name that ran is the point,
        # and gating it on a risk-cap breach is precisely what made every trim an ATR trim.
        if rsi_usable and rsi is not None and rsi > RSI_OVERBOUGHT:
            genuinely_up = (abs_pct is not None and abs_pct > 0) if rel_usable else None
            if genuinely_up is not False:
                size = mv * OVERBOUGHT_TRIM_FRACTION
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
                overbought.append({**base, "trigger_type": "overbought_distribution",
                                   "direction": "TRIM", "vote": "live",
                                   "suggested_size_usd": round(size, 2),
                                   "trim_fraction": OVERBOUGHT_TRIM_FRACTION,
                                   "over_cap_independent": True,
                                   "cluster_tension": cluster_tension,
                                   "cluster_drift_pt": cl_drift,
                                   "rotation_targets": rotation_targets,
                                   "retires_when": f"{ticker} RSI14 falls below {RSI_OVERBOUGHT_EXIT:g} "
                                                   "or it is no longer up on the month",
                                   "reasons": reasons, "blockers": blockers})

        # --- C. laggard_rotation (BUY, shadow) --------------------------------
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

        # --- D/E. profit_ratchet + scale_out_ladder (shadow) -------------------
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
            tiers = [{"gain_pct": t, "triggered": gain_pct >= t,
                      "slice_usd": round(mv * LADDER_FRACTION, 2)} for t in LADDER_TIERS_PCT]
            if any(t["triggered"] for t in tiers):
                hit = [t for t in tiers if t["triggered"]]
                rungs = ", ".join("+%g%%" % t["gain_pct"] for t in hit)
                ladder.append({**base, "trigger_type": "scale_out_ladder", "direction": "TRIM",
                               "vote": "shadow",
                               "avg_cost_usd": round(avg_cost, 4), "gain_pct": round(gain_pct, 2),
                               "tiers": tiers,
                               "suggested_size_usd": hit[-1]["slice_usd"],
                               "reasons": [f"up {gain_pct:+.1f}% vs basis -- "
                                           f"{len(hit)} of {len(tiers)} scale-out rung(s) reached "
                                           f"({rungs})"],
                               "blockers": basis_note})
        elif ticker in laggard_set or (rsi is not None and rsi > RSI_OVERBOUGHT):
            if not lots.get(ticker):
                dq.append(f"{ticker} has no lots.json entry -- profit_ratchet/scale_out_ladder "
                          "cannot be computed (no cost basis)")

    oversold.sort(key=lambda x: x["rsi14"])
    overbought.sort(key=lambda x: -x["rsi14"])
    laggard.sort(key=lambda x: x["rel_strength_1m_pp"])
    ratchet.sort(key=lambda x: -(x["gain_at_risk_usd"] or 0))
    ladder.sort(key=lambda x: -x["gain_pct"])

    live_counts = {"oversold_reversion": len(oversold), "overbought_distribution": len(overbought)}
    shadow_counts = {"laggard_rotation": len(laggard), "profit_ratchet": len(ratchet),
                     "scale_out_ladder": len(ladder)}

    # Shadow entries mirror cmd_derisk's shadow_new contract: price_at_flag now, scored later.
    shadow_new = [{"date": today.isoformat(), "ticker": c["ticker"],
                   "trigger_type": c["trigger_type"], "price_at_flag": c.get("price_usd"),
                   "rsi14": c.get("rsi14"), "gain_pct": c.get("gain_pct"),
                   "rel_strength_1m_pp": c.get("rel_strength_1m_pp"), "scored": False}
                  for c in laggard + ratchet + ladder]

    emit({
        "as_of": today.isoformat(),
        "rsi_as_of": rsi_cache.get("as_of"), "rsi_age_days": rsi_age, "rsi_usable": rsi_usable,
        "rel_as_of": rel_cache.get("as_of"), "rel_age_days": rel_age, "rel_usable": rel_usable,
        "deployable_cash_usd": round(deployable, 2),
        "max_single_deploy_usd": round(max_single, 2),
        "thresholds": {"rsi_oversold": RSI_OVERSOLD, "rsi_overbought": RSI_OVERBOUGHT,
                       "laggard_pctile": LAGGARD_PCTILE, "ratchet_min_gain_pct": RATCHET_MIN_GAIN_PCT,
                       "ladder_tiers_pct": LADDER_TIERS_PCT},
        "live_counts": live_counts, "shadow_counts": shadow_counts,
        "oversold_reversion": oversold, "overbought_distribution": overbought,
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


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    for name in ("book", "journal", "attribution", "drift", "risk", "rotation", "derisk", "triggers"):
        sp = sub.add_parser(name)
        sp.add_argument("--base-dir", default=DEFAULT_BASE)
        sp.add_argument("--run-dir", required=True, help="this run's directory containing holdings.json")
        if name == "book":
            sp.add_argument("--lots", default=None)
        if name in ("journal", "derisk", "triggers"):
            sp.add_argument("--today", default=None)

    sp = sub.add_parser("sentiment")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--market-inputs", required=True)

    # No --run-dir: this checks policy.json's internal consistency only, so it can be run
    # standalone (e.g. right after editing the policy) without a live run directory.
    sp = sub.add_parser("validate")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)

    sp = sub.add_parser("proposals")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--run-dir", required=True, help="this run's directory containing compute_drift.json and holdings.json")
    sp.add_argument("--today", default=None, help="reference date for expiry (YYYY-MM-DD); default today")

    sp = sub.add_parser("dismiss")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--id", required=True, help="stable proposal id, e.g. P-014")
    sp.add_argument("--reason", default=None, help="optional free-text note on why the user dismissed it")

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

    sp = sub.add_parser("maxpain", help="max-pain + put/call OI ratio from a saved options chain (G18)")
    sp.add_argument("--chain", required=True, help="JSON chain file: {underlyingPrice, data:{expiry:{calls,puts}}}")
    sp.add_argument("--symbol", default=None)

    sp = sub.add_parser("slices", help="render per-agent data embeds from the declared table")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--run-dir", required=True)
    sp.add_argument("--mode", default="deep")
    sp.add_argument("--today", default=None)
    sp.add_argument("--agents", default=None, help="comma-separated; default = all")

    sp = sub.add_parser("gaps", help="look up known_gaps across BOTH state.json and the archive")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--id", default=None, help="exact gap id, e.g. G44")
    sp.add_argument("--query", default=None, help="free-text search across both files")
    sp.add_argument("--open-only", action="store_true")

    sp = sub.add_parser("compact", help="enforce RETENTION: archive resolved history out of the hot files")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--holdings", default=None, help="a run's holdings.json, to know which tickers are live")
    sp.add_argument("--today", default=None)
    sp.add_argument("--write", action="store_true", help="apply (default: dry run)")

    sp = sub.add_parser("history", help="authoritative was-this-ever-held lookup for a ticker (G72)")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--ticker", required=True, help="one ticker, or a comma-separated list")

    sp = sub.add_parser("pipeline", help="run all per-run computes in dependency order, failing loudly")
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
    sp.add_argument("--dry-run", action="store_true",
                    help="compute and print the scorecard without writing proposals.json")

    args = p.parse_args()
    try:
        {"book": cmd_book, "journal": cmd_journal, "attribution": cmd_attribution,
         "drift": cmd_drift, "risk": cmd_risk, "rotation": cmd_rotation, "derisk": cmd_derisk,
         "triggers": cmd_triggers, "score": cmd_score, "pipeline": cmd_pipeline, "lots": cmd_lots,
         "history": cmd_history, "maxpain": cmd_maxpain, "compact": cmd_compact, "gaps": cmd_gaps, "slices": cmd_slices,
         "sentiment": cmd_sentiment, "validate": cmd_validate, "proposals": cmd_proposals,
         "dismiss": cmd_dismiss, "stops": cmd_stops}[args.cmd](args)
    except Exception as e:  # noqa: BLE001 -- deliberate: any failure degrades gracefully
        fail(f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
