"""Benchmark-plausibility gate on the relative-performance chart and the ledger write path.

Regression pin for the 2026-09-08 user report: the dashboard's "Beat or lag SMH, per period"
chart rendered periods claiming SMH moved +754.66%, -123.90% and +579.06% in a session, and
those periods were being COUNTED in the "N of M periods beat SMH" footer. Root cause was in
ledger.csv, not the chart -- on 2026-08-12/08-13 the real SMH close was written one column to
the RIGHT (into est_net_flows_usd) and a net-flow figure landed in `smh`; on 08-25/08-26 a
flow figure was passed as --smh outright. An ETF cannot move that far, so the reading is a
value from another series and, per the desk's standing doctrine, never counts as performance.
"""
import csv
import json
import os
import subprocess
import sys

import pytest

from smith_core import BENCHMARK_WEEKLY_PLAUSIBLE_PCT

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

HEADER = ["ts", "mode", "value_usd", "usdinr", "wallet_usd", "spx", "ndx", "smh",
          "smh_asof", "est_net_flows_usd", "external_flow_usd", "value_trust", "notes"]


def _row(ts, value, smh, trust="ok", flows=""):
    return [ts, "quick", value, 95.0, 1000.0, 7700, 26400, smh, ts[:10], flows, "", trust, "n"]


def _write_ledger(base, rows):
    with open(os.path.join(base, "ledger.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        for r in rows:
            w.writerow(r)


# The three chart_relative tests retired with scripts/smith_charts.py (archived 2026-09-14).
# Dashboard v2 plots no per-period SMH figure, so the guarantee that matters is the write
# path below: an implausible benchmark level never reaches ledger.csv.


def _append(base, **kw):
    args = [sys.executable, os.path.join(REPO, "scripts", "smith_math.py"), "append-ledger",
            "--base-dir", base, "--ts", "2026-08-14T09:00:00+05:30", "--mode", "quick",
            "--value-usd", "40000", "--usdinr", "95", "--wallet-usd", "1000",
            "--spx", "7700", "--ndx", "26400", "--value-trust", "ok", "--summary", "t"]
    for k, v in kw.items():
        args += ["--" + k.replace("_", "-"), str(v)]
    p = subprocess.run(args, capture_output=True, text=True)
    return p.returncode, json.loads(p.stdout or "{}")


def _seeded(tmp_path):
    base = str(tmp_path)
    _write_ledger(base, [
        _row("2026-08-10T09:00:00+05:30", 40000.0, 582.70),
        _row("2026-08-11T09:00:00+05:30", 40400.0, 572.93),
        _row("2026-08-13T09:00:00+05:30", 40550.0, 584.83),
    ])
    return base


def test_append_ledger_refuses_out_of_band_smh(tmp_path):
    base = _seeded(tmp_path)
    rc, out = _append(base, smh=4896.61)
    assert rc != 0
    assert "plausibility band" in out["error"]
    # Nothing was written -- the write is refused, not repaired after the fact.
    assert len(list(csv.DictReader(open(os.path.join(base, "ledger.csv"))))) == 3


def test_append_ledger_names_the_column_swap(tmp_path):
    base = _seeded(tmp_path)
    rc, out = _append(base, smh=4896.61, est_net_flows_usd=586.22)
    assert rc != 0
    assert "look swapped" in out["error"]


def test_append_ledger_accepts_a_real_level(tmp_path):
    base = _seeded(tmp_path)
    rc, out = _append(base, smh=587.82)
    assert rc == 0 and out["appended"] is True


def test_append_ledger_allows_an_empty_benchmark_cell(tmp_path):
    base = _seeded(tmp_path)
    rc, out = _append(base)
    assert rc == 0 and out["appended"] is True
