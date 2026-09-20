"""Phase 5: `executed` has exactly one writer -- a matching fill in trades.json. Never from acceptance."""
import copy
import json
import os
from argparse import Namespace
from datetime import date

import smith_ledger as sl

TODAY = date(2026, 9, 21)


def prop(pid="P-1", ticker="AMAT", bucket="BUY", size=500.0, day="2026-09-15", status="open", **kw):
    return {"id": pid, "ticker": ticker, "direction_bucket": bucket, "size_usd": size, "date": day,
            "action": f"{bucket} {ticker}", "status": status, **kw}


def fill(ticker="AMAT", qty=1.0, px=450.0, day="2026-09-16", ref="m1", **kw):
    return {"ticker": ticker, "qty_change": qty, "price_at_trade": px, "amount_usd": abs(qty) * px,
            "date": day, "message_id": ref, **kw}


def test_matching_fill_sets_executed_with_date_and_price():
    ps = [prop()]
    done = sl.reconcile_proposals(ps, [fill()], TODAY)
    assert ps[0]["status"] == "executed" and ps[0]["filled_date"] == "2026-09-16"
    assert ps[0]["filled_price"] == 450.0 and ps[0]["executed_source"] == "reconcile-proposals"
    assert done[0]["condition"] == "fill_matched"


def test_acceptance_alone_never_marks_executed():
    ps = [prop(status="accepted_by_user", accepted_on="2026-09-15")]
    assert sl.reconcile_proposals(ps, [], TODAY) == [] and ps[0]["status"] == "accepted_by_user"


def test_an_accepted_row_with_a_matching_fill_is_executed_and_flagged():
    ps = [prop(status="accepted_by_user")]
    assert sl.reconcile_proposals(ps, [fill()], TODAY)[0]["was_accepted"] is True


def test_idempotent_and_a_fill_is_consumed_once():
    ps = [prop("P-1"), prop("P-2", day="2026-09-16")]
    sl.reconcile_proposals(ps, [fill()], TODAY)
    snap = copy.deepcopy(ps)
    assert sl.reconcile_proposals(ps, [fill()], TODAY) == [] and ps == snap
    assert sorted(p["status"] for p in ps) == ["executed", "open"]


def test_wrong_side_or_ticker_does_not_match():
    assert sl.reconcile_proposals([prop()], [fill(qty=-1.0)], TODAY) == []
    assert sl.reconcile_proposals([prop()], [fill(ticker="KLAC")], TODAY) == []
    assert sl.reconcile_proposals([prop(bucket="TRIM")], [fill(qty=-1.0)], TODAY)


def test_size_tolerance_is_fifty_percent():
    assert sl.reconcile_proposals([prop(size=500)], [fill(px=740.0)], TODAY)        # 1.48x
    assert not sl.reconcile_proposals([prop(size=500)], [fill(px=760.0)], TODAY)    # 1.52x
    assert not sl.reconcile_proposals([prop(size=500)], [fill(px=240.0)], TODAY)    # 0.48x


def test_window_closes_ten_days_after_and_never_opens_before_the_proposal():
    """The plan said +/-10. A fill made BEFORE the proposal existed is not its execution: the first
    scratch run matched three brand-new tickets to fills 2, 4 and 9 days earlier."""
    assert sl.reconcile_proposals([prop(day="2026-09-15")], [fill(day="2026-09-25")], TODAY)
    assert not sl.reconcile_proposals([prop(day="2026-09-15")], [fill(day="2026-09-26")], TODAY)
    assert not sl.reconcile_proposals([prop(day="2026-09-15")], [fill(day="2026-09-14")], TODAY)
    assert sl.reconcile_proposals([prop(day="2026-09-15")], [fill(day="2026-09-15")], TODAY)


def test_a_restated_row_may_match_a_fill_after_its_first_statement():
    p = prop(day="2026-09-15", history=[{"date": "2026-09-08"}])
    assert sl.reconcile_proposals([p], [fill(day="2026-09-10")], TODAY)


def test_split_fills_on_one_day_are_summed():
    fs = [fill(qty=0.5, px=450.0, ref="a"), fill(qty=0.5, px=450.0, ref="b")]
    ps = [prop(size=450.0)]
    sl.reconcile_proposals(ps, fs, TODAY)
    assert ps[0]["status"] == "executed" and ps[0]["fill_refs"] == ["a", "b"]


def test_unsized_rows_and_corporate_actions_are_skipped():
    assert not sl.reconcile_proposals([prop(size=0)], [fill()], TODAY)
    assert not sl.reconcile_proposals([prop()], [fill(ca_type="split")], TODAY)
    assert not sl.reconcile_proposals([prop(bucket="HOLD")], [fill()], TODAY)


def test_terminal_rows_are_never_reopened_or_marked():
    for st in ("auto_retired", "dismissed_by_user", "superseded", "executed"):
        ps = [prop(status=st)]
        assert sl.reconcile_proposals(ps, [fill()], TODAY) == [] and ps[0]["status"] == st


def test_command_writes_only_when_something_matched(tmp_path, capsys):
    base = str(tmp_path)
    json.dump({"proposals": [prop()]}, open(os.path.join(base, "proposals.json"), "w"))
    json.dump({"trades": [fill()]}, open(os.path.join(base, "trades.json"), "w"))
    sl.cmd_reconcile_proposals(Namespace(base_dir=base, today="2026-09-21"))
    assert json.loads(capsys.readouterr().out)["count"] == 1
    assert json.load(open(os.path.join(base, "proposals.json")))["proposals"][0]["status"] == "executed"
    sl.cmd_reconcile_proposals(Namespace(base_dir=base, today="2026-09-21"))
    assert json.loads(capsys.readouterr().out)["count"] == 0
