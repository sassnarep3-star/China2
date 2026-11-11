#!/usr/bin/env python3
"""Cost model for estimate-facf2fe9.

Reads data/inputs.json and data/methods.json and writes data/costs.json.
Every number is arithmetic on inputs that were read from an official page
(see data/sources.json). Where an input was not read, the output is None
(shown blank on the site) and the row carries the flag that explains why.

Deterministic: same inputs -> same bytes. No clock, no network.
"""
import json
import sys
from decimal import Decimal as D, ROUND_HALF_UP, ROUND_CEILING
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
DATA = HERE / "data"

TIERS = [10000 * i for i in range(1, 41)]
CENT = D("0.01")


def q(x, places=CENT):
    return x.quantize(places, rounding=ROUND_HALF_UP)


def ceil_div(a, b):
    return int((a / b).to_integral_value(rounding=ROUND_CEILING))


def load(name):
    with open(DATA / name, encoding="utf-8") as fh:
        return json.load(fh)


def dec(x):
    return None if x is None else D(str(x))


def build():
    inputs = load("inputs.json")
    methods = load("methods.json")["methods"]
    lim = {k: D(str(v["value"])) for k, v in inputs["limits"].items()}

    # ---- boards -------------------------------------------------------------
    boards = {}
    for b in inputs["boards"]:
        buy, sell, notes = dec(b["buy"]), dec(b["sell"]), dec(b.get("notes_sell"))
        if b["key"] == "HSBC":
            raw = b["raw_usd_per_cny"]
            # feed quotes USD per 1 CNY; the bank sells USD at the lower USD-per-CNY figure
            sell = D(1) / D(str(raw["transfer_selling"]))
            buy = D(1) / D(str(raw["transfer_buying"]))
            notes = D(1) / D(str(raw["notes_selling"]))
        boards[b["key"]] = {"bank": b["bank"], "buy": buy, "sell": sell, "notes_sell": notes,
                            "stamp": b["stamp"], "source": b["source"], "status": b["status"]}
    ref_keys = inputs["reference_banks"]
    mids = [(boards[k]["buy"] + boards[k]["sell"]) / 2 for k in ref_keys]
    ref = sum(mids) / len(mids)

    board_rows = []
    for key, b in boards.items():
        row = {"key": key, "bank": b["bank"], "stamp": b["stamp"], "source": b["source"], "status": b["status"],
               "buy": None, "sell": None, "mid": None, "half_spread_pct": None, "sell_vs_ref_pct": None,
               "in_reference": key in ref_keys}
        if b["sell"] is not None:
            mid = (b["buy"] + b["sell"]) / 2
            row.update({
                "buy": str(q(b["buy"], D("0.00001"))), "sell": str(q(b["sell"], D("0.00001"))),
                "mid": str(q(mid, D("0.00001"))),
                "half_spread_pct": str(q((b["sell"] - mid) / mid * 100, D("0.001"))),
                "sell_vs_ref_pct": str(q((b["sell"] / ref - 1) * 100, D("0.001"))),
            })
        board_rows.append(row)

    tariffs = {t["key"]: t for t in inputs["tariffs"]}

    def wire_fee_cny(tkey, cny_principal):
        t = tariffs[tkey]
        if t["pct"] is None:
            return None
        commission = cny_principal * D(str(t["pct"]))
        lo, hi = D(str(t["min"])), D(str(t["max"]))
        commission = max(lo, min(hi, commission))
        return commission + D(str(t["cable"]))

    def wire_block(bkey, tkey, usd_parts):
        """Cost of sending the listed USD amounts as separate wires."""
        sell = boards[bkey]["sell"]
        if sell is None:
            return None
        cny_principal = sum(p * sell for p in usd_parts)
        spread_usd = sum(p * (sell / ref - 1) for p in usd_parts)
        fees = [wire_fee_cny(tkey, p * sell) for p in usd_parts]
        if any(f is None for f in fees):
            return {"cny_principal": cny_principal, "spread_usd": spread_usd, "fee_cny": None,
                    "fee_usd": None, "total_usd": None, "cny_total": None}
        fee_cny = sum(fees)
        fee_usd = fee_cny / ref
        return {"cny_principal": cny_principal, "spread_usd": spread_usd, "fee_cny": fee_cny,
                "fee_usd": fee_usd, "total_usd": spread_usd + fee_usd, "cny_total": cny_principal + fee_cny}

    rows = []
    for m in methods:
        kind = m["cost_model"].split(":")
        for tier in TIERS:
            x = D(tier)
            r = {"method": m["id"], "tier": tier, "total_usd": None, "pct": None, "cny_needed": None,
                 "spread_usd": None, "fee_usd": None, "fee_cny": None, "count": None, "count_unit": "",
                 "note": "", "status": "unverified"}
            blk = None
            if kind[0] == "wire":
                blk = wire_block(kind[1], kind[2], [x])
                r["count"], r["count_unit"] = 1, "wire"
            elif kind[0] == "quota":
                n = ceil_div(x, lim["annual_quota_usd"])
                blk = wire_block(kind[1], kind[2], [x / n] * n)
                r["count"], r["count_unit"] = n, "calendar years, one wire each"
            # The former "emigrant" cost model (three wires of 50% / 25% / 25% over two years above
            # RMB 200,000, from PBOC Announcement [2004] No. 16 Art. 6) was removed on 2026-11-11:
            # SAFE Hui Fa [2014] No. 2 Section 6(2) abolished the instalment requirement (source R17),
            # so M14 is priced with the plain "wire" model above.
            elif kind[0] == "fee_only":
                r["fee_usd"], r["fee_cny"] = "0.00", "0.00"
                r["note"] = "Fee shown is for Private Banking and Premier; Advance pays USD 20. Rate not published for this service."
                r["status"] = "partial"
            elif kind[0] == "count_only":
                r["count"] = ceil_div(x * ref, lim["wise_transfer_cny"])
                r["count_unit"] = "transfers of at most ¥300,000"
                r["note"] = "Fee not read."
                r["status"] = "partial"
            elif kind[0] == "atm":
                r["count"] = ceil_div(x * ref, lim["atm_year_cny"])
                r["count_unit"] = "calendar years at ¥100,000 a year"
                r["fee_usd"] = str(q(x * lim["cmb_atm_fee_pct"]))
                r["note"] = "Fee shown is China Merchants Bank's issuer fee only (0.5%). Network rate and ATM surcharge not read."
                r["status"] = "partial"
            elif kind[0] == "cash_usd":
                b = boards["BOC"]
                r["count"] = ceil_div(x, lim["cash_bank_permit_usd"])
                r["count_unit"] = "trips with a bank permit"
                r["spread_usd"] = str(q(x * (b["notes_sell"] / ref - 1)))
                r["cny_needed"] = str(q(x * b["notes_sell"]))
                r["note"] = f"{ceil_div(x, lim['cash_no_permit_usd'])} trips without a permit. Travel cost not included."
                r["status"] = "partial"
            elif kind[0] == "cash_rmb":
                r["count"] = ceil_div(x * ref, lim["rmb_cash_trip_cny"])
                r["count_unit"] = "trips at ¥20,000 a trip"
                r["note"] = "Exchange rate for notes abroad not published."
                r["status"] = "partial"
            elif kind[0] == "none":
                r["total_usd"], r["pct"], r["status"] = "0.00", "0.000", "no transaction"
                r["note"] = "Nothing is converted, so nothing is charged; the exchange-rate risk and US reporting remain."
            elif kind[0] == "penalty":
                r["status"] = "penalty exposure"
                r["note"] = (f"Fine up to USD {q(x * lim['fine_band_ordinary'], D('1'))} (30%); "
                             f"in serious cases up to USD {q(x * lim['fine_band_serious'], D('1'))} (100%). Not a price.")
            elif kind[0] == "blank":
                r["note"] = "Nothing verified."
            if kind[0] in ("wire", "quota", "emigrant"):
                if blk is None:
                    r["note"] = "Rate not read."
                else:
                    r["cny_needed"] = str(q(blk["cny_principal"] if blk["cny_total"] is None else blk["cny_total"]))
                    r["spread_usd"] = str(q(blk["spread_usd"]))
                    if blk["total_usd"] is None:
                        r["status"] = "partial"
                        r["note"] = "Fee not read; rate margin only. Renminbi shown excludes the fee."
                    else:
                        r["fee_cny"] = str(q(blk["fee_cny"]))
                        r["fee_usd"] = str(q(blk["fee_usd"]))
                        r["total_usd"] = str(q(blk["total_usd"]))
                        r["pct"] = str(q(blk["total_usd"] / x * 100, D("0.001")))
                        r["status"] = "estimated"
            rows.append(r)

    # ---- US exchange-gain illustration --------------------------------------
    sell_boc = boards["BOC"]["sell"]
    fx = []
    for year in ("2021", "2022", "2023", "2024", "2025"):
        avg = D(str(inputs["irs_yearly_avg_cny_per_usd"][year]))
        share = 1 - sell_boc / avg
        fx.append({"year": year, "irs_avg": str(q(avg, D("0.001"))), "gain_pct": str(q(share * 100, D("0.01"))),
                   "per_10k": str(q(D(10000) * share, D("1"))), "per_100k": str(q(D(100000) * share, D("1"))),
                   "per_400k": str(q(D(400000) * share, D("1")))})

    out = {
        "meta": {
            "session": "arena/facf2fe9-china2",
            "rates_read": "2026-11-10, 17:39-17:49 Beijing time",
            "reference_mid": str(q(ref, D("0.000001"))),
            "reference_formula": "average of (buy + sell) / 2 over the Bank of China, ICBC, CCB, ABC and CMB boards",
            "cost_formula": "cost in USD = amount x (bank selling rate / reference mid - 1) + (commission + cable fee in CNY) / reference mid",
            "parity_cny_per_usd": str(D(str(inputs["parity"]["cny_per_usd"]))),
            "tiers": TIERS,
            "methods": len(methods),
            "rows": len(rows),
            "gain_rate": str(sell_boc),
        },
        "boards": board_rows,
        "rows": rows,
        "fx_gain": fx,
    }
    with open(DATA / "costs.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    return out


if __name__ == "__main__":
    o = build()
    print(f"costs.json: {o['meta']['rows']} rows = {o['meta']['methods']} methods x {len(TIERS)} tiers; "
          f"reference mid {o['meta']['reference_mid']}")
