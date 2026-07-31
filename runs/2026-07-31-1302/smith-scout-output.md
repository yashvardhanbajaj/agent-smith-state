# Market Scout — Deep Review, 2026-07-31

## 1. Session Read

**US futures (pre-open):** ES +0.40%, NQ +1.03% — mild, constructive continuation. Note these are modest relative to the overnight Asia move; futures are NOT pricing a full pass-through of the KOSPI/TAIEX explosion, they're pricing yesterday's SMH +6.91% US relief rally continuing into today.

**Asia — the KOSPI story (needs real explanation, not "mean reversion"):**
This is a 3-day sequence, not a single clean bounce:
- Jul 28: KOSPI -10.84% (4th-largest single-day decline in index history) — market-wide circuit breaker (8th of 2026).
- Jul 29: KOSPI -5.98%, second consecutive-session circuit breaker — unprecedented back-to-back trigger. Driver cited: AI capex/leverage-liquidation concerns hitting Samsung/SK Hynix specifically.
- Jul 31 (today): KOSPI +17.91% to 6,595.45 — largest single-day gain in index history. Samsung Electronics +22.5%, SK Hynix +27.7%. Catalyst: strong overnight US semiconductor performance (yesterday's SMH +6.91%) triggering a relief/short-covering rally in the same names that were liquidated two sessions prior.

**Read: this is a violent snapback from an oversold, forced-liquidation low — not new positive fundamental news on Samsung/SK Hynix.** No company-specific catalyst (no earnings surprise, no policy action) turned up in the scan; the move is US-semis-sentiment-led short covering after a historic 2-day circuit-breaker crash. Flagging as an open question: whether the leverage/liquidation unwind that caused the Jul 28-29 crash is actually resolved, or whether today's snap is itself a squeeze that could reverse again. Treat KOSPI/EWY as still in a high-vol regime, not newly stable.

TAIEX +7.98% (2330.TW/TSM home listing) — same read, chip-sector relief bounce tracking the SMH move, no independent Taiwan-specific catalyst found.
Nikkei +4.03% — broad regional risk-on carried by the same chip rally, smaller magnitude (less memory-chip weight than KOSPI/TAIEX).
Europe: STOXX50E +0.90%, unremarkable, no ADR gap flags from European home listings this session.

**Gap risk / opportunity for the book:**
- **EWY (3.35% weight) — highest gap-risk name today, by far.** Direct KOSPI proxy; index up 17.9% overnight after a -16% two-day crash. yfinance already shows EWY +11.8% intraday (144.21→161.21) with 50M volume — the ETF is already catching up to NAV in real time, meaning some of the gap has already been captured ahead of the formal US cash open. Do not assume the full 17.9% flows through 1:1 — Depositary Receipt/ETF premium-discount mechanics plus the fact this follows a two-session crash argue for treating the print as still volatile, not a clean re-rate. Whipsaw risk both ways today.
- TSM: home listing (2330.TW) implied +7.98% overnight tailwind; US futures (NQ +1.03%) suggest only partial pass-through priced in — TSM likely gaps up but probably not the full Taiwan-session magnitude.
- No overnight/weekend US-specific headline found for other book holdings beyond the general chip-sector rally read.

## 2. Sentiment Narrative

Score 65.9 ("greed," unchanged band from prior). The composite is being driven almost entirely by low realized volatility (VIX sub-score 81.3, VIX itself 16.86 and falling) and proximity to 52-week highs (92.5), not by momentum excess — RSI14 sub-score is only 35.4, meaning price momentum is actually soft/neutral, not stretched. This is a "calm and near-highs" greed reading, not a "melt-up euphoria" greed reading — the kind of tension worth sitting with given last night's violent Asia whipsaw sits directly upstream of two of the book's holdings (EWY, TSM exposure). action_hint is null, so no extreme-greed/extreme-fear override applies this run; the strategist should size normally but weight the EWY/TSM gap-risk read above when considering fresh entries today specifically.

## 3. Diversifier Bench (ranked, upside% × cleanliness)

| Ticker | Price | Target | Upside% | Thesis | Status | Diversifier |
|---|---|---|---|---|---|---|
| NEM | $95.76 | $133.00 | +38.9% | Gold miner, zero AI-capex overlap, beta 0.48 | active | clean |
| VST | $148.62 | $223.17 | +50.2% | Merchant power gen, AI-load-adjacent | active | **partial** (datacenter-power correlated to book's AI-capex bet) |
| PG | $143.96 | $163.35 | +13.5% | Staples ballast, yield | active | clean |
| UNH | $421.47 | $471.65 | +11.9% | Managed care rebound, no capex correlation | active | clean |
| LLY | $1154.97 | $1270.37 | +10.0% | Pharma/GLP-1, decoupled from semis | active | clean |
| DUK | $126.27 | $138.61 | +9.8% | Regulated utility, rate-base growth, beta 0.37 | active | clean |
| SO | $94.34 | $101.45 | +7.5% | Regulated SE utility, defensive, beta 0.33 | active | clean |
| JNJ | $255.82 | $269.95 | +5.5% | Diversified pharma/medtech | active | clean |
| KO | $88.49 | $87.35 | -1.3% | Staples, now trading above prior target | stale | clean |

GOLD ticker mismatch note still applies (resolves to Gold.com fintech, not Barrick — excluded).
Analyst targets not refetched this run (budget) — carried forward from prior bench; only live prices refreshed. Flag for next run to refresh targets, especially KO (price now exceeds prior target).

## Data Quality
- Analyst mean targets not refetched this run — carried from prior diversifier_candidates map; prices refreshed live via yfinance.
- No company-specific (non-macro) news catalyst found for Samsung/SK Hynix beyond the US-semis-sentiment-led short-covering read — flagged as open question, not asserted as resolved.
- EWY intraday print (+11.8%) may not fully reflect final cash-open gap; treat as directional, not final.
