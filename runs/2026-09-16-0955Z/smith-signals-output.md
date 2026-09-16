# Smith Signals — 2026-09-16 pre-open (05:56 ET) — FOMC decision day

Context: yesterday (09-15) was an FOMC-eve selloff (Amodei "pace the frontier" essay, GLW $2B dilution,
GEV GLJ Sell initiation, hawkish 84-88% hike-odds prints). Overnight: Asia up across the board (KOSPI
+1.37%, Nikkei +0.69%, TAIEX +0.74%), VIX 16.98 (-1.28%), SMH premarket +1.34% (549.37 vs 542.11 close),
ES +1.08%/NQ +1.43%. Gate: STABILIZING. FOMC decision ~14:00 ET today. Buckets below are compute_buckets.json's
snapshot (deterministic, script-owned); live quotes fetched ~08:46 ET show several names have moved further
pre-market since that snapshot — noted as color, not used to override bucket firing.

## HEADLINE — yesterday's selloff-driven technical signals are clearing
9 names that carried STRONG DOWNTREND / MOMENTUM+VOLUME? / PEER LAGGARD yesterday show NONE of those today,
only the persistent TARGET GAP: **ASML, GEV, KLAC, TER, AMAT, APH, STM, GLW, CIEN**. This tracks the
overnight bounce, not new fundamentals — none of these have a fresh (post-09-15) name-specific catalyst;
GLW's dilution overhang and GEV's GLJ Sell call are structural (expire 09-29) and untouched by the bounce.
Live premarket color: ASML +1.04%, GEV +0.92%, TER +1.11%, COHR +1.75%, CIEN +4.6% (biggest premarket mover
in this cluster), GLW flat, STM +0.29%, AMAT -0.72%, APH -1.15%, KLAC -0.63%.

## STRONG UPTREND
- **AMD** — pos 0.832 (near 52wk high), day_atr_mult 0.36 (well under its 6.07% threshold, not an extreme
  day) — swapped in from PEER LEADER as rel_sigma cooled to +0.62 (was firing peer-leader threshold
  yesterday). 3.02% weight. Mean target $615.07, upside 20.3%. News flow mixed-to-positive, nothing new
  since watermark (09-14 "AI concerns" headline still pending, offset by a string of positive
  data-center/demand stories through 09-12).

## PEER LEADER
- **QCOM** — rel_sigma +2.52 (rel_strength +21.1pp vs SMH), unchanged from yesterday. 2.80% weight. Mean
  target $193.90, upside 2.4% (near-fully priced, no TARGET GAP). Live fetch shows QCOM +4.25% premarket on
  "Qualcomm Stock Rises on Data Center Growth Prospects" (15 Sep) — a real, dated, single-outlet story;
  if that move holds into the open this would approach (not yet cross) its own MOMENTUM+VOLUME threshold.
- **NOW** — rel_sigma +1.63 (+17.7pp vs XLK), unchanged. 1.65% weight. Mean target $142.97, upside 2.1%
  (near target). Grade A/100% (n=1, low-confidence) on its 07-12 OVERSOLD BOUNCE flag.
- **BE** — NEW today (empty yesterday). rel_sigma +1.31 (+19.5pp vs XLU). 1.59% weight. Mean target
  $276.05, upside 2.9%. Driven by the still-pending S&P 500 inclusion catalyst (effective 09-21, expires
  09-28) — not a fresh trigger, the peer-relative math just crossed the +1.0σ line today.

## PEER LAGGARD
- **NBIS** — NEW today (TARGET GAP only yesterday). rel_sigma -1.28 (-22.0pp vs XLK). 3.12% weight.
  Mean target $280.00 (compute_buckets cache; the live API call returned no analyst consensus this run —
  data_quality), upside 32.6%. News: still-pending 09-14 "shares fell on growth risks and risk-off tone"
  (negative) alongside a genuinely positive Palantir partnership (09-08) and a $5.75B convert closed
  (08-27) — net story is a name caught in beta more than a fresh fundamental break.

## OVERSOLD BOUNCE (promoted from the "?" judgment leg)
- **AVGO** — pos 0.254 (near 52wk low band), upside 55.5% per compute_buckets ($531.85 target) — the
  upside>15% leg alone satisfies the bounce criterion, so promoting off the script's "?" flag. 2.02%
  weight. This is a REPEAT of the 09-14 open journal flag (day 3, still unscored) — not a new entry.
  PEER LAGGARD cleared since yesterday (rel_sigma now -0.77, was -1.0-crossing). News is genuinely split:
  positive AI-revenue-growth prints (09-09/09-10/09-11) vs a negative "AI slowdown fears" headline
  (09-14, still pending) — no fresh resolution either way.

## TARGET GAP — swap noted
- **MSFT** — swapped OUT of PEER LEADER (rel_sigma now 0.73, below the 1.0 line) and INTO TARGET GAP
  (upside 15.5%, right at the ≥15% threshold). 1.47% weight, small position. Live day move -1.64%.

## Unchanged repeats (no material change vs 09-15 signal_history)
TARGET GAP only, unchanged: VRT, GOOG, ALAB, TSM, COHR, LITE, CLS, WDC, MRVL, MU, AMZN — all cite the
same mean-target/upside pairs as yesterday's run, no new news crossing the watermark.
PEER LEADER, unchanged: QCOM, NOW (see above, restated for grade context only).

## Still pending (pre-09-15 items carried forward, not new)
- FOMC: 25bp-hike odds 84-88% (CME, as of 09-14); decision + SEP dot-plot today ~14:00 ET.
- GLW: $2bn ATM equity program (Goldman, filed 09-11) — structural dilution overhang, untouched by today's bounce.
- GEV: GLJ Research Sell init, $470 PT (09-14) — contested against GEV's own FY26 guidance raise same day.
- Amodei "We Must Pace the Frontier" essay (09-12) — the sentiment trigger for Monday's AI-infra de-rating; no hyperscaler capex guidance has actually moved.
- BE: S&P 500 inclusion effective 09-21.
- CXMT HBM3E risk-production ahead of 2027 consensus — structural memory-supply watch item, unchanged.

## Insider activity / Policy / New tailwinds-headwinds
No post-09-15-watermark, dated, distinct-event items found for insider activity or new policy catalysts
this scan. TSM's insider-purchase and LITE's CEO tax-withholding items are both pre-watermark and already
logged. No NEW TAILWINDS/HEADWINDS bucket fires — everything found was either already in prior_findings or
dated on/before 09-15.

## Earnings proximity
No >5%-weight holding (VRT 8.46%, ASML 8.43%, GEV 6.59%, GOOG 6.05%, ALAB 5.32%, KLAC 5.04%, TER 5.01%)
confirmed reporting within 7 days from this scan's news; a dedicated earnings-calendar pull is
smith-earnings/smith-watchlist's cache, not re-derived here (budget).

## Data quality
- Compute_buckets.json's snapshot and my ~08:46 ET live fetch diverge on several names' day-move magnitude
  (CIEN +4.6% live vs a ~1.5% implied day_pct in the bucket snapshot; WDC -3.51% live vs ~1.2% implied;
  QCOM +4.25% live vs ~0.8% implied) — normal pre-market drift given market_session=pre-open and thin
  liquidity before the open, not a data error. None of these divergences cross a strong-move threshold, so
  no bucket determination changed; flagging for the record.
- NBIS analyst consensus came back empty (None) from get_us_stocks_details this call; used compute_buckets'
  cached target ($280.00) instead.
- AVGO's live-fetched upside_per (36.21%) does not reconcile with compute_buckets' upside_pct (55.5%) off
  the same target ($531.85); used the buckets figure for internal consistency with pos/rel_sigma math.
