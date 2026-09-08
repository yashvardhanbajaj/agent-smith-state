"""Factor-catalyst carry-forward and freshness (added 2026-09-08).

THE INCIDENT THESE TESTS PIN. `_merge_catalyst` used to REPLACE
`state.factor_catalysts` wholesale. On the 2026-09-08 deep run -- first session
after a Labor Day long weekend -- smith-catalyst ran five searches and correctly
returned `"catalysts": []`. The REPLACE wiped the array: live `catalyst_threat`
triggers went 6 -> 0, the dashboard panel vanished, and two structural CXMT
HBM3E threats dated 2026-09-01 and 2026-09-03 were deleted for not being
RE-reported in a window that began after them.

"No NEW catalyst found in this window" is not "no catalyst exists". Only three
things may delete a catalyst now: an explicit retirement, its own horizon
expiring, or the user suppressing it. Silence is not one of them.
"""
from datetime import date

import smith_memory as sm
import smith_risk


CXMT = {"headline": "CXMT reaches HBM3E risk production", "date": "2026-09-01",
        "direction": "threat", "horizon": "structural", "magnitude": "5 units vs ASML's 131",
        "affects": ["MU", "SKHY"], "first_seen": "2026-09-01", "last_confirmed": "2026-09-07"}


def _state(cats=None):
    return {"factor_catalysts": list(cats if cats is not None else [dict(CXMT)]),
            "factor_themes": {"themes": []}}


class TestEmptyReturnIsNotRetirement:
    def test_empty_list_carries_forward_existing_entries(self):
        st = _state()
        res = sm._merge_catalyst({"catalysts": []}, st, "2026-09-08")
        assert len(st["factor_catalysts"]) == 1, "a quiet scan must not delete evidence"
        assert st["factor_catalysts"][0]["carried_forward"] is True
        assert res["factor_catalysts_fresh"] == 0
        assert res["factor_catalysts_carried"] == 1

    def test_carried_entry_keeps_its_last_confirmed_date(self):
        st = _state()
        sm._merge_catalyst({"catalysts": []}, st, "2026-09-08")
        assert st["factor_catalysts"][0]["last_confirmed"] == "2026-09-07", \
            "carrying forward must not forge a confirmation that never happened"

    def test_absent_key_means_the_agent_did_not_run_and_changes_nothing(self):
        st = _state()
        res = sm._merge_catalyst({}, st, "2026-09-08")
        assert st["factor_catalysts"] == [dict(CXMT)]
        assert res["factor_catalysts_ran"] is False

    def test_returned_catalyst_is_marked_fresh_and_keeps_first_seen(self):
        st = _state()
        again = {k: v for k, v in CXMT.items() if k not in ("first_seen", "last_confirmed")}
        sm._merge_catalyst({"catalysts": [again]}, st, "2026-09-08")
        c = st["factor_catalysts"][0]
        assert c["last_confirmed"] == "2026-09-08" and c["first_seen"] == "2026-09-01"
        assert c["carried_forward"] is False

    def test_a_new_catalyst_lands_alongside_the_carried_one(self):
        st = _state()
        new = {"headline": "Second story", "date": "2026-09-08", "direction": "tailwind",
               "horizon": "immediate", "affects": ["AAA"]}
        sm._merge_catalyst({"catalysts": [new]}, st, "2026-09-08")
        assert {c["headline"] for c in st["factor_catalysts"]} == {CXMT["headline"], "Second story"}


class TestExplicitRetirementDeletes:
    def test_named_retirement_removes_exactly_that_entry(self):
        st = _state()
        res = sm._merge_catalyst(
            {"catalysts": [],
             "retired_catalysts": [{"headline": CXMT["headline"], "date": CXMT["date"],
                                    "reason": "Micron confirmed CXMT samples failed qualification"}]},
            st, "2026-09-08")
        assert st["factor_catalysts"] == []
        assert res["factor_catalysts_retired"][0]["reason"].startswith("Micron confirmed")

    def test_retirement_must_match_the_date_too_not_just_the_headline(self):
        """(headline, date) is the identity -- the same story dated differently is a genuine
        update, not the thing that was retired. Same rule `catalyst_is_suppressed` uses."""
        st = _state()
        sm._merge_catalyst({"catalysts": [],
                            "retired_catalysts": [{"headline": CXMT["headline"],
                                                   "date": "2026-08-01"}]}, st, "2026-09-08")
        assert len(st["factor_catalysts"]) == 1


class TestHorizonExpiry:
    def test_noise_ages_out_but_structural_survives_the_same_gap(self):
        noise = {"headline": "Friday tape wobble", "date": "2026-08-25", "horizon": "noise",
                 "direction": "ambiguous", "last_confirmed": "2026-08-25"}
        st = _state([dict(CXMT), noise])
        res = sm._merge_catalyst({"catalysts": []}, st, "2026-09-08")
        heads = {c["headline"] for c in st["factor_catalysts"]}
        assert heads == {CXMT["headline"]}
        assert res["factor_catalysts_aged_out"][0]["headline"] == "Friday tape wobble"

    def test_structural_eventually_ages_out_too(self):
        st = _state()
        sm._merge_catalyst({"catalysts": []}, st, "2026-11-30")
        assert st["factor_catalysts"] == [], "carry-forward is bounded, not an accumulating log"

    def test_unparseable_date_is_never_silently_expired(self):
        broken = {"headline": "No date", "date": "", "horizon": "noise"}
        st = _state([broken])
        sm._merge_catalyst({"catalysts": []}, st, "2026-09-08")
        assert len(st["factor_catalysts"]) == 1, \
            "a bad date is a data-quality problem, not a licence to delete a threat"


class TestLiveCatalystReaders:
    def test_live_catalysts_hides_expired_and_suppressed(self):
        stale = {"headline": "Old noise", "date": "2026-07-01", "horizon": "noise"}
        supp = {"headline": "Priced in", "date": "2026-09-05", "horizon": "structural"}
        st = {"factor_catalysts": [dict(CXMT), stale, supp],
              "catalyst_suppressed": [{"headline": "Priced in", "date": "2026-09-05"}]}
        live = smith_risk.live_catalysts(st, date(2026, 9, 8))
        assert [c["headline"] for c in live] == [CXMT["headline"]]

    def test_carry_summary_counts_this_run_as_fresh(self):
        st = {"factor_catalysts": [dict(CXMT, last_confirmed="2026-09-08"),
                                   dict(CXMT, headline="Other", last_confirmed="2026-09-07")]}
        assert smith_risk.catalyst_carry_summary(st, date(2026, 9, 8)) == (1, 1)
