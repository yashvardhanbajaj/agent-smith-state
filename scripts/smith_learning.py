"""
Agent Smith -- self-learning substrate. Added 2026-08-25, Phase 0 of a user-requested,
explicitly phased plan (see the plan file this session wrote for the full diagnosis).

WHAT THIS FILE IS NOT: an ML library. There are no model weights and no gradient updates
anywhere in this module. A "learned value" here is always a named number with an observation
count (n), a hand-set default it can never lose, and a bounded drift off that default. The
actual learning -- recognizing a systematic bias and deciding what to do about it -- still
happens by a human reading `learn status` and `lessons`, same as every fix in this codebase's
history to date. This module's job is narrower: stop letting that recognition depend entirely
on someone re-deriving it from raw files in their head each time.

THE GOVERNING DOCTRINE, stated three times already in this codebase before this file existed
(smith_core.py's shadow-trigger rule, `journal.json`'s note, `trigger_journal.json`'s note):
DERIVE ON READ FROM AN APPEND-ONLY LOG; NEVER STORE A DERIVED NUMBER AS AUTHORITATIVE. This
module follows that literally: `observations` is the only thing ever trusted as ground truth.
A parameter's current value is *computed* from its observations every time `evaluate()` runs,
gated and clamped, never read back as a cached number. What DOES get persisted is the STATE
MACHINE POSITION (default/shadow/active/escalated) and a human-readable history of when and
why it moved -- because that is a decision, not a statistic, and deciding it fresh on every
read would mean a parameter could flicker between active and shadow run to run on noise.

STATE MACHINE (mirrors smith_core.py's LIVE_TRIGGERS/SHADOW_TRIGGERS split exactly, applied to
parameters instead of signals -- "a new signal class earns its vote before it gets one" becomes
"a new calibration earns its vote before it gets one"):

    default --> shadow --> active --> escalated
                (derived,   (voting,   (measurement wants to move
                 not voting)  in band)   beyond its band -- asks the user)

Nothing skips `shadow`. `default` (the hand-set original) is always recoverable -- it is never
overwritten, only shadowed by `current` in the parameter record.
"""

import os
from datetime import date, datetime

from smith_core import load_json, emit, fail, safe_write
from smith_lifecycle import _proposal_parse_date  # `import *` skips underscore names

STORE_FILENAME = "learning.json"

DEFAULT_STORE = {
    "schema_version": 1,
    "_readme": ("Self-learning substrate. `observations` is the only ground truth -- append-"
                "only, never edited in place. `parameters` holds each tunable's STATE (default/"
                "shadow/active/escalated) and change history; the numeric value itself is "
                "DERIVED from observations on every read via smith_learning.evaluate(), never "
                "cached here as authoritative. `lessons` is corrections, decisions not to "
                "re-litigate, and dead ends -- read this before proposing a fix that sounds "
                "familiar, it may already be lesson #1."),
    "observations": [],
    "parameters": {},
    "lessons": [],
}

# Every parameter this module knows how to gate uses these unless a call site overrides them --
# same bound the one pre-existing learning hook (smith_conviction.track_record_multiplier)
# already used, so a newly-learned parameter behaves like the one that's been live since
# 2026-08-24 rather than introducing a second convention.
DEFAULT_BAND_PCT = 20
DEFAULT_N_GATE = 30


def _today(args_today=None):
    if args_today:
        return datetime.strptime(args_today, "%Y-%m-%d").date()
    return date.today()


def load_store(base_dir):
    # load_json's `default` only kicks in when truthy (`if default is not None` reads as "was
    # a default given", but None itself fails that test and falls through to raise) -- same
    # footgun documented in smith_memory.py's standalone-journal compaction pass. Pass {} and
    # test emptiness, not `default=None` + `is None`.
    raw = load_json(os.path.join(base_dir, STORE_FILENAME), default={})
    if not raw:
        # Genuinely absent (Phase 0 has just been built, or a fresh checkout) -- start from
        # the documented default shape rather than raising, same graceful-first-run contract
        # as state.json's own "first-run baseline" path in the orchestrator flow.
        return dict(DEFAULT_STORE)
    # Defensive merge: an older store missing a top-level key (schema drift) degrades to the
    # default for that key rather than KeyError-ing every reader.
    out = dict(DEFAULT_STORE)
    out.update(raw)
    return out


def write_store(base_dir, store):
    safe_write(os.path.join(base_dir, STORE_FILENAME), store)


# ---------------------------------------------------------------------------
# Observations -- the only thing ever trusted
# ---------------------------------------------------------------------------

def record_observation(base_dir, param_id, value, today=None, run_dir=None, note=None,
                        write=True):
    """Append one observation for `param_id`. `value` is whatever the measurement produced for
    THIS single instance -- e.g. a repeat_count->acted-or-not flag, a hit/miss verdict, a
    measured hit-rate delta. evaluate() decides how to aggregate a param's observations; this
    function's only job is to record one, honestly, with enough provenance to audit later.
    Never mutates or removes a prior observation -- corrections are new lessons, not edits."""
    store = load_store(base_dir)
    obs = {
        "date": str(today or date.today()),
        "param_id": param_id,
        "value": value,
        "run_dir": run_dir,
        "note": note,
    }
    store["observations"].append(obs)
    if write:
        write_store(base_dir, store)
    return obs


def add_lesson(base_dir, kind, text, evidence=None, source_run=None, supersedes=None,
               today=None, write=True):
    """kind: 'correction' | 'calibration' | 'dead_end'. This is what makes the store MEMORY
    rather than telemetry -- e.g. lesson #1 (dead_end): a strong-looking $700-vs-$360
    revealed-preference size effect that evaporated under a within-month control, so no future
    run re-derives and "fixes" the same non-effect. `supersedes` links to a prior lesson's
    index (int) when this one corrects it, so the record shows the correction without deleting
    the original mistake -- same ARCHIVE-NEVER-DELETE spirit as smith_memory's RETENTION."""
    if kind not in ("correction", "calibration", "dead_end"):
        fail(f"lesson kind must be correction|calibration|dead_end, got {kind!r}")
    store = load_store(base_dir)
    lesson = {
        "date": str(today or date.today()),
        "kind": kind,
        "text": text,
        "evidence": evidence,
        "source_run": source_run,
        "supersedes": supersedes,
    }
    store["lessons"].append(lesson)
    if write:
        write_store(base_dir, store)
    return lesson


# ---------------------------------------------------------------------------
# Parameter state machine
# ---------------------------------------------------------------------------

def evaluate(base_dir, param_id, default, aggregator, band_pct=DEFAULT_BAND_PCT,
             n_gate=DEFAULT_N_GATE, store=None):
    """Compute param_id's current derived value and state WITHOUT writing anything -- pure
    read. `aggregator(observations_for_this_param) -> (measured_value, n)` is supplied by the
    caller because different parameters aggregate differently (a mean, a hit-rate, a weighted
    tilt); this function owns only the shared gating/clamping/state-labelling logic, not the
    statistics.

    Returns a dict: {value, state, n, n_gate, measured, band_lo, band_hi, clamped}.
    `value` is what a consumer should actually use RIGHT NOW:
      - state == "default"  -> value == default, always (n below any use)
      - state == "shadow"   -> value == default STILL (computed but not voting), `measured` shown
      - state == "active"   -> value == measured, clamped into [default*(1-band), default*(1+band)]
      - state == "escalated"-> value == default (a value wanting to move beyond its band does
                                NOT get to act on its own authority) while `measured` shows what
                                it's asking for -- this is the one state a human needs to see.
    """
    if store is None:
        store = load_store(base_dir)
    obs = [o for o in store.get("observations", []) if o.get("param_id") == param_id]
    n = len(obs)
    measured, agg_n = aggregator(obs)
    # n from the aggregator wins if it differs from len(obs) -- some aggregators legitimately
    # discount observations (e.g. only scored ones count), so len(obs) is an upper bound, not
    # the authoritative n the gate should test.
    n = agg_n if agg_n is not None else n

    band_lo, band_hi = default * (1 - band_pct / 100.0), default * (1 + band_pct / 100.0)
    stored = store.get("parameters", {}).get(param_id, {})
    prior_state = stored.get("state", "default")

    if n == 0 or measured is None:
        return {"value": default, "state": "default", "n": n, "n_gate": n_gate,
                "measured": measured, "band_lo": band_lo, "band_hi": band_hi,
                "clamped": False, "prior_state": prior_state}

    if n < n_gate:
        return {"value": default, "state": "shadow", "n": n, "n_gate": n_gate,
                "measured": measured, "band_lo": band_lo, "band_hi": band_hi,
                "clamped": False, "prior_state": prior_state}

    if band_lo <= measured <= band_hi:
        return {"value": measured, "state": "active", "n": n, "n_gate": n_gate,
                "measured": measured, "band_lo": band_lo, "band_hi": band_hi,
                "clamped": False, "prior_state": prior_state}

    # Past the n-gate but wants to move beyond its band -- escalate, don't self-apply. The
    # value in USE stays default; `measured` is what a human would see if they read `learn
    # status`, which is the whole point of calling this state "escalated" rather than "denied".
    return {"value": default, "state": "escalated", "n": n, "n_gate": n_gate,
            "measured": measured, "band_lo": band_lo, "band_hi": band_hi,
            "clamped": True, "prior_state": prior_state}


def promote(base_dir, param_id, default, aggregator, band_pct=DEFAULT_BAND_PCT,
            n_gate=DEFAULT_N_GATE, today=None, run_dir=None, why=None, write=True):
    """Persist a STATE TRANSITION if evaluate()'s state differs from what's stored. This is the
    only function in this module that writes to `parameters` -- called explicitly (a pipeline
    step or a CLI call), never implicitly inside evaluate(), so a mere read can never silently
    move a parameter's recorded state. Idempotent: calling twice with the same observations
    produces no second history entry."""
    store = load_store(base_dir)
    result = evaluate(base_dir, param_id, default, aggregator, band_pct, n_gate, store=store)
    prior = store.get("parameters", {}).get(param_id, {
        "default": default, "current": default, "band_pct": band_pct, "n_gate": n_gate,
        "state": "default", "history": [],
    })
    moved = prior.get("state") != result["state"]
    if moved:
        prior["history"].append({
            "date": str(today or date.today()),
            "from": prior.get("state"), "to": result["state"],
            "n": result["n"], "why": why or f"n reached {result['n']} (gate {n_gate})",
            "run_dir": run_dir,
        })
    prior["state"] = result["state"]
    prior["current"] = result["value"]
    # `measured` persisted alongside `current` (added 2026-08-25) specifically so a later
    # `user_force_approve` can read back "what was this parameter actually asking for" without
    # re-running the aggregator -- promote() is the only place that HAS the aggregator, since
    # it's supplied per-call by whichever pipeline step owns this param_id; nothing downstream
    # (the dashboard, sync-decisions) can re-derive it generically.
    prior["measured"] = result["measured"]
    prior["n"] = result["n"]
    prior["default"] = default
    prior["band_pct"] = band_pct
    prior["n_gate"] = n_gate
    store.setdefault("parameters", {})[param_id] = prior
    if write and moved:
        write_store(base_dir, store)
    return {"param_id": param_id, "moved": moved, **result}


def user_force_approve(base_dir, param_id, today=None, run_dir=None, why=None, write=True):
    """The ONE deliberate bypass of promote()'s gate -- and it exists precisely because the
    gate is right to refuse on its own authority. `evaluate()`'s "escalated" state means a
    parameter has enough n to have an opinion but wants to move further than its bounded band
    allows; promote() will never self-apply that. This function is what a human's explicit
    approval looks like: it reads the CURRENT escalated value and writes it as `active`,
    stamping the history entry with why (defaults to a generic dashboard-approval note, but the
    interactive-dashboard sync path should always pass a real one). Added 2026-08-25 for the
    dashboard's Approve/Defer buttons on learning-parameter escalations -- Defer needs no
    function at all, since doing nothing IS deferring; only Approve is a write.

    Silently no-ops (returns None) if the parameter isn't actually in `escalated` state --
    a stale dashboard click on a parameter that has since moved (e.g. new observations pulled
    it back inside its band before the click was reconciled) must never force a value that
    isn't what the user was actually looking at when they clicked."""
    store = load_store(base_dir)
    stored = store.get("parameters", {}).get(param_id)
    if not stored or stored.get("state") != "escalated":
        return None
    from_state = stored["state"]
    stored["state"] = "active"
    stored["current"] = stored.get("measured", stored["current"])
    stored.setdefault("history", []).append({
        "date": str(today or date.today()), "from": from_state, "to": "active",
        "n": stored.get("n"), "why": why or "user-approved via dashboard", "run_dir": run_dir,
    })
    store.setdefault("parameters", {})[param_id] = stored
    if write:
        write_store(base_dir, store)
    return {"param_id": param_id, "from": from_state, "to": "active", "value": stored["current"]}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def cmd_learn_status(args):
    """Report every known parameter's state, n, and (if shadow/escalated) what it's asking
    for -- the one place to see the whole learning system's position at a glance. Does not
    evaluate anything not already registered in store['parameters'] via a prior `promote()`
    call; Phase 0 ships with an empty parameter set by design (no consumer wired yet)."""
    store = load_store(args.base_dir)
    params = store.get("parameters", {})
    rows = []
    for pid, p in sorted(params.items()):
        rows.append({
            "param_id": pid, "state": p.get("state"), "default": p.get("default"),
            "current": p.get("current"), "n": None, "n_gate": p.get("n_gate"),
            "last_moved": (p.get("history") or [{}])[-1].get("date") if p.get("history") else None,
        })
    obs = store.get("observations", [])
    by_param = {}
    for o in obs:
        by_param[o.get("param_id")] = by_param.get(o.get("param_id"), 0) + 1
    emit({
        "parameters": rows,
        "observation_counts": by_param,
        "total_observations": len(obs),
        "lessons_count": len(store.get("lessons", [])),
        "note": ("Values are DERIVED from observations on every read, never cached as "
                 "authoritative -- 'current' above reflects the last time `promote` ran, not "
                 "necessarily this instant's observation set. Run the relevant `promote` call "
                 "to refresh before trusting a state transition is current."),
    })


def cmd_learn_lessons(args):
    """List lessons, most recent first, optionally filtered by kind."""
    store = load_store(args.base_dir)
    lessons = store.get("lessons", [])
    if args.kind:
        lessons = [l for l in lessons if l.get("kind") == args.kind]
    lessons = sorted(lessons, key=lambda l: l.get("date") or "", reverse=True)
    emit({"count": len(lessons), "lessons": lessons})


def cmd_learn_add_lesson(args):
    lesson = add_lesson(args.base_dir, args.kind, args.text, evidence=args.evidence,
                        source_run=args.source_run, supersedes=args.supersedes,
                        today=args.today)
    emit({"added": lesson})


# ---------------------------------------------------------------------------
# Agent token/call/time usage -- added 2026-09-01, self-detecting efficiency audit.
# ---------------------------------------------------------------------------
# WHY THIS EXISTS: a 2026-09-01 quick sweep was manually reconstructed after the fact from six
# task-notification `usage` blocks to answer "where did the tokens go" -- the answer (one agent
# re-deriving data the orchestrator already gave it, another paying for a per-row decision whose
# outcome was already known ~100% of the time) was real and fixable, but nothing would have
# surfaced it without a human explicitly asking. This module closes that loop: every dispatched
# agent's usage is logged as an observation (same DERIVE-ON-READ-FROM-AN-APPEND-ONLY-LOG
# discipline as every other learning.json parameter -- `usage:<agent>` observations are the only
# thing trusted, nothing here caches a "this agent normally costs X" number), and usage-audit
# compares THIS run's numbers against that agent's own trailing history and flags an outlier the
# same run it happens, not on the next person who happens to read a completion notification
# closely. A flagged outlier auto-writes a `correction` lesson via add_lesson -- the same
# substrate a human would have written by hand -- so a future run (or a future orchestrator
# instance with zero memory of this one) inherits the finding via the standard `learn-lessons`
# read at MEMORY step 1, not by someone re-noticing it.
#
# AGENT_BUDGETS is deliberately sparse: only agents whose OWN .md file states an explicit
# tool-call/time target get a budget-breach check (currently smith-rebound: <=8 calls/<90s,
# per its own dispatch description). Every other agent is judged only against ITS OWN trailing
# median (n>=3 required before any flag fires) -- there is no invented universal budget, because
# a fabricated threshold would be exactly the kind of confident-wrong number this codebase's own
# standing discipline (COMPUTE-FIRST, EVIDENCE PRINCIPLE) exists to prevent.
AGENT_BUDGETS = {
    "smith-rebound": {"tool_calls": 8, "duration_s": 90},
    "smith-catalyst": {"tool_calls": 6, "duration_s": 90},
}

USAGE_TOKEN_OUTLIER_MULT = 1.5   # this run's tokens > 1.5x trailing median -> flag
USAGE_TRAILING_WINDOW = 10       # look back at most this many prior observations
USAGE_MIN_N_FOR_MEDIAN_CHECK = 3  # need at least this many prior runs before trusting a median


def cmd_usage_log(args):
    """Append one agent's this-run usage as an observation. Call once per dispatched agent,
    right after its completion notification arrives -- same moment `out_<agent>.json` gets
    written, so usage tracking piggybacks on a step the orchestrator already performs."""
    value = {"tokens": args.tokens, "tool_calls": args.tool_calls,
             "duration_s": args.duration_s, "mode": args.mode}
    obs = record_observation(args.base_dir, f"usage:{args.agent}", value,
                              today=args.today, run_dir=args.run_id,
                              note=f"mode={args.mode}")
    emit({"logged": obs})


def _usage_history(base_dir, agent, exclude_run_id=None):
    store = load_store(base_dir)
    obs = [o for o in store.get("observations", [])
           if o.get("param_id") == f"usage:{agent}"
           and (exclude_run_id is None or o.get("run_dir") != exclude_run_id)]
    obs = sorted(obs, key=lambda o: o.get("date") or "", reverse=True)[:USAGE_TRAILING_WINDOW]
    return obs


def _median(values):
    if not values:
        return None
    s = sorted(values)
    n = len(s)
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2.0


def cmd_usage_audit(args):
    """Compare THIS run's usage for one agent against its own trailing history (median tokens,
    excluding this run's own just-logged observation) and against any stated AGENT_BUDGETS
    entry. Flags -- and auto-logs a correction lesson for -- either kind of outlier. Read-mostly:
    the only write is the auto-lesson, and only when something is actually flagged."""
    history = _usage_history(args.base_dir, args.agent, exclude_run_id=args.run_id)
    prior_tokens = [h["value"]["tokens"] for h in history if h.get("value", {}).get("tokens")]
    median_tokens = _median(prior_tokens)

    flags = []
    if median_tokens is not None and len(prior_tokens) >= USAGE_MIN_N_FOR_MEDIAN_CHECK:
        ratio = args.tokens / median_tokens if median_tokens else None
        if ratio and ratio > USAGE_TOKEN_OUTLIER_MULT:
            flags.append({
                "kind": "token_outlier",
                "detail": (f"{args.agent} used {args.tokens:,} tokens this run vs a trailing "
                           f"median of {median_tokens:,.0f} over its last {len(prior_tokens)} "
                           f"runs -- {ratio:.1f}x, past the {USAGE_TOKEN_OUTLIER_MULT}x flag "
                           f"threshold."),
            })

    budget = AGENT_BUDGETS.get(args.agent)
    if budget:
        if args.tool_calls is not None and args.tool_calls > budget["tool_calls"]:
            flags.append({
                "kind": "tool_call_budget_breach",
                "detail": (f"{args.agent} used {args.tool_calls} tool calls this run vs its "
                           f"stated budget of <={budget['tool_calls']}."),
            })
        if args.duration_s is not None and args.duration_s > budget["duration_s"]:
            flags.append({
                "kind": "duration_budget_breach",
                "detail": (f"{args.agent} ran {args.duration_s:.0f}s this run vs its stated "
                           f"budget of <{budget['duration_s']}s."),
            })

    lessons_added = []
    if flags:
        detail = " ".join(f["detail"] for f in flags)
        text = (f"USAGE AUDIT (auto-logged, {args.run_id}): {detail} Investigate whether this "
                 f"run's dispatch prompt asked {args.agent} to do something outside its normal "
                 f"scope, or whether this is a recurring pattern worth a standing fix (check "
                 f"`learn-lessons --kind correction` for prior findings on this agent before "
                 f"assuming it's new).")
        lesson = add_lesson(args.base_dir, "correction", text,
                             evidence=f"usage-audit run_id={args.run_id}, agent={args.agent}, "
                                      f"tokens={args.tokens}, tool_calls={args.tool_calls}, "
                                      f"duration_s={args.duration_s}",
                             source_run=args.run_id, today=args.today)
        lessons_added.append(lesson)

    emit({"agent": args.agent, "flags": flags, "prior_n": len(prior_tokens),
          "median_tokens": median_tokens, "lessons_added": lessons_added})


# ---------------------------------------------------------------------------
# Revealed preference -- Phase 2. HONESTLY SCOPED: a steer, not a model.
# ---------------------------------------------------------------------------
# The near-miss that shapes every line below: a strong-looking size effect (acted-on median
# $700 vs ignored $360) evaporated the instant it was checked within-period instead of pooled
# across all history -- July acted $705 vs ignored $700, August $325 vs $300, i.e. no effect at
# all, the whole thing was time-confounding (see lesson kind=dead_end, source of this module's
# hard rule). SO: THIS MODULE NEVER POOLS ACROSS PERIODS. Every profile below is period-keyed
# from the start, structurally -- there is no code path that produces one flattened number
# spanning multiple months, because that code path is exactly what produced the false result.

ACTED_STATUSES = {"executed", "fulfilled", "filled"}
IGNORED_STATUSES = {"auto_retired"}
DISMISSED_STATUSES = {"dismissed_by_user"}
# A DESK withdrawal is not a revealed preference. Added 2026-08-31: `dismiss` stamped
# `dismissed_by_user` regardless of who called it, so four proposals the orchestrator withdrew
# for its own faulty evidence (P-152, P-174, P-179, P-182 -- stale relative strength, an
# evaporated over-cap leg, a self-contradicting pair, and a premise built on an unaudited name)
# were on record as the USER rejecting those ideas. This module measures what the user prefers;
# feeding it the desk's own retractions teaches it a preference the user never expressed.
DESK_WITHDRAWN_STATUSES = {"dismissed_by_desk"}
DEFERRED_STATUSES = {"deferred", "watch"}
# Deliberately excluded from every profile: "open" (outcome not yet known), "superseded"
# (a mechanical dedup merge into a restated duplicate, not a user decision about the idea),
# and "dismissed_by_desk" (the desk withdrawing its own proposal -- not a user decision at all).


def _period_key(proposal_date_str):
    """Month bucket, e.g. '2026-07'. The unit the confound was found at -- not a magic choice,
    it's literally the granularity the dead_end lesson's within-period check used."""
    d = _proposal_parse_date(proposal_date_str or "")
    return d.strftime("%Y-%m") if d else "unknown"


def _size_band(size_usd):
    if size_usd is None:
        return "unsized"
    if size_usd < 200:
        return "<$200"
    if size_usd < 500:
        return "$200-500"
    if size_usd < 1000:
        return "$500-1000"
    return "$1000+"


def compute_revealed_preference(base_dir):
    """Returns a PERIOD-KEYED report: {period: {acted, dismissed, ignored, deferred,
    engagement_rate_pct, by_trigger_type, by_direction, by_cluster, by_size_band}}. Never
    returns a pooled cross-period number -- that is the whole point of this function existing
    separately from a naive groupby. A caller wanting a single headline number must explicitly
    look at one period (e.g. the most recent complete month), never sum across the dict."""
    proposals = load_json(os.path.join(base_dir, "proposals.json"), default={}).get("proposals", [])

    def classify(p):
        st = p.get("status")
        if st in ACTED_STATUSES:
            return "acted"
        if st in IGNORED_STATUSES:
            return "ignored"
        if st in DISMISSED_STATUSES:
            return "dismissed"
        if st in DEFERRED_STATUSES:
            return "deferred"
        return None  # open/superseded/etc -- not a terminal user-facing decision, excluded

    by_period = {}
    for p in proposals:
        label = classify(p)
        if label is None:
            continue
        period = _period_key(p.get("date"))
        by_period.setdefault(period, {"acted": [], "ignored": [], "dismissed": [], "deferred": []})
        by_period[period][label].append(p)

    def profile_group(rows):
        sizes = sorted(r.get("size_usd") or 0 for r in rows)
        return {
            "n": len(rows),
            "median_size_usd": sizes[len(sizes) // 2] if sizes else None,
            "by_trigger_type": _count_by(rows, lambda r: r.get("trigger_type") or "none"),
            "by_direction": _count_by(rows, lambda r: r.get("direction_bucket") or "?"),
            "by_cluster": _count_by(rows, lambda r: r.get("cluster") or "?"),
            "by_size_band": _count_by(rows, lambda r: _size_band(r.get("size_usd"))),
        }

    report = {}
    for period, groups in sorted(by_period.items()):
        acted_n = len(groups["acted"])
        terminal_n = acted_n + len(groups["ignored"]) + len(groups["dismissed"])
        report[period] = {
            "acted": profile_group(groups["acted"]),
            "ignored": profile_group(groups["ignored"]),
            "dismissed": profile_group(groups["dismissed"]),
            "deferred": profile_group(groups["deferred"]),
            # THE headline metric this phase exists to surface -- nothing reported it before.
            "engagement_rate_pct": round(acted_n / terminal_n * 100, 1) if terminal_n else None,
            "terminal_n": terminal_n,
        }
    return report


def _count_by(rows, keyfn):
    out = {}
    for r in rows:
        k = keyfn(r)
        out[k] = out.get(k, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def cmd_learn_revealed_preference(args):
    """CLI entry: emit the period-keyed revealed-preference report. See
    compute_revealed_preference's docstring for why this never pools across periods."""
    report = compute_revealed_preference(args.base_dir)
    emit({
        "by_period": report,
        "note": ("Period-keyed by design -- do NOT sum acted/ignored/dismissed counts across "
                 "periods into one pooled figure. A pooled $700-vs-$360 size effect looked real "
                 "and was pure time-confounding (see learn-lessons, kind=dead_end): 8 of 9 "
                 "acted-on rows were from one month, 33 of 37 ignored rows from another. Compare "
                 "engagement_rate_pct WITHIN a period, or across periods as a trend -- never as "
                 "a single blended number."),
    })


# ---------------------------------------------------------------------------
# Named priority-scorer literals -- Phase 2's first shadow-parameter targets
# ---------------------------------------------------------------------------
# The priority scorer (smith_lifecycle.py cmd_proposals) has ELEVEN bare inline literals --
# +2/+3/-1 bonuses and a >55 hit-rate bar duplicated as prose at smith_lifecycle.py:935 -- with
# no named constant anywhere. This is the least principled surface in the codebase per the
# Phase-2 audit. Named here first (a prerequisite for ever calibrating them); NOT yet read from
# learning.json by the scorer itself -- these stay their hand-set defaults, exactly as today,
# until real per-signal observations accumulate past a real n_gate. Wiring evaluate()/promote()
# into the scorer without that data would let n=1 noise vote on real position sizing, which is
# the one thing the state machine exists to prevent.
PRIORITY_SCORER_DEFAULTS = {
    "priority.bonus.over_cap": 2,
    "priority.bonus.cluster_breach": 2,
    "priority.bonus.cash_short_trim": 2,
    "priority.bonus.cash_excess_buy": 2,
    "priority.bonus.stretch_or_signal_conviction": 2,
    "priority.bonus.non_conviction_live_trigger": 3,
    "priority.bonus.repeat_twice": 1,
    "priority.bonus.sell_bucket": 1,
    "priority.penalty.discretionary_no_trigger": -1,
    "priority.bar.high_min_score": 4,
    "priority.bar.medium_min_score": 2,
    "priority.gate.signal_conviction_hit_rate_pct": 55,
}


# ---------------------------------------------------------------------------
# Stop-distance calibration -- Phase 3. ESCALATES ONLY, never auto-applies.
# ---------------------------------------------------------------------------
# stop_distance_pct = max(2*ATR%, 3.0%) is CODE (smith_risk.py) implementing a PROSE rule the
# user confirmed in policy.json on 2026-07-27 ("2x the name's trailing average daily range,
# floored at 3%"). policy.json is never auto-modified (HARD RULES) -- so this calibration can
# only ever produce a PROPOSAL for the user to act on by hand, never a self-applied change.
# Deliberately does NOT route through evaluate()/promote(): those exist to gate a SPECIFIC
# proposed numeric value into shadow/active/escalated, and this function has no specific value
# to propose (see below -- the honest finding this run is "no clear signal", not a number). If
# a future run's data supports a concrete new floor, wire that through promote() with band_pct=0
# so it can only ever reach "escalated", never "active" -- never through this reporting path.
#
# What the data can and cannot show: stops_analysis.json's 140 rows carry cohort (cascade vs
# deliberate) and a verdict, but NO ATR-at-fill -- so a genuine per-volatility-TIER calibration
# (which is what "calibrate stop distance" most naturally means) is not currently computable.
# This function is honest about that rather than inventing tiers from data that doesn't exist:
# it reports cohort-level win rates, states plainly whether they diverge enough from a 50/50
# coin flip to indicate anything, and does NOT propose a specific new numeric floor unless the
# divergence is large enough to say something concrete. "No calibration change indicated" is a
# legitimate, honest output of a calibration pass, not a null result to paper over.
STOP_CALIBRATION_NEUTRAL_BAND_PP = 10.0  # win rate within 50%+/-this = "no clear signal"


def compute_stop_calibration(base_dir):
    stops = load_json(os.path.join(base_dir, "stops_analysis.json"), default={})
    overall = stops.get("overall") or {}
    by_cohort = stops.get("by_cohort") or {}

    def read(win_rate_dict):
        n = win_rate_dict.get("count")
        wr = win_rate_dict.get("win_rate_pct")
        if not n or wr is None:
            return {"n": n or 0, "win_rate_pct": wr, "signal": "insufficient data"}
        delta = wr - 50.0
        if abs(delta) <= STOP_CALIBRATION_NEUTRAL_BAND_PP:
            signal = "no clear signal (within +/-10pp of a coin flip)"
        elif delta > 0:
            signal = "leans toward TIGHTER being affordable -- stops are working better than a coin flip"
        else:
            signal = "leans toward WIDER being warranted -- stops are underperforming a coin flip"
        return {"n": n, "win_rate_pct": wr, "signal": signal}

    cohort_reads = {k: read(v) for k, v in by_cohort.items()}
    if "unknown" in cohort_reads:
        cohort_reads["unknown"]["caveat"] = (
            "unknown means fill_time_utc was missing/unparseable, not a real cascade/deliberate "
            "classification -- its win rate may reflect whatever caused the missing timestamp "
            "(older rows, a different price source) rather than a genuine cohort effect. Treat "
            "this one more cautiously than cascade/deliberate; it's data-quality-confounded.")

    return {
        "overall": read(overall),
        "by_cohort": cohort_reads,
        "current_policy": "stop_distance_pct = max(2*ATR%, 3.0%), confirmed 2026-07-27",
        "note": ("ESCALATION-ONLY finding -- policy.json's stop_loss_framework is never auto-"
                 "modified regardless of what this shows. Per-volatility-TIER calibration is "
                 "not currently possible: stops_analysis.json has no ATR-at-fill per row, only "
                 "cascade-vs-deliberate cohort. If tier-level calibration is wanted, that field "
                 "needs adding to the stop-scoring pipeline first, not estimated here."),
    }


def cmd_learn_stop_calibration(args):
    emit(compute_stop_calibration(args.base_dir))


def cmd_learn_priority_params(args):
    """Report the priority scorer's named literals and their current (still hand-set, Phase 2
    ships these observable but not yet wired) state -- the visible first step toward eventually
    calibrating them, once revealed-preference or outcome observations exist per-literal."""
    store = load_store(args.base_dir)
    rows = []
    for pid, default in PRIORITY_SCORER_DEFAULTS.items():
        stored = store.get("parameters", {}).get(pid)
        rows.append({
            "param_id": pid, "default": default,
            "state": stored.get("state", "default") if stored else "default",
            "note": ("not yet wired to learning.json -- smith_lifecycle.py still uses its "
                     "hand-set literal directly; named here so it CAN be targeted next, not "
                     "because it already is") if not stored else None,
        })
    emit({"parameters": rows,
          "note": "Phase 2 named these; a future phase wires cmd_proposals to read them via "
                  "evaluate(), once real per-signal observations exist."})
