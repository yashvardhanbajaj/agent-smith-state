# AI Memory/Storage — cluster ladder, 2026-09-20 (deep, wave 2)

## DELTA since 2026-09-19T08:56Z
The HBM tracker refreshed mid-run. Two brand-new tier-1 **contract_quote** points landed
(price_staleness_days=0), replacing the stack-derived proxies every prior memory verdict leaned on:
- HBM3E $12.40/GB [12.0–12.8] contract_quote, 2026-09-20
- HBM4  $16.00/GB contract_quote, 2026-09-20
Everything else in my inputs (CXMT risk production, Solidigm US fab, the unexplained 09-18 rally)
is a reaffirmation, not news.

## The one number that matters, and its caveat
HBM4 now prints a **~29% per-GB premium over HBM3E** ($16.00 vs $12.40) on the *same* basis, both
tier-1, both corroborated, same date. That is the first time the generational premium has been
observable without splicing bases — C2 had it at ~25% from stack arithmetic. It holds.

DISCREPANCY I will not paper over: hbm_build segments the 2026-09-20 HBM3E contract_quote into a
NEW segment, separate from the 2026-01-15 contract_quote ($15.00) because stack_derived points sit
between them. Both endpoints are the same basis, so a −17.3% Jan→Sep comparison is arithmetically
legal, and it points the opposite way to correction C1 ("HBM3E contract prices are RISING", from a
Dec-2025 TrendForce +20% hike expectation). I report the discrepancy rather than publish either
figure as the trend: the tracker's own segmentation refuses the delta, and C1's basis is a forecast,
not a print. Flagged to the tracker and to smith-cycle.

## Ranking — on the playbook's axes, not on rel_intra_pp
rel_intra_pp order is SKHY +12.08 / MU +0.41 / WDC −12.48. My ladder agrees on the order. That
agreement is only worth something because the axis says the same thing independently:

1. **SKHY (leader)** — HBM4 Vera Rubin allocation 60–70% vs Samsung 25–30%, Micron the residual
   (HBMTracker supply_structure, 2026-06-05). HBM4 is the generation now carrying a 29% ASP premium.
   The name with the most HBM4 capacity is the name that captures the most of the premium. That is
   an allocation fact, not a month of price.
   *Against:* 0.56% weight and an UNRECONCILED fill — this "leader" is a token the book may not even
   own. +20.07% in a month with KOSPI +2.66% on Friday alone. INDmoney 52wk_low=0 kills its signal
   buckets. And the same HBM4 qualification round is the first where all three vendors passed at
   ramp start — SK Hynix's HBM3E near-monopoly does NOT carry forward.
2. **MU (middle)** — HBM4 qualified but smallest allocation, so it captures least of the premium
   leg. What it does own that SKHY's ADR does not express cleanly: the conventional-DRAM crowd-out
   (HBM wafer input 18%→30% of DRAM by end-2027, TrendForce) plus enterprise SSD. Two axes, both
   evidenced, both second-order. Prints 2026-10-01 — 11 days.
   *For, against the rank:* $1,513 mean target on a $1,017.75 close (n=30) is the widest in the
   cluster; a clean FQ4 with HBM4 committed-capacity detail promotes it over SKHY immediately.
3. **WDC (laggard)** — and the reason is structural, not weakness. Post-SanDisk separation WDC is
   nearline HDD. It scores *zero* on four of the six differentiators: no HBM qualification at any
   generation, no HBM4 timing, no DRAM, no NAND. It cannot capture this cluster's tailwind because
   it is not exposed to it; it is exposed to a real but different one (nearline exabyte demand).
   *For:* thesis is `strengthening` on primary verification, and the −4.49% month is exactly what a
   non-HBM name does when HBM leads. Dead money in THIS cluster is not dead money in the book.

## Margin pool
Moving TOWARD HBM4-generation stacked DRAM and the vendors holding committed HBM4 wafer allocation.
Moving AWAY FROM HBM3E-generation supply and, on the tracker's own flat stack-derived series,
from anything priced off HBM3 ($9.00/GB, 0.0% trend 07-19→09-15). Commodity DRAM is the ambiguous
leg: crowd-out tightens it, CXMT's ~10% domestic share loosens it.

## The $2,430 question — answer: not here
Cluster is 10.52% of equity inside a 6–16% band, $3,257 room, no breach. It would *fit*. It should
not go here anyway, for three reasons that are not about capacity: desk cycle_position is `late`;
MU prints in 11 days and is the only liquid vehicle in the cluster, so adding now is buying an
earnings straddle at 4.28% ATR; and the leader on the axis (SKHY) is an unreconciled 0.56% line the
book cannot size into responsibly. If the user wants memory exposure added, the honest sequencing is
after 2026-10-01, sized on what MU discloses about HBM4 committed capacity.

## Redundancy
Script screen returned no pairs. I concur and go further: MU/WDC are the least redundant pair in the
book's memory sleeve — different products, different customers, different cycle. Consolidating them
would REDUCE exposure, not shorten the tail.

## Prior ladder (2026-09-09, medium, SKHY leader / WDC laggard)
Correct. SKHY +20.07% vs WDC −4.49% over the window. But it was right for a reason I can only now
evidence — the HBM4 premium was stack-derived guesswork on 09-09.
