# Agent Smith — Architecture Reference

Durable description of how the system is built and what runs where. For file-level
memory contents see [README.md](README.md); for dated decisions and fixes see
[CHANGELOG.md](CHANGELOG.md); for policy rationale see [POLICY-DECISIONS.md](POLICY-DECISIONS.md).

## Orchestration

**Skill**: `/Users/yb/.claude/skills/agent-smith/SKILL.md` — the orchestrator. Runs
QUICK (default) or DEEP mode. Compute-first: all deterministic arithmetic (currency
conversion, weights, concentration, drawdown, journal scoring, drift-vs-policy,
sentiment) goes through `scripts/smith_math.py`, never through an LLM sub-agent.

Flow: LOCK → intraday-refresher check → MEMORY load → market inputs (one batched
fetch) → holiday/session check → PREFETCH+COMPUTE (one holdings snapshot, script runs
every subcommand) → STAGE 1 (parallel analyst dispatch) → STAGE 2 (strategist) →
SYNTHESIZE (briefing) → dashboard artifact → PERSIST → milestone JSON.

## Compute layer

`scripts/smith_math.py` — stdlib-only Python, five subcommands:
- `book` — value/weights/concentration/beta/drawdown/cash/LTCG-flags/qty_changes
- `journal` — signal scoring at 7d/30d horizons, bucket hit-rates
- `attribution` — FX/flow/residual decomposition, rolling windows
- `drift` — policy validation + cluster/position/cash/AI-capex breach checks, drawdown ladder
- `sentiment` — Fear/Greed-style composite from market inputs
- `validate` — structural policy.json + cache-staleness checks (no run needed)
- `proposals` — lifecycle rules (auto-supersede/expire/void) on proposals.json

Sub-agents receive the script's output inline and reason from it — they never
re-derive arithmetic the script already computed. This is a hard guardrail: an agent
that estimates a number instead of getting it from the script or a tool is a defect,
not a shortcut (see CHANGELOG 2026-07-26 beta-guessing revert for what happens when
this is violated).

## Sub-agent fleet

| Agent | Roster | Scope |
|---|---|---|
| `smith-book` | deep only | Dividends, ex-dates, LTCG narrative, beta refresh — script owns the arithmetic |
| `smith-signals` | quick+deep | News/signal buckets, peer-relative strength, journal judgment |
| `smith-thesis` | quick+deep | Per-holding thesis (intact/strengthening/broken/watch), factor overlap, sector map. Reconciles Memory-cluster thesis against HBMTracker pricing data when Memory names are held (Tier 2.1) |
| `smith-watchlist` | quick+deep | Entry setups, earnings-calendar cache, attribution-driven scan |
| `smith-scout` | deep only | Sentiment narrative, pre-market/international session read, diversifier bench |
| `smith-macro` | deep only | Fed/FOMC stance, options PCR/max-pain, macro calendar |
| `smith-quality` | monthly/on-demand | Credit-officer's lens: PAT-vs-OCF, dilution, leverage, going-concern |
| `smith-rebound` | conditional (gate=ESCALATING/AMBIGUOUS) | Rapid redeployment triage on a hot/bleeding pre-market |
| `smith-strategist` | every run (Stage 2) | Sized proposals, stress table, risk-off checks, hit-rate readout |
| `smith-cycle` | skeleton, not yet wired | AI capex cycle position (accelerating/mid/late/rolling) — needs hyperscaler capex + SEMI b2b data sources |
| `smith-earnings` | skeleton, not yet wired | Earnings calendar, option-implied move, historical surprise rate — needs FMP/options-chain wiring |
| `smith-tax` | skeleton, blocked on lots.json | LTCG lot sequencing, wash-sale alerts, harvest windows |

Dispatch discipline: every prompt embeds slices only (holdings rows, compute_*.json,
prior JSON tail, trimmed known_gaps) — never a pointer to whole state files an agent
must re-read. Tail validation on every return; malformed JSON gets one re-emit retry
before falling back to a degraded, flagged section.

## State model

`/Users/yb/Claude/AgentSmith/` is the memory of record (git-snapshotted after every
run). Working rule: **state.json is working memory, not an archive** — anything a
future run won't act on moves to a dedicated `*-archive.json` file instead of being
carried forever. Current archives: `proposals-archive.json` (terminal-status
proposals), `known-gaps-archive.json` (resolved gaps), `exited-holdings-archive.json`
(thesis/sector_map for positions no longer held), `journal-archive.json` (scored
entries >12mo).

## Known architectural gaps (not yet built)

- **No investment mandate**: policy.json is an allocation grid (targets/bands/caps),
  not an IPS — no return target, risk budget, horizon, or liquidity floor is stated
  anywhere. Drift is measured against a default band, not a chosen objective.
- **No decision-first briefing**: 14 sections reported at equal weight every run. A
  breach restated 6 times in a row (07-16 through 07-23 cash-floor breach) with no
  escalation is a symptom of this — there is no `decisions.json` queue and no breach
  aging.
- **No shadow-book accountability**: journal.json scores signals, proposals.json
  scores proposals, but nothing marks "would following Smith have beaten just
  holding SMH" — the one number that would justify trusting it in the next drawdown.
- **No event-driven wake**: the daily cron is the only trigger; a gap-risk or
  drawdown-rung crossing intraday gets no response until the next scheduled run.
