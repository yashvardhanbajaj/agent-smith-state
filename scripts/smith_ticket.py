#!/usr/bin/env python3
"""
Agent Smith -- trade-ticket sizing in RISK DOLLARS (Phase 2 of the proposal-engine rebuild).

Pure functions, stdlib only, no I/O -- same contract as smith_risk.py and smith_conviction.py.
Imports only smith_core's constants (as smith_risk does), never smith_lifecycle or smith_math.

THE INCIDENT. On 2026-09-20 the engine proposed rotating $56.37 of SKHY into CIEN on a $42,542
book. A correct 10-point call on that ticket earns $5.64; the round trip costs 0.30% of the buy.
It was not a bad judgment -- it was the arithmetic of `market_value x 0.30` applied to a $188
stub. The engine's BUYS were already sized in risk dollars (smith_risk.stop_and_cap: 0.5% of
book / stop distance); its SELLS were market-value fractions, so nothing on the sell side could
say "this trade is too small to matter" or "this trim removes this much risk". This module makes
risk dollars the currency of both sides.

NOTATION (from smith_risk.stop_and_cap):
    stop_pct = max(2 * atr20_pct, 3.0)
    R_base   = risk_per_position_pct_of_book / 100 * total_book        (0.5% -> ~$212.71)
    size_usd = risk_usd / (stop_pct / 100)

A severity is a multiple of R_base (smith_core.SEVERITY_R). A 3%-ATR name therefore gets a
LARGER dollar trim than a 12%-ATR name for the same severity -- equal risk removed, which a
market-value fraction cannot express.

WHAT IS NOT HERE. No heat budget and no expected-value gate: those are Phases 3 and 4. This
module sizes one ticket, or one rotation, at a time.
"""
from smith_core import (DUST_USD_DEFAULT, FEE_COVER_MULT, MIN_TICKET_PCT_OF_BOOK, MIN_TICKET_R,
                        MIN_TICKET_USD, ROUND_TRIP_FEE_PCT, TRIM_TO_EXIT_FRACTION, dust_usd)

# Reported when a value cannot be sized because an input is missing. Never estimated: a stop the
# desk cannot compute is not a stop it should trade on.
UNSIZED = "unsized"


def stop_pct_from_atr(atr20_pct):
    """policy's stop rule, exactly as smith_risk.stop_and_cap states it. None in, None out."""
    if atr20_pct is None:
        return None
    return max(2 * atr20_pct, 3.0)


def r_base_usd(total_book_usd, policy):
    """R_base: the dollar risk budget of ONE standard position (0.5% of book, from policy)."""
    pct = ((policy or {}).get("stop_loss_framework") or {}).get("risk_per_position_pct_of_book", 0.5)
    return (pct / 100.0) * (total_book_usd or 0.0)


def size_from_risk(r_ticket_usd, stop_pct):
    """Dollars of position that put `r_ticket_usd` at risk when the stop is `stop_pct` away."""
    if r_ticket_usd is None or not stop_pct or stop_pct <= 0:
        return None
    return r_ticket_usd / (stop_pct / 100.0)


def trim_risk_cap_severity(r_open_usd, r_base_usd_):
    """Severity of a risk-cap trim, in R_base units: (R_open - R_base) / R_base.

    This is the one severity that is COMPUTED rather than chosen, and it is exact: for a
    position with market value mv and stop s, R_open = mv*s and R_base = max_position*s, so
    severity*R_base/s = mv - max_position -- the trim lands the position EXACTLY on its ATR cap
    and can never overshoot it. A position at or under its cap has severity 0 (nothing to trim).
    """
    if not r_base_usd_ or r_open_usd is None:
        return None
    return max(0.0, (r_open_usd - r_base_usd_) / r_base_usd_)


def sell_size_from_risk(severity_r, r_base, stop_pct, mv):
    """Dollar size of a sell that removes `severity_r` x R_base of risk, clamped to the position.

    min(severity_r * r_base / (stop_pct/100), mv). `clamped_by_mv` says the SIGNAL asked for at
    least the whole position -- which is how thesis_break / conviction_exit (2.0R) usually end up
    a full exit on a high-volatility name, and why that is not a bug.
    """
    raw = size_from_risk(severity_r * r_base if (severity_r is not None and r_base) else None, stop_pct)
    if raw is None or mv is None:
        return {"size_usd": None, "unclamped_usd": None, "clamped_by_mv": False,
                "risk_removed_usd": None, "reason": "missing stop, severity or market value"}
    size = min(raw, mv)
    return {"size_usd": round(size, 2), "unclamped_usd": round(raw, 2),
            "clamped_by_mv": raw >= mv,
            "risk_removed_usd": round(size * stop_pct / 100.0, 2), "reason": None}


def rotation_legs(sell_size_usd, sell_stop_pct, buy_r_ticket, buy_stop_pct):
    """Size the BUY leg of a rotation to the RISK the sell leg freed, not to its dollars.

        R_freed  = sell_size * sell_stop_pct / 100
        buy_size = min(buy_r_ticket, R_freed) / (buy_stop_pct / 100)

    WHY. The old rotations conserved DOLLARS: sell $610.76 of MU, buy <= $610.76 of something.
    But MU carries a 12% stop and AMAT a 7.84% one, so those dollars are not the same risk --
    selling $610.76 of MU frees $73.30 of risk, which is $935 of AMAT. A dollar-conserving swap
    silently cuts book heat whenever the buy is the calmer name (and raises it when it is the
    louder one). A risk-conserving swap leaves aggregate open risk where it was.

    `buy_r_ticket` is the risk the buy's OWN sizing would take (its conviction tier / staged
    tranche); None means the pair has no ticket of its own (cluster_rotation buys whatever the
    sale freed). The buy is capped by the smaller of the two, and `bound_by` names which. Callers
    then apply every existing clamp (headroom, cluster room, deployable cash) via
    smith_conviction.clamp_size -- so a rotation is flat on heat ONLY when neither the ticket nor
    a downstream clamp binds; `heat_delta_usd` reports the difference honestly either way.
    """
    if not sell_size_usd or not sell_stop_pct or not buy_stop_pct:
        return {"r_freed_usd": 0.0, "buy_size_usd": 0.0, "buy_uncapped_usd": 0.0,
                "bound_by": "no_sell_leg" if not sell_size_usd else "missing_stop",
                "buy_risk_usd": 0.0, "heat_delta_usd": 0.0}
    r_freed = sell_size_usd * sell_stop_pct / 100.0
    uncapped = r_freed / (buy_stop_pct / 100.0)
    if buy_r_ticket is not None and buy_r_ticket < r_freed:
        bound_by, r_buy = "buy_r_ticket", max(0.0, buy_r_ticket)
    else:
        bound_by, r_buy = "r_freed", r_freed
    buy_size = r_buy / (buy_stop_pct / 100.0)
    return {"r_freed_usd": round(r_freed, 2), "buy_size_usd": round(buy_size, 2),
            "buy_uncapped_usd": round(uncapped, 2), "bound_by": bound_by,
            "buy_risk_usd": round(r_buy, 2), "heat_delta_usd": round(r_buy - r_freed, 2)}


def materiality_policy(trade_materiality=None):
    """Resolve the five floors from policy.trade_materiality, defaulting each to smith_core's
    constant. `confirmed` is carried through so the briefing can say the floors are unsigned."""
    tm = trade_materiality or {}

    def pick(key, default):
        v = tm.get(key)
        return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0 else default

    return {"min_ticket_usd": pick("min_ticket_usd", MIN_TICKET_USD),
            "min_ticket_pct_of_book": pick("min_ticket_pct_of_book", MIN_TICKET_PCT_OF_BOOK),
            "min_ticket_r": pick("min_ticket_r", MIN_TICKET_R),
            "fee_cover_mult": pick("fee_cover_mult", FEE_COVER_MULT),
            "min_position_usd": pick("min_position_usd", DUST_USD_DEFAULT),
            "confirmed": bool(tm.get("confirmed")) if tm else False}


def materiality(size_usd, stop_pct, total_book, r_base, round_trip_fee_usd, policy=None):
    """Does a ticket clear ALL four floors?

        floor = max( MIN_TICKET_USD,
                     MIN_TICKET_PCT_OF_BOOK% x total_book,
                     MIN_TICKET_R x R_base / (stop_pct/100),
                     FEE_COVER_MULT x round_trip_fee_usd )

    Returns {ok, floor_usd, binding_term, shortfall_usd, terms}. A sub-floor ticket is NEITHER
    shrunk up to the floor (that would invent size the signal never asked for) NOR silently
    dropped (that would hide how many ideas are too small to act on -- itself the signal that the
    book needs consolidating). The caller emits it with vote "below_materiality".

    THE R TERM is the one that scales with the name: 0.20R of a 4.6%-stop name is $929, of a
    12%-stop name $354. A ticket must move at least a fifth of a standard position's risk budget.

    THE FEE TERM IS STRUCTURALLY INERT TODAY, and this docstring says so rather than pretending
    otherwise. INDmoney's fee is proportional (0.30% on buys, measured to three decimals), so
    the fee on a ticket is 0.003 x size and FEE_COVER_MULT x that is 0.075 x size -- always below
    the size itself. The term only binds when the caller passes a fee that does NOT scale with
    the ticket (a fixed per-order charge, or a minimum-fee tier). It is kept because the plan
    specifies it and because it becomes live the day the broker adds a fixed component; the
    other three terms are what set today's $400-$900 floors.

    Full exits are exempt -- see exit_or_hold; the CALLER applies that exemption.
    """
    pol = materiality_policy(policy)   # accepts the raw block or an already-resolved one
    r_term = (pol["min_ticket_r"] * r_base / (stop_pct / 100.0)) if (r_base and stop_pct) else 0.0
    terms = {"min_ticket_usd": pol["min_ticket_usd"],
             "pct_of_book": pol["min_ticket_pct_of_book"] / 100.0 * (total_book or 0.0),
             "min_ticket_r": r_term,
             "fee_cover": pol["fee_cover_mult"] * (round_trip_fee_usd or 0.0)}
    binding = max(terms, key=lambda k: terms[k])
    floor = terms[binding]
    size = size_usd or 0.0
    # compared at the cent, the precision every figure here is reported at: a ticket that
    # matches the printed floor must not fail on a sub-cent remainder nobody can see
    ok = round(size, 2) >= round(floor, 2)
    return {"ok": ok, "floor_usd": round(floor, 2), "binding_term": binding,
            "shortfall_usd": 0.0 if ok else round(floor - size, 2),
            "terms": {k: round(v, 2) for k, v in terms.items()}}


def exit_or_hold(mv, trim_usd, min_position_usd):
    """Decide whether a proposed trim is a trim, a full exit, or nothing.

        * trim >= mv                            -> full exit (the signal asked for everything)
        * position ALREADY below min_position   -> hold: a stub is a consolidation candidate,
                                                   never a trim candidate
        * post-trim residual < min_position     -> full exit (a stub left behind is worse than
                                                   either outcome)
        * trim removes > TRIM_TO_EXIT_FRACTION  -> full exit (60% gone is an exit in all but name)
        * otherwise                             -> trim as sized

    WHY (SKHY $37.58, CIEN $2.98). A 20% catalyst trim of a $188 SKHY was $37.58 -- a fill the
    broker's fee alone makes negative-EV -- and 30% of a $2.98 CIEN residue is 89 cents. Neither
    can be "a partial trim" of anything: they are leftovers. The rule turns them into either a
    whole-position exit (when the signal is strong enough to ask for it) or no ticket at all.

    Returns {action: trim|full_exit|hold, size_usd, reason}. min_position_usd is smith_core's
    dust_usd(policy) -- ONE dust number for the whole desk (see that function's docstring).
    """
    if mv is None or trim_usd is None:
        return {"action": "hold", "size_usd": None, "reason": "missing market value or trim size"}
    if trim_usd <= 0 or mv <= 0:
        return {"action": "hold", "size_usd": 0.0, "reason": "nothing to trim"}
    if trim_usd >= mv:
        return {"action": "full_exit", "size_usd": round(mv, 2),
                "reason": "the risk-sized trim is at least the whole position -- a full exit"}
    if mv < min_position_usd:
        return {"action": "hold", "size_usd": 0.0,
                "reason": (f"position ${mv:,.2f} is already below the ${min_position_usd:,.0f} "
                           f"minimum-position threshold -- a stub is a consolidation candidate, "
                           f"never partially trimmed")}
    residual = mv - trim_usd
    if residual < min_position_usd:
        return {"action": "full_exit", "size_usd": round(mv, 2),
                "reason": (f"a ${trim_usd:,.2f} trim would leave ${residual:,.2f}, under the "
                           f"${min_position_usd:,.0f} minimum position -- converted to a full exit")}
    if trim_usd > TRIM_TO_EXIT_FRACTION * mv:
        return {"action": "full_exit", "size_usd": round(mv, 2),
                "reason": (f"the ${trim_usd:,.2f} trim removes {trim_usd / mv:.0%} of the position "
                           f"(> {TRIM_TO_EXIT_FRACTION:.0%}) -- converted to a full exit")}
    return {"action": "trim", "size_usd": round(trim_usd, 2), "reason": None}


def sizing_context(total_book_usd, policy, stop_pct_by_ticker=None):
    """Everything a trigger needs to size a sell, gathered once per run from policy + book."""
    tm = materiality_policy((policy or {}).get("trade_materiality"))
    return {"total_book_usd": total_book_usd or 0.0,
            "r_base_usd": r_base_usd(total_book_usd, policy),
            "materiality": tm,
            "min_position_usd": dust_usd(policy),
            "fee_pct": ROUND_TRIP_FEE_PCT,
            "stop_pct_by_ticker": dict(stop_pct_by_ticker or {})}


def size_sell_leg(severity_r, mv, stop_pct, ctx):
    """One sell leg, end to end: risk-sized -> exit-or-hold -> materiality.

    Returns the fields a trigger row carries: size_usd, action, severity_r, stop_pct,
    risk_removed_usd, clamped_by_mv, sizing_note, materiality, and `vote_hint` -- "ok" or
    "below_materiality" (a full exit is never below materiality; a hold is, with a zero size).
    A missing stop or book yields size None / vote_hint "unsized" -- never an estimate.
    """
    r_base = ctx["r_base_usd"]
    if stop_pct is None or not r_base or mv is None:
        return {"size_usd": None, "action": UNSIZED, "severity_r": severity_r, "stop_pct": stop_pct,
                "risk_removed_usd": None, "clamped_by_mv": False,
                "sizing_note": "no stop distance (ATR20 missing) or no book value -- a risk-sized "
                               "sell cannot be computed and is never estimated",
                "materiality": None, "vote_hint": UNSIZED}
    raw = sell_size_from_risk(severity_r, r_base, stop_pct, mv)
    eoh = exit_or_hold(mv, raw["size_usd"], ctx["min_position_usd"])
    size = eoh["size_usd"]
    note = [f"{severity_r:g}R x ${r_base:,.2f} / {stop_pct:.2f}% stop = ${raw['unclamped_usd']:,.2f}"
            + (f", clamped to the ${mv:,.2f} position" if raw["clamped_by_mv"] else "")]
    if eoh["reason"]:
        note.append(eoh["reason"])
    fee = (size or 0.0) * ctx["fee_pct"] / 100.0
    mat = materiality(size, stop_pct, ctx["total_book_usd"], r_base, fee, ctx["materiality"])
    if eoh["action"] == "full_exit":
        mat = dict(mat, ok=True, shortfall_usd=0.0, exempt="full_exit")
        vote_hint = "ok"
    elif eoh["action"] == "hold":
        vote_hint = "below_materiality"
    else:
        vote_hint = "ok" if mat["ok"] else "below_materiality"
    return {"size_usd": size, "action": eoh["action"], "severity_r": severity_r,
            "stop_pct": round(stop_pct, 3),
            "risk_removed_usd": round((size or 0.0) * stop_pct / 100.0, 2),
            "clamped_by_mv": raw["clamped_by_mv"], "sizing_note": "; ".join(note),
            "materiality": mat, "vote_hint": vote_hint}
