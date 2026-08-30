"""Retention, archives, schema validation, and per-agent embed rendering.

Split out of smith_math.py 2026-08-16: the file had reached 4,085 lines and mixed
four unrelated domains. Shared primitives live in smith_core; smith_math keeps the
per-run compute stages, the pipeline runner and the CLI, and imports these.
"""

import hashlib
import json
import os
from datetime import date, datetime

import smith_risk
from smith_core import *  # noqa: F401,F403 -- shared constants and IO helpers
from smith_core import load_json, emit, fail
from smith_lifecycle import _proposal_parse_date  # `import *` skips underscore names


# ---------------------------------------------------------------------------
# RETENTION -- one declarative table for every memory-of-record file (2026-08-16)
# ---------------------------------------------------------------------------
# Measured on 2026-08-16: state.json had grown to 232KB, and 53.3% of it (112KB) was
# `known_gaps` -- of which 109KB was 61 CLOSED gaps. That file is read on every run and sliced
# into every sub-agent prompt, so resolved history was being paid for on every single dispatch,
# forever. proposals.json carried 72 terminal rows against 14 open ones.
#
# The striking part is that the fix already half-existed: known-gaps-archive.json,
# proposals-archive.json and exited-holdings-archive.json were all present, all sharing the same
# {schema_version, _readme, <payload>} shape -- and only journal.json had a documented prune
# rule. Three archives, one rule. So the defect is not "state.json is big", it is that RETENTION
# WAS A PER-FILE AFTERTHOUGHT instead of a policy. This table is the policy.
#
# Invariants, because this touches the memory of record:
#   * ARCHIVE, NEVER DELETE. Every evicted record lands in its archive file first; the hot file
#     shrinks only after the archive write succeeds.
#   * IDEMPOTENT. Re-running compacts nothing further and rewrites nothing.
#   * DRY RUN BY DEFAULT (same contract as `lots`); --write to apply.
#   * NEVER EVICT SOMETHING STILL LIVE -- an open gap, an open proposal, a held ticker.
#   * G72 COMPATIBILITY: archived records stay queryable. Eviction must never become the reason
#     the desk answers "no such thing" -- that is precisely the LITE failure one level up.

RETENTION = {
    "known_gaps": {
        "archive": "known-gaps-archive.json", "payload": "known_gaps",
        "keep_recent": 8,
        "why": "closed gaps are cited by ID, never re-read in full; the registry only needs the "
               "open ones plus enough recent history to avoid re-opening a just-fixed issue",
    },
    "proposals": {
        "archive": "proposals-archive.json", "payload": "proposals",
        "keep_recent": 20, "terminal_after_days": 90,
        "why": "a proposal in a terminal state (superseded/auto_retired/dismissed_by_user/"
               "executed) past the 90d scoring window can never change again",
    },
    "thesis": {
        "archive": "exited-holdings-archive.json", "payload": "thesis",
        "why": "a thesis for a name no longer held is history, not context -- the dashboard "
               "already filters these out, so they were pure prompt weight",
    },
    "sector_map": {
        "archive": "exited-holdings-archive.json", "payload": "sector_map",
        "why": "same as thesis; keep it in step so the two never disagree about which "
               "tickers exist",
    },
}

# STANDALONE JOURNAL FILES (added 2026-08-25, self-learning Phase 0). journal.json,
# trigger_journal.json, derisk_journal.json and the new learning.json were never in RETENTION
# at all -- unmanaged since the day each was created, unlike everything above which lives
# nested inside state.json. All four share a compatible shape (a top-level `entries` list, each
# row carrying `date`/`ticker`/`scored`), so one generic eviction pass in cmd_compact (below)
# handles all of them rather than four bespoke ones. A row is only eligible once `scored` is
# true -- an unscored row is still live work, never evicted regardless of age, same
# NEVER-EVICT-SOMETHING-STILL-LIVE invariant as everything else in this table.
STANDALONE_JOURNAL_RETENTION = {
    "journal.json": {
        "archive": "journal-archive.json", "payload": "entries",
        "keep_recent": 60, "terminal_after_days": 365,
        "why": "a 30d-scored signal entry a year old has nothing left to teach a live decision; "
               "bucket_hit_rates/name_bucket_grades are recomputed from what remains, not archived",
    },
    "trigger_journal.json": {
        "archive": "trigger-journal-archive.json", "payload": "entries",
        "keep_recent": 60, "terminal_after_days": 365,
        "why": "shadow-trigger observations past their scoring window and past a year of "
               "relevance to the shadow->live promotion decision",
    },
    "derisk_journal.json": {
        "archive": "derisk-journal-archive.json", "payload": "entries",
        "keep_recent": 60, "terminal_after_days": 365,
        "why": "same as trigger_journal -- the composite queue's own shadow-scoring log",
    },
    "learning.json": {
        "archive": "learning-archive.json", "payload": "observations",
        "keep_recent": 500, "terminal_after_days": 730,
        "why": "learning.json's observations are the source parameters are DERIVED from on "
               "every read (never pinned) -- kept generously long since pruning them changes "
               "what a parameter's current value computes to, unlike the other three journals "
               "where old scored rows are purely historical record",
    },
}

TERMINAL_PROPOSAL_STATUSES = ("superseded", "auto_retired", "dismissed_by_user",
                              "executed", "fulfilled", "filled")

def _archive_load(path):
    d = load_json(path, default=None)
    if not isinstance(d, dict):
        d = {"schema_version": 1,
             "_readme": "Archived records evicted from the hot file by `smith_math.py compact`. "
                        "Full history lives HERE; the hot file keeps only what a run needs. "
                        "Nothing is ever deleted -- if you are looking for something that "
                        "vanished from state.json, it is in this file."}
    return d

def _archive_merge(arc, payload_key, records):
    """Merge into the archive without duplicating. Dict payloads merge by key; list payloads
    de-duplicate on a stable identity so a re-run cannot double-append."""
    cur = arc.get(payload_key)
    if isinstance(records, dict):
        cur = cur if isinstance(cur, dict) else {}
        cur.update(records)
    else:
        cur = cur if isinstance(cur, list) else []
        def ident(r):
            if not isinstance(r, dict):
                return json.dumps(r, sort_keys=True)
            return r.get("id") or r.get("gap_id") or json.dumps(r, sort_keys=True)
        seen = {ident(r) for r in cur}
        cur.extend(r for r in records if ident(r) not in seen)
    arc[payload_key] = cur
    return arc

# _safe_write used to be defined here; promoted to smith_core.safe_write 2026-08-25 so every
# module can reach it via the `from smith_core import *` they already do, instead of each
# needing a one-off cross-module import. Kept as a thin alias so existing call sites in this
# file (and anything external still spelling the old private name) keep working unchanged.
_safe_write = safe_write

def cmd_compact(args):
    """Enforce RETENTION across every memory-of-record file. Dry run unless --write."""
    base = args.base_dir
    today = datetime.strptime(args.today, "%Y-%m-%d").date() if args.today else date.today()
    state = load_json(os.path.join(base, "state.json"), default={})
    before = len(json.dumps(state))
    moves, writes = [], {}

    held = set()
    if args.holdings:
        h = load_json(args.holdings, default={})
        held = {r.get("ticker") for r in (h.get("holdings_inr") or []) if r.get("ticker")}
    if not held:
        held = {r.get("ticker") for r in (state.get("holdings") or []) if r.get("ticker")}

    # --- known_gaps: keep open + N most recent closed -----------------------
    cfg = RETENTION["known_gaps"]
    gaps = state.get("known_gaps") or []
    live = [g for g in gaps if (g.get("status") or "open") not in ("closed",)]
    closed = [g for g in gaps if (g.get("status") or "open") == "closed"]
    closed.sort(key=lambda g: g.get("resolved_on") or g.get("closed") or "", reverse=True)
    keep_closed, evict = closed[:cfg["keep_recent"]], closed[cfg["keep_recent"]:]
    if evict:
        moves.append({"file": "state.known_gaps", "moved": len(evict),
                      "to": cfg["archive"], "kept_live": len(live),
                      "kept_recent_closed": len(keep_closed),
                      "ids": [g.get("id") for g in evict][:12], "why": cfg["why"]})
        state["known_gaps"] = live + keep_closed
        writes.setdefault(cfg["archive"], _archive_load(os.path.join(base, cfg["archive"])))
        _archive_merge(writes[cfg["archive"]], cfg["payload"], evict)

    # --- thesis + sector_map: evict names no longer held ---------------------
    if held:
        for key in ("thesis", "sector_map"):
            cfg = RETENTION[key]
            m = state.get(key) or {}
            gone = {t: v for t, v in m.items() if t not in held}
            if gone:
                moves.append({"file": f"state.{key}", "moved": len(gone),
                              "to": cfg["archive"], "kept": len(m) - len(gone),
                              "ids": sorted(gone)[:12], "why": cfg["why"]})
                state[key] = {t: v for t, v in m.items() if t in held}
                writes.setdefault(cfg["archive"],
                                  _archive_load(os.path.join(base, cfg["archive"])))
                _archive_merge(writes[cfg["archive"]], cfg["payload"], gone)

    # --- proposals: evict terminal rows past the scoring window --------------
    cfg = RETENTION["proposals"]
    p_path = os.path.join(base, "proposals.json")
    praw = load_json(p_path, default=None)
    p_rows = (praw.get("proposals") if isinstance(praw, dict) else praw) or []
    def _age(r):
        d = _proposal_parse_date(r.get("date", "") or "")
        return (today - d).days if d else None
    terminal = [r for r in p_rows
                if r.get("status") in TERMINAL_PROPOSAL_STATUSES
                and (_age(r) or 0) > cfg["terminal_after_days"]]
    terminal.sort(key=lambda r: r.get("date") or "", reverse=True)
    p_evict = terminal[cfg["keep_recent"]:]
    if p_evict:
        ev_ids = {id(r) for r in p_evict}
        moves.append({"file": "proposals.json", "moved": len(p_evict), "to": cfg["archive"],
                      "kept": len(p_rows) - len(p_evict),
                      "ids": [r.get("id") for r in p_evict][:12], "why": cfg["why"]})
        kept = [r for r in p_rows if id(r) not in ev_ids]
        writes.setdefault(cfg["archive"], _archive_load(os.path.join(base, cfg["archive"])))
        _archive_merge(writes[cfg["archive"]], cfg["payload"], p_evict)
        writes["__proposals__"] = ({"proposals": kept} if isinstance(praw, dict) else kept)
        if isinstance(praw, dict):
            merged = dict(praw); merged["proposals"] = kept
            writes["__proposals__"] = merged

    # --- standalone journals: evict scored rows past keep_recent/terminal_after_days ---------
    # Generic because all four files share one shape (entries[], each row carrying date/
    # ticker/scored) -- see STANDALONE_JOURNAL_RETENTION above for why these were unmanaged
    # until now. `journal_writes` is kept separate from `writes` (which is keyed by archive
    # filename for the state.json-nested passes above) because these hot files are NOT
    # state.json sub-keys -- they are top-level files in their own right and need their own
    # read-modify-write, not a merge into `state`.
    journal_writes = {}
    for fname, cfg in STANDALONE_JOURNAL_RETENTION.items():
        fpath = os.path.join(base, fname)
        # load_json's `default` param only kicks in when truthy (`if default is not None`
        # reads as "was a default given", but `None` itself fails that test and falls through
        # to raise) -- pass {} so a missing file (learning.json doesn't exist until Phase 0's
        # smith_learning.py creates it) degrades to "nothing to compact" instead of a crash.
        raw = load_json(fpath, default={})
        if not raw:
            continue
        rows = raw.get(cfg["payload"]) or []
        if not rows:
            continue
        def _row_age(r):
            d = _proposal_parse_date(r.get("date", "") or "")
            return (today - d).days if d else None
        scored_rows = [r for r in rows if r.get("scored")]
        eligible = [r for r in scored_rows if (_row_age(r) or 0) > cfg["terminal_after_days"]]
        eligible.sort(key=lambda r: r.get("date") or "", reverse=True)
        evict = eligible[cfg["keep_recent"]:]
        if not evict:
            continue
        evict_ids = {id(r) for r in evict}
        kept_rows = [r for r in rows if id(r) not in evict_ids]
        moves.append({"file": fname, "moved": len(evict), "to": cfg["archive"],
                      "kept": len(kept_rows), "why": cfg["why"]})
        arc = _archive_load(os.path.join(base, cfg["archive"]))
        _archive_merge(arc, cfg["payload"], evict)
        journal_writes[cfg["archive"]] = arc
        # kept_rows already includes every unscored row (never eligible) plus every scored row
        # that didn't make the eviction list -- unscored_rows above is used only to decide
        # eligibility, not re-assembled here.
        merged = dict(raw); merged[cfg["payload"]] = kept_rows
        journal_writes[fname] = merged

    after = len(json.dumps(state))
    out = {"dry_run": not args.write, "moves": moves,
           "state_bytes_before": before, "state_bytes_after": after,
           "state_bytes_freed": before - after,
           "state_pct_freed": round((before - after) / before * 100, 1) if before else 0,
           "note": ("ARCHIVE, NEVER DELETE -- every evicted record is written to its archive "
                    "file before the hot file shrinks, and archives stay queryable. Re-running "
                    "is a no-op.")}
    if not moves:
        out["note"] = "already compact -- nothing met an eviction rule (this command is idempotent)"
    if args.write and moves:
        for path, payload in writes.items():
            if path == "__proposals__":
                _safe_write(os.path.join(base, "proposals.json"), payload)
            else:
                _safe_write(os.path.join(base, path), payload)
        for path, payload in journal_writes.items():
            _safe_write(os.path.join(base, path), payload)
        _safe_write(os.path.join(base, "state.json"), state)
        out["written"] = True
    emit(out)

def cmd_gaps(args):
    """Look up known_gaps across BOTH the hot registry and the archive (added 2026-08-16).

    This exists because `compact` evicts resolved gaps out of state.json, and an eviction that
    made a record unfindable would recreate G72 exactly one level up: the desk told the user LITE
    was "never held" because it consulted a file that could not represent the answer. Archiving
    is only safe if the archive is queryable, so this command is a REQUIRED companion to compact,
    not a convenience. Search by ID, by status, or by free text across both files.
    """
    base = args.base_dir
    hot = (load_json(os.path.join(base, "state.json"), default={}) or {}).get("known_gaps") or []
    arc = (load_json(os.path.join(base, "known-gaps-archive.json"), default={}) or {}).get("known_gaps") or []
    rows = [dict(g, _where="state.json") for g in hot] + [dict(g, _where="archive") for g in arc]

    q = (args.id or args.query or "").strip().lower()
    if args.id:
        hits = [g for g in rows if (g.get("id") or "").lower() == q]
    elif args.query:
        hits = [g for g in rows
                if q in json.dumps({k: v for k, v in g.items() if k != "_where"}).lower()]
    else:
        hits = [g for g in rows if smith_risk.gap_is_live(g)] if args.open_only else rows

    hits.sort(key=lambda g: (g.get("id") or ""))
    emit({"searched": {"hot": len(hot), "archived": len(arc), "total": len(rows)},
          "matched": len(hits),
          "gaps": [{"id": g.get("id"), "status": g.get("status") or "open",
                    "where": g["_where"], "opened": g.get("opened"),
                    "resolved_on": g.get("resolved_on"),
                    "gap": (g.get("gap") or g.get("description") or "")[:400],
                    "resolution": (g.get("resolution") or "")[:400]} for g in hits],
          "note": ("Searches BOTH state.json and known-gaps-archive.json. A gap missing from "
                   "state.json is ARCHIVED, never deleted -- absence here, and only here, is "
                   "evidence a gap never existed.")})

# ---------------------------------------------------------------------------
# drift
# ---------------------------------------------------------------------------
def validate_policy(policy):
    """Structural checks on policy.json. Returns a list of defect strings (empty == clean).

    Exists because the draft carried an arithmetically impossible target set from 2026-07-12 to
    2026-07-25 (targets summed to 105% alongside a 3-15% cash band) and nothing caught it -- every
    drift table in that window was measured against an unsatisfiable spec. These checks make that
    class of defect loud instead of silent.
    """
    defects = []
    targets = policy.get("cluster_targets", {})
    if not targets:
        return ["cluster_targets missing or empty -- no drift analysis possible"]

    tsum = sum(t.get("target_pct", 0) for t in targets.values())
    denom = policy.get("cluster_target_denominator")
    if denom not in ("invested_equity", "total_book"):
        defects.append(
            "cluster_target_denominator is not declared (expected 'invested_equity' or 'total_book'). "
            "Cluster percentages and cash percentage are then computed against different bases and are "
            "not comparable -- this is how the 105%-sum defect went unnoticed."
        )

    # Targets must sum to 100 of whatever base they are declared against, except that a
    # total_book basis must leave room for the cash target.
    if denom == "total_book":
        cash_band = policy.get("cash_band_pct") or [0, 0]
        cash_mid = (cash_band[0] + cash_band[1]) / 2 if None not in cash_band else 0
        expected = 100 - cash_mid
        if abs(tsum - expected) > 1.0:
            defects.append(
                f"cluster targets sum to {tsum:g}% but denominator is total_book with a cash band of "
                f"{cash_band} -- targets plus cash must total 100%, so targets should sum to about "
                f"{expected:g}%. Off by {tsum - expected:+.1f}pt."
            )
    else:
        if abs(tsum - 100) > 1.0:
            defects.append(
                f"cluster targets sum to {tsum:g}%, not 100%. Off by {tsum - 100:+.1f}pt. "
                f"Drift is measured against an unsatisfiable target set."
            )

    # Bands must be jointly satisfiable: you cannot honour every floor if the floors sum past 100,
    # and you cannot reach 100 if every ceiling together falls short.
    lo_sum = sum((t.get("band_pct") or [0, 0])[0] or 0 for t in targets.values())
    hi_sum = sum((t.get("band_pct") or [0, 0])[1] or 0 for t in targets.values())
    if lo_sum > 100:
        defects.append(f"band floors sum to {lo_sum:g}% (>100%) -- no allocation can satisfy every floor at once.")
    if hi_sum < 100:
        defects.append(f"band ceilings sum to {hi_sum:g}% (<100%) -- no allocation can reach 100% within every ceiling.")

    for name, t in targets.items():
        band = t.get("band_pct") or [None, None]
        tgt = t.get("target_pct")
        if None in band or tgt is None:
            defects.append(f"'{name}': target_pct or band_pct missing.")
            continue
        if band[0] > band[1]:
            defects.append(f"'{name}': band {band} is inverted (floor > ceiling).")
        if not (band[0] <= tgt <= band[1]):
            defects.append(f"'{name}': target {tgt:g}% sits outside its own band {band}.")

    if policy.get("max_ai_capex_factor_pct") is not None and \
            policy.get("ai_capex_denominator") not in ("invested_equity", "total_book"):
        defects.append(
            "max_ai_capex_factor_pct is set but ai_capex_denominator is not declared. This single choice "
            "flips the headline: on 2026-07-24 the book was 100% of equity (breach) but 86.3% of total "
            "book (no breach) against the same 90% cap."
        )

    unknown = [c for c in policy.get("ai_capex_clusters", []) if c not in targets]
    if unknown:
        defects.append(f"ai_capex_clusters names clusters with no target defined: {unknown}")

    return defects

def validate_cache_events(state):
    """Check that any future-dated event in caches (FOMC date, etc.) hasn't already passed.
    FIXED 1.7: 2026-07-26 — cache payload validation to prevent stale event dates.
    Returns list of defects.
    """
    defects = []
    today = date.today()
    fomc_cache = state.get("fomc_cache", {})
    if fomc_cache:
        # fomc_cache should have a next_date or similar field; if it's a future date, flag if it's past
        next_check = fomc_cache.get("next_check_date")
        if next_check:
            try:
                check_date = datetime.strptime(next_check, "%Y-%m-%d").date()
                if check_date < today:
                    defects.append(f"fomc_cache.next_check_date {next_check} is in the past; cache is stale and should be refreshed")
            except (ValueError, TypeError):
                pass
    return defects

def validate_thesis_schema(state, base_dir="."):
    """Guard the thesis map's shape at the validation boundary (added 2026-08-16).

    All 42 entries were migrated to the evidence-object schema on 2026-08-16, so a bare string
    reappearing means something wrote the legacy shape back -- most likely a sub-agent tail
    merged verbatim, or a hand-edit. That is worth catching immediately rather than discovering
    it the next time a reader silently degrades: before consolidation, a legacy string with no
    pipe parsed its entire prose as a "status", which matched nothing and quietly exempted the
    name from every thesis gate in cmd_rotation, cmd_derisk and cmd_triggers.

    Also enforces the G58 contract that BOTH evidence arrays are present. An empty side must be
    an explicit [] -- a missing key is a schema violation, not a stylistic one.
    """
    defects = []
    thesis = state.get("thesis") or {}
    legacy = sorted(t for t, v in thesis.items() if smith_risk.is_legacy_thesis(v))
    if legacy:
        defects.append(
            f"THESIS SCHEMA REGRESSION: {len(legacy)} entry(ies) are legacy bare strings again "
            f"({', '.join(legacy[:8])}{' ...' if len(legacy) > 8 else ''}). Every entry was "
            f"migrated to the evidence-object schema on 2026-08-16. Re-run the migration via "
            f"smith_risk.normalize_thesis_entry rather than hand-patching, and check whichever "
            f"writer reintroduced the string shape.")
    missing = sorted(t for t, v in thesis.items()
                     if isinstance(v, dict)
                     and ("evidence_for" not in v or "evidence_against" not in v))
    if missing:
        defects.append(
            f"THESIS EVIDENCE SCHEMA: {len(missing)} entry(ies) are missing an evidence array "
            f"({', '.join(missing[:8])}{' ...' if len(missing) > 8 else ''}). Both sides are "
            f"mandatory (G58); an empty side is an explicit [] plus a note, never an omitted key.")
    # Generic sweep: any per-ticker namespace holding two value shapes is the same defect one
    # level up. thesis was the instance that shipped; this catches the next one in any namespace.
    dc = state.get("data_cache") or {}
    for mapping, nm, want in (
            (state.get("thesis"), "state.thesis", dict),
            (state.get("sector_map"), "state.sector_map", str),
            (state.get("peer_map"), "state.peer_map", dict),
            (state.get("signal_history"), "state.signal_history", list),
            (state.get("signal_history_as_of"), "state.signal_history_as_of", str),
            (state.get("diversifier_candidates"), "state.diversifier_candidates", dict),
            (dc.get("betas"), "data_cache.betas", dict),
            (dc.get("ticker_map"), "data_cache.ticker_map", str),
            (dc.get("earnings_calendar"), "data_cache.earnings_calendar", dict),
            (dc.get("earnings_facts"), "data_cache.earnings_facts", dict)):
        defects.extend(smith_risk.mixed_shape_defects(mapping, nm, want))

    # known_gaps statuses -- same vocabulary defect as thesis, found 2026-08-16: 9 records stored
    # a resolution narrative in `status`, so nine long-closed gaps read as open and one genuinely
    # open one (G22) stayed invisible for 3.5 weeks.
    for src, label in ((state.get("known_gaps") or [], "state.known_gaps"),
                       ((load_json(os.path.join(base_dir, "known-gaps-archive.json"),
                                   default={}) or {}).get("known_gaps") or [],
                        "known-gaps-archive.json")):
        bad = sorted(str(g.get("id")) for g in src if smith_risk.gap_status(g) is None)
        if bad:
            defects.append(
                f"UNREADABLE GAP STATUS in {label} on {len(bad)} record(s) ({', '.join(bad[:8])}) "
                f"-- not one of {smith_risk.KNOWN_GAP_STATUSES}. These sort as live by the safe "
                f"default, but they cannot be reported on accurately; put the narrative in "
                f"`resolution` and set a real status.")

    unknown = sorted(t for t, v in thesis.items()
                     if v and smith_risk.thesis_status(v) is None)
    if unknown:
        defects.append(
            f"THESIS STATUS UNREADABLE on {len(unknown)} entry(ies) ({', '.join(unknown[:8])}) -- "
            f"status is not one of {smith_risk.KNOWN_STATUSES}. These names fall through every "
            f"thesis gate silently; they are not blocked, they are simply never considered.")
    return defects

def validate_learning_schema(base_dir):
    """Guard learning.json's shape (added 2026-08-25, self-learning Phase 0). Absent entirely is
    fine (first run, or the feature simply unused yet) -- only checks shape once the file exists,
    same "missing is not a defect, malformed is" contract as the rest of this validator."""
    defects = []
    path = os.path.join(base_dir, "learning.json")
    if not os.path.exists(path):
        return defects
    store = load_json(path, default={})
    for key, want in (("observations", list), ("parameters", dict), ("lessons", list)):
        if key in store and not isinstance(store[key], want):
            defects.append(f"LEARNING SCHEMA: learning.json's '{key}' is "
                           f"{type(store[key]).__name__}, expected {want.__name__}.")
    for o in store.get("observations", []) if isinstance(store.get("observations"), list) else []:
        if not isinstance(o, dict) or "param_id" not in o or "date" not in o:
            defects.append("LEARNING SCHEMA: an observation is missing 'param_id' or 'date' -- "
                           "every observation must be attributable to a parameter and dated, or "
                           "evaluate()'s aggregation and any future audit cannot trust it.")
            break
    for kind_defect_pid, p in (store.get("parameters") or {}).items():
        if p.get("state") not in (None, "default", "shadow", "active", "escalated"):
            defects.append(f"LEARNING SCHEMA: parameter '{kind_defect_pid}' has state "
                           f"{p.get('state')!r}, not one of default/shadow/active/escalated.")
        if "default" not in p:
            defects.append(f"LEARNING SCHEMA: parameter '{kind_defect_pid}' has no 'default' -- "
                           "every learned parameter must keep its hand-set original recoverable.")
    for l in store.get("lessons", []) if isinstance(store.get("lessons"), list) else []:
        if not isinstance(l, dict) or l.get("kind") not in ("correction", "calibration", "dead_end"):
            defects.append("LEARNING SCHEMA: a lesson has an unrecognised or missing 'kind' -- "
                           "must be correction|calibration|dead_end.")
            break
    return defects

def validate_proposals_schema(base_dir):
    """Guard proposals.json's `action` field shape (added 2026-08-29, same-day incident).

    The dashboard renders `action` verbatim as the row's human-readable label (e.g. "Sell
    ASML"), separately from the machine-readable `ticker`/`direction_bucket` fields the
    lifecycle logic actually keys off. On 2026-08-29 a hand-written batch of 7 proposals set
    `action` to a bare direction word ("SELL", "BUY", "TRIM") instead of a verb+ticker
    sentence -- internally harmless (direction/ticker still parsed fine from the separate
    fields), but the dashboard rendered "SELL SELL" / "BUY BUY" / "TRIM TRIM" because the
    ticker was never actually in the label. The user caught it, not the system.

    The check: `action` must not equal a bare direction keyword once whitespace-stripped, and
    if `ticker` is set, it must appear as a substring of `action` (case-insensitive) -- the
    same contract `_proposal_infer_ticker` already assumes when it back-derives a ticker from
    action text. This is a *rendering* contract validated at the schema boundary, exactly the
    class of thing the thesis/known_gaps checks above already do for their own fields.
    """
    defects = []
    path = os.path.join(base_dir, "proposals.json")
    if not os.path.exists(path):
        return defects
    proposals = load_json(path, default={})
    props = proposals.get("proposals", []) if isinstance(proposals, dict) else proposals
    bare_direction_words = {"BUY", "SELL", "TRIM", "HOLD", "ADD", "EXIT", "REDUCE", "REBUILD"}
    bad_bare = []
    bad_no_ticker_in_label = []
    bad_bucket = []
    bad_size = []
    no_ticker = []
    for pr in props:
        if pr.get("status") not in ("open", "accepted_by_user"):
            # terminal/historical rows are never re-rendered as a live row's label; don't
            # force a schema fix on history that will never be displayed this way again.
            continue
        pid = pr.get("id", "?")
        action = (pr.get("action") or "").strip()
        ticker = pr.get("ticker")
        bucket = pr.get("direction_bucket")
        if action.upper() in bare_direction_words:
            bad_bare.append(pid)
        elif ticker and ticker.upper() not in action.upper():
            bad_no_ticker_in_label.append(pid)
        # a HOLD-bucket proposal is legitimately allowed to be portfolio-level/multi-ticker
        # (e.g. "Rebuild cash buffer", "Hold fire on ... (CLS/BE/NBIS/MRVL)") -- only a
        # single-instrument BUY/SELL/TRIM is required to name its ticker.
        if not ticker and bucket in ("BUY", "SELL", "TRIM"):
            no_ticker.append(pid)
        if bucket is not None and bucket not in ("BUY", "TRIM", "SELL", "HOLD"):
            bad_bucket.append(pid)
        size = pr.get("size_usd")
        if size is not None and not isinstance(size, (int, float)):
            bad_size.append(pid)
    if bad_bare:
        defects.append(
            f"PROPOSAL ACTION SCHEMA: {len(bad_bare)} open proposal(s) have a bare direction "
            f"word as `action` instead of a verb+ticker sentence ({', '.join(bad_bare[:10])}"
            f"{' ...' if len(bad_bare) > 10 else ''}) -- the dashboard renders `action` "
            f"verbatim as the row label and will show e.g. \"SELL SELL\". Use `add-proposal` "
            f"or set action to \"Sell TICKER\"/\"Buy TICKER\"/\"Trim TICKER\".")
    if bad_no_ticker_in_label:
        defects.append(
            f"PROPOSAL ACTION SCHEMA: {len(bad_no_ticker_in_label)} proposal(s) have a "
            f"`ticker` that does not appear in their `action` label ({', '.join(bad_no_ticker_in_label[:10])}"
            f"{' ...' if len(bad_no_ticker_in_label) > 10 else ''}) -- the label will not name "
            f"the instrument it's about.")
    if no_ticker:
        defects.append(
            f"PROPOSAL SCHEMA: {len(no_ticker)} open proposal(s) have no `ticker` field at all "
            f"({', '.join(no_ticker[:10])}{' ...' if len(no_ticker) > 10 else ''}) -- every "
            f"downstream check (void-on-exit, dedup, retirement) that keys off ticker silently "
            f"skips these.")
    if bad_bucket:
        defects.append(
            f"PROPOSAL SCHEMA: {len(bad_bucket)} proposal(s) have a `direction_bucket` that "
            f"isn't one of BUY/TRIM/SELL/HOLD ({', '.join(bad_bucket[:10])}).")
    if bad_size:
        defects.append(
            f"PROPOSAL SCHEMA: {len(bad_size)} proposal(s) have a non-numeric `size_usd` "
            f"({', '.join(bad_size[:10])}).")
    return defects


def validate_policy_narrative_drift(base_dir):
    """Guard against a number quoted in narrative prose drifting from the number policy.json
    actually holds (added 2026-08-29, same-day incident). On 2026-08-29 four consecutive
    ledger.csv rows asserted a drawdown "8% warn line" -- there is no such threshold anywhere
    in policy.json (drawdown_warn_pct is 15). The phantom number was typed once, then copied
    forward run over run, and both the strategist and the orchestrator repeated it in the same
    session without either checking policy.json. This check can't catch every possible prose
    drift, but it catches the recurring, high-stakes one: any narrative claiming a drawdown
    warn/risk-off percentage that doesn't match policy.json's actual thresholds.
    """
    defects = []
    policy = load_json(os.path.join(base_dir, "policy.json"), default=None)
    if not policy:
        return defects
    warn_pct = policy.get("drawdown_warn_pct")
    risk_off_pct = policy.get("drawdown_risk_off_pct")
    ledger_path = os.path.join(base_dir, "ledger.csv")
    if not os.path.exists(ledger_path) or warn_pct is None:
        return defects
    import csv as _csv
    import re as _re
    pat = _re.compile(r"(-?\d+(?:\.\d+)?)\s*%\s*warn\s*(?:line|threshold)?", _re.IGNORECASE)
    with open(ledger_path, newline="") as f:
        rows = list(_csv.reader(f))
    # only check the MOST RECENT row -- this is a drift-detector for "did the run that just
    # finished repeat the error", not an archaeology project. Older rows are permanent record
    # (never rewritten); a historical mistake belongs in known_gaps, not in a check that
    # blocks every future run from reading clean once the record moves on.
    for row in rows[-1:]:
        if not row:
            continue
        notes = row[-1] if len(row) else ""
        if "CORRECTION" in notes.upper():
            # a row that already narrates its own correction (see G84) is not a fresh drift --
            # it's the record of having caught one. Don't re-flag the phrase inside the fix.
            continue
        for m in pat.finditer(notes):
            claimed = float(m.group(1))
            if abs(claimed) != abs(warn_pct):
                defects.append(
                    f"NARRATIVE/POLICY DRIFT: ledger.csv row (ts={row[0] if row else '?'}) "
                    f"claims a {claimed}% drawdown warn line, but policy.json's "
                    f"drawdown_warn_pct is {warn_pct}. A narrative number that isn't read from "
                    f"policy.json will drift silently -- state the threshold from policy.json "
                    f"directly in future briefings, never retype it.")
                break  # one defect per row is enough signal
    return defects


LEDGER_HEADER = ["ts", "mode", "value_usd", "usdinr", "wallet_usd", "spx", "ndx", "smh",
                  "smh_asof", "est_net_flows_usd", "external_flow_usd", "value_trust", "notes"]
LEDGER_SUMMARY_MAX_CHARS = 300


def cmd_append_ledger(args):
    """The only sanctioned way to append a ledger.csv row (added 2026-08-29, same-day
    incident). Before this command existed, a run's whole narrative -- often 3,000-4,000
    characters -- was hand-typed directly into the `notes` cell. That is precisely the medium
    a fact drifts in: on 2026-08-29 a nonexistent "8% drawdown warn line" (policy.json's real
    threshold is 15%) was typed once into a notes blob, then effectively copied forward by the
    next run reading the previous one's narrative as context, across four consecutive rows,
    before anyone checked it against policy.json.

    This command enforces a hard split: `--summary` is a SHORT one-liner (capped at
    LEDGER_SUMMARY_MAX_CHARS, refused if longer) that goes into the CSV `notes` cell -- short
    enough to skim, short enough that `validate_policy_narrative_drift` can actually check it.
    The full run narrative goes to `--briefing-file` (a path under runs/<ts>/, written by the
    orchestrator BEFORE calling this command), and the CSV cell carries only a pointer to it.
    Long-form narrative still exists and is still readable -- it just isn't the thing every
    future run re-ingests as compressed "context," which is how a single typo becomes a
    standing belief.

    Skipped entirely on a weekend/holiday mini-briefing (no ledger row at all) per the
    existing HOLIDAY CALENDAR CHECK rule -- this command does not change when a row is
    written, only what a row is allowed to contain.
    """
    if len(args.summary) > LEDGER_SUMMARY_MAX_CHARS:
        fail(f"--summary is {len(args.summary)} chars, over the {LEDGER_SUMMARY_MAX_CHARS}-char "
             f"cap -- put the full narrative in --briefing-file and shorten the summary to a "
             f"skimmable one-liner (this is the enforcement mechanism, not a style suggestion: "
             f"a 4,000-char notes blob is exactly how the 2026-08-29 phantom-8%-warn-line "
             f"incident propagated unnoticed for four runs).")
    briefing_path = args.briefing_file
    if briefing_path and not os.path.exists(briefing_path):
        fail(f"--briefing-file {briefing_path!r} does not exist -- write the full narrative "
             f"there before calling append-ledger, so the pointer this command stores is real.")
    notes = args.summary
    if briefing_path:
        rel = os.path.relpath(briefing_path, args.base_dir)
        notes = f"{notes} [full: {rel}]"

    import csv
    ledger_path = os.path.join(args.base_dir, "ledger.csv")
    is_new = not os.path.exists(ledger_path)
    row = [args.ts, args.mode, args.value_usd, args.usdinr, args.wallet_usd, args.spx,
           args.ndx, args.smh or "", args.smh_asof or "", args.est_net_flows_usd or "",
           args.external_flow_usd or "", args.value_trust, notes]
    with open(ledger_path, "a", newline="") as f:
        w = csv.writer(f)
        if is_new:
            w.writerow(LEDGER_HEADER)
        w.writerow(row)
    emit({"appended": True, "ts": args.ts, "notes_chars": len(notes),
          "briefing_file": briefing_path})


def _load_agent_tail(path):
    """Read a Stage-1 agent's out_<agent>.json file, which per SKILL.md's own STAGE 1 contract
    ("returns a prose summary PLUS its fenced JSON tail verbatim") is often prose text ending
    in a ```json fenced block, not pure JSON. Tries a straight json.load first (some agents do
    write pure JSON); on failure, extracts the LAST fenced ```json ... ``` or ``` ... ``` block
    in the file and parses that. Raises the original JSONDecodeError, unmodified, if neither
    works -- a merge-tails caller should see a real parse failure, not a silently empty merge.
    """
    with open(path) as f:
        text = f.read()
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        import re as _re
        blocks = _re.findall(r"```(?:json)?\s*\n(.*?)\n```", text, _re.DOTALL)
        if blocks:
            try:
                return json.loads(blocks[-1])
            except json.JSONDecodeError:
                pass
        raise e


def _merge_thesis(out, state, today):
    changed = out.get("thesis", {}).get("changed", {})
    for tk, entry in changed.items():
        if "evidence_for" not in entry or "evidence_against" not in entry:
            entry.setdefault("evidence_for", [])
            entry.setdefault("evidence_against", [])
            entry.setdefault("verified", "unverified")
        state["thesis"][tk] = entry
    sm_changed = out.get("sector_map", {}).get("changed", {})
    state.setdefault("sector_map", {}).update(sm_changed)
    for tk, fact in out.get("earnings_facts", {}).items():
        state["data_cache"].setdefault("earnings_facts", {})[tk] = fact
    return {"thesis_changed": list(changed), "sector_map_changed": list(sm_changed)}


def _merge_signals(out, state, today, scanned_tickers=None):
    changed = out.get("signal_history", {}).get("changed", {})
    state.setdefault("signal_history", {}).update(changed)
    stamp_tickers = set(changed) | set(scanned_tickers or [])
    state.setdefault("signal_history_as_of", {})
    for tk in stamp_tickers:
        state["signal_history_as_of"][tk] = today
    return {"signal_history_changed": list(changed), "stamped": len(stamp_tickers)}


def _merge_catalyst(out, state, today):
    cats = out.get("catalysts")
    if cats is not None:
        state["factor_catalysts"] = cats  # REPLACE, never append -- point-in-time snapshot (G50)
    themes = out.get("theme_updates", {})
    if isinstance(themes, dict) and themes.get("id") is not None:
        for t in state.setdefault("factor_themes", {}).setdefault("themes", []):
            if t.get("id") == themes["id"]:
                t[f"live_{today.replace('-', '_')}"] = themes.get("update")
    return {"factor_catalysts_replaced": cats is not None}


def _merge_earnings(out, state, today):
    updates = out.get("earnings_facts_updates", {})
    state["data_cache"].setdefault("earnings_facts", {}).update(updates)
    return {"earnings_facts_updated": list(updates)}


def _merge_book(out, state, today):
    betas = out.get("refreshed_betas", {})
    for tk, v in betas.items():
        state["data_cache"].setdefault("betas", {})[tk] = {"value": v, "as_of": today, "benchmark": "SMH"}
    return {"betas_refreshed": list(betas)}


def _merge_scout(out, state, today):
    dc = out.get("diversifier_candidates")
    if dc is not None:
        state["diversifier_candidates"] = dc
    return {"diversifier_candidates_replaced": dc is not None}


def _merge_watchlist(out, state, today):
    cursor = out.get("watchlist_scan_cursor")
    if cursor is not None:
        state["watchlist_scan_cursor"] = cursor
    ec = out.get("earnings_calendar_updates", {})
    state["data_cache"].setdefault("earnings_calendar", {}).update(ec)
    return {"watchlist_scan_cursor": cursor}


def _merge_macro(out, state, today):
    upd = out.get("fomc_cache_update")
    if upd is not None:
        state["fomc_cache"] = upd
    return {"fomc_cache_updated": upd is not None}


# One entry per Stage-1 agent whose tail this command knows how to fold into state.json.
# Mirrors AGENT_SLICES (the outbound embed table) in spirit -- this is the inbound counterpart.
# Extend this table, don't hand-merge, when a new agent's output needs to land in state.
MERGE_RULES = {
    "thesis": _merge_thesis,
    "signals": _merge_signals,
    "catalyst": _merge_catalyst,
    "earnings": _merge_earnings,
    "book": _merge_book,
    "scout": _merge_scout,
    "watchlist": _merge_watchlist,
    "macro": _merge_macro,
}


def cmd_merge_tails(args):
    """Fold Stage-1 sub-agent output files (runs/<ts>/out_<agent>.json) into state.json,
    mechanically, per MERGE_RULES (added 2026-08-29, same-day cleanup). Before this command
    existed, this was ~80 lines of one-off Python written fresh in the same session it was
    used -- exactly the kind of hand-assembly step SKILL.md already warns about for the
    OUTBOUND embed direction (see AGENT_SLICES's own docstring: "hand-assembly of a spec that
    already exists in writing is a copying exercise, and copying silently drops fields"). This
    is the same principle applied to the INBOUND merge direction.

    Reads runs/<run-dir>/out_<agent>.json for every agent named in --agents (or every agent in
    MERGE_RULES whose out_*.json file exists, if --agents is omitted). Agents not yet covered
    by MERGE_RULES (currently: rebound, ledger, tax, quality, cycle, strategist -- their state
    writes are either handled by dedicated commands like `lots`/`proposals`, or don't merge
    into state.json at all) are skipped and reported, not silently ignored.

    Writes state.json with WRITE SAFETY (.bak then tmp-then-mv). Does NOT run `validate` or
    `compact` -- run those as separate, explicit steps after, same as every other PERSIST
    sub-step.

    OPERATIONAL CAVEAT, found while building this (2026-08-29): an agent's out_<agent>.json
    file is not always byte-identical to the fenced JSON tail it returned in its chat
    response -- on this same run, smith-earnings and smith-macro's output files held a
    DIFFERENT (older/interim) tail than what the notification actually reported, apparently
    because those two agents wrote state directly themselves at some point mid-task. The
    orchestrator's job is therefore to WRITE each agent's exact returned tail into
    runs/<ts>/out_<agent>.json itself the moment the notification arrives (a plain Write call,
    overwriting whatever the agent already left there) BEFORE calling this command -- the
    returned tail is the authoritative source, the agent's own file write is a convenience,
    not a guarantee. This command trusts whatever is in the file; making that file trustworthy
    is a separate, one-line discipline at dispatch time.
    """
    state_path = os.path.join(args.base_dir, "state.json")
    state = load_json(state_path, default={})
    state.setdefault("data_cache", {})
    state.setdefault("thesis", {})

    today = args.today or date.today().isoformat()
    requested = args.agents.split(",") if args.agents else list(MERGE_RULES)

    results = {}
    skipped_no_file = []
    skipped_no_rule = []
    for agent in requested:
        if agent not in MERGE_RULES:
            skipped_no_rule.append(agent)
            continue
        out_path = os.path.join(args.run_dir, f"out_{agent}.json")
        if not os.path.exists(out_path):
            skipped_no_file.append(agent)
            continue
        out = _load_agent_tail(out_path)
        extra = {}
        if agent == "signals":
            holdings = load_json(os.path.join(args.run_dir, "holdings.json"), default={})
            extra["scanned_tickers"] = [h["ticker"] for h in holdings.get("holdings_inr", [])]
        results[agent] = MERGE_RULES[agent](out, state, today, **extra)

    safe_write(state_path, state)
    emit({"merged": list(results), "results": results,
          "skipped_no_output_file": skipped_no_file, "skipped_no_merge_rule": skipped_no_rule,
          "written": True,
          "next_step": "run smith_math.py validate before trusting this state"})


TECHNICAL_CACHE_HARD_STALE_DAYS = TRIGGER_CACHE_MAX_AGE_DAYS * 2  # 20 days


def validate_technical_cache_staleness(base_dir):
    """Escalate a chronically-stale rsi14/rel_strength_1m cache from a quiet per-run
    data_quality note into a hard `validate` defect (added 2026-08-29).

    `cmd_triggers` already gates on TRIGGER_CACHE_MAX_AGE_DAYS (10) and silently suppresses
    oversold_reversion/overbought_distribution/laggard_rotation when the cache is older than
    that -- correct behaviour for a single stale run (never fire a trigger on data that old).
    But by 2026-08-29 this had happened on THREE CONSECUTIVE runs (two deep, one quick), each
    time reported only as one line in that run's data_quality and each time deferred again "on
    cost grounds" -- and oversold/overbought triggers are the single most-requested feature in
    this desk's history (2026-08-12 user report, the whole reason `oversold_reversion`/
    `overbought_distribution` exist as LIVE triggers at all). A per-run soft note that nobody
    is forced to act on is exactly how a standing request goes dark for weeks without anyone
    deciding that on purpose.

    This check does not change cmd_triggers' behaviour at all -- it still suppresses
    correctly, every time. It adds a SEPARATE, LOUDER signal: once the cache is stale beyond
    TECHNICAL_CACHE_HARD_STALE_DAYS (double the trigger's own suppression threshold), `validate`
    stops reporting clean until either the cache is refreshed or the run explicitly records
    (in `state.data_cache.rsi14.stale_ack_on` / `.rel_strength_1m.stale_ack_on`) that skipping
    the refresh was a deliberate, dated decision -- not a default nobody made.
    """
    defects = []
    state = load_json(os.path.join(base_dir, "state.json"), default={})
    dc = state.get("data_cache", {}) or {}
    today = date.today()
    for cache_name, values_key in (("rsi14", "values"), ("rel_strength_1m", "values_pp")):
        cache = dc.get(cache_name, {}) or {}
        as_of = cache.get("as_of")
        if not as_of or not cache.get(values_key):
            continue  # absent entirely is already reported by cmd_triggers each run; not this check's job
        try:
            as_of_date = datetime.strptime(as_of, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            continue
        age = (today - as_of_date).days
        if age <= TECHNICAL_CACHE_HARD_STALE_DAYS:
            continue
        ack_on = cache.get("stale_ack_on")
        if ack_on == today.isoformat():
            continue  # today's run explicitly acknowledged the staleness in writing -- allowed through once
        defects.append(
            f"TECHNICAL CACHE CHRONICALLY STALE: data_cache.{cache_name} is {age} days old "
            f"(hard threshold {TECHNICAL_CACHE_HARD_STALE_DAYS}d, 2x cmd_triggers' own "
            f"{TRIGGER_CACHE_MAX_AGE_DAYS}d suppression floor) -- oversold/overbought/laggard "
            f"triggers have been silently dark well past a single deferred run. Either refresh "
            f"it this run (deep mode, 3-symbol yfinance batches, same cost as ATR20 which "
            f"shares the daily-bars fetch) or set data_cache.{cache_name}.stale_ack_on = "
            f"today's date to record that skipping it again was a deliberate, dated choice, "
            f"not a silent default.")
    return defects


EARNINGS_PENDING_HARD_STALE_DAYS = 0  # flag on the very first run at/after reported_date -- see G84-class rationale below


def validate_pending_earnings_staleness(base_dir):
    """Escalate an earnings_facts entry stuck at status=PENDING at/past its own reported_date
    into a hard `validate` defect (added 2026-08-30, tightened same-day after user feedback
    that a multi-day grace period was too slow -- "no 3 days stuck").

    smith-earnings exists specifically to "own the words beat/miss for the whole fleet" and
    write verified actuals into data_cache.earnings_facts so no other agent re-derives a
    quarter from price action (G58/G75's whole lesson). But nothing currently RE-dispatches
    it after a tracked print date passes -- it only fires on the PRE-print 5-day-window
    trigger. Found 2026-08-30: NVDA (reported 2026-08-26) and MRVL (reported 2026-08-27) both
    sat at status=PENDING for 3+ days, so smith-catalyst's 2026-08-29 run had to independently
    re-search and re-characterise "beat but sold off" from price action and news -- duplicated
    verification effort AND exactly the un-scripted-residue risk EVIDENCE PRINCIPLE exists to
    close, just for a fact that was cheap to settle days earlier.

    EARNINGS_PENDING_HARD_STALE_DAYS is 0: this fires on the FIRST run at or after
    reported_date, not after a grace period -- both on quick and deep sweeps (see SKILL.md's
    EARNINGS VERIFY trigger, which is deliberately NOT gated to deep-only, since a verify-only
    dispatch is cheap and the whole point is closing the gap same-day). A same-day print (an
    after-hours report that yfinance hasn't indexed yet) may legitimately still come back
    unresolved on the very first attempt -- that's fine and not a bug; the check just makes
    the orchestrator try immediately and every run after, rather than waiting for a threshold.

    This check does not dispatch anything itself (validate is read-only) -- it makes the gap
    loud enough that the orchestrator dispatches a verify pass immediately.
    """
    defects = []
    state = load_json(os.path.join(base_dir, "state.json"), default={})
    facts = state.get("data_cache", {}).get("earnings_facts", {}) or {}
    today = date.today()
    stale = []
    for tk, f in facts.items():
        if not isinstance(f, dict) or f.get("status") != "PENDING":
            continue
        reported = f.get("reported_date")
        if not reported:
            continue
        try:
            reported_date = datetime.strptime(reported, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            continue
        age = (today - reported_date).days
        if age >= EARNINGS_PENDING_HARD_STALE_DAYS:
            stale.append(f"{tk} (reported {reported}, {age}d ago)")
    if stale:
        defects.append(
            f"EARNINGS FACTS STUCK PENDING: {len(stale)} name(s) reported their print but "
            f"earnings_facts never recorded actuals ({', '.join(stale)}) -- dispatch "
            f"smith-earnings (or a lighter verify-only pass) to fill in revenue_actual/"
            f"eps_actual/quarter_verdict/guide_verdict before another agent re-derives "
            f"beat/miss from price action independently.")
    return defects


def cmd_validate(args):
    policy = load_json(os.path.join(args.base_dir, "policy.json"), default=None)
    state = load_json(os.path.join(args.base_dir, "state.json"), default={})

    policy_defects = []
    if policy is None:
        policy_defects = ["no policy.json"]
    else:
        policy_defects = validate_policy(policy)

    cache_defects = validate_cache_events(state)
    thesis_defects = validate_thesis_schema(state, args.base_dir)
    learning_defects = validate_learning_schema(args.base_dir)
    proposals_defects = validate_proposals_schema(args.base_dir)
    narrative_defects = validate_policy_narrative_drift(args.base_dir)
    staleness_defects = validate_technical_cache_staleness(args.base_dir)
    earnings_pending_defects = validate_pending_earnings_staleness(args.base_dir)
    all_defects = (policy_defects + cache_defects + thesis_defects + learning_defects
                   + proposals_defects + narrative_defects + staleness_defects
                   + earnings_pending_defects)

    emit({
        "policy_present": policy is not None,
        "policy_confirmed": policy.get("confirmed", False) if policy else False,
        "policy_as_of": policy.get("as_of") if policy else None,
        "clean": not all_defects,
        "defect_count": len(all_defects),
        "defects": all_defects,
    })

# ---------------------------------------------------------------------------
# SLICES -- deterministic per-agent embeds (added 2026-08-16)
# ---------------------------------------------------------------------------
# SKILL.md section 3 specifies exactly what each sub-agent receives, and until now the
# orchestrator hand-assembled that from state.json every run. Hand-assembly of a spec that
# already exists in writing is a copying exercise, and copying silently drops fields:
#
#   * 2026-08-16, diversifier_candidates rewritten WITHOUT `status: "active"` -- the dashboard
#     bench panel filters on it, so the panel silently vanished.
#   * 2026-08-16, the `us` block rewritten without `peak_total_book_usd` -- chart_drawdown
#     returns empty without it, so the drawdown-vs-trim-ladder meter silently vanished.
#
# Both were caught only by the dashboard's section-count regression guard, i.e. by luck plus one
# unrelated control. Neither would have happened if the embed were GENERATED from a declared
# table. That table is AGENT_SLICES; this command renders it.
#
# It does NOT replace the orchestrator's judgement about WHICH agents to dispatch, or the prose
# framing of a prompt. It guarantees the DATA half is complete and identical every run.



# ---------------------------------------------------------------------------
# SLICES -- per-agent embeds, rebuilt 2026-08-16 after measuring the first version
# ---------------------------------------------------------------------------
# v1 rendered 11 slices totalling 368KB of which **56.3% was duplicated payload**: `thesis`
# copied into 4 agents at 27KB each, `open_flags` broadcast to 10 agents at 3KB each, and
# `compute_*.json` inlined into 5 agents despite those files ALREADY EXISTING in the same run
# directory. Copying a file that sits next to the reader is pure waste.
#
# Measured on the same run, agents were also re-pulling identical EXTERNAL data: the HBM tracker
# was read by smith-thesis AND smith-catalyst (smith-cycle now makes three), stockanalysis.com
# by watchlist AND thesis, yfinance by scout, macro and book.
#
# Three changes:
#   1. REFS, NOT COPIES. Anything already on disk in the run dir is handed over as a PATH in
#      `read_these_files`. The agent reads what it needs, when it needs it, and can read
#      selectively rather than carrying 27KB to use one field of.
#   2. SHARED SNAPSHOTS. External resources more than one agent reads are snapshotted ONCE into
#      runs/<ts>/shared/. This cuts duplicate fetches, and removes a real correctness hazard:
#      agents reading the same LIVE file at different moments can legitimately disagree, and
#      then the desk holds two "facts". A snapshot makes the run internally consistent.
#   3. OPT-IN BROADCAST. open_flags went to all 10 agents because "embed in every prompt" was
#      read literally. Only agents that act on flags receive them.

AGENT_SLICES = {
    "signals":    {"state": ["news_watermark", "signal_history", "signal_history_as_of",
                             "open_flags", "peer_map"],
                   "cache": ["atr20"], "refs": ["journal"], "holdings": "trim"},
    "thesis":     {"state": ["thesis", "sector_map", "news_watermark", "open_flags"],
                   "cache": ["etf_constituents", "earnings_facts"], "refs": [],
                   "holdings": "trim", "shared": ["hbm_tracker"]},
    "watchlist":  {"state": ["news_watermark", "watchlist_scan_cursor"],
                   "cache": ["earnings_calendar"], "refs": ["attribution"], "holdings": "trim"},
    "book":       {"state": [], "cache": ["betas"], "refs": ["book", "lots"], "holdings": None},
    "scout":      {"state": ["diversifier_candidates"], "cache": [],
                   "refs": ["sentiment", "market_inputs"], "holdings": "trim"},
    "macro":      {"state": ["fomc_cache"], "cache": [],
                   "refs": ["sentiment", "market_inputs"], "holdings": None},
    "catalyst":   {"state": ["factor_themes", "factor_catalysts", "news_watermark"],
                   "cache": [], "refs": ["drift"], "holdings": "trim",
                   "shared": ["hbm_tracker"]},
    "cycle":      {"state": ["factor_themes", "sector_map"], "cache": ["earnings_facts"],
                   "refs": ["drift"], "holdings": "trim", "shared": ["hbm_tracker"]},
    "earnings":   {"state": [], "cache": ["earnings_calendar", "earnings_facts"],
                   "refs": ["book"], "holdings": "trim"},
    "tax":        {"state": ["thesis"], "cache": [], "refs": ["book", "lots"],
                   "holdings": "trim"},
    "quality":    {"state": ["open_flags"], "cache": [], "refs": ["book"], "holdings": "trim"},
    "rebound":    {"state": ["sector_map"], "cache": [], "refs": ["book", "risk"],
                   "holdings": "full"},
    "ledger":     {"state": [], "cache": ["ticker_map"], "refs": ["book", "lots"],
                   "holdings": "full"},
    "strategist": {"state": ["thesis", "sector_map", "preferences", "open_flags"], "cache": [],
                   "refs": ["drift", "sentiment", "risk", "book", "derisk", "triggers",
                            "rotation"],
                   "holdings": "trim"},
}

REF_FILES = {
    "book": "compute_book.json", "risk": "compute_risk.json", "drift": "compute_drift.json",
    "journal": "compute_journal.json", "attribution": "compute_attribution.json",
    "rotation": "compute_rotation.json", "sentiment": "compute_sentiment.json",
    "derisk": "compute_derisk.json", "triggers": "compute_triggers.json",
    "market_inputs": "market_inputs.json",
}
BASE_REF_FILES = {"lots": "lots.json"}

# Agents whose REAL input is the outside world, not a file. Their slice can be byte-identical to
# last run's and they still have work to do, because news, prices and filings moved even when
# state did not. NEVER skip these on an unchanged digest -- that is the difference between a
# genuine saving and silently going blind.
EXTERNAL_READERS = {"signals", "thesis", "watchlist", "catalyst", "scout", "macro",
                    "earnings", "cycle", "quality"}
# NEVER_SKIP covers a second, subtler case: agents whose true inputs are NOT VISIBLE in their
# slice, so the digest cannot speak for them. smith-strategist is the example -- it reasons over
# the Stage-1 JSON tails, which arrive inline in its prompt and never touch its slice file. Its
# digest can be byte-identical while every analyst finding underneath it changed. A digest that
# cannot see an input must never be allowed to vote on skipping it.
NEVER_SKIP = {"strategist"}

# MATERIALITY (added 2026-08-17, from running the thing). The byte-exact digest below is correct
# and was, on its first live outing, useless: between the 08-16 and 08-17 runs NOT ONE SHARE moved
# and not one US price changed, but USD/INR ticked 95.43 -> 95.415 (**0.0157%**) and every USD
# figure in the book shifted with it. Every digest differed; nothing was skippable.
#
# "Byte-identical" is the wrong bar for a system whose inputs include a continuously-drifting FX
# rate. But rounding values before hashing would HIDE the change, which is worse. So the exact
# digest stays authoritative, and alongside it we report the LARGEST RELATIVE CHANGE across
# numeric fields. A run whose worst numeric delta is 0.0157% has not materially changed, and the
# orchestrator can see exactly how close it was instead of being told a binary.
MATERIALITY_PCT = 0.25   # below this, a numeric delta is noise, not news

# DOMAIN DISPATCH (added 2026-08-17, from measuring two real runs).
# Measured subagent cost is nearly FLAT across agents -- 77K to 148K tokens -- while yield is
# not: on 2026-08-16 `thesis` spent 116,870 tokens to report ZERO status changes and `book`
# 91,687 to report "unchanged", while `catalyst` spent 105,223 on the CXMT finding that moved
# the read on a 15.53% sleeve. Cost per agent is therefore NOT the lever; SELECTION is.
#
# And the right selection question is not "did this agent's slice bytes change" (the byte digest
# was defeated by a 0.0157% FX tick) but **"did the thing this agent actually reads move?"**
# Each agent is mapped to the domain it consumes, and the domain is evaluated from concrete
# observable facts about the run rather than from file hashes.
AGENT_DOMAIN = {
    "signals": "news", "thesis": "news", "catalyst": "news", "cycle": "news",
    "quality": "fundamentals", "earnings": "calendar", "watchlist": "calendar",
    "macro": "macro", "scout": "session",
    "book": "holdings", "ledger": "holdings", "tax": "holdings", "rebound": "session",
    "strategist": "always",
}
DOMAIN_HELP = {
    "news": "new items since news_watermark",
    "calendar": "an earnings date confirmed/changed, or a print entering the window",
    "macro": "a rate/FOMC/CPI/NFP event, or a live options session",
    "session": "a trading session actually occurred since the last run",
    "holdings": "qty_changes non-empty, or lots.json changed",
    "fundamentals": "a new filing or reported quarter",
    "always": "its inputs are the Stage-1 tails, which are never visible here",
}


def _domain_moved(domain, ctx):
    """(moved, evidence). None = cannot tell from the script alone -- say so, never guess."""
    if domain == "always":
        return True, "always dispatched -- its real inputs are not visible to this check"
    if domain == "holdings":
        if ctx["qty_changes"]:
            return True, f"{len(ctx['qty_changes'])} qty change(s) this run"
        if ctx["lots_changed"]:
            return True, "lots.json changed since the previous run"
        return False, "no qty_changes and lots.json unchanged -- nothing for it to read"
    if domain == "session":
        if ctx["session_occurred"]:
            return True, "a trading session occurred since the previous run"
        return False, (f"market_session={ctx['market_session']} and prices are unchanged since "
                       f"the previous run -- no session to read")
    if domain == "calendar":
        if ctx["calendar_changed"]:
            return True, "earnings_calendar changed since the previous run"
        return False, "earnings_calendar unchanged since the previous run"
    return None, (f"'{domain}' cannot be evaluated from files alone ({DOMAIN_HELP.get(domain,'')}) "
                  f"-- the orchestrator must judge it. Default to dispatching.")


def _numeric_leaves(obj, prefix="", out=None):
    """Flatten every numeric leaf to {path: value} for a field-by-field delta."""
    out = {} if out is None else out
    if isinstance(obj, dict):
        for k, v in obj.items():
            _numeric_leaves(v, f"{prefix}.{k}", out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _numeric_leaves(v, f"{prefix}[{i}]", out)
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        out[prefix] = float(obj)
    return out


def _max_relative_delta(a, b):
    """(max_pct, field) across numeric leaves common to both. None if shapes are incomparable --
    a structural change is never 'immaterial', so it must not be reported as a small number."""
    la, lb = _numeric_leaves(a), _numeric_leaves(b)
    common = set(la) & set(lb)
    if not common or set(la) != set(lb):
        return None, "structure changed"
    worst, where = 0.0, ""
    for k in common:
        x, y = la[k], lb[k]
        if x == y:
            continue
        denom = max(abs(x), abs(y), 1e-9)
        d = abs(y - x) / denom * 100.0
        if d > worst:
            worst, where = d, k
    return worst, where
# Everything else (book, ledger, tax, rebound) reasons purely over files this run already
# produced. If every one is byte-identical to the previous run, the agent has, by construction,
# nothing new to say.
SHARED_SOURCES = {"hbm_tracker": "/Users/yb/Claude/HBMTracker/consumer_view.json"}
GAPS_CAP, FLAGS_CAP = 8, 5

# Any single payload at or above this size is materialised ONCE into runs/<ts>/shared/ and
# referenced by path instead of being copied into each slice. A size rule rather than a
# hand-maintained list of "big keys", because a hand-maintained list is one more thing that goes
# stale -- `thesis` was 27KB and copied 3 times, `holdings` 3KB copied 10 times, and both would
# have had to be remembered. The threshold self-tunes as the book grows.
INLINE_MAX_BYTES = 2048


def _place(sl, key, value, shared_dir, shared_once, name=None):
    """Inline a small payload; materialise a large one ONCE into shared/ and hand over a path.

    Deduplication is by CONTENT, not by key name: two agents asking for the same payload under
    different keys still get one file. Identical bytes for every reader is the point -- it is
    both smaller and safer than each agent holding its own copy.
    """
    if value is None:
        sl[key] = None
        return
    blob = json.dumps(value, indent=2)
    if len(blob) < INLINE_MAX_BYTES:
        sl[key] = value
        return
    fname = (name or key).replace(".", "_")
    digest = hashlib.md5(blob.encode()).hexdigest()[:8]
    path = shared_once.get(digest)
    if path is None:
        path = os.path.join(shared_dir, f"{fname}.{digest}.json")
        with open(path, "w") as fh:
            fh.write(blob)
        shared_once[digest] = path
    sl["read_these_files"][key] = path


def cmd_slices(args):
    """Render each agent's embed: small state inline, everything file-backed by reference."""
    base, rd = args.base_dir, args.run_dir
    state = load_json(os.path.join(base, "state.json"), default={})
    holdings = load_json(os.path.join(rd, "holdings.json"), default={})
    rows = holdings.get("holdings_inr") or []
    held = {r.get("ticker") for r in rows if r.get("ticker")}
    trim = [{"ticker": r.get("ticker"), "name": r.get("name"), "qty": r.get("qty"),
             "weight_pct": round(r.get("weight_pct") or 0, 2)} for r in rows]

    shared_dir = os.path.join(rd, "shared")
    os.makedirs(shared_dir, exist_ok=True)
    shared_paths, shared_notes = {}, []
    for name, src in SHARED_SOURCES.items():
        payload = load_json(src, default=None)
        if payload is None:
            shared_notes.append(f"{name}: source {src} UNREADABLE -- agents must degrade, not guess")
            continue
        dst = os.path.join(shared_dir, f"{name}.json")
        with open(dst, "w") as fh:
            json.dump(payload, fh, indent=2)
        shared_paths[name] = dst
        shared_notes.append(f"{name}: snapshotted once from {src}; every agent this run reads "
                            f"the SAME bytes and cannot disagree about it")

    dc = state.get("data_cache") or {}
    live_gaps = [g for g in (state.get("known_gaps") or []) if smith_risk.gap_is_live(g)]
    common = {
        "mode": args.mode, "today": args.today or str(date.today()),
        "market_session": holdings.get("market_session"),
        "gate_classification": holdings.get("gate_classification"),
        "macro": holdings.get("macro_strip") or {}, "usdinr": holdings.get("usdinr"),
        "known_gaps": [{"id": g.get("id"), "status": smith_risk.gap_status(g),
                        "gap": (g.get("gap") or g.get("description") or "")[:240]}
                       for g in live_gaps[:GAPS_CAP]],
        "known_gaps_truncated": max(0, len(live_gaps) - GAPS_CAP),
    }

    shared_once = {}
    runs_root = os.path.dirname(os.path.abspath(rd))
    # previous run's digests, for the unchanged-input check
    prior_run, prior_digests, prior_slices = None, {}, {}
    runs_root = os.path.dirname(os.path.abspath(rd))
    try:
        sibs = sorted(d for d in os.listdir(runs_root)
                      if os.path.isdir(os.path.join(runs_root, d))
                      and os.path.join(runs_root, d) != os.path.abspath(rd))
        if sibs:
            prior_run = sibs[-1]
            for f in os.listdir(os.path.join(runs_root, prior_run)):
                if f.startswith("slice_") and f.endswith(".json"):
                    d = load_json(os.path.join(runs_root, prior_run, f), default={})
                    prior_slices[f[6:-5]] = d
                    if d.get("inputs_digest"):
                        prior_digests[f[6:-5]] = d["inputs_digest"]
    except OSError:
        pass
    skippable, immaterial, no_domain_move = [], [], []
    # observable facts this run, for the domain check
    book_now = load_json(os.path.join(rd, "compute_book.json"), default={})
    prior_book = (load_json(os.path.join(runs_root, prior_run, "compute_book.json"), default={})
                  if prior_run else {})
    prior_holdings = (load_json(os.path.join(runs_root, prior_run, "holdings.json"), default={})
                      if prior_run else {})
    lots_now = load_json(os.path.join(base, "lots.json"), default={})
    prior_lots_digest = (prior_slices.get("book", {}) or {}).get("_lots_digest")
    lots_digest = hashlib.md5(json.dumps(lots_now, sort_keys=True).encode()).hexdigest()[:12]
    ctx = {
        "qty_changes": book_now.get("qty_changes") or [],
        "lots_changed": bool(prior_lots_digest) and prior_lots_digest != lots_digest,
        "market_session": holdings.get("market_session"),
        # A session occurred only if the BROKER'S OWN INR values moved. Comparing price_usd was
        # the obvious thing to write and it is wrong for exactly the reason the byte-digest was
        # wrong: price_usd is DERIVED through the FX rate, so a 0.0157% USD/INR tick makes every
        # USD price differ and fakes a session that never happened. Caught 2026-08-17, minutes
        # after fixing the identical contamination one layer up -- the lesson generalises:
        # **never test for change on a derived value when the source value is available.**
        "session_occurred": any(
            (a.get("market_value_inr") != b.get("market_value_inr"))
            for a, b in zip(rows, (prior_holdings.get("holdings_inr") or []))),
        "calendar_changed": (json.dumps(dc.get("earnings_calendar"), sort_keys=True) !=
                             json.dumps((prior_slices.get("watchlist", {}) or {})
                                        .get("data_cache.earnings_calendar"), sort_keys=True))
                            if prior_slices.get("watchlist") else False,
    }
    want = [a.strip() for a in (args.agents or "").split(",") if a.strip()] or list(AGENT_SLICES)
    written, problems = [], []
    for agent in want:
        spec = AGENT_SLICES.get(agent)
        if not spec:
            problems.append(f"unknown agent '{agent}' -- not in AGENT_SLICES")
            continue
        sl = dict(common)
        sl["agent"] = f"smith-{agent}"
        sl["output_file"] = os.path.join(rd, f"smith-{agent}-output.md")
        sl["holdings_path"] = os.path.join(rd, "holdings.json")
        sl["read_these_files"] = {}

        for k in spec["state"]:
            v = state.get(k)
            if k in ("thesis", "sector_map") and isinstance(v, dict):
                v = {t: x for t, x in v.items() if t in held}
            if k == "open_flags":
                v = (v or [])[-FLAGS_CAP:]
            _place(sl, k, v, shared_dir, shared_once)
        for k in spec["cache"]:
            _place(sl, f"data_cache.{k}", dc.get(k), shared_dir, shared_once)

        for r in spec.get("refs", []):
            path = (os.path.join(rd, REF_FILES[r]) if r in REF_FILES
                    else os.path.join(base, BASE_REF_FILES[r]) if r in BASE_REF_FILES else None)
            if path is None:
                problems.append(f"smith-{agent}: unknown ref '{r}'")
            elif not os.path.exists(path):
                problems.append(f"smith-{agent}: {os.path.basename(path)} MISSING -- run the "
                                f"pipeline before rendering slices")
            else:
                sl["read_these_files"][r] = path
        for sname in spec.get("shared", []):
            if sname in shared_paths:
                sl["read_these_files"][sname] = shared_paths[sname]
            else:
                problems.append(f"smith-{agent}: shared source '{sname}' unavailable this run")

        if spec.get("holdings") == "trim":
            _place(sl, "holdings", trim, shared_dir, shared_once, name="holdings_trim")
        elif spec.get("holdings") == "full":
            _place(sl, "holdings", rows, shared_dir, shared_once, name="holdings_full")

        # completeness: a required payload must be present EITHER inline OR as a ref -- it
        # moved representation when large payloads became content-addressed, and a guard that
        # only knows the old shape reports false alarms instead of real ones.
        for k in spec["state"]:
            if k in ("thesis", "sector_map") and not sl.get(k) and k not in sl["read_these_files"]:
                problems.append(f"smith-{agent}: '{k}' is neither inline nor referenced -- "
                                f"refusing to pretend that is a valid embed")
        # Fingerprint the agent's ACTUAL inputs: inline values plus the CONTENT of every
        # referenced file (not its path -- paths are stable while contents change).
        h = hashlib.md5()
        for k in sorted(k for k in sl if k not in ("read_these_files", "output_file", "today")):
            h.update(f"{k}={json.dumps(sl[k], sort_keys=True)}".encode())
        for k, path in sorted(sl["read_these_files"].items()):
            try:
                with open(path, "rb") as fh:
                    h.update(k.encode() + hashlib.md5(fh.read()).digest())
            except OSError:
                h.update(k.encode() + b"MISSING")
        sl["inputs_digest"] = h.hexdigest()[:12]

        out = os.path.join(rd, f"slice_{agent}.json")
        with open(out, "w") as fh:
            json.dump(sl, fh, indent=2)
        rec = {"agent": f"smith-{agent}", "file": out, "bytes": os.path.getsize(out),
               "refs": len(sl["read_these_files"]), "inputs_digest": sl["inputs_digest"]}
        dom = AGENT_DOMAIN.get(agent, "always")
        moved, evidence = _domain_moved(dom, ctx)
        rec["domain"] = dom
        rec["domain_moved"] = moved
        rec["domain_evidence"] = evidence
        if moved is False:
            no_domain_move.append(f"smith-{agent}")
        # materiality: compare this slice against the prior run's slice, field by field
        prior_slice = prior_slices.get(agent)
        if prior_slice is not None:
            cmp_now = {k: v for k, v in sl.items()
                       if k not in ("read_these_files", "output_file", "today", "inputs_digest")}
            cmp_old = {k: v for k, v in prior_slice.items()
                       if k not in ("read_these_files", "output_file", "today", "inputs_digest")}
            worst, where = _max_relative_delta(cmp_old, cmp_now)
            if worst is not None:
                rec["max_delta_pct"] = round(worst, 4)
                rec["max_delta_field"] = where
                if worst < MATERIALITY_PCT and sl["inputs_digest"] != prior_digests.get(agent):
                    rec["immaterial_change"] = True
                    rec["immaterial_note"] = (
                        f"inputs differ but the largest numeric change is {worst:.4f}% "
                        f"(at {where}), below the {MATERIALITY_PCT}% materiality bar -- this is "
                        f"noise, not news. Skipping is defensible for a file-only agent; the "
                        f"decision is the orchestrator's and must be stated in the briefing.")
                    if agent not in EXTERNAL_READERS and agent not in NEVER_SKIP:
                        immaterial.append(f"smith-{agent}")

        prior = prior_digests.get(agent)
        if prior and prior == sl["inputs_digest"]:
            rec["inputs_unchanged_since"] = prior_run
            if agent in EXTERNAL_READERS or agent in NEVER_SKIP:
                rec["skip"] = False
                rec["skip_reason"] = (
                    "inputs unchanged BUT this agent reads the outside world -- news and prices "
                    "moved even though state did not. Dispatch it."
                    if agent in EXTERNAL_READERS else
                    "inputs unchanged BUT its real inputs (the Stage-1 tails) are not in its "
                    "slice, so this digest cannot speak for them. Dispatch it.")
            else:
                rec["skip"] = True
                rec["skip_reason"] = ("every input is byte-identical to " + str(prior_run) +
                                      " and this agent reasons only over files -- it can have "
                                      "nothing new to say. Reuse its prior output.")
                skippable.append(f"smith-{agent}")
        written.append(rec)

    emit({"run_dir": rd, "written": written, "problems": problems,
          "compared_against": prior_run,
          "skip_candidates": skippable,
          "immaterial_change_candidates": immaterial,
          "domain_did_not_move": no_domain_move,
          "dispatch_note": ("`domain_did_not_move` lists agents whose INPUT DOMAIN is observably "
                            "unchanged -- the strongest skip signal, because it asks whether the "
                            "thing they read moved rather than whether their bytes did. Measured "
                            "2026-08-16/17: agent cost is nearly flat (77K-148K tokens) while "
                            "yield is not, so selection is the lever, not trimming. A null "
                            "domain_moved means the script cannot tell -- dispatch."),
          "materiality_pct": MATERIALITY_PCT,
          "skip_note": ("Agents listed here have byte-identical inputs to the previous run AND "
                        "reason only over files, so they cannot produce a new finding -- reuse "
                        "their prior output instead of dispatching. Agents that read the outside "
                        "world are NEVER listed here even when their slice is unchanged, because "
                        "their real input is news and prices, not the file."),
          "shared_snapshots": shared_notes,
          "total_bytes": sum(w["bytes"] for w in written),
          "note": ("Small agent-specific state inline; anything already on disk handed over as a "
                   "path in `read_these_files`, never copied. Shared external sources are "
                   "snapshotted once into runs/<ts>/shared/ -- fewer fetches, and every agent "
                   "this run sees identical bytes.")})
