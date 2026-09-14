#!/usr/bin/env python3
"""Evidence audit — catch qualitative claims that lost a side, or that drive money unverified.

WHY THIS EXISTS (G58, 2026-08-10). Agent Smith's compute layer hardens *numbers*: weights,
drift, concentration and drawdown all travel a source-of-truth spine with a gate at every
joint. A *qualitative* claim passed exactly one gate — a JSON parser — and then became a sized
dollar proposal. That failed twice in eight days:

  * G44 — smith-quality reported an MRVL interest-coverage "collapse" (8.1x -> 1.4x). The
    arithmetic was reproducible; MRVL's own 10-Q showed the feed had bucketed a one-time
    acquisition-financing charge as run-rate interest. It drove a strategist veto and a trim.
  * G58 — smith-thesis called SanDisk's FQ4 "a real demand-guide miss". It was a BEAT; only the
    forward guide was light. It drove a sized trim and led the briefing.

G58's root cause was NOT a bad reading. The agent's prose said, correctly, "rev guide missed
DESPITE Q4 EPS beat" — and its own JSON tail compressed that to "rev guide miss". The
countervailing half died at serialization, and every downstream hop inherited the one-sided
version. The same run dropped the *negative* half on INTC and ASML, so the loss is not
directionally biased: whichever clause is subordinate in the prose is the one at risk.

This script is the standing, repeatable version of the hand audit that found those three. Run
it after any deep sweep. It is read-only and stdlib-only, consistent with the compute-first
split: fetching and judging are the orchestrator's job, arithmetic and checking are the
script's.

CHECKS
  1. one-sided        — a migrated thesis entry whose evidence_against (or _for) is empty.
                        Empty is legal, but it must be DELIBERATE, so this reports rather than
                        fails: a genuinely uncontested thesis is a real thing.
  2. unmigrated       — a held name still on the legacy bare-string schema. These cannot carry
                        provenance at all and are treated as unverified everywhere.
  3. dropped-clause   — the actual G58 detector. Scans the run's smith-thesis PROSE output for
                        contrastive markers (despite / however / but / mixed / offset by) and
                        flags any name whose prose is two-sided while its persisted entry is
                        not. This is the exact signature of the original failure.
  4. money-unverified — an open proposal whose only support is unverified qualitative claims
                        (mirrors cmd_proposals' typed gate, reported here for visibility).

Exit code is 0 unless --strict is passed, in which case any check-3 hit (a genuinely dropped
clause) exits 1 — suitable for wiring into a run as a hard gate later.

Usage:
  smith_evidence_audit.py --base-dir /Users/yb/Claude/AgentSmith [--run-dir runs/<ts>] [--strict]
"""
import argparse
import json
import os
import re
import sys

# Contrastive markers: prose containing these is making a two-sided claim. Deliberately narrow --
# "but" and "however" are common enough that a looser list would flag most sentences.
CONTRAST = re.compile(
    r'\b(despite|however|but |mixed[:,]|offset by|although|though |even as|whereas|'
    r'on the other hand|that said|counterpoint|not resolved|un-escalated)\b', re.I)

# A LEGACY bare string can still be two-sided in prose form ("growth vs royalty overhang"), it
# just can't separate the sides structurally. Flagging every such name as a "dropped clause"
# would bury the real hits under the whole unmigrated book -- and a noisy detector gets ignored,
# which is how the original bug survived. So legacy strings are tested with a WIDER contrastive
# vocabulary (adding "vs", "not X", "weak ... win"), and only count as dropped when the prose was
# two-sided and the persisted string retains no counterpoint at all. That is the true G58
# signature: a countervailing clause present upstream and absent downstream.
CONTRAST_LOOSE = re.compile(
    r'(\bvs\.?\b|\bversus\b|\bdespite\b|\bhowever\b|\bbut\b|\bmixed\b|\boffset\b|\balthough\b|'
    r'\bthough\b|\bwhereas\b|\bnot resolved\b|\bun-escalated\b|\boverhang\b|\bwhile\b|'
    r'\bnot broken\b|\bnot a\b|\bstill\b|\bcorrected\b|—\s*trimmed|\bconcern\b)', re.I)


def load(path, default=None):
    try:
        with open(path) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-dir", default=".")
    ap.add_argument("--run-dir", default=None,
                    help="run directory holding smith-thesis-output.md; defaults to state.last_run_dir")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if a dropped countervailing clause is detected")
    a = ap.parse_args()

    state = load(os.path.join(a.base_dir, "state.json"), {})
    if not state:
        print(json.dumps({"error": "state.json unreadable"}))
        return 1

    thesis = state.get("thesis") or {}
    held = {h["ticker"] for h in state.get("holdings") or [] if h.get("ticker")}

    one_sided, unmigrated, migrated = [], [], []
    for tk in sorted(held):
        v = thesis.get(tk)
        if v is None:
            continue
        if not isinstance(v, dict):
            unmigrated.append(tk)
            continue
        migrated.append(tk)
        ef, ea = v.get("evidence_for"), v.get("evidence_against")
        if ef is None or ea is None:
            one_sided.append({"ticker": tk, "issue": "missing evidence key entirely (schema violation)"})
        elif not ea:
            one_sided.append({"ticker": tk, "issue": "evidence_against empty",
                              "verified": v.get("verified")})
        elif not ef:
            one_sided.append({"ticker": tk, "issue": "evidence_for empty",
                              "verified": v.get("verified")})

    # -- check 3: the real G58 detector, prose vs persisted --
    run_dir = a.run_dir or state.get("last_run_dir") or ""
    prose_path = os.path.join(a.base_dir, run_dir, "smith-thesis-output.md")
    dropped, prose_note = [], None
    if os.path.exists(prose_path):
        with open(prose_path) as fh:
            for line in fh:
                m = re.match(r'\s*([A-Z]{1,5})\s+[—-]', line)
                if not m:
                    continue
                tk = m.group(1)
                if tk not in held or not CONTRAST.search(line):
                    continue
                v = thesis.get(tk)
                if isinstance(v, dict):
                    # migrated: the schema can hold both sides, so require it actually does
                    two_sided = bool(v.get("evidence_for")) and bool(v.get("evidence_against"))
                    shape = "object"
                else:
                    # legacy: can't separate sides structurally, but may still carry a
                    # counterpoint in prose. Only a string with NO counterpoint is a real drop.
                    two_sided = bool(CONTRAST_LOOSE.search(str(v or "")))
                    shape = "legacy-string"
                if not two_sided:
                    hit = CONTRAST.search(line)
                    dropped.append({
                        "ticker": tk,
                        "persisted_shape": shape,
                        "marker_in_prose": hit.group(0).strip(),
                        "prose_excerpt": line.strip()[:260],
                        "persisted": (str(v)[:200] if not isinstance(v, dict) else "(object, a side is empty)"),
                    })
    else:
        prose_note = f"no smith-thesis prose found at {prose_path} -- check 3 skipped"

    # -- check 4: money resting only on unverified qualitative claims --
    props = (load(os.path.join(a.base_dir, "proposals.json"), {}) or {}).get("proposals", [])
    money_unverified = []
    for p in props:
        if p.get("status") != "open":
            continue
        eq = p.get("evidence_quality")
        if isinstance(eq, dict) and (eq.get("verified", 0) + eq.get("computed", 0)) == 0 \
                and eq.get("unverified", 0) > 0:
            money_unverified.append({"id": p.get("id"), "action": p.get("action"),
                                     "size_usd": p.get("size_usd"), "evidence_quality": eq})

    out = {
        "held": len(held),
        "migrated": len(migrated),
        "unmigrated": unmigrated,
        "one_sided": one_sided,
        "dropped_clause": dropped,
        "money_on_unverified": money_unverified,
        "verdict": ("DROPPED CLAUSE DETECTED" if dropped else
                    "clean -- no prose/persisted mismatch"),
    }
    if prose_note:
        out["data_quality"] = [prose_note]
    print(json.dumps(out, indent=2))
    return 1 if (a.strict and dropped) else 0


if __name__ == "__main__":
    sys.exit(main())
