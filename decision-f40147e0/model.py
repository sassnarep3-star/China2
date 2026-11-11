#!/usr/bin/env python3
"""Recompute every cost cell in decision-f40147e0 from published inputs.

Inputs (read, never invented):
  * data/sources.json  - the pages read on 2026-11-11, with the exact words used
  * data/methods.json  - per-method pricing spec (selling rate, fee formula, cap)

Output:
  * data/costs.json    - 40 tiers x priced methods, plus the meta block

Rules enforced here:
  * no method without a published selling rate and a published fee formula is priced;
  * a tier above a method's published ceiling is marked, not priced;
  * the reference mid is arithmetic on the readable boards and is labelled as such;
  * every derived number is a pure function of the inputs above.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

SOURCES = {s["id"]: s for s in json.loads((DATA / "sources.json").read_text())}
METHODS = json.loads((DATA / "methods.json").read_text())

TIERS = list(range(10_000, 400_001, 10_000))
IRS_2025_YUAN_PER_USD = 7.129  # S18, China row, 2025 column
RUN_DATE = "2026-11-11"  # fixed so the CI rebuild is byte-identical on any later day


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def sale_cell(usd: float, spec: dict) -> dict:
    """One tier for one priced method. Pure arithmetic on published inputs."""
    ref = spec["ref"]
    cny = usd * ref
    spread_usd = usd * (spec["sell"] / ref - 1.0)
    fee_cny = clamp(spec["fee_pct"] * cny, spec["fee_min"], spec["fee_max"]) + spec["cable"]
    fee_usd = fee_cny / ref
    total = spread_usd + fee_usd
    return {
        "usd": usd,
        "cny": round(cny, 2),
        "spread_usd": round(spread_usd, 2),
        "fee_cny": round(fee_cny, 2),
        "fee_usd": round(fee_usd, 2),
        "total_usd": round(total, 2),
        "pct": round(total / usd * 100, 4),
        "spread_pct": round((spec["sell"] / ref - 1.0) * 100, 4),
    }


def build() -> dict:
    priced, unpriced, blocked = [], [], []

    for m in METHODS:
        if m["pricing"] is None:
            (unpriced if m["status"] in {"lawful", "conditional", "unverified"} else blocked).append(m["id"])
            continue
        priced.append(m["id"])

    rows = []
    for m in METHODS:
        spec = m.get("pricing")
        if spec is None:
            continue
        for usd in TIERS:
            cap = m.get("cap_usd")
            if cap is not None and usd > cap:
                rows.append({
                    "method": m["id"], "usd": usd,
                    "state": "above-published-ceiling",
                    "ceiling_usd": cap,
                    "note": m.get("ceiling_note")
                    or f"Published ceiling is USD {cap:,.0f}; this tier is not reachable in one transaction.",
                })
                continue
            cell = sale_cell(usd, spec)
            cell.update({"method": m["id"], "state": "priced"})
            rows.append(cell)

    # Per-method headline cells, using only tiers that are actually priced.
    by_method = {}
    for r in rows:
        by_method.setdefault(r["method"], []).append(r)

    headline = {}
    for mid, cells in by_method.items():
        headline[mid] = {}
        for usd in (10_000, 50_000, 100_000, 200_000, 400_000):
            hit = next((c for c in cells if c["usd"] == usd), None)
            if hit and hit["state"] == "priced":
                headline[mid][str(usd)] = {
                    "total_usd": hit["total_usd"], "pct": hit["pct"],
                    "spread_usd": hit["spread_usd"], "fee_usd": hit["fee_usd"],
                }
            else:
                headline[mid][str(usd)] = None

    # Ranking at USD 100,000 over priced methods only.
    ranking = sorted(
        (
            {"method": mid, "total_usd": headline[mid]["100000"]["total_usd"],
             "pct": headline[mid]["100000"]["pct"]}
            for mid in headline
            if headline[mid].get("100000")
        ),
        key=lambda r: r["total_usd"],
    )

    ref_used = next(m["pricing"]["ref"] for m in METHODS if m.get("pricing"))

    # Illustrative section 988 exchange result: the CNY converted now, if acquired at the
    # IRS 2025 yearly average, cost fewer dollars than the proceeds. Labelled illustrative.
    illus = []
    for usd in (10_000, 100_000, 400_000):
        basis_usd = usd * ref_used / IRS_2025_YUAN_PER_USD
        illus.append({
            "usd": usd,
            "basis_usd": round(basis_usd, 2),
            "gain_usd": round(usd - basis_usd, 2),
            "gain_pct": round((1 - ref_used / IRS_2025_YUAN_PER_USD) * 100, 4),
        })

    meta = {
        "generated": RUN_DATE,
        "ref_mid": ref_used,
        "ref_mid_basis": "arithmetic mean of the three readable bank mids (BOC 6.67705, CMB 6.67747, HSBC 6.6745513); SAFE parity could not be read (F01)",
        "irs_2025_yuan_per_usd": IRS_2025_YUAN_PER_USD,
        "formula": "total = amount x (selling rate / reference mid - 1) + clamp(0.1% x CNY amount, floor, cap) + cable / reference mid",
        "tier_count": len(TIERS),
        "priced_methods": [m["id"] for m in METHODS if m.get("pricing")],
        "unpriced_methods": [m["id"] for m in METHODS if not m.get("pricing")],
        "row_count": len(rows),
        "priced_rows": sum(1 for r in rows if r["state"] == "priced"),
        "ceiling_rows": sum(1 for r in rows if r["state"] != "priced"),
        "boards_read": {
            "BOC": {"retrieved": "2026-11-11 10:25:02 Beijing", "buy": 6.6630, "sell": 6.6911, "src": "S01"},
            "CMB": {"retrieved": "2026-11-11 10:28:44 (page dated 2026-11-10)", "buy": 6.66295, "sell": 6.69199, "src": "S03"},
            "HSBC": {"retrieved": "2026-11-11 (page updated 2026-11-10)", "buy": 6.6411822, "sell": 6.7079204, "src": "S05"},
        },
    }

    return {
        "meta": meta,
        "headline": headline,
        "ranking_100k": ranking,
        "illustrative_988": illus,
        "tiers": TIERS,
        "rows": rows,
    }


def write_exports(payload: dict) -> None:
    """CSV and JSON of every cell, with the two official URLs behind each priced row."""
    import csv

    methods = {m["id"]: m for m in METHODS}
    out = ROOT / "exports"
    out.mkdir(exist_ok=True)
    cols = ["method", "method_name", "amount_usd", "state", "cny_converted", "spread_cost_usd",
            "fee_cny", "fee_usd", "all_in_usd", "all_in_pct", "rate_source", "rate_url",
            "fee_source", "fee_url"]
    with (out / "cost-ladder.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for r in payload["rows"]:
            m = methods[r["method"]]
            spec = m.get("pricing") or {}
            w.writerow([
                r["method"], m["name"], r["usd"], r["state"],
                r.get("cny", ""), r.get("spread_usd", ""), r.get("fee_cny", ""),
                r.get("fee_usd", ""), r.get("total_usd", ""), r.get("pct", ""),
                spec.get("rate_src", ""), SOURCES[spec["rate_src"]]["url"] if spec.get("rate_src") in SOURCES else "",
                spec.get("fee_src", ""), SOURCES[spec["fee_src"]]["url"] if spec.get("fee_src") in SOURCES else "",
            ])
    (out / "cost-ladder.json").write_text(json.dumps(payload, indent=1) + "\n")


def main() -> None:
    payload = build()
    (DATA / "costs.json").write_text(json.dumps(payload, indent=1) + "\n")
    write_exports(payload)
    m = payload["meta"]
    print(f"tiers={m['tier_count']} rows={m['row_count']} priced={m['priced_rows']} "
          f"ceiling={m['ceiling_rows']} ref_mid={m['ref_mid']}")
    for r in payload["ranking_100k"]:
        print(f"  ${r['total_usd']:>9,.2f}  {r['pct']:.3f}%  {r['method']}")


if __name__ == "__main__":
    main()
