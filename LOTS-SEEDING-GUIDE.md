# Seeding lots.json from INDmoney Order History
**Unblocks smith-tax agent (Tier 3.3) and LTCG tracking on all trim proposals.**

---

## Why This Matters

`lots.json` is currently empty (G1 standing gap since 07-12). Until populated with purchase dates and prices, the tax agent cannot:
- Sequence trims by LTCG proximity (24-month India boundary)
- Flag wash-sale risks (can't re-buy within 30d of a loss)
- Identify year-end tax-harvesting windows (Jan-Mar FY closing)
- Report tax impact (LTCG vs STCG rate) on every trim proposal

**Result:** Trim proposals lack tax context. A $1000 trim might be a LTCG (favorable) or STCG (unfavorable) — the proposal has no way to know.

**Impact after seeding:** smith-tax runs on first deep review post-seeding and immediately starts flagging LTCG boundaries, making every de-risk decision tax-aware.

---

## Data Source: INDmoney Order History

INDmoney holds the authoritative record of all your US-listed purchase dates and prices.

### Step 1: Export Order History from INDmoney
1. Log into INDmoney web/app
2. Navigate to **Portfolio → US Stocks → Orders** (or **Order History**)
3. Filter for **filled** orders only (not pending/cancelled)
4. Look for the **oldest holdings** first; focus on positions you still hold (ignore already-exited tickers)
5. Export to CSV or screenshot if no bulk export available

**Fields you need from the export:**
- Ticker (or "Instrument Name")
- Qty
- Purchase date (YYYY-MM-DD format)
- Price USD (cost per share)

### Step 2: Map Against Current Holdings

Cross-check the exports against current `holdings.json` to identify which purchases are still held (vs exited on 07-24 or earlier).

**Holdings still held (21 names as of 07-24 post-close):**
SNDK, DRAM, NVDA, TSM, MU, ASML, EWY, CLS, LRCX, TER, QCOM, GLW, MRVL, CIEN, VRT, DELL, AMD, AMAT, COHR, ARM, ORCL

**Holdings exited or trimmed (use PARTIAL lot dates if trimmed, not full exit):**
GLW (⅓ exited 07-24), STM (full exit 07-24), DLR (exit 07-14), ETN (exit 07-14), ANET (exit 07-14), CRDO (exit 07-16), LITE (exit 07-24), NBIS (exit 07-24), IREN (exit 07-24), GOOG (exit 07-24), META (exit 07-24), BABA (exit 07-24), CQQQ (exit 07-18)

**For this first pass, prioritize current holdings.** Exited positions can be added later (needed for wash-sale detection and LTCG timing on re-entries).

### Step 3: Populate lots.json

Schema (already in template):
```json
{
  "_metadata": {
    "schema": "lot-based tax tracking for LTCG/STCG and wash-sale detection",
    "ltcg_boundary_months": 24,
    "seeded_as_of": "2026-07-26"
  },
  "TICKER": [
    {
      "qty": 1.5,
      "date": "2024-02-10",
      "price_usd": 185.50,
      "notes": "original entry"
    },
    {
      "qty": 0.5,
      "date": "2024-06-15",
      "price_usd": 210.00,
      "notes": "top-up during consolidation"
    }
  ],
  "ANOTHER_TICKER": [...]
}
```

**How to fill it:**

For each held ticker:
1. List **every purchase lot** separately (not aggregated)
   - If you bought MU twice (Feb and June), create two entries
   - If you bought MU in March, held, then trimmed in July, create ONE entry with the full original qty (the tax agent will sequence from this when you request a trim)
2. Use INDmoney order date as `date` (YYYY-MM-DD)
3. Use INDmoney fill price as `price_usd`
4. Leave `notes` blank or use "from INDmoney export 2026-07-26" as a batch note

**If you have multiple partial fills (e.g., "MU x 1 @ $85, x 1 @ $88 on the same day"), combine them into one lot:**
```json
"MU": [
  {
    "qty": 2,
    "date": "2024-09-15",
    "price_usd": 86.50,
    "notes": "two fills same day, blended price"
  }
]
```

---

## How to Do This in Claude

**Option A: Copy-paste INDmoney CSV, I'll parse it**
- Export INDmoney orders as CSV
- Paste the CSV into chat
- I'll parse and populate lots.json

**Option B: Manual population (5-10 min for ~20-25 names)**
- Copy the template from lots.json
- Manually enter each ticker's purchases from INDmoney
- Paste the completed JSON; I'll validate and commit

**Option C: If you have a spreadsheet already**
- Share the format (column names + a few rows)
- I'll automate the transformation

---

## Next Step After Seeding

Once lots.json is seeded:
1. Run `smith_math.py book` to verify LTCG flags surface
2. Trigger smith-tax agent on next deep review to see tax-optimized trim sequencing
3. Every trim proposal will include "tax_impact: LTCG|STCG" and "months_to_ltcg" fields

---

## Timeline

- **LTCG boundary for purchases before 2024-07-26:** happens on/after 2026-07-26 (can harvest now at LTCG rate)
- **LTCG boundary for purchases before 2025-07-26:** happens on/after 2027-07-26
- **Year-end tax harvest window:** 2027-01-15 onwards (Jan 15 through Mar 31 FY close)

So any purchases made before 2024-07-26 are **already eligible for LTCG** — good news if you want to raise cash at the favorable rate.

---

## Example: MU

If INDmoney shows:
```
Instrument: Micron Technology Inc
Date: 2024-03-10
Qty: 2.000365376
Price: $75.50
Filled: Yes
```

Then in lots.json:
```json
"MU": [
  {
    "qty": 2.000365376,
    "date": "2024-03-10",
    "price_usd": 75.50,
    "notes": "from INDmoney export"
  }
]
```

---

**Ready to help. Send me the INDmoney order export (CSV, screenshot, or copy-paste), and I'll get lots.json seeded and smith-tax unblocked.**
