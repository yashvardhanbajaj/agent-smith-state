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

Usage:
  smith_math.py book        --base-dir DIR --run-dir DIR [--lots lots.json]
  smith_math.py journal     --base-dir DIR --run-dir DIR [--today YYYY-MM-DD]
  smith_math.py attribution --base-dir DIR --run-dir DIR
  smith_math.py drift       --base-dir DIR --run-dir DIR
  smith_math.py sentiment   --base-dir DIR --market-inputs market_inputs.json
"""
import argparse
import json
import math
import os
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


def load_json(path, default=None):
    if not os.path.exists(path):
        if default is not None:
            return default
        raise FileNotFoundError(path)
    with open(path) as f:
        return json.load(f)


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
            "market_cap": r.get("market_cap", ""),
        })
    positions.sort(key=lambda p: -p["weight_pct"])

    top3 = [{"ticker": p["ticker"], "weight_pct": p["weight_pct"]} for p in positions[:3]]
    top5_pct = round(sum(p["weight_pct"] for p in positions[:5]), 3)
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

    # track full exits (in prior, not in current)
    for prior in state.get("holdings", []):
        if prior["ticker"] not in current_holdings:
            qty_changes.append({
                "ticker": prior["ticker"], "prior_qty": prior.get("qty"), "current_qty": 0.0,
                "ratio": 0.0, "likely_corporate_action": False,
            })

    # track new entries (in current, not in prior)
    for p in positions:
        if p["ticker"] not in prior_holdings:
            qty_changes.append({
                "ticker": p["ticker"], "prior_qty": 0.0, "current_qty": p["qty"],
                "ratio": None, "likely_corporate_action": False,
            })

    # load trade rationales from trades.json if present (FIXED 1.2: 2026-07-26)
    trades = load_json(os.path.join(args.base_dir, "trades.json"), default={})
    trade_reasons = {}  # ticker -> reason
    for trade in trades.get("trades", []):
        t = trade.get("ticker")
        if t:
            trade_reasons[t] = trade.get("reason", "UNCAPTURED")

    # attach trade rationale to qty_changes
    for qc in qty_changes:
        if qc["ticker"] in trade_reasons:
            qc["trade_reason"] = trade_reasons[qc["ticker"]]

    data_quality = []
    if not recon["persist_safe"]:
        data_quality.append("PERSIST BLOCKED (G3): " + "; ".join(recon.get("breaches", [])))
    if beta_missing:
        data_quality.append(f"betas defaulted to 1.0 for {len(beta_missing)} names (no data_cache entry): {', '.join(beta_missing[:8])}{'...' if len(beta_missing) > 8 else ''}")
    if not lots:
        data_quality.append("lots.json absent/empty -- LTCG flags unavailable (standing gap)")

    emit({
        "value_usd": value_usd, "pnl_pct": pnl_pct, "count": count,
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

    prior_holdings = {h["ticker"]: h for h in state.get("holdings", [])}
    rows = {r["ticker"]: r for r in holdings["holdings_inr"]}
    flow_usd = 0.0
    qty_changes = []
    for ticker, r in rows.items():
        prior = prior_holdings.get(ticker)
        if prior is None or prior.get("qty") is None or not r.get("qty"):
            continue
        qty_diff = r["qty"] - prior["qty"]
        if abs(qty_diff) < 1e-6:
            continue
        ratio = r["qty"] / prior["qty"] if prior["qty"] else None
        is_split_like = ratio is not None and abs(ratio - round(ratio)) < 0.02 and round(ratio) != 1
        price_usd = r["market_value_inr"] / r["qty"] / usdinr
        entry = {"ticker": ticker, "qty_diff": round(qty_diff, 6), "likely_corporate_action": bool(is_split_like)}
        qty_changes.append(entry)
        if not is_split_like:
            flow_usd += qty_diff * price_usd

    residual = value_delta - fx_effect - flow_usd

    result.update({
        "value_delta_usd": round(value_delta, 2),
        "fx_effect_usd": round(fx_effect, 2),
        "flow_usd": round(flow_usd, 2),
        "residual_market_move_usd": round(residual, 2),
        "qty_changes": qty_changes,
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
        body, _, status = (thesis.get(ticker, "") or "").rpartition("|")
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
    ("REBUILD", "HOLD"), ("STAGE", "BUY"), ("INITIATE", "BUY"), ("DEPLOY", "BUY"),
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
    # backfill from the action text: last all-caps token 2-5 chars is almost always the symbol
    words = (pr.get("action") or "").replace("(", " ").replace(")", " ").split()
    for w in reversed(words):
        wc = w.strip(".,")
        if wc.isupper() and 2 <= len(wc) <= 5 and wc not in ("BUY", "TRIM", "EXIT", "ADD", "HOLD", "NO"):
            return wc
    return None


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

    for i in to_supersede:
        if props[i].get("status") == "open":
            props[i]["status"] = "superseded"

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

    for pr in props:
        if pr.get("status") != "open":
            continue
        score, reasons = 0, []
        ticker, bucket, rc = pr.get("ticker"), pr.get("direction_bucket", "HOLD"), pr.get("repeat_count", 1)
        rpos = risk_by_ticker.get(ticker) if ticker else None
        cluster = rpos.get("cluster") if rpos else pr.get("cluster")
        if rpos and rpos.get("over_cap"):
            score += 3
            reasons.append(f"{ticker} at {rpos.get('cap_multiple', 0):.2f}x its ATR risk cap")
        if cluster and cluster in cluster_breach:
            cb = cluster_breach[cluster]
            score += 2
            reasons.append(f"{cluster} {'over' if cb.get('breach_edge')=='over' else 'under'} band "
                            f"({cb.get('drift_pt', 0):+.1f}pt)")
        if cash_short and bucket in ("TRIM", "SELL"):
            score += 2
            reasons.append(f"cash short at {_cash_pct:.1f}% vs a [{_cash_band[0]},{_cash_band[1]}]% band "
                           "-- this also rebuilds it")
        if cash_excess and bucket == "BUY":
            score += 2
            reasons.append(f"cash in excess at {_cash_pct:.1f}% vs a [{_cash_band[0]},{_cash_band[1]}]% band "
                           "-- deploying is the live problem, not raising more")
        if rc >= 3:
            score += 2
            reasons.append(f"recommended {rc}x, still unactioned")
        elif rc == 2:
            score += 1
            reasons.append(f"recommended {rc}x, still unactioned")
        if bucket == "SELL":
            score += 1
        if bucket == "BUY" and score == 0:
            score -= 1
            reasons.append("discretionary add -- no active breach behind it")
        pr["priority_score"] = score
        pr["priority"] = "HIGH" if score >= 4 else "MEDIUM" if score >= 2 else "LOW"
        pr["priority_reasons"] = reasons
        if cluster:
            pr["cluster"] = cluster

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
        cl = cluster_breach.get(cluster) if cluster else None
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
            # A trim exists to cure one of exactly two structural problems: a position over its
            # own ATR risk cap, or a cluster outside its policy band. If NEITHER is true today,
            # the trim has nothing left to fix.
            if not over_cap and not cl:
                why = (f"neither trigger is live: {ticker} is within its ATR risk cap"
                       + (f" and {cluster} is inside its policy band" if cluster else "")
                       + " -- the structural reason for this trim has cleared")
        elif bucket == "BUY":
            # An "initiate"/"new position" buy is self-evidently done once the name is held.
            if ticker and ticker in current_tickers and any(
                    w in action_l for w in ("initiate", "new position", "open a position")):
                why = f"{ticker} is now held -- this proposed initiating a position that already exists"
            # A cluster-fill buy is done once the cluster is back inside its band.
            elif cluster and not cl and any(w in action_l for w in ("top up", "fill", "stage", "deploy")):
                why = f"{cluster} is back inside its policy band -- the underweight this filled has cleared"
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
        if not live:
            live.append("no active structural trigger -- kept open on the strategist's judgement, not a breach")
        pr["still_valid_because"] = live
        pr["review_flags"] = flags
        pr["revalidated_on"] = str(today_date)

    proposals["proposals"] = props
    json.dump(proposals, open(p_path + ".tmp", "w"), indent=2)
    os.replace(p_path + ".tmp", p_path)

    open_now = [pr for pr in props if pr.get("status") == "open"]
    priority_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for pr in open_now:
        priority_counts[pr.get("priority", "LOW")] += 1

    emit({"proposals_count": len(props), "superseded_count": len(to_supersede), "changes_made": len(to_supersede),
          "auto_retired_count": len(retired), "auto_retired": retired,
          "open_count": len(open_now), "priority_counts": priority_counts, "written": True})


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

        raw.append({"ticker": t, "market_value_usd": round(mv, 2),
                    "cluster": sector_map.get(t), "thesis_status": (thesis.get(t, "") or "").split("|")[-1].strip() or None,
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


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    for name in ("book", "journal", "attribution", "drift", "risk", "rotation", "derisk"):
        sp = sub.add_parser(name)
        sp.add_argument("--base-dir", default=DEFAULT_BASE)
        sp.add_argument("--run-dir", required=True, help="this run's directory containing holdings.json")
        if name == "book":
            sp.add_argument("--lots", default=None)
        if name in ("journal", "derisk"):
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

    args = p.parse_args()
    try:
        {"book": cmd_book, "journal": cmd_journal, "attribution": cmd_attribution,
         "drift": cmd_drift, "risk": cmd_risk, "rotation": cmd_rotation, "derisk": cmd_derisk,
         "sentiment": cmd_sentiment, "validate": cmd_validate, "proposals": cmd_proposals,
         "dismiss": cmd_dismiss}[args.cmd](args)
    except Exception as e:  # noqa: BLE001 -- deliberate: any failure degrades gracefully
        fail(f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
