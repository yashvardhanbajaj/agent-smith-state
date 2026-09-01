"""Shared pytest fixtures for the unit suite.

These tests exercise the functions extracted from cmd_triggers (smith_math.py),
cmd_proposals (smith_lifecycle.py), and build() (smith_dashboard.py) in the
2026-09 god-function refactor -- real unit tests with edge cases, on top of the
golden-master regression harness in tests/verify_*.sh (which proves the refactor
itself changed nothing; these prove the pieces are individually correct).
"""
import os
import sys

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import pytest


def make_base(ticker="AAA", cluster="Compute/Hyperscaler", thesis_status="intact",
              rsi14=50.0, rel_strength_1m_pp=0.0, abs_return_1m_pct=0.0,
              price_usd=100.0, market_value_usd=1000.0):
    """The per-ticker `base` dict every smith_math.py trigger function spreads via {**base, ...}
    -- shape taken from cmd_triggers' own construction site (smith_math.py, the main loop)."""
    return {"ticker": ticker, "cluster": cluster, "thesis_status": thesis_status,
            "rsi14": rsi14, "rel_strength_1m_pp": rel_strength_1m_pp,
            "abs_return_1m_pct": abs_return_1m_pct, "price_usd": price_usd,
            "market_value_usd": market_value_usd}


@pytest.fixture
def base():
    return make_base()


def make_proposal(id="P-001", ticker="AAA", action="Trim AAA", status="open",
                   direction_bucket="TRIM", date="2026-08-20", **extra):
    d = {"id": id, "ticker": ticker, "action": action, "status": status,
         "direction_bucket": direction_bucket, "date": date}
    d.update(extra)
    return d


@pytest.fixture
def no_breach():
    """A directional_breach(cluster, bucket) stub that never reports a breach -- the common
    case in cmd_proposals' scorer/retirement passes."""
    return lambda cluster, bucket: None
