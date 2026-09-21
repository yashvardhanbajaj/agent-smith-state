"""Agent Smith knowledge base (2026-09-21). The desk's long-term memory.

WHY. Every run used to overwrite its own conclusions: a thesis was a snapshot, a ladder was replaced,
a finding expired after 1-60 days, and the desk debates lived only in `runs/` (pruned to 10). The
system learned a lot each run and kept almost none of it. The knowledge base keeps what each run
learns about each STOCK, CLUSTER, THEME and the MACRO backdrop, and lets the next run retrieve it.

SHAPE (git-tracked JSON, no database -- user decision 2026-09-21):
  knowledge/observations.jsonl   APPEND-ONLY event log. The single source of truth. Never edited.
  knowledge/entities/*.json      derived pages (verdict timelines, live facts, tensions), rebuilt on demand
  knowledge/graph.json           derived connections between entities, weights strengthen / decay
  knowledge/config.json          retrieval budget per agent (default 5000 tokens, override per agent)

An OBSERVATION is one thing learned: entities, kind (fact | verdict | event | lesson | relation |
tension | correction), text, source, as_of, confidence (primary | secondary | unverified), and for a
verdict a `topic` + structured `value` so a timeline can be drawn. EVENTS on the log: add, reinforce
(re-confirmed by a later run), supersede (a fresher verdict replaces it; the old one stays), refute
(an agent found it false; it stays, flagged), use.

NOTHING IS EVER DELETED. Age only lowers RETRIEVAL rank (a half-life per kind), so a fact that nobody has
touched for a year is quiet, not gone, and `kb-query` still finds it. Connections between entities
gain weight each time a run re-confirms them and lose it with time: the neural-network-like behaviour
the user asked for, in a form that diffs cleanly in git.

KNOWLEDGE IS CONTEXT, NEVER A GATE. Retrieved memories carry their provenance and confidence tier and an
unverified one is labelled as such; nothing here feeds sizing, an EV gate or a vote. (Same rule as
ENGINE_EPOCH: outcomes from before the rebuild are not evidence.)

Pure functions + a small IO layer. No agent calls; harvesting reads the tails agents already write."""
import datetime as _dt
import hashlib
import json
import math
import os
import re

KB_DIR = "knowledge"
OBS_FILE = "observations.jsonl"
CFG_FILE = "config.json"
KINDS = ("fact", "verdict", "event", "lesson", "relation", "tension", "correction")
CONFIDENCE_WEIGHT = {"primary": 1.0, "verified": 1.0, "computed": 1.0, "secondary": 0.8, "unverified": 0.5}
# retrieval half-lives (days): how fast a memory quiets, NOT when it is forgotten
# how much a kind matters when memories compete for a token budget (analysis outranks bookkeeping)
KIND_WEIGHT = {"verdict": 1.3, "correction": 1.3, "lesson": 1.0, "event": 1.0, "fact": 0.85, "relation": 0.9, "tension": 1.0}
TOPIC_WEIGHT = {"signal": 0.3, "member": 0.25}
HALF_LIFE_DAYS = {"fact": 60, "verdict": 45, "event": 30, "lesson": 365, "relation": 180, "tension": 30,
                  "correction": 365}
DEFAULT_CONFIG = {"default_tokens": 5000, "per_agent": {}, "recent_change_days": 14,
                  "max_text_chars": 700, "neighbour_weight": 0.4, "cluster_weight": 0.6}
TEXT_CAP = 700


# --------------------------------------------------------------------------------------------- helpers
def _today(v=None):
    if isinstance(v, _dt.date):
        return v
    if v:
        return _dt.date.fromisoformat(str(v)[:10])
    return _dt.date.today()


def clean_date(v, fallback=None):
    """A valid ISO date string from anything an agent wrote: '2026-09-14', '2026-09-14T..', '2026-07-late' -> 2026-07-01."""
    m = re.match(r"^\s*(\d{4})-(\d{2})-(\d{2})", str(v or ""))
    if m:
        try:
            return _dt.date(int(m[1]), int(m[2]), int(m[3])).isoformat()
        except ValueError:
            pass
    m = re.match(r"^\s*(\d{4})-(\d{2})", str(v or ""))
    if m:
        try:
            return _dt.date(int(m[1]), int(m[2]), 1).isoformat()
        except ValueError:
            pass
    return str(fallback or _today())


def _norm(text):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9$%.+\- ]", " ", str(text or "").lower())).strip()


def entity_key(kind, name):
    return f"{kind}:{str(name).strip()}"


def T(ticker):
    return entity_key("T", str(ticker).upper())


def C(cluster):
    return entity_key("C", cluster)


def safe_name(key):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", key)


def obs_id(entities, kind, topic, text):
    blob = "|".join([",".join(sorted(entities)), kind, str(topic or ""), _norm(text)])
    return hashlib.sha1(blob.encode()).hexdigest()[:12]


def cap_text(text, n=TEXT_CAP):
    t = re.sub(r"\s+", " ", str(text or "")).strip()
    return t if len(t) <= n else t[: n - 1] + "…"


def make_obs(entities, kind, text, *, topic=None, value=None, source=None, as_of=None, confidence="unverified",
             agent=None, run=None, meta=None):
    """Build one `add` event. `value` is structured (e.g. a thesis status or a rank) so timelines can be drawn."""
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}")
    ents = sorted({e for e in (entities or []) if e})
    if not ents or not str(text or "").strip():
        raise ValueError("an observation needs at least one entity and some text")
    ev = {"op": "add", "id": obs_id(ents, kind, topic, text if value is None else f"{text}|{json.dumps(value, sort_keys=True)}"),
          "entities": ents, "kind": kind, "text": cap_text(text), "as_of": clean_date(as_of),
          "confidence": confidence if confidence in CONFIDENCE_WEIGHT else "unverified"}
    if topic:
        ev["topic"] = topic
    if value is not None:
        ev["value"] = value
    if source:
        ev["source"] = str(source)[:300]
    if agent:
        ev["agent"] = agent
    if run:
        ev["run"] = run
    if meta:
        ev["meta"] = meta
    return ev


# ------------------------------------------------------------------------------------------------- IO
def kb_path(base, name=""):
    return os.path.join(base, KB_DIR, name) if name else os.path.join(base, KB_DIR)


def load_config(base):
    cfg = dict(DEFAULT_CONFIG)
    p = kb_path(base, CFG_FILE)
    if os.path.exists(p):
        try:
            cfg.update(json.load(open(p)))
        except (OSError, ValueError):
            pass
    return cfg


def budget_for(base, agent):
    cfg = load_config(base)
    return int((cfg.get("per_agent") or {}).get(agent) or cfg.get("default_tokens") or 5000)


def read_events(base):
    p = kb_path(base, OBS_FILE)
    out = []
    if not os.path.exists(p):
        return out
    with open(p) as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    continue
    return out


def append_events(base, events):
    if not events:
        return 0
    os.makedirs(kb_path(base), exist_ok=True)
    with open(kb_path(base, OBS_FILE), "a") as fh:
        for e in events:
            fh.write(json.dumps(e, separators=(",", ":"), ensure_ascii=False) + "\n")
    return len(events)


# -------------------------------------------------------------------------------------------- replay
def replay(events):
    """Materialise the log: {id: obs} with status, confirmations, runs, supersession. Pure and deterministic."""
    kb = {}
    for e in events:
        op, i = e.get("op"), e.get("id")
        if op == "add":
            o = kb.get(i)
            if o is None:
                kb[i] = {**{k: v for k, v in e.items() if k != "op"}, "status": "live", "confirmations": 1,
                         "first_seen": e.get("as_of"), "last_confirmed": e.get("as_of"),
                         "runs": [e["run"]] if e.get("run") else [], "superseded_by": None, "refuted": None,
                         "uses": 0}
            else:                       # the same fact seen again on a later date / run = reinforcement
                run = e.get("run")
                if run and run in o["runs"]:
                    continue
                o["confirmations"] += 1
                o["last_confirmed"] = max(str(o["last_confirmed"]), str(e.get("as_of")))
                if run:
                    o["runs"].append(run)
        elif op == "reinforce" and i in kb:
            o = kb[i]
            if not (e.get("run") and e["run"] in o["runs"]):
                o["confirmations"] += 1
                o["last_confirmed"] = max(str(o["last_confirmed"]), str(e.get("on") or o["last_confirmed"]))
                if e.get("run"):
                    o["runs"].append(e["run"])
        elif op == "revive" and i in kb:
            kb[i]["status"], kb[i]["superseded_by"] = "live", None
            kb[i]["last_confirmed"] = max(str(kb[i]["last_confirmed"]), str(e.get("on") or ""))
            kb[i]["confirmations"] += 1
        elif op == "supersede" and i in kb and e.get("by") != i:
            kb[i]["status"], kb[i]["superseded_by"] = "superseded", e.get("by")
            kb[i]["superseded_on"] = e.get("on")
        elif op == "refute" and i in kb:
            kb[i]["status"] = "refuted"
            kb[i]["refuted"] = {"reason": e.get("reason"), "on": e.get("on"), "by": e.get("by")}
        elif op == "use" and i in kb:
            kb[i]["uses"] += 1
    return kb


# ------------------------------------------------------------------------------------ write helpers
def plan_add(kb, ev):
    """Events to append for one add: the add itself, plus a supersede for the live verdict it replaces
    (same entity set + topic, different id). Returns [] when it is an exact repeat within the same run."""
    evs = []
    existing = kb.get(ev["id"])
    run = ev.get("run")
    slot_verdict = ev["kind"] == "verdict" and ev.get("topic")
    revive = bool(existing and slot_verdict and existing["status"] == "superseded")
    if existing and not revive and run and run in existing["runs"]:
        return []
    if revive:                          # A -> B -> A: the desk went back to an earlier reading
        evs.append({"op": "revive", "id": ev["id"], "on": ev["as_of"], "run": run})
    else:
        evs.append(ev)
    if slot_verdict and (not existing or revive):
        for o in kb.values():
            if (o["status"] == "live" and o["kind"] == "verdict" and o.get("topic") == ev["topic"]
                    and o["entities"] == ev["entities"] and o["id"] != ev["id"]
                    and str(o["as_of"]) <= str(ev["as_of"])):
                evs.append({"op": "supersede", "id": o["id"], "by": ev["id"], "on": ev["as_of"]})
    return evs


def add_observations(base, observations, kb=None, reinforce=True):
    """Append observations (dicts from make_obs). De-duplicates and supersedes. With reinforce=False an
    observation already known is skipped (used when replaying snapshots, where "still present" is not
    a fresh confirmation). Returns a small report."""
    kb = kb if kb is not None else replay(read_events(base))
    out, added, reinforced = [], 0, 0
    for ev in observations:
        if not reinforce and ev["id"] in kb and not (ev["kind"] == "verdict" and ev.get("topic")
                                                      and kb[ev["id"]]["status"] == "superseded"):
            continue
        evs = plan_add(kb, ev)
        if not evs:
            continue
        if ev["id"] in kb:
            reinforced += 1
        else:
            added += 1
        out.extend(evs)
        _apply(kb, evs)
    append_events(base, out)
    return {"added": added, "reinforced": reinforced, "events": len(out)}


def _apply(kb, evs):
    """Fold events into an already-materialised kb (cheap incremental replay)."""
    for e in evs:
        i, op = e.get("id"), e.get("op")
        if op == "add":
            if i in kb:
                run = e.get("run")
                if run and run in kb[i]["runs"]:
                    continue
                kb[i]["confirmations"] += 1
                kb[i]["last_confirmed"] = max(str(kb[i]["last_confirmed"]), str(e.get("as_of")))
                if run:
                    kb[i]["runs"].append(run)
            else:
                kb[i] = {**{k: v for k, v in e.items() if k != "op"}, "status": "live", "confirmations": 1,
                         "first_seen": e.get("as_of"), "last_confirmed": e.get("as_of"),
                         "runs": [e["run"]] if e.get("run") else [], "superseded_by": None, "refuted": None,
                         "uses": 0}
        elif op == "revive" and i in kb:
            kb[i]["status"], kb[i]["superseded_by"] = "live", None
            kb[i]["last_confirmed"] = max(str(kb[i]["last_confirmed"]), str(e.get("on") or ""))
            kb[i]["confirmations"] += 1
        elif op == "supersede" and i in kb:
            kb[i]["status"], kb[i]["superseded_by"], kb[i]["superseded_on"] = "superseded", e.get("by"), e.get("on")
        elif op == "refute" and i in kb:
            kb[i]["status"], kb[i]["refuted"] = "refuted", {"reason": e.get("reason"), "on": e.get("on"), "by": e.get("by")}
    return kb


def done_keys(events):
    """Batches already folded in (op `batch_done`): re-running a backfill or a run harvest is a no-op."""
    return {e.get("key") for e in events if e.get("op") == "batch_done"}


def mark_done(base, key):
    append_events(base, [{"op": "batch_done", "key": key, "on": str(_today())}])


def refute(base, obs_ids, reason, by=None, on=None):
    kb = replay(read_events(base))
    evs = [{"op": "refute", "id": i, "reason": cap_text(reason, 300), "by": by, "on": str(on or _today())}
           for i in obs_ids if i in kb and kb[i]["status"] != "refuted"]
    append_events(base, evs)
    return len(evs)


def record_use(base, obs_ids, run=None, on=None):
    kb = replay(read_events(base))
    evs = [{"op": "use", "id": i, "run": run, "on": str(on or _today())} for i in obs_ids if i in kb]
    append_events(base, evs)
    return len(evs)


# ----------------------------------------------------------------------------------------- ranking
def salience(o, today):
    """Retrieval weight: confidence tier x confirmation count x half-life decay. Not a truth score."""
    age = max(0, (_today(today) - _today(o.get("last_confirmed") or o.get("as_of"))).days)
    hl = HALF_LIFE_DAYS.get(o["kind"], 60)
    base = CONFIDENCE_WEIGHT.get(o.get("confidence"), 0.5) * (1.0 + math.log(1 + o.get("confirmations", 1)))
    base *= KIND_WEIGHT.get(o["kind"], 1.0) * TOPIC_WEIGHT.get(o.get("topic"), 1.0)
    return base * (0.5 ** (age / hl))


def graph(kb, today):
    """Derived connections {a|b: weight}. Weight = sum of salience of the relation observations linking the pair
    (strengthens each time a run re-confirms it, decays with time). Only live relations count."""
    edges = {}
    for o in kb.values():
        if o["kind"] != "relation" or o["status"] != "live":
            continue
        ents = o["entities"]
        for i in range(len(ents)):
            for j in range(i + 1, len(ents)):
                k = "|".join(sorted((ents[i], ents[j])))
                edges[k] = edges.get(k, 0.0) + salience(o, today)
    return {k: round(v, 4) for k, v in sorted(edges.items(), key=lambda kv: -kv[1])}


def neighbours(edges, entity, top=6):
    out = []
    for k, w in edges.items():
        a, b = k.split("|")
        if entity in (a, b):
            out.append((b if a == entity else a, w))
    return [n for n, _ in sorted(out, key=lambda x: -x[1])[:top]]


def _tokens(s):
    return max(1, len(s) // 4)


def render_line(o):
    ents = ",".join(e.split(":", 1)[-1] for e in o["entities"][:3])
    v = f" ={o['value']}" if o.get("value") not in (None, "") and not isinstance(o.get("value"), (dict, list)) else ""
    conf = "" if o.get("confidence") in ("primary", "verified", "computed") else f" [{o.get('confidence')}]"
    seen = f"x{o['confirmations']}" if o.get("confirmations", 1) > 1 else ""
    return (f"[{o['id']}] {o['kind']}{('/' + o['topic']) if o.get('topic') else ''} {ents}{v} "
            f"({o['as_of']}{(' ' + seen) if seen else ''}){conf}: {o['text']}")


def retrieve(kb, entities, budget_tokens, today, *, focus=(), cfg=None, exclude_ids=()):
    """The memory an agent gets: the most salient LIVE observations about `entities` (and their strongest
    neighbours), filled greedily into `budget_tokens`, plus what changed recently. Returns a dict."""
    cfg = cfg or DEFAULT_CONFIG
    today = _today(today)
    ents = list(dict.fromkeys(entities))
    edges = graph(kb, today)
    weight = {e: 1.0 for e in ents}
    for e in ents:
        for n in neighbours(edges, e):
            weight.setdefault(n, cfg["neighbour_weight"])
    focus = set(focus or ())
    scored = []
    for o in kb.values():
        if o["id"] in exclude_ids:
            continue
        live = o["status"] == "live"
        if not live and not (o["kind"] == "tension" and o["status"] != "refuted"):
            continue
        rel = max((weight.get(e, 0.0) for e in o["entities"]), default=0.0)
        if not rel:
            continue
        s = salience(o, today) * rel * (1.5 if focus & set(o["entities"]) else 1.0)
        if o["kind"] in ("tension", "correction"):
            s *= 1.3                     # unresolved disagreements and corrections matter more than their age
        scored.append((s, o))
    scored.sort(key=lambda x: -x[0])
    used, items, ids = 0, [], []
    for s, o in scored:
        line = render_line(o)
        t = _tokens(line)
        if used + t > budget_tokens:
            continue
        used += t
        items.append(line)
        ids.append(o["id"])
    horizon = today - _dt.timedelta(days=cfg.get("recent_change_days", 14))
    changed = []
    for o in kb.values():
        ch = None
        if o["status"] == "superseded" and str(o.get("superseded_on") or "") >= horizon.isoformat():
            ch = f"superseded by {o['superseded_by']}"
        elif o["status"] == "refuted" and str((o.get("refuted") or {}).get("on") or "") >= horizon.isoformat():
            ch = f"REFUTED: {(o['refuted'] or {}).get('reason')}"
        if ch and set(o["entities"]) & set(weight):
            line = f"[{o['id']}] {ch} -- was: {cap_text(o['text'], 160)}"
            if used + _tokens(line) <= budget_tokens:
                used += _tokens(line)
                changed.append(line)
    return {"budget_tokens": budget_tokens, "used_tokens": used, "n_items": len(items), "items": items,
            "changed_recently": changed, "ids": ids,
            "entities": ents, "neighbours_pulled": [e for e in weight if e not in ents][:10]}


# ----------------------------------------------------------------------------------- entity pages
def entity_page(kb, entity, today):
    obs = [o for o in kb.values() if entity in o["entities"]]
    topics = {}
    for o in sorted(obs, key=lambda x: (str(x["as_of"]), x["id"])):
        if o["kind"] == "verdict" and o.get("topic"):
            topics.setdefault(o["topic"], []).append({"as_of": o["as_of"], "value": o.get("value"),
                                                      "status": o["status"], "id": o["id"], "text": cap_text(o["text"], 160)})
    live = sorted((o for o in obs if o["status"] == "live" and o["kind"] != "verdict"),
                  key=lambda o: -salience(o, today))
    return {"entity": entity, "as_of": str(_today(today)), "n_observations": len(obs),
            "timelines": topics,
            "live_facts": [render_line(o) for o in live[:25]],
            "open_tensions": [render_line(o) for o in obs if o["kind"] == "tension" and o["status"] == "live"][:10],
            "refuted": [{"id": o["id"], "reason": (o.get("refuted") or {}).get("reason"), "text": cap_text(o["text"], 120)}
                        for o in obs if o["status"] == "refuted"][:10]}


def rebuild_pages(base, today, only=None):
    """Write knowledge/entities/*.json (+ graph.json). Skips writing when a page is unchanged."""
    kb = replay(read_events(base))
    ents = sorted({e for o in kb.values() for e in o["entities"]})
    os.makedirs(kb_path(base, "entities"), exist_ok=True)
    wrote = 0
    for e in ents:
        if only and e not in only:
            continue
        page = entity_page(kb, e, today)
        page.pop("as_of")
        p = kb_path(base, os.path.join("entities", safe_name(e) + ".json"))
        new = json.dumps(page, indent=1, sort_keys=True, ensure_ascii=False)
        if os.path.exists(p) and open(p).read() == new:
            continue
        with open(p, "w") as fh:
            fh.write(new)
        wrote += 1
    g = json.dumps(graph(kb, today), indent=1, ensure_ascii=False)
    gp = kb_path(base, "graph.json")
    if not os.path.exists(gp) or open(gp).read() != g:
        open(gp, "w").write(g)
    return {"entities": len(ents), "pages_written": wrote, "observations": len(kb)}


def search(kb, text, today, limit=15):
    """Plain substring search over ALL observations (live, superseded and refuted) -- nothing is ever lost."""
    q = _norm(text)
    hits = [o for o in kb.values() if q in _norm(o["text"]) or q in _norm(" ".join(o["entities"]))]
    hits.sort(key=lambda o: (o["status"] != "live", -salience(o, today)))
    return [{"status": o["status"], "line": render_line(o)} for o in hits[:limit]]
