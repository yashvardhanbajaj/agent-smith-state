# Signal Scanner — DEEP — 2026-07-20 pre-open (gate: STABILIZING)

## Core Technical
- ASML — STRONG UPTREND pos=0.81 — 4.5% of book — target $2123.53 (+17.7%)
- AMAT — STRONG DOWNTREND, day -5.57% (semicap-wide selloff w/ LRCX -2.4%, TER flat but -26% 1m) — 2.7% of book — target $623.06 (+15.0%)
- ORCL — BREAKDOWN pos=0.02, at 52wk low — 1.3% of book — target $251.85 (+49.8%) — unchanged, open_flags proposal stands
- NOW — STRONG DOWNTREND pos=0.17 — 0.8% of book — target $141.64 (+27.1%) — unchanged

## Momentum / Swing (new today)
- AMAT — MOMENTUM+VOLUME: day -5.57%, catalyst = broad semicap sell-off, volume elevated — 2.7% of book — target $623.06 (+15.0%)
- IREN — pos=0.304, just above the 0.30 oversold-bounce cutoff; upside +58.5% is huge but not flagging given proximity to threshold and mixed recent news

## Policy Impact (persisting — still pending, no resolution since watermark)
- ASML — US export-control exposure to China (~20% of revenue) — pending since 07-14
- AVGO — EU antitrust review on VMware licensing — pending since 07-15

## Insider Activity
- CIEN — CONFIRMED cluster sale, CEO + 3 execs, filed 7/17 (per open_flags) — 3.3% of book — target $565.71 (+33.8%) — unchanged, trim candidate stands
- Deep-mode Form-4 pull on top holdings: SNDK (CLO Shek recurring ~600sh 10b5-1 sales, CTO Ilkbahar June sales, all routine, latest filing 07-02), GLW (CEO Weeks 100k-sh option exercise+sale 06-09, directors' routine RSU awards 07-01), NVDA (new-director Form 3 filed 07-15, director gift of 500k sh 07-01 — not a sale), MU (EVP Arnzen ~28k-sh cluster sale filed 07-06, sizable but already priced in). Nothing filed after watermark (07-18) for any of these four.

## Peer-Relative Strength (first full seed — peer_map was empty coming in)
PEER LEADER:
- META +20.2% 1m vs XLK -8.3% — leading, not riding — 3.3% of book — target $822.69 (+21.5%)
- NOW +16.9% 1m vs XLK -8.3% — matches open_flags whipsaw watch — 0.8% of book — target $141.64 (+27.1%)
- NVDA +11.9% 1m vs SMH -15.7% — 6.3% of book — target $302.31 (+32.9%)

PEER LAGGARD:
- IREN -35.7% vs XLK -8.3% — 2.2% of book — target $80.93 (+58.5%)
- NBIS -29.7% vs XLK -8.3% — 2.7% of book — no target avail (data gap)
- ORCL -23.1% vs XLK -8.3% — compounds BREAKDOWN — 1.3% of book
- ARM -23.5% vs SMH -15.7% — 1.4% of book — target $303.97 (+12.1%)
- MRVL -23.6% vs SMH -15.7% — 3.4% of book — target $253.69 (+25.6%)
- SNDK -22.3% vs SMH -15.7% — largest position, 10.5% of book — see open_flags
- COHR -13.1% vs SMH — 2.1% of book — target $391.45 (+29.1%)
- VRT -12.2% vs XLI — 3.7% of book — target $380 (+23.8%)
- CLS -10.8% vs XLK — 3.9% of book — target $448 (+32.7%)
- TER -10.7% vs SMH — NEW laggard — 2.5% of book — target $426.35 (+24.4%)
- MU -9.5% vs SMH — 4.4% of book — target $1491.95 (+43.1%)
- QCOM -8.4% vs SMH — NEW laggard — 2.7% of book — target $222.73 (+22.9%)

CHANGED: ASML and AVGO drop out of PEER LEADER — ASML +6.2% vs SMH -15.7% (below +8% threshold), AVGO +5.8% vs SMH -15.7% — both merely tracking the sector bounce, not leading it.

## Target Gap (≥15%; unchanged unless flagged)
NEW: ASML +17.7% (newly crosses threshold, wasn't flagged before)
NARROWING below 15%, watch for resolution: LRCX 14.5%, AMAT 15.0% (borderline), STM 11.2%, ARM 12.1%
Unchanged (already tracked in journal/signal_history, still ≥15%): GLW +27.8%, TSM +23.4%, MU +43.1%, MRVL +25.6%, QCOM +22.9%, CLS +32.7%, CIEN +33.8%, VRT +23.8%, TER +24.4%, COHR +29.1%, LITE +33.7%, IREN +58.5%, META +21.5%, AVGO +29.3%, NVDA +32.9%, GOOG +19.1%, ORCL +49.8%, NOW +27.1%

## Unchanged repeats (no material change since 07-18)
ORCL (BREAKDOWN, NEW HEADWINDS), NOW (STRONG DOWNTREND, OVERSOLD BOUNCE), AMAT (STRONG DOWNTREND, TARGET GAP, INSIDER ACTIVITY), ASML (STRONG UPTREND, POLICY IMPACT), plus the full unchanged TARGET GAP list above and all PEER LAGGARD names already carried from prior run (SNDK, MU, MRVL, VRT, ARM, COHR, IREN, NBIS, CLS, ORCL).

## Still pending (older news, no resolution)
- ASML export-control risk (since 07-14)
- AVGO EU antitrust review (since 07-15)
- ORCL debt/FCF concerns (since 07-18, open_flags)
- SNDK peer-laggard despite thesis flip to "strengthening" (since 07-14, open_flags)
- CIEN insider cluster-sale reversing deploy-to-trim (since 07-18, open_flags)
- NOW 62.5% trim vs strong peer-RS whipsaw watch (since 07-17, open_flags)

## Journal — new actionable flags
- AMAT MOMENTUM+VOLUME (day -5.57%, sector-wide semicap selloff) — new flag, price_at_flag = $529.66, target $623.06

## Data quality
- DRAM: feed returned 52wk_low=0 (implausible) — guardrail applied, pos set to 0.5, excluded from core-technical buckets.
- SNDK, NBIS: analyst_forecast target/upside missing from feed — TARGET GAP citation omitted for these two.
- TSM, ASML excluded from insiderTrades pull — foreign private issuers, no Form-4 filings expected.
- form13F skipped this run (budget) — institutional-stake-change view not refreshed; candidate for known_gaps registry.
- Only SNDK/GLW/NVDA/MU sampled for Form-4 this run (4 of top-8 domestic-issuer holdings by weight); CLS/VRT/MRVL/COHR not yet pulled — rotate coverage next deep run.
- ~13 tool calls used this run, within soft cap.

```json
{"signal_history":{"changed":{"ASML":["STRONG UPTREND","TARGET GAP","POLICY IMPACT"],"AVGO":["TARGET GAP","POLICY IMPACT"],"QCOM":["TARGET GAP","PEER LAGGARD"],"TER":["TARGET GAP","PEER LAGGARD"],"AMAT":["STRONG DOWNTREND","TARGET GAP","INSIDER ACTIVITY","MOMENTUM+VOLUME"]},"unchanged_count":24},
 "news_watermark":"2026-07-20","resolved_flags":[],"new_flags":[],
 "journal_new":[{"date":"2026-07-20","ticker":"AMAT","bucket":"MOMENTUM+VOLUME","price_at_flag":529.66,"analyst_target":623.06}],
 "peer_map_updates":{"SNDK":{"peer_etf":"SMH","label":"memory"},"GLW":{"peer_etf":"SMH","label":"optical-interconnect"},"NVDA":{"peer_etf":"SMH","label":"semicap/GPU"},"TSM":{"peer_etf":"SMH","label":"foundry"},"ASML":{"peer_etf":"SMH","label":"semicap"},"MU":{"peer_etf":"SMH","label":"memory"},"LRCX":{"peer_etf":"SMH","label":"semicap"},"CLS":{"peer_etf":"XLK","label":"hyperscaler-EMS/compute"},"VRT":{"peer_etf":"XLI","label":"DC-infra"},"MRVL":{"peer_etf":"SMH","label":"semicap/optical-interconnect"},"META":{"peer_etf":"XLK","label":"hyperscaler/compute"},"CIEN":{"peer_etf":"SMH","label":"optical-interconnect"},"NBIS":{"peer_etf":"XLK","label":"AI cloud/hyperscaler"},"AMAT":{"peer_etf":"SMH","label":"semicap"},"QCOM":{"peer_etf":"SMH","label":"semicap/compute"},"AMD":{"peer_etf":"SMH","label":"semicap/GPU"},"TER":{"peer_etf":"SMH","label":"semicap"},"IREN":{"peer_etf":"XLK","label":"AI compute/mining"},"COHR":{"peer_etf":"SMH","label":"optical-interconnect"},"AVGO":{"peer_etf":"SMH","label":"semicap/compute"},"LITE":{"peer_etf":"SMH","label":"optical-interconnect"},"GOOG":{"peer_etf":"XLK","label":"hyperscaler/compute"},"STM":{"peer_etf":"SMH","label":"semicap"},"ARM":{"peer_etf":"SMH","label":"semicap/compute IP"},"ORCL":{"peer_etf":"XLK","label":"hyperscaler/compute"},"NOW":{"peer_etf":"XLK","label":"hyperscaler/compute"},"GEV":{"peer_etf":"XLU","label":"power-infra"}},
 "data_quality":["DRAM 52wk_low=0 implausible, pos set 0.5 via guardrail","SNDK/NBIS missing analyst target/upside","TSM/ASML skipped for insiderTrades (foreign private issuers)","form13F skipped this run for budget","only 4 of top-8 domestic holdings sampled for Form-4 (SNDK/GLW/NVDA/MU)","~13 tool calls used, within soft cap"]}
```
