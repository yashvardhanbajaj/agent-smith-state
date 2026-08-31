"""Retention, archives, schema validation, and per-agent embed rendering.

Split out of smith_math.py 2026-08-16: the file had reached 4,085 lines and mixed
four unrelated domains. Shared primitives live in smith_core; smith_math keeps the
per-run compute stages, the pipeline runner and the CLI, and imports these.
"""

import hashlib
import json
import os
from datetime import date, datetime, timedelta

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
                              "dismissed_by_desk",
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

    # --- RESTORE BEFORE EVICTING (added 2026-08-30) --------------------------
    # The archive was WRITE-ONLY. compact evicted thesis/sector_map for names no longer held,
    # and nothing ever read them back when a name RETURNED. Measured on 2026-08-30: 12 archived
    # tickers were held again. Four (AMKR, SMCI, LITE, IREN = 6.53% of book) had no live
    # classification at all and were invisible to cluster accounting; the other eight had been
    # re-derived from scratch by smith-thesis, which is wasted work with a worse failure mode --
    # two came back under DIFFERENT cluster names (BX 'Alternative Asset Manager/Diversifier' ->
    # 'Financials/Alt-Asset Diversifier'; BABA 'China Consumer/Cloud' -> 'China Internet/
    # Diversifier'). cmd_drift matches policy.cluster_targets by EXACT STRING, so a rename drops
    # a cluster out of drift tracking entirely -- the G73 hazard, reached by a different route.
    #
    # ARCHIVE-NEVER-DELETE already guaranteed the record survived. The missing half was reading
    # it back. This matters more now that the universe's T2_ALUMNI tier makes re-entry a
    # first-class path rather than an accident.
    #
    # RESTORE COPIES, NEVER MOVES: the archive keeps its entry, so a name that exits again is
    # not re-archiving something that has since been deleted, and the archive stays a complete
    # history rather than a queue.
    restored = {}
    if held:
        for key in ("thesis", "sector_map"):
            cfg = RETENTION[key]
            arch = _archive_load(os.path.join(base, cfg["archive"])).get(cfg["payload"], {}) or {}
            live = state.setdefault(key, {})
            back = {t: v for t, v in arch.items() if t in held and t not in live}
            if back:
                live.update(back)
                restored[key] = sorted(back)
                moves.append({"file": f"state.{key}", "restored": len(back),
                              "from": cfg["archive"], "ids": sorted(back)[:12],
                              "why": "held again -- archived on a prior exit and never read back; "
                                     "an unrestored name is invisible to cluster accounting and "
                                     "gets re-derived from scratch under a possibly different name"})

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
    out = {"dry_run": not args.write, "moves": moves, "restored": restored,
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
def validate_policy(policy, state=None):
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
    # LIVE-BOOK CHECKS (added 2026-08-30). Everything above validates the DOCUMENT against
    # itself, which is how a 14.53%-of-equity hole stayed invisible for weeks: the target sum
    # checked only the clusters policy declares, so clusters the book actually holds and policy
    # has never heard of simply did not enter the arithmetic. cmd_drift emits those with
    # target_pct: null and breach: false -- reported, but structurally unable to breach.
    if state:
        sm = state.get("sector_map") or {}
        held = [h.get("ticker") for h in (state.get("holdings") or []) if h.get("ticker")]
        unclassified = sorted(t for t in held if t not in sm)
        if unclassified:
            defects.append(
                f"{len(unclassified)} held ticker(s) have no sector_map entry "
                f"({', '.join(unclassified[:8])}) -- they sit outside cluster accounting "
                f"entirely and cannot breach any band. Usually an archived classification that "
                f"was never restored on re-entry; `compact` now restores these.")
        live_clusters = {sm[t] for t in held if t in sm}
        orphan = sorted(live_clusters - set(targets))
        if orphan:
            defects.append(
                f"cluster(s) held but absent from cluster_targets: {', '.join(orphan)} -- "
                f"cmd_drift matches policy by EXACT STRING, so these are reported with a null "
                f"target and can never breach. Either give each a target/band or reclassify "
                f"the holdings into an existing cluster.")

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
        entry["reviewed_on"] = today
        state["thesis"][tk] = entry
    # Names the agent explicitly confirmed unchanged were still LOOKED AT this run, so they
    # are reviewed too -- otherwise a name that is genuinely stable ages as if abandoned.
    for tk in out.get("thesis", {}).get("reviewed_unchanged", []) or []:
        if tk in state["thesis"] and isinstance(state["thesis"][tk], dict):
            state["thesis"][tk]["reviewed_on"] = today
    sm_changed = out.get("sector_map", {}).get("changed", {})
    state.setdefault("sector_map", {}).update(sm_changed)
    for tk, fact in out.get("earnings_facts", {}).items():
        state["data_cache"].setdefault("earnings_facts", {})[tk] = fact
    etfc = out.get("etf_constituents_updates", {}) or {}
    if etfc:
        state["data_cache"].setdefault("etf_constituents", {}).update(etfc)
        state["data_cache"]["etf_constituents"]["as_of"] = today
    return {"thesis_changed": list(changed), "sector_map_changed": list(sm_changed)}


def _merge_signals(out, state, today, scanned_tickers=None, base_dir="."):
    changed = out.get("signal_history", {}).get("changed", {})
    state.setdefault("signal_history", {}).update(changed)
    stamp_tickers = set(changed) | set(scanned_tickers or [])
    state.setdefault("signal_history_as_of", {})
    for tk in stamp_tickers:
        state["signal_history_as_of"][tk] = today
    # analyst_targets had a declared 7-day TTL in cache_policy and was an EMPTY DICT -- while
    # TARGET GAP was the second most-fired signal bucket (n=19) and 4 of 9 live watchlist
    # setups. So every run re-derived targets nothing could audit, against a cache the TTL
    # table claimed existed. signals already pulls mean targets per name to build the bucket;
    # persisting them costs nothing and makes the number checkable.
    # journal_new: smith-signals has emitted this array since the desk began, and NOTHING EVER
    # INGESTED IT. `journal_new` appears nowhere in any compute script; entries reached
    # journal.json only when an orchestrator hand-wrote them at PERSIST. The cost is specific
    # and measurable: `day_atr_mult`/`rel_sigma`/`normalized` were added to that schema on
    # 2026-08-01 expressly so 30-day scoring could TEST whether volatility-normalised flags beat
    # the old absolute thresholds. A month later exactly ONE of 108 journal entries carried
    # them, so the test could never run and the doctrine stayed unvalidated by default.
    #
    # This is the same failure as G50 (factor_catalysts), cycle_position and rebound: an agent
    # produces output, no table names the write path, the output evaporates. A documented schema
    # is not a write instruction.
    jn = out.get("journal_new") or []
    if jn:
        jpath = os.path.join(base_dir, "journal.json")
        jr = load_json(jpath, default={"schema_version": 1, "entries": []})
        existing = {(e.get("date"), e.get("ticker"), e.get("bucket")) for e in jr.get("entries", [])}
        added = []
        for e in jn:
            key = (e.get("date") or today, e.get("ticker"), e.get("bucket"))
            if not all(key) or key in existing:
                continue
            e.setdefault("date", today)
            e.setdefault("verdict", "open")
            jr.setdefault("entries", []).append(e)
            existing.add(key)
            added.append(f"{key[1]}/{key[2]}")
        if added:
            safe_write(jpath, jr)

    # 5-day returns come from the SAME daily bars as ATR20/RSI14 -- zero marginal fetch cost.
    r5 = out.get("ret_5d_updates") or {}
    if r5:
        cache = state["data_cache"].setdefault("ret_5d", {})
        cache.setdefault("values_pct", {}).update(r5.get("values_pct") or {})
        if r5.get("benchmark_return_pct") is not None:
            cache["benchmark_return_pct"] = r5["benchmark_return_pct"]
        cache["benchmark"] = r5.get("benchmark", "SMH")
        cache["as_of"] = today
    targets = out.get("analyst_targets_updates", {}) or {}
    if targets:
        tc = state["data_cache"].setdefault("analyst_targets", {})
        tc.update(targets)
        tc["as_of"] = today
    # rsi14 / rel_strength_1m / atr20 -- THE THREE CACHES THE WHOLE FRESHNESS CONTRACT EXISTS
    # TO POLICE, and until 2026-08-31 the only signals outputs with NO WRITE PATH HERE. The
    # 08-30 run dispatched smith-signals expressly to lift the 19-day-dark trigger layer; the
    # agent returned all five caches correctly and this function merged two of them and dropped
    # rsi14, rel_strength_1m and atr20 on the floor. `freshness` then still reported DARK, which
    # is the only reason it was caught. Same shape as G50 / cycle_position / journal_new: the
    # agent produced it, no table named the write path, the output evaporated -- except this
    # instance silently defeated the specific repair it had been dispatched to perform.
    #
    # UNITS ARE NOT ASSUMED. rel_strength_1m_updates carries a `benchmark` key and its values are
    # PERCENTAGE POINTS RELATIVE to that benchmark, matching the existing cache's `values_pp`;
    # writing them into `values_abs_pct` would silently corrupt every relative-strength read.
    # Per the _merge_book benchmark guard: refuse rather than guess.
    rsi_upd = {k: v for k, v in (out.get("rsi14_updates") or {}).items()
               if isinstance(v, (int, float))}
    if rsi_upd:
        c = state["data_cache"].setdefault("rsi14", {})
        c.setdefault("values", {}).update(rsi_upd)
        c["as_of"] = today
    atr_upd = {k: v for k, v in (out.get("atr20_updates") or {}).items()
               if isinstance(v, (int, float))}
    if atr_upd:
        c = state["data_cache"].setdefault("atr20", {})
        c.setdefault("values_pct", {}).update(atr_upd)
        c["as_of"] = today
    rel_raw = out.get("rel_strength_1m_updates") or {}
    rel_bench = (rel_raw.get("benchmark") or "").upper()
    rel_upd = {k: v for k, v in rel_raw.items() if isinstance(v, (int, float))}
    rel_rejected = 0
    if rel_upd and rel_bench != "SMH":
        rel_rejected, rel_upd = len(rel_upd), {}
    elif rel_upd:
        c = state["data_cache"].setdefault("rel_strength_1m", {})
        c.setdefault("values_pp", {}).update(rel_upd)
        c["benchmark"] = "SMH"
        if rel_raw.get("benchmark_return_1m_pct") is not None:
            c["benchmark_return_1m_pct"] = rel_raw["benchmark_return_1m_pct"]
        c["as_of"] = today

    peer_upd = out.get("peer_map_updates", {}) or {}
    if peer_upd:
        state.setdefault("peer_map", {}).update(peer_upd)
    return {"signal_history_changed": list(changed), "stamped": len(stamp_tickers),
            "analyst_targets_updated": len(targets), "peer_map_updated": len(peer_upd),
            "ret_5d_updated": len((r5.get("values_pct") or {}) if r5 else {}),
            "rsi14_updated": len(rsi_upd), "atr20_updated": len(atr_upd),
            "rel_strength_1m_updated": len(rel_upd),
            "rel_strength_1m_rejected": rel_rejected,
            "journal_new_added": added if jn else []}


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
    """Merge refreshed betas -- and REFUSE to relabel a foreign benchmark as SMH.

    This hardcoded `"benchmark": "SMH"` on every write regardless of what the agent actually
    computed. Found live 2026-08-30: smith-book returned 21 betas and said plainly in its own
    data_quality that they were "yfinance NATIVE (SPX-benchmarked), not SMH". Merging them would
    have stamped SPX betas as SMH ones -- and SKILL.md 2.7 is explicit that the SPX beta is
    "actively misleading" for this book (it predicted +0.075% for a session that delivered
    -5.06%), which is the entire reason the desk moved to SMH.

    The agent was honest; the merge rule was not listening. A label written by the consumer
    rather than the producer is not provenance, it is an assumption wearing provenance's clothes.
    """
    betas = out.get("refreshed_betas", {})
    bench = (out.get("beta_benchmark") or "").upper()
    if betas and bench and bench != "SMH":
        return {"betas_refreshed": [], "betas_rejected": len(betas),
                "reason": f"agent returned {bench}-benchmarked betas; this book's betas are "
                          f"SMH-benchmarked and an SPX beta is documented as actively "
                          f"misleading here. Not merged, cache left intact."}
    if betas and not bench:
        return {"betas_refreshed": [], "betas_rejected": len(betas),
                "reason": "agent did not state `beta_benchmark`; refusing to assume SMH. "
                          "Return beta_benchmark:'SMH' explicitly to merge."}
    for tk, v in betas.items():
        state["data_cache"].setdefault("betas", {})[tk] = {"value": v, "as_of": today, "benchmark": "SMH"}
    if betas:
        state["data_cache"]["betas"]["as_of"] = today
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
    if ec:
        state["data_cache"].setdefault("earnings_calendar", {}).update(ec)
        state["data_cache"]["earnings_calendar"]["as_of"] = today
    setups = out.get("watchlist_setups")
    if setups is not None:
        state["watchlist_setups"] = setups  # REPLACE: a setup list is point-in-time, like catalysts
    return {"watchlist_scan_cursor": cursor, "watchlist_setups_replaced": setups is not None}


def _merge_macro(out, state, today):
    upd = out.get("fomc_cache_update")
    if upd is not None:
        state["fomc_cache"] = upd
    return {"fomc_cache_updated": upd is not None}


def _merge_cycle(out, state, today):
    """smith-cycle's position had NO merge rule and NO state key, despite SKILL.md 3 saying
    'persist its position and date so the next run can check the falsifier' and calling it the
    highest-leverage single read on the book. Same shape as G50: dispatched, then discarded."""
    pos = out.get("cycle_position")
    if pos is not None:
        state["cycle_position"] = {
            "position": pos,
            "confidence": out.get("confidence"),
            # The falsifier is the whole point -- a cycle call nothing can disprove is a mood.
            "falsifier": out.get("falsifier"),
            "as_of": today,
        }
    return {"cycle_position": pos}


def _merge_quality(out, state, today):
    """The monthly audit's cadence was inferred from 'were there deep rows in ledger.csv this
    month', which tests whether a DEEP RUN happened, not whether QUALITY ran. Persist the read
    itself so the trigger can test the real thing.

    MERGES PER TICKER, never replaces (changed 2026-08-31). The audit is budget-bound and
    routinely covers PART of the book -- the 08-30 run reached 8 of the top 15 and stopped, so
    the 7 remaining names were audited in a second pass. Under the previous wholesale-replace
    the second pass would have silently deleted the first pass's 8 findings AND the
    primary-source verification block attached to them, leaving a `quality_read` that looked
    complete and covered a third of what it claimed. Partial coverage is the NORMAL case for
    this agent, so the merge has to be additive: same-ticker findings are overwritten by the
    newer audit, untouched tickers survive, and any sibling key (e.g. primary_source_
    verification) is preserved rather than clobbered.

    `audited_on` per ticker is what makes partial coverage legible afterwards -- without it a
    name audited five weeks ago is indistinguishable from one audited today."""
    flags = out.get("quality_flags")
    cleared = out.get("cleared") or []
    if flags is None and not cleared:
        return {"quality_flags": 0, "note": "no quality_flags key in tail"}
    flags = flags or {}
    prior = state.get("quality_read") or {}
    merged = dict(prior.get("quality_flags") or {})
    merged.update(flags)
    audited = dict(prior.get("audited_on") or {})
    for tk in list(flags) + list(cleared):
        audited[tk] = today
    cleared_all = sorted(set(prior.get("cleared") or []) - set(flags) | set(cleared))
    ftr = {r.get("ticker"): r for r in (prior.get("force_thesis_review") or [])
           if isinstance(r, dict) and r.get("ticker")}
    for r in (out.get("force_thesis_review") or []):
        if isinstance(r, dict) and r.get("ticker"):
            ftr[r["ticker"]] = r
    read = dict(prior)                      # keep siblings (primary_source_verification, ...)
    read.update({"quality_flags": merged,
                 "cleared": cleared_all,
                 "audited_on": audited,
                 "force_thesis_review": list(ftr.values()),
                 "book_pct_flagged": out.get("book_pct_flagged"),
                 "top_concern": out.get("top_concern") or prior.get("top_concern"),
                 "as_of": today})
    state["quality_read"] = read
    return {"quality_flags": len(merged), "flags_this_pass": len(flags),
            "cleared_this_pass": len(cleared), "tickers_audited_total": len(audited),
            "force_thesis_review": len(ftr)}


def _merge_tax(out, state, today):
    # smith-tax's whole tail IS the read -- there is no single `tax_read` key to lift. Store the
    # decision-bearing fields and stamp them; the full tail stays in the run dir as always.
    if not any(k in out for k in ("lot_file_state", "ltcg_window", "trim_sequencing")):
        return {"tax_read_updated": False, "note": "tail carried no tax fields"}
    state["tax_read"] = {"lot_file_state": out.get("lot_file_state"),
                         "ltcg_window": out.get("ltcg_window"),
                         "trim_sequencing": out.get("trim_sequencing", []),
                         "harvest_candidates": out.get("harvest_candidates", []),
                         "fy_window": out.get("fy_window"),
                         "as_of": today}
    return {"tax_read_updated": True,
            "trim_sequencing": len(out.get("trim_sequencing", []) or [])}


def _merge_rebound(out, state, today):
    """smith-rebound had NO merge rule and NO state key, so every candidate list it ever
    produced was discarded at the end of the run -- the 2026-08-24 run named four rebuy
    candidates and none of them survived to the next run, the dashboard or any report. Same
    shape as the cycle_position and factor_catalysts (G50) losses: an agent dispatched, its
    output landing nowhere the persist table names.

    That is also part of why the agent looked unused. It was not only being skipped; on the
    runs it DID work, nothing kept what it found."""
    props = out.get("proposals")
    if props is None:
        return {"rebound_candidates": 0, "note": "tail carried no proposals array"}
    state["rebound_candidates"] = {
        "as_of": today,
        "correction_state": out.get("correction_state"),
        "gate": out.get("gate", {}),
        "candidates": props,
        "considered_excluded": out.get("considered_excluded", []),
    }
    return {"rebound_candidates": len(props)}


# Which state keys each agent OWNS the freshness of. After a successful merge, `<key>_as_of`
# is stamped so smith_core.FRESHNESS can age it. Generalises the one case that already worked
# (signal_history_as_of) instead of leaving every other artefact undateable -- which is how
# factor_themes reached 33 days and `thesis` reached 35 entries with no review date at all.
# Keys whose stamp lives INSIDE the artefact (macro_read.as_of, cycle_position.as_of) are set
# by their merge function and deliberately absent here -- one writer per stamp.
MERGE_STAMPS = {
    "thesis":    ["sector_map"],
    "signals":   ["peer_map"],
    "catalyst":  ["factor_themes"],
    # scout: diversifier_candidates carries its own per-entry `as_of`; no sibling stamp.
    "watchlist": ["watchlist_setups"],
}


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
    "rebound": _merge_rebound,
    "cycle": _merge_cycle,
    "quality": _merge_quality,
    "tax": _merge_tax,
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
    by MERGE_RULES (currently: ledger, strategist -- their state
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
            extra["base_dir"] = args.base_dir
        results[agent] = MERGE_RULES[agent](out, state, today, **extra)
        for key in MERGE_STAMPS.get(agent, []):
            state[f"{key}_as_of"] = today

    safe_write(state_path, state)
    emit({"merged": list(results), "results": results,
          "skipped_no_output_file": skipped_no_file, "skipped_no_merge_rule": skipped_no_rule,
          "written": True,
          "next_step": "run smith_math.py validate before trusting this state"})


# NOTE (2026-08-30): TECHNICAL_CACHE_HARD_STALE_DAYS and validate_technical_cache_staleness
# lived here and have been retired into smith_core.FRESHNESS + validate_freshness, which check
# rsi14/rel_strength_1m through the same declarative table as every other artefact instead of
# as a one-off. Running both produced two defects per cache saying the same thing with
# different thresholds in the text. The original rationale is kept, because it is the clearest
# statement of why FRESHNESS exists at all:
#
#   cmd_triggers already suppressed oversold_reversion/overbought_distribution/laggard_rotation
#   whenever the cache passed TRIGGER_CACHE_MAX_AGE_DAYS -- correct behaviour for a single
#   stale run. But by 2026-08-29 that had happened on THREE CONSECUTIVE runs (two deep, one
#   quick), each reported as one line in that run's data_quality and each deferred again "on
#   cost grounds", while oversold/overbought remained the single most-requested feature in this
#   desk's history. A per-run soft note that nobody is forced to act on is exactly how a
#   standing request goes dark for weeks without anyone deciding that on purpose.
#
# The original escalation threshold was TRIGGER_CACHE_MAX_AGE_DAYS * 2, so the system was
# DESIGNED to tolerate up to 10 FURTHER days of dark triggers before saying anything loudly --
# on 2026-08-30 the caches were 18 days old and validate still reported clean. FRESHNESS sets
# the dark line at the suppression floor itself for suppress-class artefacts: escalation fires
# when the capability dies, not at twice that. The stale_ack_on escape hatch survives unchanged.


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
        policy_defects = validate_policy(policy, state)

    cache_defects = validate_cache_events(state)
    thesis_defects = validate_thesis_schema(state, args.base_dir)
    learning_defects = validate_learning_schema(args.base_dir)
    proposals_defects = validate_proposals_schema(args.base_dir)
    narrative_defects = validate_policy_narrative_drift(args.base_dir)
    earnings_pending_defects = validate_pending_earnings_staleness(args.base_dir)
    freshness_defects = validate_freshness(args.base_dir)
    ledger_defects = validate_ledger_schema(args.base_dir)
    aggrisk_defects = validate_aggregate_risk(args.base_dir, state)
    all_defects = (policy_defects + cache_defects + thesis_defects + learning_defects
                   + proposals_defects + narrative_defects
                   + earnings_pending_defects + freshness_defects + ledger_defects
                   + aggrisk_defects)

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
    # Absolute for the same reason as refs: the reader is a sub-agent with its own cwd.
    sl["read_these_files"][key] = os.path.abspath(path)


def _thesis_tiers(thesis, state, base_dir):
    """Split the thesis map into names this run may ACT on (full text + both evidence arrays)
    and the quiet remainder (status only).

    SKILL.md 3 has prescribed exactly this since 2026-08-07 and nobody implemented it -- the
    slice shipped the whole map. Measured on the 2026-08-25 run that map was 32-35KB and went
    to three agents, and because it legitimately changes mid-run, content-addressing correctly
    produced TWO copies in one run directory: 68KB of one artefact.

    The tiering is safe precisely because G48 and G58 were both about names being ACTED ON:
    G48, a WATCH verdict that could not be revised because its slice carried only the status
    word and not the original rationale; G58, a verdict that could not be CHALLENGED downstream
    because its countervailing evidence had been dropped. Both hazards live entirely in the
    full tier, which keeps the complete text and BOTH arrays. A name that is intact, quiet,
    unflagged and carries no open proposal is not being reasoned about this run.

    `note` states which names got which treatment, because the same section requires saying so
    -- a reader who cannot tell a trimmed entry from a complete one will read absence of
    evidence as absence of evidence.
    """
    props = load_json(os.path.join(base_dir, "proposals.json"), default={}).get("proposals", [])
    open_tickers = {p.get("ticker") for p in props if p.get("status") == "open"}
    # "anything in this run's signal buckets" (SKILL.md 3's wording) does not discriminate on
    # this book: TARGET GAP alone fires on ~28 of 31 names, so ANY-bucket qualified 30 of 31
    # and the tiering saved nothing. The intent behind the wording is "names likely to be acted
    # on", and what puts a thesis at risk of REVISION is a BEARISH read, not a bullish or
    # ambiguous one -- a name with a bullish TARGET GAP is not about to have its verdict
    # challenged. Bearish buckets only, per smith_risk.SIGNAL_POLARITY.
    bearish = smith_risk.SIGNAL_POLARITY.get("bearish", set())
    flagged = {t for t, b in (state.get("signal_history") or {}).items()
               if any(x in bearish for x in (b or []))}
    full, brief = {}, {}
    for t, entry in thesis.items():
        status = smith_risk.thesis_status(entry)
        act = (status not in HEALTHY_THESIS) or (t in flagged) or (t in open_tickers)
        if act or not isinstance(entry, dict):
            full[t] = entry
        else:
            brief[t] = {"status": status, "verified": entry.get("verified"),
                        "reviewed_on": entry.get("reviewed_on"),
                        "_trimmed": "quiet name -- intact/strengthening, no live signal bucket, "
                                    "no open proposal. Full text and both evidence arrays are in "
                                    "state.json; ask for it if you need to revise this verdict."}
    return full, brief, open_tickers, flagged


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
            if k == "thesis" and isinstance(v, dict):
                full, brief, open_t, flagged = _thesis_tiers(v, state, base)
                v = dict(full)
                v.update(brief)
                sl["thesis_tiering"] = {
                    "full_text": sorted(full), "status_only": sorted(brief),
                    "reason_full": "watch/broken status, a BEARISH signal bucket, or an open proposal",
                    "note": (f"{len(full)} of {len(full) + len(brief)} entries carry full text and "
                             f"both evidence arrays; the remaining {len(brief)} are quiet names "
                             f"reduced to status. This is a TRIM, not an absence of evidence -- "
                             f"if you need to revise a status-only verdict, say so and ask for it."),
                }
            if k == "open_flags":
                v = (v or [])[-FLAGS_CAP:]
            _place(sl, k, v, shared_dir, shared_once)
        for k in spec["cache"]:
            _place(sl, f"data_cache.{k}", dc.get(k), shared_dir, shared_once)

        for r in spec.get("refs", []):
            # ABSOLUTE, always (fixed 2026-08-30). These paths were emitted relative to the
            # orchestrator's cwd -- "./lots.json", "runs/<ts>/compute_book.json". A sub-agent
            # does not share that cwd (it runs from the session's own working directory), so a
            # relative ref resolves to nothing on its side. smith-book hit this live on the
            # 2026-08-30 deep run: "lots.json not found at the supplied path this run", and it
            # degraded to the orchestrator's prose instead of reading the file. Silent, because
            # a missing optional input just produces a thinner answer.
            path = (os.path.join(rd, REF_FILES[r]) if r in REF_FILES
                    else os.path.join(base, BASE_REF_FILES[r]) if r in BASE_REF_FILES else None)
            path = os.path.abspath(path) if path else None
            if path is None:
                problems.append(f"smith-{agent}: unknown ref '{r}'")
            elif not os.path.exists(path):
                problems.append(f"smith-{agent}: {os.path.basename(path)} MISSING -- run the "
                                f"pipeline before rendering slices")
            else:
                sl["read_these_files"][r] = path
        for sname in spec.get("shared", []):
            if sname in shared_paths:
                sl["read_these_files"][sname] = os.path.abspath(shared_paths[sname])
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


# ---------------------------------------------------------------------------
# FRESHNESS EVALUATION (added 2026-08-30) -- the enforcer for smith_core.FRESHNESS
# ---------------------------------------------------------------------------
# smith_core.FRESHNESS declares WHAT may go stale and what staleness means. This is the half
# that actually looks. Deliberately one pass over one table rather than a per-artefact check
# bolted on wherever someone happened to notice, which is how the codebase arrived at three
# age constants covering nine declared TTLs.
#
# Note the fifth state, `unstamped`, which is not the same as `missing`: the artefact is
# present and in active use but carries no date at all, so its age is UNKNOWABLE rather than
# large. `thesis` was in exactly this position -- 35 live entries, no review date on any of
# them, feeding a live trigger and outranking computed drift breaches under SKILL.md §2g. An
# unknown age is worse than a known-bad one, because nothing can even flag it.

def freshness_root(base_dir, state=None):
    """The lookup root for FRESHNESS keys.

    Almost every tracked artefact lives in state.json, so the root IS state -- but not all of
    them. `proposals.scorecard` lives in proposals.json, and until 2026-08-31 that meant the
    outcome scorecard was the one decision-bearing artefact with NO freshness coverage at all.
    It had been frozen at 2026-08-29 and nothing said so: `score` correctly refused to shrink
    it (19 rows on record, only 14 gradable), because the orchestrator's price source is
    holdings.json and 6 of the 19 rows reference tickers that are NOT HELD -- exited names,
    watchlist names and GOOGL against a book that holds GOOG. A correct anti-shrink guard plus
    a structurally incomplete price source is a permanent deadlock, and a deadlock nobody can
    see is indistinguishable from a healthy artefact.

    Exposing proposals.json under the `proposals.` prefix keeps FRESHNESS a flat declarative
    table rather than growing per-artefact file-loading special cases.
    """
    root = dict(state if state is not None
                else load_json(os.path.join(base_dir, "state.json"), default={}))
    root["proposals"] = load_json(os.path.join(base_dir, "proposals.json"), default={})
    return root


def _fresh_lookup(state, dotted):
    node = state
    for part in dotted.split("."):
        if not isinstance(node, dict):
            return None
        node = node.get(part)
    return node


def _fresh_stamp(state, artefact, spec):
    """Resolve an artefact's as_of date per its `stamp` rule. Returns (date_str, detail)."""
    kind, _, name = spec.partition(":")
    if kind == "field":
        return (artefact.get(name) if isinstance(artefact, dict) else None), None
    if kind == "sibling":
        return state.get(name), None
    if kind == "max_date":
        dates = [r.get("date") for r in artefact if isinstance(r, dict) and r.get("date")] \
            if isinstance(artefact, list) else []
        return (max(dates) if dates else None), None
    if kind == "per_entry":
        # Stamps may live in a sibling map keyed by ticker (signal_history_as_of) or on each
        # entry itself (diversifier_candidates[t].as_of). Try the sibling map first.
        stamps = {}
        sibling = state.get(name)
        if isinstance(sibling, dict) and isinstance(artefact, dict):
            stamps = {k: v for k, v in sibling.items()
                      if k in artefact and isinstance(v, str)}
        if not stamps and isinstance(artefact, dict):
            stamps = {k: v.get(name) for k, v in artefact.items()
                      if isinstance(v, dict) and isinstance(v.get(name), str)}
        if not stamps:
            return None, None
        oldest = min(stamps.values())
        # The age of the OLDEST entry is the artefact's age -- a map-level date would hide
        # precisely the names nobody has looked at, which is the whole reason for per-entry.
        unstamped = [k for k in (artefact or {}) if k not in stamps]
        detail = {"entries_stamped": len(stamps), "entries_unstamped": len(unstamped),
                  "oldest_entries": sorted(k for k, v in stamps.items() if v == oldest)[:5]}
        if unstamped:
            detail["unstamped_sample"] = sorted(unstamped)[:5]
        return oldest, detail
    return None, None


def evaluate_freshness(state, today=None):
    """Return one row per FRESHNESS artefact: age, ttl, owner, and fresh|stale|dark|unstamped|missing."""
    today = today or date.today()
    rows = []
    for key, cfg in FRESHNESS.items():
        artefact = _fresh_lookup(state, key)
        ttl = cfg["ttl_days"]
        on_stale = cfg["on_stale"]
        mult = DARK_MULTIPLIER.get(on_stale)
        dark_at = TRIGGER_CACHE_MAX_AGE_DAYS if mult is None else int(ttl * mult)
        row = {"key": key, "owner": cfg["owner"], "ttl_days": ttl, "on_stale": on_stale,
               "dark_at_days": dark_at, "as_of": None, "age_days": None, "state": None}

        if artefact is None or (isinstance(artefact, (dict, list, str)) and len(artefact) == 0):
            row["state"] = "missing"
            rows.append(row)
            continue

        as_of, detail = _fresh_stamp(state, artefact, cfg["stamp"])
        if detail:
            row.update(detail)
        if not as_of:
            row["state"] = "unstamped"
            rows.append(row)
            continue

        try:
            age = (today - datetime.strptime(str(as_of)[:10], "%Y-%m-%d").date()).days
        except (ValueError, TypeError):
            row["as_of"] = as_of
            row["state"] = "unstamped"
            rows.append(row)
            continue

        row["as_of"], row["age_days"] = as_of, age
        row["state"] = "fresh" if age <= ttl else ("dark" if age > dark_at else "stale")
        # A map is only as current as its least-examined entry. Taking the oldest STAMPED
        # entry's age silently skips entries with no stamp at all -- precisely the names
        # nobody has looked at -- so a partially-stamped map may never read as fresh.
        if row.get("entries_unstamped") and row["state"] == "fresh":
            row["state"] = "stale"
            row["partial"] = True
        # Same one-day written-acknowledgement escape hatch as validate_technical_cache_staleness:
        # skipping a refresh is allowed, pretending it didn't happen is not.
        ack = artefact.get("stale_ack_on") if isinstance(artefact, dict) else None
        ack = ack or state.get(key.split(".")[-1] + "_stale_ack_on")
        if row["state"] == "dark" and ack == today.isoformat():
            row["state"], row["acknowledged"] = "stale", True
        rows.append(row)
    return rows


def validate_aggregate_risk(base_dir, state):
    """Fail when the book's aggregate open risk exceeds its own policy cap.

    `cmd_risk` computes `aggregate_open_risk_pct` and `aggregate_over_cap` on EVERY run and no
    validator ever read them. That is how a breach ran for weeks as a line in a table: 11.947%
    against a 10% cap on 2026-08-30, and 13.028% on 08-26. The stop framework's own rationale
    still claims worst-case-if-every-stop-fires is "~7.4% of book, deliberately inside the -15%
    drawdown_warn rung" -- a stated safety property that stopped being true and that nothing was
    positioned to notice.

    Reads the newest run's compute_risk.json rather than recomputing: this is a validator, not a
    second implementation of the risk math (ONE FIELD, ONE READER).
    """
    # Prefer `latest_run_dir` (stamped by cmd_pipeline, always the run just completed) and fall
    # back to `last_run_dir` only when it is absent. See cmd_pipeline: `last_run_dir` means the
    # PREVIOUS run to _prior_run_prices, and trusting it here graded a two-day-old file on
    # 2026-08-31 -- reporting a 13.183% breach that a fresh ATR20 had already resolved to 9.331%.
    rd = state.get("latest_run_dir") or state.get("last_run_dir")
    path = os.path.join(base_dir, rd, "compute_risk.json") if rd else None
    if not path or not os.path.exists(path):
        return []  # no run yet, or pruned -- absence is not a defect
    risk = load_json(path, default={})
    if not risk.get("aggregate_over_cap"):
        return []
    return [f"AGGREGATE OPEN RISK OVER CAP: {risk.get('aggregate_open_risk_pct')}% against a "
            f"{risk.get('aggregate_open_risk_cap_pct')}% policy cap "
            f"(${risk.get('aggregate_open_risk_usd', 0):,.0f}). Every new position competes for a "
            f"budget that is already overdrawn, so a rebound or re-entry must be FUNDED by "
            f"reducing risk elsewhere, not added on top."]


def validate_ledger_schema(base_dir):
    """Every ledger.csv row must have exactly as many fields as the header.

    Found 2026-08-30: four rows (2026-07-29, 08-25, 08-26, 08-29) carried TWELVE fields against
    a thirteen-column header, having omitted `external_flow_usd`. Every column from `smh`
    onward was therefore shifted left by one, which put the run narrative into `value_trust`
    and the trust flag into `external_flow_usd`.

    That is not cosmetic. smith_charts' stated honesty constraint is that ledger rows whose
    `value_trust` is not `ok` are drawn ringed and EXCLUDED from scales and win/loss counts --
    so a shifted row reads as untrusted and silently drops out of every chart. Four of
    thirty-nine rows, including the three most recent, were being excluded from the desk's own
    performance history by a missing comma.

    A column-count check is the cheapest possible guard and there was none. Note this is NOT a
    cmd_append_ledger bug -- that function builds all thirteen fields correctly, and the oldest
    bad row predates it by a month. These were hand-written rows, which is the same argument
    for a sanctioned write path that G84 already made.
    """
    import csv as _csv
    path = os.path.join(base_dir, "ledger.csv")
    if not os.path.exists(path):
        return []
    with open(path, newline="") as fh:
        rows = list(_csv.reader(fh))
    if not rows:
        return []
    n = len(rows[0])
    bad = [(r[0] if r else "?", len(r)) for r in rows[1:] if len(r) != n]
    if not bad:
        return []
    return [f"LEDGER SCHEMA: {len(bad)} row(s) do not have {n} fields "
            f"({', '.join(f'{ts} has {k}' for ts, k in bad[:5])}) -- a short row shifts every "
            f"later column, which puts prose into value_trust and silently excludes the row "
            f"from every chart (smith_charts drops value_trust != 'ok'). Repair by reinserting "
            f"the omitted column, and append rows only via `smith_math.py append-ledger`."]


def validate_freshness(base_dir):
    """Turn the freshness table into hard `validate` defects.

    Proportionality is the whole design here. A DARK artefact is a defect regardless of class,
    because dark means a capability is genuinely off -- that is the rsi14 case this was built
    for. But `missing` and `unstamped` are only defects for the ESCALATE class: those are the
    artefacts with no downstream consumer that suppresses on them, so nothing else in the
    system would ever notice. A flag-class cache that is merely absent (analyst_targets) shows
    up as a freshness row and stays out of the defect list -- otherwise validate goes
    permanently red and stops meaning anything, which is the failure mode one level up from
    the one this fixes.
    """
    state = load_json(os.path.join(base_dir, "state.json"), default={})
    defects = []
    for row in evaluate_freshness(freshness_root(base_dir, state)):
        key, owner, st = row["key"], row["owner"], row["state"]
        if st == "dark":
            defects.append(
                f"FRESHNESS DARK: {key} is {row['age_days']}d old (ttl {row['ttl_days']}d, dark "
                f"past {row['dark_at_days']}d, owner {owner}) -- its consumer has stopped using "
                f"it. Refresh it this run, or set stale_ack_on to today's date to record that "
                f"skipping it again was a deliberate, dated choice.")
        elif st == "unstamped" and row["on_stale"] == "escalate":
            defects.append(
                f"FRESHNESS UNSTAMPED: {key} is present and in use but carries no date, so its "
                f"age cannot be checked at all (owner {owner}). An unknown age is worse than a "
                f"known-bad one -- nothing can flag it. Stamp it on the next merge-tails.")
        elif st == "missing" and row["on_stale"] == "escalate":
            defects.append(
                f"FRESHNESS MISSING: {key} does not exist in state.json, though {owner} is "
                f"meant to produce it (ttl {row['ttl_days']}d). Either the agent has not run "
                f"or its output is being discarded at PERSIST -- the G50 shape.")
    return defects


def cmd_freshness(args):
    """Report every FRESHNESS artefact's age and state; write compute_freshness.json if asked."""
    state = load_json(os.path.join(args.base_dir, "state.json"), default={})
    today = datetime.strptime(args.today, "%Y-%m-%d").date() if args.today else date.today()
    rows = evaluate_freshness(freshness_root(args.base_dir, state), today)
    by_state = {}
    for r in rows:
        by_state.setdefault(r["state"], []).append(r["key"])
    payload = {
        "as_of": today.isoformat(),
        "counts": {k: len(v) for k, v in sorted(by_state.items())},
        "dark": sorted(by_state.get("dark", [])),
        "unstamped": sorted(by_state.get("unstamped", [])),
        "missing": sorted(by_state.get("missing", [])),
        "stale": sorted(by_state.get("stale", [])),
        "artefacts": rows,
        # One line the briefing header can print verbatim -- the point of this whole table is
        # that staleness is SEEN, not logged somewhere nobody is obliged to look.
        "headline": _freshness_headline(rows),
    }
    emit(payload)


def _freshness_headline(rows):
    dark = [r for r in rows if r["state"] == "dark"]
    blind = [r for r in rows if r["state"] in ("unstamped", "missing") and r["on_stale"] == "escalate"]
    if not dark and not blind:
        return "Freshness: all artefacts within TTL."
    bits = []
    if dark:
        bits.append("DARK " + ", ".join(f"{r['key']} {r['age_days']}d" for r in dark))
    if blind:
        bits.append("UNCHECKABLE " + ", ".join(f"{r['key']} ({r['state']})" for r in blind))
    return "Freshness: " + " | ".join(bits)


# ---------------------------------------------------------------------------
# REPORTS (added 2026-08-30) -- the durable dated record
# ---------------------------------------------------------------------------
# Until now the desk produced exactly two things: a chat briefing that existed only in
# scrollback, and ONE dashboard artifact overwritten on every run. So there was no dated daily
# record, no week-over-week view, and no way to ask "what did I actually do against what was
# proposed" without re-reading a month of transcripts. `briefing.md` per run dir arrived
# 2026-08-29 and is a pointer, not a report.
#
# GENERATED, NEVER HAND-AUTHORED -- the same rule that governs the dashboard, for the same
# reason that G84 records: a hand-typed narrative is the medium a fact drifts in. A nonexistent
# "8% drawdown warn line" (policy.json says 15) was typed once and copied forward across four
# consecutive runs before anyone checked it. Every number below is read from state, the compute
# files, or the ledger; nothing here is retyped.
#
# The daily is written on EVERY run including a market-closed mini-briefing, so the series has
# no holes that would read as missed runs.

def _r_money(x):
    return "n/a" if x is None else f"${x:,.2f}"


def _r_pct(x, dp=2):
    return "n/a" if x is None else f"{x:+.{dp}f}%"


def _iso_week(d):
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def _read_ledger(base_dir):
    import csv as _csv
    path = os.path.join(base_dir, "ledger.csv")
    if not os.path.exists(path):
        return []
    with open(path, newline="") as fh:
        return list(_csv.DictReader(fh))


def _ledger_date(row):
    try:
        return datetime.fromisoformat(row["ts"]).date()
    except (ValueError, TypeError, KeyError):
        return None


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _report_daily(base_dir, run_dir, today, state, freshness_rows):
    L = []
    ledger = _read_ledger(base_dir)
    cur = ledger[-1] if ledger else {}
    prev = ledger[-2] if len(ledger) > 1 else {}
    us = state.get("us", {}) or {}

    def compute(name):
        return load_json(os.path.join(run_dir, f"compute_{name}.json"), default={}) if run_dir else {}

    book, triggers = compute("book"), compute("triggers")
    universe, drift = compute("universe"), compute("drift")

    L.append(f"# Agent Smith — daily · {today.isoformat()}")
    L.append("")
    L.append(f"*Generated by `smith_math.py report`. Mode: {cur.get('mode', 'unknown')}. "
             f"Nothing in this file is hand-typed.*")
    L.append("")

    # --- 1. the number -------------------------------------------------------
    val = book.get("value_usd") or _f(cur.get("value_usd")) or us.get("value_usd")
    # The delta compares this run's book against the PREVIOUS ledger row, so it is only
    # meaningful if this run is actually the newest thing on record. Pointing the report at an
    # older run directory would otherwise render a confident backwards number -- the run dir
    # supplies `val` while the ledger supplies `pval`, and nothing forced them into order.
    cur_date = _ledger_date(cur)
    stale_run = bool(run_dir and cur_date and cur_date > today)
    pval = _f(prev.get("value_usd"))
    delta = (val - pval) if (val is not None and pval and not stale_run) else None
    delta_pct = (100.0 * delta / pval) if (delta is not None and pval) else None
    L.append("## The number")
    L.append("")
    L.append(f"| metric | value |\n|---|---|")
    L.append(f"| Book value | {_r_money(val)} |")
    L.append(f"| Change vs last run | " + (
        f"not shown — the newest ledger row ({cur_date}) is later than this report's date "
        f"({today}), so a delta would compare across the wrong direction"
        if stale_run else f"{_r_money(delta)} ({_r_pct(delta_pct)})") + " |")
    L.append(f"| P&L | {_r_pct(book.get('pnl_pct') if book.get('pnl_pct') is not None else us.get('pnl_pct'))} |")
    L.append(f"| Drawdown | {_r_pct(book.get('drawdown_pct') if book.get('drawdown_pct') is not None else us.get('drawdown_pct'))} |")
    cash_pct = drift.get("cash_pct")
    band = drift.get("cash_band_pct") or []
    L.append(f"| Cash | {_r_pct(cash_pct, 2) if cash_pct is not None else 'n/a'}"
             f"{f' (band {band[0]}–{band[1]}%)' if len(band) == 2 else ''} |")
    L.append(f"| Risk-off status | {drift.get('risk_off_status', 'n/a')} |")
    L.append("")

    # --- 2. freshness: how much to trust the rest ----------------------------
    L.append("## Freshness")
    L.append("")
    L.append(_freshness_headline(freshness_rows))
    bad = [r for r in freshness_rows if r["state"] != "fresh"]
    if bad:
        L.append("")
        L.append("| artefact | state | age | ttl | owner |\n|---|---|---|---|---|")
        for r in sorted(bad, key=lambda r: (r["state"] != "dark", r["key"])):
            L.append(f"| `{r['key']}` | {r['state']} | {r['age_days'] if r['age_days'] is not None else '—'}d "
                     f"| {r['ttl_days']}d | {r['owner']} |")
    L.append("")

    # --- 3. can the desk actually generate an idea today? --------------------
    if triggers:
        lc = triggers.get("live_counts", {}) or {}
        fired = {k: v for k, v in lc.items() if v}
        L.append("## Trigger layer")
        L.append("")
        L.append(f"- RSI cache: {'usable' if triggers.get('rsi_usable') else '**DARK**'} "
                 f"({triggers.get('rsi_age_days')}d old, {triggers.get('rsi_coverage_pct')}% coverage)")
        L.append(f"- Relative strength: {'usable' if triggers.get('rel_usable') else '**DARK**'} "
                 f"({triggers.get('rel_age_days')}d old, {triggers.get('rel_coverage_pct')}% coverage)")
        L.append(f"- Deployable cash for ideas: {_r_money(triggers.get('deployable_cash_for_ideas_usd'))}")
        L.append(f"- Live triggers fired: {', '.join(f'{k} ×{v}' for k, v in sorted(fired.items())) or 'none'}")
        L.append("")

    # --- 3b. correction state + rebound candidates ---------------------------
    reb = (triggers or {}).get("rebound") or {}
    if reb:
        L.append("## Correction & rebound")
        L.append("")
        cs = reb.get("correction_state", "none")
        L.append(f"**correction_state: {cs}**"
                 + (f" — {'; '.join(reb.get('reasons') or [])}" if reb.get("reasons") else ""))
        L.append("")
        if cs == "none":
            L.append("No broad correction by drawdown, benchmark or breadth — smith-rebound not dispatched.")
        else:
            L.append("smith-rebound dispatches on this state — not on stop-outs, spare cash, or the "
                     "pre-market gate, each of which wrongly suppressed it before.")
            if reb.get("stale_warning"):
                L.append("")
                L.append(f"> {reb['stale_warning']}")
            cands = reb.get("candidates") or []
            if cands:
                L.append("")
                L.append("| ticker | tier | fall | window | ATR20 | fall / ATR | score | thesis |\n|---|---|---|---|---|---|---|---|")
                for c in cands[:8]:
                    # `fall_pct` + `fall_window` since the 5-day rewrite -- the 1-month figure
                    # survives only as an explicitly labelled fallback, and the two are not
                    # comparable magnitudes, so the window is shown rather than assumed.
                    win = c.get("fall_window") or "?"
                    L.append(f"| {c['ticker']} | {c['tier'].split('_', 1)[1].lower()} | "
                             f"{c.get('fall_pct')}% | {win} | {c['atr20_pct']}% | "
                             f"{c['fall_atr_mult']}× | {c['rebound_score']} | "
                             f"{c.get('thesis_status') or '**none**'} |")
                L.append("")
                L.append("*Ranked on the mandate — fall depth × volatility, where high volatility is the "
                         "thesis. `fall / ATR` is the counterweight: under ~1.5× is a loud name being "
                         "loud rather than a dislocation. Size with it; never veto on it.*")
            else:
                L.append("")
                L.append("No candidates cleared the screen (fall depth, volatility floor, falling-knife "
                         "thesis gate). See `compute_triggers.json` → `rebound.excluded` for what was "
                         "considered and why each was dropped.")
            if reb.get("thesis_gap"):
                L.append("")
                L.append(f"*{reb['thesis_gap']}*")
        L.append("")

    # --- 4. the candidate set ------------------------------------------------
    if universe:
        c = universe.get("counts", {})
        L.append("## Universe")
        L.append("")
        parts = ", ".join(f"{k.split('_', 1)[1].lower()} {v}" for k, v in c.items() if v)
        supp = universe.get("suppressed_count") or 0
        L.append(f"{universe.get('total', 0)} candidates — {parts}"
                 + (f" · {supp} suppressed" if supp else ""))
        L.append("")

    # --- 5. open proposals ---------------------------------------------------
    props = load_json(os.path.join(base_dir, "proposals.json"), default={}).get("proposals", [])
    open_props = [p for p in props if p.get("status") == "open"]
    L.append("## Open proposals")
    L.append("")
    if not open_props:
        L.append("None open. *(\"No proposals — book within policy\" beats manufactured activity.)*")
    else:
        L.append("| id | priority | action | size | trigger | rationale |\n|---|---|---|---|---|---|")
        for p in sorted(open_props, key=lambda p: -(p.get("priority_score") or 0)):
            rat = (p.get("rationale") or "").replace("|", "\\|").replace("\n", " ")
            L.append(f"| {p.get('id')} | {p.get('priority')} | {p.get('action')} | "
                     f"{_r_money(p.get('size_usd'))} | {p.get('trigger_type') or '—'} | {rat[:160]} |")
    L.append("")

    # --- 6. thesis -----------------------------------------------------------
    thesis = state.get("thesis", {}) or {}
    counts = {}
    for v in thesis.values():
        st = smith_risk.thesis_status(v) or "unreadable"
        counts[st] = counts.get(st, 0) + 1
    reviewed = [t for t, v in thesis.items()
                if isinstance(v, dict) and v.get("reviewed_on") == today.isoformat()]
    L.append("## Thesis")
    L.append("")
    L.append(", ".join(f"{k} {v}" for k, v in sorted(counts.items())) or "empty")
    L.append("")
    L.append(f"Reviewed today: {len(reviewed)} of {len(thesis)}"
             + (f" — {', '.join(sorted(reviewed)[:15])}" if reviewed else ""))
    L.append("")

    # --- 7. data quality, unioned across every compute stage -----------------
    dq = []
    for name in ("book", "risk", "drift", "triggers", "derisk", "rotation", "journal", "universe"):
        for line in (compute(name).get("data_quality") or []):
            if line not in dq:
                dq.append(line)
    for line in (state.get("data_quality") or []):
        if isinstance(line, str) and line not in dq:
            dq.append(line)
    if dq:
        L.append("## Data quality")
        L.append("")
        for line in dq[:20]:
            L.append(f"- {line}")
        if len(dq) > 20:
            L.append(f"- *(+{len(dq) - 20} more)*")
        L.append("")
    return "\n".join(L)


def _report_weekly(base_dir, run_dir, today, state, freshness_rows):
    """The product that did not exist: what changed over a week, and what was DONE about it.

    Deliberately answers questions a daily cannot. A daily says "9 proposals open"; a weekly
    says "11 were made, 2 were acted on, 5 auto-retired untouched" -- which is the only view
    that shows the desk talking past its user. The self-learning work already measured that
    (engagement collapsed 61.5% -> 2.4% between July and August) and then buried it in
    learning.json where nobody reads it.
    """
    L = []
    monday = today - timedelta(days=today.weekday())
    L.append(f"# Agent Smith — weekly · {_iso_week(today)}")
    L.append("")
    L.append(f"*Week of {monday.isoformat()} to {(monday + timedelta(days=6)).isoformat()}. "
             f"Generated by `smith_math.py report --kind weekly`; nothing here is hand-typed.*")
    L.append("")

    # --- book, week over week ------------------------------------------------
    ledger = _read_ledger(base_dir)
    wk = [r for r in ledger if (_ledger_date(r) or date.min) >= monday]
    before = [r for r in ledger if (_ledger_date(r) or date.min) < monday]
    start_v = _f(before[-1]["value_usd"]) if before else (_f(wk[0]["value_usd"]) if wk else None)
    end_v = _f(wk[-1]["value_usd"]) if wk else None
    chg = (end_v - start_v) if (start_v and end_v) else None
    L.append("## Book")
    L.append("")
    L.append(f"| metric | value |\n|---|---|")
    L.append(f"| Start of week | {_r_money(start_v)} |")
    L.append(f"| End of week | {_r_money(end_v)} |")
    L.append(f"| Change | {_r_money(chg)} ({_r_pct(100.0 * chg / start_v if (chg is not None and start_v) else None)}) |")
    # The benchmark line is PLAUSIBILITY-GATED before it is printed. ledger.csv's `smh` column
    # holds a mix of real SMH levels (~$545-570) and at least two values from another series
    # entirely (3705.11, 1984.37), which produced a "+254.09%" weekly benchmark move on the
    # first run of this report. The desk's standing rule is that a corrupt reading never sets
    # an axis and never counts as performance -- printing a wrong number is worse than printing
    # none, so this omits the line and names the reason instead.
    smh = [_f(r.get("smh")) for r in wk if _f(r.get("smh"))]
    if len(smh) >= 2:
        move = 100.0 * (smh[-1] - smh[0]) / smh[0]
        if abs(move) <= BENCHMARK_WEEKLY_PLAUSIBLE_PCT:
            L.append(f"| SMH over the same rows | {_r_pct(move)} |")
        else:
            L.append(f"| SMH over the same rows | not shown — implied {move:+.1f}% is outside the "
                     f"±{BENCHMARK_WEEKLY_PLAUSIBLE_PCT:.0f}% plausibility band, so the `smh` "
                     f"column holds at least one value from another series |")
    L.append("")

    # --- did the desk actually run? -----------------------------------------
    # A gap in the series reads as a quiet week rather than a missed one unless something counts.
    modes = {}
    for r in wk:
        modes[r.get("mode", "?")] = modes.get(r.get("mode", "?"), 0) + 1
    weekdays_so_far = sum(1 for i in range((today - monday).days + 1)
                          if (monday + timedelta(days=i)).weekday() < 5)
    L.append("## Runs")
    L.append("")
    L.append(f"{len(wk)} run(s) this week ({', '.join(f'{k} {v}' for k, v in sorted(modes.items())) or 'none'}) "
             f"against {weekdays_so_far} weekday(s) elapsed."
             + ("  **Fewer runs than weekdays — check the scheduled tasks are firing.**"
                if len(wk) < weekdays_so_far else ""))
    L.append("")

    # --- proposals: made vs acted on ----------------------------------------
    props = load_json(os.path.join(base_dir, "proposals.json"), default={})
    plist = props.get("proposals", [])

    def in_week(v):
        try:
            return date.fromisoformat(str(v)[:10]) >= monday
        except (ValueError, TypeError):
            return False

    opened = [p for p in plist if in_week(p.get("date"))]
    retired = [p for p in plist if in_week(p.get("retired_on"))]
    accepted = [p for p in plist if in_week(p.get("accepted_on"))]
    acted = [p for p in plist if p.get("status") in ("executed", "fulfilled", "filled")
             and in_week(p.get("filled_date") or p.get("fulfilled_date") or p.get("date"))]
    L.append("## Proposals")
    L.append("")
    L.append(f"| event | n |\n|---|---|")
    L.append(f"| Opened this week | {len(opened)} |")
    L.append(f"| Accepted (dashboard/chat) | {len(accepted)} |")
    L.append(f"| Executed / filled | {len(acted)} |")
    L.append(f"| Auto-retired untouched | {len(retired)} |")
    L.append(f"| Open right now | {sum(1 for p in plist if p.get('status') == 'open')} |")
    L.append("")
    if opened:
        engaged = len(accepted) + len(acted)
        L.append(f"**Engagement this week: {engaged} of {len(opened)} "
                 f"({100.0 * engaged / len(opened):.1f}%).** A low number is not automatically a "
                 f"failure of the proposals — it may equally mean they were not worth acting on. "
                 f"It is here so the trend is visible rather than assumed.")
        L.append("")
    sc = props.get("scorecard") or {}
    if sc.get("overall"):
        o = sc["overall"]
        L.append(f"Scorecard (all-time, not just this week): **{o.get('accuracy_pct')}% over n={o.get('n')}** "
                 f"— worked {o.get('worked')}, missed {o.get('missed')}, avg benefit "
                 f"{_r_pct(o.get('avg_benefit_pct'))}. {sc.get('not_yet_30d', 0)} not yet in the 30d window.")
        for d, row in (sc.get("by_direction") or {}).items():
            L.append(f"  - {d}: {row.get('accuracy_pct')}% (n={row.get('n')})")
        L.append("")

    # --- external contributions: track, never assume -------------------------
    # policy.json commits $1,000/month of new external cash from 2026-08 with a stated
    # deployment rule. `append-ledger --external-flow-usd` has existed the whole time and was
    # populated in 0 of 38 rows, so nothing knew whether it arrived. Two consequences: deposits
    # were indistinguishable from returns in attribution, and smith_charts deliberately refuses
    # to plot cumulative book-vs-SMH while the column is empty, so the benchmark chart was
    # missing for a reason nobody had connected.
    #
    # The user's instruction is TRACK BUT NEVER ASSUME: contributions are irregular, so this
    # reports what was actually recorded and never projects a future one. Nothing downstream may
    # size a proposal against an expected contribution.
    committed = (load_json(os.path.join(base_dir, "policy.json"), default={})
                 .get("monthly_contribution_usd"))
    flows = [(r["ts"][:10], _f(r.get("external_flow_usd")))
             for r in ledger if _f(r.get("external_flow_usd"))]
    wk_flows = [(d_, v) for d_, v in flows if d_ >= monday.isoformat()]
    L.append("## External contributions")
    L.append("")
    if wk_flows:
        L.append(f"Recorded this week: " + ", ".join(f"{d_} {_r_money(v)}" for d_, v in wk_flows))
    else:
        L.append("None recorded this week.")
    if committed:
        L.append("")
        L.append(f"Policy notes a ${committed:,} monthly commitment. **Irregular by the user's own "
                 f"instruction — recorded when it happens, never assumed.** Total recorded to date: "
                 f"{len(flows)} deposit(s), {_r_money(sum(v for _, v in flows)) if flows else '$0.00'}. "
                 f"No proposal may be sized against an expected future contribution.")
    if not flows:
        L.append("")
        L.append("> `external_flow_usd` has never been populated. While it is empty, deposits are "
                 "indistinguishable from returns in attribution, and the cumulative book-vs-SMH "
                 "chart stays suppressed by design. Pass `--external-flow-usd` to `append-ledger` "
                 "on any run where cash arrived from outside.")
    L.append("")

    # --- signal hit rates, advisory only ------------------------------------
    j = load_json(os.path.join(base_dir, "journal.json"), default={})
    rates = j.get("bucket_hit_rates") or {}
    if rates:
        L.append("## Signal hit rates (30d, advisory)")
        L.append("")
        L.append("| bucket | hit rate | n |\n|---|---|---|")
        for b, r in sorted(rates.items(), key=lambda kv: -(kv[1].get("n") or 0)):
            L.append(f"| {b} | {r.get('hit_rate_pct')}% | {r.get('n')} |")
        weak = [b for b, r in rates.items()
                if (r.get("n") or 0) >= 5 and (r.get("hit_rate_pct") or 0) < 40]
        if weak:
            L.append("")
            L.append(f"Below the strategist's own de-emphasis line (<40% over n>=5): **{', '.join(sorted(weak))}**. "
                     f"Reported, not suppressed — the measured record is advisory here by explicit choice.")
        L.append("")

    # --- stop-loss efficacy --------------------------------------------------
    stops = load_json(os.path.join(base_dir, "stops_analysis.json"), default={})
    if stops.get("overall"):
        o = stops["overall"]
        L.append("## Stop-loss efficacy")
        L.append("")
        L.append(f"{o.get('win_rate_pct')}% over n={o.get('count')}"
                 + (" — " + ", ".join(f"{k} {v.get('win_rate_pct')}% (n={v.get('count')})"
                                      for k, v in (stops.get("by_cohort") or {}).items())
                    if stops.get("by_cohort") else ""))
        L.append("")

    # --- cycle position and its falsifier ------------------------------------
    cyc = state.get("cycle_position")
    L.append("## Cycle position")
    L.append("")
    if isinstance(cyc, dict) and cyc.get("position"):
        L.append(f"**{cyc['position']}** (confidence {cyc.get('confidence', 'n/a')}, as of {cyc.get('as_of')}).")
        L.append("")
        L.append(f"Falsifier: {cyc.get('falsifier') or '**none recorded — a cycle call nothing can disprove is a mood.**'}")
    else:
        L.append("Not recorded. smith-cycle runs on the first deep review of a calendar month; "
                 "if that has passed without this being set, its output is being discarded.")
    L.append("")

    # --- what has gone stale, and who owns it --------------------------------
    L.append("## Staleness ledger")
    L.append("")
    stale = [r for r in freshness_rows if r["state"] != "fresh"]
    if not stale:
        L.append("Everything within TTL.")
    else:
        L.append("| artefact | state | age | owner |\n|---|---|---|---|")
        for r in sorted(stale, key=lambda r: (r["state"] != "dark", r["owner"])):
            L.append(f"| `{r['key']}` | {r['state']} | "
                     f"{r['age_days'] if r['age_days'] is not None else '—'}d | {r['owner']} |")
        L.append("")
        L.append("A limb that has quietly stopped contributing shows up here in weeks, not months.")
    L.append("")
    return "\n".join(L)


def cmd_report(args):
    """Write the dated daily or weekly report. Generated from state and the compute files."""
    today = datetime.strptime(args.today, "%Y-%m-%d").date() if args.today else date.today()
    state = load_json(os.path.join(args.base_dir, "state.json"), default={})
    rows = evaluate_freshness(state, today)
    if args.kind == "weekly":
        body = _report_weekly(args.base_dir, args.run_dir, today, state, rows)
        rel = os.path.join("reports", "weekly", f"{_iso_week(today)}.md")
    else:
        body = _report_daily(args.base_dir, args.run_dir, today, state, rows)
        rel = os.path.join("reports", "daily", f"{today.isoformat()}.md")
    path = os.path.join(args.base_dir, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(body + "\n")
    emit({"kind": args.kind, "path": rel, "chars": len(body), "as_of": today.isoformat()})
