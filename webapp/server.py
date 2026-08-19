"""
Phase 0: static dashboard server — zero Claude Code dependency.

Serves the dashboard.html files that Agent Smith / The Operator / HBM Tracker
already generate, read fresh from disk on every request. This process does
not run any sweep logic itself; it only exposes the last-generated output
over HTTP so it's reachable from a phone browser instead of requiring an
open Claude Code session.

Run:
    ./.venv/bin/uvicorn server:app --host 0.0.0.0 --port 8420

Then open http://<this-machine's-IP>:8420/ on any device on the same
network (or tunnel it — see README.md for the ngrok one-liner).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

app = FastAPI(title="Portfolio Dashboards")

# name -> path to the dashboard.html that agent already writes
DASHBOARDS: dict[str, Path] = {
    "smith": Path("/Users/yb/Claude/AgentSmith/dashboard.html"),
    "operator": Path("/Users/yb/Claude/TheOperator/dashboard.html"),
    "hbm": Path("/Users/yb/Claude/HBMTracker/dashboard.html"),
}

LABELS = {
    "smith": "Agent Smith — US Portfolio",
    "operator": "The Operator — India Portfolio",
    "hbm": "HBM Price Tracker",
}


def _read_dashboard(key: str) -> str:
    path = DASHBOARDS.get(key)
    if path is None:
        raise HTTPException(status_code=404, detail=f"Unknown dashboard: {key}")
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"{LABELS.get(key, key)} hasn't generated a dashboard yet ({path}).",
        )
    return path.read_text(encoding="utf-8")


@app.get("/health")
def health() -> dict:
    status = {}
    for key, path in DASHBOARDS.items():
        status[key] = {
            "exists": path.exists(),
            "last_modified": (
                datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
                if path.exists()
                else None
            ),
        }
    return {"ok": True, "dashboards": status}


@app.get("/{key}", response_class=HTMLResponse)
def dashboard(key: str) -> str:
    return _read_dashboard(key)


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    rows = []
    for key, path in DASHBOARDS.items():
        if path.exists():
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            age = datetime.now(timezone.utc) - mtime
            hours = age.total_seconds() / 3600
            freshness = f"{hours:.1f}h ago" if hours < 48 else f"{hours / 24:.1f}d ago"
            rows.append(
                f'<li><a href="/{key}">{LABELS[key]}</a> '
                f'<span class="age">— last updated {freshness}</span></li>'
            )
        else:
            rows.append(f'<li class="missing">{LABELS[key]} — not generated yet</li>')

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Portfolio Dashboards</title>
<style>
  :root {{ --bg: #fff; --fg: #1a1a1a; --border: #eee; --muted: #888; --accent: #0a7a45; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg: #111; --fg: #f0f0f0; --border: #2a2a2a; --muted: #999; --accent: #3ecf8e; }}
  }}
  body {{ font-family: -apple-system, system-ui, sans-serif; max-width: 480px;
         margin: 3rem auto; padding: 0 1.25rem; color: var(--fg); background: var(--bg); }}
  h1 {{ font-size: 1.25rem; }}
  ul {{ list-style: none; padding: 0; }}
  li {{ padding: 0.9rem 0; border-bottom: 1px solid var(--border); }}
  a {{ color: var(--accent); text-decoration: none; font-weight: 600; }}
  .age {{ color: var(--muted); font-size: 0.85rem; font-weight: 400; }}
  .missing {{ color: var(--muted); }}
</style>
</head>
<body>
  <h1>Portfolio Dashboards</h1>
  <ul>{''.join(rows)}</ul>
</body>
</html>"""
