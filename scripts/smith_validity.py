"""Is each open proposal still worth your attention? A per-run re-check (added 2026-09-19).

WHY. The user, looking at P-346 (Trim MU, HIGH) on the dashboard: the card was proposed at
$929 on 09-16; MU was $1,018 by 09-18 (+9.5% against SMH's +5.0%, so the trim had already cost
~4.5pp of alpha); the user had BOUGHT a share of MU on 09-18; the strategist had recommended
retiring it that morning; and the threat trigger it rested on had been narrowed by the desk.
The card showed none of that. It still said HIGH, still led with a paragraph of 09-16 rationale,
and offered Accept / Reject / Hold as equals. A proposal's rationale is written once; the world
it describes keeps moving, and nothing re-asked the question "is this still true?".

WHAT IT CHECKS, per open proposal, from data already on disk:
  * trigger_state   does the trigger family it rests on still fire on that ticker, per the
                    latest compute_triggers.json (which reads STAGED state, so desk revisions
                    count)
  * alpha since     the stock's move against SMH since the proposal's own anchors -- signed
                    so positive always means "the market has agreed with the proposal"
  * contradicted    a trade YOU made after the proposal in the opposite direction
  * desk_retire     the strategist's latest stale_proposal_retirements list, with its reason
  * thesis_conflict a BUY on a watch/broken thesis, or a TRIM/SELL on a strengthening one
  * desk debate     the latest desk debate on the ticker, and whether anything is unresolved
  * earnings_soon   a print inside 10 sessions
  * after_trade     share count, share of the position, and equity weight before -> after

VERDICT: retire | weakened | valid, with every reason listed. The proposal itself is never
edited: `status` and `priority` in proposals.json stay exactly as the engine wrote them, and
nothing here dismisses anything. The user decided (2026-09-19) that a retire verdict WAITS for
their click. What changes is what the dashboard and the briefing lead with, via
`effective_priority` -- a proposal the desk itself says to retire is not HIGH, whatever it was.
"""
import os
import re
from datetime import date

from smith_core import (LIVE_PROPOSAL_STATUSES, OWNER_VALIDITY, canonical_status, emit, load_json,
                        atomic_write_json, resolve_today, retirement_conditions)

# WHICH PROPOSALS GET RE-CHECKED (widened 2026-09-20, on the user's correction).
# `accepted_by_user` used to be exempt, because "accepted" was read as a standing instruction to
# execute. The user corrected that: an acceptance means "I agree with your reasoning AS OF THEN" --
# it is not an execution order, it does not expire into one, and it carries no obligation to trade
# later without re-checking whether the reasoning still holds. Exempting it was exactly backwards:
# an accepted proposal is MORE likely to be acted on, so a stale premise there is more dangerous,
# not less. The case that proved it: P-186 (Sell CIEN, accepted 2026-08-31) rested on a weak-guide
# overhang; CIEN reported a clean beat+raise on 2026-09-03 and its thesis flipped to
# `strengthening`. The premise died three days after acceptance and nothing re-asked for 20 days.
# `deferred` and `watch` USED to stay out ("explicitly 'not now' states that re-decide themselves
# each run"). Nothing re-decided them: five hand-written rows from July sat unchecked for two
# months. Phase 5 folded both into `open` (smith_core.STATUS_ALIASES) with `defer_until` carrying the
# "not now", so they are rechecked like any open row -- the comparison is by CANONICAL status.
RECHECKED_STATUSES = LIVE_PROPOSAL_STATUSES

# WHICH CONDITIONS THIS MODULE MAY ACT ON (smith_core.RETIREMENT_OWNERS). Judgmental or cross-source
# evidence only; it yields a VERDICT and never edits a proposal -- the user clicks. The mechanical
# facts (trigger no longer fires, expires_on passed, position gone, invalidation met) belong to
# cmd_proposals, which may auto-retire on them; a test asserts no condition is owned by both.
VERDICT_CONDITIONS = retirement_conditions(OWNER_VALIDITY)

ALPHA_AGAINST_PP = 3.0        # the market has moved this far against the proposal -> weakened
ALPHA_AGAINST_RETIRE_PP = 3.0  # ... and the trigger is gone too -> retire
STALE_SESSIONS = 10
EARNINGS_SOON_DAYS = 14        # calendar days, ~10 sessions
BUY_DIRS = ("BUY", "ADD")
SELL_DIRS = ("TRIM", "SELL")


def _read(path, default=None):
    try:
        return load_json(path, default=default)
    except Exception:  # noqa: BLE001 -- an unreadable input degrades one check, not the run
        return default


def _latest_run(base_dir):
    st = _read(os.path.join(base_dir, "state.json"), {}) or {}
    rd = st.get("latest_run_dir") or st.get("last_run_dir")
    return os.path.join(base_dir, rd) if rd else None


def _tickers_in(row):
    """Every ticker a trigger row names, whatever its shape (single or paired legs)."""
    out = set()
    if not isinstance(row, dict):
        return out
    for k in ("ticker", "t"):
        if isinstance(row.get(k), str):
            out.add(row[k])
    # Paired rotation rows (profit_rotation, cluster_rotation, laggard_rotation) nest their
    # tickers under `sell_leg`/`buy_leg`. Reading only `sell`/`buy` found NOTHING in them, so
    # every rotation-derived proposal was scored `trigger_state: not_firing` on the very run
    # that created it -- "its profit rotation trigger no longer fires on MU" about a proposal
    # the profit_rotation trigger had just produced. That silently demoted every rotation
    # proposal's effective_priority on the dashboard (found 2026-09-20).
    for leg in ("sell", "buy", "sell_leg", "buy_leg"):
        v = row.get(leg)
        if isinstance(v, dict):
            out |= _tickers_in(v)
    return out


def _sessions_between(d0, d1):
    """Weekdays strictly after d0 up to and including d1. Exchange holidays are ignored -- an
    age label off by one on a holiday week is harmless; one computed from calendar days is not
    (a Wednesday proposal read as 3 sessions old on the Saturday)."""
    from datetime import timedelta
    n, d = 0, d0
    while d < d1:
        d += timedelta(days=1)
        if d.weekday() < 5:
            n += 1
    return n


def _drops_off_when(p):
    """What retires this proposal, READ from the row -- never re-derived here. A ticket row's own
    `invalidation` is the single author (smith_ticket.build_invalidation); a pre-ticket row has only
    the legacy `retires_when` sentence cmd_proposals derived for it. Before Phase 5 this module, the
    trigger row and cmd_proposals each authored their own version of that sentence."""
    t = p.get("ticket") if isinstance(p.get("ticket"), dict) else {}
    return t.get("invalidation") or p.get("invalidation") or p.get("retires_when")


def check_one(p, ctx):
    tk = p.get("ticker")
    direction = (p.get("direction_bucket") or "").upper()
    reasons_retire, reasons_weak, against, notes = [], [], [], []
    cond_retire, cond_weak = [], []      # smith_core.RETIREMENT_OWNERS codes, parallel to the reasons
    try:
        d0 = date.fromisoformat(str(p.get("date") or "")[:10])
    except ValueError:
        d0 = None
    today = ctx["today"]

    # --- trigger still firing? ------------------------------------------------------
    fam = p.get("trigger_type")
    fam_rows = ctx["triggers"].get(fam) if fam else None
    if isinstance(fam_rows, list):
        live = any(tk in _tickers_in(r) for r in fam_rows)
        trigger_state = "firing" if live else "not_firing"
    else:
        trigger_state = "n/a"      # a judgment proposal with no trigger family behind it
    if trigger_state == "not_firing":
        # INFORMATIONAL here, not a verdict reason (Phase 5). "The trigger no longer fires on this
        # ticker" is an objective, ticker-level fact -- cmd_proposals owns it and retires on it
        # (trigger_no_longer_fires). It used to ALSO count as a `weakened` reason in this module, so
        # one fact was judged twice by two owners. What stays here is the judgment built ON it: the
        # compound below (trigger gone AND the market moved against the call).
        against.append(f"{fam.replace('_', ' ')} no longer fires on {tk} (recomputed this run)")

    # --- alpha since proposed -------------------------------------------------------
    px0, px1 = p.get("price_at_proposal"), ctx["price"].get(tk)
    b0, b1 = p.get("benchmark_price_at_proposal"), ctx["smh"]
    stock_pct = (px1 / px0 - 1) * 100 if (px0 and px1) else None
    bench_pct = (b1 / b0 - 1) * 100 if (b0 and b1) else None
    agree_pp = None
    if stock_pct is not None and bench_pct is not None:
        rel = stock_pct - bench_pct
        agree_pp = rel if direction in BUY_DIRS else -rel if direction in SELL_DIRS else None
    if agree_pp is not None and agree_pp <= -ALPHA_AGAINST_PP:
        reasons_weak.append(f"the market moved {abs(agree_pp):.1f}pp against it relative to SMH")
        cond_weak.append("alpha_against_proposal")
        against.append(f"{tk} {stock_pct:+.1f}% vs SMH {bench_pct:+.1f}% since proposed "
                       f"({abs(agree_pp):.1f}pp against the proposal)")
        if trigger_state == "not_firing" and agree_pp <= -ALPHA_AGAINST_RETIRE_PP:
            reasons_retire.append("trigger gone and the market has moved against it")
            cond_retire.append("trigger_gone_alpha_against")

    # --- contradicted by your own trade --------------------------------------------
    contra, acted = [], []
    if d0:
        for t in ctx["trades"]:
            if t.get("ticker") != tk or t.get("ca_type"):
                continue
            try:
                td = date.fromisoformat(str(t.get("date"))[:10])
            except ValueError:
                continue
            if td < d0:
                continue
            q = float(t.get("qty_change") or 0)
            if (direction in SELL_DIRS and q > 0) or (direction in BUY_DIRS and q < 0):
                contra.append(f"you {'bought' if q > 0 else 'sold'} {abs(q):g} {tk} on {td}")
            elif q:
                acted.append(f"you {'bought' if q > 0 else 'sold'} {abs(q):g} {tk} on {td}")
    if acted and not contra:
        # SAME direction after the proposal: you already did (some of) this. Not a contradiction
        # and not a desk miss -- but it is no longer a thing to decide.
        reasons_retire.append(acted[-1] + " -- already acted on")
        cond_retire.append("own_trade_same_direction")
    if contra:
        reasons_retire.append(contra[-1] + " -- the opposite of this proposal")
        cond_retire.append("own_trade_contradicts")
        against += contra[-2:]

    # --- the strategist's retirement list ------------------------------------------
    desk = ctx["retire"].get(p.get("id"))
    if desk:
        reasons_retire.append("the strategist recommends retiring it: " + desk[:300])
        cond_retire.append("strategist_retire_list")

    # --- thesis direction -----------------------------------------------------------
    th = ctx["thesis"].get(tk) if isinstance(ctx["thesis"].get(tk), dict) else {}
    status = th.get("status")
    if direction in BUY_DIRS and status in ("watch", "broken"):
        reasons_weak.append(f"buying into a `{status}` thesis")
        cond_weak.append("thesis_conflict")
    if direction in SELL_DIRS and status == "strengthening":
        reasons_weak.append("trimming a `strengthening` thesis")
        cond_weak.append("thesis_conflict")
    side = "evidence_against" if direction in BUY_DIRS else "evidence_for"
    for e in (th.get(side) or [])[:2]:
        if isinstance(e, dict) and e.get("claim"):
            against.append(f"thesis: {str(e['claim'])[:160]}")

    # --- desk debate on this ticker -------------------------------------------------
    debates = [d for d in ctx["debates"] if d.get("ticker") == tk]
    desk_line = None
    if debates:
        d = debates[-1]
        desk_line = f"{d['debate'].split('|')[0].replace('_', ' ')}: {d['outcome']}"
        if d["outcome"] == "unresolved":
            reasons_weak.append("an unresolved desk disagreement on this name")
            cond_weak.append("desk_unresolved")
    unresolved = [u for u in ctx["unresolved"] if u.get("ticker") == tk]
    if unresolved and not desk_line:
        desk_line = f"{len(unresolved)} unresolved desk question(s)"

    # --- earnings ------------------------------------------------------------------
    earn = None
    e = ctx["earnings"].get(tk) if isinstance(ctx["earnings"], dict) else None
    if isinstance(e, dict) and e.get("date"):
        try:
            ed = date.fromisoformat(str(e["date"])[:10])
            if 0 <= (ed - today).days <= EARNINGS_SOON_DAYS:
                earn = str(ed)
                against.append(f"earnings {ed} ({_sessions_between(today, ed)} sessions away)")
        except ValueError:
            pass

    # --- age -----------------------------------------------------------------------
    age = _sessions_between(d0, today) if d0 else None
    if age is not None and age >= STALE_SESSIONS:
        reasons_weak.append(f"{age} sessions old")
        cond_weak.append("age_sessions")

    # --- what the trade does -------------------------------------------------------
    pos = ctx["positions"].get(tk) or {}
    size = float(p.get("size_usd") or 0)
    after = {}
    if px1 and size:
        after["shares"] = round(size / px1, 4)
    if pos.get("value") and size:
        after["pct_of_position"] = round(size / pos["value"] * 100, 1)
    eq = ctx["equity"]
    if eq and size:
        v0 = pos.get("value") or 0.0
        if direction in SELL_DIRS:
            v1, e1 = max(0.0, v0 - size), eq - min(size, v0)
        else:
            v1, e1 = v0 + size, eq + size
        after["weight_before"] = round(v0 / eq * 100, 2)
        after["weight_after"] = round(v1 / e1 * 100, 2) if e1 else None

    verdict = "retire" if reasons_retire else "weakened" if reasons_weak else "valid"
    prio = p.get("priority")
    ladder = ["HIGH", "MEDIUM", "LOW"]
    if verdict == "retire":
        eff = "RETIRE"
    elif verdict == "weakened" and prio in ladder:
        eff = ladder[min(len(ladder) - 1, ladder.index(prio) + 1)]
    else:
        eff = prio

    # "Drops off when" -- met once the trigger it waits on has stopped firing
    drops_met = trigger_state == "not_firing"

    return {"id": p.get("id"), "ticker": tk, "direction": direction,
            "verdict": verdict, "effective_priority": eff, "priority": prio,
            "retire_because": reasons_retire, "weakened_because": reasons_weak,
            "retire_conditions": sorted(set(cond_retire)), "weakened_conditions": sorted(set(cond_weak)),
            "informational_conditions": (["earnings_proximity"] if earn else []),
            "trigger_state": trigger_state, "trigger": fam,
            "since": {"stock_pct": round(stock_pct, 2) if stock_pct is not None else None,
                      "smh_pct": round(bench_pct, 2) if bench_pct is not None else None,
                      "agree_pp": round(agree_pp, 2) if agree_pp is not None else None,
                      "price_now": px1},
            "against": against[:6], "contradicting_trades": contra, "acted_on": acted,
            "desk_retire_reason": desk, "thesis_status": status, "desk": desk_line,
            "earnings": earn, "age_sessions": age, "after_trade": after,
            "drops_off_when": _drops_off_when(p), "drops_off_met": drops_met,
            "ticket": bool(p.get("ticket_version"))}


def build_context(base_dir, run_dir=None, today=None):
    run_dir = run_dir or _latest_run(base_dir)
    st = _read(os.path.join(base_dir, "state.json"), {}) or {}
    trig = _read(os.path.join(run_dir, "compute_triggers.json"), {}) if run_dir else {}
    mi = _read(os.path.join(run_dir, "market_inputs.json"), {}) if run_dir else {}
    hold = _read(os.path.join(run_dir, "holdings.json"), {}) if run_dir else {}
    rows = (hold or {}).get("holdings_inr") or []
    usdinr = (hold or {}).get("usdinr") or 0
    price, positions, equity = {}, {}, 0.0
    for r in rows if isinstance(rows, list) else []:
        t = r.get("ticker")
        px = r.get("live_price_usd") or r.get("price_usd")
        if t and px:
            price[t] = float(px)
            val = float(r.get("qty") or 0) * float(px)
            positions[t] = {"value": val, "weight": r.get("weight_pct")}
            equity += val
    # names no longer held still need a price for their open BUY proposals
    bars = _read(os.path.join(base_dir, "perf_bars.json"), {}) or {}
    for t, series in bars.items():
        if t not in price and isinstance(series, list) and series:
            price[t] = float(series[-1]["c"])
    retire = {}
    so = _read(os.path.join(run_dir, "out_strategist.json"), {}) if run_dir else {}
    spr = (so or {}).get("stale_proposal_retirements") or {}
    rows_r = spr.get("retire_open_now") if isinstance(spr, dict) else spr
    for r in rows_r or []:
        if isinstance(r, dict) and r.get("id"):
            retire[r["id"]] = r.get("reason") or "recommended"
    for pid in (so or {}).get("stale_retire_open") or []:
        retire.setdefault(pid, "recommended")
    dg = _read(os.path.join(run_dir, "comms", "digest.json"), {}) if run_dir else {}
    return {"today": resolve_today(today), "triggers": trig or {},
            "smh": (mi or {}).get("smh") or (bars.get("SMH") or [{}])[-1].get("c"),
            "price": price, "positions": positions, "equity": equity or None,
            "trades": ((_read(os.path.join(base_dir, "trades.json"), {}) or {}).get("trades") or []),
            "retire": retire, "thesis": st.get("thesis") or {},
            "earnings": (st.get("data_cache") or {}).get("earnings_calendar") or {},
            "debates": (dg or {}).get("debates") or [],
            "unresolved": (dg or {}).get("unresolved") or [],
            "run_dir": run_dir, "usdinr": usdinr}


def check_all(base_dir, run_dir=None, today=None):
    ctx = build_context(base_dir, run_dir, today)
    props = ((_read(os.path.join(base_dir, "proposals.json"), {}) or {}).get("proposals") or [])
    rows = [check_one(p, ctx) for p in props if canonical_status(p) in RECHECKED_STATUSES]
    counts = {}
    for r in rows:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    return {"as_of": str(ctx["today"]), "run_dir": ctx["run_dir"], "counts": counts,
            "rows": rows,
            "note": ("advisory: proposals.json is not edited and nothing is dismissed. A `retire` "
                     "verdict waits for the user's click (user decision 2026-09-19).")}


def cmd_validity(args):
    out = check_all(args.base_dir, args.run_dir, args.today)
    if args.run_dir:
        atomic_write_json(os.path.join(args.run_dir, "compute_validity.json"), out)
        out["written"] = os.path.join(args.run_dir, "compute_validity.json")
    emit(out)
