"""FIFO lot accounting, corporate actions, and the authoritative trade-history lookup.

Split out of smith_math.py 2026-08-16: the file had reached 4,085 lines and mixed
four unrelated domains. Shared primitives live in smith_core; smith_math keeps the
per-run compute stages, the pipeline runner and the CLI, and imports these.
"""

import json
import os
from datetime import date, datetime

import smith_risk
from smith_core import *  # noqa: F401,F403 -- shared constants and IO helpers
from smith_core import load_json, emit


# Smallest share quantity any broker actually records. Below this a residual is float noise
# from summing decimal fractions, not a missing transaction -- reporting it as a phantom short
# produced a "shortfall_qty: 0.0" row that read as a real defect (2026-08-15).
SHARE_EPS = 1e-6

def _lot_sort_key(lot):
    """Oldest first. A lot with no date sorts FIRST -- synthetic pre-history lots from the
    2.9b backfill are by construction the oldest thing in the book, so consuming them first
    is both chronologically right and the conservative LTCG choice."""
    return (lot.get("date") or "0000-00-00", lot.get("price_usd") or 0)

def _consume_fifo(lot_list, qty, log, ticker, when):
    """Remove `qty` shares oldest-first. Returns (consumed_lots, shortfall).

    consumed_lots preserves each slice's original date and price so a conversion can carry
    them to the destination symbol. shortfall > 0 means the record claims more shares left
    than it ever recorded arriving -- surfaced, never silently floored at zero.
    """
    remaining, consumed = qty, []
    lot_list.sort(key=_lot_sort_key)
    while remaining > SHARE_EPS and lot_list:
        lot = lot_list[0]
        take = min(lot["qty"], remaining)
        consumed.append({"qty": take, "date": lot.get("date"), "price_usd": lot.get("price_usd")})
        lot["qty"] -= take
        remaining -= take
        if lot["qty"] <= SHARE_EPS:
            lot_list.pop(0)
    if remaining > SHARE_EPS:
        log.append({"ticker": ticker, "date": when, "shortfall_qty": round(remaining, 6),
                    "note": "sell/conversion consumed more shares than the record ever shows "
                            "arriving -- phantom short, NOT clamped to zero (G71 signature)"})
    return consumed, remaining

def _avg_cost_from_lots(tlots):
    """Weighted average cost over lots with a REAL price. Returns
    (avg_cost_usd, priced_qty, unpriced_qty). Synthetic null-price lots from the 2.9b backfill
    (quantity that predates available email history) are counted separately, never imputed --
    a ratchet computed against a guessed basis would move a real stop on a fabricated number."""
    cost, priced_qty, unpriced_qty = 0.0, 0.0, 0.0
    for lot in tlots or []:
        q = lot.get("qty") or 0.0
        px = lot.get("price_usd")
        if px is None:
            unpriced_qty += q
        else:
            cost += q * px
            priced_qty += q
    avg = (cost / priced_qty) if priced_qty else None
    return avg, priced_qty, unpriced_qty

def _months_between(d_iso, today):
    try:
        d = datetime.strptime(d_iso, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None
    return (today.year - d.year) * 12 + (today.month - d.month) + (today.day - d.day) / 30.44

def cmd_lots(args):
    """Rebuild lots.json from trades.json by deterministic FIFO, honouring corporate actions.

    CORPORATE-ACTION ROW SHAPE (in trades.json; a row with no `type` is a plain trade, so
    every one of the existing 803 rows keeps working unchanged):

      {"date":"2026-06-15", "type":"corporate_action", "ca_type":"conversion",
       "ticker":"GOOG", "qty_change":-3.0,          # shares leaving this symbol
       "to_ticker":"GOOGL", "to_qty":3.0,           # shares arriving at that one
       "ratio":null,                                # split only: new shares per old
       "price_at_trade":null,                       # corporate actions have no fill price
       "reason":"corporate_action",
       "source":"brokerage statement 2026-06",      # REQUIRED -- this data is not in email
       "notes":"GOOG->GOOGL share-class conversion"}

    ca_type semantics:
      conversion        move shares between symbols, CARRYING basis and acquisition date.
                        Not a taxable sale; the holding-period clock does not restart.
      split             multiply every open lot by `ratio`, divide its per-share price by the
                        same. Total basis and every acquisition date unchanged.
      fractional_credit shares appearing with no purchase (DRIP, fractional program). Basis is
                        `price_at_trade` if stated, else 0 -- and 0 is FLAGGED, because a
                        zero-basis lot overstates future gains if it is wrong.
      spinoff           like conversion but the source keeps its shares; destination lots are
                        created dated the spinoff, basis 0 unless stated.
      adjustment        an explicit, sourced reconciliation to broker truth when the cause is
                        genuinely unknown. The honest escape hatch: it records that a delta was
                        applied and why, instead of force-matching lots and pretending the
                        record was always right. Always shows up in the output.
    """
    trades = load_json(os.path.join(args.base_dir, "trades.json"), default={"trades": []})
    rows = list(trades.get("trades", []))
    rows.sort(key=lambda r: (r.get("date") or "", r.get("fill_time_utc") or ""))

    lots, shorts, applied_ca, warnings = {}, [], [], []

    # G80 DETECTOR (added 2026-08-15). Any quantity derived as Amount / Price is arithmetically
    # invalid, because INDmoney's Amount includes SEC/FINRA fees. Proven twice: a share-based
    # order (2026-06-22 META, Amount/Price = 1.002954, Shares field = 1) and a dollar-based one
    # (2025-04-30 GOOG, Amount/Price = 0.626330953, Shares field = 0.62453024). It inflates buys,
    # understates sells, and was the root cause of most of G68 and G79.
    #
    # The rule forbidding it lives in smith-ledger.md -- but a prose rule is exactly what lapsed
    # here in the first place, and that file had ALREADY contradicted itself on this point for
    # months. So the compute layer now names the offending rows on every run. Cheap, and it
    # cannot quietly stop being true.
    # Split known-and-accepted residue from a genuine relapse. The 24 rows predating the rule
    # hardening were quantified at ~$29 of basis error total (~$12 on live positions, 0.027% of
    # book) and deliberately left rather than spending 20+ confirmation pulls on twelve dollars.
    # A row dated AFTER the cutoff means the forbidden method is BACK, which is an alarm, not
    # residue -- so the two are reported differently and the alarm is impossible to mistake for
    # the accepted noise.
    G80_CUTOFF = "2026-08-15"
    derived = [r for r in rows if r.get("qty_source") == "derived_amount_over_price"]
    old_rows = [r for r in derived if (r.get("date") or "") < G80_CUTOFF]
    new_rows = [r for r in derived if (r.get("date") or "") >= G80_CUTOFF]
    if new_rows:
        warnings.append(
            f"G80 RELAPSE -- {len(new_rows)} row(s) dated on/after {G80_CUTOFF} were reconstructed "
            f"with the FORBIDDEN Amount/Price method: "
            + ", ".join(f"{r.get('ticker')} {r.get('date')}" for r in new_rows[:8])
            + ". Amount includes SEC/FINRA fees, so this is arithmetically invalid, not merely "
              "approximate. Re-pull each confirmation and read its `Shares:` field. Do NOT model a "
              "fee ratio -- that is the same error one level up. See smith-ledger.md task 2.")
    if old_rows:
        by_tk = {}
        for r in old_rows:
            by_tk[r.get("ticker")] = by_tk.get(r.get("ticker"), 0) + 1
        warnings.append(
            f"G80 accepted residue: {len(old_rows)} pre-{G80_CUTOFF} row(s) still carry the old "
            f"Amount/Price derivation ("
            + ", ".join(f"{k} x{v}" for k, v in sorted(by_tk.items(), key=lambda kv: -kv[1]))
            + "). Quantified at ~$29 of cost-basis error in total, ~$12 of it on live positions "
              "(0.027% of book) -- knowingly left, not overlooked. Informational.")

    for r in rows:
        tk = r.get("ticker")
        if not tk:
            continue
        when = r.get("date")
        lots.setdefault(tk, [])
        rtype = r.get("type", "trade")

        if rtype != "corporate_action":
            q = r.get("qty_change") or 0
            if q > 0:
                lots[tk].append({"qty": q, "date": when, "price_usd": r.get("price_at_trade"),
                                 "price_source": r.get("price_source") or "trade"})
            elif q < 0:
                _consume_fifo(lots[tk], -q, shorts, tk, when)
            continue

        ca = r.get("ca_type")
        if ca not in CA_TYPES:
            warnings.append(f"{tk} {when}: unknown ca_type {ca!r} -- row ignored, nothing applied")
            continue
        if not r.get("source"):
            warnings.append(f"{tk} {when}: corporate action has no `source` -- this data cannot "
                            f"come from email, so an unsourced row is unverifiable")

        if ca == "split":
            ratio = r.get("ratio")
            if not ratio or ratio <= 0:
                warnings.append(f"{tk} {when}: split needs a positive `ratio` -- row ignored")
                continue
            for lot in lots[tk]:
                lot["qty"] *= ratio
                if lot.get("price_usd"):
                    lot["price_usd"] = lot["price_usd"] / ratio
            applied_ca.append({"date": when, "ca_type": ca, "ticker": tk, "ratio": ratio,
                               "note": "qty scaled, per-share basis inversely scaled; total "
                                       "basis and all acquisition dates preserved"})

        elif ca in ("conversion", "spinoff"):
            dst = r.get("to_ticker")
            if not dst:
                warnings.append(f"{tk} {when}: {ca} needs `to_ticker` -- row ignored")
                continue
            lots.setdefault(dst, [])
            out_q = abs(r.get("qty_change") or 0)
            in_q = r.get("to_qty")
            if in_q is None:
                in_q = out_q
            if ca == "conversion":
                moved, short = _consume_fifo(lots[tk], out_q, shorts, tk, when)
                got = sum(m["qty"] for m in moved)
                scale = (in_q / got) if got > 1e-9 else 1.0
                for m in moved:
                    # basis and acquisition date CARRY -- a conversion is not a purchase
                    lots[dst].append({
                        "qty": m["qty"] * scale,
                        "date": m["date"],
                        "price_usd": (m["price_usd"] / scale) if m.get("price_usd") and scale else m.get("price_usd"),
                        "price_source": "carried_through_conversion"})
                applied_ca.append({"date": when, "ca_type": ca, "from": tk, "to": dst,
                                   "qty_out": round(got, 6), "qty_in": round(in_q, 6),
                                   "shortfall": round(short, 6) if short else 0,
                                   "note": "basis and acquisition dates carried; LTCG clock NOT reset"})
            else:  # spinoff -- source keeps its shares
                lots[dst].append({"qty": in_q, "date": when,
                                  "price_usd": r.get("price_at_trade"),
                                  "price_source": "spinoff"})
                applied_ca.append({"date": when, "ca_type": ca, "from": tk, "to": dst,
                                   "qty_in": in_q,
                                   "note": "source position unchanged; destination dated the spinoff"})

        elif ca == "fractional_credit":
            q = r.get("qty_change") or 0
            px = r.get("price_at_trade")
            lots[tk].append({"qty": q, "date": when, "price_usd": px,
                             "price_source": "fractional_credit"})
            if px is None:
                warnings.append(f"{tk} {when}: fractional_credit has no price -- lot carries a "
                                f"null basis, which understates cost and overstates future gain")
            applied_ca.append({"date": when, "ca_type": ca, "ticker": tk, "qty": q})

        elif ca == "adjustment":
            q = r.get("qty_change") or 0
            if q > 0:
                lots[tk].append({"qty": q, "date": when, "price_usd": r.get("price_at_trade"),
                                 "price_source": "adjustment"})
            elif q < 0:
                _consume_fifo(lots[tk], -q, shorts, tk, when)
            applied_ca.append({"date": when, "ca_type": ca, "ticker": tk, "qty": q,
                               "source": r.get("source"), "notes": r.get("notes"),
                               "note": "EXPLICIT reconciliation to broker truth -- recorded, "
                                       "not force-matched"})

    # tidy
    out = {}
    for tk, ls in lots.items():
        keep = [{k: (round(v, 6) if isinstance(v, float) else v) for k, v in lot.items()}
                for lot in ls if lot["qty"] > 1e-9]
        if keep:
            keep.sort(key=_lot_sort_key)
            out[tk] = keep

    # reconcile against the broker, if a run's holdings were supplied
    recon, mismatches = None, []
    if args.holdings:
        h = load_json(args.holdings, default={})
        live = {r["ticker"]: r.get("qty") for r in h.get("holdings_inr", [])}
        for tk, q in live.items():
            ls = round(sum(l["qty"] for l in out.get(tk, [])), 6)
            if abs(ls - (q or 0)) > 1e-4:
                mismatches.append({"ticker": tk, "lots_sum": ls, "broker_qty": q,
                                   "delta": round(ls - (q or 0), 6)})
        # ALSO check the other direction (added during the 2026-08-15 cutover). The loop above
        # only walks tickers the broker reports, so a ticker the LEDGER thinks is still open
        # while the broker shows NO position at all was invisible -- and that is the more
        # alarming case, because it means a sell is missing entirely rather than partially.
        # The cutover surfaced PLTR carrying ~5.0sh across five lots and META ~1.0sh, both
        # fully exited per the broker. Neither would have been reported without this.
        orphans = []
        for tk, ls in out.items():
            if tk in live:
                continue
            q = round(sum(l["qty"] for l in ls), 6)
            # TWO TIERS (added 2026-08-17). The single >1e-4 threshold hid a real finding: LLY
            # carried 0.000004sh across one lot for a name the broker does not hold, invisible
            # because it sat between SHARE_EPS and the orphan bar. Its cause was diagnostic --
            # bought 0.106681, sold 0.106677, with the SELL derived via the FORBIDDEN
            # Amount/Price method (G80), which is arithmetically wrong because Amount includes
            # SEC/FINRA fees. So the dust was not rounding; it was the known-bad derivation
            # leaving residue. A material orphan is an ALARM (a sell missing outright); a dust
            # orphan is RESIDUE. Both must be visible, framed differently, neither swept away.
            if q > 1e-4:
                orphans.append({"ticker": tk, "lots_sum": q, "broker_qty": 0, "lots": len(ls),
                                "severity": "material",
                                "note": "ledger shows an open position the broker does not report "
                                        "-- a sell is missing from the trade record entirely"})
            elif q > SHARE_EPS:
                orphans.append({"ticker": tk, "lots_sum": q, "broker_qty": 0, "lots": len(ls),
                                "severity": "dust",
                                "note": "sub-0.0001sh residue on a name the broker does not hold. "
                                        "Almost always a qty_source=derived_amount_over_price sell "
                                        "(G80) that under-consumed the position. Not a valuation "
                                        "risk, but it inflates the ticker count and will confuse "
                                        "any consumer that trusts lots.json's key set -- clear it "
                                        "with a sourced `adjustment` row, do not silently drop it."})
        recon = {"tickers_checked": len(live), "reconciled": len(live) - len(mismatches),
                 "mismatches": sorted(mismatches, key=lambda m: -abs(m["delta"])),
                 "orphaned_positions": sorted(orphans, key=lambda o: -o["lots_sum"])}

    # --write-if-clean: the sanctioned way to keep lots.json current automatically (added
    # 2026-08-31, lots-engine cutover formally adopted). The cutover itself was already de facto
    # complete -- lots.json has carried this engine's own `_rebuilt` header since 2026-08-29, and
    # a fresh run reproduces it exactly: 35/35 tickers, 74/74 lots, identical qty/date/price, all
    # 74 retaining email_confirmed provenance, reconciling 35/35 against broker quantities with
    # zero mismatches, orphans or phantom shorts. What was missing was not confidence in the
    # engine but any code path that RE-RAN it, so lots.json drifted from trades.json until a
    # human remembered -- the same write-path-with-no-refresh shape as the dark technical caches.
    #
    # Reconcile-FIRST, never a blind auto-write. The engine faithfully propagates whatever
    # trades.json says, and G83 is live evidence the trade record can carry a wrong date (BX
    # dated 2026-08-21 there against 2026-08-24 in state). So this writes ONLY when the rebuild
    # reconciles cleanly against broker quantities, and otherwise leaves the existing file
    # untouched and says why -- a silent overwrite on a bad trade record is exactly how the P&L
    # spine gets corrupted, and that spine is where every serious incident in this system has
    # lived (G3, G64, G71).
    write_blocked = None
    if getattr(args, "write_if_clean", False):
        if recon is None:
            write_blocked = ("--write-if-clean requires --holdings: without broker quantities "
                             "there is nothing to reconcile against, and an unreconciled "
                             "rebuild must never overwrite the lots spine")
        elif recon["mismatches"] or recon["orphaned_positions"] or shorts:
            write_blocked = (f"reconciliation not clean -- {len(recon['mismatches'])} mismatch(es), "
                             f"{len(recon['orphaned_positions'])} orphan(s), {len(shorts)} phantom "
                             f"short(s). lots.json left exactly as it was; fix trades.json first.")
        else:
            args.write = True

    written = None
    if args.write:
        path = os.path.join(args.base_dir, "lots.json")
        prev = load_json(path, default={})
        payload = {"schema_version": prev.get("schema_version", 1),
                   "_note": ("Rebuilt deterministically by `smith_math.py lots` from trades.json. "
                             "Do NOT hand-edit: re-running the engine overwrites it. Record "
                             "share-moving events that generate no buy/sell confirmation as "
                             "corporate_action rows in trades.json instead."),
                   "_rebuilt": str(date.today())}
        payload.update(out)
        safe_write(path, payload)
        written = path

    emit({"tickers": len(out),
          "total_lots": sum(len(v) for v in out.values()),
          "corporate_actions_applied": applied_ca,
          "phantom_shorts": shorts,
          "reconciliation": recon,
          "warnings": warnings,
          "written": written,
          "write_blocked": write_blocked,
          "note": ("phantom_shorts are sells/conversions that consumed more than the record shows "
                   "arriving -- surfaced rather than clamped to zero. A non-empty list means the "
                   "trade record is missing share-creating events (see G68/G71).")})

def cmd_history(args):
    """Authoritative 'was this ever held?' lookup, sourced from trades.json (G72).

    Built because the orchestrator told the user LITE was "never actually held" when the
    ledger carried 22 LITE trades. The false answer came from reading silence in
    state.thesis / state.signal_history as proof of absence -- but both are seeded from
    CURRENT holdings, so a fully-exited name is ALWAYS silent there. Absence of evidence in
    those two files is not evidence of absence; trades.json is the only file that can answer
    this, because it is the only one that records positions that no longer exist.
    """
    trades = load_json(os.path.join(args.base_dir, "trades.json"), default={"trades": []}).get("trades", [])
    state = load_json(os.path.join(args.base_dir, "state.json"), default={})
    lots = load_json(os.path.join(args.base_dir, "lots.json"), default={})
    # lots.json keys tickers at the TOP level; the metadata keys start with "_" or are scalars.
    holdings_now = {t for t, v in smith_risk.data_entries(lots, value_type=list)
                    if sum((l.get("qty") or 0) for l in v) > SHARE_EPS}

    out = {}
    for tk in [t.strip().upper() for t in args.ticker.split(",") if t.strip()]:
        rows = sorted([r for r in trades if (r.get("ticker") or "").upper() == tk],
                      key=lambda r: (r.get("date") or "", r.get("fill_time_utc") or ""))
        if not rows:
            out[tk] = {"ever_held": False, "trade_count": 0,
                       "answer": f"{tk}: no trade of any kind in the ledger. Never held.",
                       "caveat": "Absence here is meaningful ONLY because trades.json is the "
                                 "authoritative record. Never answer this from state.thesis."}
            continue
        buys = [r for r in rows if (r.get("qty_change") or 0) > 0]
        sells = [r for r in rows if (r.get("qty_change") or 0) < 0]
        cas = [r for r in rows if r.get("type") == "corporate_action"]
        net = sum(r.get("qty_change") or 0 for r in rows)
        peak, run = 0.0, 0.0
        for r in rows:
            run += r.get("qty_change") or 0
            peak = max(peak, run)
        held = tk in holdings_now
        out[tk] = {
            "ever_held": True, "currently_held": held,
            "trade_count": len(rows), "buys": len(buys), "sells": len(sells),
            "corporate_actions": len(cas),
            "first_trade": rows[0].get("date"), "last_trade": rows[-1].get("date"),
            "peak_qty": round(peak, 6), "net_qty_now": round(net, 6),
            "answer": (f"{tk}: HELD SINCE {rows[0].get('date')} -- {len(rows)} trades "
                       f"({len(buys)} buys, {len(sells)} sells), peak {round(peak, 4)} shares."
                       if held else
                       f"{tk}: WAS held and is now EXITED -- {len(rows)} trades between "
                       f"{rows[0].get('date')} and {rows[-1].get('date')} "
                       f"({len(buys)} buys, {len(sells)} sells), peak {round(peak, 4)} shares."),
        }
    emit({"generated": str(date.today()), "source": "trades.json + lots.json",
          "tickers": out,
          "note": ("G72 fix. state.thesis and state.signal_history are seeded from CURRENT "
                   "holdings, so an exited name is silent in both by construction. Answer "
                   "'was this ever held' from THIS command only.")})


# ---------------------------------------------------------------------------
# UNIVERSE (added 2026-08-30) -- the candidate set the desk is allowed to reason over
# ---------------------------------------------------------------------------
# Built because idea sourcing had no funnel. A proposal could only ever name a currently-held
# ticker, an INDmoney watchlist name, or a name exited within the last 20 trading days (the
# `reentry` trigger's expiry). Everything else was invisible BY CONSTRUCTION -- including the
# 35 distinct tickers this book has traded and no longer holds, sitting in trades.json, which
# is the one file that records positions that no longer exist (the G72 lesson, one level up:
# a source that cannot represent a thing cannot be used to rule it out, and a funnel that
# cannot see a name cannot propose it).
#
# The tiers are SEEDS OF STATED INTEREST, not a fence. T1-T4 are names the user has already
# demonstrated interest in by holding, having held, holding a peer of, or watchlisting. T5 is
# how genuinely new names get in, capped and weekly, because a book that can only re-rank what
# it already owns stays single-factor by construction.
#
# Deterministic and network-free, like every other compute stage: everything here is already
# on disk. T3 needs data_cache.etf_constituents seeded for the ETFs peer_map references --
# without it, "peers of what I hold" is simply not derivable, which was the state on the day
# this was written (etf_constituents held DRAM and EWY; peer_map referenced SMH, XLK, XLU,
# XLF and REMX).

UNIVERSE_TIERS = ("T1_HELD", "T2_ALUMNI", "T3_PEERS", "T4_WATCHLIST", "T5_MARKET")


def cmd_universe(args):
    base = args.base_dir
    trades = load_json(os.path.join(base, "trades.json"), default={"trades": []}).get("trades", [])
    state = load_json(os.path.join(base, "state.json"), default={})
    dc = state.get("data_cache", {}) or {}

    holdings = []
    if getattr(args, "run_dir", None):
        holdings = load_json(os.path.join(args.run_dir, "holdings.json"),
                             default={}).get("holdings_inr", []) or []
    held = {(h.get("ticker") or "").upper() for h in holdings if h.get("ticker")}
    if not held:  # standalone invocation with no run dir -- fall back to the lot file
        lots = load_json(os.path.join(base, "lots.json"), default={})
        held = {t for t, v in smith_risk.data_entries(lots, value_type=list)
                if sum((l.get("qty") or 0) for l in v) > SHARE_EPS}

    # --- per-ticker trade history, one pass over the ledger ---
    hist = {}
    for r in trades:
        tk = (r.get("ticker") or "").upper()
        if not tk:
            continue
        h = hist.setdefault(tk, {"first": None, "last": None, "n": 0, "last_sell": None})
        d = r.get("date")
        h["n"] += 1
        if d:
            h["first"] = min(h["first"], d) if h["first"] else d
            h["last"] = max(h["last"], d) if h["last"] else d
            if (r.get("qty_change") or 0) < 0:
                h["last_sell"] = max(h["last_sell"], d) if h["last_sell"] else d

    sector_map = state.get("sector_map", {}) or {}
    peer_map = state.get("peer_map", {}) or {}
    wl_suppressed = state.get("watchlist_suppressed", {}) or {}
    scr_suppressed = state.get("screener_suppressed", {}) or {}

    watchlist = {(t or "").upper() for t in (state.get("watchlist_universe") or [])}
    watchlist |= {(s.get("ticker") or "").upper()
                  for s in (state.get("watchlist_setups") or []) if s.get("ticker")}
    watchlist |= {(t or "").upper() for t in (state.get("diversifier_candidates") or {})}
    watchlist.discard("")

    # T3: constituents of the peer ETFs the book's own names map to. Not "the whole market" --
    # the ETFs are chosen by peer_map, which is itself derived from what is held.
    peer_etfs = sorted({(v or {}).get("peer_etf") for v in peer_map.values()
                        if isinstance(v, dict) and (v or {}).get("peer_etf")})
    etf_cache = dc.get("etf_constituents", {}) or {}
    peers, peer_source = {}, {}
    for etf in peer_etfs:
        entry = etf_cache.get(etf) or {}
        for tk in (entry.get("constituents") or []):
            tk = (tk or "").upper()
            if tk:
                peers.setdefault(tk, etf)
    peer_source = peers

    market = {(t or "").upper() for t in (state.get("screener_candidates") or {})}
    market.discard("")

    # Tier precedence: strongest claim wins. A held name is T1 even though it is also its own
    # peer; an alumnus is T2 even if it is also watchlisted, because "you owned this once" is
    # a stronger statement of interest than "you listed it".
    rows, seen = [], set()
    def add(tk, tier):
        if not tk or tk in seen:
            return
        seen.add(tk)
        h = hist.get(tk, {})
        ever = bool(h.get("n"))
        rows.append({
            "ticker": tk,
            "tier": tier,
            "cluster": sector_map.get(tk),
            "ever_held": ever,
            "trade_count": h.get("n", 0),
            "first_trade": h.get("first"),
            "last_trade": h.get("last"),
            # For an alumnus this is when the position was closed out, which is the context a
            # re-entry rationale needs. It is CONTEXT, never an eligibility gate -- see the
            # note on `reentry`'s retired expiry below.
            "last_held_date": None if tier == "T1_HELD" else h.get("last_sell") or h.get("last"),
            "in_watchlist": tk in watchlist,
            "peer_of_etf": peer_source.get(tk),
            "suppressed": (tk in wl_suppressed) or (tk in scr_suppressed),
            "suppressed_reason": (wl_suppressed.get(tk) or scr_suppressed.get(tk) or {}).get("reason"),
        })

    for tk in sorted(held):
        add(tk, "T1_HELD")
    for tk in sorted(set(hist) - held):
        add(tk, "T2_ALUMNI")
    for tk in sorted(watchlist):
        add(tk, "T4_WATCHLIST")
    for tk in sorted(peers):
        add(tk, "T3_PEERS")
    for tk in sorted(market):
        add(tk, "T5_MARKET")

    counts = {t: sum(1 for r in rows if r["tier"] == t) for t in UNIVERSE_TIERS}
    dq = []
    missing_etfs = [e for e in peer_etfs if not (etf_cache.get(e) or {}).get("constituents")]
    if missing_etfs:
        dq.append(f"T3_PEERS is empty or partial: data_cache.etf_constituents has no "
                  f"constituents for {', '.join(missing_etfs)}, which peer_map references. "
                  f"Seed them (30-day TTL) or 'peers of what I hold' is not derivable at all.")
    if not watchlist:
        dq.append("T4_WATCHLIST is empty -- state.watchlist_universe unset and no live setups. "
                  "smith-watchlist should persist the full INDmoney list, not only its setups.")
    if not market:
        dq.append("T5_MARKET is empty -- no screener_candidates persisted. Expected on any run "
                  "that is not the weekly discovery sweep; not a defect on a daily run.")

    emit({"as_of": (args.today or str(date.today())),
          "counts": counts,
          "total": len(rows),
          "suppressed_count": sum(1 for r in rows if r["suppressed"]),
          "peer_etfs_referenced": peer_etfs,
          "tickers": rows,
          "data_quality": dq,
          "note": ("Tiers are seeds of stated interest, not a fence. Tier precedence on "
                   "overlap: T1 > T2 > T4 > T3 > T5. `last_held_date` is CONTEXT for a "
                   "re-entry rationale, never an eligibility gate -- an ever-held name stays "
                   "in the universe permanently.")})


# ---------------------------------------------------------------------------
# LEDGER PARSE (added 2026-09-06) -- the deterministic half of smith-ledger
# ---------------------------------------------------------------------------
# WHY. smith-ledger cost 107,874 tokens and 24 tool calls on the 2026-09-06 deep run, the
# second-largest agent in the fleet and by far the heaviest in tool use, to record SEVEN fills.
# Almost none of that was judgment: INDmoney confirmations are a rigid template, and pulling
# `Shares:`/`Price:`/`Order Type:` out of one is regex work, not reasoning.
#
# THE MEASUREMENT THAT DROVE THIS, and it contradicts the agent's own standing rule. Its file
# said the search snippet "truncates before Shares:/Order Type: on close to every one of these
# confirmations -- that is not occasional, it is the normal case", and therefore instructed a
# `get_thread` for EVERY confirmation as a planned batch. Measured against the same 7 rows:
#
#     ticker  Shares in snippet?   Order Type in snippet?
#     AMD     NO                   no
#     APH     yes (10)             partial
#     ASML    yes (0.25)           partial
#     COHR    yes (1)              yes (Market)
#     KLAC    yes (1)              yes (Market)
#     GLW     yes (2)              yes (stop)
#     GLW     yes (3)              yes (stop)
#
# SIX OF SEVEN carried the quantity, and BOTH stop-sells -- the only rows where Order Type
# changes anything -- carried it too. The snippet is a fixed-length field, so whether `Shares:`
# survives depends on how long the company NAME is (it appears twice before that point);
# "Advanced Micro Devices Inc." is what pushed AMD past the cut. One body fetch was needed, not
# seven. A blanket rule was written from a few long-named examples and cost ~7x its value on
# every run since.
#
# THE SELF-CHECK THAT MAKES THIS SAFE. Amount == Shares x Price exactly, plus a broker fee that
# is 0.30% on buys and 0.00% on sells -- verified across all seven rows to three decimals. So a
# parse is not trusted because a regex matched; it is trusted because three independently
# extracted numbers reconcile. Any row failing that is a parse failure, never a trade.
#
# WHAT STAYS WITH THE AGENT: a body that does not match the template, an extraction that
# disagrees with an existing trades.json row, corporate actions, and phantom shorts. Those are
# the exceptions, and the agent should be dispatched only when this reports one.

LEDGER_FEE_PCT = {"BUY": 0.30, "SELL": 0.0}   # measured 2026-09-06 across 7 confirmations
LEDGER_FEE_TOL_PCT = 0.25                     # how far from the expected fee before we refuse
_LED_FIELDS = {
    "amount": r"Amount:\s*\$?\s*([0-9][0-9,]*\.?[0-9]*)",
    "price":  r"Price:\s*\$?\s*([0-9][0-9,]*\.?[0-9]*)",
    "shares": r"Shares:\s*([0-9]*\.?[0-9]+)",
    "order_type": r"Order Type:\s*([A-Za-z ]+?)(?:\s+US\b|\s+a/c|$)",
    "name": r"Ticker:\s*(.+?)\s+Amount:",
}


def _led_num(s):
    try:
        return float(str(s).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def _led_extract(text):
    import re
    out = {}
    for k, pat in _LED_FIELDS.items():
        m = re.search(pat, text or "")
        out[k] = m.group(1).strip() if m else None
    return out


def _led_side(subject, text):
    blob = f"{subject or ''} {text or ''}".upper()
    if "SELL ORDER" in blob:
        return "SELL"
    if "BUY ORDER" in blob:
        return "BUY"
    return None


def cmd_ledger_parse(args):
    """Parse INDmoney BUY/SELL confirmations deterministically from search_threads output.

    --threads-file : the raw search_threads JSON (a dict with "threads", or a LIST of such
                     dicts when several pages were fetched -- pass every page, order irrelevant).
    --bodies-file  : optional. get_thread results for the rows a previous invocation listed in
                     `needs_body`. Same shape tolerance. Bodies WIN over snippets on conflict,
                     because a body is complete and a snippet is truncated by construction.

    Emits `parsed` (ready to append), `needs_body` (fetch ONLY these), `excluded_cancelled`,
    `unresolved_ticker` and `failed_validation`. Dispatch smith-ledger only if any of the last
    two are non-empty, or a body still will not parse.
    """
    state = load_json(os.path.join(args.base_dir, "state.json"), default={}) or {}
    tmap = (state.get("data_cache", {}) or {}).get("ticker_map", {}) or {}
    # name -> ticker, matched case/punctuation-insensitively. NEVER infer a ticker from text.
    norm = {}
    for nm, tk in tmap.items():
        if isinstance(tk, str):
            norm[_led_norm_name(nm)] = tk
    aliases = {_led_norm_name(k): v for k, v in
               ((state.get("data_cache", {}) or {}).get("ticker_map_email_aliases", {}) or {}).items()
               if isinstance(v, str)}

    def collect(path):
        raw = load_json(path, default=None) if path else None
        if raw is None:
            return []
        pages = raw if isinstance(raw, list) else [raw]
        msgs = []
        for pg in pages:
            for th in (pg.get("threads") or []) if isinstance(pg, dict) else []:
                for m in th.get("messages") or []:
                    msgs.append(m)
        return msgs

    by_id = {}
    for m in collect(args.threads_file):
        by_id.setdefault(m.get("id"), dict(m, _src="snippet"))
    for m in collect(args.bodies_file):          # bodies override snippets
        if m.get("id"):
            prev = by_id.get(m["id"], {})
            by_id[m["id"]] = dict(prev, **m, _src="body")

    parsed, needs_body, cancelled, unresolved, failed = [], [], [], [], []
    alias_suggestions = {}
    for mid, m in sorted(by_id.items(), key=lambda kv: kv[1].get("internalDate") or ""):
        subject = m.get("subject") or ""
        text = m.get("plaintextBody") or m.get("plaintext_body") or m.get("snippet") or ""
        blob = f"{subject} {text}"
        if "is cancelled" in blob.lower() or "cancelled" in subject.lower():
            cancelled.append({"id": mid, "subject": subject})
            continue
        side = _led_side(subject, text)
        f = _led_extract(text)
        name = f.get("name")
        ticker, how = _led_resolve(name, norm, aliases)
        amount, price, shares = (_led_num(f["amount"]), _led_num(f["price"]),
                                 _led_num(f["shares"]))

        missing = [k for k, v in (("side", side), ("amount", amount), ("price", price),
                                  ("shares", shares)) if v is None]
        # Order Type is only load-bearing when it might be `stop`; a truncated one on a row we
        # otherwise resolved still needs the body, because "reason" must never be guessed.
        if f.get("order_type") is None:
            missing.append("order_type")
        if missing:
            if m.get("_src") == "body":
                failed.append({"id": mid, "subject": subject, "missing": missing,
                               "note": "full body fetched and STILL unparseable -- template may "
                                       "have changed; smith-ledger must handle this row"})
            else:
                needs_body.append({"id": mid, "thread_id": m.get("threadId") or mid,
                                   "subject": subject, "missing": missing,
                                   "note": "snippet truncated before these fields -- "
                                           "get_thread (PLAIN_TEXT) this one"})
            continue
        if not ticker:
            unresolved.append({"id": mid, "name": name, "subject": subject, "reason": how,
                               "note": "could not resolve this display name to a ticker SAFELY. "
                                       "Resolve it properly and cache it under "
                                       "data_cache.ticker_map_email_aliases; never infer from "
                                       "the name (TICKER INTEGRITY)."})
            continue
        if how == "unique_prefix":
            alias_suggestions[name] = ticker

        gross = shares * price
        fee_pct = round((amount - gross) / gross * 100, 3) if gross else None
        expected = LEDGER_FEE_PCT.get(side, 0.0)
        if fee_pct is None or abs(fee_pct - expected) > LEDGER_FEE_TOL_PCT:
            failed.append({"id": mid, "ticker": ticker, "side": side, "amount": amount,
                           "price": price, "shares": shares, "implied_fee_pct": fee_pct,
                           "expected_fee_pct": expected,
                           "note": "Amount != Shares x Price within the expected broker fee. "
                                   "Three independently extracted numbers do not reconcile, so "
                                   "this is a PARSE failure, not a trade. Do not append it."})
            continue

        ot = (f.get("order_type") or "").strip().lower()
        parsed.append({
            "date": (m.get("date") or "")[:10],
            "ts_utc": m.get("date"),
            "ticker": ticker, "name": name, "side": side,
            "action": "add" if side == "BUY" else "trim",
            "qty": shares, "price_usd": price, "amount_usd": amount,
            "order_type": ot, "implied_fee_pct": fee_pct, "ticker_resolved_by": how,
            "price_source": "email_confirmed",
            # Objective, never inferred: only a literal `stop` sets a reason here.
            "reason": "stop-loss" if ot == "stop" else "UNCAPTURED",
            "message_id": mid, "extracted_from": m.get("_src"),
        })

    emit({"parsed": parsed, "parsed_count": len(parsed),
          "needs_body": needs_body, "needs_body_count": len(needs_body),
          "excluded_cancelled": cancelled, "unresolved_ticker": unresolved,
          "failed_validation": failed, "alias_suggestions": alias_suggestions,
          "dispatch_agent": bool(unresolved or failed),
          "snippet_sufficiency_pct": (round(100.0 * len(parsed) / max(1, len(parsed) + len(needs_body)), 1)
                                      if args.bodies_file is None else None),
          "note": ("Every parsed row reconciles Amount == Shares x Price within the expected "
                   "broker fee (0.30% buy / 0.00% sell, measured 2026-09-06). Fetch bodies ONLY "
                   "for needs_body, then re-run with --bodies-file. Dispatch smith-ledger only "
                   "when dispatch_agent is true.")})


def _led_resolve(name, norm, aliases):
    """(ticker, how). Resolve an email display name to a ticker WITHOUT inferring one.

    TICKER INTEGRITY is a hard rule with a real incident behind it, so this fails closed. The
    problem is that ticker_map holds broker long-names ("Corning Incorporated", "ASML Holding
    N.V. New York Registry Shares") while the confirmation emails use short forms ("Corning
    Inc.", "ASML Holding NV"), so exact matching resolves almost nothing.

    Three tiers, in order, and NONE of them guesses:
      exact        -- normalized names identical.
      alias        -- a previously CONFIRMED email-name mapping, cached in
                      data_cache.ticker_map_email_aliases. Once written, resolution is a stored
                      fact rather than a match, which is what the integrity rule actually wants.
      unique_prefix-- the normalized email name is a prefix of EXACTLY ONE map key. Uniqueness
                      is the whole safety property: "Alphabet Inc." is a prefix of BOTH
                      "Alphabet Inc. Class C Capital Stock" (GOOG) and "Alphabet Inc. Class A
                      Common Stock" (GOOGL), so it resolves to NOTHING and goes to
                      unresolved -- exactly the GOOG/GOOGL confusion that must never happen
                      silently. Every prefix match is reported as `ticker_resolved_by:
                      "unique_prefix"` and echoed in `alias_suggestions` so it can be promoted
                      to a cached alias and stop being a match at all.
    """
    if not name:
        return None, "no_name_in_email"
    n = _led_norm_name(name)
    if n in norm:
        return norm[n], "exact"
    if n in aliases:
        return aliases[n], "alias"
    hits = {tk for key, tk in norm.items() if key.startswith(n) or n.startswith(key)}
    if len(hits) == 1:
        return hits.pop(), "unique_prefix"
    if len(hits) > 1:
        return None, f"ambiguous_prefix ({len(hits)} candidates: {sorted(hits)})"
    return None, "no_candidate"


def _led_norm_name(s):
    import re
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def cmd_ledger_apply(args):
    """Append parsed confirmations to trades.json. Deterministic, idempotent, WRITE-SAFE.

    Completes the script-first ledger path: with this, a normal run's fills go from Gmail to
    trades.json without an LLM touching the write. The agent is for exceptions only.

    IDEMPOTENT ON `message_id`. Re-running after a partial failure, or re-parsing an overlapping
    date window (the pull deliberately uses overlapping windows rather than risking a missed
    page), must not double-count a fill -- and a duplicated SELL is the shape that silently
    corrupts FIFO. Rows already present are reported as `skipped_duplicate`, not re-appended.

    Dry run by default; --write to apply. Never rebuilds lots itself -- run `lots --write`
    after, so the FIFO rebuild stays the single writer of lots.json.
    """
    parsed = load_json(args.parsed_file, default=None)
    if isinstance(parsed, dict):
        parsed = parsed.get("parsed")
    if not isinstance(parsed, list):
        fail(f"--parsed-file must contain a `parsed` list (or be one): {args.parsed_file}")

    path = os.path.join(args.base_dir, "trades.json")
    doc = load_json(path, default={"schema_version": 1, "trades": []}) or {}
    rows = doc.get("trades", doc if isinstance(doc, list) else [])
    seen = {r.get("message_id") for r in rows if isinstance(r, dict) and r.get("message_id")}
    # Fallback identity for rows predating message_id capture, so a re-parse of an old window
    # does not re-append history that is already recorded under a different provenance.
    seen_fp = {(r.get("date"), r.get("ticker"), r.get("qty"), r.get("price_usd"))
               for r in rows if isinstance(r, dict)}

    added, dupes, rejected = [], [], []
    for r in parsed:
        if not isinstance(r, dict) or not r.get("ticker") or r.get("qty") is None:
            rejected.append(r)
            continue
        if r.get("price_source") != "email_confirmed":
            rejected.append(dict(r, _why="not email_confirmed -- only confirmed fills append here"))
            continue
        mid = r.get("message_id")
        fp = (r.get("date"), r.get("ticker"), r.get("qty"), r.get("price_usd"))
        if (mid and mid in seen) or fp in seen_fp:
            dupes.append({"message_id": mid, "ticker": r.get("ticker"), "date": r.get("date")})
            continue
        row = {k: v for k, v in r.items() if k not in ("name", "extracted_from")}
        row["notes"] = (f"auto-parsed from INDmoney confirmation {mid or '(no id)'}; "
                        f"Amount ${r.get('amount_usd')} reconciles to qty x price within a "
                        f"{r.get('implied_fee_pct')}% fee; ticker resolved by "
                        f"{r.get('ticker_resolved_by')}")
        rows.append(row)
        seen.add(mid)
        seen_fp.add(fp)
        added.append({"date": row.get("date"), "ticker": row.get("ticker"),
                      "side": row.get("side"), "qty": row.get("qty"),
                      "price_usd": row.get("price_usd"), "reason": row.get("reason")})

    rows.sort(key=lambda r: (str(r.get("date") or ""), str(r.get("ticker") or "")))
    if isinstance(doc, dict):
        doc["trades"] = rows
    else:
        doc = rows

    if args.write and added:
        safe_write(path, doc)           # .bak + tmp-then-mv, same as every memory-of-record file

    emit({"dry_run": not args.write, "added": added, "added_count": len(added),
          "skipped_duplicate": dupes, "rejected": rejected,
          "total_rows": len(rows), "written": bool(args.write and added),
          "next_step": ("run `smith_math.py lots --write` to FIFO-rebuild lots.json and "
                        "reconcile against broker quantities" if added else
                        "nothing to append"),
          "uncaptured_reasons": [a["ticker"] for a in added if a.get("reason") == "UNCAPTURED"]})
