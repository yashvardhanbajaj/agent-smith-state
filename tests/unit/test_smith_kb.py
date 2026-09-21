import json, os, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
import smith_kb as K
import smith_kb_harvest as H


def mk(base, ents, kind, text, **kw):
    return K.make_obs(ents, kind, text, **kw)


def test_add_reinforce_dedupe_and_never_delete(tmp_path):
    b = str(tmp_path)
    o = mk(b, [K.T("MU")], "fact", "HBM4 booked through 2027", as_of="2026-09-01", confidence="primary", run="r1")
    assert K.add_observations(b, [o])["added"] == 1
    assert K.add_observations(b, [o])["added"] == 0                       # same run: exact repeat is a no-op
    o2 = mk(b, [K.T("MU")], "fact", "HBM4 booked through 2027", as_of="2026-09-08", confidence="primary", run="r2")
    rep = K.add_observations(b, [o2])
    kb = K.replay(K.read_events(b))
    assert len(kb) == 1 and kb[o["id"]]["confirmations"] == 2 and kb[o["id"]]["last_confirmed"] == "2026-09-08"
    assert rep["reinforced"] == 1


def test_verdict_timeline_supersedes_and_revives(tmp_path):
    b = str(tmp_path)
    A = mk(b, [K.T("APH")], "verdict", "STRENGTHENING x", topic="thesis", value="strengthening", as_of="2026-09-01", run="r1")
    B = mk(b, [K.T("APH")], "verdict", "INTACT y", topic="thesis", value="intact", as_of="2026-09-02", run="r1")
    A2 = mk(b, [K.T("APH")], "verdict", "STRENGTHENING x", topic="thesis", value="strengthening", as_of="2026-09-03", run="r1")
    K.add_observations(b, [A]); K.add_observations(b, [B])
    kb = K.replay(K.read_events(b))
    assert kb[A["id"]]["status"] == "superseded" and kb[B["id"]]["status"] == "live"
    K.add_observations(b, [A2])                                            # the desk went back: A -> B -> A
    kb = K.replay(K.read_events(b))
    assert kb[A["id"]]["status"] == "live" and kb[B["id"]]["status"] == "superseded"
    tl = K.entity_page(kb, K.T("APH"), "2026-09-04")["timelines"]["thesis"]
    assert [x["value"] for x in tl] == ["strengthening", "intact"] and tl[0]["status"] == "live"


def test_supersession_is_per_entity_set_not_per_cluster(tmp_path):
    b = str(tmp_path)
    r1 = mk(b, [K.T("LITE"), K.C("Optics")], "verdict", "rank 1", topic="ladder_rank", value=1, as_of="2026-09-01", run="r")
    r2 = mk(b, [K.T("COHR"), K.C("Optics")], "verdict", "rank 2", topic="ladder_rank", value=2, as_of="2026-09-01", run="r")
    K.add_observations(b, [r1, r2])
    kb = K.replay(K.read_events(b))
    assert kb[r1["id"]]["status"] == "live" and kb[r2["id"]]["status"] == "live"


def test_refute_keeps_the_memory_and_excludes_it_from_retrieval(tmp_path):
    b = str(tmp_path)
    o = mk(b, [K.T("TER")], "fact", "TER is a dust position", as_of="2026-08-19", run="r")
    ok = mk(b, [K.T("TER")], "fact", "TER 5.0 shares 1853 dollars", as_of="2026-09-21", run="r")
    K.add_observations(b, [o, ok])
    assert K.refute(b, [o["id"]], "holdings.json shows $1,853", by="thesis") == 1
    kb = K.replay(K.read_events(b))
    assert kb[o["id"]]["status"] == "refuted" and o["id"] in kb                 # never deleted
    r = K.retrieve(kb, [K.T("TER")], 1000, "2026-09-22")
    assert all("dust position" not in l for l in r["items"])
    assert any("REFUTED" in c for c in r["changed_recently"])
    assert K.search(kb, "dust position", "2026-09-22")[0]["status"] == "refuted"   # still findable


def test_retrieval_respects_budget_and_prefers_analysis_over_bookkeeping(tmp_path):
    b = str(tmp_path)
    obs = [mk(b, [K.T("MU")], "verdict", "WATCH: CXMT share risk " + "x" * 300, topic="thesis", value="watch", as_of="2026-09-20", run="r"),
           mk(b, [K.T("MU")], "fact", "[signals] PEER LEADER", topic="signal", as_of="2026-09-20", confidence="computed", run="r")]
    obs += [mk(b, [K.T("MU")], "fact", f"filler fact number {i} " + "y" * 200, as_of="2026-01-01", run="r") for i in range(40)]
    K.add_observations(b, obs)
    kb = K.replay(K.read_events(b))
    r = K.retrieve(kb, [K.T("MU")], 400, "2026-09-21")
    assert r["used_tokens"] <= 400 and r["n_items"] < len(obs)
    assert r["items"][0].startswith("[") and "verdict/thesis" in r["items"][0]      # the verdict outranks the signal-bucket line


def test_decay_lowers_rank_but_nothing_disappears():
    o = {"kind": "fact", "confidence": "primary", "confirmations": 1, "last_confirmed": "2026-01-01", "as_of": "2026-01-01"}
    assert K.salience(o, "2026-09-01") < K.salience(dict(o, last_confirmed="2026-08-25"), "2026-09-01")
    assert K.salience(o, "2027-09-01") > 0


def test_graph_relation_weights_strengthen_with_confirmation(tmp_path):
    b = str(tmp_path)
    rel = mk(b, [K.T("LITE"), K.T("COHR")], "relation", "redundant pair", topic="pair", as_of="2026-09-01", run="r1")
    K.add_observations(b, [rel])
    w1 = K.graph(K.replay(K.read_events(b)), "2026-09-02")["T:COHR|T:LITE"]
    K.add_observations(b, [dict(rel, as_of="2026-09-05", run="r2")])
    w2 = K.graph(K.replay(K.read_events(b)), "2026-09-06")["T:COHR|T:LITE"]
    assert w2 > w1


def test_harvest_thesis_cluster_revision_and_learned():
    thesis_tail = {"thesis": {"changed": {"APH": {"status": "strengthening", "thesis": "IT datacom growing", "verified": "primary",
                                                  "evidence_for": [{"claim": "Communications Solutions +42% organic", "source": "10-Q"}],
                                                  "evidence_against": []}}},
                   "learned": [{"entities": ["APH", "C:Optics"], "kind": "lesson", "text": "10-Q beats a news note", "confidence": "primary"}]}
    obs = H.harvest_tail("thesis", thesis_tail, "2026-09-21", "r")
    kinds = sorted(o["kind"] for o in obs if o.get("op") == "add")
    assert "verdict" in kinds and "lesson" in kinds and kinds.count("fact") == 1
    cluster_reply = {"cluster": "Optics", "comms": {"answers": [{"revision": {"ranking": [{"rank": 4, "ticker": "APH", "verdict": "middle", "case_against": "x"}],
                                                                              "leader": "LITE", "laggard": "GLW"}}]}}
    o2 = H.harvest_tail("cluster_optics", cluster_reply, "2026-09-21", "r")
    assert any(o.get("topic") == "ladder_rank" and o.get("value") == 4 for o in o2)          # a desk-round revision is harvested


def test_bad_dates_from_agents_do_not_break_replay():
    assert K.clean_date("2026-07-late") == "2026-07-01" and K.clean_date("garbage", "2026-01-01") == "2026-01-01"
    o = K.make_obs([K.T("X")], "fact", "some fact", as_of="2026-07-late")
    assert o["as_of"] == "2026-07-01"


def test_run_batches_orders_revision_rounds_not_mtimes(tmp_path):
    rd = tmp_path / "run"; rd.mkdir()
    (rd / "out_thesis.json").write_text(json.dumps({"thesis": {"changed": {}}}))
    (rd / "out_thesis.r4.json").write_text(json.dumps({"thesis": {"changed": {}}}))
    (rd / "out_thesis.r2.json").write_text(json.dumps({"thesis": {"changed": {}}}))
    os.utime(rd / "out_thesis.r2.json", (9e9, 9e9))                                        # newest mtime, lowest round after base
    names = [n for _, _, n in H.run_batches(str(tmp_path), str(rd), "run", "2026-09-21")]
    assert names == ["thesis", "thesis.r2", "thesis.r4"]


def test_batch_done_markers_make_a_rerun_a_noop(tmp_path):
    b = str(tmp_path)
    assert K.done_keys(K.read_events(b)) == set()
    K.mark_done(b, "run:2026-09-21-0632Z")
    assert "run:2026-09-21-0632Z" in K.done_keys(K.read_events(b))
    o = mk(b, [K.T("MU")], "fact", "some fact", as_of="2026-09-01", run="r")
    K.add_observations(b, [o])
    assert len(K.replay(K.read_events(b))) == 1                       # batch_done events never appear as observations


def test_late_arriving_history_is_recorded_as_already_superseded(tmp_path):
    b = str(tmp_path)
    new = mk(b, [K.T("AVGO")], "verdict", "WATCH: exited", topic="thesis", value="watch", as_of="2026-09-16", run="a")
    old = mk(b, [K.T("AVGO")], "verdict", "STRENGTHENING: before", topic="thesis", value="strengthening", as_of="2026-08-17", run="b")
    K.add_observations(b, [new]); K.add_observations(b, [old])          # history inserted AFTER the newer reading
    kb = K.replay(K.read_events(b))
    assert kb[new["id"]]["status"] == "live" and kb[old["id"]]["status"] == "superseded"


def test_a_complete_ladder_closes_names_it_no_longer_ranks(tmp_path):
    b = str(tmp_path)
    C = K.C("Optics")
    keep = [mk(b, [K.T(t), C], "verdict", f"rank {i}", topic="ladder_rank", value=i, as_of="2026-09-21", run="r")
            for i, t in enumerate(("LITE", "COHR"), 1)]
    stale = mk(b, [K.T("AVGO"), C], "verdict", "rank 5", topic="ladder_rank", value=5, as_of="2026-09-14", run="old")
    K.add_observations(b, [stale] + keep + [K.close_slot_event("ladder_rank", C, {K.T("LITE"), K.T("COHR")}, "2026-09-21")])
    kb = K.replay(K.read_events(b))
    assert kb[stale["id"]]["status"] == "superseded" and kb[keep[0]["id"]]["status"] == "live"


def test_partial_ladder_revision_is_not_stored_as_the_ladder_order():
    rev = {"cluster": "Optics", "ranking": [{"rank": 4, "ticker": "APH", "verdict": "middle", "case_against": "x"},
                                            {"rank": 5, "ticker": "MRVL", "verdict": "middle", "case_against": "y"}],
           "leader": "LITE", "laggard": "GLW"}
    obs = H.from_cluster_tail(rev, "2026-09-21", "r")
    assert not any(o.get("topic") == "ladder_order" for o in obs) and not any(o.get("op") == "close_slot" for o in obs)
    rev["order"] = "LITE > COHR > ALAB > APH > MRVL > CIEN > GLW"
    assert any(o.get("topic") == "ladder_order" for o in H.from_cluster_tail(rev, "2026-09-21", "r"))


def test_new_thesis_review_supersedes_the_evidence_it_no_longer_cites(tmp_path):
    b = str(tmp_path)
    v1 = {"status": "intact", "thesis": "first read of the name", "verified": "unverified",
          "evidence_for": [{"claim": "no primary revenue mix found yet, so uncertain"}], "evidence_against": []}
    v2 = {"status": "strengthening", "thesis": "second read of the name", "verified": "primary",
          "evidence_for": [{"claim": "Communications Solutions grew 42% organically per the 10-Q"}], "evidence_against": []}
    K.add_observations(b, H.thesis_obs("APH", v1, "2026-09-06", run="r1"))
    K.add_observations(b, H.thesis_obs("APH", v2, "2026-09-21", run="r2"))
    live = [o["text"] for o in K.replay(K.read_events(b)).values() if o["status"] == "live" and o.get("topic") == "thesis_evidence"]
    assert len(live) == 1 and "42%" in live[0]


def test_proposals_are_events_not_standing_verdicts():
    obs = H.from_strategist_tail({"proposals": [{"ticker": "MU", "direction": "TRIM", "size_usd": 407, "trigger_type": "x", "rationale": "because"}]},
                                 "2026-09-21", "r")
    assert obs and obs[0]["kind"] == "event" and obs[0]["topic"] == "proposal"


def test_briefs_plan_apply_supersede_and_outrank(tmp_path):
    b = str(tmp_path)
    obs = [mk(b, [K.T("MU")], "fact", f"fact {i} about MU with detail", as_of="2026-09-10", run="r") for i in range(5)]
    K.add_observations(b, obs)
    kb = K.replay(K.read_events(b))
    plan = K.briefs_plan(kb, "2026-09-21", min_new=3, held=[K.T("MU")])
    assert [p["entity"] for p in plan] == ["T:MU"] and plan[0]["previous_brief"] is None and plan[0]["n_new"] == 5
    rep = K.briefs_apply(b, {"briefs": [{"entity": "T:MU", "brief": "MU is on watch because of CXMT share risk; nothing else changed. " * 2,
                                         "key_points": ["CXMT G5"], "open_questions": ["10-01 print"], "contradictions": ["x vs y"],
                                         "obs_ids": [o["id"] for o in obs[:2]]}]}, "run1", "2026-09-21")
    assert rep["briefs"] == 1 and rep["tensions"] == 1
    kb = K.replay(K.read_events(b))
    assert K.entity_page(kb, "T:MU", "2026-09-22")["brief"]["as_of"] == "2026-09-21"
    assert K.retrieve(kb, ["T:MU"], 2000, "2026-09-22")["items"][0].split("]")[1].strip().startswith("brief")
    assert K.briefs_plan(kb, "2026-09-22", min_new=3, held=[]) == []                 # nothing new since the brief
    K.briefs_apply(b, {"briefs": [{"entity": "T:MU", "brief": "A newer and different brief about MU that supersedes the old one entirely.", "obs_ids": []}]}, "run2", "2026-09-25")
    live = [o for o in K.replay(K.read_events(b)).values() if o["kind"] == "brief" and o["status"] == "live"]
    assert len(live) == 1 and "newer" in live[0]["text"]


def test_outcomes_count_only_post_epoch_decisive_calls_and_reliability_gates(tmp_path):
    props = [{"id": "P-1", "action": "Buy X", "ticker": "X", "created_utc": "2026-08-01T00:00:00Z", "outcome_verdict": "worked"},   # legacy
             {"id": "P-2", "action": "Buy Y", "ticker": "Y", "created_utc": "2026-09-22T00:00:00Z", "outcome_verdict": "missed"},
             {"id": "P-3", "action": "Buy Z", "ticker": "Z", "created_utc": "2026-09-22T00:00:00Z", "outcome_verdict": "neutral"},
             {"id": "P-4", "action": "Buy W", "ticker": "W", "created_utc": "2026-09-22T00:00:00Z"}]
    obs = K.outcome_observations(props, "2026-09-21", "2026-10-30", run="o")
    assert [o["meta"]["proposal"] for o in obs] == ["P-2"]
    b = str(tmp_path)
    K.add_observations(b, obs)
    assert K.reliability(K.replay(K.read_events(b)))["strategist"]["status"] == "unproven"        # n < 12: changes nothing
    many = [{"id": f"P-{i}", "action": "Buy", "ticker": f"T{i}", "created_utc": "2026-09-22", "outcome_verdict": "missed"} for i in range(20, 32)]
    K.add_observations(b, K.outcome_observations(many, "2026-09-21", "2026-11-01"), reinforce=False)
    assert K.reliability(K.replay(K.read_events(b)))["strategist"]["status"] == "weak"


def test_dashboard_payload_shape_and_one_live_verdict_per_slot(tmp_path):
    b = str(tmp_path)
    K.add_observations(b, [mk(b, [K.T("MU")], "verdict", "WATCH: x", topic="thesis", value="watch", as_of="2026-09-01", run="r"),
                           mk(b, [K.T("MU")], "verdict", "INTACT: y", topic="thesis", value="intact", as_of="2026-09-05", run="r"),
                           mk(b, [K.T("MU")], "fact", "some standing fact", as_of="2026-09-05", run="r")])
    kb = K.replay(K.read_events(b))
    p = K.dashboard_payload(kb, ["T:MU", "T:NOPE"], "2026-09-06")
    assert p["stats"]["observations"] == 3 and [e["entity"] for e in p["entities"]] == ["T:MU"]
    assert [x["value"] for x in p["entities"][0]["timelines"]["thesis"]] == ["watch", "intact"]
    live = [o for o in kb.values() if o["kind"] == "verdict" and o["status"] == "live"]
    assert len(live) == 1


def test_a_close_slot_that_closes_nothing_is_not_recorded(tmp_path):
    b = str(tmp_path)
    o = mk(b, [K.T("APH")], "fact", "evidence claim number one", topic="thesis_evidence", as_of="2026-09-21", run="r")
    close = K.close_slot_event("thesis_evidence", K.T("APH"), (), "2026-09-21", keep_ids=[o["id"]])
    K.add_observations(b, [o, close])
    n1 = len(K.read_events(b))
    K.add_observations(b, [o, close], reinforce=False)                     # postflight re-run: nothing new, nothing closed
    assert len(K.read_events(b)) == n1
