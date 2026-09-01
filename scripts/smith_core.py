#!/usr/bin/env python3
"""
Agent Smith deterministic compute layer.

Moves arithmetic that sub-agents were doing with an LLM (currency conversion,
weights, concentration, drawdown, journal scoring, drift-vs-policy, a Fear/Greed
composite) into plain Python. Sub-agents are for judgment and external data
gathering; this script is for math. Stdlib only, no pip deps.

Subcommands emit one compact JSON object to stdout. On any error, emit
{"error": "..."} to stdout and exit 1 -- the orchestrator treats that as a
signal to note the gap in data_quality and let the relevant sub-agent
compute that section inline, same as any other sub-agent failure.

Usage -- PREFER THE PIPELINE. It runs every per-run stage below in dependency order and
fails loudly instead of letting a stage emit silent zeros (see cmd_pipeline for the incident
that motivated it):

  smith_math.py pipeline    --base-dir DIR --run-dir DIR [--today YYYY-MM-DD] [--lots lots.json]

Per-run stages (all run by `pipeline`; invoke individually only to debug one):
  book        --base-dir DIR --run-dir DIR [--lots lots.json]   value/weights/concentration/drawdown
  risk        --base-dir DIR --run-dir DIR                      ATR caps, open risk   (needs book)
  drift       --base-dir DIR --run-dir DIR                      cluster/cash/AI-capex (needs book)
  journal     --base-dir DIR --run-dir DIR [--today ...]        signal hit-rate scoring
  attribution --base-dir DIR --run-dir DIR                      FX / flow / residual decomposition
  rotation    --base-dir DIR --run-dir DIR                      accumulate/trim buckets (needs risk)
  sentiment   --base-dir DIR --market-inputs market_inputs.json Fear/Greed composite
  derisk      --base-dir DIR --run-dir DIR [--today ...]        fragility queue (needs risk+sentiment)
  triggers    --base-dir DIR --run-dir DIR [--today ...]        oversold/overbought/ratchet triggers

Stages the pipeline deliberately does NOT run (each needs something it cannot supply itself):
  score       --base-dir DIR --prices-json P.json [--today ...] [--dry-run]
              proposal outcome scoring, 30d/90d. Needs prices -> run with --prices-json /dev/null
              first and it will NAME the tickers it wants.
  stops       --base-dir DIR --prices-json P.json [--today ...] stop-loss efficacy; same price rule
  proposals   --base-dir DIR --run-dir DIR [--today ...]        lifecycle/dedup/priority; run AFTER
                                                                the strategist appends this run
  dismiss     --base-dir DIR --id P-### [--reason "..."]        user-invoked, terminal
  validate    --base-dir DIR                                    policy sanity check, not per-run
"""
import json
import math
import os
import re
import sys
from datetime import date, datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


"""Shared primitives: constants and IO helpers used by every Smith module."""

DEFAULT_BASE = "/Users/yb/Claude/AgentSmith"

# Clusters counted toward the combined "AI-capex chain" factor exposure.
# Overridable via policy.json's optional "ai_capex_clusters" list.
DEFAULT_AI_CAPEX_CLUSTERS = [
    "AI Semis/Fabs", "AI Memory/Storage", "AI Networking/Optics",
    "AI Power/Cooling/DC Infra", "Compute/Hyperscaler OEM",
]

# Bucket -> expected direction, for journal verdict scoring.
BUCKET_DIRECTION = {
    "MOMENTUM+VOLUME": "up", "OVERSOLD BOUNCE": "up", "STRONG UPTREND": "up",
    "BREAKOUT": "up", "TARGET GAP": "up", "NEW TAILWINDS": "up",
    "REVERSAL - BUY WATCH": "up",
    "OVERBOUGHT PULLBACK": "down", "STRONG DOWNTREND": "down",
    "REVERSAL - TRIM WATCH": "down", "CAPITAL ROTATION": "down",
    "NEW HEADWINDS": "down",
    "EARNINGS PROXIMITY": None, "POLICY IMPACT": None, "INSIDER ACTIVITY": None,
    # Added 2026-08-25 (self-learning Phase 1 audit): these three ARE journaled by
    # smith-signals (11 entries found: 6 PEER LEADER, 4 PEER LAGGARD, 1 BREAKDOWN) but were
    # simply absent here, so every one scored "n/a" permanently regardless of what actually
    # happened to the price. Directions taken from smith_risk.SIGNAL_POLARITY, which already
    # classifies PEER LEADER/BREAKOUT/STRONG UPTREND as bullish and PEER LAGGARD/BREAKDOWN/
    # STRONG DOWNTREND as bearish -- matched here rather than re-derived, so the two tables
    # cannot silently disagree about the same bucket name.
    "PEER LEADER": "up", "PEER LAGGARD": "down", "BREAKDOWN": "down",
}

VERDICT_THRESHOLD_PCT = 2.0  # move must exceed this to call worked/failed vs neutral

ANCHOR_REVIEW_PCT = 35.0  # |move| beyond this quarantines a proposal score pending anchor review

# ---------------------------------------------------------------------------
# Trigger thresholds (added 2026-08-12, user-reported: "still most of the proposals are based
# on ATR risk-cap... I prefer oversold/overbought proposals to catch a bounce back for the good
# stocks... book profit if something had a good enough run and put my money on another stock
# which is yet to run").
#
# Diagnosis behind these numbers, all verified against the live book that day:
#   (a) the priority scorer gave over_cap +3, the largest single weight, and PENALISED a BUY
#       carrying no breach (-1) -- so "buy the good stock that is merely oversold" was
#       structurally the lowest-priority thing the engine could emit;
#   (b) rel_strength_1m was 12 days stale against its own 7-day TTL and missing 10 of 28 names,
#       starving the one existing profit-take trigger (names_stretched was just [AVGO, CEG]);
#   (c) no per-name RSI existed anywhere in data_cache, so overbought/oversold could not be
#       computed deterministically at all -- OVERBOUGHT PULLBACK had fired ONCE in 69 journal
#       entries, while OVERSOLD BOUNCE carried the book's best interim 7d hit rate (100%, n=4)
#       and was almost never flagged.
#
# Entry and exit thresholds deliberately differ (hysteresis): a setup that triggers at RSI<35
# is not un-triggered the moment it ticks to 36. Without the gap a proposal would flip between
# open and auto_retired on noise, which is exactly the churn the retirement pass exists to avoid.
RSI_OVERSOLD = 35.0

RSI_OVERSOLD_EXIT = 50.0

RSI_OVERBOUGHT = 70.0

RSI_OVERBOUGHT_EXIT = 60.0

# A live trigger may never fire off a stale technical read. 10 days is deliberately looser than
# the 7-day cache TTL (a 1-day overrun should not blind the desk) but far tighter than the 12-day
# staleness that was found in production -- past this, the lists come back empty with a flag
# rather than acting on numbers that no longer describe the market. Never estimate.
TRIGGER_CACHE_MAX_AGE_DAYS = 10

# A cache can be perfectly fresh and still describe only part of the book, which shrinks the
# trigger candidate set just as effectively as staleness -- and nothing named it until 2026-08-30,
# when rsi14 and rel_strength_1m each covered 31 of 35 held names. Set at 85% rather than 100%
# because a genuinely new or short-history listing (SKHY's ADR has too few closes for RSI14) is a
# legitimate permanent gap, not a refresh failure; the flag should fire on neglect, not on physics.
# ---------------------------------------------------------------------------
# REBOUND / BROAD-CORRECTION SCREEN (added 2026-08-30)
# ---------------------------------------------------------------------------
# smith-rebound's mandate was RESTATED by the user on 2026-08-30 and it is not what the agent
# had been built to do. Its file framed it as a "Drawdown-Day Rapid Redeployment Desk" whose
# rule A is stop-loss forensics (diff holdings, find what got stopped out) and whose rule E
# only scans names ALREADY HELD. So the orchestrator skipped it, correctly under that framing,
# on runs with no stop-outs and no spare cash -- 2026-08-26 and 08-29 both say so in the ledger.
#
# The real mandate: find names that have fallen too far in a BROAD CORRECTION, biased toward
# HIGH-VOLATILITY names, as candidates to buy for a relief rally. That needs none of the three
# things it was being gated on -- it does not require a stop-out, does not require spare cash
# (the candidates are equally the buy leg of a rotation), and must not be limited to current
# holdings, since a name exited in the selloff is exactly the kind of candidate wanted.
#
# So the dispatch condition becomes a MEASURED correction state rather than a pre-market
# futures gate. The futures gate answers "is this morning scary", which is a different and much
# noisier question than "has this book actually corrected".
#
# Thresholds are derived from policy.drawdown_warn_pct rather than invented, so they track the
# user's own stated risk appetite instead of drifting away from it: `deep` is the policy warn
# line itself, `correction` is half of it, `pullback` a quarter. On the day this was written the
# book sat at -7.94% -- a real correction by any reading, and less than a third of the way to the
# policy warn line, which is precisely the zone the old gate had no way to name.
REBOUND_DEEP_FRACTION_OF_WARN = 1.0
REBOUND_CORRECTION_FRACTION_OF_WARN = 0.5
REBOUND_PULLBACK_FRACTION_OF_WARN = 0.25

# Benchmark confirmation, independent of the book's own peak. A book can be near its peak while
# its sector is mid-correction (and vice versa after a large deposit), so either route qualifies.
REBOUND_BENCH_1M_CORRECTION_PCT = -6.0
REBOUND_BENCH_1M_PULLBACK_PCT = -3.0

# Breadth: a correction that has hit half the book is a correction whatever the peak says.
REBOUND_BREADTH_FALL_PCT = -10.0
REBOUND_BREADTH_SHARE = 0.50

# Candidate screen. A name must have fallen at least this much to be a rebound candidate at all,
# and must carry at least this much volatility -- the high vol IS the thesis here (it is what
# makes the relief rally worth catching), not a risk to be screened out.
# WINDOW: a selloff resolves in about a week, so the fall measure must be a WEEK, not a month
# (user, 2026-08-30). The first cut used rel_strength_1m's `values_abs_pct` purely because it was
# the only per-name return already cached -- a convenience, not a judgement, and a bad one: a
# 1-month window straddles the pre-selloff rally, so a name that dropped 18% in five days can
# read flat over the month and never surface at all. `ret_5d` is computed from the SAME daily
# bars that already produce ATR20 and RSI14, so it costs nothing extra to collect.
# ret_1m is kept only as a labelled fallback for names with too little history.
REBOUND_FALL_WINDOW_DAYS = 5
REBOUND_MIN_FALL_PCT = -8.0          # over 5 days
REBOUND_MIN_FALL_PCT_1M_FALLBACK = -12.0
REBOUND_MIN_ATR_PCT = 6.0

# SUPPORT-ANCHORED STOP EXCEPTION (added 2026-08-30, explicit user instruction).
# The general rule sizes every position off a stop 2xATR below SPOT, which is correct when you
# have no view on where the name should hold. A rebound entry does: it is bought AT a support
# level, so the stop belongs just under that level -- a much shorter distance, and therefore a
# larger position at the SAME 0.5% dollar risk. No extra risk is taken; the risk is measured
# where it actually sits.
#
# THE DANGER, and the floor that answers it. A 4% stop on a 14%-ATR name is exactly the whipsaw
# policy.json's own rationale was written to prevent ("a 3% stop on a name that ranges 8-9%
# intraday is a near-certain whipsaw"). So the support-anchored stop is floored at half the
# name's average daily range: you may stop tighter than 2x the noise band because you have a
# real level, but never inside half a day's normal movement.
#
# That floor doubles as the uplift bound, which is why it needs no separate cap: the standard
# stop is 2xATR and the tightest permitted is 0.5xATR, so this exception can never size more
# than 4x the standard cap for any name where 2xATR clears the 3% absolute floor.
REBOUND_STOP_ATR_FLOOR_MULT = 0.5

# Trigger types allowed to use the exception. Deliberately narrow: this is a rebound-entry
# mechanism, not a general loosening of position sizing.
SUPPORT_ANCHORED_TRIGGERS = {"rebound", "rebound_entry"}

CORRECTION_STATES = ("none", "pullback", "correction", "deep_correction")

TRIGGER_CACHE_MIN_COVERAGE_PCT = 85.0

# A weekly move in a sector ETF beyond this is not a market event, it is a corrupt cell.
# ledger.csv's `smh` column mixes real levels (~545-570) with values from another series
# entirely, which rendered a '+254.09%' weekly benchmark move. Same doctrine as the charts:
# a corrupt reading never sets an axis and never counts as performance.
BENCHMARK_WEEKLY_PLAUSIBLE_PCT = 25.0

LAGGARD_PCTILE = 25.0            # bottom quartile of 1m relative strength = "yet to run"

RATCHET_MIN_GAIN_PCT = 15.0      # gain before a stop is worth ratcheting to breakeven

LADDER_TIERS_PCT = [25.0, 50.0]  # scale-out rungs, each selling LADDER_FRACTION of the position

LADDER_FRACTION = 1.0 / 3.0

OVERBOUGHT_TRIM_FRACTION = 0.25  # profit-take slice on an overbought name

MAX_SINGLE_DEPLOY_FRACTION = 0.25  # cap one buy suggestion at this share of deployable cash

# 2026-08-17, user-reported: "most of the proposals and the analysis is banked on the ATR
# risk/cluster cap/cash band... these caps/bands was formed as a loose portfolio composition.
# The trades/proposals should focus on other important criteria impacting an individual stock
# price instead." Diagnosis confirmed against a live run: the 2026-08-12 fix (demoting over_cap,
# adding the two RSI-based live triggers) was necessary but not sufficient -- 6 of 8 HIGH
# proposals that run carried NO live trigger at all and reached HIGH purely by stacking
# over_cap+cluster+cash+repeat, none of which says anything about whether the STOCK itself gave
# a reason. Worse, the two things that actually DO move a stock for company-specific reasons --
# a structural threat catalyst (smith-catalyst) and a thesis flipping to broken (smith-thesis) --
# had NO path into the scorer at all; the AVGO/BX bond-downgrade catalyst that same run only
# became a proposal because the strategist manually folded it in by hand.
#
# catalyst_threat and thesis_break close that gap. Deliberately LIVE from day one, not
# shadow-first like laggard_rotation/profit_ratchet/scale_out_ladder above: the shadow-first
# rule exists for NEWLY INVENTED STATISTICAL HEURISTICS with no track record in this book
# (bottom-quartile relative strength, an arbitrary gain threshold) -- it does not apply to
# findings that are already evidence-graded and sourced before they ever reach this scorer. A
# catalyst_threat requires smith-catalyst to have classified something direction="threat" AND
# horizon="structural" with a named source; a thesis_break requires smith-thesis to have
# explicitly flipped a name to "broken", which under the G58 evidence gate means it carries its
# own evidence_for/evidence_against arrays. Gating these behind a fabricated hit-rate measurement
# would mean re-deriving conviction the analyst agents already established, which is the exact
# manual-workaround gap this closes, not a new heuristic being tested.
CATALYST_THREAT_TRIM_FRACTION = 0.20  # a probabilistic tail risk -- lighter than overbought's 0.25

THESIS_BREAK_TRIM_FRACTION = 0.40  # a confirmed fundamental break -- heavier; strategist may size to a full exit

# A technical dip on an intact thesis is a bounce setup; a technical dip alongside a FUNDAMENTAL
# negative is a falling knife. Only the latter disqualifies -- requiring net-bullish signals
# would disqualify every oversold name by definition, since being oversold IS bearish price action.
FUNDAMENTAL_HEADWIND_BUCKETS = {"NEW HEADWINDS"}

# G62: how recently a thesis must have been source-verified to outrank a stale, untimestamped
# signal_history headwind bucket. 7d ties it to the same weekly cadence the ATR/beta/rel caches
# use, so an override always rests on evidence from the current week.
THESIS_OVERRIDES_STALE_BUCKET_DAYS = 7

# G62 part (a) -- the general decay rule, complementing the narrow thesis-override below.
# smith-signals REWRITES a ticker's bucket list wholesale on every successful run, so buckets only
# go stale when that agent FAILS -- which is exactly what happened to META on 2026-08-12. A
# per-ticker refresh stamp (state.signal_history_as_of) therefore captures staleness precisely: it
# advances whenever signals ran, and freezes when it didn't. Past this age an unrefreshed
# news-flow bucket stops being decisive. It is still REPORTED -- decay removes the veto, not the
# information. A ticker with no stamp at all is treated as stale: the veto is the dangerous
# default, so unknown age must fail open, not closed.
HEADWIND_BUCKET_MAX_AGE_DAYS = 10

# ---------------------------------------------------------------------------
# FRESHNESS -- one declarative table for every artefact that can go stale (2026-08-30)
# ---------------------------------------------------------------------------
# Counterpart to smith_memory's RETENTION, and written for the same reason. RETENTION exists
# because eviction was a per-file afterthought; FRESHNESS exists because STALENESS was too.
#
# Audited 2026-08-30 across ~11k lines: exactly THREE age constants existed anywhere --
# TRIGGER_CACHE_MAX_AGE_DAYS (10), HEADWIND_BUCKET_MAX_AGE_DAYS (10) and
# EARNINGS_PENDING_HARD_STALE_DAYS (0) -- plus validate_cache_events for fomc_cache and
# HOLD_MAX_AGE_DAYS for hold proposals. Meanwhile data_cache.cache_policy.ttl_days DECLARED
# NINE TTLs, of which two were enforced anywhere at all; the rest were documentation.
#
# Worse: only data CACHES were checked. No sub-agent OUTPUT was age-checked at any point. On
# the day this table was written the live state carried factor_themes at 33 days old, tax_read
# at 13, a `thesis` map of 35 entries with no review date on any of them, and cycle_position
# -- which SKILL.md §3 calls "the highest-leverage single read on the book" -- simply absent,
# the same shape as the G50 factor-catalysts loss (agent dispatched, output silently discarded).
#
# The invariant this table encodes: A DECLARED TTL MUST HAVE AN ENFORCER. If an artefact
# matters enough to carry a refresh cadence, going past that cadence has to produce a visible
# consequence -- not a data_quality bullet nobody is obliged to read. That failure mode is
# documented verbatim in validate_technical_cache_staleness' own docstring: rsi14 sat stale
# across three consecutive runs, each noting it quietly, each deferring "on cost grounds",
# while the desk's single most-requested feature stayed dark.
#
# FIELDS
#   key       dotted path into state.json ("data_cache.rsi14", "factor_themes")
#   stamp     how to find its as_of date:
#               "field:<name>"      -- a date string on the artefact dict itself
#               "sibling:<name>"    -- a sibling key on state ("watchlist_setups_as_of")
#               "max_date"          -- newest `date` across a list of records
#               "per_entry:<name>"  -- each entry carries its own stamp; the artefact's age is
#                                     the age of its OLDEST entry, because a 35-name map goes
#                                     stale unevenly and a single map-level date hides exactly
#                                     the names nobody has looked at
#   ttl_days  refresh cadence
#   owner     the agent responsible -- so a stale artefact names who stopped contributing
#   on_stale  what going past ttl means, and hence when the artefact counts as DARK:
#               "suppress" -- a live consumer already refuses to use it (dark past
#                             TRIGGER_CACHE_MAX_AGE_DAYS); the capability is genuinely off
#               "escalate" -- no consumer suppresses, so staleness is invisible without this;
#                             dark the moment it passes ttl
#               "flag"     -- degrades gracefully; dark only at 2x ttl
# Combined size of an ACCEPTED-but-unexecuted proposal plus a new OPEN one on the same name and
# side, as a percentage of the position, above which a SELL/TRIM stack is escalated. Sells are
# the bounded side -- you cannot sell more than you hold -- so a large combined percentage there
# is a concrete error rather than merely an oversized bet. 50% chosen because the live case that
# prompted it (MSFT, 2026-08-31) was 73% and the two benign cases were 50% and 60% BUY-side.
# --- TIMESTAMP DISCIPLINE (added 2026-09-01) --------------------------------------------------
# Two separate timestamp failures on 2026-08-31/09-01 motivated this:
#   (a) An unattended run wrote "2026-08-31-1554" -- a RUN-DIR LABEL -- into ledger.csv's `ts`
#       column, which takes --ts verbatim. It survived only because every reader slices [:10],
#       so it parsed as a date by luck while carrying no time and no timezone.
#   (b) A scheduled task's lastRunAt is UTC and this desk thinks in IST. Reading 03:38Z as an
#       IST clock time put a run 5.5 hours from where it happened and sent a filesystem search
#       to the wrong window, which produced a confidently wrong "the run wrote nothing" read.
# So: one parser, one renderer, and both always show BOTH zones.
IST = timezone(timedelta(hours=5, minutes=30))
LEDGER_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$")


def parse_ts(value):
    """Parse a ledger/artefact timestamp. Returns an aware datetime, or None if unparseable.

    Deliberately strict about what it ACCEPTS as a real timestamp but lenient about what it can
    read, so a validator can tell "malformed but recoverable" from "not a timestamp at all"."""
    t = str(value or "").strip()
    try:
        dt = datetime.fromisoformat(t)
        return dt if dt.tzinfo else dt.replace(tzinfo=IST)
    except ValueError:
        pass
    m = re.match(r"^(\d{4}-\d{2}-\d{2})-(\d{2})(\d{2})$", t)   # run-dir label, e.g. 2026-08-31-1554
    if m:
        return datetime.fromisoformat(f"{m.group(1)}T{m.group(2)}:{m.group(3)}:00").replace(tzinfo=IST)
    try:
        return datetime.fromisoformat(t[:10]).replace(tzinfo=IST)
    except ValueError:
        return None


def fmt_ts(value):
    """Render a timestamp as '<UTC>Z (<HH:MM> IST)'. Never show one zone alone: every time this
    desk has been confidently wrong about when something happened, it was reading one zone's
    clock as the other's."""
    dt = parse_ts(value)
    if dt is None:
        return f"{value!r} (unparseable)"
    return (dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            + dt.astimezone(IST).strftime(" (%H:%M IST %Y-%m-%d)"))


STACK_WARN_PCT = 50.0

FRESHNESS = {
    # --- technical caches: feed LIVE proposal triggers, suppressed by cmd_triggers ---
    "data_cache.rsi14":            {"stamp": "field:as_of", "ttl_days": 7,  "owner": "smith-signals",   "on_stale": "suppress"},
    "data_cache.rel_strength_1m":  {"stamp": "field:as_of", "ttl_days": 7,  "owner": "smith-signals",   "on_stale": "suppress"},
    "signal_history":              {"stamp": "per_entry:signal_history_as_of", "ttl_days": HEADWIND_BUCKET_MAX_AGE_DAYS,
                                    "owner": "smith-signals", "on_stale": "suppress"},
    # --- technical caches: degrade gracefully (a stale ATR makes stops marginally wide) ---
    "data_cache.atr20":            {"stamp": "field:as_of", "ttl_days": 7,  "owner": "smith-signals",   "on_stale": "flag"},
    # Feeds the rebound screen, which only matters DURING a selloff -- a week-old 5-day return
    # describes last week's selloff, so this is the tightest TTL in the table.
    "data_cache.ret_5d":           {"stamp": "field:as_of", "ttl_days": 3,  "owner": "smith-signals",   "on_stale": "suppress"},
    "data_cache.betas":            {"stamp": "field:as_of", "ttl_days": 30, "owner": "smith-signals",   "on_stale": "flag"},
    "data_cache.analyst_targets":  {"stamp": "field:as_of", "ttl_days": 7,  "owner": "smith-signals",   "on_stale": "flag"},
    # Lives in proposals.json, not state.json -- reachable via freshness_root()'s `proposals.`
    # prefix. Added 2026-08-31: this is the artefact that measures whether the desk's own
    # proposals WORK, and it was the only decision-bearing one with no freshness coverage. It
    # sat frozen for two days behind a correctly-refusing anti-shrink guard, because grading it
    # needs prices for exited/watchlist tickers that holdings.json structurally cannot supply.
    # 14 days, not 7: it only scores at 30-day maturity, so a week-old scorecard is normal.
    # The six-scenario stress table. Added to FRESHNESS 2026-08-31 in the same change that gave
    # it a structured output and a write path -- an artefact with a persist path but no age check
    # is only half out of the dark. 7 days: it is a deep-run product and a stress picture built
    # against a fortnight-old rate/VIX strip is describing a different market.
    "stress_table":                {"stamp": "field:as_of", "ttl_days": 7,  "owner": "smith-strategist", "on_stale": "flag"},
    "proposals.scorecard":         {"stamp": "field:as_of", "ttl_days": 14, "owner": "orchestrator", "on_stale": "flag"},
    "data_cache.etf_constituents": {"stamp": "field:as_of", "ttl_days": 30, "owner": "smith-thesis",    "on_stale": "flag"},
    "data_cache.earnings_calendar":{"stamp": "field:as_of", "ttl_days": 30, "owner": "smith-earnings",  "on_stale": "flag"},
    # --- sub-agent OUTPUTS: nothing checked any of these before this table existed ---
    "thesis":                      {"stamp": "per_entry:reviewed_on", "ttl_days": 21, "owner": "smith-thesis",  "on_stale": "escalate"},
    "sector_map":                  {"stamp": "sibling:sector_map_as_of", "ttl_days": 30, "owner": "smith-thesis", "on_stale": "flag"},
    "peer_map":                    {"stamp": "sibling:peer_map_as_of",   "ttl_days": 30, "owner": "smith-signals","on_stale": "flag"},
    "factor_catalysts":            {"stamp": "max_date",   "ttl_days": 7,  "owner": "smith-catalyst",  "on_stale": "flag"},
    "factor_themes":               {"stamp": "sibling:factor_themes_as_of", "ttl_days": 30, "owner": "smith-catalyst", "on_stale": "escalate"},
    "diversifier_candidates":      {"stamp": "per_entry:as_of", "ttl_days": 7, "owner": "smith-scout", "on_stale": "flag"},
    "watchlist_setups":            {"stamp": "sibling:watchlist_setups_as_of", "ttl_days": 7,
                                    "owner": "smith-watchlist", "on_stale": "escalate"},
    "macro_read":                  {"stamp": "field:as_of", "ttl_days": 7,  "owner": "smith-macro",     "on_stale": "flag"},
    "tax_read":                    {"stamp": "field:as_of", "ttl_days": 30, "owner": "smith-tax",       "on_stale": "flag"},
    # --- monthly agents: a missed month must be a defect, not a silence (G50 shape) ---
    # Only meaningful during a correction, so a short TTL: a rebound list from a fortnight ago
    # describes a selloff that has already resolved one way or the other.
    "rebound_candidates":          {"stamp": "field:as_of", "ttl_days": 5,  "owner": "smith-rebound", "on_stale": "flag"},
    "cycle_position":              {"stamp": "field:as_of", "ttl_days": 35, "owner": "smith-cycle",   "on_stale": "escalate"},
    "quality_read":                {"stamp": "field:as_of", "ttl_days": 35, "owner": "smith-quality", "on_stale": "escalate"},
}

# How far past ttl an artefact must be before its capability counts as genuinely OFF rather
# than merely overdue. Keyed by on_stale, because "dark" means different things: a suppressed
# cache is dark when its live consumer stops reading it; an escalate-class artefact has no
# consumer that suppresses, so it is dark the moment it lapses; a flag-class one degrades.
DARK_MULTIPLIER = {"suppress": None, "escalate": 1.0, "flag": 2.0}

HEALTHY_THESIS = {"intact", "strengthening"}

LIVE_TRIGGERS = {"oversold_reversion", "overbought_distribution", "catalyst_threat", "thesis_break"}

SHADOW_TRIGGERS = {"laggard_rotation", "profit_ratchet", "scale_out_ladder"}

# ---------------------------------------------------------------------------
# CONVICTION-DRIVEN TRIGGERS (added 2026-08-24, third time the user reported the same defect --
# see smith_conviction.py's module docstring for the full diagnosis). These generate and SIZE
# proposals from conviction (smith_conviction.score_conviction / conviction_size), never from a
# flat fraction of market value or a bare ATR-headroom minimum -- risk caps then CLAMP the
# result via smith_conviction.clamp_size, they never invent it.
#
# All are LIVE, same reasoning as catalyst_threat/thesis_break above: each consumes findings the
# analyst agents already evidence-graded (thesis, factor_catalysts, signal buckets, analyst
# targets, earnings_facts) rather than a newly invented statistical heuristic with no track
# record -- the shadow-first rule does not apply to re-using already-verified conviction.
#
# One deliberate consolidation vs the original design sketch: a separate `dip_redeploy` trigger
# reading smith-rebound's live proposals[] was dropped -- that data is ephemeral per-run output,
# not persisted state, so a trigger keyed on it would silently return empty on any run rebound
# wasn't dispatched. `conviction_average` (for held names) and `reentry` (for exited names)
# already cover the identical behaviour -- a real dip on a name worth owning -- from data that
# IS always available, so the post-cascade-redeploy case is covered without a fragile dependency.
CONVICTION_TRIGGERS = {
    "trend_entry", "trend_breakdown", "profit_rotation", "cluster_rotation",
    "conviction_average", "conviction_exit", "entry_setup", "reentry", "bench_diversifier",
}

LIVE_TRIGGERS = LIVE_TRIGGERS | CONVICTION_TRIGGERS

# Proposal classification for the dashboard's two-panel split (added 2026-08-24). IDEAS are
# conviction-driven investment decisions; HOUSEKEEPING is portfolio-mechanics maintenance (a cap
# breach, a stop-raise, a band drift) that is still sized and actionable but must never compete
# with an idea for the top of the list -- that competition, with mechanics winning by sheer
# stacking, is the root defect this whole file exists to fix. A trigger_type not listed here
# (legacy proposals, hand-written strategist ideas with no trigger_type) defaults to "idea" --
# the safe direction, since the alternative (defaulting everything unlabelled to housekeeping)
# would have silently reclassified every historical proposal the day this shipped.
HOUSEKEEPING_TRIGGERS = {
    "oversold_reversion", "overbought_distribution", "laggard_rotation",
    "profit_ratchet", "scale_out_ladder",
}


def proposal_class(trigger_type):
    if trigger_type in HOUSEKEEPING_TRIGGERS:
        return "housekeeping"
    return "idea"

# Every agent gets these, per SKILL section 3's "Embed in EVERY prompt".
GAPS_CAP, FLAGS_CAP = 8, 5

# ---------------------------------------------------------------------------
# Canonical 4-way bucket every proposal verb collapses to, for both dedup-matching and the
# dashboard's color coding. Deliberately coarse: "Stage AMD", "Deploy GOOGL", "Top up GOOGL",
# "Initiate META" and "ADD MRVL" are all different staging language for the same underlying
# idea (put more money into this name), and "Light trim X" is the same idea as "Trim X" --
# treating them as different directions was why near-identical proposals (see G46) weren't
# recognized as duplicates of each other. Longest phrase first so multi-word keywords are
# matched before a shorter keyword nested inside a longer action string would win instead.
DIRECTION_KEYWORDS = [
    ("DEPLOY INTO", "BUY"), ("TOP UP", "BUY"), ("LIGHT TRIM", "TRIM"), ("HOLD FIRE", "HOLD"),
    ("REBUILD", "HOLD"), ("RE-ENTER", "BUY"), ("RE-ENTRY", "BUY"), ("REENTER", "BUY"),
    ("RE-ACCUMULATE", "BUY"), ("ACCUMULATE", "BUY"),
    ("STAGE", "BUY"), ("INITIATE", "BUY"), ("DEPLOY", "BUY"),
    ("BUILD", "BUY"), ("BUY", "BUY"), ("ADD", "BUY"), ("TRIM", "TRIM"), ("REDUCE", "TRIM"),
    ("EXIT", "SELL"), ("SELL", "SELL"), ("HOLD", "HOLD"),
]

DIRECTION_BUCKET = {"BUY": "BUY", "TRIM": "TRIM", "SELL": "SELL", "HOLD": "HOLD"}

# ---------------------------------------------------------------------------
# derisk -- the De-risk Queue (added 2026-07-31)
#
# Ranks every holding by how much damage it can do IF a drawdown comes, not by
# any attempt to predict one. Three transparent sub-scores, never a black box:
#
#   FRAGILITY  dollars-at-risk share (already embeds ATR x size) x how far the
#              position sits over its own 2xATR cap. "How hard does this hit."
#   STRETCH    1-month return RELATIVE TO SMH, positive side only. A name that
#              has run ahead of its own sector has something to give back; a
#              name lagging SMH has already been punished and is NOT a trim
#              candidate on stretch grounds. Deliberately relative, not
#              absolute: in a ~100% single-factor book an absolute RSI/52wk
#              screen flags all-or-nothing (2026-07-31: sentiment read "greed"
#              while 20 of 27 names sat >20% below their own 52wk highs, and the
#              only name an absolute screen flagged was DRAM -- on a known bad
#              52wk-low of $0. That is the failure mode this design avoids.)
#   FRICTION   cost of acting: LTCG proximity from lots.json (never trim a lot
#              weeks from its 24-month boundary when a comparable one is far
#              away), plus a dust-position discount.
#
# Sentiment is an URGENCY DIAL on the whole queue, never a trigger. Extreme
# greed raises the ranking; extreme fear damps it (do not sell into panic).
# It cannot manufacture stretch that does not exist per-name.
# ---------------------------------------------------------------------------
BAND_URGENCY = {"extreme_greed": 1.25, "greed": 1.0, "neutral": 0.9,
                "fear": 0.75, "extreme_fear": 0.5}

LTCG_MONTHS_DEFAULT = 24          # India: US-listed foreign shares

LTCG_DEFER_WINDOW_MONTHS = 6.0    # inside this, trimming forfeits a near boundary

DUST_USD_DEFAULT = 400.0

# ---------------------------------------------------------------------------
# lots -- deterministic FIFO with corporate-action support
# ---------------------------------------------------------------------------
# WHY THIS EXISTS (added 2026-08-15). Two things were wrong at once.
#
# 1. FIFO WAS BEING DONE BY AN LLM. lots.json is the desk's cost-basis and holding-period
#    record, and until now it was rebuilt by hand by the smith-ledger sub-agent. Consuming
#    lots oldest-first is pure deterministic arithmetic over data already on disk -- exactly
#    what the COMPUTE-FIRST PRINCIPLE says must never be an LLM's job. It stayed that way only
#    because nobody had written the engine.
#
# 2. THE LEDGER COULD NOT EXPRESS EVENTS THAT MOVE SHARES WITHOUT A TRADE. Share-class
#    conversions, splits, fractional-share credits and DRIP all change share counts and
#    generate NO buy/sell confirmation, so an email-sourced ledger simply cannot see them.
#    That produced two standing gaps: G71 (GOOG's FIFO runs -2.9919sh -- it "sold" three more
#    shares than it ever bought, across a GOOG->GOOGL conversion) and G68 (QCOM +3.0sh and
#    MSFT +1.5sh over-counted against the broker, with fractional-share activity visible in
#    the fills). Both are the same shape: a real event the schema had no row for.
#
# The corporate-action row closes that. Critically it CARRIES COST BASIS AND ACQUISITION DATE
# through a conversion or split -- a conversion is not a sale and a split is not a purchase,
# so neither restarts the LTCG holding-period clock. Getting that wrong would silently reset
# every affected lot's clock and corrupt the tax picture, which is worse than the gap it fixes.
#
# It also refuses to clamp. If a sell consumes more than exists, the old hand-FIFO floored at
# zero and moved on, which is how a phantom short stayed invisible until someone eyeballed a
# negative. Here it is recorded as a `phantom_short` and reported.

CA_TYPES = ("conversion", "split", "fractional_credit", "spinoff", "adjustment")

def load_json(path, default=None):
    if not os.path.exists(path):
        if default is not None:
            return default
        raise FileNotFoundError(path)
    with open(path) as f:
        return json.load(f)

def emit(obj):
    print(json.dumps(obj, indent=None, sort_keys=False))

def fail(msg):
    print(json.dumps({"error": msg}))
    sys.exit(1)

def clamp(x, lo=0.0, hi=100.0):
    return max(lo, min(hi, x))


def safe_write(path, obj):
    """WRITE SAFETY contract for any memory-of-record file: .bak (one rolling generation) then
    tmp-then-mv. An interrupted run leaves either the old file intact or a stray .tmp, never a
    truncated file. Promoted here 2026-08-25 from smith_memory._safe_write (added 2026-08-16) --
    that copy was the only one three places actually used; five other call sites
    (smith_ledger.py, four in smith_lifecycle.py) had each hand-rolled a WEAKER version that
    skips the .bak half entirely (tmp-then-mv only). Every module already does
    `from smith_core import *`, so this is reachable everywhere without a new import -- the
    prior home in smith_memory required a manual cross-module import that nobody added."""
    if os.path.exists(path):
        with open(path) as f_in, open(path + ".bak", "w") as f_out:
            f_out.write(f_in.read())
    with open(path + ".tmp", "w") as f:
        json.dump(obj, f, indent=2)
    os.replace(path + ".tmp", path)

# Metadata keys that live ALONGSIDE ticker entries inside a stamped cache map. `as_of` is
# written as a sibling of the tickers in earnings_calendar and analyst_targets (see
# _merge_watchlist / _merge_signals) because that is where the FRESHNESS table reads it from.
# The cost is that a naive `.items()` over such a map yields a fake ticker called "as_of" whose
# value is a string -- which crashed the dashboard build on 2026-08-31 with
# `'str' object has no attribute 'get'`, a latent break introduced whenever the stamp was first
# added and invisible until the next rebuild. Iterate stamped maps through ticker_rows() rather
# than fixing each call site as it blows up.
CACHE_META_KEYS = {"as_of", "ttl_days", "period", "method", "window", "source", "note",
                   "benchmark", "benchmark_return_pct", "benchmark_return_1m_pct",
                   "coverage_pct", "schema_version"}


def ticker_rows(cache, want=dict):
    """(ticker, value) pairs from a stamped cache map, excluding metadata siblings.

    `want` filters by value type so a caller that needs dict rows never receives a bare string;
    pass want=None to accept any value. Returns a list, not a generator, so callers can len()
    it -- coverage counts are the usual second question after "what is in here".
    """
    if not isinstance(cache, dict):
        return []
    return [(k, v) for k, v in cache.items()
            if k not in CACHE_META_KEYS and not k.startswith("_")
            and (want is None or isinstance(v, want))]


def _prior_run_prices(base_dir, run_dir, state):
    """Last-known price per ticker from the PREVIOUS run's compute_book.json.

    Used to price full exits (the row is gone from the current snapshot, so there is no
    live price for it) -- see G41. Deliberately defensive, because two ways of getting
    this wrong were both hit for real on 2026-08-07:
      (a) SELF-REFERENCE: state.last_run_dir can already point at the run currently being
          computed. Reading the file we are about to overwrite is meaningless at best, and
          if a shell redirect truncated it first, json.load raises and takes the whole
          subcommand down. Skip when the paths resolve to the same directory.
      (b) UNPARSEABLE PRIOR: a truncated/partial compute_book.json from an interrupted run
          must degrade to "no prior prices" (exits then land in exits_unpriced and are
          reported), never crash the run.
    """
    if not run_dir:
        return {}
    prior_dir = os.path.join(base_dir, run_dir)
    try:
        if os.path.realpath(prior_dir) == os.path.realpath(getattr(_prior_run_prices, "_current", "")):
            return {}
    except OSError:
        pass
    path = os.path.join(prior_dir, "compute_book.json")
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return {}
    try:
        with open(path) as f:
            prior_book = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    return {pp["ticker"]: pp["price_usd"]
            for pp in prior_book.get("positions", []) if pp.get("price_usd")}
