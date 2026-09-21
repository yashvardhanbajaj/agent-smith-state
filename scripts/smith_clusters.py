"""Fluid clusters (2026-09-21). User decision: clusters exist to GROUP holdings and show the exposure
inside each group; they are not a fixed policy fence. The desk may create, rename, retarget or retire
any cluster on its own authority, and every change carries a rationale.

Precedence for what a run sees (`overlay`):
  policy.cluster_targets  = SEEDS (defaults, never required)
  state.cluster_book      = the desk's live layer; a record here overrides the seed, and
                            {"removed": true} retires a seed's target (the cluster stays as an
                            exposure-only group while any ticker maps to it)
A cluster with no target is reported as exposure only -- it can never breach, and that is now a
stated state, not a defect. Any string a ticker is mapped to IS a cluster; no registration step.
Pure: no I/O except `write_*`, which take/return plain dicts."""
import copy
import re

AI_CAPEX_DEFAULT_FLAG = False
GENERIC_DIFFERENTIATORS = [
    "which member captures the most of the cluster's shared demand driver, and whether that share is rising",
    "balance-sheet and margin resilience if the shared driver slows",
    "valuation versus growth relative to the other members",
    "customer or supplier concentration that the other members do not share",
]


def default_band(target_pct):
    """+/- max(3pt, half the target), floored at 0. Used only when the desk sets a target without a band."""
    t = float(target_pct)
    half = max(3.0, round(t * 0.5, 1))
    return [max(0.0, round(t - half, 1)), round(t + half, 1)]


def slugify(cluster):
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", str(cluster).lower())).strip("_")


def overlay(policy, state):
    """Effective policy for cluster purposes: a deep-enough copy with cluster_targets,
    ai_capex_clusters and cluster_playbooks resolved from seeds + state.cluster_book + sector_map.
    Never mutates its inputs. Returns `policy` unchanged when it is None."""
    if not isinstance(policy, dict):
        return policy
    state = state or {}
    book = state.get("cluster_book") or {}
    out = dict(policy)
    targets = {k: dict(v) for k, v in (policy.get("cluster_targets") or {}).items() if isinstance(v, dict)}
    ai = list(policy.get("ai_capex_clusters") or [])
    for name, rec in book.items():
        if not isinstance(rec, dict):
            continue
        if rec.get("removed"):
            targets.pop(name, None)      # retiring a target never changes factor membership
            if rec.get("ai_capex") is False and name in ai:
                ai.remove(name)
            elif rec.get("ai_capex") is True and name not in ai:
                ai.append(name)
            continue
        if rec.get("target_pct") is not None:
            band = rec.get("band_pct") or default_band(rec["target_pct"])
            base = targets.get(name, {})
            base.update(target_pct=rec["target_pct"], band_pct=band, source="desk",
                        rationale=rec.get("rationale"), set_on=rec.get("set_on"))
            targets[name] = base
        if rec.get("ai_capex") is True and name not in ai:
            ai.append(name)
        if rec.get("ai_capex") is False and name in ai:
            ai.remove(name)
    for name in targets:
        targets[name].setdefault("source", "policy")
    out["cluster_targets"] = targets
    out["ai_capex_clusters"] = ai
    pbs = dict(policy.get("cluster_playbooks") or {})
    used = {v.get("slug") for v in pbs.values() if isinstance(v, dict)}
    for name in sorted({c for c in (state.get("sector_map") or {}).values() if c} | set(targets)):
        if name in pbs:
            continue
        slug = slugify(name)
        while slug in used:
            slug += "_x"
        used.add(slug)
        pbs[name] = {"slug": slug, "generated": True, "differentiators": list(GENERIC_DIFFERENTIATORS),
                     "read_throughs": []}
    out["cluster_playbooks"] = pbs
    return out


def exposure(sector_map, weights):
    """{cluster: {"tickers": [...], "weight_pct": x}} from a ticker->cluster map and ticker->weight."""
    out = {}
    for t, w in weights.items():
        c = (sector_map or {}).get(t, "Unclassified")
        e = out.setdefault(c, {"tickers": [], "weight_pct": 0.0})
        e["tickers"].append(t)
        e["weight_pct"] = round(e["weight_pct"] + (w or 0.0), 3)
    return out


def set_cluster(state, cluster, today, rationale, target_pct=None, band_pct=None, ai_capex=None,
                remove_target=False, by="desk"):
    """Create/modify a cluster's desk record in state.cluster_book. Returns the record written."""
    if not str(cluster or "").strip():
        raise ValueError("cluster name required")
    if not str(rationale or "").strip():
        raise ValueError("a rationale is required for every cluster change")
    if remove_target and target_pct is not None:
        raise ValueError("--remove-target and --target are mutually exclusive")
    if target_pct is not None:
        target_pct = float(target_pct)
        if not 0 <= target_pct <= 100:
            raise ValueError("target must be within 0-100")
        band_pct = [float(band_pct[0]), float(band_pct[1])] if band_pct else default_band(target_pct)
        if band_pct[0] > band_pct[1] or not band_pct[0] <= target_pct <= band_pct[1]:
            raise ValueError(f"target {target_pct:g} must sit inside band {band_pct}")
    book = state.setdefault("cluster_book", {})
    prev = book.get(cluster) or {}
    rec = {k: v for k, v in prev.items() if k != "history"}
    if remove_target:
        rec.update(removed=True)
        rec.pop("target_pct", None); rec.pop("band_pct", None)
    elif target_pct is not None:
        rec.update(target_pct=target_pct, band_pct=band_pct)
        rec.pop("removed", None)
    if ai_capex is not None:
        rec["ai_capex"] = bool(ai_capex)
    rec.update(rationale=rationale, set_on=str(today), set_by=by)
    hist = list(prev.get("history") or [])
    hist.append({k: prev.get(k) for k in ("target_pct", "band_pct", "removed", "ai_capex", "rationale", "set_on")})
    rec["history"] = hist[-20:]
    book[cluster] = rec
    return rec


def assign_ticker(state, ticker, cluster, today, rationale):
    """Point a ticker at a cluster (creating the group implicitly). Returns the previous cluster."""
    if not str(rationale or "").strip():
        raise ValueError("a rationale is required for every reassignment")
    sm = state.setdefault("sector_map", {})
    prev = sm.get(ticker)
    sm[ticker] = cluster
    log = state.setdefault("cluster_assignments_log", [])
    log.append({"ticker": ticker, "from": prev, "to": cluster, "on": str(today), "rationale": rationale})
    del log[:-100]
    return prev
