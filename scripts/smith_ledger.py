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
            if q > 1e-4:
                orphans.append({"ticker": tk, "lots_sum": q, "broker_qty": 0, "lots": len(ls),
                                "note": "ledger shows an open position the broker does not report "
                                        "-- a sell is missing from the trade record entirely"})
        recon = {"tickers_checked": len(live), "reconciled": len(live) - len(mismatches),
                 "mismatches": sorted(mismatches, key=lambda m: -abs(m["delta"])),
                 "orphaned_positions": sorted(orphans, key=lambda o: -o["lots_sum"])}

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
        tmp = path + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(payload, fh, indent=2)
        os.replace(tmp, path)
        written = path

    emit({"tickers": len(out),
          "total_lots": sum(len(v) for v in out.values()),
          "corporate_actions_applied": applied_ca,
          "phantom_shorts": shorts,
          "reconciliation": recon,
          "warnings": warnings,
          "written": written,
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
