"""One clock for the whole desk (added 2026-09-14).

Before this module the scripts carried 41 bare `date.today()` calls, ~15 hand-copied
`strptime(args.today, ...) if args.today else date.today()` lines, a deprecated `utcnow()`, a
naive `datetime.now()`, and three timestamp parsers that disagreed about what a zone-less value
means. The live symptoms were a ledger row stamped in the future and run-dir labels that switch
between UTC and IST from one run to the next.

Conventions, stated once:
  * DESK DATE = the IST calendar date. It is what `--today` defaults to, what ledger rows and
    reports are keyed on, and what every bare `date.today()` on this Mac already returned -- so
    adopting it changes no output, it only makes the rule explicit and machine-independent.
  * SESSION DATE = the America/New_York calendar date: the US trading session a timestamp
    belongs to. A 01:04 IST run is analysing the PREVIOUS ET session.
  * A zone-less timestamp is read as IST (the ledger's historical convention), unless a caller
    says otherwise.
  * Machine-written stamps are UTC ISO-8601 with a `Z` suffix.

Standard library only; imports nothing from the other smith_* modules.
"""
import re
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

IST = timezone(timedelta(hours=5, minutes=30))
ET = ZoneInfo("America/New_York")

_RUN_LABEL_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(\d{2})(\d{2})(Z?)$")


def now_utc():
    return datetime.now(timezone.utc)


def desk_today(now=None):
    """The IST calendar date -- the default meaning of `today` everywhere in this codebase."""
    return (now or now_utc()).astimezone(IST).date()


def session_date(now=None):
    """The US/Eastern calendar date of `now` (DST-aware)."""
    return (now or now_utc()).astimezone(ET).date()


def resolve_today(value=None):
    """THE `--today` parser. None/empty -> desk_today(); a date passes through; a string must be
    YYYY-MM-DD (anything else raises ValueError, exactly like the strptime calls it replaces)."""
    if value is None or value == "":
        return desk_today()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value), "%Y-%m-%d").date()


def parse_any(value, naive_tz=IST):
    """Parse any timestamp shape this desk has ever written. Returns an aware datetime or None.

    Accepts ISO-8601 with or without offset (`Z` included), `YYYY-MM-DDTHH:MM`, a bare date, and
    run-dir labels `YYYY-MM-DD-HHMM` (zone-less, read as `naive_tz`) or `YYYY-MM-DD-HHMMZ` (UTC).
    """
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=naive_tz)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=naive_tz)
    t = str(value or "").strip()
    if not t:
        return None
    try:
        dt = datetime.fromisoformat(t)
        return dt if dt.tzinfo else dt.replace(tzinfo=naive_tz)
    except ValueError:
        pass
    m = _RUN_LABEL_RE.match(t)
    if m:
        dt = datetime.fromisoformat(f"{m.group(1)}T{m.group(2)}:{m.group(3)}:00")
        return dt.replace(tzinfo=timezone.utc if m.group(4) else naive_tz)
    try:
        return datetime.fromisoformat(t[:10]).replace(tzinfo=naive_tz)
    except ValueError:
        return None


def iso_utc(dt=None):
    """`2026-09-14T06:55:40Z`. Naive input is treated as UTC."""
    dt = dt or now_utc()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_label(now=None):
    """Run-dir label, always UTC and self-describing: `2026-09-14-0655Z`."""
    return (now or now_utc()).astimezone(timezone.utc).strftime("%Y-%m-%d-%H%MZ")
