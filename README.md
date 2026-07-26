# Agent Smith — state directory

Durable memory for the Agent Smith US portfolio agent. Smith reads these files at the start of every run and writes them at the end. Files are bootstrapped on first v3+ run — don't create them by hand (but you may edit `policy.json` anytime; Smith treats your edits as authoritative).

See [ARCHITECTURE.md](ARCHITECTURE.md) for the agent fleet/flow reference, [CHANGELOG.md](CHANGELOG.md) for dated fixes and decisions, [POLICY-DECISIONS.md](POLICY-DECISIONS.md) for why policy.json's values are what they are, and [LOTS-SEEDING-GUIDE.md](LOTS-SEEDING-GUIDE.md) for unblocking LTCG tracking. `archive/session-docs-2026-07-26/` holds retired status docs from a single work session, superseded by the four files above — kept for the record, not for reading.

| File | What it holds |
|---|---|
| `policy.json` | Investment Policy Statement: cluster targets + bands, max single-position %, cash band, max AI-capex factor %, drawdown thresholds (warn / risk-off), LTCG preference. Smith drafts from the current book on first run and asks you to confirm; `"confirmed": false` marks a draft (drift analysis labeled provisional until you confirm). |
| `state.json` | Primary run-to-run memory: portfolio value, peak value, USD/INR, thesis map, sector map, signal history, open flags, news watermark, preferences, data_cache (betas, analyst targets with TTLs), us_market_holidays (US stock market closure calendar). Replaces the old transcript MILESTONE JSON (which is still emitted in chat as summary + fallback). |
| `ledger.csv` | One row per run: `ts,mode,value_usd,usdinr,wallet_usd,spx,ndx,est_net_flows_usd,notes`. Powers rolling performance vs S&P (TWR/XIRR windows) and supports intraday refresher fast-path. |
| `journal.json` | Signal accountability journal: every actionable flag Smith raises (date, ticker, bucket, price at flag, target); scored on later runs at 7d/30d horizons (`outcome_7d_pct`, `outcome_30d_pct`, verdict worked/failed/open); rolling hit-rate per bucket AND per-name×bucket combo. |
| `proposals.json` | Strategist's proposal tracking: every sized proposal ("trim NVDA ~$800") recorded with date, price_at_proposal, and status (open); scored at 30d/90d with outcome_pct and verdict (worked/missed). Aggregate strategist scorecard (% accuracy by proposal type: trim-watch, add, etc.). |
| `dashboard.html` | Source file for the "Portfolio Sweep — Agent Smith" artifact (stable path = stable artifact URL). Updated after every run. The published artifact URL is stored in `state.json` (`artifact_url`) so every session updates the same page instead of minting new links. |
| `journal-archive.json` | Fully-scored journal entries older than 12 months, pruned from `journal.json` (aggregate hit-rate counts stay in the live journal). |
| `proposals-archive.json` | Proposals with a terminal, non-scoreable status (superseded/closed/hold/not_taken), pruned from `proposals.json` to keep the live file to entries still inside a 30d/90d scoring window. |
| `known-gaps-archive.json` | Resolved/closed entries pruned from `state.json`'s `known_gaps`. |
| `exited-holdings-archive.json` | `thesis`/`sector_map` entries for positions no longer held, pruned from `state.json` (drift logic only needs current holdings). |
| `runs/<timestamp>/` | Each run's raw sub-agent outputs (holdings.json snapshot + book/signals/thesis/watchlist/quality/strategist.md files) — an auditable per-run archive. Only the 10 most recent runs are kept; older ones deleted. Enables intraday refresher fast-path and prior-self reads. |
| `.running` | Lockfile while a sweep is in progress (stale after 30 min). Prevents concurrent sweeps from clobbering state. Safe to delete if no sweep is actually running. |

**New v3+ features:**
- **Intraday refresher fast-path**: second same-day quick check reuses the morning's run, one price fetch, deltas only — no sub-agent re-dispatch.
- **Corporate-action detection**: splits and bonuses never miscounted as capital flows.
- **Data cache with TTLs**: betas, analyst targets cached in state.json; stale entries auto-pruned.
- **Per-name×bucket signal grades**: historical hit-rate grades (A/B/C/F) assigned to each name+bucket combo.
- **Proposal-outcome tracking**: every strategist proposal scored 30/90d; aggregate accuracy scorecard shows real hit-rate.
- **Preferences memory**: "stop showing X" gets logged in state and respected on future runs.
- **Macro strip + holiday calendar**: US 10-yr yield, VIX, DXY, Fed status in every briefing header; market-closed detection.
- **Quality auditor (monthly)**: PAT-vs-OCF, share dilution, leverage, customer concentration, going-concern flags.

All JSON state files carry `"schema_version": 1`. Deleting `state.json` resets Smith's memory but not your policy, ledger, proposals, or journal.

## KILL SWITCH (how to stop everything, fast)
1. **Scheduled runs**: sidebar → Scheduled → disable `agent-smith-daily-us`, `agent-smith-weekly-us`, `operator-daily-india`, `operator-weekly-india`, and delete any pending `smith-rebound-primer-YYYY-MM-DD` one-shot.
2. **A run in flight**: it stops when its session ends; if one died mid-flight, delete the stale `.running` lockfile in this directory so the next run isn't blocked.
3. **Bad state after a misbehaving run**: this directory is a git repo (since 2026-07-18, one commit per run) — `git log --oneline` to find the last good snapshot, `git checkout <hash> -- .` to restore it.
4. **Nothing here ever places trades** — stopping the agents stops analysis only; no positions or orders are affected.
