# Agent Smith — Architecture Reference

A map of how the system is built and what runs where. For file-level memory contents see
[README.md](README.md). For dated decisions see [DECISIONS.md](DECISIONS.md), which
`scripts/gen_decisions_md.py` generates (never hand-edited). The investment mandate is
[INVESTMENT-POLICY-STATEMENT.md](INVESTMENT-POLICY-STATEMENT.md).

**Rewritten 2026-09-14** after the robustness and efficiency overhaul (phases 0–6). This file
records mechanisms, not thresholds or line counts. Those move and belong in SKILL.md,
DECISIONS.md or the code. `tests/unit/test_smith_fleet_contract.py` and `test_skill_budget.py`
enforce the parts of this file that most often drifted.

## Principle: scripts own everything deterministic

LLM sub-agents do judgment and outside research. Scripts do everything else:
- fetching market data
- arithmetic and indicators
- the dispatch roster, the materiality diff and session/gate classification
- locking and state persistence
- retention

An agent that estimates a number a script or tool did not hand it is a defect.

## Orchestration

**Skill:** `~/.claude/skills/agent-smith/SKILL.md`. The core is about 38KB with a 60KB budget
enforced by test. Rare branches live in `reference/*.md` and are loaded only when their step
runs. `skill/` in this repo mirrors the live config (`skill/sync-from-live.sh`), and `health`
reports mirror drift.

**Scheduled tasks** (`~/.claude/scheduled-tasks/`):
- `agent-smith-daily-us`: weekdays 14:30 IST, quick.
- `agent-smith-weekly-us`: Monday, deep.

The prompt of each carries no dispatch logic of its own; it defers to SKILL.md.

**Run sequence.** Every step is a script call, and the orchestrator's prose only connects them.

| step | command | what it owns |
|---|---|---|
| 0 | `preflight --mode` | acquires the run lock; runs `health`, `validate`, `freshness`, the correction-lesson titles and a ~5KB `memory` digest (replacing a ~1MB read); writes `health.json` |
| 1.7 | `sync-decisions` | drains dashboard clicks all-or-nothing; a failed sync blocks republishing |
| 2 | `smith_fetch.py all` | market data (below) |
| 2 | `build-holdings`, `session-gate` | holdings rows, `qty_changes`, market session, GATE v2 |
| 2 | `ledger-parse` / `ledger-apply` | fills from confirmation emails, **before** compute |
| 2 | `pipeline` | indicators → freshness → lots → book → universe → risk → drift → journal → attribution → rotation → buckets → sentiment → derisk → triggers → ladder |
| 2 | `bookcalc`, `taxcalc` | dividends, ex-dates, LTCG window, risk-weighted concentration; trim lot sequencing and harvest candidates (stages `tax_read`) |
| 2 | `dispatch-plan` | the waves, each agent's mode and reasons, skipped agents, and scripts to run first |
| 2 | `slices` | each agent's data embed |
| 3 | Wave 1 → `merge-tails` → re-slice → Wave 2 → `merge-tails` → `crosscheck` | staged, never written to state.json |
| 4 | `score` → strategist → `merge-tails` → `commit-state` → `add-proposal` → `proposals` | the only commit point |
| 7 | `postflight --phase commit` | journal merge, trigger journal, ledger row (script timestamp; refuses future stamps), daily/weekly report, DECISIONS.md |
| 6 | `smith_dashboard.py` → publish | payload build plus client app; republished only after a successful sync |
| 7 | `postflight --phase close` | `compact` (cheap every run, full on deep), prune `runs/` to 10 (kept in git history), git commit/push, lock release |

The alternate branches are the **refresher** (a same-day repeat, prices only) and the **priced
refresh** (pipeline plus strategist on live prices). `abort` is the failure exit: it discards
staged state, writes a report stub, declares an outage and releases the lock.

**Degraded paths** are a table in SKILL.md:
- INDmoney down → abort.
- yfinance down → fallback chain.
- Gmail down → ledger reported unreconciled.
- A failed agent → Wave 2 runs with that agent's tail marked missing.
- A failed script stage → its section is null with the real error.

## Data layer

`scripts/smith_fetch.py` is the only module that touches the network for market data. It runs
from the repo `.venv` (yfinance, pinned in `requirements.txt`), always exits 0 and writes
`fetch_report.json`. Its output files:

| file | contents |
|---|---|
| `market_inputs.json` | core macro strip, Asia block, the sentiment inputs |
| `live_quotes.json` | pre/post-market-aware quotes |
| `bars.json` | 1y daily bars for holdings, SMH and peer ETFs |
| `chain_SPY/QQQ.json` → `compute_options.json` | options, deep runs only |
| `earnings_calendar.json` | earnings dates, deep runs only; never overwrites a confirmed date |

The fallback chain is yfinance MCP → FMP MCP → the shared market cache labelled with its age.
`normalize-bars` converts MCP output so both paths feed one computation.

Holdings stay on the INDmoney connector, and trade confirmations on Gmail.

## Compute layer

`scripts/smith_math.py` is the single CLI (`--help` lists the subcommands). Its implementation
is split by domain:

| module | owns |
|---|---|
| `smith_core.py` | constants, `FRESHNESS`, `load_json`/`emit`/`fail`, crash-safe IO (`safe_write`, `atomic_write_json`, `atomic_append_line`, `file_lock`, `locked_json`) |
| `smith_clock.py` | one desk clock: UTC instants, IST desk date, America/New_York session date, UTC run labels `YYYY-MM-DD-HHMMZ`, `parse_any` |
| `smith_state.py` | the state transaction (`load_state` overlay, `stage_state`, `commit_state`) and the script-owned run lock |
| `smith_runlife.py` | `preflight`, `health` (+ `health.json` snapshot, `--notify`), `memory-summary`, `abort`, `lock`, `commit-state` |
| `smith_orchestrate.py` | `dispatch-plan`, `triggers-diff` (materiality gate), `postflight` |
| `smith_marketdata.py` | indicators (simple-mean ATR20, Wilder RSI14, 21-session relative strength, beta vs SMH needing ≥60 observations), `normalize-bars`, `session-gate` |
| `smith_risk.py` | risk primitives and the single readers for mixed-shape fields (thesis status, gap status, `data_entries`) |
| `smith_ledger.py` | FIFO lots, corporate actions, email ledger parse/apply, one LTCG rule (`ltcg_eligible_on`), `bookcalc`/`taxcalc`, `trade-rationale` |
| `smith_memory.py` | merge rules, `slices`, retention/`compact`, `gaps` search, `validate`, `evaluate_runs`, reports |
| `smith_lifecycle.py` | proposal lifecycle: `add-proposal` (IST date + `created_utc`), `score`, `stops`, `dismiss`, auto-retirement, priority |
| `smith_conviction.py` | the sizing engine for non-ATR triggers |
| `smith_learning.py` | the self-learning store (`learn-status`, lessons `L-###`, `usage-report`, the Phase-4 readiness counter) |
| `smith_dashboard.py` | payload plus client app; `REQUIRED_KEYS` fails the build on a missing panel key |

Standalone CLIs:
- `smith_valuation.py`: reverse-DCF, ROIC vs WACC, forensic scores.
- `smith_edgar.py`: SEC XBRL verification, Form 4.

`scripts/migrations/` holds the one-time, dry-run-by-default data migrations.

## Sub-agent fleet (12 files: 11 roles plus the cluster template)

`dispatch-plan` decides who runs. The thresholds live in `smith_orchestrate.py`, copied from the
desk's rules.

| agent | when | scope |
|---|---|---|
| `smith-signals` | every run, Wave 1 | judges script-computed buckets, news/insider signals, journal judgment; never writes indicators |
| `smith-watchlist` | deep, or on ask; Wave 1 | watchlist entry setups (the earnings calendar is script-owned) |
| `smith-scout` | deep (`full`), or quick `macro_only` on the MACRO trigger; Wave 1 | session read, sentiment narrative, Fed/FOMC stance and cache, options read, regime, diversifier bench |
| `smith-catalyst` | event-triggered or deep; Wave 1 | named, dated, sourced factor catalysts with magnitude |
| `smith-earnings` | a held name reporting within 5 trading days on a deep run, or VERIFY-ONLY (sonnet) on a stuck PENDING; Wave 1 | beat/miss, expected move, confirmations of the fetched calendar |
| `smith-quality` | monthly stagger, or on ask; Wave 1 | credit-officer lens and forensic scores |
| `smith-thesis` | THESIS triggers or deep; Wave 2 | per-holding thesis with `evidence_for`/`evidence_against`, factor overlap, sector map, HBM reconciliation |
| `smith-cycle` | monthly stagger, or on ask; Wave 2 | one cycle position with a falsifier |
| `smith-cluster` | deep, up to 3 clusters selected by `ladder`; Wave 2 | intra-cluster ranking rationale, margin pool, bench |
| `smith-rebound` | `correction_state` is correction or deep_correction | relief-rally candidates sized off support |
| `smith-ledger` | exceptions only | hard cases of the email ledger; routine parsing is script |
| `smith-strategist` | every run, Stage 2 | sized proposals, stress table, scorecard read, one harvest-vs-thesis sentence from `taxcalc` |

**Retired 2026-09-14,** archived in `archive/agents-retired-2026-09/`:
- `smith-book`: replaced by `bookcalc` and the indicators stage.
- `smith-macro`: folded into scout.
- `smith-tax`: replaced by `taxcalc` plus the strategist sentence.

Each agent writes `out_<key>.json`; when it only returns a tail, the orchestrator writes the tail
it returned. `merge-tails` ignores script-owned fields an agent tries to write.

## State model

`/Users/yb/Claude/AgentSmith/` is the memory of record. It is committed after every run and
pushed to the private `agent-smith-state` repo, and CI runs on code changes.

- **Transaction.** During a run nothing writes `state.json`:
  - `merge-tails` and the stages write `runs/<id>/state.pending.json`;
  - every reader goes through `load_state`;
  - `commit-state` applies the pending file once, advances `news_watermark`, and withholds price-derived keys when `compute_book.persist_safe` is false.

  A run that dies leaves state untouched, and `health` names the orphaned run.
- **Lock.** `.smith.lock` is created with O_EXCL, carries a heartbeat, and goes stale after 45
  minutes silent or 150 minutes total. Steals are recorded. It is gitignored, and every path
  releases it.
- **Retention** (`compact`, archive never delete):
  - flags auto-close after 30 days once every ticker has exited, except `kind=user_decision`;
  - dated data-quality notes expire after 7 days;
  - a ticker unheld and unreferenced for 30 days leaves `data_cache`;
  - unscorable superseded or auto-retired proposals are archived immediately;
  - text of terminal proposals and long trade notes moves to sidecar archives;
  - deferred, accepted_by_user and watch proposals are never auto-expired.
- **Freshness** is tracked per artefact against its TTL, and its headline goes in every
  briefing.

## Reliability layer

- **`health`** reports:
  - scheduled runs that left no run directory or ledger row (evaluated per task: the Monday weekly needs its own deep row);
  - today's run still missing after 16:00 IST;
  - a stale lock;
  - uncommitted staged state;
  - a future-stamped ledger row;
  - skill mirror drift.

  Days older than the oldest kept run directory count as pruned, not missing.
- **Watchdog.** `scripts/launchd/` installs `com.agentsmith.health`, a per-user LaunchAgent that
  runs `health --notify` on weekdays at 16:00 local time and posts a macOS notification when
  health is not ok. It is independent of Claude, so a run that never fires still gets noticed.
  Its log is `logs/health-watchdog.log`.
- **Surfacing.** Health appears in three places:
  - the preflight output, whose headline goes in the briefing header;
  - the dashboard payload key `health`, read from `health.json` and never recomputed at build;
  - the weekly report's "Missed runs" section.
- **Tests.**
  - unit tests (`tests/unit`);
  - five golden masters (`tests/verify_*.sh`);
  - a replay harness (`tests/replay_run.sh` plus `replay_diff.py`) that re-runs a saved run on a copy of the base;
  - the fleet contract and SKILL budget tests;
  - CI on every push that touches code.

## Decision and accountability layer

- **Dashboard decisions.** Accept/Reject/Hold and eight other surfaces are embedded in the
  published page and drained by the next run's `sync-decisions`.
- **Scorecard.** `score` grades matured proposals against SMH when the proposal carries a
  benchmark anchor, and on the raw move otherwise, flagged as such. `phase4.readiness` counts
  distinct scored proposals. Adaptive learning stays deferred and the hit rate advisory.

## Known architectural gaps (still open)

- **No event-driven wake for the book.** The watchdog notices missing runs, not intraday
  drawdowns. A price event gets no response until the next run or a user refresh.
- **Rolling benchmark windows are a stub.** `attribution.rolling` always returns null windows,
  so the dashboard's "beat or lag SMH" panel shows its empty state. The plausibility gate on SMH
  values is enforced where the values are written (`append-ledger`).
- **The strategist can mis-state `price_at_proposal`.** It wrote MU at 185 against a live 925 on
  2026-09-14. The orchestrator corrects prices from `live_quotes.json` before `add-proposal`, but
  that check is not yet in the script.
- **The IPS glide path** for years 3–5 is specified in prose and is not yet a dated trigger in
  `policy.json`.
- **Enterprise Software has no cluster playbook.** `validate` reports it; it is a policy decision.
