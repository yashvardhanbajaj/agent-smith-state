"""Health must not flag days whose run dir postflight's keep-10 prune removed (2026-09-14)."""
import os

import smith_memory as sm


def _ledger(base, stamps):
    with open(os.path.join(base, "ledger.csv"), "w") as fh:
        fh.write("ts,mode,value_usd\n")
        for ts in stamps:
            fh.write(f"{ts},quick,1\n")


def test_ledger_row_older_than_oldest_kept_run_dir_is_pruned_not_a_defect(tmp_path):
    base = str(tmp_path)
    os.makedirs(os.path.join(base, "runs", "2026-09-10-0331"))
    _ledger(base, ["2026-09-08T09:00:00Z", "2026-09-10T03:31:00Z", "2026-09-11T09:00:00Z"])
    rows = {r["date"]: r["verdict"] for r in sm.evaluate_runs(base, today="2026-09-14", days=7)}
    assert rows["2026-09-08"] == "ok_pruned"
    assert rows["2026-09-11"] == "LEDGER_ROW_WITHOUT_RUN_DIR"   # newer than the oldest kept dir: still a defect
    assert rows["2026-09-10"] == "ok"
