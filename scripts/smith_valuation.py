#!/usr/bin/env python3
"""Intrinsic valuation and forensic-accounting checks for the US book.

WHY THIS EXISTS (added 2026-09-07, user request following an external architecture review).
The desk had no floor under a stock price other than analyst consensus targets — thesis
verdicts and proposal sizing never asked "what growth rate does the CURRENT price already
assume, and does the company's own cash-flow history support that assumption?" This closes
that gap with three checks, run per ticker from data the calling agent has already fetched via
the FMP MCP tools (`discountedCashFlow`, `statements`) — this script forms no network
connections and NEVER estimates a missing input; a check with an insufficient input is skipped
for that ticker and named in data_quality, exactly like every other compute stage in this repo.

  1. REVERSE DCF — solves for the constant near-term growth rate `g` that makes a standard
     two-stage FCFF DCF equal the market's own enterprise value, then compares `g` to the
     company's trailing 5-year FCF CAGR. A market pricing in growth far above what the company
     has ever delivered is a distinct, checkable claim — VALUATION_STRETCHED.

  2. ROIC vs WACC — FMP's `key-metrics` already computes returnOnInvestedCapital properly
     (NOPAT / invested capital); re-deriving it in-house would be a shakier duplicate of a
     trusted number, not an improvement, so this consumes it directly. WACC is computed here
     via CAPM, since FMP does not expose it. A negative spread means the business is destroying
     capital even while GAAP earnings look fine — the signal `smith-thesis` downgrades on.

  3. BENEISH M-SCORE — FMP has no equivalent, so this implements the standard eight-variable
     model from two years of as-reported financials. Altman Z-Score is NOT re-derived here for
     the same reason as ROIC — FMP's `financial-scores` endpoint already returns a validated
     `altmanZScore`; this module only classifies it (`distress_band`) and folds it together
     with the Beneish flag into one FORENSIC_RISK verdict.

COMPUTE-FIRST: every number here is arithmetic over inputs the caller supplies. No judgment,
no news, no "does this makes sense given the story" — that stays with smith-quality/smith-thesis.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from smith_core import emit, load_json, safe_write  # noqa: E402

REVERSE_DCF_STRETCH_GAP_PP_DEFAULT = 15.0   # implied growth vs 5y FCF CAGR, percentage points
BENEISH_MANIPULATION_THRESHOLD = -1.78      # M-score above this => flagged
ALTMAN_DISTRESS_THRESHOLD = 1.81
ALTMAN_SAFE_THRESHOLD = 2.99
MARKET_RISK_PREMIUM_PCT_DEFAULT = 5.0       # long-run US equity risk premium assumption
TERMINAL_GROWTH_PCT_DEFAULT = 2.5           # long-run nominal GDP-ish assumption
FORECAST_YEARS_DEFAULT = 5

# ---------------------------------------------------------------------------
# 1. Reverse DCF
# ---------------------------------------------------------------------------

def fcf_cagr_pct(fcf_history):
    """CAGR over a list of annual FCF figures, oldest first. None (never guessed) if fewer
    than 2 points or either endpoint is non-positive -- a CAGR over a loss-to-profit swing is
    not a growth rate, it's a sign change, and reporting one as if it were a rate is the exact
    kind of manufactured precision this codebase's own PLAUSIBILITY BANDS guardrails exist to
    stop."""
    if not fcf_history or len(fcf_history) < 2:
        return None
    first, last = fcf_history[0], fcf_history[-1]
    years = len(fcf_history) - 1
    if first is None or last is None or first <= 0 or last <= 0:
        return None
    return (((last / first) ** (1.0 / years)) - 1.0) * 100.0


def _dcf_ev(g_pct, fcf0, wacc_pct, terminal_growth_pct, years):
    """Two-stage FCFF DCF: `years` of growth at g, then a Gordon-growth terminal value."""
    g, wacc, term = g_pct / 100.0, wacc_pct / 100.0, terminal_growth_pct / 100.0
    if wacc <= term:
        return None  # terminal value undefined/infinite -- degenerate input, not a real answer
    pv = 0.0
    fcf_t = fcf0
    for t in range(1, years + 1):
        fcf_t = fcf_t * (1 + g)
        pv += fcf_t / ((1 + wacc) ** t)
    terminal_fcf = fcf_t * (1 + term)
    terminal_value = terminal_fcf / (wacc - term)
    pv += terminal_value / ((1 + wacc) ** years)
    return pv


def reverse_dcf_implied_growth_pct(enterprise_value_usd, fcf0_usd, wacc_pct,
                                    terminal_growth_pct=TERMINAL_GROWTH_PCT_DEFAULT,
                                    forecast_years=FORECAST_YEARS_DEFAULT):
    """Bisects for the constant growth rate `g` (years 1..N) that makes the two-stage DCF equal
    the market's actual enterprise value. Returns {"implied_growth_pct": g} or {"refused": why}
    -- never a guess. `_dcf_ev` is monotonically increasing in g over the search range (more
    growth is worth more, always, at a fixed discount rate), so bisection is exact and stable;
    no gradient method or external solver is needed for a one-variable monotone root."""
    if enterprise_value_usd is None or enterprise_value_usd <= 0:
        return {"refused": "enterprise_value_usd missing or non-positive"}
    if fcf0_usd is None or fcf0_usd <= 0:
        return {"refused": "fcf0_usd missing or non-positive -- a reverse DCF off a "
                           "loss-making base FCF has no economically meaningful growth "
                           "solution; report the DCF as inapplicable rather than solving one"}
    if wacc_pct is None or wacc_pct <= terminal_growth_pct:
        return {"refused": f"wacc_pct ({wacc_pct}) must exceed terminal_growth_pct "
                           f"({terminal_growth_pct}) or the terminal value is undefined"}

    lo, hi = -50.0, 300.0
    ev_lo = _dcf_ev(lo, fcf0_usd, wacc_pct, terminal_growth_pct, forecast_years)
    ev_hi = _dcf_ev(hi, fcf0_usd, wacc_pct, terminal_growth_pct, forecast_years)
    if ev_lo is None or ev_hi is None:
        return {"refused": "degenerate DCF inputs (wacc <= terminal growth at a search bound)"}
    if not (ev_lo <= enterprise_value_usd <= ev_hi):
        return {"refused": f"market EV (${enterprise_value_usd:,.0f}) implies a growth rate "
                           f"outside the searched -50%..+300% range -- outside any plausible "
                           f"answer, not solved rather than guessed"}

    for _ in range(80):
        mid = (lo + hi) / 2.0
        ev_mid = _dcf_ev(mid, fcf0_usd, wacc_pct, terminal_growth_pct, forecast_years)
        if ev_mid < enterprise_value_usd:
            lo = mid
        else:
            hi = mid
    return {"implied_growth_pct": round((lo + hi) / 2.0, 3)}


def reverse_dcf_check(row, terminal_growth_pct=TERMINAL_GROWTH_PCT_DEFAULT,
                      forecast_years=FORECAST_YEARS_DEFAULT,
                      stretch_gap_pp=REVERSE_DCF_STRETCH_GAP_PP_DEFAULT):
    """row: {"enterprise_value_usd", "fcf0_usd", "wacc_pct", "fcf_history": [oldest..newest]}.
    Returns the full check result for one ticker, including the historical CAGR and the
    stretched-vs-not verdict. `wacc_pct` is expected precomputed (see wacc_pct() below) and
    passed in, not re-derived here, so this function's only job is the DCF root-find."""
    dq = []
    cagr = fcf_cagr_pct(row.get("fcf_history"))
    if cagr is None:
        dq.append("fcf_history missing, too short (<2 points), or non-positive at an "
                  "endpoint -- historical CAGR not computed")

    result = reverse_dcf_implied_growth_pct(
        row.get("enterprise_value_usd"), row.get("fcf0_usd"), row.get("wacc_pct"),
        terminal_growth_pct, forecast_years)
    if "refused" in result:
        dq.append(f"reverse DCF refused: {result['refused']}")
        return {"implied_growth_pct": None, "fcf_cagr_5y_pct": cagr,
               "gap_pp": None, "valuation_stretched": None, "data_quality": dq}

    g = result["implied_growth_pct"]
    gap = None if cagr is None else round(g - cagr, 2)
    stretched = None if gap is None else gap > stretch_gap_pp
    return {"implied_growth_pct": g, "fcf_cagr_5y_pct": round(cagr, 2) if cagr is not None else None,
           "gap_pp": gap, "valuation_stretched": stretched, "data_quality": dq,
           "note": (f"market EV implies {g:+.1f}% growth vs a trailing {cagr:+.1f}% FCF CAGR "
                    f"({gap:+.1f}pp gap) -- {'exceeds' if stretched else 'within'} the "
                    f"{stretch_gap_pp:g}pp stretch threshold" if cagr is not None else
                    f"market EV implies {g:+.1f}% growth; no historical CAGR to compare against")}


# ---------------------------------------------------------------------------
# 2. ROIC vs WACC
# ---------------------------------------------------------------------------

def capm_cost_of_equity_pct(risk_free_rate_pct, beta, market_risk_premium_pct=MARKET_RISK_PREMIUM_PCT_DEFAULT):
    if risk_free_rate_pct is None or beta is None:
        return None
    return risk_free_rate_pct + beta * market_risk_premium_pct


def wacc_pct(risk_free_rate_pct, beta, tax_rate_pct, total_debt_usd, total_equity_usd,
             cost_of_debt_pct=None, market_risk_premium_pct=MARKET_RISK_PREMIUM_PCT_DEFAULT):
    """Standard CAPM + capital-structure WACC. total_equity_usd is expected as market cap (the
    market's own valuation of equity), not book equity -- book equity understates a growth
    stock's true equity weight and skews WACC low. cost_of_debt_pct, if not supplied, defaults
    to risk_free + 200bp (a generic investment-grade spread) -- flagged in the caller's
    data_quality as an assumption, never presented as measured."""
    coe = capm_cost_of_equity_pct(risk_free_rate_pct, beta, market_risk_premium_pct)
    if coe is None or tax_rate_pct is None or total_equity_usd is None or total_equity_usd <= 0:
        return None, []
    dq = []
    debt = total_debt_usd or 0.0
    equity = total_equity_usd
    v = debt + equity
    cod = cost_of_debt_pct
    if cod is None:
        cod = (risk_free_rate_pct or 0) + 2.0
        dq.append("cost_of_debt_pct not supplied -- assumed risk-free + 200bp")
    w = (equity / v) * coe + (debt / v) * cod * (1 - tax_rate_pct / 100.0)
    return round(w, 3), dq


def roic_wacc_check(row, market_risk_premium_pct=MARKET_RISK_PREMIUM_PCT_DEFAULT):
    """row: {"roic_pct", "roic_history_pct": [oldest..newest], "risk_free_rate_pct", "beta",
    "tax_rate_pct", "total_debt_usd", "total_equity_usd", "cost_of_debt_pct" (optional)}.
    roic_pct is consumed as-is from the caller (FMP's key-metrics.returnOnInvestedCapital *
    100) -- this function never re-derives ROIC itself."""
    dq = []
    roic = row.get("roic_pct")
    if roic is None:
        dq.append("roic_pct not supplied")
        return {"wacc_pct": None, "spread_pct": None, "capital_destruction": None,
               "trend": None, "thesis_downgrade_signal": None, "data_quality": dq}

    w, wacc_dq = wacc_pct(row.get("risk_free_rate_pct"), row.get("beta"), row.get("tax_rate_pct"),
                          row.get("total_debt_usd"), row.get("total_equity_usd"),
                          row.get("cost_of_debt_pct"), market_risk_premium_pct)
    dq.extend(wacc_dq)
    if w is None:
        dq.append("WACC not computable -- missing risk_free_rate_pct/beta/tax_rate_pct/total_equity_usd")
        return {"wacc_pct": None, "spread_pct": None, "capital_destruction": None,
               "trend": None, "thesis_downgrade_signal": None, "data_quality": dq}

    spread = round(roic - w, 3)
    destruction = spread < 0
    history = row.get("roic_history_pct") or []
    trend = None
    if len(history) >= 2 and all(isinstance(x, (int, float)) for x in history):
        delta = history[-1] - history[0]
        trend = "improving" if delta > 1.0 else "deteriorating" if delta < -1.0 else "stable"
    return {"roic_pct": roic, "wacc_pct": w, "spread_pct": spread,
           "capital_destruction": destruction, "trend": trend,
           # "WATCH", not an invented status -- this codebase's real thesis vocabulary is
           # exactly {INTACT, STRENGTHENING, BROKEN, WATCH} (smith_risk.py), and a fifth value
           # here would be the same vocabulary defect the thesis schema audit already exists
           # to catch (see smith_memory.validate_thesis_schema). A negative ROIC-WACC spread
           # means erode-and-watch, not necessarily broken.
           "thesis_downgrade_signal": "WATCH" if destruction else None,
           "data_quality": dq,
           "note": (f"ROIC {roic:.1f}% vs WACC {w:.1f}% ({spread:+.1f}pp spread) -- "
                    f"{'capital-DESTROYING' if destruction else 'capital-accretive'}, "
                    f"trend {trend or 'unknown'}")}


# ---------------------------------------------------------------------------
# 3. Beneish M-Score + Altman Z-Score classification
# ---------------------------------------------------------------------------

BENEISH_FIELDS = ("receivables", "revenue", "cogs", "current_assets", "ppe_gross",
                  "securities", "total_assets", "sga", "depreciation",
                  "long_term_debt", "current_liabilities", "net_income", "cfo")


def beneish_m_score(cur, prior):
    """Standard 8-variable Beneish model. cur/prior are dicts with BENEISH_FIELDS, current
    year and the immediately prior year. Refuses (never estimates) if any required field is
    missing on either side, or if a ratio's denominator is zero."""
    missing = [f for f in BENEISH_FIELDS if cur.get(f) is None or prior.get(f) is None]
    if missing:
        return {"refused": f"missing field(s) for Beneish M-Score: {', '.join(sorted(missing))}"}

    def safe_div(n, d):
        return None if not d else n / d

    gross_margin_cur = safe_div(cur["revenue"] - cur["cogs"], cur["revenue"])
    gross_margin_prior = safe_div(prior["revenue"] - prior["cogs"], prior["revenue"])
    dsri = safe_div(safe_div(cur["receivables"], cur["revenue"]),
                    safe_div(prior["receivables"], prior["revenue"]))
    gmi = safe_div(gross_margin_prior, gross_margin_cur)
    aqi_cur = safe_div(cur["total_assets"] - cur["current_assets"] - cur["ppe_gross"] - (cur.get("securities") or 0),
                       cur["total_assets"])
    aqi_prior = safe_div(prior["total_assets"] - prior["current_assets"] - prior["ppe_gross"] - (prior.get("securities") or 0),
                         prior["total_assets"])
    aqi = safe_div(aqi_cur, aqi_prior)
    sgi = safe_div(cur["revenue"], prior["revenue"])
    depi_cur = safe_div(prior["depreciation"], prior["depreciation"] + prior["ppe_gross"])
    depi_prior = safe_div(cur["depreciation"], cur["depreciation"] + cur["ppe_gross"])
    depi = safe_div(depi_cur, depi_prior)
    sgai = safe_div(safe_div(cur["sga"], cur["revenue"]), safe_div(prior["sga"], prior["revenue"]))
    lvgi = safe_div(safe_div(cur["long_term_debt"] + cur["current_liabilities"], cur["total_assets"]),
                    safe_div(prior["long_term_debt"] + prior["current_liabilities"], prior["total_assets"]))
    tata = safe_div(cur["net_income"] - cur["cfo"], cur["total_assets"])

    ratios = {"DSRI": dsri, "GMI": gmi, "AQI": aqi, "SGI": sgi, "DEPI": depi,
             "SGAI": sgai, "LVGI": lvgi, "TATA": tata}
    unresolved = [k for k, v in ratios.items() if v is None]
    if unresolved:
        return {"refused": f"zero-denominator ratio(s), cannot compute M-score: {', '.join(unresolved)}"}

    m = (-4.84 + 0.92 * dsri + 0.528 * gmi + 0.404 * aqi + 0.892 * sgi
         + 0.115 * depi - 0.172 * sgai + 4.679 * tata - 0.327 * lvgi)
    return {"m_score": round(m, 3), "ratios": {k: round(v, 3) for k, v in ratios.items()},
           "manipulation_flag": m > BENEISH_MANIPULATION_THRESHOLD}


def altman_distress_band(altman_z):
    if altman_z is None:
        return None
    if altman_z < ALTMAN_DISTRESS_THRESHOLD:
        return "distress"
    if altman_z < ALTMAN_SAFE_THRESHOLD:
        return "grey_zone"
    return "safe"


def forensic_risk_check(altman_z, beneish_inputs):
    """Combines the Altman classification (pass-through from FMP, never re-derived) with a
    fresh Beneish M-Score into one FORENSIC_RISK verdict. Either signal alone is enough to
    flag -- a company can be solvent (safe Altman) and still be actively massaging earnings
    (a manipulation-flagged Beneish), and the reverse."""
    band = altman_distress_band(altman_z)
    beneish = beneish_m_score(beneish_inputs.get("cur", {}), beneish_inputs.get("prior", {})) \
        if beneish_inputs else {"refused": "no beneish_inputs supplied"}
    m_flag = beneish.get("manipulation_flag")
    distress = band == "distress"
    forensic_risk = bool(m_flag) or distress
    return {"altman_z": altman_z, "altman_band": band, "beneish": beneish,
           "forensic_risk": forensic_risk,
           "bypass_bullish_signals": forensic_risk,
           "note": ("FORENSIC RISK -- " + ", ".join(
                       ([f"Altman in {band}"] if distress else [])
                       + (["Beneish flags manipulation risk"] if m_flag else []))
                    if forensic_risk else "no forensic flags")}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def cmd_valuation(args):
    """One compute stage, one input file: --statements-json is a dict keyed by ticker, each
    value carrying whatever subset of the three checks' inputs the caller fetched (see the
    module docstring for the full per-ticker shape). Any check missing its inputs for a given
    ticker is skipped for that ticker only and named in that ticker's data_quality -- never
    silently dropped, never guessed. Writes compute_valuation.json to the run dir."""
    statements = load_json(args.statements_json, default=None)
    if statements is None or not isinstance(statements, dict):
        emit({"error": f"--statements-json must be a ticker-keyed JSON object, got: {args.statements_json}"})
        return

    rows = {}
    stretched, weakened, forensic = [], [], []
    for ticker, row in statements.items():
        if not isinstance(row, dict):
            continue
        dcf = reverse_dcf_check(row, args.terminal_growth_pct, args.forecast_years, args.stretch_gap_pp) \
            if any(k in row for k in ("enterprise_value_usd", "fcf0_usd", "wacc_pct", "fcf_history")) else None
        roic = roic_wacc_check(row, args.market_risk_premium_pct) \
            if any(k in row for k in ("roic_pct", "beta", "total_equity_usd")) else None
        forensic_res = forensic_risk_check(row.get("altman_z"), row.get("beneish_inputs")) \
            if (row.get("altman_z") is not None or row.get("beneish_inputs")) else None

        rows[ticker] = {"reverse_dcf": dcf, "roic_wacc": roic, "forensic": forensic_res}
        if dcf and dcf.get("valuation_stretched"):
            stretched.append(ticker)
        if roic and roic.get("thesis_downgrade_signal") == "WATCH":
            weakened.append(ticker)
        if forensic_res and forensic_res.get("forensic_risk"):
            forensic.append(ticker)

    out = {"as_of": args.today, "rows": rows,
          "valuation_stretched": sorted(stretched), "roic_weakened": sorted(weakened),
          "forensic_risk": sorted(forensic),
          "note": ("valuation_stretched -> suppress new BUY proposals (smith-strategist); "
                   "roic_weakened -> downgrade thesis to WATCH regardless of earnings beats "
                   "(smith-thesis); forensic_risk -> bypass normal Stage-1 bullish signals "
                   "(smith-quality/smith-strategist).")}
    if args.run_dir:
        safe_write(os.path.join(args.run_dir, "compute_valuation.json"), out)
    emit(out)


def build_subparser(sub):
    v = sub.add_parser("valuation", help="reverse-DCF, ROIC-vs-WACC and forensic (Beneish/Altman) checks")
    v.add_argument("--run-dir", default=None)
    v.add_argument("--statements-json", required=True)
    v.add_argument("--today", default=None)
    v.add_argument("--terminal-growth-pct", type=float, default=TERMINAL_GROWTH_PCT_DEFAULT)
    v.add_argument("--forecast-years", type=int, default=FORECAST_YEARS_DEFAULT)
    v.add_argument("--stretch-gap-pp", type=float, default=REVERSE_DCF_STRETCH_GAP_PP_DEFAULT)
    v.add_argument("--market-risk-premium-pct", type=float, default=MARKET_RISK_PREMIUM_PCT_DEFAULT)
    v.set_defaults(fn=cmd_valuation)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    build_subparser(sub)
    a = p.parse_args()
    if not a.today:
        from datetime import date
        a.today = date.today().isoformat()
    a.fn(a)
