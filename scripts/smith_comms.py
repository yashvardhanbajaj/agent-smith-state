"""The desk conversation: sub-agents asking, telling, answering and debating each other.

WHY (added 2026-09-19, user request: "they should not just compute, they should be able to talk
to each other and pass on relevant info"). Until now the fleet shared a blackboard but never
spoke. Wave 1 wrote its tail, the orchestrator re-rendered slices, Wave 2 read those tails, a
script listed where they disagreed, and the strategist "weighed both". Information only ever
flowed forward, and nobody could ask anything:
  * 2026-09-19: crosscheck flagged thesis `strengthening` on AMAT and QCOM against a live
    catalyst_threat. Neither agent ever heard about it. The strategist adjudicated by guessing,
    and the underlying cause -- one article mapped onto all 27 holdings -- was never put to the
    agent that owns it, which is the only one that could have said "that threat does not touch
    AMAT's revenue".
  * An earlier run: thesis wrote "handed to smith-catalyst" about a question catalyst had
    already finished running without. A handoff with no delivery path is a note to nobody.

WHAT THIS IS. A message ledger per run (runs/<id>/comms/messages.json) and a router the
orchestrator calls between layers. Agents write three kinds of message in their JSON tail
under `comms`:
    asks     a question to the analyst that OWNS the answer (see DIRECTORY)
    tells    a finding that falls inside another analyst's ownership
    answers  a reply to a message in their inbox: held / revised / cannot_answer / noted
Crosscheck conflicts become DEBATES: the verdict owner and the counter-party each receive the
other's evidence and must answer. A `revised` answer carries a revision of the agent's own
output; the router overlays it into out_<agent>.json (the original is kept as
out_<agent>.r0.json), re-stages it, and TELLS every agent that already consumed the stale
version. Rounds continue until nothing is open, not for a fixed number of waves -- the user's
instruction was that analysis quality outranks time and tokens, and that the run is not
restricted to two waves.

WHAT IT DELIBERATELY IS NOT.
  * Not free-form chat. Every message names one issue, one owner, and the verdict that hinges
    on it. Prose between agents cannot be audited; typed messages can, and every one of them
    reaches the briefing and findings.json.
  * Not unbounded. Rounds, thread depth and per-agent asks are capped (generously), identical
    questions are refused, and a settled debate is never reopened in the same run. A cap that
    is hit is REPORTED -- an unanswered question is shown to the user, never silently dropped
    and never answered by the orchestrator on an agent's behalf.
  * Not a way around compute-first. Numbers a script can produce are asked of `desk`, which the
    orchestrator answers by running the script; no analyst estimates them for another.
"""
import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone

SCHEMA_VERSION = 1
COMMS_DIR = "comms"
LEDGER = "messages.json"
DIGEST = "digest.json"

MAX_ROUNDS = 6                    # quality first (user, 2026-09-19); still a hard stop
MAX_ASKS_PER_AGENT_PER_ROUND = 8
MAX_THREAD_DEPTH = 4              # ask -> answer -> follow-up -> answer
MAX_OPEN = 120
REDELIVER_LIMIT = 1               # an agent that returns without answering gets one reminder
DEBATE_SEVERITIES = ("high", "medium")
POSITIONS = ("held", "revised", "cannot_answer", "noted")

# Who owns what. An ask goes to the OWNER of the answer, never to whoever happens to be nearby.
# Embedded into every slice so an agent routes its own questions correctly.
DIRECTORY = {
    "signals": "price/volume/news signal buckets per holding, peer-relative strength, "
               "journal-scored signal history and hit rates",
    "catalyst": "dated, sourced FACTOR events (competitors, supply chain, policy, financing, "
                "Asia session) and exactly which holdings each one touches, with magnitude",
    "thesis": "per-holding thesis status (intact/strengthening/watch/broken) with evidence for "
              "and against; the sector map",
    "earnings": "a specific print: beat/miss vs consensus, guidance, implied move, post-earnings drift",
    "cycle": "AI-capex cycle position (accelerating/mid/late/rolling) from capex guides, memory "
             "contract pricing and semicap book-to-bill",
    "quality": "financial-statement quality: accruals vs cash, dilution, leverage, SBC, customer "
               "concentration, auditor and going-concern flags",
    "scout": "macro regime, Fed/FOMC, rates, options positioning, the event calendar, and the "
             "non-AI diversifier bench",
    "watchlist": "entry setups on non-held names; the earnings calendar",
    "rebound": "names that fell too far in a broad selloff, their support levels and staging",
    "cluster": "(cluster_<slug>) which member of one cluster captures the shared tailwind: "
               "ranking, redundancy, margin-pool migration, non-held substitutes",
    "strategist": "sized proposals, the risk-off read, the stress table, and adjudicating "
                  "trade-offs between the other analysts' verdicts",
    "desk": "the orchestrator's scripts: prices, indicators, correlations, realized returns, "
            "SEC filing verification -- ask here for any number a script can compute",
}

# A revision may change what the agent concluded. It may not rewrite the bookkeeping keys that
# merge rules append from or that the ledger itself owns.
REVISION_BLOCKLIST = {"comms", "journal_new", "findings_reaffirmed", "findings_revised",
                      "news_watermark", "usage", "agent", "run", "mode"}

PROTOCOL = """You are one analyst on a desk. You talk to the other analysts through the `comms`
block of your JSON tail; the orchestrator routes every message and nothing in prose is read.

1. ANSWER every message in `desk_inbox`. Each answer:
   {"id": "<message id>", "position": "held" | "revised" | "cannot_answer" | "noted",
    "answer": "<engage the specific point raised>", "evidence": [{"claim","source","date"}],
    "confidence": "high" | "medium" | "low",
    "revision": {<ONLY when position is revised: the changed part of YOUR OWN normal output, in
                 your usual schema -- e.g. {"thesis": {"changed": {"AMAT": {...}}}}>}}
   `held` must say why the point does not change your verdict. `cannot_answer` must say what
   data would settle it. `noted` is only for a tell. An unanswered message is shown to the user.
2. ASK when a verdict you are writing depends on something another analyst OWNS (see
   `desk_directory`) and your inputs do not already contain it:
   {"to": "<agent key>", "ticker": "<TICKER or null>", "question": "<one specific, answerable
    issue>", "why": "<which verdict of yours hinges on it, and how>", "blocking": true|false}
   `blocking` means you would write a different verdict depending on the answer. Do not ask for
   anything already in your slice, your prior_findings, or a sibling tail you were given. Ask
   `desk` for any number a script can compute -- never estimate it yourself.
3. TELL when you found something inside another analyst's ownership it may not have:
   {"to": "<agent key>", "ticker": "<TICKER or null>", "fact": "...", "source": "...",
    "weight": "high" (could change their verdict; they must acknowledge) | "normal"}
4. A blocking question does not stop you. Write your best current verdict, say in its note that
   it is provisional pending message <id>, and expect to be resumed with the answer.
5. A message of kind `debate` means your output and another analyst's conflict on the same name.
   The counter-party's position and evidence are quoted in it. Either revise, or hold with the
   specific reason their evidence does not apply to this name. "Both can be true" is acceptable
   only if you say how.
6. Reply to an answer with a follow-up by setting "reply_to": "<id>" on a new ask. Threads are
   capped; do not re-ask a question that has been answered -- engage with the answer instead."""


# ---------------------------------------------------------------------------
# io
# ---------------------------------------------------------------------------

def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read(path, default=None):
    try:
        with open(path) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def _write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(obj, fh, indent=2)
    os.replace(tmp, path)


def comms_dir(run_dir):
    return os.path.join(run_dir, COMMS_DIR)


def load_ledger(run_dir):
    doc = _read(os.path.join(comms_dir(run_dir), LEDGER), None)
    if not isinstance(doc, dict):
        doc = {"schema_version": SCHEMA_VERSION, "round": 0, "messages": [], "revisions": [],
               "settled": [], "harvested": {}, "rounds": [], "seq": 0}
    for k, v in (("messages", []), ("revisions", []), ("settled", []), ("harvested", {}),
                 ("rounds", []), ("seq", 0), ("round", 0)):
        doc.setdefault(k, v)
    return doc


def save_ledger(run_dir, doc):
    _write(os.path.join(comms_dir(run_dir), LEDGER), doc)


# ---------------------------------------------------------------------------
# roster: who exists, who has run, who is scheduled, who consumes whom
# ---------------------------------------------------------------------------

def _family(agent):
    return "cluster" if str(agent).startswith("cluster_") else str(agent)


def _canon(agent):
    a = str(agent or "").strip()
    return a[len("smith-"):] if a.startswith("smith-") else a


def roster(run_dir):
    """{ran, scheduled, known}. `ran` = has an out_<agent>.json; `scheduled` = named in this run's
    dispatch_plan.json but not yet run; `known` = every addressable key this run."""
    ran = set()
    try:
        for f in os.listdir(run_dir):
            # an answer-only dispatch writes only out_<agent>.r<N>.json -- it has still run,
            # and a second question to it must RESUME it, not dispatch a fresh copy
            m = re.match(r"^out_([a-z_]+)(?:\.r\d+)?\.json$", f)
            if m and m.group(1) != "desk":
                ran.add(m.group(1))
    except OSError:
        pass
    plan = _read(os.path.join(run_dir, "dispatch_plan.json"), {}) or {}
    planned = set()
    for wave in (plan.get("waves") or {}).values():
        planned.update(wave or [])
    ladder = _read(os.path.join(run_dir, "compute_ladder.json"), {}) or {}
    cluster_keys = {f"cluster_{row.get('slug')}" for row in (ladder.get("clusters") or {}).values()
                    if isinstance(row, dict) and row.get("slug")}
    known = set(DIRECTORY) - {"cluster"} | cluster_keys | ran | planned
    return {"ran": ran, "scheduled": planned - ran, "known": known}


def consumers(agent, run_dir=None):
    """Agents whose slices embed `agent`'s tail, from AGENT_SLICES itself -- one source of truth
    for "who read this", so a revision reaches exactly the agents that relied on the stale one.
    The strategist always consumes: it adjudicates everything."""
    try:
        from smith_memory import AGENT_SLICES
    except Exception:  # noqa: BLE001 -- router must still run in isolation (tests)
        AGENT_SLICES = {}
    fam = _family(agent)
    out = {"strategist"}
    for key, spec in AGENT_SLICES.items():
        if f"{fam}_tail" in (spec.get("refs") or []):
            out.add(key)
    out.discard(agent)
    if "cluster" in out:
        out.discard("cluster")
        if run_dir:
            out |= {a for a in roster(run_dir)["ran"] if a.startswith("cluster_")}
    return sorted(out)


# ---------------------------------------------------------------------------
# harvesting agent tails
# ---------------------------------------------------------------------------

def _tail_files(run_dir):
    """(agent, round, path) for every tail on disk: out_<agent>.json is round 0, and
    out_<agent>.r<N>.json is that agent's reply in desk round N. r0 snapshots are skipped --
    they are the pre-revision original, kept for audit, not a new utterance."""
    out = []
    try:
        names = sorted(os.listdir(run_dir))
    except OSError:
        return out
    for f in names:
        m = re.match(r"^out_([a-z_]+)(?:\.r(\d+))?\.json$", f)
        if not m:
            continue
        rnd = int(m.group(2)) if m.group(2) else 0
        if m.group(2) == "0":
            continue
        out.append((m.group(1), rnd, os.path.join(run_dir, f)))
    return out


def _digest(path):
    try:
        with open(path, "rb") as fh:
            return hashlib.sha1(fh.read()).hexdigest()[:16]
    except OSError:
        return None


def _norm(text):
    return re.sub(r"[^a-z0-9 ]", "", str(text or "").lower()).strip()


def _fingerprint(frm, to, ticker, text):
    return hashlib.sha1(f"{frm}|{to}|{ticker or ''}|{_norm(text)[:240]}".encode()).hexdigest()[:12]


def _extract_comms(tail):
    """Accept `comms` at the top level or nested one level under a wrapper key."""
    if not isinstance(tail, dict):
        return {}
    c = tail.get("comms")
    if isinstance(c, dict):
        return c
    for v in tail.values():
        if isinstance(v, dict) and isinstance(v.get("comms"), dict):
            return v["comms"]
    return {}


# ---------------------------------------------------------------------------
# revisions
# ---------------------------------------------------------------------------

_MATCH_KEYS = ("id", "ticker", "headline", "cluster", "scenario")


def _overlay(base, patch):
    """Deep-merge `patch` onto `base`. Dicts merge key by key; a list of dicts is merged element
    by element on the first identity key both sides carry (id/ticker/headline/...), new elements
    appended; any other value is replaced. This lets a revision say "AMAT's entry is now X"
    without restating the other 26 names."""
    if isinstance(base, dict) and isinstance(patch, dict):
        out = dict(base)
        for k, v in patch.items():
            out[k] = _overlay(base.get(k), v) if k in base else v
        return out
    if isinstance(base, list) and isinstance(patch, list) and all(isinstance(x, dict) for x in patch):
        key = next((k for k in _MATCH_KEYS
                    if any(isinstance(b, dict) and k in b for b in base)
                    and all(k in p for p in patch)), None)
        if key is None:
            return patch
        out = [dict(b) if isinstance(b, dict) else b for b in base]
        idx = {b.get(key): i for i, b in enumerate(out) if isinstance(b, dict)}
        for p in patch:
            if p.get(key) in idx:
                out[idx[p[key]]] = _overlay(out[idx[p[key]]], p)
            else:
                out.append(p)
        return out
    return patch


def _list_key(before, after):
    if not (isinstance(before, list) and isinstance(after, list)):
        return None
    return next((k for k in _MATCH_KEYS
                 if any(isinstance(b, dict) and k in b for b in before)
                 and any(isinstance(a, dict) and k in a for a in after)), None)


def _summarize_change(before, after, depth=0):
    """Short human-readable diff of what a revision changed, for the ledger and the briefing.
    Lists of identified entries (catalysts by headline, rows by ticker) are diffed PER ENTRY and
    set-valued fields like `affects` report what was added/removed -- "list replaced" told a
    colleague nothing about what it now had to reconsider."""
    lines = []
    key = _list_key(before, after)
    if key:
        old = {b.get(key): b for b in before if isinstance(b, dict)}
        new_keys = {a.get(key) for a in after if isinstance(a, dict)}
        for k in old:
            if k not in new_keys:
                lines.append(f"[{str(k)[:50]}] removed (retired)")
        for a in after:
            if not isinstance(a, dict):
                continue
            b = old.get(a.get(key))
            label = str(a.get(key))[:50]
            if b is None:
                lines.append(f"[{label}] added")
                continue
            for f, v in a.items():
                if b.get(f) == v:
                    continue
                if isinstance(v, list) and isinstance(b.get(f), list) and \
                        all(not isinstance(x, (dict, list)) for x in v + b[f]):
                    rm, ad = sorted(set(b[f]) - set(v)), sorted(set(v) - set(b[f]))
                    lines.append(f"[{label}].{f}: " + ", ".join(
                        x for x in (f"removed {rm}" if rm else "", f"added {ad}" if ad else "") if x))
                elif f not in ("revised_on_desk", "last_confirmed", "carried_forward"):
                    lines.append(f"[{label}].{f}: {json.dumps(b.get(f))[:50]} -> {json.dumps(v)[:50]}")
        return lines[:12]
    if isinstance(before, dict) and isinstance(after, dict) and depth < 4:
        for k in after:
            if before.get(k) != after.get(k):
                if isinstance(after[k], (dict, list)) and k in before and depth < 3:
                    sub = _summarize_change(before.get(k), after[k], depth + 1)
                    lines += [f"{k}.{s}" for s in sub[:6]] or [k]
                else:
                    bv = before.get(k)
                    lines.append(f"{k}: {json.dumps(bv)[:60] if bv is not None else '(new)'} -> "
                                 f"{json.dumps(after[k])[:60]}")
    elif before != after:
        lines.append("list/value replaced")
    return lines[:12]


def _headline_match(candidates, headline):
    """A carried catalyst by headline: exact first, then an 80-character prefix either way --
    agents restate a headline they were quoted, and a trailing clause must not orphan a fix."""
    h = str(headline or "")
    for c in candidates:
        if isinstance(c, dict) and c.get("headline") == h:
            return c
    for c in candidates:
        ch = str((c or {}).get("headline") or "")
        if ch and h and (ch[:80] == h[:80] or ch.startswith(h[:60]) or h.startswith(ch[:60])):
            return c
    return None


def _hydrate(run_dir, agent, patch, base):
    """Complete a PARTIAL revision of an item that lives in state, not in this run's tail.

    FOUND ON THE FIRST LIVE ROUND (2026-09-19). smith-catalyst correctly withdrew AMAT from the
    CXMT catalyst -- but that catalyst was CARRIED from 09-01 and sat in state.factor_catalysts,
    not in today's tail. Its revision carried only {headline, affects}. Overlaid naively it would
    have been appended as a stub with no date, horizon or source, and because catalyst identity is
    (headline, date) the merge would have kept BOTH the stub and the untouched original. The fix
    reads the full record from staged state and applies the change to it, so a revision always
    means "this entry, changed", never "a new fragment". Same for a thesis entry on a name the
    tail did not re-review: a partial entry must not overwrite the full one in state.
    """
    notes, sources = [], []
    fam = _family(agent)
    st = _state(run_dir)
    if fam == "catalyst" and isinstance(patch.get("catalysts"), list):
        tail_cats = [c for c in (base.get("catalysts") or []) if isinstance(c, dict)]
        fc = st.get("factor_catalysts")
        carried = fc.get("catalysts") if isinstance(fc, dict) else (fc or [])
        out = []
        for p in patch["catalysts"]:
            if not isinstance(p, dict):
                continue
            if _headline_match(tail_cats, p.get("headline")):
                hit = _headline_match(tail_cats, p.get("headline"))
                out.append(dict(p, headline=hit.get("headline")))
                continue
            src = _headline_match(carried, p.get("headline"))
            if src is None:
                notes.append(f"catalyst '{str(p.get('headline'))[:70]}' is in neither the tail nor "
                             f"state -- dropped rather than appended as a fragment")
                continue
            full = _overlay({k: v for k, v in src.items()
                             if k not in ("carried_forward", "last_confirmed")}, p)
            full["headline"] = src.get("headline")
            full["revised_on_desk"] = True
            out.append(full)
            sources.append(src)
            notes.append(f"hydrated carried catalyst '{str(src.get('headline'))[:70]}' ({src.get('date')})")
        if out:
            patch = dict(patch, catalysts=out)
        else:
            patch = {k: v for k, v in patch.items() if k != "catalysts"}
    if fam == "catalyst" and isinstance(patch.get("retired_catalysts"), list):
        # _merge_catalyst retires by (headline, date); an agent names a retirement by headline
        fc = st.get("factor_catalysts")
        carried = fc.get("catalysts") if isinstance(fc, dict) else (fc or [])
        tail_cats = [c for c in (base.get("catalysts") or []) if isinstance(c, dict)]
        fixed = []
        for r in patch["retired_catalysts"]:
            if not isinstance(r, dict):
                continue
            src = _headline_match(carried + tail_cats, r.get("headline"))
            if src is None:
                notes.append(f"retirement of unknown catalyst '{str(r.get('headline'))[:70]}' dropped")
                continue
            fixed.append({"headline": src.get("headline"), "date": src.get("date"),
                          "reason": r.get("reason") or "retired on the desk"})
            notes.append(f"retirement resolved to '{str(src.get('headline'))[:60]}' ({src.get('date')})")
        if fixed:
            patch = dict(patch, retired_catalysts=fixed)
        else:
            patch = {k: v for k, v in patch.items() if k != "retired_catalysts"}
    if fam == "thesis":
        changed = ((patch.get("thesis") or {}).get("changed") or {})
        tail_changed = ((base.get("thesis") or {}).get("changed") or {})
        full_map = st.get("thesis") or {}
        for t, e in list(changed.items()):
            if t not in tail_changed and isinstance(full_map.get(t), dict) and isinstance(e, dict):
                changed[t] = _overlay(dict(full_map[t]), e)
                notes.append(f"hydrated thesis entry {t} from state")
                sources.append({"_thesis": t, "entry": full_map[t]})
    return patch, notes, sources


def apply_revision(run_dir, agent, revision, msg_id, round_no):
    """Overlay a revision into out_<agent>.json, keeping the original as out_<agent>.r0.json.

    Returns a ledger record. The agent's canonical file always holds its CURRENT position, which
    is what makes every downstream reader -- crosscheck, re-rendered slices, merge-tails, the
    strategist -- see the revised verdict without being taught about revisions at all.
    """
    if not isinstance(revision, dict) or not revision:
        return {"applied": False, "reason": "empty or non-object revision"}
    dropped = sorted(k for k in revision if k in REVISION_BLOCKLIST)
    patch = {k: v for k, v in revision.items() if k not in REVISION_BLOCKLIST}
    if not patch:
        return {"applied": False, "reason": f"revision only touched blocked keys {dropped}"}
    path = os.path.join(run_dir, f"out_{agent}.json")
    base = _read(path, None)
    if not isinstance(base, dict):
        return {"applied": False, "reason": f"out_{agent}.json missing -- nothing to revise"}
    patch, hydration, sources = _hydrate(run_dir, agent, patch, base)
    if not patch:
        return {"applied": False, "reason": "; ".join(hydration) or "nothing left to apply"}
    snap = os.path.join(run_dir, f"out_{agent}.r0.json")
    if not os.path.exists(snap):
        _write(snap, base)
    after = _overlay(base, patch)
    # RETIREMENT WINS over an amendment of the same entry: _merge_catalyst only retires CARRIED
    # entries, so a catalyst revised and retired in one breath would otherwise survive as fresh.
    retired_heads = {r.get("headline") for r in (after.get("retired_catalysts") or [])
                     if isinstance(r, dict)}
    if retired_heads and isinstance(after.get("catalysts"), list):
        after["catalysts"] = [c for c in after["catalysts"]
                              if not (isinstance(c, dict) and c.get("headline") in retired_heads)]
    _write(path, after)
    # diff against the TRUE before: a hydrated entry came from state, not from the tail, and
    # diffed against the tail it would read as "added" instead of "AMAT removed"
    before_view = json.loads(json.dumps(base))
    for src in sources:
        if "_thesis" in src:
            before_view.setdefault("thesis", {}).setdefault("changed", {})[src["_thesis"]] = src["entry"]
        else:
            before_view.setdefault("catalysts", []).append(src)
    return {"applied": True, "agent": agent, "message": msg_id, "round": round_no,
            "keys": sorted(patch), "dropped_keys": dropped, "hydration": hydration,
            "changed": _summarize_change(before_view, after), "at": _now(),
            # full precision: `at` is second-resolution for humans, and a crosscheck file written
            # in the same second as the revision must not count as "re-run after it landed"
            "at_epoch": time.time()}


# ---------------------------------------------------------------------------
# debates from crosscheck
# ---------------------------------------------------------------------------

def _thesis_entry(run_dir, ticker):
    t = _read(os.path.join(run_dir, "out_thesis.json"), {}) or {}
    e = ((t.get("thesis") or {}).get("changed") or {}).get(ticker)
    return e if isinstance(e, dict) else None


def _state(run_dir):
    """Staged state if this run has one, else the committed state -- via smith_state.load_state,
    the same reader every later wave uses, so a debate quotes what the agents themselves see."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(run_dir)))
    try:
        from smith_state import load_state
        return load_state(base, run_dir) or {}
    except Exception:  # noqa: BLE001 -- isolated tests have no state module path
        return _read(os.path.join(base, "state.json"), {}) or {}


def _catalysts_on(run_dir, ticker):
    """Every catalyst naming `ticker`: this run's fresh ones AND the carried-forward record in
    state -- a live trigger usually rests on a carried catalyst, and quoting only the fresh
    ones handed the agent an empty counter-case."""
    c = _read(os.path.join(run_dir, "out_catalyst.json"), {}) or {}
    rows = [x for x in (c.get("catalysts") or []) if isinstance(x, dict)
            and ticker in (x.get("affects") or [])]
    fc = _state(run_dir).get("factor_catalysts")
    carried = fc.get("catalysts") if isinstance(fc, dict) else fc
    seen = {str(x.get("headline"))[:80] for x in rows}
    for x in carried or []:
        if isinstance(x, dict) and ticker in (x.get("affects") or []) \
                and str(x.get("headline"))[:80] not in seen:
            rows.append(x)
            seen.add(str(x.get("headline"))[:80])
    trig = _read(os.path.join(run_dir, "compute_triggers.json"), {}) or {}
    live = [x for x in (trig.get("catalyst_threat") or []) if isinstance(x, dict)
            and x.get("ticker") == ticker]
    return rows, live


def _brief_evidence(entry, side, n=3):
    rows = (entry or {}).get(side) or []
    return [{k: r.get(k) for k in ("claim", "source", "date") if r.get(k)}
            for r in rows[:n] if isinstance(r, dict)]


def debates_from_crosscheck(run_dir, include_low=False):
    """Turn each conflict crosscheck found into a pair of challenges, one to each side, each
    quoting the other side's position and evidence. Returns [(debate_key, [message specs])]."""
    cc = _read(os.path.join(run_dir, "crosscheck.json"), {}) or {}
    sev_ok = DEBATE_SEVERITIES + (("low",) if include_low else ())
    out = []
    for f in cc.get("findings") or []:
        if not isinstance(f, dict) or f.get("severity") not in sev_ok:
            continue
        kind, tk = f.get("kind"), f.get("ticker")
        if kind == "thesis_vs_catalyst_threat" and tk:
            entry = _thesis_entry(run_dir, tk) or {}
            cats, live = _catalysts_on(run_dir, tk)
            threat_reasons = sorted({str((r.get("reasons") or [r.get("reason")])[0])[:420]
                                     for r in live if (r.get("reasons") or r.get("reason"))})
            key = f"{kind}|{tk}"
            out.append((key, [
                {"to": "thesis", "from": "crosscheck", "ticker": tk, "kind": "debate",
                 "question": (f"You hold {tk} `{entry.get('status')}`, but a live catalyst_threat "
                              f"fires on it. The threat's stated basis: "
                              f"{'; '.join(threat_reasons) or 'see compute_triggers.json'}. "
                              f"Does it touch {tk}'s revenue, margins or thesis mechanism? Hold "
                              f"with the reason it does not apply, or revise."),
                 "why": "an unargued strengthening verdict under a live threat reaches the "
                        "strategist as an open contradiction",
                 "counterparty": {"agent": "catalyst", "catalysts": [
                     {k: c.get(k) for k in ("headline", "date", "horizon", "direction",
                                            "magnitude", "source", "affects") if c.get(k)}
                     for c in cats[:4]],
                     "live_trigger_reasons": threat_reasons[:3]},
                 "blocking": True},
                {"to": "catalyst", "from": "crosscheck", "ticker": tk, "kind": "debate",
                 "question": (f"Your factor-threat mapping lists {tk}. Thesis holds it "
                              f"`{entry.get('status')}` on the evidence quoted. Name the specific "
                              f"mechanism by which your threat reaches {tk} -- or withdraw {tk} "
                              f"from its `affects` list if the mapping was blanket rather than "
                              f"specific."),
                 "why": "a threat mapped onto names it does not touch fans one article into many "
                        "trim triggers",
                 "counterparty": {"agent": "thesis", "status": entry.get("status"),
                                  "evidence_for": _brief_evidence(entry, "evidence_for"),
                                  "evidence_against": _brief_evidence(entry, "evidence_against")},
                 "blocking": True},
            ]))
        elif kind == "evidence_gap" and tk:
            entry = _thesis_entry(run_dir, tk) or {}
            key = f"{kind}|{tk}"
            out.append((key, [
                {"to": "thesis", "from": "crosscheck", "ticker": tk, "kind": "debate",
                 "question": (f"You wrote {tk} `{entry.get('status')}` with an empty "
                              f"evidence_against while smith-quality flagged it this run: "
                              f"{f.get('detail')}. Add the counter-evidence and state whether "
                              f"it changes the verdict."),
                 "why": "G58: both sides must survive into the record",
                 "counterparty": {"agent": "quality"}, "blocking": True},
                {"to": "quality", "from": "crosscheck", "ticker": tk, "kind": "debate",
                 "question": (f"Thesis holds {tk} `{entry.get('status')}` with no counter-"
                              f"evidence. How material is your flag to the equity thesis -- "
                              f"magnitude and direction?"),
                 "why": "thesis needs the magnitude to weigh the flag",
                 "counterparty": {"agent": "thesis", "status": entry.get("status"),
                                  "evidence_for": _brief_evidence(entry, "evidence_for")},
                 "blocking": True},
            ]))
        elif kind == "catalyst_vs_cycle":
            head = (f.get("detail") or "")[:300]
            key = f"{kind}|{_norm(head)[:80]}"
            out.append((key, [
                {"to": "cycle", "from": "crosscheck", "ticker": None, "kind": "debate",
                 "question": (f"Catalyst reports a STRUCTURAL tailwind while you hold the cycle "
                              f"late/rolling: {head}. Which reading do you weight and why -- is "
                              f"it a level vs rate-of-change distinction?"),
                 "why": "the strategist sizes against one cycle read, not two",
                 "counterparty": {"agent": "catalyst", "affects": f.get("affects"),
                                  "source": f.get("source")}, "blocking": True},
                {"to": "catalyst", "from": "crosscheck", "ticker": None, "kind": "debate",
                 "question": (f"Cycle holds the AI-capex cycle late/rolling. Is your structural "
                              f"tailwind a statement about the level or the rate of change, and "
                              f"is it tier-1 corroborated? {head}"),
                 "why": "an uncorroborated structural claim once failed tier-1 check outright",
                 "counterparty": {"agent": "cycle"}, "blocking": True},
            ]))
        elif kind == "ladder_vs_thesis" and tk:
            cname = f.get("cluster")
            ladder = _read(os.path.join(run_dir, "compute_ladder.json"), {}) or {}
            slug = ((ladder.get("clusters") or {}).get(cname) or {}).get("slug")
            entry = _thesis_entry(run_dir, tk) or \
                ((_state(run_dir).get("thesis") or {}).get(tk) or {})
            lad = ((_state(run_dir).get("cluster_ladders") or {}).get(cname) or {})
            row = next((r for r in (lad.get("ranking") or [])
                        if isinstance(r, dict) and (r.get("t") or r.get("ticker")) == tk), {})
            ladder_case = {"agent": f"cluster_{slug}" if slug else "cluster", "cluster": cname,
                           "rank": row.get("rank"), "verdict": row.get("verdict"),
                           # the schema drifted: older ladders store `differentiator_reads` and a
                           # `case_against`; newer ones `reads`. Quote whichever this one has.
                           "reads": (row.get("reads") or row.get("differentiator_reads") or [])[:3],
                           "case_against": row.get("case_against"),
                           "ladder_as_of": lad.get("as_of"),
                           "confidence": lad.get("confidence"), "leader": lad.get("leader"),
                           "laggard": lad.get("laggard")}
            key = f"{kind}|{tk}|{cname}"
            msgs = [{"to": "thesis", "from": "crosscheck", "ticker": tk, "kind": "debate",
                     "question": (f"The {cname} ladder ranks {tk} opposite to your "
                                  f"`{entry.get('status')}` verdict: {f.get('detail')} "
                                  f"Which comparative axis does the ladder get wrong, or do you "
                                  f"revise?"),
                     "why": "a ladder with authority can size a rotation on this ranking",
                     "counterparty": ladder_case,
                     "blocking": f.get("severity") == "high"}]
            if slug:
                msgs.append({"to": f"cluster_{slug}", "from": "crosscheck", "ticker": tk,
                             "kind": "debate",
                             "question": (f"Thesis holds {tk} `{entry.get('status')}`. Which axis "
                                          f"places it where you ranked it, and does the thesis "
                                          f"evidence quoted change that?"),
                             "why": "ranking and per-name verdict disagree on the same company",
                             "counterparty": {"agent": "thesis", "status": entry.get("status"),
                                              "evidence_for": _brief_evidence(entry, "evidence_for"),
                                              "evidence_against": _brief_evidence(entry, "evidence_against")},
                             "blocking": f.get("severity") == "high"})
            out.append((key, msgs))
        elif kind == "handoff_to_nowhere":
            frm, to = _canon(f.get("from")), _canon(f.get("to"))
            key = f"{kind}|{frm}|{to}"
            out.append((key, [{"to": to, "from": frm, "ticker": None, "kind": "ask",
                               "question": (f"{frm} deferred a question to you in prose that was "
                                            f"never delivered. Read out_{frm}.json for the "
                                            f"handoff and answer it: {f.get('detail')}"),
                               "why": f"{frm}'s verdict was formed without your answer",
                               "blocking": True}]))
        elif kind == "thesis_vs_price" and tk and include_low:
            key = f"{kind}|{tk}"
            out.append((key, [{"to": "thesis", "from": "crosscheck", "ticker": tk, "kind": "debate",
                               "question": f.get("detail"), "why": "low-severity tension",
                               "blocking": False}]))
    return out


# ---------------------------------------------------------------------------
# the router
# ---------------------------------------------------------------------------

_MSG_ID = re.compile(r"^M\d+\.\d+$")


def _normalize_answer(a):
    """ONE READER for an agent's answer, tolerant of the shapes agents actually emit.

    FOUND ON THE FIRST LIVE ROUND (2026-09-19): smith-strategist answered with
    {"to": "M2.7", "status": "noted, no change", "detail": "..."} instead of
    {"id", "position", "answer"}; smith-catalyst put `retired_catalysts_suggested` beside its
    answer instead of inside `revision`. Rejecting those would have recorded two substantive
    replies as SILENCE and shown the user an analyst who never answered. Known variants are
    mapped here, once, and every repair is recorded on the answer so schema drift stays visible
    instead of being papered over. An answer whose message id cannot be recovered is still
    rejected -- guessing which question a reply belongs to would be worse than a gap.
    """
    if not isinstance(a, dict):
        return None, ["not an object"]
    fixed, out = [], dict(a)
    if not out.get("id"):
        for k in ("message_id", "message", "ref", "reply_to", "to", "answering"):
            v = a.get(k)
            if isinstance(v, str) and _MSG_ID.match(v.strip()):
                out["id"] = v.strip()
                fixed.append(f"id<-{k}")
                break
    if out.get("position") not in POSITIONS:
        raw = str(a.get("position") or a.get("status") or a.get("verdict") or "").lower()
        guess = ("revised" if "revis" in raw or "withdr" in raw else
                 "cannot_answer" if "cannot" in raw or "unable" in raw else
                 "noted" if "noted" in raw or "acknowledg" in raw else
                 "held" if raw else None)
        if guess:
            fixed.append(f"position<-'{raw[:30]}'")
        out["position"] = guess or "held"
    if not out.get("answer"):
        for k in ("detail", "text", "reason", "response", "reply", "rationale"):
            if a.get(k):
                out["answer"] = a[k]
                fixed.append(f"answer<-{k}")
                break
    if not out.get("revision") and isinstance(a.get("revisions"), dict):
        out["revision"] = a["revisions"]
        fixed.append("revision<-revisions")
    retire = a.get("retired_catalysts") or a.get("retired_catalysts_suggested")
    if isinstance(retire, list) and retire:
        rev = dict(out.get("revision") or {})
        rev["retired_catalysts"] = (rev.get("retired_catalysts") or []) + retire
        out["revision"] = rev
        if out["position"] == "held":
            out["position"] = "revised"
        fixed.append("revision.retired_catalysts<-answer-level retirement")
    return out, fixed


def _infer_ticker(run_dir, text):
    """The single held ticker named in a message, when the sender omitted the field. Exactly one
    or nothing: a question naming two holdings is about both, and filing it under either would
    hide it from the other's thread."""
    h = _read(os.path.join(run_dir, "holdings.json"), {}) or {}
    rows = h.get("holdings_inr") or []
    held = {r.get("ticker") for r in (rows if isinstance(rows, list) else []) if r.get("ticker")}
    found = {t for t in held if re.search(rf"(?<![A-Za-z]){re.escape(t)}(?![A-Za-z])", str(text or ""))}
    return found.pop() if len(found) == 1 else None


def _new_msg(doc, spec, round_no, source):
    doc["seq"] += 1
    return {"id": f"M{round_no}.{doc['seq']}", "round": round_no, "created": _now(),
            "from": spec.get("from"), "to": spec.get("to"), "ticker": spec.get("ticker"),
            "kind": spec.get("kind") or "ask", "question": spec.get("question") or spec.get("fact"),
            "why": spec.get("why"), "blocking": bool(spec.get("blocking")),
            "weight": spec.get("weight"), "source": spec.get("source"),
            "counterparty": spec.get("counterparty"), "reply_to": spec.get("reply_to"),
            "debate_key": spec.get("debate_key"), "depth": spec.get("depth", 1),
            "fingerprint": spec.get("fingerprint"), "origin_file": source,
            "status": "open", "deliveries": 0, "delivered_round": None, "answer": None}


def _validate(spec, known, sender):
    to = _canon(spec.get("to"))
    if not to:
        return "no recipient"
    if to == sender:
        return "an agent cannot address itself"
    if to not in known and to != "desk" and not to.startswith("cluster_"):
        return f"unknown recipient '{to}' -- use a key from desk_directory"
    if not (spec.get("question") or spec.get("fact")):
        return "empty question/fact"
    return None


def route(run_dir, include_low=False, max_rounds=MAX_ROUNDS, today=None):
    """One desk round. Idempotent over unchanged inputs: re-running without new tails delivers
    nothing new and advances nothing. Returns the round record (also written to disk)."""
    doc = load_ledger(run_dir)
    rnd = doc["round"] + 1
    rs = roster(run_dir)
    known = rs["known"]
    by_id = {m["id"]: m for m in doc["messages"]}
    fps = {m.get("fingerprint") for m in doc["messages"] if m.get("fingerprint")}
    settled = set(doc["settled"])
    rejected, revisions, remerge, answered_now, schema_repairs = [], [], set(), [], []
    # One revision notice per (reviser, consumer) per round, however many revisions it made:
    # two notices about the same agent's output in one round wake the consumer twice for one job.
    pending_notices = {}
    asks_by_sender = {}

    # ---- 1. harvest every new or changed tail -------------------------------------------
    for agent, trnd, path in _tail_files(run_dir):
        dg = _digest(path)
        hk = os.path.basename(path)
        if doc["harvested"].get(hk) == dg:
            continue
        tail = _read(path, {}) or {}
        comms = _extract_comms(tail)

        for raw_a in comms.get("answers") or []:
            a, repairs = _normalize_answer(raw_a)
            if a is None:
                rejected.append({"from": agent, "why": "answer is not an object"})
                continue
            if repairs:
                schema_repairs.append({"from": agent, "id": a.get("id"), "repairs": repairs})
            m = by_id.get(a.get("id"))
            if m is None:
                rejected.append({"from": agent, "why": f"answer to unknown id {a.get('id')}"})
                continue
            if _canon(m.get("to")) != agent:
                rejected.append({"from": agent, "why": f"{a.get('id')} is addressed to {m.get('to')}"})
                continue
            if m["status"] == "answered":
                continue
            pos = a.get("position") if a.get("position") in POSITIONS else "held"
            m["answer"] = {"position": pos, "answer": a.get("answer"),
                           "evidence": a.get("evidence") or [], "confidence": a.get("confidence"),
                           "file": hk, "round": trnd or rnd,
                           "schema_repaired": repairs or None}
            m["status"] = "answered"
            answered_now.append(m["id"])
            if pos == "revised" and agent != "desk":
                rec = apply_revision(run_dir, agent, a.get("revision"), m["id"], rnd)
                revisions.append(rec)
                if rec.get("applied"):
                    remerge.add(agent)
                    m["answer"]["revision_applied"] = rec["changed"]
                    for c in consumers(agent, run_dir):
                        if c in rs["ran"] or c in rs["scheduled"] or c == "strategist":
                            pending_notices.setdefault((agent, c), []).append(
                                {"msg": m["id"], "ticker": m.get("ticker"),
                                 "changed": rec["changed"], "why": str(a.get("answer") or "")})
                else:
                    m["answer"]["revision_rejected"] = rec.get("reason")
            # CLOSE THE LOOP: the asker hears the answer. A blocking ask means the asker wrote a
            # provisional verdict, so it is woken to integrate the answer (and may revise); a
            # non-blocking one is recorded and surfaces in its desk_replies if it is woken anyway.
            asker = _canon(m.get("from"))
            if m["kind"] in ("ask", "reply") and asker in rs["known"] and asker != agent:
                spec = {"to": asker, "from": agent, "ticker": m.get("ticker"), "kind": "reply",
                        "reply_to": m["id"],
                        "question": (f"Answer to your {m['id']} ({str(m['question'])[:160]}): "
                                     f"[{pos}] {str(a.get('answer') or '')[:700]}"),
                        "why": ("your verdict was provisional on this answer -- confirm it (held) "
                                "or revise" if m.get("blocking") else "for your record"),
                        "weight": "high" if m.get("blocking") else "normal",
                        "blocking": False, "depth": m.get("depth", 1) + 1,
                        "fingerprint": _fingerprint(agent, asker, m.get("ticker"), f"reply{m['id']}")}
                if spec["depth"] <= MAX_THREAD_DEPTH + 1 and spec["fingerprint"] not in fps:
                    nm = _new_msg(doc, spec, rnd, hk)
                    doc["messages"].append(nm)
                    by_id[nm["id"]] = nm
                    fps.add(spec["fingerprint"])
            if m.get("debate_key"):
                sibs = [x for x in doc["messages"] if x.get("debate_key") == m["debate_key"]]
                if all(x["status"] in ("answered", "unanswered", "expired", "recorded") for x in sibs):
                    settled.add(m["debate_key"])

        for kind, rows in (("ask", comms.get("asks") or []), ("tell", comms.get("tells") or [])):
            for s in rows:
                if not isinstance(s, dict):
                    continue
                s = dict(s)
                if not s.get("ticker"):
                    inferred = _infer_ticker(run_dir, s.get("question") or s.get("fact")
                                             or s.get("ask") or s.get("text"))
                    if inferred:
                        s["ticker"] = inferred
                        schema_repairs.append({"from": agent, "kind": kind,
                                               "repairs": [f"ticker<-inferred {inferred}"]})
                if kind == "ask" and not s.get("question"):
                    s["question"] = s.get("ask") or s.get("text") or s.get("query")
                if kind == "tell" and not s.get("fact"):
                    s["fact"] = s.get("finding") or s.get("text") or s.get("note")
                err = _validate(s, known, agent)
                if err:
                    rejected.append({"from": agent, "kind": kind, "why": err,
                                     "text": str(s.get("question") or s.get("fact"))[:160]})
                    continue
                to = _canon(s["to"])
                text = s.get("question") or s.get("fact")
                fp = _fingerprint(agent, to, s.get("ticker"), text)
                if fp in fps:
                    continue
                parent = by_id.get(s.get("reply_to")) if s.get("reply_to") else None
                depth = (parent.get("depth", 1) + 1) if parent else 1
                if depth > MAX_THREAD_DEPTH:
                    rejected.append({"from": agent, "why": f"thread depth {depth} > {MAX_THREAD_DEPTH}",
                                     "text": str(text)[:160]})
                    continue
                if kind == "ask":
                    asks_by_sender[agent] = asks_by_sender.get(agent, 0) + 1
                    if asks_by_sender[agent] > MAX_ASKS_PER_AGENT_PER_ROUND:
                        rejected.append({"from": agent, "why": f"more than "
                                         f"{MAX_ASKS_PER_AGENT_PER_ROUND} asks this round",
                                         "text": str(text)[:160]})
                        continue
                spec = dict(s, to=to, **{"from": agent, "kind": kind, "depth": depth,
                                         "fingerprint": fp,
                                         "blocking": bool(s.get("blocking")) if kind == "ask" else False})
                nm = _new_msg(doc, spec, rnd, hk)
                doc["messages"].append(nm)
                by_id[nm["id"]] = nm
                fps.add(fp)
        doc["harvested"][hk] = _digest(path)

    for (reviser, c), items in pending_notices.items():
        tickers = sorted({i["ticker"] for i in items if i["ticker"]})
        body = " | ".join(f"after {i['msg']}{' (' + i['ticker'] + ')' if i['ticker'] else ''}: "
                          f"{'; '.join(i['changed'][:4])}. Reason: {i['why'][:300]}" for i in items)
        spec = {"to": c, "from": reviser, "ticker": tickers[0] if len(tickers) == 1 else None,
                "kind": "revision", "weight": "high", "blocking": False,
                "question": (f"{reviser} REVISED its output ({len(items)} change set(s)"
                             f"{', on ' + ', '.join(tickers) if tickers else ''}). {body}"),
                "why": "you consumed the pre-revision version -- acknowledge (noted) or revise",
                "fingerprint": _fingerprint(reviser, c, None,
                                            "rev" + ",".join(sorted(i["msg"] for i in items)))}
        if spec["fingerprint"] not in fps:
            nm = _new_msg(doc, spec, rnd, "revisions")
            doc["messages"].append(nm)
            by_id[nm["id"]] = nm
            fps.add(spec["fingerprint"])

    # ---- 2. crosscheck conflicts become debates (never reopened once settled) -----------
    opened_debates = []
    live_keys = {m.get("debate_key") for m in doc["messages"] if m.get("debate_key")}
    cc_path = os.path.join(run_dir, "crosscheck.json")
    cc_mtime = os.path.getmtime(cc_path) if os.path.exists(cc_path) else 0
    for key, specs in debates_from_crosscheck(run_dir, include_low=include_low):
        if key in settled:
            # INCOMPLETE REVISION (2026-09-19, found on the first live round): a side revised to
            # remove the conflict, crosscheck was re-run after the revision landed, and the
            # conflict is STILL there -- e.g. a ticker withdrawn from one catalyst while near-
            # duplicate catalysts in state still map it. Settled means argued, not fixed; ask the
            # reviser once to finish the job, listing exactly what still produces the conflict.
            fu = key + "|followup"
            revisers = [m for m in doc["messages"] if m.get("debate_key") == key
                        and (m.get("answer") or {}).get("position") == "revised"]
            rev_times = [r.get("at_epoch") for r in doc["revisions"] + revisions
                         if r.get("applied") and r.get("at_epoch")
                         and r.get("message") in {m["id"] for m in revisers}]
            # strictly AFTER: crosscheck must have been re-run once the revision had landed
            landed_before_cc = bool(rev_times) and cc_mtime > max(rev_times)
            if revisers and landed_before_cc and fu not in settled and fu not in live_keys:
                tk = specs[0].get("ticker")
                cats, live = _catalysts_on(run_dir, tk) if tk else ([], [])
                for r in revisers:
                    spec = {"to": r["to"], "from": "crosscheck", "ticker": tk, "kind": "debate",
                            "debate_key": fu, "blocking": True,
                            "question": (f"Your revision on {tk} (message {r['id']}) did not remove "
                                         f"the conflict: after it landed and triggers/crosscheck were "
                                         f"re-run, it still fires. Still mapping {tk}: "
                                         + "; ".join(f"'{str(c.get('headline'))[:90]}' ({c.get('date')})"
                                                     for c in cats[:5])
                                         + ". Apply your reasoning consistently to each, or say why "
                                           "one of them genuinely does reach this name."),
                            "why": "a withdrawal applied to one of several near-duplicate entries "
                                   "leaves the live trigger firing",
                            "counterparty": {"remaining": [{k: c.get(k) for k in ("headline", "date", "affects")}
                                                           for c in cats[:5]]},
                            "fingerprint": _fingerprint("crosscheck", r["to"], tk, fu)}
                    if spec["fingerprint"] not in fps:
                        nm = _new_msg(doc, spec, rnd, "crosscheck.json")
                        doc["messages"].append(nm)
                        by_id[nm["id"]] = nm
                        fps.add(spec["fingerprint"])
                opened_debates.append(fu)
            continue
        if key in live_keys:
            continue
        for s in specs:
            s["debate_key"] = key
            s["fingerprint"] = _fingerprint("crosscheck", s["to"], s.get("ticker"), key)
            if s["fingerprint"] in fps:
                continue
            nm = _new_msg(doc, s, rnd, "crosscheck.json")
            doc["messages"].append(nm)
            by_id[nm["id"]] = nm
            fps.add(s["fingerprint"])
        opened_debates.append(key)

    # ---- 3. unanswered bookkeeping -------------------------------------------------------
    reminders = []
    for m in doc["messages"]:
        if m["status"] != "delivered":
            continue
        to = _canon(m["to"])
        replied = (os.path.exists(os.path.join(run_dir, f"out_{to}.r{m['delivered_round']}.json"))
                   if m.get("delivery_mode") != "inbox" else to in rs["ran"])
        if not replied:
            continue
        if m["deliveries"] <= REDELIVER_LIMIT:
            m["status"] = "open"
            reminders.append(m["id"])
        else:
            m["status"] = "unanswered"
            if m.get("debate_key"):
                sibs = [x for x in doc["messages"] if x.get("debate_key") == m["debate_key"]]
                if all(x["status"] in ("answered", "unanswered", "expired", "recorded") for x in sibs):
                    settled.add(m["debate_key"])

    # ---- 4. deliveries -------------------------------------------------------------------
    open_msgs = [m for m in doc["messages"] if m["status"] in ("open", "queued")]
    if len(open_msgs) > MAX_OPEN:
        for m in sorted(open_msgs, key=lambda x: (x.get("blocking"), x.get("weight") == "high"))[:len(open_msgs) - MAX_OPEN]:
            m["status"] = "expired"
            m["expired_reason"] = f"desk exceeded {MAX_OPEN} open messages; lowest priority dropped"
        open_msgs = [m for m in open_msgs if m["status"] in ("open", "queued")]

    deliveries, desk_requests, new_agents = {}, [], []
    cap_hit = rnd > max_rounds
    for m in open_msgs:
        to = _canon(m["to"])
        # normal-weight tells to an agent that has already finished are FYI: recorded, and
        # surfaced if that agent is resumed anyway, but they never wake it on their own.
        fyi = m["kind"] in ("tell", "reply") and m.get("weight") != "high"
        if to == "desk":
            desk_requests.append(m)
            continue
        if to in rs["scheduled"] and to not in rs["ran"]:
            mode = "inbox"
        elif to in rs["ran"]:
            mode = "resume"
        else:
            mode = "dispatch"
            if to not in new_agents:
                new_agents.append(to)
        if cap_hit and mode != "inbox":
            m["status"] = "expired"
            m["expired_reason"] = f"round cap {max_rounds} reached before delivery"
            continue
        deliveries.setdefault(to, {"mode": mode, "messages": []})
        if mode == "resume" and fyi:
            deliveries[to].setdefault("fyi", []).append(m["id"])
            continue
        deliveries[to]["messages"].append(m["id"])
        m["status"] = "queued" if mode == "inbox" else "delivered"
        m["delivery_mode"] = mode
        if mode != "inbox":
            m["deliveries"] += 1
            m["delivered_round"] = rnd
    # An agent woken only by FYI is not woken: those messages are RECORDED (terminal, shown in
    # the digest and in its desk_replies if it is ever resumed). If it is being woken anyway,
    # the FYI rides along and needs a `noted`.
    for a, d in list(deliveries.items()):
        fyi_ids = d.pop("fyi", [])
        if d["messages"]:
            for mid in fyi_ids:
                fm = by_id[mid]
                fm.update(status="delivered", delivery_mode=d["mode"], delivered_round=rnd,
                          deliveries=fm["deliveries"] + 1)
                d["messages"].append(mid)
        else:
            for mid in fyi_ids:
                by_id[mid]["status"] = "recorded"
    deliveries = {a: d for a, d in deliveries.items() if d["messages"]}

    # ---- 5. inbox files ------------------------------------------------------------------
    for agent in {_canon(m["to"]) for m in doc["messages"]}:
        if agent == "desk":
            continue
        write_inbox(run_dir, agent, doc)

    action_needed = any(d["mode"] in ("resume", "dispatch") for d in deliveries.values())
    # Converged means nothing is owed. A message DELIVERED but not yet answered is owed; a
    # message QUEUED for an agent whose scheduled layer has not run yet is not -- it rides in
    # that agent's slice and is harvested from its normal tail, so it must not stall the loop.
    awaiting = [m["id"] for m in doc["messages"] if m["status"] in ("open", "delivered")]
    converged = (not action_needed and not desk_requests and not remerge and not awaiting)
    doc["settled"] = sorted(settled)
    doc["round"] = rnd
    doc["revisions"] += [r for r in revisions if r.get("applied")]
    record = {
        "round": rnd, "at": _now(), "converged": converged,
        "stop_reason": ("round cap reached -- remaining messages expired and are reported"
                        if cap_hit else "no open messages" if converged else None),
        "deliveries": {a: {"mode": d["mode"], "messages": d["messages"],
                           "inbox": os.path.join(comms_dir(run_dir), f"inbox_{a}.json"),
                           "reply_file": (os.path.join(run_dir, f"out_{a}.r{rnd}.json")
                                          if d["mode"] != "inbox" else os.path.join(run_dir, f"out_{a}.json"))}
                       for a, d in deliveries.items()},
        "new_agents": new_agents,
        "desk_requests": [{"id": m["id"], "from": m["from"], "ticker": m.get("ticker"),
                           "question": m["question"]} for m in desk_requests],
        "answered_this_round": answered_now,
        "awaiting_answers": awaiting,
        "queued_for_scheduled_agents": sorted({_canon(m["to"]) for m in doc["messages"]
                                                if m["status"] == "queued"}),
        "revisions": revisions,
        "remerge": sorted(remerge),
        "rerun_crosscheck": bool(remerge),
        "debates_opened": opened_debates,
        "reminders": reminders,
        "rejected": rejected,
        "schema_repairs": schema_repairs,
        "counts": _counts(doc),
    }
    doc["rounds"].append({k: record[k] for k in ("round", "at", "converged", "counts", "remerge",
                                                 "debates_opened", "new_agents")})
    save_ledger(run_dir, doc)
    _write(os.path.join(comms_dir(run_dir), f"round_{rnd}.json"), record)
    write_digest(run_dir, doc)
    return record


def _counts(doc):
    c = {}
    for m in doc["messages"]:
        c[m["status"]] = c.get(m["status"], 0) + 1
    c["total"] = len(doc["messages"])
    c["revisions"] = len(doc["revisions"])
    return c


def _public(m):
    return {k: m.get(k) for k in ("id", "from", "kind", "ticker", "question", "why", "blocking",
                                  "weight", "source", "counterparty", "reply_to", "depth")
            if m.get(k) not in (None, "", [], {})}


def inbox_messages(doc, agent):
    """Open/queued/delivered messages addressed to `agent`, plus answers to its own questions."""
    agent = _canon(agent)
    answered_by_me = [m for m in doc["messages"]
                      if _canon(m["to"]) == agent and m["status"] == "answered"]
    mine = []
    for m in doc["messages"]:
        if _canon(m["to"]) != agent or m["status"] not in ("open", "queued", "delivered"):
            continue
        row = _public(m)
        # WHAT YOU ALREADY SAID ON THIS NAME (2026-09-19): two colleagues asked thesis nearly the
        # same SKHY question two rounds apart. Showing the recipient its own earlier answers on
        # the same ticker lets it answer consistently -- or say why it now answers differently --
        # instead of re-deriving from scratch and drifting.
        if m.get("ticker"):
            rel = [{"id": x["id"], "asked_by": x.get("from"), "question": str(x["question"])[:200],
                    "your_position": (x.get("answer") or {}).get("position"),
                    "your_answer": str((x.get("answer") or {}).get("answer") or "")[:400]}
                   for x in answered_by_me if x.get("ticker") == m["ticker"] and x["id"] != m["id"]]
            if rel:
                row["your_prior_answers_on_this_name"] = rel[-3:]
        mine.append(row)
    replies = [{"your_message": m["id"], "to": m["to"], "question": m["question"],
                **{k: (m.get("answer") or {}).get(k) for k in ("position", "answer", "evidence",
                                                               "confidence", "revision_applied")}}
               for m in doc["messages"]
               if m.get("from") == agent and m["status"] == "answered"]
    return mine, replies


def write_inbox(run_dir, agent, doc=None):
    doc = doc or load_ledger(run_dir)
    mine, replies = inbox_messages(doc, agent)
    _write(os.path.join(comms_dir(run_dir), f"inbox_{agent}.json"),
           {"agent": agent, "round": doc["round"], "messages": mine,
            "answers_to_your_questions": replies})


def slice_block(run_dir, agent):
    """What cmd_slices embeds: protocol, directory, this agent's inbox and replies, and a short
    list of what the rest of the desk has already settled on this agent's names."""
    doc = load_ledger(run_dir)
    mine, replies = inbox_messages(doc, agent)
    rs = roster(run_dir)
    directory = {k: v for k, v in DIRECTORY.items()}
    directory["_on_desk_this_run"] = sorted((rs["ran"] | rs["scheduled"]) - {agent})
    return {"desk_protocol": PROTOCOL, "desk_directory": directory,
            "desk_inbox": mine, "desk_replies": replies,
            "desk_round": doc["round"]}


# ---------------------------------------------------------------------------
# digest: what the strategist, the briefing and findings.json read
# ---------------------------------------------------------------------------

def digest(doc):
    threads = []
    debates = {}
    for m in doc["messages"]:
        if m.get("debate_key"):
            # a follow-up is the SAME argument's second exchange, not a new debate
            debates.setdefault(m["debate_key"].replace("|followup", ""), []).append(m)
    for key, ms in debates.items():
        sides = [{"agent": m["to"], "status": m["status"],
                  "exchange": "follow-up" if str(m.get("debate_key")).endswith("|followup") else "opening",
                  "position": (m.get("answer") or {}).get("position"),
                  "answer": str((m.get("answer") or {}).get("answer") or "")[:500],
                  "revision_applied": (m.get("answer") or {}).get("revision_applied")}
                 for m in ms]
        positions = [s["position"] for s in sides]
        outcome = ("revised" if "revised" in positions else
                   "unresolved" if any(s["status"] in ("unanswered", "expired", "open",
                                                        "delivered", "queued") for s in sides)
                   else "held")
        threads.append({"debate": key, "ticker": ms[0].get("ticker"), "outcome": outcome,
                        "sides": sides})
    asks = [{"id": m["id"], "from": m["from"], "to": m["to"], "ticker": m.get("ticker"),
             "question": str(m["question"])[:300], "status": m["status"],
             "position": (m.get("answer") or {}).get("position"),
             "answer": str((m.get("answer") or {}).get("answer") or "")[:400]}
            for m in doc["messages"] if m["kind"] == "ask"]
    tells = [{"id": m["id"], "from": m["from"], "to": m["to"], "ticker": m.get("ticker"),
              "fact": str(m["question"])[:300], "weight": m.get("weight"), "status": m["status"]}
             for m in doc["messages"] if m["kind"] == "tell"]
    unresolved = [{"id": m["id"], "to": m["to"], "ticker": m.get("ticker"), "kind": m["kind"],
                   "status": m["status"], "question": str(m["question"])[:300],
                   "why": m.get("expired_reason")}
                  for m in doc["messages"]
                  if m["status"] in ("unanswered", "expired") and m["kind"] != "revision"]
    return {"round": doc["round"], "counts": _counts(doc), "debates": threads,
            "asks": asks, "tells": tells,
            "revisions": [{"agent": r["agent"], "message": r["message"], "changed": r["changed"]}
                          for r in doc["revisions"]],
            "unresolved": unresolved,
            "rule": ("Adjudicate on the post-debate record. A `revised` outcome means the owning "
                     "analyst changed its output and every consumer was told. A `held` outcome "
                     "means the challenge was answered with a reason; weigh that reason, do not "
                     "re-open it. `unresolved` items are live disagreements -- do not size a "
                     "proposal on one without naming it.")}


def write_digest(run_dir, doc=None):
    doc = doc or load_ledger(run_dir)
    d = digest(doc)
    _write(os.path.join(comms_dir(run_dir), DIGEST), d)
    return d


def findings_rows(run_dir):
    """Settled debates and answered blocking asks, for findings.json -- so the next run starts
    from what the desk already argued out instead of re-arguing it."""
    doc = _read(os.path.join(comms_dir(run_dir), LEDGER), None)
    if not isinstance(doc, dict):
        return []
    rows = []
    for t in digest(doc)["debates"]:
        if t["outcome"] == "unresolved":
            continue
        claim = f"Desk debate {t['debate'].split('|')[0]} on {t['ticker'] or 'book'}: {t['outcome']}. " + \
                " | ".join(f"{s['agent']} {s['position']}: {s['answer'][:180]}" for s in t["sides"])
        rows.append({"key": hashlib.sha1(t["debate"].encode()).hexdigest()[:10],
                     "subject": t["ticker"] or "book", "claim": claim, "ttl_days": 7,
                     "agents": sorted({s["agent"] for s in t["sides"]})})
    seen = set()
    for m in doc["messages"]:
        a = m.get("answer") or {}
        # A CHANGED POSITION IS A CONCLUSION, whatever kind of message prompted it (2026-09-19):
        # the strategist's forward sizing rule for SKHY arrived as a `revised` answer to a
        # non-blocking reply, carried no output revision, and would otherwise not have survived
        # to the next run -- which is exactly when it applies.
        if m["status"] == "answered" and a.get("position") == "revised" and m["kind"] != "debate":
            rows.append({"key": hashlib.sha1(("rev" + m["id"]).encode()).hexdigest()[:10],
                         "subject": m.get("ticker") or "book",
                         "claim": f"{m['to']} changed its position ({m['id']}, on "
                                  f"{str(m['question'])[:120]}): {str(a.get('answer') or '')[:360]}",
                         "ttl_days": 7, "agents": [m["to"], str(m.get("from"))]})
            seen.add(m["id"])
    for m in doc["messages"]:
        if m["id"] in seen:
            continue
        if m["kind"] == "ask" and m["status"] == "answered" and m.get("blocking"):
            a = m.get("answer") or {}
            rows.append({"key": hashlib.sha1(m["id"].encode() + str(m["question"]).encode()).hexdigest()[:10],
                         "subject": m.get("ticker") or "book",
                         "claim": f"{m['from']} asked {m['to']}: {str(m['question'])[:160]} -> "
                                  f"{a.get('position')}: {str(a.get('answer') or '')[:220]}",
                         "ttl_days": 7, "agents": [m["from"], m["to"]]})
    return rows


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def cmd_comms_route(args):
    from smith_core import emit
    rec = route(args.run_dir, include_low=args.include_low, max_rounds=args.max_rounds,
                today=args.today)
    rec["next"] = _next_steps(rec, args)
    emit(rec)


def _next_steps(rec, args):
    steps = []
    if rec["remerge"]:
        steps.append(f"python3 scripts/smith_math.py merge-tails --base-dir . --run-dir {args.run_dir} "
                     f"--today <date> --agents {','.join(rec['remerge'])} --revision")
        if set(rec["remerge"]) & {"catalyst", "thesis", "signals"}:
            # triggers are computed FROM thesis statuses and catalyst mappings; without this the
            # withdrawn threat keeps firing and crosscheck re-reports a conflict already fixed
            steps.append(f"python3 scripts/smith_math.py pipeline --base-dir . --run-dir {args.run_dir} "
                         f"--today <date> --lots lots.json --stages triggers")
        steps.append(f"python3 scripts/smith_math.py crosscheck --base-dir . --run-dir {args.run_dir} "
                     f"--today <date>")
    if rec["new_agents"]:
        steps.append(f"python3 scripts/smith_math.py slices --base-dir . --run-dir {args.run_dir} "
                     f"--mode <mode> --today <date> --agents {','.join(rec['new_agents'])}  "
                     f"(new layer: answer-only dispatch)")
    for a, d in rec["deliveries"].items():
        if d["mode"] == "resume":
            steps.append(f"resume {a} (SendMessage if its agent id is live, else fresh dispatch "
                         f"with its slice): read {d['inbox']}, answer every message, write the "
                         f"reply tail to {d['reply_file']}")
        elif d["mode"] == "dispatch":
            steps.append(f"dispatch {a} in answer-only mode with slice_{a}.json; it writes "
                         f"{d['reply_file']}")
    if rec["desk_requests"]:
        steps.append("answer desk_requests by running the named script; write "
                     "out_desk.r<round>.json {\"comms\":{\"answers\":[...]}}")
    if not steps:
        steps.append("converged -- proceed" if rec["converged"] else
                     "queued messages wait in inboxes of agents not yet dispatched; render their "
                     "slices (they embed desk_inbox) and dispatch the next layer")
    else:
        steps.append("then run comms-route again")
    return steps


def cmd_comms_status(args):
    from smith_core import emit
    doc = load_ledger(args.run_dir)
    d = digest(doc)
    if not args.full:
        d.pop("asks", None)
        d.pop("tells", None)
    emit(d)
