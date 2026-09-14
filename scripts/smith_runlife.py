"""Run lifecycle commands (added 2026-09-14): lock, commit-state, health, memory-summary,
preflight, abort.

These replace orchestrator prose that an LLM used to execute by hand -- writing and ageing a lock
file, reading ~1MB of state files at MEMORY load, deciding whether a scheduled run silently died,
and cleaning up after a connector outage. Each is now one deterministic call.
"""
import contextlib
import io
import json
import os
from datetime import timedelta, timezone
import subprocess
from argparse import Namespace

from smith_core import *  # noqa: F401,F403
import smith_risk
import smith_state as ss

BAD_RUN_VERDICTS = ("MISSING", "FIRED_BUT_NO_LEDGER_ROW", "LEDGER_ROW_WITHOUT_RUN_DIR",
                    "WEEKLY_NO_DEEP_RUN")
LEDGER_SILENCE_H = 96          # Friday evening -> Monday pre-market is ~70h; 96h is a real gap
WATCHDOG_HOUR_IST = 16   # launchd com.agentsmith.health fires weekdays 16:00 local (IST)
OPEN_PROPOSAL_STATUSES = ("open", "accepted_by_user", "deferred", "watch")


def _capture(fn, **kw):
    """Run a cmd_* function in-process and return its emitted JSON (last stdout line)."""
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            fn(Namespace(**kw))
    except SystemExit:
        pass
    lines = [l for l in buf.getvalue().strip().splitlines() if l.strip()]
    try:
        return json.loads(lines[-1])
    except (ValueError, IndexError):
        return {"error": "unparseable output", "raw": buf.getvalue()[-300:]}


# ---------------------------------------------------------------------------------------------
# health
# ---------------------------------------------------------------------------------------------
def _mirror_status(base_dir):
    live_skill = os.environ.get("SMITH_LIVE_SKILL_DIR",
                                os.path.expanduser("~/.claude/skills/agent-smith"))
    live_agents = os.environ.get("SMITH_LIVE_AGENTS_DIR", os.path.expanduser("~/.claude/agents"))
    mirror = os.path.join(base_dir, "skill")
    if not (os.path.isdir(live_skill) and os.path.isdir(mirror)):
        return {"checked": False}
    pairs = [(os.path.join(live_skill, "SKILL.md"), os.path.join(mirror, "SKILL.md"))]
    for sub_live, sub_mirror, prefix in ((os.path.join(live_skill, "reference"),
                                          os.path.join(mirror, "reference"), ""),
                                         (live_agents, os.path.join(mirror, "agents"), "smith-")):
        names = set()
        for d in (sub_live, sub_mirror):
            if os.path.isdir(d):
                names |= {f for f in os.listdir(d) if f.endswith(".md") and f.startswith(prefix)}
        pairs += [(os.path.join(sub_live, n), os.path.join(sub_mirror, n)) for n in sorted(names)]

    def read(p):
        try:
            with open(p, "rb") as fh:
                return fh.read()
        except OSError:
            return None

    differ = [os.path.relpath(m, mirror) for l, m in pairs if read(l) != read(m)]
    return {"checked": True, "stale": bool(differ), "differs": differ[:8]}


def _last_ledger_row(base_dir):
    try:
        with open(os.path.join(base_dir, "ledger.csv")) as fh:
            import csv
            rows = list(csv.DictReader(fh))
        return rows[-1] if rows else None
    except OSError:
        return None


def health(base_dir, now=None):
    from smith_memory import evaluate_runs
    now = now or now_utc()
    today = desk_today(now)
    rows = evaluate_runs(base_dir, today, days=10)
    missed = [{"date": r["date"], "weekday": r["weekday"], "verdict": r["verdict"],
               "expected": r["expected"]}
              for r in rows if r["verdict"] in BAD_RUN_VERDICTS and r["date"] != today.isoformat()]
    lock = ss.lock_status(base_dir, now)
    last = _last_ledger_row(base_dir)
    last_dt = parse_ts(last.get("ts")) if last else None
    ledger_age_h = round((now - last_dt).total_seconds() / 3600.0, 1) if last_dt else None
    pending = ss.uncommitted_runs(base_dir)
    mirror = _mirror_status(base_dir)
    today_row = next((r for r in rows if r["date"] == today.isoformat()), None)
    ist_now = now.astimezone(timezone(timedelta(hours=5, minutes=30)))

    problems = []
    # evaluate_runs calls today "pending" all day. The 16:00 IST watchdog exists precisely to
    # catch TODAY's run never firing, so past the watchdog hour a pending weekday is a problem.
    if (today_row and today_row["verdict"] == "pending" and today_row["expected"]
            and ist_now.hour >= WATCHDOG_HOUR_IST):
        problems.append(f"today's scheduled run ({', '.join(today_row['expected'])}) has left no run "
                        f"directory and no ledger row by {WATCHDOG_HOUR_IST}:00 IST")
    if missed:
        problems.append(f"{len(missed)} scheduled run(s) in the last 10 days left no or partial "
                        f"artefacts: " + ", ".join(f"{m['date']} {m['verdict']}" for m in missed[:5]))
    if lock["held"] and lock["stale"]:
        problems.append(f"stale {lock['kind']} run lock (age {lock['age_min']} min, heartbeat "
                        f"{lock['heartbeat_age_min']} min) -- a run died holding it")
    if ledger_age_h is None or ledger_age_h > LEDGER_SILENCE_H:
        problems.append(f"no ledger row for {ledger_age_h} h -- the desk has not completed a run")
    if last_dt and last_dt > now:
        problems.append(f"newest ledger row is stamped in the FUTURE ({last.get('ts')})")
    if pending:
        problems.append(f"uncommitted staged state in {', '.join(pending)} -- a run died before "
                        f"commit-state; recover with `commit-state --run-dir runs/<dir>` or "
                        f"`abort --run-dir runs/<dir>`")
    if mirror.get("stale"):
        problems.append(f"skill/ mirror differs from live config ({', '.join(mirror['differs'][:4])}) "
                        f"-- run skill/sync-from-live.sh")
    return {"ok": not problems, "as_of": iso_utc(now), "problems": problems,
            "headline": ("Health: ok." if not problems else
                         f"Health: {len(problems)} problem(s) -- {problems[0]}"),
            "missed_runs": missed, "lock": lock, "last_ledger_row_age_h": ledger_age_h,
            "uncommitted_runs": pending, "mirror": mirror}


def write_health_snapshot(base_dir, h):
    """The dashboard reads the newest health result from here (never recomputes it: a build must
    not depend on the wall clock or on ~/.claude)."""
    try:
        atomic_write_json(os.path.join(base_dir, "health.json"), h)
    except OSError:
        pass


def cmd_health(args):
    h = health(args.base_dir)
    write_health_snapshot(args.base_dir, h)
    if getattr(args, "notify", False) and not h["ok"]:
        msg = h["headline"].replace('"', "'")[:230]
        try:
            subprocess.run(["osascript", "-e",
                            f'display notification "{msg}" with title "Agent Smith health"'],
                           timeout=10, check=False, capture_output=True)
            h["notified"] = True
        except (OSError, subprocess.SubprocessError):
            h["notified"] = False
    emit(h)


# ---------------------------------------------------------------------------------------------
# memory summary -- what the orchestrator needs at MEMORY load, instead of ~1MB of raw files
# ---------------------------------------------------------------------------------------------
def _gap_title(g):
    for k in ("title", "summary", "description", "gap", "text"):
        if isinstance(g.get(k), str):
            return g[k][:110]
    return ""


def memory_summary(base_dir):
    state = load_json(os.path.join(base_dir, "state.json"), default={}) or {}
    props_file = load_json(os.path.join(base_dir, "proposals.json"), default={}) or {}
    policy = load_json(os.path.join(base_dir, "policy.json"), default={}) or {}
    rows = []
    try:
        import csv
        with open(os.path.join(base_dir, "ledger.csv")) as fh:
            rows = list(csv.DictReader(fh))[-3:]
    except OSError:
        pass
    props = [p for p in (props_file.get("proposals") or []) if isinstance(p, dict)
             and p.get("status") in OPEN_PROPOSAL_STATUSES]
    scorecard = {k: v for k, v in (props_file.get("scorecard") or {}).items()
                 if isinstance(v, (int, float, str)) and not isinstance(v, bool)}
    us = state.get("us") or {}
    return {
        "state_ts": state.get("ts"), "mode": state.get("mode"),
        "latest_run_dir": state.get("latest_run_dir") or state.get("last_run_dir"),
        "artifact_url": state.get("artifact_url"),
        "dashboard_last_synced_ts": state.get("dashboard_last_synced_ts"),
        "news_watermark": state.get("news_watermark"),
        "us": {k: us.get(k) for k in ("value_usd", "wallet_usd", "pnl_pct", "count", "top3",
                                      "peak_value_usd", "beta") if k in us},
        "ledger_tail": [{"ts": r.get("ts"), "mode": r.get("mode"), "value_usd": r.get("value_usd"),
                         "wallet_usd": r.get("wallet_usd"), "value_trust": r.get("value_trust"),
                         "notes": (r.get("notes") or "")[:160]} for r in rows],
        "open_proposals": [{"id": p.get("id"), "action": p.get("action"), "ticker": p.get("ticker"),
                            "size_usd": p.get("size_usd"), "priority": p.get("priority"),
                            "status": p.get("status"), "date": str(p.get("date"))[:10]}
                           for p in props][:30],
        "open_proposal_count": len(props),
        "scorecard": scorecard,
        "live_gaps": [{"id": g.get("id"), "title": _gap_title(g)}
                      for g in (state.get("known_gaps") or [])
                      if isinstance(g, dict) and smith_risk.gap_is_live(g)][:15],
        "open_flags_count": len(state.get("open_flags") or []),
        "cycle_position": state.get("cycle_position"),
        "fomc_next": (state.get("fomc_cache") or {}).get("next_meeting"),
        "policy": {"confirmed": policy.get("confirmed"), "as_of": policy.get("as_of")},
        "note": "Summary only. Scripts read the full files; do not Read state.json or "
                "proposals.json wholesale into context.",
    }


def cmd_memory_summary(args):
    emit(memory_summary(args.base_dir))


# ---------------------------------------------------------------------------------------------
# lock / commit-state
# ---------------------------------------------------------------------------------------------
def cmd_lock(args):
    if args.action == "acquire":
        emit(ss.lock_acquire(args.base_dir, args.run_id or run_label(), args.mode, args.run_dir))
    elif args.action == "heartbeat":
        emit(ss.lock_heartbeat(args.base_dir, args.run_id, args.run_dir))
    elif args.action == "release":
        emit(ss.lock_release(args.base_dir, args.run_id, force=args.force))
    else:
        emit(ss.lock_status(args.base_dir))


def cmd_commit_state(args):
    flag = {"auto": None, "true": True, "false": False}[args.persist_safe]
    emit(ss.commit_state(args.base_dir, args.run_dir, persist_safe=flag))


# ---------------------------------------------------------------------------------------------
# preflight / abort
# ---------------------------------------------------------------------------------------------
def _health_snap(base):
    h = health(base)
    write_health_snapshot(base, h)
    return h


def cmd_preflight(args):
    from smith_memory import cmd_validate, cmd_freshness
    import smith_learning
    base = args.base_dir
    run_id = args.run_id or run_label()
    lock = ss.lock_acquire(base, run_id, args.mode, args.run_dir)
    if not lock["acquired"]:
        emit({"proceed": False, "run_id": run_id, "lock": lock,
              "instruction": "another sweep holds the run lock -- say so in one line and stop"})
        return
    val = _capture(cmd_validate, base_dir=base)
    rd = args.run_dir if (args.run_dir and os.path.isdir(args.run_dir)) else None
    fr = _capture(cmd_freshness, base_dir=base, run_dir=rd, today=args.today)
    rows = fr.get("rows") or fr.get("artefacts") or []
    not_fresh = [r for r in rows if isinstance(r, dict) and r.get("state") not in (None, "fresh")]
    lessons = sorted((l for l in (smith_learning.load_store(base).get("lessons") or [])
                      if l.get("kind") == "correction"),
                     key=lambda l: l.get("date") or "", reverse=True)[:8]
    emit({
        "proceed": True, "run_id": run_id,
        "lock": {k: lock.get(k) for k in ("acquired", "stolen", "reentrant")},
        "health": _health_snap(base),
        "validate": {"defect_count": val.get("defect_count"),
                     "defects": [str(d)[:220] for d in (val.get("defects") or [])[:12]]},
        "freshness": {"headline": fr.get("headline"),
                      "not_fresh": [{k: r.get(k) for k in ("artefact", "key", "state", "age_days")
                                     if k in r} for r in not_fresh][:15]},
        "lessons": [{"id": l.get("id"), "date": l.get("date"), "text": (l.get("text") or "")[:160]}
                    for l in lessons],
        "memory": memory_summary(base),
        "release_with": f"python3 scripts/smith_math.py lock release --run-id {run_id}",
    })


def cmd_abort(args):
    from smith_memory import cmd_runs
    base = args.base_dir
    today = resolve_today(args.today)
    out = {"aborted": True, "reason": args.reason, "kind": args.kind, "utc": iso_utc()}
    rd = args.run_dir
    if rd and os.path.isdir(rd):
        pend = ss.pending_path(rd)
        if os.path.exists(pend):
            os.replace(pend, os.path.join(rd, "state.pending.aborted.json"))
            out["discarded_pending"] = True
        atomic_write_json(os.path.join(rd, "ABORTED.json"), out)
    if args.kind in ("connector", "host"):
        out["outage"] = _capture(cmd_runs, base_dir=base, days=10, today=str(today),
                                 declare_outage=f"{today}:{today}",
                                 reason=f"{args.kind}: {args.reason}")
    report = os.path.join(base, "reports", "daily", f"{today}.md")
    if not os.path.exists(report):
        os.makedirs(os.path.dirname(report), exist_ok=True)
        atomic_write_text(report, f"# Agent Smith — daily · {today}\n\n"
                                  f"**Run aborted** ({args.kind}) at {out['utc']}: {args.reason}\n\n"
                                  f"No analysis this run. The memory of record was not changed.\n")
        out["report_stub"] = os.path.relpath(report, base)
    lock = ss.lock_status(base)
    holder = lock.get("holder") or {}
    mine = lock["held"] and (
        (args.run_id and holder.get("run_id") == args.run_id) or
        (rd and holder.get("run_dir") == os.path.basename(os.path.normpath(rd))) or
        lock.get("kind") == "legacy")
    out["lock"] = (ss.lock_release(base, holder.get("run_id"), force=True) if mine
                   else {"released": False, "reason": "no lock owned by this run"})
    emit(out)
