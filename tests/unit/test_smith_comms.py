"""The desk conversation router (smith_comms.py, added 2026-09-19).

Each class pins one promise the protocol makes to the analysts. Most of these fail SILENTLY if
broken -- the run still produces a briefing, just one where a question went nowhere, a revision
reached nobody, or a settled argument was re-opened every round -- which is the exact failure
the module was built to end ("handed to smith-catalyst" about a question catalyst never saw).
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import smith_comms as sc


def make_run(tmp_path, ran=(), scheduled=(), crosscheck=None):
    base = tmp_path / "base"
    rd = base / "runs" / "r"
    rd.mkdir(parents=True)
    (base / "state.json").write_text("{}")
    waves = {"1": sorted(set(ran) | set(scheduled))}
    (rd / "dispatch_plan.json").write_text(json.dumps({"waves": waves}))
    for a in ran:
        (rd / f"out_{a}.json").write_text("{}")
    if crosscheck is not None:
        (rd / "crosscheck.json").write_text(json.dumps({"findings": crosscheck}))
    return str(rd)


def tail(rd, name, obj):
    Path(rd, name).write_text(json.dumps(obj))


def ledger(rd):
    return sc.load_ledger(rd)


class TestAddressing:
    def test_unknown_recipient_is_rejected_not_dropped_silently(self, tmp_path):
        rd = make_run(tmp_path, ran=["thesis"])
        tail(rd, "out_thesis.json", {"comms": {"asks": [{"to": "oracle", "question": "q?"}]}})
        rec = sc.route(rd)
        assert rec["rejected"] and "unknown recipient" in rec["rejected"][0]["why"]
        assert rec["counts"]["total"] == 0

    def test_an_agent_cannot_ask_itself(self, tmp_path):
        rd = make_run(tmp_path, ran=["thesis"])
        tail(rd, "out_thesis.json", {"comms": {"asks": [{"to": "thesis", "question": "q?"}]}})
        assert "itself" in sc.route(rd)["rejected"][0]["why"]


class TestDeliveryModes:
    def test_question_to_a_scheduled_agent_rides_in_its_slice_for_free(self, tmp_path):
        rd = make_run(tmp_path, ran=["catalyst"], scheduled=["thesis"])
        tail(rd, "out_catalyst.json", {"comms": {"asks": [
            {"to": "thesis", "ticker": "MU", "question": "Is MU's HBM share thesis intact?",
             "why": "sets threat magnitude", "blocking": True}]}})
        rec = sc.route(rd)
        assert rec["deliveries"]["thesis"]["mode"] == "inbox"
        assert rec["converged"]            # queued for a scheduled layer is not "owed" yet
        block = sc.slice_block(rd, "thesis")
        assert block["desk_inbox"][0]["ticker"] == "MU"
        assert "desk_protocol" in block and "thesis" in block["desk_directory"]

    def test_question_to_an_agent_off_the_roster_opens_a_new_layer(self, tmp_path):
        rd = make_run(tmp_path, ran=["thesis"])
        tail(rd, "out_thesis.json", {"comms": {"asks": [
            {"to": "earnings", "ticker": "MU", "question": "Was FQ4 a beat on revenue?",
             "blocking": True}]}})
        rec = sc.route(rd)
        assert rec["deliveries"]["earnings"]["mode"] == "dispatch"
        assert rec["new_agents"] == ["earnings"]
        assert not rec["converged"]

    def test_question_to_desk_goes_to_the_orchestrator(self, tmp_path):
        rd = make_run(tmp_path, ran=["thesis"])
        tail(rd, "out_thesis.json", {"comms": {"asks": [
            {"to": "desk", "ticker": "AMAT", "question": "AMAT 60d correlation to KLAC?"}]}})
        rec = sc.route(rd)
        assert rec["desk_requests"][0]["ticker"] == "AMAT"
        assert not rec["converged"]


class TestAnswersCloseTheLoop:
    def _ask(self, tmp_path, blocking=True):
        rd = make_run(tmp_path, ran=["thesis", "catalyst"])
        tail(rd, "out_thesis.json", {"comms": {"asks": [
            {"to": "catalyst", "ticker": "AMAT", "question": "Does CXMT reach AMAT?",
             "why": "strengthening vs watch", "blocking": blocking}]}})
        sc.route(rd)
        return rd, ledger(rd)["messages"][0]["id"]

    def test_answer_marks_answered_and_the_asker_hears_it(self, tmp_path):
        rd, mid = self._ask(tmp_path)
        tail(rd, "out_catalyst.r1.json", {"comms": {"answers": [
            {"id": mid, "position": "held", "answer": "No: CXMT is a memory maker, not a WFE buyer "
             "at AMAT scale", "confidence": "medium"}]}})
        rec = sc.route(rd)
        doc = ledger(rd)
        asked = next(m for m in doc["messages"] if m["id"] == mid)
        assert asked["status"] == "answered" and asked["answer"]["position"] == "held"
        reply = next(m for m in doc["messages"] if m["kind"] == "reply")
        assert reply["to"] == "thesis" and reply["reply_to"] == mid
        assert rec["deliveries"]["thesis"]["mode"] == "resume"     # blocking -> asker woken

    def test_non_blocking_answer_is_recorded_not_woken(self, tmp_path):
        rd, mid = self._ask(tmp_path, blocking=False)
        tail(rd, "out_catalyst.r1.json", {"comms": {"answers": [
            {"id": mid, "position": "held", "answer": "no"}]}})
        rec = sc.route(rd)
        assert "thesis" not in rec["deliveries"]
        assert rec["converged"]
        assert sc.slice_block(rd, "thesis")["desk_replies"][0]["position"] == "held"

    def test_only_the_addressee_may_answer(self, tmp_path):
        rd, mid = self._ask(tmp_path)
        tail(rd, "out_signals.r1.json", {"comms": {"answers": [{"id": mid, "answer": "x"}]}})
        rec = sc.route(rd)
        assert any("addressed to" in r["why"] for r in rec["rejected"])

    def test_returning_without_answering_gets_one_reminder_then_is_reported(self, tmp_path):
        rd, mid = self._ask(tmp_path)
        tail(rd, "out_catalyst.r1.json", {"comms": {}})
        rec2 = sc.route(rd)
        assert mid in rec2["reminders"]
        assert rec2["deliveries"]["catalyst"]["messages"] == [mid]
        tail(rd, "out_catalyst.r2.json", {"comms": {}})
        sc.route(rd)
        m = next(x for x in ledger(rd)["messages"] if x["id"] == mid)
        assert m["status"] == "unanswered"
        assert any(u["id"] == mid for u in sc.digest(ledger(rd))["unresolved"])


class TestRevisions:
    def test_revision_overlays_the_tail_keeps_the_original_and_tells_consumers(self, tmp_path):
        rd = make_run(tmp_path, ran=["thesis", "catalyst"], scheduled=["strategist"])
        tail(rd, "out_thesis.json", {"thesis": {"changed": {
            "AMAT": {"status": "strengthening"}, "MU": {"status": "watch"}}}})
        tail(rd, "out_catalyst.json", {"comms": {"asks": [
            {"to": "thesis", "ticker": "AMAT", "question": "CXMT threat on AMAT?", "blocking": True}]}})
        sc.route(rd)
        mid = ledger(rd)["messages"][0]["id"]
        tail(rd, "out_thesis.r1.json", {"comms": {"answers": [
            {"id": mid, "position": "revised", "answer": "downgrade to intact",
             "revision": {"thesis": {"changed": {"AMAT": {"status": "intact"}}},
                          "journal_new": [{"x": 1}]}}]}})
        rec = sc.route(rd)
        now = json.loads(Path(rd, "out_thesis.json").read_text())
        assert now["thesis"]["changed"]["AMAT"]["status"] == "intact"
        assert now["thesis"]["changed"]["MU"]["status"] == "watch"        # untouched
        assert "journal_new" not in now                                     # blocked key
        orig = json.loads(Path(rd, "out_thesis.r0.json").read_text())
        assert orig["thesis"]["changed"]["AMAT"]["status"] == "strengthening"
        assert rec["remerge"] == ["thesis"] and rec["rerun_crosscheck"]
        revs = [m for m in ledger(rd)["messages"] if m["kind"] == "revision"]
        assert {m["to"] for m in revs} >= {"strategist"}
        assert rec["deliveries"]["strategist"]["mode"] == "inbox"

    def test_list_overlay_matches_on_identity_not_position(self):
        base = {"catalysts": [{"headline": "A", "affects": ["X", "AMAT"]},
                              {"headline": "B", "affects": ["Y"]}]}
        out = sc._overlay(base, {"catalysts": [{"headline": "A", "affects": ["X"]}]})
        assert out["catalysts"][0]["affects"] == ["X"]
        assert out["catalysts"][1]["headline"] == "B"


class TestDebates:
    CC = [{"kind": "thesis_vs_catalyst_threat", "ticker": "AMAT", "severity": "medium"}]

    def test_a_conflict_becomes_a_challenge_to_each_side(self, tmp_path):
        rd = make_run(tmp_path, ran=["thesis", "catalyst"], crosscheck=self.CC)
        tail(rd, "out_thesis.json", {"thesis": {"changed": {"AMAT": {
            "status": "strengthening", "evidence_for": [{"claim": "Q3 beat"}]}}}})
        rec = sc.route(rd)
        assert rec["debates_opened"] == ["thesis_vs_catalyst_threat|AMAT"]
        to = sorted(m["to"] for m in ledger(rd)["messages"] if m["kind"] == "debate")
        assert to == ["catalyst", "thesis"]
        cat = next(m for m in ledger(rd)["messages"] if m["to"] == "catalyst")
        assert cat["counterparty"]["evidence_for"][0]["claim"] == "Q3 beat"

    def test_a_settled_debate_is_never_reopened_even_after_a_revision(self, tmp_path):
        rd = make_run(tmp_path, ran=["thesis", "catalyst"], crosscheck=self.CC)
        tail(rd, "out_thesis.json", {"thesis": {"changed": {"AMAT": {"status": "strengthening"}}}})
        sc.route(rd)
        ids = {m["to"]: m["id"] for m in ledger(rd)["messages"]}
        tail(rd, "out_thesis.r1.json", {"comms": {"answers": [
            {"id": ids["thesis"], "position": "revised", "answer": "intact",
             "revision": {"thesis": {"changed": {"AMAT": {"status": "intact"}}}}}]}})
        tail(rd, "out_catalyst.r1.json", {"comms": {"answers": [
            {"id": ids["catalyst"], "position": "revised", "answer": "mapping was blanket"}]}})
        sc.route(rd)
        n_debate = sum(1 for m in ledger(rd)["messages"] if m["kind"] == "debate")
        sc.route(rd)                        # crosscheck still lists the finding
        assert sum(1 for m in ledger(rd)["messages"] if m["kind"] == "debate") == n_debate
        assert "thesis_vs_catalyst_threat|AMAT" in ledger(rd)["settled"]
        t = sc.digest(ledger(rd))["debates"][0]
        assert t["outcome"] == "revised"

    def test_settled_debates_become_findings_for_the_next_run(self, tmp_path):
        rd = make_run(tmp_path, ran=["thesis", "catalyst"], crosscheck=self.CC)
        tail(rd, "out_thesis.json", {"thesis": {"changed": {"AMAT": {"status": "strengthening"}}}})
        sc.route(rd)
        for m in ledger(rd)["messages"]:
            tail(rd, f"out_{m['to']}.r1.json", {"comms": {"answers": [
                {"id": m["id"], "position": "held", "answer": "reason"}]}})
        sc.route(rd)
        rows = sc.findings_rows(rd)
        assert rows and rows[0]["subject"] == "AMAT" and "held" in rows[0]["claim"]


class TestBounds:
    def test_identical_question_is_not_asked_twice(self, tmp_path):
        rd = make_run(tmp_path, ran=["thesis", "catalyst"])
        ask = {"to": "catalyst", "ticker": "MU", "question": "Same question?"}
        tail(rd, "out_thesis.json", {"comms": {"asks": [ask]}})
        sc.route(rd)
        tail(rd, "out_thesis.r1.json", {"comms": {"asks": [ask]}})
        sc.route(rd)
        assert len(ledger(rd)["messages"]) == 1

    def test_round_cap_expires_rather_than_loops_and_reports_it(self, tmp_path):
        rd = make_run(tmp_path, ran=["thesis", "catalyst"])
        tail(rd, "out_thesis.json", {"comms": {"asks": [
            {"to": "catalyst", "question": "late question", "blocking": True}]}})
        rec = sc.route(rd, max_rounds=0)
        assert rec["stop_reason"].startswith("round cap")
        m = ledger(rd)["messages"][0]
        assert m["status"] == "expired"
        assert sc.digest(ledger(rd))["unresolved"][0]["status"] == "expired"

    def test_normal_tell_to_a_finished_agent_does_not_wake_it(self, tmp_path):
        rd = make_run(tmp_path, ran=["thesis", "catalyst"])
        tail(rd, "out_catalyst.json", {"comms": {"tells": [
            {"to": "thesis", "ticker": "WDC", "fact": "Solidigm weighing US NAND fab",
             "source": "Reuters", "weight": "normal"}]}})
        rec = sc.route(rd)
        assert "thesis" not in rec["deliveries"]
        assert rec["converged"]
        assert ledger(rd)["messages"][0]["status"] == "recorded"

    def test_high_weight_tell_does_wake_it(self, tmp_path):
        rd = make_run(tmp_path, ran=["thesis", "catalyst"])
        tail(rd, "out_catalyst.json", {"comms": {"tells": [
            {"to": "thesis", "ticker": "MU", "fact": "HBM4 qualification lost", "weight": "high"}]}})
        assert sc.route(rd)["deliveries"]["thesis"]["mode"] == "resume"

    def test_rerouting_unchanged_inputs_is_a_no_op(self, tmp_path):
        rd = make_run(tmp_path, ran=["thesis", "catalyst"])
        tail(rd, "out_thesis.json", {"comms": {"asks": [{"to": "catalyst", "question": "q?"}]}})
        sc.route(rd)
        n = len(ledger(rd)["messages"])
        rec = sc.route(rd)
        assert len(ledger(rd)["messages"]) == n
        assert rec["deliveries"] == {}
        assert not rec["converged"]         # still owed an answer


class TestFoundOnTheFirstLiveRound:
    """Three defects the 2026-09-19 live round exposed -- each would have produced plausible
    output, not an error: a fragment appended beside the record it meant to change, a conflict
    re-reported forever as 'settled', and a change summary that told nobody what changed."""

    def _state_with_carried(self, rd, cats):
        base = Path(rd).parents[1]
        (base / "state.json").write_text(json.dumps({"factor_catalysts": {"catalysts": cats}}))

    def test_revision_of_a_carried_catalyst_amends_the_full_record(self, tmp_path):
        rd = make_run(tmp_path, ran=["catalyst", "thesis"])
        self._state_with_carried(rd, [{"headline": "CXMT reaches HBM3E risk production", "date": "2026-09-01",
                                        "horizon": "structural", "source": "techtimes",
                                        "affects": ["MU", "AMAT", "TER"]}])
        tail(rd, "out_catalyst.json", {"catalysts": [{"headline": "Solidigm", "affects": ["WDC"]}]})
        rec = sc.apply_revision(rd, "catalyst", {"catalysts": [
            {"headline": "CXMT reaches HBM3E risk production", "affects": ["MU", "TER"]}]}, "M1.1", 1)
        now = json.loads(Path(rd, "out_catalyst.json").read_text())["catalysts"]
        cx = [c for c in now if c["headline"].startswith("CXMT")]
        assert len(cx) == 1                                   # amended, not duplicated
        assert cx[0]["date"] == "2026-09-01" and cx[0]["source"] == "techtimes"
        assert cx[0]["affects"] == ["MU", "TER"]
        assert any("removed ['AMAT']" in line for line in rec["changed"])
        assert any(c["headline"] == "Solidigm" for c in now)  # untouched sibling survives

    def test_revision_naming_an_unknown_catalyst_is_dropped_not_appended(self, tmp_path):
        rd = make_run(tmp_path, ran=["catalyst"])
        self._state_with_carried(rd, [])
        tail(rd, "out_catalyst.json", {"catalysts": []})
        rec = sc.apply_revision(rd, "catalyst", {"catalysts": [{"headline": "nonexistent", "affects": []}]},
                                "M1.1", 1)
        assert rec["applied"] is False

    def test_a_restated_headline_still_finds_its_record(self, tmp_path):
        rd = make_run(tmp_path, ran=["catalyst"])
        long = "Anthropic CEO Dario Amodei publishes 'We Must Pace the Frontier' essay (2026-09-12) urging labs"
        self._state_with_carried(rd, [{"headline": long, "date": "2026-09-14", "affects": ["QCOM", "MU"]}])
        tail(rd, "out_catalyst.json", {"catalysts": []})
        sc.apply_revision(rd, "catalyst", {"catalysts": [{"headline": long[:85], "affects": ["MU"]}]}, "M", 1)
        now = json.loads(Path(rd, "out_catalyst.json").read_text())["catalysts"]
        assert now[0]["headline"] == long and now[0]["affects"] == ["MU"]

    def test_partial_thesis_revision_on_an_unreviewed_name_is_hydrated(self, tmp_path):
        rd = make_run(tmp_path, ran=["thesis"])
        base = Path(rd).parents[1]
        (base / "state.json").write_text(json.dumps({"thesis": {"KLAC": {
            "status": "strengthening", "thesis": "process control", "evidence_for": [{"claim": "x"}]}}}))
        tail(rd, "out_thesis.json", {"thesis": {"changed": {}}})
        sc.apply_revision(rd, "thesis", {"thesis": {"changed": {"KLAC": {"status": "intact"}}}}, "M", 1)
        e = json.loads(Path(rd, "out_thesis.json").read_text())["thesis"]["changed"]["KLAC"]
        assert e["status"] == "intact" and e["thesis"] == "process control" and e["evidence_for"]

    def test_conflict_surviving_a_revision_sends_the_reviser_back(self, tmp_path):
        cc = [{"kind": "thesis_vs_catalyst_threat", "ticker": "QCOM", "severity": "medium"}]
        rd = make_run(tmp_path, ran=["thesis", "catalyst"], crosscheck=cc)
        self._state_with_carried(rd, [
            {"headline": "Essay A", "date": "2026-09-14", "affects": ["QCOM"]},
            {"headline": "Essay B near-duplicate", "date": "2026-09-14", "affects": ["QCOM"]}])
        tail(rd, "out_thesis.json", {"thesis": {"changed": {"QCOM": {"status": "strengthening"}}}})
        tail(rd, "out_catalyst.json", {"catalysts": []})
        sc.route(rd)
        ids = {m["to"]: m["id"] for m in ledger(rd)["messages"]}
        tail(rd, "out_thesis.r1.json", {"comms": {"answers": [{"id": ids["thesis"], "position": "held",
                                                              "answer": "handset revenue"}]}})
        tail(rd, "out_catalyst.r1.json", {"comms": {"answers": [{"id": ids["catalyst"], "position": "revised",
            "answer": "blanket", "revision": {"catalysts": [{"headline": "Essay A", "affects": []}]}}]}})
        sc.route(rd)
        # crosscheck re-run AFTER the revision and the finding is still there
        import time
        time.sleep(1.1)
        Path(rd, "crosscheck.json").write_text(json.dumps({"findings": cc}))
        rec = sc.route(rd)
        assert "thesis_vs_catalyst_threat|QCOM|followup" in rec["debates_opened"]
        fu = next(m for m in ledger(rd)["messages"] if (m.get("debate_key") or "").endswith("followup"))
        assert fu["to"] == "catalyst" and "Essay B near-duplicate" in fu["question"]
        again = sc.route(rd)                      # asked once, never re-opened
        assert again["debates_opened"] == []

    def test_a_held_debate_never_generates_a_followup(self, tmp_path):
        cc = [{"kind": "thesis_vs_catalyst_threat", "ticker": "QCOM", "severity": "medium"}]
        rd = make_run(tmp_path, ran=["thesis", "catalyst"], crosscheck=cc)
        tail(rd, "out_thesis.json", {"thesis": {"changed": {"QCOM": {"status": "strengthening"}}}})
        sc.route(rd)
        for m in ledger(rd)["messages"]:
            tail(rd, f"out_{m['to']}.r1.json", {"comms": {"answers": [
                {"id": m["id"], "position": "held", "answer": "reason"}]}})
        sc.route(rd)
        Path(rd, "crosscheck.json").write_text(json.dumps({"findings": cc}))
        assert sc.route(rd)["debates_opened"] == []   # argued out; nobody claimed to fix it


class TestTolerantReader:
    """Agents drift from the schema. A substantive reply must not be recorded as silence --
    but a reply whose question cannot be identified must not be guessed onto one either."""

    def test_the_strategist_shape_seen_live_is_understood_and_the_repair_recorded(self, tmp_path):
        rd = make_run(tmp_path, ran=["strategist", "thesis"])
        tail(rd, "out_thesis.json", {"comms": {"tells": [
            {"to": "strategist", "ticker": "AMAT", "fact": "revised", "weight": "high"}]}})
        sc.route(rd)
        mid = ledger(rd)["messages"][0]["id"]
        tail(rd, "out_strategist.r1.json", {"comms": {"answers": [
            {"to": mid, "from_ticker": "AMAT", "status": "noted, no change", "detail": "consistent"}]}})
        rec = sc.route(rd)
        m = ledger(rd)["messages"][0]
        assert m["status"] == "answered" and m["answer"]["position"] == "noted"
        assert m["answer"]["answer"] == "consistent"
        assert rec["schema_repairs"] and "id<-to" in rec["schema_repairs"][0]["repairs"]

    def test_an_answer_with_no_recoverable_id_is_rejected(self, tmp_path):
        rd = make_run(tmp_path, ran=["strategist"])
        tail(rd, "out_strategist.r1.json", {"comms": {"answers": [{"status": "noted", "detail": "x"}]}})
        assert sc.route(rd)["rejected"]

    def test_answer_level_retirement_is_folded_into_the_revision_with_its_date(self, tmp_path):
        rd = make_run(tmp_path, ran=["catalyst", "thesis"])
        (Path(rd).parents[1] / "state.json").write_text(json.dumps({"factor_catalysts": {"catalysts": [
            {"headline": "Essay dup", "date": "2026-09-14", "affects": ["QCOM"]},
            {"headline": "Essay canonical", "date": "2026-09-14", "affects": ["MU"]}]}}))
        tail(rd, "out_catalyst.json", {"catalysts": []})
        tail(rd, "out_thesis.json", {"comms": {"asks": [{"to": "catalyst", "ticker": "QCOM", "question": "q"}]}})
        sc.route(rd)
        mid = ledger(rd)["messages"][0]["id"]
        tail(rd, "out_catalyst.r1.json", {"comms": {"answers": [{
            "id": mid, "position": "revised", "answer": "dup",
            "revision": {"catalysts": [{"headline": "Essay dup", "affects": []}]},
            "retired_catalysts_suggested": [{"headline": "Essay dup", "reason": "near-duplicate"}]}]}})
        sc.route(rd)
        now = json.loads(Path(rd, "out_catalyst.json").read_text())
        assert now["retired_catalysts"] == [{"headline": "Essay dup", "date": "2026-09-14",
                                             "reason": "near-duplicate"}]
        assert all(c["headline"] != "Essay dup" for c in now.get("catalysts") or [])  # retirement wins


class TestRound4Refinements:
    def test_an_answer_only_agent_is_resumed_not_redispatched(self, tmp_path):
        rd = make_run(tmp_path, ran=["thesis"])
        tail(rd, "out_cluster_memory.r1.json", {"comms": {}})   # answer-only: no base tail
        tail(rd, "out_thesis.json", {"comms": {"asks": [
            {"to": "cluster_memory", "ticker": "SKHY", "question": "rank axis?", "blocking": True}]}})
        assert sc.route(rd)["deliveries"]["cluster_memory"]["mode"] == "resume"

    def test_several_revisions_in_one_round_send_one_notice_per_consumer(self, tmp_path):
        rd = make_run(tmp_path, ran=["catalyst", "thesis"], scheduled=["strategist"])
        tail(rd, "out_catalyst.json", {"catalysts": [{"headline": "A", "affects": ["X", "Y"]},
                                                     {"headline": "B", "affects": ["X", "Z"]}]})
        tail(rd, "out_thesis.json", {"comms": {"asks": [
            {"to": "catalyst", "ticker": "X", "question": "A reach X?"},
            {"to": "catalyst", "ticker": "Z", "question": "B reach Z?"}]}})
        sc.route(rd)
        ids = [m["id"] for m in ledger(rd)["messages"]]
        tail(rd, "out_catalyst.r1.json", {"comms": {"answers": [
            {"id": ids[0], "position": "revised", "answer": "no",
             "revision": {"catalysts": [{"headline": "A", "affects": ["Y"]}]}},
            {"id": ids[1], "position": "revised", "answer": "no",
             "revision": {"catalysts": [{"headline": "B", "affects": ["X"]}]}}]}})
        sc.route(rd)
        notices = [m for m in ledger(rd)["messages"] if m["kind"] == "revision"]
        per = {}
        for n in notices:
            per[n["to"]] = per.get(n["to"], 0) + 1
        assert per and all(v == 1 for v in per.values())
        assert "2 change set(s)" in notices[0]["question"]

    def test_a_retired_entry_is_named_in_the_change_summary(self):
        lines = sc._summarize_change({"catalysts": [{"headline": "dup"}, {"headline": "keep"}]},
                                     {"catalysts": [{"headline": "keep"}]})
        assert any("[dup] removed" in x for x in lines)

    def test_the_recipient_sees_what_it_already_said_on_the_same_name(self, tmp_path):
        rd = make_run(tmp_path, ran=["thesis", "cluster_memory", "strategist"])
        tail(rd, "out_cluster_memory.json", {"comms": {"asks": [
            {"to": "thesis", "ticker": "SKHY", "question": "Is watch fundamental?"}]}})
        sc.route(rd)
        first = ledger(rd)["messages"][0]["id"]
        tail(rd, "out_thesis.r1.json", {"comms": {"answers": [
            {"id": first, "position": "held", "answer": "only CXMT timing + unreconciled fill"}]}})
        tail(rd, "out_strategist.json", {"comms": {"asks": [
            {"to": "thesis", "ticker": "SKHY", "question": "Would a reconciled fill change watch?"}]}})
        sc.route(rd)
        inbox = sc.slice_block(rd, "thesis")["desk_inbox"]
        q = next(m for m in inbox if m.get("from") == "strategist")
        assert q["your_prior_answers_on_this_name"][0]["your_answer"].startswith("only CXMT")


class TestTickerInference:
    def _run(self, tmp_path):
        rd = make_run(tmp_path, ran=["strategist", "thesis"])
        Path(rd, "holdings.json").write_text(json.dumps({"holdings_inr": [
            {"ticker": "SKHY"}, {"ticker": "MU"}, {"ticker": "AMAT"}]}))
        return rd

    def test_one_named_holding_is_inferred_and_recorded(self, tmp_path):
        rd = self._run(tmp_path)
        tail(rd, "out_strategist.json", {"comms": {"asks": [
            {"to": "thesis", "question": "SKHY: is WATCH still your call once the fill is confirmed?"}]}})
        rec = sc.route(rd)
        assert ledger(rd)["messages"][0]["ticker"] == "SKHY"
        assert any("inferred SKHY" in r["repairs"][0] for r in rec["schema_repairs"])

    def test_two_named_holdings_are_not_guessed(self, tmp_path):
        rd = self._run(tmp_path)
        tail(rd, "out_strategist.json", {"comms": {"asks": [
            {"to": "thesis", "question": "Does MU's HBM4 share cut into SKHY's?"}]}})
        sc.route(rd)
        assert ledger(rd)["messages"][0]["ticker"] is None


def test_a_changed_position_on_any_thread_survives_to_the_next_run(tmp_path):
    """The strategist's SKHY sizing rule came as a `revised` answer to a non-blocking reply with
    no output revision. It must still reach findings.json -- tomorrow is when it applies."""
    rd = make_run(tmp_path, ran=["strategist", "thesis"])
    tail(rd, "out_thesis.json", {"comms": {"tells": [
        {"to": "strategist", "ticker": "SKHY", "fact": "watch holds", "weight": "high"}]}})
    sc.route(rd)
    mid = ledger(rd)["messages"][0]["id"]
    tail(rd, "out_strategist.r1.json", {"comms": {"answers": [
        {"id": mid, "position": "revised", "answer": "no rotation into SKHY on rank alone"}]}})
    sc.route(rd)
    rows = sc.findings_rows(rd)
    assert any("no rotation into SKHY" in r["claim"] and r["subject"] == "SKHY" for r in rows)
