"""Realised correlation: the risk dimension this desk has never measured.

WHY (added 2026-09-19). Concentration here has always been managed by LABEL. policy.json assigns
each holding to a named cluster and cluster caps police those names, but nothing in that chain
looks at what the prices actually do. On 2026-09-18 the book's clusters moved +4.18% (memory),
+2.92% (analog), +2.71% (semis) and +2.06% (optics) on the same session -- four "separate"
buckets and one factor. A cap that counts tickers cannot see that; a correlation matrix can.

WHAT IT ADDS, none of which the label-based view can produce:
  * EFFECTIVE NUMBER OF BETS. 27 positions that all load on one factor are not 27 bets. The
    diversification ratio answers how many independent positions the book actually behaves like.
    On the live book: 2.05.
  * DIVERSIFICATION CREDIT, AND WHETHER IT IS EARNED. `aggregate_open_risk_usd` sums every stop
    distance, which is the all-fire case and therefore already conservative. The question
    correlation settles is whether the book may hold LESS than that sum. At rho~0.40 it may not,
    because a factor drawdown is exactly when all the stops fire together.
  * CLUSTER COHESION. Whether policy's named clusters correspond to anything in the returns --
    a cluster whose members correlate no more with each other than with outsiders is a label,
    not a risk bucket, and its cap is not doing the job it appears to do.

DELIBERATELY NOT A COVARIANCE-OPTIMISED PORTFOLIO. No mean-variance optimiser, no shrinkage
estimator, no efficient frontier. Correlations on ~250 daily observations of 27 names are noisy
and unstable, and a full covariance optimisation would give that noise authority over position
sizing. This module measures and reports; sizing stays with the conviction/ATR chain and the
user's own judgment.
"""

from collections import defaultdict


MIN_PAIR_OBS = 40


def daily_returns(bars, tickers, lookback=250):
    """{ticker: {date: return}} per ticker over its OWN history.

    PAIRWISE-COMPLETE, NOT LISTWISE-COMPLETE (corrected 2026-09-19 before first use). Taking the
    intersection of every ticker's dates sounds tidy and is badly wrong here: one newly-bought
    name truncates the whole matrix. On the live book it cut 27 names to 50 shared observations
    -- 351 pairs estimated from 50 points, because SKHY was bought last week. Returns are keyed
    by date so each PAIR can use its own overlap: AMAT/KLAC gets its full year, anything paired
    with SKHY gets a fortnight and is marked thin rather than silently dragging everyone down.
    """
    out, dropped = {}, []
    for t in tickers:
        rows = (bars or {}).get(t)
        if not rows:
            dropped.append(t)
            continue
        series = (dict(rows) if isinstance(rows, dict)
                  else {str(r["d"])[:10]: float(r["c"]) for r in rows if r.get("c")})
        dates = sorted(series)[-(lookback + 1):]
        if len(dates) < 2 or any(series[d] <= 0 for d in dates):
            dropped.append(t)
            continue
        out[t] = {dates[i]: series[dates[i]] / series[dates[i - 1]] - 1
                  for i in range(1, len(dates))}
    spans = [d for r in out.values() for d in r]
    return out, (sorted(set(spans)) if spans else []), sorted(set(dropped))


def _corr(a, b):
    n = len(a)
    if n < 2:
        return None
    ma, mb = sum(a) / n, sum(b) / n
    va = sum((x - ma) ** 2 for x in a)
    vb = sum((x - mb) ** 2 for x in b)
    if va <= 0 or vb <= 0:
        return None
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    return cov / (va ** 0.5 * vb ** 0.5)


def matrix(rets, min_obs=MIN_PAIR_OBS):
    """Pairwise Pearson correlation, each pair on its own overlapping dates.

    Returns (corr, obs) where `obs[a][b]` is how many observations that pair actually had. A
    pair with fewer than `min_obs` is None rather than a number, because a correlation from a
    fortnight of a rallying tape is not evidence and this book buys new names often enough for
    that to matter every run.
    """
    tickers = sorted(rets)
    out = {t: {} for t in tickers}
    obs = {t: {} for t in tickers}
    for i, a in enumerate(tickers):
        out[a][a], obs[a][a] = 1.0, len(rets[a])
        for b in tickers[i + 1:]:
            shared = sorted(set(rets[a]) & set(rets[b]))
            n = len(shared)
            obs[a][b] = obs[b][a] = n
            if n < min_obs:
                out[a][b] = out[b][a] = None
                continue
            c = _corr([rets[a][d] for d in shared], [rets[b][d] for d in shared])
            out[a][b] = out[b][a] = (round(c, 4) if c is not None else None)
    return out, obs


def _stdev(xs):
    n = len(xs)
    if n < 2:
        return 0.0
    m = sum(xs) / n
    return (sum((x - m) ** 2 for x in xs) / (n - 1)) ** 0.5


def diversification(weights, rets, corr):
    """Diversification ratio and the effective number of bets it implies.

    DR = (sum of weighted individual vols) / (vol of the weighted portfolio). It is 1.0 when
    every holding is perfectly correlated -- i.e. one bet wearing N tickers -- and rises toward
    sqrt(N) as holdings become independent. The effective bet count is DR^2, the standard
    reading: a book of 27 names with DR 1.3 behaves like roughly 1.7 independent positions.
    """
    names = [t for t in weights if t in rets and weights[t] > 0]
    if len(names) < 2:
        return {"diversification_ratio": None, "effective_bets": None,
                "reason": "fewer than 2 correlated holdings"}
    total = sum(weights[t] for t in names)
    w = {t: weights[t] / total for t in names}
    vols = {t: _stdev(list(rets[t].values())) for t in names}
    weighted_vol_sum = sum(w[t] * vols[t] for t in names)

    # AN UNKNOWN CORRELATION IS NOT ZERO (fixed 2026-09-19, caught by its own unit test). The
    # first version fell back to `or 0.0`, which treats an unmeasurable pair as INDEPENDENT --
    # the optimistic direction, and the one that inflates the effective bet count exactly for the
    # newly-bought names whose risk is least understood. Unknown pairs now take the book's own
    # measured average instead, and the count of imputed pairs is reported so the reader can see
    # how much of the answer is measurement and how much is assumption.
    measured = [c for a in names for b in names
                if a != b for c in [corr.get(a, {}).get(b)] if c is not None]
    fallback = (sum(measured) / len(measured)) if measured else 1.0
    imputed = 0
    port_var = 0.0
    for a in names:
        for b in names:
            if a == b:
                c = 1.0
            else:
                c = corr.get(a, {}).get(b)
                if c is None:
                    c = fallback
                    imputed += 1
            port_var += w[a] * w[b] * vols[a] * vols[b] * c
    port_vol = port_var ** 0.5 if port_var > 0 else 0.0
    if not port_vol:
        return {"diversification_ratio": None, "effective_bets": None,
                "reason": "portfolio variance is zero"}
    dr = weighted_vol_sum / port_vol
    return {"diversification_ratio": round(dr, 3),
            "effective_bets": round(dr ** 2, 2),
            "holdings_counted": len(names),
            "portfolio_vol_daily_pct": round(port_vol * 100, 3),
            "portfolio_vol_annualized_pct": round(port_vol * (252 ** 0.5) * 100, 1),
            "weighted_avg_vol_annualized_pct": round(weighted_vol_sum * (252 ** 0.5) * 100, 1),
            "imputed_pairs": imputed // 2,
            "imputed_with": round(fallback, 3) if imputed else None,
            "reads_as": (f"{len(names)} positions behaving like ~{dr ** 2:.1f} independent bets")}


def correlated_stop_loss(positions, corr):
    """How much of the desk's stop-sum is real, given how correlated the names actually are.

    THE FRAMING HERE WAS WRONG ON FIRST WRITING AND THE CORRECTION IS THE POINT. The initial
    version claimed `aggregate_open_risk_usd` UNDERSTATES risk by assuming independence. It does
    not: summing every position's stop distance is the ALL-FIRE case, which is what perfect
    correlation looks like, so the desk's existing number is already the conservative end.

    What correlation actually decides is how much diversification credit the book is entitled to
    take off that sum. A genuinely diversified book would rarely see every stop fire in one
    drawdown and could hold less against it; a single-factor book cannot, because that is exactly
    the scenario where they all fire together. So `correlated_usd` is the statistically expected
    joint loss at the measured average correlation, and `diversification_credit_usd` is the gap
    the book would be claiming if it treated its positions as independent. On a book at rho~0.44
    the credit is small and should NOT be taken -- which is the finding, not a licence to hold
    less capital against the stops.
    """
    rows = [p for p in positions if p.get("position_open_risk_usd") and p.get("ticker")]
    if len(rows) < 2:
        return {"independent_sum_usd": round(sum(p.get("position_open_risk_usd") or 0
                                                 for p in rows), 2),
                "correlated_usd": None, "reason": "fewer than 2 positions carrying stop risk"}
    independent = sum(p["position_open_risk_usd"] for p in rows)
    pairs, total = 0, 0.0
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            c = corr.get(a["ticker"], {}).get(b["ticker"])
            if c is not None:
                total += c
                pairs += 1
    avg_corr = (total / pairs) if pairs else None
    if avg_corr is None:
        return {"independent_sum_usd": round(independent, 2), "correlated_usd": None,
                "reason": "no pairwise correlation available"}
    # sqrt of the quadratic form with equal risk contributions: sqrt(n + n(n-1)*rho) / n
    n = len(rows)
    scale = ((n + n * (n - 1) * max(0.0, avg_corr)) ** 0.5) / n
    return {"independent_sum_usd": round(independent, 2),
            "avg_pairwise_correlation": round(avg_corr, 3),
            "correlated_usd": round(independent * scale, 2),
            "diversification_credit_usd": round(independent * (1 - scale), 2),
            "credit_pct_of_sum": round((1 - scale) * 100, 1),
            "positions": n,
            "take_the_credit": bool(avg_corr < 0.25),
            "note": ("aggregate_open_risk_usd is the ALL-FIRE sum (the perfect-correlation case) "
                     "and stays the number to hold capital against. `correlated_usd` is the "
                     "expected joint loss at the measured correlation; the difference is the "
                     "diversification credit a book would claim by treating these as independent "
                     "bets. At this correlation that credit is not earned -- a factor drawdown is "
                     "precisely when every one of these stops fires together.")}


def cluster_cohesion(clusters, corr):
    """Does each policy cluster correspond to anything in the returns?

    `within` is the average correlation among a cluster's own members; `outside` is the average
    against everything else. A cluster whose members correlate no more tightly with each other
    than with the rest of the book is a naming convention, and its cap polices a group the market
    does not trade as a group. Reported, never auto-applied: re-drawing cluster boundaries is a
    policy change and policy.json is the user's.
    """
    out = []
    all_members = {t for members in clusters.values() for t in members}
    for name, members in sorted(clusters.items()):
        inside = [t for t in members if t in corr]
        if len(inside) < 2:
            out.append({"cluster": name, "members": len(inside),
                        "verdict": "too few priced members to test"})
            continue
        within, cross = [], []
        for i, a in enumerate(inside):
            for b in inside[i + 1:]:
                c = corr.get(a, {}).get(b)
                if c is not None:
                    within.append(c)
            for b in all_members - set(members):
                c = corr.get(a, {}).get(b)
                if c is not None:
                    cross.append(c)
        if not within:
            out.append({"cluster": name, "members": len(inside), "verdict": "no pairs"})
            continue
        w = sum(within) / len(within)
        x = (sum(cross) / len(cross)) if cross else None
        gap = (w - x) if x is not None else None
        out.append({
            "cluster": name, "members": len(inside),
            "avg_within": round(w, 3),
            "avg_vs_rest_of_book": round(x, 3) if x is not None else None,
            "cohesion_gap": round(gap, 3) if gap is not None else None,
            "verdict": ("coherent risk bucket" if gap is not None and gap >= 0.10 else
                        "label only -- members are no more correlated with each other than "
                        "with the rest of the book" if gap is not None and gap < 0.03 else
                        "weak" if gap is not None else "no comparison set"),
        })
    return out


def top_pairs(corr, k=10, minimum=0.0):
    """Most-correlated pairs, the concrete form of "these two are one position"."""
    seen, out = set(), []
    for a, row in corr.items():
        for b, c in row.items():
            if a == b or c is None or (b, a) in seen:
                continue
            seen.add((a, b))
            if c >= minimum:
                out.append({"pair": [a, b], "corr": c})
    out.sort(key=lambda r: -r["corr"])
    return out[:k]


def cmd_correlation(args):
    """Realised-correlation view of concentration, written to compute_correlation.json.

    Reads the same perf_bars.json the realized-return reconstruction uses, so the correlation
    window and the performance window cannot drift apart.
    """
    import os
    from smith_core import emit, load_json, atomic_write_json, resolve_today

    bars = load_json(os.path.join(args.base_dir, "perf_bars.json"), default=None)
    if not bars:
        emit({"ok": False, "error": "perf_bars.json missing -- run `smith_fetch.py perf-bars`"})
        return
    holdings = load_json(os.path.join(args.run_dir, "holdings.json"), default={}) or {}
    rows = holdings.get("holdings_inr") or []
    rows = rows if isinstance(rows, list) else list(rows.values())
    weights = {r["ticker"]: float(r.get("weight_pct") or 0) for r in rows if r.get("ticker")}
    held = [t for t, w in weights.items() if w > 0]
    if len(held) < 2:
        emit({"ok": False, "error": "fewer than 2 weighted holdings"})
        return

    rets, dates, dropped = daily_returns(bars, held, lookback=args.lookback)
    corr, obs = matrix(rets, min_obs=args.min_obs)
    div = diversification(weights, rets, corr)

    risk = load_json(os.path.join(args.run_dir, "compute_risk.json"), default={}) or {}
    stop_view = correlated_stop_loss(risk.get("positions") or [], corr)

    # cluster membership lives in state.sector_map, not on the holdings row
    state = load_json(os.path.join(args.base_dir, "state.json"), default={}) or {}
    sector_map = state.get("sector_map") or {}
    clusters = defaultdict(list)
    for r in rows:
        t = r.get("ticker")
        if not t:
            continue
        entry = sector_map.get(t)
        name = entry.get("cluster") if isinstance(entry, dict) else entry
        if name:
            clusters[name].append(t)
    cohesion = cluster_cohesion(dict(clusters), corr)

    thin = [[a, b, obs[a][b]] for a in corr for b in corr[a]
            if a < b and corr[a][b] is None]
    out = {
        "as_of": str(resolve_today(args.today)),
        "window": {"from": dates[0] if dates else None, "to": dates[-1] if dates else None,
                   "lookback_sessions": args.lookback, "min_pair_obs": args.min_obs},
        "diversification": div,
        "stop_risk": stop_view,
        "cluster_cohesion": cohesion,
        "most_correlated_pairs": top_pairs(corr, k=args.top),
        "matrix": corr if args.full else None,
        "tickers": sorted(corr),
        "dropped_no_history": dropped,
        "pairs_below_min_obs": thin,
        "data_quality": [
            "pairwise-complete: each pair uses its own overlapping dates, so a recently-bought "
            "name does not truncate the whole matrix (it would have cut 27 names to 50 shared "
            "sessions before this was fixed).",
            "correlations are realised and backward-looking; they rise in drawdowns, which is "
            "precisely when the diversification credit would be relied on.",
        ],
    }
    if not args.full:
        out.pop("matrix")
    atomic_write_json(os.path.join(args.run_dir, "compute_correlation.json"), out)
    out["written"] = os.path.join(args.run_dir, "compute_correlation.json")
    emit(out)
