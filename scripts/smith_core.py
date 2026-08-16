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
import argparse
import json
import math
import os
import re
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smith_risk


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

LAGGARD_PCTILE = 25.0            # bottom quartile of 1m relative strength = "yet to run"

RATCHET_MIN_GAIN_PCT = 15.0      # gain before a stop is worth ratcheting to breakeven

LADDER_TIERS_PCT = [25.0, 50.0]  # scale-out rungs, each selling LADDER_FRACTION of the position

LADDER_FRACTION = 1.0 / 3.0

OVERBOUGHT_TRIM_FRACTION = 0.25  # profit-take slice on an overbought name

MAX_SINGLE_DEPLOY_FRACTION = 0.25  # cap one buy suggestion at this share of deployable cash

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

HEALTHY_THESIS = {"intact", "strengthening"}

LIVE_TRIGGERS = {"oversold_reversion", "overbought_distribution"}

SHADOW_TRIGGERS = {"laggard_rotation", "profit_ratchet", "scale_out_ladder"}

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
