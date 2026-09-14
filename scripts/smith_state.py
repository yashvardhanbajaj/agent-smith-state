"""Run-scoped state transaction and the script-owned run lock (added 2026-09-14).

WHY. Until now every `merge-tails` call wrote state.json immediately, once per wave. A run that
died after Wave 1 therefore left the memory of record half-updated -- thesis, signal history and
an advanced `news_watermark` from a run that never briefed anyone -- and the next run treated
that news as already seen. The persist gate could not help: it only guarded the final PERSIST
write, long after the merges had landed.

THE TRANSACTION. Mid-run writers STAGE into `runs/<ts>/state.pending.json`, a top-level-key patch
(`set` / `unset`). Readers that run inside the same run call `load_state(base, run_dir)` and see
state.json with the patch applied (read-your-writes). `commit_state` applies the patch to the
CURRENT state.json under the shared write lock, so writers that touched other keys in the
meantime (sync-decisions, the pipeline's latest_run_dir stamp) are preserved. A run that dies
before committing leaves state.json byte-identical; its pending file stays on disk and `health`
reports it, so nothing is silently lost either.

THE LOCK. `.smith.lock` is created with O_EXCL, carries a heartbeat every run-scoped command
refreshes, and is stale after 45 minutes without a heartbeat or 150 minutes in total. A steal is
recorded in the lock itself, never silent. It replaces the LLM-managed `.running` file (still
honoured while any old-style run could be live).

Imports only smith_core, so any module may import this one.
"""
import os

from smith_core import (atomic_write_json, file_lock, iso_utc, load_json, now_utc, parse_any,
                        safe_write)

PENDING = "state.pending.json"
COMMITTED = "state.committed.json"
# Keys derived from this run's prices. Withheld at commit when compute_book.json says the price
# snapshot failed its sanity gate -- analysis may still be shown, labelled, but never persisted.
PRICE_KEYS = ("us", "holdings", "changes")

LOCK_FILE = ".smith.lock"
LEGACY_LOCK_FILE = ".running"
HEARTBEAT_STALE_MIN = 45
HARD_STALE_MIN = 150
STEALS_CAP = 10

_MISSING = object()


# ---------------------------------------------------------------------------------------------
# state transaction
# ---------------------------------------------------------------------------------------------
def _state_path(base_dir):
    return os.path.join(base_dir, "state.json")


def pending_path(run_dir):
    return os.path.join(run_dir, PENDING)


def load_patch(run_dir):
    patch = load_json(pending_path(run_dir), default=None) if run_dir else None
    if not isinstance(patch, dict):
        return {"set": {}, "unset": [], "staged_by": []}
    patch.setdefault("set", {})
    patch.setdefault("unset", [])
    patch.setdefault("staged_by", [])
    return patch


def apply_patch(state, patch, skip=()):
    for k, v in (patch.get("set") or {}).items():
        if k not in skip:
            state[k] = v
    for k in patch.get("unset") or []:
        if k not in skip:
            state.pop(k, None)
    return state


def load_state(base_dir, run_dir=None):
    """state.json with this run's staged patch applied. `run_dir=None` reads the committed file."""
    state = load_json(_state_path(base_dir), default={}) or {}
    if run_dir and os.path.exists(pending_path(run_dir)):
        apply_patch(state, load_patch(run_dir))
    return state


def stage_state(base_dir, run_dir, new_state, by):
    """Record `new_state` as this run's pending state: the patch is recomputed against the
    committed file, so it always carries every key staged so far this run and nothing else."""
    raw = load_json(_state_path(base_dir), default={}) or {}
    prior = load_patch(run_dir)
    patch = {
        "set": {k: v for k, v in new_state.items() if raw.get(k, _MISSING) != v},
        "unset": sorted(k for k in raw if k not in new_state),
        "staged_by": (prior.get("staged_by") or []) + [{"by": by, "utc": iso_utc()}],
    }
    atomic_write_json(pending_path(run_dir), patch)
    return {"staged_keys": sorted(patch["set"]), "unset_keys": patch["unset"],
            "pending": pending_path(run_dir)}


def commit_state(base_dir, run_dir, persist_safe=None):
    """Apply the pending patch to the current state.json, stamp `ts` and `latest_run_dir`.

    Idempotent: with no pending patch it only re-stamps. `persist_safe=None` reads
    compute_book.json's own verdict; False withholds PRICE_KEYS and says so."""
    if persist_safe is None:
        book = load_json(os.path.join(run_dir, "compute_book.json"), default={}) or {}
        persist_safe = book.get("persist_safe", True) is not False
    with file_lock(base_dir):
        raw = load_json(_state_path(base_dir), default={}) or {}
        has_pending = os.path.exists(pending_path(run_dir))
        patch = load_patch(run_dir)
        withheld = [] if persist_safe else sorted(k for k in PRICE_KEYS if k in patch["set"])
        apply_patch(raw, patch, skip=withheld)
        raw["latest_run_dir"] = os.path.relpath(os.path.realpath(run_dir),
                                                os.path.realpath(base_dir))
        raw["ts"] = iso_utc()
        safe_write(_state_path(base_dir), raw)
        if has_pending:
            os.replace(pending_path(run_dir), os.path.join(run_dir, COMMITTED))
    return {"committed": has_pending, "keys": sorted(k for k in patch["set"] if k not in withheld),
            "unset": patch["unset"], "withheld": withheld, "persist_safe": persist_safe,
            "ts": raw["ts"], "latest_run_dir": raw["latest_run_dir"]}


def uncommitted_runs(base_dir):
    """Run dirs holding a pending patch that was never committed -- a run that died mid-flight."""
    runs = os.path.join(base_dir, "runs")
    if not os.path.isdir(runs):
        return []
    return sorted(d for d in os.listdir(runs) if os.path.exists(os.path.join(runs, d, PENDING)))


# ---------------------------------------------------------------------------------------------
# run lock
# ---------------------------------------------------------------------------------------------
def _minutes_since(ts, now):
    dt = parse_any(ts)
    return None if dt is None else round((now - dt).total_seconds() / 60.0, 1)


def lock_status(base_dir, now=None):
    now = now or now_utc()
    path = os.path.join(base_dir, LOCK_FILE)
    lock = load_json(path, default=None) if os.path.exists(path) else None
    if isinstance(lock, dict):
        age = _minutes_since(lock.get("acquired_utc"), now)
        hb = _minutes_since(lock.get("heartbeat_utc") or lock.get("acquired_utc"), now)
        stale = (age is None or hb is None or hb > HEARTBEAT_STALE_MIN or age > HARD_STALE_MIN)
        return {"held": True, "stale": stale, "kind": "smith", "age_min": age,
                "heartbeat_age_min": hb, "holder": lock}
    legacy = os.path.join(base_dir, LEGACY_LOCK_FILE)
    if os.path.exists(legacy):
        try:
            with open(legacy) as fh:
                raw = fh.read().strip()
        except OSError:
            raw = ""
        age = _minutes_since(raw, now)
        return {"held": True, "stale": age is None or age > HARD_STALE_MIN, "kind": "legacy",
                "age_min": age, "heartbeat_age_min": age, "holder": {"legacy_ts": raw}}
    return {"held": False, "stale": False}


def lock_acquire(base_dir, run_id, mode=None, run_dir=None, now=None):
    now = now or now_utc()
    path = os.path.join(base_dir, LOCK_FILE)
    body = {"run_id": run_id, "mode": mode,
            "run_dir": os.path.basename(os.path.normpath(run_dir)) if run_dir else None,
            "acquired_utc": iso_utc(now), "heartbeat_utc": iso_utc(now), "steals": []}
    with file_lock(base_dir):
        st = lock_status(base_dir, now)
        if st["held"] and not st["stale"]:
            holder = st["holder"]
            if st["kind"] == "smith" and holder.get("run_id") == run_id:
                return {"acquired": True, "reentrant": True, "lock": holder}
            return {"acquired": False, "reason": f"{st['kind']} lock held "
                    f"(age {st['age_min']} min, heartbeat {st['heartbeat_age_min']} min)",
                    "holder": holder}
        if st["held"]:
            prior = st["holder"]
            body["steals"] = ((prior.get("steals") or []) + [{
                "from_run_id": prior.get("run_id") or prior.get("legacy_ts"),
                "kind": st["kind"], "age_min": st["age_min"],
                "heartbeat_age_min": st["heartbeat_age_min"], "stolen_utc": iso_utc(now)}]
            )[-STEALS_CAP:]
            if st["kind"] == "legacy":
                try:
                    os.remove(os.path.join(base_dir, LEGACY_LOCK_FILE))
                except OSError:
                    pass
        atomic_write_json(path, body)
    return {"acquired": True, "stolen": bool(body["steals"]) and st["held"], "lock": body}


def lock_heartbeat(base_dir, run_id=None, run_dir=None, now=None):
    """Refresh the heartbeat of the lock owned by `run_id` (or by the run whose dir is `run_dir`).
    Never touches a lock held by a different run."""
    path = os.path.join(base_dir, LOCK_FILE)
    if not os.path.exists(path):
        return {"refreshed": False, "reason": "no lock"}
    with file_lock(base_dir):
        lock = load_json(path, default=None)
        if not isinstance(lock, dict):
            return {"refreshed": False, "reason": "unreadable lock"}
        mine = ((run_id and lock.get("run_id") == run_id) or
                (run_dir and lock.get("run_dir") == os.path.basename(os.path.normpath(run_dir))))
        if not mine:
            return {"refreshed": False, "reason": "lock held by another run"}
        lock["heartbeat_utc"] = iso_utc(now or now_utc())
        atomic_write_json(path, lock)
    return {"refreshed": True, "heartbeat_utc": lock["heartbeat_utc"]}


def lock_release(base_dir, run_id, force=False):
    path = os.path.join(base_dir, LOCK_FILE)
    with file_lock(base_dir):
        lock = load_json(path, default=None) if os.path.exists(path) else None
        if not isinstance(lock, dict):
            legacy = os.path.join(base_dir, LEGACY_LOCK_FILE)
            if force and os.path.exists(legacy):
                os.remove(legacy)
                return {"released": True, "kind": "legacy"}
            return {"released": False, "reason": "no lock held"}
        if lock.get("run_id") != run_id and not force:
            return {"released": False, "reason": f"lock belongs to run {lock.get('run_id')!r}",
                    "holder": lock}
        os.remove(path)
    return {"released": True, "run_id": lock.get("run_id")}
