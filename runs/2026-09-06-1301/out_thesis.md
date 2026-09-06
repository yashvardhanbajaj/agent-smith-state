# Thesis & Factor — 2026-09-06 (deep)

## 1. Thesis table (changes only; rest unchanged per prior run)

**APH (NEW, 2.08% wt)** — Amphenol Corp, 10sh. Thesis: high-speed interconnect/cable-assembly supplier for AI servers and datacenter networking (IT Datacom segment now the fastest-growing unit, direct beneficiary of AI-server buildout rather than a diversified industrial play). Status: **strengthening** (new position, default constructive until first review cycle).
- evidence_for: [{"claim":"IT Datacom segment is APH's largest and fastest-growing, driven by AI server/high-speed interconnect demand","date":"2026-09-06","source":"orchestrator holdings note / sector classification, qualitative — no quantified figure available this run"}]
- evidence_against: [{"claim":"none found this run — no earnings/news check performed; new position added below G58 verification trigger (no discrete corporate event to check yet)","date":"2026-09-06","source":"n/a"}]
- verified: unverified (no discrete corporate event this run; carve-out — new-position classification only, not an earnings/guidance claim)

**AVGO** — no status change (watch, unchanged since 2026-09-03). Re-checked load-bearing Q3 FY26 print via SEC EDGAR XBRL (`smith_edgar.py verify --ticker AVGO`): latest filed quarter on EDGAR is Q2 FY26 ($22.187B rev, ended 2026-05-03, 10-Q filed 2026-06-09) — the Q3 FY26 print (~$29.6B, reported 2026-09-02) has not yet reached EDGAR (10-Q filing lag is normal, ~4-6wk). Existing `secondary` (stockanalysis.com) verification stands; cannot upgrade to primary yet. No change to evidence arrays.

**MSFT** — no status change (watch, unchanged). No discrete earnings/guidance event to verify this run (position built via two open-market buys, not tied to a print); stays `unverified` per G58 (verification trigger not met — no corporate event).

## 2. Friday 2026-09-04 memory melt-up — reconciliation

SNDK +11.9%, SKHY +8.1%, MU +6.1%, WDC +5.9%, KLAC +7.3%, DRAM ETF +6.6% vs SMH +2.61% (all names ran 2-4.5x the index beta). HBM tracker snapshot (`shared/hbm_tracker.json`) is dated **2026-08-05, staleness = 32 days as of today** — exceeds the ~30-day threshold; **flagged stale, confidence degraded**. Within that stale window: HBM3E stack-derived basis is flat (2026-07-19→2026-08-05, trend_pct_within_basis = 0.0%); contract-quote basis shows a prior -18.92% run through 2026-01-15 (old news, pre-dates the 2026 price-hike cycle); TrendForce forecast (2025-12-24, tier1) called an 18-22% HBM3E contract hike for 2026 deliveries. **No fresh datapoint in the tracker covers 2026-09-04** — the tracker cannot confirm or deny a fundamental driver for Friday's move.

**Verdict: this reads as late-cycle blow-off risk, not thesis confirmation.** The move is priced-only — no corroborating fundamental datapoint this recent in-house, magnitude is 2-4.5x the sector benchmark in a single session (classic rotation/short-covering signature), and it lands on a `cycle_position: late` (confidence medium) standing call. Evidence for "strengthening": broad participation across the whole memory/storage complex plus semicap (KLAC) argues a real catalyst, not one-name noise. Evidence against: SNDK (NAND, not HBM) leading at +11.9% with no tracker corroboration, and DRAM ETF's move outrunning any known contract-price data, is consistent with a squeeze/rotation into laggards rather than a re-rating on fresh fundamentals. **No thesis status change is warranted from this signal alone** — recommend smith-catalyst identify the proximate news driver (earnings, M&A, index rebalance, short interest data) before this is treated as durable.

## 3. Factor cluster note
APH added to **AI Networking/Optics** (exact policy.json cluster_targets string) — joins MRVL, AVGO, CIEN, GLW, COHR, LITE, ALAB. Cluster now carries an additional 2.08pp of book weight; full recompute deferred to the strategist's drift script.

## 4. Data quality
- HBM tracker snapshot is 32 days stale (last_run 2026-08-05 vs today 2026-09-06) — exceeded the ~30-day confidence threshold; all HBM reconciliation above is weighted accordingly.
- No fundamental datapoint in-house covers the 2026-09-04 memory rally; proximate cause unresolved (recommend smith-catalyst follow-up).
- AVGO Q3 FY26 print not yet on EDGAR (filing lag) — could not upgrade verification tier this run.
- APH has no earnings/news check yet (new position, below G58 verification trigger).
