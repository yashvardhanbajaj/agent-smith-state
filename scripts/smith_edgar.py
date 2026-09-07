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
import argparse, json, os, subprocess, sys, time
from datetime import date, datetime, timedelta

UA = "AgentSmith-PortfolioResearch yashvardhanbajaj@gmail.com"
TICKER_URL = "https://www.sec.gov/files/company_tickers.json"
CONCEPT_URL = "https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{tag}.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"

# ---------------------------------------------------------------------------
# PERSISTENT CACHE (added 2026-09-01, cache-awareness audit).
# ---------------------------------------------------------------------------
# Found while auditing this desk's caching for gaps: this module had NO cross-process cache at
# all -- _TICKER_CACHE/_FACTS_CACHE below are plain dicts that vanish the instant a `smith_edgar.py`
# subprocess exits, which is every single invocation (each verify/concept/tags/filings call is
# its own process, spawned via Bash by whichever agent needs it). That means:
#   (a) EVERY call re-downloaded the FULL SEC ticker->CIK master list (thousands of entries)
#       just to resolve ONE ticker, even though a CIK never changes once assigned to a company.
#   (b) A ticker verified in one run and checked again days later (a stubborn quality finding
#       re-audited, or two different agents needing the same company's same concept) re-fetched
#       from EDGAR every time, even though AS-FILED SEC DATA IS IMMUTABLE for a given fiscal
#       period -- the whole reason this module exists as a primary source. There is no more
#       cache-worthy data in this codebase than an as-filed XBRL fact.
# Fix: a disk-backed cache at `<base_dir>/edgar_cache.json`, two sections with different TTLs
# reflecting how often each actually changes:
#   - ticker_cik: essentially permanent (180 days -- a CIK reassignment/ticker change is rare
#     enough that re-resolving it every 6 months is plenty safe, and free if it hasn't moved).
#   - concepts, keyed "{cik}:{tag}": short (3 days) -- long enough that a same-week re-check of
#     the same fact costs nothing, short enough that a fresh quarterly filing is picked up
#     within days, never staler than the freshness this module's own callers already tolerate
#     (smith-quality is monthly cadence; smith-thesis's occasional 1-3-name verification is not
#     time-critical to the hour).
EDGAR_CACHE_FILENAME = "edgar_cache.json"
TTL_DAYS_CIK = 180
TTL_DAYS_CONCEPT = 3
_BASE_DIR = "."
_disk_cache = None  # lazy-loaded, then held for the life of this process


def _cache_path():
    return os.path.join(_BASE_DIR, EDGAR_CACHE_FILENAME)


def _load_disk_cache():
    global _disk_cache
    if _disk_cache is not None:
        return _disk_cache
    try:
        with open(_cache_path()) as f:
            _disk_cache = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        _disk_cache = {"schema_version": 1, "ticker_cik": {}, "ticker_cik_fetched_at": None,
                        "concepts": {}}
    _disk_cache.setdefault("ticker_cik", {})
    _disk_cache.setdefault("concepts", {})
    return _disk_cache


def _save_disk_cache():
    if _disk_cache is None:
        return
    # Same WRITE SAFETY spirit as the rest of this codebase (.bak then tmp-then-mv), scaled
    # down: this is a cache, not a memory-of-record file, so a single tmp-then-mv is enough --
    # worst case on an interrupted write is a cache miss next run, never data loss.
    tmp = _cache_path() + ".tmp"
    with open(tmp, "w") as f:
        json.dump(_disk_cache, f, indent=1)
    os.replace(tmp, _cache_path())


def _days_since(iso_date_str):
    if not iso_date_str:
        return None
    try:
        return (date.today() - datetime.strptime(iso_date_str, "%Y-%m-%d").date()).days
    except ValueError:
        return None

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


def _get_text(url, tries=3):
    """Same transport as `_get` (curl + declared UA, same CA-bundle reason), but for a Form 4
    filing's raw XML document rather than a JSON API response -- returns the response body as
    text, unparsed, or None on a 404."""
    last = None
    for i in range(tries):
        try:
            proc = subprocess.run(
                ["curl", "-sS", "--compressed", "--max-time", "30",
                 "-H", f"User-Agent: {UA}", "-w", "\n%{http_code}", url],
                capture_output=True, text=True)
            if proc.returncode != 0:
                last = (proc.stderr or "").strip()[:200] or f"curl exit {proc.returncode}"
                time.sleep(1.0 + i)
                continue
            body, _, code = proc.stdout.rpartition("\n")
            code = code.strip()
            if code == "404":
                return None
            if code != "200":
                last = f"HTTP {code}"
                time.sleep(1.0 + i)
                continue
            return body
        except Exception as e:       # noqa: BLE001
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


_FACTS_CACHE = {}  # in-process only -- companyfacts fallback, fetched at most once per process


def cik_for(ticker):
    """Ticker->CIK, disk-cached at TTL_DAYS_CIK. A CIK is assigned once and essentially never
    changes, so this is the single highest-value cache in this module: without it, every
    invocation downloaded the ENTIRE SEC ticker file (thousands of rows) to resolve one ticker."""
    cache = _load_disk_cache()
    ticker = ticker.upper()
    age = _days_since(cache.get("ticker_cik_fetched_at"))
    if ticker in cache["ticker_cik"] and age is not None and age <= TTL_DAYS_CIK:
        return cache["ticker_cik"][ticker]
    # Stale, missing entirely, or this specific ticker isn't in a stale cache yet -- refetch the
    # whole map (it's one call regardless of how many tickers we need) and overwrite the section.
    data = _get(TICKER_URL) or {}
    fresh = {row["ticker"].upper(): str(row["cik_str"]).zfill(10) for row in data.values()}
    cache["ticker_cik"] = fresh
    cache["ticker_cik_fetched_at"] = str(date.today())
    _save_disk_cache()
    cik = fresh.get(ticker)
    if not cik:
        raise SystemExit(json.dumps({"error": f"no CIK on file for {ticker}"}))
    return cik


def _facts(cik):
    """companyfacts for one issuer, fetched at most once per process."""
    if cik not in _FACTS_CACHE:
        _FACTS_CACHE[cik] = ((_get(FACTS_URL.format(cik=cik)) or {})
                             .get("facts", {}).get("us-gaap", {}))
    return _FACTS_CACHE[cik]


def _units_for(cik, tag):
    """Unit->rows for one tag, from companyconcept, FALLING BACK to companyfacts. Disk-cached
    per (cik, tag) at TTL_DAYS_CONCEPT: as-filed data for a completed fiscal period never
    changes, so a re-check within the TTL window is a pure cache hit, not a re-verification --
    the only reason the TTL isn't infinite is to pick up a newly-filed quarter within a few days.

    Bloom Energy (CIK 1664703) is why the fallback exists: its companyconcept endpoint returns
    HTTP 200 with `units` present but EMPTY for StockholdersEquity, LongTermDebt and diluted
    shares, while companyfacts carries all three. A 200 with nothing in it is the same
    "success wearing a green light" failure cmd_pipeline's emptiness probe was built for --
    and here it would have silently produced "BE files no equity data", which is false and
    would have quietly killed a real quality finding rather than confirming or refuting it."""
    cache = _load_disk_cache()
    key = f"{cik}:{tag}"
    entry = cache["concepts"].get(key)
    if entry and _days_since(entry.get("fetched_at")) is not None and \
       _days_since(entry.get("fetched_at")) <= TTL_DAYS_CONCEPT:
        via = entry["via"]
        return entry["units"], (via + " (cached)") if via else None

    doc = _get(CONCEPT_URL.format(cik=cik, tag=tag))
    units = (doc or {}).get("units") or {}
    via = None
    if any(units.values()):
        via = "companyconcept"
    else:
        body = _facts(cik).get(tag)
        if body and any((body.get("units") or {}).values()):
            units, via = body["units"], "companyfacts"
    cache["concepts"][key] = {"units": units, "via": via, "fetched_at": str(date.today())}
    _save_disk_cache()
    return units, via


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


# ---------------------------------------------------------------------------
# Insider transactions (Form 4) -- added 2026-09-07
# ---------------------------------------------------------------------------
# WHY THIS TAKES THE RAW-EDGAR PATH, NOT FMP `insiderTrades` (same reasoning that put the rest
# of this module here in the first place): FMP's insiderTrades and form13F endpoints are BOTH
# gated behind a plan tier this account does not have -- confirmed live, "ACCESS DENIED ...
# requires the Starter, Premium, Ultimate, or Enterprise plan" -- while a Form 4 is a public
# filing SEC serves for free to anyone declaring a User-Agent, exactly like companyconcept was.
#
# Form 13F is NOT given the same treatment here. A Form 4 is one ISSUER's own filings -- cheap
# to enumerate via `submissions`, one CIK. Institutional ownership BY TICKER requires scanning
# ACROSS many institutional filers' 13F holdings tables for a mention of that ticker's CUSIP --
# there is no free, ticker-keyed EDGAR endpoint for that; FMP's paid tier exists precisely
# because it pre-aggregates that fan-out. `cmd_institutional_flow` below is real, tested
# detection logic that RUNS the moment ticker-keyed 13F data is available (an FMP plan upgrade,
# or a future scraping project), but this file does not fetch that data itself yet -- said
# plainly rather than pretending a fetch path exists that doesn't.

TRANSACTION_CODE_LABELS = {
    "P": "open-market purchase", "S": "open-market sale", "A": "grant/award",
    "M": "option exercise", "G": "gift", "F": "tax withholding", "D": "disposition to issuer",
    "C": "conversion",
}
# Only P/S are a genuine discretionary market bet -- grants, exercises, gifts and tax
# withholding are compensation mechanics or routine tax events an insider doesn't choose in
# the way a cluster-of-sells-into-a-rally signal is supposed to mean. Counting those as
# "insider selling" is how a normal RSU vesting quarter gets mistaken for a warning sign.
DISCRETIONARY_CODES = {"P", "S"}


def _xml_text(elem, path):
    node = elem.find(path)
    return node.text.strip() if node is not None and node.text else None


def _parse_form4(xml_text):
    """Parse one Form 4 XML document (schema confirmed live, 2026-09-07) into a flat list of
    discretionary (P/S) transactions. Non-derivative table only -- derivative transactions
    (options, RSUs before vesting) are a distinct signal this pass does not attempt to
    interpret; returning fewer, cleaner rows beats returning more, ambiguous ones."""
    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_text)
    owner_name = _xml_text(root, ".//reportingOwner/reportingOwnerId/rptOwnerName")
    rel = root.find(".//reportingOwner/reportingOwnerRelationship")
    is_officer = _xml_text(rel, "isOfficer") == "1" if rel is not None else False
    is_director = _xml_text(rel, "isDirector") == "1" if rel is not None else False
    officer_title = _xml_text(rel, "officerTitle") if rel is not None else None

    rows = []
    for tx in root.findall(".//nonDerivativeTable/nonDerivativeTransaction"):
        code = _xml_text(tx, "transactionCoding/transactionCode")
        if code not in DISCRETIONARY_CODES:
            continue
        shares = _xml_text(tx, "transactionAmounts/transactionShares/value")
        price = _xml_text(tx, "transactionAmounts/transactionPricePerShare/value")
        ad_code = _xml_text(tx, "transactionAmounts/transactionAcquiredDisposedCode/value")
        rows.append({
            "owner_name": owner_name, "is_officer": is_officer, "is_director": is_director,
            "officer_title": officer_title,
            "transaction_date": _xml_text(tx, "transactionDate/value"),
            "transaction_code": code, "transaction_label": TRANSACTION_CODE_LABELS.get(code),
            "acquired_or_disposed": ad_code,
            "shares": float(shares) if shares else None,
            "price_usd": float(price) if price else None,
        })
    return rows


def _recent_form4_filings(cik, lookback_days, max_filings):
    doc = _get(SUBMISSIONS_URL.format(cik=cik)) or {}
    rec = (doc.get("filings") or {}).get("recent") or {}
    cutoff = (date.today() - timedelta(days=lookback_days)).isoformat()
    hits = []
    for i, form in enumerate(rec.get("form", [])):
        if form != "4":
            continue
        filed = rec["filingDate"][i]
        if filed < cutoff:
            continue
        hits.append({"filed": filed, "accession": rec["accessionNumber"][i],
                    "primary_document": rec["primaryDocument"][i]})
        if len(hits) >= max_filings:
            break
    return hits


def cmd_insider_cluster(a):
    """Fetch and parse an issuer's recent Form 4 filings, then apply two deterministic cluster
    rules over the discretionary (P/S) transactions found:

      * insider_sell_into_rally: >= --min-sellers distinct insiders with open-market SALES
        inside the lookback window, while the caller-supplied price is within
        --near-high-pct of the 52-week high.
      * insider_buy_the_drawdown: >= --min-buyers distinct insiders with open-market PURCHASES
        inside the lookback window, while the caller-supplied drawdown from the 52-week high
        is at or beyond --severe-drawdown-pct.

    Price/52-week context is NEVER fetched here -- pass --price-usd and --wk52-high-usd (both
    required to evaluate the rally rule) and/or --drawdown-from-high-pct (required for the
    drawdown rule); a rule with a missing required price input is skipped, not guessed, and
    named in data_quality. This mirrors the rest of the codebase's ONE canonical reader for
    price/52-week data (data_cache.wk52) -- this module has no opinion about it."""
    cik = cik_for(a.ticker)
    filings = _recent_form4_filings(cik, a.lookback_days, a.max_filings)
    all_tx, fetch_errors = [], []
    for f in filings:
        doc_name = os.path.basename(f["primary_document"])
        accn = f["accession"].replace("-", "")
        url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accn}/{doc_name}"
        try:
            xml_text = _get_text(url)
            if xml_text:
                for row in _parse_form4(xml_text):
                    row["filed"] = f["filed"]
                    all_tx.append(row)
        except Exception as e:  # noqa: BLE001 -- one bad filing must not sink the whole scan
            fetch_errors.append({"accession": f["accession"], "error": str(e)[:200]})
        time.sleep(0.15)  # SEC's <=10 req/s courtesy limit, same spirit as `_get`'s own backoff

    sells = [t for t in all_tx if t["transaction_code"] == "S"]
    buys = [t for t in all_tx if t["transaction_code"] == "P"]
    distinct_sellers = sorted({t["owner_name"] for t in sells if t["owner_name"]})
    distinct_buyers = sorted({t["owner_name"] for t in buys if t["owner_name"]})

    dq = list(fetch_errors and [f"{len(fetch_errors)} filing(s) failed to fetch/parse"] or [])
    findings = []

    if len(distinct_sellers) >= a.min_sellers:
        if a.price_usd is not None and a.wk52_high_usd:
            near_high = a.price_usd >= a.wk52_high_usd * (1 - a.near_high_pct / 100.0)
            if near_high:
                findings.append({
                    "type": "insider_sell_into_rally",
                    "sellers": distinct_sellers, "seller_count": len(distinct_sellers),
                    "total_shares_sold": round(sum(t["shares"] or 0 for t in sells), 0),
                    "note": (f"{len(distinct_sellers)} distinct insider(s) sold in the last "
                             f"{a.lookback_days}d while price (${a.price_usd:.2f}) sits within "
                             f"{a.near_high_pct:g}% of the 52-week high (${a.wk52_high_usd:.2f}).")})
        else:
            dq.append(f"{len(distinct_sellers)} distinct seller(s) found but --price-usd/"
                      f"--wk52-high-usd not supplied -- rally proximity not evaluated")

    if len(distinct_buyers) >= a.min_buyers:
        if a.drawdown_from_high_pct is not None:
            severe = a.drawdown_from_high_pct <= -abs(a.severe_drawdown_pct)
            if severe:
                findings.append({
                    "type": "insider_buy_the_drawdown",
                    "buyers": distinct_buyers, "buyer_count": len(distinct_buyers),
                    "total_shares_bought": round(sum(t["shares"] or 0 for t in buys), 0),
                    "note": (f"{len(distinct_buyers)} distinct insider(s) bought in the last "
                             f"{a.lookback_days}d during a {a.drawdown_from_high_pct:.1f}% "
                             f"drawdown from the 52-week high.")})
        else:
            dq.append(f"{len(distinct_buyers)} distinct buyer(s) found but "
                      f"--drawdown-from-high-pct not supplied -- severity not evaluated")

    print(json.dumps({"ticker": a.ticker.upper(), "cik": cik,
                      "lookback_days": a.lookback_days, "filings_scanned": len(filings),
                      "transactions": all_tx, "findings": findings,
                      "distinct_sellers": distinct_sellers, "distinct_buyers": distinct_buyers,
                      "data_quality": dq}, indent=1))


# ---------------------------------------------------------------------------
# Institutional ownership (Form 13F) -- detection logic only, see module note above
# ---------------------------------------------------------------------------

def cmd_institutional_flow(a):
    """Deterministic QoQ institutional flow read from a PRE-FETCHED positions file (FMP
    `form13F` positions-summary shape, or any source keyed the same way) -- this command does
    not fetch 13F data itself (see the module note above). --positions-json: a JSON object
    with "current" and "prior" quarter arrays, each row carrying at least
    {"investor_name", "shares"}. Net share change across the top --top-n holders by current
    shares classifies the flow; a holder present in one quarter and absent in the other counts
    as a full exit/new entry, not silently dropped."""
    try:
        with open(a.positions_json) as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        data = None
    if not isinstance(data, dict) or "current" not in data or "prior" not in data:
        print(json.dumps({"error": f"--positions-json must be {{'current':[...], 'prior':[...]}}, "
                                    f"got: {a.positions_json}"}))
        return
    cur = sorted(data["current"], key=lambda r: -(r.get("shares") or 0))[:a.top_n]
    prior_by_name = {r.get("investor_name"): r.get("shares") or 0 for r in data.get("prior", [])}
    rows, net_change = [], 0
    for r in cur:
        name, shares_now = r.get("investor_name"), r.get("shares") or 0
        shares_prior = prior_by_name.pop(name, 0)
        delta = shares_now - shares_prior
        net_change += delta
        rows.append({"investor_name": name, "shares_current": shares_now,
                    "shares_prior": shares_prior, "delta_shares": delta,
                    "status": "new_entry" if shares_prior == 0 else
                              "full_exit" if shares_now == 0 else
                              "increased" if delta > 0 else "decreased" if delta < 0 else "unchanged"})
    exits = [{"investor_name": n, "shares_prior": s, "delta_shares": -s}
            for n, s in prior_by_name.items() if s > 0]
    total_current = sum(r["shares_current"] for r in rows) or 1
    flow = "institutional_distribution" if net_change < 0 else \
           "institutional_accumulation" if net_change > 0 else "flat"
    print(json.dumps({"ticker": a.ticker.upper() if a.ticker else None, "top_n": a.top_n,
                      "rows": rows, "exited_top_holders": exits,
                      "net_share_change": net_change, "flow": flow,
                      "net_change_pct_of_current": round(net_change / total_current * 100, 2)},
                     indent=1))


def main():
    global _BASE_DIR
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base-dir", default=".",
                   help="where edgar_cache.json lives/gets written (default: cwd)")
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

    ic = sub.add_parser("insider-cluster",
                        help="Form 4 cluster detection: insiders selling into a rally, or "
                             "buying a severe drawdown -- free EDGAR source, no FMP plan needed")
    ic.add_argument("--ticker", required=True)
    ic.add_argument("--lookback-days", type=int, default=30)
    ic.add_argument("--max-filings", type=int, default=20)
    ic.add_argument("--min-sellers", type=int, default=3)
    ic.add_argument("--min-buyers", type=int, default=2)
    ic.add_argument("--near-high-pct", type=float, default=5.0)
    ic.add_argument("--severe-drawdown-pct", type=float, default=15.0)
    ic.add_argument("--price-usd", type=float, default=None)
    ic.add_argument("--wk52-high-usd", type=float, default=None)
    ic.add_argument("--drawdown-from-high-pct", type=float, default=None)
    ic.set_defaults(fn=cmd_insider_cluster)

    inst = sub.add_parser("institutional-flow",
                          help="QoQ institutional ownership flow from a pre-fetched 13F "
                               "positions file (detection logic only -- see module note; "
                               "needs a data source, this repo has none free yet)")
    inst.add_argument("--ticker", default=None)
    inst.add_argument("--positions-json", required=True)
    inst.add_argument("--top-n", type=int, default=10)
    inst.set_defaults(fn=cmd_institutional_flow)

    a = p.parse_args()
    _BASE_DIR = a.base_dir
    a.fn(a)


if __name__ == "__main__":
    main()
