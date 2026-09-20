#!/usr/bin/env python3
"""
Agent Smith -- edge estimate, expected-value gate and gate-and-scale feedback (Phase 4 of the
proposal-engine rebuild, 2026-09-20).

Pure functions, stdlib only, NO I/O -- same contract as smith_risk / smith_conviction /
smith_ticket. Imports smith_core's constants (and its `idea_key`) and smith_conviction's Kelly
helper; never smith_lifecycle or smith_math. `explain()` RETURNS the compute_edge.json payload;
the pipeline writes it (a stage that wrote into the run dir from here would dirty the golden-master
fixture trees).

THE INCIDENT. The desk graded its own proposals for two months and nothing that grade said ever
reached a dollar. The scorecard had ZERO gating consumers: the only feedback path was the
strategist LLM reading prose, which is not reproducible, auditable or testable -- it happened to
reject a bad trim batch on 2026-09-19 and would as readily have missed it. Meanwhile every ticket
was sized with no estimate of whether it was worth taking at all: a proposal with non-positive
expected value was as likely to be emitted as one with a large edge, and the engine could produce
88 proposals at negative expectancy and not notice.

WHAT THIS MODULE IS, IN THREE PARTS.

1. EDGE. p_win (never invented: shrunk from an UNCALIBRATED prior toward the family's own record as
   independent ideas accumulate), payoff_R (from an analyst target HARD-CAPPED at TARGET_CAP_R so a
   51% sell-side upside cannot manufacture a 12R trade), fee_R, and EV_R.

2. GATE. The EV bar (MIN_EV_R) applies to BUYS ONLY -- the actions that ADD risk. A buy below the
   bar is emitted with vote "shadow" and a recorded `refused_because`; refusals are never silent.
   SELLS ARE NOT EV-GATED. At the 0.45 prior a sell "worth" a 1.0R payoff has EV_R = -0.13 and
   would need p_win >= 0.59 to clear a 0.15R bar, so an EV gate on sells refuses EVERY sell --
   thesis_break, conviction_exit and catalyst_threat included -- until the desk proves a hit rate no
   record supports. A gate that blocks protective exits is a risk hazard, not risk management.
   Sells are governed only by the evidence-based FAMILY verdict below, and PROTECTIVE exits
   (smith_core.PROTECTIVE_EXIT_TRIGGERS: thesis_break, conviction_exit, trim_risk_cap,
   factor_threat, catalyst_threat) ignore even a `suppressed` verdict: a suppressed family may not
   stop the desk from proposing to reduce a genuinely broken position.

3. FEEDBACK. Family verdicts per (direction, trigger_type) AND per direction:
       n_eff <  N_MIN                       unproven   x1.00   never gates, never scales
       n_eff >= N_MIN, lb95 > 0             proven     x1.00..1.25
       n_eff >= N_MIN, CI straddles 0       watch      x0.75
       n_eff >= N_SUPPRESS, ub95 < 0        suppressed x0.00   (family -> vote "shadow")
   Suppressed is NOT deleted: the family keeps firing as shadow and keeps being scored, which is the
   only way it can earn its vote back -- reversible by evidence, never a hard removal.

THE EVIDENCE RULE (user decision 2026-09-20): ONLY proposals on/after smith_core.ENGINE_EPOCH feed
any of this. Everything before it came from the legacy engine (mechanical sizing, discarded stops,
no materiality floor, no heat budget, no EV bar) -- "earlier proposals were too broke" -- so its
outcomes measure that engine, not this one, and are inadmissible as calibration however large the
sample. The legacy record stays REPORTED (scorecard `legacy` block) and is labelled history. On the
day this shipped every family and direction has n_eff = 0, so every verdict is `unproven`
(multiplier 1.00) and p_win is the prior shrunk only by conviction. P_WIN_PRIOR = 0.45 is an
UNCALIBRATED engineering prior chosen for conservatism, NOT a number measured from legacy history;
re-derive it once post-epoch scored ideas exist. Nothing here was tuned by looking at legacy hit
rates. The shadow-journal source obeys the same rule: only entries whose trigger row was emitted
on/after the epoch count.

THE SAME RULE NOW COVERS EVERY OTHER PATH BY WHICH A LEGACY OUTCOME COULD MOVE A SIZE, PRIORITY, VOTE,
RETIREMENT OR GATE (user instruction 2026-09-21: "correct this and any similar older hit-rate issue"):
signal-bucket hit rates and per-name grades (cmd_journal tallies only firings on/after the epoch and
stamps its output; admissible_bucket_tables is the one reader), the Kelly conviction tilt and priority
penalty/reward and signal_conviction retirement that read them, cluster-ladder authority
(smith_risk.ladder_authority counts only calls made on/after the epoch), the phase4.readiness counter,
the shadow-journal hit_rate written to trigger_journal.json, and every reporting surface. All of them go
inert until post-epoch outcomes mature; none was softened.

HORIZON MIX (disclosed, not hidden): proposal rows are scored at 30d (alpha vs SMH where anchored);
shadow-journal rows at 7d on the raw move. Both feed a family's n_eff -- a suppressed family can
only earn its vote back through the shadow journal -- and `source_counts` on every table row says
how many of each. An idea present in both is counted once, the proposal winning.

WHAT IS NOT HERE. Heat allocation, materiality and the sell sizers live in smith_ticket; the
post-pass that wires this into cmd_triggers is smith_math._apply_edge_gate.
"""
import math
import statistics

import smith_conviction
import smith_core
from smith_core import (BUCKET_PENALTY_HIT_RATE_PCT, BUCKET_PENALTY_MIN_N, BUCKET_PENALTY_POINTS,
                        BUCKET_REWARD_HIT_RATE_PCT, CI_Z, DEEMPH_SIZE_MULT, EV_R_FULL, F_EDGE_MIN,
                        FAMILY_MULT_MAX, FAMILY_MULT_MEAN_SCALE_PCT, FAMILY_MULT_SLOPE,
                        FAMILY_MULT_WATCH, GATE_OVERRIDE_LABEL, MIN_EV_R, N_MIN, N_SUPPRESS,
                        P_WIN_CEILING, P_WIN_CONVICTION_LOW, P_WIN_CONVICTION_SPAN, P_WIN_FLOOR,
                        P_WIN_PRIOR, P_WIN_SHRINK_K, PROTECTIVE_EXIT_TRIGGERS,
                        ROTATION_MIN_EDGE_R, ROUND_TRIP_FEE_PCT, SCOREABLE_STATUSES, TARGET_CAP_R,
                        VERDICT_THRESHOLD_PCT, idea_key, proposal_direction)

UNATTRIBUTED = "unattributed"   # a legacy-style row with no trigger_type: direction-level evidence only
UNPROVEN, PROVEN, WATCH, SUPPRESSED = "unproven", "proven", "watch", "suppressed"
GRADED_VERDICTS = ("worked", "missed", "neutral")
# shadow-journal verdicts use "failed" where a proposal uses "missed"
JOURNAL_GRADED = ("worked", "failed", "neutral")
# what a shadow-journal trigger_type bets on, for entries written before they carried a direction
# (mirrors smith_lifecycle.TRIGGER_TYPE_DIRECTION; None = not a directional bet, unscoreable)
JOURNAL_DIRECTION = {"laggard_rotation": "BUY", "scale_out_ladder": "TRIM", "profit_ratchet": None}

# reason codes on a refused ticket
REFUSED_EV, REFUSED_NO_TARGET, REFUSED_FAMILY = "ev_below_bar", "no_analyst_target", "family_suppressed"
REFUSED_ROTATION_EDGE = "rotation_edge_below_bar"
REFUSED_NO_STOP, REFUSED_NO_PRICE = "no_stop", "no_price"


def _epoch(epoch=None):
    """Read the epoch at CALL time so a test (or a future policy override) can move it."""
    return epoch or smith_core.ENGINE_EPOCH


def post_epoch(date_str, epoch=None):
    """True when an ISO date/datetime string is on/after the engine epoch. An unparseable or
    missing date is NOT post-epoch: evidence we cannot date is evidence we cannot admit."""
    d = str(date_str or "")[:10]
    return len(d) == 10 and d >= _epoch(epoch)


def direction_group(bucket):
    """BUY stays BUY; TRIM and SELL collapse to SELL (the scorecard's 'TRIM/SELL'); HOLD and
    anything else is None -- HOLD is not graded on the same claim and is excluded entirely."""
    if bucket == "BUY":
        return "BUY"
    if bucket in ("TRIM", "SELL"):
        return "SELL"
    return None


# ---------------------------------------------------------------------------
# Evidence rows -> ideas
# ---------------------------------------------------------------------------
def scored_rows_from_proposals(proposals, epoch=None, count_excluded=False):
    """Graded, post-epoch proposal rows as {idea, direction, trigger_type, signed_pct, size_usd,
    source}. Reads the outcome cmd_score already wrote onto each proposal (`outcome_pct` is the
    SIGNED benefit: positive = the recommendation worked). Same admission rules as cmd_score's
    scorecard -- SCOREABLE_STATUSES (so `superseded` restatements are absent), graded verdicts only,
    HOLD excluded -- plus the epoch. With count_excluded, returns (rows, n_legacy_excluded)."""
    rows, legacy = [], 0
    for pr in proposals or []:
        if pr.get("status") not in SCOREABLE_STATUSES:
            continue
        if pr.get("outcome_verdict") not in GRADED_VERDICTS or pr.get("outcome_pct") is None:
            continue
        grp = direction_group(pr.get("direction_bucket") or proposal_direction(pr.get("action")))
        if grp is None:
            continue
        if not post_epoch(pr.get("date"), epoch):
            legacy += 1
            continue
        rows.append({"idea": idea_key(pr), "direction": grp,
                     "trigger_type": pr.get("trigger_type") or UNATTRIBUTED,
                     "signed_pct": float(pr["outcome_pct"]), "size_usd": pr.get("size_usd"),
                     "source": "proposal"})
    return (rows, legacy) if count_excluded else rows


def scored_rows_from_shadow_journal(entries, epoch=None, count_excluded=False):
    """Scored, post-epoch trigger_journal.json entries in the same row shape. `date` is the day the
    trigger row was EMITTED, so the epoch test is on the emission date. The signed value applies the
    entry's direction to the raw 7d move (BUY: up is a win; TRIM/SELL: down is a win). An entry
    with no directional claim (profit_ratchet, `n/a`) is skipped. Entries carrying a
    `direction_bucket` (written by the gate for shadowed rows) use it; older ones use
    JOURNAL_DIRECTION by trigger_type."""
    rows, legacy = [], 0
    for e in entries or []:
        if not e.get("scored") or e.get("verdict") not in JOURNAL_GRADED or e.get("outcome_pct") is None:
            continue
        bucket = e.get("direction_bucket") or JOURNAL_DIRECTION.get(e.get("trigger_type"))
        grp = direction_group(bucket)
        if grp is None:
            continue
        if not post_epoch(e.get("date"), epoch):
            legacy += 1
            continue
        pct = float(e["outcome_pct"])
        pseudo = {"ticker": e.get("ticker"), "direction_bucket": "BUY" if grp == "BUY" else "TRIM",
                  "trigger_type": e.get("trigger_type"), "date": e.get("date")}
        rows.append({"idea": idea_key(pseudo), "direction": grp,
                     "trigger_type": e.get("trigger_type") or UNATTRIBUTED,
                     "signed_pct": pct if grp == "BUY" else -pct, "size_usd": None,
                     "source": "shadow_journal"})
    return (rows, legacy) if count_excluded else rows


def dedupe_scored_rows(rows):
    """One record per IDEA (smith_core.idea_key -- the scorecard's own definition, not a copy).

    An idea is restated every run it has not yet worked, so counting rows inflates n and biases the
    record negative. Each idea's value is the MEAN signed outcome over its rows, net of the
    round-trip fee; it is a `hit` when that mean clears VERDICT_THRESHOLD_PCT (the scorecard's
    'worked' bar). When an idea appears in both the proposal record and the shadow journal the
    proposal rows win -- the journal must never double-count what the scorecard already holds."""
    by_idea = {}
    for r in rows:
        by_idea.setdefault(r["idea"], []).append(r)
    ideas = []
    for key in sorted(by_idea, key=lambda k: tuple(str(x) for x in k)):
        grp = by_idea[key]
        props = [r for r in grp if r["source"] == "proposal"]
        use = props or grp
        mean_signed = sum(r["signed_pct"] for r in use) / len(use)
        ideas.append({"idea": key, "direction": use[0]["direction"],
                      "trigger_type": use[0]["trigger_type"], "n_rows": len(use),
                      "net_pct": mean_signed - ROUND_TRIP_FEE_PCT,
                      "hit": mean_signed > VERDICT_THRESHOLD_PCT,
                      "source": "proposal" if props else "shadow_journal"})
    return ideas


# ---------------------------------------------------------------------------
# Family verdicts
# ---------------------------------------------------------------------------
def edge_multiplier(mean_ev_net_pct):
    """clamp(1 + 0.5*mean/5.0, 0, 1.25): monotone in the family's measured net expectancy. Only a
    `proven` family uses it (floored at 1.0 there); it is exposed separately so its monotonicity is
    a tested property, not an accident of the verdict logic."""
    return max(0.0, min(FAMILY_MULT_MAX,
                        1.0 + FAMILY_MULT_SLOPE * mean_ev_net_pct / FAMILY_MULT_MEAN_SCALE_PCT))


def _stats(ideas):
    n_eff = len(ideas)
    out = {"n_rows": sum(i["n_rows"] for i in ideas), "n_ideas": n_eff, "n_eff": n_eff,
           "source_counts": {"proposal": sum(1 for i in ideas if i["source"] == "proposal"),
                             "shadow_journal": sum(1 for i in ideas if i["source"] == "shadow_journal")},
           "hit_rate": None, "mean_ev_net_pct": None, "se": None, "ci95": [None, None]}
    if not n_eff:
        return out
    nets = [i["net_pct"] for i in ideas]
    mean = sum(nets) / n_eff
    out["hit_rate"] = round(sum(1 for i in ideas if i["hit"]) / n_eff, 4)
    out["mean_ev_net_pct"] = round(mean, 4)
    if n_eff >= 2:
        se = statistics.stdev(nets) / math.sqrt(n_eff)
        out["se"] = round(se, 4)
        out["ci95"] = [round(mean - CI_Z * se, 4), round(mean + CI_Z * se, 4)]
    return out


def family_verdict(rows):
    """Verdict + multiplier for ONE family (or one direction) from its scored rows.

    `rows` are raw evidence rows (already epoch-filtered by the scored_rows_* readers); they are
    de-duplicated to ideas here, so n_eff is a count of independent ideas. The order of the tests is
    the safety property: NOTHING below N_MIN can gate or scale, however bad the numbers look --
    five ideas that all lost is an anecdote, and this desk has taken a single corrupt anchor for a
    trend before (a phantom -39% TRIM set the whole trim accuracy on n=7)."""
    ideas = dedupe_scored_rows(rows)
    st = _stats(ideas)
    n, mean = st["n_eff"], st["mean_ev_net_pct"]
    lb, ub = st["ci95"]
    if n < N_MIN or lb is None:
        verdict, mult = UNPROVEN, 1.0
        basis = (f"n_eff {n} < {N_MIN}: too few independent post-epoch ideas to gate or scale "
                 "(multiplier 1.00, never gates)" if n else
                 "n_eff 0: no post-epoch scored ideas -- the legacy engine's record is excluded "
                 "(ENGINE_EPOCH), so nothing measured yet (multiplier 1.00, never gates)")
    elif n >= N_SUPPRESS and ub < 0:
        verdict, mult = SUPPRESSED, 0.0
        basis = (f"n_eff {n} >= {N_SUPPRESS} and upper 95% bound {ub:+.2f}% < 0: the family loses "
                 "net of fees -> shadow (still fires, still scored, can earn its vote back)")
    elif lb > 0:
        verdict, mult = PROVEN, max(1.0, edge_multiplier(mean))
        basis = (f"n_eff {n} >= {N_MIN} and lower 95% bound {lb:+.2f}% > 0: measured positive edge "
                 f"(mean {mean:+.2f}% net)")
    else:
        verdict, mult = WATCH, FAMILY_MULT_WATCH
        basis = (f"n_eff {n} >= {N_MIN} but the 95% interval [{lb:+.2f}%, {ub:+.2f}%] straddles 0: "
                 "no proven edge, no proven loss -> x0.75 haircut, no gate")
    return {**st, "verdict": verdict, "multiplier": round(mult, 4), "basis": basis}


def build_table(proposals, journal_entries=None, epoch=None):
    """The whole evidence table: one verdict per (direction, trigger_type) family AND one per
    direction, over post-epoch evidence only. Keys are 'BUY|trend_entry' / 'SELL|thesis_break' and
    'BUY' / 'SELL'. `excluded_legacy` counts what the epoch kept OUT, so the exclusion is visible."""
    p_rows, p_legacy = scored_rows_from_proposals(proposals, epoch, count_excluded=True)
    j_rows, j_legacy = scored_rows_from_shadow_journal(journal_entries, epoch, count_excluded=True)
    rows = p_rows + j_rows
    fams = {}
    for r in rows:
        fams.setdefault(f"{r['direction']}|{r['trigger_type']}", []).append(r)
    dirs = {d: [r for r in rows if r["direction"] == d] for d in ("BUY", "SELL")}
    return {"engine_epoch": _epoch(epoch),
            "by_family": {k: family_verdict(v) for k, v in sorted(fams.items())},
            "by_direction": {d: family_verdict(v) for d, v in dirs.items()},
            "excluded_legacy": {"proposal_rows": p_legacy, "shadow_journal_rows": j_legacy},
            "evidence_rule": ("only proposals / shadow-journal rows dated on or after ENGINE_EPOCH "
                              "count; the legacy engine's outcomes are history, not calibration")}


def gate_for(table, direction, trigger_type):
    """The `gate` block a ticket carries. Uses the FAMILY's verdict once the family has enough
    independent ideas to have one (n_eff >= N_MIN); until then it falls back to the DIRECTION's
    verdict, labelled, so a thinly-observed trigger inherits what the desk has shown about buys or
    sells in general instead of being an unexamined blank. A direction that is itself unproven
    yields the inert unproven/1.00 block -- the honest day-one answer."""
    grp = direction_group(direction) or direction
    fam_key = f"{grp}|{trigger_type or UNATTRIBUTED}"
    fam = (table.get("by_family") or {}).get(fam_key)
    dr = (table.get("by_direction") or {}).get(grp)
    level, src, key = "none", None, fam_key
    if fam and fam["n_eff"] >= N_MIN:
        level, src = "family", fam
    elif dr and dr["n_eff"] >= N_MIN:
        level, src, key = "direction", dr, grp
    else:
        src = fam or dr
        if src is not None:
            level = "family" if fam else "direction"
            key = fam_key if fam else grp
    if src is None:
        src = {"verdict": UNPROVEN, "multiplier": 1.0, "n_eff": 0, "n_rows": 0, "n_ideas": 0,
               "hit_rate": None, "mean_ev_net_pct": None, "ci95": [None, None],
               "basis": family_verdict([])["basis"]}
    basis = src["basis"] + ("" if level != "direction" or not fam else
                            f" [family {fam_key} has n_eff {fam['n_eff']} < {N_MIN}: direction verdict used]")
    return {"verdict": src["verdict"], "multiplier": src["multiplier"], "basis": basis,
            "family": key, "level": level, "n_eff": src["n_eff"], "n_rows": src["n_rows"],
            "hit_rate": src["hit_rate"], "mean_ev_net_pct": src["mean_ev_net_pct"],
            "ci95": src["ci95"], "protective_exit": trigger_type in PROTECTIVE_EXIT_TRIGGERS}


# ---------------------------------------------------------------------------
# Edge estimate
# ---------------------------------------------------------------------------
def p_win_estimate(family_hit_rate, n_eff, conviction_score):
    """P(win), never invented.

        w      = n_eff / (n_eff + P_WIN_SHRINK_K)
        p_base = w * family_hit_rate + (1 - w) * P_WIN_PRIOR
        p_win  = clamp(p_base * (0.8 + 0.4 * conviction/100), P_WIN_FLOOR, P_WIN_CEILING)

    With n_eff = 0 this is the UNCALIBRATED prior (0.45), shrunk only by conviction -- the correct
    day-one behaviour with the legacy record excluded. Conviction is a 0-100 score; None is treated
    as neutral (factor 1.0) rather than guessed."""
    n = max(0, int(n_eff or 0))
    w = n / (n + P_WIN_SHRINK_K)
    fhr = P_WIN_PRIOR if family_hit_rate is None else family_hit_rate
    p_base = w * fhr + (1.0 - w) * P_WIN_PRIOR
    if conviction_score is None:
        tilt = 1.0
    else:
        c = max(0.0, min(100.0, float(conviction_score)))
        tilt = P_WIN_CONVICTION_LOW + P_WIN_CONVICTION_SPAN * c / 100.0
    return max(P_WIN_FLOOR, min(P_WIN_CEILING, p_base * tilt))


def fee_r(stop_pct):
    """The round-trip fee expressed in R: ROUND_TRIP_FEE_PCT / stop_pct. None without a stop."""
    if not stop_pct or stop_pct <= 0:
        return None
    return ROUND_TRIP_FEE_PCT / stop_pct


def payoff_r(entry_price, target_price, stop_pct):
    """(payoff_R, uncapped_R, was_capped) from a target hard-capped at entry*(1 + TARGET_CAP_R *
    stop_pct/100). A target at or below entry pays 0R (never negative: the loss side of the EV
    formula already carries the downside). None when any input is missing -- an unknown payoff is
    never estimated."""
    if not entry_price or entry_price <= 0 or not target_price or not stop_pct or stop_pct <= 0:
        return None, None, False
    uncapped = max(0.0, (target_price - entry_price) / entry_price * 100.0 / stop_pct)
    capped = min(uncapped, TARGET_CAP_R)
    return capped, uncapped, uncapped > TARGET_CAP_R


def expected_value(p_win, payoff_r_, fee_r_):
    """EV_R = p_win*payoff_R - (1 - p_win) - fee_R. The loss side is exactly 1R (the stop)."""
    if p_win is None or payoff_r_ is None or fee_r_ is None:
        return None
    return p_win * payoff_r_ - (1.0 - p_win) - fee_r_


def f_edge(ev_r):
    """Entry size scale from EV: clamp(EV_R / EV_R_FULL, F_EDGE_MIN, 1.0). A barely-passing idea is a
    small position, a strong one is full size; it can never ENLARGE a ticket past its conviction
    size (conviction already sizes it -- see the identity in smith_math._apply_edge_gate)."""
    if ev_r is None:
        return F_EDGE_MIN
    return max(F_EDGE_MIN, min(1.0, ev_r / EV_R_FULL))


def evaluate_position(*, conviction_score, gate, price, stop_pct, target_usd, target_source=None,
                      target_as_of=None, include_fee=True):
    """The `edge` block for one long position (an entry, or -- include_fee=False -- HOLDING one).

    Returns {status, p_win, p_win_basis, payoff_r, payoff_r_uncapped, target_capped, target_usd,
    fee_r, ev_r, ev_bar_r, kelly_quarter, f_edge, refused_because, reason_code}. `status` is `ok`
    only when p_win, payoff and fee are all known; otherwise EV is None and `refused_because` names
    what is missing (a buy with no analyst target is SHADOW with that reason -- payoff is never
    estimated)."""
    fam_hr, n_eff = gate.get("hit_rate"), gate.get("n_eff") or 0
    p = p_win_estimate(fam_hr, n_eff, conviction_score)
    w = n_eff / (n_eff + P_WIN_SHRINK_K)
    p_basis = (f"prior {P_WIN_PRIOR:.2f} (UNCALIBRATED) shrunk by conviction "
               f"{'n/a' if conviction_score is None else format(conviction_score, '.1f')}"
               if n_eff == 0 else
               f"family {gate.get('family')} hit rate {fam_hr:.2f} at n_eff {n_eff} "
               f"(weight {w:.2f}) blended with prior {P_WIN_PRIOR:.2f}, tilted by conviction "
               f"{'n/a' if conviction_score is None else format(conviction_score, '.1f')}")
    edge = {"status": "ok", "p_win": round(p, 4), "p_win_basis": p_basis, "payoff_r": None,
            "payoff_r_uncapped": None, "target_capped": False, "target_usd": target_usd,
            "target_source": target_source, "target_as_of": target_as_of, "entry_usd": price,
            "stop_pct": stop_pct, "fee_r": None, "ev_r": None, "ev_bar_r": MIN_EV_R,
            "kelly_quarter": None, "f_edge": None, "refused_because": None, "reason_code": None}
    if not price:
        edge.update(status="no_price", reason_code=REFUSED_NO_PRICE,
                    refused_because="no entry price -- payoff cannot be computed (never estimated)")
        return edge
    if not stop_pct:
        edge.update(status="no_stop", reason_code=REFUSED_NO_STOP,
                    refused_because="no stop distance (no ATR) -- R cannot be defined (never estimated)")
        return edge
    fr = fee_r(stop_pct) if include_fee else 0.0
    edge["fee_r"] = round(fr, 4)
    if not target_usd:
        edge.update(status="no_target", reason_code=REFUSED_NO_TARGET,
                    refused_because=("no fresh analyst target (none cached within "
                                     f"{smith_core.ANALYST_TARGET_MAX_AGE_DAYS}d) -- payoff is unknown, "
                                     "so the buy is shadow, not estimated"))
        return edge
    pr, unc, capped = payoff_r(price, target_usd, stop_pct)
    ev = expected_value(p, pr, fr)
    edge.update(payoff_r=round(pr, 4), payoff_r_uncapped=round(unc, 4), target_capped=capped,
                ev_r=round(ev, 4), f_edge=round(f_edge(ev), 4),
                kelly_quarter=smith_conviction.kelly_fraction(p, pr) if pr > 0 else 0.0)
    if include_fee and ev < MIN_EV_R:
        edge["reason_code"] = REFUSED_EV
        edge["refused_because"] = (f"EV {ev:.2f}R below the {MIN_EV_R:.2f}R bar (p_win {p:.2f}, "
                                   f"payoff {pr:.1f}R{' capped from %.1fR' % unc if capped else ''}, "
                                   f"fee {fr:.2f}R)")
    return edge


def rotation_edge(buy_edge, hold_edge):
    """The pair-level term: EV_R(buy) - EV_R(holding the name being sold) >= ROTATION_MIN_EDGE_R.

    EV_R_of_holding is defined from what is measurable and nothing else: the SOLD name's own
    conviction-derived p_win and its own capped analyst-target payoff, no fee (it is already held),
    on the same evidence family as the buy. If the held name has no target or no stop its EV is
    unknown and the term is `unassessed` -- it neither passes nor refuses, and is recorded as such
    -- rather than fabricating a number. (A rotation is a SELL plus a BUY: the sell leg is not
    EV-gated, only the buy leg and this comparison are.)"""
    if not buy_edge or buy_edge.get("ev_r") is None:
        return {"assessed": False, "reason": "buy leg EV unknown", "edge_r": None,
                "min_edge_r": ROTATION_MIN_EDGE_R, "passes": None}
    if not hold_edge or hold_edge.get("ev_r") is None:
        why = (hold_edge or {}).get("refused_because") or "no measurable EV for the name being sold"
        return {"assessed": False, "reason": f"EV of holding the sell name unknown: {why}",
                "edge_r": None, "min_edge_r": ROTATION_MIN_EDGE_R, "passes": None,
                "hold_ev_r": None}
    edge_r = buy_edge["ev_r"] - hold_edge["ev_r"]
    return {"assessed": True, "edge_r": round(edge_r, 4), "min_edge_r": ROTATION_MIN_EDGE_R,
            "hold_ev_r": hold_edge["ev_r"], "passes": edge_r >= ROTATION_MIN_EDGE_R, "reason": None}


def deemph_factor(name_buckets, deemphasized):
    """x0.85 (once, never per bucket) when any of a name's bullish signal buckets is in the
    strategist's `deemphasize_buckets`; else 1.0. BOUNDED by construction: the strategist's
    opinion is one LLM read of a hit-rate table, so it can shrink a ticket by 15% and never zero
    it, whatever list it writes."""
    if deemphasized and set(name_buckets or ()) & set(deemphasized):
        return DEEMPH_SIZE_MULT
    return 1.0


def active_deemphasis(state, today, extra_buckets=None):
    """The set of signal buckets the strategist asked to de-emphasise, that are still admissible.

    Read from `state.strategist_deemphasis` ({buckets, as_of}, written by smith_memory's strategist
    merge) plus, for a same-run desk revision, `extra_buckets` from the current out_strategist.json.
    Two bounds keep one LLM opinion from becoming policy: an opinion older than DEEMPH_MAX_AGE_DAYS
    lapses, and only names in smith_core.BUCKET_DIRECTION (the buckets the journal actually scores)
    are admitted, so free text or a typo can never match anything."""
    known = set(smith_core.BUCKET_DIRECTION)
    out = set()
    rec = (state or {}).get("strategist_deemphasis") or {}
    as_of = str(rec.get("as_of") or "")[:10]
    if as_of and today is not None:
        try:
            import datetime as _dt
            age = (today - _dt.date.fromisoformat(as_of)).days
        except (ValueError, TypeError):
            age = None
        if age is not None and 0 <= age <= smith_core.DEEMPH_MAX_AGE_DAYS:
            out |= {b for b in (rec.get("buckets") or []) if b in known}
    out |= {b for b in (extra_buckets or []) if b in known}
    return frozenset(out)


def scaled_size(size_usd, factor, clamped_by, growth_cap_usd):
    """size * factor, where a factor above 1 (only a `proven` family) may lift a ticket only if it
    was NOT already bound by a clamp and never past `growth_cap_usd` (the policy max for the stop).
    A factor <= 1 always applies in full."""
    if not size_usd or size_usd <= 0:
        return size_usd
    new = size_usd * factor
    if new > size_usd:
        if clamped_by:
            return size_usd
        if growth_cap_usd is not None:
            new = min(new, max(size_usd, growth_cap_usd))
    return new


# ---------------------------------------------------------------------------
# The gate
# ---------------------------------------------------------------------------
def decide_gate(cands):
    """vote per candidate. Each cand: {id, kind ('single'|'pair'), direction ('BUY'|'SELL'),
    trigger_type, gate, edge (buys), rotation (pairs)}.

      SELL   live, unless its family is `suppressed` AND it is not a protective exit. Never EV-gated.
      BUY    shadow (with refused_because) when the family is suppressed, the edge is unknown
             (no target/stop/price), EV_R < MIN_EV_R, or -- for a rotation -- the assessed pair edge is
             below ROTATION_MIN_EDGE_R. Otherwise live.
    """
    out = {}
    for c in cands:
        g, tt = c.get("gate") or {}, c.get("trigger_type")
        protective = tt in PROTECTIVE_EXIT_TRIGGERS
        d = {"vote": "live", "refused_because": None, "reason_code": None, "protective": protective,
             "suppression_ignored": False}
        if c["direction"] == "SELL":
            if g.get("verdict") == SUPPRESSED:
                if protective:
                    d["suppression_ignored"] = True
                else:
                    d.update(vote="shadow", reason_code=REFUSED_FAMILY,
                             refused_because=f"family {g.get('family')} suppressed: {g.get('basis')}")
        else:
            e, rot = c.get("edge") or {}, c.get("rotation")
            if g.get("verdict") == SUPPRESSED:
                d.update(vote="shadow", reason_code=REFUSED_FAMILY,
                         refused_because=f"family {g.get('family')} suppressed: {g.get('basis')}")
            elif e.get("status") != "ok":
                d.update(vote="shadow", reason_code=e.get("reason_code"),
                         refused_because=e.get("refused_because"))
            elif e.get("reason_code") == REFUSED_EV:
                d.update(vote="shadow", reason_code=REFUSED_EV, refused_because=e["refused_because"])
            elif rot and rot.get("assessed") and rot.get("passes") is False:
                d.update(vote="shadow", reason_code=REFUSED_ROTATION_EDGE,
                         refused_because=(f"rotation edge {rot['edge_r']:+.2f}R (buy EV {e['ev_r']:.2f}R "
                                          f"minus holding {rot['hold_ev_r']:.2f}R) below the "
                                          f"{ROTATION_MIN_EDGE_R:.2f}R bar"))
        out[c["id"]] = d
    return out


def override_order(cands, decisions):
    """Gate-refused BUYS, best first: known EV descending, then conviction, then id. A buy whose EV
    is unknown ranks AFTER every buy whose EV is known but is still eligible -- the invariant must
    hold even when the data is thin."""
    gated = [c for c in cands if c["direction"] == "BUY" and decisions[c["id"]]["vote"] == "shadow"
             and decisions[c["id"]]["reason_code"] not in (REFUSED_NO_STOP, REFUSED_NO_PRICE)]

    def key(c):
        ev = (c.get("edge") or {}).get("ev_r")
        return (0 if ev is not None else 1, -(ev if ev is not None else 0.0),
                -(c.get("conviction_score") or 0.0), c["id"])
    return sorted(gated, key=key)


def enforce_cash_invariant(cands, decisions, cash_above_band, clears=None):
    """THE SAFETY INVARIANT: the gate may never take live BUY tickets to zero while cash is above
    band. One bad month must not become a permanent freeze.

    If the gate left no live buy, at least one buy was gate-refused, and cash is above band, the
    single highest-EV refused buy is restored with `gate_override` -- but only one that still
    clears materiality and heat, which `clears(cand_id) -> bool` reports (default: yes). The first
    that clears wins; if none does the shortfall is reported, never forced. Holds when EVERY buy
    fails the EV bar, and never fires when cash is not above band or when there was nothing to
    restore. Returns {"override": id|None, "attempted": [...], "required": bool, "why_not": str}."""
    live = [c for c in cands if c["direction"] == "BUY" and decisions[c["id"]]["vote"] == "live"]
    order = override_order(cands, decisions)
    res = {"required": bool(not live and order and cash_above_band), "override": None,
           "attempted": [], "why_not": None, "cash_above_band": bool(cash_above_band)}
    if live:
        res["why_not"] = "live buys remain after the gate"
        return res
    if not order:
        res["why_not"] = "the gate refused no buy -- nothing to restore"
        return res
    if not cash_above_band:
        res["why_not"] = "cash is not above band -- no override"
        return res
    for c in order:
        res["attempted"].append(c["id"])
        if clears is None or clears(c["id"]):
            decisions[c["id"]] = {**decisions[c["id"]], "vote": "live", "gate_override": GATE_OVERRIDE_LABEL,
                                  "overridden_refusal": decisions[c["id"]]["refused_because"]}
            res["override"] = c["id"]
            return res
    res["why_not"] = ("no gate-refused buy clears materiality and heat -- override not forced "
                      f"(tried {', '.join(res['attempted'])})")
    return res


# ---------------------------------------------------------------------------
# One reader for signal-bucket hit rates -- EPOCH-FILTERED
# ---------------------------------------------------------------------------
# THE USER'S INSTRUCTION (2026-09-20/21): "Don't use the earlier proposal hit data as the actual
# performance data in the current redesign, as earlier proposals were too broken", then, told the
# signal-bucket tables were not epoch-filtered: "correct this and any similar older hit-rate issue".
# The bucket tables (journal.json / compute_journal.json `bucket_hit_rates`, `bucket_hit_rates_7d`,
# `name_bucket_grades`) are built by cmd_journal from signal firings, and every firing before
# ENGINE_EPOCH was sized, ranked and traded by the legacy engine -- the record the user ruled
# inadmissible. cmd_journal now tallies only firings dated on/after the epoch and stamps its output
# with BUCKET_RATES_EPOCH_KEY. This module is the ONE reader: a table whose stamp is missing or
# differs from the live epoch is a legacy table (persisted before the filter, or built under an
# older epoch) and is treated as EMPTY, so a stale journal.json can never leak legacy rates into a
# size, a priority, a vote or a retirement. The effect is meant to be large and goes inert until
# post-epoch signals mature (7d / 30d).
BUCKET_RATES_EPOCH_KEY = "bucket_rates_epoch"


def evidence_window(epoch=None):
    """The label every bucket-rate consumer prints beside a number: what window the rate covers."""
    return "since %s" % _epoch(epoch)


def admissible_bucket_tables(journal, epoch=None):
    """{bucket_hit_rates, bucket_hit_rates_7d, name_bucket_grades} a consumer may act on, from a
    journal.json / compute_journal.json dict. Empty tables unless the dict carries the CURRENT
    epoch's stamp; bucket-rate rows below BUCKET_RATE_MIN_N are dropped even then (grades keep their own low_confidence flag). Pure."""
    j = journal or {}
    empty = {"bucket_hit_rates": {}, "bucket_hit_rates_7d": {}, "name_bucket_grades": {}}
    if j.get(BUCKET_RATES_EPOCH_KEY) != _epoch(epoch):
        return empty

    def floor(table):
        return {b: r for b, r in (table or {}).items()
                if isinstance(r, dict) and (r.get("n") or 0) >= smith_core.BUCKET_RATE_MIN_N}
    # name_bucket_grades keep their thin (n<3, `low_confidence`) rows by design: they are DISPLAY
    # only -- no size, priority or gate reads them -- and each states its own n.
    return {"bucket_hit_rates": floor(j.get("bucket_hit_rates")),
            "bucket_hit_rates_7d": floor(j.get("bucket_hit_rates_7d")),
            "name_bucket_grades": dict(j.get("name_bucket_grades") or {})}


def bucket_rate(journal, bucket, epoch=None):
    """A signal bucket's measured hit rate, from ONE reader, with its source AND window LABELLED.

    `journal` is a dict of already-admitted tables (admissible_bucket_tables output, or a
    compute_journal.json stamped by cmd_journal). Prefers the validated 30d table when it has a
    reading for the bucket and falls back to 7d only then. Returns {n, hit_rate_pct, payoff_ratio,
    source: '30d'|'7d', interim: bool, window: 'since <epoch>'} or None -- None below
    BUCKET_RATE_MIN_N, so a thin post-epoch sample never speaks. Two consumers used to disagree
    (the priority scorer read 7d while the track-record lookup read 30d); this is the one reader.

    SCOPE CORRECTION (2026-09-21): this docstring used to say the epoch exclusion does not apply
    because these are signal outcomes, not proposal outcomes. The user ruled otherwise: signals
    that fired under the legacy engine were graded on trades that engine sized and timed, and the
    bucket tables now count only firings on/after ENGINE_EPOCH."""
    j = journal or {}
    for table, src in ((j.get("bucket_hit_rates") or {}, "30d"), (j.get("bucket_hit_rates_7d") or {}, "7d")):
        hr = table.get(bucket)
        if hr and (hr.get("n") or 0) >= smith_core.BUCKET_RATE_MIN_N:
            return {"n": hr["n"], "hit_rate_pct": hr.get("hit_rate_pct"),
                    "payoff_ratio": hr.get("payoff_ratio"), "source": src, "interim": src == "7d",
                    "window": evidence_window(epoch)}
    return None


def bucket_adjustment(journal, bullish_buckets, epoch=None):
    """(points, reason) for a BUY from its bullish signal buckets' measured record.

    PENALTY: any bullish bucket below BUCKET_PENALTY_HIT_RATE_PCT over at least BUCKET_PENALTY_MIN_N
    scored signals costs 2 points (the worst such bucket is named). MOMENTUM+VOLUME (20%, n=15) and
    TARGET GAP (36.8%, n=19) were ignored entirely -- the branch only ever rewarded. REWARD: as
    before, the best bucket above 55% earns +2 -- but only when no bullish bucket is in penalty,
    because a name is only as well-evidenced as its worst signal (the same conservative rule the
    track-record multiplier uses). Those two example rates were LEGACY-engine rates; since the
    2026-09-21 epoch filter both branches read only post-epoch signals and stay silent (0, None)
    until enough have matured. Every reason names its window."""
    rated = [(b, bucket_rate(journal, b, epoch)) for b in (bullish_buckets or [])]
    rated = [(b, r) for b, r in rated if r and r.get("hit_rate_pct") is not None]
    bad = [(b, r) for b, r in rated
           if r["hit_rate_pct"] < BUCKET_PENALTY_HIT_RATE_PCT and r["n"] >= BUCKET_PENALTY_MIN_N]
    if bad:
        b, r = min(bad, key=lambda x: (x[1]["hit_rate_pct"], -x[1]["n"], x[0]))
        return (-BUCKET_PENALTY_POINTS,
                f"bullish signal '{b}' has a {r['hit_rate_pct']:.0f}% {r['source']} hit rate "
                f"(n={r['n']}, {r['window']}) -- below {BUCKET_PENALTY_HIT_RATE_PCT:.0f}% over at least "
                f"{BUCKET_PENALTY_MIN_N} scored signals in this book")
    good = [(b, r) for b, r in rated if r["hit_rate_pct"] > BUCKET_REWARD_HIT_RATE_PCT]
    if good:
        b, r = max(good, key=lambda x: (x[1]["hit_rate_pct"], x[0]))
        tag = " INTERIM (not yet 30d-validated)" if r["interim"] else ""
        return (2, f"bullish signal '{b}' has a {r['hit_rate_pct']:.0f}%{tag} {r['source']} hit rate "
                   f"(n={r['n']}, {r['window']}) in this book")
    return 0, None


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def explain(as_of, table, tickets, invariant, constants_extra=None):
    """The compute_edge.json payload: the whole evidence table per family and direction (n_rows,
    n_ideas, n_eff, mean, CI, verdict, multiplier, basis), every gated ticket with the numbers the
    sizer used, the invariant's outcome, and the constants. RETURNS the dict; the pipeline writes
    the file."""
    live = [t for t in tickets if t.get("vote_after") == "live"]
    refused = [t for t in tickets if t.get("refused_because")]
    verdicts = {}
    for row in list((table.get("by_family") or {}).values()) + list((table.get("by_direction") or {}).values()):
        verdicts[row["verdict"]] = verdicts.get(row["verdict"], 0) + 1
    return {
        "as_of": as_of,
        "engine_epoch": table.get("engine_epoch"),
        "evidence_rule": table.get("evidence_rule"),
        "excluded_legacy": table.get("excluded_legacy"),
        "by_direction": table.get("by_direction"),
        "by_family": table.get("by_family"),
        "verdict_counts": verdicts or {UNPROVEN: 0},
        "all_unproven": all(r["verdict"] == UNPROVEN for r in
                            list((table.get("by_family") or {}).values())
                            + list((table.get("by_direction") or {}).values())),
        "tickets": tickets,
        "summary": {"tickets": len(tickets), "live_after_gate": len(live), "refused": len(refused),
                    "buys_refused_by_ev": sum(1 for t in tickets if t.get("reason_code") == REFUSED_EV),
                    "buys_refused_no_target": sum(1 for t in tickets if t.get("reason_code") == REFUSED_NO_TARGET)},
        "invariant": invariant,
        "constants": {"MIN_EV_R": MIN_EV_R, "EV_R_FULL": EV_R_FULL, "F_EDGE_MIN": F_EDGE_MIN,
                      "ROTATION_MIN_EDGE_R": ROTATION_MIN_EDGE_R, "TARGET_CAP_R": TARGET_CAP_R,
                      "P_WIN_PRIOR": P_WIN_PRIOR, "P_WIN_PRIOR_STATUS": "UNCALIBRATED engineering prior",
                      "P_WIN_SHRINK_K": P_WIN_SHRINK_K, "P_WIN_CEILING": P_WIN_CEILING,
                      "N_MIN": N_MIN, "N_SUPPRESS": N_SUPPRESS, "FAMILY_MULT_WATCH": FAMILY_MULT_WATCH,
                      "FAMILY_MULT_MAX": FAMILY_MULT_MAX, "DEEMPH_SIZE_MULT": DEEMPH_SIZE_MULT,
                      "ROUND_TRIP_FEE_PCT": ROUND_TRIP_FEE_PCT, **(constants_extra or {})},
        "rules": ["EV gate applies to BUYS only; sells are never EV-refused",
                  "protective exits ignore even a suppressed family verdict",
                  "unproven (n_eff < %d) never gates or scales" % N_MIN,
                  "legacy proposals (before ENGINE_EPOCH) are excluded from every number here"],
    }


LEGACY_EXCLUSION_NOTE = (
    "Proposals dated before %s came from the LEGACY engine (mechanical sizing, discarded stops, no "
    "materiality floor, no heat budget, no EV bar). Their outcomes measure that engine, not this "
    "one, and are EXCLUDED from every number the sizer and gate use. Do not quote legacy accuracy "
    "or expectancy as the current engine's record -- if you cite it at all, label it 'legacy-engine "
    "history'.")


def scorecard_gate_block(edge_payload, scorecard=None):
    """What the strategist's slice carries: the EXACT numbers the sizer used (read from
    compute_edge.json), so the LLM cannot contradict them in prose. The legacy scorecard is shown
    only as labelled history. `edge_payload` None -> an explicit unavailable block, never silence."""
    ep = _epoch()
    if not edge_payload:
        return {"available": False, "engine_epoch": ep,
                "reason": "compute_edge.json absent this run -- run the triggers stage; do not "
                          "characterise the sizer's gate from memory",
                "legacy_exclusion": LEGACY_EXCLUSION_NOTE % ep}
    sc = scorecard or {}
    since = sc.get("since_epoch")
    tickets = [{k: t.get(k) for k in ("id", "ticker", "family", "direction", "vote_before", "vote_after",
                                       "refused_because", "gate_override", "p_win", "payoff_r", "ev_r",
                                       "f_edge", "f_family", "f_deemph", "size_before_usd", "size_after_usd")}
               for t in (edge_payload.get("tickets") or [])]
    return {
        "available": True, "source": "compute_edge.json (the file the sizer wrote this run)",
        "as_of": edge_payload.get("as_of"), "engine_epoch": edge_payload.get("engine_epoch"),
        "legacy_exclusion": LEGACY_EXCLUSION_NOTE % edge_payload.get("engine_epoch"),
        "excluded_legacy": edge_payload.get("excluded_legacy"),
        "all_families_unproven": edge_payload.get("all_unproven"),
        "direction_verdicts": {d: {k: v.get(k) for k in ("verdict", "multiplier", "n_eff", "n_rows",
                                                          "mean_ev_net_pct", "ci95")}
                               for d, v in (edge_payload.get("by_direction") or {}).items()},
        "non_unproven_families": {k: {kk: v.get(kk) for kk in ("verdict", "multiplier", "n_eff", "mean_ev_net_pct", "ci95")}
                                  for k, v in (edge_payload.get("by_family") or {}).items()
                                  if v.get("verdict") != UNPROVEN},
        "since_epoch_scorecard": since if since else "no post-rebuild proposal has been scored yet (n=0)",
        "tickets": tickets, "summary": edge_payload.get("summary"),
        "invariant": edge_payload.get("invariant"), "constants": edge_payload.get("constants"),
        "rule": ("These are the numbers the sizer used. State them as given; do not restate a "
                 "different expectancy, hit rate or verdict in prose. A buy marked shadow with a "
                 "refused_because is not to be proposed live; a gate_override buy was restored by "
                 "the cash-above-band safety invariant and is live."),
    }
