# Phase 0 — Static Dashboard Server

Serves `dashboard.html` from Agent Smith / The Operator / HBM Tracker over
plain HTTP. This process runs **no sweep logic** — it reads whatever file is
on disk at request time, so it stays in sync automatically whenever any of
those agents next regenerate their dashboard.

It has zero Claude Code dependency: `server.py` only needs the `.venv` set
up below. Kill your Claude Code session and this keeps serving.

## Run it

```bash
cd /Users/yb/Claude/AgentSmith/webapp
./.venv/bin/uvicorn server:app --host 0.0.0.0 --port 8420
```

`--host 0.0.0.0` (not `127.0.0.1`) is what makes it reachable from your phone.

## View it

- **On this Mac:** http://localhost:8420
- **On your phone, same Wi-Fi:** http://192.168.1.34:8420
  (this machine's current LAN IP — re-run `ipconfig getifaddr en0` if it
  changes, e.g. after reconnecting to Wi-Fi)
- **Routes:** `/` (index of all three), `/smith`, `/operator`, `/hbm`,
  `/health` (JSON — which dashboards exist and how stale each is)

## Remote access before Phase 1 lands

Phase 1 puts this on a real VPS with a stable URL. Until then, if you want
to check the book from outside your home Wi-Fi, tunnel it:

```bash
brew install ngrok
ngrok http 8420
```

That prints a temporary public URL. Treat it as unauthenticated — anyone
with the link can see your portfolio — so only use it for a quick check
and stop `ngrok` after.

## What this does NOT do

- Doesn't run sweeps. Agent Smith/Operator still generate `dashboard.html`
  the normal way (scheduled task or you asking me to run one).
- Doesn't survive a reboot on its own. Start it manually, or `nohup ... &`
  it, or use `launchctl` if you want it to persist — not set up here.
- No auth. Fine on your home network; not fine on the open internet.

## Stopping it

```bash
lsof -ti:8420 | xargs kill
```
