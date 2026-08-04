# Watchlist & Market Context — 2026-08-04 (quick mode)

## Session context
Pre-market risk-on: SPX fut +0.35%, NDX fut +1.13%, most AI-capex names up several % pre-open. Gate = STABILIZING (no urgency signal). AMD reports earnings TODAY after this session — live binary catalyst for the whole book's rotation narrative (AMD is a held position, this is calendar context, not a new-entry setup).

## Watchlist setups (US only, ENTRY setups, held tickers excluded)
Scanned rotation slice (cursor 137→8, wrapped): ONTO, INTC, FSLR, EWZ, VNAM, KTEC, BKH, LAND, PLD, IONQ, RGTI, HOOD, CQQQ, MCHI, FPXI (15 names).

- **RGTI** — watchlist — OVERSOLD BOUNCE: pos 0.08 (52w $12.53–$58.15, live $16.02), mean target $29.65, upside 45.97%. News: HPE quantum collaboration + NSF grant, analysts buy-rated (27 Jul).
- **IONQ** — watchlist — OVERSOLD BOUNCE: pos 0.22 (52w $25.89–$84.64, live $38.85), mean target $68.41, upside 43.21%. News: record Q1 revenue +755% YoY, Northland raised target to $70 (28 Jun).
- **LAND** — watchlist — OVERSOLD BOUNCE / TARGET GAP: pos 0.00 (sitting at 52w low $8.06), mean target $11.00, upside 26.73%, consensus 73% buy.
- **HOOD** — watchlist — OVERSOLD BOUNCE: pos 0.30 (52w $63.52–$153.86, live $90.34), mean target $119.51, upside 24.41%. News mixed (Q2 beat but crypto revenue miss; Cantor trimmed target but kept Overweight, nano-futures launch 03 Aug).
- **ONTO** — watchlist — TARGET GAP: mean target $369.60, upside 27.36%, pos 0.60. Morgan Stanley initiated Overweight, $371 target (15 Jun).
- **INTC** — watchlist — TARGET GAP: mean target $115.27, upside 21.05%, pos 0.58. Strong Q2 (revenue +25%, best in 15yrs) but stock choppy on AI-competition concerns (03 Aug).
- **BKH** — watchlist — TARGET GAP: mean target $85.00, upside 16.2%, pos 0.64, consensus HOLD (44% buy).

No setups: FSLR (pos 0.39, upside 9.0% — below threshold despite positive analyst upgrades), PLD (pos 0.82, upside 8.7%), EWZ/KTEC/VNAM/CQQQ/MCHI (ETFs — no analyst target data, can't score target-gap/breakout).

## Earnings calendar (holdings only)
- **AMD** — 2026-08-04 (TODAY, confirmed) — reports after this session. Live catalyst.
- **CEG** — 2026-08-06 (confirmed).
- **COHR** — 2026-08-12 (confirmed, just outside quick-mode 7-day window but cross-checked per request).
- Cross-check: yfinance `get_earnings_calendar` returned empty for the 08-04–08-12 window; `get_earnings` (EPS history) had no forward-date field to override the cache. All three cached dates stand unchanged, source unchanged.
- MRVL (08-26), AVGO (09-02), NVDA (08-26) remain outside the 7-day quick-mode window — untouched this run.

## Attribution context (consumed from compute_attribution.json, not recomputed)
Value delta +$2,118.04 (FX -$20.57, flow +$278.84, residual market move +$1,859.77 — i.e. move is almost entirely price action, not FX or contributions). Qty changes: BABA +2, ORCL +2. Rolling 1m/3m/6m/12m windows unavailable (only 21 ledger rows). Per known gap G41, flow_usd likely undercounts the LRCX new-entry cash outlay since new positions aren't folded in — noted, not re-derived.

```json
{"watchlist_setups":[
 {"ticker":"RGTI","type":"oversold_bounce","upside_pct":45.97,"pos":0.08},
 {"ticker":"IONQ","type":"oversold_bounce","upside_pct":43.21,"pos":0.22},
 {"ticker":"LAND","type":"oversold_bounce","upside_pct":26.73,"pos":0.00},
 {"ticker":"HOOD","type":"oversold_bounce","upside_pct":24.41,"pos":0.30},
 {"ticker":"ONTO","type":"target_gap","upside_pct":27.36,"pos":0.60},
 {"ticker":"INTC","type":"target_gap","upside_pct":21.05,"pos":0.58},
 {"ticker":"BKH","type":"target_gap","upside_pct":16.2,"pos":0.64}],
 "earnings_calendar_updates":{},
 "watchlist_scan_cursor":8,
 "data_quality":[
   "yfinance get_earnings_calendar returned empty for 08-04..08-12 and get_earnings exposed no forward-date field -- AMD/CEG/COHR cache dates left unchanged (still source=prior).",
   "ETF watchlist names (EWZ, KTEC, VNAM, CQQQ, MCHI, FPXI) carry no analyst target-price data via get_us_stocks_details -- cannot be scored for target-gap/breakout setups.",
   "G41 (known gap, not re-derived here): flow_usd in compute_attribution.json likely undercounts LRCX new-entry cash outlay since new positions aren't folded into flow detection."
 ]}
```
