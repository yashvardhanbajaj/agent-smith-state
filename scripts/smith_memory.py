"""Retention, archives, schema validation, and per-agent embed rendering.

Split out of smith_math.py 2026-08-16: the file had reached 4,085 lines and mixed
four unrelated domains. Shared primitives live in smith_core; smith_math keeps the
per-run compute stages, the pipeline runner and the CLI, and imports these.
"""

import hashlib
import json
import csv
import math
import os
import statistics
import re
from collections import Counter
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
    # default=None returns None on a first-ever archive write (smith_core._NO_DEFAULT); the
    # isinstance test below then seeds the documented shape. Before the 2026-09-08 load_json
    # fix this raised instead, so the very first eviction into a new archive crashed.
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
        # `default={}` here is deliberate and outlives the 2026-09-08 load_json fix (see the
        # _NO_DEFAULT sentinel in smith_core): an absent file and an existing-but-empty one
        # must take the same "nothing to compact" path, which `{}` + the emptiness test below
        # gives and `default=None` + an `is None` test would not. learning.json in particular
        # does not exist until Phase 0's smith_learning.py creates it.
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

_GAPS_STOPWORDS = {
    "the", "a", "an", "of", "to", "in", "on", "for", "and", "or", "is", "was", "were",
    "this", "that", "these", "those", "with", "as", "by", "at", "it", "its", "be", "are",
    "from", "not", "no", "than", "then", "but", "so", "if", "into", "over", "under",
    "any", "all", "both", "each", "per", "via", "vs", "run", "runs", "gap", "gaps",
}


def _gaps_tokenize(text):
    """Lowercase word-tokenize, dropping a small stopword list. No stemming -- deliberately:
    this corpus is finance/incident jargon (basis, splice, phantom, reconciliation) where
    stemming risks collapsing distinct terms (e.g. 'stale' vs 'staleness' carry the same
    signal here, so leaving both surface forms costs nothing and avoids a stemmer dependency).
    """
    return [t for t in re.findall(r"[a-z0-9]+", (text or "").lower()) if t not in _GAPS_STOPWORDS and len(t) > 1]


def _bm25_rank(query, docs, k1=1.5, b=0.75):
    """Rank `docs` (list of raw text strings) against `query` by Okapi BM25.

    Added 2026-09-07 to replace cmd_gaps' single-literal-substring '--query' match, which
    required the exact query text to appear verbatim in a gap's JSON blob -- querying
    "measurement basis mismatch" would miss a gap phrased "two different measurement bases
    were plotted as one line" even though that IS the precedent being asked about.

    Hand-rolled rather than a pip dependency (e.g. rank_bm25): every module in this compute
    layer is stdlib-only by design (see smith_core.py's own docstring, "Stdlib only, no pip
    deps") so a run never depends on what happens to be installed. The corpus here is small
    (currently under 100 gap records, growing a few a week) and the algorithm is ~20 lines,
    so there is no real cost to keeping it in-house -- unlike an embeddings-based approach,
    which would need a provider Anthropic doesn't offer natively and a key this system
    doesn't otherwise hold.

    Returns a list of (index_into_docs, score) sorted by score descending, ZERO-score docs
    excluded (a doc that shares no term with the query is not a ranked-low hit, it is not a
    hit). This is lexical overlap, not semantic similarity -- a paraphrase with no shared
    vocabulary at all will still score 0. That is a real, known limitation, not a bug: the
    fallback is that the caller can still browse by --open-only or --id.
    """
    q_terms = _gaps_tokenize(query)
    if not q_terms:
        return []
    doc_tokens = [_gaps_tokenize(d) for d in docs]
    doc_lens = [len(toks) for toks in doc_tokens]
    avgdl = (sum(doc_lens) / len(doc_lens)) if doc_lens else 0.0
    n = len(docs)

    df = Counter()
    for toks in doc_tokens:
        for term in set(toks):
            df[term] += 1

    idf = {}
    for term in set(q_terms):
        d = df.get(term, 0)
        # Standard BM25 idf with a +1 floor so a term present in every doc still contributes
        # a small positive weight rather than going negative (which the classic formula can).
        idf[term] = math.log((n - d + 0.5) / (d + 0.5) + 1.0)

    scores = []
    for i, toks in enumerate(doc_tokens):
        if not toks:
            continue
        tf = Counter(toks)
        dl = doc_lens[i]
        score = 0.0
        for term in q_terms:
            f = tf.get(term, 0)
            if f == 0:
                continue
            denom = f + k1 * (1 - b + b * dl / avgdl) if avgdl else f + k1
            score += idf.get(term, 0.0) * (f * (k1 + 1)) / denom
        if score > 0:
            scores.append((i, score))

    scores.sort(key=lambda pair: pair[1], reverse=True)
    return scores


def cmd_gaps(args):
    """Look up known_gaps across BOTH the hot registry and the archive (added 2026-08-16;
    --query upgraded 2026-09-07 from a literal substring match to ranked BM25 search -- see
    _bm25_rank's docstring for why).

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
        ordered = [(None, g) for g in rows if (g.get("id") or "").lower() == q]
        ordered.sort(key=lambda pair: (pair[1].get("id") or ""))
    elif args.query:
        # Rank over description/gap + resolution + owner -- the three fields a precedent
        # search actually cares about; dates and status are structured, not searched text.
        docs = [" ".join([
            g.get("gap") or g.get("description") or "",
            g.get("resolution") or "",
            g.get("owner") or "",
        ]) for g in rows]
        top_n = max(1, args.top)
        ranked = _bm25_rank(args.query, docs)[:top_n]
        # Rank order (highest relevance first), not re-sorted by id -- that IS the result.
        ordered = [(score, rows[i]) for i, score in ranked]
    else:
        hits = [g for g in rows if smith_risk.gap_is_live(g)] if args.open_only else rows
        hits.sort(key=lambda g: (g.get("id") or ""))
        ordered = [(None, g) for g in hits]

    out_gaps = []
    for score, g in ordered:
        row = {"id": g.get("id"), "status": g.get("status") or "open",
               "where": g["_where"], "opened": g.get("opened"),
               "resolved_on": g.get("resolved_on"),
               "gap": (g.get("gap") or g.get("description") or "")[:400],
               "resolution": (g.get("resolution") or "")[:400]}
        if args.query:
            row["relevance"] = round(score, 3)
        out_gaps.append(row)

    note = ("Searches BOTH state.json and known-gaps-archive.json. A gap missing from "
            "state.json is ARCHIVED, never deleted -- absence here, and only here, is "
            "evidence a gap never existed.")
    if args.query:
        note += (" --query is ranked lexical (BM25) search, not semantic: it finds gaps "
                 "sharing vocabulary with the query, sorted by relevance, top "
                 f"{max(1, args.top)}. A precedent phrased with entirely different words "
                 "will not surface here -- browse --open-only or a narrower query if a hit "
                 "you expected is missing.")

    emit({"searched": {"hot": len(hot), "archived": len(arc), "total": len(rows)},
          "matched": len(out_gaps),
          "gaps": out_gaps,
          "note": note})

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
    # TS GUARD (added 2026-09-01). --ts was taken verbatim, and on 2026-08-31 an unattended run
    # passed its RUN-DIR LABEL ("2026-08-31-1554") into the timestamp column. It went unnoticed
    # because every reader slices [:10], so it parsed as a date by luck while carrying no time
    # and no timezone -- 38 ISO rows and one that merely looked like one. A ledger is the P&L
    # spine; a column that is 97% one format and silently 3% another is a trap for the next
    # reader who does arithmetic on it. Recoverable shapes are NORMALISED (with the correction
    # reported, never silent); anything unparseable is refused outright.
    ts_in = args.ts
    if not LEDGER_TS_RE.match(str(ts_in).strip()):
        parsed = parse_ts(ts_in)
        if parsed is None:
            fail(f"--ts {ts_in!r} is not a timestamp. ledger.csv's ts column is ISO-8601 with a "
                 f"UTC offset, e.g. 2026-09-01T14:36:00+05:30. A run-dir label like "
                 f"'2026-09-01-1436' is not a timestamp -- it has no timezone.")
        args.ts = parsed.isoformat(timespec="seconds")
        ts_normalised = {"given": ts_in, "written": args.ts, "reason":
                         "not ISO-8601 with offset; normalised rather than written verbatim"}
    else:
        ts_normalised = None

    # BENCHMARK GUARD (added 2026-09-08, user-reported). The chart's plausibility gate keeps a
    # corrupt cell out of the tally, but the real defect is upstream: --smh was taken verbatim,
    # and four rows in August received a NET-FLOW figure in the benchmark column. On 2026-08-12
    # and 2026-08-13 the real SMH level (586.22, 584.83) is sitting one column to the RIGHT, in
    # est_net_flows_usd, and the flow (4896.61, -1170.30) is in `smh` -- an argument-order slip,
    # not a bad price feed. Left unguarded it silently poisons every relative-performance
    # statement the desk makes, so the write is REFUSED here rather than repaired later.
    smh_in = _f(args.smh) if args.smh not in (None, "") else None
    if smh_in is not None:
        # Baseline is the MEDIAN of the last 10 recorded levels, not the last one. The last
        # one is exactly what a corrupt cell overwrites, and once one lands, comparing to it
        # would wave the next corrupt cell through (and refuse the next correct one). A median
        # over a window survives a minority of poisoned cells, which is the actual failure
        # shape here -- 4 bad rows out of ~30.
        hist = []
        if os.path.exists(ledger_path):
            for r in csv.DictReader(open(ledger_path)):
                v = _f(r.get("smh"))
                if v:
                    hist.append(v)
        prev = statistics.median(hist[-10:]) if hist else None
        if prev:
            move = 100.0 * (smh_in - prev) / prev
            if abs(move) > BENCHMARK_WEEKLY_PLAUSIBLE_PCT:
                flow_in = _f(args.est_net_flows_usd) if args.est_net_flows_usd not in (None, "") else None
                swap = ""
                if flow_in and abs(100.0 * (flow_in - prev) / prev) <= BENCHMARK_WEEKLY_PLAUSIBLE_PCT:
                    swap = (f" --est-net-flows-usd is {flow_in}, which IS a plausible SMH level "
                            f"against {prev:.2f} -- the two arguments look swapped.")
                fail(f"--smh {smh_in} implies a {move:+.1f}% move from the last recorded level "
                     f"{prev:.2f} (median of the last 10 recorded levels), outside the \u00b1{BENCHMARK_WEEKLY_PLAUSIBLE_PCT:.0f}% "
                     f"plausibility band. SMH is a sector ETF; it does not move that far between "
                     f"runs, so this is a value from another series, not a price.{swap} Pass the "
                     f"SMH close in --smh, or omit --smh entirely if you don't have one -- an "
                     f"empty benchmark cell is honest, a wrong one corrupts every "
                     f"relative-performance number downstream.")

    row = [args.ts, args.mode, args.value_usd, args.usdinr, args.wallet_usd, args.spx,
           args.ndx, args.smh or "", args.smh_asof or "", args.est_net_flows_usd or "",
           args.external_flow_usd or "", args.value_trust, notes]
    with open(ledger_path, "a", newline="") as f:
        w = csv.writer(f)
        if is_new:
            w.writerow(LEDGER_HEADER)
        w.writerow(row)
    emit({"ts_normalised": ts_normalised, "appended": True, "ts": args.ts, "notes_chars": len(notes),
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

    # rel_strength_1m_peer -- the peer_map-aware companion, added 2026-09-07. Before this cache
    # existed, smith-signals recomputed the same BE/GEV/VRT-vs-XLU, MSFT/NBIS-vs-XLK override
    # from a fresh fetch on EVERY dispatch (no TTL gate at all, quick or deep) because the
    # compute layer had nowhere to persist the answer for cmd_buckets to reuse next run. Shape
    # per ticker: {"rel_pp": float, "peer_etf": str}. Rejects (never guesses) a row whose
    # peer_etf is missing or literally "SMH" -- that ticker belongs in the plain
    # rel_strength_1m cache above, not here; this cache exists specifically for the tickers
    # where SMH is the WRONG benchmark.
    rel_peer_raw = out.get("rel_strength_1m_peer_updates") or {}
    rel_peer_upd, rel_peer_rejected = {}, []
    for tk, v in rel_peer_raw.items():
        if not isinstance(v, dict):
            rel_peer_rejected.append(tk)
            continue
        pp, etf = v.get("rel_pp"), v.get("peer_etf")
        if isinstance(pp, (int, float)) and isinstance(etf, str) and etf and etf.upper() != "SMH":
            rel_peer_upd[tk] = (pp, etf)
        else:
            rel_peer_rejected.append(tk)
    if rel_peer_upd:
        c = state["data_cache"].setdefault("rel_strength_1m_peer", {})
        vp, pe = c.setdefault("values_pp", {}), c.setdefault("peer_etf", {})
        for tk, (pp, etf) in rel_peer_upd.items():
            vp[tk] = pp
            pe[tk] = etf
        c["as_of"] = today

    # wk52 -- 52-week high/low, added 2026-09-06. Feeds the pos-based buckets in cmd_buckets,
    # which were `deferred_pos_buckets` until this cache existed because nothing persisted a
    # 52-week range: smith-signals fetched it every run and it died with the run. Each entry
    # must carry BOTH a numeric low and high and low < high -- a zero/absent low is not a
    # harmless gap, it drives pos to 1.0 and fakes a breakout (SKHY did exactly that on
    # 2026-09-06 and smith-signals had to flag it by hand as an artifact).
    wk_raw = out.get("wk52_updates") or {}
    wk_upd, wk_rejected = {}, []
    for k, v in wk_raw.items():
        if not isinstance(v, dict):
            continue
        lo, hi = v.get("low"), v.get("high")
        if all(isinstance(x, (int, float)) for x in (lo, hi)) and 0 < lo < hi:
            wk_upd[k] = {"low": lo, "high": hi, "as_of": today}
        else:
            wk_rejected.append(k)
    if wk_upd:
        c = state["data_cache"].setdefault("wk52", {})
        c.update(wk_upd)
        c["as_of"] = today

    peer_upd = out.get("peer_map_updates", {}) or {}
    if peer_upd:
        state.setdefault("peer_map", {}).update(peer_upd)
    return {"signal_history_changed": list(changed), "stamped": len(stamp_tickers),
            "wk52_updated": len(wk_upd), "wk52_rejected": sorted(wk_rejected),
            "analyst_targets_updated": len(targets), "peer_map_updated": len(peer_upd),
            "ret_5d_updated": len((r5.get("values_pct") or {}) if r5 else {}),
            "rsi14_updated": len(rsi_upd), "atr20_updated": len(atr_upd),
            "rel_strength_1m_updated": len(rel_upd),
            "rel_strength_1m_rejected": rel_rejected,
            "rel_strength_1m_peer_updated": len(rel_peer_upd),
            "rel_strength_1m_peer_rejected": sorted(rel_peer_rejected),
            "journal_new_added": added if jn else []}


def _as_date(today):
    """merge-tails hands `today` around as an ISO string; the freshness helpers work in
    `date`. Tolerant of already being a date so callers don't have to care."""
    return today if isinstance(today, date) else date.fromisoformat(str(today)[:10])


def _merge_catalyst(out, state, today):
    """CARRY-FORWARD merge (rewritten 2026-09-08; the full incident is in
    `smith_risk`'s FACTOR-CATALYST FRESHNESS block).

    This used to be a wholesale REPLACE. That is correct for the case it was
    written for -- an agent that returns two catalysts should not leave last
    week's three sitting alongside them -- and catastrophic for the case nobody
    wrote it for: an agent that ran, searched honestly, and found nothing NEW.
    On 2026-09-08 that emptied the array, took live `catalyst_threat` triggers
    from 6 to 0, made the dashboard panel vanish, and deleted two structural
    CXMT threats that were four and seven days old.

    Three distinct states now, only one of which deletes anything:

      1. The `catalysts` key is ABSENT   -> the agent did not run (or returned no
         opinion). Leave the array exactly as it is. Unchanged behaviour.
      2. The `catalysts` key is PRESENT  -> the returned items are merged by
         (headline, date): a returned item is fresh (`last_confirmed = today`),
         and an existing item the agent did NOT return is CARRIED FORWARD, not
         dropped. An empty list is therefore a valid, non-destructive answer --
         it says "nothing new", which is what the agent meant.
      3. `retired_catalysts` names specific (headline, date) pairs -> THOSE, and
         only those, are deleted. Deletion becomes an affirmative act with a
         reason attached, rather than a side effect of a quiet news day.

    Entries also age out on their own `horizon` (structural 45d, noise 3d --
    `smith_risk.catalyst_is_expired`), so carrying forward is bounded and the
    array cannot grow into the accumulating log the REPLACE rule was guarding
    against. `first_seen` is preserved across confirmations so the age clock
    measures the event, not the last time someone mentioned it.
    """
    cats = out.get("catalysts")
    existing = list(state.get("factor_catalysts", []) or [])
    result = {"factor_catalysts_ran": cats is not None}
    if cats is None:
        result["factor_catalysts_carried"] = len(existing)
        result["reason"] = "agent did not run / returned no `catalysts` key -- array untouched"
        return result

    retired = {smith_risk.catalyst_key(r): (r.get("reason") or "retired by smith-catalyst")
               for r in (out.get("retired_catalysts") or [])}
    fresh_by_key = {}
    merged, fresh_n = [], 0
    for c in cats:
        c = dict(c)
        k = smith_risk.catalyst_key(c)
        prior = next((e for e in existing if smith_risk.catalyst_key(e) == k), None)
        c["first_seen"] = (prior or {}).get("first_seen") or c.get("date") or today
        c["last_confirmed"] = today
        c["carried_forward"] = False
        fresh_by_key[k] = c
        merged.append(c)
        fresh_n += 1

    carried, dropped_retired, dropped_stale = [], [], []
    for e in existing:
        k = smith_risk.catalyst_key(e)
        if k in fresh_by_key:
            continue
        if k in retired:
            dropped_retired.append({"headline": k[0], "date": k[1], "reason": retired[k]})
            continue
        if smith_risk.catalyst_is_expired(e, _as_date(today)):
            dropped_stale.append({"headline": k[0], "date": k[1],
                                  "horizon": e.get("horizon"),
                                  "ttl_days": smith_risk.catalyst_ttl_days(e)})
            continue
        e = dict(e)
        e.setdefault("first_seen", e.get("date") or today)
        e["carried_forward"] = True
        carried.append(e)
        merged.append(e)

    state["factor_catalysts"] = merged
    result.update({"factor_catalysts_fresh": fresh_n,
                   "factor_catalysts_carried": len(carried),
                   "factor_catalysts_retired": dropped_retired,
                   "factor_catalysts_aged_out": dropped_stale})
    if not cats:
        result["reason"] = (f"agent ran and found nothing new -- {len(carried)} catalyst(s) "
                            "carried forward. A quiet scan is not a retirement.")
    themes = out.get("theme_updates", {})
    if isinstance(themes, dict) and themes.get("id") is not None:
        for t in state.setdefault("factor_themes", {}).setdefault("themes", []):
            if t.get("id") == themes["id"]:
                t[f"live_{today.replace('-', '_')}"] = themes.get("update")
    return result


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
    narrative = out.get("sentiment_narrative")
    if narrative:
        state["scout_narrative"] = {"text": narrative, "as_of": today}
    return {"diversifier_candidates_replaced": dc is not None,
            "scout_narrative_updated": bool(narrative)}


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
    """Merge smith-macro's tail into state["macro_read"].

    Before 2026-09-07 this only kept `fomc_cache_update` -- the rest of the documented tail
    (PCR/max-pain, the FOMC/CPI/NFP calendar, the regime read and cluster_impact) was computed,
    used once in that turn's own briefing text, and then discarded (the G50 shape). Worse:
    smith_core.FRESHNESS already carried a "macro_read" entry (7-day TTL, owner smith-macro)
    from the day the freshness table was built, expecting exactly this key -- so `validate`/
    `freshness` were silently checking the age of a state key nothing ever wrote, the same
    always-dark-never-flagged gap `tax_read` avoids by existing. Two real consumers were unfed
    across runs as a result: SKILL.md's quick-mode macro headline (needs a cached regime, not a
    fresh smith-macro dispatch every run) and smith-strategist's stress table, documented
    (smith-strategist.md line 72) as "anchored to smith-macro's live regime read" with no
    code-guaranteed delivery path -- see the new "macro_tail" ref in
    AGENT_SLICES["strategist"], which reads out_macro.json directly for the same-run case; this
    state write is what makes a *stale-but-present* regime read available on a quick run where
    smith-macro doesn't dispatch at all, and what finally gives FRESHNESS's "macro_read" entry
    something real to check.
    """
    upd = out.get("fomc_cache_update")
    if upd is not None:
        state["fomc_cache"] = upd
    regime_fields = ("fed_funds_pct", "fomc_stance", "spy_pcr", "spy_pcr_oi", "spy_pcr_vol",
                      "spy_max_pain", "qqq_pcr", "qqq_pcr_oi", "qqq_pcr_vol", "qqq_max_pain",
                      "calendar", "regime", "regime_note", "cluster_impact")
    regime = {k: out[k] for k in regime_fields if k in out}
    if regime:
        regime["as_of"] = today
        state["macro_read"] = regime
    return {"fomc_cache_updated": upd is not None, "macro_read_updated": bool(regime)}


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

    # RAW-NUMBERS cache, separate from the findings above (added 2026-09-01). `quality_read`
    # only ever held VERDICTS ("OCF/PAT ratio looks weak"), never the OCF/PAT figures those
    # verdicts came from -- so a monthly re-audit re-fetched full financial statements from
    # scratch even in a month where nothing new had been filed. `financials_updates` covers
    # only the tickers this pass actually fetched fresh (task 0 in smith-quality.md); every
    # other ticker's cached entry is left untouched, same non-destructive-merge shape as
    # quality_flags above -- this cache and that one are audited per-ticker independently, so
    # they can legitimately be at different ages for the same name (a raw figure a fresh audit
    # skipped re-deriving is not the same event as a fresh finding about it).
    fin_updates = out.get("financials_updates") or {}
    cache = state.setdefault("data_cache", {}).setdefault("quality_financials", {})
    cache.update(fin_updates)

    return {"quality_flags": len(merged), "flags_this_pass": len(flags),
            "cleared_this_pass": len(cleared), "tickers_audited_total": len(audited),
            "force_thesis_review": len(ftr), "financials_cache_updated": len(fin_updates)}


def _merge_cluster(out, state, today, cluster_name=None, ladder_track_record=None):
    """Fold ONE cluster specialist's tail into state.cluster_ladders[<cluster>].

    PER-CLUSTER, never wholesale. Up to LADDER_MAX_DISPATCH clusters are refreshed per run and
    the rest keep the ladder they already have -- replacing the whole map with one agent's
    answer would silently blank every cluster the round-robin did not reach this run, which is
    the exact shape of the archived-on-exit / re-derived-on-entry cluster-name incident.

    `confidence` is load-bearing and is written verbatim from the agent, with one exception:
    a cluster whose own track record has gone below coin-flip over a real sample is FORCED to
    `low` here, which removes its trigger authority. The agent does not get to grade its own
    homework. See _apply_ladder_track_record.
    """
    cname = out.get("cluster") or cluster_name
    if not cname:
        return {"merged": False, "reason": "tail carries no `cluster` field -- cannot place it"}
    ranking = out.get("ranking") or []
    # Read-only until the tail is known good -- a refused merge must leave state byte-identical,
    # not quietly create the key it declined to write into.
    prior = (state.get("cluster_ladders") or {}).get(cname) or {}
    entry = {
        "as_of": today,
        "cluster_thesis": out.get("cluster_thesis"),
        "margin_pool": out.get("margin_pool"),
        "ranking": ranking,
        "leader": out.get("leader"),
        "laggard": out.get("laggard"),
        "confidence": out.get("confidence"),
        "redundant_pairs": out.get("redundant_pairs") or [],
        "bench": out.get("bench") or [],
        "reorder_when": out.get("reorder_when") or [],
        "catalysts": out.get("catalysts") or [],
        # PERSISTED, not dropped (fixed 2026-09-08 on the first live run). The agent is asked to
        # self-report ranks that contradict state.thesis, and cmd_crosscheck's ladder_vs_thesis
        # rule dedups against exactly this list so it only reports the tensions the agent MISSED.
        # Leaving it out of the entry meant the dedup could never match: on the first real run all
        # three findings crosscheck raised were ones the agents had already flagged themselves.
        # That is the G50 shape -- produced, then discarded -- in new code.
        "thesis_tensions": out.get("thesis_tensions") or [],
        # Also carried: the honest limits the agent put on its own ranking. `unranked` names are
        # ones it refused to rank rather than guess at, and confidence_reasons is what `confidence`
        # -- which gates trigger authority -- actually rests on. Both are load-bearing for a reader
        # deciding how much to trust the order.
        "unranked": out.get("unranked") or [],
        "confidence_reasons": out.get("confidence_reasons") or [],
        # Carried forward, never rewritten by the agent -- the score of its PREVIOUS calls.
        "track_record": prior.get("track_record") or [],
    }
    # APPEND THE SCORE OF THE LADDER BEING REPLACED, here, at the only moment both exist.
    # cmd_ladder computes it (did the previous leader actually beat the previous laggard?) and
    # emits it, but emitting is not persisting -- without this the record would be recomputed
    # and discarded every run, which is the same G50 shape this codebase keeps fixing, and the
    # confidence auto-downgrade in smith_risk.ladder_authority would never have a sample to act
    # on. Capped at LADDER_TRACK_RECORD_CAP: a rolling window, because a ranking that was right
    # about a different cluster composition two years ago is not evidence about this one.
    score = (ladder_track_record or {}).get(cname)
    if score:
        entry["track_record"] = (entry["track_record"] + [score])[-LADDER_TRACK_RECORD_CAP:]
    # A ladder with no ordering is not a ladder. Persisting one would hand the rotation trigger
    # a `leader`/`laggard` pair with nothing behind it, which is worse than having no ladder at
    # all because the trigger's freshness gate would treat it as a real answer.
    if len(ranking) < 2 or not entry["leader"] or not entry["laggard"]:
        return {"merged": False, "cluster": cname,
                "reason": f"tail carries {len(ranking)} ranked name(s) and "
                          f"leader={entry['leader']!r}/laggard={entry['laggard']!r} -- "
                          f"not a ladder; prior entry left intact"}
    state.setdefault("cluster_ladders", {})[cname] = entry
    state["cluster_ladders_as_of"] = today
    state.setdefault("cluster_scan_cursor", {})[cname] = today
    return {"merged": True, "cluster": cname, "ranked": len(ranking),
            "leader": entry["leader"], "laggard": entry["laggard"],
            "confidence": entry["confidence"],
            # Handed back so the caller can log it to learning.json. Returned rather than
            # written here because this function stays a pure state-merge; the learning store
            # is a separate spine with its own append-only contract.
            "scored_call": score if (score or {}).get("scored") else None}


def _merge_strategist(out, state, today):
    """Persist the strategist's stress table (added 2026-08-31).

    smith-strategist was the ONLY Stage-1/2 agent with no merge rule at all. That was defensible
    for its main deliverable -- proposals go through `add-proposal`, the sanctioned write path --
    but it silently meant its OTHER deliverable, the six-scenario stress table, had no write path
    anywhere. It was rebuilt from scratch every deep run, lived only in runs/<ts>/, and could not
    be compared against the previous run even though "did the stress picture change" is the whole
    reason for producing it repeatedly. Same shape as G50 and cycle_position.

    Keeps ONE prior generation as `stress_table_prev` so the next run can diff rather than merely
    overwrite -- the cheapest possible version of the comparison the table exists to support.
    """
    st = out.get("stress_table")
    if not isinstance(st, dict) or not st.get("scenarios"):
        return {"stress_table": None, "note": "tail carried no stress_table scenarios"}
    scen = st.get("scenarios") or []
    # Numbers, not prose: a row whose impact bounds are not numeric cannot be ranked or diffed,
    # which is the entire point of structuring this. Surface such rows rather than storing them
    # as if they were usable.
    unusable = [x.get("scenario") for x in scen
                if not isinstance(x.get("impact_pct_low"), (int, float))
                or not isinstance(x.get("impact_pct_high"), (int, float))]
    prior = state.get("stress_table")
    if prior:
        state["stress_table_prev"] = prior
    st.setdefault("as_of", today)
    state["stress_table"] = st
    worst = min([x["impact_pct_low"] for x in scen
                 if isinstance(x.get("impact_pct_low"), (int, float))], default=None)
    return {"stress_table": len(scen), "worst_case_pct": worst,
            "rows_without_numeric_impact": unusable,
            "kept_prior_for_diff": bool(prior)}


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
    # factor_catalysts_as_of added 2026-09-08: the dashboard needs to be able to say "last
    # scanned <date>" when the live array is empty, which is only honest if something records
    # WHEN a scan last happened as distinct from when a catalyst was last found.
    "catalyst":  ["factor_themes", "factor_catalysts"],
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
    "strategist": _merge_strategist,
    "tax": _merge_tax,
    # Reached through the cluster_<slug> prefix, never by that literal key -- see the merge loop.
    "cluster": _merge_cluster,
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
    MERGE_RULES whose out_*.json file exists, if --agents is omitted). The one agent not
    covered by MERGE_RULES is `ledger` (2026-09-07: `rebound`/`strategist` used to be in this
    same boat, both since fixed -- see `_merge_rebound`/`_merge_strategist` below; this
    docstring had drifted behind those fixes) -- its state writes are handled by its own
    dedicated commands (`ledger-apply`, `lots --write`), by design, not because merge-tails
    forgot it. Any agent named in --agents but genuinely missing a rule is skipped and
    reported, not silently ignored.

    CALL THIS ONCE PER WAVE, not once for the whole run (SKILL.md's own merge-tails
    instruction was corrected 2026-09-07 for the same reason): `smith-earnings` (WAVE 1) and
    `smith-thesis` (WAVE 2) can both write `state.data_cache.earnings_facts` for the same
    ticker, and the merge is a per-ticker overwrite with no conflict detection -- whichever
    call applies LAST wins. Batching both waves into one call processes agents in this dict's
    fixed insertion order regardless of actual dispatch order, which let Wave-1 earnings'
    OLDER fact silently overwrite Wave-2 thesis' NEWER, sibling-informed one. Calling this
    once per wave, in wave order, makes the later wave's write land later by construction.

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
    # The bare "cluster" key is a TEMPLATE, not a dispatchable agent -- there is never an
    # out_cluster.json. When --agents is omitted, discover the real cluster tails on disk.
    requested = args.agents.split(",") if args.agents else (
        [a for a in MERGE_RULES if a != "cluster"] +
        sorted(f[4:-5] for f in os.listdir(args.run_dir)
               if f.startswith("out_" + CLUSTER_AGENT_PREFIX) and f.endswith(".json")))

    results = {}
    skipped_no_file = []
    skipped_no_rule = []
    for agent in requested:
        # cluster_<slug> keys all resolve to the one _merge_cluster rule (see resolve_agent).
        rule = MERGE_RULES.get("cluster") if is_cluster_agent(agent) else MERGE_RULES.get(agent)
        if rule is None:
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
        if is_cluster_agent(agent):
            # Fall back to the slice's own cluster_name when the tail omits it -- the slice is
            # what TOLD the agent which cluster it was working on, so it is authoritative, and
            # a dropped field must not silently misfile a ladder onto another cluster.
            sl = load_json(os.path.join(args.run_dir, f"slice_{agent}.json"), default={})
            extra["cluster_name"] = sl.get("cluster_name")
            extra["ladder_track_record"] = (
                load_json(os.path.join(args.run_dir, "compute_ladder.json"),
                          default={}).get("track_record") or {})
        results[agent] = rule(out, state, today, **extra)
        # LADDER CALLS FEED THE LEARNING STORE (added 2026-09-08). Each scored call -- did the
        # ladder's named leader actually beat its named laggard -- is one observation, on the
        # same append-only spine the journal's own hit-rate work uses. The per-cluster
        # track_record already gates trigger authority on its own; this is the fleet-wide view,
        # which is what answers "is the cluster layer worth its token cost at all?". Local
        # import: smith_learning pulls in smith_lifecycle, which this module does not otherwise
        # need, and a top-level import would make every `slices`/`gaps` call pay for it.
        _sc = (results[agent] or {}).get("scored_call") if isinstance(results[agent], dict) else None
        if _sc:
            import smith_learning
            smith_learning.record_observation(
                args.base_dir, "ladder.hit_rate", 1 if _sc.get("correct") else 0,
                today=today, run_dir=args.run_dir,
                note=(f"{_sc.get('leader')} over {_sc.get('laggard')} in "
                      f"{results[agent].get('cluster')}: spread {_sc.get('spread_pp')}pp "
                      f"(ladder of {_sc.get('ladder_as_of')}, confidence "
                      f"{_sc.get('ladder_confidence_at_call')})"))
        for key in MERGE_STAMPS.get(agent, []):
            state[f"{key}_as_of"] = today

    # ADVANCE news_watermark (added 2026-09-07, closing a real dead-code gap). signals/thesis/
    # watchlist/catalyst are all handed `news_watermark` every run and told to dedupe against
    # it -- but nothing ever wrote it back, so every run re-embedded the same permanently-stale
    # value and the dedup was structurally inert. Advance it whenever at least one news-reading
    # agent actually merged this call, to the date that agent's news scan covered -- never to a
    # date no agent actually looked at, which would silently widen the dedup window past what
    # was really checked.
    NEWS_WATERMARK_AGENTS = ("signals", "thesis", "watchlist", "catalyst")
    if any(a in results for a in NEWS_WATERMARK_AGENTS):
        state["news_watermark"] = today

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


def validate_ticker_map_coverage(base_dir):
    """SKILL.md documents data_cache.ticker_map as 365-day TTL, but the map is manually
    maintained (added-on-new-holding, never re-stamped) -- there is no write-side timestamp to
    check a TTL against, so a time-based freshness entry would just report a fake age. The real
    risk the TTL was trying to guard against is a ticker with live trade history that ticker_map
    still can't resolve, which would silently break cmd_ledger_parse's name->ticker matching
    (smith_ledger.py:648) the next time an INDmoney confirmation email needs it. lots.json is
    keyed by ticker for every position ever opened, so it is the actionable coverage check:
    every ticker with lots must have SOME entry in ticker_map or ticker_map_email_aliases.
    """
    state = load_json(os.path.join(base_dir, "state.json"), default={}) or {}
    dc = state.get("data_cache", {}) or {}
    tmap = dc.get("ticker_map", {}) or {}
    aliases = dc.get("ticker_map_email_aliases", {}) or {}
    known = set(tmap.values()) | set(aliases.values())
    lots = load_json(os.path.join(base_dir, "lots.json"), default={}) or {}
    uncovered = sorted(t for t, ls in lots.items()
                       if isinstance(ls, list) and ls and t not in known)
    if not uncovered:
        return []
    return [f"TICKER_MAP COVERAGE: {len(uncovered)} ticker(s) with open/historical lots have no "
            f"entry in data_cache.ticker_map or ticker_map_email_aliases "
            f"({', '.join(uncovered[:8])}{' ...' if len(uncovered) > 8 else ''}) -- an INDmoney "
            f"trade-confirmation email for these will fail name resolution in cmd_ledger_parse "
            f"and require a smith-ledger dispatch to sort out by hand."]


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
    run_defects = validate_runs(args.base_dir) + validate_ledger_ts(args.base_dir)
    ledger_defects = validate_ledger_schema(args.base_dir)
    aggrisk_defects = validate_aggregate_risk(args.base_dir, state)
    ticker_map_defects = validate_ticker_map_coverage(args.base_dir)
    all_defects = (policy_defects + cache_defects + thesis_defects + learning_defects
                   + proposals_defects + narrative_defects
                   + earnings_pending_defects + freshness_defects + ledger_defects + run_defects
                   + aggrisk_defects + ticker_map_defects)

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
                   # `buckets` added 2026-09-06: compute_buckets.json is now this agent's FIRST
                   # input, carrying the move arithmetic it used to derive itself.
                   # `rel_strength_1m_peer` added 2026-09-07: task 9's cache-check-first
                   # rewrite needs to see the CURRENT peer-cache entries to know which tickers
                   # are actually stale before spending a fetch on one that isn't.
                   "cache": ["atr20", "rel_strength_1m_peer"], "refs": ["journal", "buckets"], "holdings": "trim"},
    "thesis":     {"state": ["thesis", "sector_map", "news_watermark", "open_flags"],
                   "cache": ["etf_constituents", "earnings_facts"],
                   # Added 2026-09-07 -- this is the code-side half of the WAVES rewrite's
                   # promise ("thesis <- catalyst's events, quality's flags, signals'
                   # buckets"), which until now only existed in SKILL.md prose. Requires this
                   # slice to be (re)generated AFTER Wave 1 has landed -- see the WAVES section
                   # for the two-slices-calls-per-run instruction this fix requires.
                   # "valuation" added 2026-09-07 -- reverse-DCF/ROIC-WACC checks are
                   # on-demand/monthly (see SKILL.md), so this ref reports MISSING on most
                   # runs by design, same accepted pattern as catalyst_tail on a run where
                   # catalyst wasn't dispatched. When present: roic_weakened means downgrade
                   # to WEAKENED regardless of an earnings beat (§ROIC-WACC in SKILL.md).
                   "refs": ["catalyst_tail", "quality_tail", "signals_tail", "valuation"],
                   "holdings": "trim", "shared": ["hbm_tracker"]},
    "watchlist":  {"state": ["news_watermark", "watchlist_scan_cursor"],
                   "cache": ["earnings_calendar", "analyst_targets"], "refs": ["attribution"],
                   "holdings": "trim"},
    "book":       {"state": [], "cache": ["betas"],
                   # "bookcalc" added 2026-09-07 -- REF_FILES had no entry for
                   # compute_bookcalc.json before this, so this WAVE-0 script output (which
                   # smith-book.md's own CONSUME addendum says the agent now reads instead of
                   # computing dividends/ex-dates/LTCG itself) was unreachable through the
                   # normal ref mechanism.
                   "refs": ["book", "lots", "bookcalc"], "holdings": None},
    "scout":      {"state": ["diversifier_candidates"], "cache": [],
                   "refs": ["sentiment", "market_inputs"], "holdings": "trim"},
    "macro":      {"state": ["fomc_cache"], "cache": [],
                   "refs": ["sentiment", "market_inputs"], "holdings": None},
    # "market_inputs" added 2026-09-07 -- catalyst's own task 6 ("Asia session leadership")
    # independently WebSearched KOSPI/TAIEX/Nikkei moves every run, genuinely redundant with the
    # orchestrator's own step 1.5 ASIA BLOCK (fetched once, into market_inputs.json, and already
    # read by smith-scout the same way) -- catalyst simply never had this ref to read from. Its
    # actual differentiated job is the NAMED CAUSE behind a move that crossed the threshold, not
    # rediscovering the raw percentage a sibling agent's input already carries.
    "catalyst":   {"state": ["factor_themes", "factor_catalysts", "news_watermark"],
                   "cache": [], "refs": ["drift", "market_inputs"], "holdings": "trim",
                   "shared": ["hbm_tracker"]},
    "cycle":      {"state": ["factor_themes", "sector_map"], "cache": ["earnings_facts"],
                   # "catalyst_tail" added 2026-09-07 -- same WAVES-promise fix as thesis above
                   # ("cycle <- catalyst's events"), so the memory-pricing contradiction this
                   # rewrite exists to catch (catalyst's structural DRAM read vs cycle's own
                   # TrendForce guide) is an input cycle can actually see, not just something
                   # crosscheck notices after the fact.
                   "refs": ["drift", "catalyst_tail"], "holdings": "trim", "shared": ["hbm_tracker"]},
    "earnings":   {"state": [], "cache": ["earnings_calendar", "earnings_facts"],
                   "refs": [], "holdings": "trim"},
    "tax":        {"state": ["thesis"], "cache": [],
                   # "taxcalc" added 2026-09-07 -- same fix as "book" above: compute_taxcalc.json
                   # was unreachable through REF_FILES, even though smith-tax.md's own CONSUME
                   # addendum says taxcalc now computes the FIFO-vs-HIFO comparison this agent
                   # was still being told (in a since-corrected HARD RULES line) to derive itself.
                   "refs": ["book", "lots", "taxcalc"],
                   "holdings": "trim"},
    # "quality_read" added 2026-09-07 -- smith-quality.md line 13 promises the agent its own
    # prior audit ("state.quality_read -- your FINDINGS from last time, for trend comparison")
    # but this slice never actually carried it, so every audit ran blind on trend comparison
    # against itself. Same promised-but-undelivered class already fixed for thesis/cycle/book/tax.
    "quality":    {"state": ["open_flags", "quality_read"],
                   "cache": ["quality_financials", "earnings_facts"],
                   # "valuation" added 2026-09-07 -- forensic_risk (Beneish/Altman), on-demand/
                   # monthly, MISSING on most runs by design (see the thesis slice's comment).
                   "refs": ["book", "valuation"], "holdings": "trim"},
    "rebound":    {"state": ["sector_map"], "cache": [], "refs": ["book", "risk"],
                   "holdings": "full"},
    "ledger":     {"state": [], "cache": ["ticker_map"], "refs": ["book", "lots"],
                   "holdings": "full"},
    # ONE TEMPLATE, N DISPATCHES (added 2026-09-08). Cluster specialists are dispatched under
    # pseudo-agent keys -- cluster_semis, cluster_optics, cluster_memory -- so their slices and
    # tails do not collide, but they all resolve to THIS one entry and all run the single
    # smith-cluster.md agent. Seven per-cluster agent files would drift apart and each would
    # re-derive the shared output contract; the cluster-specific knowledge lives in
    # policy.cluster_playbooks instead, as data, editable without touching a prompt.
    # See _resolve_agent_spec for the prefix resolution.
    # No "sector_map": cluster_ladder_row.members already IS this cluster's membership, and the
    # whole-book map would be filtered to held names and add nothing. `thesis` is here only so
    # the agent can report thesis_tensions -- a ladder rank that contradicts a per-name verdict.
    "cluster":    {"state": ["thesis", "cluster_ladders", "open_flags"],
                   "cache": ["atr20", "earnings_calendar", "analyst_targets", "earnings_facts"],
                   # `ladder` is this agent's FIRST input: the deterministic ranking arithmetic
                   # (rel_intra_pp, dispersion, redundancy candidates, cluster room) it must not
                   # re-derive. The Wave-1 tails are the judgment it reasons ON TOP of -- a
                   # cluster ladder that ignores this run's catalysts is a price ranking wearing
                   # a fundamental costume.
                   "refs": ["ladder", "risk", "drift", "catalyst_tail", "signals_tail",
                            "quality_tail", "earnings_tail"],
                   "holdings": "trim", "shared": ["hbm_tracker"]},
    "strategist": {"state": ["thesis", "sector_map", "preferences", "open_flags"], "cache": [],
                   # "crosscheck" added 2026-09-07 -- crosscheck now runs after WAVE 2 (see
                   # cmd_crosscheck's docstring), specifically so its findings reach the
                   # strategist as a real ref instead of depending on the orchestrator to paste
                   # them into the dispatch prompt by hand.
                   # "valuation" added 2026-09-07 -- valuation_stretched means suppress a NEW
                   # BUY on that name (SKILL.md's valuation section); on-demand/monthly,
                   # MISSING on most runs by design.
                   "refs": ["drift", "sentiment", "risk", "book", "derisk", "triggers",
                            "rotation", "crosscheck", "macro_tail", "valuation"],
                   "holdings": "trim"},
}

REF_FILES = {
    "book": "compute_book.json", "risk": "compute_risk.json", "drift": "compute_drift.json",
    "journal": "compute_journal.json", "attribution": "compute_attribution.json",
    "rotation": "compute_rotation.json", "sentiment": "compute_sentiment.json",
    "derisk": "compute_derisk.json", "triggers": "compute_triggers.json",
    "buckets": "compute_buckets.json",
    "market_inputs": "market_inputs.json",
    # Added 2026-09-07, closing a gap between what SKILL.md's WAVES section promised (book
    # gets compute_bookcalc.json, tax gets compute_taxcalc.json) and what AGENT_SLICES actually
    # had a ref for -- neither WAVE-0 script output was reachable through this table before,
    # so slice_book.json/slice_tax.json could not carry them even though both files already
    # sit in the same run directory.
    "bookcalc": "compute_bookcalc.json", "taxcalc": "compute_taxcalc.json",
    # Cross-agent tail refs (added 2026-09-07). These are WAVE 1 agents' own out_<agent>.json
    # files, not compute script output -- but they live in the same run dir and the same
    # ref-by-path mechanism applies. This is what makes SKILL.md's WAVES promise ("thesis <-
    # catalyst's events, quality's flags, signals' buckets"; "cycle <- catalyst's events")
    # code-guaranteed instead of orchestrator hand-assembly: AGENT_SLICES["thesis"]/["cycle"]
    # below now actually reference these paths.
    "catalyst_tail": "out_catalyst.json", "quality_tail": "out_quality.json",
    "signals_tail": "out_signals.json", "earnings_tail": "out_earnings.json",
    # compute_ladder.json (added 2026-09-08) -- the deterministic half of the cluster ladder.
    "ladder": "compute_ladder.json",
    # macro_tail (added 2026-09-07): smith-strategist.md line 72 documents its stress table as
    # "anchored to smith-macro's live regime read" but AGENT_SLICES["strategist"] had no ref for
    # it -- the orchestrator had to hand-paste smith-macro's tail into the strategist dispatch
    # prompt, the same hand-assembly gap already fixed for thesis/cycle/crosscheck.
    "macro_tail": "out_macro.json",
    # crosscheck.json (added 2026-09-07, see cmd_crosscheck's docstring for the invocation-
    # order fix that makes this file exist before WAVE 3 dispatches).
    "crosscheck": "crosscheck.json",
    # compute_valuation.json (added 2026-09-07, smith_valuation.py) -- ON-DEMAND / MONTHLY,
    # not a mandatory every-run stage (see SKILL.md's valuation section). Only produced on a
    # run where the orchestrator dispatched a fetch of FMP statement data and ran
    # `smith_math.py valuation`; missing on a normal run is EXPECTED, not a problem -- refs
    # this file only from agents that already gate on cadence/mode, so cmd_slices' missing-ref
    # warning doesn't fire noise on every quick sweep.
    "valuation": "compute_valuation.json",
}
BASE_REF_FILES = {"lots": "lots.json"}

# ---------------------------------------------------------------------------
# PSEUDO-AGENT KEYS (added 2026-09-08)
# ---------------------------------------------------------------------------
# A cluster specialist is dispatched once per cluster in the same run, so it needs a distinct
# key per dispatch (slice_cluster_semis.json, out_cluster_optics.json) while running ONE agent
# definition. `cluster_<slug>` is that key: everything file-scoped uses the full key, everything
# prompt-scoped resolves to the shared template and to smith-cluster.md.
#
# Kept as a prefix convention rather than a registry deliberately -- the set of clusters is
# state.sector_map's business, changes whenever the book does, and a hard-coded roster here
# would silently make a newly-created cluster undispatchable.
CLUSTER_AGENT_PREFIX = "cluster_"


def is_cluster_agent(agent):
    return bool(agent) and agent.startswith(CLUSTER_AGENT_PREFIX)


def _skip_key(agent):
    """The key EXTERNAL_READERS / NEVER_SKIP are tested against. Every cluster_* dispatch is an
    external reader -- its real input is filings, product news and qualification announcements,
    which move when no file in the run dir does -- so it must resolve to the template name, not
    to its own namespaced key, or the never-skip protection would silently not apply to it."""
    return "cluster" if is_cluster_agent(agent) else agent


def resolve_agent(agent):
    """(slice spec, agent name for the prompt/definition). Any cluster_<slug> key resolves to
    the one shared "cluster" template; everything else is itself."""
    if is_cluster_agent(agent):
        return AGENT_SLICES.get("cluster"), "smith-cluster"
    return AGENT_SLICES.get(agent), f"smith-{agent}"

# Refs whose PRODUCER is genuinely on-demand, not a WAVE-0/Wave-1 stage that runs every time --
# a missing file here is the expected case, not a problem. Added 2026-09-07: cmd_slices'
# missing-ref check has no such distinction before this, so "valuation" (an on-demand check
# that runs on maybe 1 run in 50) would have reported MISSING on essentially every single run,
# training the orchestrator (and the user reading "problems") to tune out that list as
# permanently noisy -- the same alarm-fatigue risk this codebase's own G50/silence-shape
# incidents exist to prevent. catalyst_tail is folded in for the same reason, found live in
# the same audit that added "valuation": it is only conditionally dispatched (SKILL.md's
# CATALYST trigger), so a run where catalyst didn't fire showed the identical false-alarm
# MISSING line -- previously assessed as "cosmetic, not a bug", now actually fixed rather than
# just noted. An optional ref that IS present still resolves into read_these_files exactly
# like a mandatory one; only the missing case is treated differently.
# quality_tail / earnings_tail / signals_tail added 2026-09-08 with the cluster agent: quality
# is monthly, earnings is dispatched only near a print, and signals does not run on every mode.
# A cluster slice refs all three deliberately (they are the judgment it reasons on top of) and
# would otherwise report MISSING on most runs -- the same false-alarm class as `valuation`.
OPTIONAL_REFS = {"valuation", "catalyst_tail", "quality_tail", "earnings_tail", "signals_tail"}

# Agents whose REAL input is the outside world, not a file. Their slice can be byte-identical to
# last run's and they still have work to do, because news, prices and filings moved even when
# state did not. NEVER skip these on an unchanged digest -- that is the difference between a
# genuine saving and silently going blind.
EXTERNAL_READERS = {"signals", "thesis", "watchlist", "catalyst", "scout", "macro",
                    "earnings", "cycle", "quality", "cluster"}
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
    "book": "holdings", "ledger": "holdings", "tax": "lots_trims", "rebound": "session",
    "strategist": "always",
    # "cluster" (added 2026-09-08) is the TEMPLATE key every cluster_<slug> dispatch resolves
    # to via _skip_key. Its domain is `news`: a substitution ladder is reordered by
    # qualification announcements, product-transition timing and margin-pool evidence, none of
    # which move a file in the run dir. It is in EXTERNAL_READERS for the same reason and
    # therefore never skips on an unchanged digest.
    "cluster": "news",
}
DOMAIN_HELP = {
    "news": "new items since news_watermark",
    "calendar": "an earnings date confirmed/changed, or a print entering the window",
    "macro": "a rate/FOMC/CPI/NFP event, or a live options session",
    "session": "a trading session actually occurred since the last run",
    "holdings": "qty_changes non-empty, or lots.json changed",
    "fundamentals": "a new filing or reported quarter",
    "lots_trims": "lots.json changed, or the set of open TRIM/SELL proposals changed",
    "always": "its inputs are the Stage-1 tails, which are never visible here",
}


def _open_trims_sig(base_dir):
    """Stable signature of WHICH TRIM/SELL proposals are open, for smith-tax's domain check.
    Deliberately ids-only and sorted, NOT sizes: a re-sized trim sequences the same lots, so
    including size would fire the domain on a change that cannot alter the answer. Returns ""
    when proposals.json is unreadable, which compares unequal to any real signature and
    therefore dispatches -- unreadable state must never look like 'nothing changed'."""
    try:
        props = load_json(os.path.join(base_dir, "proposals.json"), default={}) or {}
        rows = props.get("proposals", props if isinstance(props, list) else [])
        ids = sorted(r.get("id") for r in rows
                     if isinstance(r, dict) and r.get("status") == "open"
                     and (r.get("direction_bucket") in ("TRIM", "SELL")
                          or any(w in str(r.get("action", "")).lower() for w in ("trim", "sell")))
                     and r.get("id"))
        return ",".join(ids)
    except Exception:
        return ""


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
    if domain == "lots_trims":
        # smith-tax was gated on "at least one open TRIM/SELL exists", which is nearly always
        # true, so it ran every deep review. Measured 2026-09-06: 77,880 tokens to conclude
        # FIFO == HIFO with a $0.00 tax delta on all five open trims -- a conclusion that cannot
        # change while neither the lots nor the trim set moves. Its real inputs are the lots and
        # WHICH trims are open, not whether any are.
        if ctx["lots_changed"]:
            return True, "lots.json changed since the previous run"
        if ctx["open_trims_changed"]:
            return True, "the set of open TRIM/SELL proposals changed since the previous run"
        return False, ("lots.json unchanged and the same TRIM/SELL proposals are open -- lot "
                       "sequencing cannot have changed")
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
    prior_open_trims_sig = (prior_slices.get("tax", {}) or {}).get("_open_trims_sig")
    open_trims_sig = _open_trims_sig(base)
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
        # None (no prior slice) reads as CHANGED -- a first run for this agent must dispatch.
        "open_trims_changed": prior_open_trims_sig is None or open_trims_sig != prior_open_trims_sig,
        "calendar_changed": (json.dumps(dc.get("earnings_calendar"), sort_keys=True) !=
                             json.dumps((prior_slices.get("watchlist", {}) or {})
                                        .get("data_cache.earnings_calendar"), sort_keys=True))
                            if prior_slices.get("watchlist") else False,
    }
    want = [a.strip() for a in (args.agents or "").split(",") if a.strip()] or list(AGENT_SLICES)
    written, problems = [], []
    for agent in want:
        spec, agent_label = resolve_agent(agent)
        if not spec:
            problems.append(f"unknown agent '{agent}' -- not in AGENT_SLICES")
            continue
        sl = dict(common)
        # The prompt-facing name is the AGENT DEFINITION (smith-cluster for every cluster_*
        # key); every file path stays on the namespaced key so N same-run dispatches of one
        # agent cannot overwrite each other's slice or tail.
        sl["agent"] = agent_label
        sl["agent_key"] = agent
        sl["output_file"] = os.path.join(rd, f"smith-{agent}-output.md")
        sl["holdings_path"] = os.path.join(rd, "holdings.json")
        sl["read_these_files"] = {}
        # Persist the markers the NEXT run's domain check reads back. `_lots_digest` was read at
        # the top of this function but never actually written into any slice, so `lots_changed`
        # had been permanently False since it was added -- the lots half of the `holdings`
        # domain check never once fired. Underscore-prefixed so they read as bookkeeping, and
        # excluded from the materiality comparison below like every other non-payload key.
        if agent == "book":
            sl["_lots_digest"] = lots_digest
        if agent == "tax":
            sl["_open_trims_sig"] = open_trims_sig
        if is_cluster_agent(agent):
            # WHICH cluster this dispatch is for. Without this the agent has a template and a
            # 30-cluster file and no idea which row is its job. The playbook (the axes that
            # decide the winner in THIS cluster) and the deterministic ladder row are inlined
            # because they are its primary input; compute_ladder.json stays referenced too, so
            # it can still see how its cluster sits against the rest of the book.
            slug = agent[len(CLUSTER_AGENT_PREFIX):]
            ladder = load_json(os.path.join(rd, "compute_ladder.json"), default={})
            match = [(name, row) for name, row in (ladder.get("clusters") or {}).items()
                     if row.get("slug") == slug]
            if not match:
                problems.append(f"{agent_label} [{agent}]: no cluster in compute_ladder.json has "
                                f"slug '{slug}' -- run `ladder` before rendering this slice, or "
                                f"check policy.cluster_playbooks for a renamed slug")
            else:
                cname, crow = match[0]
                sl["cluster_name"] = cname
                sl["cluster_prior_ladder"] = crow.get("prior_ladder")
                _place(sl, "cluster_ladder_row", crow, shared_dir, shared_once,
                       name=f"ladder_{slug}")

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
                problems.append(f"{agent_label} [{agent}]: unknown ref '{r}'")
            elif not os.path.exists(path):
                if r not in OPTIONAL_REFS:
                    problems.append(f"{agent_label} [{agent}]: {os.path.basename(path)} MISSING -- run the "
                                    f"pipeline before rendering slices")
                # else: silent by design -- an on-demand ref's absence is the expected case,
                # not a problem to surface every run (see OPTIONAL_REFS above).
            else:
                sl["read_these_files"][r] = path
        for sname in spec.get("shared", []):
            if sname in shared_paths:
                sl["read_these_files"][sname] = os.path.abspath(shared_paths[sname])
            else:
                problems.append(f"{agent_label} [{agent}]: shared source '{sname}' unavailable this run")

        if spec.get("holdings") == "trim":
            _place(sl, "holdings", trim, shared_dir, shared_once, name="holdings_trim")
        elif spec.get("holdings") == "full":
            _place(sl, "holdings", rows, shared_dir, shared_once, name="holdings_full")

        # completeness: a required payload must be present EITHER inline OR as a ref -- it
        # moved representation when large payloads became content-addressed, and a guard that
        # only knows the old shape reports false alarms instead of real ones.
        for k in spec["state"]:
            if k in ("thesis", "sector_map") and not sl.get(k) and k not in sl["read_these_files"]:
                problems.append(f"{agent_label} [{agent}]: '{k}' is neither inline nor referenced -- "
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
        rec = {"agent": agent_label, "agent_key": agent, "file": out,
               "bytes": os.path.getsize(out),
               "refs": len(sl["read_these_files"]), "inputs_digest": sl["inputs_digest"]}
        if is_cluster_agent(agent):
            rec["cluster"] = sl.get("cluster_name")
        dom = AGENT_DOMAIN.get(_skip_key(agent), "always")
        moved, evidence = _domain_moved(dom, ctx)
        rec["domain"] = dom
        rec["domain_moved"] = moved
        rec["domain_evidence"] = evidence
        if moved is False:
            no_domain_move.append(agent)
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
                    if _skip_key(agent) not in EXTERNAL_READERS and _skip_key(agent) not in NEVER_SKIP:
                        immaterial.append(agent)

        # THE SKIP SIGNAL IS `domain_moved`, NOT THE BYTE DIGEST (rewired 2026-09-06).
        #
        # The digest skip never fired once. Measured across every run that wrote slices
        # (08-30, 08-31, 09-01, 09-06): no skip-eligible agent's digest EVER repeated -- four
        # distinct values for `rebound`, all different. It cannot fire, by construction: the
        # digest hashes the CONTENT of every referenced file, and those references include
        # compute_*.json, which embeds live prices. Any run where a price moved -- i.e. every
        # run -- produces a fresh digest. A saving mechanism that is structurally unreachable
        # is worse than none, because its presence in the output implies the question was asked
        # and answered "no".
        #
        # `domain_moved` asks the right question: did the thing this agent READS actually move.
        # It was already computed above and already documented in dispatch_note as "the
        # strongest skip signal" -- it simply was not wired to anything. Now it is.
        # `moved is None` means the script cannot tell (news, fundamentals) and always
        # dispatches; only an explicit False skips.
        if moved is False and _skip_key(agent) not in EXTERNAL_READERS \
                and _skip_key(agent) not in NEVER_SKIP:
            rec["skip"] = True
            rec["skip_reason"] = (f"input domain '{dom}' did not move: {evidence}. "
                                  f"Reuse its prior output.")
            skippable.append(agent)

        prior = prior_digests.get(agent)
        if prior and prior == sl["inputs_digest"]:
            # Retained as an observation only -- never a skip vote. See above for why.
            rec["inputs_unchanged_since"] = prior_run
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
          "skip_note": ("Agents listed here had their INPUT DOMAIN observably not move -- no "
                        "qty_changes and unchanged lots for a holdings agent, no trading session "
                        "for a session agent, unchanged lots and the same open trims for tax. "
                        "Reuse their prior output instead of dispatching. Agents that read the "
                        "outside world (news, fundamentals) are NEVER listed, because the script "
                        "cannot see whether their domain moved; nor is the strategist, whose real "
                        "inputs are the Stage-1 tails and are not in its slice. Rewired from the "
                        "byte-digest test on 2026-09-06: that test never fired once in four "
                        "measured runs and could not, since the digest hashes compute_*.json "
                        "content, which embeds live prices."),
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
    # External producers Smith READS but does not write. Mounted under their SHARED_SOURCES key
    # so FRESHNESS stays a flat declarative table (same reasoning as `proposals.` above) and so
    # the path is declared exactly once for both the slice snapshot and the age check -- two
    # copies of a path is how one of them goes stale. A missing file reads as `missing`, which
    # for an `escalate` artefact is a validate defect, not a silence.
    for key, path in SHARED_SOURCES.items():
        root[key] = load_json(path, default={})
    return root


def _fresh_held_tickers(state):
    """The set of tickers currently in the book, for FRESHNESS `scope: held`.

    state["holdings"] is the authoritative live snapshot ([{ticker, qty, weight_pct}, ...]).
    Returns None -- meaning "do not scope" -- when it is absent or empty, so a state file
    without holdings fails OPEN to the old whole-map behaviour rather than silently ageing
    an artefact against an empty held set and calling everything out of scope.
    """
    rows = state.get("holdings")
    if not isinstance(rows, list) or not rows:
        return None
    held = {r.get("ticker") for r in rows if isinstance(r, dict) and r.get("ticker")}
    return held or None


def _fresh_lookup(state, dotted):
    node = state
    for part in dotted.split("."):
        if not isinstance(node, dict):
            return None
        node = node.get(part)
    return node


def _fresh_stamp(state, artefact, spec, scope=None):
    """Resolve an artefact's as_of date per its `stamp` rule. Returns (date_str, detail).

    `scope="held"` restricts per-entry ageing to tickers still in the book -- see the `scope`
    field note in smith_core.FRESHNESS for why (2026-09-09: three exited names were driving
    signal_history dark while every held name was stamped that morning).
    """
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
        keys = set(artefact or {})
        out_of_scope = set()
        if scope == "held":
            held = _fresh_held_tickers(state)
            if held is not None:
                out_of_scope = keys - held
                stamps = {k: v for k, v in stamps.items() if k in held}
                keys = keys & held
        if not stamps:
            # Every stamped entry is out of scope -- the artefact holds only exited names.
            # Unknowable age, not a fresh one.
            return None, ({"entries_out_of_scope": len(out_of_scope)} if out_of_scope else None)
        oldest = min(stamps.values())
        # The age of the OLDEST IN-SCOPE entry is the artefact's age -- a map-level date would
        # hide precisely the names nobody has looked at, which is the whole reason for
        # per-entry. Entries outside the scope are counted and reported, never dropped
        # silently: "3 exited names not aged" is information, an absence is not.
        unstamped = [k for k in keys if k not in stamps]
        detail = {"entries_stamped": len(stamps), "entries_unstamped": len(unstamped),
                  "oldest_entries": sorted(k for k, v in stamps.items() if v == oldest)[:5]}
        if unstamped:
            detail["unstamped_sample"] = sorted(unstamped)[:5]
        if out_of_scope:
            detail["entries_out_of_scope"] = len(out_of_scope)
            detail["out_of_scope_sample"] = sorted(out_of_scope)[:5]
            detail["scope"] = scope
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

        as_of, detail = _fresh_stamp(state, artefact, cfg["stamp"], cfg.get("scope"))
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


def validate_ledger_ts(base_dir):
    """`ts` must be ISO-8601 with a UTC offset.

    Added 2026-09-01: an unattended run wrote its RUN-DIR LABEL ("2026-08-31-1554") into this
    column -- no time, no timezone. It went unnoticed because every reader slices [:10], so it
    parsed as a date by luck: 38 real timestamps and one that merely looked like one. A ledger
    is the P&L spine, and a column that is silently 3% a different format is a trap for the next
    reader who does arithmetic on it. `append-ledger` now normalises on write; this catches
    anything written by another path.
    """
    out = []
    try:
        with open(os.path.join(base_dir, "ledger.csv")) as fh:
            for n, r in enumerate(csv.DictReader(fh), start=2):
                t = str(r.get("ts") or "").strip()
                if not LEDGER_TS_RE.match(t):
                    out.append(f"ledger.csv row {n} has ts={t!r}, not ISO-8601 with a UTC offset "
                               f"(e.g. 2026-09-01T14:36:00+05:30). A run-dir label is not a "
                               f"timestamp -- it carries no timezone.")
    except OSError:
        pass
    return out


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

        # An IN-SCOPE entry with no stamp of its own is its own defect, named separately
        # (2026-09-09). Before this, a single unstamped entry only ever showed up as the
        # PARENT map reading `stale` -- so `thesis` escalated across a 34-name map because
        # exactly one held name, META, had been revived from archive without a `reviewed_on`.
        # The parent's status told you something was wrong; it could not tell you it was one
        # field on one ticker, which is a two-second fix wearing the costume of a stale map.
        # Reported for every class, not just escalate: an unstamped held entry is a bookkeeping
        # error whatever the artefact's on_stale policy, and it is cheap to say which name.
        if row.get("entries_unstamped"):
            names = ", ".join(row.get("unstamped_sample") or []) or "unknown"
            more = row["entries_unstamped"] - len(row.get("unstamped_sample") or [])
            defects.append(
                f"FRESHNESS ENTRY UNSTAMPED: {key} has {row['entries_unstamped']} in-scope "
                f"entr{'y' if row['entries_unstamped'] == 1 else 'ies'} with no per-entry date "
                f"({names}{f' +{more} more' if more > 0 else ''}, owner {owner}). The entry's "
                f"age is unknowable, so the whole map cannot read fresh. Stamp the named "
                f"entr{'y' if row['entries_unstamped'] == 1 else 'ies'} with the date they were "
                f"genuinely last reviewed -- not today's date, which would assert a review "
                f"that did not happen.")
    return defects


def evaluate_runs(base_dir, today=None, days=10):
    """Reconcile EXPECTED scheduled runs against the artefacts a run actually leaves behind.

    Added 2026-09-01 after two failures a week apart that a single check would have caught:
      * agent-smith-weekly-us fired 2026-08-31 09:08 IST, hung 22 seconds in, and left NO run
        directory, NO ledger row and NO report -- while its session stayed flagged `running` for
        30 hours. Nothing on this desk noticed. The weekly report's own run-counter said "0 runs"
        but could not say WHY, because it only counts ledger rows and cannot distinguish "the
        task never fired" from "the task fired and died".
      * The opposite error, made by a reader rather than the code: a session's `lastActivityAt`
        was taken as proof a run had happened. Session metadata is not a run record. THE ONLY
        EVIDENCE THAT A RUN HAPPENED IS THE ARTEFACTS IT LEFT -- a run directory and a ledger
        row. This function is the sanctioned way to ask.

    Deliberately reads only the desk's own files. It does not (and cannot) see the scheduler's
    lastRunAt, which is the point: an expectation derived from the schedule and compared against
    artefacts catches a task that fired and produced nothing, which is exactly the case that a
    scheduler-reported "it ran" would hide.
    """
    today = today or date.today()
    # Declared outages: days the desk COULD NOT have run for a reason outside it -- the host was
    # unavailable, the account was blocked, the machine was off. Declared 2026-09-01 after `runs`
    # flagged 2026-08-27/28 as MISSING and the cause turned out to be a Claude membership issue:
    # Claude Code could not run, so the scheduler never fired. That is not a desk defect and
    # should not sit in `validate` forever pretending to be one.
    #
    # An outage SUPPRESSES THE DEFECT, NEVER THE FACT. The day still appears in the report with
    # its reason attached, because "we did not look at the book on those days" stays true and
    # stays relevant to any week-over-week read; what changes is only that it stops being
    # something to fix.
    state = load_json(os.path.join(base_dir, "state.json"), default={})
    outages = []
    for o in (state.get("run_outages") or []):
        try:
            outages.append((date.fromisoformat(o["from"]), date.fromisoformat(o["to"]),
                            o.get("reason") or "declared outage"))
        except (KeyError, ValueError, TypeError):
            continue

    def outage_for(d):
        for a, b, why in outages:
            if a <= d <= b:
                return why
        return None

    rows = []
    try:
        with open(os.path.join(base_dir, "ledger.csv")) as fh:
            rows = list(csv.DictReader(fh))
    except OSError:
        pass
    by_day = {}
    for r in rows:
        dt = parse_ts(r.get("ts"))
        if dt:
            by_day.setdefault(dt.astimezone(IST).date(), []).append(r)
    runs_dir = os.path.join(base_dir, "runs")
    dirs_by_day = {}
    if os.path.isdir(runs_dir):
        for name in os.listdir(runs_dir):
            dt = parse_ts(name)
            if dt:
                dirs_by_day.setdefault(dt.astimezone(IST).date(), []).append(name)

    out = []
    for i in range(days):
        d = today - timedelta(days=i)
        expected = []
        if d.weekday() < 5:
            expected.append("agent-smith-daily-us")
        if d.weekday() == 0:
            expected.append("agent-smith-weekly-us")
        led, rd = by_day.get(d, []), dirs_by_day.get(d, [])
        modes = {r.get("mode", "?") for r in led}
        why = outage_for(d)
        # PER-TASK, not per-day. A Monday expects BOTH the daily and the weekly, and checking
        # only "did anything run" marks 2026-08-31 as ok -- the daily delivered while the weekly
        # fired, hung and left nothing. That is precisely the failure this function exists to
        # catch, so the weekly is tested on its own evidence: a deep-mode ledger row that day.
        weekly_missing = ("agent-smith-weekly-us" in expected and "deep" not in modes
                          and d != today)
        if expected and not led and not rd:
            verdict = "MISSING" if d != today else "pending"
        elif expected and rd and not led:
            verdict = "FIRED_BUT_NO_LEDGER_ROW"
        elif led and not rd:
            verdict = "LEDGER_ROW_WITHOUT_RUN_DIR"
        elif weekly_missing:
            verdict = "WEEKLY_NO_DEEP_RUN"
        elif not expected and (led or rd):
            verdict = "unscheduled"          # an interactive run -- normal, not a defect
        else:
            verdict = "ok"
        if why and verdict in ("MISSING", "WEEKLY_NO_DEEP_RUN", "FIRED_BUT_NO_LEDGER_ROW"):
            verdict = "outage"
        out.append({"date": d.isoformat(), "weekday": d.strftime("%a"), "outage_reason": why,
                    "expected": expected, "run_dirs": sorted(rd),
                    "ledger_rows": len(led),
                    "modes": sorted({r.get("mode", "?") for r in led}),
                    "verdict": verdict})
    return out


def validate_runs(base_dir):
    """Fail on a scheduled run that fired and left nothing, or left half of what it should.

    Only looks back 3 completed weekdays: older gaps are history the weekly report already
    carries, and a validator that fails forever on a month-old miss stops being read."""
    defects, checked = [], 0
    for row in evaluate_runs(base_dir):
        if row["date"] == str(date.today()):
            continue
        if checked >= 3:
            break
        if row["verdict"] == "outage":
            continue                     # declared unavailable: not a miss, and it must not
                                         # consume the lookback budget either, or two outage
                                         # days would push a real miss out of the window
        if row["expected"]:
            checked += 1
        if row["verdict"] == "MISSING":
            defects.append(f"NO RUN ARTEFACTS for {row['date']} ({row['weekday']}) despite "
                           f"{', '.join(row['expected'])} being scheduled: no run directory and "
                           f"no ledger row. A task that fires and dies leaves exactly this "
                           f"signature -- check the session, do not assume it ran.")
        elif row["verdict"] == "WEEKLY_NO_DEEP_RUN":
            defects.append(f"WEEKLY DID NOT DELIVER on {row['date']} ({row['weekday']}): "
                           f"agent-smith-weekly-us was scheduled and no deep-mode ledger row "
                           f"exists for that day. The daily running that day does NOT satisfy "
                           f"it -- on 2026-08-31 the daily completed while the weekly hung 22 "
                           f"seconds in and left nothing.")
        elif row["verdict"] == "FIRED_BUT_NO_LEDGER_ROW":
            defects.append(f"{row['date']} has run director{'ies' if len(row['run_dirs'])>1 else 'y'} "
                           f"{row['run_dirs']} but NO ledger row -- the run started and did not "
                           f"finish its PERSIST step.")
    return defects


def cmd_runs(args):
    """Report expected-vs-actual runs. Every timestamp shown in UTC and IST together.

    `--declare-outage FROM:TO --reason "..."` records a period the desk could not have run for
    an external reason. Written through this command rather than by hand-editing state.json,
    for the same reason `add-proposal` and `append-ledger` exist: every hand-assembled write in
    this codebase's history eventually produced a malformed record.
    """
    today = datetime.strptime(args.today, "%Y-%m-%d").date() if args.today else date.today()
    if getattr(args, "declare_outage", None):
        raw = args.declare_outage
        sep = ":" if ":" in raw else (".." if ".." in raw else None)
        if not sep:
            fail("--declare-outage takes FROM:TO, e.g. 2026-08-27:2026-08-28")
        a, _, b = raw.partition(sep)
        try:
            d_from, d_to = date.fromisoformat(a.strip()), date.fromisoformat(b.strip().lstrip("."))
        except ValueError:
            fail(f"--declare-outage dates must be YYYY-MM-DD, got {raw!r}")
        if d_to < d_from:
            fail(f"--declare-outage end {d_to} precedes start {d_from}")
        if not args.reason:
            fail("--declare-outage requires --reason: an undocumented outage is indistinguishable "
                 "from a bug someone silenced")
        sp = os.path.join(args.base_dir, "state.json")
        st = load_json(sp, default={})
        lst = st.setdefault("run_outages", [])
        entry = {"from": d_from.isoformat(), "to": d_to.isoformat(), "reason": args.reason,
                 "declared_on": str(today)}
        if any(o.get("from") == entry["from"] and o.get("to") == entry["to"] for o in lst):
            emit({"declared": False, "note": "an outage with those exact dates is already on "
                                             "record -- not duplicated", "run_outages": lst})
            return
        lst.append(entry)
        safe_write(sp, st)
        emit({"declared": True, "outage": entry, "run_outages": lst,
              "note": "the days remain visible in `runs` with their reason; they simply stop "
                      "counting as defects."})
        return
    rows = evaluate_runs(args.base_dir, today, args.days)
    bad = [r for r in rows if r["verdict"] in ("MISSING", "FIRED_BUT_NO_LEDGER_ROW",
                                               "LEDGER_ROW_WITHOUT_RUN_DIR",
                                               "WEEKLY_NO_DEEP_RUN")]
    emit({"as_of": fmt_ts(datetime.now(IST).isoformat(timespec="seconds")),
          "days": args.days, "rows": rows, "problems": bad,
          "headline": ("Runs: all scheduled runs left artefacts."
                       if not bad else
                       "Runs: " + "; ".join(f"{b['date']} {b['verdict']}" for b in bad)),
          "note": "A run is evidenced by a run directory plus a ledger row. Session metadata "
                  "(lastActivityAt, isRunning) is NOT a run record and must never be read as one."})


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

    # --- stress table (added 2026-08-31, the run that gave it a structured contract) ---------
    # A persisted key nothing reads is the same defect as no key at all, so the artefact and its
    # reader landed together. The weekly is the right reader: this is a deep-run product and the
    # question it answers -- how much of the book is exposed to each way the thesis can fail --
    # is a weekly question, not a daily one.
    stress = state.get("stress_table") or {}
    scen = stress.get("scenarios") or []
    L.append("## Stress table")
    L.append("")
    if scen:
        anch = stress.get("anchored_to") or {}
        worst = min([x["impact_pct_low"] for x in scen
                     if isinstance(x.get("impact_pct_low"), (int, float))], default=None)
        bits = [f"{k.replace('_pct','').replace('_',' ')} {v}"
                for k, v in anch.items() if v not in (None, "")]
        L.append(f"As of {stress.get('as_of', 'n/a')}"
                 + (f" · anchored to {', '.join(bits)}" if bits else "") + ".")
        L.append("")
        L.append("| scenario | impact | most exposed | basis |")
        L.append("|---|---|---|---|")
        for x in sorted(scen, key=lambda r: (r.get("impact_pct_low")
                                             if isinstance(r.get("impact_pct_low"), (int, float))
                                             else 0)):
            lo, hi = x.get("impact_pct_low"), x.get("impact_pct_high")
            rng = (f"{lo:+.0f}% to {hi:+.0f}%"
                   if isinstance(lo, (int, float)) and isinstance(hi, (int, float))
                   else "not quantified")
            exposed = ", ".join(x.get("most_exposed") or []) or "—"
            basis = x.get("basis") or "—"
            flag = " ⚠" if basis == "static_assumption" else ""
            L.append(f"| {x.get('scenario','')} | {rng} | {exposed} | {basis}{flag} |")
        L.append("")
        if worst is not None:
            L.append(f"Worst modelled single scenario: **{worst:+.0f}%** of book. These are "
                     "independent scenarios, not additive, and a `static_assumption` basis means "
                     "that row carries a standing rule of thumb rather than a figure re-derived "
                     "against this run's macro strip.")
        prev = state.get("stress_table_prev") or {}
        if prev.get("scenarios"):
            pw = min([x["impact_pct_low"] for x in prev["scenarios"]
                      if isinstance(x.get("impact_pct_low"), (int, float))], default=None)
            if pw is not None and worst is not None and pw != worst:
                L.append("")
                L.append(f"Worst case moved {pw:+.0f}% → {worst:+.0f}% since the previous run "
                         f"(as of {prev.get('as_of', 'n/a')}).")
    else:
        L.append("Not recorded. smith-strategist emits `stress_table` on every deep run; "
                 "if this is empty after one, its output is being discarded.")
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
    # freshness_root, not bare state -- the report's staleness ledger reported
    # `proposals.scorecard` as MISSING on the first W36 run while the scorecard was present and
    # stamped today, because that artefact lives in proposals.json and only resolves through the
    # `proposals.` prefix. A staleness ledger that invents a missing artefact is worse than none:
    # it sends the reader hunting for a limb that is working.
    rows = evaluate_freshness(freshness_root(args.base_dir, state), today)
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


# ---------------------------------------------------------------------------
# CROSSCHECK (added 2026-09-06) -- adjudicate conflicts BETWEEN sub-agents
# ---------------------------------------------------------------------------
# THE PROBLEM. Stage 1 dispatches every analyst in parallel, so no agent can see any other's
# findings. That is fine for agents that observe independent things and fatal for agents whose
# job is to INTERPRET what the others found. Four failures from the 2026-09-06 deep run, all in
# the same run, none detected by anything:
#
#   1. EVIDENCE GAP. smith-thesis wrote APH `strengthening` with
#      evidence_against: "none found this run". smith-quality, the same run, found APH interest
#      expense +157% QoQ with debt +21% and goodwill +66%. The G58 rule says both sides must
#      survive compression -- it is defeated by parallelism, because the counter-evidence existed
#      in a sibling's output that thesis could not read.
#   2. HANDOFF TO NOWHERE. smith-thesis ended a tension with "proximate cause unresolved, handed
#      to smith-catalyst". Catalyst had already run, in parallel. The handoff went nowhere, and
#      thesis's verdict was formed without the answer catalyst had actually found.
#   3. UNADJUDICATED CONTRADICTION. smith-catalyst reported a STRUCTURAL memory tailwind
#      (DRAM +50%/NAND +60% QoQ "this quarter"); smith-cycle reported TrendForce 4Q26 at
#      +3-8% QoQ. Directly opposed, neither saw the other, and the briefing carried both. The
#      catalyst figure later failed tier-1 corroboration entirely.
#   4. READ-WRITE RACE. smith-ledger rebuilt lots.json while smith-tax was reading it -- tax's
#      own output records a 13:04 read showing 6 mismatches and a 13:09 read showing clean --
#      and smith-book reported "APH has no lots.json entry" for the same reason.
#
# This command finds 1-3 mechanically from the merged tails. 4 is fixed by ordering (see the
# WAVES section of SKILL.md), not by detection.

_HANDOFF_RE = r"(?:handed|hand(?:ing)?\s+(?:it\s+)?(?:off\s+)?|defer(?:red)?|passed)\s+to\s+(smith-[a-z]+)"


def _cc_load(rd, agent):
    """A missing agent output is NORMAL -- not every agent runs in every wave or every mode --
    so this returns {} rather than raising. load_json(default=...) still raises on a missing
    path, which is right for a required input and wrong for an optional one."""
    path = os.path.join(rd, f"out_{agent}.json")
    if not os.path.exists(path):
        return {}
    try:
        return load_json(path, default={}) or {}
    except Exception:
        return {}


def cmd_crosscheck(args):
    """Detect conflicts between this run's sub-agent outputs. Read-only; emits findings only.

    CORRECTED INVOCATION POINT (2026-09-07). Originally documented to run "after the observer
    wave, before the interpreter wave" -- but two of its own five rules (evidence_gap,
    thesis_vs_catalyst_threat) read `thesis`'s ACTUAL WRITTEN VERDICT, and two more
    (catalyst_vs_cycle, thesis_vs_price) read `cycle`/`thesis` too. thesis and cycle are WAVE 2
    (interpreter) agents -- at the documented invocation point their out_*.json files do not
    exist yet, so `_cc_load` silently returns {} for both and 4 of 5 rules are structurally
    inert (only handoff_to_nowhere, a text-regex over Wave-1 outputs, can ever fire there).
    This was found live: a real deep run's crosscheck call returned `agents_seen: [catalyst,
    signals]` and 0 findings, exactly this bug, silently -- not the "0 findings, everything's
    fine" it read as.

    Run this AFTER WAVE 2 has merged and BEFORE WAVE 3 (the strategist) dispatches. This can no
    longer PREVENT an interpreter from writing a bad verdict (that job belongs to the
    AGENT_SLICES embed -- thesis/cycle receiving Wave-1 tails inline in their own dispatch
    prompt, so they have the evidence before they write anything). What crosscheck catches now
    is the backstop case: an interpreter had the evidence and still produced a conflicting
    verdict, or an unresolved tension between two interpreters. Its findings feed WAVE 3 --
    the strategist should know about an unadjudicated tension before sizing a proposal on top
    of it, which is a genuinely useful recipient this rule never had before.

    Writes crosscheck.json to run_dir (added 2026-09-07) so cmd_slices can reference it as a
    plain ref file into the strategist's slice, the same mechanism every other compute output
    already uses -- previously this only ever printed to stdout, so "embed high findings into
    the next dispatch" depended on the orchestrator remembering to paste JSON into a prompt by
    hand, the exact G50 shape this codebase elsewhere closes with a mechanical file+ref path.
    """
    import re
    rd = args.run_dir
    thesis = _cc_load(rd, "thesis") or {}
    quality = _cc_load(rd, "quality") or {}
    catalyst = _cc_load(rd, "catalyst") or {}
    signals = _cc_load(rd, "signals") or {}
    cycle = _cc_load(rd, "cycle") or {}
    triggers = load_json(os.path.join(rd, "compute_triggers.json"), default={}) or {}

    changed = ((thesis.get("thesis") or {}).get("changed") or {})
    qflags = quality.get("quality_flags") or {}
    findings = []

    # --- 1. evidence gap: a sibling produced counter-evidence the thesis says does not exist ---
    for tk, entry in changed.items():
        if not isinstance(entry, dict):
            continue
        against = entry.get("evidence_against")
        empty = (not against) or all(
            isinstance(a, dict) and re.search(r"\bnone\b|not found|no counter", str(a.get("claim", "")), re.I)
            for a in against)
        if empty and tk in qflags:
            mags = [f.get("magnitude") for f in (qflags[tk] if isinstance(qflags[tk], list) else [])
                    if isinstance(f, dict) and f.get("magnitude")]
            findings.append({
                "kind": "evidence_gap", "ticker": tk, "severity": "high",
                "detail": (f"smith-thesis wrote {tk} `{entry.get('status')}` with an EMPTY "
                           f"evidence_against, while smith-quality flagged it in the same run: "
                           f"{'; '.join(str(m) for m in mags[:2])}. G58 says both sides must "
                           f"survive -- they cannot when the other side is in a sibling's output "
                           f"the agent could not read."),
                "action": "re-dispatch smith-thesis for this ticker with the quality flag embedded"})

    # --- 2. thesis vs a live catalyst_threat / trigger ------------------------------------
    threats = {c.get("ticker") for c in (triggers.get("catalyst_threat") or []) if isinstance(c, dict)}
    for tk, entry in changed.items():
        if isinstance(entry, dict) and entry.get("status") in ("strengthening", "intact") and tk in threats:
            findings.append({
                "kind": "thesis_vs_catalyst_threat", "ticker": tk, "severity": "medium",
                "detail": (f"thesis says `{entry.get('status')}` while a live catalyst_threat "
                           f"fires on {tk}. Not necessarily wrong -- a name can strengthen under "
                           f"a probabilistic threat -- but it must be argued, not left implicit."),
                "action": "strategist weighs both; thesis should name the tension"})

    # --- 3. handoffs to an agent that already ran ----------------------------------------
    for name, blob in (("thesis", thesis), ("catalyst", catalyst), ("cycle", cycle),
                       ("quality", quality), ("signals", signals)):
        for m in re.finditer(_HANDOFF_RE, json.dumps(blob), re.I):
            target = m.group(1).lower()
            findings.append({
                "kind": "handoff_to_nowhere", "from": f"smith-{name}", "to": target,
                "severity": "high",
                "detail": (f"smith-{name} handed a question to {target}, which runs in the SAME "
                           f"parallel wave -- so it never received it and smith-{name}'s verdict "
                           f"was formed without the answer."),
                "action": f"either order {target} before smith-{name}, or re-dispatch smith-{name} "
                          f"with {target}'s output embedded"})

    # --- 4. catalyst direction vs cycle position -----------------------------------------
    pos = cycle.get("cycle_position")
    if pos in ("late", "rolling"):
        for c in (catalyst.get("catalysts") or []):
            if isinstance(c, dict) and c.get("direction") == "tailwind" and c.get("horizon") == "structural":
                findings.append({
                    "kind": "catalyst_vs_cycle", "severity": "high",
                    "detail": (f"smith-catalyst calls \"{str(c.get('headline'))[:90]}\" a "
                               f"STRUCTURAL tailwind while smith-cycle holds the cycle at "
                               f"`{pos}`. A structural tailwind and a late cycle are not "
                               f"automatically contradictory -- price up, second derivative down "
                               f"is coherent -- but ONE of them must say which it weighted, with "
                               f"its source. Neither saw the other."),
                    "affects": c.get("affects"), "source": c.get("source"),
                    "action": "state explicitly in the briefing which reading was weighted and why"})

    # --- 5. thesis strengthening on a peer laggard ---------------------------------------
    hist = (signals.get("signal_history") or {}).get("changed") or {}
    for tk, entry in changed.items():
        buckets = hist.get(tk) or []
        if isinstance(entry, dict) and entry.get("status") == "strengthening" and "PEER LAGGARD" in buckets:
            findings.append({
                "kind": "thesis_vs_price", "ticker": tk, "severity": "low",
                "detail": (f"thesis `strengthening` on {tk} while signals has it a PEER LAGGARD. "
                           f"Often correct -- that is what a value entry looks like -- but it is "
                           f"the pattern that also describes a thesis lagging the tape."),
                "action": "note in the briefing rather than resolve"})

    # --- 6. cluster ladder vs per-name thesis (added 2026-09-08) --------------------------
    # smith-cluster ranks members COMPARATIVELY; smith-thesis judges each one on its own. When
    # a name is ranked last in its cluster while the desk still calls it strengthening -- or is
    # ranked first on a watch thesis -- two agents have looked at the same company and reached
    # opposite conclusions. That is not noise to be averaged away: from 2026-09-08 the ladder
    # can DRIVE a live rotation, so an unadjudicated tension here becomes a sized trade. The
    # agent is asked to self-report these in `thesis_tensions`; this rule catches the ones it
    # did not, which is the whole point of a backstop.
    #
    # Reads state, not a tail: only up to LADDER_MAX_DISPATCH clusters refresh per run, and a
    # ladder from two runs ago that still contradicts today's thesis is exactly as consequential
    # as one written this morning -- it has the same trigger authority.
    _cc_state = load_json(os.path.join(args.base_dir, "state.json"), default={}) or {}
    _ladders = _cc_state.get("cluster_ladders") or {}
    _thesis_map = _cc_state.get("thesis") or {}
    for _cname, _L in _ladders.items():
        if not isinstance(_L, dict):
            continue
        _auth, _, _ = smith_risk.ladder_authority(
            _L, date.fromisoformat(args.today) if args.today else date.today(),
            ttl_days=LADDER_TTL_DAYS, min_scored=LADDER_MIN_SCORED_CALLS)
        _ranking = _L.get("ranking") or []
        _self_reported = {r.get("ticker") for r in (_L.get("thesis_tensions") or [])
                          if isinstance(r, dict)}
        for _r in _ranking:
            if not isinstance(_r, dict):
                continue
            _tk, _verdict = _r.get("ticker"), _r.get("verdict")
            if not _tk or _tk in _self_reported:
                continue
            _st = smith_risk.thesis_status(_thesis_map.get(_tk))
            if _verdict == "laggard" and _st == "strengthening":
                _detail = (f"the {_cname} ladder ranks {_tk} LAST while smith-thesis calls it "
                           f"strengthening. One of the two is wrong about the same company.")
            elif _verdict == "leader" and _st in ("watch", "broken"):
                _detail = (f"the {_cname} ladder ranks {_tk} FIRST while smith-thesis calls it "
                           f"{_st}. One of the two is wrong about the same company.")
            else:
                continue
            findings.append({
                "kind": "ladder_vs_thesis", "ticker": _tk, "cluster": _cname,
                # `high` only when the ladder can actually act. A contradicted ranking that
                # carries no trigger authority is worth reporting, not worth blocking on.
                "severity": "high" if _auth in ("rank", "full") else "medium",
                "detail": (_detail + f" The ladder's authority this run is `{_auth}`"
                           + (" -- it can size a rotation on this ranking."
                              if _auth in ("rank", "full") else
                              " -- advisory only, so nothing is being sized on it yet.")),
                "action": "strategist adjudicates before sizing any rotation in this cluster"})

    by_sev = {"high": 0, "medium": 0, "low": 0}
    for f in findings:
        by_sev[f.get("severity", "low")] += 1
    blocking = [f for f in findings if f.get("severity") == "high"]

    # Write to run_dir FIRST (added 2026-09-07) so cmd_slices can reference this file as a
    # plain ref -- the same mechanism as any other compute output -- into the strategist's
    # slice, instead of "embed high findings" depending on the orchestrator remembering to
    # paste JSON into a prompt by hand.
    safe_write(os.path.join(rd, "crosscheck.json"),
              {"as_of": args.today, "findings": findings, "count": len(findings),
               "by_severity": by_sev, "blocking": blocking})

    emit({"as_of": args.today, "findings": findings, "count": len(findings), "by_severity": by_sev,
          "agents_seen": [n for n, b in (("thesis", thesis), ("quality", quality),
                                         ("catalyst", catalyst), ("signals", signals),
                                         ("cycle", cycle)) if b],
          "blocking": blocking,
          "note": ("Run between WAVE 2 (interpreters) and WAVE 3 (strategist) -- see this "
                   "function's docstring for why the old pre-Wave-2 timing left 4 of 5 rules "
                   "structurally inert. A `high` finding here means an interpreter formed a "
                   "verdict that still conflicts with a sibling's finding despite the "
                   "AGENT_SLICES embed; embed it into the strategist's Wave-3 dispatch so a "
                   "sized proposal is never built on top of an unadjudicated tension.")})
