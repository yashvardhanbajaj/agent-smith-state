"""Freshness coverage for EXTERNAL producers Smith reads but does not write.

Added 2026-09-06. The HBM tracker is a separate, deliberately on-demand skill, but three Smith
sub-agents (thesis, catalyst, cycle) read its consumer_view.json every deep run via the
runs/<ts>/shared/ snapshot. It was NOT declared in FRESHNESS, so Smith depended on it entirely
and owned none of its freshness: on the run that found this, the briefing headline said
"Freshness: all artefacts within TTL" while the snapshot was 32 days old.

These tests pin the two halves of the fix -- the declaration and the mount -- because either one
alone is silent: a FRESHNESS row whose key never resolves reports `missing` forever, and a mount
with no row is never evaluated at all.
"""
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import smith_core as sc
import smith_memory as sm


class TestExternalProducerFreshness:
    def test_hbm_tracker_is_declared_and_escalates(self):
        row = sc.FRESHNESS.get("hbm_tracker")
        assert row is not None, "hbm_tracker must stay declared -- 3 sub-agents read it every deep run"
        assert row["stamp"] == "field:last_run"
        assert row["owner"] == "hbm-tracker"
        # escalate makes dark_at == ttl, so `validate` FAILS rather than merely noting it.
        assert row["on_stale"] == "escalate"
        # Tighter than the tracker's own ~30-day confidence rule, so there is a week to refresh
        # before consumers are obliged to degrade.
        assert row["ttl_days"] == 21 < 30

    def test_every_shared_source_is_mounted_by_freshness_root(self, tmp_path):
        """The mount is what makes the declaration resolve. Without it the row reports
        `missing` forever, which looks like a broken artefact rather than a stale one."""
        (tmp_path / "state.json").write_text("{}")
        (tmp_path / "proposals.json").write_text("{}")
        root = sm.freshness_root(str(tmp_path), state={})
        for key in sm.SHARED_SOURCES:
            assert key in root, f"{key} declared in SHARED_SOURCES but not mounted"

    def test_path_is_declared_once_not_twice(self):
        """The slice snapshot and the age check must read the SAME declared path. Two copies of
        a path is how one of them goes stale."""
        assert "hbm_tracker" in sm.SHARED_SOURCES
        assert sm.SHARED_SOURCES["hbm_tracker"].endswith("consumer_view.json")

    def test_stale_tracker_reads_dark_not_fresh(self, tmp_path, monkeypatch):
        """The founding case: last_run 2026-08-05 evaluated at 2026-09-06 is 32 days, past a
        21-day escalate TTL, and must come back `dark` -- not fresh, not merely stale."""
        ext = tmp_path / "consumer_view.json"
        ext.write_text(json.dumps({"last_run": "2026-08-05", "schema_version": 1}))
        monkeypatch.setattr(sm, "SHARED_SOURCES", {"hbm_tracker": str(ext)})
        (tmp_path / "state.json").write_text("{}")
        (tmp_path / "proposals.json").write_text("{}")
        root = sm.freshness_root(str(tmp_path), state={})
        rows = {r["key"]: r for r in sm.evaluate_freshness(root, date(2026, 9, 6))}
        r = rows["hbm_tracker"]
        assert r["as_of"] == "2026-08-05"
        assert r["age_days"] == 32
        assert r["state"] == "dark"

    def test_fresh_tracker_reads_fresh(self, tmp_path, monkeypatch):
        ext = tmp_path / "consumer_view.json"
        ext.write_text(json.dumps({"last_run": "2026-09-01"}))
        monkeypatch.setattr(sm, "SHARED_SOURCES", {"hbm_tracker": str(ext)})
        (tmp_path / "state.json").write_text("{}")
        (tmp_path / "proposals.json").write_text("{}")
        rows = {r["key"]: r for r in
                sm.evaluate_freshness(sm.freshness_root(str(tmp_path), state={}), date(2026, 9, 6))}
        assert rows["hbm_tracker"]["state"] == "fresh"

    def test_missing_tracker_file_is_missing_not_silently_fresh(self, tmp_path, monkeypatch):
        monkeypatch.setattr(sm, "SHARED_SOURCES",
                            {"hbm_tracker": str(tmp_path / "does_not_exist.json")})
        (tmp_path / "state.json").write_text("{}")
        (tmp_path / "proposals.json").write_text("{}")
        rows = {r["key"]: r for r in
                sm.evaluate_freshness(sm.freshness_root(str(tmp_path), state={}), date(2026, 9, 6))}
        assert rows["hbm_tracker"]["state"] == "missing"
