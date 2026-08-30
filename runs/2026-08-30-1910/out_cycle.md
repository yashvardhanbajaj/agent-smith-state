# smith-cycle — AI-capex cycle position — 2026-08-30 (first persisted read)

## CALL: `late` — confidence MEDIUM
Prior: none. `state.cycle_position` has never existed; this is the baseline.

**The two claims, separated (this is the whole job):**
- **Is AI capex strong?** Yes, and it is still *accelerating on the spend line*. Guidance is being RAISED, not held.
- **Is it fully priced?** No — and that is the surprise. The market is paying **LESS** per unit of
  supplier capex growth than three months ago. This is not a fully-priced melt-up; it is a **de-rating
  on accelerating fundamentals**, which is the specific late-cycle signature.

## Why `late` and not `mid` or `accelerating`
`late` = capex still growing, second derivative decelerating, margin regime peaking. Two of three hold:

1. **Margin regime PEAKING — documented, guided, not inferred.** NVDA Q2 GM 75% → Q3 guided 74% →
   Q4 trough 71–72%, recovering only to 72–73% in FY28. Cause is memory cost, not demand: NVDA's
   component commitments went **$119bn → $279bn in one quarter**, memory's share of a rack BOM went
   from 5–10% (Blackwell) to 25–30% (Vera Rubin) — ~$370k → ~$2M per rack. NVDA is passing it on at
   **+15% on AI servers**. Cost pass-through at the top of the chain is a late-cycle behaviour.
2. **Memory second derivative rolling over while the level still rises.** Conventional DRAM contract:
   +90–95% QoQ (1Q26) → +58–63% (2Q26) → **+13–18% (3Q26, gains explicitly "narrowing")**. Prices are
   still up. The *rate* has fallen by roughly a factor of five in two quarters. Level excellent,
   acceleration gone — exactly the reading absolute numbers conceal.
3. **Inventory tell is ABSENT.** No rising channel inventory days found; the evidence runs the other
   way (reduced authorised-distributor stock, allocation notes, lead times extending). This missing
   leg is why confidence is MEDIUM, not high, and why this is late-*by-cost*, not late-by-demand.

## The 08-28 bifurcation — the discriminating evidence, weighed
SMH −3.47% while AMZN +3.97% / MSFT +1.68% / GOOG +1.53%. Buyers outperformed suppliers on the same
tape. Mechanism is credit, not earnings: NVDA 5Y CDS ~2x in two months; ORCL cut to BBB− at 215bp;
~$500bn AI-related debt issued in 2026; NVDA backstopping ~$125bn of a $500bn third-party compute-
financing platform. Meanwhile good numbers are punished — MRVL beat AND guided ~4% above consensus
and fell 10.28%; COHR beat revenue and EPS with a raised FY27 outlook and fell; NVDA beat (+6.16% EPS
surprise) with 2-day drift −5.3%. When the marginal financier of capex is levered and the marginal
buyer refuses to pay for a beat, the cycle's *financial* clock is later than its *physical* one.

## Components
| Component | Read |
|---|---|
| Hyperscaler capex revisions | **RAISED** — META $115–135bn → $125–145bn (2nd raise), GOOGL ceiling → $205bn; ~$700–725bn combined 2026, +77% YoY |
| Memory contract | **UP**, decelerating (3Q26 +13–18% QoQ vs 1Q26 +90–95%); HBM 2027 contracts expected multiples higher |
| Memory spot | **DOWN** (consumer channel) — 16GB DDR4 second-hand ~450 CNY, >30% below early-2026 peak |
| **Weighted** | **CONTRACT.** HBM has no spot market; the only live spot series is Huaqiangbei used consumer modules, which does not map to this book's AI-capex exposure. Not blended. |
| Semicap book-to-bill | **null** — no B2B figure sourced. Proxy is strongly positive: etch/depo lead times doubled to 12mo, advanced packaging/test >18mo, RF power to 24mo; ASML raised 2026–27 capacity plans; KLA guides 2H26 ~+20% over 1H, Sep-q $4.0bn |
| Inventory days | **flat/falling** — no correction signal; allocation conditions persist |
| Margin regime | **PEAKING** |

## HBM tracker cross-check (mandatory)
Read `/Users/yb/Claude/HBMTracker/consumer_view.json`. **C1** (phantom −51% HBM3E) and **C2** (HBM4
"+14.29%" basis-splice artifact) both checked; **neither figure is cited here**. Within-basis truth:
HBM3 and HBM3E FLAT at $9.00/GB stack-derived, 2026-07-19 → 2026-08-05 (0.0%); defensible HBM4 is
~$10.42/GB ($500/48GB), ~25%/GB generational premium over HBM3E. G5 stands: no contract-basis HBM
$/GB newer than 2026-01-15, so all HBM contract direction above is percentage guidance, not a level.

## Falsifier — check this next run
**If TrendForce's 4Q26 conventional-DRAM contract forecast comes in at or above the 3Q26 +13–18% QoQ
pace (i.e. the sequential rate stops decelerating), AND NVDA's Q3 print does not confirm the guided
74% gross margin step-down, then the second-derivative and margin-peak legs both fail and this call
moves back to `mid`.** Conversely, a single hyperscaler capex guidance CUT, or rising channel
inventory days, moves it to `rolling`.

## Discipline notes
Book P&L was NOT used as cycle evidence. The −8.95% drawdown and 89.4% AI-capex concentration are
context for who is exposed, never proof of where the cycle is. No trade recommendation is made here.
