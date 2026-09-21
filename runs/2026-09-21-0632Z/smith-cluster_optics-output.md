# smith-cluster — AI Networking/Optics — 2026-09-21 (deep, pre-open)

## The axis that decides this cluster
Position in the stack. Every member rides the same 800G→1.6T tailwind; what separates them is
whether they own the component that is *binding* (200G/lane EML lasers), the component that is
*attached* (scale-up silicon, custom-ASIC content), or the component that is *passive* (fiber,
glass, connectors). Rank order below is stack position, not one-month price.

## Differentiator reads (dated, sourced)
- **200G/lane EML supply.** LITE is the only supplier shipping 200G-per-lane EMLs at volume;
  1.6T DR4 OSFP demonstrated on four Lumentum 400G differential EMLs (OFC 2026, Mar-2026).
  COHR ships 200G EMLs for 800G/1.6T and demoed a 400G differential EML for 3.2T/6.4T at the
  same show — second source, not sole source. Source: investor.lumentum.com OFC-2026 release;
  chipstrat "Coherent's Vertical Integration Strategy".
- **1.6T ramp timing.** COHR management (Aug-2026): 1.6T ramp "even faster than expected three
  months ago". LITE first 1.6T modules shipping. Both are qualified TODAY — this axis no longer
  separates them; the EML axis does.
- **CPO threat.** Co-packaged optics disintermediates *module assembly*, not laser supply — a CPO
  switch still needs an external laser source. LITE/COHR are on the right side of that; pure
  module assemblers (FN, Innolight) are not. This is why FN is explicitly NOT on my bench.
- **NVDA supply lock-up.** NVDA announced strategic partnerships/investments in both LITE and
  COHR to expand laser/photonics supply (reported $2bn each; secondary sourcing, treat magnitude
  as unverified, direction as verified). Confirms lasers are the binding constraint.
- **Scale-up vs scale-out.** ALAB is scale-up/within-rack (retimers, Scorpio switching) with
  custom-ASIC attach; APH is scale-up copper/connector; MRVL is custom-ASIC + optical DSP,
  i.e. scale-out silicon facing merchant-share loss to AVGO; CIEN is scale-across/DCI systems;
  GLW is passive fiber + glass with no active-component content.

## Ladder vs price
Price says LITE>COHR>ALAB>MRVL>APH>GLW>CIEN. I say LITE>COHR>ALAB>MRVL>APH>CIEN>GLW.
The agreement in ranks 1-5 is NOT momentum-following: the price order happens to reproduce
stack position (laser supply > scale-up silicon > custom ASIC > connector > materials), which is
the axis I would have ranked on with no price at all. The one disagreement — CIEN above GLW —
is where price is wrong: CIEN printed FQ3 EPS $2.11 vs $1.73 consensus with a guide above
consensus on 2026-09-03 and is still -12.68% on the month, while GLW carries a live $2bn ATM
dilution overhang and a `watch` thesis. A beat-and-raise ranked last is a price artifact.

## Fundamental prints on file
- CIEN FQ3 2026 (09-03): rev $1.67bn vs $1.64bn, EPS $2.11 vs $1.73, guide above. **beat**
- ALAB Q2 2026 (08-05): rev $392.4M vs $360.8M, EPS $0.80 vs $0.69, guide $540-560M vs $417M
  consensus — a guide ~30% above the street, the strongest forward statement in the cluster.
- LITE Q4 FY26 (08-11): rev $1.01bn vs $987.7M, EPS $3.23 vs $2.97, guide >$1.25bn, >39% op mgn.
- COHR Q4 FY26 (08-12): rev $2.045bn vs $2.025bn, EPS $1.74 vs $1.65, FY27 outlook raised —
  and the stock fell anyway.
- MRVL Q2 FY26 (08-27): EPS $0.94 vs $0.930 — a 1.05% avg-surprise name; thinnest beat here.

## Margin-pool migration
Toward **laser/EML supply (InP epitaxy and 200G/lane device)** and away from **pluggable module
assembly and passive optical materials**. Mechanism: CPO removes module-assembly value-add while
preserving (and concentrating) external-laser demand; NVDA is investing directly into laser
capacity rather than module capacity; the constraint quoted across 2026 is laser lead time, not
module capacity. Practical consequence: a laser lead-time datapoint reads through to module
makers' *gross margin*, not their revenue — watch COHR/LITE mix, not their top line.

## Redundancy verdicts (27-position book, 15-20 target: 7 optics line items → 4-5)
- **LITE / COHR — REDUNDANT.** Same binding component (200G/lane EML), same 1.6T sockets, same
  NVDA relationship, same 2026-09-14 ATM contagion (-9%/-11% together), same Friday rebound
  (+3%/+5%). Keep **LITE** (sole-source at the binding node, purer AI torque); COHR's industrial
  laser / telecom half dilutes exactly the exposure the book is paying for. Drop COHR.
- **MRVL / ALAB — DISTINCT.** Both ride custom-ASIC attach at the same hyperscalers, but MRVL is
  the accelerator/DSP silicon and ALAB the scale-up connectivity layer — different content per
  rack, different competitors (AVGO vs Broadcom/Nvidia-native). Two bets, not one.
- **LITE / GLW — DISTINCT as bets, but GLW is not worth a full position.** Active laser vs passive
  fiber are different economics; GLW simply sits where margin is leaving. Fold on conviction,
  not on overlap.
- **APH — full position, but the lowest AI torque per dollar here.** Largest weight (4.61%),
  lowest ATR (3.27%), and its AI content is diluted by a large auto/industrial/mobile base.
  It is the cluster's ballast, and should be sized as ballast rather than as an AI expression.
- **CIEN — not a position.** $2.98 / 0.009% weight. Same pathology as the open TER dust flag:
  either re-establish it as a real position on its beat-and-raise, or zero it. Holding $2.98 is
  neither exposure nor discipline.

## Bench (non-held)
- **CRDO $175.89** — beats APH on the same scale-up axis with far more torque per dollar
  (AEC/copper interconnect is ~all AI datacenter vs APH's diluted base). Entry on a pullback to
  the low-$150s or on a disclosed hyperscaler AEC design-win.
- **AVGO $357.61** — beats MRVL on the exact axis MRVL loses: merchant switch silicon share
  (Tomahawk) plus the larger custom-ASIC book. Was exited 09-16 by round-lot sizing, not by
  thesis. Entry on a re-test of $330 or a confirmed third custom-ASIC customer.
- **ANET $199.39** — systems-level 1.6T beneficiary, better than GLW as an optics expression.
  Entry only on evidence in-house hyperscaler switching is NOT displacing merchant systems.
- **FN $388.55 — deliberately NOT benched.** Module assembly is the pool CPO drains. Naming it
  here so the omission is a judgement, not an oversight.

## Confidence
`medium`. Return coverage is complete (7/7). Ranks 1-2 and the margin-pool call are evidenced on
dated, named sources. Ranks 3-5 rest on prints and stack position rather than a fresh 1.6T
qualification datapoint per name, and the NVDA $2bn-each magnitude is secondary-sourced.
