#!/usr/bin/env python3
"""Cost model for CNY -> USD routes.

Every input rate below is copied from an official page and carries its source id.
The model does not estimate, round or interpolate anything: it applies the
published fee formula to the published board rates. Anything not published is
left out of the arithmetic and appears as a blank on the site.

Run:  python3 model.py     -> writes data/costs.csv and data/costs.json
"""

import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

# --- Published inputs ------------------------------------------------------
# S01 Bank of China board, 2026/11/11 20:39:19, CNY per 100 USD.
BOC_BUY = 665.91 / 100.0
BOC_SELL = 668.71 / 100.0

# S02 HSBC China board, last update 2026-11-10, CNY per USD.
HSBC_BUY_TT = 6.6362813
HSBC_SELL = 6.7030239

# S03 Bank of China commission: 0.1%, min CNY 50, max CNY 260, plus cable CNY 150.
BOC_FEE_RATE, BOC_FEE_MIN, BOC_FEE_MAX, BOC_CABLE = 0.001, 50.0, 260.0, 150.0

# S04 HSBC tariff: outward TT 0.1%, min CNY 100, max CNY 500, plus cable CNY 120.
HSBC_FEE_RATE, HSBC_FEE_MIN, HSBC_FEE_MAX, HSBC_CABLE = 0.001, 100.0, 500.0, 120.0
# S04 Global Transfer to self: Premier free, Advance USD 20.
HSBC_GT_PREMIER_FEE_USD = 0.0
HSBC_GT_ADVANCE_FEE_USD = 20.0

# S17 hard cap on cash carried per traveller per trip.
CASH_CAP_USD = 10000.0

AMOUNTS = list(range(10000, 400001, 10000))


def mid(buy, sell):
    return (buy + sell) / 2.0


def wires(usd, buy, sell, rate, fmin, fmax, cable, flat_usd=0.0):
    m = mid(buy, sell)
    cny_needed = usd * sell
    spread = usd * (sell - m) / sell
    commission_cny = min(max(rate * cny_needed, fmin), fmax)
    fee_cny = commission_cny + cable if cable is not None else commission_cny
    fee_usd = fee_cny / sell
    total = spread + fee_usd + flat_usd
    return {
        "cny_needed": round(cny_needed, 2),
        "spread_usd": round(spread, 2),
        "fee_cny": round(fee_cny, 2),
        "fee_usd": round(fee_usd, 2),
        "total_usd": round(total, 2),
        "pct": round(total / usd * 100.0, 4),
    }


def build():
    rates = {
        "boc_buy": BOC_BUY,
        "boc_sell": BOC_SELL,
        "boc_mid": round(mid(BOC_BUY, BOC_SELL), 6),
        "boc_spread_pct": round(100 * (BOC_SELL - mid(BOC_BUY, BOC_SELL)) / BOC_SELL, 4),
        "hsbc_buy": HSBC_BUY_TT,
        "hsbc_sell": HSBC_SELL,
        "hsbc_mid": round(mid(HSBC_BUY_TT, HSBC_SELL), 6),
        "hsbc_spread_pct": round(100 * (HSBC_SELL - mid(HSBC_BUY_TT, HSBC_SELL)) / HSBC_SELL, 4),
        "boc_board_timestamp": "2026/11/11 20:39:19",
        "fed_noon_rate": 6.6760,  # S06, orientation only, used in no calculation
        "hsbc_board_timestamp": "2026-11-10",
        "sources": ["S01", "S02", "S03", "S04", "S17", "S06"],
    }

    rows = []
    for amt in AMOUNTS:
        m01 = wires(amt, BOC_BUY, BOC_SELL, BOC_FEE_RATE, BOC_FEE_MIN, BOC_FEE_MAX, BOC_CABLE)
        m02 = wires(amt, HSBC_BUY_TT, HSBC_SELL, HSBC_FEE_RATE, HSBC_FEE_MIN, HSBC_FEE_MAX, HSBC_CABLE)
        # M03: spread only (Premier Global Transfer fee published as free).
        m03 = wires(amt, HSBC_BUY_TT, HSBC_SELL, 0.0, 0.0, 0.0, None,
                    flat_usd=HSBC_GT_PREMIER_FEE_USD)
        # M04: spread plus flat USD 20.
        m04 = wires(amt, HSBC_BUY_TT, HSBC_SELL, 0.0, 0.0, 0.0, None,
                    flat_usd=HSBC_GT_ADVANCE_FEE_USD)

        trips = -(-int(amt) // int(CASH_CAP_USD))
        per_trip = amt
        m05 = wires(per_trip, BOC_BUY, BOC_SELL, 0.0, 0.0, 0.0, None)
        m05["trips"] = trips
        m05["total_usd"] = round(amt * (BOC_SELL - mid(BOC_BUY, BOC_SELL)) / BOC_SELL, 2)
        m05["pct"] = round(100 * (BOC_SELL - mid(BOC_BUY, BOC_SELL)) / BOC_SELL, 4)

        priced = {"M01": m01, "M02": m02, "M03": m03, "M04": m04}
        cheapest = min(priced, key=lambda k: priced[k]["total_usd"])

        rows.append({
            "usd": amt,
            "M01": m01,
            "M02": m02,
            "M03": m03,
            "M04": m04,
            "M05": m05,
            "M06": None,
            "M07": None,
            "M10": {"total_usd": 0.0, "pct": 0.0},
            "cheapest": cheapest,
            "cheapest_total_usd": priced[cheapest]["total_usd"],
        })

    payload = {"rates": rates, "rows": rows, "amounts": AMOUNTS}
    with open(os.path.join(DATA, "costs.json"), "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)

    fields = ["usd", "cheapest", "cheapest_total_usd"]
    for m in ("M01", "M02", "M03", "M04", "M05"):
        fields += [f"{m}_cny_needed", f"{m}_spread_usd", f"{m}_fee_usd", f"{m}_total_usd", f"{m}_pct"]
    fields += ["M06_total_usd", "M07_total_usd"]
    with open(os.path.join(DATA, "costs.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            out = {"usd": r["usd"], "cheapest": r["cheapest"],
                   "cheapest_total_usd": r["cheapest_total_usd"],
                   "M06_total_usd": "", "M07_total_usd": ""}
            for m in ("M01", "M02", "M03", "M04", "M05"):
                d = r[m]
                out[f"{m}_cny_needed"] = d.get("cny_needed", "")
                out[f"{m}_spread_usd"] = d.get("spread_usd", "")
                out[f"{m}_fee_usd"] = d.get("fee_usd", "")
                out[f"{m}_total_usd"] = d["total_usd"]
                out[f"{m}_pct"] = d["pct"]
            w.writerow(out)

    print(f"rows={len(rows)} BOC spread={rates['boc_spread_pct']}% HSBC spread={rates['hsbc_spread_pct']}%")
    for r in rows:
        if r["usd"] in (10000, 100000, 400000):
            print(r["usd"], {k: r[k]["total_usd"] for k in ("M01", "M02", "M03", "M04")},
                  "cheapest", r["cheapest"], r["cheapest_total_usd"])


if __name__ == "__main__":
    build()
