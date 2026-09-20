"""Phase 5 front end: the proposal card shows the ticket, renders pre-ticket rows as LEGACY, and does not
regress the verdict-first card or the Retire button. Runs the built page in jsdom with a fake db (dev
servers are blocked in unattended sessions); skipped when node/jsdom are not installed."""
import glob
import json
import os
import shutil
import subprocess
import sys

import pytest

HERE = os.path.dirname(__file__)
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
FIX = os.path.join(REPO, "tests", "fixtures", "dashboard_case1", "base")


def _jsdom_path():
    env = os.environ.get("JSDOM_NODE_PATH")
    cands = [env] if env else []
    cands += glob.glob("/private/tmp/claude-*/*/*/scratchpad/jsd/node_modules") + [os.path.join(REPO, "node_modules")]
    for c in cands:
        if c and os.path.isdir(os.path.join(c, "jsdom")):
            return c
    return None


def _row(pid, action, ticker, bucket, **kw):
    return {"id": pid, "date": "2026-09-20", "ticker": ticker, "action": action, "direction_bucket": bucket,
            "size_usd": 500.0, "price_at_proposal": 100.0, "status": "open", "rationale": "r", "priority": "MEDIUM",
            "trigger_type": "trend_entry", **kw}


TICKET = {"entry": {"price_usd": 443.75}, "stop": {"price_usd": 408.96, "distance_pct": 7.84},
          "target": {"price_usd": 582.9, "r_multiple": 4.0},
          "size": {"usd": 504.51, "shares": 1.1369, "pct_of_book": 1.19, "wanted_usd": 600.0, "clamped_by": "heat"},
          "risk": {"kind": "added", "usd": 39.55, "r_ticket": 0.19}, "edge": {"ev_r": 0.99, "p_win": 0.41},
          "invalidation": "price trades below $408.96 (the stop) OR AMAT drops out of this run's live trend_entry list",
          "horizon": {"expires_on": "2026-10-04", "review_on": "2026-09-27", "days": 14}, "lots": {}, "source": "trigger_row"}
SELL_TICKET = {"entry": {"price_usd": 1670.0}, "stop": None, "target": None,
               "size": {"usd": 584.7, "shares": 0.35, "pct_of_book": 1.37},
               "risk": {"kind": "removed", "usd": None, "removed_usd": 33.91, "r_ticket": 0.16}, "edge": {},
               "invalidation": "ASML drops out of the live list", "horizon": {"expires_on": "2026-09-25", "review_on": "2026-09-22"},
               "lots": {"ltcg_note": "FIFO: 0.35 sh short-term"}, "source": "trigger_row"}


@pytest.mark.skipif(shutil.which("node") is None or _jsdom_path() is None, reason="node + jsdom not available")
def test_ticket_card_legacy_card_and_retire_button(tmp_path):
    base = str(tmp_path / "base")
    shutil.copytree(FIX, base)
    props = [_row("P-901", "Buy AMAT", "AMAT", "BUY", ticket_version=1, ticket=TICKET, size_usd=504.51),
             _row("P-902", "Buy KLAC", "KLAC", "BUY"),                                   # pre-ticket
             _row("P-903", "Trim ASML", "ASML", "TRIM", ticket_version=1, ticket=SELL_TICKET, size_usd=584.7)]
    json.dump({"proposals": props, "scorecard": {}}, open(os.path.join(base, "proposals.json"), "w"))
    # you SOLD KLAC after the desk said buy it -> smith_validity's verdict is `retire` -> the Retire button
    json.dump({"trades": [{"ticker": "KLAC", "date": "2026-09-21", "qty_change": -1.0}]},
              open(os.path.join(base, "trades.json"), "w"))
    html = str(tmp_path / "d.html")
    subprocess.run([sys.executable, os.path.join(REPO, "scripts", "smith_dashboard.py"), "--base-dir", base,
                    "--built-at", "T", "--out", html], check=True, capture_output=True)
    env = dict(os.environ, NODE_PATH=_jsdom_path())
    p = subprocess.run(["node", os.path.join(REPO, "tests", "jsdom", "ticket_card.js"), html], env=env,
                       capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, p.stderr
    out = json.loads(p.stdout.strip().splitlines()[-1])
    assert out["errors"] == []
    assert out["ticketKeys"] == ["Entry", "Stop", "Target", "Size", "Risk", "EV", "Expires"]
    assert "$408.96" in out["ticketText"] and "4.0R" in out["ticketText"] and "2026-10-04" in out["ticketText"]
    assert out["sellKeys"] == ["Entry", "Size", "Risk removed", "Expires"]          # a sell shows no stop
    assert out["legacy"] is True and out["legacyHasTiles"] is False                 # LEGACY, no invented stop
    assert out["hasVerdictTiles"] and "accept" in out["decide"]                     # verdict-first card intact
    assert out["retireButtonOnLegacyCard"] is True
    assert out["retireWrites"] == 1                                                 # the Retire button still writes
