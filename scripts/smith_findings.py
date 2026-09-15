"""Prior-findings digest (added 2026-09-15).

User, after smith-catalyst spent its search budget re-answering a question the previous run had
already answered ("why did AI hardware fall 5-9% while SPX fell 0.5%?"): every sub-agent should
know the relevant findings of previously completed analyses.

The earlier conclusions did exist -- in state.factor_catalysts, the thesis map, cluster_ladders,
the strategist's tail and the briefing prose -- but nothing handed an agent "this is settled,
research the delta". This module keeps one typed record, findings.json. `postflight --phase commit`
updates it on EVERY run mode, and `slices` embeds a per-agent filtered view.

Rules of the record:
  * built from committed state and this run's tails only. Briefing prose is never parsed; the
    orchestrator's own conclusions arrive as a typed `findings_orchestrator.json`;
  * every finding carries as_of + ttl_days. An expired finding is shown flagged for a few days,
    then pruned EXPIRED_KEEP_DAYS after expiry. Its sources stay in state and run dirs;
  * agents feed back through two optional tail keys, `findings_reaffirmed` and `findings_revised`,
    so a re-check is recorded rather than silently repeated.
"""
import hashlib
import os
from datetime import date, timedelta

from smith_core import load_json, safe_write, now_utc, iso_utc

SCHEMA_VERSION = 1
FINDINGS_FILE = "findings.json"
CLAIM_MAX = 400
EXPIRED_KEEP_DAYS = 30
SHOW_EXPIRED_DAYS = 3

# How long a finding stays "settled" before an agent should treat it as needing a re-check.
TTL_DAYS = {"macro_regime": 1, "macro_calendar": 7, "playbook": 2, "orchestrator": 2,
            "thesis": 21, "ladder": 7,
            "catalyst:structural": 14, "catalyst:immediate": 2, "catalyst:noise": 1, "catalyst": 3}

# Which finding kinds each agent receives. An agent never gets a kind its own slice already carries
# in full (thesis/strategist/cluster already embed state.thesis), so the digest adds no duplicate bytes.
AGENT_KINDS = {
    "catalyst": ("catalyst", "macro", "orchestrator"),
    "signals": ("catalyst", "thesis", "orchestrator"),
    "thesis": ("catalyst", "ladder", "macro", "orchestrator"),
    "watchlist": ("catalyst", "macro"),
    "scout": ("macro", "playbook", "orchestrator"),
    "rebound": ("catalyst", "macro", "playbook", "orchestrator"),
    "cycle": ("catalyst", "macro", "ladder", "orchestrator"),
    "earnings": ("catalyst",),
    "quality": ("thesis",),
    "cluster": ("ladder", "catalyst", "orchestrator"),
    "strategist": ("playbook", "macro", "catalyst", "ladder", "orchestrator"),
    "ledger": (),
}
AGENT_CAP = {"strategist": 60}
DEFAULT_CAP = 30
DIGEST_FIELDS = ("id", "kind", "subject", "claim", "as_of", "expires", "verified", "source",
                 "horizon", "direction", "runs_seen", "last_reaffirmed", "revised_by")

RULE = ("PRIOR FINDINGS are what earlier runs (deep and quick, including the orchestrator's own "
        "conclusions) already established. Start from them and research only the delta since "
        "`prior_findings_since`. Do not re-search a finding unless it is expired, it directly drives "
        "a number you are about to put in a verdict or proposal, or you have new evidence against "
        "it. List ids you re-checked and still hold in `findings_reaffirmed`; put corrections in "
        "`findings_revised` as {id, claim, source, reason}. Never restate a prior finding as new.")


def _day(value):
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def _h(text):
    return hashlib.md5(str(text).encode()).hexdigest()[:10]


def _clip(text, n):
    text = " ".join(str(text or "").split())
    return text if len(text) <= n else text[:n - 1] + "…"


def load(base_dir):
    doc = load_json(os.path.join(base_dir, FINDINGS_FILE), default=None)
    return doc if isinstance(doc, dict) else {"schema_version": SCHEMA_VERSION, "findings": []}


def _catalyst_rows(state):
    fc = state.get("factor_catalysts")
    rows = fc.get("catalysts") if isinstance(fc, dict) else fc
    return [r for r in (rows or []) if isinstance(r, dict) and r.get("headline")]


def extract(state, run_dir, run_id, today):
    """Every finding this run can vouch for, from committed state plus this run's own tails."""
    out = []

    def add(kind, key, subject, claim, as_of, ttl, **extra):
        as_d = _day(as_of) or today
        f = {"id": f"{kind}:{key}", "kind": kind, "subject": subject, "claim": _clip(claim, CLAIM_MAX),
             "as_of": as_d.isoformat(), "ttl_days": ttl,
             "expires": (as_d + timedelta(days=ttl)).isoformat(), "run_id": run_id}
        f.update({k: v for k, v in extra.items() if v not in (None, "", [], {})})
        out.append(f)

    held = {h.get("ticker") for h in (state.get("holdings") or []) if isinstance(h, dict) and h.get("ticker")}

    for r in _catalyst_rows(state):
        horizon = r.get("horizon")
        claim = r["headline"] + (f" -- magnitude: {r['magnitude']}" if r.get("magnitude") else "")
        add("catalyst", _h(str(r["headline"])[:120] + str(r.get("date"))), list(r.get("affects") or [])[:15],
            claim, r.get("last_confirmed") or r.get("date"),
            TTL_DAYS.get(f"catalyst:{horizon}", TTL_DAYS["catalyst"]),
            horizon=horizon, direction=r.get("direction"), source=r.get("source"),
            verified=r.get("verified"), agent="smith-catalyst")

    mr = state.get("macro_read") or {}
    fomc = state.get("fomc_cache") or {}
    macro_as_of = _day(mr.get("as_of")) or today
    if fomc.get("stance") or fomc.get("rate_pct") is not None:
        nxt = _day(fomc.get("next_check_date"))
        ttl = max(1, (nxt - macro_as_of).days) if nxt and nxt > macro_as_of else 1
        add("macro", "fomc", "Fed", f"Fed funds {fomc.get('rate_pct')}% (stance {fomc.get('stance')}). "
            f"{fomc.get('note') or ''}", macro_as_of, ttl, agent="smith-scout")
    if mr.get("regime"):
        add("macro", "regime", "regime", f"Regime {mr['regime']}: {mr.get('regime_note') or ''}",
            macro_as_of, TTL_DAYS["macro_regime"], agent="smith-scout")
    cal = mr.get("calendar") or {}
    if cal:
        add("macro", "calendar", "calendar", "; ".join(f"{k}: {v}" for k, v in sorted(cal.items())),
            macro_as_of, TTL_DAYS["macro_calendar"], agent="smith-scout")

    for t, e in (state.get("thesis") or {}).items():
        if not isinstance(e, dict) or not e.get("status") or (held and t not in held):
            continue
        add("thesis", t, t, f"{e['status']} -- {e.get('thesis') or ''}", e.get("reviewed_on") or e.get("verified_on"),
            TTL_DAYS["thesis"], verified=e.get("verified"), agent="smith-thesis")

    for cname, lad in (state.get("cluster_ladders") or {}).items():
        if not isinstance(lad, dict) or not lad.get("leader"):
            continue
        names = [r.get("t") or r.get("ticker") for r in (lad.get("ranking") or []) if isinstance(r, dict)]
        ct = lad.get("cluster_thesis") if isinstance(lad.get("cluster_thesis"), dict) else {}
        claim = (f"{cname}: leader {lad['leader']}, laggard {lad.get('laggard')}; order {' > '.join(n for n in names if n)}"
                 + (f"; cluster thesis {ct.get('status')}, innings {ct.get('innings')}" if ct.get("status") else ""))
        add("ladder", _h(cname), cname, claim, lad.get("as_of"), TTL_DAYS["ladder"],
            verified=lad.get("confidence"), agent="smith-cluster")

    st = load_json(os.path.join(run_dir, "out_strategist.json"), default=None)
    if isinstance(st, dict):
        ro = st.get("risk_off_read") or {}
        if ro.get("note"):
            add("playbook", "risk_off", "book", f"Risk-off {ro.get('risk_off_status')}: {ro['note']}",
                today, TTL_DAYS["playbook"], agent="smith-strategist")
        fp = st.get("fomc_playbook") or {}
        decision = _day(fp.get("decision_date"))
        ttl = (decision - today).days + 1 if decision and decision >= today else TTL_DAYS["playbook"]
        pre = fp.get("pre_decision_posture") or {}
        if pre:
            add("playbook", "fomc_pre", "book", "FOMC pre-decision posture: "
                + " | ".join(f"{k}: {v}" for k, v in pre.items()), today, ttl,
                verified="judgment", agent="smith-strategist")
        for s in fp.get("scenarios") or []:
            if not isinstance(s, dict) or not s.get("branch"):
                continue
            sa = s.get("staged_actions") or {}
            hold = sa.get("hold") or sa.get("hold_then_tranche") or []
            add("playbook", f"fomc_{s['branch']}", "book",
                f"FOMC branch {s['branch']} (~{s.get('probability_pct')}%): execute "
                f"{', '.join(sa.get('execute') or []) or 'none'}; hold {', '.join(hold) or 'none'}. "
                f"Rule: {sa.get('confirmation_rule') or ''}", today, ttl,
                verified="judgment", agent="smith-strategist")

    orch = load_json(os.path.join(run_dir, "findings_orchestrator.json"), default=None)
    rows = orch.get("findings") if isinstance(orch, dict) else orch
    for r in rows or []:
        if not isinstance(r, dict) or not r.get("claim"):
            continue
        key = r.get("id") or _h(str(r.get("subject")) + str(r["claim"])[:120])
        try:
            ttl = max(1, int(r.get("ttl_days") or TTL_DAYS["orchestrator"]))
        except (TypeError, ValueError):
            ttl = TTL_DAYS["orchestrator"]
        add("orchestrator", key, r.get("subject") or "book", r["claim"], r.get("as_of") or today, ttl,
            source=r.get("source"), verified=r.get("verified"), agent="orchestrator")
    return out


def _apply_feedback(by_id, run_dir, today):
    reaffirmed, revised, unknown = 0, 0, []
    try:
        names = sorted(os.listdir(run_dir))
    except OSError:
        names = []
    for name in names:
        if not (name.startswith("out_") and name.endswith(".json")):
            continue
        agent = name[4:-5]
        tail = load_json(os.path.join(run_dir, name), default=None)
        if not isinstance(tail, dict):
            continue
        for fid in tail.get("findings_reaffirmed") or []:
            f = by_id.get(fid) if isinstance(fid, str) else None
            if f is None:
                unknown.append(str(fid))
                continue
            f["last_reaffirmed"] = today.isoformat()
            f["reaffirmed_by"] = sorted(set((f.get("reaffirmed_by") or []) + [agent]))
            reaffirmed += 1
        for r in tail.get("findings_revised") or []:
            f = by_id.get(r.get("id")) if isinstance(r, dict) else None
            if f is None or not r.get("claim"):
                unknown.append(str(r.get("id") if isinstance(r, dict) else r))
                continue
            f["previous_claim"] = f.get("claim")
            f["claim"] = _clip(r["claim"], CLAIM_MAX)
            f["as_of"] = today.isoformat()
            f["expires"] = (today + timedelta(days=f.get("ttl_days") or 1)).isoformat()
            f["revised_by"] = agent
            f["revised_reason"] = r.get("reason")
            if r.get("source"):
                f["source"] = r["source"]
            revised += 1
    return {"reaffirmed": reaffirmed, "revised": revised, "unknown_ids": unknown[:20]}


def update(base_dir, run_dir, run_id, today, state=None):
    """Fold this run's findings and agent feedback into findings.json. Never raises on bad input
    rows; a newer schema_version than this code knows is refused, not overwritten."""
    doc = load(base_dir)
    if (doc.get("schema_version") or 1) > SCHEMA_VERSION:
        return {"error": f"findings.json schema_version {doc.get('schema_version')} is newer than this code"}
    if state is None:
        state = load_json(os.path.join(base_dir, "state.json"), default={}) or {}
    by_id = {f["id"]: f for f in (doc.get("findings") or []) if isinstance(f, dict) and f.get("id")}
    added = changed = 0
    for n in extract(state, run_dir, run_id, today):
        old = by_id.get(n["id"])
        if old is None:
            n["first_seen"], n["runs_seen"] = n["as_of"], 1
            added += 1
        else:
            n["first_seen"] = old.get("first_seen") or old.get("as_of")
            for k in ("last_reaffirmed", "reaffirmed_by"):
                if k in old:
                    n[k] = old[k]
            if old.get("claim") == n["claim"]:
                n["runs_seen"] = (old.get("runs_seen") or 1) + (0 if old.get("run_id") == run_id else 1)
            else:
                n["runs_seen"], n["previous_claim"] = 1, old.get("claim")
                changed += 1
        by_id[n["id"]] = n
    feedback = _apply_feedback(by_id, run_dir, today)
    pruned = 0
    for fid, f in list(by_id.items()):
        exp = _day(f.get("expires"))
        f["expired"] = bool(exp and exp < today)
        if exp and exp < today - timedelta(days=EXPIRED_KEEP_DAYS):
            del by_id[fid]
            pruned += 1
    rows = sorted(by_id.values(), key=lambda f: (str(f.get("kind")), str(f.get("id"))))
    safe_write(os.path.join(base_dir, FINDINGS_FILE),
               {"schema_version": SCHEMA_VERSION, "updated": today.isoformat(), "run_id": run_id,
                "run_ts": iso_utc(now_utc()), "findings": rows})
    kinds = {}
    for f in rows:
        kinds[f["kind"]] = kinds.get(f["kind"], 0) + 1
    return {"count": len(rows), "by_kind": kinds, "added": added, "changed": changed, "pruned": pruned,
            "expired": sum(1 for f in rows if f.get("expired")), "feedback": feedback}


def digest_for(doc, agent_key, held=None, cluster_name=None, cluster_members=None, today=None):
    """The slice of findings.json one agent should start from."""
    fam = "cluster" if str(agent_key).startswith("cluster_") else agent_key
    kinds = AGENT_KINDS.get(fam, ())
    today = today or date.today()
    held, members = set(held or ()), set(cluster_members or ())
    picked = []
    for f in (doc or {}).get("findings") or []:
        if not isinstance(f, dict) or f.get("kind") not in kinds:
            continue
        exp = _day(f.get("expires"))
        if exp and exp < today - timedelta(days=SHOW_EXPIRED_DAYS):
            continue
        subj = f.get("subject")
        subj_set = set(subj) if isinstance(subj, list) else {subj}
        if fam == "cluster":
            if f["kind"] == "ladder" and subj != cluster_name:
                continue
            if f["kind"] == "catalyst" and members and not (subj_set & members):
                continue
        elif f["kind"] == "thesis" and held and not (subj_set & held):
            continue
        row = {k: f[k] for k in DIGEST_FIELDS if f.get(k) not in (None, "", [])}
        row["expired"] = bool(exp and exp < today)
        picked.append(row)
    picked.sort(key=lambda r: (r["expired"], kinds.index(r["kind"]),
                               -((_day(r.get("as_of")) or date.min).toordinal())))
    cap = AGENT_CAP.get(fam, DEFAULT_CAP)
    return {"since": (doc or {}).get("run_ts"), "since_run": (doc or {}).get("run_id"),
            "rule": RULE, "findings": picked[:cap], "truncated": max(0, len(picked) - cap)}
