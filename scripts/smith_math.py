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

DEFAULT_BASE = "/Users/yb/Claude/AgentSmith"

# Clusters counted toward the combined "AI-capex chain" factor exposure.
# Overridable via policy.json's optional "ai_capex_clusters" list.
DEFAULT_AI_CAPEX_CLUSTERS = [
    "AI Semis/Fabs", "AI Memory/Storage", "AI Networking/Optics",
    "AI Power/Cooling/DC Infra", "Compute/Hyperscaler OEM",
]

# Bucket -> expected direction, for journal verdict scoring.
BUCKET_DIRECTION = {
    "MOMENTUM+VOLUME": "up", "OVERSOLD BOUNCE": "up", "STRONG UPTREND": "up",
    "BREAKOUT": "up", "TARGET GAP": "up", "NEW TAILWINDS": "up",
    "REVERSAL - BUY WATCH": "up",
    "OVERBOUGHT PULLBACK": "down", "STRONG DOWNTREND": "down",
    "REVERSAL - TRIM WATCH": "down", "CAPITAL ROTATION": "down",
    "NEW HEADWINDS": "down",
    "EARNINGS PROXIMITY": None, "POLICY IMPACT": None, "INSIDER ACTIVITY": None,
}
VERDICT_THRESHOLD_PCT = 2.0  # move must exceed this to call worked/failed vs neutral
ANCHOR_REVIEW_PCT = 35.0  # |move| beyond this quarantines a proposal score pending anchor review
                          # (see cmd_score: a corrupt $305.87 TSM anchor produced a phantom -39%)

# ---------------------------------------------------------------------------
# Trigger thresholds (added 2026-08-12, user-reported: "still most of the proposals are based
# on ATR risk-cap... I prefer oversold/overbought proposals to catch a bounce back for the good
# stocks... book profit if something had a good enough run and put my money on another stock
# which is yet to run").
#
# Diagnosis behind these numbers, all verified against the live book that day:
#   (a) the priority scorer gave over_cap +3, the largest single weight, and PENALISED a BUY
#       carrying no breach (-1) -- so "buy the good stock that is merely oversold" was
#       structurally the lowest-priority thing the engine could emit;
#   (b) rel_strength_1m was 12 days stale against its own 7-day TTL and missing 10 of 28 names,
#       starving the one existing profit-take trigger (names_stretched was just [AVGO, CEG]);
#   (c) no per-name RSI existed anywhere in data_cache, so overbought/oversold could not be
#       computed deterministically at all -- OVERBOUGHT PULLBACK had fired ONCE in 69 journal
#       entries, while OVERSOLD BOUNCE carried the book's best interim 7d hit rate (100%, n=4)
#       and was almost never flagged.
#
# Entry and exit thresholds deliberately differ (hysteresis): a setup that triggers at RSI<35
# is not un-triggered the moment it ticks to 36. Without the gap a proposal would flip between
# open and auto_retired on noise, which is exactly the churn the retirement pass exists to avoid.
RSI_OVERSOLD = 35.0
RSI_OVERSOLD_EXIT = 50.0
RSI_OVERBOUGHT = 70.0
RSI_OVERBOUGHT_EXIT = 60.0
# A live trigger may never fire off a stale technical read. 10 days is deliberately looser than
# the 7-day cache TTL (a 1-day overrun should not blind the desk) but far tighter than the 12-day
# staleness that was found in production -- past this, the lists come back empty with a flag
# rather than acting on numbers that no longer describe the market. Never estimate.
TRIGGER_CACHE_MAX_AGE_DAYS = 10
LAGGARD_PCTILE = 25.0            # bottom quartile of 1m relative strength = "yet to run"
RATCHET_MIN_GAIN_PCT = 15.0      # gain before a stop is worth ratcheting to breakeven
LADDER_TIERS_PCT = [25.0, 50.0]  # scale-out rungs, each selling LADDER_FRACTION of the position
LADDER_FRACTION = 1.0 / 3.0
OVERBOUGHT_TRIM_FRACTION = 0.25  # profit-take slice on an overbought name
MAX_SINGLE_DEPLOY_FRACTION = 0.25  # cap one buy suggestion at this share of deployable cash
# A technical dip on an intact thesis is a bounce setup; a technical dip alongside a FUNDAMENTAL
# negative is a falling knife. Only the latter disqualifies -- requiring net-bullish signals
# would disqualify every oversold name by definition, since being oversold IS bearish price action.
FUNDAMENTAL_HEADWIND_BUCKETS = {"NEW HEADWINDS"}

# G62: how recently a thesis must have been source-verified to outrank a stale, untimestamped
# signal_history headwind bucket. 7d ties it to the same weekly cadence the ATR/beta/rel caches
# use, so an override always rests on evidence from the current week.
THESIS_OVERRIDES_STALE_BUCKET_DAYS = 7
# G62 part (a) -- the general decay rule, complementing the narrow thesis-override below.
# smith-signals REWRITES a ticker's bucket list wholesale on every successful run, so buckets only
# go stale when that agent FAILS -- which is exactly what happened to META on 2026-08-12. A
# per-ticker refresh stamp (state.signal_history_as_of) therefore captures staleness precisely: it
# advances whenever signals ran, and freezes when it didn't. Past this age an unrefreshed
# news-flow bucket stops being decisive. It is still REPORTED -- decay removes the veto, not the
# information. A ticker with no stamp at all is treated as stale: the veto is the dangerous
# default, so unknown age must fail open, not closed.
HEADWIND_BUCKET_MAX_AGE_DAYS = 10
HEALTHY_THESIS = {"intact", "strengthening"}
LIVE_TRIGGERS = {"oversold_reversion", "overbought_distribution"}
SHADOW_TRIGGERS = {"laggard_rotation", "profit_ratchet", "scale_out_ladder"}


def load_json(path, default=None):
    if not os.path.exists(path):
        if default is not None:
            return default
        raise FileNotFoundError(path)
    with open(path) as f:
        return json.load(f)


def _prior_run_prices(base_dir, run_dir, state):
    """Last-known price per ticker from the PREVIOUS run's compute_book.json.

    Used to price full exits (the row is gone from the current snapshot, so there is no
    live price for it) -- see G41. Deliberately defensive, because two ways of getting
    this wrong were both hit for real on 2026-08-07:
      (a) SELF-REFERENCE: state.last_run_dir can already point at the run currently being
          computed. Reading the file we are about to overwrite is meaningless at best, and
          if a shell redirect truncated it first, json.load raises and takes the whole
          subcommand down. Skip when the paths resolve to the same directory.
      (b) UNPARSEABLE PRIOR: a truncated/partial compute_book.json from an interrupted run
          must degrade to "no prior prices" (exits then land in exits_unpriced and are
          reported), never crash the run.
    """
    if not run_dir:
        return {}
    prior_dir = os.path.join(base_dir, run_dir)
    try:
        if os.path.realpath(prior_dir) == os.path.realpath(getattr(_prior_run_prices, "_current", "")):
            return {}
    except OSError:
        pass
    path = os.path.join(prior_dir, "compute_book.json")
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return {}
    try:
        with open(path) as f:
            prior_book = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    return {pp["ticker"]: pp["price_usd"]
            for pp in prior_book.get("positions", []) if pp.get("price_usd")}


def emit(obj):
    print(json.dumps(obj, indent=None, sort_keys=False))


def fail(msg):
    print(json.dumps({"error": msg}))
    sys.exit(1)


def clamp(x, lo=0.0, hi=100.0):
    return max(lo, min(hi, x))


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
    lots = {k: v for k, v in lots.items() if not k.startswith("_") and isinstance(v, list)}
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


# ---------------------------------------------------------------------------
# drift
# ---------------------------------------------------------------------------
def validate_policy(policy):
    """Structural checks on policy.json. Returns a list of defect strings (empty == clean).

    Exists because the draft carried an arithmetically impossible target set from 2026-07-12 to
    2026-07-25 (targets summed to 105% alongside a 3-15% cash band) and nothing caught it -- every
    drift table in that window was measured against an unsatisfiable spec. These checks make that
    class of defect loud instead of silent.
    """
    defects = []
    targets = policy.get("cluster_targets", {})
    if not targets:
        return ["cluster_targets missing or empty -- no drift analysis possible"]

    tsum = sum(t.get("target_pct", 0) for t in targets.values())
    denom = policy.get("cluster_target_denominator")
    if denom not in ("invested_equity", "total_book"):
        defects.append(
            "cluster_target_denominator is not declared (expected 'invested_equity' or 'total_book'). "
            "Cluster percentages and cash percentage are then computed against different bases and are "
            "not comparable -- this is how the 105%-sum defect went unnoticed."
        )

    # Targets must sum to 100 of whatever base they are declared against, except that a
    # total_book basis must leave room for the cash target.
    if denom == "total_book":
        cash_band = policy.get("cash_band_pct") or [0, 0]
        cash_mid = (cash_band[0] + cash_band[1]) / 2 if None not in cash_band else 0
        expected = 100 - cash_mid
        if abs(tsum - expected) > 1.0:
            defects.append(
                f"cluster targets sum to {tsum:g}% but denominator is total_book with a cash band of "
                f"{cash_band} -- targets plus cash must total 100%, so targets should sum to about "
                f"{expected:g}%. Off by {tsum - expected:+.1f}pt."
            )
    else:
        if abs(tsum - 100) > 1.0:
            defects.append(
                f"cluster targets sum to {tsum:g}%, not 100%. Off by {tsum - 100:+.1f}pt. "
                f"Drift is measured against an unsatisfiable target set."
            )

    # Bands must be jointly satisfiable: you cannot honour every floor if the floors sum past 100,
    # and you cannot reach 100 if every ceiling together falls short.
    lo_sum = sum((t.get("band_pct") or [0, 0])[0] or 0 for t in targets.values())
    hi_sum = sum((t.get("band_pct") or [0, 0])[1] or 0 for t in targets.values())
    if lo_sum > 100:
        defects.append(f"band floors sum to {lo_sum:g}% (>100%) -- no allocation can satisfy every floor at once.")
    if hi_sum < 100:
        defects.append(f"band ceilings sum to {hi_sum:g}% (<100%) -- no allocation can reach 100% within every ceiling.")

    for name, t in targets.items():
        band = t.get("band_pct") or [None, None]
        tgt = t.get("target_pct")
        if None in band or tgt is None:
            defects.append(f"'{name}': target_pct or band_pct missing.")
            continue
        if band[0] > band[1]:
            defects.append(f"'{name}': band {band} is inverted (floor > ceiling).")
        if not (band[0] <= tgt <= band[1]):
            defects.append(f"'{name}': target {tgt:g}% sits outside its own band {band}.")

    if policy.get("max_ai_capex_factor_pct") is not None and \
            policy.get("ai_capex_denominator") not in ("invested_equity", "total_book"):
        defects.append(
            "max_ai_capex_factor_pct is set but ai_capex_denominator is not declared. This single choice "
            "flips the headline: on 2026-07-24 the book was 100% of equity (breach) but 86.3% of total "
            "book (no breach) against the same 90% cap."
        )

    unknown = [c for c in policy.get("ai_capex_clusters", []) if c not in targets]
    if unknown:
        defects.append(f"ai_capex_clusters names clusters with no target defined: {unknown}")

    return defects


def validate_cache_events(state):
    """Check that any future-dated event in caches (FOMC date, etc.) hasn't already passed.
    FIXED 1.7: 2026-07-26 — cache payload validation to prevent stale event dates.
    Returns list of defects.
    """
    defects = []
    today = date.today()
    fomc_cache = state.get("fomc_cache", {})
    if fomc_cache:
        # fomc_cache should have a next_date or similar field; if it's a future date, flag if it's past
        next_check = fomc_cache.get("next_check_date")
        if next_check:
            try:
                check_date = datetime.strptime(next_check, "%Y-%m-%d").date()
                if check_date < today:
                    defects.append(f"fomc_cache.next_check_date {next_check} is in the past; cache is stale and should be refreshed")
            except (ValueError, TypeError):
                pass
    return defects


def cmd_validate(args):
    policy = load_json(os.path.join(args.base_dir, "policy.json"), default=None)
    state = load_json(os.path.join(args.base_dir, "state.json"), default={})

    policy_defects = []
    if policy is None:
        policy_defects = ["no policy.json"]
    else:
        policy_defects = validate_policy(policy)

    cache_defects = validate_cache_events(state)
    all_defects = policy_defects + cache_defects

    emit({
        "policy_present": policy is not None,
        "policy_confirmed": policy.get("confirmed", False) if policy else False,
        "policy_as_of": policy.get("as_of") if policy else None,
        "clean": not all_defects,
        "defect_count": len(all_defects),
        "defects": all_defects,
    })


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
        entry = thesis.get(ticker, "")
        if isinstance(entry, dict):
            # newer evidence-schema entries carry status as an explicit key rather than
            # a trailing "| status" suffix on a bare string (see G58) -- read it directly.
            thesis_status = (entry.get("status") or "").strip().lower() or None
        else:
            _, _, status = (entry or "").rpartition("|")
            thesis_status = status.strip().lower() if status else None
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


# ---------------------------------------------------------------------------
# Canonical 4-way bucket every proposal verb collapses to, for both dedup-matching and the
# dashboard's color coding. Deliberately coarse: "Stage AMD", "Deploy GOOGL", "Top up GOOGL",
# "Initiate META" and "ADD MRVL" are all different staging language for the same underlying
# idea (put more money into this name), and "Light trim X" is the same idea as "Trim X" --
# treating them as different directions was why near-identical proposals (see G46) weren't
# recognized as duplicates of each other. Longest phrase first so multi-word keywords are
# matched before a shorter keyword nested inside a longer action string would win instead.
DIRECTION_KEYWORDS = [
    ("DEPLOY INTO", "BUY"), ("TOP UP", "BUY"), ("LIGHT TRIM", "TRIM"), ("HOLD FIRE", "HOLD"),
    ("REBUILD", "HOLD"), ("RE-ENTER", "BUY"), ("RE-ENTRY", "BUY"), ("REENTER", "BUY"),
    ("RE-ACCUMULATE", "BUY"), ("ACCUMULATE", "BUY"),
    ("STAGE", "BUY"), ("INITIATE", "BUY"), ("DEPLOY", "BUY"),
    ("BUILD", "BUY"), ("BUY", "BUY"), ("ADD", "BUY"), ("TRIM", "TRIM"), ("REDUCE", "TRIM"),
    ("EXIT", "SELL"), ("SELL", "SELL"), ("HOLD", "HOLD"),
]
DIRECTION_BUCKET = {"BUY": "BUY", "TRIM": "TRIM", "SELL": "SELL", "HOLD": "HOLD"}


def _proposal_direction(action):
    """Returns one of BUY/TRIM/SELL/HOLD. Coarser than the old per-verb token on purpose --
    see DIRECTION_KEYWORDS. One consequence: an "ADD X" proposal (which presupposes X is
    already held) now buckets identically to a fresh "BUY X" (which doesn't) for dedup and
    the holds_presupposed/auto-void check below no longer distinguishes them -- a stale ADD
    for an exited ticker won't be immediately auto-voided the way it used to be. That's an
    acceptable trade: the 7-day auto-expiry below is still a backstop, so the cost is a few
    extra days of visible clutter, not a silently-corrupted proposal."""
    a = (action or "").upper()
    for kw, bucket in DIRECTION_KEYWORDS:
        if kw in a:
            return bucket
    return "HOLD"


def _proposal_infer_ticker(pr):
    if pr.get("ticker"):
        return pr["ticker"]
    # backfill from the action text: last all-caps token 2-5 chars is almost always the symbol.
    #
    # FIXED 2026-08-15 (G77). The old version did `.replace("(", " ").replace(")", " ")` --
    # it stripped the BRACKETS but kept the text inside them, then took the LAST caps token.
    # On "Re-enter VRT (funded by TSM trim)" that returns TSM: the funding leg named in the
    # parenthetical, not VRT, the actual subject of the proposal. P-005 was mis-tickered that
    # way on 2026-07-29 and sat wrong for 32 days. It surfaced only because the new proposal
    # scorer tried to grade it and produced "TRIM TSM missed by 39.4%" -- scoring VRT's
    # $305.87 price against TSM's price history. The anchor was never corrupt; the ticker was.
    #
    # A parenthetical in this desk's action grammar is always qualifying context ("(funded by
    # X trim)", "(rotation funding leg)", "(new position)"), never the subject. So DISCARD the
    # parenthetical content entirely, then take the last caps token from what remains.
    #   "Re-enter VRT (funded by TSM trim)" -> "Re-enter VRT"  -> VRT   (was TSM)
    #   "Trim CEG (rotation funding leg)"   -> "Trim CEG"      -> CEG   (unchanged)
    #   "Top up TSM"                        -> "Top up TSM"    -> TSM   (unchanged)
    SKIP = ("BUY", "TRIM", "EXIT", "ADD", "HOLD", "NO", "SELL", "SET", "STOP", "RAISE")

    def _last_symbol(text):
        for w in reversed(text.split()):
            wc = w.strip(".,;:")
            if wc.isupper() and 2 <= len(wc) <= 5 and wc not in SKIP:
                return wc
        return None

    action = pr.get("action") or ""
    outside = re.sub(r"\([^)]*\)", " ", action)   # drop parenthetical content, not just brackets
    sym = _last_symbol(outside)
    if sym:
        return sym
    # Nothing outside the parens -- fall back to the full string rather than returning None,
    # but this is the ambiguous case and the caller marks it as backfilled either way.
    return _last_symbol(action.replace("(", " ").replace(")", " "))


def _proposal_parse_date(raw):
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw).date()
    except ValueError:
        pass
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def cmd_proposals(args):
    """Apply lifecycle rules to proposals.json: cross-run supersede-on-repeat, auto-expire
    old, auto-void when position changes materially. Also assigns each proposal a stable
    `id` (P-###, never reassigned) so a proposal can be referenced precisely -- by the
    dashboard, by a chat "dismiss P-014" request, or by a future automation -- without
    fragile string matching on the action text.
    FIXED 2026-07-26 (1.6): Tier 1 defect -- proposals accumulated as stale duplicates.
    FIXED 2026-07-29 (four compounding bugs found via a user-spotted duplicate CEG proposal):
      (a) this function computed supersessions but NEVER WROTE proposals.json back -- every prior
          "cleanup" run was a silent no-op, which is why the file had drifted this far;
      (b) the dedup key did exact string match on `action`, so "BUY CEG" and "BUY CEG (new position)"
          were treated as different proposals instead of the same trade -- normalize to a
          (ticker, direction) key instead, where direction is the leading verb;
      (c) six proposals were missing their `ticker` field entirely, silently disabling the
          void-on-exit check -- backfill ticker from the action text when absent;
      (d) the date parser only tried two exact formats and silently gave up on an ISO string with
          seconds and a UTC offset, disabling auto-expiry for that whole batch -- try
          datetime.fromisoformat first, with the old formats as fallback.
    FIXED 2026-08-03 (G46, user-reported: "the open proposal keeps on increasing"): the dedup
    key included `date`, so the SAME idea proposed on different calendar days (the actual,
    common case -- e.g. "Exit ORCL" recommended 07-22, 07-27 AND 07-31, all three still open
    simultaneously) was never recognized as a duplicate; only accidental same-day double-asks
    were ever merged, and 32 of 51 proposals had piled up open as a result. Key is now
    (ticker, direction) with no date component, so ANY currently-open proposal for the same
    ticker+direction merges into one running entry regardless of how many days apart the
    restatements were. The merge keeps the CHRONOLOGICALLY LATEST occurrence's numbers/date
    (freshest pricing and rationale, not the longest-winded one) and rolls every earlier
    occurrence into a `history` list with a `repeat_count`, so "recommended 4x since 07-22"
    is one compact row instead of four, while the repeat count itself stays visible and the
    7-day expiry clock resets off the latest restatement (a proposal the strategist keeps
    reiterating should stay alive; one it stops mentioning should lapse).
    """
    p_path = os.path.join(args.base_dir, "proposals.json")
    proposals = load_json(p_path, default={"proposals": [], "scorecard": {}})
    drift = load_json(os.path.join(args.run_dir, "compute_drift.json"), default={})
    holdings = load_json(os.path.join(args.run_dir, "holdings.json"), default={"holdings_inr": []})

    props = proposals.get("proposals", [])
    today_date = datetime.strptime(args.today, "%Y-%m-%d").date() if args.today else date.today()
    current_tickers = {h["ticker"] for h in holdings.get("holdings_inr", [])}
    direction = _proposal_direction
    infer_ticker = _proposal_infer_ticker
    parse_date = _proposal_parse_date

    # -- stable IDs: assign once, never reassign or reuse --
    max_id = 0
    for pr in props:
        pid = pr.get("id", "")
        if pid.startswith("P-") and pid[2:].isdigit():
            max_id = max(max_id, int(pid[2:]))
    for pr in props:
        if not pr.get("id"):
            max_id += 1
            pr["id"] = f"P-{max_id:03d}"

    # backfill ticker before the main pass so every later check sees it
    for pr in props:
        if not pr.get("ticker"):
            inferred = infer_ticker(pr)
            if inferred:
                pr["ticker"] = inferred
                pr["note"] = (pr.get("note", "") + " | ticker backfilled from action text (2026-07-29 fix)").strip(" |")
        pr.setdefault("direction_bucket", DIRECTION_BUCKET.get(direction(pr.get("action")), "HOLD"))

    seen = {}  # (ticker, direction) -> index of the current running survivor
    to_supersede = set()

    for i, pr in enumerate(props):
        if pr.get("status") != "open":
            continue
        prop_date = parse_date(pr.get("date", ""))
        key = (pr.get("ticker"), direction(pr.get("action")))
        if key in seen and key[0] is not None:
            j = seen[key]
            date_i, date_j = prop_date, parse_date(props[j].get("date", ""))
            # keep whichever occurrence is chronologically LATEST (freshest price/rationale);
            # on an exact date tie, keep the longer rationale as the original heuristic did.
            if date_i and date_j and date_i != date_j:
                survivor, loser = (i, j) if date_i > date_j else (j, i)
            elif date_i and not date_j:
                survivor, loser = i, j
            elif date_j and not date_i:
                survivor, loser = j, i
            else:
                len_i = len(pr.get("rationale", "") or "")
                len_j = len(props[j].get("rationale", "") or "")
                survivor, loser = (i, j) if len_i >= len_j else (j, i)

            history = props[survivor].setdefault("history", [])
            # fold the loser's own history (if it was itself already a merged survivor once) in first,
            # oldest-first, then the loser's own top-level occurrence.
            history.extend(props[loser].get("history", []))
            history.append({
                "date": props[loser].get("date"),
                "size_usd": props[loser].get("size_usd"),
                "price_at_proposal": props[loser].get("price_at_proposal"),
                "rationale": props[loser].get("rationale"),
            })
            history.sort(key=lambda h: parse_date(h.get("date", "")) or date.min)
            props[survivor]["repeat_count"] = len(history) + 1
            first_date = history[0].get("date") if history else props[survivor].get("date")
            props[survivor]["note"] = (
                props[survivor].get("note", "").replace(" | auto-superseded 2026-07-29 -- duplicate of another open", "")
                + f" | recommended {len(history) + 1}x since {first_date}, still open"
            ).strip(" |")

            seen[key] = survivor
            to_supersede.add(loser)
            if "duplicate" not in props[loser].get("note", ""):
                props[loser]["note"] = (props[loser].get("note", "")
                                        + f" | auto-superseded 2026-08-03 -- folded into {props[survivor]['id']}"
                                        " as a repeat of the same open proposal").strip(" |")
            i = survivor  # re-point so the expiry/void checks below use the surviving row
            pr = props[survivor]
            prop_date = parse_date(pr.get("date", ""))
        else:
            seen[key] = i

        if prop_date and (today_date - prop_date).days > 7:
            to_supersede.add(i)
            if "auto-expired" not in pr.get("note", ""):
                pr["note"] = (pr.get("note", "") + " | auto-expired after 7 calendar days").strip(" |")

        # Breach-cleared auto-void is DISABLED as of 2026-07-29. The prior implementation parsed
        # free-text rationale (splitting on "(") and false-positive-voided every TRIM proposal with normal
        # prose, since none of them happen to start with a bare cluster name. A second attempt at matching
        # the structured `cites` field against live_breaches cluster names ran into the same class of
        # problem one level up: cites uses informal short labels ("Power/DC floor breach") while
        # compute_drift uses the formal taxonomy ("AI Power/Cooling/DC Infra"), and no reliable mapping
        # between the two exists yet. Voiding a still-valid proposal silently is worse than leaving a
        # cleared one open for manual review, so this check is off until proposals carry an explicit
        # cited_cluster_id field drawn from the same enum compute_drift emits (see known_gaps).

        # Only TRIM/EXIT/ADD/HOLD presuppose the position is currently held; a BUY or "Deploy into"
        # proposes OPENING a position, so "not currently held" is the normal, expected state for those,
        # not a staleness signal. Conflating the two (found 2026-07-29) voided a same-day CEG buy
        # proposal on the grounds that CEG "had been exited" when it had simply never been bought yet.
        holds_presupposed = direction(pr.get("action")) in ("TRIM", "SELL", "HOLD")
        if holds_presupposed and pr.get("ticker") and pr.get("ticker") not in current_tickers:
            to_supersede.add(i)
            if "auto-voided" not in pr.get("note", ""):
                pr["note"] = (pr.get("note", "") + " | auto-voided -- position exited").strip(" |")

    # G60 remainder: an auto-void is normal for an OLD proposal whose position has since been
    # exited, and an ALARM for one created this run -- that combination means the strategist
    # just wrote an idea the void logic killed on arrival. It happened on 2026-08-12: a fresh
    # "Re-enter VRT" proposal was destroyed the instant it was created, because RE-ENTER was
    # missing from DIRECTION_KEYWORDS and defaulted to HOLD, which presupposes a holding that a
    # re-entry proposal by definition does not have. It was caught only because the open_count
    # (5) didn't match the 6 proposals the strategist actually wrote -- i.e. by eye. Counting is
    # not a control, so the two cases are now separated and named.
    voided_today, voided_stale, recon_warnings = [], [], []
    for i in to_supersede:
        if props[i].get("status") == "open":
            props[i]["status"] = "superseded"
        pid = props[i].get("id") or f"idx{i}"
        label = f"{pid} {props[i].get('ticker')} \"{props[i].get('action')}\""
        (voided_today if (props[i].get("date") or "")[:10] == str(today_date) else voided_stale
         ).append(label)
    if voided_today:
        warn = ("PROPOSAL AUTO-VOIDED ON THE RUN THAT CREATED IT (G60) -- "
                + "; ".join(voided_today) + ". A proposal killed the same day it was written is "
                "almost always a direction-classification bug, not a stale idea: the action verb "
                "did not map to a direction bucket, defaulted to HOLD, and HOLD presupposes a "
                "position the proposal exists to establish. Check DIRECTION_KEYWORDS covers this "
                "verb before assuming the void was correct.")
        recon_warnings.append(warn)

    # -- priority scoring (added 2026-08-03, G47: user asked "which proposal is what
    # priority" for the Open Proposals panel). Deterministic and score-able off data this
    # function already has or can cheaply load -- never a vibe-based HIGH/MEDIUM/LOW guess:
    #   +3  the ticker's own position is over its ATR risk cap (compute_risk.json)
    #   +2  the ticker's cluster is outside its policy band (compute_drift.json cluster_table)
    #   +2  a TRIM/SELL proposal when cash itself sits outside its normal band (raising cash
    #       is doing double duty, not just optional profit-taking)
    #   +2  reiterated 3+ times unactioned, +1 if reiterated exactly twice (repeat_count)
    #   +1  a SELL (full exit) skews more urgent than a partial trim, all else equal
    #   -1  a BUY that triggers none of the above -- a discretionary add, not a fix for
    #       anything currently broken
    # Thresholds: score >= 4 -> HIGH, 2-3 -> MEDIUM, otherwise LOW. Cluster is attached from
    # the same risk lookup so the dashboard can show/group by it alongside priority.
    risk = load_json(os.path.join(args.run_dir, "compute_risk.json"), default={})
    risk_by_ticker = {p["ticker"]: p for p in risk.get("positions", [])}
    cluster_breach = {c["cluster"]: c for c in drift.get("cluster_table", []) if c.get("breach")}
    book = load_json(os.path.join(args.run_dir, "compute_book.json"), default={})
    equity_usd = book.get("value_usd")
    total_book_usd = book.get("total_book_usd")

    # -- rotation / stretch / signal-conviction (added 2026-08-06, user-reported: proposals were
    # "all ATR risk correction... nothing about rotating capital toward what's likely to rally").
    # Two new, DETERMINISTIC scoring dimensions, same discipline as everything else in this
    # scorer -- typed numbers from compute files, never narrative judgment:
    #   stretch: is this TRIM candidate actually ahead of its sector and up (real profit to
    #     take), not just "fell less than everything else"? Reuses compute_derisk.json's
    #     stretch_score, which already encodes exactly that distinction (see its own docstring).
    #   signal_conviction: does this BUY candidate's bullish signal have a MEASURED track record
    #     in this book, not just "the rotation chip says accumulate"? Reads journal.json's
    #     bucket_hit_rates_7d (added this same session) -- an INTERIM, direction-aware hit rate
    #     from 7-day outcomes, always labelled interim since the validated 30d table isn't
    #     populated yet. A bar of >55% with n>=3 is deliberately modest given the small samples.
    derisk = load_json(os.path.join(args.run_dir, "compute_derisk.json"), default={})
    stretch_by_ticker = {r["ticker"]: r for r in derisk.get("queue", [])}
    rotation = load_json(os.path.join(args.run_dir, "compute_rotation.json"), default={})
    rotation_by_ticker = rotation.get("tickers", {})
    journal = load_json(os.path.join(args.base_dir, "journal.json"), default={})
    hit_rates_7d = journal.get("bucket_hit_rates_7d", {})
    # compute_triggers.json (added 2026-08-12): deterministic candidate lists for the five
    # non-ATR triggers. Only the LIVE ones score here -- a shadow trigger that somehow reached
    # a proposal is flagged, not rewarded, so the "earns its vote first" rule can't be bypassed
    # by the strategist simply writing the trigger_type onto a proposal.
    triggers = load_json(os.path.join(args.run_dir, "compute_triggers.json"), default={})
    trigger_live_sets = {tt: {c["ticker"] for c in (triggers.get(tt) or [])}
                         for tt in LIVE_TRIGGERS}
    trigger_rows = {tt: {c["ticker"]: c for c in (triggers.get(tt) or [])}
                    for tt in LIVE_TRIGGERS | SHADOW_TRIGGERS}
    # Already staleness-gated by cmd_triggers -- empty dicts when the cache is too old, which makes
    # every RSI-based retirement check below untestable and therefore a no-op (proposal stays open).
    trig_rsi = triggers.get("rsi_values") or {}
    trig_abs = triggers.get("abs_return_1m_pct_values") or {}
    # Thesis map, for the oversold_reversion retirement check only: that trigger's premise is
    # "healthy name, technical dip", so a thesis leaving intact/strengthening invalidates it
    # regardless of where RSI sits. Read defensively -- a missing state.json degrades to "cannot
    # test", never to a retirement on absent data.
    _state = load_json(os.path.join(args.base_dir, "state.json"), default={})
    state_thesis = _state.get("thesis", {}) or {}
    # Cluster fallback for NON-HELD tickers (added 2026-08-12). `cluster` was resolved only from
    # compute_risk.json, which contains held positions ONLY -- so a BUY proposal for a ticker the
    # book does not currently hold had cluster=None and could never earn the directional
    # cluster-breach bonus. Found live: "Re-enter VRT" scored -1 "discretionary add -- no active
    # breach" while AI Power/Cooling/DC Infra sat 10.27pt UNDER its floor and VRT was the exact
    # name that would fill it. Same directional-logic family as G56, mirrored: G56 stopped a trim
    # citing an underweight, this stops an underweight from justifying the buy that cures it.
    # sector_map retains exited names, which is precisely what makes it the right fallback.
    state_sector_map = _state.get("sector_map", {}) or {}
    # DIRECTIONAL cash check (fixed 2026-08-06). `cash_breach_vs_normal` is a bare boolean that
    # fires on BOTH edges -- too little cash and too much. The scorer previously treated any
    # breach as a reason to favour trimming ("this also rebuilds cash"), which inverts on the
    # high side: on 2026-08-06 cash sat at 25.3% against a [5,15] band, and every trim proposal
    # was being awarded +2 and captioned "cash outside its normal band -- this also rebuilds it"
    # while the book was in fact drowning in idle cash. Split the two edges: a trim earns the
    # bonus only when cash is genuinely SHORT, and a buy earns one when cash is in EXCESS.
    _cash_pct = drift.get("cash_pct")
    _cash_band = drift.get("cash_band_normal_pct") or drift.get("cash_band_pct") or [None, None]
    cash_short = bool(_cash_pct is not None and _cash_band[0] is not None and _cash_pct < _cash_band[0])
    cash_excess = bool(_cash_pct is not None and _cash_band[1] is not None and _cash_pct > _cash_band[1])

    def directional_breach(cluster, bucket):
        """The cluster's breach entry, but ONLY if its edge matches a trade in this bucket's
        direction -- over-ceiling for TRIM/SELL, under-floor for BUY. Shared by the scorer, the
        auto-retirement pass, and retires_when so all three agree by construction (fixed
        2026-08-07: previously each read cluster_breach directly with no direction check, so a
        TRIM could survive/score on a cluster that had fallen UNDER its floor -- citing an
        underweight as the reason to trim MORE of it, which deepens the underweight)."""
        cb = cluster_breach.get(cluster) if cluster else None
        if not cb:
            return None
        edge = cb.get("breach_edge")
        if (edge == "over" and bucket in ("TRIM", "SELL")) or (edge == "under" and bucket == "BUY"):
            return cb
        return None

    for pr in props:
        if pr.get("status") != "open":
            continue
        score, reasons = 0, []
        ticker, bucket, rc = pr.get("ticker"), pr.get("direction_bucket", "HOLD"), pr.get("repeat_count", 1)
        rpos = risk_by_ticker.get(ticker) if ticker else None
        cluster = (rpos.get("cluster") if rpos
                   else (pr.get("cluster") or state_sector_map.get(ticker)))
        if rpos and rpos.get("over_cap"):
            # DEMOTED +3 -> +2 on 2026-08-12 (user decision). At +3 this was the largest single
            # weight in the scorer and, combined with the repeat bonus below, the only trigger
            # that reliably reached HIGH -- so the open list was structurally almost all ATR
            # trims. Risk discipline is unchanged (an over-cap name still always surfaces, and
            # cmd_risk still computes the cap identically); what changes is that a genuine
            # profit-take or a measured oversold entry can now outrank it.
            score += 2
            reasons.append(f"{ticker} at {rpos.get('cap_multiple', 0):.2f}x its ATR risk cap")
        # DIRECTIONAL cluster-breach check (fixed 2026-08-07, found live: MRVL's 08-06 trim cured
        # its own risk cap, but the AI Networking/Optics cluster had meanwhile fallen UNDER its
        # floor from the same trim plus several stops in the same cluster -- the untested version
        # of this check kept citing that under-floor breach as justification to trim MORE, which
        # is backwards: trimming a name inside an underweight cluster deepens the underweight.
        # See directional_breach() above -- shared with the retirement pass and retires_when.
        db = directional_breach(cluster, bucket)
        if db:
            score += 2
            reasons.append(f"{cluster} {'over' if db.get('breach_edge')=='over' else 'under'} band "
                            f"({db.get('drift_pt', 0):+.1f}pt)")
        if cash_short and bucket in ("TRIM", "SELL"):
            score += 2
            reasons.append(f"cash short at {_cash_pct:.1f}% vs a [{_cash_band[0]},{_cash_band[1]}]% band "
                           "-- this also rebuilds it")
        if cash_excess and bucket == "BUY":
            score += 2
            reasons.append(f"cash in excess at {_cash_pct:.1f}% vs a [{_cash_band[0]},{_cash_band[1]}]% band "
                           "-- deploying is the live problem, not raising more")
        if bucket in ("TRIM", "SELL") and ticker:
            dr = stretch_by_ticker.get(ticker)
            # names_stretched is the authoritative "ahead of sector AND up" list computed by
            # cmd_derisk -- do not re-derive it from stretch_score>0 here, that would silently
            # diverge from derisk's own "beat a falling benchmark ≠ stretched" distinction.
            if dr and ticker in (derisk.get("names_stretched") or []):
                score += 2
                reasons.append(f"{ticker} genuinely stretched: +{dr.get('abs_return_1m_pct',0):.1f}% "
                               f"1m, {dr.get('rel_strength_1m_pp',0):+.1f}pp vs SMH -- real profit "
                               "to take, not just a smaller loss")
        if bucket == "BUY" and ticker:
            rtk = rotation_by_ticker.get(ticker, {})
            best_hr = None
            for bkt in rtk.get("bullish_buckets", []):
                hr = hit_rates_7d.get(bkt)
                if hr and hr["hit_rate_pct"] > 55 and (best_hr is None or hr["hit_rate_pct"] > best_hr[1]):
                    best_hr = (bkt, hr["hit_rate_pct"], hr["n"])
            if best_hr:
                score += 2
                reasons.append(f"bullish signal '{best_hr[0]}' has a {best_hr[1]:.0f}% INTERIM 7d hit "
                               f"rate (n={best_hr[2]}, not yet 30d-validated) in this book")
        # -- non-ATR triggers (added 2026-08-12). Weighted +3 so either can reach MEDIUM alone and
        # HIGH with any one supporting term -- deliberately ABOVE the now-demoted ATR weight of
        # +2, because the whole point of the change is that "this ran, book some" and "this good
        # name is oversold, add" should be able to outrank "this position is 1.2x a volatility cap".
        # Both are gated on the ticker actually appearing in compute_triggers.json's LIVE list this
        # run, so a trigger_type written onto a proposal whose condition has since cleared scores
        # nothing rather than coasting on a label.
        tt = pr.get("trigger_type")
        if tt in LIVE_TRIGGERS and ticker in trigger_live_sets.get(tt, set()):
            row = trigger_rows[tt][ticker]
            score += 3
            reasons.append(f"{tt}: " + "; ".join(row.get("reasons") or []))
            for b in row.get("blockers") or []:
                reasons.append(f"caveat -- {b}")
        elif tt in SHADOW_TRIGGERS:
            reasons.append(f"{tt} is SHADOW-SCORED, not yet voting -- this trigger has no measured "
                           "hit rate in this book, so it contributes 0 to priority by design")
        elif tt in LIVE_TRIGGERS:
            reasons.append(f"{tt} was the stated trigger but {ticker} is not in this run's "
                           f"{tt} candidate list -- condition is no longer live")

        # Repeat bonus, with a DECAY (added 2026-08-12). A proposal restated 5+ times and never
        # actioned is not more urgent -- in practice it has been declined, and the old uncapped
        # +2 was promoting exactly those to HIGH and crowding out fresh ideas (DRAM sat at rc=6).
        # Past the decay point it earns nothing and says so, which is also the cue to dismiss it.
        if rc >= 5:
            reasons.append(f"recommended {rc}x and never actioned -- treated as implicitly declined "
                           f"(no priority bonus); consider `dismiss {pr.get('id')}` to clear it")
        elif rc >= 3:
            score += 2
            reasons.append(f"recommended {rc}x, still unactioned")
        elif rc == 2:
            score += 1
            reasons.append(f"recommended {rc}x, still unactioned")
        if bucket == "SELL":
            score += 1
        # The old penalty fired on any BUY with score==0, which punished precisely the trade this
        # book was missing: a well-founded add on a healthy name that happens to breach nothing.
        # It now only applies to a buy with NO typed trigger at all -- genuinely discretionary.
        if bucket == "BUY" and score <= 0 and tt not in (LIVE_TRIGGERS | SHADOW_TRIGGERS):
            score -= 1
            reasons.append("discretionary add -- no active breach or typed trigger behind it")
        pr["priority_score"] = score
        pr["priority"] = "HIGH" if score >= 4 else "MEDIUM" if score >= 2 else "LOW"
        pr["priority_reasons"] = reasons
        if cluster:
            pr["cluster"] = cluster

        # -- honest sizing (added 2026-08-06, user-reported: "seems ATR risk correction is the
        # only thing these proposals are suggesting" and sizes were small relative to the
        # breach). full_cure_usd is what it would actually take to clear whichever trigger is
        # live -- the position's own risk-cap excess (compute_risk's headroom_usd, exact) and/or
        # the cluster's dollar overage (derived here: ceiling breaches are tested against
        # total_book_usd per compute_drift's own denominator choice, floor breaches against
        # equity_usd -- using the WRONG denominator would silently mis-state the cure amount).
        # When a proposal cites both triggers, the binding one is whichever needs the larger
        # trim -- curing the smaller one first would still leave the position non-compliant on
        # the other. This DISPLAYS the gap, it does not auto-resize size_usd -- resizing a
        # proposal is a judgment call for the strategist/user, not something this lifecycle
        # pass should do silently.
        if bucket in ("TRIM", "SELL"):
            cures = []
            if rpos and rpos.get("over_cap") and rpos.get("headroom_usd") is not None:
                cures.append(("risk cap", abs(rpos["headroom_usd"])))
            if cluster and cluster in cluster_breach:
                cb = cluster_breach[cluster]
                if cb.get("breach_edge") == "over" and total_book_usd:
                    over_pct = cb.get("actual_pct_of_total_book", 0) - (cb.get("band_pct") or [0, 100])[1]
                    if over_pct > 0:
                        cures.append(("cluster ceiling", over_pct / 100 * total_book_usd))
            if cures:
                basis, cure_usd = max(cures, key=lambda c: c[1])
                pr["full_cure_usd"] = round(cure_usd, 0)
                pr["cure_basis"] = basis
                sz = pr.get("size_usd") or 0
                pr["cure_pct"] = round(sz / cure_usd * 100, 0) if cure_usd else None
                if pr["cure_pct"] is not None and pr["cure_pct"] < 90:
                    n_tranches = max(1, -(-round(cure_usd) // sz)) if sz else None  # ceil div
                    pr["tranche_note"] = (f"cures {pr['cure_pct']:.0f}% of the {basis} excess "
                                          f"(${cure_usd:,.0f}) -- roughly {n_tranches} tranches "
                                          f"this size to fully clear it" if n_tranches else
                                          f"cures {pr['cure_pct']:.0f}% of the {basis} excess (${cure_usd:,.0f})")

    # -- CONDITION-BASED AUTO-RETIREMENT (added 2026-08-06, user-reported: "the dashboard is
    # not live and dynamic... under low priority proposals it is showing rebuild cash buffer"
    # while cash sat at 25.3%, three times its normal band ceiling).
    #
    # Root cause was three compounding gaps, not one:
    #   (a) the only automatic cleanup was a 7-day *calendar* expiry -- a blunt instrument that
    #       says nothing about whether the proposal's REASON still holds. On 2026-08-06 the six
    #       stalest proposals were all 6 days old, i.e. one day short of lapsing, so every one
    #       of them still rendered as live advice.
    #   (b) the breach-cleared void was DISABLED in 2026-07-29 (see the comment above) because
    #       it tried to parse free-text rationale and false-positived. That reasoning was right,
    #       and the fix is not to re-enable text parsing -- it is to stop reading prose entirely.
    #   (c) nothing ever checked the non-cluster premises: cash already rebuilt, an "initiate X"
    #       whose X is now held, a HOLD gated on an earnings print that has since happened.
    #
    # The fix reuses the SAME structural signals the priority scorer already computes above
    # (over_cap from compute_risk, cluster breach from compute_drift, cash band from
    # compute_drift). Those are typed enums and numbers, never prose, so this cannot repeat the
    # 2026-07-29 false-positive class. A proposal is retired only when its objective trigger is
    # verifiably gone; anything requiring judgement is FLAGGED for the strategist instead, and
    # left open. Status is `auto_retired`, deliberately distinct from `superseded` (folded into
    # a duplicate) and from `dismissed_by_user` (terminal, user's own call) so the audit trail
    # shows who retired what -- and so a genuinely re-emerging condition is free to be proposed
    # afresh under a new id rather than being permanently suppressed.
    HOLD_MAX_AGE_DAYS = 2  # HOLDs are tactical ("hold fire until tonight's print") and go off fast
    retired = []
    for pr in props:
        if pr.get("status") != "open":
            continue
        ticker = pr.get("ticker")
        bucket = pr.get("direction_bucket", "HOLD")
        rpos = risk_by_ticker.get(ticker) if ticker else None
        cluster = pr.get("cluster")
        cl = directional_breach(cluster, bucket)
        over_cap = bool(rpos and rpos.get("over_cap"))
        age = (today_date - (parse_date(pr.get("date", "")) or today_date)).days
        why = None

        action_l = (pr.get("action") or "").lower()
        is_cash_proposal = ticker is None and ("cash" in action_l)

        if is_cash_proposal:
            # "Rebuild cash buffer" is satisfied the moment cash re-enters (or overshoots) its
            # normal band -- which is exactly what a stop-loss cascade does for free.
            cash_pct = drift.get("cash_pct")
            band = drift.get("cash_band_normal_pct") or drift.get("cash_band_pct") or [None, None]
            if cash_pct is not None and band[0] is not None and cash_pct >= band[0]:
                why = (f"cash is {cash_pct:.2f}% vs a normal band of [{band[0]},{band[1]}]% -- "
                       "the buffer this proposed to rebuild is already rebuilt")
        elif bucket in ("TRIM", "SELL"):
            # A trim exists to cure one of exactly three structural problems now (added a third,
            # 2026-08-06, for rotation/pair-trade proposals): a position over its own ATR risk
            # cap, a cluster outside its policy band, or -- when the proposal was explicitly
            # created as a stretch-based profit-take (trigger_type=="stretch", see the pair-trade
            # generation in §6/§7) -- the ticker no longer sitting in compute_derisk's
            # names_stretched list. Checking stretch ONLY when trigger_type says so, never as a
            # blanket rule, matters: most trims are cap/cluster driven and were never claiming
            # the position was a "winner" to begin with, so testing stretch on those would be a
            # non-sequitur retirement reason.
            # An overbought_distribution trim (added 2026-08-12) is deliberately CAP-INDEPENDENT --
            # it exists to book profit on a name that ran, not to cure a breach -- so it must be
            # tested on its OWN condition and must never be retired merely for being within its
            # ATR cap. Hysteresis: triggered above RSI_OVERBOUGHT, retires below the lower exit
            # threshold, so a name oscillating around 70 doesn't churn open/retired every run.
            if pr.get("trigger_type") == "overbought_distribution":
                rsi_now = trig_rsi.get(ticker)
                abs_now = trig_abs.get(ticker)
                if rsi_now is None:
                    pass  # cannot test (cache stale/absent) -- keep open rather than guess
                elif rsi_now < RSI_OVERBOUGHT_EXIT:
                    why = (f"{ticker} RSI14 has cooled to {rsi_now:.1f} (below the "
                           f"{RSI_OVERBOUGHT_EXIT:g} exit) -- the overbought condition this "
                           "profit-take was sized against has cleared")
                elif abs_now is not None and abs_now <= 0:
                    why = (f"{ticker} is no longer up on the month ({abs_now:+.1f}%) -- there is no "
                           "longer a gain to protect, so this is not a profit-take any more")
            elif pr.get("trigger_type") in SHADOW_TRIGGERS:
                pass  # shadow triggers are logged, not lifecycle-managed as live proposals
            else:
                is_stretch_trigger = pr.get("trigger_type") == "stretch"
                stretch_ok = (ticker in (derisk.get("names_stretched") or [])) if is_stretch_trigger else True
                if not over_cap and not cl and (not is_stretch_trigger or not stretch_ok):
                    if is_stretch_trigger:
                        why = (f"{ticker} is no longer in the stretched cohort (ahead of sector AND "
                               "up) -- the profit-taking rationale for this trim has cleared")
                    else:
                        # Be honest about WHY the cluster stopped counting: it may be genuinely
                        # in-band, or it may have flipped to an under-floor breach that a trim
                        # would only worsen -- "inside its policy band" is false in the second case
                        # and would misreport a real, live problem as resolved.
                        raw_cb = cluster_breach.get(cluster) if cluster else None
                        if raw_cb and raw_cb.get("breach_edge") == "under":
                            cluster_note = (f", though {cluster} is now UNDER its floor "
                                            f"({raw_cb.get('drift_pt', 0):+.1f}pt) -- a separate live issue, "
                                            "just not one a trim addresses")
                        elif cluster:
                            cluster_note = f" and {cluster} is inside its policy band"
                        else:
                            cluster_note = ""
                        why = (f"neither trigger is live: {ticker} is within its ATR risk cap"
                               + cluster_note + " -- the structural reason for this trim has cleared")
        elif bucket == "BUY":
            # An "initiate"/"new position" buy is self-evidently done once the name is held.
            if ticker and ticker in current_tickers and any(
                    w in action_l for w in ("initiate", "new position", "open a position")):
                why = f"{ticker} is now held -- this proposed initiating a position that already exists"
            # A cluster-fill buy is done once the cluster is back inside its band.
            elif cluster and not cl and any(w in action_l for w in ("top up", "fill", "stage", "deploy")):
                why = f"{cluster} is back inside its policy band -- the underweight this filled has cleared"
            # A signal-conviction buy (added 2026-08-06, pair-trade proposals) retires once the
            # measured edge that justified it is gone -- either the signal no longer fires on
            # this ticker, or its interim 7d hit rate has fallen out of the >55% bar the
            # proposal was sized against. Checked ONLY for proposals explicitly created this way
            # (trigger_type=="signal_conviction"), same discipline as the stretch check above.
            # An oversold_reversion buy (added 2026-08-12) is a TIMING setup, not a structural one:
            # it is consumed the moment the dip it was built on mean-reverts. Retiring on the
            # hysteresis exit (RSI back above RSI_OVERSOLD_EXIT) rather than the entry threshold
            # keeps a name hovering at 35-36 from flipping every run. A thesis that leaves
            # intact/strengthening kills it outright -- the quality gate was the whole premise.
            elif pr.get("trigger_type") == "oversold_reversion":
                rsi_now = trig_rsi.get(ticker)
                th_now = _thesis_status(state_thesis.get(ticker))
                if th_now is not None and th_now not in HEALTHY_THESIS:
                    why = (f"{ticker}'s thesis is now '{th_now}' -- an oversold entry is only a dip-buy "
                           "while the thesis is intact; without that it is a falling knife")
                elif rsi_now is None:
                    pass  # cannot test (cache stale/absent) -- keep open rather than guess
                elif rsi_now > RSI_OVERSOLD_EXIT:
                    why = (f"{ticker} RSI14 has recovered to {rsi_now:.1f} (above the "
                           f"{RSI_OVERSOLD_EXIT:g} exit) -- the oversold setup this buy was timed "
                           "against has been consumed")
            elif pr.get("trigger_type") == "signal_conviction" and pr.get("trigger_bucket"):
                tb = pr["trigger_bucket"]
                rtk = rotation_by_ticker.get(ticker, {}) if ticker else {}
                hr = hit_rates_7d.get(tb)
                if tb not in rtk.get("bullish_buckets", []):
                    why = f"{ticker} no longer carries the '{tb}' signal -- the edge this buy was sized against is gone"
                elif not hr or hr.get("hit_rate_pct", 0) <= 55:
                    why = (f"'{tb}'s interim 7d hit rate has fallen to "
                           f"{hr.get('hit_rate_pct') if hr else 'unmeasured'}% (was >55% when proposed) "
                           "-- the measured edge behind this buy no longer clears the bar")
        elif bucket == "HOLD":
            if ticker and ticker not in current_tickers:
                why = f"{ticker} is no longer held -- the position this advised holding on is gone"
            elif age >= HOLD_MAX_AGE_DAYS:
                why = (f"tactical HOLD is {age} days old -- hold-fire advice is time-bound by nature "
                       "and is not carried forward as standing guidance")

        if why:
            pr["status"] = "auto_retired"
            pr["retired_on"] = str(today_date)
            pr["retired_reason"] = why
            pr["note"] = (pr.get("note", "") + f" | auto-retired {today_date}: {why}").strip(" |")
            retired.append({"id": pr.get("id"), "action": pr.get("action"), "reason": why})

    # -- LIVE RE-JUSTIFICATION (same change). Every proposal still open after the pass above
    # carries a freshly recomputed `still_valid_because` and a re-priced `price_drift_pct`, so
    # the dashboard renders TODAY's reason a proposal survives rather than a frozen sentence
    # written days ago against conditions that may no longer exist. This is what makes the
    # panel read as live: the rationale is history, this field is current.
    price_now_by_ticker = {}
    for h in holdings.get("holdings_inr", []):
        if h.get("price_usd") is not None:
            price_now_by_ticker[h["ticker"]] = h["price_usd"]

    for pr in props:
        if pr.get("status") != "open":
            continue
        live = list(pr.get("priority_reasons") or [])
        flags = []
        p0, pnow = pr.get("price_at_proposal"), price_now_by_ticker.get(pr.get("ticker"))
        if p0 and pnow:
            dp = (pnow - p0) / p0 * 100
            pr["price_now"] = round(pnow, 2)
            pr["price_drift_pct"] = round(dp, 2)
            if abs(dp) >= 10:
                flags.append(f"price has moved {dp:+.1f}% since proposed (${p0:.2f} -> ${pnow:.2f}) -- re-size before acting")
        # EVIDENCE GATE (added 2026-08-10, G58). The strategist's standing rule is "cite at least
        # two inputs" -- that counts inputs, it does not test them, so two unverified qualitative
        # claims satisfy it. On 2026-08-10 a sized SNDK trim shipped citing a thesis WATCH that
        # rested on a mischaracterized earnings headline (the quarter was a beat; only the forward
        # guide was light). Three days earlier a strategist veto rested on a quality finding that
        # MRVL's own 10-Q contradicted (G44). Same shape twice: an unverified word outranking
        # verified arithmetic -- smith-strategist.md literally says thesis WATCH/BROKEN "outrank
        # pure drift breaches as trim candidates".
        #
        # This reads the TYPED counts the strategist supplies, never the rationale prose. Parsing
        # prose is what made the breach-cleared voider false-positive and get disabled in
        # 2026-07-29; that lesson holds. A proposal with no evidence_quality block is simply not
        # assessed (older rows stay untouched) rather than being flagged on an absent field.
        eq = pr.get("evidence_quality")
        if isinstance(eq, dict):
            n_ver = eq.get("verified") or 0
            n_unver = eq.get("unverified") or 0
            n_comp = eq.get("computed") or 0
            if (n_ver + n_comp) == 0 and n_unver > 0:
                flags.append(
                    f"sole basis is {n_unver} unverified qualitative claim(s) -- no verified or "
                    f"computed input backs this; confirm the underlying claim before acting (G58)")
        if not live:
            live.append("no active structural trigger -- kept open on the strategist's judgement, not a breach")
        pr["still_valid_because"] = live
        pr["review_flags"] = flags
        pr["revalidated_on"] = str(today_date)

        # Forward-looking retirement condition (added 2026-08-06, same change as
        # auto-retirement above). `still_valid_because` says why the proposal survived TODAY;
        # `retires_when` says what would make it NOT survive tomorrow -- the inverse condition
        # of the retirement checks earlier in this function, kept in sync by construction since
        # both read the same rpos/cl/bucket signals rather than being independently authored.
        # This is what makes the automation legible instead of mysterious: the reader can see
        # the actual bar a proposal has to clear, not just that "the system decides".
        ticker = pr.get("ticker")
        bucket = pr.get("direction_bucket", "HOLD")  # NOT the leaked loop var from the scorer above
        rpos = risk_by_ticker.get(ticker) if ticker else None
        cl = directional_breach(pr.get("cluster"), bucket)
        retires_when = None
        _tt = pr.get("trigger_type")
        if _tt == "overbought_distribution":
            retires_when = (f"{ticker} RSI14 falls below {RSI_OVERBOUGHT_EXIT:g} or it is no longer "
                            "up on the month (cap-independent -- staying inside the ATR cap does "
                            "NOT retire this)")
        elif _tt == "oversold_reversion":
            retires_when = (f"{ticker} RSI14 recovers above {RSI_OVERSOLD_EXIT:g} (setup consumed) "
                            "or its thesis leaves intact/strengthening")
        elif _tt in SHADOW_TRIGGERS:
            retires_when = (f"n/a -- {_tt} is shadow-scored, tracked in trigger_journal.json rather "
                            "than lifecycle-managed here")
        elif bucket in ("TRIM", "SELL") and pr.get("trigger_type") == "stretch":
            retires_when = f"{ticker} drops out of the stretched cohort (no longer ahead of sector AND up)"
        elif bucket in ("TRIM", "SELL"):
            conds = []
            if rpos and rpos.get("over_cap"):
                conds.append(f"{ticker} drops under its ATR risk cap")
            if cl:
                conds.append(f"{pr.get('cluster')} re-enters its policy band")
            retires_when = " OR ".join(conds) + " (both must clear -- either alone keeps it open)" if len(conds) > 1 else (conds[0] if conds else None)
        elif bucket == "BUY" and pr.get("trigger_type") == "signal_conviction":
            retires_when = f"'{pr.get('trigger_bucket')}' signal drops off {ticker} or its 7d hit rate falls to/below 55%"
        elif bucket == "BUY" and pr.get("cluster") and cl:
            retires_when = f"{pr.get('cluster')} re-enters its policy band"
        pr["retires_when"] = retires_when

    proposals["proposals"] = props
    json.dump(proposals, open(p_path + ".tmp", "w"), indent=2)
    os.replace(p_path + ".tmp", p_path)

    open_now = [pr for pr in props if pr.get("status") == "open"]
    priority_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for pr in open_now:
        priority_counts[pr.get("priority", "LOW")] += 1

    emit({"proposals_count": len(props), "superseded_count": len(to_supersede), "changes_made": len(to_supersede),
          "auto_retired_count": len(retired), "auto_retired": retired,
          "open_count": len(open_now), "priority_counts": priority_counts, "written": True,
          "auto_voided_created_this_run": voided_today,
          "auto_voided_stale": voided_stale,
          "reconciliation_warnings": recon_warnings})


def cmd_stops(args):
    """Stop-loss efficacy: for every stop-loss trade with a known fill price, measure whether
    the stop helped or hurt versus simply holding through -- using PRICE, not narrative.
    Added 2026-08-06 (dashboard feature review): trades.json had 24 stop-loss fills with exact
    prices and was referenced by the dashboard generator exactly zero times. Manually computed
    once, this data showed a real, non-obvious pattern: stops that fired in a same-day cluster
    of 3+ (an "opening cascade" -- market-open liquidity gaps triggering several stops within
    minutes of each other) recovered +2.82% on average, while deliberate, isolated stops fired
    mid-session averaged -1.92% (i.e. correctly avoided further downside). This command makes
    that comparison a standing, auto-updating artifact instead of a one-off calculation.

    Cohort tagging deliberately does NOT hardcode "9:30-9:40 ET" as the open -- that drifts
    with DST and this book has both US and (via ADRs) implicit Asia-session exposure. Instead:
    group same-day stop-loss fills that carry a fill_time_utc, and any fill with >=2 OTHER
    same-day fills within a +/-5-minute window is tagged "cascade"; everything else (isolated
    fills, or fills lacking a captured time) is "deliberate" or "unknown" respectively. This is
    the same "typed signal, not text parsing" discipline as the proposals auto-retirement engine.

    --prices-json is a flat {"TICKER": price_usd} map the ORCHESTRATOR must supply (fetched via
    yfinance at sweep time) for every ticker with an unscored stop -- this script has no network
    access by design (compute-first: fetching is a judgment/tool-use step, this file is pure
    arithmetic on data already on disk). A stop whose ticker isn't in the map that run simply
    stays unscored until a future run supplies it; nothing is silently dropped, see data_quality.

    Output is a standing file at base_dir/stops_analysis.json (NOT run-dir scoped, unlike
    compute_book.json etc) because run dirs get pruned to the last 10 and this needs the FULL
    trade history to be useful -- recomputed from scratch each call, so pruning is harmless.
    """
    trades = load_json(os.path.join(args.base_dir, "trades.json"), default={"trades": []})
    prices = load_json(args.prices_json, default={}) if args.prices_json else {}
    today = datetime.strptime(args.today, "%Y-%m-%d").date() if args.today else date.today()

    all_stops = [t for t in trades.get("trades", []) if t.get("reason") == "stop-loss"]
    no_fill_price = [t for t in all_stops if not t.get("price_at_trade")]
    # PROVENANCE QUARANTINE (added 2026-08-13, G64). A fill price reconstructed from a quantity
    # diff is a guess, and guesses were silently scored here for weeks: NVDA 2026-07-27 was really
    # TWO sells (7sh @ $201.01 + 5sh @ $197.51, weighted $199.55) recorded as one 12sh fill @
    # $196.51; GEV was $973.57 recorded as $996.57; LRCX $295.74 as $291.61. Those errors flowed
    # into this file and overstated the measured cost of the user's stop-loss discipline by ~$402
    # -- enough to invert the desk's verdict on their own strategy across two briefings.
    # So: only an email-confirmed price is scoreable. A row explicitly tagged "reconstructed" is
    # EXCLUDED and surfaced in data_quality; it is quarantined, never deleted, and re-enters
    # scoring the moment smith-ledger confirms it. Rows with NO price_source predate the tagging
    # convention -- they are scored (removing them would blank the whole history) but counted and
    # reported, so the share of the result resting on unverified prices is always visible.
    reconstructed = [t for t in all_stops
                     if t.get("price_at_trade") and t.get("price_source") == "reconstructed"]
    candidates = [t for t in all_stops
                  if t.get("price_at_trade") and t.get("price_source") != "reconstructed"]
    untagged = [t for t in candidates if not t.get("price_source")]

    # -- cohort tagging: cluster same-day fills within a +/-5-minute window --
    by_date = {}
    for t in candidates:
        by_date.setdefault(t.get("date"), []).append(t)
    cohort = {}  # id(trade) -> "cascade" | "deliberate" | "unknown"
    for d, day_trades in by_date.items():
        timed = [t for t in day_trades if t.get("fill_time_utc")]
        for t in day_trades:
            if not t.get("fill_time_utc"):
                cohort[id(t)] = "unknown"
                continue
            try:
                t_dt = datetime.strptime(t["fill_time_utc"], "%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                cohort[id(t)] = "unknown"
                continue
            nearby = 0
            for o in timed:
                if o is t:
                    continue
                try:
                    o_dt = datetime.strptime(o["fill_time_utc"], "%Y-%m-%dT%H:%M:%SZ")
                except ValueError:
                    continue
                if abs((t_dt - o_dt).total_seconds()) <= 300:
                    nearby += 1
            cohort[id(t)] = "cascade" if nearby >= 2 else "deliberate"

    scored, unscored_missing_price = [], []
    for t in candidates:
        ticker = t.get("ticker")
        fill = t.get("price_at_trade")
        now = prices.get(ticker)
        if now is None:
            unscored_missing_price.append(ticker)
            continue
        try:
            trade_date = datetime.strptime(t.get("date", ""), "%Y-%m-%d").date()
            days_since = (today - trade_date).days
        except ValueError:
            days_since = None
        move_pct = round((now - fill) / fill * 100, 2)
        qty_abs = abs(t.get("qty_change") or 0)
        dollar_impact = round((now - fill) * qty_abs, 2)
        verdict = "hurt" if move_pct > 1.0 else ("saved" if move_pct < -1.0 else "flat")
        scored.append({
            "ticker": ticker, "date": t.get("date"), "fill_time_utc": t.get("fill_time_utc"),
            "days_since": days_since, "fill_price": fill, "price_now": now,
            "move_pct": move_pct, "qty": qty_abs, "dollar_impact": dollar_impact,
            "verdict": verdict, "cohort": cohort.get(id(t), "unknown"),
        })
    scored.sort(key=lambda r: r.get("date") or "", reverse=True)

    def summarize(rows):
        if not rows:
            return None
        n = len(rows)
        avg_move = round(sum(r["move_pct"] for r in rows) / n, 2)
        net_impact = round(sum(r["dollar_impact"] for r in rows), 2)
        saved = sum(1 for r in rows if r["verdict"] == "saved")
        hurt = sum(1 for r in rows if r["verdict"] == "hurt")
        win_rate = round(saved / (saved + hurt) * 100, 1) if (saved + hurt) else None
        return {"count": n, "avg_move_pct": avg_move, "net_dollar_impact": net_impact,
                "saved": saved, "hurt": hurt, "flat": n - saved - hurt, "win_rate_pct": win_rate}

    overall = summarize(scored)
    by_cohort = {c: summarize([r for r in scored if r["cohort"] == c])
                 for c in ("cascade", "deliberate", "unknown")}
    by_cohort = {k: v for k, v in by_cohort.items() if v}

    dq = []
    if no_fill_price:
        dq.append(f"{len(no_fill_price)} stop-loss trades have no captured fill price "
                   f"(pre-dates live email capture, G26) and can never be scored: "
                   + ", ".join(sorted({t['ticker'] for t in no_fill_price})))
    if reconstructed:
        dq.append(f"QUARANTINED (G64): {len(reconstructed)} stop-loss trades carry "
                  f"price_source='reconstructed' -- a fill price inferred from a quantity diff, not "
                  f"an email confirmation. EXCLUDED from every figure in this file. They re-enter "
                  f"scoring automatically once smith-ledger confirms them: "
                  + ", ".join(sorted({t['ticker'] for t in reconstructed})))
    if untagged:
        dq.append(f"{len(untagged)} of {len(candidates)} scored stops carry NO price_source tag "
                  f"(predate the 2026-08-13 provenance convention). They are scored, because "
                  f"dropping them would blank most of the history -- but that means "
                  f"{len(untagged)/max(1,len(candidates))*100:.0f}% of this result still rests on "
                  f"prices no one has verified against a confirmation.")
    if unscored_missing_price:
        dq.append(f"{len(set(unscored_missing_price))} tickers had no current price supplied "
                   f"this run, stays unscored until provided: " + ", ".join(sorted(set(unscored_missing_price))))
    untimed = sum(1 for r in scored if r["cohort"] == "unknown")
    if untimed:
        dq.append(f"{untimed} scored stops lack a fill_time_utc so cannot be cohort-tagged "
                   "(pre-dates the 2026-08-06 timestamp backfill)")

    out = {
        "as_of": today.isoformat(), "overall": overall, "by_cohort": by_cohort,
        "stops": scored, "data_quality": dq,
    }
    out_path = args.out or os.path.join(args.base_dir, "stops_analysis.json")
    json.dump(out, open(out_path + ".tmp", "w"), indent=2)
    os.replace(out_path + ".tmp", out_path)
    emit({"written": out_path, "scored_count": len(scored), "overall": overall, "by_cohort": by_cohort})


def cmd_dismiss(args):
    """Mark one proposal dismissed_by_user by its stable id (see cmd_proposals). This is the
    write path behind a chat request like "dismiss P-014" -- the user's way of saying "don't
    keep proposing this" without the strategist re-adding it next run, since dismissed_by_user
    is a terminal status the dedup pass never reopens or merges into.
    """
    p_path = os.path.join(args.base_dir, "proposals.json")
    proposals = load_json(p_path, default={"proposals": [], "scorecard": {}})
    props = proposals.get("proposals", [])
    for pr in props:
        if pr.get("id") == args.id:
            if pr.get("status") not in ("open",):
                fail(f"proposal {args.id} is status={pr.get('status')!r}, not open -- nothing to dismiss")
            pr["status"] = "dismissed_by_user"
            stamp = f" | dismissed by user {datetime.now().isoformat(timespec='minutes')}"
            if args.reason:
                stamp += f": {args.reason}"
            pr["note"] = (pr.get("note", "") + stamp).strip(" |")
            proposals["proposals"] = props
            json.dump(proposals, open(p_path + ".tmp", "w"), indent=2)
            os.replace(p_path + ".tmp", p_path)
            emit({"dismissed": args.id, "action": pr.get("action"), "written": True})
            return
    fail(f"no proposal with id {args.id}")


# ---------------------------------------------------------------------------
# derisk -- the De-risk Queue (added 2026-07-31)
#
# Ranks every holding by how much damage it can do IF a drawdown comes, not by
# any attempt to predict one. Three transparent sub-scores, never a black box:
#
#   FRAGILITY  dollars-at-risk share (already embeds ATR x size) x how far the
#              position sits over its own 2xATR cap. "How hard does this hit."
#   STRETCH    1-month return RELATIVE TO SMH, positive side only. A name that
#              has run ahead of its own sector has something to give back; a
#              name lagging SMH has already been punished and is NOT a trim
#              candidate on stretch grounds. Deliberately relative, not
#              absolute: in a ~100% single-factor book an absolute RSI/52wk
#              screen flags all-or-nothing (2026-07-31: sentiment read "greed"
#              while 20 of 27 names sat >20% below their own 52wk highs, and the
#              only name an absolute screen flagged was DRAM -- on a known bad
#              52wk-low of $0. That is the failure mode this design avoids.)
#   FRICTION   cost of acting: LTCG proximity from lots.json (never trim a lot
#              weeks from its 24-month boundary when a comparable one is far
#              away), plus a dust-position discount.
#
# Sentiment is an URGENCY DIAL on the whole queue, never a trigger. Extreme
# greed raises the ranking; extreme fear damps it (do not sell into panic).
# It cannot manufacture stretch that does not exist per-name.
# ---------------------------------------------------------------------------
BAND_URGENCY = {"extreme_greed": 1.25, "greed": 1.0, "neutral": 0.9,
                "fear": 0.75, "extreme_fear": 0.5}
LTCG_MONTHS_DEFAULT = 24          # India: US-listed foreign shares
LTCG_DEFER_WINDOW_MONTHS = 6.0    # inside this, trimming forfeits a near boundary
DUST_USD_DEFAULT = 400.0


def _months_between(d_iso, today):
    try:
        d = datetime.strptime(d_iso, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None
    return (today.year - d.year) * 12 + (today.month - d.month) + (today.day - d.day) / 30.44


# ---------------------------------------------------------------------------
# lots -- deterministic FIFO with corporate-action support
# ---------------------------------------------------------------------------
# WHY THIS EXISTS (added 2026-08-15). Two things were wrong at once.
#
# 1. FIFO WAS BEING DONE BY AN LLM. lots.json is the desk's cost-basis and holding-period
#    record, and until now it was rebuilt by hand by the smith-ledger sub-agent. Consuming
#    lots oldest-first is pure deterministic arithmetic over data already on disk -- exactly
#    what the COMPUTE-FIRST PRINCIPLE says must never be an LLM's job. It stayed that way only
#    because nobody had written the engine.
#
# 2. THE LEDGER COULD NOT EXPRESS EVENTS THAT MOVE SHARES WITHOUT A TRADE. Share-class
#    conversions, splits, fractional-share credits and DRIP all change share counts and
#    generate NO buy/sell confirmation, so an email-sourced ledger simply cannot see them.
#    That produced two standing gaps: G71 (GOOG's FIFO runs -2.9919sh -- it "sold" three more
#    shares than it ever bought, across a GOOG->GOOGL conversion) and G68 (QCOM +3.0sh and
#    MSFT +1.5sh over-counted against the broker, with fractional-share activity visible in
#    the fills). Both are the same shape: a real event the schema had no row for.
#
# The corporate-action row closes that. Critically it CARRIES COST BASIS AND ACQUISITION DATE
# through a conversion or split -- a conversion is not a sale and a split is not a purchase,
# so neither restarts the LTCG holding-period clock. Getting that wrong would silently reset
# every affected lot's clock and corrupt the tax picture, which is worse than the gap it fixes.
#
# It also refuses to clamp. If a sell consumes more than exists, the old hand-FIFO floored at
# zero and moved on, which is how a phantom short stayed invisible until someone eyeballed a
# negative. Here it is recorded as a `phantom_short` and reported.

CA_TYPES = ("conversion", "split", "fractional_credit", "spinoff", "adjustment")


def _lot_sort_key(lot):
    """Oldest first. A lot with no date sorts FIRST -- synthetic pre-history lots from the
    2.9b backfill are by construction the oldest thing in the book, so consuming them first
    is both chronologically right and the conservative LTCG choice."""
    return (lot.get("date") or "0000-00-00", lot.get("price_usd") or 0)


# Smallest share quantity any broker actually records. Below this a residual is float noise
# from summing decimal fractions, not a missing transaction -- reporting it as a phantom short
# produced a "shortfall_qty: 0.0" row that read as a real defect (2026-08-15).
SHARE_EPS = 1e-6


def _consume_fifo(lot_list, qty, log, ticker, when):
    """Remove `qty` shares oldest-first. Returns (consumed_lots, shortfall).

    consumed_lots preserves each slice's original date and price so a conversion can carry
    them to the destination symbol. shortfall > 0 means the record claims more shares left
    than it ever recorded arriving -- surfaced, never silently floored at zero.
    """
    remaining, consumed = qty, []
    lot_list.sort(key=_lot_sort_key)
    while remaining > SHARE_EPS and lot_list:
        lot = lot_list[0]
        take = min(lot["qty"], remaining)
        consumed.append({"qty": take, "date": lot.get("date"), "price_usd": lot.get("price_usd")})
        lot["qty"] -= take
        remaining -= take
        if lot["qty"] <= SHARE_EPS:
            lot_list.pop(0)
    if remaining > SHARE_EPS:
        log.append({"ticker": ticker, "date": when, "shortfall_qty": round(remaining, 6),
                    "note": "sell/conversion consumed more shares than the record ever shows "
                            "arriving -- phantom short, NOT clamped to zero (G71 signature)"})
    return consumed, remaining


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


def cmd_history(args):
    """Authoritative 'was this ever held?' lookup, sourced from trades.json (G72).

    Built because the orchestrator told the user LITE was "never actually held" when the
    ledger carried 22 LITE trades. The false answer came from reading silence in
    state.thesis / state.signal_history as proof of absence -- but both are seeded from
    CURRENT holdings, so a fully-exited name is ALWAYS silent there. Absence of evidence in
    those two files is not evidence of absence; trades.json is the only file that can answer
    this, because it is the only one that records positions that no longer exist.
    """
    trades = load_json(os.path.join(args.base_dir, "trades.json"), default={"trades": []}).get("trades", [])
    state = load_json(os.path.join(args.base_dir, "state.json"), default={})
    lots = load_json(os.path.join(args.base_dir, "lots.json"), default={})
    # lots.json keys tickers at the TOP level; the metadata keys start with "_" or are scalars.
    holdings_now = {t for t, v in lots.items()
                    if isinstance(v, list) and sum((l.get("qty") or 0) for l in v) > SHARE_EPS}

    out = {}
    for tk in [t.strip().upper() for t in args.ticker.split(",") if t.strip()]:
        rows = sorted([r for r in trades if (r.get("ticker") or "").upper() == tk],
                      key=lambda r: (r.get("date") or "", r.get("fill_time_utc") or ""))
        if not rows:
            out[tk] = {"ever_held": False, "trade_count": 0,
                       "answer": f"{tk}: no trade of any kind in the ledger. Never held.",
                       "caveat": "Absence here is meaningful ONLY because trades.json is the "
                                 "authoritative record. Never answer this from state.thesis."}
            continue
        buys = [r for r in rows if (r.get("qty_change") or 0) > 0]
        sells = [r for r in rows if (r.get("qty_change") or 0) < 0]
        cas = [r for r in rows if r.get("type") == "corporate_action"]
        net = sum(r.get("qty_change") or 0 for r in rows)
        peak, run = 0.0, 0.0
        for r in rows:
            run += r.get("qty_change") or 0
            peak = max(peak, run)
        held = tk in holdings_now
        out[tk] = {
            "ever_held": True, "currently_held": held,
            "trade_count": len(rows), "buys": len(buys), "sells": len(sells),
            "corporate_actions": len(cas),
            "first_trade": rows[0].get("date"), "last_trade": rows[-1].get("date"),
            "peak_qty": round(peak, 6), "net_qty_now": round(net, 6),
            "answer": (f"{tk}: HELD SINCE {rows[0].get('date')} -- {len(rows)} trades "
                       f"({len(buys)} buys, {len(sells)} sells), peak {round(peak, 4)} shares."
                       if held else
                       f"{tk}: WAS held and is now EXITED -- {len(rows)} trades between "
                       f"{rows[0].get('date')} and {rows[-1].get('date')} "
                       f"({len(buys)} buys, {len(sells)} sells), peak {round(peak, 4)} shares."),
        }
    emit({"generated": str(date.today()), "source": "trades.json + lots.json",
          "tickers": out,
          "note": ("G72 fix. state.thesis and state.signal_history are seeded from CURRENT "
                   "holdings, so an exited name is silent in both by construction. Answer "
                   "'was this ever held' from THIS command only.")})


def cmd_lots(args):
    """Rebuild lots.json from trades.json by deterministic FIFO, honouring corporate actions.

    CORPORATE-ACTION ROW SHAPE (in trades.json; a row with no `type` is a plain trade, so
    every one of the existing 803 rows keeps working unchanged):

      {"date":"2026-06-15", "type":"corporate_action", "ca_type":"conversion",
       "ticker":"GOOG", "qty_change":-3.0,          # shares leaving this symbol
       "to_ticker":"GOOGL", "to_qty":3.0,           # shares arriving at that one
       "ratio":null,                                # split only: new shares per old
       "price_at_trade":null,                       # corporate actions have no fill price
       "reason":"corporate_action",
       "source":"brokerage statement 2026-06",      # REQUIRED -- this data is not in email
       "notes":"GOOG->GOOGL share-class conversion"}

    ca_type semantics:
      conversion        move shares between symbols, CARRYING basis and acquisition date.
                        Not a taxable sale; the holding-period clock does not restart.
      split             multiply every open lot by `ratio`, divide its per-share price by the
                        same. Total basis and every acquisition date unchanged.
      fractional_credit shares appearing with no purchase (DRIP, fractional program). Basis is
                        `price_at_trade` if stated, else 0 -- and 0 is FLAGGED, because a
                        zero-basis lot overstates future gains if it is wrong.
      spinoff           like conversion but the source keeps its shares; destination lots are
                        created dated the spinoff, basis 0 unless stated.
      adjustment        an explicit, sourced reconciliation to broker truth when the cause is
                        genuinely unknown. The honest escape hatch: it records that a delta was
                        applied and why, instead of force-matching lots and pretending the
                        record was always right. Always shows up in the output.
    """
    trades = load_json(os.path.join(args.base_dir, "trades.json"), default={"trades": []})
    rows = list(trades.get("trades", []))
    rows.sort(key=lambda r: (r.get("date") or "", r.get("fill_time_utc") or ""))

    lots, shorts, applied_ca, warnings = {}, [], [], []

    # G80 DETECTOR (added 2026-08-15). Any quantity derived as Amount / Price is arithmetically
    # invalid, because INDmoney's Amount includes SEC/FINRA fees. Proven twice: a share-based
    # order (2026-06-22 META, Amount/Price = 1.002954, Shares field = 1) and a dollar-based one
    # (2025-04-30 GOOG, Amount/Price = 0.626330953, Shares field = 0.62453024). It inflates buys,
    # understates sells, and was the root cause of most of G68 and G79.
    #
    # The rule forbidding it lives in smith-ledger.md -- but a prose rule is exactly what lapsed
    # here in the first place, and that file had ALREADY contradicted itself on this point for
    # months. So the compute layer now names the offending rows on every run. Cheap, and it
    # cannot quietly stop being true.
    # Split known-and-accepted residue from a genuine relapse. The 24 rows predating the rule
    # hardening were quantified at ~$29 of basis error total (~$12 on live positions, 0.027% of
    # book) and deliberately left rather than spending 20+ confirmation pulls on twelve dollars.
    # A row dated AFTER the cutoff means the forbidden method is BACK, which is an alarm, not
    # residue -- so the two are reported differently and the alarm is impossible to mistake for
    # the accepted noise.
    G80_CUTOFF = "2026-08-15"
    derived = [r for r in rows if r.get("qty_source") == "derived_amount_over_price"]
    old_rows = [r for r in derived if (r.get("date") or "") < G80_CUTOFF]
    new_rows = [r for r in derived if (r.get("date") or "") >= G80_CUTOFF]
    if new_rows:
        warnings.append(
            f"G80 RELAPSE -- {len(new_rows)} row(s) dated on/after {G80_CUTOFF} were reconstructed "
            f"with the FORBIDDEN Amount/Price method: "
            + ", ".join(f"{r.get('ticker')} {r.get('date')}" for r in new_rows[:8])
            + ". Amount includes SEC/FINRA fees, so this is arithmetically invalid, not merely "
              "approximate. Re-pull each confirmation and read its `Shares:` field. Do NOT model a "
              "fee ratio -- that is the same error one level up. See smith-ledger.md task 2.")
    if old_rows:
        by_tk = {}
        for r in old_rows:
            by_tk[r.get("ticker")] = by_tk.get(r.get("ticker"), 0) + 1
        warnings.append(
            f"G80 accepted residue: {len(old_rows)} pre-{G80_CUTOFF} row(s) still carry the old "
            f"Amount/Price derivation ("
            + ", ".join(f"{k} x{v}" for k, v in sorted(by_tk.items(), key=lambda kv: -kv[1]))
            + "). Quantified at ~$29 of cost-basis error in total, ~$12 of it on live positions "
              "(0.027% of book) -- knowingly left, not overlooked. Informational.")

    for r in rows:
        tk = r.get("ticker")
        if not tk:
            continue
        when = r.get("date")
        lots.setdefault(tk, [])
        rtype = r.get("type", "trade")

        if rtype != "corporate_action":
            q = r.get("qty_change") or 0
            if q > 0:
                lots[tk].append({"qty": q, "date": when, "price_usd": r.get("price_at_trade"),
                                 "price_source": r.get("price_source") or "trade"})
            elif q < 0:
                _consume_fifo(lots[tk], -q, shorts, tk, when)
            continue

        ca = r.get("ca_type")
        if ca not in CA_TYPES:
            warnings.append(f"{tk} {when}: unknown ca_type {ca!r} -- row ignored, nothing applied")
            continue
        if not r.get("source"):
            warnings.append(f"{tk} {when}: corporate action has no `source` -- this data cannot "
                            f"come from email, so an unsourced row is unverifiable")

        if ca == "split":
            ratio = r.get("ratio")
            if not ratio or ratio <= 0:
                warnings.append(f"{tk} {when}: split needs a positive `ratio` -- row ignored")
                continue
            for lot in lots[tk]:
                lot["qty"] *= ratio
                if lot.get("price_usd"):
                    lot["price_usd"] = lot["price_usd"] / ratio
            applied_ca.append({"date": when, "ca_type": ca, "ticker": tk, "ratio": ratio,
                               "note": "qty scaled, per-share basis inversely scaled; total "
                                       "basis and all acquisition dates preserved"})

        elif ca in ("conversion", "spinoff"):
            dst = r.get("to_ticker")
            if not dst:
                warnings.append(f"{tk} {when}: {ca} needs `to_ticker` -- row ignored")
                continue
            lots.setdefault(dst, [])
            out_q = abs(r.get("qty_change") or 0)
            in_q = r.get("to_qty")
            if in_q is None:
                in_q = out_q
            if ca == "conversion":
                moved, short = _consume_fifo(lots[tk], out_q, shorts, tk, when)
                got = sum(m["qty"] for m in moved)
                scale = (in_q / got) if got > 1e-9 else 1.0
                for m in moved:
                    # basis and acquisition date CARRY -- a conversion is not a purchase
                    lots[dst].append({
                        "qty": m["qty"] * scale,
                        "date": m["date"],
                        "price_usd": (m["price_usd"] / scale) if m.get("price_usd") and scale else m.get("price_usd"),
                        "price_source": "carried_through_conversion"})
                applied_ca.append({"date": when, "ca_type": ca, "from": tk, "to": dst,
                                   "qty_out": round(got, 6), "qty_in": round(in_q, 6),
                                   "shortfall": round(short, 6) if short else 0,
                                   "note": "basis and acquisition dates carried; LTCG clock NOT reset"})
            else:  # spinoff -- source keeps its shares
                lots[dst].append({"qty": in_q, "date": when,
                                  "price_usd": r.get("price_at_trade"),
                                  "price_source": "spinoff"})
                applied_ca.append({"date": when, "ca_type": ca, "from": tk, "to": dst,
                                   "qty_in": in_q,
                                   "note": "source position unchanged; destination dated the spinoff"})

        elif ca == "fractional_credit":
            q = r.get("qty_change") or 0
            px = r.get("price_at_trade")
            lots[tk].append({"qty": q, "date": when, "price_usd": px,
                             "price_source": "fractional_credit"})
            if px is None:
                warnings.append(f"{tk} {when}: fractional_credit has no price -- lot carries a "
                                f"null basis, which understates cost and overstates future gain")
            applied_ca.append({"date": when, "ca_type": ca, "ticker": tk, "qty": q})

        elif ca == "adjustment":
            q = r.get("qty_change") or 0
            if q > 0:
                lots[tk].append({"qty": q, "date": when, "price_usd": r.get("price_at_trade"),
                                 "price_source": "adjustment"})
            elif q < 0:
                _consume_fifo(lots[tk], -q, shorts, tk, when)
            applied_ca.append({"date": when, "ca_type": ca, "ticker": tk, "qty": q,
                               "source": r.get("source"), "notes": r.get("notes"),
                               "note": "EXPLICIT reconciliation to broker truth -- recorded, "
                                       "not force-matched"})

    # tidy
    out = {}
    for tk, ls in lots.items():
        keep = [{k: (round(v, 6) if isinstance(v, float) else v) for k, v in lot.items()}
                for lot in ls if lot["qty"] > 1e-9]
        if keep:
            keep.sort(key=_lot_sort_key)
            out[tk] = keep

    # reconcile against the broker, if a run's holdings were supplied
    recon, mismatches = None, []
    if args.holdings:
        h = load_json(args.holdings, default={})
        live = {r["ticker"]: r.get("qty") for r in h.get("holdings_inr", [])}
        for tk, q in live.items():
            ls = round(sum(l["qty"] for l in out.get(tk, [])), 6)
            if abs(ls - (q or 0)) > 1e-4:
                mismatches.append({"ticker": tk, "lots_sum": ls, "broker_qty": q,
                                   "delta": round(ls - (q or 0), 6)})
        # ALSO check the other direction (added during the 2026-08-15 cutover). The loop above
        # only walks tickers the broker reports, so a ticker the LEDGER thinks is still open
        # while the broker shows NO position at all was invisible -- and that is the more
        # alarming case, because it means a sell is missing entirely rather than partially.
        # The cutover surfaced PLTR carrying ~5.0sh across five lots and META ~1.0sh, both
        # fully exited per the broker. Neither would have been reported without this.
        orphans = []
        for tk, ls in out.items():
            if tk in live:
                continue
            q = round(sum(l["qty"] for l in ls), 6)
            if q > 1e-4:
                orphans.append({"ticker": tk, "lots_sum": q, "broker_qty": 0, "lots": len(ls),
                                "note": "ledger shows an open position the broker does not report "
                                        "-- a sell is missing from the trade record entirely"})
        recon = {"tickers_checked": len(live), "reconciled": len(live) - len(mismatches),
                 "mismatches": sorted(mismatches, key=lambda m: -abs(m["delta"])),
                 "orphaned_positions": sorted(orphans, key=lambda o: -o["lots_sum"])}

    written = None
    if args.write:
        path = os.path.join(args.base_dir, "lots.json")
        prev = load_json(path, default={})
        payload = {"schema_version": prev.get("schema_version", 1),
                   "_note": ("Rebuilt deterministically by `smith_math.py lots` from trades.json. "
                             "Do NOT hand-edit: re-running the engine overwrites it. Record "
                             "share-moving events that generate no buy/sell confirmation as "
                             "corporate_action rows in trades.json instead."),
                   "_rebuilt": str(date.today())}
        payload.update(out)
        tmp = path + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(payload, fh, indent=2)
        os.replace(tmp, path)
        written = path

    emit({"tickers": len(out),
          "total_lots": sum(len(v) for v in out.values()),
          "corporate_actions_applied": applied_ca,
          "phantom_shorts": shorts,
          "reconciliation": recon,
          "warnings": warnings,
          "written": written,
          "note": ("phantom_shorts are sells/conversions that consumed more than the record shows "
                   "arriving -- surfaced rather than clamped to zero. A non-empty list means the "
                   "trade record is missing share-creating events (see G68/G71).")})


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


def cmd_score(args):
    """Score past proposals on price outcome. The strategist's accountability loop.

    WHY THIS EXISTS (added 2026-08-15). SKILL.md section 7 has instructed the desk to
    "Score past (non-open) proposals at 30d/90d with outcome_pct + verdict (open|worked|missed)
    ... Compute per-proposal and aggregate strategist scorecard" since the file was written.
    No code ever did it. As of this build the book has produced **96 proposals, 9 of them
    actually executed or filled, and not one has an outcome** -- `outcome_pct` appeared nowhere
    in this script. The scorecard field existed, was loaded, was written back, and was always
    null; its `note` had grown into a five-entry log of "still zero proposals in the 30d/90d
    scoring window" stretching from 2026-07-18, an excuse that stopped being true weeks ago
    (the earliest cohort crossed 30 days on ~2026-08-12).

    The asymmetry this fixes: journal.json has scored SIGNALS since July and now carries real
    30-day hit rates (TARGET GAP 57.1% on n=14, MOMENTUM+VOLUME 60% on n=5). Signals are held
    to account; the sized dollar recommendations built ON those signals never were. A desk that
    measures its indicators but not its decisions is grading the easy half.

    METHOD -- deliberately the same shape as cmd_stops, which already works:
      * The orchestrator supplies prices via --prices-json (this script has no network, by
        design). A ticker with no price stays unscored and is NAMED in data_quality; it is
        never silently dropped and never guessed.
      * Verdict is DIRECTION-AWARE, because "the price went up" means opposite things for a BUY
        and a TRIM. A BUY works if price rose; a TRIM/SELL works if price fell (you avoided the
        drawdown); a HOLD works if the move stayed inside the noise band, since the whole claim
        of a HOLD is "nothing needed doing".
      * VERDICT_THRESHOLD_PCT (2.0) is reused from the journal scorer rather than inventing a
        second threshold, so a "worked" here means the same magnitude as a "worked" there.
      * Both 30d and 90d are computed when the age allows; a proposal older than 30 but younger
        than 90 scores 30d only and stays `open_90d`. Age is measured from the proposal date,
        not from when it was actioned -- the recommendation is what is being graded.

    HONESTY CONSTRAINTS, matching the charts' own rules:
      * `status: "dismissed_by_user"` is EXCLUDED from the scorecard. The user overriding a
        proposal is not the strategist being wrong, and counting it either way would corrupt
        the record -- but the count of exclusions is reported so the omission is visible.
      * `superseded` proposals are excluded as individual rows (the surviving row carries the
        idea) but their `history` is not double-counted, mirroring the dedup rule in
        cmd_proposals: one idea counts once.
      * A HOLD with size_usd 0 still scores -- "do nothing" is a real call with a real outcome.
    """
    p_path = os.path.join(args.base_dir, "proposals.json")
    proposals = load_json(p_path, default={"proposals": [], "scorecard": {}})
    props = proposals.get("proposals", [])
    prices = load_json(args.prices_json, default={}) if args.prices_json else {}
    today = (datetime.strptime(args.today, "%Y-%m-%d").date() if args.today else date.today())

    # statuses that represent a real, closed recommendation worth grading
    SCOREABLE = {"executed", "fulfilled", "filled", "auto_retired", "superseded", "deferred", "watch"}
    EXCLUDED = {"dismissed_by_user"}

    rows, unpriced, excluded_n, too_young = [], [], 0, 0
    for pr in props:
        st = pr.get("status")
        if st in EXCLUDED:
            excluded_n += 1
            continue
        if st == "open" or st not in SCOREABLE:
            continue
        tk, p0 = pr.get("ticker"), pr.get("price_at_proposal")
        d0 = _proposal_parse_date(pr.get("date", ""))
        if not tk or not p0 or not d0:
            continue  # cannot grade without an anchor; not an error, just unscoreable
        age = (today - d0).days
        if age < 30:
            too_young += 1
            continue
        now = prices.get(tk)
        if now is None:
            unpriced.append(tk)
            continue
        move = (now - p0) / p0 * 100.0
        direction = pr.get("direction_bucket") or _proposal_direction(pr.get("action"))
        # direction-aware: the same move is a win or a loss depending on what was advised
        if direction == "BUY":
            signed = move
        elif direction in ("TRIM", "SELL"):
            signed = -move
        else:  # HOLD -- the claim is "no action needed", so small moves vindicate it
            signed = VERDICT_THRESHOLD_PCT - abs(move)
        # ANCHOR PLAUSIBILITY GUARD (added 2026-08-15, first run of this scorer).
        # The very first scoring pass produced a "TRIM TSM missed by 39.4%" row off a
        # price_at_proposal of $305.87 dated 2026-07-14. TSM traded $386-$448 that week and
        # closed $398.37; it never saw $305.87. The anchor was corrupt, and on a sample of
        # seven that single row set the ENTIRE trim-accuracy figure (avg benefit -19.54%,
        # accuracy 0%). A bad reading was about to become the desk's self-assessment.
        # This is the same principle the charts already enforce -- a row whose value_trust is
        # not ok is drawn ringed and EXCLUDED from scales and win/loss counts, never allowed to
        # set an axis. Same rule here: an implausible move is quarantined for review, reported
        # in full so it is visible, and kept OUT of the aggregate until a human confirms the
        # anchor. Real 30-day moves of this size do happen (NBIS ran +34% this month), so this
        # is deliberately a REVIEW flag, not a discard -- the row is never silently dropped.
        if abs(move) > ANCHOR_REVIEW_PCT:
            verdict = "needs_anchor_review"
        else:
            verdict = ("worked" if signed > VERDICT_THRESHOLD_PCT
                       else "missed" if signed < -VERDICT_THRESHOLD_PCT else "neutral")
        row = {"id": pr.get("id"), "ticker": tk, "direction": direction, "status": st,
               "date": str(d0), "age_days": age, "price_at_proposal": round(p0, 4),
               "price_now": round(now, 4), "move_pct": round(move, 2),
               "signed_benefit_pct": round(signed, 2), "verdict": verdict,
               "window": "90d" if age >= 90 else "30d"}
        rows.append(row)
        pr["outcome_pct"] = None if verdict == "needs_anchor_review" else round(signed, 2)
        pr["outcome_verdict"] = verdict
        pr["outcome_window"] = row["window"]
        pr["outcome_scored_on"] = str(today)

    def agg(subset):
        n = len(subset)
        if not n:
            return None
        w = sum(1 for r in subset if r["verdict"] == "worked")
        m = sum(1 for r in subset if r["verdict"] == "missed")
        return {"n": n, "worked": w, "missed": m, "neutral": n - w - m,
                "accuracy_pct": round(w / n * 100, 1),
                "avg_benefit_pct": round(sum(r["signed_benefit_pct"] for r in subset) / n, 2)}

    # quarantined rows are reported but never counted -- see the anchor guard above
    graded = [r for r in rows if r["verdict"] != "needs_anchor_review"]
    review = [r for r in rows if r["verdict"] == "needs_anchor_review"]
    trims = [r for r in graded if r["direction"] in ("TRIM", "SELL")]
    buys = [r for r in graded if r["direction"] == "BUY"]
    holds = [r for r in graded if r["direction"] == "HOLD"]
    scorecard = {
        "as_of": str(today),
        "trim_accuracy_30d": (agg(trims) or {}).get("accuracy_pct"),
        "add_accuracy_30d": (agg(buys) or {}).get("accuracy_pct"),
        "overall_accuracy_30d": (agg(graded) or {}).get("accuracy_pct"),
        "by_direction": {"TRIM/SELL": agg(trims), "BUY": agg(buys), "HOLD": agg(holds)},
        "overall": agg(graded),
        "scored_count": len(graded),
        "quarantined_anchor_review": len(review),
        "excluded_dismissed_by_user": excluded_n,
        "not_yet_30d": too_young,
        "note": ("Direction-aware: a TRIM 'worked' if the price FELL after it, a BUY if it ROSE, "
                 "a HOLD if the move stayed inside the +/-%.1f%% noise band. Threshold shared with "
                 "the journal scorer so 'worked' means the same magnitude in both. "
                 "dismissed_by_user proposals are excluded -- a user override is not a strategist "
                 "error." % VERDICT_THRESHOLD_PCT),
    }
    proposals["scorecard"] = scorecard

    dq = []
    if unpriced:
        u = sorted(set(unpriced))
        dq.append(f"{len(u)} ticker(s) had no price supplied and stay unscored until a later run "
                  f"provides one (never guessed, never dropped): {', '.join(u[:12])}"
                  f"{'...' if len(u) > 12 else ''}")
    if too_young:
        dq.append(f"{too_young} proposal(s) are under 30 days old -- not yet in the scoring window.")
    if review:
        dq.append("QUARANTINED pending anchor review, excluded from the scorecard: "
                  + "; ".join(f"{r['id']} {r['direction']} {r['ticker']} implies {r['move_pct']:+.1f}% "
                              f"from a ${r['price_at_proposal']:.2f} anchor" for r in review)
                  + ". Verify the anchor against price history before trusting these.")
    if not rows:
        dq.append("nothing scoreable this run: no closed proposal has both a price anchor and a "
                  "supplied current price.")
    scorecard["data_quality"] = dq

    if not args.dry_run:
        tmp = p_path + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(proposals, fh, indent=2)
        os.replace(tmp, p_path)

    emit({"scored_count": len(rows), "scorecard": scorecard, "rows": rows,
          "written": (not args.dry_run) and p_path or None, "data_quality": dq})


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

        t_entry = thesis.get(t, "")
        if isinstance(t_entry, dict):
            # newer evidence-schema entries carry status as an explicit key rather than
            # a trailing "| status" suffix on a bare string (see G58) -- read it directly.
            t_status = (t_entry.get("status") or "").strip().lower() or None
        else:
            t_status = (t_entry or "").split("|")[-1].strip() or None

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


def _thesis_status(entry):
    """Newer evidence-schema entries carry status as an explicit key; older ones as a trailing
    '| status' suffix on a bare string (see G58). Both shapes are live in state.json."""
    if isinstance(entry, dict):
        return (entry.get("status") or "").strip().lower() or None
    return ((entry or "").rpartition("|")[2].strip().lower()) or None


def _avg_cost_from_lots(tlots):
    """Weighted average cost over lots with a REAL price. Returns
    (avg_cost_usd, priced_qty, unpriced_qty). Synthetic null-price lots from the 2.9b backfill
    (quantity that predates available email history) are counted separately, never imputed --
    a ratchet computed against a guessed basis would move a real stop on a fabricated number."""
    cost, priced_qty, unpriced_qty = 0.0, 0.0, 0.0
    for lot in tlots or []:
        q = lot.get("qty") or 0.0
        px = lot.get("price_usd")
        if px is None:
            unpriced_qty += q
        else:
            cost += q * px
            priced_qty += q
    avg = (cost / priced_qty) if priced_qty else None
    return avg, priced_qty, unpriced_qty


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
        status = _thesis_status(thesis.get(ticker))
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
                        if _thesis_status(thesis.get(ot)) == "broken":
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

    sp = sub.add_parser("lots", help="rebuild lots.json from trades.json by FIFO, honouring corporate actions")
    sp.add_argument("--base-dir", default=DEFAULT_BASE)
    sp.add_argument("--holdings", default=None,
                    help="a run's holdings.json, to reconcile lot sums against broker quantities")
    sp.add_argument("--write", action="store_true", help="write lots.json (default: dry run)")

    sp = sub.add_parser("maxpain", help="max-pain + put/call OI ratio from a saved options chain (G18)")
    sp.add_argument("--chain", required=True, help="JSON chain file: {underlyingPrice, data:{expiry:{calls,puts}}}")
    sp.add_argument("--symbol", default=None)

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
         "history": cmd_history, "maxpain": cmd_maxpain,
         "sentiment": cmd_sentiment, "validate": cmd_validate, "proposals": cmd_proposals,
         "dismiss": cmd_dismiss, "stops": cmd_stops}[args.cmd](args)
    except Exception as e:  # noqa: BLE001 -- deliberate: any failure degrades gracefully
        fail(f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
