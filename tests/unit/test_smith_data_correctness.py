"""Phase 1D: one LTCG rule, honest proposal dates, readers not raw fields, report delta, learning."""
import contextlib
import importlib.util
import io
import json
import os
from argparse import Namespace
from datetime import date

import smith_learning as lrn
import smith_ledger as sl
import smith_lifecycle as lc
import smith_memory as sm

MIGRATIONS = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "migrations")


def _migration(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(MIGRATIONS, f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --- LTCG -------------------------------------------------------------------------------------
def test_ltcg_date_is_calendar_months_with_day_clamp():
    assert sl.ltcg_eligible_on(date(2024, 9, 15), 24) == date(2026, 9, 15)
    assert sl.ltcg_eligible_on(date(2024, 2, 29), 24) == date(2026, 2, 28)
    assert sl.ltcg_eligible_on(date(2025, 8, 31), 6) == date(2026, 2, 28)


def test_months_until_ltcg_is_negative_once_long_term():
    assert sl.months_until_ltcg(date(2024, 9, 30), date(2026, 9, 1), 24) > 0   # was "past" under whole-month math
    assert sl.months_until_ltcg(date(2024, 8, 1), date(2026, 9, 1), 24) < 0


def test_one_policy_reader():
    assert sl.policy_ltcg_months({}) == 24
    assert sl.policy_ltcg_months({"ltcg_boundary_months": 12}) == 12
    assert sl.policy_ltcg_months({"mandate": {"ltcg_months": 18}, "ltcg_boundary_months": 12}) == 18


# --- proposal dates -----------------------------------------------------------------------------
def test_zone_less_proposal_datetimes_are_ist():
    a = lc._proposal_parse_datetime("2026-09-14T09:00")
    b = lc._proposal_parse_datetime("2026-09-14T09:00:00+05:30")
    assert a == b


def test_dates_migration_rewrites_only_dishonest_shapes_and_is_idempotent():
    m = _migration("m2026_09_proposals_dates")
    rows = [{"date": "2026-09-01T00:00:00Z"}, {"date": "2026-09-01T10:30"},
            {"date": "2026-09-01T10:30:00+05:30"}, {"date": "2026-09-01"}, {"date": "2026-09-01T05:00:00Z"}]
    first = m.migrate_rows(rows)
    assert first == {"fake_midnight": 1, "naive_minute": 1}
    assert rows[0] == {"date": "2026-09-01", "date_raw": "2026-09-01T00:00:00Z"}
    assert rows[1]["date"] == "2026-09-01T10:30:00+05:30"
    assert "date_raw" not in rows[2] and "date_raw" not in rows[4]
    assert m.migrate_rows(rows) == {"fake_midnight": 0, "naive_minute": 0}


# --- readers --------------------------------------------------------------------------------------
def test_compact_archives_resolved_gaps_not_only_literal_closed(tmp_path):
    gaps = [{"id": "G1", "status": "open"}] + [
        {"id": f"G{i}", "status": s, "resolved_on": f"2026-08-{i:02d}"}
        for i, s in zip(range(2, 14), ["resolved", "fixed", "done", "closed"] * 3)]
    (tmp_path / "state.json").write_text(json.dumps({"known_gaps": gaps, "thesis": {}, "sector_map": {}}))
    (tmp_path / "holdings.json").write_text(json.dumps({"holdings_inr": []}))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        sm.cmd_compact(Namespace(base_dir=str(tmp_path), holdings=str(tmp_path / "holdings.json"),
                                 today="2026-09-14", write=True))
    kept = json.loads((tmp_path / "state.json").read_text())["known_gaps"]
    assert "G1" in {g["id"] for g in kept}
    assert len(kept) == 1 + sm.RETENTION["known_gaps"]["keep_recent"]


# --- report ---------------------------------------------------------------------------------------
def test_daily_report_counts_cash_so_a_sell_down_is_not_a_loss(tmp_path):
    base, rd = tmp_path, tmp_path / "runs" / "r"
    rd.mkdir(parents=True)
    hdr = "ts,mode,value_usd,usdinr,wallet_usd,spx,ndx,smh,smh_asof,est_net_flows_usd,external_flow_usd,value_trust,notes\r\n"
    (base / "ledger.csv").write_text(hdr + "2026-09-10T03:31:00+00:00,quick,42000,95,1500,1,1,,,,,ok,a\r\n"
                                           "2026-09-14T01:00:00+00:00,quick,33800,95,9700,1,1,,,,,ok,b\r\n")
    (rd / "compute_book.json").write_text(json.dumps({"value_usd": 33800, "wallet_usd": 9700}))
    text = "\n".join(sm._report_daily(str(base), str(rd), date(2026, 9, 14), {}, [])) \
        if isinstance(sm._report_daily(str(base), str(rd), date(2026, 9, 14), {}, []), list) \
        else sm._report_daily(str(base), str(rd), date(2026, 9, 14), {}, [])
    line = next(l for l in text.splitlines() if l.startswith("| Change vs last run"))
    assert "equity + cash" in line and "-20" not in line and "−20" not in line


# --- learning -------------------------------------------------------------------------------------
def _proposals(tmp_path, hot, archived=()):
    (tmp_path / "proposals.json").write_text(json.dumps({"proposals": hot}))
    (tmp_path / "proposals-archive.json").write_text(json.dumps({"proposals": list(archived)}))


POST = "2026-09-22"   # on/after smith_core.ENGINE_EPOCH


def test_readiness_counts_distinct_scored_proposals_across_archive(tmp_path):
    _proposals(tmp_path,
               # dated post-epoch: the readiness counter admits only proposals on/after ENGINE_EPOCH
               # (user instruction 2026-09-21); the pre-epoch behaviour is in test_smith_epoch_filter.py
               [{"id": "P-1", "outcome_verdict": "worked", "date": POST}, {"id": "P-2", "outcome_verdict": "missed", "date": POST},
                {"id": "P-3", "date": POST}],
               [{"id": "P-1", "outcome_verdict": "worked", "date": POST}, {"id": "P-9", "outcome_verdict": "neutral", "date": POST}])
    counts = lrn.update_phase4_readiness(str(tmp_path))
    assert (counts["scored"], counts["worked"], counts["missed"], counts["decided"]) == (3, 1, 1, 2)
    assert counts["legacy_excluded"] == 0
    p = lrn.load_store(str(tmp_path))["parameters"]["phase4.readiness"]
    assert p["current"] == 3 and p["n_gate"] == 100


def test_validate_flags_a_stale_readiness_counter(tmp_path):
    _proposals(tmp_path, [{"id": "P-1", "outcome_verdict": "worked", "date": POST}])
    (tmp_path / "learning.json").write_text(json.dumps({"observations": [], "lessons": [],
                                                        "parameters": {"phase4.readiness": {"current": 8}}}))
    assert any("LEARNING COUNTER" in d for d in sm.validate_learning_schema(str(tmp_path)))


def test_lessons_get_stable_ids_and_supersede_by_id(tmp_path):
    a = lrn.add_lesson(str(tmp_path), "correction", "first")
    b = lrn.add_lesson(str(tmp_path), "correction", "fixes first", supersedes=a["id"])
    c = lrn.add_lesson(str(tmp_path), "correction", "legacy index", supersedes=1)
    assert (a["id"], b["id"], c["id"]) == ("L-001", "L-002", "L-003")
    assert b["supersedes"] == "L-001" and c["supersedes"] == "L-002"


def test_learning_migration_assigns_ids_fixes_pointers_and_merges_usage_keys():
    m = _migration("m2026_09_learning_ids")
    lessons = [{"text": f"l{i}"} for i in range(30)]
    lessons[4]["supersedes"], lessons[28]["supersedes"] = 2, 7
    store = {"lessons": lessons, "observations": [{"param_id": "usage:smith-thesis"},
                                                  {"param_id": "usage:thesis"}]}
    out = m.migrate(store)
    assert lessons[4]["supersedes"] == "L-002" and lessons[28]["supersedes"] == "L-028"
    assert lessons[4]["supersedes_raw"] == 2
    assert {o["param_id"] for o in store["observations"]} == {"usage:thesis"}
    assert m.migrate(store)["ids_assigned"] == 0 and out["usage_keys_canonicalised"] == 1


def test_canonical_agent():
    assert lrn.canonical_agent("smith-thesis") == lrn.canonical_agent("thesis") == "thesis"
