"""cmd_pipeline: real reasons, no hollow files, degraded stages that don't stop the run."""
import contextlib
import io
import json
import subprocess
from argparse import Namespace

import smith_math as smm

OK = {"indicators": {"skipped": True, "tickers": None}, "freshness": {"artefacts": [1]}, "lots": {"total_lots": 3}, "book": {"value_usd": 1},
      "universe": {"total": 1}, "risk": {"positions": [1]}, "drift": {"cluster_table": [1]},
      "journal": {"journal_updates": []}, "attribution": {"value_delta_usd": 0},
      "rotation": {"tickers": [1]}, "buckets": {"tickers": []}, "sentiment": {"score": 50},
      "derisk": {"queue": [1]}, "triggers": {"correction_state": "none"},
      "ladder": {"clusters": {}},
      # both added 2026-09-19; DEGRADABLE, so a missing perf_bars.json must not fail a sweep
      "correlation": {"diversification": {"effective_bets": 2.05}}, "perf": {"twr": {"twr_pct": 1.0}}}


def _run(tmp_path, monkeypatch, overrides=None, market_inputs=True, pre=(), **kw):
    base = tmp_path / "base"
    rd = base / "runs" / "r"
    rd.mkdir(parents=True)
    (rd / "holdings.json").write_text("{}")
    if market_inputs:
        (rd / "market_inputs.json").write_text("{}")
    for f in pre:
        (rd / f).write_text("{}")
    calls = []

    def fake_run(cmd, capture_output=True, text=True):
        stage = cmd[2]
        calls.append(stage)
        rc, out = (overrides or {}).get(stage, (0, OK[stage]))
        return subprocess.CompletedProcess(cmd, rc, json.dumps(out), "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    args = Namespace(run_dir=str(rd), base_dir=str(base), today="2026-09-14", lots=None,
                     stages=kw.get("stages"), from_stage=kw.get("from_stage"))
    buf, code = io.StringIO(), 0
    with contextlib.redirect_stdout(buf):
        try:
            smm.cmd_pipeline(args)
        except SystemExit as e:
            code = e.code
    return json.loads(buf.getvalue().strip().splitlines()[-1]), rd, calls, code


def test_clean_run(tmp_path, monkeypatch):
    out, rd, calls, code = _run(tmp_path, monkeypatch)
    assert code == 0 and out["ok"] and out["degraded"] == []
    # `perf` is last since 2026-09-19; `ladder` stays last of the trigger-dependent stages
    assert calls[0] == "indicators" and calls[-1] == "perf"
    # correlation runs BEFORE triggers since Phase 3 (the heat budget reads it)
    assert calls.index("correlation") < calls.index("triggers") < calls.index("ladder")
    assert json.loads((rd / "compute_triggers.json").read_text()) == {"correction_state": "none"}


def test_failure_reports_the_error_from_stdout(tmp_path, monkeypatch):
    out, rd, calls, code = _run(tmp_path, monkeypatch, {"risk": (1, {"error": "KeyError: 'beta'"})})
    assert code == 1 and out["failed_at"] == "risk" and out["reason"] == "KeyError: 'beta'"
    assert not (rd / "compute_risk.json").exists()


def test_hollow_output_is_never_promoted(tmp_path, monkeypatch):
    out, rd, calls, code = _run(tmp_path, monkeypatch, {"rotation": (0, {"tickers": []})})
    assert code == 1 and out["failed_at"] == "rotation"
    assert not (rd / "compute_rotation.json").exists()
    assert (rd / "compute_rotation.rejected.json").exists()


def test_hollow_output_also_removes_a_stale_file_from_an_earlier_attempt(tmp_path, monkeypatch):
    out, rd, calls, code = _run(tmp_path, monkeypatch, {"rotation": (0, {"tickers": []})},
                                pre=("compute_rotation.json",))
    assert not (rd / "compute_rotation.json").exists()


def test_unreconciled_lots_degrades_and_continues(tmp_path, monkeypatch):
    out, rd, calls, code = _run(tmp_path, monkeypatch,
                                {"lots": (0, {"total_lots": 3, "write_blocked": "2 mismatch(es)"})})
    assert code == 0 and out["ok"] and out["degraded"] == ["lots"]
    assert "ladder" in calls


def test_missing_market_inputs_degrades_sentiment_but_triggers_still_run(tmp_path, monkeypatch):
    out, rd, calls, code = _run(tmp_path, monkeypatch, market_inputs=False)
    assert code == 0 and out["degraded"] == ["sentiment"]
    assert "sentiment" not in calls and "triggers" in calls
    assert json.loads((rd / "compute_sentiment.json").read_text())["degraded"] is True


def test_sentiment_crash_degrades(tmp_path, monkeypatch):
    out, rd, calls, code = _run(tmp_path, monkeypatch, {"sentiment": (1, {"error": "KeyError: 'vix'"})})
    assert code == 0 and out["degraded"] == ["sentiment"] and "derisk" in calls


def test_from_resumes_mid_pipeline(tmp_path, monkeypatch):
    out, rd, calls, code = _run(tmp_path, monkeypatch, from_stage="risk", pre=("compute_book.json",))
    assert code == 0 and calls[0] == "risk"
    assert not {"indicators", "freshness", "lots", "book", "universe"} & set(calls)


def test_inputs_must_be_in_the_run_dir(tmp_path, monkeypatch):
    (tmp_path / "base").mkdir()
    (tmp_path / "base" / "holdings.json").write_text("{}")      # a same-named file in base
    out, rd, calls, code = _run(tmp_path, monkeypatch, stages="book")
    assert code == 0                                              # run-dir copy exists -> fine
    (rd / "holdings.json").unlink()
    out, rd2, calls, code = _run(tmp_path / "second", monkeypatch, stages="risk")
    assert code == 1 and out["stages"][0]["status"] == "BLOCKED"
