"""
In-process SDK MCP server standing in for the mcp__yfinance__* connector.

Named "yfinance" deliberately — every subagent prompt already calls tools
named mcp__yfinance__get_stock_price etc. (see /Users/yb/.claude/agents/
smith-*.md), so matching the server name here means those prompts run
unmodified. Only the subset actually exercised by a QUICK-mode run is
implemented; the rest of the mcp__yfinance__* surface (get_options,
get_recommendations, get_screener, ...) follows the same pattern and can
be added on demand — see the stubs at the bottom for how.

Requires: pip install yfinance
"""

from __future__ import annotations

import asyncio
from typing import Annotated, Any

import yfinance as yf
from claude_agent_sdk import create_sdk_mcp_server, tool


def _err(msg: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": msg}], "is_error": True}


def _ok(text: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": text}]}


@tool(
    "get_stock_price",
    "Returns current price, change, market cap, and volume for one or more symbols.",
    {"symbols": Annotated[str, "Space-separated symbols, e.g. 'AAPL MSFT'"]},
)
async def get_stock_price(args: dict[str, Any]) -> dict[str, Any]:
    symbols = args["symbols"].split()

    def fetch() -> dict[str, Any]:
        out: dict[str, Any] = {}
        for sym in symbols:
            t = yf.Ticker(sym)
            info = t.fast_info
            out[sym] = {
                "symbol": sym,
                "price": info.get("lastPrice"),
                "prevClose": info.get("previousClose"),
                "open": info.get("open"),
                "dayHigh": info.get("dayHigh"),
                "dayLow": info.get("dayLow"),
                "volume": info.get("lastVolume"),
                "marketCap": info.get("marketCap"),
                "currency": info.get("currency"),
            }
            if out[sym]["price"] and out[sym]["prevClose"]:
                out[sym]["change"] = out[sym]["price"] - out[sym]["prevClose"]
                out[sym]["changePct"] = out[sym]["change"] / out[sym]["prevClose"]
        return out

    try:
        result = await asyncio.to_thread(fetch)
    except Exception as e:  # noqa: BLE001 — surfaced to the model as a tool error
        return _err(f"yfinance fetch failed: {e}")
    import json

    return _ok(json.dumps(result))


@tool(
    "get_stock_history",
    "Historical OHLCV with optional stats. period: 1d/5d/1mo/3mo/6mo/1y/2y/5y/10y/ytd/max. "
    "interval: 1d/1wk/1mo etc.",
    {
        "symbols": Annotated[str, "Space-separated symbols"],
        "period": Annotated[str, "e.g. '1mo', '6mo'"],
        "interval": Annotated[str, "e.g. '1d', '1wk'"],
    },
)
async def get_stock_history(args: dict[str, Any]) -> dict[str, Any]:
    symbols = args["symbols"].split()
    period = args.get("period", "1mo")
    interval = args.get("interval", "1d")

    def fetch() -> dict[str, Any]:
        out: dict[str, Any] = {}
        for sym in symbols:
            hist = yf.Ticker(sym).history(period=period, interval=interval)
            rows = [
                {
                    "date": idx.strftime("%Y-%m-%d"),
                    "open": round(float(r["Open"]), 4),
                    "high": round(float(r["High"]), 4),
                    "low": round(float(r["Low"]), 4),
                    "close": round(float(r["Close"]), 4),
                    "volume": int(r["Volume"]),
                }
                for idx, r in hist.iterrows()
            ]
            out[sym] = {"symbol": sym, "period": period, "rows": rows}
        return out

    try:
        result = await asyncio.to_thread(fetch)
    except Exception as e:  # noqa: BLE001
        return _err(f"yfinance history fetch failed: {e}")
    import json

    return _ok(json.dumps(result))


@tool(
    "search_stocks",
    "Search for stock symbols by company name or ticker fragment.",
    {"query": str, "limit": Annotated[int, "max results, default 10"]},
)
async def search_stocks(args: dict[str, Any]) -> dict[str, Any]:
    query = args["query"]
    limit = args.get("limit", 10)

    def fetch() -> dict[str, Any]:
        results = yf.Search(query, max_results=limit).quotes
        return {
            "count": len(results),
            "quotes": [
                {
                    "symbol": r.get("symbol"),
                    "quoteType": r.get("quoteType"),
                    "exchange": r.get("exchange"),
                    "sector": r.get("sector"),
                    "industry": r.get("industry"),
                }
                for r in results
            ],
        }

    try:
        result = await asyncio.to_thread(fetch)
    except Exception as e:  # noqa: BLE001
        return _err(f"yfinance search failed: {e}")
    import json

    return _ok(json.dumps(result))


yfinance_server = create_sdk_mcp_server(
    name="yfinance",
    version="1.0.0",
    tools=[get_stock_price, get_stock_history, search_stocks],
)

# To add more of the original mcp__yfinance__* surface (get_earnings,
# get_key_stats, get_options, get_recommendations, get_screener, ...):
# 1. Write an @tool()-decorated async function following the pattern above
# 2. Add it to the `tools=[...]` list two lines up
# No other file needs to change — the prompts already reference these
# names and will pick up new tools automatically once registered here.
