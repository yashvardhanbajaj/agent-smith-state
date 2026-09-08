"""smith_core.load_json's default contract, and the degrade-gracefully guards that depend on it.

Until 2026-09-08 load_json tested `if default is not None` on a missing file -- which reads as
"was a default given", but None itself fails that test and fell through to `raise
FileNotFoundError`. So `load_json(path, default=None)` raised, and every call site that paired
it with an `if x is None:` guard had an unreachable guard: nine of them across scripts/,
each written to emit a self-describing empty result and each actually crashing with a traceback.

cmd_rotation was the live example. It is masked in normal use because cmd_pipeline asserts each
stage's required inputs first, but SKILL.md documents per-stage invocation by hand, and
`rotation` run before `risk` crashed instead of saying "run `risk` first".

The fix is a _NO_DEFAULT sentinel, so "no default given" is distinguishable from "the default
IS None". These tests pin both halves: omitting `default` still raises, and `default=None`
genuinely returns None.
"""
import json
import os

import pytest

import smith_core
import smith_math


class TestLoadJsonDefaultContract:
    def test_missing_file_with_no_default_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            smith_core.load_json(str(tmp_path / "nope.json"))

    def test_missing_file_with_default_none_returns_none(self, tmp_path):
        # The regression under test: this used to raise, making `is None` guards unreachable.
        assert smith_core.load_json(str(tmp_path / "nope.json"), default=None) is None

    def test_missing_file_with_falsy_non_none_default_returns_that_default(self, tmp_path):
        assert smith_core.load_json(str(tmp_path / "nope.json"), default={}) == {}
        assert smith_core.load_json(str(tmp_path / "nope.json"), default=[]) == []
        assert smith_core.load_json(str(tmp_path / "nope.json"), default=0) == 0

    def test_present_file_ignores_the_default(self, tmp_path):
        p = tmp_path / "there.json"
        p.write_text(json.dumps({"a": 1}))
        assert smith_core.load_json(str(p), default=None) == {"a": 1}


class _RotationArgs:
    def __init__(self, base_dir, run_dir, today="2026-09-08"):
        self.base_dir, self.run_dir, self.today = base_dir, run_dir, today


class TestRotationMissingRisk:
    def test_missing_risk_file_degrades_rather_than_raises(self, tmp_path, capsys):
        """`rotation` run by hand before `risk` must say so, not traceback."""
        base, rd = tmp_path / "b", tmp_path / "r"
        base.mkdir(); rd.mkdir()
        assert not os.path.exists(str(rd / "compute_risk.json"))

        smith_math.cmd_rotation(_RotationArgs(str(base), str(rd)))
        out = json.loads(capsys.readouterr().out)

        assert out["tickers"] == {}
        assert out["polarity_table"]            # still self-describing for the reader
        assert "compute_risk.json not found" in out["data_quality"][0]
        assert "run `risk` before `rotation`" in out["data_quality"][0]
