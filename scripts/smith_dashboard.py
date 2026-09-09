#!/usr/bin/env python3
"""smith_dashboard.py -- Agent Smith dashboard, second generation.

WHY A SECOND GENERATOR (2026-09-09). the v1 builder (now `archive/smith_dashboard_v1.py`)
reached 193KB of Python emitting 193KB of pre-baked HTML strings, and had silently regressed: `build()` called only 12 of its
~35 `_render_*` functions, so thirteen panels -- thesis map, signal history, execution log,
data-quality caveats, self-learning, stop-loss efficacy, watchlist setups, factor themes,
trade triggers, diversifier bench, rotation analysis, retired proposals, open gaps -- were
defined and never invoked. The entire Diagnostics tier had vanished from the published page.
That is exactly the failure the v1 REGRESSION GUARD was written to prevent, and it recurred
because "is this panel on the page?" is invisible when the page is assembled from 35 string
builders wired by hand.

THE STRUCTURAL FIX, not just a rewiring: this generator does not build HTML strings per panel.
It builds ONE payload dict, embeds it as JSON, and ships a client-side app that renders from
it. A panel can no longer be silently dropped by a missing call -- the tab manifest at the
bottom of the JS is a single list, and `assert_payload_complete()` below fails the build if a
required payload key is absent. Adding analysis means adding a key and a renderer, both in
one place.

WHAT THIS BUYS BEYOND PARITY: the v1 page was a document -- 20 stacked sections, no filtering,
no cross-linking. 254 proposals existed and you could see 12. This one is an instrument:
five tabs, sortable/filterable tables, a full proposal history browser, and a ticker sheet
that pulls everything the desk knows about one name -- thesis, evidence, signals, lots, stops,
cluster rank, every proposal ever made about it -- into one place.

CARRIED FORWARD DELIBERATELY from v1, do not "simplify" these away:
  * The `self` capability decision round trip (§1.7). Decisions persist in the
    `<script type="application/json" id="smith-decisions">` blob, which `smith_math.py
    sync-decisions` parses on the next run. Format unchanged -- v1 and v2 pages reconcile
    through the same code path.
  * BUT the v1 attribute-order landmine is GONE. v1 located a clicked row by string-matching
    `data-surface="X" data-element-id="Y"` inside the pristine HTML, so reordering two
    attributes silently broke the "recorded" confirmation. Here rows are rendered client-side
    FROM the decisions array, so a recorded decision re-renders as recorded with no string
    surgery at all. Only the blob itself is swapped in the pristine source.
  * `artifact_url` persistence -- the caller passes state.json's `artifact_url` to the Artifact
    tool's `url` parameter, and writes the returned URL back. This script does not publish.
  * The honesty constraints: ledger rows whose `value_trust` is not `ok` are excluded from
    chart scales and drawn hatched; cumulative book-vs-benchmark stays unplotted while
    `external_flow_usd` is unpopulated, because a cumulative line would mix deposits with
    returns.

RETIRED 2026-09-09: v1 moved to `archive/smith_dashboard_v1.py` and this generator took over
the `scripts/smith_dashboard.py` path and the `dashboard.html` output. v1 is kept, not deleted,
because its per-panel HTML is the reference for any panel whose v2 port needs checking against
what shipped before.

Usage:  python3 scripts/smith_dashboard.py --base-dir . [--out dashboard.html]
"""

import argparse
import csv
import json
import os
import re
from datetime import date, datetime, timedelta, timezone

# --------------------------------------------------------------------------------------
# loading
# --------------------------------------------------------------------------------------


def load(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def clip(s, n):
    """Trim prose for payload size. Returns None unchanged so absent stays absent."""
    if not isinstance(s, str):
        return s
    s = s.strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def num(x):
    return x if isinstance(x, (int, float)) and not isinstance(x, bool) else None


# --------------------------------------------------------------------------------------
# payload
# --------------------------------------------------------------------------------------

# Every key the client app renders. The build fails loudly if one goes missing -- this is the
# structural answer to v1's silent panel loss.
REQUIRED_KEYS = [
    "meta", "kpi", "read", "macro", "positions", "clusters", "ladders", "proposals",
    "triggers", "derisk", "thesis", "signals", "catalysts", "themes", "diversifiers",
    "watchlist", "track", "stress", "quality", "tax", "rebound", "freshness", "dq",
    "gaps", "outages", "trades", "ledger", "earnings", "learning", "attribution",
]


def assert_payload_complete(p):
    missing = [k for k in REQUIRED_KEYS if k not in p]
    if missing:
        raise SystemExit(
            "smith_dashboard: payload is missing required keys: %s\n"
            "A panel would render empty. Add the key or remove it from REQUIRED_KEYS "
            "deliberately -- do not let it fall out silently (this is the v1 regression)."
            % ", ".join(missing)
        )


def build_payload(base, built_at=None):
    st = load(os.path.join(base, "state.json"), {}) or {}
    policy = load(os.path.join(base, "policy.json"), {}) or {}
    props_store = load(os.path.join(base, "proposals.json"), {}) or {}
    trades_store = load(os.path.join(base, "trades.json"), {}) or {}
    lots = load(os.path.join(base, "lots.json"), {}) or {}
    stops = load(os.path.join(base, "stops_analysis.json"), {}) or {}
    learning = load(os.path.join(base, "learning.json"), {}) or {}
    narrative = load(os.path.join(base, "narrative.json"), {}) or {}

    run_dir = st.get("latest_run_dir") or st.get("last_run_dir") or ""

    def rf(name):
        if not run_dir:
            return {}
        return load(os.path.join(base, run_dir, name), {}) or {}

    book = rf("compute_book.json")
    risk = rf("compute_risk.json")
    drift = rf("compute_drift.json")
    trig = rf("compute_triggers.json")
    derisk = rf("compute_derisk.json")
    ladder = rf("compute_ladder.json")
    journal = rf("compute_journal.json")
    attrib = rf("compute_attribution.json")
    fresh = rf("compute_freshness.json")
    buckets = rf("compute_buckets.json")
    mkt = rf("market_inputs.json")
    holdings = rf("holdings.json")

    sector_map = st.get("sector_map", {}) or {}
    thesis = st.get("thesis", {}) or {}
    sighist = st.get("signal_history", {}) or {}
    dcache = st.get("data_cache", {}) or {}
    rsi = (trig.get("rsi_values") or {})
    ret1m = (trig.get("abs_return_1m_pct_values") or {})
    rel = (dcache.get("rel_strength_1m") or {})

    risk_by = {r.get("ticker"): r for r in (risk.get("positions") or [])}
    derisk_by = {r.get("ticker"): r for r in (derisk.get("queue") or [])}
    grades = (journal.get("name_bucket_grades") or {})

    # ---- positions -------------------------------------------------------------------
    positions = []
    for b in book.get("positions") or []:
        t = b.get("ticker")
        r = risk_by.get(t, {})
        d = derisk_by.get(t, {})
        th = thesis.get(t, {})
        relv = rel.get(t)
        if isinstance(relv, dict):
            relv = relv.get("value", relv.get("pp"))
        positions.append({
            "t": t,
            "cluster": r.get("cluster") or sector_map.get(t) or "Unmapped",
            "qty": num(b.get("qty")),
            "px": num(b.get("price_usd")),
            "day": num(b.get("day_chg_pct")),
            "val": num(b.get("market_value_usd")),
            "wt": num(b.get("weight_pct")),
            "mcap": b.get("market_cap"),
            "atr": num(r.get("atr20_pct")),
            "beta": num(r.get("beta")),
            "stop_px": num(r.get("stop_price_usd")),
            "stop_dist": num(r.get("stop_distance_pct")),
            "cap": num(r.get("max_position_usd")),
            "headroom": num(r.get("headroom_usd")),
            "over_cap": bool(r.get("over_cap")),
            "cap_mult": num(r.get("cap_multiple")),
            "risk_usd": num(r.get("position_open_risk_usd")),
            "risk_share": num(d.get("risk_share_pct")),
            "rsi": num(rsi.get(t)),
            "rel": num(relv),
            "ret1m": num(ret1m.get(t)),
            "thesis": th.get("status"),
            "signals": sighist.get(t) or [],
            "frag": num(d.get("fragility_score")),
            "stretch": num(d.get("stretch_score")),
            "derisk": num(d.get("derisk_score")),
            "drank": d.get("rank"),
            "grades": grades.get(t) or {},
        })
    positions.sort(key=lambda p: -(p["wt"] or 0))

    held = {p["t"] for p in positions}

    # ---- clusters + ladders ----------------------------------------------------------
    ladders_state = st.get("cluster_ladders", {}) or {}
    ladder_clusters = (ladder.get("clusters") or {})
    clusters = []
    for row in drift.get("cluster_table") or []:
        name = row.get("cluster") or row.get("name")
        band = row.get("band_pct") or row.get("target_band_pct") or []
        members = sorted([p for p in positions if p["cluster"] == name],
                         key=lambda p: -(p["wt"] or 0))
        gone = sorted([t for t, c in sector_map.items() if c == name and t not in held])
        L = ladders_state.get(name) or {}
        clusters.append({
            "name": name,
            "eq_pct": num(row.get("actual_pct_of_equity")
                          if row.get("actual_pct_of_equity") is not None
                          else row.get("actual_pct")),
            "book_pct": num(row.get("actual_pct_of_total_book")),
            "target": num(row.get("target_pct")),
            "drift": num(row.get("drift_pt")),
            "room_usd": num(row.get("cluster_room_usd")),
            "band": band if isinstance(band, list) else [],
            "edge": row.get("breach_edge"),
            "breach": bool(row.get("breach")),
            "members": [m["t"] for m in members],
            "gone": gone,
            "ladder_as_of": L.get("as_of"),
            "ladder_conf": L.get("confidence"),
            "innings": (L.get("cluster_thesis") or {}).get("innings"),
            "cthesis_status": (L.get("cluster_thesis") or {}).get("status"),
        })

    ladders = {}
    for name, L in ladders_state.items():
        ct = L.get("cluster_thesis") or {}
        ladders[name] = {
            "as_of": L.get("as_of"),
            "confidence": L.get("confidence"),
            "confidence_reasons": L.get("confidence_reasons") or [],
            "status": ct.get("status"),
            "innings": ct.get("innings"),
            "text": clip(ct.get("text"), 1400),
            "falsifier": clip(ct.get("falsifier"), 700),
            "margin_pool": clip(L.get("margin_pool") if isinstance(L.get("margin_pool"), str)
                                else json.dumps(L.get("margin_pool") or {}), 700),
            "leader": L.get("leader"),
            "laggard": L.get("laggard"),
            "ranking": [{
                "rank": r.get("rank"), "t": r.get("ticker"), "held": bool(r.get("held")),
                "verdict": r.get("verdict"),
                "reads": [{"axis": clip(x.get("axis"), 160), "read": clip(x.get("read"), 320),
                           "source": clip(x.get("source"), 90), "date": x.get("date")}
                          for x in (r.get("differentiator_reads") or [])[:4]],
            } for r in (L.get("ranking") or [])],
            "bench": [{"t": b.get("ticker"), "px": num(b.get("price_usd")),
                       "why": clip(b.get("why_better_than"), 480),
                       "entry": clip(b.get("entry_condition"), 300)}
                      for b in (L.get("bench") or [])],
            "redundant": L.get("redundant_pairs") or [],
            "tensions": [{"t": x.get("ticker"), "rank": x.get("ladder_rank"),
                          "thesis": x.get("thesis_status"), "text": clip(x.get("tension"), 500)}
                         for x in (L.get("thesis_tensions") or [])],
            "catalysts": L.get("catalysts") or [],
            "reorder_when": [clip(x, 340) for x in (L.get("reorder_when") or [])],
            "unranked": L.get("unranked") or [],
            "track": L.get("track_record") or {},
        }
    for name, c in (ladder_clusters or {}).items():
        if name not in ladders and isinstance(c, dict):
            ladders[name] = {"as_of": ladder.get("as_of"), "confidence": c.get("confidence"),
                             "ranking": [], "bench": [], "redundant": [], "tensions": [],
                             "catalysts": [], "reorder_when": [], "unranked": [],
                             "confidence_reasons": [], "track": {}}

    # ---- proposals -------------------------------------------------------------------
    all_props = props_store.get("proposals") or []

    def prop_lite(p):
        return {
            "id": p.get("id"), "date": (p.get("date") or "")[:10], "t": p.get("ticker"),
            "action": p.get("action"), "dir": p.get("direction_bucket"),
            "size": num(p.get("size_usd")), "status": p.get("status"),
            "priority": p.get("priority"), "trigger": p.get("trigger_type"),
            "cluster": p.get("cluster"), "cls": p.get("proposal_class"),
            "rationale": clip(p.get("rationale"), 700),
            "px0": num(p.get("price_at_proposal")), "px1": num(p.get("price_now")),
            "drift": num(p.get("price_drift_pct")),
            "outcome": p.get("outcome") or p.get("scored_outcome"),
            "closed": p.get("closed_on") or p.get("retired_on") or p.get("dismissed_on"),
        }

    def prop_full(p):
        d = prop_lite(p)
        d.update({
            "reasons": [clip(x, 480) for x in (p.get("priority_reasons") or [])],
            "valid": [clip(x, 480) for x in (p.get("still_valid_because") or [])],
            "flags": p.get("review_flags") or [],
            "retires": clip(p.get("retires_when"), 300),
            "revalidated": p.get("revalidated_on"),
            "pair_id": p.get("pair_id"),
            "stacks": p.get("stacks_on") or [],
            "tranche": clip(p.get("tranche_note"), 300),
            "score": p.get("priority_score"),
        })
        return d

    open_props = [prop_full(p) for p in all_props if p.get("status") == "open"]
    accepted = [prop_full(p) for p in all_props
                if p.get("status") in ("accepted_by_user", "deferred", "watch")]
    prio_rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    open_props.sort(key=lambda p: (prio_rank.get(p["priority"], 3), -(p["size"] or 0)))

    proposals = {
        "open": open_props,
        "accepted": accepted,
        "history": [prop_lite(p) for p in sorted(
            all_props, key=lambda x: (x.get("date") or ""), reverse=True)],
        "scorecard": props_store.get("scorecard") or {},
        "counts": {},
    }
    for p in all_props:
        s = p.get("status") or "unknown"
        proposals["counts"][s] = proposals["counts"].get(s, 0) + 1

    # ---- triggers --------------------------------------------------------------------
    TRIGGER_FAMILIES = [
        "catalyst_threat", "thesis_break", "oversold_reversion", "overbought_distribution",
        "trend_entry", "trend_breakdown", "conviction_average", "conviction_exit",
        "entry_setup", "reentry", "bench_diversifier", "profit_rotation", "cluster_rotation",
        "cluster_bench_rotation", "cluster_consolidation", "laggard_rotation",
        "profit_ratchet", "scale_out_ladder",
    ]

    def trig_row(r):
        if "sell_leg" in r or "buy_leg" in r:  # paired rotation
            sl, bl = r.get("sell_leg") or {}, r.get("buy_leg") or {}
            return {
                "paired": True, "pair_id": r.get("pair_id"), "cluster": r.get("cluster"),
                "vote": r.get("vote"), "trigger_type": r.get("trigger_type"),
                "ladder_driven": bool(r.get("ladder_driven")),
                "ladder_conf": r.get("ladder_confidence"),
                "ladder_reasons": [clip(x, 340) for x in (r.get("ladder_authority_reasons") or [])],
                "sell": {"t": sl.get("ticker"), "dir": sl.get("direction"),
                         "size": num(sl.get("suggested_size_usd")),
                         "reasons": [clip(x, 400) for x in (sl.get("reasons") or [])]},
                "buy": {"t": bl.get("ticker"), "dir": bl.get("direction"),
                        "size": num(bl.get("suggested_size_usd")),
                        "reasons": [clip(x, 400) for x in (bl.get("reasons") or [])]},
                "blockers": [clip(x, 300) for x in (r.get("blockers") or [])],
            }
        return {
            "paired": False, "t": r.get("ticker"), "cluster": r.get("cluster"),
            "thesis": r.get("thesis_status"), "vote": r.get("vote"),
            "dir": r.get("direction"), "trigger_type": r.get("trigger_type"),
            "size": num(r.get("suggested_size_usd")), "px": num(r.get("price_usd")),
            "val": num(r.get("market_value_usd")), "rsi": num(r.get("rsi14")),
            "rel": num(r.get("rel_strength_1m_pp")), "ret1m": num(r.get("abs_return_1m_pct")),
            "gain": num(r.get("gain_pct")), "stop_now": num(r.get("current_stop_usd")),
            "stop_new": num(r.get("suggested_stop_usd")),
            "gain_at_risk": num(r.get("gain_at_risk_usd")),
            "reasons": [clip(x, 400) for x in (r.get("reasons") or [])],
            "blockers": [clip(x, 300) for x in (r.get("blockers") or [])],
            "sources": (r.get("catalyst_sources") or [])[:3],
            "retires": clip(r.get("retires_when"), 260),
        }

    fam = {}
    for f in TRIGGER_FAMILIES:
        rows = trig.get(f) or []
        if isinstance(rows, list) and rows:
            fam[f] = [trig_row(r) for r in rows]
    triggers = {
        "as_of": trig.get("as_of"),
        "families": fam,
        "live_counts": trig.get("live_counts") or {},
        "shadow_counts": trig.get("shadow_counts") or {},
        "thresholds": trig.get("thresholds") or {},
        "deployable_usd": num(trig.get("deployable_cash_usd")),
        "max_deploy_usd": num(trig.get("max_single_deploy_usd")),
        "correction_state": trig.get("correction_state"),
        "rsi_as_of": trig.get("rsi_as_of"), "rsi_age": trig.get("rsi_age_days"),
        "rsi_cov": num(trig.get("rsi_coverage_pct")),
        "rel_as_of": trig.get("rel_as_of"), "rel_age": trig.get("rel_age_days"),
        "rel_cov": num(trig.get("rel_coverage_pct")),
        "shadow_new": trig.get("shadow_new") or [],
    }

    # ---- track record ----------------------------------------------------------------
    track = {
        "scorecard": props_store.get("scorecard") or {},
        "buckets": journal.get("bucket_hit_rates") or {},
        "buckets_7d": journal.get("bucket_hit_rates_7d") or {},
        "grades": grades,
        "journal_n": len(journal.get("journal_updates") or []),
        "stops": {
            "as_of": stops.get("as_of"),
            "overall": stops.get("overall") or {},
            "by_cohort": stops.get("by_cohort") or {},
            "by_ticker": stops.get("by_ticker") or {},
            "reentry": stops.get("reentry_summary") or {},
            "rows": [{
                "t": s.get("ticker"), "date": s.get("date"), "cohort": s.get("cohort"),
                "exit_px": num(s.get("exit_price_usd") or s.get("price_usd")),
                "now_px": num(s.get("current_price_usd")),
                "move": num(s.get("move_pct")), "impact": num(s.get("dollar_impact")),
                "verdict": s.get("verdict"),
            } for s in (stops.get("stops") or [])],
        },
        "ladder_track": ladder.get("track_record") or {},
    }

    # ---- ledger series ---------------------------------------------------------------
    ledger = []
    lpath = os.path.join(base, "ledger.csv")
    if os.path.exists(lpath):
        with open(lpath, newline="") as f:
            for row in csv.DictReader(f):
                try:
                    v = float(row.get("value_usd") or 0)
                except ValueError:
                    continue
                try:
                    w = float(row.get("wallet_usd") or 0)
                except ValueError:
                    w = 0.0
                ledger.append({
                    "ts": (row.get("ts") or "")[:10],
                    "v": round(v, 2), "w": round(w, 2),
                    "mode": row.get("mode"),
                    # HONESTY: rows whose trust is not ok are kept but marked -- the client
                    # excludes them from scales and draws them hatched. Never dropped silently.
                    "trust": row.get("value_trust") or "unknown",
                    "note": clip(row.get("notes"), 240),
                })

    # ---- trades / execution log ------------------------------------------------------
    tr = trades_store.get("trades") or []
    trades = [{
        "date": t.get("date"), "t": t.get("ticker"), "side": t.get("side"),
        "action": t.get("action"), "qty": num(t.get("qty")), "px": num(t.get("price_usd")),
        "amt": num(t.get("amount_usd")), "type": t.get("order_type"),
        "reason": clip(t.get("reason"), 300), "src": t.get("price_source"),
    } for t in tr[-120:]][::-1]

    # ---- week ahead ------------------------------------------------------------------
    ts = st.get("ts") or datetime.now(timezone.utc).isoformat()
    try:
        today = datetime.fromisoformat(ts.replace("Z", "+00:00")).date()
    except ValueError:
        today = date.today()
    horizon = today + timedelta(days=10)
    earn_cache = dcache.get("earnings_calendar") or {}
    week = []
    for t, e in earn_cache.items():
        # entries are usually {"date":..., "confirmed":...} but some legacy rows are a bare
        # date string -- accept both rather than crashing the whole build on one row
        if isinstance(e, str):
            e = {"date": e, "confirmed": False}
        if not isinstance(e, dict):
            continue
        ds = e.get("date")
        if not ds:
            continue
        try:
            d0 = date.fromisoformat(ds)
        except ValueError:
            continue
        if today <= d0 <= horizon:
            week.append({"date": ds, "what": "%s earnings" % t, "t": t,
                         "kind": "earnings", "confirmed": bool(e.get("confirmed"))})
    cal = (st.get("macro_read") or {}).get("calendar") or {}
    for key, label in (("next_fomc", "FOMC"), ("next_cpi", "CPI"), ("next_nfp", "Nonfarm payrolls")):
        v = cal.get(key)
        if v:
            week.append({"date": str(v)[:10], "what": label, "t": None,
                         "kind": "macro", "confirmed": "~" not in str(v)})
    week.sort(key=lambda x: x["date"])

    # ---- learning --------------------------------------------------------------------
    params = learning.get("parameters") or {}
    readiness = (params.get("phase4.readiness") or {})
    learning_out = {
        "readiness_current": readiness.get("current"),
        "readiness_gate": readiness.get("n_gate"),
        "readiness_note": clip(readiness.get("note"), 600),
        "params": [{"id": k, "current": v.get("current"), "default": v.get("default"),
                    "state": v.get("state"), "note": clip(v.get("note"), 400)}
                   for k, v in params.items()],
        "lessons": [{"date": x.get("date"), "kind": x.get("kind"),
                     "text": clip(x.get("text"), 700)}
                    for x in (learning.get("lessons") or [])[-16:]][::-1],
        "obs_n": len(learning.get("observations") or []),
    }

    # ---- data quality (unioned, as v1 required) --------------------------------------
    dq = []
    for src, arr in (("state", st.get("data_quality")), ("book", book.get("data_quality")),
                     ("risk", risk.get("data_quality")), ("derisk", derisk.get("data_quality")),
                     ("ladder", ladder.get("data_quality")), ("journal", journal.get("data_quality")),
                     ("buckets", buckets.get("data_quality")),
                     ("attribution", attrib.get("data_quality")),
                     ("stops", stops.get("data_quality"))):
        for item in (arr or []):
            dq.append({"src": src, "text": clip(item if isinstance(item, str)
                                                else json.dumps(item), 400)})

    # ---- KPI strip -------------------------------------------------------------------
    sent = st.get("sentiment") or {}
    cyc = st.get("cycle_position") or {}
    kpi = {
        "equity": num(book.get("value_usd")),
        "total_book": num(book.get("total_book_usd")),
        "pnl_pct": num(book.get("pnl_pct")),
        "day_pct": num(book.get("day_chg_pct_weighted")),
        "cash_usd": num(book.get("wallet_usd")),
        "cash_pct": num(drift.get("cash_pct") if drift.get("cash_pct") is not None
                        else book.get("wallet_pct")),
        "cash_band": drift.get("cash_band_pct") or [],
        "cash_breach": bool(drift.get("cash_breach")),
        "cash_regime": drift.get("cash_regime"),
        "cash_reason": clip(drift.get("cash_regime_reason"), 420),
        "dd_pct": num(book.get("drawdown_pct")),
        "dd_peak": num(book.get("peak_total_book_usd")),
        "risk_pct": num(risk.get("aggregate_open_risk_pct")),
        "risk_cap": num(risk.get("aggregate_open_risk_cap_pct")),
        "ai_capex": num(drift.get("ai_capex_pct")),
        "ai_cap": num(drift.get("ai_capex_cap_pct")),
        "beta": num(book.get("beta")),
        "beta_bm": (book.get("primary_benchmark") or {}).get("peer_etf"),
        "beta_note": clip((book.get("primary_benchmark") or {}).get("note"), 300),
        "count": book.get("count"),
        "top5": num(book.get("top5_pct")),
        "top10": num(book.get("top10_pct")),
        "sent_score": num(sent.get("score")),
        "sent_band": sent.get("band"),
        "sent_components": sent.get("components") or {},
        "risk_off": st.get("risk_off_status"),
        "correction_state": trig.get("correction_state"),
        "queue_state": derisk.get("queue_state"),
        "cycle": cyc.get("position"),
        "cycle_conf": cyc.get("confidence"),
        "cycle_falsifier": clip(cyc.get("falsifier"), 900),
        "cycle_as_of": cyc.get("as_of"),
        "risk_conc": book.get("risk_concentration") or [],
    }

    payload = {
        "meta": {
            "ts": ts, "mode": st.get("mode"), "run_dir": run_dir,
            "usdinr": num(st.get("usdinr")), "usdinr_drift": num(book.get("usdinr_drift_pct")),
            # Wall-clock by default. Overridable so the golden master can be byte-compared:
            # a build stamp that changes every second makes any diff-based regression check
            # useless, which would quietly retire the very guard this rewrite exists to add.
            "generated": built_at or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%MZ"),
            "artifact_url": st.get("artifact_url"),
            "market_closed": bool(st.get("market_closed_run")),
            "policy_confirmed": bool(drift.get("policy_confirmed")),
        },
        "kpi": kpi,
        "read": clip(narrative.get("session_read"), 2400),
        "macro": {
            "us10y": num(mkt.get("us10y")), "vix": num(mkt.get("vix")),
            "vix_prev": num(mkt.get("vix_prev")), "dxy": num(mkt.get("dxy")),
            "spx": num(mkt.get("spx")), "ndx": num(mkt.get("ndx")),
            "smh": num(mkt.get("smh")), "smh_chg": num(mkt.get("smh_chg_pct")),
            "es_chg": num(mkt.get("es_f_chg_pct")), "nq_chg": num(mkt.get("nq_f_chg_pct")),
            "asia": mkt.get("asia") or {}, "session": mkt.get("market_session"),
            "gate": mkt.get("gate_classification"), "gate_reason": clip(mkt.get("gate_reason"), 420),
            "fed": num((st.get("macro_read") or {}).get("fed_funds_pct")),
            "fomc": (st.get("macro_read") or {}).get("fomc_stance"),
            "regime": (st.get("macro_read") or {}).get("regime"),
            "regime_note": clip((st.get("macro_read") or {}).get("regime_note"), 700),
            "cluster_impact": (st.get("macro_read") or {}).get("cluster_impact") or {},
            "calendar": cal, "week": week,
        },
        "positions": positions,
        "clusters": clusters,
        "ladders": ladders,
        "proposals": proposals,
        "triggers": triggers,
        "derisk": {
            "headline": clip(derisk.get("headline"), 400),
            "queue_state": derisk.get("queue_state"),
            "benchmark": derisk.get("benchmark"),
            "bm_1m": num(derisk.get("benchmark_return_1m_pct")),
            "sentiment_band": derisk.get("sentiment_band"),
            "urgency": num(derisk.get("urgency_multiplier")),
            "stretched": derisk.get("names_stretched") or [],
            "beat_but_down": derisk.get("names_beat_benchmark_but_down") or [],
            "queue": [{"t": q.get("ticker"), "rank": q.get("rank"),
                       "frag": num(q.get("fragility_score")), "stretch": num(q.get("stretch_score")),
                       "score": num(q.get("derisk_score")), "cluster": q.get("cluster"),
                       "thesis": q.get("thesis_status"), "val": num(q.get("market_value_usd")),
                       "rel": num(q.get("rel_strength_1m_pp")), "rsi": num(q.get("rsi14")),
                       "friction": num(q.get("friction_score")),
                       "friction_why": [clip(x, 220) for x in (q.get("friction_reasons") or [])]}
                      for q in (derisk.get("queue") or [])],
        },
        "thesis": {t: {
            "status": v.get("status"),
            "text": clip(v.get("thesis"), 900),
            "verified": v.get("verified"),
            "against_src": clip(v.get("verified_against"), 240),
            "for": [{"claim": clip(e.get("claim"), 400), "date": e.get("date"),
                     "source": clip(e.get("source"), 140)}
                    for e in (v.get("evidence_for") or [])[:5]],
            "vs": [{"claim": clip(e.get("claim"), 400), "date": e.get("date"),
                    "source": clip(e.get("source"), 140)}
                   for e in (v.get("evidence_against") or [])[:5]],
            "held": t in held,
        } for t, v in thesis.items()},
        "signals": {t: v for t, v in sighist.items()},
        "signals_as_of": st.get("signal_history_as_of") or {},
        "catalysts": [{
            "headline": clip(c.get("headline"), 400), "date": c.get("date"),
            "horizon": c.get("horizon"), "direction": c.get("direction"),
            "affects": c.get("affects") or [], "exposure": num(c.get("exposure_pct_equity")),
            "magnitude": clip(c.get("magnitude"), 500),
            "sources": (c.get("sources") or c.get("source") or [])
            if isinstance(c.get("sources") or c.get("source"), list)
            else [c.get("source")] if c.get("source") else [],
        } for c in (st.get("factor_catalysts") or [])],
        "catalysts_as_of": st.get("factor_catalysts_as_of"),
        "themes": st.get("factor_themes") or {},
        "diversifiers": st.get("diversifier_candidates") or {},
        "watchlist": st.get("watchlist_setups") or [],
        "watchlist_as_of": st.get("watchlist_setups_as_of"),
        "track": track,
        "stress": st.get("stress_table") or {},
        "quality": {
            "flags": (st.get("quality_read") or {}).get("quality_flags") or {},
            "book_pct": num((st.get("quality_read") or {}).get("book_pct_flagged")),
            "top_concern": clip((st.get("quality_read") or {}).get("top_concern"), 500),
            "as_of": (st.get("quality_read") or {}).get("as_of"),
            "cleared": (st.get("quality_read") or {}).get("cleared") or [],
            "unauditable": (st.get("quality_read") or {}).get("unauditable") or [],
        },
        "tax": st.get("tax_read") or {},
        "rebound": st.get("rebound_candidates") or {},
        "freshness": {
            "as_of": fresh.get("as_of"), "counts": fresh.get("counts") or {},
            "headline": clip(fresh.get("headline"), 300),
            "artefacts": fresh.get("artefacts") or [],
            "dark": fresh.get("dark") or [], "stale": fresh.get("stale") or [],
        },
        "dq": dq,
        "gaps": [{"text": clip(g if isinstance(g, str) else json.dumps(g), 400)}
                 for g in (st.get("known_gaps") or [])] +
                [{"text": clip(g if isinstance(g, str) else json.dumps(g), 400)}
                 for g in (st.get("open_flags") or [])],
        "outages": st.get("run_outages") or [],
        "trades": trades,
        "ledger": ledger,
        "earnings": earn_cache,
        "learning": learning_out,
        "attribution": {
            "delta": num(attrib.get("value_delta_usd")), "fx": num(attrib.get("fx_effect_usd")),
            "flow": num(attrib.get("flow_usd")),
            "residual": num(attrib.get("residual_market_move_usd")),
            "components": attrib.get("flow_components") or {},
            "rolling": attrib.get("rolling") or {},
            "changes": attrib.get("qty_changes") or [],
        },
        "lots": lots if isinstance(lots, dict) else {},
        "policy_targets": (policy.get("cluster_targets")
                           or policy.get("targets") or {}),
    }
    assert_payload_complete(payload)
    return payload


# --------------------------------------------------------------------------------------
# CSS -- token-first, all three theme states (bare :root, prefers-color-scheme, [data-theme])
# --------------------------------------------------------------------------------------

CSS = r"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans+Condensed:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>
/* Palette: cool green-biased neutrals + a teal instrument accent. Semantic good/warn/bad are
   deliberately NOT the accent -- a dashboard needs "this is fine" to read differently from
   "this is the thing you clicked". Every token is declared here in bare :root first. */
:root{
  --bg:#F6F8F7; --surf:#FFFFFF; --surf-2:#EFF3F2; --surf-3:#E4EAE8;
  --ink:#101817; --ink-2:#42504E; --ink-3:#6D7B79; --line:#D7DEDC; --line-2:#C2CDCA;
  --acc:#0F766E; --acc-2:#0D5D57; --acc-soft:#D6EDEA;
  --pos:#15803D; --pos-soft:#DCF0E3; --neg:#B4231E; --neg-soft:#FBE3E1;
  --warn:#A65A08; --warn-soft:#FBEBD6; --info:#1D5FA8; --info-soft:#DCE9F8;
  --c1:#0F766E; --c2:#B45309; --c3:#1D5FA8; --c4:#7C3F98; --c5:#A1123C;
  --c6:#4D7C0F; --c7:#0E7490; --c8:#6B7280;
  --shadow:0 1px 2px rgba(16,24,23,.06),0 4px 14px rgba(16,24,23,.05);
  --mono:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace;
  --sans:"IBM Plex Sans",system-ui,-apple-system,Segoe UI,sans-serif;
  --cond:"IBM Plex Sans Condensed","IBM Plex Sans",system-ui,sans-serif;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --bg:#0C1211; --surf:#141B1A; --surf-2:#1A2322; --surf-3:#222D2B;
    --ink:#E6EDEB; --ink-2:#A9B7B4; --ink-3:#7C8B88; --line:#263230; --line-2:#33423F;
    --acc:#2DD4BF; --acc-2:#5EEAD4; --acc-soft:#12312E;
    --pos:#4ADE80; --pos-soft:#12301D; --neg:#F87171; --neg-soft:#361616;
    --warn:#FBBF24; --warn-soft:#382709; --info:#7DB3F0; --info-soft:#122438;
    --c1:#2DD4BF; --c2:#FBBF24; --c3:#7DB3F0; --c4:#C79BE0; --c5:#F4869E;
    --c6:#A3D65C; --c7:#67D3E8; --c8:#94A3A0;
    --shadow:0 1px 2px rgba(0,0,0,.4),0 4px 14px rgba(0,0,0,.3);
  }
}
:root[data-theme="dark"]{
  --bg:#0C1211; --surf:#141B1A; --surf-2:#1A2322; --surf-3:#222D2B;
  --ink:#E6EDEB; --ink-2:#A9B7B4; --ink-3:#7C8B88; --line:#263230; --line-2:#33423F;
  --acc:#2DD4BF; --acc-2:#5EEAD4; --acc-soft:#12312E;
  --pos:#4ADE80; --pos-soft:#12301D; --neg:#F87171; --neg-soft:#361616;
  --warn:#FBBF24; --warn-soft:#382709; --info:#7DB3F0; --info-soft:#122438;
  --c1:#2DD4BF; --c2:#FBBF24; --c3:#7DB3F0; --c4:#C79BE0; --c5:#F4869E;
  --c6:#A3D65C; --c7:#67D3E8; --c8:#94A3A0;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 4px 14px rgba(0,0,0,.3);
}

*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);
  font-size:14px;line-height:1.5;-webkit-font-smoothing:antialiased}
.num,td.n,.mono{font-family:var(--mono);font-variant-numeric:tabular-nums}
h1,h2,h3{font-family:var(--cond);text-wrap:balance;margin:0}
a{color:var(--acc);text-decoration-thickness:1px;text-underline-offset:2px}
button{font:inherit;color:inherit}
:focus-visible{outline:2px solid var(--acc);outline-offset:2px;border-radius:3px}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}

/* masthead ---------------------------------------------------------------- */
.mast{position:sticky;top:0;z-index:40;background:var(--surf);
  border-bottom:1px solid var(--line)}
.mast-in{max-width:1520px;margin:0 auto;padding:14px 22px 0}
.mast-top{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap}
.brand{font-family:var(--cond);font-weight:700;font-size:19px;letter-spacing:.01em}
.brand em{font-style:normal;color:var(--acc)}
.mast-meta{font-family:var(--mono);font-size:11.5px;color:var(--ink-3);
  display:flex;gap:12px;flex-wrap:wrap;margin-left:auto}
.mast-meta b{font-weight:500;color:var(--ink-2)}

.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(122px,1fr));
  gap:0;margin:12px 0 0;border-top:1px solid var(--line)}
.kpi{padding:9px 14px 10px;border-right:1px solid var(--line)}
.kpi:last-child{border-right:0}
.kpi .k{font-family:var(--cond);font-size:10.5px;font-weight:600;letter-spacing:.07em;
  text-transform:uppercase;color:var(--ink-3);display:block;margin-bottom:2px}
.kpi .v{font-family:var(--mono);font-size:17px;font-weight:500;letter-spacing:-.02em;
  display:block;line-height:1.2}
.kpi .s{font-family:var(--mono);font-size:10.5px;color:var(--ink-3);display:block}
.kpi.hot{background:var(--neg-soft)} .kpi.hot .v{color:var(--neg)}
.kpi.warm{background:var(--warn-soft)} .kpi.warm .v{color:var(--warn)}
.kpi.good .v{color:var(--pos)}

.tabs{display:flex;gap:2px;max-width:1520px;margin:0 auto;padding:0 18px;
  overflow-x:auto;scrollbar-width:none}
.tabs::-webkit-scrollbar{display:none}
.tab{background:none;border:0;border-bottom:2px solid transparent;padding:11px 13px 9px;
  font-family:var(--cond);font-size:13.5px;font-weight:600;letter-spacing:.02em;
  color:var(--ink-3);cursor:pointer;white-space:nowrap;display:flex;align-items:center;gap:7px}
.tab:hover{color:var(--ink)}
.tab[aria-selected="true"]{color:var(--ink);border-bottom-color:var(--acc)}
.tab .cnt{font-family:var(--mono);font-size:10.5px;background:var(--surf-3);
  color:var(--ink-2);padding:1px 5px;border-radius:9px;font-weight:500}
.tab[aria-selected="true"] .cnt{background:var(--acc-soft);color:var(--acc)}

/* layout ------------------------------------------------------------------ */
.wrap{max-width:1520px;margin:0 auto;padding:20px 22px 90px}
.grid{display:grid;gap:16px}
.g2{grid-template-columns:repeat(auto-fit,minmax(380px,1fr))}
.g3{grid-template-columns:repeat(auto-fit,minmax(290px,1fr))}
.span2{grid-column:1/-1}

.panel{background:var(--surf);border:1px solid var(--line);border-radius:6px;
  overflow:hidden}
.panel.flat{background:none;border:0;border-radius:0}
.panel > header{display:flex;align-items:baseline;gap:10px;padding:12px 15px;
  border-bottom:1px solid var(--line);flex-wrap:wrap}
.panel > header h2{font-size:14px;font-weight:600;letter-spacing:.01em}
.panel > header .sub{font-size:11.5px;color:var(--ink-3);font-family:var(--mono)}
.panel > header .right{margin-left:auto;display:flex;gap:8px;align-items:center}
.pad{padding:14px 15px}
/* severity stripe -- spent only where something needs attention, not on every panel */
.panel.sev-bad{border-left:3px solid var(--neg)}
.panel.sev-warn{border-left:3px solid var(--warn)}
.panel.sev-ok{border-left:3px solid var(--pos)}

.note{color:var(--ink-3);font-size:12.5px;margin:0}
.empty{color:var(--ink-3);font-size:13px;padding:16px 15px;font-style:italic}

/* pills / chips ----------------------------------------------------------- */
.pill{display:inline-flex;align-items:center;gap:4px;font-family:var(--cond);font-size:10.5px;
  font-weight:600;letter-spacing:.05em;text-transform:uppercase;padding:2px 7px;
  border-radius:3px;background:var(--surf-3);color:var(--ink-2);white-space:nowrap}
.pill.buy{background:var(--pos-soft);color:var(--pos)}
.pill.sell,.pill.trim{background:var(--neg-soft);color:var(--neg)}
.pill.hold,.pill.watch{background:var(--warn-soft);color:var(--warn)}
.pill.info{background:var(--info-soft);color:var(--info)}
.pill.acc{background:var(--acc-soft);color:var(--acc)}
.pill.live{background:var(--acc-soft);color:var(--acc)}
.pill.shadow{background:var(--surf-3);color:var(--ink-3)}
.pill.high{background:var(--neg-soft);color:var(--neg)}
.pill.medium{background:var(--warn-soft);color:var(--warn)}
.pill.low{background:var(--surf-3);color:var(--ink-3)}

.tk{font-family:var(--mono);font-weight:600;font-size:12.5px;background:none;border:0;
  padding:1px 3px;margin:0 -3px;cursor:pointer;color:var(--ink);border-radius:3px;
  border-bottom:1px dotted var(--line-2)}
.tk:hover{background:var(--acc-soft);color:var(--acc);border-bottom-color:transparent}
.tk.gone{opacity:.45;text-decoration:line-through}

.dot{width:7px;height:7px;border-radius:50%;display:inline-block;flex:none}
.dot.strengthening{background:var(--pos)} .dot.intact{background:var(--acc)}
.dot.watch{background:var(--warn)} .dot.broken{background:var(--neg)}
.dot.none{background:var(--ink-3)}

.pos{color:var(--pos)} .neg{color:var(--neg)} .warnc{color:var(--warn)}
.muted{color:var(--ink-3)}

/* tables ------------------------------------------------------------------ */
.tbl-scroll{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:12.5px}
th{font-family:var(--cond);font-size:10.5px;font-weight:600;letter-spacing:.06em;
  text-transform:uppercase;color:var(--ink-3);text-align:left;padding:7px 10px;
  border-bottom:1px solid var(--line);white-space:nowrap;position:sticky;top:0;
  background:var(--surf);z-index:1}
th.sortable{cursor:pointer;user-select:none}
th.sortable:hover{color:var(--ink)}
th.sorted{color:var(--acc)}
td{padding:6px 10px;border-bottom:1px solid var(--line);vertical-align:top}
td.n{text-align:right;white-space:nowrap}
tbody tr:hover{background:var(--surf-2)}
tr.flagged td{background:var(--neg-soft)}
tr.flagged:hover td{background:var(--neg-soft);filter:brightness(.98)}

/* meters ------------------------------------------------------------------ */
.meter{position:relative;height:7px;background:var(--surf-3);border-radius:4px;
  overflow:hidden;min-width:70px}
.meter i{position:absolute;left:0;top:0;bottom:0;background:var(--acc);border-radius:4px}
.meter i.over{background:var(--neg)}
.meter .band{position:absolute;top:0;bottom:0;background:var(--acc-soft);opacity:.85}
.meter .tick{position:absolute;top:-2px;bottom:-2px;width:1.5px;background:var(--ink-2)}

/* filter bar -------------------------------------------------------------- */
.filters{display:flex;gap:7px;align-items:center;flex-wrap:wrap;padding:10px 15px;
  border-bottom:1px solid var(--line);background:var(--surf-2)}
.filters input[type=search],.filters select{font:inherit;font-size:12.5px;padding:4px 8px;
  border:1px solid var(--line-2);border-radius:4px;background:var(--surf);color:var(--ink)}
.filters input[type=search]{font-family:var(--mono);min-width:130px}
.chipbtn{font-family:var(--cond);font-size:11px;font-weight:600;letter-spacing:.04em;
  text-transform:uppercase;padding:3px 9px;border-radius:12px;border:1px solid var(--line-2);
  background:var(--surf);color:var(--ink-3);cursor:pointer}
.chipbtn[aria-pressed="true"]{background:var(--acc);border-color:var(--acc);color:var(--surf)}
:root[data-theme="dark"] .chipbtn[aria-pressed="true"],
:root:not([data-theme="light"]) .chipbtn[aria-pressed="true"]{color:#0C1211}

/* proposal / trigger cards ------------------------------------------------ */
.card{border-bottom:1px solid var(--line);padding:13px 15px;display:grid;
  grid-template-columns:170px 1fr auto;gap:14px;align-items:start}
.card:last-child{border-bottom:0}
.card .lhs{display:flex;flex-direction:column;gap:5px}
.card .act{font-family:var(--cond);font-weight:700;font-size:14.5px;letter-spacing:.01em}
.card .amt{font-family:var(--mono);font-size:15px;font-weight:500}
.card .why{font-size:12.5px;color:var(--ink-2);line-height:1.55}
.card .meta{font-family:var(--mono);font-size:10.5px;color:var(--ink-3);margin-top:5px}
.card ul{margin:6px 0 0;padding-left:16px}
.card li{font-size:12px;color:var(--ink-2);margin-bottom:3px}
.card .rhs{display:flex;flex-direction:column;gap:6px;align-items:flex-end;min-width:120px}
@media(max-width:720px){.card{grid-template-columns:1fr}.card .rhs{align-items:flex-start}}

.pair{border:1px solid var(--acc);border-radius:5px;margin:12px 15px;overflow:hidden}
.pair-head{background:var(--acc-soft);color:var(--acc);padding:6px 12px;
  font-family:var(--cond);font-weight:600;font-size:11.5px;letter-spacing:.05em;
  text-transform:uppercase}
.pair-legs{display:grid;grid-template-columns:1fr 1fr}
.pair-leg{padding:12px}
.pair-leg+.pair-leg{border-left:1px solid var(--line)}
@media(max-width:640px){.pair-legs{grid-template-columns:1fr}
  .pair-leg+.pair-leg{border-left:0;border-top:1px solid var(--line)}}

/* decisions --------------------------------------------------------------- */
.decide{display:flex;gap:5px;flex-wrap:wrap;align-items:center}
.decide button{font-family:var(--cond);font-size:11px;font-weight:600;letter-spacing:.04em;
  text-transform:uppercase;padding:4px 10px;border-radius:4px;border:1px solid var(--line-2);
  background:var(--surf);cursor:pointer}
.decide button:hover{border-color:var(--ink-3)}
.decide button.b-accept:hover{border-color:var(--pos);color:var(--pos)}
.decide button.b-reject:hover{border-color:var(--neg);color:var(--neg)}
.decide button:disabled{opacity:.5;cursor:default}
.decide input.reason{font:inherit;font-size:11.5px;padding:3px 7px;border-radius:4px;
  border:1px solid var(--line-2);background:var(--surf);color:var(--ink);width:150px}
.decide select{font:inherit;font-size:11.5px;padding:3px 5px;border-radius:4px;
  border:1px solid var(--line-2);background:var(--surf);color:var(--ink)}
.recorded{font-family:var(--mono);font-size:11px;color:var(--pos);
  background:var(--pos-soft);padding:3px 8px;border-radius:4px;display:inline-block}
.ro-banner{background:var(--warn-soft);color:var(--warn);border:1px solid var(--warn);
  border-radius:5px;padding:8px 12px;font-size:12.5px;margin-bottom:14px}

/* details ----------------------------------------------------------------- */
details{border-top:1px solid var(--line)}
details:first-of-type{border-top:0}
summary{cursor:pointer;padding:10px 15px;list-style:none}
summary::-webkit-details-marker{display:none}
summary::marker{display:none}
summary:hover{background:var(--surf-2)}
/* NEVER style <summary> itself as grid/flex -- several engines fall back to block flow and
   the children overlap. Wrap the row in a plain child div and grid THAT. (v1 landmine, kept.) */
.srow{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.srow .caret{color:var(--ink-3);font-family:var(--mono);font-size:11px;flex:none}
details[open] > summary .caret{color:var(--acc)}
.dbody{padding:2px 15px 15px;border-top:1px dashed var(--line)}

/* ticker sheet ------------------------------------------------------------ */
.sheet-back{position:fixed;inset:0;background:rgba(10,16,15,.42);z-index:60;
  opacity:0;pointer-events:none;transition:opacity .16s}
.sheet-back.on{opacity:1;pointer-events:auto}
.sheet{position:fixed;top:0;right:0;bottom:0;width:min(560px,94vw);background:var(--surf);
  border-left:1px solid var(--line);z-index:61;transform:translateX(100%);
  transition:transform .2s ease;overflow-y:auto;box-shadow:var(--shadow)}
.sheet.on{transform:none}
.sheet-head{position:sticky;top:0;background:var(--surf);border-bottom:1px solid var(--line);
  padding:14px 18px;display:flex;align-items:baseline;gap:10px;z-index:2}
.sheet-head h2{font-family:var(--mono);font-size:20px;font-weight:600}
.sheet-close{margin-left:auto;background:none;border:1px solid var(--line-2);border-radius:4px;
  width:26px;height:26px;cursor:pointer;color:var(--ink-3);line-height:1}
.sheet-sec{padding:14px 18px;border-bottom:1px solid var(--line)}
.sheet-sec h3{font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;
  color:var(--ink-3);margin-bottom:9px}
.kv{display:grid;grid-template-columns:auto 1fr;gap:3px 14px;font-size:12.5px}
.kv dt{color:var(--ink-3)}
.kv dd{margin:0;font-family:var(--mono);text-align:right}

/* the read ---------------------------------------------------------------- */
.read{padding:16px 18px 18px}
.rd-lead{margin:0;font-size:17px;line-height:1.5;max-width:60ch;letter-spacing:-.005em;
  font-weight:500;text-wrap:pretty}
.rd-body{margin-top:12px;display:flex;flex-direction:column;gap:9px;
  border-left:2px solid var(--line);padding-left:15px}
.rd-body p{margin:0;font-size:13.5px;line-height:1.62;max-width:66ch;color:var(--ink-2);
  text-wrap:pretty}
.rd-fig{font-family:var(--mono);font-size:.94em;color:var(--ink);
  font-variant-numeric:tabular-nums}
.rd-fwd{margin-top:16px;padding:11px 14px;background:var(--acc-soft);border-radius:5px;
  max-width:70ch}
.rd-fwd-k{display:block;font-family:var(--cond);font-size:10.5px;font-weight:600;
  letter-spacing:.08em;text-transform:uppercase;color:var(--acc);margin-bottom:5px}
.rd-fwd p{margin:0;font-size:13.5px;line-height:1.6;color:var(--ink);text-wrap:pretty}
.rd-fwd p+p{margin-top:6px}
.read .tk{font-size:.95em}

/* charts ------------------------------------------------------------------ */
.chart{width:100%;display:block;overflow:visible}
.chart text{font-family:var(--mono);font-size:9.5px;fill:var(--ink-3)}
.chart .axis{stroke:var(--line);stroke-width:1}
.chart .grid-l{stroke:var(--line);stroke-width:1;stroke-dasharray:2 3}
.legend{display:flex;gap:12px;flex-wrap:wrap;font-size:11.5px;color:var(--ink-2);
  padding:0 15px 12px;font-family:var(--mono)}
.legend i{width:9px;height:9px;border-radius:2px;display:inline-block;margin-right:5px}
.tm-cell text{font-family:var(--cond);font-weight:600}
.evbar{height:5px;border-radius:3px;background:var(--surf-3);overflow:hidden;display:flex}
.evbar i{display:block;height:100%}
</style>
"""


# --------------------------------------------------------------------------------------
# client app
# --------------------------------------------------------------------------------------

APP_JS = r"""<script>
"use strict";
/* Agent Smith dashboard v2 -- client renderer.
   Renders every tab from the embedded payload. A panel cannot be silently dropped: TABS
   below is the single manifest, and each entry names its renderer. */

var D = JSON.parse(document.getElementById("smith-payload").textContent);
var DEC = (function(){ try { return JSON.parse(
    document.getElementById("smith-decisions").textContent) || []; } catch(e){ return []; } })();

/* ---------- formatting ---------- */
function esc(s){ return String(s==null?"":s).replace(/[&<>"']/g, function(c){
  return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]; }); }
function n(v,d){ return (v==null||isNaN(v)) ? "—" : Number(v).toFixed(d==null?1:d); }
function usd(v,d){ if(v==null||isNaN(v)) return "—";
  var x=Number(v), s=x<0?"-":""; x=Math.abs(x);
  return s+"$"+x.toLocaleString("en-US",{minimumFractionDigits:d==null?0:d,
    maximumFractionDigits:d==null?0:d}); }
function pct(v,d){ return v==null||isNaN(v) ? "—" : n(v,d==null?1:d)+"%"; }
function signed(v,d){ if(v==null||isNaN(v)) return "—";
  return (v>0?"+":"")+n(v,d==null?1:d)+"%"; }
function cls(v){ return v==null||isNaN(v) ? "" : (v>0?"pos":(v<0?"neg":"")); }
function el(tag,attrs,html){ var a=""; for(var k in attrs){ if(attrs[k]==null) continue;
  a+=" "+k+'="'+esc(attrs[k])+'"'; } return "<"+tag+a+">"+(html||"")+"</"+tag+">"; }
function tk(t,extra){ if(!t) return "—";
  return '<button class="tk'+(extra||"")+'" data-tk="'+esc(t)+'">'+esc(t)+'</button>'; }
function tks(list,extra){ return (list||[]).map(function(t){ return tk(t,extra); }).join(" "); }
function dirPill(d){ if(!d) return "";
  var k=String(d).toLowerCase();
  var c = /buy|add|accum/.test(k)?"buy" : /sell|trim|exit/.test(k)?"sell" :
          /hold|stop/.test(k)?"hold" : "info";
  return '<span class="pill '+c+'">'+esc(d)+"</span>"; }
function thDot(s){ return '<span class="dot '+esc(s||"none")+'" title="thesis: '+
  esc(s||"none")+'"></span>'; }
function human(k){ return String(k||"").replace(/_/g," ")
  .replace(/\b\w/g,function(c){return c.toUpperCase();}); }

/* cluster colors -- stable assignment so a cluster keeps its hue across tabs and charts */
var CCOL={};
(function(){ var v=["--c1","--c2","--c3","--c4","--c5","--c6","--c7","--c8"], i=0;
  (D.clusters||[]).forEach(function(c){ CCOL[c.name]="var("+v[i++%v.length]+")"; });
  (D.positions||[]).forEach(function(p){ if(!CCOL[p.cluster])
    CCOL[p.cluster]="var("+v[i++%v.length]+")"; }); })();

var POS_BY={}; (D.positions||[]).forEach(function(p){ POS_BY[p.t]=p; });

/* ---------- small building blocks ---------- */
function panel(title,sub,body,opts){
  opts=opts||{};
  var right = opts.right ? '<div class="right">'+opts.right+"</div>" : "";
  return '<section class="panel'+(opts.sev?" sev-"+opts.sev:"")+
    (opts.span?" span2":"")+'">'+
    "<header><h2>"+esc(title)+"</h2>"+
    (sub?'<span class="sub">'+esc(sub)+"</span>":"")+right+"</header>"+
    (body||'<p class="empty">Nothing to show.</p>')+"</section>";
}
function meter(v,cap,band){
  var w=Math.max(0,Math.min(100,(v/(cap||100))*100));
  var b="";
  if(band && band.length===2 && cap){
    var l=(band[0]/cap)*100, r=(band[1]/cap)*100;
    b='<span class="band" style="left:'+l+'%;width:'+Math.max(0,r-l)+'%"></span>';
  }
  return '<span class="meter">'+b+'<i class="'+(v>((band&&band[1])||cap)?"over":"")+
    '" style="width:'+w+'%"></i></span>';
}
function detailsRow(summaryHtml,bodyHtml,open){
  return "<details"+(open?" open":"")+"><summary>"+
    '<div class="srow"><span class="caret">▸</span>'+summaryHtml+"</div></summary>"+
    '<div class="dbody">'+bodyHtml+"</div></details>";
}
function table(cols,rows,opts){
  opts=opts||{};
  var head=cols.map(function(c,i){
    return '<th class="'+(c.n?"n ":"")+(opts.sortKey?"sortable":"")+
      (opts.sortIdx===i?" sorted":"")+'"'+(opts.sortKey?' data-sort="'+opts.sortKey+
      '" data-col="'+i+'"':"")+">"+esc(c.h)+(opts.sortIdx===i?
      (opts.sortDir<0?" ↓":" ↑"):"")+"</th>"; }).join("");
  return '<div class="tbl-scroll"><table><thead><tr>'+head+"</tr></thead><tbody>"+
    rows.join("")+"</tbody></table></div>";
}
function decideBox(surface,id,extra){
  var rec=null;
  for(var i=DEC.length-1;i>=0;i--){
    if(DEC[i].surface===surface && DEC[i].element_id===id){ rec=DEC[i]; break; } }
  if(rec) return '<span class="recorded">Recorded: '+esc(rec.decision)+
    (rec.reason?" — "+esc(rec.reason):"")+" (syncs next run)</span>";
  var B={proposal:[["accept","Accept","b-accept"],["reject","Reject","b-reject"],
                   ["hold","Hold","b-hold"]],
         auto_retired_proposal:[["revive","Revive","b-revive"]],
         watchlist:[["watch_closely","Watch closely","b-watch"],
                    ["not_interested","Not interested","b-reject"]],
         diversifier:[["not_interested","Not interested","b-reject"]],
         derisk:[["disagree","Disagree — not fragile","b-reject"]],
         gap:[["resolve","Mark resolved","b-accept"]],
         learning_param:[["approve","Approve","b-accept"],["defer","Defer","b-hold"]],
         thesis:[["confirm","Confirm","b-accept"],["override","Override","b-hold"]],
         catalyst:[["priced_in","Already priced in","b-hold"]]}[surface]||[];
  var btns=B.map(function(b){ return '<button type="button" class="'+b[2]+
    '" data-decision="'+b[0]+'">'+esc(b[1])+"</button>"; }).join("");
  var sel = surface==="thesis" ? '<select class="new-status" aria-label="new thesis status">'+
    ["strengthening","intact","watch","broken"].map(function(s){
      return '<option value="'+s+'">'+s+"</option>"; }).join("")+"</select>" : "";
  return '<div class="decide" data-surface="'+esc(surface)+'" data-element-id="'+esc(id)+'"'+
    (extra||"")+">"+btns+sel+
    '<input class="reason" type="text" placeholder="reason (optional)" maxlength="200"></div>';
}

/* ---------- charts (SVG, drawn to one scale, labels inside the viewBox) ---------- */
function lineChart(series,opts){
  opts=opts||{};
  var W=opts.w||720,H=opts.h||190,ml=52,mr=14,mt=12,mb=24;
  var pts=series.filter(function(p){ return p.trust!=="bad" && p.v!=null; });
  if(pts.length<2) return '<p class="empty">Not enough trusted points to plot.</p>';
  var vals=pts.map(function(p){ return p.v; }).concat(
           opts.stack? pts.map(function(p){ return p.v+(p.w||0); }) : []);
  var lo=Math.min.apply(null,vals), hi=Math.max.apply(null,vals);
  var pad=(hi-lo)*0.12||1; lo-=pad; hi+=pad;
  var x=function(i){ return ml+(i/(pts.length-1))*(W-ml-mr); };
  var y=function(v){ return mt+(1-(v-lo)/(hi-lo))*(H-mt-mb); };
  var gridv=[lo,(lo+hi)/2,hi], g="",ticks="";
  gridv.forEach(function(v){
    g+='<line class="grid-l" x1="'+ml+'" x2="'+(W-mr)+'" y1="'+y(v)+'" y2="'+y(v)+'"/>';
    ticks+='<text x="'+(ml-6)+'" y="'+(y(v)+3)+'" text-anchor="end">'+
      usd(v)+"</text>"; });
  var d="",area="";
  pts.forEach(function(p,i){ d+=(i?"L":"M")+x(i).toFixed(1)+" "+y(p.v).toFixed(1)+" "; });
  area=d+"L"+x(pts.length-1).toFixed(1)+" "+(H-mb)+" L"+ml+" "+(H-mb)+" Z";
  var stackPath="";
  if(opts.stack){
    pts.forEach(function(p,i){ stackPath+=(i?"L":"M")+x(i).toFixed(1)+" "+
      y(p.v+(p.w||0)).toFixed(1)+" "; });
  }
  var marks=pts.map(function(p,i){
    return '<circle cx="'+x(i).toFixed(1)+'" cy="'+y(p.v).toFixed(1)+'" r="'+
      (i===pts.length-1?3.6:2)+'" fill="'+(i===pts.length-1?"var(--acc)":"var(--acc)")+
      '" opacity="'+(i===pts.length-1?1:.5)+'"><title>'+esc(p.ts)+" · "+usd(p.v)+
      (p.note?" · "+esc(p.note):"")+"</title></circle>"; }).join("");
  var bad=series.filter(function(p){ return p.trust==="bad"; }).length;
  var xl='<text x="'+ml+'" y="'+(H-6)+'">'+esc(pts[0].ts)+"</text>"+
         '<text x="'+(W-mr)+'" y="'+(H-6)+'" text-anchor="end">'+
         esc(pts[pts.length-1].ts)+"</text>";
  return '<svg class="chart" viewBox="0 0 '+W+" "+H+'" role="img" aria-label="'+
    esc(opts.label||"time series")+'">'+g+
    '<path d="'+area+'" fill="var(--acc)" opacity=".10"/>'+
    (stackPath?'<path d="'+stackPath+'" fill="none" stroke="var(--c2)" stroke-width="1.4" '+
      'stroke-dasharray="3 3"/>':"")+
    '<path d="'+d+'" fill="none" stroke="var(--acc)" stroke-width="1.8" '+
    'stroke-linejoin="round"/>'+marks+ticks+xl+
    '<line class="axis" x1="'+ml+'" x2="'+(W-mr)+'" y1="'+(H-mb)+'" y2="'+(H-mb)+'"/>'+
    (bad?'<text x="'+ml+'" y="'+(mt+2)+'" fill="var(--warn)">'+bad+
      " untrusted row(s) excluded</text>":"")+"</svg>";
}

function barsHChart(rows,opts){
  opts=opts||{};
  var W=opts.w||700, rowH=opts.rowH||20, mt=8, ml=opts.ml||78, mr=70;
  var H=mt+rows.length*rowH+10;
  var mx=Math.max.apply(null,rows.map(function(r){
    return Math.max(Math.abs(r.v)||0, Math.abs(r.cap)||0); }))||1;
  var x=function(v){ return ml+(v/mx)*(W-ml-mr); };
  var body=rows.map(function(r,i){
    var y=mt+i*rowH, h=rowH-7;
    var capMark = r.cap!=null ? '<line x1="'+x(r.cap).toFixed(1)+'" x2="'+x(r.cap).toFixed(1)+
      '" y1="'+(y-1)+'" y2="'+(y+h+1)+'" stroke="var(--ink-2)" stroke-width="1.3"/>' : "";
    return '<g><text x="'+(ml-7)+'" y="'+(y+h-1)+'" text-anchor="end">'+esc(r.label)+"</text>"+
      '<rect x="'+ml+'" y="'+y+'" width="'+Math.max(0,x(r.v)-ml).toFixed(1)+'" height="'+h+
      '" rx="2" fill="'+(r.color||"var(--acc)")+'" opacity="'+(r.over?1:.82)+'">'+
      "<title>"+esc(r.title||r.label)+"</title></rect>"+capMark+
      '<text x="'+(x(Math.max(r.v,r.cap||0))+7).toFixed(1)+'" y="'+(y+h-1)+
      '" fill="'+(r.over?"var(--neg)":"var(--ink-2)")+'">'+esc(r.vlabel)+"</text></g>"; }).join("");
  return '<svg class="chart" viewBox="0 0 '+W+" "+H+'" role="img" aria-label="'+
    esc(opts.label||"bars")+'">'+body+"</svg>";
}

function divergingBars(rows,opts){
  opts=opts||{};
  var W=opts.w||620, rowH=22, mt=10, ml=110, H=mt+rows.length*rowH+16;
  var mx=Math.max.apply(null,rows.map(function(r){ return Math.abs(r.v)||0; }))||1;
  var mid=ml+(W-ml-58)/2, half=(W-ml-58)/2;
  var body=rows.map(function(r,i){
    var y=mt+i*rowH, h=rowH-8, w=(Math.abs(r.v)/mx)*half;
    var x0=r.v>=0?mid:mid-w;
    return '<g><text x="'+(ml-8)+'" y="'+(y+h-1)+'" text-anchor="end">'+esc(r.label)+"</text>"+
      '<rect x="'+x0.toFixed(1)+'" y="'+y+'" width="'+w.toFixed(1)+'" height="'+h+
      '" rx="2" fill="'+(r.v>=0?"var(--pos)":"var(--neg)")+'" opacity=".85"><title>'+
      esc(r.title||"")+"</title></rect>"+
      '<text x="'+(W-52)+'" y="'+(y+h-1)+'" fill="var(--ink-2)">'+esc(r.vlabel)+
      "</text></g>"; }).join("");
  return '<svg class="chart" viewBox="0 0 '+W+" "+H+'" role="img" aria-label="'+
    esc(opts.label||"diverging bars")+'">'+
    '<line class="axis" x1="'+mid+'" x2="'+mid+'" y1="'+mt+'" y2="'+(H-14)+'"/>'+
    body+"</svg>";
}

/* squarified treemap */
function treemap(items,opts){
  opts=opts||{};
  var W=opts.w||760,H=opts.h||330;
  var tot=items.reduce(function(a,b){ return a+b.v; },0)||1;
  var out=[], stack=items.slice().sort(function(a,b){ return b.v-a.v; });
  function worst(row,len,scale){
    var s=row.reduce(function(a,b){ return a+b.v*scale; },0);
    var mn=Math.min.apply(null,row.map(function(r){ return r.v*scale; }));
    var mx=Math.max.apply(null,row.map(function(r){ return r.v*scale; }));
    return Math.max((len*len*mx)/(s*s),(s*s)/(len*len*mn));
  }
  function layout(list,x,y,w,h){
    if(!list.length) return;
    if(list.length===1){ out.push({d:list[0],x:x,y:y,w:w,h:h}); return; }
    var scale=(w*h)/list.reduce(function(a,b){ return a+b.v; },0);
    var vert=w>=h, len=vert?h:w, row=[], i=0;
    while(i<list.length){
      var next=row.concat([list[i]]);
      if(row.length && worst(row,len,scale)<worst(next,len,scale)) break;
      row=next; i++;
    }
    var rs=row.reduce(function(a,b){ return a+b.v; },0)*scale;
    var thick=rs/len, off=0;
    row.forEach(function(r){
      var sz=(r.v*scale)/thick;
      if(vert) out.push({d:r,x:x,y:y+off,w:thick,h:sz});
      else out.push({d:r,x:x+off,y:y,w:sz,h:thick});
      off+=sz;
    });
    if(vert) layout(list.slice(i),x+thick,y,w-thick,h);
    else layout(list.slice(i),x,y+thick,w,h-thick);
  }
  layout(stack,0,0,W,H);
  var body=out.map(function(c){
    var d=c.d, showT=c.w>34&&c.h>20, showP=c.w>46&&c.h>34;
    return '<g class="tm-cell"><rect x="'+c.x.toFixed(1)+'" y="'+c.y.toFixed(1)+
      '" width="'+Math.max(0,c.w-1.5).toFixed(1)+'" height="'+Math.max(0,c.h-1.5).toFixed(1)+
      '" rx="2" fill="'+d.color+'" opacity="'+(d.over?.95:.78)+
      '" stroke="'+(d.over?"var(--neg)":"none")+'" stroke-width="'+(d.over?1.6:0)+'"/>'+
      "<title>"+esc(d.title)+"</title>"+
      (showT?'<text x="'+(c.x+6).toFixed(1)+'" y="'+(c.y+15).toFixed(1)+
        '" fill="#fff" font-size="11">'+esc(d.label)+"</text>":"")+
      (showP?'<text x="'+(c.x+6).toFixed(1)+'" y="'+(c.y+28).toFixed(1)+
        '" fill="#fff" font-size="9.5" opacity=".9">'+esc(d.sub)+"</text>":"")+
      "</g>"; }).join("");
  return '<svg class="chart" viewBox="0 0 '+W+" "+H+'" role="img" aria-label="'+
    esc(opts.label||"treemap")+'">'+body+"</svg>";
}

function gauge(score,band){
  var W=220,H=124,cx=110,cy=104,r=82;
  function pt(v){ var a=Math.PI*(1-v/100);
    return [cx+r*Math.cos(a),cy-r*Math.sin(a)]; }
  var segs=[[0,25,"var(--neg)"],[25,45,"var(--warn)"],[45,55,"var(--ink-3)"],
            [55,75,"var(--c6)"],[75,100,"var(--pos)"]];
  var arcs=segs.map(function(s){
    var a=pt(s[0]),b=pt(s[1]);
    return '<path d="M'+a[0].toFixed(1)+" "+a[1].toFixed(1)+" A"+r+" "+r+" 0 0 1 "+
      b[0].toFixed(1)+" "+b[1].toFixed(1)+'" fill="none" stroke="'+s[2]+
      '" stroke-width="12" opacity=".8"/>'; }).join("");
  var np=pt(Math.max(0,Math.min(100,score||0)));
  return '<svg class="chart" viewBox="0 0 '+W+" "+H+'" role="img" aria-label="sentiment '+
    esc(n(score,1))+'">'+arcs+
    '<line x1="'+cx+'" y1="'+cy+'" x2="'+np[0].toFixed(1)+'" y2="'+np[1].toFixed(1)+
    '" stroke="var(--ink)" stroke-width="2.4" stroke-linecap="round"/>'+
    '<circle cx="'+cx+'" cy="'+cy+'" r="4" fill="var(--ink)"/>'+
    '<text x="'+cx+'" y="'+(cy-16)+'" text-anchor="middle" font-size="26" '+
    'fill="var(--ink)" font-weight="600">'+esc(n(score,1))+"</text>"+
    '<text x="'+cx+'" y="'+(cy+16)+'" text-anchor="middle" font-size="11" '+
    'fill="var(--ink-3)">'+esc(String(band||"").toUpperCase())+"</text>"+
    '<text x="20" y="'+(cy+16)+'" font-size="9">FEAR</text>'+
    '<text x="'+(W-20)+'" y="'+(cy+16)+'" font-size="9" text-anchor="end">GREED</text></svg>';
}

/* The session read arrives as one unbroken block of prose. Rendering it as a single
   paragraph buries the three things it actually carries -- the finding, what changed, and
   what happens next -- so it gets parsed into those roles instead. Every known ticker
   becomes a click into that name's sheet, and figures/dates are set in the mono face so
   they scan the way they do everywhere else on the page. */
var TICKER_RE = null;
(function(){
  var known = {};
  (D.positions||[]).forEach(function(p){ known[p.t]=1; });
  Object.keys(D.thesis||{}).forEach(function(t){ known[t]=1; });
  Object.keys(D.signals||{}).forEach(function(t){ known[t]=1; });
  (D.watchlist||[]).forEach(function(w){ if(w.ticker) known[w.ticker]=1; });
  Object.keys(D.diversifiers||{}).forEach(function(t){ known[t]=1; });
  var list = Object.keys(known).filter(function(t){ return /^[A-Z]{1,5}$/.test(t); })
    .sort(function(a,b){ return b.length-a.length; });
  TICKER_RE = list.length ? new RegExp("\\b("+list.join("|")+")\\b","g") : null;
})();

function markupRead(sentence){
  var out = esc(sentence).replace(/\s--\s/g, " \u2014 ");
  /* figures first, so a ticker inserted later cannot be re-matched inside markup */
  out = out.replace(/(\$[\d,]+(?:\.\d+)?|[-+]?\d+(?:\.\d+)?%|\b\d{4}-\d{2}-\d{2}\b)/g,
    '<span class="rd-fig">$1</span>');
  if(TICKER_RE) out = out.replace(TICKER_RE, function(m){
    return '<button class="tk" data-tk="'+m+'">'+m+"</button>"; });
  return out;
}

function renderRead(text){
  /* split on sentence ends, but never inside a decimal or a $1,016.83 */
  var parts = String(text).split(/(?<=[.!?])\s+(?=[A-Z(])/).map(function(x){
    return x.trim(); }).filter(Boolean);
  if(!parts.length) return '<p class="empty">No read recorded for this run.</p>';

  var FWD = /^(looking ahead|ahead|next|going forward|watch for|the next)\b/i;
  var FWD_MARK = /^(looking ahead|going forward|ahead)\s*[:,-]+\s*/i;
  var lead = parts[0];
  var body = [], fwd = [];
  parts.slice(1).forEach(function(sn){ (FWD.test(sn) ? fwd : body).push(sn); });
  /* a forward-looking clause is often welded onto the last sentence with a colon */
  if(!fwd.length && body.length){
    var last = body[body.length-1];
    var m = last.match(/^(.*?)(\bLooking ahead:\s*)(.+)$/i);
    if(m){ body[body.length-1] = m[1].trim(); fwd.push(m[3]);
      if(!body[body.length-1]) body.pop(); }
  }

  return '<div class="read">'+
    '<p class="rd-lead">'+markupRead(lead)+"</p>"+
    (body.length ? '<div class="rd-body">'+body.map(function(sn){
      return "<p>"+markupRead(sn)+"</p>"; }).join("")+"</div>" : "")+
    (fwd.length ? '<div class="rd-fwd"><span class="rd-fwd-k">What happens next</span>'+
      fwd.map(function(sn){
        return "<p>"+markupRead(sn.replace(FWD_MARK,"")); }).join("</p>")+"</p></div>" : "")+
    "</div>";
}

/* ====================================================================== TAB: COMMAND */
function tabCommand(){
  var H=[], k=D.kpi;

  /* the read */
  if(D.read) H.push(panel("The read", D.meta.mode+" run · "+D.meta.ts.slice(0,16),
    renderRead(D.read),{span:true}));

  /* macro strip + sentiment */
  var m=D.macro;
  var macroCells=[
    ["10-yr", pct(m.us10y,3)], ["VIX", n(m.vix,2)+
      (m.vix_prev? ' <span class="'+cls(m.vix-m.vix_prev)+'">'+
        signed(((m.vix-m.vix_prev)/m.vix_prev)*100,2)+"</span>":"")],
    ["DXY", n(m.dxy,2)], ["SMH", n(m.smh,2)+' <span class="'+cls(m.smh_chg)+'">'+
      signed((m.smh_chg||0)*100,2)+"</span>"],
    ["ES fut", '<span class="'+cls(m.es_chg)+'">'+signed((m.es_chg||0)*100,2)+"</span>"],
    ["NQ fut", '<span class="'+cls(m.nq_chg)+'">'+signed((m.nq_chg||0)*100,2)+"</span>"],
    ["Fed funds", pct(m.fed,2)+' <span class="muted">'+esc(m.fomc||"")+"</span>"],
    ["Beta vs "+esc(k.beta_bm||"SMH"), n(k.beta,2)]
  ];
  var asia=Object.keys(m.asia||{}).map(function(key){
    return "<dt>"+esc(human(key.replace(/_chg_pct$/,"")))+"</dt><dd class=\""+
      cls(m.asia[key])+"\">"+signed((m.asia[key]||0)*100,2)+"</dd>"; }).join("");
  H.push(panel("Market context", m.session||"", '<div class="pad">'+
    '<div class="grid g3" style="gap:10px 18px">'+
    macroCells.map(function(c){
      return '<div><span class="k" style="font-family:var(--cond);font-size:10.5px;'+
        'letter-spacing:.07em;text-transform:uppercase;color:var(--ink-3);display:block">'+
        c[0]+'</span><span class="num" style="font-size:15px">'+c[1]+"</span></div>"; }).join("")+
    "</div>"+
    (m.gate?'<p class="note" style="margin-top:12px"><span class="pill '+
      (m.gate==="STABILIZING"?"buy":m.gate==="AMBIGUOUS"?"hold":"sell")+'">gate '+
      esc(m.gate)+"</span> "+esc(m.gate_reason||"")+"</p>":"")+
    (m.regime_note?'<p class="note" style="margin-top:8px"><b>Regime '+esc(m.regime||"")+
      ".</b> "+esc(m.regime_note)+"</p>":"")+
    (asia?'<dl class="kv" style="margin-top:12px;max-width:340px">'+asia+"</dl>":"")+
    "</div>",{span:true}));

  var sc=k.sent_components||{};
  H.push(panel("Sentiment","composite · "+esc(k.sent_band||""),
    '<div class="pad" style="display:flex;gap:18px;align-items:center;flex-wrap:wrap">'+
    gauge(k.sent_score,k.sent_band)+
    '<dl class="kv" style="flex:1;min-width:190px">'+
    Object.keys(sc).map(function(key){ return "<dt>"+esc(human(key))+"</dt><dd>"+
      n(sc[key],1)+"</dd>"; }).join("")+"</dl></div>"));

  /* open proposals */
  var props=D.proposals.open||[];
  var pairs={}, singles=[];
  props.forEach(function(p){ if(p.pair_id){ (pairs[p.pair_id]=pairs[p.pair_id]||[]).push(p); }
    else singles.push(p); });
  var body="";
  Object.keys(pairs).forEach(function(pid){
    var legs=pairs[pid];
    body+='<div class="pair"><div class="pair-head">Rotation · '+esc(pid)+
      '</div><div class="pair-legs">'+legs.map(function(p){
        return '<div class="pair-leg">'+propCardInner(p)+"</div>"; }).join("")+"</div></div>";
  });
  ["HIGH","MEDIUM","LOW"].forEach(function(tier){
    var rows=singles.filter(function(p){ return (p.priority||"LOW")===tier; });
    if(!rows.length) return;
    var inner=rows.map(propCard).join("");
    body+=detailsRow('<span class="pill '+tier.toLowerCase()+'">'+tier+"</span>"+
      '<span class="muted">'+rows.length+" proposal"+(rows.length>1?"s":"")+" · "+
      usd(rows.reduce(function(a,b){ return a+(b.size||0); },0))+"</span>",
      inner, tier==="HIGH");
  });
  H.push(panel("Open proposals", props.length+" live · advisory only, never executed",
    body||null,{span:true, sev: props.some(function(p){ return p.priority==="HIGH"; })?
      "warn":null}));

  /* accepted awaiting execution */
  if((D.proposals.accepted||[]).length){
    H.push(panel("Accepted — awaiting execution",
      "stated intent, not a confirmed fill",
      D.proposals.accepted.map(propCard).join(""),{span:true,sev:"ok"}));
  }

  /* live triggers */
  H.push(panel("Live triggers",
    "as of "+esc(D.triggers.as_of||"")+" · RSI "+D.triggers.rsi_age+
    "d old, coverage "+pct(D.triggers.rsi_cov,0),
    triggerBody(),{span:true}));

  /* factor catalysts */
  var cats=D.catalysts||[];
  if(cats.length){
    H.push(panel("Factor catalysts", D.catalysts_as_of||"",
      cats.map(function(c,i){
        var dirc=c.direction==="threat"?"sell":c.direction==="tailwind"?"buy":"hold";
        return '<div class="card"><div class="lhs">'+
          '<span class="pill '+dirc+'">'+esc(c.direction||"")+"</span>"+
          '<span class="meta">'+esc(c.date||"")+" · "+esc(c.horizon||"")+"</span>"+
          '<span class="meta">'+pct(c.exposure,1)+" of equity</span></div>"+
          '<div><p class="why" style="margin:0 0 6px"><b>'+esc(c.headline)+"</b></p>"+
          (c.magnitude?'<p class="why" style="margin:0 0 6px">'+esc(c.magnitude)+"</p>":"")+
          '<div class="meta">Affects: '+tks(c.affects)+"</div>"+
          (c.sources&&c.sources.length?'<div class="meta">'+c.sources.filter(Boolean)
            .map(function(s){ return '<a href="'+esc(s)+
              '" target="_blank" rel="noopener">source</a>'; }).join(" · ")+"</div>":"")+
          "</div>"+
          '<div class="rhs">'+decideBox("catalyst","catalyst-"+i,
            ' data-headline="'+esc(c.headline)+'" data-date="'+esc(c.date||"")+'"')+
          "</div></div>"; }).join(""),
      {span:true, sev: cats.some(function(c){ return c.direction==="threat"; })?"warn":null}));
  }

  /* week ahead */
  var wk=(D.macro.week||[]);
  H.push(panel("The week ahead","next 10 days",
    wk.length? table([{h:"Date"},{h:"Event"},{h:"Type"},{h:"Confirmed"}],
      wk.map(function(w){
        return "<tr><td class=\"n mono\">"+esc(w.date)+"</td><td>"+
          (w.t? tk(w.t)+" earnings" : esc(w.what))+"</td><td>"+
          '<span class="pill '+(w.kind==="macro"?"info":"acc")+'">'+esc(w.kind)+
          "</span></td><td>"+(w.confirmed?"yes":'<span class="muted">estimated</span>')+
          "</td></tr>"; })) : null));

  return H.join("");
}

function propCardInner(p){
  var stale = (p.flags||[]).length>0;
  return '<div class="lhs">'+
    '<span class="act">'+esc(p.action||"")+"</span>"+
    '<span class="amt">'+usd(p.size)+"</span>"+
    (p.cluster?'<span class="pill">'+esc(p.cluster)+"</span>":"")+
    '<span class="meta">'+esc(p.id||"")+" · "+esc(p.date||"")+"</span></div>"+
    "<div>"+dirPill(p.dir)+" "+
    (p.trigger?'<span class="pill info">'+esc(p.trigger)+"</span> ":"")+
    (p.priority?'<span class="pill '+String(p.priority).toLowerCase()+'">'+
      esc(p.priority)+"</span>":"")+
    '<p class="why" style="margin:7px 0 0">'+esc(p.rationale||"")+"</p>"+
    ((p.valid||[]).length?"<ul>"+p.valid.map(function(v){
      return "<li>"+esc(v)+"</li>"; }).join("")+"</ul>":"")+
    (stale?'<p class="meta warnc">⚠ '+p.flags.map(esc).join(" · ")+"</p>":"")+
    (p.tranche?'<p class="meta">'+esc(p.tranche)+"</p>":"")+
    (p.retires?'<p class="meta">Retires when: '+esc(p.retires)+"</p>":"")+
    (p.px0!=null?'<p class="meta">Proposed at '+usd(p.px0,2)+
      (p.px1!=null?" · now "+usd(p.px1,2):"")+
      (p.drift!=null?" ("+signed(p.drift,1)+")":"")+"</p>":"")+
    "</div>"+
    '<div class="rhs">'+tk(p.t)+decideBox("proposal",p.id)+"</div>";
}
function propCard(p){ return '<div class="card">'+propCardInner(p)+"</div>"; }

function triggerBody(){
  var fams=D.triggers.families||{}, keys=Object.keys(fams);
  if(!keys.length) return '<p class="empty">No triggers fired this run.</p>';
  var order=["catalyst_threat","thesis_break","cluster_rotation","profit_rotation",
    "laggard_rotation","cluster_bench_rotation","cluster_consolidation","conviction_exit",
    "conviction_average","oversold_reversion","overbought_distribution","trend_entry",
    "trend_breakdown","profit_ratchet","scale_out_ladder","entry_setup","reentry",
    "bench_diversifier"];
  keys.sort(function(a,b){ var i=order.indexOf(a),j=order.indexOf(b);
    return (i<0?99:i)-(j<0?99:j); });
  return keys.map(function(f){
    var rows=fams[f], live=rows.filter(function(r){ return r.vote==="live"; }).length;
    var inner=rows.map(function(r){
      if(r.paired){
        return '<div class="pair"><div class="pair-head">'+esc(r.pair_id||"rotation")+
          (r.ladder_driven?" · ladder-driven ("+esc(r.ladder_conf||"")+")":"")+
          '</div><div class="pair-legs">'+
          [["sell",r.sell],["buy",r.buy]].map(function(x){
            var leg=x[1]||{};
            return '<div class="pair-leg">'+dirPill(leg.dir)+" "+tk(leg.t)+
              ' <span class="amt num">'+usd(leg.size)+"</span>"+
              "<ul>"+(leg.reasons||[]).map(function(s){
                return "<li>"+esc(s)+"</li>"; }).join("")+"</ul></div>"; }).join("")+
          "</div>"+
          ((r.blockers||[]).length?'<p class="meta" style="padding:0 12px 10px">'+
            "⚠ "+r.blockers.map(esc).join(" · ")+"</p>":"")+"</div>";
      }
      return '<div class="card"><div class="lhs">'+tk(r.t)+dirPill(r.dir)+
        '<span class="pill '+(r.vote==="live"?"live":"shadow")+'">'+esc(r.vote||"")+
        "</span>"+(r.size?'<span class="amt">'+usd(r.size)+"</span>":"")+"</div><div>"+
        '<div class="meta">'+esc(r.cluster||"")+" · thesis "+esc(r.thesis||"n/a")+
        (r.rsi!=null?" · RSI "+n(r.rsi,0):"")+
        (r.rel!=null?" · rel "+signed(r.rel,1)+"pp":"")+
        (r.ret1m!=null?" · 1m "+signed(r.ret1m,1):"")+"</div>"+
        "<ul>"+(r.reasons||[]).map(function(s){ return "<li>"+esc(s)+"</li>"; }).join("")+
        "</ul>"+
        (r.stop_new!=null?'<p class="meta">Stop '+usd(r.stop_now,2)+" → "+
          usd(r.stop_new,2)+(r.gain_at_risk!=null?" · "+usd(r.gain_at_risk)+
          " of gain at risk":"")+"</p>":"")+
        ((r.blockers||[]).length?'<p class="meta warnc">⚠ '+
          r.blockers.map(esc).join(" · ")+"</p>":"")+
        ((r.sources||[]).length?'<p class="meta">'+r.sources.filter(Boolean).map(function(s){
          return '<a href="'+esc(s)+'" target="_blank" rel="noopener">source</a>'; })
          .join(" · ")+"</p>":"")+
        "</div><div class=\"rhs\"></div></div>";
    }).join("");
    return detailsRow('<b style="font-family:var(--cond);font-size:13px">'+
      esc(human(f))+"</b>"+
      '<span class="pill '+(live?"live":"shadow")+'">'+live+" live</span>"+
      '<span class="muted">'+rows.length+" total</span>",
      inner, live>0 && ["catalyst_threat","thesis_break","cluster_rotation"].indexOf(f)>=0);
  }).join("");
}

/* ========================================================================= TAB: BOOK */
var posSort={key:"wt",dir:-1};
function tabBook(){
  var H=[], k=D.kpi;

  /* treemap */
  var items=(D.positions||[]).map(function(p){
    return {v:p.val||0, color:CCOL[p.cluster]||"var(--c8)", label:p.t,
      sub:pct(p.wt,1), over:p.over_cap,
      title:p.t+" · "+p.cluster+" · "+usd(p.val)+" · "+pct(p.wt,2)+
        (p.over_cap?" · OVER ATR RISK CAP":"")}; });
  var legend=(D.clusters||[]).map(function(c){
    return '<span><i style="background:'+CCOL[c.name]+'"></i>'+esc(c.name)+"</span>"; }).join("");
  H.push(panel("Allocation", k.count+" positions · red outline = over its ATR risk cap",
    '<div class="pad">'+treemap(items,{label:"allocation treemap"})+"</div>"+
    '<div class="legend">'+legend+"</div>",{span:true}));

  /* clusters */
  H.push(panel("Clusters","% of invested equity vs policy band",
    (D.clusters||[]).map(clusterRow).join(""),{span:true}));

  /* positions table */
  H.push(panel("Positions", k.count+" holdings",
    '<div class="filters">'+
    '<input type="search" id="posq" placeholder="filter ticker…" value="">'+
    '<select id="posc"><option value="">All clusters</option>'+
    (D.clusters||[]).map(function(c){ return '<option>'+esc(c.name)+"</option>"; }).join("")+
    "</select>"+
    '<button class="chipbtn" id="posover" aria-pressed="false">Over cap only</button>'+
    '<button class="chipbtn" id="posbroken" aria-pressed="false">Thesis not intact</button>'+
    "</div>"+'<div id="postbl">'+positionsTable()+"</div>",{span:true}));

  /* risk caps + LTCG */
  var breaches=(D.positions||[]).filter(function(p){ return p.over_cap; });
  H.push(panel("Risk-cap breaches",
    "ATR-based caps · aggregate "+pct(k.risk_pct,2)+" of "+pct(k.risk_cap,0),
    breaches.length? table([{h:"Ticker"},{h:"Cluster"},{h:"Value",n:1},{h:"Cap",n:1},
      {h:"Over by",n:1},{h:"× cap",n:1},{h:"ATR20",n:1}],
      breaches.sort(function(a,b){ return (b.cap_mult||0)-(a.cap_mult||0); })
      .map(function(p){
        return '<tr class="flagged"><td>'+tk(p.t)+"</td><td>"+esc(p.cluster)+
          '</td><td class="n">'+usd(p.val)+'</td><td class="n">'+usd(p.cap)+
          '</td><td class="n neg">'+usd(Math.abs(p.headroom||0))+
          '</td><td class="n">'+n(p.cap_mult,2)+'</td><td class="n">'+pct(p.atr,1)+
          "</td></tr>"; }))
      : '<p class="pad" style="color:var(--pos);margin:0">Every position inside its ATR risk cap.</p>',
    {sev:breaches.length?"bad":"ok"}));

  var lt=(D.tax||{});
  var ltrows=(lt.ltcg_window&&lt.ltcg_window.lots)||[];
  H.push(panel("LTCG watch", lt.as_of||"",
    ltrows.length? table([{h:"Ticker"},{h:"Lot date"},{h:"Days to LT",n:1},{h:"Qty",n:1}],
      ltrows.map(function(l){
        return "<tr><td>"+tk(l.ticker||l.t)+"</td><td class=\"n mono\">"+
          esc(l.date||l.lot_date||"")+'</td><td class="n">'+n(l.days_to_ltcg,0)+
          '</td><td class="n">'+n(l.qty,2)+"</td></tr>"; }))
      : '<p class="pad" style="margin:0"><span class="pill buy">clear</span> '+
        'No lot is inside the LTCG boundary window this run.</p>',
    {sev:ltrows.length?"warn":"ok"}));

  /* de-risk queue */
  var q=D.derisk||{};
  H.push(panel("De-risk queue", q.headline||"",
    '<div class="pad note" style="padding-bottom:6px">Ranked fragility × stretch. '+
    "Benchmark "+esc(q.benchmark||"")+" "+signed(q.bm_1m,2)+" 1m · sentiment "+
    esc(q.sentiment_band||"")+" · urgency ×"+n(q.urgency,2)+"</div>"+
    table([{h:"#",n:1},{h:"Ticker"},{h:"Cluster"},{h:"Value",n:1},{h:"Fragility",n:1},
      {h:"Stretch",n:1},{h:"Score",n:1},{h:"Rel 1m",n:1},{h:"RSI",n:1},{h:""}],
      (q.queue||[]).slice(0,14).map(function(r){
        return '<tr><td class="n">'+n(r.rank,0)+"</td><td>"+thDot(r.thesis)+" "+tk(r.t)+
          "</td><td>"+esc(r.cluster||"")+'</td><td class="n">'+usd(r.val)+
          '</td><td class="n">'+n(r.frag,0)+'</td><td class="n">'+n(r.stretch,0)+
          '</td><td class="n"><b>'+n(r.score,0)+'</b></td><td class="n '+cls(r.rel)+'">'+
          signed(r.rel,1)+'</td><td class="n">'+n(r.rsi,0)+"</td><td>"+
          decideBox("derisk",r.t)+"</td></tr>"; })),{span:true}));

  /* charts */
  var series=(D.ledger||[]).map(function(r){
    return {ts:r.ts,v:r.v,w:r.w,trust:r.trust==="ok"?"ok":"bad",note:r.note}; });
  H.push(panel("Book value","equity line; dashed = equity + wallet cash",
    '<div class="pad">'+lineChart(series,{stack:true,label:"book value over time"})+"</div>"+
    '<div class="legend"><span><i style="background:var(--acc)"></i>equity</span>'+
    '<span><i style="background:var(--c2)"></i>+ wallet</span></div>'));

  var wrows=(D.positions||[]).slice(0,18).map(function(p){
    return {label:p.t, v:p.val||0, cap:p.cap, over:p.over_cap,
      color:CCOL[p.cluster]||"var(--acc)", vlabel:pct(p.wt,1),
      title:p.t+" "+usd(p.val)+" vs cap "+usd(p.cap)}; });
  H.push(panel("Position value vs ATR cap","vertical rule = the name's own cap",
    '<div class="pad">'+barsHChart(wrows,{label:"position value versus cap"})+"</div>"));

  var roll=(D.attribution.rolling||{});
  var rollRows=Object.keys(roll).filter(function(key){ return key!=="note"; })
    .map(function(key){
      var v=roll[key];
      var val = typeof v==="number" ? v :
        (v && typeof v==="object" ? (v.excess_pp!=null? v.excess_pp : v.vs_benchmark_pp)
         : null);
      return {label:human(key), v:val, vlabel:signed(val,2)+"pp",
        title:human(key)+" "+signed(val,2)+"pp vs benchmark"};
    }).filter(function(r){ return r.v!=null && !isNaN(r.v); });
  H.push(panel("Beat or lag "+esc(q.benchmark||"SMH"),
    "per period, never cumulative — a cumulative line would mix deposits with returns",
    rollRows.length? '<div class="pad">'+divergingBars(rollRows,
      {label:"relative performance per period"})+"</div>"
    : '<p class="empty">'+esc(roll.note||
        "No rolling window has enough ledger history yet.")+"</p>"));

  return H.join("");
}

function clusterRow(c){
  var band=c.band&&c.band.length===2?c.band:null;
  var over = band && c.eq_pct>band[1];
  var under = band && c.eq_pct<band[0];
  var members=(c.members||[]).map(function(t){
    var p=POS_BY[t]||{};
    return "<tr><td>"+thDot(p.thesis)+" "+tk(t)+'</td><td class="n">'+pct(p.wt,2)+
      '</td><td class="n">'+usd(p.px,2)+'</td><td class="n '+cls(p.day)+'">'+
      signed(p.day,2)+"</td><td>"+(p.signals||[]).map(function(s){
        var isPeer=/PEER/.test(s);
        return '<span class="pill '+(isPeer?(/LEADER/.test(s)?"buy":"sell"):"")+'">'+
          esc(s)+"</span>"; }).join(" ")+
      (p.over_cap?' <span class="pill sell" title="over its ATR risk cap">⚠ cap</span>':"")+
      "</td></tr>"; }).join("");
  var L=D.ladders[c.name];
  var ladderHtml="";
  if(L && (L.ranking||[]).length){
    ladderHtml='<h3 style="font-size:11px;letter-spacing:.07em;text-transform:uppercase;'+
      'color:var(--ink-3);margin:14px 0 7px">Substitution ladder · '+
      esc(L.as_of||"")+" · "+esc(L.confidence||"")+" confidence</h3>"+
      table([{h:"#",n:1},{h:"Ticker"},{h:"Held"},{h:"Verdict"},{h:"Why it ranks there"}],
        L.ranking.map(function(r){
          return '<tr><td class="n">'+n(r.rank,0)+"</td><td>"+tk(r.t)+"</td><td>"+
            (r.held?'<span class="pill acc">held</span>':'<span class="pill">bench</span>')+
            "</td><td>"+'<span class="pill '+(r.verdict==="leader"?"buy":
              r.verdict==="laggard"?"sell":"")+'">'+esc(r.verdict||"")+"</span></td><td>"+
            (r.reads||[]).map(function(x){
              return "<b>"+esc(x.axis)+":</b> "+esc(x.read); }).join("<br>")+"</td></tr>"; }));
  }
  var summary='<b style="font-family:var(--cond);font-size:13.5px;min-width:190px">'+
    esc(c.name)+"</b>"+
    '<span class="num" style="font-size:14px">'+pct(c.eq_pct,1)+"</span>"+
    (band?meter(c.eq_pct,Math.max(band[1]*1.6,c.eq_pct*1.1),band):"")+
    (band?'<span class="muted mono" style="font-size:11px">target '+band[0]+"–"+band[1]+
      "%</span>":"")+
    (over?'<span class="pill sell">over</span>':under?'<span class="pill hold">under</span>':
      '<span class="pill buy">in band</span>')+
    (c.innings?'<span class="pill info">'+esc(c.innings)+" innings</span>":"")+
    '<span class="muted">'+(c.members||[]).length+" names</span>";
  var body=table([{h:"Ticker"},{h:"Weight",n:1},{h:"Price",n:1},{h:"Day",n:1},{h:"Signals"}],
    [members])+
    ((c.gone||[]).length?'<p class="note" style="margin-top:10px">'+
      "No longer held / tracked only: "+tks(c.gone," gone")+"</p>":"")+
    ladderHtml;
  return detailsRow(summary,body,over===true);
}

function positionsTable(){
  var q=(document.getElementById("posq")||{}).value||"";
  var cl=(document.getElementById("posc")||{}).value||"";
  var onlyOver=(document.getElementById("posover")||{}).getAttribute
    ?document.getElementById("posover").getAttribute("aria-pressed")==="true":false;
  var onlyBroken=(document.getElementById("posbroken")||{}).getAttribute
    ?document.getElementById("posbroken").getAttribute("aria-pressed")==="true":false;
  var rows=(D.positions||[]).filter(function(p){
    if(q && p.t.toLowerCase().indexOf(q.toLowerCase())<0) return false;
    if(cl && p.cluster!==cl) return false;
    if(onlyOver && !p.over_cap) return false;
    if(onlyBroken && (p.thesis==="intact"||p.thesis==="strengthening")) return false;
    return true; });
  var K=posSort.key, dir=posSort.dir;
  rows.sort(function(a,b){
    var x=a[K],y=b[K];
    if(typeof x==="string"||typeof y==="string")
      return String(x||"").localeCompare(String(y||""))*dir*-1;
    return (((y==null?-1e18:y)-(x==null?-1e18:x))*(dir<0?1:-1));
  });
  var cols=[{h:"Ticker",k:"t"},{h:"Cluster",k:"cluster"},{h:"Qty",k:"qty",n:1},
    {h:"Price",k:"px",n:1},{h:"Day",k:"day",n:1},{h:"Value",k:"val",n:1},
    {h:"Weight",k:"wt",n:1},{h:"ATR20",k:"atr",n:1},{h:"Beta",k:"beta",n:1},
    {h:"Stop",k:"stop_px",n:1},{h:"Cap",k:"cap",n:1},{h:"Headroom",k:"headroom",n:1},
    {h:"RSI",k:"rsi",n:1},{h:"Rel 1m",k:"rel",n:1}];
  var sortIdx=-1; cols.forEach(function(c,i){ if(c.k===K) sortIdx=i; });
  var body=rows.map(function(p){
    return "<tr"+(p.over_cap?' class="flagged"':"")+">"+
      "<td>"+thDot(p.thesis)+" "+tk(p.t)+"</td>"+
      '<td><span class="dot" style="background:'+(CCOL[p.cluster]||"var(--c8)")+
      '"></span> '+esc(p.cluster)+"</td>"+
      '<td class="n">'+n(p.qty,2)+'</td><td class="n">'+usd(p.px,2)+
      '</td><td class="n '+cls(p.day)+'">'+signed(p.day,2)+
      '</td><td class="n">'+usd(p.val)+'</td><td class="n">'+pct(p.wt,2)+
      '</td><td class="n">'+pct(p.atr,1)+'</td><td class="n">'+n(p.beta,2)+
      '</td><td class="n">'+usd(p.stop_px,2)+'</td><td class="n">'+usd(p.cap)+
      '</td><td class="n '+(p.headroom<0?"neg":"")+'">'+usd(p.headroom)+
      '</td><td class="n">'+n(p.rsi,0)+'</td><td class="n '+cls(p.rel)+'">'+
      signed(p.rel,1)+"</td></tr>"; });
  return table(cols.map(function(c){ return {h:c.h,n:c.n}; }), body,
    {sortKey:"pos", sortIdx:sortIdx, sortDir:dir}) +
    '<script type="application/json" id="poscols">'+JSON.stringify(
      cols.map(function(c){ return c.k; }))+"<\/script>";
}

/* =================================================================== TAB: CONVICTION */
function tabConviction(){
  var H=[], k=D.kpi;

  /* cycle position */
  H.push(panel("AI-capex cycle position", k.cycle_as_of||"",
    '<div class="pad">'+
    '<div style="display:flex;gap:14px;align-items:center;flex-wrap:wrap">'+
    '<span class="num" style="font-size:30px;font-family:var(--cond);font-weight:700">'+
    esc(String(k.cycle||"unknown").toUpperCase())+"</span>"+
    '<span class="pill '+(k.cycle_conf==="high"?"buy":k.cycle_conf==="medium"?"hold":"")+
    '">'+esc(k.cycle_conf||"")+" confidence</span>"+
    '<span class="muted">'+pct(k.ai_capex,1)+" of equity rides this one factor</span></div>"+
    (k.cycle_falsifier?'<p class="note" style="margin-top:11px;max-width:74ch">'+
      "<b>Falsifier.</b> "+esc(k.cycle_falsifier)+"</p>":"")+"</div>",
    {span:true, sev:k.cycle==="late"?"warn":null}));

  /* thesis map */
  var TH=D.thesis||{}, order=["broken","watch","intact","strengthening"];
  var groups={};
  Object.keys(TH).forEach(function(t){
    if(!TH[t].held) return;
    (groups[TH[t].status||"none"]=groups[TH[t].status||"none"]||[]).push(t); });
  var thBody=order.filter(function(s){ return groups[s]; }).map(function(s){
    var list=groups[s].sort();
    return detailsRow(thDot(s)+'<b style="font-family:var(--cond);font-size:13px">'+
      esc(human(s))+"</b>"+'<span class="muted">'+list.length+" held</span>"+
      '<span style="margin-left:6px">'+tks(list)+"</span>",
      list.map(function(t){
        var v=TH[t];
        return '<div class="card"><div class="lhs">'+tk(t)+
          '<span class="pill '+(v.verified==="primary"?"buy":v.verified?"hold":"")+'">'+
          esc(v.verified||"unverified")+"</span></div><div>"+
          '<p class="why" style="margin:0">'+esc(v.text||"")+"</p>"+
          ((v["for"]||[]).length?'<p class="meta" style="color:var(--pos)">FOR</p><ul>'+
            v["for"].map(function(e){ return "<li>"+esc(e.claim)+
              ' <span class="muted">('+esc(e.date||"")+", "+esc(e.source||"")+
              ")</span></li>"; }).join("")+"</ul>":"")+
          ((v.vs||[]).length?'<p class="meta" style="color:var(--neg)">AGAINST</p><ul>'+
            v.vs.map(function(e){ return "<li>"+esc(e.claim)+
              ' <span class="muted">('+esc(e.date||"")+", "+esc(e.source||"")+
              ")</span></li>"; }).join("")+"</ul>":
            '<p class="meta muted">No evidence against recorded — that is itself a gap.</p>')+
          '</div><div class="rhs">'+decideBox("thesis",t)+"</div></div>"; }).join(""),
      s==="broken"||s==="watch");
  }).join("");
  var stale=Object.keys(TH).filter(function(t){ return !TH[t].held; });
  H.push(panel("Thesis map",
    Object.keys(TH).filter(function(t){ return TH[t].held; }).length+
    " held · exited names kept for history, not shown as current",
    thBody+(stale.length?'<p class="note pad">Theses retained for exited names: '+
      tks(stale," gone")+"</p>":""),{span:true}));

  /* cluster ladders in full */
  var lk=Object.keys(D.ladders||{});
  if(lk.length){
    H.push(panel("Cluster ladders", lk.length+" clusters ranked · advisory until scored",
      lk.map(function(name){
        var L=D.ladders[name];
        return detailsRow(
          '<b style="font-family:var(--cond);font-size:13.5px;min-width:200px">'+esc(name)+
          "</b>"+(L.status?'<span class="pill '+(L.status==="watch"?"hold":"")+'">'+
          esc(L.status)+"</span>":"")+
          (L.innings?'<span class="pill info">'+esc(L.innings)+" innings</span>":"")+
          '<span class="pill">'+esc(L.confidence||"")+" conf</span>"+
          (L.leader?'<span class="muted">leader '+esc(L.leader)+"</span>":""),
          (L.text?'<p class="why" style="max-width:76ch">'+esc(L.text)+"</p>":"")+
          (L.falsifier?'<p class="note"><b>Reorders when:</b> '+esc(L.falsifier)+"</p>":"")+
          ((L.ranking||[]).length? table([{h:"#",n:1},{h:"Ticker"},{h:"Held"},{h:"Verdict"},
            {h:"Differentiator reads"}],
            L.ranking.map(function(r){
              return '<tr><td class="n">'+n(r.rank,0)+"</td><td>"+tk(r.t)+"</td><td>"+
                (r.held?'<span class="pill acc">held</span>':'<span class="pill">bench</span>')+
                '</td><td><span class="pill '+(r.verdict==="leader"?"buy":
                  r.verdict==="laggard"?"sell":"")+'">'+esc(r.verdict||"")+
                "</span></td><td>"+(r.reads||[]).map(function(x){
                  return "<b>"+esc(x.axis)+":</b> "+esc(x.read)+
                    ' <span class="muted">('+esc(x.source||"")+")</span>"; })
                  .join("<br>")+"</td></tr>"; })):"")+
          ((L.bench||[]).length?"<h3 style=\"font-size:11px;letter-spacing:.07em;"+
            "text-transform:uppercase;color:var(--ink-3);margin:14px 0 7px\">"+
            "Bench — best non-held names in this cluster</h3>"+
            L.bench.map(function(b){
              return '<div class="card"><div class="lhs">'+tk(b.t)+
                '<span class="amt">'+usd(b.px,2)+"</span></div><div>"+
                '<p class="why" style="margin:0">'+esc(b.why||"")+"</p>"+
                (b.entry?'<p class="meta">Entry condition: '+esc(b.entry)+"</p>":"")+
                "</div><div class=\"rhs\"></div></div>"; }).join(""):"")+
          ((L.tensions||[]).length?'<p class="meta" style="margin-top:10px">'+
            "<b>Tensions with per-name theses</b></p><ul>"+L.tensions.map(function(x){
              return "<li>"+esc(x.t)+" (rank "+x.rank+", thesis "+esc(x.thesis)+"): "+
                esc(x.text)+"</li>"; }).join("")+"</ul>":"")+
          ((L.redundant||[]).length?'<p class="meta"><b>Redundancy</b></p><ul>'+
            L.redundant.map(function(r){
              return "<li>"+(r.pair||[]).join(" / ")+" — "+esc(r.same_bet_because||"")+
                " <b>"+esc(r.verdict||"")+"</b>, keep "+esc(r.keep||"")+"</li>"; })
              .join("")+"</ul>":"")+
          ((L.catalysts||[]).length?'<p class="meta"><b>Reordering catalysts</b></p><ul>'+
            L.catalysts.map(function(c){ return "<li>"+esc(c.date||"")+" — "+
              esc(c.event||"")+" (reorders "+(c.reorders||[]).join(", ")+")</li>"; })
              .join("")+"</ul>":"")+
          ((L.confidence_reasons||[]).length?'<p class="note">Confidence limits: '+
            L.confidence_reasons.map(esc).join(" · ")+"</p>":""),
          false); }).join(""),{span:true}));
  }

  /* signals */
  var SH=D.signals||{}, bull=[], bear=[];
  Object.keys(SH).forEach(function(t){
    var tags=SH[t]||[];
    var isBear=tags.some(function(s){ return /BREAKDOWN|LAGGARD|THREAT|OVERBOUGHT/.test(s); });
    (isBear?bear:bull).push({t:t,tags:tags,held:!!POS_BY[t]}); });
  function sigList(arr){ return arr.sort(function(a,b){
      return a.t.localeCompare(b.t); }).map(function(x){
      return '<tr><td>'+tk(x.t,x.held?"":" gone")+"</td><td>"+
        x.tags.map(function(s){ return '<span class="pill">'+esc(s)+"</span>"; }).join(" ")+
        '</td><td class="mono muted">'+esc((D.signals_as_of||{})[x.t]||"")+
        "</td></tr>"; }).join(""); }
  H.push(panel("Signal history","struck-through = no longer held",
    '<div class="grid g2" style="padding:0">'+
    "<div>"+table([{h:"Bullish"},{h:"Tags"},{h:"As of"}],[sigList(bull)])+"</div>"+
    "<div>"+table([{h:"Bearish"},{h:"Tags"},{h:"As of"}],[sigList(bear)])+"</div></div>",
    {span:true}));

  /* quality */
  var QF=D.quality.flags||{};
  H.push(panel("Quality audit",
    (D.quality.as_of||"")+" · "+pct(D.quality.book_pct,1)+" of book flagged",
    Object.keys(QF).length? Object.keys(QF).map(function(t){
      return detailsRow(tk(t)+'<span class="pill sell">'+(QF[t]||[]).length+
        " finding(s)</span>",
        (QF[t]||[]).map(function(f){
          return '<div class="card"><div class="lhs"><span class="pill sell">'+
            esc(f.metric||"")+"</span></div><div>"+
            '<p class="why" style="margin:0"><b>'+esc(f.finding||"")+"</b></p>"+
            (f.magnitude?'<p class="meta">'+esc(f.magnitude)+"</p>":"")+
            ((f.evidence_against||[]).length?'<p class="meta" style="color:var(--pos)">'+
              "Mitigating: "+esc((f.evidence_against[0]||{}).claim||"")+"</p>":"")+
            "</div><div class=\"rhs\"></div></div>"; }).join(""),
        false); }).join("") : null,
    {sev:Object.keys(QF).length?"warn":"ok",span:true}));

  /* watchlist + diversifiers */
  var wl=D.watchlist||[];
  H.push(panel("Watchlist setups", D.watchlist_as_of||"",
    wl.length? table([{h:"Ticker"},{h:"Setup"},{h:"Upside",n:1},{h:"52w pos",n:1},{h:""}],
      wl.map(function(w){
        return "<tr><td>"+tk(w.ticker)+"</td><td>"+esc(w.type||"")+
          '</td><td class="n pos">'+signed(w.upside_pct,1)+'</td><td class="n">'+
          n((w.pos||0)*100,0)+"%</td><td>"+decideBox("watchlist",w.ticker)+
          "</td></tr>"; })) : null));

  var dv=D.diversifiers||{};
  H.push(panel("Diversifier bench",
    "a bench of what a real hedge would look like — not a proposal to buy",
    Object.keys(dv).length? Object.keys(dv).map(function(t){
      var v=dv[t]||{};
      return '<div class="card"><div class="lhs">'+tk(t)+
        '<span class="amt">'+usd(v.price_usd,2)+"</span>"+
        '<span class="pill '+(v.clean_diversifier?"buy":"hold")+'">'+
        (v.clean_diversifier?"clean":"AI-adjacent")+"</span></div><div>"+
        '<p class="why" style="margin:0">'+esc(v.thesis||"")+"</p>"+
        '<p class="meta">Target '+usd(v.target_usd,2)+" · "+signed(v.upside_pct,1)+
        " upside · as of "+esc(v.as_of||"")+"</p></div>"+
        '<div class="rhs">'+decideBox("diversifier",t)+"</div></div>"; }).join("") : null));

  /* stress */
  var sc=(D.stress||{}).scenarios||[];
  H.push(panel("Stress table",(D.stress||{}).as_of||"",
    sc.length? table([{h:"Scenario"},{h:"Impact",n:1},{h:"Mechanism"},{h:"Most exposed"}],
      sc.map(function(s){
        return "<tr><td><b>"+esc(s.scenario||"")+'</b></td><td class="n neg">'+
          n(s.impact_pct_low,0)+"% to "+n(s.impact_pct_high,0)+"%</td><td>"+
          esc(s.mechanism||"")+"</td><td>"+tks(s.most_exposed)+"</td></tr>"; }))
      : null,{span:true,sev:"warn"}));

  return H.join("");
}

/* ================================================================ TAB: TRACK RECORD */
function tabTrack(){
  var H=[], S=D.track.scorecard||{}, byd=S.by_direction||{};

  var rows=Object.keys(byd).map(function(key){
    var v=byd[key];
    return {label:key, v:v.accuracy_pct||0, vlabel:pct(v.accuracy_pct,1)+" (n="+v.n+")",
      color:(v.accuracy_pct>=50?"var(--pos)":v.accuracy_pct>=35?"var(--warn)":"var(--neg)"),
      title:key+": "+v.worked+" worked, "+v.missed+" missed, avg benefit "+
        signed(v.avg_benefit_pct,2)}; });
  H.push(panel("Proposal accuracy, 30 days",
    "n="+(S.overall||{}).n+" scored · "+(S.excluded_dismissed_by_user||0)+
    " excluded (dismissed by you) · "+(S.withdrawn_by_desk||0)+" withdrawn by the desk",
    '<div class="pad">'+barsHChart(rows,{label:"accuracy by direction",ml:92})+"</div>"+
    '<div class="pad" style="padding-top:0">'+
    table([{h:"Direction"},{h:"n",n:1},{h:"Worked",n:1},{h:"Missed",n:1},{h:"Neutral",n:1},
      {h:"Accuracy",n:1},{h:"Avg benefit",n:1}],
      Object.keys(byd).map(function(key){ var v=byd[key];
        return "<tr><td><b>"+esc(key)+'</b></td><td class="n">'+v.n+
          '</td><td class="n pos">'+v.worked+'</td><td class="n neg">'+v.missed+
          '</td><td class="n">'+v.neutral+'</td><td class="n">'+pct(v.accuracy_pct,1)+
          '</td><td class="n '+cls(v.avg_benefit_pct)+'">'+signed(v.avg_benefit_pct,2)+
          "</td></tr>"; }).concat([
        '<tr><td><b>Overall</b></td><td class="n">'+(S.overall||{}).n+
        '</td><td class="n pos">'+(S.overall||{}).worked+'</td><td class="n neg">'+
        (S.overall||{}).missed+'</td><td class="n">'+(S.overall||{}).neutral+
        '</td><td class="n"><b>'+pct((S.overall||{}).accuracy_pct,1)+
        '</b></td><td class="n '+cls((S.overall||{}).avg_benefit_pct)+'">'+
        signed((S.overall||{}).avg_benefit_pct,2)+"</td></tr>"]))+"</div>",
    {span:true, sev:((S.overall||{}).accuracy_pct||0)<40?"warn":null}));

  /* bucket hit rates */
  var B=D.track.buckets||{};
  H.push(panel("Signal-bucket hit rates","n≥50 makes a rate trustworthy; below n=5 it is noise",
    Object.keys(B).length? table([{h:"Bucket"},{h:"n",n:1},{h:"Hit rate",n:1},
      {h:"Payoff ratio",n:1},{h:"Weight it carries"}],
      Object.keys(B).sort(function(a,b){ return B[b].n-B[a].n; }).map(function(key){
        var v=B[key], weak=v.hit_rate_pct<40&&v.n>=5;
        return "<tr"+(weak?' class="flagged"':"")+"><td><b>"+esc(key)+
          '</b></td><td class="n">'+v.n+'</td><td class="n">'+pct(v.hit_rate_pct,1)+
          '</td><td class="n">'+n(v.payoff_ratio,2)+"</td><td>"+
          (v.n<5?'<span class="pill">too few to judge</span>':
           weak?'<span class="pill sell">de-emphasised</span>':
           '<span class="pill buy">carries weight</span>')+"</td></tr>"; })) : null));

  /* stop-loss efficacy */
  var ST=D.track.stops||{}, ov=ST.overall||{}, co=ST.by_cohort||{};
  var cohortRows=Object.keys(co).map(function(key){
    var v=co[key];
    return {label:key, v:v.win_rate_pct||0, vlabel:pct(v.win_rate_pct,1)+" (n="+v.count+")",
      color:(v.win_rate_pct>=50?"var(--pos)":"var(--neg)"),
      title:key+": saved "+v.saved+", hurt "+v.hurt+", net "+usd(v.net_dollar_impact)}; });
  H.push(panel("Stop-loss efficacy",
    ov.count+" scored fills · win rate "+pct(ov.win_rate_pct,1)+
    " · net "+usd(ov.net_dollar_impact),
    '<div class="pad">'+barsHChart(cohortRows,{label:"stop win rate by cohort",ml:92})+
    "</div>"+
    '<div class="pad" style="padding-top:0"><p class="note">A stop that "hurt" means the name '+
    "is higher now than where the stop sold it. Cascade stops fired inside a broad selloff; "+
    "deliberate stops were set on a single name's own thesis.</p>"+
    table([{h:"Cohort"},{h:"n",n:1},{h:"Saved",n:1},{h:"Hurt",n:1},{h:"Flat",n:1},
      {h:"Win rate",n:1},{h:"Avg move",n:1},{h:"Net $",n:1}],
      Object.keys(co).map(function(key){ var v=co[key];
        return "<tr><td><b>"+esc(key)+'</b></td><td class="n">'+v.count+
          '</td><td class="n pos">'+v.saved+'</td><td class="n neg">'+v.hurt+
          '</td><td class="n">'+v.flat+'</td><td class="n">'+pct(v.win_rate_pct,1)+
          '</td><td class="n">'+signed(v.avg_move_pct,2)+'</td><td class="n">'+
          usd(v.net_dollar_impact)+"</td></tr>"; }))+"</div>",
    {span:true, sev:(ov.win_rate_pct||0)<50?"warn":null}));

  /* proposal history browser */
  H.push(panel("Every proposal ever made",
    (D.proposals.history||[]).length+" total · "+
    Object.keys(D.proposals.counts||{}).map(function(k){
      return D.proposals.counts[k]+" "+k.replace(/_/g," "); }).join(" · "),
    '<div class="filters">'+
    '<input type="search" id="hq" placeholder="ticker or text…">'+
    '<select id="hs"><option value="">All statuses</option>'+
    Object.keys(D.proposals.counts||{}).sort().map(function(k){
      return "<option>"+esc(k)+"</option>"; }).join("")+"</select>"+
    '<select id="hd"><option value="">All directions</option>'+
    ["BUY","TRIM","SELL","HOLD"].map(function(k){
      return "<option>"+k+"</option>"; }).join("")+"</select>"+
    "</div>"+'<div id="htbl">'+historyTable()+"</div>",{span:true}));

  /* execution log */
  H.push(panel("Execution log","last "+(D.trades||[]).length+
    " reconciled fills · the why, not just the what",
    table([{h:"Date"},{h:"Ticker"},{h:"Side"},{h:"Qty",n:1},{h:"Price",n:1},{h:"Amount",n:1},
      {h:"Type"},{h:"Reason"}],
      (D.trades||[]).slice(0,60).map(function(t){
        return '<tr><td class="mono">'+esc(t.date||"")+"</td><td>"+tk(t.t)+"</td><td>"+
          '<span class="pill '+(t.side==="BUY"?"buy":"sell")+'">'+esc(t.side||"")+
          '</span></td><td class="n">'+n(t.qty,2)+'</td><td class="n">'+usd(t.px,2)+
          '</td><td class="n">'+usd(t.amt,2)+"</td><td>"+esc(t.type||"")+"</td><td"+
          (t.reason==="UNCAPTURED"?' class="muted"':"")+">"+esc(t.reason||"")+
          "</td></tr>"; })),{span:true}));

  /* learning */
  var L=D.learning||{};
  H.push(panel("Self-learning",
    L.obs_n+" observations · phase 4 readiness "+L.readiness_current+"/"+L.readiness_gate,
    '<div class="pad">'+
    meter(L.readiness_current||0, L.readiness_gate||100)+
    '<p class="note" style="margin-top:9px;max-width:72ch">'+esc(L.readiness_note||"")+"</p>"+
    "</div>"+
    ((L.lessons||[]).length? detailsRow('<b>Lessons learned</b><span class="muted">'+
      L.lessons.length+" recorded</span>",
      "<ul>"+L.lessons.map(function(x){
        return '<li style="margin-bottom:7px"><span class="pill">'+esc(x.kind||"")+
          '</span> <span class="mono muted">'+esc(x.date||"")+"</span><br>"+
          esc(x.text)+"</li>"; }).join("")+"</ul>",false):""),{span:true}));

  return H.join("");
}

function historyTable(){
  var q=((document.getElementById("hq")||{}).value||"").toLowerCase();
  var s=(document.getElementById("hs")||{}).value||"";
  var d=(document.getElementById("hd")||{}).value||"";
  var rows=(D.proposals.history||[]).filter(function(p){
    if(s && p.status!==s) return false;
    if(d && p.dir!==d) return false;
    if(q){ var hay=((p.t||"")+" "+(p.action||"")+" "+(p.rationale||"")+" "+
      (p.trigger||"")).toLowerCase();
      if(hay.indexOf(q)<0) return false; }
    return true; }).slice(0,300);
  return table([{h:"ID"},{h:"Date"},{h:"Ticker"},{h:"Action"},{h:"Size",n:1},{h:"Trigger"},
    {h:"Status"},{h:"Drift",n:1}],
    rows.map(function(p){
      return '<tr><td class="mono muted">'+esc(p.id||"")+'</td><td class="mono">'+
        esc(p.date||"")+"</td><td>"+tk(p.t)+"</td><td>"+dirPill(p.dir)+" "+
        esc(p.action||"")+'</td><td class="n">'+usd(p.size)+"</td><td>"+
        (p.trigger?'<span class="pill info">'+esc(p.trigger)+"</span>":"")+"</td><td>"+
        '<span class="pill '+(p.status==="open"?"acc":
          /executed|filled|fulfilled|accepted/.test(p.status||"")?"buy":
          /dismissed|retired|superseded/.test(p.status||"")?"":"hold")+'">'+
        esc((p.status||"").replace(/_/g," "))+'</span></td><td class="n '+cls(p.drift)+'">'+
        signed(p.drift,1)+"</td></tr>"; }))+
    (rows.length>=300?'<p class="note pad">Showing the first 300 matches — narrow the filter.</p>':"");
}

/* ================================================================= TAB: DIAGNOSTICS */
function tabDiag(){
  var H=[], F=D.freshness||{};

  var art=(F.artefacts||[]).slice().sort(function(a,b){
    var o={dark:0,stale:1,fresh:2}; return (o[a.state]||3)-(o[b.state]||3); });
  H.push(panel("Freshness contract", F.headline||"",
    table([{h:"Artefact"},{h:"Owner"},{h:"As of"},{h:"Age",n:1},{h:"TTL",n:1},{h:"State"},
      {h:"On stale"}],
      art.map(function(a){
        return "<tr"+(a.state==="dark"?' class="flagged"':"")+'><td class="mono">'+
          esc(a.key||"")+"</td><td>"+esc(a.owner||"")+'</td><td class="mono">'+
          esc(a.as_of||"")+'</td><td class="n">'+n(a.age_days,0)+'d</td><td class="n">'+
          n(a.ttl_days,0)+"d</td><td>"+'<span class="pill '+(a.state==="dark"?"sell":
            a.state==="stale"?"hold":"buy")+'">'+esc(a.state||"")+"</span></td><td>"+
          esc(a.on_stale||"")+"</td></tr>"; })),
    {span:true, sev:(F.counts||{}).dark?"bad":(F.counts||{}).stale?"warn":"ok"}));

  H.push(panel("Data-quality caveats",
    (D.dq||[]).length+" self-reported · a dashboard hiding its own uncertainty "+
    "invites more trust than the numbers earn",
    (D.dq||[]).length? "<ul style=\"margin:0;padding:14px 15px 14px 32px\">"+
      D.dq.map(function(x){ return '<li style="margin-bottom:5px"><span class="pill">'+
        esc(x.src)+"</span> "+esc(x.text)+"</li>"; }).join("")+"</ul>" : null,
    {span:true,sev:(D.dq||[]).length?"warn":"ok"}));

  H.push(panel("Open gaps", (D.gaps||[]).length+" tracked",
    (D.gaps||[]).length? (D.gaps||[]).map(function(g,i){
      return '<div class="card"><div class="lhs"><span class="pill">gap '+(i+1)+
        '</span></div><div><p class="why" style="margin:0">'+esc(g.text)+"</p></div>"+
        '<div class="rhs">'+decideBox("gap","gap-"+i)+"</div></div>"; }).join("") : null,
    {span:true}));

  if((D.outages||[]).length){
    H.push(panel("Run outages","runs that did not happen, kept visible rather than forgotten",
      "<ul style=\"margin:0;padding:14px 15px 14px 32px\">"+(D.outages||[]).map(function(o){
        return "<li>"+esc(typeof o==="string"?o:JSON.stringify(o))+"</li>"; }).join("")+
      "</ul>",{span:true,sev:"warn"}));
  }

  /* attribution */
  var A=D.attribution||{};
  H.push(panel("Attribution vs last run","what actually moved the number",
    '<div class="pad"><dl class="kv" style="max-width:420px">'+
    "<dt>Value delta</dt><dd class=\""+cls(A.delta)+"\">"+usd(A.delta,2)+"</dd>"+
    "<dt>FX effect</dt><dd class=\""+cls(A.fx)+"\">"+usd(A.fx,2)+"</dd>"+
    "<dt>Flow (deposits, trades)</dt><dd class=\""+cls(A.flow)+"\">"+usd(A.flow,2)+"</dd>"+
    "<dt>Residual market move</dt><dd class=\""+cls(A.residual)+"\">"+usd(A.residual,2)+
    "</dd></dl>"+
    ((A.changes||[]).length?'<p class="meta" style="margin-top:11px">Quantity changes: '+
      A.changes.map(function(c){ return esc(typeof c==="string"?c:
        (c.ticker||"")+" "+(c.delta||c.change||"")); }).join(" · ")+"</p>":"")+
    "</div>"));

  /* ledger */
  H.push(panel("Run ledger",(D.ledger||[]).length+" runs recorded",
    table([{h:"Timestamp"},{h:"Mode"},{h:"Equity",n:1},{h:"Wallet",n:1},{h:"Trust"},{h:"Note"}],
      (D.ledger||[]).slice().reverse().slice(0,40).map(function(r){
        return '<tr'+(r.trust!=="ok"?' class="flagged"':"")+'><td class="mono">'+
          esc(r.ts)+"</td><td>"+'<span class="pill '+(r.mode==="deep"?"acc":"")+'">'+
          esc(r.mode||"")+'</span></td><td class="n">'+usd(r.v)+'</td><td class="n">'+
          usd(r.w)+"</td><td>"+'<span class="pill '+(r.trust==="ok"?"buy":"sell")+'">'+
          esc(r.trust)+'</span></td><td class="muted" style="max-width:460px">'+
          esc(r.note||"")+"</td></tr>"; })),{span:true}));

  return H.join("");
}

/* ====================================================================== ticker sheet */
function openTicker(t){
  var p=POS_BY[t], th=(D.thesis||{})[t], sigs=(D.signals||{})[t]||[];
  var props=(D.proposals.history||[]).filter(function(x){ return x.t===t; });
  var trades=(D.trades||[]).filter(function(x){ return x.t===t; });
  var stops=((D.track.stops||{}).rows||[]).filter(function(x){ return x.t===t; });
  var grades=(p&&p.grades)||{};
  var lots=((D.lots||{})[t])||((D.lots||{}).lots||{})[t];
  var trig=[];
  Object.keys(D.triggers.families||{}).forEach(function(f){
    (D.triggers.families[f]||[]).forEach(function(r){
      if(r.paired){ if((r.sell||{}).t===t||(r.buy||{}).t===t) trig.push([f,r]); }
      else if(r.t===t) trig.push([f,r]); }); });
  var lad=[];
  Object.keys(D.ladders||{}).forEach(function(name){
    (D.ladders[name].ranking||[]).forEach(function(r){
      if(r.t===t) lad.push([name,r]); }); });

  var H='<div class="sheet-head"><h2>'+esc(t)+"</h2>"+
    (p?'<span class="pill">'+esc(p.cluster)+"</span>":
       '<span class="pill">not held</span>')+
    (th?thDot(th.status)+'<span class="muted">'+esc(th.status||"")+"</span>":"")+
    '<button class="sheet-close" aria-label="Close">✕</button></div>';

  if(p){
    H+='<div class="sheet-sec"><h3>Position</h3><dl class="kv">'+
      "<dt>Value</dt><dd>"+usd(p.val)+"</dd>"+
      "<dt>Weight</dt><dd>"+pct(p.wt,2)+"</dd>"+
      "<dt>Quantity</dt><dd>"+n(p.qty,4)+"</dd>"+
      "<dt>Price</dt><dd>"+usd(p.px,2)+"</dd>"+
      '<dt>Day</dt><dd class="'+cls(p.day)+'">'+signed(p.day,2)+"</dd>"+
      "<dt>ATR20</dt><dd>"+pct(p.atr,1)+"</dd>"+
      "<dt>Beta</dt><dd>"+n(p.beta,2)+"</dd>"+
      "<dt>Stop</dt><dd>"+usd(p.stop_px,2)+" ("+pct(p.stop_dist,1)+" away)</dd>"+
      "<dt>ATR risk cap</dt><dd>"+usd(p.cap)+"</dd>"+
      '<dt>Headroom</dt><dd class="'+(p.headroom<0?"neg":"pos")+'">'+usd(p.headroom)+"</dd>"+
      "<dt>Open risk</dt><dd>"+usd(p.risk_usd)+" ("+pct(p.risk_share,1)+" of book risk)</dd>"+
      "<dt>RSI14</dt><dd>"+n(p.rsi,1)+"</dd>"+
      '<dt>Rel 1m vs SMH</dt><dd class="'+cls(p.rel)+'">'+signed(p.rel,1)+"pp</dd>"+
      '<dt>Abs 1m</dt><dd class="'+cls(p.ret1m)+'">'+signed(p.ret1m,1)+"</dd>"+
      "<dt>De-risk rank</dt><dd>"+(p.drank?"#"+p.drank+" (score "+n(p.derisk,0)+")":
        "—")+"</dd></dl>"+
      (p.over_cap?'<p class="note" style="color:var(--neg);margin-top:9px">'+
        "⚠ Over its ATR risk cap by "+usd(Math.abs(p.headroom||0))+" ("+
        n(p.cap_mult,2)+"×).</p>":"")+"</div>";
  }
  if(sigs.length) H+='<div class="sheet-sec"><h3>Live signals</h3>'+
    sigs.map(function(s){ return '<span class="pill">'+esc(s)+"</span> "; }).join("")+
    '<p class="note" style="margin-top:7px">As of '+esc((D.signals_as_of||{})[t]||"—")+
    "</p></div>";

  if(th) H+='<div class="sheet-sec"><h3>Thesis · '+esc(th.status||"")+"</h3>"+
    "<p style=\"margin:0 0 9px\">"+esc(th.text||"")+"</p>"+
    '<p class="note">Verification: '+esc(th.verified||"unverified")+
    (th.against_src?" · "+esc(th.against_src):"")+"</p>"+
    ((th["for"]||[]).length?'<p class="meta" style="color:var(--pos);margin:9px 0 3px">'+
      "EVIDENCE FOR</p><ul style=\"margin:0;padding-left:18px\">"+th["for"].map(function(e){
      return '<li style="font-size:12.5px;margin-bottom:4px">'+esc(e.claim)+
        ' <span class="muted">('+esc(e.date||"")+")</span></li>"; }).join("")+"</ul>":"")+
    ((th.vs||[]).length?'<p class="meta" style="color:var(--neg);margin:9px 0 3px">'+
      "EVIDENCE AGAINST</p><ul style=\"margin:0;padding-left:18px\">"+th.vs.map(function(e){
      return '<li style="font-size:12.5px;margin-bottom:4px">'+esc(e.claim)+
        ' <span class="muted">('+esc(e.date||"")+")</span></li>"; }).join("")+"</ul>":
      '<p class="note" style="color:var(--warn);margin-top:9px">'+
      "No evidence against on file — an unfalsified thesis is a weak one.</p>")+
    "</div>";

  if(lad.length) H+='<div class="sheet-sec"><h3>Cluster rank</h3>'+lad.map(function(x){
    return "<p style=\"margin:0 0 7px\"><b>"+esc(x[0])+"</b> — rank #"+x[1].rank+
      ' <span class="pill '+(x[1].verdict==="leader"?"buy":x[1].verdict==="laggard"?"sell":"")+
      '">'+esc(x[1].verdict||"")+"</span></p>"+
      (x[1].reads||[]).map(function(r){
        return '<p class="note" style="margin:0 0 5px"><b>'+esc(r.axis)+":</b> "+
          esc(r.read)+"</p>"; }).join(""); }).join("")+"</div>";

  if(trig.length) H+='<div class="sheet-sec"><h3>Triggers firing now</h3>'+
    trig.map(function(x){
      var r=x[1];
      var leg = r.paired ? ((r.sell||{}).t===t?r.sell:r.buy) : r;
      return '<p style="margin:0 0 8px"><span class="pill info">'+esc(human(x[0]))+
        "</span> "+dirPill(leg.dir)+" "+(leg.size?usd(leg.size):"")+
        (r.vote?' <span class="pill '+(r.vote==="live"?"live":"shadow")+'">'+esc(r.vote)+
        "</span>":"")+"</p>"+
        "<ul style=\"margin:0 0 10px;padding-left:18px\">"+(leg.reasons||r.reasons||[])
          .map(function(s){ return '<li style="font-size:12.5px">'+esc(s)+"</li>"; })
          .join("")+"</ul>"; }).join("")+"</div>";

  if(props.length) H+='<div class="sheet-sec"><h3>Proposal history · '+props.length+
    "</h3>"+table([{h:"Date"},{h:"Action"},{h:"Size",n:1},{h:"Status"}],
    props.slice(0,25).map(function(p2){
      return '<tr><td class="mono">'+esc(p2.date||"")+"</td><td>"+esc(p2.action||"")+
        '</td><td class="n">'+usd(p2.size)+"</td><td>"+
        '<span class="pill '+(p2.status==="open"?"acc":"")+'">'+
        esc((p2.status||"").replace(/_/g," "))+"</span></td></tr>"; }))+"</div>";

  if(trades.length) H+='<div class="sheet-sec"><h3>Fills · '+trades.length+"</h3>"+
    table([{h:"Date"},{h:"Side"},{h:"Qty",n:1},{h:"Price",n:1},{h:"Reason"}],
    trades.slice(0,20).map(function(t2){
      return '<tr><td class="mono">'+esc(t2.date||"")+'</td><td><span class="pill '+
        (t2.side==="BUY"?"buy":"sell")+'">'+esc(t2.side)+'</span></td><td class="n">'+
        n(t2.qty,2)+'</td><td class="n">'+usd(t2.px,2)+"</td><td>"+esc(t2.reason||"")+
        "</td></tr>"; }))+"</div>";

  if(stops.length) H+='<div class="sheet-sec"><h3>Stop-loss record</h3>'+
    table([{h:"Date"},{h:"Cohort"},{h:"Exit",n:1},{h:"Now",n:1},{h:"Move",n:1},{h:"Verdict"}],
    stops.map(function(s){
      return '<tr><td class="mono">'+esc(s.date||"")+"</td><td>"+esc(s.cohort||"")+
        '</td><td class="n">'+usd(s.exit_px,2)+'</td><td class="n">'+usd(s.now_px,2)+
        '</td><td class="n '+cls(-(s.move||0))+'">'+signed(s.move,1)+"</td><td>"+
        esc(s.verdict||"")+"</td></tr>"; }))+"</div>";

  if(Object.keys(grades).length) H+='<div class="sheet-sec"><h3>Smith’s record on '+
    esc(t)+"</h3>"+table([{h:"Bucket"},{h:"Grade"},{h:"n",n:1},{h:"Hit rate",n:1}],
    Object.keys(grades).map(function(b){
      var g=grades[b];
      return "<tr><td>"+esc(b)+'</td><td><span class="pill '+
        (/A|B/.test(g.grade)?"buy":/F|D/.test(g.grade)?"sell":"hold")+'">'+esc(g.grade)+
        '</span></td><td class="n">'+g.n+'</td><td class="n">'+pct(g.hit_rate_pct,0)+
        "</td></tr>"; }))+
    '<p class="note" style="margin-top:7px">Low n means low confidence — these grades '+
    "describe how often a bucket has worked on this name, not a forecast.</p></div>";

  if(lots) H+='<div class="sheet-sec"><h3>Tax lots</h3><pre class="mono" '+
    'style="font-size:11px;overflow-x:auto;margin:0">'+esc(JSON.stringify(lots,null,1))+
    "</pre></div>";

  document.getElementById("sheet").innerHTML=H;
  document.getElementById("sheet").classList.add("on");
  document.getElementById("sheetback").classList.add("on");
  document.getElementById("sheet").focus();
}
function closeSheet(){
  document.getElementById("sheet").classList.remove("on");
  document.getElementById("sheetback").classList.remove("on");
}

/* ============================================================================ shell */
var TABS=[
  {id:"command", label:"Command", render:tabCommand,
   count:function(){ return (D.proposals.open||[]).length; }},
  {id:"book", label:"Book & risk", render:tabBook,
   count:function(){ return (D.positions||[]).length; }},
  {id:"conviction", label:"Conviction", render:tabConviction,
   count:function(){ return Object.keys(D.ladders||{}).length; }},
  {id:"track", label:"Track record", render:tabTrack,
   count:function(){ return (D.proposals.history||[]).length; }},
  {id:"diag", label:"Diagnostics", render:tabDiag,
   count:function(){ return (D.dq||[]).length+(D.gaps||[]).length; }}
];

function kpiCells(){
  var k=D.kpi, out=[];
  function cell(label,val,sub,tone){
    out.push('<div class="kpi'+(tone?" "+tone:"")+'"><span class="k">'+esc(label)+
      '</span><span class="v">'+val+"</span>"+
      (sub?'<span class="s">'+sub+"</span>":"")+"</div>"); }
  cell("Total book", usd(k.total_book), esc(k.count)+" positions");
  cell("Equity", usd(k.equity), "wallet "+usd(k.cash_usd));
  if(k.pnl_pct!=null) cell("P&L", signed(k.pnl_pct,2), "vs invested",
    k.pnl_pct>=0?"good":"hot");
  if(k.day_pct!=null) cell("Today", signed(k.day_pct,2), "book-weighted",
    k.day_pct>=0?"good":null);
  cell("Cash", pct(k.cash_pct,2),
    "band "+(k.cash_band||[]).join("–")+"%", k.cash_breach?"warm":null);
  cell("Drawdown", pct(k.dd_pct,2), "peak "+usd(k.dd_peak),
    (k.dd_pct||0)<-10?"hot":(k.dd_pct||0)<-5?"warm":null);
  cell("Open risk", pct(k.risk_pct,2), "cap "+pct(k.risk_cap,0),
    (k.risk_pct||0)>(k.risk_cap||100)?"hot":null);
  cell("AI-capex", pct(k.ai_capex,1), "single factor",
    (k.ai_capex||0)>=90?"warm":null);
  return out.join("");
}

function render(id){
  var t=null; TABS.forEach(function(x){ if(x.id===id) t=x; });
  if(!t) t=TABS[0];
  document.querySelectorAll(".tab").forEach(function(b){
    b.setAttribute("aria-selected", b.dataset.tab===t.id ? "true":"false"); });
  var w=document.getElementById("wrap");
  w.innerHTML='<div class="grid g2">'+t.render()+"</div>";
  if(location.hash.slice(1)!==t.id) history.replaceState(null,"","#"+t.id);
  window.scrollTo(0,0);
}

document.addEventListener("DOMContentLoaded", function(){
  document.getElementById("kpis").innerHTML=kpiCells();
  document.getElementById("tabbar").innerHTML=TABS.map(function(t){
    return '<button class="tab" role="tab" data-tab="'+t.id+'" aria-selected="false">'+
      esc(t.label)+'<span class="cnt">'+t.count()+"</span></button>"; }).join("");
  document.getElementById("tabbar").addEventListener("click", function(e){
    var b=e.target.closest(".tab"); if(b) render(b.dataset.tab); });
  render((location.hash||"").slice(1)||"command");
});

/* delegated interactions */
document.addEventListener("click", function(e){
  var t=e.target.closest("[data-tk]");
  if(t){ openTicker(t.dataset.tk); return; }
  if(e.target.closest(".sheet-close") || e.target.id==="sheetback"){ closeSheet(); return; }
  var chip=e.target.closest(".chipbtn");
  if(chip){ chip.setAttribute("aria-pressed",
      chip.getAttribute("aria-pressed")==="true"?"false":"true");
    if(document.getElementById("postbl"))
      document.getElementById("postbl").innerHTML=positionsTable();
    return; }
  var th=e.target.closest('th[data-sort="pos"]');
  if(th){
    var cols=JSON.parse(document.getElementById("poscols").textContent);
    var k=cols[+th.dataset.col];
    posSort = (posSort.key===k) ? {key:k,dir:-posSort.dir} : {key:k,dir:-1};
    document.getElementById("postbl").innerHTML=positionsTable();
    return; }
});
document.addEventListener("input", function(e){
  if(["posq","posc"].indexOf(e.target.id)>=0)
    document.getElementById("postbl").innerHTML=positionsTable();
  if(["hq","hs","hd"].indexOf(e.target.id)>=0)
    document.getElementById("htbl").innerHTML=historyTable();
});
document.addEventListener("change", function(e){
  if(["posc"].indexOf(e.target.id)>=0)
    document.getElementById("postbl").innerHTML=positionsTable();
  if(["hs","hd"].indexOf(e.target.id)>=0)
    document.getElementById("htbl").innerHTML=historyTable();
});
document.addEventListener("keydown", function(e){ if(e.key==="Escape") closeSheet(); });
</script>"""


# The decision round trip. Unlike v1 this does NOT string-surgery a row's markup -- rows are
# rendered client-side from the decisions array, so a recorded decision simply re-renders as
# recorded. Only the blob is swapped in the pristine source, which is the one thing
# smith_math.py's sync-decisions actually parses. That removes v1's attribute-order landmine
# entirely (see the module docstring).
DECISIONS_JS = r"""<script>
(function(){
  var PRISTINE = document.documentElement.outerHTML;   // captured at load, never the live DOM
  function readOnly(msg){
    document.querySelectorAll(".decide").forEach(function(el){
      el.querySelectorAll("button,input,select").forEach(function(x){ x.disabled = true; }); });
    var b = document.createElement("div");
    b.className = "ro-banner";
    b.textContent = msg || "Read-only view — decisions cannot be recorded from here. " +
      "Open your own copy of this artifact to accept or reject proposals.";
    var w = document.getElementById("wrap");
    if (w) w.insertBefore(b, w.firstChild);
  }
  if (!window.claude || !window.claude.self){
    document.addEventListener("DOMContentLoaded", function(){ readOnly(); });
    return;
  }
  document.body.addEventListener("click", function(ev){
    var btn = ev.target.closest(".decide button");
    if (!btn) return;
    var g = btn.closest(".decide");
    var surface = g.getAttribute("data-surface");
    var elementId = g.getAttribute("data-element-id");
    var decision = btn.getAttribute("data-decision");
    var ri = g.querySelector("input.reason");
    var reason = (ri && ri.value.trim()) ? ri.value.trim() : null;
    var payload = {surface: surface, element_id: elementId, decision: decision,
                   reason: reason, decided_on: new Date().toISOString().slice(0,10)};
    if (surface === "thesis" && decision === "override"){
      var sel = g.querySelector("select.new-status");
      payload.new_status = sel ? sel.value : null;
      if (!reason){ alert("An override needs a reason — your own read of the company " +
        "is the point of the button."); return; }
    }
    if (surface === "catalyst"){
      payload.headline = g.getAttribute("data-headline");
      payload.date = g.getAttribute("data-date");
    }
    var ctrls = g.querySelectorAll("button,input,select");
    ctrls.forEach(function(x){ x.disabled = true; });

    var arr;
    var m = PRISTINE.match(
      /<script type="application\/json" id="smith-decisions">([\s\S]*?)<\/script>/);
    try { arr = m ? (JSON.parse(m[1]) || []) : []; } catch(e){ arr = []; }
    arr.push(payload);
    var newHtml = PRISTINE.replace(
      /<script type="application\/json" id="smith-decisions">[\s\S]*?<\/script>/,
      '<script type="application/json" id="smith-decisions">' +
        JSON.stringify(arr).replace(/</g, "\\u003c") + "<\/script>");

    // optimistic local confirmation; the reload after publish re-renders it from the blob
    var span = document.createElement("span");
    span.className = "recorded";
    span.textContent = "Recorded: " + decision + (reason ? " — " + reason : "") +
      " (syncs on the next Agent Smith run)";
    g.replaceChildren(span);

    window.claude.self.publish("<!doctype html>" + newHtml).catch(function(err){
      var code = err && err.code;
      if (code === "conflict") return;
      if (code === "not_writer" || code === "not_granted" || code === "consent_required"){
        readOnly(); return; }
      alert("That decision was not saved (" + (code || "unknown error") + "). Try again.");
    });
  });
})();
</script>"""


def render_html(payload):
    meta = payload["meta"]
    blob = json.dumps(payload, separators=(",", ":"), default=str)
    # </script> inside data would close the tag early -- escape the only sequence that can.
    blob = blob.replace("</", "<\\/")
    head = (
        "<title>Agent Smith Desk</title>" + CSS +
        '<div class="mast"><div class="mast-in">'
        '<div class="mast-top"><span class="brand">Agent <em>Smith</em></span>'
        '<span class="pill acc">%s run</span>'
        '<div class="mast-meta">'
        "<span>%s</span><span>USD/INR <b>%s</b></span>"
        "<span>run <b>%s</b></span><span>built <b>%s</b></span>"
        "</div></div>"
        '<div class="kpis" id="kpis"></div></div>'
        '<div class="tabs" id="tabbar" role="tablist"></div></div>'
        % (
            (meta.get("mode") or "").upper(),
            (meta.get("ts") or "")[:16].replace("T", " "),
            ("%.2f" % meta["usdinr"]) if meta.get("usdinr") else "—",
            meta.get("run_dir") or "—",
            meta.get("generated") or "",
        )
    )
    return (
        head +
        '<main class="wrap" id="wrap"></main>'
        '<div class="sheet-back" id="sheetback"></div>'
        '<aside class="sheet" id="sheet" tabindex="-1" aria-label="ticker detail"></aside>'
        '<script type="application/json" id="smith-payload">' + blob + "</script>"
        '<script type="application/json" id="smith-decisions">[]</script>' +
        APP_JS + DECISIONS_JS
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-dir", default=".")
    ap.add_argument("--out", default=None)
    ap.add_argument("--built-at", default=None,
                    help="override the build timestamp (golden-master comparisons)")
    args = ap.parse_args()
    base = os.path.abspath(args.base_dir)
    out = args.out or os.path.join(base, "dashboard.html")

    payload = build_payload(base, built_at=args.built_at)
    html = render_html(payload)
    with open(out, "w") as f:
        f.write(html)

    # Build-time report -- the counts a reviewer needs to spot a regression at a glance.
    print("wrote %s (%.1f KB)" % (out, len(html) / 1024.0))
    print("  payload      %.1f KB" % (
        len(json.dumps(payload, default=str)) / 1024.0))
    print("  positions    %d" % len(payload["positions"]))
    print("  clusters     %d (%d with ladders)" % (
        len(payload["clusters"]), len(payload["ladders"])))
    print("  proposals    %d open / %d total" % (
        len(payload["proposals"]["open"]), len(payload["proposals"]["history"])))
    print("  triggers     %d families, %d rows" % (
        len(payload["triggers"]["families"]),
        sum(len(v) for v in payload["triggers"]["families"].values())))
    print("  thesis       %d / signals %d / catalysts %d" % (
        len(payload["thesis"]), len(payload["signals"]), len(payload["catalysts"])))
    print("  stops        %d scored / trades %d / ledger %d" % (
        len(payload["track"]["stops"]["rows"]), len(payload["trades"]),
        len(payload["ledger"])))
    print("  dq %d / gaps %d / freshness artefacts %d" % (
        len(payload["dq"]), len(payload["gaps"]),
        len(payload["freshness"]["artefacts"])))


if __name__ == "__main__":
    main()
