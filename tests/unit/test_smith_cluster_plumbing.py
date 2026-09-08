"""Pseudo-agent keys: dispatching ONE agent definition N times in a single run (2026-09-08).

Cluster specialists are dispatched once per cluster under `cluster_<slug>` keys. Every
file-scoped thing (slice, tail, output_file, cursor) uses the namespaced key so N same-run
dispatches cannot overwrite each other; every prompt-scoped thing resolves to the single shared
template and to smith-cluster.md. These tests pin both halves of that split, plus the two places
a near-miss would be silent: a tail that names no cluster, and a tail carrying no actual ranking.
"""
import json
import os

import pytest

import smith_memory as sm


class TestAgentKeyResolution:
    def test_cluster_keys_resolve_to_the_shared_template(self):
        spec, label = sm.resolve_agent("cluster_memory")
        assert spec is sm.AGENT_SLICES["cluster"]
        assert label == "smith-cluster"

    def test_every_cluster_key_gets_the_same_spec_object(self):
        assert sm.resolve_agent("cluster_semis")[0] is sm.resolve_agent("cluster_optics")[0]

    def test_a_normal_agent_is_unaffected(self):
        spec, label = sm.resolve_agent("thesis")
        assert spec is sm.AGENT_SLICES["thesis"] and label == "smith-thesis"

    def test_an_unknown_agent_still_resolves_to_nothing(self):
        assert sm.resolve_agent("nonsense")[0] is None

    def test_is_cluster_agent_does_not_match_the_bare_template_key(self):
        # "cluster" is a template, never a dispatchable agent -- there is no out_cluster.json.
        assert sm.is_cluster_agent("cluster") is False
        assert sm.is_cluster_agent("cluster_memory") is True
        assert sm.is_cluster_agent(None) is False


class TestSkipProtection:
    def test_a_cluster_dispatch_is_an_external_reader(self):
        """Its real input is qualification news and filings, which move when no file in the run
        dir does. If the namespaced key were tested directly it would miss EXTERNAL_READERS and
        the never-skip protection would silently not apply."""
        assert sm._skip_key("cluster_memory") == "cluster"
        assert sm._skip_key("cluster_memory") in sm.EXTERNAL_READERS
        assert sm._skip_key("thesis") == "thesis"

    def test_the_cluster_template_has_a_domain(self):
        assert sm.AGENT_DOMAIN["cluster"] in sm.DOMAIN_HELP


# ---------------------------------------------------------------------------
# _merge_cluster
# ---------------------------------------------------------------------------

def _tail(cluster="AI Networking/Optics", n=3, **kw):
    d = {"cluster": cluster, "confidence": "high",
         "cluster_thesis": {"status": "strengthening", "innings": "early"},
         "margin_pool": {"moving_toward": "lasers"},
         "ranking": [{"rank": i + 1, "ticker": f"T{i}"} for i in range(n)],
         "leader": "T0", "laggard": f"T{n - 1}",
         "bench": [{"ticker": "NEW"}], "reorder_when": ["x"]}
    d.update(kw)
    return d


class TestMergeCluster:
    def test_a_good_tail_lands_under_its_cluster(self):
        state = {}
        res = sm._merge_cluster(_tail(), state, "2026-09-08")
        assert res["merged"] is True
        entry = state["cluster_ladders"]["AI Networking/Optics"]
        assert entry["leader"] == "T0" and entry["confidence"] == "high"
        assert entry["as_of"] == "2026-09-08"
        assert state["cluster_ladders_as_of"] == "2026-09-08"

    def test_the_cursor_advances_only_for_the_merged_cluster(self):
        state = {"cluster_scan_cursor": {"Other": "2026-01-01"}}
        sm._merge_cluster(_tail(), state, "2026-09-08")
        assert state["cluster_scan_cursor"] == {"Other": "2026-01-01",
                                                "AI Networking/Optics": "2026-09-08"}

    def test_other_clusters_ladders_survive(self):
        """PER-CLUSTER, never wholesale. Up to LADDER_MAX_DISPATCH clusters refresh per run;
        replacing the whole map with one agent's answer would blank every cluster the
        round-robin did not reach."""
        state = {"cluster_ladders": {"AI Semis/Fabs": {"leader": "NVDA", "as_of": "2026-09-01"}}}
        sm._merge_cluster(_tail(), state, "2026-09-08")
        assert state["cluster_ladders"]["AI Semis/Fabs"]["leader"] == "NVDA"
        assert len(state["cluster_ladders"]) == 2

    def test_track_record_is_carried_forward_not_rewritten_by_the_agent(self):
        # The agent does not get to grade its own homework.
        state = {"cluster_ladders": {"AI Networking/Optics": {"track_record": [{"correct": False}]}}}
        sm._merge_cluster(_tail(track_record=[{"correct": True}]), state, "2026-09-08")
        assert state["cluster_ladders"]["AI Networking/Optics"]["track_record"] == [{"correct": False}]

    def test_a_tail_with_no_ranking_is_refused_and_leaves_the_prior_intact(self):
        """A `leader`/`laggard` pair with nothing behind it is worse than no ladder: the
        rotation trigger's freshness gate would treat it as a real answer."""
        prior = {"leader": "OLD", "laggard": "OLDER", "as_of": "2026-09-01"}
        state = {"cluster_ladders": {"AI Networking/Optics": dict(prior)}}
        res = sm._merge_cluster(_tail(n=0, leader="A", laggard="B"), state, "2026-09-08")
        assert res["merged"] is False and "not a ladder" in res["reason"]
        assert state["cluster_ladders"]["AI Networking/Optics"] == prior

    def test_a_single_name_ranking_is_not_a_ladder(self):
        state = {}
        assert sm._merge_cluster(_tail(n=1), state, "2026-09-08")["merged"] is False
        assert state == {}

    def test_a_missing_leader_is_refused(self):
        assert sm._merge_cluster(_tail(leader=None), {}, "2026-09-08")["merged"] is False

    def test_a_tail_with_no_cluster_falls_back_to_the_slices_name(self):
        """The slice is what TOLD the agent which cluster it was working on, so it is
        authoritative -- a dropped field must not silently misfile a ladder."""
        state = {}
        res = sm._merge_cluster(_tail(cluster=None), state, "2026-09-08",
                                cluster_name="AI Memory/Storage")
        assert res["merged"] is True and "AI Memory/Storage" in state["cluster_ladders"]

    def test_no_cluster_anywhere_is_refused_rather_than_guessed(self):
        res = sm._merge_cluster(_tail(cluster=None), {}, "2026-09-08")
        assert res["merged"] is False and "cannot place it" in res["reason"]

    def test_the_tails_own_cluster_wins_over_the_slice(self):
        state = {}
        sm._merge_cluster(_tail(cluster="AI Semis/Fabs"), state, "2026-09-08",
                          cluster_name="AI Memory/Storage")
        assert list(state["cluster_ladders"]) == ["AI Semis/Fabs"]


class TestMergeRulesWiring:
    def test_the_cluster_rule_is_registered_under_the_template_key(self):
        assert sm.MERGE_RULES["cluster"] is sm._merge_cluster

    def test_the_bare_template_is_excluded_from_an_agentless_merge(self, tmp_path):
        """`merge-tails` with no --agents must not look for out_cluster.json, which never
        exists -- it discovers the real cluster_* tails on disk instead."""
        rd = tmp_path / "rd"
        rd.mkdir()
        (rd / "out_cluster_optics.json").write_text("{}")
        (rd / "out_thesis.json").write_text("{}")
        discovered = ([a for a in sm.MERGE_RULES if a != "cluster"] +
                      sorted(f[4:-5] for f in os.listdir(rd)
                             if f.startswith("out_" + sm.CLUSTER_AGENT_PREFIX)
                             and f.endswith(".json")))
        assert "cluster" not in discovered
        assert "cluster_optics" in discovered


class TestSliceSubject:
    """The slice must tell the agent WHICH cluster it is. Without it the agent has a template,
    a many-cluster file, and no idea which row is its job."""

    def _render(self, tmp_path, slug, *, ladder_slug="optics"):
        base, rd = tmp_path / "b", tmp_path / "r"
        base.mkdir(); rd.mkdir()
        (base / "state.json").write_text(json.dumps(
            {"thesis": {"COHR": "1.6T lasers|strengthening"}, "data_cache": {}}))
        (base / "policy.json").write_text("{}")
        (base / "lots.json").write_text("{}")
        (rd / "holdings.json").write_text(json.dumps(
            {"holdings_inr": [{"ticker": "COHR", "name": "Coherent", "qty": 5,
                               "weight_pct": 4.0}], "usdinr": 88.0}))
        for f in ("compute_ladder", "compute_risk", "compute_drift", "compute_book"):
            (rd / f"{f}.json").write_text("{}")
        (rd / "compute_ladder.json").write_text(json.dumps({"clusters": {
            "AI Networking/Optics": {"slug": ladder_slug, "members": [{"ticker": "COHR"}],
                                     "prior_ladder": {"present": False}}}}))

        class A:
            base_dir, run_dir, mode, today, agents = str(base), str(rd), "deep", "2026-09-08", slug
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            sm.cmd_slices(A())
        return json.loads(buf.getvalue()), rd

    def test_the_slice_names_its_cluster_and_stays_on_a_namespaced_path(self, tmp_path):
        out, rd = self._render(tmp_path, "cluster_optics")
        assert out["problems"] == []
        sl = json.loads((rd / "slice_cluster_optics.json").read_text())
        assert sl["agent"] == "smith-cluster"          # the DEFINITION
        assert sl["agent_key"] == "cluster_optics"     # this DISPATCH
        assert sl["cluster_name"] == "AI Networking/Optics"
        assert sl["output_file"].endswith("smith-cluster_optics-output.md")

    def test_two_clusters_in_one_run_do_not_collide(self, tmp_path):
        base, rd = tmp_path / "b", tmp_path / "r"
        out, rd = self._render(tmp_path, "cluster_optics")
        assert (rd / "slice_cluster_optics.json").exists()
        assert not (rd / "slice_cluster.json").exists()

    def test_a_slug_with_no_matching_cluster_is_a_loud_problem(self, tmp_path):
        """Silently rendering a subject-less cluster slice would send the agent to rank a
        cluster it was never told the name of."""
        out, _ = self._render(tmp_path, "cluster_ghost")
        assert any("no cluster in compute_ladder.json has slug 'ghost'" in p
                   for p in out["problems"])


class TestPlaybooks:
    """policy.cluster_playbooks is the cluster-specific knowledge that keeps one agent file
    from becoming seven. A slug is an agent key and a filename, so it must be unique."""

    @pytest.fixture(scope="class")
    @classmethod
    def live(cls):
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return (json.load(open(os.path.join(root, "policy.json"))),
                json.load(open(os.path.join(root, "state.json"))))

    def test_every_held_cluster_has_a_playbook(self, live):
        policy, state = live
        held = set(state["sector_map"].values())
        assert held - set(policy["cluster_playbooks"]) == set()

    def test_slugs_are_unique(self, live):
        policy, _ = live
        slugs = [v["slug"] for v in policy["cluster_playbooks"].values()]
        assert len(slugs) == len(set(slugs))

    def test_every_playbook_names_real_ranking_axes(self, live):
        policy, _ = live
        for name, pb in policy["cluster_playbooks"].items():
            assert len(pb.get("differentiators") or []) >= 3, name


class TestTrackRecordPersistence:
    """cmd_ladder has computed a score since phase 1 -- did the previous leader actually beat
    the previous laggard -- but emitting is not persisting. Without this the record would be
    recomputed and discarded every run, and the confidence auto-downgrade that gates trigger
    authority would never have a sample to act on. That is the G50 shape, in new code."""

    SCORE = {"scored": True, "correct": True, "leader": "A", "laggard": "B", "spread_pp": 5.0}

    def test_the_score_is_appended_when_the_ladder_is_replaced(self):
        state = {}
        sm._merge_cluster(_tail(), state, "2026-09-08",
                          ladder_track_record={"AI Networking/Optics": self.SCORE})
        assert state["cluster_ladders"]["AI Networking/Optics"]["track_record"] == [self.SCORE]

    def test_it_appends_rather_than_replaces(self):
        prior = {"scored": True, "correct": False}
        state = {"cluster_ladders": {"AI Networking/Optics": {"track_record": [prior]}}}
        sm._merge_cluster(_tail(), state, "2026-09-08",
                          ladder_track_record={"AI Networking/Optics": self.SCORE})
        assert state["cluster_ladders"]["AI Networking/Optics"]["track_record"] == [prior, self.SCORE]

    def test_the_window_is_rolling(self):
        """A ranking that was right about a different cluster composition two years ago is not
        evidence about this one."""
        old = [{"scored": True, "correct": False}] * (sm.LADDER_TRACK_RECORD_CAP + 5)
        state = {"cluster_ladders": {"AI Networking/Optics": {"track_record": old}}}
        sm._merge_cluster(_tail(), state, "2026-09-08",
                          ladder_track_record={"AI Networking/Optics": self.SCORE})
        tr = state["cluster_ladders"]["AI Networking/Optics"]["track_record"]
        assert len(tr) == sm.LADDER_TRACK_RECORD_CAP and tr[-1] == self.SCORE

    def test_a_score_for_another_cluster_is_not_misfiled(self):
        state = {}
        sm._merge_cluster(_tail(), state, "2026-09-08",
                          ladder_track_record={"AI Semis/Fabs": self.SCORE})
        assert state["cluster_ladders"]["AI Networking/Optics"]["track_record"] == []

    def test_an_unscoreable_call_is_handed_back_as_nothing_to_log(self):
        """An unscoreable call is not a wrong call and must not reach the learning store."""
        res = sm._merge_cluster(_tail(), {}, "2026-09-08", ladder_track_record={
            "AI Networking/Optics": {"scored": False, "reason": "no return cached"}})
        assert res["scored_call"] is None

    def test_a_scored_call_is_handed_back_for_the_learning_store(self):
        res = sm._merge_cluster(_tail(), {}, "2026-09-08",
                                ladder_track_record={"AI Networking/Optics": self.SCORE})
        assert res["scored_call"] == self.SCORE

    def test_a_refused_merge_records_nothing_anywhere(self):
        state = {}
        res = sm._merge_cluster(_tail(n=0, leader="A", laggard="B"), state, "2026-09-08",
                                ladder_track_record={"AI Networking/Optics": self.SCORE})
        assert res["merged"] is False and "scored_call" not in res and state == {}
