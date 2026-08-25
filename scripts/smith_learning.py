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
    prior["default"] = default
    prior["band_pct"] = band_pct
    prior["n_gate"] = n_gate
    store.setdefault("parameters", {})[param_id] = prior
    if write and moved:
        write_store(base_dir, store)
    return {"param_id": param_id, "moved": moved, **result}


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
