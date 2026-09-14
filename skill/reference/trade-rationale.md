# Trade rationale capture

> Moved verbatim out of SKILL.md on 2026-09-14 (core cut to <=60KB). Load this file only when the core step that cites it runs. Where this text and the core disagree, the core wins — it reflects the scripted flow (`preflight`, `smith_fetch.py`, `dispatch-plan`, `postflight`).

### 2.9. TRADE RATIONALE CAPTURE (added 2026-07-29, interactive sessions only)

**Facts vs motive.** Fills (qty, price, order type, timestamp) are recorded ONLY by the LEDGER pipeline (§3b) — trades.json has one writer for facts, and `stops` quarantines any `price_source: reconstructed` row (DECISIONS.md#G64). This step only attaches the *reason*.

trades.json's own header has always said rationale gets "populated by interactive runs asking 'why'" — this step is that ask, made concrete. The *reason* still comes from the user (or from an objective `Order Type: stop`); `smith-ledger` supplies the *facts* it attaches to.

**Trigger:** every trade `ledger-apply` recorded this run whose `reason` is still `UNCAPTURED`. **Do not gate this on `likely_corporate_action`** — that heuristic (ratio near a clean integer) false-positives on ordinary same-size adds (two separate +2-share buys were flagged `true` on 2026-07-29 and would have been silently skipped). A genuine split is rare enough, and the question is cheap enough, that asking and letting the user answer "Other: stock split" costs less than a silently mis-skipped real trade.

**Scheduled/non-interactive runs:** never ask. `ledger-apply` already recorded each fill as `UNCAPTURED` (or `stop-loss` when the confirmation's order type is `stop`); put the count awaiting rationale in data_quality.

**Interactive runs**: before finalizing the briefing, capture rationale per ticker in TWO STEPS, not one — AskUserQuestion hard-caps at 4 custom options per question (5th slot is always a fixed free-text "Other", not a labeled button you control), so 7 standing named reasons plus a true catch-all cannot fit in a single question. Added 2026-07-29 after DCA went 5-for-5 via "Other" on its first day and the user asked for it as a real button, not typed text, without dropping any of the original 4; extended the same day to be direction-aware after the user pointed out buys and sells have different most-likely reasons. Extended again 2026-08-03: `re-entry-after-stop` and `dca-into-diversification` promoted to standing buttons after both recurred multiple times via "Other" (a same-day MU stop-loss/rebuy whipsaw pair, and a five-ticker weekend diversification buy confirmed by the user as "DCA into diversification") — this pushed the buy side from 1 relevant reason to 3, so buy-side step 1 changed shape (see below) to keep every question within the 4-custom-option cap.

The 7 standing reasons are `dollar-cost-averaging`, `dca-into-diversification`, `re-entry-after-stop`, `stop-loss`, `thesis-change`, `raise-cash`, `rebalance`. **Step 1's question depends on the sign of the ticker's `qty_diff`** (not the `action` label — `qty_diff` is unambiguous, `action` strings like "add" vs "entry" have drifted inconsistently across trades.json's history):

- **`qty_diff > 0` (a buy/add)** → step 1 is a 4-option question, *"What kind of buy was this?"*: `DCA` / `DCA into diversification` / `Re-entry after a stop` / `Something else`. Picking one of the first three writes that reason straight to `reason`, one click, done — skip step 2. Picking "Something else" (or the tool's own free-text Other, if used directly at step 1) proceeds as below.
- **`qty_diff < 0` (a sell/trim/exit)** → step 1 stays a yes/no: *"Was this a stop-loss?"* (`Yes — stop-loss` / `No — something else`). "Yes" writes `stop-loss` straight to `reason`, one click, done.

If step 1 didn't resolve it (a sell's "No", or a buy's "Something else"): **step 2 shows the remaining 4 reasons** — whichever ones step 1 already tested are dropped, so this is always exactly 4 options, never a separate filtering decision:

| Label | Description shown to the user | Shown in step 2 for |
|---|---|---|
| Dollar-cost-averaging | Buying on a schedule/discipline, not reacting to a specific signal | sells only (buys resolve this in step 1) |
| Stop-loss | Hit the stop / sized down under the tight stop discipline this book runs on | buys only (sells resolve this in step 1) |
| Thesis-change | Your view on the company or story itself changed | both |
| Raise-cash | Trimmed specifically to build dry powder, not a stop or a thesis call | both |
| Rebalance | Sizing move — staged deployment, bringing a position/cluster back toward target | both |

(`dca-into-diversification` and `re-entry-after-stop` never appear in step 2 — they're buy-only and already offered directly in buy-side step 1.)

The tool adds a free-text "Other" automatically on every question — if picked, store the user's own words as `reason` verbatim (don't force it into one of the 7 buckets) and put any elaboration in `notes`. For a bucketed answer (from either step), write the matching enum value straight to `reason` and put ticker/qty/direction context in `notes`.

Write each answer with `python3 scripts/smith_math.py trade-rationale --base-dir . --ticker <T> --date <YYYY-MM-DD> [--side buy|sell] --reason <reason> [--notes "..."]` before Stage 1, so the strategist sees it this run. Never edit trades.json by hand.

### 2.9b. LOTS.JSON BACKFILL — one-time done, now a standing rule (added 2026-07-31, closes most of G1)
lots.json is rebuilt deterministically from trades.json by `lots` (the `pipeline` stage, run after `ledger-apply`) — never append or FIFO-consume lots by hand. A lot with no traceable fill carries `date: null`, never a fabricated date. Backfill history: DECISIONS.md#G1.

