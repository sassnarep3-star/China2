#!/usr/bin/env python3
"""Cost engine for the consolidated guide.

Reads guide/data/methods.json and guide/data/sources.json, computes the
$10,000-to-$400,000 ladder for every method that has a published fee plus the
one labelled spread assumption, and writes guide/data/costs.json.

Rules, deliberately strict:
  * A method is costed ONLY if its fee type is pct_minmax, flat_usd or zero.
  * Any 'unverified' fee type stays null at every tier - never estimated.
  * The spread percentage comes from one source (a same-day published board
    rate) and is applied uniformly; it is labelled as an assumption everywhere
    it appears.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

RATE = 7.10           # CNY per USD, only to express CNY-denominated fees
TIERS = list(range(10_000, 400_001, 10_000))


def load(name: str):
    return json.loads((DATA / name).read_text())


def money(x: float | None) -> float | None:
    return None if x is None else round(x, 2)


def fee_usd(cost: dict, principal: float) -> float | None:
    fee = cost["fee"]
    t = fee["type"]
    if t == "zero":
        return 0.0
    if t == "flat_usd":
        return float(fee["usd"])
    if t == "pct_minmax":
        raw = fee["pct"] * principal
        lo = fee["min_cny"] / RATE
        hi = fee["max_cny"] / RATE
        capped = min(max(raw, lo), hi)
        return capped + fee.get("cable_cny", 0) / RATE + fee.get("flat_usd", 0)
    return None


def build() -> dict:
    methods = load("methods.json")
    sources = load("sources.json")
    meta = methods["meta"]

    source_ids = {s["id"] for s in sources["sources"]}
    for m in methods["methods"]:
        assert m["basis"], m["id"]
        for sid in m["basis"]:
            assert sid in source_ids, f"{m['id']}: unknown source {sid}"
        for sid in m["cost"].get("cost_sources", []):
            assert sid in source_ids, f"{m['id']}: unknown cost source {sid}"

    rows = []
    for m in methods["methods"]:
        cost = m["cost"]
        for tier in TIERS:
            f = fee_usd(cost, tier)
            spread_pct = cost["spread"]["pct"]
            spread = None if spread_pct is None else tier * spread_pct / 100
            total = None if (f is None or spread is None) else f + spread
            over_cap = bool(cost["annual_cap_usd"]) and tier > cost["annual_cap_usd"]
            rows.append({
                "method": m["id"],
                "name": m["short"],
                "status": m["status"],
                "tier": tier,
                "fee_usd": money(f),
                "spread_pct": spread_pct,
                "spread_usd": money(spread),
                "total_usd": money(total),
                "pct_of_principal": None if total is None else round(total / tier * 100, 3),
                "over_annual_cap": over_cap,
                "annual_cap_usd": cost["annual_cap_usd"],
                "per_tx_cap_usd": cost["per_tx_cap_usd"],
            })

    # A method counts as costed only if EVERY tier produced a number; otherwise
    # its cells are blank on the site and it is listed on flagged.html.
    all_ids = [m["id"] for m in methods["methods"]]
    complete = sorted({r["method"] for r in rows if r["total_usd"] is not None})
    costed = [i for i in all_ids if i in complete]
    unverified = [i for i in all_ids if i not in complete]

    out = {
        "meta": {
            "title": "Cost ladder: every $10,000 step from $10,000 to $400,000",
            "generated": meta["retrieved"],
            "rate_cny_per_usd": RATE,
            "rate_assumption": meta["rate_assumption"],
            "spread_assumption": meta["spread_assumption"],
            "tiers": TIERS,
            "tier_count": len(TIERS),
            "method_count": len(methods["methods"]),
            "costed_method_count": len(costed),
            "costed_methods": costed,
            "unverified_methods": unverified,
            "row_count": len(rows),
            "policy": "fee_usd and spread_usd are separate so every number can be recomputed by hand. total_usd = fee_usd + spread_usd. A null cell means no published figure exists: it is blank on the site and listed on flagged.html, never filled by inference.",
            "formula": "fee = clamp(0.001 x principal, 100/7.10, 500/7.10) + 120/7.10 + flat_usd; spread = principal x 0.419/100; total = fee + spread",
        },
        "rows": rows,
    }
    (DATA / "costs.json").write_text(json.dumps(out, indent=1) + "\n")

    # A plain CSV for spreadsheet review, one row per method and tier.
    lines = ["method,name,status,tier_usd,fee_usd,spread_pct,spread_usd,total_usd,pct_of_principal,over_annual_cap"]
    for r in rows:
        lines.append(",".join([
            r["method"], '"' + r["name"].replace('"', "'") + '"', r["status"], str(r["tier"]),
            "" if r["fee_usd"] is None else f'{r["fee_usd"]:.2f}',
            "" if r["spread_pct"] is None else f'{r["spread_pct"]:.3f}',
            "" if r["spread_usd"] is None else f'{r["spread_usd"]:.2f}',
            "" if r["total_usd"] is None else f'{r["total_usd"]:.2f}',
            "" if r["pct_of_principal"] is None else f'{r["pct_of_principal"]:.3f}',
            "yes" if r["over_annual_cap"] else "no",
        ]))
    (DATA / "costs.csv").write_text("\n".join(lines) + "\n")

    print(f"costs.json: {len(rows)} rows, {len(costed)} costed methods, "
          f"{len(unverified)} unverified methods, {len(TIERS)} tiers")
    return out


if __name__ == "__main__":
    build()
