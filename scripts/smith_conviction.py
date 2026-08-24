#!/usr/bin/env python3
"""
Agent Smith -- conviction scoring and inverted sizing.

Added 2026-08-24, third time the user reported the same defect (08-12, 08-17, today): every
prior fix added a new DEFECT DETECTOR to what remained a defect-detection engine. A proposal's
size was the dollar magnitude of the problem it cured (ATR cap excess, cluster overage), never
an expression of how good the idea is. Live evidence the day this was built: 11 of 12 open
proposals cited cap/cluster mechanics; total BUY dollars proposed were $1,001 against $12,431 of
idle cash; median proposal size had fallen $700 -> $350 over six weeks as headroom kept shrinking;
19 rotation pairs had been attempted all-time and 0 survived; a fully-exited name had no position
row, hence no headroom, hence sized its own re-entry at exactly $0.

This module inverts that: CONVICTION decides the idea and how big it should be; risk caps only
CLAMP the result, and every clamp is stated, never silently substituted. Pure functions, no I/O,
stdlib only -- same contract as smith_risk.py, which this module leans on for the one canonical
thesis reader and the signal-polarity table rather than re-deriving either.

Organising rule for the direction-vs-price behaviours the user asked for explicitly ("exiting a
breakdown, entering an uptrend, booking profit into an unrallied name, averaging into a drawdown,
rotating a cluster laggard to its performer, headwind/tailwind"): PRICE says WHEN, THESIS says
WHICH WAY.

    price state          thesis strong                thesis weak
    -----------          --------------                -----------
    extended/ran hard    hold or add on strength       book profit -> rotate out
    lagging/fallen       buy the laggard, or average    sell the laggard -> rotate to performer

A laggard with an intact thesis is an opportunity; a laggard with a weak thesis is dead money.
Same price signal, opposite action, decided by thesis -- this is what makes "sell what ran, buy
what hasn't" (profit_rotation) and "in a cluster, back the performer over the laggard"
(cluster_rotation) NOT contradict each other; they only look opposite if price alone decides.
"""

import smith_risk

# ---------------------------------------------------------------------------
# Conviction scoring
# ---------------------------------------------------------------------------
# 0-100 composite. Every term is a typed number from data the desk already collects each run --
# never a re-read of prose. A component that cannot be computed (missing cache, no earnings_facts
# entry, no analyst target) contributes exactly 0 and is named in `reasons` as absent, never
# estimated. This mirrors the COMPUTE-FIRST / EVIDENCE GATE discipline the rest of the codebase
# already runs under (see smith_lifecycle.py's evidence_quality gate).

# Component weights sum to 100 at full strength; a candidate rarely clears all of them at once,
# which is intentional -- conviction should require multiple things pointing the same way, not
# one strong number carrying the whole score.
WEIGHTS = {
    "thesis": 28,          # status + evidence quality -- the single most load-bearing input
    "catalyst": 20,        # dated, sourced, exposure-quantified factor_catalysts entry
    "trend": 14,           # SIGNAL_POLARITY net bullish/bearish reading, bidirectional
    "valuation": 14,       # analyst target upside %
    "earnings": 10,        # surprise history / implied move, from earnings_facts
    "technical": 8,        # RSI / relative strength, degrades explicitly when stale
    "corroboration": 6,    # count of independent Stage-1 agents naming this ticker this run
}

CONVICTION_TIERS = [
    (70, "high", 1.00),
    (45, "medium", 0.60),
    (20, "low", 0.30),
    (0, "none", 0.0),
]
# The "low" floor is deliberately 20, not a rounder 25 -- verified against the live book:
# WEIGHTS["thesis"] x 1.0 (strengthening) x 0.75 (unverified) = 21.0 EXACTLY, and 22 of 33
# thesis entries in this book are unverified. A 25 floor would mean the single most common
# thesis case here (a genuine strengthening call the desk simply hasn't source-verified yet)
# could never clear "low" on thesis alone, no matter how strong -- starving conviction on the
# most load-bearing input for the majority of the book. 20 lets it through; a genuinely weak or
# absent thesis (base 0.1 or 0.0) still does not.
#
# TIER LABEL vs TIER PCT are deliberately split (2026-08-24, first live run found the bug):
# CONVICTION_TIERS' step-function pct field is now used ONLY as anchor points for a piecewise-
# linear interpolation (_tier_pct_for), not looked up directly. The label (_tier_label_for)
# stays a discrete step -- "high"/"medium"/"low"/"none" is a natural-language bucket the
# dashboard and priority scorer read, and forcing that to be continuous would just replace one
# arbitrary line with infinitely many. The DOLLAR SIZE must not have a cliff, the LABEL can.
#
# Concretely, on 2026-08-24's first live dispatch: a scoped thesis-verification pass moved 7
# scores up (unverified->secondary/primary evidence multiplier). NVDA (42.5->51.5) and GLW
# (37.0->46.0) happened to cross the old 45-point low->medium step and roughly doubled in size;
# CLS/AMAT/TER/WDC/AMZN improved by comparable or larger margins (+9 to +11 points) but stayed
# on the low side of the same line and got ZERO dollar change -- WDC's thesis reached "primary"
# verification, the highest evidence tier that exists, and its size didn't move at all. That is
# not a policy choice, it is a step-function artifact: two candidates one point apart on either
# side of 45 got a 2x size difference for a 1-point difference in conviction. Interpolation
# fixes this without changing what "high"/"medium"/"low" mean or where policy_max itself is
# computed -- same anchors, same endpoints (score 0 -> pct 0.0, score >=70 -> pct 1.0), just no
# jump between them.
TIER_PCT_ANCHORS = [(0, 0.0), (20, 0.30), (45, 0.60), (70, 1.00)]


def _tier_pct_for(score):
    """Piecewise-linear interpolation across TIER_PCT_ANCHORS. Below the first anchor's score
    (0) returns 0.0; at/above the last anchor's score (70) returns 1.0 -- same endpoints the old
    step function had, so a "high" conviction idea still gets the full policy-max fraction and a
    zero/negative score still sizes at zero. Everything between two anchors scales linearly, so
    a 1-point difference in score never produces more than a 1-anchor-segment's worth of dollar
    difference, regardless of which side of a tier LABEL boundary it happens to land on."""
    if score <= TIER_PCT_ANCHORS[0][0]:
        return TIER_PCT_ANCHORS[0][1]
    for (s0, p0), (s1, p1) in zip(TIER_PCT_ANCHORS, TIER_PCT_ANCHORS[1:]):
        if s0 <= score <= s1:
            frac = (score - s0) / (s1 - s0)
            return p0 + frac * (p1 - p0)
    return TIER_PCT_ANCHORS[-1][1]  # score >= last anchor


def _tier_label_for(score):
    """Discrete label only -- for display and the priority scorer's tier-name reasons, never for
    sizing. Uses the same floors as the old CONVICTION_TIERS step function."""
    for floor, name, _pct in CONVICTION_TIERS:
        if score >= floor:
            return name
    return "none"


def thesis_component(thesis_entry):
    """+WEIGHTS['thesis'] scaled by status and evidence quality. `broken` scores negative --
    conviction to ADD should fall through zero for a broken thesis, not just stop climbing;
    a negative thesis component is what lets conviction_exit outrank a merely-lukewarm holding."""
    status = smith_risk.thesis_status(thesis_entry)
    ev_for, ev_against, verified = smith_risk.thesis_evidence(thesis_entry)
    base = {"strengthening": 1.0, "intact": 0.6, "watch": 0.1, "broken": -1.0, "exited": 0.0,
            None: 0.0}.get(status, 0.0)
    # Evidence quality modulates magnitude, not direction -- a verified strengthening thesis
    # counts more than an unverified one, but an unverified watch still counts as a mild watch.
    ev_mult = {"primary": 1.15, "secondary": 1.0, "unverified": 0.75}.get(verified, 0.75)
    score = base * ev_mult * WEIGHTS["thesis"]
    reason = None
    if status is not None:
        reason = f"thesis {status} ({verified}, {len(ev_for)} for / {len(ev_against)} against)"
    return score, reason, status, verified


def catalyst_component(ticker, factor_catalysts):
    """+/-WEIGHTS['catalyst'] for a dated, sourced factor_catalysts entry naming this ticker.
    structural threats and structural tailwinds score full weight; immediate/noise horizon
    scores half (real, but not the standing kind conviction should lean hard on)."""
    hits = [c for c in (factor_catalysts or []) if ticker in (c.get("affects") or [])]
    if not hits:
        return 0.0, None
    total, reasons = 0.0, []
    for c in hits:
        horizon_mult = 1.0 if c.get("horizon") == "structural" else 0.5 if c.get("horizon") == "immediate" else 0.0
        dir_sign = {"tailwind": 1.0, "threat": -1.0, "ambiguous": 0.0}.get(c.get("direction"), 0.0)
        total += dir_sign * horizon_mult * WEIGHTS["catalyst"]
        reasons.append(f"{c.get('direction')}/{c.get('horizon')}: {c.get('headline','')[:80]}")
    # Multiple catalysts on one name do not stack past the weight cap in either direction --
    # capping prevents one ticker with three noise-horizon mentions from outscoring a name with
    # one clean structural catalyst.
    total = max(-WEIGHTS["catalyst"], min(WEIGHTS["catalyst"], total))
    return total, "; ".join(reasons)


def trend_component(buckets):
    """+/-WEIGHTS['trend'] from smith_risk.classify_signal_polarity's net bullish/bearish read.
    This is the direct fix for the user-reported gap: tailwind (`NEW TAILWINDS`, bullish) and
    breakdown (`BREAKDOWN`/`STRONG DOWNTREND`, bearish) previously rolled into `net_signal` and
    then into `rotate_out`/`accumulate` rotation buckets that nothing downstream ever read.
    This makes the same classification move a score directly."""
    polarity = smith_risk.classify_signal_polarity(buckets)
    net = polarity["net"]
    total = len(polarity["bullish"]) + len(polarity["bearish"])
    if total == 0:
        return 0.0, None
    # Normalize by how many directional buckets are active so a single tailwind flag isn't
    # drowned out by counting unrelated ambiguous buckets, but two bearish flags outweigh one
    # bullish one, same as the polarity table's own `net` semantics.
    frac = net / max(total, 1)
    score = frac * WEIGHTS["trend"]
    reason = f"signal polarity net {net:+d} ({', '.join(polarity['bullish'] + polarity['bearish']) or 'none directional'})"
    return score, reason


def valuation_component(upside_pct):
    """+WEIGHTS['valuation'], linear 0-40% upside, capped -- deliberately capped rather than
    let VST's 63.9% headline number dominate the whole score on one input. Negative upside
    (price above target) scores negative, same magnitude."""
    if upside_pct is None:
        return 0.0, None
    frac = max(-1.0, min(1.0, upside_pct / 40.0))
    score = frac * WEIGHTS["valuation"]
    return score, f"{upside_pct:+.1f}% vs analyst target"


def earnings_component(earnings_fact):
    """+WEIGHTS['earnings'] from a verified quarter's beat/miss, or from surprise-history
    average for a pending print. Reported quarter and forward guide are scored SEPARATELY,
    never collapsed, per the G58 evidence discipline (`quarter_verdict` already states them
    apart in earnings_facts) -- this reads whichever verdict is present without inventing one."""
    if not earnings_fact:
        return 0.0, None
    qv = str(earnings_fact.get("quarter_verdict") or "")
    if qv:
        beat = "beat" in qv.lower() and "miss" not in qv.lower().split("beat")[0]
        # a mixed verdict ("revenue beat / EPS miss") scores near zero -- genuinely ambiguous,
        # not a strong signal either way
        if "beat" in qv.lower() and "miss" in qv.lower():
            return 0.0, f"mixed print: {qv[:80]}"
        score = (1.0 if beat else -1.0) * WEIGHTS["earnings"]
        return score, f"reported: {qv[:80]}"
    avg_surprise = earnings_fact.get("avg_surprise_pct")
    if avg_surprise is not None:
        frac = max(-1.0, min(1.0, avg_surprise / 5.0))
        return frac * WEIGHTS["earnings"] * 0.6, f"avg surprise history {avg_surprise:+.2f}% (pending print)"
    return 0.0, None


def technical_component(rsi, rsi_usable, rel_pp, rel_usable):
    """+/-WEIGHTS['technical']. Degrades EXPLICITLY to 0 with a named reason when caches are
    stale -- never silently drops out, never estimates. Oversold + healthy thesis scores
    positive (a dip on a name worth owning); overbought scores negative (extended, less room)."""
    if not rsi_usable:
        return 0.0, "technical: RSI cache stale, degraded to 0 (not estimated)"
    reasons = []
    score = 0.0
    if rsi is not None:
        if rsi < 35:
            score += 0.6 * WEIGHTS["technical"]
            reasons.append(f"RSI14 {rsi:.0f} oversold")
        elif rsi > 70:
            score -= 0.6 * WEIGHTS["technical"]
            reasons.append(f"RSI14 {rsi:.0f} overbought")
    if rel_usable and rel_pp is not None:
        frac = max(-1.0, min(1.0, rel_pp / 20.0))
        score += frac * WEIGHTS["technical"] * 0.4
        reasons.append(f"{rel_pp:+.1f}pp vs benchmark")
    return score, "; ".join(reasons) if reasons else None


def corroboration_component(mention_count):
    """+WEIGHTS['corroboration'] per independent Stage-1 agent naming this ticker this run,
    capped at 3 mentions. Direct fix for the user-reported gap: SKHY was named by both
    smith-rebound and smith-thesis the same run and received zero proposals -- corroboration
    was invisible to the old engine because nothing counted it."""
    if not mention_count:
        return 0.0, None
    n = min(mention_count, 3)
    score = (n / 3.0) * WEIGHTS["corroboration"]
    return score, f"named by {mention_count} independent source(s) this run"


def track_record_multiplier(hit_rate_pct, n, max_effect=0.20, n_for_full_authority=20):
    """Bounded tilt, not a veto -- per user decision. A signal bucket with a measured hit rate
    nudges conviction up or down by at most `max_effect` (20%), and that ceiling itself scales
    with sample size so a bucket earns authority rather than being handed it: n=4 gets ~1/5 of
    the full effect, n=20+ gets the full +/-20%. Centered on 50% (a coin flip moves nothing)."""
    if hit_rate_pct is None or not n:
        return 1.0, None
    authority = min(1.0, n / n_for_full_authority)
    tilt = ((hit_rate_pct - 50.0) / 50.0) * max_effect * authority
    tilt = max(-max_effect, min(max_effect, tilt))
    mult = 1.0 + tilt
    reason = (f"track record {hit_rate_pct:.0f}% (n={n}) applies a {tilt:+.1%} tilt "
              f"({authority:.0%} authority at this sample size)")
    return mult, reason


def score_conviction(ctx):
    """ctx: a dict with keys thesis_entry, factor_catalysts, buckets, upside_pct, earnings_fact,
    rsi, rsi_usable, rel_pp, rel_usable, mention_count, track_record (hit_rate_pct, n) or None.

    Returns {"conviction_score": float 0-100 (can go negative pre-clamp for a clearly bad
    candidate, clamped to 0 in the output), "conviction_tier", "conviction_reasons": [...]}.
    Score is a straight sum of the (already correctly-weighted) components, clamped to [-100,100]
    then track-record-tilted, then floored at 0 for display/tiering -- a genuinely negative
    composite (broken thesis + threat catalyst + downtrend) is exactly what conviction_exit's
    "convergence of negatives" reads, so the pre-floor sign is preserved for that check.
    """
    reasons = []
    total = 0.0

    s, r, thesis_status, verified = thesis_component(ctx.get("thesis_entry"))
    total += s
    if r:
        reasons.append(r)

    s, r = catalyst_component(ctx.get("ticker"), ctx.get("factor_catalysts"))
    total += s
    if r:
        reasons.append(r)

    s, r = trend_component(ctx.get("buckets"))
    total += s
    if r:
        reasons.append(r)

    s, r = valuation_component(ctx.get("upside_pct"))
    total += s
    if r:
        reasons.append(r)

    s, r = earnings_component(ctx.get("earnings_fact"))
    total += s
    if r:
        reasons.append(r)

    s, r = technical_component(ctx.get("rsi"), ctx.get("rsi_usable"), ctx.get("rel_pp"), ctx.get("rel_usable"))
    total += s
    if r:
        reasons.append(r)

    s, r = corroboration_component(ctx.get("mention_count"))
    total += s
    if r:
        reasons.append(r)

    raw_total = max(-100.0, min(100.0, total))

    tr = ctx.get("track_record")
    mult = 1.0
    if tr:
        mult, r = track_record_multiplier(tr.get("hit_rate_pct"), tr.get("n"))
        if r:
            reasons.append(r)

    display_score = max(0.0, raw_total * mult) if raw_total > 0 else raw_total * mult
    tier = _tier_label_for(display_score) if display_score > 0 else "none"
    tier_pct = _tier_pct_for(display_score) if display_score > 0 else 0.0

    return {
        "conviction_score": round(display_score, 1),
        "conviction_raw_pre_tilt": round(raw_total, 1),
        "conviction_tier": tier,
        "conviction_tier_pct": tier_pct,
        "conviction_reasons": reasons,
        "thesis_status": thesis_status,
    }


# ---------------------------------------------------------------------------
# Sizing inversion
# ---------------------------------------------------------------------------

STAGE_FRACTION = 0.5  # first tranche only; the rest is explicitly reserved, never deployed in one pass


def policy_max_position_usd(atr_pct, price_usd, total_book_usd, policy):
    """Reuses smith_risk.stop_and_cap AS-IS (qty=0) rather than re-deriving the formula --
    ONE FIELD, ONE READER. max_position_usd/stop_price_usd do not depend on qty or current
    market value at all, so calling with qty=0 correctly returns the FULL policy-allowed size
    for a ticker with no current position (a re-entry, a watchlist name, a bench diversifier) --
    this is precisely what makes re-entry sizing possible; the old engine's `headroom_usd` was
    read only from currently-held positions in compute_risk.json, so an unheld ticker was never
    even in that lookup and sized at $0 by omission, not by a $0 formula result."""
    return smith_risk.stop_and_cap(atr_pct, price_usd, 0, total_book_usd, policy)


def conviction_size(conviction_tier_pct, policy_max_usd, stage_fraction=STAGE_FRACTION):
    """target = how much of the policy-allowed maximum this conviction level should use.
    size_wanted = the first staged tranche of that target -- never the whole target in one pass,
    per the user's explicit 'staged tranches' pacing decision. Returns (target_usd, size_wanted_usd)."""
    if policy_max_usd is None:
        return None, None
    target = conviction_tier_pct * policy_max_usd
    size_wanted = target * stage_fraction
    return round(target, 2), round(size_wanted, 2)


def clamp_size(size_wanted, headroom_usd, cluster_room_usd, deployable_cash_usd):
    """Returns (size_final, clamped_by). Clamps to the TIGHTEST of: ATR headroom (never breach
    the position's own risk cap), cluster room (never push a cluster over its ceiling),
    deployable cash (never spend below the cash floor). None inputs are treated as
    non-binding (unknown != a reason to block) but are never used to justify a LARGER size than
    size_wanted -- an unclamped size_wanted already respects the policy max by construction."""
    if size_wanted is None or size_wanted <= 0:
        return 0.0, None
    candidates = [("size_wanted (unclamped)", size_wanted)]
    if headroom_usd is not None:
        candidates.append(("ATR headroom", max(0.0, headroom_usd)))
    if cluster_room_usd is not None:
        candidates.append(("cluster ceiling room", max(0.0, cluster_room_usd)))
    if deployable_cash_usd is not None:
        candidates.append(("deployable cash", max(0.0, deployable_cash_usd)))
    label, size_final = min(candidates, key=lambda c: c[1])
    clamped_by = None if label == "size_wanted (unclamped)" else label
    return round(size_final, 2), clamped_by


def convergence_exit_score(components_negative_count, min_negatives=3):
    """conviction_exit fires on CONVERGENCE, not on the word 'broken' -- there are 0 broken
    theses in the live book (16 strengthening / 16 watch), so a broken-keyed trigger can never
    fire. Counts how many of {thesis, catalyst, trend, technical} independently read negative;
    fires only when at least `min_negatives` agree, so one bad signal never triggers an exit on
    its own -- convergence is the whole point."""
    return components_negative_count >= min_negatives
