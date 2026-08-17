"""Proposal lifecycle, outcome scoring, and stop-loss efficacy.

Split out of smith_math.py 2026-08-16: the file had reached 4,085 lines and mixed
four unrelated domains. Shared primitives live in smith_core; smith_math keeps the
per-run compute stages, the pipeline runner and the CLI, and imports these.
"""

import json
import re
import os
from datetime import date, datetime

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
        has_live_trigger = False
        if tt in LIVE_TRIGGERS and ticker in trigger_live_sets.get(tt, set()):
            row = trigger_rows[tt][ticker]
            score += 3
            has_live_trigger = True
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
            # catalyst_threat and thesis_break (added 2026-08-17): both cap/cluster-independent,
            # same discipline as overbought_distribution -- tested on their OWN condition, never
            # retired merely for being within the ATR cap or inside its policy band.
            elif pr.get("trigger_type") == "catalyst_threat":
                if ticker in trigger_live_sets.get("catalyst_threat", set()):
                    pass  # the catalyst is still live this run -- keep open
                else:
                    why = (f"{ticker} no longer appears in a structural-threat factor catalyst -- "
                           "the finding this trim was sized against has cleared or was superseded")
            elif pr.get("trigger_type") == "thesis_break":
                th_now = smith_risk.thesis_status(state_thesis.get(ticker))
                if th_now == "broken":
                    pass  # thesis is still broken -- keep open
                elif th_now is None:
                    pass  # cannot test (no usable status) -- keep open rather than guess
                else:
                    why = (f"{ticker}'s thesis is now '{th_now}', no longer 'broken' -- the "
                           "fundamental break this trim was sized against has been resolved or "
                           "reassessed")
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
                why = None      # standing instruction: never expires on age alone
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
        elif _tt == "catalyst_threat":
            retires_when = (f"{ticker} no longer appears in a structural-threat factor catalyst "
                            "(cap/cluster-independent -- staying inside the ATR cap does NOT "
                            "retire this)")
        elif _tt == "thesis_break":
            retires_when = (f"{ticker}'s thesis is no longer 'broken' (cap/cluster-independent -- "
                            "staying inside the ATR cap does NOT retire this)")
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
