"""
Push notification via ntfy.sh - free, no signup, no APNs/FCM app
registration. A "topic" is just a URL path; anyone who knows the exact
topic string can read your notifications, so treat NTFY_TOPIC as a secret
and pick something long and random (see .env.example), not "agent-smith".

Setup on your phone (one-time): install the free "ntfy" app (iOS/Android),
subscribe to your topic. Nothing else to configure.
"""

from __future__ import annotations

import os

import httpx

NTFY_BASE = "https://ntfy.sh"


def notify(title: str, message: str, priority: str = "default") -> bool:
    """Send a push notification. Returns False (and prints a warning)
    instead of raising, so a notification failure never crashes a sweep
    that otherwise completed successfully."""
    topic = os.environ.get("NTFY_TOPIC")
    if not topic:
        print("NTFY_TOPIC not set - skipping push notification")
        return False

    try:
        resp = httpx.post(
            f"{NTFY_BASE}/{topic}",
            data=message.encode("utf-8"),
            headers={"Title": title, "Priority": priority},
            timeout=10,
        )
        resp.raise_for_status()
        return True
    except Exception as e:  # noqa: BLE001 - notification failure is non-fatal
        print(f"ntfy push failed: {e}")
        return False
