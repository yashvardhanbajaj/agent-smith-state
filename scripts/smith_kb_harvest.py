"""Turn what the desk already writes into knowledge-base observations (2026-09-21).

Agents keep returning the same structured tails they always did; this module reads them, plus a run's
desk-debate digest, the strategist's decisions and any explicit `learned` block, and produces
observations for `smith_kb`. Best-effort and defensive: a malformed tail yields fewer observations, never an
exception. Also derives observations from a whole `state.json` snapshot (used to backfill from git history)."""
import glob
import json
import os

import smith_kb as K

STATUS_CONF = {"primary": "primary", "secondary": "secondary", "unverified": "unverified", "verified": "primary"}


def _conf(v):
    if isinstance(v, bool):
        return "primary" if v else "unverified"
    return STATUS_CONF.get(str(v or "").lower(), "unverified")


def _list(x):
    return x if isinstance(x, list) else []


def _safe(fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except (KeyError, TypeError, ValueError, AttributeError):
        return []


def _mk(out, *args, **kw):
    try:
        out.append(K.make_obs(*args, **kw))
    except ValueError:
        pass


# ------------------------------------------------------------------------------------------- thesis
def thesis_obs(ticker, entry, as_of, agent="thesis", run=None):
    """A thesis entry -> one verdict (status timeline) + its evidence as facts."""
    out = []
    if not isinstance(entry, dict):
        return out
    status = entry.get("status")
    text = entry.get("thesis") or entry.get("note") or ""
    if status and text:
        _mk(out, [K.T(ticker)], "verdict", f"{status.upper()}: {text}", topic="thesis", value=status,
            source=entry.get("verified_against"), as_of=as_of, confidence=_conf(entry.get("verified")), agent=agent, run=run)
    for side, label in (("evidence_for", "FOR"), ("evidence_against", "AGAINST")):
        for ev in _list(entry.get(side)):
            claim = ev.get("claim") if isinstance(ev, dict) else str(ev)
            if not claim or len(str(claim)) < 12 or str(claim).lower().startswith("none found"):
                continue
            src = ev.get("source") if isinstance(ev, dict) else None
            _mk(out, [K.T(ticker)], "fact", f"[thesis evidence {label}] {claim}", topic="thesis_evidence", source=src,
                as_of=(ev.get("date") if isinstance(ev, dict) and ev.get("date") else as_of), confidence=_conf(entry.get("verified")),
                agent=agent, run=run)
    # a thesis review REPLACES its evidence arrays: evidence from an earlier review that this one no longer cites
    # is stale, not live knowledge (it stays in the log, superseded).
    if status and text:
        keep = [o["id"] for o in out if o.get("topic") == "thesis_evidence"]
        out.append(K.close_slot_event("thesis_evidence", K.T(ticker), (), as_of, keep_ids=keep))
    return out


def from_thesis_tail(tail, as_of, run):
    out = []
    for t, e in ((tail.get("thesis") or {}).get("changed") or {}).items():
        out += thesis_obs(t, e if isinstance(e, dict) else {"status": None}, as_of, run=run)
    for t, note in ((tail.get("thesis") or {}).get("reviewed_notes") or {}).items():
        _mk(out, [K.T(t)], "fact", f"[reviewed, unchanged] {note}", as_of=as_of, confidence="secondary", agent="thesis", run=run)
    for te in _list(tail.get("thesis_tensions")):
        if isinstance(te, dict) and te.get("reconciliation"):
            _mk(out, [K.entity_key("M", te.get("metric") or "thesis")], "fact",
                f"[{te.get('metric')}] {te.get('reconciliation')}", as_of=as_of, confidence="secondary", agent="thesis", run=run)
    return out


# ---------------------------------------------------------------------------------------------- cluster
def from_cluster_tail(tail, as_of, run, agent="cluster"):
    out = []
    cl = tail.get("cluster")
    if not cl:
        return out
    ce = K.C(cl)
    ct = tail.get("cluster_thesis") or {}
    if ct.get("text"):
        _mk(out, [ce], "verdict", f"{str(ct.get('status') or '').upper()} ({ct.get('innings')}): {ct['text']}",
            topic="cluster_thesis", value=ct.get("status"), as_of=as_of, confidence="secondary", agent=agent, run=run)
        if ct.get("falsifier"):
            _mk(out, [ce], "fact", f"[falsifier] {ct['falsifier']}", as_of=as_of, confidence="secondary", agent=agent, run=run)
    mp = tail.get("margin_pool") or {}
    if mp.get("moving_toward"):
        _mk(out, [ce], "fact", f"[margin pool] moving toward {mp.get('moving_toward')}; away from {mp.get('moving_away_from')}",
            as_of=as_of, confidence="secondary", agent=agent, run=run,
            source="; ".join(str(e.get("source")) for e in _list(mp.get("evidence"))[:2] if isinstance(e, dict)))
    rank = [r for r in _list(tail.get("ranking")) if isinstance(r, dict)]
    # A desk-round REVISION carries only the rows that changed. Treat the ladder as complete only when it is a full
    # tail (>= 4 ranked names) or the revision states the whole order itself; a partial ranking must never be stored
    # as the ladder order, and must never close the ranks of names it simply did not mention.
    full = len(rank) >= 4
    order = tail.get("order") if isinstance(tail.get("order"), str) else None
    if rank and full:
        order = " > ".join(r.get("ticker", "?") for r in sorted(rank, key=lambda r: r.get("rank", 99)))
    if order:
        _mk(out, [ce], "verdict", f"Ladder order {order}; leader {tail.get('leader')}, laggard {tail.get('laggard')}",
            topic="ladder_order", value=order, as_of=as_of, confidence="secondary", agent=agent, run=run)
    for r in rank:
        t = r.get("ticker")
        if not t:
            continue
        _mk(out, [K.T(t), ce], "verdict",
            f"rank {r.get('rank')} ({r.get('verdict')}). Case against: {r.get('case_against') or 'n/a'}",
            topic="ladder_rank", value=r.get("rank"), as_of=as_of, confidence="secondary", agent=agent, run=run)
    if full:                                   # names absent from a complete ladder are no longer ranked
        out.append(K.close_slot_event("ladder_rank", ce, {K.T(r["ticker"]) for r in rank if r.get("ticker")}, as_of))
    for p in _list(tail.get("redundant_pairs")):
        if isinstance(p, dict) and len(_list(p.get("pair"))) == 2:
            a, b = p["pair"]
            _mk(out, [K.T(a), K.T(b)], "relation",
                f"{a}/{b}: {p.get('verdict')} -- {p.get('same_bet_because')} (keep {p.get('keep')}, drop {p.get('drop')})",
                topic="pair", value=p.get("verdict"), as_of=as_of, confidence="secondary", agent=agent, run=run)
    for w in _list(tail.get("reorder_when")):
        _mk(out, [ce], "fact", f"[reorder when] {w}", as_of=as_of, confidence="secondary", agent=agent, run=run)
    for b in _list(tail.get("bench")):
        if isinstance(b, dict) and b.get("ticker"):
            _mk(out, [K.T(b["ticker"]), ce], "fact",
                f"[bench, better than {b.get('why_better_than')}] {b.get('entry_condition')}", as_of=as_of,
                confidence="secondary", agent=agent, run=run)
    return out


# --------------------------------------------------------------------------------------------- catalyst
def catalyst_obs(c, as_of, agent="catalyst", run=None, kind="event", extra=""):
    ents = [K.T(t) for t in _list(c.get("affects"))][:12]
    if not ents:
        ents = [K.entity_key("TH", "book-factor")]
    head = c.get("headline") or c.get("event") or c.get("claim")
    if not head:
        return []
    txt = f"{str(c.get('direction') or '').upper()}/{c.get('horizon')}: {head}{extra}"
    out = []
    _mk(out, ents, kind, txt, source=c.get("source"), as_of=c.get("date") or as_of, confidence="secondary", agent=agent, run=run)
    return out


def from_catalyst_tail(tail, as_of, run):
    out = []
    for c in _list(tail.get("catalysts")):
        if isinstance(c, dict):
            out += catalyst_obs(c, as_of, run=run)
    for r in _list(tail.get("retired_catalysts")):
        if isinstance(r, dict):
            out += catalyst_obs(r, as_of, run=run, extra=f" [RETIRED: {r.get('reason')}]")
    return out


# ------------------------------------------------------------------------------------ earnings/scout/etc
def from_earnings_tail(tail, as_of, run):
    out = []
    for t, f in (tail.get("earnings_facts_updates") or {}).items():
        if not isinstance(f, dict):
            continue
        bits = [f"{f.get('period')} reported {f.get('reported_date')}: revenue {f.get('revenue_actual')} vs {f.get('revenue_consensus')}",
                f"EPS {f.get('eps_actual')} vs {f.get('eps_consensus')} ({f.get('quarter_verdict')})"]
        if f.get("guide_next_q"):
            bits.append(f"next-quarter guide {f.get('guide_next_q')}")
        if f.get("guide_fy"):
            bits.append(f"FY guide {f.get('guide_fy')}")
        if f.get("backlog"):
            bits.append(f"backlog {f.get('backlog')}")
        _mk(out, [K.T(t)], "fact", "[earnings] " + "; ".join(bits), as_of=f.get("reported_date") or as_of,
            confidence="primary" if f.get("verified") else "secondary", agent="earnings", run=run)
    return out


def from_scout_tail(tail, as_of, run):
    out = []
    m = K.entity_key("M", "macro")
    if tail.get("sentiment_narrative"):
        _mk(out, [m], "fact", f"[regime] {tail['sentiment_narrative']}", as_of=as_of, confidence="secondary", agent="scout", run=run)
    if tail.get("fomc_stance"):
        _mk(out, [m], "verdict", f"Fed funds {tail.get('fed_funds_pct')}%, stance {tail['fomc_stance']}", topic="fomc",
            value=tail["fomc_stance"], as_of=as_of, confidence="secondary", agent="scout", run=run)
    cal = tail.get("calendar") or {}
    if cal:
        _mk(out, [m], "fact", f"[calendar] FOMC {cal.get('next_fomc')}, CPI {cal.get('next_cpi')}, NFP {cal.get('next_nfp')}",
            as_of=as_of, confidence="secondary", agent="scout", run=run)
    for c in _list((tail.get("diversifier_candidates") or {}).get("candidates") if isinstance(tail.get("diversifier_candidates"), dict)
                   else tail.get("diversifier_candidates")):
        if isinstance(c, dict) and c.get("ticker"):
            _mk(out, [K.T(c["ticker"])], "fact",
                f"[diversifier bench] {'clean' if c.get('clean_diversifier', True) else 'PARTIAL'} diversifier; {c.get('note') or c.get('thesis') or ''}",
                as_of=as_of, confidence="secondary", agent="scout", run=run)
    return out


def from_signals_tail(tail, as_of, run):
    out = []
    for t, u in (tail.get("analyst_targets_updates") or {}).items():
        if isinstance(u, dict) and (u.get("mean_target") or u.get("mean")):
            _mk(out, [K.T(t)], "fact", f"[analyst targets] mean target {u.get('mean_target') or u.get('mean')} "
                f"(n {u.get('n_analysts')}), gap {u.get('gap_pct')}", as_of=as_of, confidence="secondary", agent="signals", run=run)
    for t, buckets in ((tail.get("signal_history") or {}).get("changed") or {}).items():
        _mk(out, [K.T(t)], "fact", f"[signals] {', '.join(buckets) if isinstance(buckets, list) else buckets}",
            topic="signal", as_of=as_of, confidence="computed", agent="signals", run=run)
    return out


def from_strategist_tail(tail, as_of, run):
    out = []
    for p in _list(tail.get("proposals")):
        if isinstance(p, dict) and p.get("ticker") and p.get("rationale"):
            _mk(out, [K.T(p["ticker"])], "event", f"[proposal] {p.get('direction')} ${p.get('size_usd')} ({p.get('trigger_type')}): {p.get('rationale')}",
                topic="proposal", as_of=as_of, confidence="secondary", agent="strategist", run=run)
    if tail.get("scorecard_read"):
        _mk(out, [K.entity_key("M", "desk")], "event", f"[scorecard read] {tail['scorecard_read']}", topic="scorecard_read",
            as_of=as_of, confidence="secondary", agent="strategist", run=run)
    return out


# --------------------------------------------------------------------------------------------- desk debate
def from_comms_digest(digest, as_of, run):
    out = []
    for r in _list(digest.get("revisions")):
        if not isinstance(r, dict):
            continue
        ents = [K.T(r["ticker"])] if r.get("ticker") else [K.entity_key("M", "desk")]
        _mk(out, ents, "correction", f"[desk revision by {r.get('agent')}] " + "; ".join(_list(r.get("changed"))[:3]),
            as_of=as_of, confidence="secondary", agent="desk", run=run)
    for a in _list(digest.get("asks")):
        if isinstance(a, dict) and a.get("answer") and a.get("position") in ("revised", "held", "cannot_answer"):
            ents = [K.T(a["ticker"])] if a.get("ticker") else [K.entity_key("M", "desk")]
            _mk(out, ents, "lesson", f"[desk Q&A {a.get('from')}->{a.get('to')}] Q: {K.cap_text(a.get('question'), 200)} "
                f"A ({a.get('position')}): {K.cap_text(a.get('answer'), 320)}", as_of=as_of, confidence="secondary", agent="desk", run=run)
    for u in _list(digest.get("unresolved")):
        ents = [K.T(u["ticker"])] if isinstance(u, dict) and u.get("ticker") else [K.entity_key("M", "desk")]
        _mk(out, ents, "tension", f"[unresolved] {json.dumps(u)[:300]}", as_of=as_of, confidence="unverified", agent="desk", run=run)
    return out


# ------------------------------------------------------------------------------ explicit `learned` blocks
def from_learned(tail, as_of, run, agent):
    """Any tail may carry `learned`: [{entities, kind, text, topic?, value?, source?, confidence?}]."""
    out = []
    for l in _list(tail.get("learned")):
        if not isinstance(l, dict):
            continue
        ents = [e if ":" in str(e) else K.T(e) for e in _list(l.get("entities"))]
        _mk(out, ents, l.get("kind") if l.get("kind") in K.KINDS else "fact", l.get("text"), topic=l.get("topic"),
            value=l.get("value"), source=l.get("source"), as_of=l.get("as_of") or as_of,
            confidence=_conf(l.get("confidence")), agent=agent, run=run)
    return out


TAIL_HANDLERS = {"thesis": from_thesis_tail, "catalyst": from_catalyst_tail, "earnings": from_earnings_tail,
                 "scout": from_scout_tail, "signals": from_signals_tail, "strategist": from_strategist_tail}


# ------------------------------------------------------------------- quality / cycle / watchlist / rebound
def from_quality_tail(tail, as_of, run):
    out = []
    for t, flags in (tail.get("quality_flags") or {}).items():
        for fl in _list(flags):
            _mk(out, [K.T(t)], "fact", f"[quality flag] {fl if isinstance(fl, str) else json.dumps(fl)[:400]}", as_of=as_of,
                confidence="secondary", agent="quality", run=run)
    for t, f in (tail.get("financials_updates") or {}).items():
        if isinstance(f, dict):
            _mk(out, [K.T(t)], "fact", "[quality financials] " + K.cap_text(json.dumps(f, default=str), 450), as_of=as_of,
                confidence="secondary", agent="quality", run=run)
    if tail.get("top_concern"):
        _mk(out, [K.entity_key("M", "desk")], "fact", f"[quality top concern] {tail['top_concern']}", as_of=as_of,
            confidence="secondary", agent="quality", run=run)
    return out


def from_cycle_tail(tail, as_of, run):
    out = []
    if tail.get("cycle_position"):
        m = K.entity_key("M", "ai-capex-cycle")
        _mk(out, [m], "verdict", f"{str(tail['cycle_position']).upper()} ({tail.get('confidence')}): {tail.get('priced_in_read') or ''} "
            f"Falsifier: {tail.get('falsifier') or 'n/a'}", topic="cycle_position", value=tail["cycle_position"], as_of=as_of,
            confidence="secondary", agent="cycle", run=run)
        for side, label in (("evidence_for", "FOR"), ("evidence_against", "AGAINST")):
            for e in _list(tail.get(side)):
                claim = e.get("claim") if isinstance(e, dict) else str(e)
                if claim:
                    _mk(out, [m], "fact", f"[cycle evidence {label}] {claim}", source=e.get("source") if isinstance(e, dict) else None,
                        as_of=as_of, confidence="secondary", agent="cycle", run=run)
    return out


def from_watchlist_tail(tail, as_of, run):
    out = []
    for st in _list(tail.get("watchlist_setups")):
        if isinstance(st, dict) and st.get("ticker"):
            _mk(out, [K.T(st["ticker"])], "fact", f"[watchlist setup] " + K.cap_text(
                st.get("setup") or st.get("note") or st.get("reason") or json.dumps(st, default=str), 380),
                as_of=as_of, confidence="secondary", agent="watchlist", run=run)
    return out


def from_rebound_tail(tail, as_of, run):
    out = []
    for p in _list(tail.get("proposals")):
        if isinstance(p, dict) and p.get("ticker"):
            _mk(out, [K.T(p["ticker"])], "fact", "[rebound candidate] " + K.cap_text(
                p.get("rationale") or p.get("why") or json.dumps(p, default=str), 380), as_of=as_of, confidence="secondary",
                agent="rebound", run=run)
    for e in _list(tail.get("considered_excluded")):
        if isinstance(e, dict) and e.get("ticker"):
            _mk(out, [K.T(e["ticker"])], "lesson", "[rebound excluded] " + K.cap_text(e.get("reason") or json.dumps(e, default=str), 300),
                as_of=as_of, confidence="secondary", agent="rebound", run=run)
    return out


TAIL_HANDLERS.update({"quality": from_quality_tail, "cycle": from_cycle_tail, "watchlist": from_watchlist_tail,
                      "rebound": from_rebound_tail})


def harvest_tail(agent_key, tail, as_of, run):
    if not isinstance(tail, dict):
        return []
    out = []
    if agent_key.startswith("cluster"):
        out += _safe(from_cluster_tail, tail, as_of, run)
    elif agent_key in TAIL_HANDLERS:
        out += _safe(TAIL_HANDLERS[agent_key], tail, as_of, run)
    out += _safe(from_learned, tail, as_of, run, agent_key)
    # a desk-round reply carries its REVISION inside comms.answers[*].revision: same shape as a tail, later in time
    for a in _list((tail.get("comms") or {}).get("answers")):
        rev = a.get("revision") if isinstance(a, dict) else None
        if isinstance(rev, dict):
            if agent_key.startswith("cluster"):
                rev = dict(rev, cluster=rev.get("cluster") or tail.get("cluster"))
                out += _safe(from_cluster_tail, rev, as_of, run)
            elif agent_key in TAIL_HANDLERS:
                out += _safe(TAIL_HANDLERS[agent_key], rev, as_of, run)
    return out


def apply_refutations(base, tail, agent_key):
    """`memory_refuted`: [{id, reason}] -> refute events. `memory_used`: [ids] -> use events."""
    n = 0
    for r in _list(tail.get("memory_refuted")):
        if isinstance(r, dict) and r.get("id"):
            n += K.refute(base, [r["id"]], r.get("reason") or "refuted by " + agent_key, by=agent_key)
    used = [i for i in _list(tail.get("memory_used")) if isinstance(i, str)]
    if used:
        K.record_use(base, used)
    return n


def _round_no(name):
    """out_<key>.json -> 0; out_<key>.r3.json -> 3 (desk-round revision). Deterministic: file mtimes are not trusted
    (an agent may re-touch a base tail after writing its revision)."""
    import re as _re
    m = _re.search(r"\.r(\d+)$", name)
    return int(m.group(1)) if m else 0


def run_batches(base, run_dir, run_id, as_of, apply_refute=False):
    """[(utc_timestamp, observations, filename)] for every tail (final + revision files), the desk digest and the
    orchestrator findings of one run. Order: base tails, then revision rounds ascending, then digest, then findings;
    timestamps are the run's earliest file time plus that position, so they sort the same way globally."""
    import datetime as _dt
    files = []
    for path in glob.glob(os.path.join(run_dir, "out_*.json")):
        name = os.path.basename(path)[4:-5]
        if name.split(".")[0] == "desk" or ".r0_orig" in name:
            continue
        files.append((_round_no(name), name, path))
    files.sort()
    extras = [("digest", os.path.join(run_dir, "comms", "digest.json")),
              ("findings_orchestrator", os.path.join(run_dir, "findings_orchestrator.json"))]
    existing = [p for _, _, p in files] + [p for _, p in extras if os.path.exists(p)]
    t0 = min((os.path.getmtime(p) for p in existing), default=0.0)

    def ts(pos):
        return (_dt.datetime.fromtimestamp(t0, tz=_dt.timezone.utc) + _dt.timedelta(milliseconds=pos)).isoformat()

    batches, pos = [], 0
    for rnd, name, path in files:
        try:
            tail = json.load(open(path))
        except (OSError, ValueError):
            continue
        pos += 1
        batches.append((ts(pos), harvest_tail(name.split(".")[0], tail, as_of, run_id), name))
        if apply_refute:
            apply_refutations(base, tail, name.split(".")[0])
    dp = extras[0][1]
    if os.path.exists(dp):
        try:
            pos += 1
            batches.append((ts(pos), _safe(from_comms_digest, json.load(open(dp)), as_of, run_id), "digest"))
        except (OSError, ValueError):
            pass
    fp = extras[1][1]
    if os.path.exists(fp):
        try:
            o = []
            for f in _list(json.load(open(fp))):
                subj = f.get("subject")
                ents = [K.T(subj)] if isinstance(subj, str) and subj.isupper() and len(subj) <= 5 else [K.entity_key("M", str(subj or "desk"))]
                _mk(o, ents, "fact", f.get("claim"), source=f.get("source"), as_of=as_of, confidence="secondary",
                    agent="orchestrator", run=run_id)
            pos += 1
            batches.append((ts(pos), o, "findings_orchestrator"))
        except (OSError, ValueError):
            pass
    return batches


def memory_contract(run_dir):
    """Did each agent honour the memory contract (2026-09-21)? For every base tail of a run: how many `learned`,
    `memory_used` and `memory_refuted` entries it returned, and whether its slice actually carried memory items.
    `silent` = agents that were handed memory and returned none of the three -- visible non-compliance, never a gate:
    knowledge is context, so a silent agent degrades the memory's growth, not the run."""
    rows, silent = {}, []
    for path in sorted(glob.glob(os.path.join(run_dir, "out_*.json"))):
        name = os.path.basename(path)[4:-5]
        if "." in name or name == "desk":              # revisions (.rN, .r0_orig), desk replies, librarian batches
            continue
        try:
            tail = json.load(open(path))
        except (OSError, ValueError):
            continue
        if not isinstance(tail, dict):
            continue
        try:
            sl = json.load(open(os.path.join(run_dir, f"slice_{name}.json")))
            mem = sl.get("memory")
            handed = len(mem.get("items") or []) if isinstance(mem, dict) else 0
        except (OSError, ValueError):
            handed = None
        row = {k: len(_list(tail.get(k))) for k in ("learned", "memory_used", "memory_refuted")}
        row["memory_handed"] = handed
        rows[name] = row
        if handed and not any(row[k] for k in ("learned", "memory_used", "memory_refuted")):
            silent.append(name)
    eligible = [n for n, r in rows.items() if r["memory_handed"]]
    return {"agents": rows, "silent": silent,
            "adoption": (f"{len(eligible) - len(silent)}/{len(eligible)} agents handed memory used the contract"
                         if eligible else "no agent was handed memory this run")}


def harvest_run(base, run_dir, run_id, as_of):
    """All observations of one run, in chronological order, plus the file names read."""
    obs, files = [], []
    for _, o, name in run_batches(base, run_dir, run_id, as_of, apply_refute=True):
        obs += o
        files.append(name)
    return obs, files


# ------------------------------------------------------------------------------ state snapshot (backfill)
def from_state_snapshot(state, as_of, run=None):
    """Observations from one committed state.json (thesis, ladders, catalysts, earnings, gaps, macro)."""
    out = []
    for t, e in (state.get("thesis") or {}).items():
        if isinstance(e, dict) and not str(t).startswith("_") and t != "schema_version":
            out += thesis_obs(t, e, e.get("reviewed_on") or as_of, agent="thesis", run=run)
    for cl, L in (state.get("cluster_ladders") or {}).items():
        if isinstance(L, dict) and L.get("ranking"):
            tail = dict(L, cluster=L.get("cluster") or cl)
            out += _safe(from_cluster_tail, tail, L.get("as_of") or as_of, run, "cluster")
    for c in state.get("factor_catalysts") or []:
        if isinstance(c, dict):
            out += catalyst_obs(c, as_of, run=run)
    for a in state.get("catalyst_archive") or []:
        if isinstance(a, dict):
            out += catalyst_obs(a, a.get("retired_on") or as_of, run=run, extra=f" [RETIRED: {a.get('retired_reason')}]")
    ef = ((state.get("data_cache") or {}).get("earnings_facts")) or {}
    out += _safe(from_earnings_tail, {"earnings_facts_updates": {k: v for k, v in ef.items() if isinstance(v, dict)}}, as_of, run)
    for g in state.get("known_gaps") or []:
        if isinstance(g, dict) and g.get("id"):
            _mk(out, [K.entity_key("M", "desk")], "lesson", f"[{g.get('id')}] {g.get('title') or g.get('summary') or g.get('text') or ''}",
                as_of=g.get("opened") or as_of, confidence="secondary", agent="desk", run=run)
    mr = state.get("macro_read") or {}
    if mr:
        _mk(out, [K.entity_key("M", "macro")], "fact", "[macro read] " + K.cap_text(json.dumps(mr, default=str), 500),
            as_of=(mr.get("as_of") if isinstance(mr, dict) else None) or as_of, confidence="secondary", agent="scout", run=run)
    sm = state.get("sector_map") or {}
    for t, cl in sm.items():
        if isinstance(cl, str):
            _mk(out, [K.T(t), K.C(cl)], "relation", f"{t} is classified in {cl}", topic="member", value=cl,
                as_of=as_of, confidence="computed", agent="thesis", run=run)
    return out


def from_findings_doc(doc, as_of, run=None):
    out = []
    for f in (doc or {}).get("findings") or []:
        if not isinstance(f, dict):
            continue
        subj = f.get("subject")
        subs = subj if isinstance(subj, list) else [subj]
        ents = []
        for s in subs:
            s = str(s or "")
            ents.append(K.T(s) if s.isupper() and 1 < len(s) <= 5 else K.entity_key("M", s or "desk"))
        _mk(out, ents[:6] or [K.entity_key("M", "desk")], "fact" if f.get("kind") != "debate" else "lesson",
            f"[{f.get('kind')}] {f.get('claim')}", source=f.get("source"), as_of=f.get("as_of") or as_of,
            confidence="secondary", agent=f.get("kind"), run=run)
    return out
