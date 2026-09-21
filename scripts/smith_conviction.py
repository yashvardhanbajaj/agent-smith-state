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


# A CARRIED thesis (an exited name's last held entry, smith_risk.carry_thesis_forward) is STALE
# evidence: the desk last looked while it still held the name and has not examined it since the
# exit. It scores at half weight and its verification tier is capped at `unverified` (a `primary`
# check made before the exit says nothing about today). Only a POSITIVE base is discounted: a
# carried `broken` / `watch` keeps its full weight, because softening old bad news is the
# wrong-direction error. 0.5 puts a carried unverified `strengthening` at 10.5 and `intact` at
# 6.3 of the 28-point thesis weight -- it can support a re-entry but never carry one alone
# (the `low` tier floor is 20 on the TOTAL score).
CARRIED_THESIS_MULT = 0.5
# Age term (2026-09-21): a carried read also decays with the time since the desk last reviewed it,
# linearly to CARRIED_AGE_FLOOR at CARRIED_AGE_FULL_DAYS. Unknown age gets the floor (an undated read
# is presumed old). Only applied when the caller supplies `today`, so the pure scorer stays deterministic.
CARRIED_AGE_FULL_DAYS = 180
CARRIED_AGE_FLOOR = 0.25


def carried_age_factor(thesis_entry, today):
    import datetime as _d
    ref = thesis_entry.get("last_reviewed_on") or thesis_entry.get("exited_as_of")
    try:
        age = (_d.date.fromisoformat(str(today)[:10]) - _d.date.fromisoformat(str(ref)[:10])).days
    except (TypeError, ValueError):
        return CARRIED_AGE_FLOOR, None
    return max(CARRIED_AGE_FLOOR, min(1.0, 1.0 - max(age, 0) / CARRIED_AGE_FULL_DAYS)), age


def thesis_component(thesis_entry, today=None):
    """+WEIGHTS['thesis'] scaled by status and evidence quality. `broken` scores negative --
    conviction to ADD should fall through zero for a broken thesis, not just stop climbing;
    a negative thesis component is what lets conviction_exit outrank a merely-lukewarm holding.

    A CARRIED entry (smith_risk.is_carried_thesis) is discounted by CARRIED_THESIS_MULT with its
    verification tier capped, and the reason string says so -- the ticket must never present an
    exit-time thesis as a fresh read (Phase 6)."""
    status = smith_risk.thesis_status(thesis_entry)
    ev_for, ev_against, verified = smith_risk.thesis_evidence(thesis_entry)
    base = {"strengthening": 1.0, "intact": 0.6, "watch": 0.1, "broken": -1.0, "exited": 0.0,
            None: 0.0}.get(status, 0.0)
    carried = smith_risk.is_carried_thesis(thesis_entry)
    if carried:
        verified = "unverified"
        age_f, age_d = (carried_age_factor(thesis_entry, today) if today else (1.0, None))
        if base > 0:
            base *= CARRIED_THESIS_MULT * age_f
    # Evidence quality modulates magnitude, not direction -- a verified strengthening thesis
    # counts more than an unverified one, but an unverified watch still counts as a mild watch.
    ev_mult = {"primary": 1.15, "secondary": 1.0, "unverified": 0.75}.get(verified, 0.75)
    score = base * ev_mult * WEIGHTS["thesis"]
    reason = None
    if status is not None:
        reason = f"thesis {status} ({verified}, {len(ev_for)} for / {len(ev_against)} against)"
        if carried:
            reason = (f"thesis {status} CARRIED FROM EXIT (stale, x{CARRIED_THESIS_MULT:g}"
                      + (f" x{age_f:.2f} for age {age_d}d" if today and age_d is not None else
                         f" x{age_f:.2f} undated read" if today else "")
                      + f"; last reviewed "
                      f"{thesis_entry.get('last_reviewed_on') or 'unknown'}, exited "
                      f"{thesis_entry.get('exited_as_of') or 'unknown'}, from "
                      f"{thesis_entry.get('carried_from') or 'unknown'}) -- not re-examined since the exit")
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


KELLY_FRACTION_DEFAULT = 0.25  # quarter-Kelly, conservative by construction


def kelly_fraction(p, b, fraction=KELLY_FRACTION_DEFAULT):
    """f* = (b*p - q) / b, the standard fractional-Kelly formula. p: win probability [0,1].
    b: payoff ratio (average win magnitude / average loss magnitude, both as positive numbers
    on the same scale -- e.g. avg_benefit_pct of worked rows over abs(avg_benefit_pct) of
    missed rows). fraction: the Kelly fraction applied (0.25 = quarter-Kelly). Clamped to
    [0, 1] -- this function never recommends shorting (negative f) or leverage beyond the full
    bankroll (f > 1); a negative edge (b*p <= q) returns 0, not a negative size."""
    f_full = full_kelly(p, b)
    if f_full is None:
        return None
    return round(max(0.0, min(1.0, f_full)) * fraction, 4)


def full_kelly(p, b):
    """The ONE Kelly formula, f* = (b*p - q)/b, unclamped (negative = negative edge).

    kelly_fraction clamps it to [0, 1] (never short, never leveraged) and track_record_multiplier
    clamps it to [-1, 1] (it needs the SIGN to tilt a size DOWN). Both used to carry their own
    copy of the arithmetic; Phase 4 added a third consumer (smith_edge's disclosed Kelly cross-check
    on every ticket), so the formula lives here once and each caller keeps its own clamp -- their
    outputs are unchanged."""
    if p is None or b is None or b <= 0:
        return None
    return (b * p - (1.0 - p)) / b


TRACK_RECORD_MIN_N = 3          # == smith_core.BUCKET_RATE_MIN_N (no import: this module stays leaf)


def track_record_multiplier(hit_rate_pct, n, max_effect=0.20, n_for_full_authority=20,
                            payoff_ratio=None, window=None):
    """Bounded tilt, not a veto -- per user decision. A signal bucket with a measured hit rate
    nudges conviction up or down by at most `max_effect` (20%), and that ceiling itself scales
    with sample size so a bucket earns authority rather than being handed it: n=4 gets ~1/5 of
    the full effect, n=20+ gets the full +/-20%. Centered on 50% (a coin flip moves nothing).

    KELLY-INFORMED TILT (added 2026-09-07). The plain hit-rate formula above uses ONLY win
    probability -- a bucket that wins 55% of the time with a 0.3:1 payoff ratio (small wins,
    big losses) gets the SAME tilt as one that wins 55% of the time with a 3:1 payoff ratio,
    even though the first has negative expectancy and the second has a large edge. When
    `payoff_ratio` (b) is supplied, the tilt direction and magnitude come from the Kelly
    fraction f* = (b*p-q)/b instead of the bare hit-rate gap -- Kelly's f* is 0 at breakeven
    edge and grows with true edge, not just win frequency, which is a better description of
    "how much should this signal's track record move sizing" than win-rate alone.

    THE 20% CEILING IS DELIBERATELY NOT RAISED. Full or even quarter-Kelly can imply far
    larger swings than 20% for a strong edge -- that would silently override the user's own
    stated 'tight, large-quantum stops by design' risk posture (confirmed 2026-07-27) and the
    staged-tranche/ATR-cap discipline the rest of this sizing chain already enforces. Kelly
    here answers a narrower, safer question: GIVEN the existing +/-20% governance ceiling,
    should this bucket sit near the top of that band or the bottom? It informs the tilt's
    shape, not its bound.

    EVIDENCE WINDOW (user instruction 2026-09-21). The rate handed in must be a POST-ENGINE_EPOCH
    rate (smith_edge.admissible_bucket_tables); a legacy-engine hit rate is inadmissible evidence.
    With no rate, or fewer than TRACK_RECORD_MIN_N scored signals, the answer is NO TILT (1.0)
    with a reason that says so and quotes no number. `window` ("since <epoch>") is printed beside
    any tilt that does apply. The effect of the filter is large and deliberate: the -6.7% tilt
    MOMENTUM+VOLUME's legacy 20% hit rate applied to every name carrying it is gone until post-epoch
    signals mature."""
    if hit_rate_pct is None or not n or n < TRACK_RECORD_MIN_N:
        if window is None and (hit_rate_pct is None or not n):
            return 1.0, None            # caller supplied no record and no window: nothing to explain
        return 1.0, ("no post-epoch track record%s for this name's bullish signal (an admissible "
                     "record needs at least %d scored signals since the epoch) -- no tilt" % (f" ({window})" if window else "", TRACK_RECORD_MIN_N))
    authority = min(1.0, n / n_for_full_authority)
    if payoff_ratio is not None and payoff_ratio > 0:
        p = hit_rate_pct / 100.0
        f_full_kelly = max(-1.0, min(1.0, full_kelly(p, payoff_ratio)))
        # f_full_kelly is in [-1,1] (edge direction and strength); map it onto the SAME
        # +/-max_effect band the plain formula uses, so the ceiling is identical either way.
        tilt = f_full_kelly * max_effect * authority
        basis = f"Kelly edge (p={hit_rate_pct:.0f}%, payoff {payoff_ratio:.2f}:1)"
    else:
        tilt = ((hit_rate_pct - 50.0) / 50.0) * max_effect * authority
        basis = f"hit rate {hit_rate_pct:.0f}%"
    tilt = max(-max_effect, min(max_effect, tilt))
    mult = 1.0 + tilt
    reason = (f"track record {hit_rate_pct:.0f}% (n={n}{', ' + window if window else ''}) via {basis} applies a {tilt:+.1%} "
              f"tilt ({authority:.0%} authority at this sample size)")
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

    s, r, thesis_status, verified = thesis_component(ctx.get("thesis_entry"), ctx.get("today"))
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
        mult, r = track_record_multiplier(tr.get("hit_rate_pct"), tr.get("n"),
                                          payoff_ratio=tr.get("payoff_ratio"), window=tr.get("window"))
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
# UNIVERSE BAR (Phase 6) -- which UNHELD names may produce a LIVE ticket
# ---------------------------------------------------------------------------
# THE PROBLEM. The universe is held + alumni + watchlist + benches (compute_universe.json tiers),
# and until Phase 6 each family that proposes an unheld name applied its own idea of "enough
# evidence": entry_setup had a thesis check (Phase 1), reentry a conviction gate that alumni failed
# for absence, bench_diversifier nothing at all, the bench rotation a hard-coded shadow. The
# 2026-09-20 entry_setup candidates (IONQ/QBTS/RGTI/BABA) cleared the `low` floor by 0.6-0.8 points
# on valuation + a 52-week-position RSI proxy alone. ONE bar, ONE function, every family.
#
# A name may vote `live` only with ALL of:
#   (1) a price AND an ATR fetched THIS RUN -- not an exit fill, not a setup row's stale
#       price_usd, not the atr20 cache (its `as_of` is refreshed by any ticker's update, so a
#       name's own value can be weeks old under a fresh-looking date);
#   (2) >= UNIVERSE_MIN_SOURCES INDEPENDENT evidence sources, at least one `verified` or
#       `computed` (the G58 evidence gate: two unverified claims are two claims, not evidence);
#   (3) a thesis entry, or the user's explicit no_thesis_acknowledged flag.
# Anything else votes `shadow` with a NAMED blocker. A held name is never touched (it has a live
# price, a stop and a thesis by construction). A missing input is a blocker, never an estimate.

UNIVERSE_MIN_SOURCES = 2
EVIDENCE_QUALITIES_THAT_ANCHOR = ("verified", "computed")


def evidence_sources(ctx, computed_this_run=False):
    """The INDEPENDENT evidence sources behind one candidate, from the same typed ctx
    score_conviction reads -> [{"source", "quality", "detail"}]. quality is one of
      verified   -- a primary/secondary-checked thesis, a VERIFIED earnings print
      computed   -- arithmetic on this run's own price bars (RSI / relative strength / signal buckets)
      reported   -- a third-party published figure (analyst target, an unverified print)
      unverified -- an agent's assertion (an unverified or CARRIED thesis, a sourced-but-unchecked
                    catalyst, another agent naming the ticker)
    Independence: RSI, relative strength and signal buckets are all derived from the same price
    series, so they are ONE `price_action` source, not three -- counting them separately would let
    a single price move satisfy the two-source bar by itself. Only `verified`/`computed` anchor the
    bar (EVIDENCE_QUALITIES_THAT_ANCHOR). `price_action` is `computed` only when this run really
    computed indicators for the name (`computed_this_run`); the watchlist's 52-week-position RSI
    proxy (ctx `rsi_proxy`) is an agent-supplied number, never counted as computed -- a real RSI14
    from this run's bars is added by the caller (smith_math._gate_on_universe_bar)."""
    out = []
    thesis = ctx.get("thesis_entry")
    status = smith_risk.thesis_status(thesis)
    if status is not None:
        if smith_risk.is_carried_thesis(thesis):
            q, why = "unverified", "carried from exit (stale)"
        else:
            _f, _a, ver = smith_risk.thesis_evidence(thesis)
            q, why = ("verified" if ver in ("primary", "secondary") else "unverified"), f"thesis {status}, {ver}"
        out.append({"source": "thesis", "quality": q, "detail": why})
    ticker = ctx.get("ticker")
    hits = [c for c in (ctx.get("factor_catalysts") or []) if ticker and ticker in (c.get("affects") or [])]
    if hits:
        out.append({"source": "catalyst", "quality": "unverified",
                    "detail": f"{len(hits)} factor catalyst(s) naming {ticker}"})
    computed_bits, proxy_bits = [], []
    if ctx.get("buckets"):
        computed_bits.append("signal buckets")
    if ctx.get("rsi_usable") and ctx.get("rsi") is not None:
        (proxy_bits if ctx.get("rsi_proxy") else computed_bits).append(
            "52-week-position RSI proxy" if ctx.get("rsi_proxy") else "RSI")
    if ctx.get("rel_usable") and ctx.get("rel_pp") is not None:
        computed_bits.append("relative strength")
    if computed_bits or proxy_bits:
        is_computed = bool(computed_bits) and computed_this_run
        out.append({"source": "price_action", "quality": "computed" if is_computed else "unverified",
                    "detail": "+".join(computed_bits + proxy_bits)
                              + ("" if is_computed else " (not computed from this run's bars)")})
    if ctx.get("upside_pct") is not None:
        out.append({"source": "valuation", "quality": "reported", "detail": "analyst target upside"})
    ef = ctx.get("earnings_fact")
    if ef and (ef.get("quarter_verdict") or ef.get("avg_surprise_pct") is not None):
        checked = ef.get("status") == "VERIFIED" or bool(ef.get("verified_on"))
        out.append({"source": "earnings", "quality": "verified" if checked else "reported",
                    "detail": "earnings print" + (" (verified)" if checked else "")})
    if ctx.get("mention_count"):
        out.append({"source": "agent_corroboration", "quality": "unverified",
                    "detail": f"named by {ctx['mention_count']} agent(s) this run"})
    return out


def universe_bar(ticker, *, price=None, price_source=None, atr_this_run=None, evidence=None,
                 thesis_entry=None, no_thesis_ack=None, held=False):
    """THE ONE universe-bar function every unheld-name family calls (grep-guarded by a test).

    -> {"ticker", "passes", "vote", "failed": [codes], "blockers": [named text], "checks": {...}}.
    `price`/`price_source`: this run's fetched price (live_quotes.json / bars.json) or None.
    `atr_this_run`: the ATR% computed from THIS run's bars, or None (unknowable counts as missing).
    `evidence`: evidence_sources(...). `held=True` exempts a held name (checked by the caller only
    for tests; families that propose held names simply never call this)."""
    if held:
        return {"ticker": ticker, "passes": True, "vote": "live", "failed": [], "blockers": [],
                "checks": {"exempt": "held"}}
    evidence = evidence or []
    failed, blockers = [], []
    if not price:
        failed.append("no_live_price")
        blockers.append(f"universe bar: no price for {ticker} fetched this run (live_quotes.json / bars.json) "
                        "-- a setup-row price or an old exit fill is not a live price")
    if not atr_this_run:
        failed.append("no_atr_this_run")
        blockers.append(f"universe bar: no ATR for {ticker} computed from this run's bars "
                        "(compute_indicators.json) -- the cached value's date does not vouch for the name")
    anchors = [e for e in evidence if e["quality"] in EVIDENCE_QUALITIES_THAT_ANCHOR]
    if len(evidence) < UNIVERSE_MIN_SOURCES:
        failed.append("evidence_sources")
        blockers.append(f"universe bar: {len(evidence)}/{UNIVERSE_MIN_SOURCES} independent evidence source(s) "
                        f"for {ticker} ({', '.join(e['source'] for e in evidence) or 'none'})")
    if not anchors:
        failed.append("no_verified_or_computed_source")
        blockers.append(f"universe bar: no verified or computed source for {ticker} -- unverified/reported "
                        "claims alone do not clear the G58 evidence gate")
    if not thesis_entry and not no_thesis_ack:
        failed.append("no_thesis")
        blockers.append(f"universe bar: no thesis entry for {ticker} and no no_thesis_acknowledged flag -- "
                        "smith-thesis must examine it, or the user must acknowledge it has none")
    return {"ticker": ticker, "passes": not failed, "vote": "shadow" if failed else "live",
            "failed": failed, "blockers": blockers,
            "checks": {"price": price, "price_source": price_source, "atr_pct": atr_this_run,
                       "sources": [f"{e['source']}:{e['quality']}" for e in evidence],
                       "thesis": ("carried" if smith_risk.is_carried_thesis(thesis_entry) else
                                  "entry" if thesis_entry else "acknowledged" if no_thesis_ack else None)}}


def apply_universe_bar(row, bar, leg=None):
    """Fold a universe_bar verdict into a candidate row IN PLACE. A failing bar demotes a `live`
    vote to `shadow` and appends its named blockers (a row that is already shadow / below_materiality
    keeps its vote -- the bar never promotes anything). The verdict rides on `row["universe_bar"]`
    for the dashboard and the ticket. `leg` is the dict whose blockers to extend (a paired row's
    buy_leg); default the row itself."""
    target = leg if leg is not None else row
    row["universe_bar"] = {k: bar[k] for k in ("passes", "failed", "checks")}
    if bar["passes"]:
        return row
    if row.get("vote") == "live":
        row["vote"] = "shadow"
    target.setdefault("blockers", []).extend(bar["blockers"])
    return row


# ---------------------------------------------------------------------------
# Sizing inversion
# ---------------------------------------------------------------------------

STAGE_FRACTION = 0.5  # first tranche only; the rest is explicitly reserved, never deployed in one pass


def policy_max_position_usd(atr_pct, price_usd, total_book_usd, policy, learned_multiple=None):
    """Reuses smith_risk.stop_and_cap AS-IS (qty=0) rather than re-deriving the formula --
    ONE FIELD, ONE READER. max_position_usd/stop_price_usd do not depend on qty or current
    market value at all, so calling with qty=0 correctly returns the FULL policy-allowed size
    for a ticker with no current position (a re-entry, a watchlist name, a bench diversifier) --
    this is precisely what makes re-entry sizing possible; the old engine's `headroom_usd` was
    read only from currently-held positions in compute_risk.json, so an unheld ticker was never
    even in that lookup and sized at $0 by omission, not by a $0 formula result."""
    # learned_multiple (Phase 3): forwarded so stop_and_cap's ADVISORY learned_stop block is
    # reachable from the sizing path too. It never changes max_position_usd or stop_price_usd --
    # see smith_risk.learned_stop_multiple_for.
    return smith_risk.stop_and_cap(atr_pct, price_usd, 0, total_book_usd, policy,
                                   learned_multiple=learned_multiple)


def conviction_size(conviction_tier_pct, policy_max_usd, stage_fraction=STAGE_FRACTION):
    """target = how much of the policy-allowed maximum this conviction level should use.
    size_wanted = the first staged tranche of that target -- never the whole target in one pass,
    per the user's explicit 'staged tranches' pacing decision. Returns (target_usd, size_wanted_usd)."""
    if policy_max_usd is None:
        return None, None
    target = conviction_tier_pct * policy_max_usd
    size_wanted = target * stage_fraction
    return round(target, 2), round(size_wanted, 2)


def clamp_size(size_wanted, headroom_usd, cluster_room_usd, deployable_cash_usd, *,
               heat_room_usd=None, single_position_room_usd=None, ai_capex_room_usd=None,
               cluster_risk_room_usd=None):
    """Returns (size_final, clamped_by). Clamps to the TIGHTEST of: ATR headroom (never breach
    the position's own risk cap), cluster room (never push a cluster over its ceiling),
    deployable cash (never spend below the cash floor). None inputs are treated as
    non-binding (unknown != a reason to block) but are never used to justify a LARGER size than
    size_wanted -- an unclamped size_wanted already respects the policy max by construction.

    PHASE 3 (2026-09-20) adds four keyword-only clamps, all in DOLLARS of position, all None =
    non-binding, all only ever SHRINKING a buy, and named by the constraint that bound:

        heat_room            what the run's remaining portfolio-heat budget buys at this stop
        single_position      policy.max_single_position_pct minus the name's current weight
        ai_capex             policy.max_ai_capex_factor_pct minus current AI-capex exposure
        cluster_risk_budget  the cluster's share of the correlation-adjusted heat budget

    max_single_position_pct and max_ai_capex_factor_pct were computed by cmd_drift on every run
    and displayed, and no sizing function ever received them; policy records the 10% aggregate
    cap breached at 11.9% and 13.0% while sizing carried on. The return shape is unchanged and the
    positional signature is unchanged, so every pre-Phase-3 call site keeps working. On a tie the
    older clamp keeps the name, so a row that was bound by cash yesterday is still bound by cash.
    """
    if size_wanted is None or size_wanted <= 0:
        return 0.0, None
    candidates = [("size_wanted (unclamped)", size_wanted)]
    if headroom_usd is not None:
        candidates.append(("ATR headroom", max(0.0, headroom_usd)))
    if cluster_room_usd is not None:
        candidates.append(("cluster ceiling room", max(0.0, cluster_room_usd)))
    if deployable_cash_usd is not None:
        candidates.append(("deployable cash", max(0.0, deployable_cash_usd)))
    for label, room in (("single_position", single_position_room_usd), ("ai_capex", ai_capex_room_usd),
                        ("cluster_risk_budget", cluster_risk_room_usd), ("heat_room", heat_room_usd)):
        if room is not None:
            candidates.append((label, max(0.0, room)))
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
