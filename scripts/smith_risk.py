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


# ---------------------------------------------------------------------------
# THESIS ENTRY SHAPE -- ONE canonical reader for the whole desk (added 2026-08-16)
# ---------------------------------------------------------------------------
# A state.thesis entry has had TWO shapes since G58 introduced the evidence schema:
#   legacy:  "one-liner prose | status"        (a bare string)
#   current: {"status","thesis","evidence_for","evidence_against","verified",...}
#
# That dual shape was reimplemented FOUR separate times -- twice inline in smith_math
# (cmd_rotation, cmd_derisk), once as smith_math._thesis_status, once as a nested closure in
# smith_dashboard -- and they had already drifted apart:
#
#   * smith_math's versions returned `rpartition("|")[2]` RAW. When a string carries no pipe,
#     rpartition returns ('', '', whole_string), so the ENTIRE thesis prose became the "status".
#     It then silently matched no known status and the name fell through every thesis gate --
#     no crash, no flag, just a position quietly exempt from rotation and trigger logic.
#   * smith_dashboard's version whitelisted against ("strengthening","watch","broken") via
#     startswith and returned None otherwise -- correct, but only in the dashboard.
#
# G60 was the same class of defect firing loudly (cmd_rotation/cmd_derisk crashed with
# AttributeError the first time a dict entry reached their .rpartition call). The lesson is not
# "add another isinstance branch" -- it is that a field with two shapes needs exactly ONE reader,
# in a module every consumer already imports. That is this block. smith_math, smith_dashboard
# and smith_charts all `import smith_risk`, so there is no excuse for a fifth implementation.
#
# KNOWN_STATUSES is the whitelist. Anything else normalizes to None, which every caller already
# treats as "no usable status" -- degrading to unknown is safe, inventing a status is not.

KNOWN_STATUSES = ("strengthening", "watch", "broken", "intact", "exited")


def thesis_status(entry):
    """Canonical status for either entry shape. Returns a KNOWN_STATUSES member, or None.

    None means 'no usable status' and is a normal, safe outcome -- never a crash, and never a
    fabricated value. Prefix-matched so "watch (position closed 08-04)" still reads as watch.
    """
    if not entry:
        return None
    if isinstance(entry, dict):
        raw = str(entry.get("status") or "").strip().lower()
    else:
        head, sep, tail = str(entry).rpartition("|")
        # No separator => no status was ever encoded. Do NOT treat the prose as a status.
        raw = tail.strip().lower() if sep else ""
    return next((k for k in KNOWN_STATUSES if raw.startswith(k)), None)


def thesis_text(entry):
    """The human-readable one-liner, from either shape. '' when absent."""
    if isinstance(entry, dict):
        return entry.get("thesis") or ""
    head, sep, _tail = str(entry or "").rpartition("|")
    return (head if sep else str(entry or "")).strip()


def thesis_evidence(entry):
    """(evidence_for, evidence_against, verified). Legacy strings carry no evidence, so they
    return ([], [], 'unverified') -- an honest empty, not an implied absence of risk."""
    if isinstance(entry, dict):
        return (entry.get("evidence_for") or [],
                entry.get("evidence_against") or [],
                entry.get("verified") or "unverified")
    return ([], [], "unverified")


def is_legacy_thesis(entry):
    """True for a bare-string entry that has not been migrated to the evidence schema."""
    return entry is not None and not isinstance(entry, dict)


def normalize_thesis_entry(entry, note=None):
    """Upgrade a legacy bare string to the evidence-object schema WITHOUT inventing anything.

    Both evidence arrays come back EXPLICITLY EMPTY with `verified: "unverified"` -- the legacy
    string genuinely carried no evidence, and a migration that manufactured some would be worse
    than the gap it closed. An already-migrated entry is returned untouched.
    """
    if isinstance(entry, dict):
        return entry
    return {
        "status": thesis_status(entry) or "watch",
        "thesis": thesis_text(entry),
        "evidence_for": [],
        "evidence_against": [],
        "verified": "unverified",
        "verified_against": "",
        "verified_on": "",
        "note": note or ("migrated from legacy bare-string schema 2026-08-16; the original "
                         "string carried no evidence, so both arrays are explicitly empty "
                         "rather than invented -- next smith-thesis touch should populate them"),
    }


# ---------------------------------------------------------------------------
# MIXED NAMESPACES -- data keys and metadata keys sharing one dict (2026-08-16)
# ---------------------------------------------------------------------------
# Several state/lot namespaces store per-ticker data ALONGSIDE bookkeeping keys:
#   lots.json          -> {"AMD": [...], "schema_version": 1, "_note": "...", "_rebuilt": "..."}
#   data_cache.betas   -> {"AMAT": {...}, "_method_note_2026_08_12": "..."}
# Lookups by ticker are unaffected. ITERATION is where this bites, and it already produced two
# separate ad-hoc filters for the same lots.json namespace (`not k.startswith("_") and
# isinstance(v, list)` in one place, a bare `isinstance(v, list)` in another). Two filters for
# one namespace is how they drift.
#
# Convention: bookkeeping keys are `_`-prefixed OR in RESERVED_KEYS. data_entries() is the one
# reader; value_type adds a belt-and-braces type filter for callers that want it.

RESERVED_KEYS = ("schema_version", "as_of", "note", "source", "window", "ttl_days",
                 "refresh_after", "generated", "_rebuilt")


def data_entries(mapping, value_type=None):
    """Yield only the real data (ticker) entries of a mixed namespace, as (key, value) pairs."""
    for k, v in (mapping or {}).items():
        if k.startswith("_") or k in RESERVED_KEYS:
            continue
        if value_type is not None and not isinstance(v, value_type):
            continue
        yield k, v


def mixed_shape_defects(mapping, name, expect_type):
    """Report data entries whose value type is NOT expect_type -- the generic form of the bug
    that produced the thesis string/object split. Returns a list of human-readable defects.

    Deliberately reports rather than coerces: a namespace holding two value shapes is a writer
    problem, and silently normalizing it on read is exactly how the thesis split survived for
    weeks in four different readers.
    """
    odd = sorted(k for k, v in data_entries(mapping) if not isinstance(v, expect_type))
    if not odd:
        return []
    return [f"MIXED SHAPES in {name}: {len(odd)} entry(ies) are not {expect_type.__name__} "
            f"({', '.join(odd[:8])}{' ...' if len(odd) > 8 else ''}). Every reader of this "
            f"namespace must then branch on type, and each branch is a place to drift. Fix the "
            f"writer, or add the key to RESERVED_KEYS if it is bookkeeping, not data."]


# ---------------------------------------------------------------------------
# KNOWN_GAPS STATUS -- same defect class as thesis, found 2026-08-16 by cmd_gaps
# ---------------------------------------------------------------------------
# 9 of 71 gap records stored a resolution NARRATIVE in `status` ("resolved 2026-07-18 --
# methodology folded into G3") instead of a status value. Any reader asking "is this gap open?"
# by testing `status != "closed"` therefore reported nine long-resolved gaps as OPEN. That is
# exactly the thesis string/object defect one field over: a field with no enforced vocabulary,
# and every reader left to guess.
#
# Same remedy: a whitelist, one normalizer, and a validate check. `resolved` is accepted as a
# synonym for closed because that is what the legacy records actually meant.

KNOWN_GAP_STATUSES = ("open", "closed", "partially_closed", "wontfix", "blocked")
_GAP_SYNONYMS = {"resolved": "closed", "fixed": "closed", "done": "closed"}


def gap_status(entry):
    """Canonical gap status. Unknown/narrative values normalize to None, never silently 'open'."""
    if not isinstance(entry, dict):
        return None
    raw = str(entry.get("status") or "").strip().lower()
    if not raw:
        return "open"                      # a gap with no status recorded is open by convention
    for k in KNOWN_GAP_STATUSES:
        if raw.startswith(k):
            return k
    for syn, canon in _GAP_SYNONYMS.items():
        if raw.startswith(syn):
            return canon
    return None


def gap_is_live(entry):
    """True when a gap still needs attention. An UNREADABLE status counts as live, deliberately:
    if the desk cannot tell whether something is fixed, the safe default is that it is not."""
    return gap_status(entry) in (None, "open", "partially_closed", "blocked")
