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

    over_cap = []  # populated by caller against policy; report raw >10% here as a generic flag
    over_10pct = [{"ticker": p["ticker"], "weight_pct": p["weight_pct"]} for p in positions if p["weight_pct"] > 10]

    peak_value_usd = max(prior_us.get("peak_value_usd", value_usd), value_usd)
    drawdown_pct = round((value_usd - peak_value_usd) / peak_value_usd * 100, 3) if peak_value_usd else 0.0

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
                except (KeyError, ValueError):
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

    data_quality = []
    if beta_missing:
        data_quality.append(f"betas defaulted to 1.0 for {len(beta_missing)} names (no data_cache entry): {', '.join(beta_missing[:8])}{'...' if len(beta_missing) > 8 else ''}")
    if not lots:
        data_quality.append("lots.json absent/empty -- LTCG flags unavailable (standing gap)")

    emit({
        "value_usd": value_usd, "pnl_pct": pnl_pct, "count": count,
        "usdinr": usdinr, "usdinr_drift_pct": usdinr_drift_pct,
        "top3": top3, "top5_pct": top5_pct, "top10_pct": top10_pct,
        "over_10pct": over_10pct, "beta": portfolio_beta,
        "risk_concentration": risk_concentration,
        "peak_value_usd": round(peak_value_usd, 2), "drawdown_pct": drawdown_pct,
        "wallet_usd": wallet_usd, "wallet_pct": wallet_pct,
        "ltcg_flags": ltcg_flags,
        "market_cap_allocation": market_cap_alloc,
        "qty_changes": qty_changes, "est_net_flows_usd": round(est_net_flows_usd, 2),
        "positions": positions,
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

    emit({
        "journal_updates": updates,
        "bucket_hit_rates": bucket_hit_rates,
        "name_bucket_grades": name_bucket_grades,
        "data_quality": [] if price_by_ticker else ["no current prices available -- all entries left open"],
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


def cmd_validate(args):
    policy = load_json(os.path.join(args.base_dir, "policy.json"), default=None)
    if policy is None:
        emit({"policy_present": False, "defects": ["no policy.json"]})
        return
    defects = validate_policy(policy)
    emit({
        "policy_present": True,
        "policy_confirmed": policy.get("confirmed", False),
        "policy_as_of": policy.get("as_of"),
        "clean": not defects,
        "defect_count": len(defects),
        "defects": defects,
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

    max_single = policy.get("max_single_position_pct")
    position_breaches = []
    for r in rows:
        if max_single is not None and r["weight_pct"] > max_single:
            position_breaches.append({"ticker": r["ticker"], "actual_pct": round(r["weight_pct"], 3),
                                       "cap_pct": max_single, "drift_pt": round(r["weight_pct"] - max_single, 3)})

    cash_band = policy.get("cash_band_pct", [None, None])
    cash_pct = round(wallet_usd / total_book_usd * 100, 3) if total_book_usd else 0.0
    cash_breach = (cash_band[0] is not None and cash_pct < cash_band[0]) or \
                  (cash_band[1] is not None and cash_pct > cash_band[1])

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

    prior_us = state.get("us", {})
    peak_value_usd = max(prior_us.get("peak_value_usd", value_usd), value_usd)
    drawdown_pct = round((value_usd - peak_value_usd) / peak_value_usd * 100, 3) if peak_value_usd else 0.0
    warn = policy.get("drawdown_warn_pct", 15)
    risk_off = policy.get("drawdown_risk_off_pct", 25)
    if abs(drawdown_pct) >= risk_off:
        risk_off_status = "risk_off"
    elif abs(drawdown_pct) >= warn:
        risk_off_status = "warn"
    else:
        risk_off_status = "normal"

    emit({
        "policy_present": True, "policy_confirmed": policy.get("confirmed", False),
        "policy_defects": policy_defects,
        "policy_valid": not policy_defects,
        "cluster_target_denominator": policy.get("cluster_target_denominator", "UNDECLARED"),
        "cluster_table": sorted(cluster_table, key=lambda c: c["breach"], reverse=True),
        "position_breaches": position_breaches,
        "cash_pct": cash_pct, "cash_band_pct": cash_band, "cash_breach": cash_breach,
        "cash_pct_denominator": "total_book",
        "ai_capex_pct": ai_capex_pct, "ai_capex_cap_pct": ai_cap, "ai_capex_breach": ai_capex_breach,
        "ai_capex_denominator": ai_denom,
        "ai_capex_pct_of_equity": ai_capex_pct_equity,
        "ai_capex_pct_of_total_book": ai_capex_pct_total_book,
        "drawdown_pct": drawdown_pct, "risk_off_status": risk_off_status,
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


# ---------------------------------------------------------------------------
def cmd_proposals(args):
    """Apply lifecycle rules to proposals.json: auto-supersede duplicates, auto-expire old,
    auto-void when cited breach clears or position changes materially.
    FIXED 2026-07-26 (1.6): Tier 1 defect — proposals accumulated as stale duplicates.
    """
    proposals = load_json(os.path.join(args.base_dir, "proposals.json"), default={"proposals": [], "scorecard": {}})
    drift = load_json(os.path.join(args.run_dir, "compute_drift.json"), default={})
    holdings = load_json(os.path.join(args.run_dir, "holdings.json"), default={"holdings_inr": []})

    props = proposals.get("proposals", [])
    today_date = datetime.strptime(args.today, "%Y-%m-%d").date() if args.today else date.today()
    current_tickers = {h["ticker"] for h in holdings.get("holdings_inr", [])}
    live_breaches = {c["cluster"] for c in drift.get("cluster_table", []) if c.get("breach")}

    seen = {}  # (date, action, ticker) -> index of first occurrence
    to_supersede = set()

    for i, pr in enumerate(props):
        if pr.get("status") != "open":
            continue
        key = (pr.get("date"), pr.get("action"), pr.get("ticker"))
        if key in seen:
            # duplicate of an earlier proposal — supersede this one
            to_supersede.add(i)
        else:
            seen[key] = i

        # check expiry: 5 trading days since proposal (rough: 7 calendar days)
        try:
            prop_date = datetime.strptime(pr.get("date", ""), "%Y-%m-%dT%H:%M").date()
        except (ValueError, TypeError):
            try:
                prop_date = datetime.strptime(pr.get("date", ""), "%Y-%m-%d").date()
            except (ValueError, TypeError):
                prop_date = None
        if prop_date and (today_date - prop_date).days > 7:
            to_supersede.add(i)
            if "note" not in pr or "auto-expired" not in pr["note"]:
                pr["note"] = pr.get("note", "") + " | auto-expired after 7 calendar days"

        # check void: cited breach no longer exists
        if pr.get("action", "").startswith("Trim"):
            breach_cluster = pr.get("rationale", "").split("(")[0].strip() if pr.get("rationale") else None
            if breach_cluster and breach_cluster not in live_breaches:
                to_supersede.add(i)
                if "auto-voided" not in pr.get("note", ""):
                    pr["note"] = pr.get("note", "") + " | auto-voided — cited breach cleared"

        # check void: position exited
        if pr.get("ticker") and pr.get("ticker") not in current_tickers:
            to_supersede.add(i)
            if "auto-voided" not in pr.get("note", ""):
                pr["note"] = pr.get("note", "") + " | auto-voided — position exited"

    for i in to_supersede:
        if props[i].get("status") == "open":
            props[i]["status"] = "superseded"

    emit({"proposals_count": len(props), "superseded_count": len(to_supersede), "changes_made": len(to_supersede)})


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    for name in ("book", "journal", "attribution", "drift"):
        sp = sub.add_parser(name)
        sp.add_argument("--base-dir", default=DEFAULT_BASE)
        sp.add_argument("--run-dir", required=True, help="this run's directory containing holdings.json")
        if name == "book":
            sp.add_argument("--lots", default=None)
        if name == "journal":
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

    args = p.parse_args()
    try:
        {"book": cmd_book, "journal": cmd_journal, "attribution": cmd_attribution,
         "drift": cmd_drift, "sentiment": cmd_sentiment, "validate": cmd_validate, "proposals": cmd_proposals}[args.cmd](args)
    except Exception as e:  # noqa: BLE001 -- deliberate: any failure degrades gracefully
        fail(f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
