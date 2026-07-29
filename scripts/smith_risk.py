#!/usr/bin/env python3
"""
Agent Smith -- shared risk/rotation helpers.

Imported by smith_math.py (the `risk`/`rotation` subcommands) and by
smith_charts.py (the treemap's over-cap outline), so the ATR-stop/cap formula
and the signal-polarity table exist in exactly one place. Pure functions, no
I/O, stdlib only.

SIGNAL_POLARITY is deliberately NOT the same table as smith_math.py's
BUCKET_DIRECTION. BUCKET_DIRECTION grades a single historical journal flag's
30-day realized move against an assumed expected direction -- an existing,
in-production scoring convention that already has historical grades computed
against it, so it is left untouched here. SIGNAL_POLARITY answers a different
question for rotation analysis: does a ticker's CURRENT, FULL set of active
signal buckets read net-bullish or net-bearish right now? For that question a
bucket only counts if it's unambiguously directional by its own definition
(skill/agents/smith-signals.md lines 26-34). MOMENTUM+VOLUME ("|day|>=4%") and
TARGET GAP ("...>=15% either direction") are explicitly bidirectional by that
definition and are excluded here, even though BUCKET_DIRECTION maps both to
"up" for its narrower, different purpose. This divergence is intentional --
see the G34 plan notes -- not an oversight.
"""

SIGNAL_POLARITY = {
    "bullish": {
        "BREAKOUT", "STRONG UPTREND", "NEW TAILWINDS", "PEER LEADER",
        "OVERSOLD BOUNCE", "REVERSAL - BUY WATCH",
    },
    "bearish": {
        "BREAKDOWN", "STRONG DOWNTREND", "NEW HEADWINDS", "PEER LAGGARD",
        "OVERBOUGHT PULLBACK", "REVERSAL - TRIM WATCH", "CAPITAL ROTATION",
    },
    "ambiguous": {
        "POLICY IMPACT", "INSIDER ACTIVITY", "EARNINGS PROXIMITY",
        "MOMENTUM+VOLUME", "TARGET GAP",
    },
}


def classify_signal_polarity(buckets):
    """buckets: list of bucket-name strings, as stored in state.json's
    signal_history. Returns {bullish, bearish, ambiguous, unrecognized, net}."""
    buckets = buckets or []
    bullish = [b for b in buckets if b in SIGNAL_POLARITY["bullish"]]
    bearish = [b for b in buckets if b in SIGNAL_POLARITY["bearish"]]
    ambiguous = [b for b in buckets if b in SIGNAL_POLARITY["ambiguous"]]
    known = SIGNAL_POLARITY["bullish"] | SIGNAL_POLARITY["bearish"] | SIGNAL_POLARITY["ambiguous"]
    unrecognized = [b for b in buckets if b not in known]
    return {
        "bullish": bullish, "bearish": bearish, "ambiguous": ambiguous,
        "unrecognized": unrecognized, "net": len(bullish) - len(bearish),
    }


def stop_and_cap(atr_pct, price_usd, qty, total_book_usd, policy):
    """
    Implements policy.json's stop_loss_framework:
      stop_distance_pct = max(2 * atr_pct, 3.0)
      stop_price_usd    = price_usd * (1 - stop_distance_pct/100)
      max_position_usd  = (risk_per_position_pct_of_book/100 * total_book_usd)
                           / (stop_distance_pct/100)
      headroom_usd      = max_position_usd - market_value_usd
      over_cap          = market_value_usd > max_position_usd

    atr_pct is None (no live ATR20 cache entry for this ticker) -> every
    numeric risk field is None, over_cap is False, data_quality_flag is True.
    Never estimate a missing ATR -- the compute-first guardrail this whole
    project runs on. Caller is responsible for surfacing data_quality_flag.
    """
    framework = (policy or {}).get("stop_loss_framework", {})
    risk_pct_of_book = framework.get("risk_per_position_pct_of_book", 0.5)

    market_value_usd = None
    if qty is not None and price_usd is not None:
        market_value_usd = qty * price_usd

    if atr_pct is None or price_usd is None or not total_book_usd:
        return {
            "atr20_pct": None, "stop_distance_pct": None, "stop_price_usd": None,
            "max_position_usd": None, "headroom_usd": None, "over_cap": False,
            "position_open_risk_usd": None, "cap_multiple": None,
            "market_value_usd": round(market_value_usd, 2) if market_value_usd is not None else None,
            "data_quality_flag": True,
        }

    stop_distance_pct = max(2 * atr_pct, 3.0)
    stop_price_usd = price_usd * (1 - stop_distance_pct / 100)
    max_position_usd = (risk_pct_of_book / 100 * total_book_usd) / (stop_distance_pct / 100)
    mv = market_value_usd or 0
    headroom_usd = max_position_usd - mv
    over_cap = mv > max_position_usd
    position_open_risk_usd = mv * stop_distance_pct / 100
    cap_multiple = (mv / max_position_usd) if max_position_usd else None

    return {
        "atr20_pct": atr_pct,
        "stop_distance_pct": round(stop_distance_pct, 3),
        "stop_price_usd": round(stop_price_usd, 4),
        "max_position_usd": round(max_position_usd, 2),
        "headroom_usd": round(headroom_usd, 2),
        "over_cap": over_cap,
        "position_open_risk_usd": round(position_open_risk_usd, 2),
        "cap_multiple": round(cap_multiple, 3) if cap_multiple is not None else None,
        "market_value_usd": round(mv, 2),
        "data_quality_flag": False,
    }


def rotation_bucket(over_cap, thesis_status, net_signal):
    """Deterministic classification, exact precedence:
    1. over_cap always wins -> "trim_risk_cap", regardless of thesis/signal.
    2. strengthening thesis + net-bullish signal -> "accumulate".
    3. watch thesis + net-bearish signal -> "rotate_out".
    4. everything else -> None ("mixed", not chipped)."""
    if over_cap:
        return "trim_risk_cap"
    ts = (thesis_status or "").strip().lower()
    if ts == "strengthening" and net_signal > 0:
        return "accumulate"
    if ts == "watch" and net_signal < 0:
        return "rotate_out"
    return None
