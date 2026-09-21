"""Backfill the knowledge base from what already exists (2026-09-21): the committed state.json history in git
(each version is a snapshot of every thesis, ladder and catalyst the desk held that day), findings.json history
(recovers findings that expired), pruned run directories in git, and the runs still on disk.

Every source is collected as a TIMESTAMPED batch and inserted in strict time order, so "the latest verdict"
is decided by when it was written, never by which source happened to be read last. Idempotent: an
observation already known is skipped."""
import datetime as _dt
import json
import os
import subprocess

import smith_kb as K
import smith_kb_harvest as H


def _git(base, *args):
    r = subprocess.run(["git", "-C", base, *args], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def _utc(iso):
    try:
        return _dt.datetime.fromisoformat(iso).astimezone(_dt.timezone.utc).isoformat()
    except ValueError:
        return iso


def _commits(base, path):
    """(sha, day, utc_timestamp) oldest first."""
    out = _git(base, "log", "--reverse", "--format=%H %aI", "--", path)
    res = []
    for l in out.splitlines():
        if " " in l:
            sha, iso = l.split(" ", 1)
            res.append((sha, iso[:10], _utc(iso)))
    return res


def _show(base, sha, path):
    txt = _git(base, "show", f"{sha}:{path}")
    try:
        return json.loads(txt) if txt else None
    except ValueError:
        return None


def _batches_state(base):
    for sha, day, ts in _commits(base, "state.json"):
        st = _show(base, sha, "state.json")
        if isinstance(st, dict):
            yield ts, 9, H.from_state_snapshot(st, day, run=f"git:{sha[:7]}"), "state"


def _batches_findings(base):
    for sha, day, ts in _commits(base, "findings.json"):
        doc = _show(base, sha, "findings.json")
        if isinstance(doc, dict):
            yield ts, 5, H.from_findings_doc(doc, day, run=f"git:{sha[:7]}"), "findings"


def _batches_git_runs(base):
    """Tails of runs since pruned from disk, read from the commit that added them (tails sort BEFORE the state
    snapshot of the same commit, which is the merged, final truth)."""
    out = _git(base, "log", "--diff-filter=A", "--name-only", "--format=@@%H %aI", "--",
               "runs/*/out_*.json", "runs/*/comms/digest.json", "runs/*/findings_orchestrator.json")
    sha = ts = None
    files = []
    for line in out.splitlines():
        if line.startswith("@@"):
            sha, iso = line[2:].split(" ", 1)
            ts = _utc(iso)
        elif line.strip() and sha:
            parts = line.split("/")
            if len(parts) >= 3:
                files.append((ts, sha, parts[1], line.strip()))
    def order(f):
        ts, sha, run_id, path = f
        return (ts, run_id, H._round_no(os.path.basename(path)[:-5]), path)

    for ts, sha, run_id, path in sorted(files, key=order):
        doc = _show(base, sha, path)
        if doc is None:
            continue
        name, as_of = os.path.basename(path), run_id[:10]
        if name == "digest.json":
            obs = H._safe(H.from_comms_digest, doc, as_of, run_id)
        elif name == "findings_orchestrator.json":
            obs = H.from_findings_doc({"findings": [{"subject": f.get("subject"), "claim": f.get("claim"), "source": f.get("source"),
                                                      "kind": "orchestrator", "as_of": as_of} for f in doc if isinstance(f, dict)]}, as_of, run_id)
        else:
            obs = H.harvest_tail(name[4:-5].split(".")[0], doc, as_of, run_id)
        yield ts, 3, obs, f"{run_id}/{H._round_no(name[:-5]):03d}/{name}"


def _batches_local_runs(base):
    rdir = os.path.join(base, "runs")
    for run_id in sorted(os.listdir(rdir)) if os.path.isdir(rdir) else []:
        rd = os.path.join(rdir, run_id)
        if os.path.isdir(rd):
            for ts, obs, name in H.run_batches(base, rd, run_id, run_id[:10]):
                yield ts, 4, obs, f"{run_id}/{H._round_no(name):03d}/{name}"


def _batches_archives(base):
    ex = os.path.join(base, "exited-holdings-archive.json")
    if os.path.exists(ex):
        doc = json.load(open(ex))
        for t, e in (doc.get("thesis") or {}).items():
            if isinstance(e, dict):
                yield "2000-01-01T00:00:00+00:00", 1, H.thesis_obs(t, e, e.get("reviewed_on") or doc.get("as_of") or "2026-09-01",
                                                                    run="archive"), "exited-archive"
    lp = os.path.join(base, "learning.json")
    if os.path.exists(lp):
        doc = json.load(open(lp))
        for l in (doc.get("lessons") or []):
            if isinstance(l, dict) and (l.get("text") or l.get("lesson")):
                obs = []
                H._mk(obs, [K.entity_key("M", "desk")], "lesson", l.get("text") or l.get("lesson"),
                      as_of=l.get("date") or l.get("added_on") or "2026-08-25", confidence="secondary", agent="desk", run="learning")
                yield "2000-01-01T00:00:01+00:00", 1, obs, "learning"


def backfill_all(base, use_git=True):
    batches = list(_batches_archives(base))
    if use_git:
        batches += list(_batches_state(base)) + list(_batches_findings(base)) + list(_batches_git_runs(base))
    batches += list(_batches_local_runs(base))
    batches.sort(key=lambda b: (b[0], b[1], b[3]))         # time, then tails-before-state within a commit
    kb = K.replay(K.read_events(base))
    rep = {"batches": len(batches), "added_by_source": {}}
    for ts, _, obs, label in batches:
        r = K.add_observations(base, obs, kb, reinforce=False)
        src = label.split("/")[-1] if "/" in label else label
        rep["added_by_source"][src.split(".")[0] if src.startswith("out_") else src] = \
            rep["added_by_source"].get(src.split(".")[0] if src.startswith("out_") else src, 0) + r["added"]
    rep["observations"] = len(K.replay(K.read_events(base)))
    return rep
