"""
In-process SDK MCP server standing in for the mcp__30f6267b-...__* (FMP)
connector.

Unlike the yfinance port, the existing subagent prompts don't hardcode FMP's
literal tool-call names — they describe FMP capabilities in prose ("FMP
`secFilings` for...", "FMP `insiderTrades` and `form13F`..."), so there's no
regex substitution needed. What matters is that a server named "fmp" exists
with tools whose names/descriptions match what the prose already promises.

Grep across the QUICK-mode subagent set (smith-book/signals/thesis/watchlist
+ strategist) found `secFilings` as the only FMP dependency that isn't
explicitly deep-mode-gated, so that's implemented as a real wrapper against
FMP's documented `stable` API. Everything else FMP-shaped (insiderTrades,
form13F, etfAndMutualFunds, statements, ...) goes through `fmp_raw`, a
generic passthrough — deliberately not a guess at 20+ endpoint shapes I
haven't verified. Add a dedicated wrapper the same way as quote/secFilings
once a specific endpoint is confirmed working.

Requires: FMP_API_KEY env var (free tier: financialmodelingprep.com/pricing-plans)
"""

from __future__ import annotations

import json
import os
from typing import Annotated, Any

import httpx
from claude_agent_sdk import create_sdk_mcp_server, tool

FMP_BASE = "https://financialmodelingprep.com/stable"


def _api_key() -> str:
    key = os.environ.get("FMP_API_KEY")
    if not key:
        raise RuntimeError(
            "FMP_API_KEY not set — get a free key at "
            "https://site.financialmodelingprep.com/pricing-plans and export it"
        )
    return key


def _err(msg: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": msg}], "is_error": True}


def _ok(payload: Any) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": json.dumps(payload)}]}


async def _get(path: str, params: dict[str, Any]) -> Any:
    params = {**params, "apikey": _api_key()}
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(f"{FMP_BASE}/{path.lstrip('/')}", params=params)
        resp.raise_for_status()
        return resp.json()


@tool(
    "quote",
    "Real-time quote for one symbol: price, change, volume, market cap, day range.",
    {"symbol": str},
)
async def quote(args: dict[str, Any]) -> dict[str, Any]:
    try:
        data = await _get("quote", {"symbol": args["symbol"]})
    except Exception as e:  # noqa: BLE001
        return _err(f"FMP quote failed: {e}")
    return _ok(data)


@tool(
    "secFilings",
    "Search a symbol's SEC filings by form type / date range. Metadata only "
    "(no full filing text) — matches the 'search-by-symbol' recipe step "
    "used by smith-thesis for reported-vs-guide verification.",
    {
        "symbol": str,
        "formType": Annotated[str, "e.g. '10-Q', '8-K' — omit for all types"],
        "from_date": Annotated[str, "YYYY-MM-DD, optional"],
        "to_date": Annotated[str, "YYYY-MM-DD, optional"],
    },
)
async def sec_filings(args: dict[str, Any]) -> dict[str, Any]:
    params: dict[str, Any] = {"symbol": args["symbol"]}
    if args.get("formType"):
        params["formType"] = args["formType"]
    if args.get("from_date"):
        params["from"] = args["from_date"]
    if args.get("to_date"):
        params["to"] = args["to_date"]
    try:
        data = await _get("sec-filings-search/symbol", params)
    except Exception as e:  # noqa: BLE001
        return _err(f"FMP secFilings failed: {e}")
    return _ok(data)


@tool(
    "fmp_raw",
    "Generic passthrough to any FMP 'stable' API endpoint not yet given a "
    "dedicated tool (insider-trading, form 13F, etf-holdings, financial "
    "statements, etc). Pass the endpoint path exactly as FMP documents it "
    "(e.g. 'insider-trading/search', 'institutional-ownership/symbol-holders'), "
    "plus its query params as a flat object. apikey is added automatically.",
    {"path": str, "params": Annotated[dict, "query params, e.g. {'symbol': 'MU'}"]},
)
async def fmp_raw(args: dict[str, Any]) -> dict[str, Any]:
    try:
        data = await _get(args["path"], args.get("params") or {})
    except Exception as e:  # noqa: BLE001
        return _err(f"FMP {args['path']} failed: {e}")
    return _ok(data)


fmp_server = create_sdk_mcp_server(
    name="fmp",
    version="1.0.0",
    tools=[quote, sec_filings, fmp_raw],
)
