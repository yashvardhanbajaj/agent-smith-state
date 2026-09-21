# smith-signals — DEEP — 2026-09-21 13:57Z (US intraday 09:58 ET)
Session: intraday (STABILIZING gate; SPX +0.72%, NDX +1.22%, SMH +2.04%). Book = 27 names. Move arithmetic from compute_buckets.json (rel_sigma SD 1.047, in band). Weights = holdings_trim (post today's fills: NOW 6sh, NBIS 6sh).
News source for every line below = INDmoney get_us_stocks_details news feed (dated titles, NO outlet/URL supplied). See data_quality.

## Today's two buys — size context
- NOW +1 @135.95 (limit) — 6sh, 2.38% of book. Live $138.29 (+1.7% vs fill). ZERO buckets fire: not oversold (pos 0.50, 5d -3.1%), no TARGET GAP (mean $142.97 script / $144.28 INDmoney n=29 => +3.6% to +4.3%). Signals give no support for the add and none against; peer +1.27pp vs XLK (+0.12σ). Newsflow 09-14/15 (analyst upgrades, AI Control Tower) predates fill.
- NBIS +1 @225.81 (market) — 6sh, 3.90% of book. Live $225.34 (flat vs fill). Only bucket is TARGET GAP (+27.7% to $288.33). Peer -2.45pp vs XLK (-0.17σ) = neutral. Thesis WATCH carried (G98 cluster mismatch, Vineland unresolved). Dated positive: GPU price hike up to 21% eff. 10-01 (2026-09-17, INDmoney feed). Dated negative: shares fell on risk-off tone 2026-09-14. Not a signals-driven add.

## Core / trend
- AMD — BREAKOUT (pos 1.00, at 52wk high $608) + STRONG UPTREND — 1.75% (1sh). +8.6% day = 2.31x its 3.71% ATR (threshold 5.56%), 5d +23.2%, 1m +29.5%, RSI14 72.1. Mean target $616.51 (n=35) => only +1.3%: priced at consensus.
- MU — STRONG UPTREND (pos-leg only, pos 0.812; day +2.8% = 0.74x ATR, NOT a move signal) — 6.03%. Target $1,513.11 (n=30) +44.4%.
- TSM — STRONG UPTREND (pos-leg only, pos 0.809; day 0.37x ATR) — 8.83%. Target $551.26 +25.8% (INDmoney $552.26 n=8).
- LITE — STRONG UPTREND (pos 0.887; day 0.83x ATR vs 9.4% threshold, pos-leg) — 2.82% (1sh). Target $1,149.38 (n=17) +17.3%. 5d +17.3%.
- SKHY — STRONG UPTREND (pos 0.849 using script wk52 124.80-199.87 from daily bars; INDmoney raw 52wk_low=0 NOT used) — 0.54% (1sh, unreconciled fill per desk memory). Target $249.7 +32.5%.
- Dropped vs prior run: AMAT no longer STRONG UPTREND / MOMENTUM+VOLUME (pos 0.48). MRVL no longer TARGET GAP (+13.7% < 15%).
- BREAKDOWN / STRONG DOWNTREND: none.

## Swing setups (judgment leg resolved)
- AMD — MOMENTUM+VOLUME PROMOTED. Measurable leg 2.31x ATR. Volume: 11.15M in first ~30 min vs 19.06M 20d avg (58% of a normal full day; 11.9M per yfinance) = volume elevated. Catalyst dated: GPU/CPU price-hike reports + next-gen GPU rumor (2026-09-17/18, INDmoney feed; hike is "potential 10%", rumor-grade). Size: 1.75% starter — the flag is not a sizing case. Thesis is WATCH (strategist's own 08-12 refusal unresolved).
- AMD — OVERBOUGHT PULLBACK? DROPPED: pos 1.0 but only 1.3% below mean target, and no negative news/downgrade in feed. Note as extension risk, not a fired bucket: RSI 72.1, +23% in 5d, at consensus PT.
- LITE — OVERBOUGHT PULLBACK? DROPPED: pos 0.887 but +17.3% to target and no negatives dated after watermark (09-14 sell-off was GLW-ATM contagion, since recovered).
- OVERSOLD BOUNCE / REVERSAL BUY WATCH: none (lowest pos in book: KLAC 0.396, GLW 0.404, AMAT 0.48 — none <=0.30).

## Peer-relative (rel_sigma from script; peer ETF stated)
- AMD PEER LEADER — +25.56pp vs SMH, +3.00σ (ATR 3.71%); 1m abs +29.5% — genuinely leading, not sector beta.
- BE PEER LEADER — +39.3pp vs XLU, +2.68σ; 1.54%. Peer correlation assumption weak for this mapping (fuel-cell vs utilities ETF). S&P 500 inclusion effective today (catalyst:511c7b86ce) partly priced. Target $280.24 +4.7% (n=18).
- SKHY PEER LEADER — +11.77pp vs SMH, +1.12σ; Korea beta share unmeasured. 0.54%.
- QCOM PEER LEADER (marginal) — +9.75pp vs SMH, +1.02σ; 2.63%. Target $193.90 +6.2% (n=26). Dated: Amazon data-center commitment (2026-09-15/17), Altimeter 1.88M-share stake (2026-09-16, 13F-type, INDmoney feed) vs margin-pressure headline 2026-09-17.
- AMZN PEER LAGGARD — -7.2pp vs XLK, -1.44σ (ATR 2.16%); 3.66%. Target $328.17 +28.9% (n=40). Thesis WATCH; +2sh 09-18 already in. Same laggard as prior run, unchanged.
- AMAT PEER LAGGARD — -12.16pp vs SMH, -1.40σ; 5.25%. Target $640.89 +40.8% (n=28). Reported FQ3 record $9.1B (+25% y/y, 2026-09-19 feed); the underperformance is price reaction to the print, not the results. Unchanged from prior.
- ASML PEER LAGGARD (NEW) — -7.7pp vs SMH, -1.17σ on a 2.87% ATR (low-vol name, so a small raw gap trips it); 8.49%, largest laggard weight. Target $2,157.62 +28.1% (INDmoney $2,137.63 n=6). No name-specific negative dated after watermark; Q3 bookings 2026-10-14 are the binary.
- Blind-spot check: no name has raw rel <= -25pp. Worst raw: AMAT -12.2, CIEN -11.0, WDC -9.6 — all flagged or inside sigma; nothing swallowed.

## TARGET GAP >=15% (all mean-target based; upside = target vs price, script)
- Unchanged repeats (no new news/analyst action, pos moved <0.05): TSM, MU, GOOG (+20.9%), TER (+20.1%), KLAC (+29.2%), APH (+25.0%), VRT (+35.8%), MSFT (+15.7%), CLS (+38.5%), WDC (+50.5%), NBIS, GEV (+29.6%), STM (+47.0%), COHR (+26.8%), GLW (+24.8%), ALAB (+19.5%), LITE, CIEN (+38.2%), SKHY, AMZN, AMAT, ASML.
- Widest: WDC +50.5%, STM +47.0%, MU +44.4%, AMAT +40.8%, CLS +38.5%, CIEN +38.2%. Target gaps are analyst-optimism gaps; none is corroborated by a fresh upgrade today.

## Earnings proximity (>5% weight, <=7d): NONE inside window
- MU (6.03%): FQ4 print date CONFLICT — calendar/yfinance 2026-10-01, INDmoney feed 2026-09-30 (2026-09-21 item). Treat as 9-10 days out, unconfirmed by company. Into the print: pos 0.812, 5d +13.4%, 10d +3.1%; memory records implied move ~10.2%. Next run falls inside the 7d window.
- ASML 10-14 (8.49%), TSM 10-15 (8.83%) — outside window.

## Tailwinds / Headwinds / Policy / Insider
- NEW TAILWINDS / HEADWINDS: none fired. Only 09-21-dated items counted (watermark = 2026-09-21). Candidates deduped: MSFT 09-21 item bundles "India cloud region $20.5B" + "analyst PT raises" in one feed summary = a single syndicated write-up, capex commitment not demand evidence, and MSFT is +0.36% — not counted. AMZN 09-21 item cites "$100B Anthropic deal" alongside Q2 recap; date/origin of that deal not established in the feed — not counted (flag for catalyst desk).
- POLICY IMPACT: nothing new after watermark. Pending: AMZN EU price-parity scrutiny (2026-09-18) and FTC Prime refund revision (2026-09-19), both pre-watermark.
- INSIDER (deep mode): FMP insiderTrades returned ACCESS DENIED (plan tier) on first call; not retried, so no Form-4 pull for the top-10. Only news-derived: LITE CEO share withholding for taxes (2026-08-18) = not a sale; Altimeter QCOM stake 2026-09-16 (institutional, feed). No exec buying/selling evidence either way. 13F not attempted (same plan family).

## Still pending (older stories, one clause each)
- CXMT G5/HBM3E vs MU/SKHY/ASML/AMAT/TER (catalyst:2b516b39a1, bd376b82a7) — MU 09-21 item repeats "CXMT mass production begun" (LPDDR5X), nothing new.
- GLW $2B ATM vs COHR/LITE/GLW — no usage disclosure found; GLW +3.3% today.
- Amodei "pace the frontier" essay — sentiment-only, SMH +2.0% reversing; no capex cut found.
- GEV: GLJ Sell $470 vs raised FCF/revenue guide (09-14) and CEO $200B backlog outlook (09-16).
- CIEN: Investor Forum 3-yr targets (30% revenue growth, 50% GM by FY29) and PT raises, 2026-09-17 (feed) — positive, pre-watermark; dust position ($3, 0.01%) so no size.
- ALAB: Q2 beat (08-05); +7.2% today (1.29x ATR) no new story; 5d +27%.
- Investor note: INDmoney `upside_per` is measured against the TARGET, not price (e.g. CIEN says 28.35% where target/price = +39.6%); this file uses target/price.

## Journal
- journal_new: AMD MOMENTUM+VOLUME @608.56 (re-fire; an entry from 2026-09-17 is still open at 4 days). No other actionable swing setup.
- Scoring: bucket_hit_rates empty (window since 2026-09-21) — no grades to cite.

## Repeat suppression
- signal_history deltas: AMD (+BREAKOUT, +MOMENTUM+VOLUME), AMAT (-MOMENTUM+VOLUME, -STRONG UPTREND), ASML (+PEER LAGGARD), MU (+STRONG UPTREND), TSM (+STRONG UPTREND), QCOM (+PEER LEADER), MRVL (-TARGET GAP). 20 held names unchanged.
