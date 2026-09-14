"""smith_core write primitives: nothing a crash, a concurrent writer or a stray tmp can corrupt."""
import json
import multiprocessing as mp
import os
import stat

import pytest

import smith_core as core


def test_safe_write_keeps_original_and_bak_when_dump_fails(tmp_path):
    p = tmp_path / "state.json"
    core.safe_write(str(p), {"v": 1})
    core.safe_write(str(p), {"v": 2})

    class Unserialisable:
        pass

    with pytest.raises(TypeError):
        core.safe_write(str(p), {"v": Unserialisable()})
    assert json.loads(p.read_text()) == {"v": 2}
    # serialisation fails BEFORE the .bak rotates, so the .bak still holds the generation before 2
    assert json.loads((tmp_path / "state.json.bak").read_text()) == {"v": 1}
    assert not [f for f in os.listdir(tmp_path) if f.endswith(".tmp")], "stray tmp left behind"


def test_safe_write_bytes_match_the_old_contract(tmp_path):
    p = tmp_path / "x.json"
    obj = {"b": [1, 2], "a": "é"}
    core.safe_write(str(p), obj)
    assert p.read_text() == json.dumps(obj, indent=2)


def test_atomic_write_preserves_file_mode(tmp_path):
    p = tmp_path / "x.json"
    p.write_text("{}")
    os.chmod(p, 0o644)
    core.atomic_write_json(str(p), {"a": 1})
    assert stat.S_IMODE(os.stat(p).st_mode) == 0o644


def test_new_file_is_not_left_owner_only(tmp_path):
    p = tmp_path / "new.json"
    core.atomic_write_json(str(p), {"a": 1})
    assert stat.S_IMODE(os.stat(p).st_mode) & 0o044, "mkstemp's 0600 leaked into the real file"


def test_fsync_is_called(tmp_path, monkeypatch):
    calls = []
    real = os.fsync
    monkeypatch.setattr(core.os, "fsync", lambda fd: (calls.append(fd), real(fd)))
    core.safe_write(str(tmp_path / "x.json"), {"a": 1})
    assert calls


def test_atomic_append_line(tmp_path):
    p = tmp_path / "ledger.csv"
    core.atomic_append_line(str(p), "ts,mode")
    core.atomic_append_line(str(p), "2026-09-14T06:55:40Z,quick\n")
    assert p.read_text() == "ts,mode\n2026-09-14T06:55:40Z,quick\n"


def _increment(path, n):
    for _ in range(n):
        with core.locked_json(path, default={"n": 0}) as box:
            box["obj"]["n"] += 1


def test_locked_json_loses_no_concurrent_updates(tmp_path):
    p = str(tmp_path / "counter.json")
    core.safe_write(p, {"n": 0})
    ctx = mp.get_context("spawn")
    procs = [ctx.Process(target=_increment, args=(p, 40)) for _ in range(2)]
    for pr in procs:
        pr.start()
    for pr in procs:
        pr.join(60)
    assert json.load(open(p)) == {"n": 80}


def test_locked_json_writes_nothing_when_the_body_raises(tmp_path):
    p = str(tmp_path / "s.json")
    core.safe_write(p, {"n": 1})
    with pytest.raises(RuntimeError):
        with core.locked_json(p) as box:
            box["obj"]["n"] = 99
            raise RuntimeError("abort")
    assert json.load(open(p)) == {"n": 1}
