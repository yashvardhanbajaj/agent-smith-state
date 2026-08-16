# SMITH-TAX — 2026-08-17 (deep) — first dispatch

**Lot file verified.** Re-ran `smith_math.py lots --base-dir . --holdings runs/2026-08-17-0434/holdings.json`:
36 tickers / **71 open lots, 0 undated, 0 unpriced, 0 reconstructed**, all `email_confirmed`; reconciliation
**35/35, 0 mismatches, 0 orphans, 0 phantom shorts**. Trusted; sequenced against it.

**The honest limit, up front.** Earliest open lot in the live book is **2026-07-15** (CLS, 0.003266sh). At the
policy-confirmed boundary (`policy.json ltcg_boundary_months: 24`) the first LTCG crossing is **2028-07-15**.
Every open lot is short-term. **No trim on this list can be deferred into long-term treatment this FY or next.**
`compute_book.ltcg_flags` is empty and that is correct, not a gap. LTCG sequencing has zero live decisions in it.

**Prices**: all $ figures from `compute_book.json` position prices — INDmoney snapshot embedded in the
2026-08-17 04:34 IST run, US session **closed** (last close). Re-cost at execution; a gap open moves every
gain figure below.

## 1. FIFO vs HIFO — 8 open trims

`tax_delta_usd` = realised gain FIFO minus HIFO, i.e. the **taxable-amount** difference. Cash tax is that times
the marginal slab (Indian STCG on foreign equity is slab-rate; I don't hold the slab, so I don't multiply it).
Materiality bar: $25 of gain delta.

| # | Ticker | Size | %pos | FIFO lots | Gain FIFO | HIFO lots | Gain HIFO | Δ | Material |
|---|--------|------|------|-----------|-----------|-----------|-----------|---|----------|
| P-089 | MU | $500 | 20.6% | 07-29 @788.81 ×0.000366; 07-31 @849.49 ×0.5141 | **+$62.98** | 08-13 @970.36 ×0.5000; 07-31 @850.79 ×0.0145 | **+$2.50** | **$60.48** | **YES** |
| P-090 | NBIS | $700 | 42.0% | 08-07 @188.27 ×2.5204 | **+$225.49** | 08-12 @234.79 ×1.0; 08-07 @188.27 ×1.5204 | **+$178.97** | **$46.52** | **YES** |
| P-082 | MSFT | $370 | 24.9% | 08-06 @495.97 ×0.7467 | **−$0.35** | 08-10 @509.86 ×0.7467 | **−$10.72** | $10.37 | no |
| P-099 | SNDK | $280 | 33.6% | 07-28 @1079.59 ×0.0081; 08-07 @1212.38 ×0.1624 | **+$74.27** | 08-07 @1212.38 ×0.1706 | **+$73.19** | $1.08 | no |
| P-087 | NVDA | $550 | 16.3% | 07-28 @197.51 ×2.4422 | **+$67.64** | identical (single lot) | +$67.64 | $0.00 | no |
| P-088 | SKHY | $900 | 49.4% | 08-06 @143.02 ×1; 08-07 @138.07 ×4.4313 | **+$145.14** | identical (oldest = highest basis) | +$145.14 | $0.00 | no |
| P-091 | DRAM | $450 | 26.3% | 07-16 @54.31 ×5; 07-28 @48.00 ×2.9028 | **+$39.12** | identical (oldest = highest basis) | +$39.12 | $0.00 | no |
| P-097 | BX | $185 | 24.8% | 08-10 @139.38 ×1.2387 | **+$12.35** | identical (single lot) | +$12.35 | $0.00 | no |

Every trim is fully coverable — no proposal runs short of lots.

**Two names matter: MU and NBIS.** HIFO instead of FIFO cuts realised gain by **$107.00** across $1,200 of selling. The rest is noise — four trims are *mathematically identical* under both methods (NVDA/BX consume a single lot; SKHY/DRAM happen to have oldest = highest basis), MSFT and SNDK differ by $10 and $1. **Do not complicate six executions to chase $11.**

**MU — sharpest, most caveated.** HIFO sells the 08-13 half-share bought at $970.36 against a $971.86 mark (near-zero gain), leaving the $788.81/$849.49 lots intact: $2.50 booked instead of $63. But the gain is **deferred, not erased** — it migrates into the remainder, and with no LTCG boundary reachable this is pure cross-FY timing, not a rate arbitrage. Worth having only to push taxable gain out of FY26-27. **NBIS** — HIFO leads with the 08-12 lot at $234.79 (its only expensive lot) before 08-07 @$188.27; $46.52 less gain on $700, the cleanest genuine saving here. **MSFT is the only trim that books a loss either way** (wavg basis $500.60 vs $495.50) and HIFO makes the loss *larger*, −$10.72 vs −$0.35 — same rule, inverted arithmetic.

## 2. Loss-harvesting scan — 13 names below basis, $283.21 total

| Ticker | Wavg basis | Price | Unrealised | % | Thesis | Tension |
|--------|-----------|-------|-----------|---|--------|---------|
| STM | $56.29 | $53.93 | −$47.17 | −4.19% | watch | none |
| AMZN | $271.51 | $262.71 | −$44.04 | −3.24% | **strengthening** | harvesting sells conviction |
| BE | $241.32 | $229.99 | −$31.16 | −4.70% | **strengthening** | harvesting sells conviction |
| TXN | $282.62 | $273.49 | −$27.40 | −3.23% | watch | none |
| COHR | $336.40 | $327.30 | −$27.31 | −2.71% | watch | none |
| AVGO | $398.62 | $393.07 | −$22.17 | −1.39% | **strengthening** | harvesting sells conviction |
| BABA | $130.71 | $122.19 | −$17.05 | −6.52% | watch | none |
| IREN | $45.60 | $44.77 | −$16.61 | −1.82% | **strengthening** | harvesting sells conviction |
| MSFT | $500.60 | $495.50 | −$15.29 | −1.02% | watch | already carries open trim P-082 |
| AMAT | $547.64 | $534.65 | −$13.09 | −2.37% | **strengthening** | harvesting sells conviction |
| VRT | $291.04 | $287.13 | −$11.73 | −1.34% | watch | none |
| ARM | $282.65 | $279.50 | −$9.45 | −1.11% | watch | none |
| GLW | $166.27 | $166.02 | −$0.74 | −0.15% | strengthening | immaterial |

**Whole harvestable pool is $283 — 0.65% of a $43,743 book, largest single name $47.** Five of thirteen are `strengthening`: harvesting those sells something the book wants to own for a sub-$50 offset. Tension flagged, nothing recommended. Only MSFT overlaps the strategist's trim list — the two lists barely meet.

**Repurchase note (not a wash-sale rule).** India has **no** US-style 30-day wash-sale prohibition on equities; harvest-and-rebuy is legal. The economics still change: rebuying within days resets basis lower and turns the harvest into a paid spread plus brokerage against a $47 ceiling — that arithmetic loses. No collision exists anyway: neither buy leg (QCOM P-098, CEG P-093) sits below its basis, so no proposed purchase repurchases a harvested name.

## 3. FY window

FY ends **2027-03-31**; today **2026-08-17**, **226 days out**. **Not** in the Jan–Mar harvesting window; no
clock pressure on anything above. Next genuinely time-sensitive date for this desk is ~**January 2027**; next
date LTCG matters at all is **2028-07-15**.

## 4. Data quality

- **FY26-27 realised gains NOT computable; not estimated.** 165 sells since 2026-04-01 (~$128.6k gross) but `smith_math.py lots` tracks lot *consumption* only and emits no realised-P&L block. Seven G71 reconciliation adjustments (SMCI, NVDA, GOOG ×2, TSM ×2, AMD) carry an explicitly **null basis** and FY sells consumed some. Any FY realised figure requires imputing those — not done. Hence harvest value is stated as size, never as tax saved.
- **LLY dust**: lots.json carries a 36th ticker, LLY 4e-06sh @$934.66 (2026-04-02), not in the broker's 35 positions, worth ≈$0.004. Not an engine orphan, not a harvest candidate; it is why the raw file shows an April date. Excluded from the earliest-open-lot figure.
- **G80 accepted residue** (engine warning): 24 pre-2026-08-15 rows on old Amount/Price derivation, ~$29 total basis error, ~$12 on live positions (0.027% of book). Below any threshold that changes a selection here.
- **Stale policy prose**: `policy.json` still reads "LTCG per-lot purchase dates unavailable — lots.json needs seeding (G1)". G1 closed 2026-08-15. `ltcg_boundary_months: 24` is correct and was used; only the note is stale.
