"""Conflict detection between sub-agent outputs (added 2026-09-06).

Stage 1 dispatched every analyst in parallel, so no agent could see another's findings. These
tests reconstruct the four real failures from the 2026-09-06 deep run. The detector is what makes
the wave split enforceable: without it, "interpreters run after observers" is just a doc comment.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import smith_memory as sm


def run(tmp, **outs):
    rd = tmp / "run"
    rd.mkdir(exist_ok=True)
    (rd / "compute_triggers.json").write_text(json.dumps(outs.pop("triggers", {})))
    for agent, blob in outs.items():
        (rd / f"out_{agent}.json").write_text(json.dumps(blob))
    res = {}
    orig = sm.emit
    sm.emit = lambda d: res.update(d)
    try:
        class A:
            base_dir, run_dir, today = str(tmp), str(rd), "2026-09-06"
        sm.cmd_crosscheck(A())
    finally:
        sm.emit = orig
    return res


def kinds(r):
    return sorted({f["kind"] for f in r["findings"]})


class TestEvidenceGap:
    def test_empty_evidence_against_on_a_quality_flagged_ticker(self, tmp_path):
        """THE case: thesis wrote APH `strengthening` with evidence_against "none found this
        run" while quality had +157% QoQ interest expense on APH in the same run."""
        r = run(tmp_path,
                thesis={"thesis": {"changed": {"APH": {
                    "status": "strengthening",
                    "evidence_against": [{"claim": "none found this run", "date": "2026-09-06"}]}}}},
                quality={"quality_flags": {"APH": [
                    {"finding": "acquisition financing", "magnitude": "+157% QoQ"}]}})
        assert "evidence_gap" in kinds(r)
        f = [x for x in r["findings"] if x["kind"] == "evidence_gap"][0]
        assert f["ticker"] == "APH" and f["severity"] == "high"
        assert "+157% QoQ" in f["detail"]

    def test_a_genuinely_empty_list_also_counts(self, tmp_path):
        r = run(tmp_path,
                thesis={"thesis": {"changed": {"AAA": {"status": "intact", "evidence_against": []}}}},
                quality={"quality_flags": {"AAA": [{"finding": "x", "magnitude": "y"}]}})
        assert "evidence_gap" in kinds(r)

    def test_real_counter_evidence_is_not_flagged(self, tmp_path):
        """The check must not fire when the agent DID carry the other side."""
        r = run(tmp_path,
                thesis={"thesis": {"changed": {"AAA": {"status": "intact", "evidence_against": [
                    {"claim": "debt up 21% QoQ", "source": "10-Q"}]}}}},
                quality={"quality_flags": {"AAA": [{"finding": "x", "magnitude": "y"}]}})
        assert "evidence_gap" not in kinds(r)

    def test_no_quality_flag_means_no_gap(self, tmp_path):
        r = run(tmp_path,
                thesis={"thesis": {"changed": {"AAA": {"status": "intact", "evidence_against": []}}}},
                quality={"quality_flags": {}})
        assert r["count"] == 0


class TestHandoffToNowhere:
    def test_a_handoff_to_a_same_wave_agent_is_flagged(self, tmp_path):
        r = run(tmp_path, thesis={"thesis_tensions": [
            {"reconciliation": "proximate cause unresolved, handed to smith-catalyst."}]})
        f = [x for x in r["findings"] if x["kind"] == "handoff_to_nowhere"][0]
        assert f["from"] == "smith-thesis" and f["to"] == "smith-catalyst"
        assert f["severity"] == "high"

    def test_other_phrasings_are_caught(self, tmp_path):
        r = run(tmp_path, cycle={"note": "deferred to smith-quality for the balance-sheet read"})
        assert "handoff_to_nowhere" in kinds(r)


class TestCatalystVsCycle:
    def test_structural_tailwind_against_a_late_cycle_is_flagged(self, tmp_path):
        """catalyst called DRAM +50% a STRUCTURAL tailwind while cycle held `late` on a
        decelerating contract series. Both went into the briefing unreconciled."""
        r = run(tmp_path,
                catalyst={"catalysts": [{"headline": "DRAM contract +50% QoQ", "direction": "tailwind",
                                         "horizon": "structural", "affects": ["MU"]}]},
                cycle={"cycle_position": "late"})
        f = [x for x in r["findings"] if x["kind"] == "catalyst_vs_cycle"][0]
        assert f["severity"] == "high" and f["affects"] == ["MU"]

    def test_a_mechanical_catalyst_does_not_trip_it(self, tmp_path):
        """A sympathy rally is not a claim about the cycle."""
        r = run(tmp_path,
                catalyst={"catalysts": [{"headline": "M&A read-through", "direction": "tailwind",
                                         "horizon": "mechanical"}]},
                cycle={"cycle_position": "late"})
        assert "catalyst_vs_cycle" not in kinds(r)

    def test_no_conflict_when_the_cycle_is_early(self, tmp_path):
        r = run(tmp_path,
                catalyst={"catalysts": [{"headline": "x", "direction": "tailwind",
                                         "horizon": "structural"}]},
                cycle={"cycle_position": "accelerating"})
        assert "catalyst_vs_cycle" not in kinds(r)


class TestThesisVsSignals:
    def test_strengthening_thesis_on_a_live_catalyst_threat(self, tmp_path):
        r = run(tmp_path,
                thesis={"thesis": {"changed": {"AAA": {"status": "strengthening",
                                                       "evidence_against": [{"claim": "real"}]}}}},
                triggers={"catalyst_threat": [{"ticker": "AAA"}]})
        f = [x for x in r["findings"] if x["kind"] == "thesis_vs_catalyst_threat"][0]
        assert f["severity"] == "medium"      # arguable, not wrong

    def test_strengthening_thesis_on_a_peer_laggard_is_noted_only(self, tmp_path):
        r = run(tmp_path,
                thesis={"thesis": {"changed": {"AAA": {"status": "strengthening",
                                                       "evidence_against": [{"claim": "real"}]}}}},
                signals={"signal_history": {"changed": {"AAA": ["PEER LAGGARD"]}}})
        f = [x for x in r["findings"] if x["kind"] == "thesis_vs_price"][0]
        assert f["severity"] == "low"         # often correct -- that's what a value entry is


class TestCleanRun:
    def test_a_run_with_no_conflicts_reports_none(self, tmp_path):
        r = run(tmp_path, thesis={"thesis": {"changed": {}}}, quality={"quality_flags": {}})
        assert r["count"] == 0 and r["blocking"] == []


# ---------------------------------------------------------------------------
# ladder_vs_thesis (added 2026-09-08)
# ---------------------------------------------------------------------------
# smith-cluster ranks members COMPARATIVELY; smith-thesis judges each on its own. A name ranked
# last in its cluster while the desk calls it strengthening means two agents looked at the same
# company and disagreed. Since 2026-09-08 the ladder can drive a live rotation, so leaving that
# unadjudicated turns it into a sized trade.

import json
import os

import smith_memory as sm


class _CCArgs:
    def __init__(self, base_dir, run_dir, today="2026-09-08"):
        self.base_dir, self.run_dir, self.today = base_dir, run_dir, today


def _cc(tmp_path, capsys, *, verdict="laggard", status="strengthening",
        confidence="high", as_of="2026-09-06", tensions=None):
    base, rd = tmp_path / "b", tmp_path / "r"
    base.mkdir(exist_ok=True); rd.mkdir(exist_ok=True)
    (base / "state.json").write_text(json.dumps({
        "thesis": {"APH": f"connectors|{status}"},
        "cluster_ladders": {"AI Networking/Optics": {
            "as_of": as_of, "confidence": confidence, "leader": "COHR", "laggard": "APH",
            "thesis_tensions": tensions or [],
            "ranking": [{"rank": 1, "ticker": "COHR", "verdict": "leader"},
                        {"rank": 2, "ticker": "APH", "verdict": verdict}]}}}))
    sm.cmd_crosscheck(_CCArgs(str(base), str(rd)))
    out = json.loads(capsys.readouterr().out)
    return [f for f in out["findings"] if f["kind"] == "ladder_vs_thesis"]


class TestLadderVsThesis:
    def test_a_laggard_on_a_strengthening_thesis_is_flagged(self, tmp_path, capsys):
        f = _cc(tmp_path, capsys)
        assert len(f) == 1 and f[0]["ticker"] == "APH" and f[0]["severity"] == "high"
        assert f[0]["cluster"] == "AI Networking/Optics"

    def test_a_leader_on_a_watch_thesis_is_flagged(self, tmp_path, capsys):
        f = _cc(tmp_path, capsys, verdict="leader", status="watch")
        assert len(f) == 1 and "ranks APH FIRST" in f[0]["detail"]

    def test_an_agreeing_rank_is_not_flagged(self, tmp_path, capsys):
        assert _cc(tmp_path, capsys, verdict="laggard", status="watch") == []
        assert _cc(tmp_path, capsys, verdict="leader", status="strengthening") == []

    def test_a_middle_rank_is_never_a_contradiction(self, tmp_path, capsys):
        assert _cc(tmp_path, capsys, verdict="middle") == []

    def test_a_self_reported_tension_is_not_double_counted(self, tmp_path, capsys):
        """The agent is asked to report these itself; this rule catches the ones it missed."""
        assert _cc(tmp_path, capsys, tensions=[{"ticker": "APH"}]) == []

    def test_an_advisory_only_ladder_is_medium_not_high(self, tmp_path, capsys):
        """A contradicted ranking that carries no trigger authority is worth reporting, not
        worth blocking on."""
        f = _cc(tmp_path, capsys, confidence="low")
        assert f[0]["severity"] == "medium" and "advisory only" in f[0]["detail"]

    def test_a_stale_ladder_is_medium_not_high(self, tmp_path, capsys):
        f = _cc(tmp_path, capsys, as_of="2026-07-01")
        assert f[0]["severity"] == "medium"

    def test_a_medium_confidence_ladder_still_blocks_because_it_can_size(self, tmp_path, capsys):
        assert _cc(tmp_path, capsys, confidence="medium")[0]["severity"] == "high"
