# Signal Scan — 2026-08-29 (deep, weekend review, prices = Fri 08-28 close)

Book context: SMH -3.47% Friday, gate=ESCALATING. Most of the semis/AI-capex book sold off together — expect a wide TARGET GAP list below driven by price, not by target cuts. FMP insiderTrades/form13F are plan-gated (ACCESS DENIED, Starter+ required) — INSIDER ACTIVITY section is news-derived only this run, not Form-4 sourced as the deep-mode spec calls for.

## STRONG DOWNTREND
- IREN — day -12.53%, 1.13x its 11.1% ATR20 (normalized) — pos 0.24. Earnings miss: revenue drop + adjusted loss reported 28 Aug 2026 — outlets, sentiment negative; stock still -12.5% despite $4B AI-cloud contracted revenue disclosed same release. 2.03% weight. Grade context: n/a (no prior IREN bucket in journal).
- AMKR — day -7.46% [unnormalized, no ATR20 cached] — pos 0.33. "Amkor Faces Pressure Amid Cautious Outlook" — 19 Aug 2026 — cited outlet via INDmoney feed; Treasury-yield pressure + cautious guidance despite strong Q2. 1.29% weight, small position.
- KLAC — day -4.48% [unnormalized, no ATR20 cached] — pos 0.41. No fresh negative news found beyond broad semicap selloff; sector-beta move, not idiosyncratic. Already PEER LAGGARD / TARGET GAP in signal_history — unchanged repeat on those.
- LITE — day -6.39% [unnormalized, no ATR20 cached] — but pos 0.80 (still upper half of 52wk range) — this reads as a pullback off a run, not a breakdown. Flagging here per the day-move rule but treat as lower-conviction than IREN/AMKR; no ATR to scale confidence.

## STRONG UPTREND
- FLTW — pos 0.88 (unchanged repeat, ATR20 only 1.89% — quiet name, day -0.61% is unremarkable on its own scale).
- MSFT — pos 0.80, day +1.68%. Unchanged repeat (also PEER LEADER, signal_history). News still positive: $678B AI backlog disclosed 27 Aug.
- LITE — pos 0.80 (NEW addition to signal_history) despite today's sharp down day — see STRONG DOWNTREND note above; the two buckets are in tension because the day-move fired the legacy absolute threshold with no ATR to arbitrate. Flagging both, not resolving.

## NEW TAILWINDS
- BABA — 2 distinct events, positive>negative on net toward month-end: (1) HK$80B share placement closed with Jack Ma buying alongside — 25 Aug 2026 — INDmoney feed; (2) Qwen3.8-Max AI model launch — 03 Aug 2026. Still pending: dilution/lawsuit overhang from 23/17/14 Aug items, unresolved.
- TSM — insider purchase signal + strong Q2 print, 2 distinct events: insider buy — 22 Aug 2026; Q2 beat/AI-demand commentary — 25-26 Aug 2026.

## NEW HEADWINDS
- MRVL — 1 distinct event but weight matters: Q2 beat yet "investor disappointment" sell-off — 28 Aug 2026 — day -10.28% (1.04x its 9.88% ATR20, just under the 12%-capped threshold so not STRONG DOWNTREND by the scaled rule, but the largest single-day move in the book this run). Read this as a guidance/reaction story, not a results miss — the release itself beat. 4.87% weight, book's largest holding by weight after GEV. Grade: TARGET GAP prior entry graded A (100%, n=1, low-confidence).
- QCOM — 2 distinct negative events: handset weakness — 20 Aug 2026; margin pressure tied to BMW deal — 06 Aug 2026 (stale, still pending). Net skew negative but under the 2-item net rule (2 neg vs positives on AI PC/automotive) — borderline, noting rather than fully flagging.

## TARGET GAP (book-wide — driven by Friday's selloff, not target cuts)
Unchanged repeats (already in signal_history, upside widened mechanically as prices fell): GEV (+26.2%), AMZN (+18.5%), TER (+20.5%), NVDA (+28.9%), ASML (+21.3%), AMD (+24.1%), TSM (+24.7%), WDC (+30.9%), COHR (+32.9%), LITE (+22.1%), MRVL (+19.6%), IREN (+55.8%), MU (+38.4%), GLW (+22.2%), STM (+34.1%), CIEN (+32.1%), KLAC (+25.1%), INTC (+22.1%).
New this run (crossed 15% or newly assessed): BE (+23.4%, 4.21% weight), AMKR (+37.9%), AVGO (+29.9%), CLS (+37.4%), LRCX (+18.7%), VRT (+24.0%), GOOG (+18.8%), AMAT (+27.9%), CEG (+20.5%, previously absent from signal_history entirely — first-time classification), BABA (+36.4%).
Below threshold, no flag: QCOM (+15.0%, borderline), SMCI (+12.5%), MSFT (+9.8%), BX (+0.1%).
No target/ETF: FLTW, NBIS, SKHY (see data_quality — SKHY 52wk_low returned as 0, pos calc unreliable, guardrail applied).

## OVERSOLD BOUNCE
- BABA — pos 0.267, day +2.23% against a red tape, positive AI-model/placement news outweighing the dilution overhang for now. 0.58% weight (small).

## EARNINGS PROXIMITY / POST-EARNINGS
- NVDA — signal_history still carries EARNINGS PROXIMITY but the news flow (22-24 Aug, "ahead of earnings") suggests the print has already passed; unconfirmed exact date from this run's data — flagging as data_quality rather than re-asserting proximity.
- IREN and MRVL both just reported (28 Aug) with negative price reactions on ostensibly mixed-to-strong underlying numbers — see STRONG DOWNTREND / NEW HEADWINDS above; treat as post-earnings drift candidates for the journal, not proximity.

## PEER-RELATIVE (data quality caveat)
Tool budget did not allow fresh 1-month peer-ETF pulls this run (FMP insider tools ate 3 calls before failing plan-gate). Carrying forward unchanged: MRVL, CEG, VRT, BE, HOOD, BX, NBIS = PEER LEADER; AVGO, CLS, BABA, TXN, META, GOOG, KLAC = PEER LAGGARD (all unchanged repeats, no new rel_sigma computed — see data_quality). SNDK blind-spot line from prior runs not re-verified this run (SNDK not currently held per this holdings slice).

## Unchanged repeats (bucket unchanged, suppressed to this line)
ASML/TSM/MU/CIEN/STM (TARGET GAP), AVGO/CLS/BABA/GOOG/KLAC/TXN/META (PEER LAGGARD), MRVL/CEG/VRT/BE/BX/NBIS/HOOD (PEER LEADER), TSM/AMD (INSIDER ACTIVITY, unverified this run — FMP gated), SMCI (MOMENTUM+VOLUME — day flipped to -3.59% today, cooling not confirming; not re-flagged).

## Still pending (pre-watermark, unresolved)
- BX Project Eclipse ($3B) scrap review — 12 Aug — status unknown.
- Intel dilution overhang from the $20-23B offerings (multiple Aug dates) — still weighing on sentiment despite CEO/insider buying.
- Alibaba securities-fraud class action (14/17 Aug) — unresolved.
- G81 (proximate cause of 08-18 semis rout) remains open per known_gaps — nothing this run resolves it.

```json
{"signal_history":{"changed":{"IREN":["STRONG DOWNTREND"],"AMKR":["STRONG DOWNTREND","TARGET GAP"],"KLAC":["STRONG DOWNTREND"],"LITE":["STRONG DOWNTREND","STRONG UPTREND"],"MSFT":["STRONG UPTREND","PEER LEADER"],"BABA":["OVERSOLD BOUNCE","TARGET GAP","PEER LAGGARD"],"TSM":["TARGET GAP","INSIDER ACTIVITY"],"MRVL":["NEW HEADWINDS","TARGET GAP","PEER LEADER"],"BE":["TARGET GAP","PEER LEADER"],"AVGO":["TARGET GAP","PEER LAGGARD"],"CLS":["TARGET GAP","PEER LAGGARD"],"LRCX":["TARGET GAP"],"VRT":["TARGET GAP","PEER LEADER"],"GOOG":["TARGET GAP","PEER LAGGARD"],"AMAT":["TARGET GAP"],"CEG":["TARGET GAP","PEER LEADER"],"QCOM":["NEW HEADWINDS (borderline)"]},"unchanged_count":13},
 "news_watermark":"2026-08-29","resolved_flags":[],"new_flags":[],
 "journal_new":[
   {"date":"2026-08-29","ticker":"IREN","bucket":"STRONG DOWNTREND","price_at_flag":35.45,"analyst_target":80.19,"day_atr_mult":1.13,"rel_sigma":null,"normalized":true},
   {"date":"2026-08-29","ticker":"AMKR","bucket":"STRONG DOWNTREND","price_at_flag":47.88,"analyst_target":77.11,"day_atr_mult":null,"rel_sigma":null,"normalized":false},
   {"date":"2026-08-29","ticker":"MRVL","bucket":"NEW HEADWINDS","price_at_flag":216.62,"analyst_target":269.28,"day_atr_mult":1.04,"rel_sigma":null,"normalized":true},
   {"date":"2026-08-29","ticker":"BABA","bucket":"OVERSOLD BOUNCE","price_at_flag":118.9,"analyst_target":186.99,"day_atr_mult":null,"rel_sigma":null,"normalized":false}
 ],
 "peer_map_updates":{},
 "vol_normalization":{"IREN":{"atr20_pct":11.1,"day_atr_mult":1.13,"rel_sigma":null,"threshold_pct":12.0},"MRVL":{"atr20_pct":9.88,"day_atr_mult":1.04,"rel_sigma":null,"threshold_pct":12.0}},
 "data_quality":["FMP insiderTrades/form13F both ACCESS DENIED (plan-gated) — deep-mode INSIDER ACTIVITY fell back to news-derived only, not Form-4 sourced this run.","SKHY 52wk_low returned as 0 (bad data / recent listing) — pos calc guardrail applied, breakout reading suppressed, not reported.","AMKR, SMCI, KLAC, LITE have no atr20 cache entry — all day-move triggers for these 4 used the legacy ±4%/±8pp absolute threshold, tagged [unnormalized] in journal_new.","PEER-RELATIVE section carried forward unchanged from last run's signal_history — no fresh 1-month ETF pull this run due to tool-call budget (3 calls burned on plan-gated FMP insider tools before discovering the gate).","NVDA EARNINGS PROXIMITY carried from signal_history could not be confirmed or dated this run — news suggests the print may have already occurred; treat the persisted bucket as stale pending confirmation.","CEG had no prior signal_history entry at all despite being a live holding — gap in prior run's coverage, now populated."]}
```
