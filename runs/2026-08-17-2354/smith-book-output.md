SMITH-BOOK — quick mode — run 2026-08-17-2354

## 1. INCOME (dividends / ex-dividend dates)
No yfinance tool in this session's toolset exposes dividend yield or ex-dividend dates
(available tools: get_stock_history, get_stock_price, search_stocks — get_stock_price
returns price/change/marketCap/volume only, no dividend fields). Cannot compute trailing
portfolio yield or scan ex-dates within 30 days without inventing numbers.
div_yield_pct = null, ex_dates = [] (see data_quality).

## 2. LTCG NARRATIVE
lots.json is populated and reconciled (not empty — smith-tax unblocked it 2026-08-15).
Earliest open lot across the entire book is CLS, 2026-07-15. The 24-month Indian LTCG
boundary for that lot falls ~2028-07-15. compute_book.json's own ltcg_flags array is
empty, confirming this independently. There are currently NO live LTCG-deferral
decisions anywhere in the book — every lot is well inside the short-term window, so
none is within 6 months of the 24-month boundary. Stating this plainly rather than
manufacturing urgency, per instruction.

## 3. IONQ — ATR20 / beta (the one uncapped name)
IONQ carried no ATR20 and no beta (defaulted to 1.0, open risk null) per
compute_book.json's data_quality flag. Fetched IONQ + SMH true daily bars,
period=1mo, interval=1d (22 rows each, 2026-07-17..2026-08-17) in one batched call.
- ATR20 (simple avg of 20 true-range values, most recent 20 of 21 available) = $2.8126
- ATR20 as % of last close ($46.55) = 6.04%
- Beta vs SMH (21 daily-return pairs, covariance/variance) = 1.311
Caveat: 21 observations is a thin sample spanning the same violent late-July/early-Aug
semis selloff-and-recovery window flagged elsewhere in the cache (SKHY, NOW, META-class
caveat) — directionally useful to lift IONQ off the 1.0 default and open-risk null, but
not a stable multi-quarter structural loading. Beta 1.311 and ATR% 6.04% are both within
plausibility bands (beta 0-3.5; ATR% sane for a small-cap high-beta name).

## 4. BETA CACHE TTL CHECK
Checked every held ticker's data_cache_betas.84ede988.json entry against a 30-day TTL
from today (2026-08-17). Oldest entries in the cache are dated 2026-07-31 (17 days
old) — all held names with an existing cache entry (34 of 35) are inside the 30-day
window. No refreshes triggered by TTL expiry this run. Only IONQ needed a fresh fetch
(no entry at all, item 3 above).

## 5. RISK NARRATIVE
Portfolio beta 1.287 (primary SOX/SMH benchmark beta 1.19; secondary SPX beta 1.491 is
flagged by the script as the misleading one — SOX/SMH is the true factor for this book).
Risk-weighted concentration is dominated by the memory/HBM cluster despite moderate
headline weights: MU is 5.79% of the book by weight but 8.79% of risk (beta 1.954),
SKHY is 4.33% weight / 8.21% risk (beta 2.442, thin-sample ADR — highest realized vol
in the book), DRAM is 4.14% weight / 6.66% risk (beta 2.073), MRVL 3.75%/4.88% (beta
1.676), SNDK 2.07%/4.69% (beta 2.924, the highest single beta held). Together these
five names are ~20% of book value but ~33% of risk contribution — the book's factor
risk is more concentrated than its dollar concentration alone suggests. Drawdown is
shallow: -0.865% off the total-book peak of $44,873.02 (current $44,485.08), nowhere
near a stress level on its own. The two live policy breaches this run are the cash
floor (1.122% wallet vs the [5,15]% band — under-band) and aggregate open risk (14.19%
vs the 10% cap) — both already computed by the orchestrator and simply narrated here:
the book is simultaneously too fully invested (cash) and running hotter open risk than
the cap allows, with the memory/HBM names disproportionately responsible for that open
risk given their betas above.

## DATA QUALITY
- Dividend yield and ex-dividend dates unavailable: no yfinance MCP tool in this
  session exposes dividend fields (get_stock_price returns price/change/marketCap/
  volume only). div_yield_pct and ex_dates returned null/empty rather than invented.
- IONQ beta (1.311) and ATR20 (6.04% of price) computed from only 21 daily
  observations spanning one violent sector event — directional, not a stable
  structural estimate; re-measure with a longer window on a future deep run.
- No beta cache entries were past the 30-day TTL this run; nothing else refreshed.
- Per standing gaps G69 (116 historical confirmations lost to a pointer-only
  quarantine schema) and G78 (32 uncaptured trade rationales, 2026-08-01 onward):
  neither affects lots.json's LTCG math (that data is intact/reconciled), only
  narrative rationale for recent qty changes, which is out of this agent's scope.

```json
{"div_yield_pct":null,"ex_dates":[],
 "ltcg_narrative":[{"ticker":"ALL","months_to_ltcg":null,"note":"Earliest open lot (CLS, 2026-07-15) is ~24 months from its LTCG boundary (~2028-07-15); compute_book.json ltcg_flags is empty; no live LTCG-deferral decisions exist in the book right now."}],
 "refreshed_betas":{"IONQ":1.311},
 "ionq_atr20_usd":2.8126,"ionq_atr20_pct":6.04,
 "risk_narrative":"Portfolio beta 1.287 (SOX/SMH primary 1.19; SPX secondary 1.491 flagged misleading). Memory/HBM cluster MU/SKHY/DRAM/MRVL/SNDK is ~20% of book value but ~33% of risk contribution (risk_pct 8.79/8.21/6.66/4.88/4.69 vs weights 5.79/4.33/4.14/3.75/2.07). Drawdown -0.865% off total-book peak $44,873.02 is shallow, not stress-level. Two live policy breaches narrated from orchestrator figures: cash 1.122% under the [5,15]% band, aggregate open risk 14.19% over the 10% cap -- memory/HBM betas are the main driver of the open-risk overage.",
 "data_quality":["div_yield_pct and ex_dates null -- no yfinance tool in this session exposes dividend/ex-dividend fields","IONQ beta 1.311 and ATR20 6.04% from only 21 daily obs spanning one violent sector event -- directional only, re-measure later with longer history","no held-name beta cache entry was past the 30-day TTL this run (oldest is 17 days)","G69/G78 do not affect LTCG math in lots.json, only qty-change trade-rationale narrative which is out of scope here"]}
```
