# HBMTracker Integration — Tier 2.1 Implementation
**Completed 2026-07-26**

---

## What Was Implemented

Modified `/Users/yb/.claude/agents/smith-thesis.md` to integrate HBMTracker data reconciliation with Memory-cluster thesis verdicts.

### Changes to smith-thesis.md

#### Description
- Added Tier 2.1 note: "Loads HBMTracker/history.json + forecast.json to reconcile Memory-cluster thesis vs pricing data"

#### TOOLS Section
- Added WebFetch tool for HBMTracker/history.json and /forecast.json (local file paths, not MCP)
- Triggered when any Memory-cluster names (MU, SNDK, DRAM, EWY) are held

#### TASKS Section — New Task 6: HBMTracker Reconciliation
**Logic:**
1. When Memory-cluster names are held, load HBMTracker history.json
2. Extract latest HBM3E ASP from the most recent non-null history row
3. Compute trend vs prior entries (e.g., current $8-10/GB vs H1 2025 peak $17-20/GB = -51% decline)
4. Compare against Memory-cluster thesis verdicts:
   - Flag if thesis is "strengthening" while HBM3E ASP is collapsing
   - Reconcile by either:
     - (a) Acknowledging that ASP decline is offset by demand strength (volume > ASP)
     - (b) Proposing thesis downgrade to WATCH/BROKEN due to pricing pressure
5. Include profitability crossover context (DDR5 now > HBM3E for first time, per 2026-04-21 TrendForce)
6. Include forward forecast (2027 HBM contract prices expected to surge 80-150%)

#### OUTPUT Section
- Added thesis_tensions list to JSON tail
- Schema per entry: `{metric, current_value, peak_value, trend_pct, verdict_conflict, reconciliation}`
- Example entry:
  ```json
  {
    "metric": "hbm3e_asp_usd_per_gb",
    "current_value": 9,
    "peak_value": 18.5,
    "trend_pct": -51,
    "verdict_conflict": "Memory cluster marked 'strengthening' but ASP collapsing",
    "reconciliation": "Demand (volume) may offset ASP decline — or thesis should downgrade to WATCH"
  }
  ```

#### GUARDRAILS Section
- Increased tool-call budget from 12 → 14 (allow HBMTracker WebFetch)
- Added trust boundary: permit WebFetch of `/Users/yb/Claude/HBMTracker/` (local file paths only)
- Added plausibility band: HBM ASP must be within 0-50 USD/GB range
- Added reconciliation guardrail: tensions only flagged when there is a clear verdict mismatch (e.g., "strengthening" verdict contradicted by -51% ASP decline)

---

## How It Works

### Scenario: Memory Cluster Thesis Check

**Current state (as of 2026-07-26):**
- HBM3E ASP (latest, 2026-07-19): $8-10/GB
- HBM3E ASP (H1 2025 peak): $17-20/GB
- Decline: -51%
- Memory holdings: MU ("intact"), SNDK ("watch"), DRAM ("intact"), EWY ("intact")

**Smith-thesis run (deep mode):**
1. Holdings include MU, SNDK, DRAM, EWY (all Memory-cluster)
2. Agent WebFetches HBMTracker/history.json and /forecast.json
3. Extracts latest HBM3E ASP: $8-10/GB (from 2026-07-19 row)
4. Computes peak and trend: $8-10 vs $17-20 peak = -51% decline
5. Checks thesis verdicts:
   - MU: "strengthening" ← CONFLICT: ASP down 51%, but volume (HBM demand) may be rising
   - SNDK: "watch" ← ALIGNED: already cautious due to peer-laggard signal
   - DRAM: "intact" ← NO CONFLICT: ETF holding, thesis unaffected by single-component pricing
   - EWY: "intact" ← NO CONFLICT: regional ETF, SK Hynix embedded but diversified
6. Outputs thesis_tensions for MU only:
   ```json
   {
     "metric": "hbm3e_asp_usd_per_gb",
     "current_value": 9,
     "peak_value": 18.5,
     "trend_pct": -51,
     "verdict_conflict": "MU marked 'strengthening' but HBM3E ASP collapsing 51% from peak",
     "reconciliation": "MU thesis assumes demand volume more than offsets ASP (hyperscaler HBM buys rising despite per-GB price). Forward forecast (2027 HBM prices +80-150%) may validate this. OR downgrade MU to WATCH until volume-vs-ASP tradeoff clarifies."
   }
   ```
7. Includes forward context:
   - DDR5 profitability now exceeds HBM3E (first time, 2026-04-21) — margin compression signal
   - 2027 contract prices expected +80-150% — timing-dependent: opportunity if volume locks in now, cap risk if demand softens

---

## Data Sources

### HBMTracker/history.json (Real)
- 11 history rows spanning 2024-05-06 to 2026-07-19
- Latest (2026-07-19): HBM3E $8-10/GB, $300/stack, 36GB/stack
- Previous (2026-04-21): Notes DDR5-vs-HBM3E profitability crossover
- Full trend visible: from H1 2025 peak ($17-20) through Apr 2026 correction ($13-17) to current ($8-10)

### HBMTracker/forecast.json (Real)
- 4 forecasts for 2026-2027 horizons
- Key: 2027 HBM contract prices expected to surge 80-150% (range reflects stalled negotiations as of Jun 2026)
- CXMT HBM3 downside risk (domestic Chinese supply, 2027 timeline disputed)

---

## Why This Matters

**Friday 07-24 Selloff Context:**
The -10.79% SNDK, -8.75% DRAM move happened in a session when:
- HBM3E ASP had already collapsed 51% from peak
- DDR5 profitability had crossed above HBM3E (historic first)
- Forward guidance for 2027 was +80-150%, not near-term relief

**Without reconciliation:** Memory positions marked "strengthening" or "intact" read as contradicted by pricing.

**With reconciliation:** Agent can answer: "Is this demand-led (volume rising despite lower ASP, typical of supply-constrained HBM market) or margin-pressure-led (hyperscalers negotiating lower prices)?" The 2027 forecast (+80-150%) suggests demand-led, not margin-led — supporting the "strengthening" thesis **if volume is confirmed rising.**

---

## Next Step: Deep-Run Test

When smith-thesis is invoked on a deep run (or manually for testing):
1. It will WebFetch HBMTracker data (2 files)
2. Compute thesis_tensions for Memory holdings
3. Output reconciliation guidance for the strategist
4. Strategist can then decide: carry forward MU "strengthening" (volume thesis), or downgrade to WATCH (await volume confirmation)

**Testing command** (to be run by orchestrator or manually):
```bash
# Within a deep-run mode, smith-thesis will automatically load HBMTracker
# when holdings include MU/SNDK/DRAM/EWY and emit thesis_tensions in output
```

**Expected output addition to smith-thesis JSON:**
```json
{
  "thesis_tensions": [
    {
      "metric": "hbm3e_asp_usd_per_gb",
      "current_value": 9,
      "peak_value": 18.5,
      "trend_pct": -51,
      "verdict_conflict": "MU strengthening but ASP down 51%",
      "reconciliation": "Volume-led thesis (demand > ASP) is plausible given tight HBM2e/HBM3/HBM3e capacity sold-out through 2026; 2027 forecast +80-150% supports this. Confirm volume data to validate."
    }
  ],
  "forward_signals": [
    "DDR5 profitability now exceeds HBM3E (first time, 2026-04-21) — margin compression visible",
    "2027 HBM contract prices expected +80-150% — timing-dependent opportunity if demand locks in now"
  ]
}
```

---

## Status: Ready for Deployment

- ✅ Agent code updated and documented
- ✅ Data sources validated (HBMTracker history.json + forecast.json readable and well-formed)
- ✅ Reconciliation logic designed and specified
- ✅ Guardrails added (ASP plausibility band, conflict-only flagging)
- ⏳ First live deep-run test pending (Mon 2026-07-28 or user-triggered)

All code in `/Users/yb/.claude/agents/smith-thesis.md` is ready to execute.
