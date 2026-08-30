#!/usr/bin/env python3
"""Primary-source verification against SEC EDGAR's XBRL company-facts API.

WHY THIS EXISTS (2026-08-31). Every qualitative finding smith-quality produced on 2026-08-30
came back `verified: "unverified"` -- AMZN's capex-exceeds-OCF flag, BE's dilution, INTC's
$12.8bn charge -- because FMP `secFilings` returned ACCESS DENIED and G59 had recorded
"sec.gov returns 403 to WebFetch" as a closed door. Both readings were narrower than the
facts:

  * The FMP block is a PLAN TIER limit on one vendor. It says nothing about the SEC.
  * The 403 is a WEBFETCH limitation, not an SEC policy. EDGAR requires every request to
    declare a User-Agent identifying the requester (SEC Fair Access policy). WebFetch does not
    send one it accepts. curl with a declared UA returns 200 for submissions, companyconcept,
    companyfacts and browse-edgar alike -- measured, not assumed.

So the desk had been treating a missing header as an unreachable regulator for three weeks.

This is also a BETTER source than the thing it replaces. FMP `secFilings` returns a filing
INDEX -- names and URLs of documents someone then has to read and interpret. `companyconcept`
returns the AS-FILED XBRL VALUE for a named us-gaap tag, with its fiscal period, form type,
filing date and accession number attached. That is the number the company actually filed,
which is exactly what EVIDENCE PRINCIPLE rule 3 means by a primary-source check, and it
arrives as data rather than as prose to be re-read.

COMPUTE-FIRST: this fetches and returns filed figures. It forms no opinion about them.

Usage:
  python3 smith_edgar.py verify --ticker AMZN --concepts ocf,capex,lt_debt
  python3 smith_edgar.py concept --ticker INTC --tag StockholdersEquity --quarters 6
  python3 smith_edgar.py filings --ticker BE --form 10-Q --limit 3
"""
import argparse, json, subprocess, sys, time

UA = "AgentSmith-PortfolioResearch yashvardhanbajaj@gmail.com"
TICKER_URL = "https://www.sec.gov/files/company_tickers.json"
CONCEPT_URL = "https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{tag}.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"

# Named shorthands for the concepts a quality audit actually asks about. Several map to a LIST
# of tags because issuers legitimately choose different us-gaap tags for the same line -- the
# first tag that returns data wins, and the winning tag is always reported so the reader knows
# which one was used rather than having to trust that they are equivalent.
CONCEPTS = {
    "ocf":        ["NetCashProvidedByUsedInOperatingActivities",
                   "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"],
    "capex":      ["PaymentsToAcquirePropertyPlantAndEquipment",
                   "PaymentsToAcquireProductiveAssets"],
    "lt_debt":    ["LongTermDebtNoncurrent", "LongTermDebt"],
    "equity":     ["StockholdersEquity",
                   "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
    "diluted_shares": ["WeightedAverageNumberOfDilutedSharesOutstanding"],
    "net_income": ["NetIncomeLoss"],
    "op_income":  ["OperatingIncomeLoss"],
    "pretax":     ["IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
                   "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments"],
    "interest_exp": ["InterestExpense", "InterestExpenseNonoperating"],
    "revenue":    ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"],
    "sbc":        ["ShareBasedCompensation"],
}


def _get(url, tries=3):
    """Fetch JSON from EDGAR, declaring a User-Agent (SEC Fair Access requires one; omitting it
    is what produced the 403 recorded in G59).

    Transport is curl, not urllib, for a boring but load-bearing reason: this Mac's Python has
    no CA bundle installed and no certifi, so urllib raises CERTIFICATE_VERIFY_FAILED on every
    https call while /usr/bin/curl -- which uses the system keychain -- succeeds against the
    same URL. Shelling out is the difference between this module working and not. It is NOT
    disabling verification: curl verifies against the system trust store exactly as it should.
    """
    last = None
    for i in range(tries):
        try:
            proc = subprocess.run(
                ["curl", "-sS", "--compressed", "--max-time", "30",
                 "-H", f"User-Agent: {UA}", "-H", "Accept: application/json",
                 "-w", "\n%{http_code}", url],
                capture_output=True, text=True)
            if proc.returncode != 0:
                last = (proc.stderr or "").strip()[:200] or f"curl exit {proc.returncode}"
                time.sleep(1.0 + i)
                continue
            body, _, code = proc.stdout.rpartition("\n")
            code = code.strip()
            if code == "404":
                return None          # tag genuinely not filed by this issuer -- not an error
            if code != "200":
                last = f"HTTP {code}"
                time.sleep(1.0 + i)  # SEC asks for <=10 req/s; be a good citizen on retries
                continue
            return json.loads(body)
        except Exception as e:       # noqa: BLE001 -- network shapes vary, degrade not crash
            last = str(e)
            time.sleep(1.0 + i)
    raise RuntimeError(f"EDGAR fetch failed for {url}: {last}")


FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"


def _pick_freshest(cik, tags, quarters):
    """Return (tag, unit, rows) for whichever candidate tag has the MOST RECENT filed data.

    Not "the first tag that returns anything" -- that was this module's own first bug, caught
    on its first real use (2026-08-31). AMZN abandoned `PaymentsToAcquirePropertyPlantAndEquipment`
    in 2017 in favour of `PaymentsToAcquireProductiveAssets`, and first-match-wins cheerfully
    returned 2017 capex to verify a 2026 finding. A stale primary source is worse than no
    primary source: it carries the authority of an SEC filing and none of the relevance. So
    every candidate is fetched and the freshest `end` date wins, and the loser tags are still
    reported so the choice is auditable."""
    best = (None, None, [], "")
    considered = []
    for tag in tags:
        unit, rows = _rows(cik, tag, quarters)
        if not rows:
            considered.append({"tag": tag, "latest_end": None})
            continue
        latest = max(r.get("end") or "" for r in rows)
        considered.append({"tag": tag, "latest_end": latest})
        if latest > best[3]:
            best = (tag, unit, rows, latest)
    return best[0], best[1], best[2], considered


_TICKER_CACHE = {}


def cik_for(ticker):
    if not _TICKER_CACHE:
        data = _get(TICKER_URL) or {}
        for row in data.values():
            _TICKER_CACHE[row["ticker"].upper()] = str(row["cik_str"]).zfill(10)
    cik = _TICKER_CACHE.get(ticker.upper())
    if not cik:
        raise SystemExit(json.dumps({"error": f"no CIK on file for {ticker}"}))
    return cik


_FACTS_CACHE = {}


def _facts(cik):
    """companyfacts for one issuer, fetched at most once per process."""
    if cik not in _FACTS_CACHE:
        _FACTS_CACHE[cik] = ((_get(FACTS_URL.format(cik=cik)) or {})
                             .get("facts", {}).get("us-gaap", {}))
    return _FACTS_CACHE[cik]


def _units_for(cik, tag):
    """Unit->rows for one tag, from companyconcept, FALLING BACK to companyfacts.

    Bloom Energy (CIK 1664703) is why the fallback exists: its companyconcept endpoint returns
    HTTP 200 with `units` present but EMPTY for StockholdersEquity, LongTermDebt and diluted
    shares, while companyfacts carries all three. A 200 with nothing in it is the same
    "success wearing a green light" failure cmd_pipeline's emptiness probe was built for --
    and here it would have silently produced "BE files no equity data", which is false and
    would have quietly killed a real quality finding rather than confirming or refuting it."""
    doc = _get(CONCEPT_URL.format(cik=cik, tag=tag))
    units = (doc or {}).get("units") or {}
    if any(units.values()):
        return units, "companyconcept"
    body = _facts(cik).get(tag)
    if body and any((body.get("units") or {}).values()):
        return body["units"], "companyfacts"
    return {}, None


def _rows(cik, tag, quarters, unit_pref=("USD", "shares")):
    """Filed values for one tag, newest first. Deliberately keeps `form`, `fy`/`fp`, `end`,
    `filed` and `accn` on every row: a number without its filing is not a primary-source check,
    it is a number. Deduped on (end, start) keeping the LATEST-FILED value, so a restated figure
    supersedes the original rather than appearing twice."""
    units, via = _units_for(cik, tag)
    unit = next((u for u in unit_pref if units.get(u)), None) or \
        next((u for u, v in units.items() if v), None)
    if not unit:
        return None, []
    seen = {}
    for r in units[unit]:
        key = (r.get("end"), r.get("start"))
        if key not in seen or (r.get("filed") or "") > (seen[key].get("filed") or ""):
            seen[key] = r
    rows = sorted(seen.values(), key=lambda r: (r.get("end") or "", r.get("filed") or ""),
                  reverse=True)
    out = [{"value": r.get("val"), "start": r.get("start"), "end": r.get("end"),
            "form": r.get("form"), "fy": r.get("fy"), "fp": r.get("fp"),
            "filed": r.get("filed"), "accn": r.get("accn"), "unit": unit, "via": via}
           for r in rows[:quarters]]
    return unit, out


def cmd_concept(a):
    cik = cik_for(a.ticker)
    tags = CONCEPTS.get(a.tag, [a.tag])
    tag, unit, rows, considered = _pick_freshest(cik, tags, a.quarters)
    print(json.dumps({"ticker": a.ticker.upper(), "cik": cik, "tag_used": tag,
                      "tags_considered": considered, "unit": unit, "rows": rows,
                      "source": "SEC EDGAR XBRL companyconcept"}, indent=1))


def cmd_verify(a):
    cik = cik_for(a.ticker)
    names = [c.strip() for c in a.concepts.split(",") if c.strip()]
    out = {"ticker": a.ticker.upper(), "cik": cik,
           "source": "SEC EDGAR XBRL companyconcept (as-filed)", "concepts": {}}
    for name in names:
        tags = CONCEPTS.get(name, [name])
        tag, unit, rows, considered = _pick_freshest(cik, tags, a.quarters)
        if rows:
            out["concepts"][name] = {"tag_used": tag, "unit": unit, "rows": rows,
                                     "tags_considered": considered}
        else:
            out["concepts"][name] = {"tags_tried": tags, "rows": [],
                                     "note": "not filed under any candidate tag"}
    print(json.dumps(out, indent=1))


def cmd_filings(a):
    cik = cik_for(a.ticker)
    doc = _get(SUBMISSIONS_URL.format(cik=cik)) or {}
    rec = (doc.get("filings") or {}).get("recent") or {}
    rows = []
    for i, form in enumerate(rec.get("form", [])):
        if a.form and form != a.form:
            continue
        rows.append({"form": form, "filed": rec["filingDate"][i],
                     "period": rec.get("reportDate", [None] * (i + 1))[i],
                     "accn": rec["accessionNumber"][i],
                     "url": "https://www.sec.gov/Archives/edgar/data/%s/%s/%s" % (
                         int(cik), rec["accessionNumber"][i].replace("-", ""),
                         rec["primaryDocument"][i])})
        if len(rows) >= a.limit:
            break
    print(json.dumps({"ticker": a.ticker.upper(), "cik": cik,
                      "entity": doc.get("name"), "filings": rows}, indent=1))


def cmd_tags(a):
    """List the us-gaap tags an issuer ACTUALLY files, with the latest period for each.

    Exists because CONCEPTS above is a guess about which tag a company chose, and companies
    change that choice (see _pick_freshest). When a concept comes back empty or stale, this
    answers "what does this issuer call it?" from the issuer's own filings instead of guessing
    another synonym."""
    cik = cik_for(a.ticker)
    facts = (_get(FACTS_URL.format(cik=cik)) or {}).get("facts", {}).get("us-gaap", {})
    needle = a.match.lower().replace(" ", "")
    hits = []
    for tag, body in facts.items():
        if needle not in tag.lower():
            continue
        latest = ""
        for rows in (body.get("units") or {}).values():
            for r in rows:
                if (r.get("end") or "") > latest:
                    latest = r["end"]
        hits.append({"tag": tag, "label": body.get("label"), "latest_end": latest})
    hits.sort(key=lambda h: h["latest_end"], reverse=True)
    print(json.dumps({"ticker": a.ticker.upper(), "cik": cik, "match": a.match,
                      "tags": hits[:25], "total_matched": len(hits)}, indent=1))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("verify"); v.add_argument("--ticker", required=True)
    v.add_argument("--concepts", required=True, help="comma list, e.g. ocf,capex,lt_debt")
    v.add_argument("--quarters", type=int, default=6); v.set_defaults(fn=cmd_verify)
    c = sub.add_parser("concept"); c.add_argument("--ticker", required=True)
    c.add_argument("--tag", required=True); c.add_argument("--quarters", type=int, default=6)
    c.set_defaults(fn=cmd_concept)
    t = sub.add_parser("tags", help="which us-gaap tags this issuer actually files, by keyword")
    t.add_argument("--ticker", required=True)
    t.add_argument("--match", required=True, help="case-insensitive substring, e.g. 'propertyandequipment'")
    t.set_defaults(fn=cmd_tags)
    f = sub.add_parser("filings"); f.add_argument("--ticker", required=True)
    f.add_argument("--form", default=None); f.add_argument("--limit", type=int, default=5)
    f.set_defaults(fn=cmd_filings)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
