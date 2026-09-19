"""Catalyst dedup, breadth and company-specific scoping (added 2026-09-19).

Built after 27 live catalyst_threat TRIMs: 26 came from ONE essay entry listing 26 of 27
holdings; the rest were near-duplicate reports of three events, two of which were single-company
events fanned out onto peers. Each test pins one of the three rules that now stop that -- and one
bug made while writing them (keeping only the newest duplicate dropped the named company).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import smith_risk as sr


def cat(h, date="2026-09-14", affects=(), direction="threat", **kw):
    return dict({"headline": h, "date": date, "affects": list(affects), "direction": direction,
                 "horizon": "structural"}, **kw)


class TestDedupe:
    def test_rewordings_of_one_event_collapse(self):
        cs = [cat("Anthropic CEO Dario Amodei publishes 'We Must Pace the Frontier' essay", affects=["A"]),
              cat("Anthropic's Amodei 'We Must Pace the Frontier' essay -- no walk-back", affects=["B"]),
              cat("Corning (GLW) $2bn at-the-market equity program with Goldman", affects=["GLW"])]
        out = sr.dedupe_catalysts(cs)
        assert len(out) == 2

    def test_the_merged_event_covers_every_name_any_report_listed(self):
        # the bug: the newer GLW report listed only COHR; keeping it alone dropped GLW itself
        cs = [cat("Corning (GLW) discloses $2bn at-the-market equity program", affects=["GLW", "COHR", "LITE"],
                  last_confirmed="2026-09-15"),
              cat("Corning (GLW) $2bn at-the-market equity program with Goldman", affects=["COHR"],
                  last_confirmed="2026-09-16")]
        out = sr.dedupe_catalysts(cs)
        assert len(out) == 1 and set(out[0]["affects"]) == {"GLW", "COHR", "LITE"}

    def test_different_events_are_not_merged(self):
        cs = [cat("KOSPI -3.26% (Samsung/SK Hynix) on Fed-hawkish repricing, Hormuz oil spike", affects=["MU"]),
              cat("CME FedWatch-implied odds of a 25bp hike at the FOMC surge to 88.5%", affects=["MU"])]
        assert len(sr.dedupe_catalysts(cs)) == 2

    def test_opposite_directions_are_never_merged(self):
        cs = [cat("CXMT reaches HBM3E risk production", affects=["MU"]),
              cat("CXMT reaches HBM3E risk production", affects=["MU"], direction="tailwind")]
        assert len(sr.dedupe_catalysts(cs)) == 2

    def test_events_far_apart_in_time_are_not_merged(self):
        cs = [cat("CXMT reaches HBM3E risk production", date="2026-09-01"),
              cat("CXMT reaches HBM3E risk production", date="2026-09-20")]
        assert len(sr.dedupe_catalysts(cs)) == 2


class TestBreadth:
    W = {t: 4.0 for t in "ABCDEFGHIJ"}          # ten names, 4% each

    def test_a_threat_to_most_of_the_book_is_a_factor_threat(self):
        assert sr.is_broad_catalyst(cat("x", affects=list("ABCDEFG")), self.W)   # 7 names

    def test_a_narrow_threat_is_not(self):
        assert not sr.is_broad_catalyst(cat("x", affects=list("ABC")), self.W)

    def test_a_few_names_that_are_most_of_the_equity_is_broad(self):
        w = {"A": 20.0, "B": 15.0, "C": 1.0}
        assert sr.is_broad_catalyst(cat("x", affects=["A", "B"]), w)            # 35% of equity

    def test_unheld_names_do_not_count(self):
        names, pct = sr.catalyst_breadth(cat("x", affects=["A", "ZZZ"]), self.W)
        assert names == ["A"] and pct == 4.0
