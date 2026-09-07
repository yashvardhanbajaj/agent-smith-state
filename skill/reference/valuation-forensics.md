# Valuation & forensic checks (added 2026-09-07, cadence-wired 2026-09-07)

All four checks below — reverse-DCF, ROIC-vs-WACC, Beneish M-Score, Altman Z classification,
plus Form 4 insider-cluster in its own section — run automatically alongside every monthly
`smith-quality` dispatch (the SECOND deep review of the calendar month, same top-5-by-weight
ticker list — see deep-mode-dispatch.md's QUALITY-CHECK/VALUATION-CHECK/INSIDER-CLUSTER
triggers). Confirmed with the user 2026-09-07: the earlier on-demand-only design overstated the
cost by analogizing to the cycle+quality SUB-AGENT stacking incident (180,836 tokens, two full
agent dispatches landing on one run) — fetching FMP data for the valuation check spawns no new
agent at all, it's the orchestrator making ~25 tool calls and running one script, roughly
30-40K tokens for the whole monthly batch. Real, but a different order of magnitude, and worth
it monthly. All four can ALSO be run standalone at any time, any ticker, on an explicit
"valuation check" request.

## What it answers that nothing else in this codebase does

1. **Reverse DCF** — what growth rate does the CURRENT price already assume, and does the
   company's own cash-flow history support it? `VALUATION_STRETCHED` when the implied growth
   exceeds the trailing 5-year FCF CAGR by more than 15 percentage points (default,
   `--stretch-gap-pp`). Consumed by smith-strategist: **suppress a NEW BUY proposal** on a
   stretched name (an existing thesis/hold is unaffected — this gates new capital, not
   conviction).
2. **ROIC vs WACC** — is the business actually earning more than its cost of capital, or
   merely growing revenue while destroying capital? Negative spread sets
   `thesis_downgrade_signal: "WATCH"` (this codebase's real thesis vocabulary is exactly
   INTACT/STRENGTHENING/BROKEN/WATCH — no fifth status). Consumed by smith-thesis: **force the
   verdict to WATCH regardless of a beat** — a negative spread means the incremental dollar the
   company is reinvesting earns less than what it costs, independent of whether last quarter's
   print was good.
3. **Forensic risk** — Beneish M-Score (earnings-manipulation likelihood, computed here from
   two years of as-reported financials) combined with FMP's own Altman Z-Score (consumed
   as-is, never re-derived — see smith_valuation.py's module docstring for why). Either signal
   alone sets `forensic_risk: true`. Consumed by smith-quality/smith-strategist: **bypass
   normal Stage-1 bullish signals** on a forensic-risk name — a strengthening thesis or a
   bullish technical bucket does not override a live accounting-quality or solvency flag.

## How to run it

1. **Fetch the inputs via the FMP MCP server** (tool names `statements`, `discountedCashFlow`)
   for each held ticker you're checking — this session's own FMP plan tier has confirmed
   access to `statements` (`key-metrics`, `financial-scores`, `income-statement`,
   `cashflow-statement`, `balance-sheet-statement`) and `discountedCashFlow`. Pull:
   - `key-metrics` (annual, limit 3-6): `enterpriseValue`, `freeCashFlowToFirm` (3-6 years,
     oldest→newest, for `fcf_history`), `returnOnInvestedCapital` (×100 for `roic_pct`, and the
     same field across years for `roic_history_pct`).
   - `financial-scores`: `altmanZScore` straight through as `altman_z` — do not recompute it.
   - `as-reported-income-statements` / `as-reported-balance-statements` /
     `as-reported-cashflow-statements` (2 most recent fiscal years) for the Beneish inputs —
     see smith_valuation.py's `BENEISH_FIELDS` for the exact 13 field names each of `cur`/
     `prior` needs (receivables, revenue, cogs, current_assets, ppe_gross, securities,
     total_assets, sga, depreciation, long_term_debt, current_liabilities, net_income, cfo).
   - Risk-free rate: reuse smith-macro's `fed_funds_pct`/10-yr read if a deep run has one
     fresh this month; otherwise a single current 10-yr Treasury yield fetch.
   - Beta: `data_cache.betas` (already cached, SMH-benchmarked — do not mix in a raw market
     beta from FMP, same rule as everywhere else in this book).

2. **Build `--statements-json`** — one JSON object keyed by ticker, each value carrying
   whatever subset of the three checks' fields you fetched (each check is independently
   optional per ticker; a check missing its inputs for one ticker is skipped for that ticker
   only, named in that ticker's `data_quality`, never guessed). Full shape in
   `smith_valuation.py`'s module docstring.

3. **Run** `python3 scripts/smith_math.py valuation --run-dir <run> --statements-json <path>
   --today <date>`. Writes `compute_valuation.json` — `AGENT_SLICES["thesis"|"quality"|
   "strategist"]` already ref it (added 2026-09-07); it reports MISSING on every run this
   wasn't run on, by design, same as `catalyst_tail` on a run catalyst didn't dispatch.

## Insider transactions (Form 4) — free, runs monthly automatically

**Dispatched automatically** on the same run `smith-quality` runs on (deep-mode-dispatch.md's
QUALITY-CHECK trigger, second deep review of the month) — the orchestrator runs this itself,
same top-5-by-weight ticker list, before or alongside dispatching smith-quality; not something
smith-quality or any sub-agent invokes itself. Also runnable standalone on request.

`python3 scripts/smith_edgar.py insider-cluster --ticker <T> --price-usd <p>
--wk52-high-usd <h> --drawdown-from-high-pct <d>` fetches and parses the issuer's own recent
Form 4 filings directly from SEC EDGAR (same free, UA-declared curl path the rest of
`smith_edgar.py` already uses — confirmed live, no plan tier needed) and flags:
- `insider_sell_into_rally`: ≥3 distinct insiders sold in the lookback window (default 30d)
  while price sits within 5% of the 52-week high.
- `insider_buy_the_drawdown`: ≥2 distinct insiders bought while the drawdown from the high is
  ≥15%.

Only open-market P/S transactions count — grants, option exercises, gifts and tax-withholding
dispositions are excluded (routine compensation mechanics, not a discretionary bet).

**Consumer: smith-thesis, as an inline embed, not a ref file (added 2026-09-07).** This
command's output is small and per-ticker — there is no AGENT_SLICES ref for it, and there
should not be one; fold any `findings` you get for a ticker directly into that dispatch's
inline context, the same way catalyst/quality/signals tails are already handed to thesis. When
present, smith-thesis writes it into `evidence_for`/`evidence_against` with a
`(src: SEC Form 4, as_of <today>)` provenance tag, same rule as any other quantitative claim —
`insider_sell_into_rally` is `evidence_against`, `insider_buy_the_drawdown` is `evidence_for`.
Running this and NOT handing the result to smith-thesis is the same "computed, never consumed"
gap this codebase has already found and fixed twice this session (compute_bookcalc.json,
compute_valuation.json before the OPTIONAL_REFS fix) — don't reintroduce it a third time.

## Institutional ownership (Form 13F) — NOT available yet

FMP's `insiderTrades` and `form13F` tools both returned **ACCESS DENIED** live on this
account's plan tier ("requires the Starter, Premium, Ultimate, or Enterprise plan") — 2026-09-07.
`smith_edgar.py institutional-flow` has real, tested QoQ concentration-flow detection logic
(`--positions-json`, a `{"current":[...],"prior":[...]}` shape) ready to run the moment
ticker-keyed 13F data is available, but this repo has no free source for it — unlike Form 4,
13F requires scanning ACROSS many institutional filers' holdings tables for a ticker mention,
not one issuer's own filings, and there is no free ticker-keyed EDGAR endpoint for that. **Do
not attempt this check until either the FMP plan is upgraded or a separate scraping project is
built** — say so plainly rather than fabricating a flow reading.
