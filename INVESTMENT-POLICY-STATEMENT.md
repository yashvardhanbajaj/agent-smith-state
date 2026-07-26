# Investment Policy Statement — Agent Smith (US Portfolio)

The mandate. Everything else in this system — drift bands, the drawdown ladder,
proposals, the eventual decision queue — exists to serve this. Change this document
deliberately and rarely; change policy.json's tactical values often as the book
evolves within it.

Confirmed by user: 2026-07-26.

---

## 1. Objective

**Aggressive, high-conviction, single-factor bet on AI infrastructure/capex
build-out.** This is not a diversified core holding — the concentration is the
strategy, not an accident to be corrected. Volatility is the price of admission,
not a problem to manage away.

**Success metric: beat SOX/SMH on total return over the horizon.** SMH is the
liquid, zero-effort alternative to this entire thesis — anyone can buy it in one
click. The only reason to run a concentrated, actively-managed version of the same
bet is if it outperforms the passive version by enough to justify the extra risk
and attention. If it doesn't beat SMH, the concentration isn't earning its keep and
the mandate itself should be questioned, not just the individual positions.

This requires a shadow-book comparison (book value vs. SMH-equivalent, same cash
flows) tracked over time — not yet built, see ARCHITECTURE.md known gaps.

## 2. Horizon

**2–5 years**, not indefinite.

**Named tension**: a full AI-capex cycle correction has historically taken 18–36
months to recover (semis cycles: 2000-03, 2007-09, 2018, 2022). A 2–5yr horizon
carries real risk of needing to draw down mid-trough rather than after recovery —
this is not a hypothetical, it is the single biggest risk this mandate carries
given a 100% single-factor book.

**Mitigation — horizon-aware glide-down**: absent an explicit renewal of this
mandate, tighten the risk posture as the window narrows:
- **Now → year 3**: current posture (100% AI-capex ceiling, drawdown ladder as-is).
- **Year 3 → year 4**: begin raising the minimum cash floor from 3% toward 15-20%,
  independent of any drawdown trigger — a scheduled de-risk, not a reactive one.
- **Year 4 → year 5**: AI-capex ceiling steps down from 100% to ~70% of invested
  equity; the freed allocation goes to cash or the diversifier bench, not
  necessarily new AI names.
- **At year 5**: full liquidity review. Renew the mandate explicitly (reconfirm
  2-5yr aggressive posture) or convert remaining exposure to the long-term core
  holding profile below.

This is a plan to build, not yet implemented — flag in ARCHITECTURE.md until it's
wired into policy.json as dated glide-path triggers.

## 3. Risk budget

**Maximum tolerable peak-to-trough loss on total book: 25%.**

This *validates* — rather than merely carries forward — the `drawdown_risk_off_pct:
25` already in policy.json. It was previously an unexamined default ("no drawdown
history exists yet"); it is now a deliberate ceiling matched to what the user can
sustain without a change in behavior (panic-selling, disengagement, loss of sleep).

The existing drawdown_trim_ladder (warn -15% / batch-1 -18% / batch-2 -22% /
risk-off -25%) sits entirely underneath this ceiling as pre-committed intermediate
responses — the point of the ladder is that the book never has to discover the 25%
line by hitting it. All rungs measured on **total book** (equity+cash), not equity
alone (see CHANGELOG 2026-07-26 for the equity-only bug this correction fixed).

If a real -25% drawdown occurs and the response is anything other than what the
ladder already specifies, that is itself a signal the risk budget needs
re-examination — not a reason to quietly override the ladder in the moment.

## 4. Liquidity

**No external liquidity floor.** All cash held in this book is tactical dry powder
for the drawdown ladder and rebalancing discipline — not a reserve protecting a
real-world need (no emergency fund function, no known near-term expense funded from
here). The `cash_band_pct: [3,15]` in policy.json is a rebalancing-discipline band,
not a liquidity requirement, and can be breached toward 0% without violating this
mandate (though a sustained 0% cash position removes all ladder capacity and should
itself be flagged).

The 07-24 event (cash 0.06%→45.8% in one session) was a large deviation from the
tactical band but not a mandate violation — no external liquidity need was at risk
either way. The problem with that event was the *absence of a captured rationale*
(G26), not the cash level itself.

## 5. What this mandate does NOT cover

- **Tax treatment**: LTCG/STCG sequencing is a separate, subordinate concern
  (`smith-tax`, blocked on `lots.json`). Tax efficiency should inform *which* lots
  to trim when a ladder rung fires, never *whether* to trim.
- **Individual-name conviction**: this mandate sets the book-level posture. Per-name
  thesis calls (intact/strengthening/broken/watch) remain `smith-thesis`'s job,
  operating inside these bounds.
- **Execution**: nothing here authorizes Agent Smith to place a trade. Every ladder
  rung and every proposal remains a recommendation for the user's review.

## 6. Review cadence

This document is reviewed and re-confirmed:
- **Annually**, or
- **On any horizon-glide transition** (year 3, year 4, year 5 above), or
- **On user request** ("revisit the mandate"), or
- **If a -25% risk-off event actually fires** — the response should already be
  known from §3, but the event itself is a natural checkpoint to ask whether the
  mandate as a whole still holds.

It is explicitly **not** renegotiated in the middle of a drawdown in reaction to
that drawdown — that is the exact failure mode (07-24) this mandate exists to
prevent.

---

## Cross-references

- `policy.json` — tactical values (cluster targets, caps, bands, ladder) that
  operate *within* this mandate.
- `POLICY-DECISIONS.md` — why the tactical values are what they are.
- `ARCHITECTURE.md` — what's built vs. what this mandate still needs (shadow-book
  benchmark, decision queue, glide-path automation).
- `CHANGELOG.md` — dated history.
