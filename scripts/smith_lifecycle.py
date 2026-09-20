"""Proposal lifecycle, outcome scoring, and stop-loss efficacy.

Split out of smith_math.py 2026-08-16: the file had reached 4,085 lines and mixed
four unrelated domains. Shared primitives live in smith_core; smith_math keeps the
per-run compute stages, the pipeline runner and the CLI, and imports these.
"""

import json
import re
import os
from datetime import date, datetime, timezone

import smith_marketdata
import smith_risk
from smith_core import *  # noqa: F401,F403 -- shared constants and IO helpers
from smith_core import load_json, emit, fail


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


def _proposal_parse_datetime(raw):
    """Full-precision parse, for the dedup survivor tie-break ONLY -- every other caller wants
    _proposal_parse_date's DATE granularity (age-in-days, 7-day expiry, history sort) and must
    keep using that. This exists because that truncation broke same-day reaffirmation: found live
    2026-08-24, a 08:55 quick-sweep proposal and a 14:45 deep-review resize of the SAME ticker both
    parsed to date(2026,8,24), so the "keep whichever is chronologically LATEST" rule saw them as
    date-equal and fell through to the rationale-length tie-break instead -- on five separate
    tickers that run, the fresher (often more concise) resize LOST to the older, more verbose
    rationale purely on string length, keeping stale size_usd/rationale on the surviving row.
    This desk now runs several sweeps a day, so same-day repeats are the normal case, not an edge
    case -- the comparison needs real chronological ordering, not just date equality."""
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw)
        # Zone-less = IST, the desk convention (smith_clock). Reading it as UTC put a zone-less
        # proposal 5.5 hours away from an offset-stamped one written the same morning.
        return dt if dt.tzinfo else dt.replace(tzinfo=IST)
    except ValueError:
        pass
    d = _proposal_parse_date(raw)
    return datetime(d.year, d.month, d.day, tzinfo=IST) if d else None

def _assign_stable_proposal_ids(props):
    """Assign each proposal a stable id (P-###), once, never reassigned or reused."""
    max_id = 0
    for pr in props:
        pid = pr.get("id", "")
        if pid.startswith("P-") and pid[2:].isdigit():
            max_id = max(max_id, int(pid[2:]))
    for pr in props:
        if not pr.get("id"):
            max_id += 1
            pr["id"] = f"P-{max_id:03d}"


def _backfill_proposal_ticker_and_bucket(props, infer_ticker, direction):
    """Backfill a missing ticker from action text and set direction_bucket, before the main
    pass so every later check sees both fields populated."""
    for pr in props:
        if not pr.get("ticker"):
            inferred = infer_ticker(pr)
            if inferred:
                pr["ticker"] = inferred
                pr["note"] = (pr.get("note", "") + " | ticker backfilled from action text (2026-07-29 fix)").strip(" |")
        pr.setdefault("direction_bucket", DIRECTION_BUCKET.get(direction(pr.get("action")), "HOLD"))


def _dedupe_expire_void_proposals(props, today_date, current_tickers, direction, parse_date, parse_datetime):
    """Cross-run dedup (same (ticker, direction) merges into one running survivor, folding
    repeats into a `history` list), 7-calendar-day auto-expiry, and auto-void when the
    presupposed position has since been exited. Mutates `props` in place (notes, history,
    repeat_count) and returns the set of proposal indices to supersede.

    CONSOLIDATION vs REPEAT (fixed 2026-09-14, live incident: P-285/P-286/P-287). A (ticker,
    direction) collision has always been treated as ONE idea restated -- keep the fresher/
    longer occurrence's size_usd and rationale, fold the other into `history`. That is correct
    when the two rows really are the same idea (identical pair_id, or neither carries one), but
    on 2026-09-14 two INDEPENDENT rotation legs both wanted to buy KLAC the same day --
    profit_rotation-NBIS-KLAC ($134.73) and cluster_rotation-AMD-KLAC ($309.68), different
    pair_ids, different funding sources. Treating the second as a "repeat" of the first kept
    only the smaller size and discarded the AMD-KLAC pair_id entirely, which orphaned that
    pairing's sell leg (P-286 "Sell AMD") the same run its buy leg was created -- its funding
    destination vanished with no trace of where it had gone.
    A restatement of the same idea NEVER changes pair_id (a rotation's ladder-rank refresh keeps
    proposing the same pairing, see P-269 -> P-287 above); two DIFFERENT, non-empty pair_ids is
    exactly the signal that these are two real, independently-funded trades that happen to share
    a ticker and direction, not one idea said twice. That case sums size_usd into the survivor
    instead of discarding the loser's, and records the loser's pair_id on the survivor's
    `also_funds_pair_ids` list so the pairing stays traceable (and so
    _retire_orphaned_rotation_legs can see it -- see that function's docstring). A collision
    where either side lacks a pair_id, or both share one, still merges the old way: that is
    exactly the "same idea, restated" case this function was built for."""
    seen = {}  # (ticker, direction) -> index of the current running survivor
    to_supersede = set()

    for i, pr in enumerate(props):
        if pr.get("status") != "open":
            continue
        prop_date = parse_date(pr.get("date", ""))
        key = (pr.get("ticker"), direction(pr.get("action")))
        if key in seen and key[0] is not None:
            j = seen[key]
            # Full datetime precision here (2026-08-24 fix), not just date -- this desk runs
            # several sweeps a day now, so two same-day proposals are the normal case, and
            # comparing at date-only granularity made them look tied and fall through to the
            # rationale-length coin-flip below even when one was genuinely hours fresher.
            # created_utc (2026-09-14) is the exact write instant; `date` is the fallback for rows
            # written before it existed.
            date_i = parse_datetime(pr.get("created_utc") or pr.get("date", ""))
            date_j = parse_datetime(props[j].get("created_utc") or props[j].get("date", ""))
            # keep whichever occurrence is chronologically LATEST (freshest price/rationale);
            # on an exact timestamp tie, keep the longer rationale as the original heuristic did.
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

            pid_survivor = props[survivor].get("pair_id")
            pid_loser = props[loser].get("pair_id")
            is_consolidation = bool(pid_survivor) and bool(pid_loser) and pid_survivor != pid_loser

            history = props[survivor].setdefault("history", [])
            # fold the loser's own history (if it was itself already a merged survivor once) in first,
            # oldest-first, then the loser's own top-level occurrence.
            history.extend(props[loser].get("history", []))
            history.append({
                "date": props[loser].get("date"),
                "size_usd": props[loser].get("size_usd"),
                "price_at_proposal": props[loser].get("price_at_proposal"),
                "rationale": props[loser].get("rationale"),
                **({"pair_id": pid_loser} if is_consolidation else {}),
            })
            history.sort(key=lambda h: parse_date(h.get("date", "")) or date.min)
            props[survivor]["repeat_count"] = len(history) + 1
            first_date = history[0].get("date") if history else props[survivor].get("date")

            if is_consolidation:
                # Two real, independently-funded trades -- sum the sizes rather than letting
                # the fresher/longer occurrence's size_usd win outright and silently drop the
                # other's dollars.
                combined_size = round((props[survivor].get("size_usd") or 0)
                                       + (props[loser].get("size_usd") or 0), 2)
                props[survivor]["size_usd"] = combined_size
                also_funds = list(props[survivor].get("also_funds_pair_ids") or [])
                # carry forward anything the loser had itself already absorbed from an earlier
                # 3-way same-day collision on this (ticker, direction), not just its own pair_id.
                for extra in [pid_loser] + list(props[loser].get("also_funds_pair_ids") or []):
                    if extra and extra != pid_survivor and extra not in also_funds:
                        also_funds.append(extra)
                props[survivor]["also_funds_pair_ids"] = also_funds
                props[survivor]["note"] = (
                    props[survivor].get("note", "").replace(" | auto-superseded 2026-07-29 -- duplicate of another open", "")
                    + f" | consolidated {today_date}: two independently-funded {key[1]} proposals for "
                      f"{key[0]} landed the same day ({pid_survivor} + {pid_loser}) -- sizes combined to "
                      f"${combined_size:,.2f}, both pair_ids preserved"
                ).strip(" |")
            else:
                props[survivor]["note"] = (
                    props[survivor].get("note", "").replace(" | auto-superseded 2026-07-29 -- duplicate of another open", "")
                    + f" | recommended {len(history) + 1}x since {first_date}, still open"
                ).strip(" |")

            seen[key] = survivor
            to_supersede.add(loser)
            if is_consolidation:
                if "consolidated" not in props[loser].get("note", "") and "duplicate" not in props[loser].get("note", ""):
                    props[loser]["note"] = (props[loser].get("note", "")
                                            + f" | auto-superseded {today_date} -- its {pid_loser} leg's size "
                                              f"folded into {props[survivor]['id']}, which now also funds this "
                                              "pairing (see also_funds_pair_ids on the survivor)").strip(" |")
            elif "duplicate" not in props[loser].get("note", ""):
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

    return to_supersede


def _classify_voided_proposals(props, to_supersede, today_date):
    """Marks each superseded index `status: "superseded"` and splits the labels into
    voided_today vs voided_stale (G60): an auto-void is normal for an OLD proposal whose
    position has since been exited, and an ALARM for one created this run -- that combination
    means the strategist just wrote an idea the void logic killed on arrival, almost always a
    direction-classification bug (a verb missing from DIRECTION_KEYWORDS defaulting to HOLD,
    which presupposes a holding a fresh proposal by definition doesn't have)."""
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
    return voided_today, voided_stale, recon_warnings


def _score_proposal_priority(pr, risk_by_ticker, directional_breach, cash_short, cash_excess,
                             cash_pct, cash_band, stretch_by_ticker, derisk, rotation_by_ticker,
                             hit_rates_7d, trigger_live_sets, trigger_rows, trigger_pairs,
                             state_sector_map, cluster_breach, total_book_usd):
    """Deterministic priority score for one open proposal (G47): over-cap position (+2),
    directional cluster breach (+2), directional cash-band breach (+2), genuine stretch on a
    TRIM (+2), a measured bullish signal on a BUY (+2), a live non-ATR trigger (+3 flat, or a
    conviction-proportional bonus for CONVICTION_TRIGGERS), a restatement about to auto-retire
    (+1), SELL over TRIM (+1), and a penalty for a BUY with no supporting evidence at all (-1).
    HIGH is capped to MEDIUM unless a live trigger (a price-moving criterion, not portfolio
    mechanics) backs it. Mutates `pr` in place: priority_score/priority/priority_reasons/
    proposal_class/cluster, plus the "honest sizing" full_cure_usd/cure_basis/cure_pct/
    tranche_note fields on a TRIM/SELL."""
    score, reasons = 0, []
    ticker, bucket, rc = pr.get("ticker"), pr.get("direction_bucket", "HOLD"), pr.get("repeat_count", 1)
    rpos = risk_by_ticker.get(ticker) if ticker else None
    cluster = (rpos.get("cluster") if rpos
               else (pr.get("cluster") or state_sector_map.get(ticker)))
    # Defined unconditionally (not just inside the over_cap branch below) so the honest-sizing
    # cure block and any other later use in this function can read it safely regardless of
    # whether this position is over cap at all -- see the branch below for what it means.
    exempted = False
    if rpos and rpos.get("over_cap"):
        # STRONG-NAME EXEMPTION (2026-09-07, user: "check the strategist's proposals for the
        # same fix... check everywhere"). rotation_by_ticker is cmd_rotation's own output --
        # the SAME strong/overbought exemption already applied to Rotation analysis and the
        # De-risk queue's fragility score. Reusing it here (rather than re-deriving thesis/
        # signal/RSI a fourth time) means a name reads identically across all three surfaces:
        # if rotation_bucket exempted it from trim_risk_cap (strengthening thesis + net-
        # bullish signal + not yet overbought), the priority scorer gives it NO over-cap
        # bonus either -- a proposal to trim a name that's earning its size on cap mechanics
        # alone shouldn't outrank a proposal with an actual trigger behind it. A name
        # rotation_by_ticker has no entry for (never reached compute_rotation, or missing RSI)
        # keeps the OLD, safer full bonus -- this can only ever reduce urgency, never invent it.
        rot = rotation_by_ticker.get(ticker) if ticker else None
        exempted = bool(rot) and rot.get("over_cap") and rot.get("bucket") != "trim_risk_cap"
        if exempted:
            reasons.append(f"{ticker} at {rpos.get('cap_multiple', 0):.2f}x its ATR risk cap, but "
                          f"strengthening thesis + net-bullish signal, not yet overbought -- no "
                          f"cap-breach bonus (see rotation_bucket)")
        else:
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
        reasons.append(f"cash short at {cash_pct:.1f}% vs a [{cash_band[0]},{cash_band[1]}]% band "
                       "-- this also rebuilds it")
    if cash_excess and bucket == "BUY":
        score += 2
        reasons.append(f"cash in excess at {cash_pct:.1f}% vs a [{cash_band[0]},{cash_band[1]}]% band "
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
    has_live_trigger = False
    if tt in LIVE_TRIGGERS and ticker in trigger_live_sets.get(tt, set()):
        row = trigger_rows[tt].get(ticker) or {}
        if not row and tt in PAIRED_TRIGGERS and pr.get("pair_id") in trigger_pairs:
            # Paired rows carry no top-level ticker, so trigger_rows (single-ticker only) is
            # empty for them -- pull the matching leg out of trigger_pairs instead of losing
            # the conviction number entirely.
            pair_row = trigger_pairs[pr["pair_id"]]
            for leg in (pair_row.get("sell_leg"), pair_row.get("buy_leg")):
                if leg and leg.get("ticker") == ticker:
                    row = leg
                    break
        if tt in CONVICTION_TRIGGERS:
            # Conviction-driven triggers earn a priority bonus proportional to how strong the
            # idea is, not a flat +3 -- a 21-point "low" conviction add shouldn't out-rank a
            # 4-point cluster-cap breach the way a flat bonus would. round(score/10) keeps the
            # scale comparable to the old flat bonus (a 70+ "high" conviction idea still nets +7,
            # above the old +3; a 20-point "low" nets +2, below it) while remaining monotonic.
            conv_score = row.get("conviction_score", 0) or 0
            conv_bonus = max(1, round(conv_score / 10))
            score += conv_bonus
            reasons.append(f"{tt}: conviction {conv_score} "
                            f"({row.get('conviction_tier', 'unscored')}) -- " +
                            "; ".join(row.get("conviction_reasons") or row.get("reasons") or []))
        else:
            score += 3
            reasons.append(f"{tt}: " + "; ".join(row.get("reasons") or []))
        has_live_trigger = True
        for b in row.get("blockers") or []:
            reasons.append(f"caveat -- {b}")
    elif tt in SHADOW_TRIGGERS:
        reasons.append(f"{tt} is SHADOW-SCORED, not yet voting -- this trigger has no measured "
                       "hit rate in this book, so it contributes 0 to priority by design")
    elif tt in LIVE_TRIGGERS:
        reasons.append(f"{tt} was the stated trigger but {ticker} is not in this run's "
                       f"{tt} candidate list -- condition is no longer live")

    # Repeat bonus (lowered 2026-08-24: restatement auto-retirement now fires at rc>=3, see
    # the retirement pass below, so a proposal never reaches this scoring pass carrying rc>=3
    # from a PRIOR run -- this branch only still sees rc==2 on the run where it's about to
    # cross the retirement line, one run ahead of that pass).
    if rc == 2:
        score += 1
        reasons.append(f"recommended {rc}x, still unactioned -- one more restatement auto-retires it")
    if bucket == "SELL":
        score += 1
    # The old penalty fired on any BUY with score==0, which punished precisely the trade this
    # book was missing: a well-founded add on a healthy name that happens to breach nothing.
    # It now only applies to a buy with NO typed trigger at all -- genuinely discretionary.
    if bucket == "BUY" and score <= 0 and tt not in (LIVE_TRIGGERS | SHADOW_TRIGGERS):
        score -= 1
        reasons.append("discretionary add -- no active breach or typed trigger behind it")
    pr["priority_score"] = score
    priority = "HIGH" if score >= 4 else "MEDIUM" if score >= 2 else "LOW"
    # 2026-08-17, user-reported: proposals were reaching HIGH on pure portfolio-composition
    # arithmetic (over_cap + cluster breach + cash band + repeat count can stack to 8) with
    # NO criterion that says anything about the STOCK -- no live trigger of any kind
    # (technical, catalyst, or thesis-driven). That combination is a volatility-budget/loose-
    # composition finding, not a trade idea, and is capped at MEDIUM regardless of how high
    # the mechanical score stacks. A live trigger (has_live_trigger, +3 above) is exempt from
    # the cap by construction -- it is the one component that IS a price-moving criterion.
    if priority == "HIGH" and not has_live_trigger:
        priority = "MEDIUM"
        reasons.append("capped at MEDIUM: no live trigger (technical, catalyst, or thesis) "
                       "behind this proposal -- score reached HIGH on cap/cluster/cash/repeat "
                       "mechanics alone, which describes the portfolio, not the stock")
    pr["priority"] = priority
    pr["priority_reasons"] = reasons
    pr["proposal_class"] = proposal_class(tt)
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
        # EXEMPTION APPLIES HERE TOO (2026-09-07) -- an exempted name (strengthening thesis +
        # net-bullish signal, not yet overbought) gets no cap-breach priority bonus above, and
        # for the identical reason it should not be handed a "trim $X to cure the cap" sizing
        # basis either: that number asserts the cap breach IS the reason to act, which is
        # exactly what the scorer just decided isn't true for this name. Falls through to the
        # cluster-ceiling cure below if that's separately live; if neither applies, cures stays
        # empty and no tranche_note is written -- same as any other proposal with no cure basis.
        if rpos and rpos.get("over_cap") and rpos.get("headroom_usd") is not None and not exempted:
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


def _check_condition_based_retirement(pr, today_date, risk_by_ticker, directional_breach,
                                      current_tickers, drift, trig_rsi, trig_abs,
                                      trigger_live_sets, state_thesis, derisk, cluster_breach,
                                      rotation_by_ticker, hit_rates_7d, parse_date,
                                      hold_max_age_days, is_accepted=False):
    """Retires one open (or accepted-but-unexecuted) proposal in place (status/retired_on/
    retired_reason/note) the moment its OWN objective trigger is verifiably gone -- reusing the
    same typed structural signals the priority scorer computes (over_cap, directional
    cluster/cash breach, live trigger membership), never free-text rationale (that approach
    false-positived and was disabled 2026-07-29). A condition requiring judgement is left open
    for the strategist instead of guessed at. Appends a {"id","action","reason"} dict to the
    caller-supplied `retired` list when it fires; returns nothing.

    EXTENDED 2026-09-09 to also test `accepted_by_user` rows (user: "once accepted, the
    proposal stay forever. however i want it to go if the underlying reason is gone or the
    current setup no longer remains supportive"). Accepting is a stated intention, not proof
    the trade happened -- see the dashboard's own "Accepted -- awaiting execution" panel note --
    so a row can sit there for days while its cap/cluster/trigger/thesis premise quietly
    reverses. `is_accepted` gates OUT the two retirement paths that measure INACTION rather
    than a cleared condition (tactical HOLD age-out, restatement-count decay): acceptance is
    itself the opposite of inaction, so neither should fire on an accepted row. Every objective
    condition check below (cap cleared, cluster back in band, trigger no longer live, thesis
    resolved, position exited or gone to dust) still runs exactly as it does for an open row."""
    ticker = pr.get("ticker")
    bucket = pr.get("direction_bucket", "HOLD")
    rpos = risk_by_ticker.get(ticker) if ticker else None
    cluster = pr.get("cluster")
    cl = directional_breach(cluster, bucket)
    # EXEMPTION (2026-09-07): a strengthening-thesis + net-bullish-signal name that isn't yet
    # overbought was already exempted from the cap-breach PRIORITY bonus in
    # _score_proposal_priority (same rotation_by_ticker lookup, same condition) -- treating its
    # raw over_cap flag as a reason to keep a generic cap/cluster trim OPEN here would silently
    # undo that: the proposal would carry no urgency in the score but never retire either,
    # sitting forever on a reason the scorer has already said doesn't apply to this name.
    rot = rotation_by_ticker.get(ticker) if ticker else None
    exempted = bool(rot) and rot.get("over_cap") and rot.get("bucket") != "trim_risk_cap"
    over_cap = bool(rpos and rpos.get("over_cap")) and not exempted
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
        # catalyst_threat and thesis_break (added 2026-08-17, retirement corrected 2026-08-24):
        # SCORED cap/cluster-independent, same discipline as overbought_distribution -- an
        # in-cap name is a valid catalyst-driven trim, never blocked by being within its cap.
        # But RETIREMENT follows the "stretch" pattern instead (AND of conditions, not a bare
        # own-condition test): unlike overbought_distribution, which is a purely technical
        # signal never claiming a cap problem too, the strategist routinely layers a
        # catalyst_threat trim ON TOP OF a live cap/cluster breach as co-primary evidence (BE,
        # 2026-08-24: "worst cap overage in the book (2.64x)... the structural catalyst and
        # cap breach carry this trim"). Testing only the catalyst's own condition meant that
        # when the catalyst cleared (state.factor_catalysts genuinely does replace, not
        # append, each run -- see PERSIST), the proposal retired outright even though its
        # OTHER, still-live reason (the worst cap overage in the entire book) would on its own
        # have kept any ordinary cap-breach trim open. Retire only when NEITHER survives.
        elif pr.get("trigger_type") == "catalyst_threat":
            catalyst_ok = ticker in trigger_live_sets.get("catalyst_threat", set())
            if not catalyst_ok and not over_cap and not cl:
                why = (f"{ticker} no longer appears in a structural-threat factor catalyst, "
                       f"and neither the ATR cap nor cluster band independently justifies "
                       "this trim any more -- the structural reason has cleared")
            # else: still live via the catalyst itself, OR an independent cap/cluster breach
            # -- keep open either way, same AND-of-conditions discipline as stretch below.
        elif pr.get("trigger_type") == "thesis_break":
            th_now = smith_risk.thesis_status(state_thesis.get(ticker))
            if th_now is None:
                pass  # cannot test (no usable status) -- keep open rather than guess
            elif th_now != "broken" and not over_cap and not cl:
                why = (f"{ticker}'s thesis is now '{th_now}', no longer 'broken', and "
                       "neither the ATR cap nor cluster band independently justifies this "
                       "trim any more -- the structural reason has cleared")
            # else: thesis still broken, OR an independent cap/cluster breach -- keep open.
        elif pr.get("trigger_type") in ("trend_breakdown", "conviction_exit"):
            # Conviction-driven TRIM/SELL triggers (added 2026-08-24): tested purely on their
            # OWN condition re-appearing in this run's live list, same discipline as
            # oversold_reversion/overbought_distribution -- no cap/cluster fallback, because
            # unlike catalyst_threat these are not typically layered with cap-breach
            # reasoning by construction (they fire from signal-polarity/convergence, not from
            # a breach at all). trigger_live_sets already covers every LIVE_TRIGGERS member
            # generically (see cmd_triggers), so this is one branch for both trigger types.
            tt_now = pr.get("trigger_type")
            if ticker not in trigger_live_sets.get(tt_now, set()):
                why = (f"{ticker} no longer appears in this run's live {tt_now} list -- the "
                       "condition this trim/exit was sized against has cleared")
        elif pr.get("trigger_type") in PAIRED_TRIGGERS:
            # Paired rotation SELL legs (added 2026-08-24, bug found live on first real
            # dispatch): must NOT fall through to the generic cap/cluster test below -- a
            # profit_rotation/cluster_rotation sell leg's reason for existing is "stretched
            # and yet-to-rally elsewhere" or "cluster laggard vs a performer", never a cap or
            # cluster-band breach, so testing over_cap/cl here retires it the instant it turns
            # out to (correctly) not be over cap -- which is every time, since MSFT/AMD were
            # never over-cap trims to begin with. First live proposals from the rebuilt engine
            # (MSFT->CLS, AMD->TER) were both auto-retired within the same run they were
            # created, one call after cmd_proposals appended them, before this fix. The real
            # retirement condition for both legs of a pair lives entirely in the
            # PAIRED-ROTATION RETIREMENT pass below (keyed on trigger_pairs), so this leg does
            # nothing here -- `pass`, not a test.
            pass
        elif pr.get("trigger_type") in SHADOW_TRIGGERS:
            # G85 FIX (2026-09-02): shadow triggers are SCORING-exempt (no measured hit rate
            # yet), never RETIREMENT-exempt -- the two are different questions, and the old
            # bare `pass` conflated them. The 2026-08-18 stop cascade cut MRVL 7sh->4sh and
            # cleared its cap breach to 0.809x, but its scale_out_ladder trim (P-114, sized
            # against the pre-cascade position) had no test of its own and survived anyway.
            # Three objective, schema-free checks -- no new field needed, unlike the fourth
            # criterion in G85's original fix note ("materially reduced since proposal date"),
            # which needs a stored pre-proposal baseline this schema doesn't carry yet and is
            # deliberately left for a future pass rather than guessed at here.
            if ticker and ticker not in current_tickers:
                why = (f"{ticker} is no longer held -- the shadow-scored "
                       f"{pr.get('trigger_type')} this proposed has nothing left to act on")
            elif rpos is not None and rpos.get("market_value_usd") is not None:
                remaining = rpos["market_value_usd"]
                if remaining < DUST_USD_DEFAULT:
                    why = (f"{ticker}'s remaining position (${remaining:,.0f}) is under the "
                           f"${DUST_USD_DEFAULT:g} dust threshold -- too small for this "
                           f"shadow-scored {pr.get('trigger_type')} to still apply")
                elif pr.get("size_usd") and pr["size_usd"] > 0.5 * remaining:
                    why = (f"the proposed ${pr['size_usd']:,.0f} trim now exceeds half of "
                           f"{ticker}'s remaining ${remaining:,.0f} position -- resize or "
                           "re-propose against the current position")
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
            th_now = smith_risk.thesis_status(state_thesis.get(ticker))
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
        elif pr.get("trigger_type") in ("trend_entry", "conviction_average", "entry_setup", "reentry", "bench_diversifier"):
            # Conviction-driven BUY triggers (added 2026-08-24): tested on their own
            # condition re-appearing live, same as the TRIM-side branch above. A `reentry`
            # additionally expires on a hard 20-trading-day clock even if conviction is
            # still live -- a re-entry candidate that's gone unactioned for a month is a
            # stale read of the exit event, not a standing idea.
            tt_now = pr.get("trigger_type")
            if ticker not in trigger_live_sets.get(tt_now, set()):
                why = (f"{ticker} no longer appears in this run's live {tt_now} list -- the "
                       "condition this buy was sized against has cleared")
            elif tt_now == "reentry" and pr.get("exited_on"):
                # Structured field, never parsed from rationale prose -- parsing free text is
                # exactly what made the 2026-07-29 breach-cleared voider false-positive and
                # get disabled (see this file's cmd_proposals docstring). `exited_on` must be
                # set explicitly when a reentry proposal is created.
                exited_on = _proposal_parse_date(pr["exited_on"])
                if exited_on and (today_date - exited_on).days > 20:
                    why = f"{ticker}'s exit was {(today_date - exited_on).days} days ago -- past the 20-day reentry window"
    elif bucket == "HOLD":
        # A STOP instruction is not hold-fire advice (found 2026-08-17). P-094 "Set hard stop
        # on ORCL @ $139.14" was auto-retired after 2 days as time-expired tactical guidance,
        # and P-100 "Raise MRVL stop to cost basis" was one day from the same fate. A stop
        # level is a STANDING risk instruction: it stays valid until it is acted on, the
        # position exits, or the level is superseded -- it does not go stale on a clock.
        # Both landed in the HOLD bucket only because neither buys nor sells anything.
        is_stop = bool(re.search(r"\bstop\b", str(pr.get("action") or ""), re.I)) or \
                  (pr.get("trigger_type") == "profit_ratchet")
        if ticker and ticker not in current_tickers:
            why = (f"{ticker} is no longer held -- the "
                   + ("stop this proposed has nothing left to protect"
                      if is_stop else "position this advised holding on is gone"))
        elif is_stop:
            # G85 FIX (2026-09-02): a standing stop instruction still never expires on AGE
            # alone, but it must retire once its SUBJECT has materially shrunk. The
            # ticker-no-longer-held branch above only catches a FULL exit; it missed
            # P-104 ("Raise MU stop to cost basis"), which survived a stop cascade that cut
            # MU 2.5sh->0.5sh -- still technically held, at a fraction of its former size.
            why = None
            if rpos is not None and rpos.get("market_value_usd") is not None \
                    and rpos["market_value_usd"] < DUST_USD_DEFAULT:
                why = (f"{ticker}'s remaining position (${rpos['market_value_usd']:,.0f}) is "
                       f"under the ${DUST_USD_DEFAULT:g} dust threshold -- this stop "
                       "instruction has nothing material left to protect")
        elif age >= hold_max_age_days and not is_accepted:
            # Age-out measures INACTION -- days spent unacted on. An accepted HOLD has already
            # been acted on (mentally, if not yet in the ledger), so its clock is irrelevant;
            # gated out for accepted rows rather than retiring something the user just approved.
            why = (f"tactical HOLD is {age} days old -- hold-fire advice is time-bound by nature "
                   "and is not carried forward as standing guidance")

    # RESTATEMENT AUTO-RETIREMENT REMOVED (user decision 2026-09-15). This block used to retire
    # any proposal (repeat_count >= 3) purely for having been restated 3+ times, regardless of
    # whether the underlying trigger was still live -- the user's own words: "I look and take my
    # mental note from the proposals, if the proposal is still making sense based on the latest
    # analysis we should keep it." Repeat count is not evidence the idea stopped making sense; it
    # is evidence the idea wasn't acted on, which the user wants to judge for themselves, not have
    # the desk judge on his behalf by deleting the option. `repeat_count` and `pr["note"]`
    # ("3rd time recommending this, id P-050") stay -- that's the visible signal the user reads by
    # eye; only the automatic kill switch on top of it is gone. Every OTHER rule in this function
    # (condition no longer live, thesis flipped, ticker no longer held, dust threshold, age-out for
    # tactical HOLDs) stays exactly as-is: those test whether the proposal still makes sense, which
    # is precisely the bar the user wants applied. This also retires the paired-leg exemption that
    # used to sit here (added 2026-09-08 to stop this same rule from orphaning a rotation's other
    # leg) -- with the rule itself gone, there is nothing left for that exemption to guard against.

    if why:
        if is_accepted:
            why = f"(accepted, never executed) {why}"
        pr["status"] = "auto_retired"
        pr["retired_on"] = str(today_date)
        pr["retired_reason"] = why
        pr["note"] = (pr.get("note", "") + f" | auto-retired {today_date}: {why}").strip(" |")
        return {"id": pr.get("id"), "action": pr.get("action"), "reason": why, "was_accepted": is_accepted}
    return None


def _proposal_pair_ids(pr):
    """Every PAIRED_TRIGGERS pair_id a proposal participates in: its own `pair_id`, plus any it
    absorbed via same-day consolidation (`also_funds_pair_ids`, see
    _dedupe_expire_void_proposals). A consolidated survivor belongs to more than one pairing at
    once, which is exactly what the retirement pass below needs to know to avoid recreating the
    same orphaning bug the consolidation fix closed one level up."""
    ids = [pr.get("pair_id")] + list(pr.get("also_funds_pair_ids") or [])
    return [pid for pid in ids if pid and pid.startswith(PAIRED_TRIGGER_PREFIXES)]


def _retire_orphaned_rotation_legs(props, trigger_pairs, today_date, retired):
    """profit_rotation/cluster_rotation legs must retire TOGETHER, never independently -- the
    direct fix for "19 rotation pairs attempted all-time, 0 survived" (single-sided retirement
    used to orphan the other leg into an unpaired, half-explained proposal). Both legs share a
    pair_id; if the pair is no longer in this run's live trigger_pairs, retire whichever leg(s)
    are still open, together, one reason. Mutates `props` in place and appends to `retired`.

    Covers `accepted_by_user` legs too (2026-09-09) -- a pair can go stale exactly as easily
    after one leg is accepted as before, and there is no reason a pair should stay half-real
    (one leg auto-retired, its accepted twin still standing) just because acceptance happened
    to land on the surviving side.

    CONSOLIDATED SURVIVORS (added 2026-09-14, alongside the dedup consolidation fix -- see
    _dedupe_expire_void_proposals and _proposal_pair_ids). A proposal that absorbed another
    rotation's leg via `also_funds_pair_ids` now belongs to MULTIPLE pairings, indexed here
    under each of them, not just its own top-level pair_id -- otherwise the exact bug this
    function exists to prevent recurs one level up: pairing A goes stale, this pass retires
    pairing A's far leg on the strength of A alone, while the survivor it was funding stays
    open because it also funds a still-live pairing B. If ANY leg in a stale pairing's group is
    entangled with another pairing that IS still live, this pass does not retire anything in
    that group -- it flags every leg in it for manual review instead. Silently retiring only
    the untangled leg would leave the position half-unwound with no record of why; silently
    retiring the survivor too would kill a leg a still-live pairing needs. Both are the kind of
    judgement call the disabled breach-cleared auto-void comment above already says this file
    should not make from typed data alone -- surface it, don't guess."""
    if trigger_pairs is None:
        return
    by_pair_id = {}
    for pr in props:
        if pr.get("status") not in ("open", "accepted_by_user"):
            continue
        for pid in _proposal_pair_ids(pr):
            by_pair_id.setdefault(pid, []).append(pr)
    for pid, legs in by_pair_id.items():
        if pid in trigger_pairs:
            continue  # still live this run -- both legs stay open
        entangled = any(other in trigger_pairs
                        for leg in legs for other in _proposal_pair_ids(leg) if other != pid)
        if entangled:
            for leg in legs:
                leg["review_flags"] = sorted(set((leg.get("review_flags") or [])
                                                  + ["consolidated_pairing_partially_stale"]))
            continue
        for pr in legs:
            if pr.get("status") not in ("open", "accepted_by_user"):
                continue  # already retired via another one of its pairings this same pass
            was_accepted = pr.get("status") == "accepted_by_user"
            why = (f"the {pid.split('-')[0]} pairing this leg belongs to is no longer live "
                   "this run -- both legs of a rotation retire together, never one alone")
            if was_accepted:
                why = f"(accepted, never executed) {why}"
            pr["status"] = "auto_retired"
            pr["retired_on"] = str(today_date)
            pr["retired_reason"] = why
            pr["note"] = (pr.get("note", "") + f" | auto-retired {today_date}: {why}").strip(" |")
            retired.append({"id": pr.get("id"), "action": pr.get("action"), "reason": why, "was_accepted": was_accepted})


def _apply_live_rejustification(pr, price_now_by_ticker, risk_by_ticker, directional_breach, today_date,
                               rotation_by_ticker=None):
    """Recomputes `still_valid_because` (why this proposal survives TODAY) and `retires_when`
    (the inverse condition -- what would retire it tomorrow) plus a re-priced
    `price_drift_pct` and an evidence-quality flag (G58: a proposal whose sole basis is
    unverified qualitative claims), so the dashboard renders a current reason rather than a
    frozen sentence written days ago. Mutates `pr` in place."""
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
    elif _tt == "catalyst_threat":
        retires_when = (f"{ticker} no longer appears in a structural-threat factor catalyst "
                        "(cap/cluster-independent -- staying inside the ATR cap does NOT "
                        "retire this)")
    elif _tt == "thesis_break":
        retires_when = (f"{ticker}'s thesis is no longer 'broken' (cap/cluster-independent -- "
                        "staying inside the ATR cap does NOT retire this)")
    elif _tt in ("trend_breakdown", "conviction_exit"):
        retires_when = (f"{ticker} no longer appears in this run's live {_tt} list "
                        "(cap/cluster-independent -- staying inside the ATR cap does NOT retire this)")
    elif _tt in ("trend_entry", "conviction_average", "entry_setup", "bench_diversifier"):
        retires_when = f"{ticker} no longer appears in this run's live {_tt} list"
    elif _tt == "reentry":
        retires_when = (f"{ticker} no longer appears in this run's live reentry list, or 20 "
                        "trading days pass since its exit, whichever comes first")
    elif _tt in PAIRED_TRIGGERS:
        retires_when = (f"the {_tt} pairing {pr.get('pair_id')} is no longer live this run -- "
                        "both legs retire together, never one alone")
    elif _tt in SHADOW_TRIGGERS:
        retires_when = (f"n/a -- {_tt} is shadow-scored, tracked in trigger_journal.json rather "
                        "than lifecycle-managed here")
    elif bucket in ("TRIM", "SELL") and pr.get("trigger_type") == "stretch":
        retires_when = f"{ticker} drops out of the stretched cohort (no longer ahead of sector AND up)"
    elif bucket in ("TRIM", "SELL"):
        conds = []
        # EXEMPTION (2026-09-07): same rotation_by_ticker check as the scorer and the
        # retirement pass -- an exempted name (strengthening thesis + net-bullish signal, not
        # yet overbought) never had cap urgency counted for it, so telling the reader "retires
        # when the cap clears" here would misstate why this proposal is even open.
        rot = (rotation_by_ticker or {}).get(ticker) if ticker else None
        exempted = bool(rot) and rot.get("over_cap") and rot.get("bucket") != "trim_risk_cap"
        if rpos and rpos.get("over_cap") and not exempted:
            conds.append(f"{ticker} drops under its ATR risk cap")
        if cl:
            conds.append(f"{pr.get('cluster')} re-enters its policy band")
        retires_when = " OR ".join(conds) + " (both must clear -- either alone keeps it open)" if len(conds) > 1 else (conds[0] if conds else None)
    elif bucket == "BUY" and pr.get("trigger_type") == "signal_conviction":
        retires_when = f"'{pr.get('trigger_bucket')}' signal drops off {ticker} or its 7d hit rate falls to/below 55%"
    elif bucket == "BUY" and pr.get("cluster") and cl:
        retires_when = f"{pr.get('cluster')} re-enters its policy band"
    pr["retires_when"] = retires_when


def _compute_stacking_warnings(props, risk_by_ticker):
    """STACKING GUARD (2026-09-01, rebuilt 2026-09-06 after it failed on its own founding case).

    An ACCEPTED-but-unexecuted proposal did not block a new proposal on the same ticker+side --
    the dedup pass keys on OPEN proposals only, and acceptance moves a row to `accepted_by_user`,
    so accepting a trade removed it from the duplicate check while leaving the trade undone.
    Found live 2026-08-31: P-164 Sell MSFT $437.92 accepted and awaiting execution, while P-201
    proposed a further Sell MSFT $305.96 -- $743.88 combined against a $1,019.88 position, 73% of
    the holding, neither row referencing the other.

    THE 2026-09-06 REBUILD (G88). The v1 guard did not fire on a live recurrence of exactly that
    case, for two independent reasons, and each is a general lesson:

      1. IT COMPARED ONLY accepted x open. Two OPEN rows on one ticker were never examined at
         all. Live that day: AVGO P-212 $142.60 + P-226 $500.00 = 89.8% of the position, and
         FSLR P-214 $182.69 + P-228 $300.00 = 78.7% -- both silent. The guard was written
         against the status pair that caused the original incident rather than against the
         invariant it exists to protect, which is simply "do not sell more than you hold".
      2. IT COMPARED RAW DIRECTION BUCKETS, and TRIM and SELL are distinct buckets. So "Trim
         AVGO" and "Sell AVGO" -- the same act, differing only in the verb the strategist reached
         for -- were treated as unrelated sides. A guard keyed on verb strings does not cover the
         synonym set.

    Both are fixed by grouping instead of pairing: every live row (open OR accepted) is bucketed
    by (ticker, SIDE_GROUP), and any group of two or more is reported once with the combined
    total of ALL its members. Three stacked rows now yield one warning summing three sizes, not
    three pairwise warnings that each understate the exposure.

    This FLAGS (writes `stacks_on` on every member), it never auto-retires -- some stacks are
    deliberate incremental adds, and silently killing a legitimate second leg trades one failure
    mode for another. REDUCE-side stacks escalate to severity="high" above STACK_WARN_PCT because
    they are the bounded side: you cannot sell more than you hold, so a large combined percentage
    is a concrete, checkable error rather than merely an oversized bet.

    Mutates `props` in place and returns the flat list of stack_warnings dicts."""
    pos_value = {tk: rp.get("market_value_usd") for tk, rp in risk_by_ticker.items()
                 if rp.get("market_value_usd")}
    stack_warnings = []
    # Clear from EVERY row, not just the live ones. Clearing only live rows (the v1 behaviour,
    # kept through the first pass of the 2026-09-06 rebuild) leaves a permanent stale badge on
    # any row that WAS live when a stack was flagged and has since gone superseded/auto_retired
    # -- found live the same day on P-189, P-193, P-207, P-210 and P-221, two of which were
    # still rendering their stale badge on the dashboard. "Recomputed every run" has to mean
    # every row the field can appear on, not every row the recompute happens to visit.
    for pr in props:
        pr.pop("stacks_on", None)
    live = [pr for pr in props if pr.get("status") in ("open", "accepted_by_user")]

    groups = {}
    for pr in live:
        side = SIDE_GROUP.get(pr.get("direction_bucket") or "HOLD")
        if side is None:                    # HOLD stacks on nothing; it moves no money
            continue
        groups.setdefault((pr.get("ticker"), side), []).append(pr)

    for (ticker, side), members in sorted(groups.items(), key=lambda kv: (str(kv[0][0]), kv[0][1])):
        if len(members) < 2:
            continue
        combined = sum((m.get("size_usd") or 0) for m in members)
        mv = pos_value.get(ticker)
        pct = round(100.0 * combined / mv, 1) if mv else None
        sev = ("high" if (side == "REDUCE" and pct is not None and pct >= STACK_WARN_PCT)
               else "note")
        accepted = [m for m in members if m.get("status") == "accepted_by_user"]
        info = {
            # back-compat: the first accepted member, or None when the stack is all-open.
            # Kept because smith_dashboard.stacks_badge and the golden fixtures read these.
            "accepted_id": accepted[0].get("id") if accepted else None,
            "accepted_size_usd": accepted[0].get("size_usd") if accepted else None,
            "member_ids": [m.get("id") for m in members],
            "open_ids": [m.get("id") for m in members if m.get("status") == "open"],
            "accepted_ids": [m.get("id") for m in accepted],
            # the raw buckets that got grouped -- makes a Trim+Sell merge visible rather than
            # silently collapsed, which is the defect this rebuild exists to fix
            "sides_merged": sorted({(m.get("direction_bucket") or "HOLD") for m in members}),
            "combined_usd": round(combined, 2), "position_usd": mv,
            "combined_pct_of_position": pct, "side": side, "severity": sev}
        for m in members:
            m["stacks_on"] = info
        stack_warnings.append(dict(info, open_id=(info["open_ids"] or [None])[0], ticker=ticker))
    return stack_warnings


_PROPOSAL_ID_RE = re.compile(r"^P-\d{3,}$")


def _strength_key(pr, parse_datetime):
    """Ordering for "which of two conflicting proposals survives": FRESHER analysis first, then
    higher priority_score, then larger size. Freshness leads because a later run's strategist
    was handed the open queue and chose to write something different -- the same "latest
    occurrence wins" rule _dedupe_expire_void_proposals already applies to a restated idea.
    Rows written in one add-proposal batch share created_utc, so within a batch priority decides."""
    ts = parse_datetime(pr.get("created_utc") or pr.get("date", ""))
    stamp = float("-inf")
    if isinstance(ts, datetime):
        stamp = (ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)).timestamp()
    elif isinstance(ts, date):
        stamp = datetime(ts.year, ts.month, ts.day, tzinfo=timezone.utc).timestamp()
    score = pr.get("priority_score")
    return (stamp, score if isinstance(score, (int, float)) else float("-inf"),
            pr.get("size_usd") or 0)


def _proposals_conflict(a, b):
    """True when two proposals on the SAME ticker cannot both be followed as written.
      * opposite sides (BUY vs TRIM/SELL) -- a contradiction, always;
      * same side but different verbs (TRIM vs SELL) -- the same reduce idea restated with a
        different verb, which the (ticker, direction) dedup key cannot see -- UNLESS both carry
        non-overlapping rotation pair_ids, i.e. two independently-funded rotations (the P-285
        consolidation case), which is a legitimate stack for the stacking guard to flag;
      * identical verbs are NOT a conflict here: that is dedup's job (repeat or consolidation)."""
    ba, bb = a.get("direction_bucket"), b.get("direction_bucket")
    sa, sb = SIDE_GROUP.get(ba), SIDE_GROUP.get(bb)
    if sa is None or sb is None:
        return False
    if sa != sb:
        return True
    if ba == bb:
        return False
    pa, pb = set(_proposal_pair_ids(a)), set(_proposal_pair_ids(b))
    if pa and pb and not (pa & pb):
        return False
    return True


def _retire_with_partner_legs(props, loser, winner, why, today_date, retired):
    """Retires `loser` and every other still-open leg of its rotation pairing(s) -- legs retire
    together, never one alone (see _retire_orphaned_rotation_legs). The winner, and any leg that
    shares one of the winner's own pairings, is never touched."""
    winner_pairs = set(_proposal_pair_ids(winner))
    victims = [loser]
    for pid in _proposal_pair_ids(loser):
        for pr in props:
            if (pr is not loser and pr is not winner and pr.get("status") == "open"
                    and pid in _proposal_pair_ids(pr) and not (winner_pairs & set(_proposal_pair_ids(pr)))):
                victims.append(pr)
    for pr in victims:
        if pr.get("status") != "open":
            continue
        reason = why if pr is loser else f"rotation partner {loser.get('id')} was retired -- {why}"
        pr["status"] = "auto_retired"
        pr["retired_on"] = str(today_date)
        pr["retired_reason"] = reason
        pr["superseded_by"] = winner.get("id")
        pr["note"] = (pr.get("note", "") + f" | auto-retired {today_date}: {reason}").strip(" |")
        retired.append({"id": pr.get("id"), "action": pr.get("action"), "reason": reason,
                        "was_accepted": False})


def _apply_declared_supersessions(props, today_date, retired):
    """A proposal that names older ids in its typed `supersedes` field retires them (added
    2026-09-15, user: "automate this auto-retire of the weaker proposal"). The 2026-09-15
    strategist wrote "AMENDS P-263" / "RETIRES P-264" in rationale PROSE, which this file
    deliberately never parses (the 2026-07-29 false-positive class), so its explicit calls were
    lost and the user had to dismiss P-261 and P-264 by hand. A typed field closes that without
    reopening text parsing. Accepted rows are the user's decision: flagged, never retired."""
    by_id = {pr.get("id"): pr for pr in props if pr.get("id")}
    for pr in props:
        if pr.get("status") != "open":
            continue
        for target_id in pr.get("supersedes") or []:
            tgt = by_id.get(target_id)
            if tgt is None or tgt is pr:
                continue
            if tgt.get("status") == "accepted_by_user":
                tgt["review_flags"] = sorted(set((tgt.get("review_flags") or [])
                                                  + [f"declared_superseded_by_{pr.get('id')}"]))
                continue
            if tgt.get("status") != "open":
                continue
            why = (f"superseded by {pr.get('id')} ({pr.get('action')}), declared in that "
                   "proposal's `supersedes` field")
            _retire_with_partner_legs(props, tgt, pr, why, today_date, retired)


def _retire_weaker_conflicts(props, today_date, retired, parse_datetime):
    """AUTO-RETIRE THE WEAKER OF TWO CONFLICTING OPEN PROPOSALS (added 2026-09-15, user request
    after dismissing P-261 and P-264 by hand).

    Two live incidents the existing passes could not see: P-261 "Trim ASML" (09-10) stayed open
    beside P-305 "Sell ASML" (09-15) because the dedup key is (ticker, direction) and TRIM/SELL
    are different buckets; P-264 "Trim AMAT" stayed open beside P-314 "Buy AMAT" because nothing
    compared opposite sides at all. The stacking guard grouped the first pair but only FLAGS,
    by design, because some same-side stacks are deliberate.

    Groups live rows by ticker, walks OPEN rows strongest-first (_strength_key) and retires any
    row that conflicts (_proposals_conflict) with one already kept, together with its rotation
    partner legs. Accepted rows are never retired: an open row contradicting an accepted one gets
    a `contradicts_accepted_<id>` review flag, and same-side accepted stacks stay the stacking
    guard's job. Typed fields only -- direction_bucket, pair_id, priority_score, timestamps."""
    groups = {}
    for pr in props:
        if (pr.get("status") in ("open", "accepted_by_user") and pr.get("ticker")
                and SIDE_GROUP.get(pr.get("direction_bucket"))):
            groups.setdefault(pr["ticker"], []).append(pr)
    for ticker in sorted(groups, key=str):
        rows = groups[ticker]
        if len(rows) < 2:
            continue
        accepted = [r for r in rows if r.get("status") == "accepted_by_user"]
        open_rows = sorted((r for r in rows if r.get("status") == "open"),
                           key=lambda r: _strength_key(r, parse_datetime), reverse=True)
        kept = []
        for r in open_rows:
            if r.get("status") != "open":
                continue  # already retired this pass as another loser's rotation partner
            winner = next((k for k in kept if _proposals_conflict(r, k)), None)
            if winner is None:
                kept.append(r)
                continue
            kind = ("opposite sides" if SIDE_GROUP[r["direction_bucket"]] != SIDE_GROUP[winner["direction_bucket"]]
                    else "same side, different verb")
            kw, kr = _strength_key(winner, parse_datetime), _strength_key(r, parse_datetime)
            because = ("it is the fresher analysis" if kw[0] != kr[0]
                       else f"higher priority_score ({kw[1]} vs {kr[1]})" if kw[1] != kr[1]
                       else "larger size")
            why = (f"weaker of two conflicting {ticker} proposals ({kind}): kept "
                   f"{winner.get('id')} {winner.get('action')} because {because}")
            _retire_with_partner_legs(props, r, winner, why, today_date, retired)
        for r in kept:
            if r.get("status") != "open":
                continue
            flags = [f"contradicts_accepted_{a.get('id')}" for a in accepted
                     if SIDE_GROUP[a["direction_bucket"]] != SIDE_GROUP[r["direction_bucket"]]]
            if flags:
                r["review_flags"] = sorted(set((r.get("review_flags") or []) + flags))


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
    FIXED 2026-08-03 (G87, user-reported: "the open proposal keeps on increasing"): the dedup
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
    FIXED 2026-09-14 (live incident: P-285/P-286/P-287, see _dedupe_expire_void_proposals and
    _retire_orphaned_rotation_legs docstrings for the full mechanics): the merge above treated
    EVERY same-ticker/same-direction/same-day collision as one idea restated, even when the two
    rows were actually two independently-funded rotation legs (different pair_ids) that happened
    to target the same buy ticker. That silently dropped the loser's size_usd and its pair_id,
    which orphaned the loser's own rotation partner. Two different, non-empty pair_ids now
    triggers a CONSOLIDATION instead of a repeat-fold: sizes sum, both pair_ids are kept
    (`also_funds_pair_ids` on the survivor), and the retirement pass now checks all of a
    proposal's pair_ids, not just its primary one, before deciding a leg is safe to retire.
    """
    p_path = os.path.join(args.base_dir, "proposals.json")
    proposals = load_json(p_path, default={"proposals": [], "scorecard": {}})
    drift = load_json(os.path.join(args.run_dir, "compute_drift.json"), default={})
    holdings = load_json(os.path.join(args.run_dir, "holdings.json"), default={"holdings_inr": []})

    props = proposals.get("proposals", [])
    today_date = resolve_today(args.today)
    current_tickers = {h["ticker"] for h in holdings.get("holdings_inr", [])}
    direction = _proposal_direction
    infer_ticker = _proposal_infer_ticker
    parse_date = _proposal_parse_date
    parse_datetime = _proposal_parse_datetime

    _assign_stable_proposal_ids(props)
    _backfill_proposal_ticker_and_bucket(props, infer_ticker, direction)

    to_supersede = _dedupe_expire_void_proposals(props, today_date, current_tickers, direction,
                                                 parse_date, parse_datetime)

    voided_today, voided_stale, recon_warnings = _classify_voided_proposals(props, to_supersede, today_date)

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
    # profit_rotation/cluster_rotation (added 2026-08-24) have a PAIRED shape -- no top-level
    # "ticker", instead sell_leg/buy_leg sub-dicts each carrying one -- so the generic c["ticker"]
    # extraction below would KeyError on them. _trigger_tickers() handles both shapes; every
    # other LIVE_TRIGGERS member is still a plain single-ticker row, unchanged.
    def _trigger_tickers(row):
        if row.get("ticker"):
            return [row["ticker"]]
        legs = [row.get("sell_leg"), row.get("buy_leg")]
        return [leg["ticker"] for leg in legs if leg and leg.get("ticker")]

    trigger_live_sets = {tt: {t for c in (triggers.get(tt) or []) for t in _trigger_tickers(c)}
                         for tt in LIVE_TRIGGERS}
    # trigger_rows keeps its old per-ticker single-row shape for single-ticker triggers; paired
    # triggers are looked up separately via trigger_pairs below, never through this dict, so a
    # paired row is deliberately left OUT of trigger_rows rather than picking one leg arbitrarily.
    trigger_rows = {tt: {c["ticker"]: c for c in (triggers.get(tt) or []) if c.get("ticker")}
                    for tt in LIVE_TRIGGERS | SHADOW_TRIGGERS}
    # pair_id -> the live compute_triggers.json row, for the paired-rotation retirement pass.
    trigger_pairs = {c["pair_id"]: c for tt in sorted(PAIRED_TRIGGERS)
                     for c in (triggers.get(tt) or []) if c.get("pair_id")}
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
        _score_proposal_priority(pr, risk_by_ticker, directional_breach, cash_short, cash_excess,
                                 _cash_pct, _cash_band, stretch_by_ticker, derisk, rotation_by_ticker,
                                 hit_rates_7d, trigger_live_sets, trigger_rows, trigger_pairs,
                                 state_sector_map, cluster_breach, total_book_usd)

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
    # RETIREMENT-ELIGIBLE STATUSES (extended 2026-09-09, user: "once accepted, the proposal stay
    # forever. however i want it to go if the underlying reason is gone or the current setup no
    # longer remains supportive"). `accepted_by_user` is a stated intention, not proof the trade
    # happened -- see the "Accepted -- awaiting execution" panel -- so it can go just as stale as
    # an open one while sitting unexecuted. `is_accepted` tells the checker which row it's
    # looking at so it can gate out the two decay paths (HOLD age-out, restatement count) that
    # measure inaction rather than a cleared condition -- see that function's own docstring.
    RETIREMENT_ELIGIBLE_STATUSES = ("open", "accepted_by_user")
    retired = []
    for pr in props:
        if pr.get("status") not in RETIREMENT_ELIGIBLE_STATUSES:
            continue
        result = _check_condition_based_retirement(pr, today_date, risk_by_ticker, directional_breach,
                                                    current_tickers, drift, trig_rsi, trig_abs,
                                                    trigger_live_sets, state_thesis, derisk, cluster_breach,
                                                    rotation_by_ticker, hit_rates_7d, parse_date,
                                                    HOLD_MAX_AGE_DAYS,
                                                    is_accepted=(pr.get("status") == "accepted_by_user"))
        if result:
            retired.append(result)

    # -- CONFLICT RETIREMENT (added 2026-09-15). A spec's typed `supersedes` retires the ids it
    # names; then the weaker of any two OPEN proposals on one ticker that cannot both be followed
    # (buy vs trim/sell, trim vs sell) retires with its rotation partner legs. Runs after scoring
    # so priority_score exists for same-batch ties. See _retire_weaker_conflicts.
    _apply_declared_supersessions(props, today_date, retired)
    _retire_weaker_conflicts(props, today_date, retired, parse_datetime)

    # -- PAIRED-ROTATION RETIREMENT (added 2026-08-24) -- profit_rotation/cluster_rotation legs
    # must retire TOGETHER, never independently. This is the direct fix for "19 rotation pairs
    # attempted all-time, 0 survived": the old pairing scored and lifecycle-managed each leg on
    # its own typed trigger (stretch / signal_conviction), so a single-sided retirement silently
    # orphaned the other leg into an unpaired, half-explained proposal, which is indistinguishable
    # from noise and never got acted on. Both legs share a pair_id; if the pair is no longer in
    # this run's live trigger_pairs, retire whichever leg(s) are still open, together, one reason.
    _retire_orphaned_rotation_legs(props, trigger_pairs, today_date, retired)

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
        _apply_live_rejustification(pr, price_now_by_ticker, risk_by_ticker, directional_breach, today_date,
                                   rotation_by_ticker)

    # --- STACKING GUARD (added 2026-09-01) ---------------------------------------------------
    # An ACCEPTED-but-unexecuted proposal did not block a new proposal on the same name and the
    # same side. The dedup pass above keys on OPEN proposals, and acceptance moves a row to
    # `accepted_by_user` -- so accepting a trade REMOVED it from the duplicate check while
    # leaving the trade undone. The window in which double-counting is most likely was precisely
    # the window that was unguarded.
    #
    # Found live on 2026-08-31: P-164 Sell MSFT $437.92 accepted and awaiting execution, while
    # P-201 proposed a further Sell MSFT $305.96 -- $743.88 combined against a $1,019.88
    # position, 73% of the holding, across two rows neither of which referenced the other.
    #
    # This FLAGS, it does not auto-retire. Two of the three live stacks that day (WDC, AMAT)
    # were plausibly deliberate incremental adds funded by different rotations, and silently
    # killing a legitimate second leg would trade one failure mode for another. What was missing
    # was never the judgement -- it was that nothing put the combined number in front of anyone.
    # Sell-side stacks are escalated because they are the bounded side: you cannot sell more than
    # you hold, so a large combined percentage is a concrete, checkable error rather than merely
    # an oversized bet.
    stack_warnings = _compute_stacking_warnings(props, risk_by_ticker)

    proposals["proposals"] = props
    safe_write(p_path, proposals)

    open_now = [pr for pr in props if pr.get("status") == "open"]
    priority_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for pr in open_now:
        priority_counts[pr.get("priority", "LOW")] += 1

    emit({"proposals_count": len(props), "superseded_count": len(to_supersede), "changes_made": len(to_supersede),
          "auto_retired_count": len(retired), "auto_retired": retired,
          "open_count": len(open_now), "priority_counts": priority_counts, "written": True,
          "auto_voided_created_this_run": voided_today,
          "auto_voided_stale": voided_stale,
          "reconciliation_warnings": recon_warnings,
          "stacking_warnings": sorted(stack_warnings,
                                      key=lambda w: -(w.get("combined_pct_of_position") or 0))})

def idea_key(pr):
    """(ticker, direction bucket, trigger type, month) -- what makes two proposals the SAME idea.

    Added 2026-09-20. 88 scored rows were 43 distinct ideas (QCOM BUY x6, MU TRIM x5, DRAM TRIM
    x5): the same idea is re-proposed each run until it works, so counting rows both inflated n
    and biased the record negative. The month bucket means a restatement inside one calendar
    month is one idea while a fresh call a month later is an independent observation. Used for
    the aggregate denominator only; individual rows are still graded one by one."""
    direction = pr.get("direction_bucket") or _proposal_direction(pr.get("action"))
    return (pr.get("ticker"), direction, pr.get("trigger_type"),
            str(pr.get("date") or "")[:IDEA_MONTH_PREFIX_LEN])


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
        cmd_proposals: one idea counts once. (Enforced only from 2026-09-20; until then the
        code scored them and 88 rows were 43 ideas.) The scorecard reports n_rows AND n_ideas.
      * `--run-dir` lets the SMH benchmark price come from that run's market_inputs.json, so
        alpha grading does not depend on the caller remembering to fetch SMH.
      * `--rebase-scorecard` permits the record to shrink ONCE, when a definitional fix (not a
        missing-prices probe) legitimately lowers the count; see the guard below.
      * A HOLD with size_usd 0 still scores -- "do nothing" is a real call with a real outcome.
    """
    p_path = os.path.join(args.base_dir, "proposals.json")
    proposals = load_json(p_path, default={"proposals": [], "scorecard": {}})
    props = proposals.get("proposals", [])
    prices = load_json(args.prices_json, default={}) if args.prices_json else {}
    today = (resolve_today(args.today))
    run_dir = getattr(args, "run_dir", None)
    rebase = bool(getattr(args, "rebase_scorecard", False))
    mi = load_json(os.path.join(run_dir, "market_inputs.json"), default={}) if run_dir else {}
    bench_unpriced = set()   # benchmark tickers some row needed and nobody supplied

    # statuses that represent a real, closed recommendation worth grading
    # `superseded` is deliberately ABSENT (2026-09-20). This docstring always said superseded rows
    # are excluded so one idea counts once, but the set contained it: 58 of 88 scored rows were
    # superseded restatements, and 88 rows were only 43 distinct ideas.
    SCOREABLE = {"executed", "fulfilled", "filled", "auto_retired", "deferred", "watch"}
    EXCLUDED = {"dismissed_by_user"}
    # A DESK withdrawal is excluded from ACCURACY too -- the trade never happened, so there is
    # no outcome to grade -- but it is counted and reported separately rather than folded into
    # the user-override bucket. The rationale above ("the user overriding a proposal is not the
    # strategist being wrong") is true of a user dismissal and exactly BACKWARDS for a desk one:
    # the desk withdrawing its own faulty proposal IS a strategist miss, and burying it in the
    # same silent exclusion inflates measured accuracy by hiding the desk's own errors. Four
    # such withdrawals happened on 2026-08-31 alone.
    DESK_WITHDRAWN = {"dismissed_by_desk"}

    rows, unpriced, excluded_n, too_young = [], [], 0, 0
    desk_withdrawn = []
    for pr in props:
        st = pr.get("status")
        if st in DESK_WITHDRAWN:
            desk_withdrawn.append({"id": pr.get("id"), "action": pr.get("action"),
                                   "reason": (pr.get("dismiss_reason") or "")[:160]})
            continue
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

        # ALPHA VS BENCHMARK (added 2026-09-07). A TRIM that "missed" only because the whole
        # ~89% AI-capex-factor book (and SMH with it) sold off together is not a strategist
        # error, and a BUY that "worked" only because SMH ripped 8% that month is not
        # strategist skill -- grading on the raw move conflates market beta with the desk's
        # own judgment. Grade against SMH whenever a benchmark anchor exists on the proposal
        # (see cmd_add_proposal); fall back to the unchanged absolute-move grading, flagged in
        # `scored_vs` and counted in data_quality, for the pre-2026-09-07 backlog and any
        # proposal a caller wrote without one. HOLD is deliberately excluded from the
        # benchmark comparison -- its whole claim is "stayed still", which a relative-move
        # framework doesn't fit any better than it fits profit_ratchet's stop management.
        bench_ticker = pr.get("benchmark_ticker") or "SMH"
        b0 = pr.get("benchmark_price_at_proposal")
        # --prices-json wins; otherwise read SMH from the run's market_inputs.json, the same
        # source smith_validity.build_context uses. Before 2026-09-20 the benchmark was never
        # added to the "unpriced" list, so the sanctioned "probe with {} and it names what it
        # needs" workflow structurally guaranteed SMH was never fetched: SMH appeared in zero
        # score_prices.json files and alpha_scored_count sat at 0 of 88.
        bnow = prices.get(bench_ticker)
        if bnow is None and bench_ticker == "SMH":
            bnow = mi.get("smh")
        bench_move = None
        scored_vs = "absolute (no anchor)" if not b0 else "absolute (benchmark price not supplied)"
        if b0 and bnow:
            bench_move = (bnow - b0) / b0 * 100.0
            scored_vs = f"alpha vs {bench_ticker}"
        elif b0 and not bnow:
            bench_unpriced.add(bench_ticker)

        # direction-aware: the same move is a win or a loss depending on what was advised
        hold_unscoreable = False
        if direction == "BUY":
            signed = (move - bench_move) if bench_move is not None else move
        elif direction in ("TRIM", "SELL"):
            # a TRIM/SELL worked if the stock fell MORE than the benchmark -- avoiding a
            # drawdown worse than the market's own is the actual claim being graded
            signed = (bench_move - move) if bench_move is not None else -move
        else:  # HOLD -- "no action needed": worked unless it lagged the benchmark
            # 2026-09-20: the old |move| < 2% rule was near-unwinnable here (0 for 10). A HOLD
            # is vindicated if the name did not UNDERPERFORM its benchmark by more than
            # HOLD_UNDERPERFORM_PCT. With no benchmark price for the row it is unscoreable --
            # never graded on the absolute rule it was just retired for.
            if bench_move is None:
                hold_unscoreable = True
                signed = 0.0
                scored_vs = "unscoreable (HOLD needs a benchmark)"
            else:
                signed = move - bench_move
                scored_vs = f"alpha vs {bench_ticker} (HOLD)"
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
        # A benchmark anchor gets the same guard -- SMH itself does not move 60% in a quarter,
        # so an implausible bench_move means a corrupt benchmark_price_at_proposal, not a real
        # regime shift, and must not silently poison the alpha figure.
        if hold_unscoreable:
            verdict = "unscoreable"
        elif abs(move) > ANCHOR_REVIEW_PCT or (bench_move is not None and abs(bench_move) > ANCHOR_REVIEW_PCT):
            verdict = "needs_anchor_review"
        elif direction == "HOLD":
            verdict = "missed" if signed < -HOLD_UNDERPERFORM_PCT else "worked"
        else:
            verdict = ("worked" if signed > VERDICT_THRESHOLD_PCT
                       else "missed" if signed < -VERDICT_THRESHOLD_PCT else "neutral")
        row = {"id": pr.get("id"), "ticker": tk, "direction": direction, "status": st,
               "date": str(d0), "age_days": age, "price_at_proposal": round(p0, 4),
               "price_now": round(now, 4), "move_pct": round(move, 2),
               "benchmark_move_pct": round(bench_move, 2) if bench_move is not None else None,
               "scored_vs": scored_vs,
               "signed_benefit_pct": round(signed, 2), "verdict": verdict,
               "size_usd": pr.get("size_usd"),      # expectancy weights by capital asked for
               "idea": "|".join(str(x) for x in idea_key(pr)),
               "window": "90d" if age >= 90 else "30d"}
        rows.append(row)
        pr["outcome_pct"] = None if verdict in UNGRADED_VERDICTS else round(signed, 2)
        pr["outcome_verdict"] = verdict
        pr["outcome_window"] = row["window"]
        pr["outcome_scored_on"] = str(today)

    def agg(subset):
        n = len(subset)
        if not n:
            return None
        w = sum(1 for r in subset if r["verdict"] == "worked")
        m = sum(1 for r in subset if r["verdict"] == "missed")
        out = {"n": n, "n_rows": n, "n_ideas": len({r["idea"] for r in subset}),
               "worked": w, "missed": m, "neutral": n - w - m,
               "accuracy_pct": round(w / n * 100, 1),
               "avg_benefit_pct": round(sum(r["signed_benefit_pct"] for r in subset) / n, 2)}
        out.update(expectancy(subset))
        return out

    def expectancy(subset):
        """Expectancy per dollar proposed, net of the round-trip fee.

        WHY ACCURACY IS NOT ENOUGH (added 2026-09-19). Hit rate answers "how often", never "how
        much", and the two come apart precisely when it matters: a 27% accuracy is excellent if
        the 27% are large and the 73% are small, and ruinous the other way round. This desk's
        own stop record is the proof next door -- 57.1% of stops "won" while the set lost money,
        because the wins were small and the losses were not. So the headline the strategist reads
        should be the number that survives that asymmetry.

        Three things this adds that accuracy hides:
          * SIZE WEIGHTING. A $1,604 proposal and a $150 one counted equally before. `size_usd`
            weights each row by the capital it actually asked for, so the scorecard describes the
            book rather than the list.
          * THE FEE. INDmoney charges ~0.30% on a buy (measured across 7 confirmations,
            2026-09-06). A proposal whose edge is under a round trip is not an edge; every
            expectancy figure here is stated net of it.
          * DOLLARS. expectancy_usd_per_1k is what a thousand dollars routed through this
            signal would have returned -- the unit a sizing decision is actually made in.
        """
        if not subset:
            return {}
        sizes = [abs(float(r.get("size_usd") or 0)) for r in subset]
        benefits = [r["signed_benefit_pct"] for r in subset]
        gross = sum(benefits) / len(benefits)
        net = gross - ROUND_TRIP_FEE_PCT
        total_size = sum(sizes)
        out = {"expectancy_pct_net": round(net, 3),
               "expectancy_usd_per_1k": round(net * 10.0, 2),
               "round_trip_fee_pct": ROUND_TRIP_FEE_PCT,
               "positive_expectancy": net > 0}
        if total_size > 0:
            weighted = sum(b * s for b, s in zip(benefits, sizes)) / total_size
            out.update({"size_weighted_benefit_pct": round(weighted, 3),
                        "size_weighted_expectancy_pct_net": round(weighted - ROUND_TRIP_FEE_PCT, 3),
                        "capital_proposed_usd": round(total_size, 2),
                        "expectancy_usd_total": round((weighted - ROUND_TRIP_FEE_PCT) / 100
                                                      * total_size, 2),
                        "sized_rows": sum(1 for s in sizes if s > 0)})
        else:
            out["size_weighted_note"] = "no row in this subset carries size_usd"
        # payoff ratio feeds smith_conviction.track_record_multiplier's Kelly path directly
        wins = [b for b in benefits if b > VERDICT_THRESHOLD_PCT]
        losses = [-b for b in benefits if b < -VERDICT_THRESHOLD_PCT]
        if wins and losses:
            out["avg_win_pct"] = round(sum(wins) / len(wins), 2)
            out["avg_loss_pct"] = round(sum(losses) / len(losses), 2)
            out["payoff_ratio"] = round((sum(wins) / len(wins)) / (sum(losses) / len(losses)), 2)
        return out

    # quarantined rows are reported but never counted -- see the anchor guard above
    graded = [r for r in rows if r["verdict"] not in UNGRADED_VERDICTS]
    review = [r for r in rows if r["verdict"] == "needs_anchor_review"]
    hold_unscored = [r for r in rows if r["verdict"] == "unscoreable"]
    trims = [r for r in graded if r["direction"] in ("TRIM", "SELL")]
    buys = [r for r in graded if r["direction"] == "BUY"]
    holds = [r for r in graded if r["direction"] == "HOLD"]
    # HEADLINE excludes HOLD: it is a different kind of claim ("nothing needed doing") and its
    # rule was retired as broken; it is still reported under by_direction.
    headline = [r for r in graded if r["direction"] != "HOLD"]
    alpha_scored = [r for r in graded if r["scored_vs"].startswith("alpha vs")]
    scorecard = {
        "as_of": str(today),
        "trim_accuracy_30d": (agg(trims) or {}).get("accuracy_pct"),
        "add_accuracy_30d": (agg(buys) or {}).get("accuracy_pct"),
        "overall_accuracy_30d": (agg(headline) or {}).get("accuracy_pct"),
        "by_direction": {"TRIM/SELL": agg(trims), "BUY": agg(buys), "HOLD": agg(holds)},
        "overall": agg(headline),
        "scored_count": len(graded),
        "n_rows": len(graded),
        "n_ideas": len({r["idea"] for r in graded}),
        "unscoreable_hold": len(hold_unscored),
        "alpha_scored_count": len(alpha_scored),
        "quarantined_anchor_review": len(review),
        "excluded_dismissed_by_user": excluded_n,
        "withdrawn_by_desk": len(desk_withdrawn),
        "withdrawn_by_desk_detail": desk_withdrawn,
        "not_yet_30d": too_young,
        "note": ("Direction-aware: a TRIM 'worked' if the price FELL after it, a BUY if it ROSE, "
                 "a HOLD if it did not lag its benchmark. The %.1f%% threshold is shared with "
                 "the journal scorer so 'worked' means the same magnitude in both. BUY/TRIM/SELL "
                 "are graded on ALPHA VS SMH when the proposal carries a benchmark anchor -- "
                 "%d of %d graded rows this run -- not the stock's raw move, so a trim that "
                 "'missed' only because the whole factor sold off together isn't scored as a "
                 "strategist error. dismissed_by_user proposals are excluded -- a user override "
                 "is not a strategist error. n_rows counts graded proposals; n_ideas counts "
                 "distinct (ticker, direction, trigger, month) ideas, because a restated idea is "
                 "one idea, not several -- superseded restatements are not scored. HOLD is "
                 "graded on alpha (worked unless it lagged its benchmark by more than %.1f%%), "
                 "is unscoreable without a benchmark price, and is EXCLUDED from the headline "
                 "accuracy/expectancy (`overall`, `overall_accuracy_30d`); see by_direction.HOLD."
                 % (VERDICT_THRESHOLD_PCT, len(alpha_scored), len(graded), HOLD_UNDERPERFORM_PCT)),
    }
    # REFUSE TO SHRINK THE RECORD (added 2026-08-30, found live).
    #
    # SKILL.md's own sanctioned procedure is to probe this command with a prices file containing
    # `{}` so it NAMES the tickers it needs. Doing exactly that on 2026-08-30 overwrote a
    # scorecard of 19 graded proposals (31.6% accuracy) with `scored_count: 0, overall: null`.
    # Nothing was lost permanently -- the per-proposal `outcome_verdict` fields survived intact,
    # so the aggregate is reconstructible -- but the headline figure the strategist reads, and
    # the one the weekly report prints, silently went to zero.
    #
    # This is the IDENTICAL bug class cmd_stops was already hardened against: "cmd_stops REFUSES
    # to overwrite stops_analysis.json with fewer stops than it already holds ... before that
    # guard, this exact probe silently destroyed the 94-row efficacy record twice." The lesson
    # was learned once, for one subcommand, and never generalised to its sibling -- which is how
    # a documented, sanctioned procedure became a landmine.
    prior = (proposals.get("scorecard") or {}).get("scored_count")
    rebase_note = None
    if prior and len(graded) < prior:
        # REBASE (2026-09-20). Dropping `superseded` from SCOREABLE and retiring the absolute
        # HOLD rule legitimately lowers the count (88 -> ~43). The guard must not be weakened --
        # it exists to catch the empty-prices probe -- so `--rebase-scorecard` permits the shrink
        # only up to what those definitional fixes EXPLAIN: superseded rows that used to carry a
        # verdict, plus HOLD rows that are now unscoreable. Any larger drop is still the probe
        # landmine (rows lost to missing prices) and is refused even with the flag.
        explained = (sum(1 for pr in props if pr.get("status") == "superseded"
                         and pr.get("outcome_verdict") and pr.get("outcome_verdict") not in UNGRADED_VERDICTS)
                     + len(hold_unscored))
        if rebase and len(graded) >= prior - explained:
            rebase_note = {"from_scored_count": prior, "to_scored_count": len(graded),
                           "rebased_on": str(today),
                           "explained_by": {"superseded_no_longer_scored": explained - len(hold_unscored),
                                            "hold_now_unscoreable": len(hold_unscored)}}
        else:
            emit({"refused": True, "reason": (
                      f"scoring produced {len(graded)} graded rows against {prior} already on record "
                      f"-- refusing to shrink the scorecard. This is almost always the empty-prices "
                      f"probe: supply the tickers named in needs_prices and re-run."
                      + (f" --rebase-scorecard was given but only {explained} rows of the "
                         f"{prior - len(graded)}-row drop are explained by the definitional change "
                         f"(superseded no longer scored, HOLD unscoreable); the rest is missing "
                         f"prices." if rebase else "")),
                  "needs_prices": sorted(set(unpriced) | bench_unpriced),
                  "scorecard_preserved": proposals.get("scorecard", {}).get("as_of"),
                  "prior_scored_count": prior, "would_have_written": len(graded)})
            return
    elif (proposals.get("scorecard") or {}).get("rebase"):
        scorecard["rebase"] = proposals["scorecard"]["rebase"]   # the provenance outlives the run

    if rebase_note:
        scorecard["rebase"] = rebase_note
    proposals["scorecard"] = scorecard

    dq = []
    if rebase_note:
        dq.append(f"SCORECARD REBASED {rebase_note['from_scored_count']} -> "
                  f"{rebase_note['to_scored_count']} graded rows (one-time, --rebase-scorecard). "
                  f"The drop is a DEFINITIONAL correction, not lost data: "
                  f"{rebase_note['explained_by']['superseded_no_longer_scored']} superseded "
                  f"restatement(s) are no longer scored as separate rows (cmd_score's own "
                  f"docstring always said one idea counts once; the code contradicted it), and "
                  f"{rebase_note['explained_by']['hold_now_unscoreable']} HOLD row(s) with no "
                  f"benchmark anchor are now unscoreable instead of graded on the retired "
                  f"absolute rule. Accuracy/expectancy before and after are NOT comparable.")
    if bench_unpriced:
        dq.append(f"benchmark price not supplied for {', '.join(sorted(bench_unpriced))}: rows "
                  f"with a benchmark anchor fell back to absolute grading. Pass --run-dir (reads "
                  f"SMH from market_inputs.json) or add the ticker to --prices-json.")
    if unpriced:
        u = sorted(set(unpriced))
        dq.append(f"{len(u)} ticker(s) had no price supplied and stay unscored until a later run "
                  f"provides one (never guessed, never dropped): {', '.join(u[:12])}"
                  f"{'...' if len(u) > 12 else ''}")
    if too_young:
        dq.append(f"{too_young} proposal(s) are under 30 days old -- not yet in the scoring window.")
    # Two different causes that used to share one message, blaming the proposal for what is
    # usually a missing fetch: the ANCHOR is missing (a proposal property) vs the benchmark PRICE
    # is missing (a caller property).
    no_anchor = [r for r in graded if r["direction"] in ("BUY", "TRIM", "SELL")
                 and r["scored_vs"] == "absolute (no anchor)"]
    no_bench_price = [r for r in graded if r["direction"] in ("BUY", "TRIM", "SELL")
                      and r["scored_vs"] == "absolute (benchmark price not supplied)"]
    if no_anchor:
        dq.append(f"{len(no_anchor)} BUY/TRIM/SELL row(s) graded on absolute move, not alpha -- "
                  f"no benchmark_price_at_proposal on the proposal (pre-2026-09-07 history, or a "
                  f"caller that omitted it): "
                  + ", ".join(r["id"] for r in no_anchor[:12])
                  + ("..." if len(no_anchor) > 12 else "") + ".")
    if no_bench_price:
        dq.append(f"{len(no_bench_price)} BUY/TRIM/SELL row(s) carry a benchmark anchor but the "
                  f"benchmark's CURRENT price was not supplied, so they fell back to absolute "
                  f"grading (a fetch gap, not a proposal defect): "
                  + ", ".join(r["id"] for r in no_bench_price[:12])
                  + ("..." if len(no_bench_price) > 12 else "") + ".")
    if hold_unscored:
        dq.append(f"{len(hold_unscored)} HOLD row(s) unscoreable -- HOLD is graded on alpha and "
                  f"these have no benchmark anchor or no benchmark price: "
                  + ", ".join(r["id"] for r in hold_unscored[:12])
                  + ("..." if len(hold_unscored) > 12 else "") + ".")
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
        safe_write(p_path, proposals)
        # The Phase-4 readiness counter was written once (8) and never again while scored
        # proposals reached 59 -- the user's "build Phase 4 at 100" gate could never trip.
        try:
            import smith_learning
            smith_learning.update_phase4_readiness(args.base_dir)
        except Exception as e:  # noqa: BLE001 -- a counter must never fail scoring
            dq.append(f"phase4.readiness not updated: {type(e).__name__}: {e}")

    emit({"scored_count": len(rows), "needs_prices": sorted(set(unpriced) | bench_unpriced),
          "scorecard": scorecard, "rows": rows,
          "written": (not args.dry_run) and p_path or None, "data_quality": dq})

# ---------------------------------------------------------------------------
# Shadow-journal scorer -- serves BOTH trigger_journal.json and derisk_journal.json
# ---------------------------------------------------------------------------
# Added 2026-08-25, self-learning Phase 1. Neither file has ever had a scorer: both were
# producer-only since the day they were created (cmd_triggers/cmd_derisk write shadow_new with
# scored:false every run; nothing ever flips it to true). trigger_journal.json is explicitly
# the shadow->live promotion gate for laggard_rotation/profit_ratchet/scale_out_ladder
# (SHADOW_TRIGGERS) -- with 0 scored entries, no shadow trigger could EVER earn a live vote,
# no matter how long it ran. derisk_journal.json has the identical unscored-forever gap on the
# de-risk queue's own shadow-scoring log (see SKILL.md 2.9c). One scorer because both files
# share the same shape: a top-level entries[] list, each row carrying date/ticker/price_at_flag/
# scored, differing only in what OTHER fields ride along and what "direction" means for a row.

# What "up"/"down" means for a shadow-journal entry: laggard_rotation is a BUY call (expects the
# laggard to catch up, i.e. rise); scale_out_ladder is a TRIM call (expects the trim to have
# been the right move if the price falls afterward, same "TRIM worked if price fell" convention
# cmd_score already uses); profit_ratchet is a stop-management action, not a directional price
# bet, so it is deliberately left unscoreable here (None) rather than forced into a framework
# that doesn't fit it -- same "None means genuinely doesn't apply" contract as
# BUCKET_DIRECTION's EARNINGS PROXIMITY/POLICY IMPACT/INSIDER ACTIVITY entries.
TRIGGER_TYPE_DIRECTION = {"laggard_rotation": "up", "scale_out_ladder": "down",
                          "profit_ratchet": None}


def cmd_score_shadow_journal(args):
    """Score trigger_journal.json or derisk_journal.json entries at 7d/30d against
    price_at_flag, same direction-aware verdict logic and LOCK-ON-FIRST-SCORE discipline as
    cmd_journal (smith_math.py) -- reuses BUCKET_DIRECTION/VERDICT_THRESHOLD_PCT rather than
    re-deriving them, and never recomputes a verdict once it's been scored, so a shadow
    trigger's measured hit rate doesn't drift every time this command re-runs against a fresh
    price. --prices-json is required (same probe-with-{} idiom as score/stops): run once with
    {} to discover which tickers are needed."""
    fname = args.file  # "trigger_journal.json" | "derisk_journal.json"
    if fname not in ("trigger_journal.json", "derisk_journal.json"):
        fail(f"--file must be trigger_journal.json or derisk_journal.json, got {fname!r}")
    path = os.path.join(args.base_dir, fname)
    store = load_json(path, default={})
    if not store:
        fail(f"{fname} not found or empty at {path}")
    entries = store.get("entries", [])
    prices = load_json(args.prices_json, default={}) if args.prices_json else {}
    today = resolve_today(args.today)

    def direction_for(e):
        if fname == "trigger_journal.json":
            return TRIGGER_TYPE_DIRECTION.get(e.get("trigger_type"))
        return "down"  # derisk_journal: flagged as fragile/high-risk -> expects underperformance

    updated, needs_price = [], set()
    scored_count = 0
    for e in entries:
        if e.get("scored"):
            updated.append(e)  # already locked -- never re-touch
            continue
        try:
            flag_date = datetime.strptime(e["date"], "%Y-%m-%d").date()
        except (KeyError, ValueError, TypeError):
            updated.append(e)
            continue
        days_old = (today - flag_date).days
        if days_old < 7:
            updated.append(e)  # too young to score even at 7d
            continue
        price_now = prices.get(e.get("ticker"))
        if price_now is None or not e.get("price_at_flag"):
            needs_price.add(e.get("ticker"))
            updated.append(e)
            continue
        pct_move = round((price_now - e["price_at_flag"]) / e["price_at_flag"] * 100, 3)
        direction = direction_for(e)
        e = dict(e)
        e["price_now"] = price_now
        e["outcome_pct"] = pct_move
        e["scored_on"] = str(today)
        e["days_old"] = days_old
        if direction is None:
            e["verdict"] = "n/a"
        else:
            signed = pct_move if direction == "up" else -pct_move
            e["verdict"] = ("worked" if signed > VERDICT_THRESHOLD_PCT
                           else "failed" if signed < -VERDICT_THRESHOLD_PCT else "neutral")
        e["scored"] = True
        scored_count += 1
        updated.append(e)

    scored = [e for e in updated if e.get("verdict") in ("worked", "failed")]
    hit_rate = None
    if scored:
        hit_rate = {"n": len(scored),
                    "hit_rate_pct": round(sum(1 for e in scored if e["verdict"] == "worked")
                                          / len(scored) * 100, 1)}

    # per-trigger-type / per-file breakdown -- what a shadow->live promotion decision actually
    # needs: not one pooled number across laggard_rotation and scale_out_ladder, which measure
    # unrelated things.
    by_key = {}
    key_field = "trigger_type" if fname == "trigger_journal.json" else "queue_state"
    for e in scored:
        k = e.get(key_field, "unknown")
        by_key.setdefault(k, []).append(e["verdict"])
    hit_rate_by_key = {}
    for k, verdicts in by_key.items():
        hit_rate_by_key[k] = {"n": len(verdicts),
                              "hit_rate_pct": round(sum(1 for v in verdicts if v == "worked")
                                                    / len(verdicts) * 100, 1)}

    store["entries"] = updated
    store["hit_rate"] = hit_rate
    store["hit_rate_by_key"] = hit_rate_by_key
    store["last_scored"] = str(today)

    dq = []
    if needs_price:
        dq.append(f"{len(needs_price)} ticker(s) need a price to score: "
                  f"{', '.join(sorted(t for t in needs_price if t))}. Probe with an empty {{}} "
                  f"first to confirm this list, same idiom as score/stops.")

    if not args.dry_run:
        safe_write(path, store)

    emit({"file": fname, "newly_scored": scored_count, "hit_rate": hit_rate,
          "hit_rate_by_key": hit_rate_by_key, "written": not args.dry_run,
          "data_quality": dq})


# ROUND_TRIP_FEE_PCT (0.30) now lives in smith_core -- smith_ticket's materiality gate needs the same
# number and must not import this module -- and arrives here through `from smith_core import *`.

VOL_TIERS = (("low", 3.0), ("mid", 5.5), ("high", float("inf")))


def _vol_tier(atr_pct):
    """Volatility bucket from ATR20%. Boundaries at 3% and 5.5% split this book's 72 traded names
    into roughly thirds -- a mega-cap hyperscaler (AMZN ~2.2%) from a semicap name (AMAT ~3.9%)
    from a high-beta optics/power name (LITE ~6.7%, BE ~6.5%). A single stop multiple applied
    across that range is three different risk decisions wearing one number."""
    if atr_pct is None:
        return None
    for name, hi in VOL_TIERS:
        if atr_pct < hi:
            return name
    return "high"


STOP_HORIZON_SESSIONS = 30


def _move_at_horizon(perf_bars, ticker, date, fill_price, sessions=STOP_HORIZON_SESSIONS):
    """Price move from the fill to a FIXED horizon, not to "now".

    WHY THIS EXISTS (added 2026-09-19). Every verdict in this file compares the fill against the
    LATEST price, so the measured efficacy of the entire stop discipline re-rates whenever the
    market moves. The same 165 stops scored -$2,218 net with a 57.1% win rate on 2026-09-14 and
    +$5,571 net with a 43.6% win rate on 2026-09-18 -- four sessions and one relief rally apart,
    with no new stop in between. A metric that inverts its own conclusion on a week's tape cannot
    calibrate a policy. The horizon measure asks the stable question instead: 30 sessions after
    this stop fired, was the stock above or below the fill? Returns None while a stop is younger
    than the horizon, so recent stops abstain rather than contributing a half-formed answer.
    """
    rows = (perf_bars or {}).get(ticker)
    if not rows or not date or not fill_price:
        return None, None
    after = [r for r in rows if str(r.get("d"))[:10] > str(date)[:10]]
    if len(after) < sessions:
        return None, None
    px = after[sessions - 1].get("c")
    if not px:
        return None, None
    return round((float(px) - fill_price) / fill_price * 100, 2), after[sessions - 1]["d"]


def _atr_at_fill(perf_bars, ticker, date, n=20):
    """ATR20% computed from the bars ENDING at the fill date -- never later ones.

    Using today's ATR to tier a stop taken eight months ago would leak hindsight into the
    calibration: the ATR is exactly the quantity that moved when the position blew up.
    """
    rows = (perf_bars or {}).get(ticker)
    if not rows or not date:
        return None
    upto = [r for r in rows if str(r.get("d"))[:10] <= str(date)[:10]]
    if len(upto) < n + 1:
        return None
    return smith_marketdata.atr_pct(upto, n=n)


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
    today = resolve_today(args.today)
    # optional: absent perf_bars.json just leaves atr20_pct_at_fill null on every row, which the
    # calibration reports as "not tierable" rather than silently falling back to today's ATR.
    perf_bars = load_json(os.path.join(args.base_dir, "perf_bars.json"), default={}) or {}

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
        atr_at_fill = _atr_at_fill(perf_bars, ticker, t.get("date"))
        horizon_move, horizon_date = _move_at_horizon(perf_bars, ticker, t.get("date"), fill)
        scored.append({
            "ticker": ticker, "date": t.get("date"), "fill_time_utc": t.get("fill_time_utc"),
            "days_since": days_since, "fill_price": fill, "price_now": now,
            "move_pct": move_pct, "qty": qty_abs, "dollar_impact": dollar_impact,
            "verdict": verdict, "cohort": cohort.get(id(t), "unknown"),
            # ATR-AT-FILL (added 2026-09-19). Without it, cmd_learn_stop_calibration could only
            # ever compare the cascade/deliberate cohorts and had to refuse tier-level work
            # outright ("stops_analysis.json has no ATR-at-fill per row"). That refusal made the
            # single richest dataset on the desk -- 165 scored stops -- unable to answer the one
            # question it exists for: is `max(2*ATR%, 3.0%)` the right multiple, and is it the
            # right multiple for a 2%-ATR name AND a 7%-ATR name at once? Backfilled from the
            # same daily OHLC history the realized-return reconstruction uses, so the whole
            # series is available at once rather than only for stops taken from today onward.
            "atr20_pct_at_fill": atr_at_fill,
            "vol_tier": _vol_tier(atr_at_fill),
            "move_in_atr": (round(move_pct / atr_at_fill, 2)
                            if atr_at_fill else None),
            "move_30d_pct": horizon_move,
            "horizon_date": horizon_date,
            "verdict_30d": (None if horizon_move is None else
                            ("hurt" if horizon_move > 1.0 else
                             ("saved" if horizon_move < -1.0 else "flat"))),
            "move_30d_in_atr": (round(horizon_move / atr_at_fill, 2)
                                if (horizon_move is not None and atr_at_fill) else None),
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

    def summarize_30d(rows):
        rows = [r for r in rows if r.get("verdict_30d")]
        if not rows:
            return None
        n = len(rows)
        saved = sum(1 for r in rows if r["verdict_30d"] == "saved")
        hurt = sum(1 for r in rows if r["verdict_30d"] == "hurt")
        moves = [r["move_30d_pct"] for r in rows]
        in_atr = [r["move_30d_in_atr"] for r in rows if r.get("move_30d_in_atr") is not None]
        return {"count": n, "avg_move_pct": round(sum(moves) / n, 2),
                "median_move_pct": round(sorted(moves)[n // 2], 2),
                "saved": saved, "hurt": hurt, "flat": n - saved - hurt,
                "win_rate_pct": round(saved / (saved + hurt) * 100, 1) if (saved + hurt) else None,
                "avg_move_in_atr": (round(sum(in_atr) / len(in_atr), 2) if in_atr else None)}

    # the STABLE basis: fixed 30-session horizon, immune to where the tape happens to be today
    overall_30d = summarize_30d(scored)
    by_tier_30d = {t: summarize_30d([r for r in scored if r.get("vol_tier") == t])
                   for t in ("low", "mid", "high")}
    by_tier_30d = {k: v for k, v in by_tier_30d.items() if v}
    by_tier_now = {t: summarize([r for r in scored if r.get("vol_tier") == t])
                   for t in ("low", "mid", "high")}
    by_tier_now = {k: v for k, v in by_tier_now.items() if v}

    # -- RE-ENTRY ROUND-TRIP TRACKING (added 2026-09-06, user request) --------------------
    # cmd_stops above answers "did the stop help or hurt" by comparing the STOP FILL to the
    # CURRENT price -- that is the wrong comparison for this user's actual strategy, which is
    # trim/exit on a support breach and RE-ENTER once price stabilizes. The stop firing and the
    # stock going on to fall further is a WIN for that strategy even if this user never buys
    # back in at the bottom; the number that actually measures the strategy is where the
    # re-entry landed relative to the stop, not where the stock sits today relative to the stop.
    # For every scored stop, find the next BUY on the same ticker (chronologically, trades.json
    # order) and treat it as the re-entry. Each buy trade object is claimed by at most one stop
    # (first stop, first claim) so one re-entry can't be double-counted against two exits.
    all_trades_sorted = sorted(
        trades.get("trades", []),
        key=lambda t: (t.get("date") or "", t.get("fill_time_utc") or ""))
    by_ticker_seq = {}
    for t in all_trades_sorted:
        by_ticker_seq.setdefault(t.get("ticker"), []).append(t)

    claimed_buy_ids = set()
    reentries = []
    for t in candidates:
        ticker = t.get("ticker")
        seq = by_ticker_seq.get(ticker, [])
        try:
            idx = seq.index(t)
        except ValueError:
            idx = None
        reentry_trade = None
        if idx is not None:
            for cand in seq[idx + 1:]:
                if (cand.get("action") == "buy" and (cand.get("qty_change") or 0) > 0
                        and id(cand) not in claimed_buy_ids):
                    reentry_trade = cand
                    claimed_buy_ids.add(id(cand))
                    break

        stop_price = t.get("price_at_trade")
        row = {"ticker": ticker, "stop_date": t.get("date"), "stop_price": stop_price}
        if reentry_trade is None:
            row["status"] = "still_out"
            now = prices.get(ticker)
            if now is not None and stop_price:
                # positive = price ran away above the stop without a re-entry (missed the move);
                # negative = price is still below the stop (nothing missed yet, still watching).
                row["gap_vs_stop_pct"] = round((now - stop_price) / stop_price * 100, 2)
            reentries.append(row)
            continue

        reentry_price = reentry_trade.get("price_at_trade")
        try:
            stop_dt = datetime.strptime(t.get("date", ""), "%Y-%m-%d").date()
            reentry_dt = datetime.strptime(reentry_trade.get("date", ""), "%Y-%m-%d").date()
            days_to_reentry = (reentry_dt - stop_dt).days
        except ValueError:
            days_to_reentry = None
        reentry_qty = abs(reentry_trade.get("qty_change") or 0)
        row.update({"status": "reentered", "reentry_date": reentry_trade.get("date"),
                     "reentry_price": reentry_price, "days_to_reentry": days_to_reentry,
                     "reentry_price_source": reentry_trade.get("price_source"),
                     "reentry_qty": reentry_qty})
        if reentry_price and stop_price:
            # negative = re-entered BELOW the stop price -- the strategy worked as designed,
            # sold high(er) and bought back cheaper. Positive = re-entered ABOVE the stop --
            # the stabilization was mistaken for a low and some of the stop's edge was given
            # back chasing the re-entry.
            reentry_move_pct = round((reentry_price - stop_price) / stop_price * 100, 2)
            row["reentry_move_pct"] = reentry_move_pct
            row["reentry_verdict"] = ("reentered_lower" if reentry_move_pct < -1.0
                                       else ("reentered_higher" if reentry_move_pct > 1.0
                                             else "reentered_flat"))
            # $ cost/benefit of the round trip specifically -- (stop - reentry) * qty bought
            # back. Positive = bought back cheaper than sold (the strategy earned real dollars,
            # not just "avoided a worse price"); negative = gave back edge chasing the re-entry.
            row["reentry_dollar_impact"] = round((stop_price - reentry_price) * reentry_qty, 2)
        now = prices.get(ticker)
        if now is not None and reentry_price:
            row["since_reentry_pct"] = round((now - reentry_price) / reentry_price * 100, 2)
        reentries.append(row)

    reentered_rows = [r for r in reentries if r["status"] == "reentered" and "reentry_move_pct" in r]
    reentry_summary = None
    if reentered_rows:
        n = len(reentered_rows)
        lower = sum(1 for r in reentered_rows if r["reentry_verdict"] == "reentered_lower")
        higher = sum(1 for r in reentered_rows if r["reentry_verdict"] == "reentered_higher")
        flat = n - lower - higher
        avg_reentry_move = round(sum(r["reentry_move_pct"] for r in reentered_rows) / n, 2)
        reentry_summary = {
            "count": n, "reentered_lower": lower, "reentered_higher": higher, "reentered_flat": flat,
            "reentered_lower_pct": round(lower / n * 100, 1),
            "avg_reentry_move_vs_stop_pct": avg_reentry_move,
            "still_out_count": sum(1 for r in reentries if r["status"] == "still_out"),
        }

    # -- BY-TICKER ROLL-UP (added 2026-09-06, user request) ------------------------------
    # A name that's been stopped out and re-entered several times (DRAM: 3 stops; several
    # book names carry 2+) reads as several separate rows above -- the trade-level table this
    # command already produced. That's the wrong grain for judging the STRATEGY on a given
    # name: the question is "what has trimming X on stops and buying it back on stabilization
    # cost or earned me, all-in", not "how did trade #3 on X do". This rolls every stop AND its
    # matched re-entry (if any) up to one row per ticker: total stop-side dollar impact +
    # total re-entry-side dollar impact = one combined net figure per name, plus how many
    # stops on that name are still out (no re-entry yet).
    by_ticker_stops = {}
    for r in scored:
        agg = by_ticker_stops.setdefault(r["ticker"], {"stop_count": 0, "stop_dollar_impact": 0.0})
        agg["stop_count"] += 1
        agg["stop_dollar_impact"] += r["dollar_impact"]
    by_ticker_reentry = {}
    for r in reentries:
        agg = by_ticker_reentry.setdefault(
            r["ticker"], {"reentry_count": 0, "reentry_dollar_impact": 0.0, "still_out_count": 0})
        if r["status"] == "reentered" and "reentry_dollar_impact" in r:
            agg["reentry_count"] += 1
            agg["reentry_dollar_impact"] += r["reentry_dollar_impact"]
        elif r["status"] == "still_out":
            agg["still_out_count"] += 1

    by_ticker = []
    for ticker in sorted(set(by_ticker_stops) | set(by_ticker_reentry)):
        s = by_ticker_stops.get(ticker, {"stop_count": 0, "stop_dollar_impact": 0.0})
        re_ = by_ticker_reentry.get(ticker, {"reentry_count": 0, "reentry_dollar_impact": 0.0, "still_out_count": 0})
        combined = round(s["stop_dollar_impact"] + re_["reentry_dollar_impact"], 2)
        by_ticker.append({
            "ticker": ticker, "stop_count": s["stop_count"],
            "stop_dollar_impact": round(s["stop_dollar_impact"], 2),
            "reentry_count": re_["reentry_count"],
            "reentry_dollar_impact": round(re_["reentry_dollar_impact"], 2),
            "still_out_count": re_["still_out_count"],
            "combined_net_dollar_impact": combined,
        })
    by_ticker.sort(key=lambda r: -abs(r["combined_net_dollar_impact"]))

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
        "overall_30d": overall_30d, "by_vol_tier_30d": by_tier_30d, "by_vol_tier_now": by_tier_now,
        "horizon_sessions": STOP_HORIZON_SESSIONS,
        "basis_note": ("`overall`/`by_cohort` compare the fill to the LATEST price and therefore "
                       "re-rate with the market -- these same 165 stops read -$2,218 / 57.1% win "
                       "on 2026-09-14 and +$5,571 / 43.6% on 2026-09-18. Calibrate on the _30d "
                       "blocks, which fix the horizon at "
                       f"{STOP_HORIZON_SESSIONS} sessions after each fill."),
        "stops": scored, "data_quality": dq,
        "reentries": reentries, "reentry_summary": reentry_summary, "by_ticker": by_ticker,
    }
    out_path = args.out or os.path.join(args.base_dir, "stops_analysis.json")

    # REGRESSION GUARD (added 2026-08-16). This file is the ONLY record of stop-loss efficacy and
    # is not run-dir scoped, so an overwrite is unrecoverable outside git. The documented way to
    # discover which tickers need prices is to run with an empty price map first -- which scores
    # ZERO stops and, before this guard, wrote that empty result straight over 94 real ones. That
    # destroyed the file twice (2026-08-15 and again 2026-08-16), both times recovered only via
    # `git checkout`. The probe idiom is correct; silently persisting its result was not.
    # So: refuse to shrink the file. A run that scores fewer stops than the version on disk is
    # reporting a degraded input, not a new truth -- emit the analysis, skip the write, say why.
    prior = load_json(out_path, default=None)
    prior_n = len(prior.get("stops") or []) if isinstance(prior, dict) else 0
    if prior_n and len(scored) < prior_n and not getattr(args, "force", False):
        emit({"written": None, "scored_count": len(scored), "overall": overall,
              "by_cohort": by_cohort, "data_quality": dq,
              "write_skipped": (
                  f"REFUSED to overwrite {out_path}: this run scored {len(scored)} stop(s) but the "
                  f"existing file holds {prior_n}. Shrinking it would destroy the standing efficacy "
                  f"record. This is the expected outcome when probing with an empty/partial "
                  f"--prices-json to discover which tickers are needed: read the data_quality list "
                  f"for those tickers, supply their prices, and re-run. Pass --force only if you "
                  f"genuinely intend to replace the record with a smaller one.")})
        return

    safe_write(out_path, out)
    emit({"written": out_path, "scored_count": len(scored), "overall": overall, "by_cohort": by_cohort,
          "reentry_summary": reentry_summary})

def dismiss_proposal_core(props, proposal_id, reason, actor="user"):
    """The actual dismiss mutation, extracted (2026-08-25, interactive dashboard feature) so
    cmd_dismiss (a chat-driven 'dismiss P-014') and sync-decisions' Reject button (a
    dashboard-driven click) share exactly one implementation of 'what dismissing means' rather
    than maintaining two. Mutates `props` in place; returns the matched proposal dict, or None
    if `proposal_id` doesn't exist or isn't open. Caller owns loading/writing proposals.json."""
    for pr in props:
        if pr.get("id") == proposal_id:
            if pr.get("status") not in ("open",):
                return None
            # WHO dismissed this is now STRUCTURAL, not prose. `actor` has existed since this
            # function was extracted, but it only ever reached the free-text `note` -- the
            # status was hardcoded `dismissed_by_user` whoever called. This file's own rule is
            # "never parse prose" (see cmd_dismiss), and the actor was prose, so nothing could
            # read it. Consequence found 2026-08-31: four proposals the ORCHESTRATOR withdrew
            # for its own faulty evidence (P-152, P-174, P-179, P-182) sat on record as the
            # USER rejecting those ideas -- feeding smith_learning's revealed-preference
            # profiles a preference the user never expressed, and hiding four strategist
            # misses inside the scorecard's user-override exclusion.
            pr["status"] = "dismissed_by_desk" if str(actor).startswith("desk") else "dismissed_by_user"
            pr["dismissed_by"] = actor
            stamp = f" | dismissed by {actor} {datetime.now(IST).isoformat(timespec='minutes')}"
            pr["dismiss_reason"] = reason or None
            if reason:
                stamp += f": {reason}"
            pr["note"] = (pr.get("note", "") + stamp).strip(" |")
            return pr
    return None


def cmd_dismiss(args):
    """Mark one proposal dismissed_by_user by its stable id (see cmd_proposals). This is the
    write path behind a chat request like "dismiss P-014" -- the user's way of saying "don't
    keep proposing this" without the strategist re-adding it next run, since dismissed_by_user
    is a terminal status the dedup pass never reopens or merges into.
    """
    p_path = os.path.join(args.base_dir, "proposals.json")
    proposals = load_json(p_path, default={"proposals": [], "scorecard": {}})
    props = proposals.get("proposals", [])
    pr = dismiss_proposal_core(props, args.id, args.reason,
                               actor=getattr(args, "by", "user"))
    if pr is None:
        # distinguish "no such id" from "exists but not open" for a clearer error
        match = next((p for p in props if p.get("id") == args.id), None)
        if match is not None:
            fail(f"proposal {args.id} is status={match.get('status')!r}, not open -- nothing to dismiss")
        fail(f"no proposal with id {args.id}")
    proposals["proposals"] = props
    safe_write(p_path, proposals)
    # `dismiss_reason` is stored as its OWN structured field (added 2026-08-25), not only
    # folded into the free-text `note` -- a dismissal is the single most informative NEGATIVE
    # label revealed-preference learning has (see smith_learning.py), and "never parse prose"
    # (burned twice already -- the 2026-07-29 breach-cleared voider and a near-miss this
    # session parsing rationale text for a reentry date) means a learner must be able to read
    # the reason as a typed field, not regex it back out of `note`. Every one of the 9
    # dismissals on record before this change has no reason at all (`dismiss` always accepted
    # --reason and the orchestrator never asked) -- flagged in the emitted result rather than
    # silently accepted, so the interactive caller has a cue to ask next time.
    result = {"dismissed": args.id, "action": pr.get("action"),
              "status": pr.get("status"), "by": pr.get("dismissed_by"), "written": True}
    if not args.reason:
        result["data_quality"] = [f"{args.id} dismissed with no reason -- the most "
                                   "informative negative label for revealed-preference "
                                   "learning is missing; ask for one next time"]
    emit(result)


_BARE_DIRECTION_WORDS = {"BUY", "SELL", "TRIM", "HOLD", "ADD", "EXIT", "REDUCE", "REBUILD"}


def _size_support_anchored(spec, base_dir):
    """Size a rebound entry off its real stop, and stamp what bound it.

    Returns {"fields": {...}, "rejected": None|reason}. Never silently substitutes a number:
    if the exception does not apply, the caller's own size_usd stands and the reason is
    recorded on the proposal, because a size that quietly changed basis is worse than one
    that is merely wrong.
    """
    policy = load_json(os.path.join(base_dir, "policy.json"), default={})
    state = load_json(os.path.join(base_dir, "state.json"), default={})
    atr = ((state.get("data_cache", {}) or {}).get("atr20", {}) or {}).get("values_pct", {}) or {}
    ticker, price = spec.get("ticker"), spec.get("price_at_proposal")
    rd = state.get("last_run_dir")
    risk_file = os.path.join(base_dir, rd, "compute_risk.json") if rd else None
    risk = load_json(risk_file, default={}) if risk_file and os.path.exists(risk_file) else {}
    total_book = risk.get("total_book_usd") or (state.get("us", {}) or {}).get("total_book_usd")

    if spec.get("support_usd") is None:
        return {"fields": {"sizing_basis": "standard",
                           "support_anchored_refused": "no support_usd on the spec -- smith-rebound "
                                                       "computes support levels (rule G); a rebound "
                                                       "entry without one is sized by the standard "
                                                       "2xATR rule and is not eligible for the "
                                                       "exception"}, "rejected": None}
    res = smith_risk.support_anchored_cap(atr.get(ticker), price, spec.get("support_usd"),
                                          total_book, policy)
    if "refused" in res:
        return {"fields": {"sizing_basis": "standard",
                           "support_anchored_refused": res["refused"]}, "rejected": None}

    size = spec.get("size_usd")
    fields = {
        "sizing_basis": "support_anchored",
        "support_usd": res["support_usd"],
        "stop_price_usd": res["stop_price_usd"],
        "stop_distance_pct": res["stop_distance_pct"],
        "stop_bound_by": res["bound_by"],
        "max_position_usd": res["max_position_usd"],
        "standard_max_position_usd": res["standard_max_position_usd"],
        "uplift_x": res["uplift_x"],
        "risk_at_cap_usd": res["risk_at_cap_usd"],
    }
    # The exception raises the CAP; it never raises a size the caller did not ask for.
    if size is not None and size > res["max_position_usd"]:
        fields["size_usd"] = res["max_position_usd"]
        fields["clamped_by"] = "support_anchored_cap"
        fields["size_requested_usd"] = size

    # THE AGGREGATE CAP STILL BINDS, and on 2026-08-30 it is breached. A rebound entry that
    # adds risk to an overdrawn budget must say so on its face -- this is the difference
    # between "buy the bounce" and "buy the bounce with money you have already spent".
    if risk.get("aggregate_over_cap"):
        over = (risk.get("aggregate_open_risk_usd", 0)
                - risk.get("aggregate_open_risk_cap_pct", 10) / 100 * (total_book or 0))
        added = (fields.get("size_usd") or size or 0) * res["stop_distance_pct"] / 100
        fields.setdefault("review_flags", []).append(
            f"FUNDING REQUIRED: aggregate open risk is already ${over:,.0f} over its "
            f"{risk.get('aggregate_open_risk_cap_pct')}% cap "
            f"({risk.get('aggregate_open_risk_pct')}%), and this entry adds ${added:,.0f} more. "
            f"Free at least ${over + added:,.0f} of risk elsewhere first -- this is the buy leg "
            f"of a rotation, not a standalone add.")
    return {"fields": fields, "rejected": None}


PRICE_ANCHOR_TOLERANCE_PCT = 3.0   # same threshold as the G3 staleness gate


def _run_reference_prices(run_dir):
    """Per-ticker reference prices for this run, best source first, plus the SMH anchor."""
    refs = {}

    def put(t, px, src):
        if t and isinstance(px, (int, float)) and px > 0:
            refs.setdefault(str(t).upper(), (float(px), src))

    for t, v in (load_json(os.path.join(run_dir, "live_quotes.json"), default={}) or {}).items():
        put(t, v.get("price") if isinstance(v, dict) else v, "live_quotes")
    hold = load_json(os.path.join(run_dir, "holdings.json"), default={}) or {}
    for r in hold.get("holdings_inr") or []:
        put(r.get("ticker"), r.get("live_price_usd") or r.get("price_usd"), "holdings")
    bars = load_json(os.path.join(run_dir, "bars.json"), default={}) or {}
    for t, rows in bars.items():
        if isinstance(rows, list) and rows and isinstance(rows[-1], dict):
            put(t, rows[-1].get("c"), "bars_last_close")
    mi = load_json(os.path.join(run_dir, "market_inputs.json"), default={}) or {}
    live = (mi.get("smh_live") or {}).get("price") if isinstance(mi.get("smh_live"), dict) else None
    bench = ((float(live), "smh_live") if isinstance(live, (int, float)) and live > 0 else
             (float(mi["smh"]), "market_inputs_prior_close") if isinstance(mi.get("smh"), (int, float)) else None)
    return refs, bench


def _check_anchor(pr, field, ref, ticker, checks):
    """Replace a missing or >tolerance-off anchor with the run's reference; record either way."""
    px, src = ref
    supplied = pr.get(field)
    dev = (round(abs(supplied / px - 1) * 100, 2)
           if isinstance(supplied, (int, float)) and supplied > 0 else None)
    corrected = dev is None or dev > PRICE_ANCHOR_TOLERANCE_PCT
    rec = {"supplied": supplied, "reference": round(px, 4), "source": src,
           "deviation_pct": dev, "corrected": corrected}
    if corrected:
        pr[field] = round(px, 4)
        checks.append({"ticker": ticker, "field": field, **rec})
    return rec


# ---------------------------------------------------------------------------
# add-proposal field contract (added 2026-09-20, proposal-engine rebuild Phase 1)
#
# cmd_add_proposal used to build the row from a fixed dict and silently DROP every other field
# on the spec. Measured against proposals.json on 2026-09-20: `stop_price_usd` survived on 9 of
# 323 rows, `evidence_quality` was last persisted 2026-08-25, `trigger_bucket` 2026-08-25,
# `exited_on` 2026-08-24, `clamped_by`/`size_wanted_usd` 2026-08-26 -- while the strategist
# was supplying stop_price_usd and evidence_quality on every leg of its 2026-09-20 specs. The
# consequence was worse than missing data: the G58 evidence gate (cmd_proposals), the
# signal_conviction retirement and the reentry 20-day expiry all read those fields and had
# become unreachable code, so three safety branches were dead without any test noticing.
#
# The fix is an explicit contract, not a blind `pr.update(spec)` (which would let a caller
# overwrite `status` or `outcome_verdict`): PASSTHROUGH fields are copied after validation,
# RESERVED fields belong to the lifecycle and reject the whole batch, and anything else is kept
# under `spec_extras` rather than lost.
# ---------------------------------------------------------------------------
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_EVIDENCE_COUNT_KEYS = ("verified", "computed", "unverified")


def _is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _v_positive(v):
    return _is_num(v) and v > 0


def _v_non_negative(v):
    return _is_num(v) and v >= 0


def _v_pct_open(v):
    """A percentage strictly between 0 and 100 (a stop distance of 0 or 100+ is not a stop)."""
    return _is_num(v) and 0 < v < 100


def _v_probability(v):
    return _is_num(v) and 0 <= v <= 1


def _v_positive_int(v):
    return isinstance(v, int) and not isinstance(v, bool) and v > 0


def _v_iso_date(v):
    if not (isinstance(v, str) and _ISO_DATE_RE.match(v)):
        return False
    try:
        date.fromisoformat(v)
    except ValueError:
        return False
    return True


def _v_nonempty_str(v):
    return isinstance(v, str) and bool(v.strip())


def _v_evidence_quality(v):
    """The typed claim counts the G58 gate reads -- a dict of non-negative ints, never prose."""
    return (isinstance(v, dict) and set(v) <= set(_EVIDENCE_COUNT_KEYS) and bool(v)
            and all(isinstance(n, int) and not isinstance(n, bool) and n >= 0 for n in v.values()))


def _v_gate(v):
    return _v_nonempty_str(v) or isinstance(v, dict)


# field -> validator. None is never validated: a spec that says `"stop_price_usd": null`
# (every drafted SELL leg does) means "not supplied" and is simply not written.
PASSTHROUGH = {
    "stop_price_usd": _v_positive,
    "stop_distance_pct": _v_pct_open,
    "target_price_usd": _v_positive,
    "size_wanted_usd": _v_non_negative,
    "clamped_by": _v_nonempty_str,
    "risk_usd": _v_non_negative,
    "r_multiple": _is_num,
    "ev_r": _is_num,
    "p_win": _v_probability,
    "horizon_days": _v_positive_int,
    "expires_on": _v_iso_date,
    "invalidation": _v_nonempty_str,
    "evidence_quality": _v_evidence_quality,
    "trigger_bucket": _v_nonempty_str,
    "exited_on": _v_iso_date,
    "conviction_score": _is_num,
    "gate": _v_gate,
}

# Fields the lifecycle owns. A spec naming one is rejected, not ignored: a caller that thinks it
# can set `status` or `outcome_verdict` has a wrong model of the system, and the whole batch
# aborts (the same blast radius as every other spec rejection here).
RESERVED = frozenset({
    "id", "status", "date", "created_utc", "outcome_pct", "outcome_verdict", "outcome_window",
    "outcome_scored_on", "priority", "priority_score", "history", "repeat_count",
    "superseded_by", "retired_on", "retired_reason", "dismissed_by",
})

# Spec keys this command already consumes explicitly (built into the row above, or read by
# support-anchored sizing). Everything not here, not PASSTHROUGH and not RESERVED is unknown.
_SPEC_CONSUMED = frozenset({
    "direction", "ticker", "size_usd", "price_at_proposal", "rationale", "trigger_type",
    "pair_id", "pair_role", "cluster", "action", "benchmark_price_at_proposal",
    "benchmark_ticker", "supersedes", "support_usd",
})


def _apply_spec_passthrough(pr, spec):
    """Copy validated PASSTHROUGH fields onto `pr`, stash unknown ones in `spec_extras`.

    Returns (rejection_reason_or_None, unknown_field_names). Never mutates `pr` when it returns
    a rejection, and never lets a RESERVED field through."""
    reserved = sorted(k for k in spec if k in RESERVED)
    if reserved:
        return (f"spec sets lifecycle-owned field(s) {reserved} -- these are assigned by the "
                "lifecycle and may not be supplied"), []
    bad = sorted(k for k, v in spec.items()
                 if k in PASSTHROUGH and v is not None and not PASSTHROUGH[k](v))
    if bad:
        return "spec has invalid value(s) for " + ", ".join(f"{k}={spec[k]!r}" for k in bad), []
    for k in PASSTHROUGH:
        if spec.get(k) is not None:
            pr[k] = spec[k]
    unknown = sorted(k for k in spec if k not in PASSTHROUGH and k not in _SPEC_CONSUMED)
    extras = {k: spec[k] for k in unknown if spec[k] is not None}
    if extras:
        pr["spec_extras"] = extras
    return None, sorted(extras)


def cmd_add_proposal(args):
    """The ONLY sanctioned way to append new proposals to proposals.json (added 2026-08-29,
    same-day incident). Before this command existed, a new batch of proposals was appended by
    hand-writing a JSON dict per proposal -- and on 2026-08-29 that hand-written batch set
    `action` to a bare direction word ("SELL") instead of a verb+ticker sentence ("Sell ASML"),
    which the dashboard renders verbatim as the row's label. Internally harmless (ticker/
    direction_bucket are separate fields the lifecycle logic actually keys off), but the
    dashboard showed "SELL SELL" / "BUY BUY" / "TRIM TRIM" -- the user caught it, not the
    system, because nothing enforced the label's shape at the point of writing.

    This command builds `action` FROM `ticker` + `direction`, so the bug class can't recur by
    construction (there is no code path where a caller supplies `action` directly), and it
    refuses to write if any resulting proposal would still fail the same shape check
    `smith_memory.validate_proposals_schema` runs at the validation boundary -- belt and
    braces, since a future caller could still pass a malformed spec.

    Input: --proposals-json points to a JSON array of specs, one per proposal:
      {"direction": "BUY"|"SELL"|"TRIM"|"HOLD", "ticker": "ASML" (required unless direction is
       HOLD and "action" is given explicitly for a portfolio-level hold), "size_usd": 520.97,
       "price_at_proposal": 1559.08 (or null), "rationale": "...", "trigger_type": "..." or
       null, "pair_id": "..." or null, "pair_role": "sell"|"buy" or null, "cluster": "..." or
       null, "action": "..." (only for a ticker-less HOLD, e.g. "Rebuild cash buffer"),
       "benchmark_price_at_proposal": 567.01 (or null -- holdings.json's benchmarks.smh,
       already fetched every run; pass it for BUY/TRIM/SELL so cmd_score can grade alpha vs
       SMH instead of the stock's raw move), "benchmark_ticker": "SMH" (optional, defaults to
       SMH if benchmark_price_at_proposal is given), "supersedes": ["P-263"] (optional -- open ids
       this spec replaces; cmd_proposals retires them, see _apply_declared_supersessions)}
    Typed passthrough (2026-09-20): the PASSTHROUGH fields (stop_price_usd, evidence_quality,
    trigger_bucket, exited_on, ...) are validated and persisted; a spec naming a RESERVED
    lifecycle field (id, status, outcome_*, ...) or carrying a mistyped passthrough value is
    rejected and nothing is written; any other unknown field is kept under `spec_extras` with a
    data_quality line. See the block above PASSTHROUGH for the incident.

    Does NOT assign `id` -- that stays cmd_proposals' job (it already assigns ids to any
    freshly-appended proposal missing one, "once, never reused"), so ids stay allocated from
    one place. Run `smith_math.py proposals` next to dedup/retire/prioritize as usual.
    """
    verb_word = {"BUY": "Buy", "SELL": "Sell", "TRIM": "Trim", "HOLD": "Hold"}
    specs = load_json(args.proposals_json, default=None)
    if specs is None or not isinstance(specs, list):
        fail(f"--proposals-json must point to a JSON array of proposal specs, got: {args.proposals_json}")

    p_path = os.path.join(args.base_dir, "proposals.json")
    proposals = load_json(p_path, default={"proposals": [], "scorecard": {}})
    props = proposals.get("proposals", [])

    today = resolve_today(args.today).isoformat()
    # The IST calendar date used to be written as `<date>T00:00:00Z` -- a fake UTC midnight that
    # parsed as 05:30 IST. Now: the real IST instant when writing for today, a bare date when
    # backfilling another day, and the exact UTC write time in `created_utc` either way.
    _now = now_utc()
    ts = (_now.astimezone(IST).isoformat(timespec="seconds")
          if resolve_today(args.today) == desk_today(_now) else today)
    created_utc = iso_utc(_now)
    # PRICE CHECK (2026-09-14): the strategist wrote MU at 185.04 against a live 924.86. A price
    # anchor is script data, so the script checks it against this run's own quotes.
    run_dir = getattr(args, "run_dir", None)
    refs, bench_ref = _run_reference_prices(run_dir) if run_dir else ({}, None)
    price_checks, unchecked = [], []
    unknown_seen = {}

    built = []
    rejected = []
    for i, spec in enumerate(specs):
        direction = (spec.get("direction") or "").upper()
        ticker = spec.get("ticker")
        if direction not in ("BUY", "SELL", "TRIM", "HOLD"):
            rejected.append({"index": i, "reason": f"direction must be BUY/SELL/TRIM/HOLD, got {spec.get('direction')!r}"})
            continue
        if ticker:
            action = f"{verb_word[direction]} {ticker}"
        elif direction == "HOLD" and spec.get("action"):
            # the one sanctioned escape hatch: a portfolio-level HOLD with no single ticker
            # ("Rebuild cash buffer", "Hold fire on ... (CLS/BE/NBIS/MRVL)") -- these are real
            # and legitimate (see P-009/P-046/P-047), so require an explicit human-written
            # label rather than fabricating one, and skip the ticker-in-label check for them.
            action = spec["action"]
        else:
            rejected.append({"index": i, "reason": "ticker is required unless direction=HOLD and an explicit 'action' label is given"})
            continue
        pr = {
            "action": action,
            "ticker": ticker,
            "direction_bucket": direction,
            "size_usd": spec.get("size_usd"),
            "price_at_proposal": spec.get("price_at_proposal"),
            "rationale": spec.get("rationale", ""),
            "trigger_type": spec.get("trigger_type"),
            "date": ts, "created_utc": created_utc,
            "status": "open",
        }
        # Benchmark anchor for alpha-relative scoring (added 2026-09-07). holdings.json's
        # `benchmarks.smh` is already fetched every run at zero extra cost -- the caller
        # (smith-strategist, via the dispatch prompt) is expected to pass it straight through
        # for every BUY/TRIM/SELL spec. cmd_score falls back to absolute-move grading, flagged
        # in data_quality, for any proposal missing this (all pre-2026-09-07 history, and any
        # caller that omits it) -- it is never backfilled or guessed.
        if spec.get("benchmark_price_at_proposal") is not None:
            pr["benchmark_price_at_proposal"] = spec["benchmark_price_at_proposal"]
            pr["benchmark_ticker"] = spec.get("benchmark_ticker") or "SMH"
        for optional in ("pair_id", "pair_role", "cluster"):
            if spec.get(optional) is not None:
                pr[optional] = spec[optional]
        # Typed passthrough BEFORE support-anchored sizing below, so a computed stop/size from
        # `_size_support_anchored` overrides a caller-supplied one rather than the reverse.
        why, unknown = _apply_spec_passthrough(pr, spec)
        if why:
            rejected.append({"index": i, "reason": why})
            continue
        for k in unknown:
            unknown_seen.setdefault(k, []).append(ticker)
        # `supersedes` (added 2026-09-15): ids this spec replaces, retired by cmd_proposals.
        if spec.get("supersedes"):
            sup = spec["supersedes"] if isinstance(spec["supersedes"], list) else [spec["supersedes"]]
            bad = [x for x in sup if not (isinstance(x, str) and _PROPOSAL_ID_RE.match(x))]
            if bad:
                rejected.append({"index": i, "reason": f"supersedes must be P-### ids, got {bad!r}"})
                continue
            pr["supersedes"] = sorted(set(sup))
        if run_dir and ticker and direction in ("BUY", "SELL", "TRIM"):
            ref = refs.get(str(ticker).upper())
            if ref:
                pr["price_check"] = _check_anchor(pr, "price_at_proposal", ref, ticker, price_checks)
            else:
                unchecked.append(ticker)
            if bench_ref:
                _check_anchor(pr, "benchmark_price_at_proposal", bench_ref, ticker, price_checks)
                pr.setdefault("benchmark_ticker", "SMH")

        # --- SUPPORT-ANCHORED SIZING (added 2026-08-30) -------------------------------
        # A rebound entry is bought AT a level, so its stop belongs just under that level
        # rather than 2xATR below spot -- same 0.5% risk budget, shorter stop, larger
        # position. The arithmetic is done HERE rather than by the agent, per COMPUTE-FIRST:
        # this is the point where a proposal is created, so it is the last place the size can
        # be made deterministic before it becomes a dollar figure someone acts on.
        if spec.get("trigger_type") in SUPPORT_ANCHORED_TRIGGERS:
            # Stamp the basis even when the exception does NOT apply. A rebound proposal sized
            # by the standard rule should say so and say why -- otherwise a reader cannot tell
            # a deliberate fallback from a forgotten support level, and the two want very
            # different responses.
            sized = _size_support_anchored(spec, args.base_dir)
            pr.update(sized["fields"])
            if sized["rejected"]:
                rejected.append({"index": i, "reason": sized["rejected"]})
                continue
        # belt-and-braces: re-run the exact same shape check the schema validator uses, on
        # THIS proposal, before it ever touches the file. A future caller passing a malformed
        # spec (e.g. a ticker that isn't actually in a hand-supplied `action`) gets rejected
        # here rather than silently written.
        if action.strip().upper() in _BARE_DIRECTION_WORDS:
            rejected.append({"index": i, "reason": f"constructed action {action!r} is still a bare direction word -- this should be unreachable, report as a bug"})
            continue
        if ticker and ticker.upper() not in action.upper():
            rejected.append({"index": i, "reason": f"ticker {ticker!r} does not appear in constructed action {action!r}"})
            continue
        built.append(pr)

    if rejected:
        fail(f"{len(rejected)} of {len(specs)} proposal spec(s) rejected before writing anything: {rejected}")

    props.extend(built)
    proposals["proposals"] = props
    safe_write(p_path, proposals)
    dq_prices = ([] if run_dir else
                 ["prices not checked: pass --run-dir so price_at_proposal is checked against this run's quotes"])
    if unchecked:
        dq_prices.append(f"no reference price in the run for {sorted(set(unchecked))} -- price_at_proposal kept as supplied")
    for field, tickers in sorted(unknown_seen.items()):
        dq_prices.append(f"spec field {field!r} is not in PASSTHROUGH -- kept under spec_extras on "
                         f"{sorted(set(t for t in tickers if t))} rather than dropped; add it to "
                         "PASSTHROUGH with a validator if it should be a first-class field")
    emit({"added": len(built), "tickers": [p["ticker"] for p in built], "written": True,
          "price_checks": price_checks, "unchecked": sorted(set(unchecked)), "data_quality": dq_prices,
          "next_step": "run smith_math.py proposals to assign ids, dedup and prioritize"})
