#!/usr/bin/env python3
"""
Agent Smith -- trade-ticket sizing in RISK DOLLARS (Phase 2 of the proposal-engine rebuild).

Pure functions, stdlib only, no I/O -- same contract as smith_risk.py and smith_conviction.py.
Imports smith_core's constants (as smith_risk does) and smith_conviction.clamp_size (the one place
that names a binding clamp), never smith_lifecycle or smith_math.

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

SELLS: a severity (smith_core.SEVERITY_R) is a FRACTION OF THE POSITION'S OWN OPEN RISK,
R_open = mv * stop_pct/100, so sell_size = min(severity * mv, mv). (The first version used R_base
as the unit and turned 20% catalyst trims into full liquidations -- see smith_core.SEVERITY_R.)
R_base remains the unit for ENTRIES, for rotation buys' risk conservation, for materiality's R
term, and for trim_risk_cap, whose severity (R_open - R_base)/R_base is measured against the
budget the position was sized to.

PORTFOLIO HEAT (Phase 3, 2026-09-20, the second half of this file): the functions from
`heat_policy` down allocate ONE risk budget across EVERY buy candidate of a run at once. They are
pure and operate on plain candidate dicts, not trigger rows, so the gate can be tested against a
fixture book that is over its cap -- the live book (6.45% heat vs a 10% cap) deliberately never
binds it, which is why it is safe to land and why live data alone can never validate it.

THE EXPECTED-VALUE GATE lives in smith_edge (Phase 4); `allocation_priority` is the single place
its ordering key was swapped in.
"""
import datetime as _dt

from smith_core import (CORRELATION_MAX_AGE_DAYS, DUST_USD_DEFAULT, FEE_COVER_MULT,
                        HEAT_DEFER_LABEL, HEAT_FLOOR_AT_FULL_CORRELATION, MIN_TICKET_PCT_OF_BOOK,
                        MIN_TICKET_R, MIN_TICKET_USD, ROUND_TRIP_FEE_PCT, TRIM_TO_EXIT_FRACTION,
                        dust_usd)
import smith_conviction

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


def sell_size_from_open_risk(severity, mv, stop_pct):
    """Dollar size of a sell that removes `severity` x the position's OWN open risk.

    R_open = mv * stop_pct/100; risk_removed = severity * R_open; size = risk_removed / (stop/100)
    = severity * mv, clamped to mv. `clamped_by_mv` is true only for a severity >= 1.
    """
    if severity is None or mv is None or not stop_pct or stop_pct <= 0:
        return {"size_usd": None, "clamped_by_mv": False, "risk_removed_usd": None,
                "r_open_usd": None, "reason": "missing stop, severity or market value"}
    r_open = mv * stop_pct / 100.0
    size = min(severity * mv, mv)
    return {"size_usd": round(size, 2), "clamped_by_mv": severity * mv >= mv,
            "r_open_usd": round(r_open, 2),
            "risk_removed_usd": round(size * stop_pct / 100.0, 2), "reason": None}


def sell_size_from_risk(severity_r, r_base, stop_pct, mv):
    """Dollar size of a sell that removes `severity_r` x R_base of risk, clamped to the position.
    R_base units: used by trim_risk_cap (whose severity is computed against R_base), not by the
    SEVERITY_R table, which is in fractions of the position's own open risk.

    min(severity_r * r_base / (stop_pct/100), mv). `clamped_by_mv` says the request was for at
    least the whole position.
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
    """One sell leg, end to end: severity x open risk -> exit-or-hold -> materiality.

    Returns the fields a trigger row carries: size_usd, action, severity_r, stop_pct,
    risk_removed_usd, clamped_by_mv, sizing_note, materiality, and `vote_hint` -- "ok" or
    "below_materiality" (a full exit is never below materiality; a hold is, with a zero size).
    A missing stop or book yields size None / vote_hint "unsized" -- never an estimate.
    """
    r_base = ctx["r_base_usd"]     # still needed by materiality's R term
    if stop_pct is None or not r_base or mv is None:
        return {"size_usd": None, "action": UNSIZED, "severity_r": severity_r, "stop_pct": stop_pct,
                "risk_removed_usd": None, "clamped_by_mv": False,
                "sizing_note": "no stop distance (ATR20 missing) or no book value -- a risk-sized "
                               "sell cannot be computed and is never estimated",
                "materiality": None, "vote_hint": UNSIZED}
    raw = sell_size_from_open_risk(severity_r, mv, stop_pct)
    eoh = exit_or_hold(mv, raw["size_usd"], ctx["min_position_usd"])
    size = eoh["size_usd"]
    note = [f"{severity_r:.0%} of the position's ${raw['r_open_usd']:,.2f} open risk "
            f"({stop_pct:.2f}% stop) = ${raw['size_usd']:,.2f}"
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


# ===========================================================================
# PORTFOLIO HEAT BUDGET (Phase 3, 2026-09-20)
# ===========================================================================
# THE INCIDENT. policy.stop_loss_framework records that the 10% aggregate-open-risk cap was
# breached at 13.028% (2026-08-26) and 11.947% (2026-08-30) while sizing continued at the full
# per-position formula: the cap was computed on every run and used only for a warning string. A
# ticket sized in isolation cannot know that nine others are being sized the same run against the
# same room. Here every candidate competes for one budget.
#
#   H          = aggregate_open_risk_usd        (sum of R_open over the book: the ALL-FIRE sum)
#   H_max      = cap_pct/100 x total_book
#   H_eff_max  = H_max x (HEAT_FLOOR + (1 - HEAT_FLOOR) x (1 - rho))     rho = avg pairwise corr
#   R_free     = max(0, H_eff_max - H)
#
# UNITS. Everything in this section is RISK DOLLARS (size x stop/100), the same currency as R_base
# for entries and R_open for exits -- see the Phase 2 unit trap in smith_core.SEVERITY_R. The only
# market-value quantities are the per-name dollar rooms (single_position / ai_capex) and the
# would-be ticket sizes, and each is converted through that ticket's own stop.

# Numeric slack when comparing risk dollars: figures are reported at the cent.
_EPS = 0.005


def _r2(x):
    """round to the cent; `+ 0.0` turns a -0.0 into 0.0 so a de-risking pair never prints '-0.0'."""
    return round(x, 2) + 0.0


def heat_policy(block):
    """Resolve policy.heat_budget over smith_core's defaults. `confirmed` rides along so the
    briefing can say the floor is unsigned. A malformed value falls back to the default."""
    b = block or {}
    fl = b.get("heat_floor_at_full_correlation")
    ok = isinstance(fl, (int, float)) and not isinstance(fl, bool) and 0.0 <= fl <= 1.0
    sub = b.get("cluster_sub_budget")
    return {"heat_floor": float(fl) if ok else HEAT_FLOOR_AT_FULL_CORRELATION,
            "cluster_sub_budget": sub if isinstance(sub, bool) else True,
            "confirmed": bool(b.get("confirmed")) if b else False}


def correlation_read(corr, today):
    """The correlation the budget may rely on, or the reason it may not.

    Returns {rho, rho_used, basis, measured, reason, as_of, window_to, age_days}. `rho_used` is the
    measured average pairwise correlation clamped to [0,1] when it is fresh and present, and 1.0
    (fully correlated: the conservative bound, H_eff_max = H_max x HEAT_FLOOR) otherwise. The
    caller must say which it was: a missing or stale correlation is NEVER read as zero
    correlation, because that would hand the book a diversification credit nobody measured -- the
    whole lesson of stop_risk.take_the_credit being false. Missing = degraded stage, absent file,
    no stop_risk block, or a price window older than smith_core.CORRELATION_MAX_AGE_DAYS.
    """
    out = {"rho": None, "rho_used": 1.0, "measured": False, "as_of": None, "window_to": None,
           "age_days": None, "reason": None}
    if not corr or not isinstance(corr, dict):
        out["reason"] = "compute_correlation.json absent"
    elif corr.get("degraded"):
        out["reason"] = f"correlation stage degraded ({corr.get('reason')})"
    else:
        rho = (corr.get("stop_risk") or {}).get("avg_pairwise_correlation")
        out["as_of"] = corr.get("as_of")
        wt = (corr.get("window") or {}).get("to")
        out["window_to"] = wt
        if not isinstance(rho, (int, float)) or isinstance(rho, bool):
            out["reason"] = "no stop_risk.avg_pairwise_correlation in compute_correlation.json"
        else:
            out["rho"] = float(rho)
            try:
                age = (today - _dt.date.fromisoformat(str(wt)[:10])).days
            except (TypeError, ValueError):
                age = None
            out["age_days"] = age
            if age is None:
                out["reason"] = "correlation price window has no parseable end date"
            elif age > CORRELATION_MAX_AGE_DAYS:
                out["reason"] = (f"correlation price window ends {wt}, {age}d old "
                                 f"(> {CORRELATION_MAX_AGE_DAYS}d)")
            else:
                out["measured"] = True
                out["rho_used"] = min(1.0, max(0.0, float(rho)))
    out["basis"] = ("measured avg pairwise correlation" if out["measured"] else
                    f"CONSERVATIVE BOUND (rho treated as 1.0, budget = cap x HEAT_FLOOR): {out['reason']}")
    return out


def heat_budget(h_usd, total_book_usd, cap_pct, corr_read, heat_floor=HEAT_FLOOR_AT_FULL_CORRELATION):
    """The run's risk budget. See the section header for the formula.

    `over_cap` is H > H_eff_max -- the CORRELATION-ADJUSTED budget, not the raw 10%: a 6.45% book
    at rho 0.9 is already over its adjusted cap, and it is the adjusted one that gates buys.
    """
    h = h_usd or 0.0
    h_max = (cap_pct or 0.0) / 100.0 * (total_book_usd or 0.0)
    rho_used = corr_read["rho_used"]
    factor = heat_floor + (1.0 - heat_floor) * (1.0 - rho_used)
    h_eff = h_max * factor
    return {"h_usd": round(h, 2), "h_max_usd": round(h_max, 2), "rho": corr_read["rho"],
            "rho_used": round(rho_used, 4), "rho_basis": corr_read["basis"],
            "rho_measured": corr_read["measured"], "heat_floor": heat_floor,
            "cap_factor": round(factor, 4), "h_eff_max_usd": round(h_eff, 2),
            "r_free_usd": round(max(0.0, h_eff - h), 2), "over_cap": h > h_eff + _EPS,
            "over_cap_by_usd": round(max(0.0, h - h_eff), 2)}


def cash_funded_room(limit_frac, numerator_usd, denominator_usd, denominator_moves):
    """Largest cash-funded buy X that keeps (numerator + X) / denominator <= limit_frac.

    `denominator_moves` is the whole point: on INVESTED EQUITY a cash-funded buy raises the
    numerator AND the denominator, so X <= (l*D - N) / (1 - l), which is larger than the linear
    l*D - N; on TOTAL BOOK a cash-funded buy leaves the denominator alone and the room is exactly
    linear. (Same distinction smith_math.cmd_drift documents for cluster ceilings, which uses the
    linear figure there as a deliberate under-statement.) Returns None -- non-binding, "unknown is
    not a reason to block" -- when the limit is >= 100% of a moving denominator: a position or a
    factor cannot exceed 100% of the equity it is part of by adding cash-funded shares of itself.
    Returns None for missing inputs; never negative.
    """
    if limit_frac is None or numerator_usd is None or not denominator_usd or denominator_usd <= 0:
        return None
    if denominator_moves:
        if limit_frac >= 1.0:
            return None
        return max(0.0, (limit_frac * denominator_usd - numerator_usd) / (1.0 - limit_frac))
    return max(0.0, limit_frac * denominator_usd - numerator_usd)


def cluster_risk_max_usd(h_eff_max_usd, band_hi_pct, ceiling_basis, total_book_usd, invested_equity_usd):
    """R_cluster_max: the cluster's share of the risk budget, its policy band ceiling.

    The band ceiling is a share of a market-value denominator, and the policy tests it on
    `ceiling_basis` (cmd_drift's `ceiling_tested_on`): invested_equity normally, total_book while
    cash is above the normal band. Risk lives only in invested dollars, so a ceiling of hi% of
    INVESTED EQUITY is hi% of the risk; a ceiling of hi% of TOTAL BOOK is hi x TB/E percent of the
    invested dollars' risk. The share is converted with the basis the policy used, never the other
    one -- mixing them here would silently re-open the denominator bug cmd_drift already fixed
    twice. Capped at the whole budget. None when the cluster has no band.
    """
    if band_hi_pct is None or not h_eff_max_usd:
        return None
    share = band_hi_pct / 100.0
    if ceiling_basis == "total_book" and invested_equity_usd and total_book_usd:
        share *= total_book_usd / invested_equity_usd
    return round(h_eff_max_usd * min(1.0, share), 2)


def allocation_priority(candidate):
    """THE ordering key: higher is allocated first.

    Phase 4 swap (2026-09-20): a candidate that carries an EXPECTED VALUE (`ev_r`, set by
    smith_math._apply_edge_gate) is ordered by it. EV_R is already per unit of risk, so ordering by
    it is ordering by EV per unit of the scarce thing the budget is made of -- risk -- rather than by
    a conviction score that says nothing about payoff or stop distance. A candidate with no EV (a
    cash-above-band gate override that had no analyst target) falls back to its conviction score;
    at most one such candidate ever coexists with the others, so the two scales are never mixed
    across a real ranking."""
    ev = candidate.get("ev_r")
    if ev is not None:
        return ev
    return candidate.get("score") or 0.0


def _deferred_reason(budget, net, remaining):
    if budget["over_cap"]:
        return (f"book heat ${budget['h_usd']:,.2f} exceeds the correlation-adjusted budget "
                f"${budget['h_eff_max_usd']:,.2f} -- no new net-risk-adding buys until heat falls")
    return (f"needs ${net:,.2f} of net new risk, ${max(0.0, remaining):,.2f} of the run's "
            f"${budget['h_eff_max_usd']:,.2f} correlation-adjusted budget is left")


def allocate_heat(candidates, budget, rooms=None, standalone_credit_usd=0.0, key=None):
    """Allocate ONE heat budget across every buy candidate of a run.

    ORDERING RULE (stated because two of the alternatives are wrong):
      0. If the book is already over H_eff_max, NO credit is taken from any sell: a sell frees
         heat only when it executes, and an over-cap book may not fund new risk on the promise of
         one. Only tickets whose net risk is <= 0 can fit.
      1. Otherwise the budget is R_free plus `standalone_credit_usd` (live, above-materiality
         sells that are not part of a pair -- computed by the caller from rows whose vote is
         "live": a below_materiality, shadow or deferred sell never executes and never counts).
      2. PAIRS are allocated first, in key order. A pair's net risk is buy_risk - the risk its OWN
         sell frees; net <= 0 always fits, net > 0 consumes exactly the net, and a pair with a
         negative net RAISES the remaining budget by the risk it retires. A pair whose buy leg is
         shrunk under the materiality floor by a downstream clamp is below_materiality: it neither
         consumes nor frees. Pairs are never partially sized -- half a rotation is not a rotation.
      3. SINGLES then go greedily in key order. One that fits is taken; one that partly fits is
         sized down to what is left (clamped_by "heat_room") ONLY if the result still clears its
         materiality floor; otherwise it is DEFERRED, never dropped, so the desk sees the queue.
    Before any heat test, each ticket is shrunk by the three static caps -- single_position,
    ai_capex, cluster_risk_budget -- which only ever reduce it, with running tallies so two buys
    of one name (or one cluster) in the same run share one room.

    candidate = {id, kind: "single"|"pair", ticker, score, size_usd, stop_pct, floor_usd, cluster,
                 is_ai, [pair only: freed_risk_usd, sell_size_usd, sell_cluster, sell_is_ai]}
    rooms     = {"single_position_usd": {ticker: usd|None}, "ai_capex_usd": usd|None,
                 "cluster_risk_usd": {cluster: risk usd|None}}      (all optional; None = non-binding)
    Returns {decisions: {id: {...}}, remaining_usd, h_after_usd, credit_usd}.
    """
    key = key or allocation_priority        # resolved at call time so a swap is one line
    rooms = rooms or {}
    over = budget["over_cap"]
    credit = 0.0 if over else max(0.0, standalone_credit_usd or 0.0)
    remaining = budget["r_free_usd"] + credit
    h_run = budget["h_usd"] - credit
    single_room = dict(rooms.get("single_position_usd") or {})
    ai_room = rooms.get("ai_capex_usd")
    cluster_room = dict(rooms.get("cluster_risk_usd") or {})
    ordered = (sorted([c for c in candidates if c["kind"] == "pair"], key=lambda c: (-key(c), c["id"]))
               + sorted([c for c in candidates if c["kind"] != "pair"], key=lambda c: (-key(c), c["id"])))
    decisions = {}

    for c in ordered:
        pair = c["kind"] == "pair"
        stop = c["stop_pct"]
        size0 = c["size_usd"] or 0.0
        freed = (c.get("freed_risk_usd") or 0.0) if pair else 0.0
        sell_usd = (c.get("sell_size_usd") or 0.0) if pair else 0.0
        floor = c.get("floor_usd") or 0.0
        d = {"id": c["id"], "status": None, "size_usd": None, "size_pre_heat_usd": round(size0, 2),
             "would_be_size_usd": None, "clamped_by": None, "risk_usd": None, "net_risk_usd": None,
             "book_heat_before_usd": round(h_run, 2), "book_heat_after_usd": round(h_run, 2),
             "heat_room_remaining_usd": round(max(0.0, budget["h_eff_max_usd"] - h_run), 2),
             "deferred_by": None, "deferred_reason": None}
        decisions[c["id"]] = d

        # -- static caps: only ever shrink; a swap credits back what it sells from the same pool --
        sp = single_room.get(c["ticker"])
        ai = (None if (ai_room is None or not c.get("is_ai"))
              else ai_room + (sell_usd if c.get("sell_is_ai") else 0.0))
        cr = cluster_room.get(c.get("cluster"))
        if cr is not None and pair and c.get("sell_cluster") == c.get("cluster"):
            cr += freed
        cr_usd = None if cr is None else cr / (stop / 100.0)
        size1, clamp1 = smith_conviction.clamp_size(size0, None, None, None, single_position_room_usd=sp,
                                                    ai_capex_room_usd=ai, cluster_risk_room_usd=cr_usd)
        d["would_be_size_usd"] = size1
        if pair and size1 + _EPS < floor and size1 < size0 - _EPS:
            d.update(status="below_materiality", clamped_by=clamp1,
                     size_usd=size1, risk_usd=_r2(size1 * stop / 100.0), net_risk_usd=0.0)
            continue

        if over and not pair and size0 * stop / 100.0 > _EPS:
            # an over-cap book takes NO new net-risk single buy, and each one says so by name --
            # tested on the ticket as the signal sized it, so a cluster clamp that happens to
            # zero it does not hide the real reason
            # (a would-be of $0 tells the desk nothing, so a ticket a cap zeroed reports the size
            # the signal asked for)
            wb = size1 if size1 > 0 else size0
            d.update(status="deferred", deferred_by=HEAT_DEFER_LABEL, size_usd=None, clamped_by=clamp1,
                     would_be_size_usd=_r2(wb), risk_usd=_r2(wb * stop / 100.0),
                     net_risk_usd=_r2(wb * stop / 100.0),
                     deferred_reason=_deferred_reason(budget, wb * stop / 100.0, 0.0))
            continue
        if not pair and not size1 > 0:
            # a static cap left no room at all: nothing to allocate, nothing to defer
            d.update(status="no_room", size_usd=0.0, clamped_by=clamp1, risk_usd=0.0, net_risk_usd=0.0)
            continue
        risk1 = size1 * stop / 100.0
        net = risk1 - freed
        size2, clamp2, accepted = size1, clamp1, True
        if net > _EPS and net > remaining + _EPS:
            if pair or not size1 > 0:
                accepted = False
            else:
                room_usd = max(0.0, remaining) / (stop / 100.0)
                size2, clamp2 = smith_conviction.clamp_size(size1, None, None, None, heat_room_usd=room_usd)
                # a partial fit is emitted only if it is still a ticket worth taking
                accepted = size2 > 0 and size2 + _EPS >= floor
        if not accepted:
            d.update(status="deferred", deferred_by=HEAT_DEFER_LABEL, size_usd=None, clamped_by=clamp1,
                     risk_usd=_r2(risk1), net_risk_usd=_r2(net),
                     deferred_reason=_deferred_reason(budget, net, remaining))
            continue

        risk2 = size2 * stop / 100.0
        net2 = risk2 - freed
        # a negative net (a de-risking pair) raises the budget, but never on an over-cap book
        remaining = remaining - net2 if not (over and net2 < 0) else remaining
        h_run = h_run + net2 if not (over and net2 < 0) else h_run
        if not pair:
            single_room[c["ticker"]] = (None if sp is None else max(0.0, sp - size2))
        if ai_room is not None and c.get("is_ai"):
            ai_room = max(0.0, ai_room - (size2 - (sell_usd if c.get("sell_is_ai") else 0.0)))
        if cr is not None:
            cluster_room[c.get("cluster")] = max(0.0, cluster_room.get(c.get("cluster"), 0.0) - risk2
                                                 + (freed if pair and c.get("sell_cluster") == c.get("cluster") else 0.0))
        if pair and c.get("sell_cluster") not in (None, c.get("cluster")) and c.get("sell_cluster") in cluster_room \
                and cluster_room[c["sell_cluster"]] is not None:
            cluster_room[c["sell_cluster"]] += freed
        d.update(status="clamped" if (clamp2 or size2 < size0 - _EPS) else "fit", size_usd=round(size2, 2),
                 clamped_by=clamp2, risk_usd=_r2(risk2), net_risk_usd=_r2(net2),
                 book_heat_after_usd=_r2(h_run),
                 heat_room_remaining_usd=_r2(max(0.0, budget["h_eff_max_usd"] - h_run)))
    return {"decisions": decisions, "remaining_usd": _r2(remaining), "h_after_usd": _r2(h_run),
            "credit_usd": _r2(credit)}


# =====================================================================================================
# THE TRADE TICKET (Phase 5, 2026-09-21)
# =====================================================================================================
# THE INCIDENT. Of 323 proposals ever written, 9 carried a stop. The trigger rows already knew the
# stop, the risk in dollars, the EV and the size they were clamped from -- `cmd_draft_specs` copied
# four of those numbers onto the strategist's draft and dropped the rest, and `cmd_add_proposal`
# dropped what remained. The proposal that reached the dashboard was a size and a sentence: nothing
# said where the trade is wrong, how much it risks, when it lapses, or what would make it stop
# being true -- so nothing could be scored on the terms it was taken on.
#
# The ticket is the answer, and it has ONE builder (`build_ticket`) so it is never hand-assembled.
# It is TWO-LAYER and additive: the nested `ticket` block is the truth; the legacy flat fields
# (`size_usd`, `stop_price_usd`, `risk_usd`, ...) keep their exact names and positions so the
# dashboard, cmd_score, cmd_proposals, smith_validity and all 323 historical rows work untouched,
# and they are WRITTEN FROM the ticket by one function (`apply_ticket`) so the two layers cannot
# diverge. Nothing is ever backfilled: a row with no `ticket_version` is LEGACY and every
# ticket-aware consumer must say so rather than guess a stop.
#
# What the strategist may touch: `rationale`, `evidence_quality`, and accept/reject. Every field in
# smith_core.TICKET_SCRIPT_OWNED_FIELDS belongs to the script; `script_owned_conflicts` is how
# add-proposal notices an edit.
from smith_core import (HEALTHY_THESIS, PAIRED_TRIGGERS, TICKET_REQUIRED_FIELDS, TICKET_REVIEW_FRACTION,
                        TICKET_SCRIPT_OWNED_FIELDS, TICKET_VERSION, horizon_for)

EDGE_KEYS = ("ev_r", "p_win", "payoff_r", "fee_r", "p_win_basis")
# BUY families whose trigger requires a healthy thesis at generation: the ticket's invalidation
# then also fires when the thesis leaves the healthy set (the same premise the trigger tested).
THESIS_GATED_BUY_FAMILIES = frozenset({"trend_entry", "conviction_average", "entry_setup",
                                       "oversold_reversion", "reentry", "bench_diversifier"})
# Families whose retires_when merely restates "off the live list (+ thesis)" for a BUY -- repeating
# it verbatim beside the structured clauses would say everything twice.
_GENERIC_BUY_RETIRES = THESIS_GATED_BUY_FAMILIES


def _num(x):
    return x if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def _round(x, n=2):
    x = _num(x)
    return None if x is None else round(x, n)


def leg_view(triggers, trigger_type, ticker, pair_id=None, pair_role=None):
    """The trigger row a proposal spec came from, as one flat view (pair-level fields folded into
    the leg), or None when this run's compute_triggers no longer carries it. Never raises."""
    rows = (triggers or {}).get(trigger_type)
    if not isinstance(rows, list):
        return None
    if trigger_type in PAIRED_TRIGGERS:
        for r in rows:
            if not isinstance(r, dict) or r.get("pair_id") != pair_id or pair_role not in ("sell", "buy"):
                continue
            leg = r.get(f"{pair_role}_leg")
            if not isinstance(leg, dict) or leg.get("ticker") != ticker:
                continue
            v = dict(leg)
            v.update(trigger_type=trigger_type, pair_id=pair_id, pair_role=pair_role, vote=r.get("vote"),
                     pair_retires_when=r.get("retires_when"), rotation_risk=r.get("rotation_risk"),
                     cluster=leg.get("cluster") or r.get("cluster"))
            return v
        return None
    for r in rows:
        if isinstance(r, dict) and r.get("ticker") == ticker:
            v = dict(r)
            v.setdefault("trigger_type", trigger_type)
            return v
    return None


def _ltcg_note(ticker, direction, size_usd, price, ctx):
    """FIFO tax-lot read for an exit, from lots.json -- or None. Never a guess: no lots, no price or
    no size means no note, and shares drawn from an undated lot are reported as UNKNOWN."""
    if direction not in ("SELL", "TRIM") or not size_usd or not price:
        return None
    lots = [l for l in ((ctx.get("lots") or {}).get(ticker) or []) if isinstance(l, dict)]
    if not lots:
        return None
    from smith_ledger import ltcg_eligible_on
    months, today = ctx.get("ltcg_months") or 24, ctx["today"]
    need, lt, st, unknown, first_st = size_usd / price, 0.0, 0.0, 0.0, None
    for lot in sorted(lots, key=lambda l: (l.get("date") is None, str(l.get("date") or ""))):
        if need <= 1e-9:
            break
        take = min(need, float(lot.get("qty") or 0))
        if take <= 0:
            continue
        need -= take
        try:
            elig = ltcg_eligible_on(_dt.date.fromisoformat(str(lot.get("date"))[:10]), months)
        except (ValueError, TypeError):
            unknown += take
            continue
        if elig <= today:
            lt += take
        else:
            st += take
            first_st = elig if first_st is None or elig < first_st else first_st
    bits = [f"FIFO on this exit: {lt:.4f} sh long-term, {st:.4f} sh short-term"]
    if unknown:
        bits.append(f"{unknown:.4f} sh from undated lots (holding period UNKNOWN, not guessed)")
    if first_st:
        bits.append(f"earliest short-term lot turns long-term {first_st} ({months}-month boundary; "
                    f"policy prefer_ltcg={'on' if ctx.get('prefer_ltcg') else 'off'})")
    if need > 1e-6:
        bits.append(f"{need:.4f} sh exceeds the lots on record")
    return "; ".join(bits)


def build_invalidation(direction, ticker, trigger_type, stop_price, row, thesis_gated):
    """(text, checks). One statement of what makes the ticket wrong. The `checks` list is the
    MACHINE-CHECKABLE part cmd_proposals evaluates each run; the text is what the reader sees.
    Built from the ticket's own stop, the trigger's own condition and the thesis premise -- never
    re-derived from prose elsewhere (retires_when used to be authored in three places)."""
    parts, checks = [], []
    if direction == "BUY" and stop_price:
        parts.append(f"price trades below ${stop_price:,.2f} (the stop)")
        checks.append({"type": "price_below", "price_usd": stop_price})
    if direction == "BUY" and thesis_gated:
        allowed = sorted(HEALTHY_THESIS)
        parts.append("thesis leaves " + "/".join(allowed))
        checks.append({"type": "thesis_not_in", "allowed": allowed})
    pair_id = row.get("pair_id")
    if trigger_type in PAIRED_TRIGGERS and pair_id:
        parts.append(f"the {trigger_type} pairing {pair_id} stops being live this run (both legs retire together)")
        checks.append({"type": "pair_not_live", "pair_id": pair_id})
    elif trigger_type:
        parts.append(f"{ticker} drops out of this run's live {trigger_type} list")
        checks.append({"type": "leaves_live_list", "family": trigger_type, "ticker": ticker})
    rw = row.get("pair_retires_when") or row.get("retires_when")
    if rw and not (direction == "BUY" and trigger_type in _GENERIC_BUY_RETIRES):
        parts.append(f"trigger condition: {rw}")
    if not parts:
        return None, []
    return " OR ".join(parts), checks


def _edge_block(row, direction):
    e = row.get("edge") if isinstance(row.get("edge"), dict) else {}
    if _num(e.get("ev_r")) is None:
        why = e.get("why") if direction != "BUY" else None
        return {"ev_r": None, "p_win": None, "payoff_r": None, "fee_r": None,
                "p_win_basis": ("n/a: " + why) if why else None}
    return {k: e.get(k) for k in EDGE_KEYS}


def _gate_block(row):
    g = row.get("gate") if isinstance(row.get("gate"), dict) else {}
    return {"family_verdict": g.get("verdict"), "family_multiplier": g.get("multiplier"),
            "family_basis": g.get("basis"), "n_eff": g.get("n_eff"),
            "mean_ev_net_pct": g.get("mean_ev_net_pct")}


def build_ticket(row, ctx, price_override=None):
    """THE one place a ticket is built. `row` is a trigger row/leg view (`leg_view`) or a view of a
    spec (`row_from_flat`); `ctx` carries today, total_book_usd, r_base_usd, prices, atr20_pct, lots,
    ltcg_months, prefer_ltcg. Pure: no I/O, no clock. Missing inputs become None -- never an
    estimate -- and `ticket_missing` reports them.

    BUY  : entry, stop (the row's stop, else entry x (1 - stop_pct)), target from the edge block
           (capped at TARGET_CAP_R -- the capped price is stored, the analyst target is named in
           the basis), size, risk ADDED, edge, gate, invalidation, horizon.
    SELL/TRIM: no stop (a sell exits a position that already exists), no target; risk is the risk
           REMOVED, and `lots.ltcg_note` says what the exit does to tax lots.
    """
    direction = str(row.get("direction") or "").upper()
    ticker, tt = row.get("ticker"), row.get("trigger_type")
    today, book = ctx["today"], _num(ctx.get("total_book_usd"))
    r_base = _num(ctx.get("r_base_usd"))
    is_buy = direction == "BUY"
    edge = row.get("edge") if isinstance(row.get("edge"), dict) else {}
    price = _num(price_override) or _num(row.get("price_usd")) or _num(edge.get("entry_usd")) \
        or _num((ctx.get("prices") or {}).get(ticker))
    size = _num(row.get("suggested_size_usd"))
    stop_pct = _num(row.get("stop_pct")) or _num(edge.get("stop_pct"))

    stop_price = None
    if is_buy:
        stop_price = _num(row.get("stop_price_usd"))
        if stop_price is None and price and stop_pct:
            stop_price = price * (1 - stop_pct / 100.0)
        stop_price = _round(stop_price)
    if _num(row.get("stop_distance_pct")):        # a spec-only ticket keeps the distance its author stated
        stop_dist = _round(row["stop_distance_pct"])
    else:
        stop_dist = (_round((price - stop_price) / price * 100) if (is_buy and price and stop_price)
                     else _round(stop_pct))
    stop = None
    if is_buy and stop_price is not None:
        stop = {"price_usd": stop_price, "distance_pct": stop_dist,
                "basis": row.get("stop_basis") or "policy 2xATR20, floor 3% (smith_risk.stop_and_cap)",
                "atr20_pct": _round((ctx.get("atr20_pct") or {}).get(ticker), 2)}

    target = None
    if is_buy:
        tgt = _num(edge.get("target_usd")) if _num(edge.get("target_usd")) is not None else _num(row.get("target_price_usd"))
        payoff = _num(edge.get("payoff_r"))
        if tgt is not None:
            eff = tgt
            basis = (f"{edge.get('target_source') or 'analyst target'} as of {edge.get('target_as_of')}"
                     if edge.get("target_source") else "target supplied on the spec")
            if payoff is not None and edge.get("target_capped") and price and stop_pct:
                eff = price * (1 + payoff * stop_pct / 100.0)
                basis = (f"capped at {payoff:g}R (a {_num(edge.get('payoff_r_uncapped'))}R analyst target of "
                         f"${tgt:,.2f} is not a plan); source {edge.get('target_source')}")
            target = {"price_usd": _round(eff), "basis": basis, "r_multiple": _round(payoff, 2)}

    risk_usd = _num(row.get("risk_usd"))
    risk_basis = None
    if is_buy and risk_usd is None and size and stop_pct:
        risk_usd, risk_basis = size * stop_pct / 100.0, "size x stop distance (no allocated risk on the trigger row)"
    removed = None if is_buy else _num(row.get("risk_removed_usd"))
    r_val = risk_usd if is_buy else removed

    def pct_book(x):
        return _round(x / book * 100, 3) if (x is not None and book) else None

    hb, ha = _num(row.get("book_heat_before_usd")), _num(row.get("book_heat_after_usd"))
    heat_room = _num(row.get("heat_room_remaining_usd"))
    wanted = _num(row.get("size_wanted_usd")) if is_buy else None

    text, checks = build_invalidation(direction, ticker, tt, stop_price, row,
                                      is_buy and tt in THESIS_GATED_BUY_FAMILIES
                                      and row.get("thesis_status") in HEALTHY_THESIS)
    if row.get("invalidation"):        # a spec-only path where the caller stated its own
        text = row["invalidation"]

    days = row.get("horizon_days")
    days, hbasis = (days, "supplied on the spec") if _num(days) else horizon_for(tt)
    review = max(1, int(days * TICKET_REVIEW_FRACTION))
    expires = row.get("expires_on") or (today + _dt.timedelta(days=int(days))).isoformat()

    pair = None
    if tt in PAIRED_TRIGGERS:
        rr = row.get("rotation_risk") if isinstance(row.get("rotation_risk"), dict) else {}
        pair = {"pair_id": row.get("pair_id"), "role": row.get("pair_role"),
                "r_freed_usd": rr.get("r_freed_usd"), "buy_risk_usd": rr.get("buy_risk_final_usd"),
                "heat_delta_usd": rr.get("heat_delta_final_usd")}

    ticket = {
        "ticker": ticker, "direction": direction, "trigger_type": tt,
        "source": row.get("_ticket_source") or "trigger_row", "built_on": today.isoformat(),
        "entry": {"price_usd": _round(price), "type": "limit_or_better", "valid_until": expires},
        "stop": stop, "target": target,
        "size": {"usd": _round(size), "shares": (round(size / price, 4) if (size and price) else None),
                 "pct_of_book": pct_book(size), "wanted_usd": _round(wanted) if wanted is not None else _round(size),
                 "clamped_by": row.get("clamped_by")},
        "risk": {"kind": "added" if is_buy else "removed", "usd": _round(risk_usd),
                 "removed_usd": _round(removed), "pct_of_book": pct_book(r_val), "basis": risk_basis,
                 "r_base_usd": _round(r_base), "r_ticket": _round(r_val / r_base, 3) if (r_val is not None and r_base) else None,
                 "book_heat_before_pct": pct_book(hb), "book_heat_after_pct": pct_book(ha),
                 "heat_budget_remaining_usd": _round(heat_room)},
        "edge": _edge_block(row, direction),
        "invalidation": text, "invalidation_checks": checks,
        "horizon": {"days": int(days), "review_on": (today + _dt.timedelta(days=review)).isoformat(),
                    "expires_on": expires, "basis": hbasis},
        "gate": _gate_block(row),
        "lots": {"ltcg_note": _ltcg_note(ticker, direction, size, price, ctx)},
        "pair": pair,
    }
    return ticket


def row_from_flat(pr, trigger_type=None):
    """A build_ticket row from a proposal's FLAT fields -- the spec-only path (no trigger row).
    The result is marked `_ticket_source: spec` so the ticket says it could not be verified against
    the engine's own numbers."""
    edge = {}
    if _num(pr.get("ev_r")) is not None:
        edge = {"ev_r": pr.get("ev_r"), "p_win": pr.get("p_win"), "payoff_r": pr.get("r_multiple")}
    return {"ticker": pr.get("ticker"), "direction": pr.get("direction_bucket"),
            "trigger_type": trigger_type or pr.get("trigger_type"), "price_usd": pr.get("price_at_proposal"),
            "suggested_size_usd": pr.get("size_usd"), "size_wanted_usd": pr.get("size_wanted_usd"),
            "clamped_by": pr.get("clamped_by"), "stop_price_usd": pr.get("stop_price_usd"),
            "stop_distance_pct": pr.get("stop_distance_pct"), "target_price_usd": pr.get("target_price_usd"),
            "risk_usd": pr.get("risk_usd"),
            "risk_removed_usd": pr.get("risk_removed_usd"), "edge": edge,
            "horizon_days": pr.get("horizon_days"), "expires_on": pr.get("expires_on"),
            "invalidation": pr.get("invalidation"), "pair_id": pr.get("pair_id"),
            "pair_role": pr.get("pair_role"), "_ticket_source": "spec"}


def flatten_ticket(ticket):
    """The legacy flat fields, derived from a ticket. Only non-null values are emitted, so a SELL
    never grows a `stop_price_usd`."""
    t = ticket or {}
    stop, tgt, size, risk = t.get("stop") or {}, t.get("target") or {}, t.get("size") or {}, t.get("risk") or {}
    edge, hz = t.get("edge") or {}, t.get("horizon") or {}
    flat = {"ticket_version": TICKET_VERSION, "size_usd": size.get("usd"),
            "size_wanted_usd": size.get("wanted_usd"), "clamped_by": size.get("clamped_by"),
            "stop_price_usd": stop.get("price_usd"), "stop_distance_pct": stop.get("distance_pct"),
            "target_price_usd": tgt.get("price_usd"), "r_multiple": tgt.get("r_multiple"),
            "risk_usd": risk.get("usd"), "risk_removed_usd": risk.get("removed_usd"),
            "ev_r": edge.get("ev_r"), "p_win": edge.get("p_win"),
            "horizon_days": hz.get("days"), "expires_on": hz.get("expires_on"),
            "invalidation": t.get("invalidation")}
    return {k: v for k, v in flat.items() if v is not None}


def apply_ticket(pr, ticket):
    """THE ONLY WRITER of ticket-owned flat fields onto a proposal row. The nested block goes on
    unchanged and every flat field is derived from it, so `stop_price_usd` and `ticket.stop.price_usd`
    cannot diverge. A flat field the ticket does not carry is REMOVED from the row -- a stale
    spec-supplied stop must not outlive a ticket that has none."""
    flat = flatten_ticket(ticket)
    for k in TICKET_SCRIPT_OWNED_FIELDS:
        if k not in flat:
            pr.pop(k, None)
    pr["ticket"] = ticket
    pr.update(flat)
    return pr


def ticket_divergences(pr):
    """Flat fields that disagree with the row's nested ticket (empty for a legacy row or a consistent
    ticket). The invariant `apply_ticket` exists to make impossible; tests and `validate` read it."""
    t = pr.get("ticket")
    if not isinstance(t, dict):
        return []
    flat = flatten_ticket(t)
    out = [(k, pr.get(k), v) for k, v in flat.items() if pr.get(k) != v]
    out += [(k, pr.get(k), None) for k in TICKET_SCRIPT_OWNED_FIELDS
            if k not in flat and pr.get(k) is not None]
    return out


def ticket_missing(direction, pr, rationale=None):
    """Required field names (TICKET_REQUIRED_FIELDS) that `pr` (flat view) lacks for this direction.
    HOLD and unknown directions require nothing."""
    need = TICKET_REQUIRED_FIELDS.get(str(direction or "").upper(), ())
    out = []
    for f in need:
        v = rationale if f == "rationale" else pr.get(f)
        if v is None or (isinstance(v, str) and not v.strip()):
            out.append(f)
    return out


def _same(a, b):
    if _num(a) is not None and _num(b) is not None:
        return abs(a - b) <= 0.011 + 1e-9 * abs(b)      # a cent: drafts and writes round independently
    return a == b


def script_owned_conflicts(canonical_flat, spec):
    """(field, spec_value, canonical_value) for every script-owned field the spec sets to something
    the ticket does not say. A spec value where the ticket has none also conflicts -- the strategist
    may not add a stop to a sell or a target to a hold. Also reads a nested `spec.ticket`."""
    supplied = {k: spec.get(k) for k in TICKET_SCRIPT_OWNED_FIELDS if spec.get(k) is not None}
    if isinstance(spec.get("ticket"), dict):
        for k, v in flatten_ticket(spec["ticket"]).items():
            if k in TICKET_SCRIPT_OWNED_FIELDS:
                supplied.setdefault(k, v)
    return [(k, v, canonical_flat.get(k)) for k, v in supplied.items()
            if not _same(v, canonical_flat.get(k))]
