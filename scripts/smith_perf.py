"""Realized performance: position-level reconstruction, time-weighted return, and the
money-weighted cost of security selection.

WHY THIS MODULE EXISTS (added 2026-09-19, closes the single largest measurement gap on the desk).
Until now the ONLY performance figure Smith could produce was `rolling_constant_mix` in
smith_marketdata.py -- today's holdings at today's weights, backcast through a trailing window.
That number is survivorship-biased by construction and the function's own docstring says so
("flattered by hindsight: it prices the names you kept"). It reported 12m book +128.26% vs SMH
+81.5%, i.e. +46.76pp of outperformance, while excluding all 121 positions that were stopped out
and never re-entered. Reconstructing the actual book from the trade ledger reverses the sign of
that claim outright. A desk that cannot measure its own return cannot learn from it, so every
calibration built on top of this module depends on it being right.

WHY NOT THE LEDGER'S OWN SNAPSHOTS. `realized_twr` (smith_marketdata.py) already implements
correct TWR arithmetic against ledger.csv and has never once returned a number, because
`external_flow_usd` is populated on 0 of 57 rows. Backfilling that column from wallet deltas was
tried first and abandoned: the residual is dominated by trade/snapshot timing skew, not by real
deposits. Two adjacent 2026-09-16 rows implied -$524.40 and +$508.26 of "external flow" from a
single fill straddling the snapshot boundary. Worse, the snapshots are not internally consistent
with the fills on heavy-trading days -- on 2026-07-28 ledger equity fell $21,276 -> $15,178 across
an interval in which $8,044 of stock was BOUGHT, which is arithmetically impossible and produced a
-66% "daily return". The trade ledger plus daily closes is the only self-consistent basis
available, and it reconciles to the live broker quantity on 27 of 28 tickers (the lone exception
being SKHY, itself an unreconciled fill the desk flagged independently the same morning).

THREE CORRECTIONS THE NAIVE RECONSTRUCTION NEEDS, each found by an implausible output:
  1. ADJUSTMENT ROWS ARE FLOWS, NOT PERFORMANCE. trades.json carries 13 `ca_type: adjustment`
     rows -- G71 phantom-short and G68/G79 broker reconciliations, every one of them stamped
     "basis unknown". They change quantity with no cash. Counted as free shares they manufacture
     return: 2026-02-02 (GOOG +1.009, NVDA +3.0) read as +13.87% in a day. They are priced at that
     session's close and booked as flow, so a pure adjustment day returns exactly 0.
  2. A MATERIALITY FLOOR ON THE DENOMINATOR. The account opened at ~$103. A $1,000 deposit against
     a $103 base produced -41.88% on 2025-05-07. Sessions whose PRIOR value is below MIN_BOOK_USD
     are excluded from the chain rather than allowed to dominate it.
  3. TRADE DATES ROLL FORWARD TO THE NEXT SESSION. 5 of 1003 trades are dated on non-trading days
     (the 2026-08-15 Saturday reconciliation batch, 2025-12-25). Iterating the market calendar and
     matching on date equality silently dropped them, losing $2.8K of position.

TWR AND MONEY-WEIGHTED ARE BOTH REPORTED, DELIBERATELY. They disagree by an order of magnitude on
this account and each is honest about a different question. TWR equal-weights every session, so
the 16 months when the book was under $5K count as heavily as the months at $33K -- that is what
makes it the right measure of the STRATEGY and comparable to an index, and also what makes it a
poor description of money actually lost. The money-weighted figure re-runs every equity flow into
the benchmark instead and differences the terminal values, answering "what did picking these names
instead of SMH cost in dollars". Reporting either alone would mislead: -92pp sounds catastrophic,
-$2,095 sounds trivial, and both are the same book.
"""

import os
from collections import defaultdict

from smith_core import DEFAULT_BASE, emit, load_json, atomic_write_json, resolve_today

BENCH = "SMH"
MIN_BOOK_USD = 500.0        # see correction 2 above
TRADING_DAYS = 252


# ---------------------------------------------------------------------------
# reconstruction
# ---------------------------------------------------------------------------

def closes_index(bars):
    """Normalise either accepted bar shape to {ticker: {date: close}}.

    perf_bars.json carries full OHLC rows ({ticker: [{d,h,l,c}]}) so the same file can feed
    `atr_pct` for the stop-loss backfill; the flat {ticker: {date: close}} form is still accepted
    because it is what the first version wrote and what tests find easiest to build.
    """
    out = {}
    for ticker, rows in (bars or {}).items():
        if isinstance(rows, dict):
            out[ticker] = rows
        elif isinstance(rows, list):
            out[ticker] = {str(r["d"])[:10]: float(r["c"]) for r in rows
                           if r.get("c") is not None and r.get("d")}
    return out


def _price_on(bars, ticker, day):
    """Last close at or before `day`. Carries a stale price forward rather than dropping the
    position, which would read as a sale."""
    rows = bars.get(ticker)
    if not rows:
        return None
    prior = [d for d in rows if d <= day]
    return rows[prior[-1]] if prior else None


def _equity_flow(trade, bars, session):
    """Signed cash moved INTO equities by one trade: a buy is positive, a sell negative.

    An adjustment is priced at the session close so it nets to zero return (correction 1).
    Prefers `amount_usd` -- the broker's own figure, inclusive of the ~0.30% buy fee -- and falls
    back to qty x price, which understates cost by that fee.
    """
    qty = float(trade["qty_change"])
    if trade.get("ca_type") or trade.get("type") == "corporate_action":
        px = _price_on(bars, trade["ticker"], session)
        return (qty * px, "adjustment") if px else (None, "adjustment_unpriced")
    amount = trade.get("amount_usd")
    if amount not in (None, ""):
        gross = abs(float(amount))
        basis = "amount_usd"
    else:
        px = trade.get("price_usd") or trade.get("price_at_trade")
        if px in (None, ""):
            return None, "unpriced"
        gross = abs(qty) * float(px)
        basis = "qty_x_price"
    return (gross if qty > 0 else -gross), basis


def reconstruct(trades, bars, bench=BENCH, min_book_usd=MIN_BOOK_USD, since=None, until=None):
    """Daily position book rebuilt from the trade ledger and priced at daily closes.

    Returns {series, skipped_below_floor, unpriced_trades, adjustment_flow_usd, positions_final}.
    Each series row is {d, value_usd, flow_usd, ret, n_positions} where `ret` is that session's
    time-weighted return: (V_t - flow_t - V_t-1) / V_t-1.

    Selling below the session close shows up here as a negative return, and that is correct, not
    noise -- it is the execution cost of the fill, which a close-to-close series would hide.
    """
    bars = closes_index(bars)
    sessions = sorted(bars.get(bench) or [])
    if len(sessions) < 2:
        return {"series": [], "error": f"no {bench} bars to define a session calendar"}

    def roll_forward(date):
        """First session at or after `date` (correction 3)."""
        later = [s for s in sessions if s >= date]
        return later[0] if later else None

    by_session = defaultdict(list)
    for t in trades:
        s = roll_forward(str(t.get("date") or "")[:10])
        if s:
            by_session[s].append(t)

    first_trade = min((str(t.get("date") or "")[:10] for t in trades), default=None)
    if not first_trade:
        return {"series": [], "error": "no trades"}

    positions = defaultdict(float)
    prev_value = None
    series, skipped, unpriced, adj_flow = [], 0, [], 0.0

    for day in sessions:
        if day < first_trade or (until and day > until):
            continue
        flow = 0.0
        for t in by_session.get(day, []):
            positions[t["ticker"]] += float(t["qty_change"])
            cash, basis = _equity_flow(t, bars, day)
            if cash is None:
                unpriced.append({"date": t.get("date"), "ticker": t.get("ticker"), "why": basis})
                continue
            flow += cash
            if basis == "adjustment":
                adj_flow += abs(cash)

        value, n_pos = 0.0, 0
        for ticker, qty in positions.items():
            if abs(qty) < 1e-9:
                continue
            px = _price_on(bars, ticker, day)
            if px is None:
                continue
            value += qty * px
            n_pos += 1

        if prev_value is not None and prev_value >= min_book_usd:
            if not since or day >= since:
                series.append({"d": day, "value_usd": round(value, 2), "flow_usd": round(flow, 2),
                               "ret": (value - flow - prev_value) / prev_value,
                               "n_positions": n_pos})
        elif prev_value is not None:
            skipped += 1
        prev_value = value

    return {"series": series, "skipped_below_floor": skipped, "unpriced_trades": unpriced,
            "adjustment_flow_usd": round(adj_flow, 2),
            "positions_final": {t: round(q, 6) for t, q in positions.items() if abs(q) > 1e-9}}


# ---------------------------------------------------------------------------
# statistics
# ---------------------------------------------------------------------------

def chain(series, bars, bench=BENCH):
    """Chain-link the daily returns and describe the resulting equity curve.

    Sharpe is computed at a zero risk-free rate and labelled as such -- with the 10-yr near 5%
    a zero-rf Sharpe materially overstates risk-adjusted skill, and quoting it unlabelled would
    be the same category of error this module exists to fix.
    """
    if not series:
        return {"n_sessions": 0, "twr_pct": None, "reason": "empty series"}
    bars = closes_index(bars)
    growth, equity, peak, max_dd = 1.0, 1.0, 1.0, 0.0
    for row in series:
        growth *= (1 + row["ret"])
        equity = growth
        peak = max(peak, equity)
        max_dd = min(max_dd, equity / peak - 1)
    rets = [r["ret"] for r in series]
    n = len(rets)
    mean = sum(rets) / n
    var = sum((r - mean) ** 2 for r in rets) / (n - 1) if n > 1 else 0.0
    sd = var ** 0.5
    d0, d1 = series[0]["d"], series[-1]["d"]
    b0, b1 = _price_on(bars, bench, d0), _price_on(bars, bench, d1)
    twr = (growth - 1) * 100
    out = {"from": d0, "to": d1, "n_sessions": n, "twr_pct": round(twr, 2),
           "vol_annualized_pct": round(sd * (TRADING_DAYS ** 0.5) * 100, 1),
           "max_drawdown_pct": round(max_dd * 100, 1),
           "sharpe_rf0": round(mean / sd * (TRADING_DAYS ** 0.5), 2) if sd else None,
           "sharpe_note": "risk-free rate ZERO; the 10-yr is ~5%, so this overstates risk-adjusted skill",
           "best_session_pct": round(max(rets) * 100, 2),
           "worst_session_pct": round(min(rets) * 100, 2)}
    if b0 and b1:
        bench_pct = (b1 / b0 - 1) * 100
        out.update({"benchmark": bench, "benchmark_pct": round(bench_pct, 2),
                    "excess_pp": round(twr - bench_pct, 2)})
    else:
        out.update({"benchmark": bench, "benchmark_pct": None, "excess_pp": None,
                    "benchmark_reason": "no benchmark close at a window endpoint"})
    return out


def selection_cost(series, bars, bench=BENCH):
    """Money-weighted counterfactual: every equity flow redirected into the benchmark instead.

    Terminal difference is what security selection cost (or earned) in dollars on the capital
    actually at risk, when it was actually at risk -- the question TWR deliberately does not
    answer. Returns None-bearing dict when the benchmark cannot be priced.
    """
    if not series:
        return {"selection_cost_usd": None, "reason": "empty series"}
    bars = closes_index(bars)
    units, deployed = 0.0, 0.0
    for row in series:
        px = _price_on(bars, bench, row["d"])
        if not px:
            return {"selection_cost_usd": None, "reason": f"no {bench} close on {row['d']}"}
        units += row["flow_usd"] / px
        deployed += row["flow_usd"]
    last = series[-1]["d"]
    bench_px = _price_on(bars, bench, last)
    actual = series[-1]["value_usd"]
    counterfactual = units * bench_px
    return {"as_of": last,
            "net_capital_deployed_usd": round(deployed, 2),
            "actual_value_usd": round(actual, 2),
            "same_flows_into_benchmark_usd": round(counterfactual, 2),
            "selection_cost_usd": round(actual - counterfactual, 2),
            "basis": f"every equity flow redirected into {bench} at that session's close"}


def by_period(series, bars, bench=BENCH, key=lambda d: d[:7]):
    """Sub-period TWR vs benchmark. Default key is calendar month. Used to show WHERE the
    excess came from rather than asserting a single 16-month number."""
    bars = closes_index(bars)
    buckets = defaultdict(list)
    for row in series:
        buckets[key(row["d"])].append(row)
    out = []
    for period in sorted(buckets):
        rows = buckets[period]
        growth = 1.0
        for r in rows:
            growth *= (1 + r["ret"])
        b0 = _price_on(bars, bench, rows[0]["d"])
        b1 = _price_on(bars, bench, rows[-1]["d"])
        bench_pct = (b1 / b0 - 1) * 100 if (b0 and b1) else None
        book_pct = (growth - 1) * 100
        out.append({"period": period, "sessions": len(rows),
                    "book_pct": round(book_pct, 2),
                    "benchmark_pct": round(bench_pct, 2) if bench_pct is not None else None,
                    "excess_pp": round(book_pct - bench_pct, 2) if bench_pct is not None else None,
                    "end_value_usd": rows[-1]["value_usd"]})
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def cmd_perf(args):
    """Realized performance of the actual book, reconstructed from trades.json + daily closes.

    This is the number `rolling_constant_mix` cannot produce. Writes compute_perf.json to the run
    dir when --run-dir is given, so the briefing and dashboard read a committed artefact rather
    than re-deriving.
    """
    base = args.base_dir
    bars_path = args.bars or os.path.join(base, "perf_bars.json")
    bars = load_json(bars_path, default=None)
    if not bars:
        emit({"ok": False, "error": f"no price history at {bars_path} -- run "
                                    f"`smith_fetch.py perf-bars --base-dir .` first"})
        return
    trades = (load_json(os.path.join(base, "trades.json"), default={}) or {}).get("trades", [])
    if not trades:
        emit({"ok": False, "error": "trades.json has no trades"})
        return

    recon = reconstruct(trades, bars, bench=args.bench, min_book_usd=args.min_book,
                        since=args.since, until=args.until)
    if recon.get("error"):
        emit({"ok": False, **recon})
        return
    series = recon["series"]
    stats = chain(series, bars, bench=args.bench)
    money = selection_cost(series, bars, bench=args.bench)
    months = by_period(series, bars, bench=args.bench)

    # A second chain restricted to the era when the capital was material. The full-history TWR
    # equal-weights the months the account held a few hundred dollars, which is exactly when its
    # percentage swings were wildest and least consequential.
    material = [r for r in series if r["value_usd"] >= args.material_book]
    material_stats = chain(material, bars, bench=args.bench) if material else None

    dq = []
    if recon["unpriced_trades"]:
        dq.append(f"{len(recon['unpriced_trades'])} trade(s) could not be priced and were "
                  f"excluded from flow: {recon['unpriced_trades'][:5]}")
    if recon["adjustment_flow_usd"]:
        dq.append(f"${recon['adjustment_flow_usd']:,.2f} of position arrived via `adjustment` rows "
                  f"(phantom-short/broker reconciliations, basis unknown). Priced at session close "
                  f"and booked as flow so they contribute no return, but the position history "
                  f"before 2026-08-15 rests on 13 such corrections.")
    if recon["skipped_below_floor"]:
        dq.append(f"{recon['skipped_below_floor']} early session(s) excluded: prior book below "
                  f"${args.min_book:,.0f}, where percentage returns are arithmetically unstable.")
    dq.append("Reconstructed from trades.json, NOT from ledger.csv snapshots -- the ledger's "
              "value_usd is not consistent with fills on heavy-trading days (2026-07-28).")

    out = {"as_of": str(resolve_today(args.today)), "ok": True,
           "basis": "position-level reconstruction from the trade ledger, priced at daily closes",
           "twr": stats, "twr_material_capital": material_stats,
           "material_book_floor_usd": args.material_book,
           "money_weighted": money, "by_month": months,
           "positions_final_count": len(recon["positions_final"]),
           "adjustment_flow_usd": recon["adjustment_flow_usd"],
           "data_quality": dq}
    if args.run_dir:
        atomic_write_json(os.path.join(args.run_dir, "compute_perf.json"), out)
        out["written"] = os.path.join(args.run_dir, "compute_perf.json")
    if not args.full:
        out.pop("by_month", None)
    emit(out)
