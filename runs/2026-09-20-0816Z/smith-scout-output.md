# Smith Scout — Market/Macro Desk — 2026-09-20-0816Z (DEEP, full mode)

**Read status:** US market is CLOSED (weekend). Every number below is Friday 2026-09-19's cash-session close plus Friday's after-hours futures print (bar_dates all 2026-09-18/19), carried flat over the weekend — none of this is a live Monday pre-market read. Options OI/PCR/max-pain reflect Friday's real end-of-day open interest (fetched Saturday, so it is NOT the zeroed pre-market snapshot Yahoo serves before Monday's open — but it is still Friday's tape, not current).

## 1. Session read (Friday close, not live)
- ES +0.95%, NQ +1.60% (Friday's futures close, not a fresh Monday gap indication — will likely stale-reset at Sunday-evening futures open).
- Asia >1% movers (Friday session): Nikkei +1.38%, KOSPI +2.66% (memory-tape relevant — MU/HBM-adjacent names), TAIEX +0.40% (not >1%, skip). STOXX50 -1.37% (Europe soft into the weekend).
- SMH +2.21% Friday cash / smh_live shows a further post-market print (+2.09%, session "post", as_of 2026-09-18T23:59Z) — same Friday session, not new information.
- Gap risk into Monday: the book's AI-Semis/Fabs and memory names (MU etc.) carry the most weekend gap risk given Friday's SMH +2.21% and KOSPI +2.66% — a continuation of Friday's momentum rally (per prior orchestrator finding, no fresh company catalyst behind it). Headline-level scan only (per-holding depth owned by signals/catalyst): no new macro headline found since Friday's close that would gap the book Monday.

## 2. Sentiment narrative
Composite sentiment sits at 75.1, "extreme_greed" (unchanged band vs prior run — reaffirmed). Components: VIX sub-score 92.4 (very complacent — VIX 14.81, near the bottom of its 52-week range), 125dma 68.5, RSI14 55.8 (neutral, not overbought), % off 52-week high 91.5 (SPX is close to its highs), yield trend 67.2. `action_hint` = "propose profit-booking on overweight/breach names" — this run's strategist should size any new deployment with that lean: extreme greed + a market sitting within ~2% of its 52-week high is not the setup to go max-size into diversifiers or capex adds; it argues for measured, split deployment rather than a single lump-sum committal of the full $6,684 relaxed-band cash.

## 3. Fed funds & stance — CACHED, no new meeting since last check
Today (2026-09-20) is before `fomc_cache.next_check_date` (2026-10-30) — reusing cache verbatim.
- Fed funds: 3.75–4.00% (midpoint quoted 3.875%). Stance: **hawkish**.
- Hiked +25bp on 2026-09-16, 12-0, first hike since 2023. Dot plot: 12/18 see one more 25bp hike to 4.125% by year-end; 4 see two more (4.375%). Warsh: economy "strengthening," flagged oil-driven price shocks as an inflation risk to guard against broadening. CME FedWatch: 63.7% probability of a second hike at the December meeting; futures price ~4.1% by December (~2.2 hikes/~56bp across the next 3 meetings).
- No fomc_cache_update this run (nothing changed).

## 4. Options positioning — Friday close (SPY/QQQ), not live
- **SPY**: spot $761.69. Sep-25 expiry: max_pain $763 (spot -0.17% below, essentially pinned), pcr_oi 2.26 (heavy standing put OI — defensive positioning), pcr_vol 1.13 (today's flow much closer to balanced). Sep-30 expiry: max_pain $761 (spot +0.09%, dead-on), pcr_oi 3.01 (very put-heavy OI), pcr_vol 0.98 (balanced flow). **Positioning (pcr_oi) reads meaningfully more bearish/hedged than flow (pcr_vol) at both expiries** — consistent with investors carrying protective puts into a market near highs (matches the extreme-greed complacency read) rather than an active bearish flow.
- **QQQ**: spot $721.45, trading ABOVE max-pain at both expiries (Sep-25: max_pain $717, spot +0.62%; Sep-30: max_pain $710, spot +1.61%) — tape has run ahead of the options-implied gravity point, a mild pull-lower bias if it holds. Near-dated pcr_oi 3.39 vs pcr_vol 2.75 — both elevated (put-heavy on both OI and flow, unlike SPY where flow was balanced); QQQ hedging/put demand is broader-based, not just standing OI.
- No boundary_artifact flags, no data_quality notes on either file — figures are clean, just dated to Friday's close.

## 5. Calendar + regime read
Reaffirming cached calendar (`macro:calendar`, not expired until 2026-09-23): next FOMC 2026-10-28, next CPI 2026-10-14, next NFP 2026-10-02. None inside 5 trading days of today (next trading session Monday 2026-09-22; NFP is ~7 trading days out). `earnings_season_window`: false — no mega-cap print imminent.

**Regime read:**
- US10y sits at 4.998%, +5.1bp on Friday and +34.5bp over the trailing month — still grinding toward the cycle high (5.006% seen 09-16) even as equities rally and VIX fell -4.1% to 14.81. That combination (yields up, vol down, stocks up) is a "priced for a soft landing, hawkish-hike-already-absorbed" tape, not risk-off — but it is fragile: the Fed's own dots point to a second hike (~64% odds by Dec per FedWatch), and the book's AI-capex/duration chain has already shown it moves 1.7-2.5x SMH on rate scares (09-14 episode).
- **AI-capex chain**: near-term tailwind (Friday's SMH +2.21%, KOSPI +2.66% memory strength carries into Monday), but this is the highest-beta cluster to the next yield print/FOMC dot revision — the rally is unconfirmed by any new capex-guide catalyst (per prior orchestrator finding), so it reads as momentum, not fundamentals, and is the first place a renewed yield leg higher would hit.
- **Rate-sensitive / long-duration growth**: 10-yr still near cycle highs with a hawkish Fed; no relief yet on the discount-rate side despite Friday's rally. Options positioning (SPY pcr_oi much more defensive than flow) is consistent with the market hedging this exact risk rather than believing the rally.
- **Defensives/diversifiers**: extreme-greed sentiment + SPX near its 52-week high argues for using calm to add ballast rather than chase the AI-capex momentum leg — this is exactly the setup the diversifier bench below is for.

## 6. Diversifier bench — refreshed this run (was 14 days stale)
Prices refreshed for all 9 names (yfinance, single batched call, Friday 2026-09-18 close). Target/thesis refreshed for the 7 names >7 days old (VST target NOT refreshed this run — budget; flagged below). XOM was already fresh (3 days old) — price only refreshed.

Ranked by upside × cleanliness:
1. **VST** $140.67 → $223.17 target, +58.7% upside — **NOT clean** (AI-load-adjacent merchant power, beta 1.41). Target/thesis stale (2026-09-06, not refreshed this run — flagged).
2. **UNH** $376.90 → $475.23 (updated from $471.65), +26.1% upside — clean. Consensus from 27 analysts, Buy rating.
3. **SO** $85.52 → $100.29 (updated from $101.45), +17.3% upside — clean, regulated utility, beta 0.32.
4. **DUK** $117.53 → $137.28 (updated from $138.61), +16.8% upside — clean, regulated utility, beta 0.36.
5. **LLY** $1152.93 → $1300 (updated from $1270.37, analyst raised target post-beat-and-raise), +12.75% upside — clean, GLP-1/pharma, beta 0.50.
6. **NEM** $123.41 → $139.04 (updated from $133.00), +12.7% upside — clean, gold miner, beta 0.54.
7. **PG** $146.39 → $163.25 (~flat vs $163.35), +11.5% upside — clean, staples ballast, beta 0.38.
8. **XOM** $163.54 → $173.42 (unchanged, still fresh), +6.0% upside — clean, oil-major/Brent hedge, beta 0.175. Its "fell -3.5% despite oil strength, cause unconfirmed" flag from 09-17 is now stale-resolved: XOM is +0.17% Friday, in line with the tape — that anomaly did not persist.
9. **JNJ** $269.99 → $238.20 target (**down sharply from $269.95**), **upside now -11.8%** — flagging this as a material change: consensus target flipped BELOW spot. JNJ is no longer an upside diversifier candidate at current price; still "clean" on beta (0.24) but there is no upside case left. Recommend dropping to the bottom of the bench or excluding from any new-cash proposal until target/thesis is re-underwritten.

## Delta since prior_findings_since (2026-09-19T08:56:33Z)
What actually changed: (1) diversifier bench refreshed after 14 days stale — JNJ's target flipped bearish (material), NEM/UNH targets rose, SO/DUK/PG essentially flat; (2) options positioning now readable off real Friday OI (prior runs likely had pre-market-zeroed or missing options data) — SPY/QQQ both show OI more defensive than flow; (3) no FOMC/calendar change (cache still valid, calendar not expired); (4) sentiment score/band unchanged (75.1 extreme_greed, reaffirmed). Nothing else in the macro/regime read moved materially since Friday's 08:56Z snapshot — this is a weekend carry-forward, not a new session.

## Findings reaffirmed
`macro:calendar`, `macro:fomc` (fomc_cache reused verbatim, no meeting since last check).

## Comms (desk)
- `desk_inbox` was empty this run — nothing to answer.
- Tell → strategist: JNJ's analyst-consensus target flipped from $269.95 to $238.20 (now below spot $269.99) — if JNJ was under consideration as a diversifier buy for the $2,430–$6,684 deployable cash, that case no longer holds on upside; NEM's target rose 133→139.04 (a stronger case, still clean). weight: high (directly affects which diversifier the strategist would size).
- Tell → strategist: sentiment `action_hint` = profit-booking bias under extreme_greed (unchanged band) + SPX near 52-week high + QQQ trading above both max-pain levels — argues for split/staged rather than lump-sum deployment of the relaxed-band cash. weight: normal.
