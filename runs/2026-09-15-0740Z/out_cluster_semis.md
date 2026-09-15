# smith-cluster: AI Semis/Fabs, 2026-09-15 (deep, wave 2)

## What changed since the 09-14 ladder
- Price only. The 09-14 session moves were TER -12.28%, AMAT -6.42%, ASML -6.38%, KLAC -5.34%, AMD -4.33%, TSM -3.18% and QCOM -0.84%, against SMH -4.75%. Off-cluster: LRCX -8.29% and AMKR -8.91% (live_quotes; yfinance).
- Cause: the Amodei pacing essay plus the jump in FOMC hike odds (CME 84.1%). Wave-1 catalyst verified that no hyperscaler has changed capex guidance (combined 2026 capex still ~$660-690bn).
- 247wallst (09-14) repeats AMAT's record Q3 ($9.12B, +25%), LRCX's Sept-quarter guide ($8.1B midpoint), and ASML's raised FY26 outlook plus its 2027 low-NA EUV/DUV capacity expansion.
- Correction: ASML's FY26 raise to EUR 43-45B was announced **2026-07-15** (qz.com, mlq.ai), not 09-14. The signals/thesis note that ASML "raised guidance the same session" re-uses an old datapoint, so there was no *new* positive fundamental news on 09-14. Logged in data_quality.
- China controls: nothing new found this run. Latest dated action is the April 2026 Commerce order halting some AMAT/LRCX/KLAC tool shipments to Hua Hong. China share of revenue: LRCX ~35%, AMAT ~30%, KLAC relatively insulated (electronicsforyou).
- AMKR closed at $47.12, below the prior bench entry floor of $50. That entry condition failed and has been reset.

## Prior ladder review
- 09-14 call: TSM leader, AMAT laggard. Over one session TSM -3.18% vs AMAT -6.42%, a +3.2pp spread in the direction of the call. One day is not a scorable window, so was_correct stays null.
- 09-08 ladder (TER leader) was scored incorrect. TER is now worst in the cluster on the day (-12.3%). The TER->KLAC reorder watch is acted on below, on business grounds rather than price.

## Ladder (ranked 5 of 7; QCOM and AMD unranked)
1. **TSM (leader).** Owns the CoWoS bottleneck. August revenue +53.3% YoY (6-K, 09-10). Lowest in-cluster move on a -4.75% SMH day, consistent with contract-priced wafers. Case against: Taiwan tail, AI-wafer price-hike pushback, September seasonality.
2. **KLAC (up from 3).** Process control scales with GAA layer count, HBM and packaging inspection across *all* leading-edge customers. Relatively insulated on China vs AMAT/LRCX. Q4 FY26 beat and $7B buyback. PT $233.77 (+36.7%). Case against: two beat-and-fall reactions in a row, and no dated datapoint newer than July.
3. **TER (down from 2).** Test share 7->8% (Q2 call, 07-28, not re-verified) and Q2 revenue >100% YoY. Its differentiator is AI-accelerator test volume, which is concentrated in a few compute/ASIC customers. A pacing risk, even a rhetorical one, lands on that driver first, whereas KLAC is diversified across wafer starts. Test lags a WFE turn (playbook read-through). Case for it: Q3 guide well above consensus, PT +34%, and no name-specific negative.
4. **ASML (unchanged at 5 -> 4 after QCOM unranked).** EUV monopoly and FY26 EUR 43-45B guide, with 2027 capacity being added. Case against: ~20% China DUV exposure, and 10-14 bookings are the binary where pacing would show up first. Case for it: lowest beta among the toolmakers (0.99) and the day's move was only -1.92x ATR.
5. **AMAT (laggard).** Only member with a quantified China hit: FY26 revenue -$600-710M (08-14 call coverage), ~30% China mix, broad dep/etch into mature nodes. Case for it: record Q3 and above-consensus Q4 guide, PT $640.89 (+50%), RSI 34.7. It is the likeliest name to leave the slot if 11-13 narrows the China hit.
- **Unranked QCOM** (method change vs 09-14): a fabless handset/AI-DC designer, so every WFE axis is N/A. Its rel_intra of +18.7pp is a low-beta rotation (beta 0.73) plus an AWS announcement, not booked revenue. Ranking it would be price-only, the same logic that already leaves AMD unranked.
- **Unranked AMD:** compute designer; axes N/A; thesis is watch.

## Disagreement with price
The rel_intra order is QCOM, AMD, TSM, ASML, KLAC, TER, AMAT. The ladder differs in three places:
- QCOM and AMD are removed, because they sit off the cluster's axes.
- KLAC ranks above ASML and TER, because of China insulation and diversified process-control intensity.
- TER ranks above ASML despite the worse month, on growth rate.
Only TSM at the top and AMAT at the bottom match price. TSM's position rests on the August revenue print; AMAT's rests on the quantified China loss.

## Margin pool
- Toward: foundry/advanced packaging capacity (TSM/CoWoS) and leading-edge process control.
- Away from: China-exposed broad dep/etch and DUV.
- New hypothesis, not yet evidenced: if pacing ever turns real, accelerator-volume-linked steps (test, OSAT) would feel it before litho, where 2027 capacity is already being built.

## Redundancy
- KLAC/AMAT is **distinct**. Both face the same China controls and customers, but at different process steps and with different China intensity. If the book ever consolidates, keep KLAC.

## FOMC 09-16 rate/duration sensitivity (beta from compute_risk, day_atr_mult from signals)
- **Hit hardest on a hawkish surprise** (50bp, or hawkish dots): TER (beta 1.51, ATR 6.63%, -12.3% on the odds jump), AMD 1.37, KLAC 1.31, AMAT 1.29.
- **Most insulated:** QCOM 0.73, TSM 0.85, ASML 0.99.
- **Snap-back on a hold** (the surprise, about 16% implied): TER and AMAT carry the largest odds-driven drawdown to recover. ASML is the lower-risk rebound, because its -6.4% was 1.92x its own ATR on no new negative.
- A 25bp hike is ~84% priced, so the base case is roughly neutral and the tail sits in the dots.
- None of this changes the ladder, which is ranked on axes, not beta.

## Bench (non-held)
- **AMKR $47.12:** OSAT/advanced-packaging exposure, and beats TER on margin-pool direction without single-step test concentration. Entry: reclaim $50 after the FOMC and keep the CoWoS path on 10-15.
- **LRCX $273.49:** DRAM/HBM/GAA etch tilt vs AMAT. Its China mix (~35%) is *higher* than AMAT's, so this is a partial substitute, not an escape. Entry: ASML 10-14 bookings above Q2 and no new controls.

## Sources
- https://247wallst.com/investing/2026/09/14/chip-equipment-stocks-slide-as-ai-pacing-call-reaches-fab-spending-applied-materials-and-lam-research-fall-6-asml-sinks-5/
- https://qz.com/asml-2026-guidance-raised-ai-chip-demand-q2-earnings-071526
- https://mlq.ai/news/asml-raises-2026-revenue-forecast-to-43-45-billion-on-surging-ai-chip-demand/
- https://www.electronicsforyou.biz/industry-buzz/china-exposure-hits-lam-research-applied-materials-kla-stocks/
- https://investinglive.com/stocks/us-orders-chip-equipment-companies-to-stop-shipments-to-chinas-second-largest-chipmaker-20260428/
