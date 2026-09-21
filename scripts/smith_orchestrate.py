"""Orchestration decisions and end-of-run persistence, as code (added 2026-09-14).

Three things SKILL.md used to ask the orchestrator LLM to do by reading prose every run:
  dispatch-plan   which sub-agents run this sweep, in which wave, and why. Every threshold here
                  is the one SKILL.md/deep-mode-dispatch.md already stated -- copied, not retuned.
  triggers-diff   the priced-refresh materiality gate: did the trigger set, the cash-band status or
                  the gate category change since the previous run?
  postflight      PERSIST as two script calls: `commit` (state block, commit-state, journal merge,
                  trigger_journal append, ledger row, reports, DECISIONS.md) and `close` (compact,
                  run-dir pruning, git snapshot, lock release).
"""
import contextlib
import csv
import io
import json
import os
import shutil
import subprocess
import sys
from argparse import Namespace
from datetime import date, datetime, time, timedelta, timezone

from smith_core import *  # noqa: F401,F403
import smith_state as ss

HERE = os.path.dirname(os.path.abspath(__file__))

WAVE = {"catalyst": 1, "signals": 1, "watchlist": 1, "scout": 1, "earnings": 1, "quality": 1,
        # rebound moved to Wave 1 on 2026-09-15: every input it reads is a Wave-0 compute file, so
        # waiting for Wave 1 to land only added latency.
        "rebound": 1, "thesis": 2, "cycle": 2, "strategist": 3}
# THESIS trigger (a): a live price trigger on a held name.
THESIS_LIVE_FAMILIES = ("oversold_reversion", "overbought_distribution", "catalyst_threat", "thesis_break")
MACRO_US10Y_PTS, MACRO_VIX = 0.12, 22.0
CATALYST_SMH_PCT, CATALYST_ASIA_PCT, CATALYST_CLUSTER_PCT = 3.0, 3.0, 4.0
EARNINGS_WINDOW_TRADING_DAYS = 5
CLUSTER_MAX = 3
# Priced-refresh materiality gate, part (a).
MATERIAL_FAMILIES = ("oversold_reversion", "overbought_distribution", "catalyst_threat", "thesis_break", "stretch")
RUNS_KEEP = 10
# DEEP-LITE window (added 2026-09-15, user-approved): a deep run this soon after the previous deep
# run reuses the slow-moving reads (thesis map, watchlist setups, diversifier bench) unless a fact
# says otherwise. Measured: 5 deep runs in 10 days, 09-14 and 09-15 back to back; the 09-15 thesis
# pass cost 178K tokens and changed zero statuses.
DEEP_LITE_HOURS = 48


def _j(path, default=None):
    return load_json(path, default=default)


def _capture(fn, **kw):
    buf = io.StringIO()
    code = 0
    try:
        with contextlib.redirect_stdout(buf):
            fn(Namespace(**kw))
    except SystemExit as e:
        code = e.code or 0
    lines = [l for l in buf.getvalue().strip().splitlines() if l.strip()]
    try:
        out = json.loads(lines[-1]) if lines else {}
    except ValueError:
        out = {"raw": buf.getvalue()[-300:]}
    if code:
        out.setdefault("error", out.get("error") or f"exited {code}")
    return out


def _ledger_rows(base_dir):
    try:
        with open(os.path.join(base_dir, "ledger.csv"), newline="") as fh:
            return list(csv.DictReader(fh))
    except OSError:
        return []


def _held(run_dir):
    h = _j(os.path.join(run_dir, "holdings.json"), {}) or {}
    return {r.get("ticker") for r in (h.get("holdings_inr") or []) if r.get("ticker")}


def _trading_days_until(today, target):
    if target < today:
        return None
    n, d = 0, today
    while d < target:
        d += timedelta(days=1)
        if d.weekday() < 5:
            n += 1
    return n


# ---------------------------------------------------------------------------------------------
# dispatch-plan
# ---------------------------------------------------------------------------------------------
def _deep_lite(base_dir, now, asks):
    last = None
    for r in _ledger_rows(base_dir):
        ts = parse_ts(r.get("ts")) if r.get("mode") == "deep" else None
        if ts and ts < now and (last is None or ts > last):
            last = ts
    if last is None:
        return {"active": False, "reason": "no earlier deep run on the ledger"}
    hours = (now - last).total_seconds() / 3600.0
    info = {"last_deep_ts": last.isoformat(), "hours_since": round(hours, 1), "window_hours": DEEP_LITE_HOURS}
    if "full" in asks:
        return dict(info, active=False, reason="user asked for a full deep run")
    if hours >= DEEP_LITE_HOURS:
        return dict(info, active=False, reason=f"last deep run {hours:.0f}h ago (>= {DEEP_LITE_HOURS}h)")
    return dict(info, active=True, reason=f"last deep run {hours:.1f}h ago (< {DEEP_LITE_HOURS}h)")


def _stale_artefacts(fresh):
    return {str(a.get("key", "")).split(".")[-1] for a in (fresh.get("artefacts") or [])
            if isinstance(a, dict) and a.get("state") in ("stale", "dark", "missing")}


def _live_pairs(trig, held):
    return {(fam, r.get("ticker")) for fam in THESIS_LIVE_FAMILIES for r in ((trig or {}).get(fam) or [])
            if isinstance(r, dict) and r.get("ticker") in held}


def _structural_hits(tail, held, since):
    rows = tail.get("catalysts") if isinstance(tail, dict) else tail
    hits = set()
    for r in rows or []:
        if not isinstance(r, dict) or r.get("horizon") != "structural":
            continue
        try:
            d = date.fromisoformat(str(r.get("date"))[:10])
        except ValueError:
            continue
        if d >= since:
            hits |= held & set(r.get("affects") or [])
    return sorted(hits)


# Ready-made per-agent dispatch prompts (added 2026-09-15, efficiency pass item 7). Each of
# these agents' canned dispatch instruction previously lived only as prose in
# reference/stage1-dispatch.md, re-read and hand-transcribed into the dispatch message every
# run it fired -- rebound's "gate is timing context, not the reason" line, scout's mode
# description, earnings' VERIFY-ONLY framing. Templating them here means the orchestrator can
# use dispatch_prompts[key] verbatim instead of opening that reference section again once the
# agent's dispatch condition is already known to fire the same way each time.
def _dispatch_prompt_rebound(a, gate):
    return (f"Normal mode -- your embedded compute_triggers.json `rebound` block is the "
           f"candidate pool, already screened; diff holdings vs state.json for SL forensics "
           f"only if qty_changes shows exits/trims. State this run's gate_classification "
           f"({gate}) as TIMING CONTEXT ONLY, never as the reason you were dispatched -- the "
           f"actual reason: {'; '.join(a['reasons'])}.")


def _dispatch_prompt_scout(a, gate):
    if a.get("mode") == "macro_only":
        return ("Mode macro_only: tasks 3-5 only (Fed funds/stance, options positioning, "
                "calendar + regime read). Skip session read, sentiment narrative and the "
                "diversifier bench -- an omitted bench is carried forward, never wiped.")
    return "Mode full: all six tasks, including the session read and diversifier bench refresh."


def _dispatch_prompt_earnings(a, gate):
    if a.get("mode") == "verify_only":
        return (f"VERIFY-ONLY pass on {', '.join(a.get('tickers') or [])} -- confirm or correct "
               "the earnings_facts entry now that its reported_date has passed. Do not run a "
               "full earnings read on names outside this list.")
    return None


def _dispatch_prompt_catalyst(a, gate):
    if gate == "ESCALATING":
        return (f"Dispatched on gate={gate} -- fixed <=6-query budget, target <90s. State the "
               "gate reading up front; it IS the trigger here (unlike rebound/scout, where the "
               "gate is context, not the reason).")
    return None


_DISPATCH_PROMPT_TEMPLATES = {"rebound": _dispatch_prompt_rebound, "scout": _dispatch_prompt_scout,
                              "earnings": _dispatch_prompt_earnings, "catalyst": _dispatch_prompt_catalyst}


def dispatch_plan(base_dir, run_dir, mode, asks=(), today=None, now=None):
    today = resolve_today(today)
    if now is None:
        real = now_utc()
        now = real if desk_today(real) == today else datetime.combine(today, time(12, 0), tzinfo=timezone.utc)
    asks = set(asks or ())
    mi = _j(os.path.join(run_dir, "market_inputs.json"), {}) or {}
    trig = _j(os.path.join(run_dir, "compute_triggers.json"), {}) or {}
    ladder = _j(os.path.join(run_dir, "compute_ladder.json"), {}) or {}
    fresh = _j(os.path.join(run_dir, "compute_freshness.json"), {}) or {}
    session = _j(os.path.join(run_dir, "compute_session.json"), {}) or {}
    holdings = _j(os.path.join(run_dir, "holdings.json"), {}) or {}
    state = _j(os.path.join(base_dir, "state.json"), {}) or {}
    held = _held(run_dir)
    dc = state.get("data_cache") or {}
    agents, skipped, scripts = {}, {}, []

    def add(key, reason, agent=None, wave=None, **extra):
        a = agents.setdefault(key, {"agent": agent or f"smith-{key}",
                                    "wave": wave or WAVE.get(key, 2), "reasons": []})
        a["reasons"].append(reason)
        a.update(extra)

    pending = sorted(t for t, f in (dc.get("earnings_facts") or {}).items()
                     if isinstance(f, dict) and f.get("status") == "PENDING"
                     and str(f.get("reported_date") or "9999")[:10] <= today.isoformat())

    add("signals", "every run")
    lite = _deep_lite(base_dir, now, asks) if mode == "deep" else None
    if mode == "deep" and not lite["active"]:
        for k in ("thesis", "watchlist", "catalyst"):
            add(k, "deep roster (mandatory)")
        add("scout", "deep roster (mandatory)", mode="full")
    elif mode == "deep":
        # DEEP-LITE: signals, catalyst, strategist, rebound, earnings, the monthlies and the ladder
        # gate are unchanged. Thesis, watchlist and scout's bench run only on a fact.
        stale_keys = _stale_artefacts(fresh)
        add("catalyst", f"deep-lite roster (last deep run {lite['hours_since']}h ago)")
        if "diversifier_candidates" in stale_keys:
            add("scout", "deep-lite: diversifier bench stale or missing", mode="full")
        else:
            add("scout", "deep-lite: Fed/options/regime only, diversifier bench still fresh", mode="macro_only")
        prev = previous_run_dir(base_dir, run_dir)
        prev_trig = (_j(os.path.join(prev, "compute_triggers.json"), {}) or {}) if prev else {}
        new_live = sorted(_live_pairs(trig, held) - _live_pairs(prev_trig, held))
        if new_live:
            add("thesis", "deep-lite: NEW live trigger since the last run: "
                          + ", ".join(f"{t} {fam}" for fam, t in new_live))
        if "thesis" in stale_keys:
            add("thesis", "thesis artefact stale or dark")
        if pending:
            add("thesis", f"post-print status pending adjudication: {', '.join(pending)}")
        if "thesis" in asks:
            add("thesis", "user asked about a holding's story")
        since = parse_ts(lite["last_deep_ts"]).astimezone(IST).date()
        hits = _structural_hits(_j(os.path.join(run_dir, "out_catalyst.json"), None), held, since)
        if hits:
            add("thesis", f"deep-lite: structural catalyst since {since} on held {', '.join(hits)}")
        if "thesis" not in agents:
            skipped["thesis"] = ("deep-lite: no new live trigger, staleness, pending print, ask or "
                                 f"structural catalyst on a held name since {since}")
        if "watchlist" in asks:
            add("watchlist", "user asked about the watchlist")
        elif "watchlist_setups" in stale_keys:
            add("watchlist", "deep-lite: watchlist setups stale or missing")
        else:
            skipped["watchlist"] = "deep-lite: setups still fresh, no ask"
    else:
        live = sorted({r.get("ticker") for fam in THESIS_LIVE_FAMILIES for r in (trig.get(fam) or [])
                       if isinstance(r, dict) and r.get("ticker") in held})
        if live:
            add("thesis", f"live price trigger on held {', '.join(live)}")
        stale = [a.get("key") for a in (fresh.get("artefacts") or [])
                 if isinstance(a, dict) and str(a.get("key", "")).split(".")[-1] == "thesis"
                 and a.get("state") in ("stale", "dark")]
        if stale:
            add("thesis", "thesis artefact stale or dark")
        if pending:
            add("thesis", f"post-print status pending adjudication: {', '.join(pending)}")
        if "thesis" in asks:
            add("thesis", "user asked about a holding's story")
        if "thesis" not in agents:
            skipped["thesis"] = "no live trigger on a held name, no staleness, no pending print, no ask"
        if "watchlist" in asks:
            add("watchlist", "user asked about the watchlist")
        else:
            skipped["watchlist"] = "quick mode, no explicit ask"
        us10y, vix = mi.get("us10y_change_pts"), mi.get("vix")
        macro = []
        if isinstance(us10y, (int, float)) and abs(us10y) >= MACRO_US10Y_PTS:
            macro.append(f"|us10y_change_pts| {abs(us10y):.3f} >= {MACRO_US10Y_PTS}")
        if isinstance(vix, (int, float)) and vix >= MACRO_VIX:
            macro.append(f"VIX {vix} >= {MACRO_VIX}")
        if macro:
            add("scout", "MACRO trigger: " + "; ".join(macro), mode="macro_only")
        gate = session.get("gate_classification") or holdings.get("gate_classification")
        if gate == "ESCALATING":
            add("catalyst", "gate ESCALATING")
        smh = mi.get("smh_change_pct")
        if isinstance(smh, (int, float)) and abs(smh) >= CATALYST_SMH_PCT:
            add("catalyst", f"SMH {smh:+.2f}%")
        for k, v in (mi.get("asia") or {}).items():
            if isinstance(v, (int, float)) and abs(v) >= CATALYST_ASIA_PCT:
                add("catalyst", f"{k.replace('_change_pct', '')} {v:+.2f}%")
        for c, v in (session.get("cluster_moves_pct") or {}).items():
            if isinstance(v, (int, float)) and abs(v) >= CATALYST_CLUSTER_PCT:
                add("catalyst", f"cluster {c} {v:+.2f}%")
        if "why" in asks:
            add("catalyst", "user asked why something moved")

    cs = trig.get("correction_state")
    # User decision 2026-09-15: rebound_candidates exists FOR pullbacks -- the mildest of the
    # three non-"none" tiers -- so gating dispatch on "correction"/"deep_correction" only meant
    # the screen never refreshed while the book sat in pullback territory (measured: dark 15
    # days straight through several pullback-tier sweeps). All three non-"none" states now fire.
    if cs in ("pullback", "correction", "deep_correction"):
        add("rebound", f"correction_state={cs}")
    if pending:
        add("earnings", f"VERIFY-ONLY: stuck PENDING {', '.join(pending)}", mode="verify_only",
            tickers=pending, model="sonnet")

    if mode == "deep":
        soon = []
        for t in sorted(held):
            e = (dc.get("earnings_calendar") or {}).get(t)
            try:
                d = date.fromisoformat(str((e or {}).get("date"))[:10])
            except ValueError:
                continue
            n = _trading_days_until(today, d)
            if n is not None and n <= EARNINGS_WINDOW_TRADING_DAYS:
                soon.append(f"{t} {d}")
        if soon:
            add("earnings", f"held name(s) report within {EARNINGS_WINDOW_TRADING_DAYS} trading days: "
                            f"{', '.join(soon)}", mode="full")
            agents["earnings"].pop("model", None)
        month = today.strftime("%Y-%m")
        deep_rows = sum(1 for r in _ledger_rows(base_dir) if r.get("mode") == "deep"
                        and (parse_ts(r.get("ts")) and parse_ts(r.get("ts")).astimezone(IST).strftime("%Y-%m") == month)
                        and parse_ts(r.get("ts")).astimezone(IST).date() < today)
        if deep_rows == 0:
            add("cycle", "first deep review of the month")
        elif deep_rows == 1:
            add("quality", "second deep review of the month")
            scripts.append("smith_edgar.py insider-cluster for the top 5 holdings by weight")
        for key in (ladder.get("dispatch_selected") or [])[:CLUSTER_MAX]:
            add(key, "cluster ladder dispatch gate (compute_ladder.json)", agent="smith-cluster", wave=2)
        for row in ladder.get("skipped_fresh") or []:
            if isinstance(row, dict) and row.get("agent"):
                skipped[row["agent"]] = row.get("reason")
        for a in fresh.get("artefacts") or []:
            if isinstance(a, dict) and "hbm" in str(a.get("key", "")) and a.get("state") in ("stale", "dark"):
                scripts.append("hbm-tracker narrow refresh IN PARALLEL with Wave 1 (hbm_tracker past TTL): it must land "
                               "before the Wave-2 re-slice; tell catalyst its HBM snapshot is pre-refresh")
                break
    if "quality" in asks:
        add("quality", "user asked for a quality check")
    if "cycle" in asks:
        add("cycle", "user asked for a cycle read")
    add("strategist", "every run")

    recheck = bool(lite and lite.get("active") and "thesis" not in agents
                   and not os.path.exists(os.path.join(run_dir, "out_catalyst.json")))
    waves = {"1": [], "2": [], "3": []}
    for k, a in agents.items():
        waves[str(a["wave"])].append(k)
    for w in waves.values():
        w.sort()
    gate_now = session.get("gate_classification") or holdings.get("gate_classification")
    dispatch_prompts = {}
    for k, a in agents.items():
        tmpl = _DISPATCH_PROMPT_TEMPLATES.get(k)
        if tmpl:
            txt = tmpl(a, gate_now)
            if txt:
                dispatch_prompts[k] = txt
    return {"mode": mode, "today": today.isoformat(), "waves": waves, "agents": agents,
            "skipped": skipped, "scripts": scripts, "deep_lite": lite,
            "dispatch_prompts": dispatch_prompts,
            "recheck_after_wave1": recheck,
            "merge_after_wave1": ",".join(waves["1"]),
            "reslice_wave2": ",".join(waves["2"]),
            "ledger": ("dispatch smith-ledger only if ledger-parse reports dispatch_agent, or lots "
                       "reports a mismatch or phantom short")}


def cmd_dispatch_plan(args):
    plan = dispatch_plan(args.base_dir, args.run_dir, args.mode, args.ask, args.today)
    # Persisted (2026-09-19) because the desk router needs to know who is still SCHEDULED: a
    # question to an agent that has not run yet is delivered free in its slice, while one to an
    # agent that is not on the roster at all opens a new layer. Without the plan on disk the
    # router cannot tell those apart.
    try:
        with open(os.path.join(args.run_dir, "dispatch_plan.json"), "w") as fh:
            json.dump(plan, fh, indent=2)
    except OSError:
        pass
    emit(plan)


# ---------------------------------------------------------------------------------------------
# triggers-diff
# ---------------------------------------------------------------------------------------------
def material_signature(run_dir):
    trig = _j(os.path.join(run_dir, "compute_triggers.json"), {}) or {}
    pairs = sorted({(fam, r.get("ticker")) for fam in MATERIAL_FAMILIES for r in (trig.get(fam) or [])
                    if isinstance(r, dict) and r.get("ticker")})
    drift = _j(os.path.join(run_dir, "compute_drift.json"), {}) or {}
    cash, band = drift.get("cash_pct"), drift.get("cash_band_pct") or []
    cash_state = (None if cash is None or len(band) != 2 else
                  "below" if cash < band[0] else "above" if cash > band[1] else "inside")
    gate = ((_j(os.path.join(run_dir, "compute_session.json"), {}) or {}).get("gate_classification")
            or (_j(os.path.join(run_dir, "holdings.json"), {}) or {}).get("gate_classification"))
    return {"trigger_pairs": [list(p) for p in pairs], "cash_band": cash_state, "gate": gate}


def previous_run_dir(base_dir, current):
    runs = os.path.join(base_dir, "runs")
    cur = os.path.realpath(current)
    cands = []
    for name in os.listdir(runs) if os.path.isdir(runs) else []:
        p = os.path.join(runs, name)
        if os.path.realpath(p) == cur or not os.path.exists(os.path.join(p, "compute_triggers.json")):
            continue
        dt = parse_any(name)
        cands.append((dt.isoformat() if dt else "", name, p))
    return sorted(cands)[-1][2] if cands else None


def cmd_triggers_diff(args):
    prev = args.prev or previous_run_dir(args.base_dir, args.run_dir)
    cur_sig = material_signature(args.run_dir)
    if not prev:
        emit({"changed": True, "prev": None, "reason": "no previous run with compute_triggers.json",
              "current": cur_sig})
        return
    prev_sig = material_signature(prev)
    a, b = {tuple(p) for p in prev_sig["trigger_pairs"]}, {tuple(p) for p in cur_sig["trigger_pairs"]}
    reasons = []
    if a != b:
        reasons.append("trigger set changed")
    if prev_sig["cash_band"] != cur_sig["cash_band"]:
        reasons.append(f"cash band {prev_sig['cash_band']} -> {cur_sig['cash_band']}")
    if prev_sig["gate"] != cur_sig["gate"]:
        reasons.append(f"gate {prev_sig['gate']} -> {cur_sig['gate']}")
    emit({"changed": bool(reasons), "prev": os.path.relpath(prev, args.base_dir), "reasons": reasons,
          "added": sorted(b - a), "removed": sorted(a - b),
          "cash_band": [prev_sig["cash_band"], cur_sig["cash_band"]],
          "gate": [prev_sig["gate"], cur_sig["gate"]],
          "instruction": ("proceed: score, re-slice and dispatch the strategist" if reasons else
                          "unchanged: skip the strategist; refresh prices, dashboard and ledger only")})


# ---------------------------------------------------------------------------------------------
# postflight
# ---------------------------------------------------------------------------------------------
def _merge_journal(base_dir, run_dir, today):
    cj = _j(os.path.join(run_dir, "compute_journal.json"), None)
    if not isinstance(cj, dict):
        return {"journal": "no compute_journal.json"}
    path = os.path.join(base_dir, "journal.json")
    updated = 0
    with locked_json(path, default={"schema_version": 1, "entries": []}) as box:
        j = box["obj"]
        index = {(e.get("date"), e.get("ticker"), e.get("bucket")): e for e in j.get("entries", [])}
        for u in cj.get("journal_updates") or []:
            e = index.get((u.get("date"), u.get("ticker"), u.get("bucket")))
            if e is None:
                continue
            for k, v in u.items():
                if k not in ("date", "ticker", "bucket") and not k.startswith("_"):
                    if e.get(k) != v:
                        e[k] = v
                        updated += 1
        # The epoch stamp travels with the tables: smith_edge.admissible_bucket_tables refuses any
        # persisted table that lacks the current epoch's stamp (legacy-engine evidence).
        for k in ("bucket_hit_rates", "bucket_hit_rates_7d", "name_bucket_grades",
                  "bucket_rates_epoch", "bucket_rates_window", "legacy_entries_excluded"):
            if k in cj:
                j[k] = cj[k]
        j["last_updated"] = str(today)
    return {"journal_fields_updated": updated}


def _append_shadow_triggers(base_dir, run_dir, today):
    trig = _j(os.path.join(run_dir, "compute_triggers.json"), {}) or {}
    new = [r for r in (trig.get("shadow_new") or []) if isinstance(r, dict)]
    if not new:
        return {"trigger_journal_added": 0}
    path = os.path.join(base_dir, "trigger_journal.json")
    with locked_json(path, default={"schema_version": 1, "entries": []}) as box:
        entries = box["obj"].setdefault("entries", [])
        seen = {(e.get("date"), e.get("ticker"), e.get("trigger_type")) for e in entries}
        added = 0
        for r in new:
            row = dict(r)
            row.setdefault("date", str(today))
            row.setdefault("scored", False)
            key = (row.get("date"), row.get("ticker"), row.get("trigger_type"))
            if key not in seen:
                entries.append(row)
                seen.add(key)
                added += 1
    return {"trigger_journal_added": added}


def _score_shadow_journals(base_dir, run_dir, today):
    """Score trigger_journal.json / derisk_journal.json from the prices this run already holds.

    cmd_score_shadow_journal was implemented (2026-08-25) and sat in no pipeline document:
    trigger_journal.json was 26 days stale with 60 unscored entries, so no shadow family -- including
    one the Phase 4 gate suppresses -- could ever earn its vote back. Prices come from the run's own
    files (score_prices.json, live_quotes.json, book positions); a ticker with none stays unscored and
    is named, never guessed. The scorer locks a verdict on first score, so re-running is idempotent.
    Never blocks a commit."""
    from smith_lifecycle import cmd_score_shadow_journal
    prices = {}
    book = _j(os.path.join(run_dir, "compute_book.json"), {}) or {}
    for p in book.get("positions") or []:
        if p.get("ticker") and p.get("price_usd"):
            prices[p["ticker"]] = p["price_usd"]
    for t, q in (_j(os.path.join(run_dir, "live_quotes.json"), {}) or {}).items():
        px = q.get("price") if isinstance(q, dict) else q
        if px:
            prices[t] = px
    for t, px in (_j(os.path.join(run_dir, "score_prices.json"), {}) or {}).items():
        if isinstance(px, (int, float)):
            prices[t] = px
    pj = os.path.join(run_dir, "shadow_prices.json")
    atomic_write_json(pj, prices)
    out = {}
    for fname in ("trigger_journal.json", "derisk_journal.json"):
        if not os.path.exists(os.path.join(base_dir, fname)):
            continue
        try:
            out[fname] = _capture(cmd_score_shadow_journal, base_dir=base_dir, file=fname, prices_json=pj,
                                  today=str(today), dry_run=False)
        except Exception as e:  # noqa: BLE001 -- scoring must never fail a commit
            out[fname] = {"error": f"{type(e).__name__}: {e}"}
    return {"shadow_journal_scored": out}


def _stage_run_block(base_dir, run_dir, mode, today):
    book = _j(os.path.join(run_dir, "compute_book.json"), {}) or {}
    holdings = _j(os.path.join(run_dir, "holdings.json"), {}) or {}
    drift = _j(os.path.join(run_dir, "compute_drift.json"), {}) or {}
    sentiment = _j(os.path.join(run_dir, "compute_sentiment.json"), {}) or {}
    st = ss.load_state(base_dir, run_dir)
    if book.get("value_usd") is not None:
        us = dict(st.get("us") or {})
        for k in ("value_usd", "wallet_usd", "pnl_pct", "count", "top3", "beta",
                  "peak_value_usd", "peak_total_book_usd", "total_book_usd", "drawdown_pct"):
            if book.get(k) is not None:
                us[k] = book[k]
        st["us"] = us
    rows = holdings.get("holdings_inr") or []
    if rows:
        st["holdings"] = [{"ticker": r.get("ticker"), "qty": r.get("qty"), "weight_pct": r.get("weight_pct")}
                          for r in rows]
        seen = st.setdefault("data_cache", {}).setdefault("last_seen", {})
        for r in rows:
            seen[r.get("ticker")] = str(today)
    # Both added 2026-09-15, found live by the user reading the dashboard's Sentiment panel:
    # it showed a frozen score (65.7, three components stuck at exactly 50.0) while this run's
    # own compute_sentiment.json already had the real, fresh read (71.2, no defaulted
    # components). Neither `sentiment` nor `risk_off_status` was ever in this function's staged
    # keys, so postflight's commit -- the ONLY path that writes state.json now -- never touched
    # them; state.json's copies were last written by whatever pre-postflight run happened to
    # hand-stage them, then sat frozen. risk_off_status is the more serious of the two: it is
    # read from state.json elsewhere to decide whether to flag defensive posture, so a stale
    # "normal" during an actual risk-off session would silently mask it. compute_drift.json
    # computes it fresh every run already; it was just never being carried into state.json.
    if sentiment.get("score") is not None:
        st["sentiment"] = {"score": sentiment.get("score"), "band": sentiment.get("band"),
                            "components": sentiment.get("components") or {}}
    if drift.get("risk_off_status") is not None:
        st["risk_off_status"] = drift["risk_off_status"]
    st["mode"] = mode
    st["last_run_dir"] = os.path.relpath(os.path.realpath(run_dir), os.path.realpath(base_dir))
    return ss.stage_state(base_dir, run_dir, st, by="postflight")


def postflight_commit(args):
    from smith_memory import cmd_append_ledger, cmd_report
    base, rd = args.base_dir, args.run_dir
    today = resolve_today(args.today)
    out = {"phase": "commit", "mode": args.mode}
    out["staged"] = _stage_run_block(base, rd, args.mode, today)
    out["commit"] = ss.commit_state(base, rd, persist_safe=None)
    # EXECUTED has exactly one writer: a matching fill in trades.json (smith_ledger.reconcile_proposals).
    # Runs every commit, never from acceptance alone; idempotent, so a re-run changes nothing.
    try:
        from smith_ledger import cmd_reconcile_proposals
        out["proposals_reconciled"] = _capture(cmd_reconcile_proposals, base_dir=base, today=str(today))
    except Exception as e:  # noqa: BLE001 -- never blocks a commit
        out["proposals_reconciled"] = {"error": f"{type(e).__name__}: {e}"}
    out.update(_merge_journal(base, rd, today))
    out.update(_append_shadow_triggers(base, rd, today))
    if args.mode in ("deep", "quick"):
        out.update(_score_shadow_journals(base, rd, today))
    # Prior-findings digest (2026-09-15): fold committed state, this run's tails and the
    # orchestrator's findings_orchestrator.json into findings.json. Never blocks a commit.
    try:
        import smith_findings
        out["findings"] = smith_findings.update(base, rd, os.path.basename(os.path.normpath(rd)), today)
    except Exception as e:  # noqa: BLE001
        out["findings"] = {"error": f"{type(e).__name__}: {e}"}

    # Knowledge base (2026-09-21): what this run LEARNED is folded into knowledge/ (append-only, git-tracked):
    # every tail and revision in chronological order, then the committed state's verdicts. Never blocks a commit.
    try:
        import smith_kb
        import smith_kb_harvest as _H
        _run_id = os.path.basename(os.path.normpath(rd))
        if f"run:{_run_id}" in smith_kb.done_keys(smith_kb.read_events(base)):
            _obs, _files = [], []                      # this run was already harvested (postflight re-run)
        else:
            _obs, _files = _H.harvest_run(base, rd, _run_id, str(today))
        _rep = smith_kb.add_observations(base, _obs, reinforce=True)
        if _files:
            smith_kb.mark_done(base, f"run:{_run_id}")
        _st = _j(os.path.join(base, "state.json"), {}) or {}
        _rep2 = smith_kb.add_observations(base, _H.from_state_snapshot(_st, str(today), run=_run_id), reinforce=False)
        out["knowledge"] = {"tails": len(_files), "added": _rep["added"] + _rep2["added"], "reinforced": _rep["reinforced"],
                            "pages": smith_kb.rebuild_pages(base, str(today))}
    except Exception as e:  # noqa: BLE001
        out["knowledge"] = {"error": f"{type(e).__name__}: {e}"}

    book = _j(os.path.join(rd, "compute_book.json"), {}) or {}
    mi = _j(os.path.join(rd, "market_inputs.json"), {}) or {}
    holdings = _j(os.path.join(rd, "holdings.json"), {}) or {}
    if args.no_ledger or args.mode in ("refresher", "holiday"):
        out["ledger"] = "skipped (mode or --no-ledger)"
    elif out["commit"]["persist_safe"] is False:
        out["ledger"] = "skipped: persist_safe false"
    elif None in (book.get("value_usd"), holdings.get("usdinr"), mi.get("spx"), mi.get("ndx")):
        out["ledger"] = "skipped: value_usd/usdinr/spx/ndx missing"
    else:
        label = os.path.basename(os.path.normpath(rd))
        out["ledger"] = _capture(
            cmd_append_ledger, base_dir=base, ts=None, mode="deep" if args.mode == "deep" else "quick",
            value_usd=book["value_usd"], usdinr=holdings["usdinr"], wallet_usd=book.get("wallet_usd") or 0.0,
            spx=mi["spx"], ndx=mi["ndx"], smh=mi.get("smh"), smh_asof=None,
            est_net_flows_usd=book.get("est_net_flows_usd"), external_flow_usd=args.external_flow_usd,
            value_trust="ok", summary=(args.summary or f"{args.mode} run {label}")[:300],
            briefing_file=args.briefing_file)
    out["report_daily"] = _capture(cmd_report, kind="daily", base_dir=base, run_dir=rd, today=str(today))
    if args.mode == "deep":
        wk = today.isocalendar()[:2]
        deep_this_week = [r for r in _ledger_rows(base) if r.get("mode") == "deep" and parse_ts(r.get("ts"))
                          and parse_ts(r.get("ts")).astimezone(IST).date().isocalendar()[:2] == wk]
        if len(deep_this_week) <= 1:
            out["report_weekly"] = _capture(cmd_report, kind="weekly", base_dir=base, run_dir=rd,
                                            today=str(today))
    if not args.no_decisions:
        p = subprocess.run([sys.executable, os.path.join(HERE, "gen_decisions_md.py")], cwd=base,
                           capture_output=True, text=True, timeout=120)
        out["decisions_md"] = "ok" if p.returncode == 0 else f"failed: {(p.stderr or p.stdout)[-200:]}"
    return out


def postflight_close(args):
    from smith_memory import cmd_compact
    base, rd = args.base_dir, args.run_dir
    today = resolve_today(args.today)
    out = {"phase": "close", "mode": args.mode}
    out["compact"] = _capture(cmd_compact, base_dir=base, holdings=os.path.join(rd, "holdings.json"),
                              today=str(today), write=True, mode="full" if args.mode == "deep" else "cheap")
    runs = os.path.join(base, "runs")
    keep = max(1, args.keep_runs)
    dirs = []
    for name in (os.listdir(runs) if os.path.isdir(runs) else []):
        p = os.path.join(runs, name)
        if os.path.isdir(p):
            dt = parse_any(name)
            dirs.append((dt.isoformat() if dt else "", name, p))
    dirs.sort()
    cur = os.path.realpath(rd)
    doomed = [p for _, _, p in dirs[:-keep] if os.path.realpath(p) != cur]
    for p in doomed:
        shutil.rmtree(p, ignore_errors=True)
    out["runs_pruned"] = [os.path.basename(p) for p in doomed]
    if not args.no_git and os.path.isdir(os.path.join(base, ".git")):
        label = os.path.basename(os.path.normpath(rd))
        steps = [["git", "add", "-A"], ["git", "commit", "-q", "-m", f"run {label} {args.mode} [skip ci]"],
                 ["git", "push", "-q"]]
        res = []
        for cmd in steps:
            try:
                p = subprocess.run(cmd, cwd=base, capture_output=True, text=True, timeout=90)
                res.append(p.returncode)
            except (OSError, subprocess.SubprocessError):
                res.append("error")
        out["git"] = dict(zip(("add", "commit", "push"), res))
    lock = ss.lock_status(base)
    holder = lock.get("holder") or {}
    run_id = args.run_id or holder.get("run_id")
    if lock["held"] and lock.get("kind") == "smith" and (
            holder.get("run_id") == args.run_id or holder.get("run_dir") == os.path.basename(os.path.normpath(rd))):
        out["lock"] = ss.lock_release(base, run_id)
    else:
        out["lock"] = {"released": False, "reason": "no lock held by this run"}
    return out


def cmd_postflight(args):
    emit(postflight_commit(args) if args.phase == "commit" else postflight_close(args))
