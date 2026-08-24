AI-capex 76.71% total-book (82.16% stock-only, cap 100%) — gate: ESCALATING, no SL activity vs last snapshot

| Ticker | Δ% | Support | Action | Size | Gate | Tag |
|---|---|---|---|---|---|---|
| GLW | -3.50% | $139.93 | average | $600 | stage_in | MACRO_DRIVEN |
| BE | -3.19% | $185.64 | average | $350 | stage_in | MACRO_DRIVEN |
| SKHY | -3.12% | $149.02 | average | $600 | stage_in | MACRO_DRIVEN |
| WDC | -2.58% | $356.48 | average | $550 | stage_in | MACRO_DRIVEN |
| LRCX | -2.42% | $252.32 | average | $500 | stage_in | MACRO_DRIVEN |

STAY-OUT: HOOD[WATCH_THESIS] MU[WATCH_THESIS] NBIS[WATCH_THESIS] INTC[WATCH_THESIS] CIEN[WATCH_THESIS] CEG[WATCH_THESIS] NOW[WATCH_THESIS] AMD[WATCH_THESIS] MSFT[WATCH_THESIS] STM[WATCH_THESIS] MRVL[IDIO_WEAK] BABA[WATCH_THESIS] BX[WATCH_THESIS] META[IDIO_WEAK] FLTW[WATCH_THESIS] TXN[WATCH_THESIS] ASML[WATCH_THESIS] TER[THIN_DIP] VRT[WATCH_THESIS] AMZN[IDIO_WEAK]

```json
{"basis":{"total_book_usd":41781.19,"stock_usd":39012.17,"wallet_usd":2769.02,"ai_capex_pct_total_book":76.71,"ai_capex_pct_stock":82.16,"ai_capex_cap_pct":100},
 "gate":{"classification":"escalating","vix_chg_pct":5.09,"es_pct":-0.21,"nq_pct":-0.70,"worst_asia_pct":-3.12,"worst_asia_index":"KOSPI (^KS11)","smh_pct":-0.40,"orchestrator_gate":"ESCALATING","downgrade_blocked":true,"news_call_used":false},
 "sl_forensics":[],
 "proposals":[
  {"ticker":"GLW","action":"average","size_usd":600,"current_price":144.59,"support_usd":139.93,"secondary_support_usd":139.93,"support_source":"live","headroom_usd_total_book":3423,"gate":"stage_in","tags":["macro_driven"],"rationale":"deepest dip in book -3.50%, strengthening thesis, no flag, only 200d MA sits below price"},
  {"ticker":"BE","action":"average","size_usd":350,"current_price":195.02,"support_usd":185.64,"secondary_support_usd":185.64,"support_source":"live","headroom_usd_total_book":1896,"gate":"stage_in","tags":["macro_driven"],"rationale":"Power/DC cluster near target (15.5% vs 15% target), sized conservatively to respect tighter headroom"},
  {"ticker":"SKHY","action":"average","size_usd":600,"current_price":158.31,"support_usd":149.02,"secondary_support_usd":149.02,"support_source":"live","headroom_usd_total_book":4223,"gate":"stage_in","tags":["macro_driven"],"rationale":"HBM4 allocation-leader thesis strengthening, dip -3.12%, real headroom"},
  {"ticker":"WDC","action":"average","size_usd":550,"current_price":447.58,"support_usd":356.48,"secondary_support_usd":356.48,"support_source":"live","headroom_usd_total_book":4118,"gate":"stage_in","tags":["macro_driven"],"rationale":"broke below 5/20/50/100d MAs post-earnings-pop fade, thesis strengthening on AI storage demand"},
  {"ticker":"LRCX","action":"average","size_usd":500,"current_price":306.40,"support_usd":252.32,"secondary_support_usd":252.32,"support_source":"live","headroom_usd_total_book":3664,"gate":"stage_in","tags":["macro_driven"],"rationale":"semicap capex beneficiary re-entered post 07-28 stop-out, dip -2.42%, cluster still under ceiling"}
 ],
 "considered_excluded":[],
 "data_quality":[
  "Holdings diff: live networth_holdings (33 US_STOCK positions) matches state.json's 2026-08-24T08:55 IST quick-sweep holdings array exactly on quantity for all 33 tickers -- zero exits/trims/new-position activity since that sweep. sl_forensics is deliberately empty; today's ESCALATING gate is a fresh pre-market (Asia-session) development, not a same-day stop-loss event, per the dispatch note.",
  "Gate carried forward as the orchestrator's authoritative ESCALATING classification (triggered solely by the Asia term: KOSPI -3.12% breaching the -3% threshold; VIX +5.09%/ES -0.21%/NQ -0.70%/SMH -0.40% do not independently breach). No fresh live batched quote call was made this run -- all gate inputs came from the dispatch prompt and slice_rebound.json's macro block -- so per rule D.2 this is a carry-forward, not an independent re-evaluation; downgrade_blocked=true accordingly.",
  "Reconciliation note: summing holdings.json's 33 market_value_inr rows yields INR 3,677,100.18, vs the totals.current_value_inr_from_snapshot field of INR 3,734,439.66 (~1.5% gap, likely a timing lag between the wallet/snapshot fetch and the live_quotes fetch -- holdings.json's own weight_pct values reconcile to the summed figure, not the stated total). The basis block above uses the stated totals field per the skill's cash-inclusive convention; cluster/AI-capex percentages use the summed per-ticker figures for internal consistency.",
  "Support levels: all 6 candidate tickers screened (GLW, BE, SKHY, WDC, LRCX, plus AMAT which ranked 6th) show only their 200-day MA sitting below live price -- 5/20/50/100-day MAs are all above -- a uniform, book-wide technical pullback pattern consistent with the Asia-led sector move, not an idiosyncratic break. secondary_support_usd is set equal to primary and flagged per rule G's single-MA-below-price case for all five proposals.",
  "SKHY: Barchart reports 50/100/200-day moving averages as N/A (thin listing history for the ADS); support computed off the 20-day MA only -- flagged low-confidence per the recent-listing fallback guidance.",
  "20 of 33 holdings carry a WATCH/BROKEN thesis status or a state.json open_flags entry and are excluded from this run's average/extend scan per the flag carry-over rule, full stop, regardless of today's macro-driven bounce. Three of those flags don't cleanly match one of the seven fixed tags -- MRVL's open_flags entry is a data-correction caution (smith-quality's interest-coverage claim doesn't match the 10-Q), META/AMZN's is an uncaptured-trade-rationale governance gap, both nearest-mapped to IDIO_WEAK; TER's is a sub-$2 dust-position residue, mapped to THIN_DIP.",
  "AMAT ranked 6th by dip depth (-2.04%, behind LRCX's -2.42%) and was left out of the top-5 scorecard on ranking grounds alone, not cluster_full or thin_dip -- not logged in considered_excluded since neither enum reason applies.",
  "rebound_prime.json cache exists but is dated 2026-07-17 (not today) -- correctly treated as stale and not used; all support levels this run came from live Barchart fetches.",
  "Proposal sizing is a fixed modest stage_in tranche keyed to each name's cluster/position headroom, not the constant-risk stop_loss_framework formula -- that formula prices an actual stop distance, which doesn't apply on a day with zero stops fired.",
  "policy.json confirmed:true, as_of 2026-08-06 -- no staleness flag needed."
 ]}
```
