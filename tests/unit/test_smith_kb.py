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
    kinds = sorted(o["kind"] for o in obs)
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
