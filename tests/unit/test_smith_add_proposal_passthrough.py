"""2026-09-20 (rebuild Phase 1): add-proposal used to build the row from a fixed dict and drop
every other spec field. stop_price_usd survived on 9 of 323 rows, evidence_quality and
trigger_bucket were last persisted 2026-08-25 -- so the G58 evidence gate, the signal_conviction
retirement and the reentry 20-day expiry were unreachable. These pin the typed allowlist, the
reserved-field denylist and the spec_extras safety net."""
import contextlib
import io
import json
import os
from argparse import Namespace

import pytest

import smith_lifecycle as sl

PASSTHROUGH_SAMPLE = {
    "stop_price_usd": 408.95, "stop_distance_pct": 8.5, "target_price_usd": 520.0,
    "size_wanted_usd": 600.0, "clamped_by": "deployable cash", "risk_usd": 12.5,
    "r_multiple": 2.0, "ev_r": 0.4, "p_win": 0.55, "horizon_days": 30,
    "expires_on": "2026-10-20", "invalidation": "closes below 400 on volume",
    "evidence_quality": {"verified": 1, "computed": 2, "unverified": 0},
    "trigger_bucket": "idea", "exited_on": "2026-08-01", "conviction_score": 26.0,
    "gate": "passed",
    # Phase 5 additions: the exit-side risk figure, and what `deferred`/`watch` used to mean
    "risk_removed_usd": 33.9, "defer_until": "2026-10-10",
}


def _spec(**extra):
    return {"direction": "BUY", "ticker": "AMAT", "size_usd": 504.51,
            "price_at_proposal": 443.7, "rationale": "r", "trigger_type": "reentry", **extra}


def _run(tmp_path, specs, buf=None):
    base = str(tmp_path)
    with open(os.path.join(base, "proposals.json"), "w") as fh:
        json.dump({"proposals": []}, fh)
    sp = os.path.join(base, "specs.json")
    with open(sp, "w") as fh:
        json.dump(specs, fh)
    buf = buf or io.StringIO()
    with contextlib.redirect_stdout(buf):
        sl.cmd_add_proposal(Namespace(base_dir=base, proposals_json=sp, today=None, run_dir=None))
    rows = json.load(open(os.path.join(base, "proposals.json")))["proposals"]
    return json.loads(buf.getvalue()), rows


def _fails(tmp_path, specs):
    """Run expecting fail() (prints {"error":...} and exits 1); return (message, rows after)."""
    buf = io.StringIO()
    with pytest.raises(SystemExit) as ei:
        _run(tmp_path, specs, buf)
    assert ei.value.code == 1
    rows = json.load(open(os.path.join(str(tmp_path), "proposals.json")))["proposals"]
    return json.loads(buf.getvalue())["error"], rows


def test_twelve_plus_passthrough_fields_round_trip_onto_the_row(tmp_path):
    assert len(PASSTHROUGH_SAMPLE) >= 12
    out, rows = _run(tmp_path, [_spec(**PASSTHROUGH_SAMPLE)])
    assert out["added"] == 1
    for k, v in PASSTHROUGH_SAMPLE.items():
        if k == "risk_removed_usd":
            # a BUY removes no risk: the ticket (single writer of the flat risk fields) does not carry
            # it, so a stale spec value must not survive on the row. The SELL side is covered in
            # test_smith_ticket_schema.
            assert k not in rows[0]
            continue
        assert rows[0][k] == v, k
    assert "spec_extras" not in rows[0]


def test_sample_covers_the_whole_allowlist():
    assert set(PASSTHROUGH_SAMPLE) == set(sl.PASSTHROUGH)


def test_null_passthrough_values_are_omitted_not_rejected(tmp_path):
    """Every drafted SELL leg carries stop_price_usd: null -- that means 'not supplied'."""
    _, rows = _run(tmp_path, [_spec(stop_price_usd=None, evidence_quality=None)])
    assert "stop_price_usd" not in rows[0] and "evidence_quality" not in rows[0]


@pytest.mark.parametrize("field", ["status", "id", "outcome_verdict", "history", "retired_reason"])
def test_reserved_field_rejects_the_whole_batch(tmp_path, field):
    msg, rows = _fails(tmp_path, [_spec(), _spec(ticker="KLAC", **{field: "x"})])
    assert field in msg and "lifecycle" in msg
    assert rows == []  # the good spec in the same batch was not written either


def test_mistyped_passthrough_value_rejects_and_writes_nothing(tmp_path):
    msg, rows = _fails(tmp_path, [_spec(stop_price_usd="408.95")])
    assert "stop_price_usd" in msg and rows == []


@pytest.mark.parametrize("field,bad", [
    ("stop_price_usd", -1), ("stop_price_usd", True), ("p_win", 1.5), ("horizon_days", 2.5),
    ("expires_on", "next week"), ("exited_on", "2026-13-40"),
    ("evidence_quality", "verified"), ("evidence_quality", {"verified": -1}),
    ("evidence_quality", {"trusted": 3}), ("stop_distance_pct", 100),
])
def test_validators_reject_bad_values(tmp_path, field, bad):
    msg, rows = _fails(tmp_path, [_spec(**{field: bad})])
    assert field in msg and rows == []


def test_unknown_field_is_kept_under_spec_extras_with_a_data_quality_line(tmp_path):
    out, rows = _run(tmp_path, [_spec(catalyst_note="CXMT sampling", draft_reasons=["a"])])
    # draft_reasons/blockers are draft-specs' advisory prose, reproducible from the trigger row: consumed
    # (not stored) since Phase 5 rather than left as noise under spec_extras on every drafted row
    assert rows[0]["spec_extras"] == {"catalyst_note": "CXMT sampling"}
    assert any("catalyst_note" in d and "spec_extras" in d for d in out["data_quality"])


def test_lifecycle_fields_are_still_assigned_by_the_lifecycle(tmp_path):
    _, rows = _run(tmp_path, [_spec(**PASSTHROUGH_SAMPLE)])
    assert rows[0]["status"] == "open" and "id" not in rows[0] and "outcome_verdict" not in rows[0]


def test_persisted_evidence_quality_is_visible_to_the_g58_gate(tmp_path):
    """The gate at _apply_live_rejustification reads pr['evidence_quality']; before this change
    add-proposal never wrote it, so the gate could not fire on any row created after 2026-08-25."""
    _, rows = _run(tmp_path, [_spec(evidence_quality={"verified": 0, "computed": 0, "unverified": 2})])
    pr = rows[0]
    assert pr["evidence_quality"] == {"verified": 0, "computed": 0, "unverified": 2}
    sl._apply_live_rejustification(pr, {}, {}, lambda c, b: None, sl.date(2026, 9, 20))
    assert any("G58" in f for f in pr["review_flags"])


def test_reentry_exited_on_reaches_the_expiry_branch_input(tmp_path):
    _, rows = _run(tmp_path, [_spec(exited_on="2026-08-01")])
    assert sl._proposal_parse_date(rows[0]["exited_on"]) is not None
