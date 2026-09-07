# smith-earnings — 2026-09-07 (DEEP)

Session: closed_holiday (Labor Day). Window checked: next 5 trading days = 2026-09-08, 09-09, 09-10, 09-11, 09-14.

## 1. Held names reporting inside 5 trading days

**NONE.**

Checks run this session:
- `yfinance get_earnings_calendar` 2026-09-08 → 2026-09-15: returned an EMPTY array. Treated as a data gap, not as evidence of an empty window.
- FMP `calendar/earnings-calendar` 2026-09-08 → 2026-09-14: single name, **ADBE 2026-09-10** — not held.
- Same feed widened to 2026-10-02 returned only 4 names total (NKE, COST, FDX, ADBE) and OMITTED MU, which we independently confirmed. The FMP calendar on this plan tier is a large-cap subset and is NOT a completeness check. Logged in data_quality.
- Independent per-name check on the only holding with a plausible September fiscal cadence: **MU next reports 2026-09-30** (stockanalysis.com/stocks/mu, live this run) — 16 trading days away, outside the window.
- Every other holding's last print was late-Jul / Aug 2026 (see earnings_calendar cache), placing the next print in late Oct / Nov. AVGO (Aug-ending fiscal) already reported 2026-09-02; CIEN already reported 2026-09-03.

No implied-move computation performed: nothing reports in the window, so there is no straddle worth pricing. `pre_earnings_flags` carries MU as an early heads-up only, with `implied_move_pct: null` — not an estimate.

## 2. PENDING earnings_facts entries

Scanned all 21 entries in `data_cache.earnings_facts`. **No entry carries `status: "PENDING"`.** NVDA and MRVL are both `status: "VERIFIED"`.

One entry was *materially incomplete* rather than PENDING, and I fixed it:

### AVGO — was a bare verdict with no numbers behind it

Prior stored state (from the 2026-09-06 reverify) was only:
`{"quarter_verdict":"beat","guide_verdict":"in_line","price_reaction_pct":-4.0}`
— no period, no reported_date, no actual, no consensus. That is exactly the shape of an asserted verdict, which is what this desk exists to prevent.

Sourced live this run (`yfinance get_earnings AVGO`, quarterly row `2Q2026`):
- period: **Q3 FY2026** (fiscalQuarter 3Q2026), reported **2026-09-02**
- **EPS actual $3.32 vs consensus $3.238 → +2.53% surprise. The "beat" verdict now has a real number under it.**
- Revenue actual vs consensus: **NOT SOURCED.** stockanalysis.com/stocks/avgo/ and /forecast/ both returned no quarterly actual-vs-estimate table; FMP `earnings-company` is ACCESS DENIED on this plan tier. Stays `null` — no plausible-sounding figure substituted.
- Guide vs consensus: **NOT SOURCED this run.** The prior `guide_verdict: "in_line"` had no consensus figure attached, so I am NOT propagating it. Set to `null` with a data_quality note. Next-quarter (FQ4 FY26) Street EPS is $3.827 (yfinance `currentQuarterEstimate`) but Broadcom guides revenue, not EPS, so this does not settle the guide on its own.

**Price reaction corrected.** Stored -4.0% was not reproducible. Daily closes (yfinance, live):
09-02 $367.24 (print, after close) → 09-03 $357.16 = **-2.75% (1-day)**; → 09-04 $357.90 = **-2.54% (2-day)**.
Revised `price_reaction_pct` to **-2.75**. The fall is a separate field from the quarter verdict and does not touch it — AVGO **beat**, on a sourced consensus, and fell.

EPS surprise history available from the same pull: **+1.60%, +1.32%, +2.53%** (three quarters returned, not four — 3Q2025 row is absent from the feed; `avg_surprise_pct` +1.82% is a 3-quarter average and is labelled as such).

## 3. Definitional standing (no new violations found)

Reviewed the store for beat/miss language derived from price action rather than actuals. Existing entries hold the line correctly:
- COHR Q4 FY26 — beat on revenue and EPS, fell anyway; note explicitly records the 2026-08-13 mischaracterisation.
- KLAC Q4 FY26 — EPS beat +5.1%, stock -9.6% AH; kept separate.
- BABA Jun-qtr — revenue beat +0.23% / EPS miss -20.52%, stated as two facts.
- NVDA Q2 FY27 — quarter beat, guide flagged `guide_below_consensus_china_dc`, drift -5.3% (2d) held in its own field.
- MRVL Q2 FY26 — quarter beat, guide ABOVE consensus, stock still fell; `drift_5d_avg` deliberately null because the 05-27 melt-up contaminates the mean, median +5.77% used instead.
AVGO now joins that list rather than sitting as an unsupported verdict.

## 4. Data quality

1. `yfinance get_earnings_calendar` returns an empty array for the 09-08→09-15 range — cannot be used alone to clear a window.
2. FMP `calendar/earnings-calendar` on this plan is a large-cap subset (missed MU entirely over a 3.5-week range). Per-name verification remains the only reliable clear.
3. FMP `calendar/earnings-company` is ACCESS DENIED on this plan tier — new denial, added to the do-not-retry list alongside `statements`, `earningsTranscript`, `quote`.
4. AVGO revenue actual/consensus and guide-vs-consensus unsourced; both null, not estimated.
5. AVGO surprise history is 3 quarters, not 4.
6. Ten holdings still have no forward earnings date in `earnings_calendar` at all (ASML, BE, STM, MU, INTC, TSM, WDC, SKHY, APH, GLW, MSFT, LITE, ALAB, IREN, SMCI, FSLR, COHR, AMKR-adjacent). MU is now dated 2026-09-30 (unconfirmed source = stockanalysis listing). The rest are outside any 5-day window and were not fetched.
