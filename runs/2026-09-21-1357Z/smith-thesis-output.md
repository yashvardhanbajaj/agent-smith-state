# smith-thesis 2026-09-21-1357Z (deep, intraday 09:58 ET, Wave 2)
Tail (verbatim JSON): /Users/yb/Claude/AgentSmith/runs/2026-09-21-1357Z/out_thesis.json
Inputs read: slice, Wave-1 tails (catalyst, signals, watchlist), prior_findings, memory, HBMTracker consumer_view (staleness_days 0), ORCL 10-Q via smith_edgar.

## 1. Thesis table (deep: full table for names in question; 8 quiet names unchanged, 7 reviewed_unchanged)
No status flips this run. One new entry, eleven evidence refreshes, one correction.
- ORCL (NEW, M1.8) -- OCI/AI-cloud seller on a huge contracted backlog, financed by capex, debt and equity -- WATCH -- FOR: FQ1 FY27 revenue $19.345B, OCF $23.1B (10-Q, primary); FY27 guide >= $90B, RPO ~$664B (secondary) / AGAINST: FCF -$5.4B (OCF 23.103 - capex 28.499), equity $42.5B -> $66.8B in the quarter (~$20B equity sale, secondary size), interest cover 4.7x, S&P downgrade, DC loans 89-91c (secondary) -- verified: primary (financials only). No beat/miss call: consensus unverified; smith-earnings owns it.
- MU -- memory, CXMT share risk -- WATCH (unchanged) -- CORRECTED: the stored line put HBM3 stack-derived flat 0.0% on HBM3E. HBM3E $12.4 and HBM4 $16.0 are single contract_quote points, no within-basis trend. FOR: analyst target +44%; CXMT HBM3E trial-only, 2027 mass production. AGAINST: CXMT 9.5% Q2 DRAM share, G5 LPDDR5X volume, MU residual on HBM4 -- unverified.
- SKHY -- HBM4 leader -- WATCH (unchanged) -- FOR: peer leader +11.77pp vs SMH (+1.12 sigma), buckets computable from bars wk52 / AGAINST: 60-70% is a starting allocation (all three vendors certified), Korea beta unmeasured, fill unreconciled.
- AMD -- WATCH (unchanged) -- FOR: +8.6% to 52wk high, +3.0 sigma vs SMH, volume 58% of 20d avg in 30 min / AGAINST: only +1.3% below mean target $616.51, RSI 72.1, guide_below_consensus (08-11) and the strategist's 08-12 refusal unresolved. Momentum is not thesis evidence. Text corrected 2sh -> 1sh.
- NBIS -- WATCH (unchanged), evidence_against widened -- +1sh @225.81 today into unresolved WATCH (add-ahead-of-resolution pattern), ORCL read-across (loans 89-91c, equity funding), Vineland and floating-rate funding still open.
- NOW -- STRENGTHENING held, flagged decaying -- edge vs XLK +6.70pp (09-14) -> +1.27pp; only +3.6% to mean target; today's +1sh @135.95 had zero buckets. Slides to INTACT next run without fresh evidence.
- AMZN -- WATCH -- laggard narrowed to -7.2pp / -1.44 sigma; the "$100B Anthropic deal" item has no established origin, so not entered as evidence.
- ASML -- WATCH -- new PEER LAGGARD -7.7pp / -1.17 sigma (low-ATR name), no name-specific negative; Q3 bookings 10-14; summit added.
- AMAT, KLAC, TER, TSM, QCOM -- strengthening, unchanged -- Trump-Xi summit 09-24 added to evidence_against (two-sided, nothing quantified). TSM's against-side was EMPTY on 8.83% and is now populated (summit; Nvidia-OpenAI financing concentration). QCOM: peer gap reversed to leader, intact alternative retired.
- reviewed_unchanged: GLW, COHR, LITE, GEV, APH, MRVL, CIEN. APH final = STRENGTHENING (primary, 07:02Z restore supersedes the M2.3 intact revision).
- Untouched (not re-read, no new evidence): VRT, STM, WDC, GOOG, MSFT, BE, CLS, TER-adjacent quiet names.

## 2. Factor clusters (% of invested equity, holdings_trim 2026-09-21; drift vs policy bands is compute_drift's call, denominators differ)
- AI Semis/Fabs 37.52: TSM 8.83, ASML 8.49, TER 5.36, AMAT 5.25, KLAC 5.21, QCOM 2.63, AMD 1.75
- Compute/Hyperscaler 17.87: GOOG 6.03, MSFT 4.28, NBIS 3.90, AMZN 3.66
- AI Networking/Optics 17.05: APH 4.57, MRVL 3.60, LITE 2.82, ALAB 2.82, COHR 1.89, GLW 1.34, CIEN 0.01
- AI Power/Cooling/DC Infra 8.60: VRT 4.30, GEV 2.76, BE 1.54
- AI Memory/Storage 6.57: MU 6.03, SKHY 0.54
- Compute/Hyperscaler OEM 3.97: CLS. AI Storage/HDD 3.82: WDC. Enterprise Software 2.38: NOW. Analog/Industrial 2.21: STM
- AI-capex chain combined: 95.4%. Co-movement: SMH +2.04% today, semis-led rally, AMD/BE/SKHY the outliers; no cluster diverged.

## 3. Single-factor verdict
This is one bet: 95.4% of invested equity rides datacenter AI capex, and the 4.6% outside it (NOW 2.38%, STM 2.21%) is also the weakest-evidenced sleeve (NOW's edge has faded, STM is on a guide_below_consensus WATCH). A capex pause hits about 19 of every 20 dollars at once. Hyperscaler names (GOOG/MSFT/AMZN, 13.97%) are demand-side of the same trade, not a hedge. The largest genuinely uncorrelated slice is NOW, and it is a 2.4% satellite. The live risks today are not demand: they are financing structure (GLW ATM, NBIS floating-rate debt, ORCL equity raise) and a dated China-policy event on the 37.5% semis cluster.

## 4. HBMTracker reconciliation (MU, SKHY held; EWY/DRAM not held; SNDK out of scope, WDC judged on NAND/HDD)
staleness_days 0; hbm3 price staleness 5d. Corrections C1/C2 read.
- HBM3E: $12.40/GB (2026-09-20), basis contract_quote, tier1-corroborated. Within-basis trend: NONE (single point). Cross-basis comparison REFUSED (cross_basis_change_is_meaningless = true); the 18.5 -> 15.0 -> 12.4 path mixes houses/dates. The 0.0% flat trend is HBM3 stack-derived $9.0/GB, not HBM3E. Verdict for MU: no_action (branch c); WATCH rests on CXMT share, not ASP.
- HBM4: $16.00/GB (2026-09-20) contract_quote, single point, ~29% above HBM3E same date/basis; stack-derived +14.29% (07-19 to 08-05) is a different basis, not chained. SKHY: no_action; supply_structure (SK hynix 60-70%, Samsung 25-30%, MU residual) is why price helps SKHY more than MU.
- Forecasts as context only: 2027 HBM contract hike 80-150% (TrendForce 2026-06-02); DDR5 vs HBM3E profitability crossover (TrendForce 2025-12-18 / 2026-04-21).

## 5. Desk
Answered M1.8 (ORCL): thesis given, WATCH; universe-bar consequences in comms. Tells sent: catalyst (ORCL financing read-across to NBIS), strategist (NBIS/NOW buys), quality (ORCL OCF/leverage). No asks.
