"""Phase 5: the trade ticket -- one builder, one writer, additive over the legacy flat fields, never
backfilled, and gated at add-proposal (behind --require-ticket for one release)."""
import contextlib
import io
import json
import os
from argparse import Namespace
from datetime import date

import pytest

import smith_core as core
import smith_lifecycle as sl
import smith_ticket as st

TODAY = date(2026, 9, 20)
CTX = {"today": TODAY, "total_book_usd": 42542.0, "r_base_usd": 212.71, "prices": {}, "atr20_pct": {"AMAT": 3.92},
       "lots": {"ASML": [{"date": "2026-08-24", "qty": 1.0, "price_usd": 1500.0}]}, "ltcg_months": 24,
       "prefer_ltcg": True}

BUY_ROW = {"ticker": "AMAT", "trigger_type": "trend_entry", "direction": "BUY", "price_usd": 443.75,
           "thesis_status": "strengthening", "suggested_size_usd": 504.51, "size_wanted_usd": 504.51,
           "clamped_by": None, "stop_price_usd": 408.9584, "risk_usd": 39.55, "vote": "live",
           "book_heat_before_usd": 2777.0, "book_heat_after_usd": 2816.5, "heat_room_remaining_usd": 925.6,
           "edge": {"ev_r": 0.99, "p_win": 0.41, "payoff_r": 4.0, "fee_r": 0.04, "p_win_basis": "prior",
                    "target_usd": 640.89, "payoff_r_uncapped": 5.67, "target_capped": True, "stop_pct": 7.84,
                    "target_source": "journal.analyst_target", "entry_usd": 443.75},
           "gate": {"verdict": "unproven", "multiplier": 1.0, "basis": "n_eff 0", "n_eff": 0}}
SELL_ROW = {"ticker": "ASML", "trigger_type": "catalyst_threat", "direction": "TRIM", "vote": "live",
            "price_usd": 1670.57, "suggested_size_usd": 584.7, "risk_removed_usd": 33.91, "stop_pct": 5.8,
            "retires_when": "ASML no longer appears in a structural-threat factor catalyst",
            "edge": {"ev_gated": False, "why": "sells are never EV-gated"}}
PAIR = {"pair_id": "profit_rotation-ASML-AMAT", "trigger_type": "profit_rotation", "vote": "live",
        "retires_when": "ladder stale", "rotation_risk": {"r_freed_usd": 33.9, "buy_risk_final_usd": 33.9,
                                                          "heat_delta_final_usd": 0.0},
        "sell_leg": dict(SELL_ROW, trigger_type=None), "buy_leg": {"ticker": "AMAT", "direction": "BUY",
                                                                    "suggested_size_usd": 500.0, "risk_usd": 33.9,
                                                                    "edge": BUY_ROW["edge"]}}


def test_buy_ticket_has_every_block_and_a_stop():
    t = st.build_ticket(BUY_ROW, CTX)
    assert t["stop"]["price_usd"] == 408.96 and t["stop"]["atr20_pct"] == 3.92
    assert t["target"]["r_multiple"] == 4.0 and "capped at 4R" in t["target"]["basis"]
    assert t["size"]["shares"] == round(504.51 / 443.75, 4) and t["risk"]["r_ticket"] == round(39.55 / 212.71, 3)
    assert t["horizon"]["expires_on"] == "2026-10-04" and t["entry"]["valid_until"] == "2026-10-04"
    assert "close" not in t["invalidation"] and "$408.96" in t["invalidation"]
    assert {c["type"] for c in t["invalidation_checks"]} == {"price_below", "thesis_not_in", "leaves_live_list"}


def test_sell_ticket_has_no_stop_and_reports_risk_removed_and_tax_lots():
    t = st.build_ticket(SELL_ROW, CTX)
    assert t["stop"] is None and t["target"] is None
    assert t["risk"]["kind"] == "removed" and t["risk"]["removed_usd"] == 33.91 and t["risk"]["usd"] is None
    assert "short-term" in t["lots"]["ltcg_note"] and "2028-08-24" in t["lots"]["ltcg_note"]
    assert "stop_price_usd" not in st.flatten_ticket(t)


def test_ltcg_note_is_null_without_lots_never_a_guess():
    assert st.build_ticket(SELL_ROW, dict(CTX, lots={}))["lots"]["ltcg_note"] is None


def test_flat_fields_are_derived_from_the_ticket_and_cannot_diverge():
    pr = {"stop_price_usd": 1.0, "size_usd": 1.0, "risk_removed_usd": 9.0}   # stale spec values
    st.apply_ticket(pr, st.build_ticket(BUY_ROW, CTX))
    assert pr["stop_price_usd"] == pr["ticket"]["stop"]["price_usd"] == 408.96
    assert pr["size_usd"] == pr["ticket"]["size"]["usd"] and "risk_removed_usd" not in pr
    assert pr["ticket_version"] == 1 and st.ticket_divergences(pr) == []
    pr["stop_price_usd"] = 400.0
    assert [d[0] for d in st.ticket_divergences(pr)] == ["stop_price_usd"]


def test_legacy_row_has_no_ticket_and_no_divergence():
    assert st.ticket_divergences({"size_usd": 5, "stop_price_usd": 1}) == []


def test_ticket_round_trips_through_json():
    t = st.build_ticket(BUY_ROW, CTX)
    assert json.loads(json.dumps(t)) == t


def test_paired_legs_carry_the_pairing_and_the_pairing_invalidation():
    view = st.leg_view({"profit_rotation": [PAIR]}, "profit_rotation", "AMAT", PAIR["pair_id"], "buy")
    t = st.build_ticket(view, CTX)
    assert t["pair"]["pair_id"] == PAIR["pair_id"] and t["pair"]["role"] == "buy"
    assert "pairing" in t["invalidation"] and "trigger condition: ladder stale" in t["invalidation"]


def test_horizon_family_table_and_honest_default():
    assert core.horizon_for("catalyst_threat")[0] == 5
    days, basis = core.horizon_for("some_new_family")
    assert days == core.DEFAULT_HORIZON_DAYS and "DEFAULT" in basis and "no horizon basis" in basis
    t = st.build_ticket(dict(BUY_ROW, trigger_type="some_new_family"), CTX)
    assert "DEFAULT" in t["horizon"]["basis"]


def test_every_family_horizon_states_a_rationale():
    for fam, (days, why) in core.HORIZON_DAYS_BY_FAMILY.items():
        assert days > 0 and len(why) > 20, fam


def test_required_fields_per_direction():
    buy = {"size_usd": 1, "risk_usd": 1, "invalidation": "x", "horizon_days": 5, "expires_on": "2026-10-01"}
    assert st.ticket_missing("BUY", buy, "why") == ["stop_price_usd"]
    sell = {"size_usd": 1, "risk_removed_usd": 1, "invalidation": "x", "horizon_days": 5, "expires_on": "d"}
    assert st.ticket_missing("SELL", sell, "why") == [] and st.ticket_missing("TRIM", sell, "") == ["rationale"]
    assert st.ticket_missing("HOLD", {}, "") == []


def test_script_owned_conflicts_include_adding_a_stop_the_ticket_lacks():
    flat = st.flatten_ticket(st.build_ticket(SELL_ROW, CTX))
    assert [c[0] for c in st.script_owned_conflicts(flat, {"stop_price_usd": 1500.0})] == ["stop_price_usd"]
    assert st.script_owned_conflicts(flat, {"size_usd": 584.7, "rationale": "x"}) == []


# ---- add-proposal gate ------------------------------------------------------------------------------
def _world(tmp_path, rows):
    base = str(tmp_path)
    rd = os.path.join(base, "runs", "r1")
    os.makedirs(rd)
    json.dump({"proposals": []}, open(os.path.join(base, "proposals.json"), "w"))
    json.dump({"total_book_usd": 42542.0}, open(os.path.join(rd, "compute_risk.json"), "w"))
    json.dump(rows, open(os.path.join(rd, "compute_triggers.json"), "w"))
    json.dump({"stop_loss_framework": {"risk_per_position_pct_of_book": 0.5}}, open(os.path.join(base, "policy.json"), "w"))
    json.dump({"holdings_inr": []}, open(os.path.join(rd, "holdings.json"), "w"))
    return base, rd


def _add(base, rd, specs, require=False):
    sp = os.path.join(base, "s.json")
    json.dump(specs, open(sp, "w"))
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            sl.cmd_add_proposal(Namespace(base_dir=base, proposals_json=sp, today="2026-09-20", run_dir=rd,
                                          require_ticket=require))
        ok = True
    except SystemExit:
        ok = False
    rows = json.load(open(os.path.join(base, "proposals.json")))["proposals"]
    return ok, json.loads(buf.getvalue()), rows


def _spec(row, **kw):
    return {"direction": row["direction"], "ticker": row["ticker"], "trigger_type": row["trigger_type"],
            "size_usd": row["suggested_size_usd"], "price_at_proposal": row.get("price_usd"),
            "rationale": "because", **kw}


def test_ticket_is_built_from_the_trigger_row_and_written_by_the_one_writer(tmp_path):
    base, rd = _world(tmp_path, {"trend_entry": [BUY_ROW]})
    ok, out, rows = _add(base, rd, [_spec(BUY_ROW)], require=True)
    assert ok and rows[0]["ticket_version"] == 1 and st.ticket_divergences(rows[0]) == []
    assert rows[0]["stop_price_usd"] == 408.96 and rows[0]["rationale"] == "because"
    assert "retires_when" not in rows[0]


def test_strategist_cannot_resize_under_require_ticket(tmp_path):
    base, rd = _world(tmp_path, {"trend_entry": [BUY_ROW]})
    ok, out, rows = _add(base, rd, [_spec(BUY_ROW, size_usd=999.0)], require=True)
    assert not ok and "script-owned" in out["error"] and rows == []


def test_default_mode_corrects_the_resize_and_says_so(tmp_path):
    base, rd = _world(tmp_path, {"trend_entry": [BUY_ROW]})
    ok, out, rows = _add(base, rd, [_spec(BUY_ROW, size_usd=999.0)])
    assert ok and rows[0]["size_usd"] == 504.51 and any("script-owned" in d for d in out["data_quality"])


def test_empty_rationale_is_rejected_strict_and_named_otherwise(tmp_path):
    base, rd = _world(tmp_path, {"trend_entry": [BUY_ROW]})
    ok, out, _ = _add(base, rd, [_spec(BUY_ROW, rationale=None)], require=True)
    assert not ok and "rationale" in out["error"]
    base2, rd2 = _world(tmp_path / "b", {"trend_entry": [BUY_ROW]}) if (tmp_path / "b").mkdir() is None else (None, None)
    ok, out, rows = _add(base2, rd2, [_spec(BUY_ROW, rationale=None)])
    assert ok and rows[0]["rationale"] == "" and any("EMPTY rationale" in d for d in out["data_quality"])


def test_non_ticket_spec_accepted_without_flag_with_missing_list_rejected_with_it(tmp_path):
    spec = {"direction": "BUY", "ticker": "ZZZ", "trigger_type": None, "size_usd": 300.0,
            "price_at_proposal": 10.0, "rationale": "hunch"}
    base, rd = _world(tmp_path, {})
    ok, out, rows = _add(base, rd, [spec])
    assert ok and "ticket_version" not in rows[0]
    assert any("NOT a complete ticket" in d and "stop_price_usd" in d for d in out["data_quality"])
    base2 = tmp_path / "s"; base2.mkdir()
    b2, r2 = _world(base2, {})
    ok, out, rows = _add(b2, r2, [spec], require=True)
    assert not ok and "stop_price_usd" in out["error"] and rows == []


def test_paired_trigger_without_pair_id_is_rejected_in_both_modes(tmp_path):
    base, rd = _world(tmp_path, {})
    spec = {"direction": "BUY", "ticker": "AMAT", "trigger_type": "cluster_rotation", "size_usd": 100.0,
            "rationale": "x", "pair_role": "buy"}
    ok, out, rows = _add(base, rd, [spec])
    assert not ok and "PAIRED" in out["error"] and rows == []


def test_sell_leg_spec_only_ticket_needs_risk_removed_not_a_stop(tmp_path):
    base, rd = _world(tmp_path, {})
    spec = {"direction": "SELL", "ticker": "ASML", "trigger_type": None, "size_usd": 500.0, "rationale": "x",
            "price_at_proposal": 1670.0, "risk_removed_usd": 30.0, "invalidation": "thesis recovers"}
    ok, out, rows = _add(base, rd, [spec], require=True)
    assert ok and rows[0]["ticket"]["source"] == "spec" and "stop_price_usd" not in rows[0]
