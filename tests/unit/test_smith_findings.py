"""Prior-findings digest (smith_findings, added 2026-09-15)."""
import json
from datetime import date

import smith_findings as sf

TODAY = date(2026, 9, 15)
STATE = {
    "holdings": [{"ticker": "MU"}, {"ticker": "GEV"}],
    "factor_catalysts": [
        {"headline": "Amodei pacing essay", "date": "2026-09-14", "first_seen": "2026-09-14",
         "horizon": "immediate", "direction": "threat", "affects": ["MU", "GEV"], "source": "s1",
         "magnitude": "no capex cut"},
        {"headline": "GLW ATM offering", "date": "2026-09-14", "horizon": "structural",
         "affects": ["GLW"], "source": "s2"}],
    "fomc_cache": {"rate_pct": 3.63, "stance": "hawkish", "next_check_date": "2026-09-17", "note": "n"},
    "macro_read": {"as_of": "2026-09-15", "regime": "risk_off", "regime_note": "r",
                   "calendar": {"next_fomc": "2026-09-16"}},
    "thesis": {"MU": {"status": "watch", "thesis": "CXMT risk", "reviewed_on": "2026-09-15"},
               "OLD": {"status": "intact", "thesis": "not held", "reviewed_on": "2026-09-01"}},
    "cluster_ladders": {"AI Semis/Fabs": {"as_of": "2026-09-15", "leader": "TSM", "laggard": "AMAT",
                                          "ranking": [{"t": "TSM"}, {"t": "AMAT"}], "confidence": "medium"}},
}


def _rd(tmp_path, name="2026-09-15-0740Z", **files):
    rd = tmp_path / "runs" / name
    rd.mkdir(parents=True, exist_ok=True)
    for fname, obj in files.items():
        (rd / f"{fname}.json").write_text(json.dumps(obj))
    return rd


def test_extract_covers_every_source_with_kind_specific_ttls(tmp_path):
    rd = _rd(tmp_path,
             out_strategist={"fomc_playbook": {"decision_date": "2026-09-16", "scenarios": [
                 {"branch": "surprise_hold", "probability_pct": 20, "staged_actions": {"execute": ["BUY MSFT"]}}]}},
             findings_orchestrator=[{"claim": "Monday was sentiment, not a capex cut",
                                     "subject": "AI capex", "ttl_days": 3}])
    got = {f["id"]: f for f in sf.extract(STATE, str(rd), "2026-09-15-0740Z", TODAY)}
    assert {f["kind"] for f in got.values()} == {"catalyst", "macro", "thesis", "ladder", "playbook", "orchestrator"}
    assert {f["ttl_days"] for f in got.values() if f["kind"] == "catalyst"} == {2, 14}
    assert "thesis:MU" in got and "thesis:OLD" not in got          # held names only
    assert got["macro:fomc"]["expires"] == "2026-09-17"            # lives until the next check date
    assert any(f["kind"] == "playbook" and "surprise_hold" in f["claim"] for f in got.values())


def test_update_counts_repeat_runs_and_applies_agent_feedback(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    (base / "state.json").write_text(json.dumps(STATE))
    s1 = sf.update(str(base), str(_rd(tmp_path)), "run1", TODAY)
    assert s1["added"] >= 5 and s1["feedback"]["reaffirmed"] == 0
    cat_id = next(f["id"] for f in sf.load(str(base))["findings"]
                  if f["kind"] == "catalyst" and "Amodei" in f["claim"])
    rd2 = _rd(tmp_path, name="2026-09-16-0740Z", out_catalyst={
        "findings_reaffirmed": [cat_id],
        "findings_revised": [{"id": "macro:regime", "claim": "Regime neutral after the hold",
                              "source": "CME", "reason": "hold"}]})
    s2 = sf.update(str(base), str(rd2), "run2", date(2026, 9, 16))
    assert s2["feedback"] == {"reaffirmed": 1, "revised": 1, "unknown_ids": []}
    by = {f["id"]: f for f in sf.load(str(base))["findings"]}
    assert by[cat_id]["runs_seen"] == 2 and by[cat_id]["reaffirmed_by"] == ["catalyst"]
    assert by["macro:regime"]["claim"].startswith("Regime neutral")
    assert by["macro:regime"]["revised_by"] == "catalyst"


def test_expired_findings_are_flagged_then_pruned(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    (base / "state.json").write_text(json.dumps({"holdings": []}))
    (base / "findings.json").write_text(json.dumps({"schema_version": 1, "findings": [
        {"id": "macro:old", "kind": "macro", "claim": "c", "as_of": "2026-09-10", "expires": "2026-09-11"},
        {"id": "macro:ancient", "kind": "macro", "claim": "c", "as_of": "2026-07-01", "expires": "2026-07-02"}]}))
    s = sf.update(str(base), str(_rd(tmp_path)), "r", TODAY)
    by = {f["id"]: f for f in sf.load(str(base))["findings"]}
    assert by["macro:old"]["expired"] is True and "macro:ancient" not in by and s["pruned"] == 1


def test_a_newer_schema_is_refused_not_overwritten(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    (base / "findings.json").write_text(json.dumps({"schema_version": 2, "findings": []}))
    assert "error" in sf.update(str(base), str(_rd(tmp_path)), "r", TODAY, state={})
    assert json.loads((base / "findings.json").read_text())["schema_version"] == 2


def test_digest_is_filtered_per_agent_and_per_cluster():
    doc = {"run_ts": "2026-09-15T08:39:11Z", "run_id": "r", "findings": [
        {"id": "catalyst:a", "kind": "catalyst", "subject": ["MU"], "claim": "a", "as_of": "2026-09-14", "expires": "2026-09-20"},
        {"id": "catalyst:b", "kind": "catalyst", "subject": ["GLW"], "claim": "b", "as_of": "2026-09-14", "expires": "2026-09-20"},
        {"id": "thesis:MU", "kind": "thesis", "subject": "MU", "claim": "watch", "as_of": "2026-09-15", "expires": "2026-10-06"},
        {"id": "ladder:x", "kind": "ladder", "subject": "AI Semis/Fabs", "claim": "TSM > AMAT", "as_of": "2026-09-15", "expires": "2026-09-22"},
        {"id": "ladder:y", "kind": "ladder", "subject": "AI Power", "claim": "BE > VRT", "as_of": "2026-09-15", "expires": "2026-09-22"},
        {"id": "macro:gone", "kind": "macro", "subject": "Fed", "claim": "old", "as_of": "2026-09-01", "expires": "2026-09-02"}]}
    cat = sf.digest_for(doc, "catalyst", held={"MU"}, today=TODAY)
    assert [f["id"] for f in cat["findings"]] == ["catalyst:a", "catalyst:b"]
    assert cat["since"] == "2026-09-15T08:39:11Z" and "delta" in cat["rule"]
    cl = sf.digest_for(doc, "cluster_semis", cluster_name="AI Semis/Fabs",
                       cluster_members={"MU", "TSM"}, today=TODAY)
    assert {f["id"] for f in cl["findings"]} == {"ladder:x", "catalyst:a"}
    assert sf.digest_for(doc, "ledger", today=TODAY)["findings"] == []
    assert sf.digest_for(None, "catalyst", today=TODAY)["findings"] == []
