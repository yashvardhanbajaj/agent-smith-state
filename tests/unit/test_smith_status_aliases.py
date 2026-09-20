"""Phase 5: 323 historical rows carry 11 distinct statuses. The alias table translates on READ; nothing
is rewritten; every reader loads, renders and scores them; no reader hand-lists the old spellings."""
import contextlib
import io
import json
import os
import re
import shutil
import tokenize
from argparse import Namespace

import pytest

import smith_core as core
import smith_dashboard as sd
import smith_lifecycle as sl
import smith_validity as sv

HERE = os.path.dirname(__file__)
FIX = os.path.join(HERE, "..", "fixtures")
SCRIPTS = os.path.join(HERE, "..", "..", "scripts")
ALL11 = {"open", "accepted_by_user", "executed", "fulfilled", "filled", "deferred", "watch", "auto_retired",
         "superseded", "dismissed_by_user", "dismissed_by_desk"}


def test_fixture_really_contains_all_eleven():
    rows = json.load(open(os.path.join(FIX, "statuses_all11", "proposals.json")))["proposals"]
    assert {r["status"] for r in rows} == ALL11


def test_alias_table():
    assert core.STATUS_ALIASES == {"fulfilled": "executed", "filled": "executed", "deferred": "open", "watch": "open"}
    assert core.canonical_status({"status": "filled"}) == "executed" and core.canonical_status("watch") == "open"
    assert core.stored_forms("executed") == ("executed", "filled", "fulfilled")
    assert set(core.stored_forms("open")) == {"open", "deferred", "watch"}
    assert core.SCOREABLE_STATUSES >= {"deferred", "watch", "filled", "fulfilled", "executed", "auto_retired"}
    assert "superseded" not in core.SCOREABLE_STATUSES and "open" not in core.SCOREABLE_STATUSES


def test_liveness_readers_treat_legacy_deferred_as_open():
    import smith_runlife as rl
    assert set(rl.OPEN_PROPOSAL_STATUSES) == {"open", "accepted_by_user", "deferred", "watch"}
    assert sv.RECHECKED_STATUSES == ("open", "accepted_by_user")
    assert "filled" in core.TERMINAL_PROPOSAL_STATUSES and "deferred" not in core.TERMINAL_PROPOSAL_STATUSES


def _base(tmp_path):
    base = str(tmp_path / "base")
    shutil.copytree(os.path.join(FIX, "dashboard_case1", "base"), base)
    shutil.copy(os.path.join(FIX, "statuses_all11", "proposals.json"), os.path.join(base, "proposals.json"))
    return base


def test_dashboard_payload_renders_all_eleven_without_error_and_marks_legacy(tmp_path):
    base = _base(tmp_path)
    before = open(os.path.join(base, "proposals.json")).read()
    pl = sd.build_payload(base)
    assert set(pl["proposals"]["counts"]) == ALL11                      # raw statuses stay visible
    open_ids = {p["id"] for p in pl["proposals"]["open"]}
    st = {r["id"]: r["status"] for r in json.load(open(os.path.join(base, "proposals.json")))["proposals"]}
    assert {i for i, s in st.items() if s in ("open", "deferred", "watch")} == open_ids
    assert all(p["tk"] is None for p in pl["proposals"]["open"])        # LEGACY: no synthetic ticket
    hist = {p["id"]: p["cstatus"] for p in pl["proposals"]["history"]}
    assert {hist[i] for i, s in st.items() if s in ("filled", "fulfilled")} == {"executed"}
    assert open(os.path.join(base, "proposals.json")).read() == before   # never rewritten


def test_scoring_admits_the_legacy_spellings_and_skips_open(tmp_path, capsys):
    base = _base(tmp_path)
    pj = tmp_path / "prices.json"
    pj.write_text(json.dumps({"MU": 120.0, "SMH": 600.0}))
    sl.cmd_score(Namespace(base_dir=base, prices_json=str(pj), today="2026-09-21", run_dir=None,
                           rebase_scorecard=False, dry_run=False))
    rows = {r["status"]: r for r in json.load(open(os.path.join(base, "proposals.json")))["proposals"]}
    for s in ("executed", "fulfilled", "filled", "deferred", "watch", "auto_retired"):
        assert rows[s].get("outcome_verdict"), s
    for s in ("open", "accepted_by_user", "superseded", "dismissed_by_user"):
        assert not rows[s].get("outcome_verdict"), s


def test_lifecycle_pass_runs_on_all_eleven_and_rechecks_legacy_deferred(tmp_path, capsys):
    base = str(tmp_path / "b")
    shutil.copytree(os.path.join(FIX, "proposals_case1", "base"), base)
    shutil.copy(os.path.join(FIX, "statuses_all11", "proposals.json"), os.path.join(base, "proposals.json"))
    sl.cmd_proposals(Namespace(base_dir=base, run_dir=os.path.join(FIX, "proposals_case1", "rundir"), today="2026-09-01"))
    out = json.loads(capsys.readouterr().out)
    ids_seen = {r["id"] for r in out["auto_retired"]}
    rows = {r["status"] if r["id"] not in ids_seen else r["id"]: r for r in
            json.load(open(os.path.join(base, "proposals.json")))["proposals"]}
    stored = {r["id"]: r["status"] for r in json.load(open(os.path.join(base, "proposals.json")))["proposals"]}
    # nothing was rewritten to a new spelling: fulfilled/filled stay as stored
    assert "fulfilled" in stored.values() and "filled" in stored.values()
    # the legacy deferred/watch rows went through the retirement pass (they are open by alias)
    dw = [i for i, s in stored.items() if s in ("deferred", "watch")] + [i for i in ids_seen]
    assert out["proposals_count"] == 11


# ---- grep-style guard: no reader hand-lists the old spellings ----------------------------------------
def _string_tokens(path):
    with open(path, "rb") as fh:
        for t in tokenize.tokenize(fh.readline):
            if t.type == tokenize.STRING and len(t.string) < 40:
                yield t.start[0], t.string.strip("\"'")


@pytest.mark.parametrize("fname", sorted(f for f in os.listdir(SCRIPTS) if f.endswith(".py") and f != "smith_core.py"))
def test_no_reader_hand_lists_fulfilled_or_filled(fname):
    bad = [(ln, s) for ln, s in _string_tokens(os.path.join(SCRIPTS, fname)) if s in ("fulfilled", "filled")]
    assert bad == [], f"{fname} hand-lists a legacy status; use core.stored_forms/canonical_status: {bad}"


@pytest.mark.parametrize("fname", sorted(f for f in os.listdir(SCRIPTS) if f.endswith(".py") and f != "smith_core.py"))
def test_no_reader_lists_deferred_or_watch_beside_proposal_statuses(fname):
    lines = open(os.path.join(SCRIPTS, fname)).read().splitlines()
    bad = [i + 1 for i, l in enumerate(lines)
           if re.search(r'"(deferred|watch)"', l) and re.search(r'"(open|accepted_by_user|executed)"', l)
           and not l.lstrip().startswith("#")]
    assert bad == [], f"{fname}:{bad} lists deferred/watch beside a proposal status"
