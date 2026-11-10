"""Independent structure/arithmetic checks for published cost ladders (session arena/ad300459-china2).

Scope: structure and arithmetic ONLY (row counts, tier sequences, ordering, recomputed
percentages, fee conversions, export parity). This does not verify the real-world
correctness of fees, rates or legal meanings — those are handled (or left blank) in
findings.json / flagged.html.
"""
from __future__ import annotations

import csv
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIERS = [t for t in range(10_000, 400_001, 10_000)]


def _load(path: str):
    with open(os.path.join(ROOT, path), encoding="utf-8") as fh:
        return json.load(fh)


def ladder_checks():
    """Checks on ladder/data/costs.json (600 rows = 15 costed routes x 40 tiers)."""
    results = []
    data = _load("ladder/data/costs.json")
    rows = data.get("rows", [])
    meta = data.get("meta", {})

    results.append(("ladder row count == 600", len(rows) == 600, f"rows={len(rows)}"))
    results.append(
        ("meta.tiers == 40-step sequence", meta.get("tiers") == TIERS,
         f"len={len(meta.get('tiers') or [])}"),
    )

    by_route = {}
    for r in rows:
        by_route.setdefault(r.get("route"), []).append(r)

    results.append(
        ("costed route count == 15", len(by_route) == 15, f"routes={len(by_route)}"),
    )
    results.append(
        ("meta.costed_route_count matches rows",
         meta.get("costed_route_count") == len(by_route),
         f"meta={meta.get('costed_route_count')} rows_routes={len(by_route)}"),
    )

    seq_ok = True
    seq_detail = ""
    for route, rlist in sorted(by_route.items()):
        tiers = [r.get("tier") for r in sorted(rlist, key=lambda x: x.get("tier", 0))]
        if tiers != TIERS:
            seq_ok = False
            seq_detail = f"{route}: {tiers[:5]}...({len(tiers)} tiers)"
            break
    results.append(("each costed route has exactly the 40 tiers in order", seq_ok, seq_detail or "all 15 routes OK"))

    order_ok = True
    order_detail = ""
    for route, rlist in sorted(by_route.items()):
        tiers_in_file = [r.get("tier") for r in rlist]
        if tiers_in_file != TIERS:
            order_ok = False
            order_detail = f"{route} file order differs"
            break
    results.append(("tier rows appear in ascending order within each route", order_ok, order_detail or "in-file order OK"))

    band_ok = True
    pct_ok = True
    fee_ok = True
    band_detail = ""
    pct_detail = ""
    fee_detail = ""
    blank_fee_rows = 0
    for i, r in enumerate(rows):
        try:
            if not (r["spread_lo"] <= r["spread_hi"] and r["total_lo"] <= r["total_hi"]
                    and r["pct_lo"] <= r["pct_hi"]):
                band_ok = False
                band_detail = f"row {i} bands out of order"
            tier = r["tier"]
            if tier > 0:
                for key_total, key_pct in (("total_lo", "pct_lo"), ("total_hi", "pct_hi")):
                    recomputed = round(r[key_total] / tier * 100, 3)
                    if abs(recomputed - r[key_pct]) > 0.02:
                        pct_ok = False
                        pct_detail = f"row {i} {key_pct}: {r[key_pct]} vs {recomputed}"
            # blank policy: null fee is legal ONLY when the model marks it
            # unpublished+partial (unverified stays blank, never zero-filled);
            # published/published-band/none fees must be numeric or an ordered
            # [lo, hi] band and must not claim "unpublished".
            fee = r["fixed_fee"]
            status = r.get("fixed_status")
            if fee is None:
                blank_fee_rows += 1
                if not (status == "unpublished" and r.get("partial") is True):
                    fee_ok = False
                    fee_detail = f"row {i} null fee without unpublished+partial marking"
            elif isinstance(fee, list):
                if not (status == "published-band" and len(fee) == 2
                        and all(isinstance(x, (int, float)) for x in fee)
                        and 0 <= fee[0] <= fee[1]):
                    fee_ok = False
                    fee_detail = f"row {i} bad fee band {fee!r} status={status}"
            elif not isinstance(fee, (int, float)) or fee < 0:
                fee_ok = False
                fee_detail = f"row {i} fixed_fee={fee!r}"
            elif status == "unpublished":
                fee_ok = False
                fee_detail = f"row {i} numeric fee but marked unpublished"
            if not (r["prc_tax_pct_lo"] <= r["prc_tax_pct_hi"]):
                band_ok = False
                band_detail = f"row {i} prc_tax band out of order"
        except (KeyError, TypeError) as exc:  # missing field is a failure
            band_ok = pct_ok = fee_ok = False
            band_detail = pct_detail = fee_detail = f"row {i}: {exc}"
        if not (band_ok and pct_ok and fee_ok):
            break

    results.append(("spread/total/prc-tax bands ordered lo<=hi on every row", band_ok, band_detail or "600/600 rows"))
    results.append(("pct_lo/hi recomputed from total/tier within 0.02pp", pct_ok, pct_detail or "600/600 rows"))
    results.append(("fixed_fee numeric>=0 or blank exactly when marked unpublished+partial",
                    fee_ok, fee_detail or f"600/600 rows OK ({blank_fee_rows} deliberate blanks)"))

    routes_meta_ok = meta.get("route_count") == 20
    results.append(("meta.route_count == 20 (incl. unpublished routes)", routes_meta_ok,
                    f"meta={meta.get('route_count')}"))
    return results


def repatriate_checks():
    """Checks on repatriate/exports/cost-ladders.json (680 rows = 17 methods x 40 amounts)."""
    results = []
    data = _load("repatriate/exports/cost-ladders.json")
    rows = data.get("rows", [])
    meta = data.get("meta", {})
    rate = meta.get("reference_rate_cny_per_usd")

    results.append(("repatriate row count == 680", len(rows) == 680, f"rows={len(rows)}"))
    results.append(("reference rate == 7.129", rate == 7.129, f"rate={rate}"))

    by_method = {}
    for r in rows:
        by_method.setdefault(r.get("method"), []).append(r)
    results.append(("method count == 17", len(by_method) == 17, f"methods={len(by_method)}"))

    seq_ok = True
    seq_detail = ""
    for m, rlist in sorted(by_method.items()):
        amounts = [r.get("amount_usd") for r in sorted(rlist, key=lambda x: x.get("amount_usd", 0))]
        if amounts != TIERS:
            seq_ok = False
            seq_detail = f"{m}: {amounts[:5]}...({len(amounts)})"
            break
        if [r.get("amount_usd") for r in rlist] != TIERS:
            seq_ok = False
            seq_detail = f"{m}: in-file order differs"
            break
    results.append(("each method has exactly the 40 amounts in order", seq_ok, seq_detail or "17/17 methods OK"))

    null_ok = True
    conv_ok = True
    ref_ok = True
    null_n = 0
    conv_n = 0
    detail = ""
    for i, r in enumerate(rows):
        fee_cny, fee_usd = r.get("published_fee_cny"), r.get("published_fee_usd")
        if fee_cny is None or fee_usd is None:
            if fee_cny is not None or fee_usd is not None:
                null_ok = False
                detail = f"row {i}: half-null fee"
            null_n += 1
        else:
            expected = round(fee_cny / rate, 2)
            if abs(expected - fee_usd) > 0.011:
                conv_ok = False
                detail = f"row {i}: usd {fee_usd} vs {expected}"
            conv_n += 1
        expected_cny = round(r["amount_usd"] * rate, 2)
        if abs(expected_cny - r["amount_cny_ref"]) > 0.011:
            ref_ok = False
            detail = f"row {i}: amount_cny_ref {r['amount_cny_ref']} vs {expected_cny}"
        if not (null_ok and conv_ok and ref_ok):
            break
    results.append(("null fees stay fully null (no half-fill)", null_ok, detail or f"{null_n} null rows OK"))
    results.append(("published_fee_usd == published_fee_cny / 7.129 (cents)", conv_ok, detail or f"{conv_n} rows OK"))
    results.append(("amount_cny_ref == amount_usd * 7.129 (cents)", ref_ok, detail or "680 rows OK"))

    # CSV parity
    csv_path = os.path.join(ROOT, "repatriate/exports/cost-ladders.csv")
    try:
        with open(csv_path, encoding="utf-8", newline="") as fh:
            csv_rows = list(csv.DictReader(fh))
        csv_ok = len(csv_rows) == len(rows)
        csv_detail = f"csv={len(csv_rows)} json={len(rows)}"
    except OSError as exc:
        csv_ok = False
        csv_detail = str(exc)
    results.append(("CSV export row count matches JSON", csv_ok, csv_detail))

    # Source ids resolve
    src_data = _load("repatriate/data/sources.json")
    if isinstance(src_data, dict):
        known = set(src_data.keys())
        if "sources" in src_data and isinstance(src_data["sources"], list):
            known = {s.get("id") for s in src_data["sources"]}
    else:
        known = {s.get("id") for s in src_data}
    src_ok = True
    src_detail = ""
    for i, r in enumerate(rows):
        ids = r.get("sources") or []
        if not ids or any(s not in known for s in ids):
            src_ok = False
            src_detail = f"row {i}: {ids} not all in {len(known)} known ids"
            break
    results.append(("every row's source ids resolve in repatriate/data/sources.json", src_ok,
                    src_detail or f"{len(rows)} rows OK"))

    # Ladder route basis ids resolve too (cross-check while we are here)
    l_routes = _load("ladder/data/routes.json")
    l_src_data = _load("ladder/data/sources.json")
    if isinstance(l_src_data, dict):
        l_known = set(l_src_data.keys())
        if "sources" in l_src_data and isinstance(l_src_data["sources"], list):
            l_known = {s.get("id") for s in l_src_data["sources"]}
    else:
        l_known = {s.get("id") for s in l_src_data}
    lb_ok = True
    lb_detail = ""
    for rt in l_routes:
        basis = rt.get("basis") or []
        if not basis or any(b not in l_known for b in basis):
            lb_ok = False
            lb_detail = f"{rt.get('id')}: basis {basis}"
            break
    results.append(("every ladder route basis id resolves in ladder/data/sources.json", lb_ok,
                    lb_detail or f"{len(l_routes)} routes OK"))
    return results


def all_checks():
    return ladder_checks() + repatriate_checks()


if __name__ == "__main__":
    fails = 0
    for name, ok, detail in all_checks():
        print(("PASS" if ok else "FAIL"), "-", name, "-", detail)
        if not ok:
            fails += 1
    print(f"{len(all_checks())} checks, {fails} failures")
    raise SystemExit(1 if fails else 0)
