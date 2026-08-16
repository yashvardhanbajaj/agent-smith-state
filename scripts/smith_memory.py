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

def _safe_write(path, obj):
    """.bak then tmp-then-mv -- the WRITE SAFETY contract for memory-of-record files."""
    if os.path.exists(path):
        with open(path) as f_in, open(path + ".bak", "w") as f_out:
            f_out.write(f_in.read())
    with open(path + ".tmp", "w") as f:
        json.dump(obj, f, indent=2)
    os.replace(path + ".tmp", path)

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
    all_defects = policy_defects + cache_defects + thesis_defects

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
    # previous run's digests, for the unchanged-input check
    prior_run, prior_digests = None, {}
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
                    if d.get("inputs_digest"):
                        prior_digests[f[6:-5]] = d["inputs_digest"]
    except OSError:
        pass
    skippable = []
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
