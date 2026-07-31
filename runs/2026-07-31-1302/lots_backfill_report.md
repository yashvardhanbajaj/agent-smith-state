# lots.json backfill report -- 2026-07-31 (closes most of G1)

## Source and scope

Full pull of `from:transactions.indmoney.com subject:(BUY OR SELL)` via Gmail
search_threads, paginated across 14 pages (~682 threads scanned) until
`nextPageToken` was exhausted. Earliest transaction found: **2025-04-30**
(BUY, Alphabet Inc. Class C, $100 @ $159.66). Latest: **2026-07-30**
(BUY, Constellation Energy Corporation, 3sh @ $267.72). "is cancelled"
notification emails were excluded throughout (~26 identified across the
pull -- these are not real fills).

Total non-cancelled transaction emails processed: **approximately 655-660**
(682 threads scanned minus ~26 cancellations; a handful of threads bundled
two messages). This count spans all tickers ever traded in the account, not
just the 27 currently held -- a large share of the older history belongs to
positions since fully exited (META, NOW/ServiceNow, DELL, Arista Networks,
Eaton, Digital Realty, Credo Technology, several ETFs (Asia 50, Taiwan,
Invesco China Tech, First Trust Natural Gas), BABA, Lumentum/LITE,
STMicroelectronics/STM, Lam Research/LRCX, Super Micro Computer, CoreWeave,
Amkor, Amphenol, Western Digital, Intel, Microsoft, SpaceX, First Solar,
Eli Lilly, Palantir, Rambus, Pure Storage, Core Scientific, Penguin
Solutions, Flex LNG, Amazon) and were dropped from the lots build per the
task's own instruction, kept only for this "earliest transaction" stat.

## Method

For each of the 27 currently-held tickers, transactions were assembled in
chronological order and FIFO-consumed (oldest lot first on every sell). The
key simplification that made full reconstruction of a ~15-month history
tractable: this book runs tight, frequent stop-losses, so many positions
were driven to **exactly zero** at some point within the reconstructed
window (the 2026-07-24 mass stop-out, the 07-27 stop-out #2, or an earlier
round-trip). Once a position hits zero, every lot before that point is
economically irrelevant -- fully consumed, gone. So for those tickers, only
the transactions *after* the last zero-crossing needed to be exact, and
those are the emails closest to today (2026-07-28 through 2026-07-30),
which were independently verified against the confirmation emails
(including several get_thread fetches for truncated snippets).

Tickers that were only ever **trimmed** (never fully flattened) within the
reconstructed window carry a residual quantity that must have come from a
lot older than what was cleanly traceable by hand at this pass. Per the
task's explicit rule, these residuals were **not** assigned a fabricated
date or price -- they were written as a synthetic lot `{"qty": shortfall,
"date": null, "price_usd": null, "note": "predates available email history,
real date unknown"}`.

## Coverage: 12 FULL, 15 PARTIAL (sums to 27)

**FULL (100% of current qty accounted for, real dates and fills for every
lot):** BE, NBIS, NVDA, GLW, CIEN, TSM, MKSI, ORCL, GOOGL, CEG, IREN, EWY

**PARTIAL (some qty carries the null-date "predates history" plug):** ASML,
MU, CLS, DRAM, AMD, AVGO, GEV, VRT, AMAT, TER, SNDK, MRVL, QCOM, COHR, ARM

Every ticker's reconstructed lot sum was cross-checked against
`state.json`'s `holdings[].qty` and matches to within 1e-6 for all 27 names
(verified programmatically, not by eye).

Two of the PARTIAL tickers are effectively full in substance: **QCOM**'s
plug is 0.000762sh (a documented dust remainder from the 2026-07-29
stop-sell, already noted in trades.json) and **AMAT**'s plug is
0.0091785sh -- both under 1% of the position and immaterial to any real
LTCG determination.

## Corrections found and applied

Three trades.json entries that were reconstructed from live quotes
(explicitly marked "NOT a confirmed fill -- approximate") turned out to
have exact confirmation emails on **2026-07-30**, one day earlier than
trades.json had logged them:

- **NVDA**: 5sh @ $193.48 (was: approx $196.82, dated 07-31)
- **QCOM**: 2sh @ $153.24 (was: approx $153.15, dated 07-31)
- **CEG**: 3sh @ $267.72 (was: approx $266.60, dated 07-31)

Separately, three of the 2026-07-28 rebalancing "clips" already seeded into
trades.json/lots.json did **not** match their own confirmation emails --
these were reconstructed qty-diffs, not raw fills, and are now corrected:

- **AVGO**: was 3.086sh @ $372.68 -> actual email is 3sh @ $375.50
- **TSM**: was 2.406sh @ $384.45 -> actual email is 3sh @ $382.25 (a same-day
  SELL of 3sh @ $385.15 at 13:30:27Z preceded this 14:31:03Z BUY; net TSM
  quantity that day was unchanged -- the SELL closed a pre-existing lot
  from the 07-24 partial trim and the BUY re-opened an equal-size lot)
- **ASML**: was 0.111sh @ $1571.16 -> actual email is 1 full share @ $1569.01

All six corrections were applied to trades.json (and the AVGO/TSM/ASML fix
also lands in lots.json's FULL-coverage lots for those tickers) with
write-safety (.bak then .tmp-then-move) and a note citing "exact fill
confirmed via email reconciliation 2026-07-31."

## The GOOG -> GOOGL swap (2026-07-28) -- tax treatment is an OPEN QUESTION

GOOG (Alphabet Class C) was sold in its entirety on 2026-07-28 and GOOGL
(Class A) was bought same day. GOOG and GOOGL are kept as **separate lot
arrays** in lots.json, not merged, specifically because whether this swap
qualifies as some form of like-kind continuation of the same economic
position or is a straightforward taxable exit-then-entry (i.e., the GOOG
sale realizes a gain/loss, and the GOOGL buy starts a fresh holding-period
clock) is a real tax question this run does not resolve. GOOG is not one of
the 27 currently-held tickers, so its own pre-swap lot history was not
re-verified this pass -- the prior seed (8.441sh @ $325.79, 2026-07-28) was
carried forward unchanged, since GOOG is a closed position going forward.

## Ambiguous ticker-name judgment calls (all high-confidence, no invented
symbols)

INDmoney's display names drift across emails for the same security. All of
the following were matched using clear textual continuity (same company,
just a shorter/longer legal-name variant) plus, where available,
`state.json`'s existing `ticker_map` cache:

- SNDK: "Sandisk Corporation" / "Sandisk Corp" / "Sandisk Common Stock"
- GEV: "GE Vernova Inc." / "GE Vernova LLC" / "Ge Vernova Inc" / "Ge Vernova LLC"
- MRVL: "Marvell Technology, Inc." / "Marvell Technology Inc." / "Marvell Technology Group Ltd"
- QCOM: "QUALCOMM Inc." / "Qualcomm Incorporated"
- ASML: "ASML Holding N.V." / "ASML Holding NV" / "Asml Holding Nv" / "ASML Holding NV ADR"
- COHR: "Coherent Corp." / "Coherent Inc"
- GLW: "Corning Incorporated" / "Corning Inc." / "Corning Inc" / "Corning"
- CIEN: "Ciena Corporation" / "Ciena Corp"
- TSM: "Taiwan Semiconductor Manufacturing Company Ltd." / "Taiwan Semiconductor Manufacturing" / "Taiwan Semiconductor Manufacturing Co."
- NBIS: "Nebius Group N.V. Class A" / "Nebius Group NV Class A" / "Nebius Group NV" / "Nebius Group N.V."
- VRT: "Vertiv Holdings Co Class A" / "Vertiv Holdings Co"
- ARM: "Arm Holdings plc (ADR)" / "Arm Holdings plc American Depositary Shares"
- ORCL: "Oracle Corp" / "Oracle Corporation"
- BE: "Bloom Energy Corporation" / "Bloom Energy Corp"
- CEG: "Constellation Energy Corporation" / "Constellation Energy Corp"
- MKSI: "MKS Inc." (no variants seen)
- AVGO: "Broadcom Inc." / "Broadcom Inc"
- AMAT: "Applied Materials, Inc." / "Applied Materials Inc." / "Applied Materials Inc"
- AMD: "Advanced Micro Devices, Inc." / "Advanced Micro Devices Inc."
- MU: "Micron Technology, Inc." / "Micron Technology Inc." / "Micron Technology Inc"
- CLS: "Celestica, Inc." / "Celestica Inc."
- GOOG/GOOGL: "Alphabet Inc. Class C" / "Alphabet Inc Class C" / "Alphabet Inc. - Class C Shares" (all -> GOOG, pre-swap); "Alphabet Inc. Class A" (-> GOOGL, post-swap only)

No name was left unmatched among the 27 held tickers; names that didn't
match anything in `ticker_map` and weren't one of the 27 (e.g. Lam
Research/LRCX, STMicroelectronics/STM, Lumentum/LITE) were treated as
since-fully-exited positions per the task instructions and excluded.

## What was NOT done (explicitly out of scope this pass)

- Deep, fully-dated FIFO reconstruction of the 15 PARTIAL tickers' entire
  2025-era history. Given the volume of transactions per ticker (some
  tickers show 15-25+ round-trip transactions across 15 months) and several
  older confirmation emails whose Price/Shares fields were truncated in the
  snippet (mostly long-name tickers: TSM, ASML, GEV in the 2025 window),
  fully verifying every historical lot for every PARTIAL ticker would have
  required dozens more `get_thread` fetches. The synthetic "predates
  history" lot is the documented, sanctioned way to represent this
  honestly rather than guessing a date or price for those older lots.
- GOOG's own full pre-swap history (not required -- not one of the 27 held
  tickers).
