"""smith_clock: one date convention for the whole desk."""
from datetime import date, datetime, timezone

import pytest

import smith_clock as sc


def utc(*a):
    return datetime(*a, tzinfo=timezone.utc)


class TestDeskAndSessionDates:
    def test_an_early_ist_run_is_the_previous_et_session(self):
        now = utc(2026, 9, 13, 19, 34)            # 01:04 IST on 09-14
        assert sc.desk_today(now) == date(2026, 9, 14)
        assert sc.session_date(now) == date(2026, 9, 13)

    @pytest.mark.parametrize("now,expected", [
        (utc(2026, 3, 8, 6, 30), date(2026, 3, 8)),   # 01:30 EST, just before spring-forward
        (utc(2026, 3, 8, 7, 30), date(2026, 3, 8)),   # 03:30 EDT, just after
        (utc(2026, 11, 1, 4, 30), date(2026, 11, 1)),  # 00:30 EDT
        (utc(2026, 11, 1, 3, 30), date(2026, 10, 31)),  # 23:30 EDT the night before
    ])
    def test_dst_edges(self, now, expected):
        assert sc.session_date(now) == expected


class TestResolveToday:
    def test_default_is_desk_date(self, monkeypatch):
        monkeypatch.setattr(sc, "now_utc", lambda: utc(2026, 9, 13, 19, 34))
        assert sc.resolve_today(None) == date(2026, 9, 14)
        assert sc.resolve_today("") == date(2026, 9, 14)

    def test_string_and_date_pass_through(self):
        assert sc.resolve_today("2026-09-01") == date(2026, 9, 1)
        assert sc.resolve_today(date(2026, 9, 1)) == date(2026, 9, 1)

    def test_malformed_raises_like_strptime_did(self):
        with pytest.raises(ValueError):
            sc.resolve_today("09/01/2026")


class TestParseAny:
    @pytest.mark.parametrize("raw,expected_utc", [
        ("2026-09-01T00:00:00Z", utc(2026, 9, 1, 0, 0)),
        ("2026-09-01T10:30:00+05:30", utc(2026, 9, 1, 5, 0)),
        ("2026-09-01", utc(2026, 8, 31, 18, 30)),            # bare date = IST midnight
        ("2026-09-01T10:30", utc(2026, 9, 1, 5, 0)),          # zone-less = IST
        ("2026-08-31-1554", utc(2026, 8, 31, 10, 24)),        # legacy run label = IST
        ("2026-09-14-0655Z", utc(2026, 9, 14, 6, 55)),        # new run label = UTC
    ])
    def test_every_shape_the_desk_has_written(self, raw, expected_utc):
        assert sc.parse_any(raw) == expected_utc

    def test_garbage_is_none(self):
        assert sc.parse_any("not a date") is None
        assert sc.parse_any(None) is None

    def test_naive_zone_is_overridable(self):
        assert sc.parse_any("2026-09-01T00:00", naive_tz=timezone.utc) == utc(2026, 9, 1)


def test_iso_utc_and_run_label_round_trip():
    now = utc(2026, 9, 14, 6, 55, 40)
    assert sc.iso_utc(now) == "2026-09-14T06:55:40Z"
    assert sc.run_label(now) == "2026-09-14-0655Z"
    assert sc.parse_any(sc.run_label(now)) == utc(2026, 9, 14, 6, 55)


def test_core_parse_ts_is_the_same_parser():
    import smith_core
    for raw in ("2026-09-01T10:30:00+05:30", "2026-08-31-1554", "2026-09-01", "junk"):
        assert smith_core.parse_ts(raw) == sc.parse_any(raw)
