# Agent Smith — Architecture Audit & Roadmap
**2026-07-26 · post-mortem grounded in the 07-24/07-25 cash-position failure**

Every finding below is evidenced by something that actually happened in this book's history, not
hypothesised. Ordered by expected value, not by effort.

---

## TIER 1 — Demonstrated failures. Fix these first.

### 1.1 The daily run fires in the dead zone and can never see a completed US session
**Evidence.** `agent-smith-daily-us` cron is `30 14 * * *` = **14:30 IST = 05:00 ET**. The US session
runs 09:30–16:00 ET. So every daily quick sweep executes 4.5 hours *before* the open and 13 hours
*after* the previous close — it is structurally incapable of observing a finished trading day as
"today". The 2026-07-24 run at 18:29 IST (08:59 ET, 31 min pre-open) missed that entire session: five
full exits, eight halvings, $12.5k of cash creation, and a -5.06% book move. The bad `$5,656.86` cash
figure survived into a full written analysis and was only caught because the user said "cash is more
than 10k".

The PRE-MARKET PRICE OVERLAY (SKILL.md §2.5) was built to patch this, but it only corrects *prices*.
It cannot recover the session's flows, closes, or events.

**Note the weekly run is fine**: `0 8 * * 1` = 08:00 IST Mon = **22:30 ET Sun**, which sees Friday's
complete close. The defect is specific to the daily job.

**Fix.**
- Move the daily quick sweep to **~07:30 IST** (= ~22:00 ET previous day). It then reports the last
  *completed* US session, with all flows visible.
- Optionally keep a 14:30 IST slot as an explicitly-labelled **pre-market prep** run that writes no
  ledger row and never overwrites `us.value_usd`.
- Add a mandatory `session_coverage` field to every run: `{"covers_session":"2026-07-24",
  "session_status":"complete|in_progress|not_yet_opened","ran_at_et":"05:00"}`. Any briefing whose
  coverage is not `complete` must say so in the header. This makes the class of error self-announcing.
- The cron is `* * *` (7 days). It fires on weekends; the skill handles it via `market_closed_run`, but
  `1-5` plus a holiday check would be cheaper.

### 1.2 No trade-rationale capture — the agent cannot see *why* the book changed
**Evidence.** G23, G24, G26 are three separate write-ups of the same hole. The two largest
reallocations in the book's history (07-24 wave 1: LITE/META/GOOG/BABA/STM exits; wave 2:
GLW/NBIS/IREN exits + 8 halvings) were reconstructed only by cash-balance arithmetic. No trigger, no
intent, no record. Consequence: the 07-24 strategist proposed *deploying* into GEV and COHR on the
same day the user was liquidating — because it had no idea a de-risking event was underway.

**Fix.** Add `trades.json` and a **flow interrogation** step after `qty_changes` is computed:
interactive runs ask one question ("GLW exited — stop-loss, thesis change, or raising cash?");
scheduled runs write `{"reason":"UNCAPTURED"}` and flag it. Within weeks this yields the first real
model of the user's actual sell behaviour, which is the prerequisite for any sell-discipline work
(§2.3) and for scoring proposals against what the user genuinely does.

### 1.3 `qty_changes` is blind to full exits and new entries
**Evidence.** G25, already logged, never fixed: `smith_math.py book` only diffs tickers present in
*both* prior and current holdings. Every full exit and every new position is therefore invisible to
`est_net_flows_usd` — which is exactly why the 07-24 flow event had to be inferred from the wallet.
This is a ~15-line fix in the one place that would have caught the whole incident.

### 1.4 Portfolio beta is measured against the wrong factor and is partly fabricated
**Evidence.** Stated beta 1.491 (vs SPX) predicted **+0.075%** for Friday. Actual: **-5.06%**.
Unexplained: 5.13pt. The book's real driver is SOX (implied beta from that session: **1.19**).
Separately, 4 of 21 names — including **SNDK, the largest position** — carry a hardcoded default
`beta = 1.0` because no cache entry exists. Every stress-table row that multiplies by beta is wrong.

**Fix.** Compute and store a small factor set per name: β vs **SMH/SOX** (primary), β vs SPX
(secondary), and flag memory-subfactor names. Report the SOX beta as the headline. Source the 4
missing betas from a second provider or compute them from returns; never ship a fabricated 1.0 on the
top position.

### 1.5 The journal has never scored a single entry
**Evidence.** 47 entries since 2026-07-12. `bucket_hit_rates` and `name_bucket_grades` are **empty in
every run to date**. "Smith's record" has never produced a number, so the feedback loop that
justifies the whole signal apparatus has never closed. The earliest cohort crosses 30d around
2026-08-11 — verify the scoring path actually fires *before* then rather than discovering in August
that it is broken.

### 1.6 Proposals accumulate as stale duplicates
**Evidence.** 64 proposals, and before cleanup this session **17 were still "open"** — including the
*same* SNDK trim proposed four times at four prices (07-20 $1,354.82 / 07-22 $1,554.44 / 07-23
$1,605.38 / 07-24 $1,589.40), an ORCL exit proposed twice and then silently reversed by a later
"hold" verdict, and 07-18 items whose premise had evaporated. Nothing expires anything.

**Fix.** Lifecycle rules in `PERSIST`: auto-supersede when the same (action, ticker) recurs;
auto-expire after 5 trading days unspent; auto-void when the cited breach clears or the position
changes materially. A proposal list nobody can trust is worse than none.

### 1.7 Caches serve stale contents as fact
**Evidence.** On 07-20 `smith-macro` reported **"next FOMC 2026-09-16"**. The actual next FOMC was
**2026-07-28** — eight days out, under a brand-new Fed chair, with a live hike risk (9 of 18
participants penciling a 2026 hike). `fomc_cache` has a `next_check_date` but nothing validates the
*payload*, so a wrong date propagated into the regime read and into the "no events within 5 trading
days" all-clear.

**Fix.** Every cached record gets `{value, source_url, verified_at, confidence}`. Any cache whose
payload contains a **future-dated event** must be re-verified as that date approaches, not merely
when `next_check_date` lapses.

---

## TIER 2 — Analytical gaps. Highest value per unit of effort.

### 2.1 Cross-skill integration: Agent Smith never reads the HBM tracker
**The single best available upgrade, and the data already exists locally.** `/Users/yb/Claude/HBMTracker/`
holds exactly the inputs the memory thesis needs — DDR5 contract prices **+90-95% QoQ**, DDR5 margins
approaching **90%**, HBM3E $/GB **-51% from its H1-2025 peak**, TrendForce projecting 2027 HBM
contract prices **+80-150%** — plus a `thesis_tensions` block that *already* flags the contradiction
between Smith's "MU strengthening" call and falling HBM ASPs. Memory is **24.8% of the book**. The
integration is currently one-way: the tracker reads Smith's state; Smith has never read the tracker.

Reading it would have reframed Friday's selloff correctly on the spot: the market read SK Hynix's HBM4
delay as demand weakness, when the tracker's own data shows it is a margin-mix decision (DDR5 is more
profitable right now, HBM3E lines are being *extended* because demand is too strong to interrupt).

**Fix.** `smith-thesis` reads `HBMTracker/history.json` + `forecast.json` (read-only) whenever any
Memory-cluster name is held, and must reconcile or explicitly contest the tracker's `thesis_tensions`.

### 2.2 No cycle-position awareness — the conspicuous omission for a capex-cycle book
The book *is* a leveraged bet on AI capex, yet nothing in the agent tracks where the cycle stands.
MU at **6.0x forward P/E with PEG 0.15** and 55.9% margins is not "cheap" — it is the market pricing
in a cycle top, in a business that lost $5.8B in 2023. SNDK's forward EPS of **$212.95** against
$23.41 last quarter extrapolates an explosive ramp. The agent has no way to distinguish *"AI capex is
strong"* from *"AI capex is strong and fully priced"* — which is the only question that matters now
that concentration is affirmed as intentional.

**Fix — new sub-agent `smith-cycle`** (deep runs, or monthly): hyperscaler capex guidance and
direction (MSFT/GOOGL/AMZN/META quarterly capex + guide revisions), memory pricing via §2.1, semicap
book-to-bill, inventory days across the chain, and current margins versus trough/peak. Output: a
single `cycle_position` read — accelerating / mid / late / rolling — that the strategist must cite.
For a 100%-single-factor book this is more valuable than any existing sub-agent.

### 2.3 No sell discipline — and it is now the *primary* risk control
With AI-capex diversification deliberately abandoned (user decision, 2026-07-25), the only remaining
brakes are the single-position cap, the cash band, and the drawdown thresholds. Yet the book's actual
behaviour is discretionary de-risking in waves (07-22, 07-24), with no codified rule — so it cannot be
evaluated, improved, or anticipated. A pre-committed drawdown ladder (trim X% at -15%, Y% at -20%,
etc.), agreed in advance and checked every run, converts panic into policy.

### 2.4 Proposal sizing ignores volatility
Proposals are round dollars — $700, $900, $1,500 — with no reference to SOX's **61.4% annualised
volatility** (1-week 1σ = **8.5%**). A $700 trim in a name that routinely moves ±10% a week is noise
dressed as precision. Size tranches off ATR or realised vol so a "trim" is actually a risk reduction.

### 2.5 Benchmark mismatch makes every comparison misleading
The book is benchmarked to SPX/NDX. Its real benchmark is SOX/SMH. "Book -5.06% vs SPX +0.05%" reads
as catastrophe; "-5.06% vs SOX -4.25%" reads as roughly in line (-0.81pt). Both are true; only the
second is useful. **Fix:** SMH primary, SOX secondary, SPX/NDX as context only.

### 2.6 No factor attribution on book moves
`compute_attribution` decomposes FX / flow / residual, but never market vs sector vs idiosyncratic.
So "why did the book move" is unanswerable — the -5.06% could not be split into "sector beta" versus
"our specific names" without me doing it by hand this session.

### 2.7 Tax lots still absent since inception (G1)
`lots.json` has been empty for the book's entire life, so `prefer_ltcg: true` is decorative and no
trim proposal has ever carried real LTCG guidance. Either parse INDmoney order history if reachable,
or have the user seed it once — then a `smith-tax` helper can sequence trims by lot.

---

## TIER 3 — New capabilities worth building

| Proposal | Why |
|---|---|
| **`smith-cycle`** (see §2.2) | The missing analytical core for a capex-cycle book. Highest-value new agent. |
| **`smith-earnings`** | G20 shows the earnings calendar is repeatedly unavailable and dates get confirmed ad-hoc by web search. Three held names reported this week. Should own confirmed dates, option-implied expected move, per-name historical surprise + post-earnings drift, and a pre-earnings de-risk call. |
| **`smith-tax`** | Unblocked once §2.7 lands: lot selection, LTCG proximity, wash-sale awareness. |
| **Regime-conditional diversifier screening** | The 07-20 bench ranked DUK and SO as "clean" diversifiers on AI-capex overlap alone. Under a hiking Fed they are rate-sensitive and poor choices — a filter the bench does not model. Score candidates against the *current* macro regime, not just factor overlap. |
| **Dashboard: book-value history** | `ledger.csv` has 13 rows of value/cash/flow history that the dashboard never plots. A sparkline of book value + cash % over time would have made the 07-24 cash spike visually obvious. |

---

## TIER 4 — Hygiene

- `us_market_holidays` is an **empty list** despite SKILL.md claiming it is seeded at first run — so the
  holiday branch has never had data to test against. Seed it.
- `preferences` is empty and unused; either wire it up or drop it from the schema.
- `proposals.json` grows unbounded (64 rows). The journal has pruning rules; proposals do not.
- 4 names still on fabricated `beta = 1.0` (§1.4).
- Recurring INDmoney feed defects (G3, G22) are worked around every run but never structurally solved —
  worth a decision: accept yfinance as the price source of record and stop patching.

---

## Already fixed this session
- **G28** — policy cluster targets summed to 105% alongside a 3–15% cash band (arithmetically
  impossible; every drift table 07-12 → 07-25 was measured against an unsatisfiable spec). Also, the
  drift table silently mixed denominators: clusters/AI-capex equity-based, cash total-book-based.
  Now: original targets restored (30/20/20/15/10/5, sum 100) with the Diversified 5% carved to 0,
  denominators declared explicitly, and a **validator** (`smith_math.py validate`) wired into
  `cmd_drift` that emits `policy_valid` / `policy_defects` every run and checks target sums, band
  satisfiability, inverted bands, and undeclared denominators.
- **AI-capex cap raised 90 → 100%** and the 60% nag threshold removed, per the user's affirmed
  conviction. Cluster bands now govern *mix within* the chain rather than exposure to it.
- Stale proposal backlog reconciled (9 superseded + the 4 overtaken 07-24 items).
