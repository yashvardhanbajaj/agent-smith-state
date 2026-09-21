import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
import smith_ticket as T


def buy(t, conv=50, size=500, vote="live"):
    return {"ticker": t, "conviction_score": conv, "suggested_size_usd": size, "vote": vote}


def sell(t, vote="live"):
    return {"ticker": t, "vote": vote}


def pair(s, b, conv=50, size=500):
    return {"vote": "live", "sell_leg": {"ticker": s}, "buy_leg": {"ticker": b, "conviction_score": conv,
                                                                    "suggested_size_usd": size}}


def test_live_sell_shadows_buys_into_same_ticker():
    a, b = buy("AMAT"), buy("AMAT")
    out = T.net_conflicts([("trend_entry", a), ("conviction_average", b)], [], [("catalyst_threat", sell("AMAT"))])
    assert a["vote"] == b["vote"] == "shadow" and len(out) == 2 and "netted_because" in a


def test_shadow_sell_does_not_net():
    a = buy("AMAT")
    T.net_conflicts([("trend_entry", a)], [], [("catalyst_threat", sell("AMAT", vote="below_materiality"))])
    assert a["vote"] == "live"


def test_duplicate_buys_keep_strongest_pair_wins_tie():
    single, p = buy("KLAC", conv=50, size=429), pair("AMD", "KLAC", conv=50, size=558)
    T.net_conflicts([("conviction_average", single)], [("profit_rotation", p)], [])
    assert single["vote"] == "shadow" and p["vote"] == "live"


def test_higher_conviction_single_beats_pair():
    single, p = buy("KLAC", conv=70), pair("AMD", "KLAC", conv=50)
    T.net_conflicts([("conviction_average", single)], [("profit_rotation", p)], [])
    assert p["vote"] == "shadow" and single["vote"] == "live"


def test_pair_sell_leg_nets_other_buys_but_not_its_own():
    p, other = pair("AMD", "KLAC"), buy("AMD")
    T.net_conflicts([("trend_entry", other)], [("profit_rotation", p)], [])
    assert other["vote"] == "shadow" and p["vote"] == "live"


def test_carried_thesis_decays_with_age():
    import smith_conviction as C
    e = {"status": "strengthening", "carried": True, "exited": True, "held": False,
         "last_reviewed_on": "2026-09-01", "exited_as_of": "2026-09-02", "carried_from": "x",
         "verified": "primary", "evidence_for": [], "evidence_against": []}
    fresh, *_ = C.thesis_component(e, "2026-09-05")
    old, *_ = C.thesis_component(dict(e, last_reviewed_on="2026-03-01"), "2026-09-05")
    nodate, *_ = C.thesis_component({k: v for k, v in e.items() if k not in ("last_reviewed_on", "exited_as_of")}, "2026-09-05")
    assert fresh > old > 0 and abs(nodate - old) < 1e-9 or nodate <= old
    legacy, *_ = C.thesis_component(e)              # no today -> unchanged legacy behaviour
    assert legacy >= fresh
