# smith-cycle — AI-capex cycle position — 2026-09-06 (DEEP, monthly)
**POSITION: `late` — confidence MEDIUM. Unchanged from 2026-08-31.**
Prior falsifier tested, NOT triggered: leg one needed 4Q26 conventional-DRAM contract at or
above the 3Q26 +13–18% QoQ pace; TrendForce's 4Q26 PC DRAM forecast is **+3–8% QoQ** — it
decelerated again. Leg two (NVDA Q3 GM step-down to ~74%) untested; NVDA has not printed.
One leg failed to falsify, one pending. Call stands, not upgraded.
## 1. The second derivative (the whole case)
Conventional DRAM contract QoQ: 1Q26 +90–95% → 2Q26 +58–63% → 3Q26 +13–18% → 4Q26F
**+3–8%**. Four quarters, monotonic deceleration. NAND: 3Q26 +10–15% → 4Q26 "converge
further". Prices still RISING, at record highs — textbook `late`: the level looks
excellent, the rate does not. TrendForce's stated 4Q26 cause is *weak end demand and
elevated inventory levels* — the inventory leg, sourced rather than inferred.
## 2. Hyperscaler capex revisions — the strongest evidence AGAINST me
August round: AMZN ~$200B → **~$220B**; GOOGL $180–190B → **$195–205B**; META floor
$125–145B → **$130–145B**. Revision direction = **RAISED**, 2027 flagged higher (street
~$1T+); MSFT/META declined to guide 2027. This is an accelerating-side reading and is why
confidence is medium, not high. The case: the *funding* side is still being raised while
the *pricing* side has stopped accelerating — that gap is what late looks like from inside.
## 3. Semicap
SEMI billings 1Q26 $36.55B, **+14% YoY but only +1% QoQ** — record level, flat sequential.
SEMI discontinued book-to-bill in 2017; `semicap_book_to_bill` is null by availability,
not omission. No ASML/LRCX/AMAT/TER digestion commentary this period.
## 4. Memory pricing — basis discipline
HBM tracker snapshot generated **2026-08-05; 32 days stale** — the tracker's own rule says
degrade past ~30 days. Applied.
- **C1 checked**: the −51% HBM3E decline splices contract_quote onto stack_derived.
  Within-basis HBM3E is **FLAT at $9.00/GB** (07-19 → 08-05); C1's corrected view is that
  HBM3E *contract* prices are RISING (~20% 2026 supplier hike).
- **C2 checked**: HBM4's "+14.29%" is a **basis-splice artifact** (source-spread widening,
  not an observed move) — not published here as a price signal. Defensible ~$10.42/GB
  ($500/48GB), ~25%/GB generational premium over HBM3E.
- **Weighted CONTRACT, not spot.** Server DRAM/HBM clear on contract; the spot proxies are
  32 days old and Huaqiangbei spot is a consumer-channel read that does not price AI-server
  demand. Contract: **up, decelerating**. Spot: null.
## 5. Friday 2026-09-04 — needle or noise?
**Noise on top of an unchanged series — but it moves the priced-in half.** SNDK +11.9%,
SKHY +8.1%, KLAC +7.3%, MU +6.1%, DRAM ETF +6.6%, SMH +2.61% vs SPX −0.38% and a 10-yr
that ROSE to 4.784%. Proximate causes are sell-side: a BofA upgrade and a broad UBS note,
plus Dell's $95B AI-server backlog and reports MU is sold out of leading-edge allocation
through end-2026. No pricing, capex or inventory series moved on Friday. A one-session
decoupling on broker re-rating is not demand confirmation; it is multiple.
## 6. The pricing half — is it in the price?
**Bifurcated.** The infra/semicap layer pays MORE per unit of capex growth than 3m ago —
KLAC, LRCX, AMAT, TER all re-rated hard into a decelerating pricing series. Memory pays
LESS: MU at ~6x forward with ~$18B customer prepayments and ~$100B contracted minimum
revenue is not a multiple capitalizing peak EPS. Multiple expansion on decelerating
growth is the `late` signature — present in semicap, absent in memory.
## 7. Expectations behaviour (the mid→late marker)
The market has stopped paying for good prints. AVGO 09-02 beat, guide inline-vs-consensus
below whisper; KLAC beat EPS +5.1% and fell ~9.6%; MRVL guided ~4% above and fell; COHR
beat-and-raised and fell. Four for four. Reaction is not a verdict (smith-earnings, G75) —
the *pattern* of reactions is, and it is late-cycle.
## 8. Falsifier for next month (checkable)
→ **`mid`** if BOTH: TrendForce's 1Q27 conventional-DRAM contract forecast lands at or
above 4Q26's +3–8% QoQ (deceleration stops), AND a hyperscaler raises 2027 capex guidance
at the Oct/Nov round.
→ **`rolling`** on EITHER a hyperscaler capex CUT / order pushout, OR a negative QoQ
conventional-DRAM contract print.
→ **`accelerating`** only on re-acceleration in the QoQ contract series; a record level at
a slower rate does not qualify and will not be counted as one.
## Data quality
- HBM tracker snapshot 32 days stale (gen 2026-08-05) — confidence degraded accordingly.
- `semicap_book_to_bill` null: SEMI discontinued the ratio in 2017, not retrievable.
- 4Q26 DRAM figure is PC DRAM; no server-DRAM-specific 4Q26 number sourced — cleaner
  sequential read, but not the AI-exposed segment.
- No 3Q26 channel inventory-days figure; the inventory leg rests on TrendForce's
  qualitative "elevated inventory levels", weaker than a number.
