#!/usr/bin/env python3
"""Cost model for playbook-c1d73006.

Every number used here is read from data/sources.json, where it sits next to the
exact words of the official page that states it.  Nothing is typed in by hand
below except the tier ladder ($10,000 steps to $400,000) that the brief asks for.

An amount that no official page publishes is written as None (shown blank on the
site and listed on the Flagged for Review page).  None never means zero.

Run:  PYTHONDONTWRITEBYTECODE=1 python3 playbook-c1d73006/model.py
"""
import json
from decimal import Decimal as D, ROUND_HALF_UP, ROUND_CEILING
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = {s["id"]: s for s in json.loads((HERE / "data" / "sources.json").read_text(encoding="utf-8"))}
TIERS = [10000 * i for i in range(1, 41)]


def val(sid, key):
    return D(str(SRC[sid]["values"][key]))


def cents(x):
    return x.quantize(D("0.01"), rounding=ROUND_HALF_UP)


def ceil_div(a, b):
    return int((D(a) / D(b)).to_integral_value(rounding=ROUND_CEILING))


def bank(name, board, tariff, sid_board, sid_tariff):
    per = val(sid_board, "per")
    sell = val(sid_board, "usd_sell") / per
    buy = val(sid_board, "usd_buy") / per
    mid = (sell + buy) / 2
    return {
        "name": name, "sell": sell, "buy": buy, "mid": mid,
        "spread_pct": (sell - mid) / mid,          # share of the amount lost to the bank's margin
        "pct": val(sid_tariff, "tt_pct"), "min": val(sid_tariff, "tt_min_cny"),
        "max": val(sid_tariff, "tt_max_cny"), "cable": val(sid_tariff, "cable_cny"),
        "board": board, "tariff": tariff, "sid_board": sid_board, "sid_tariff": sid_tariff,
    }


BOC = bank("Bank of China", "board of 2026/11/11 10:40:02", "e-banking fee table", "BANK-01", "BANK-03")
HSBC = bank("HSBC China (Premier / Advance)", "board last updated 2026-11-10", "tariff effective 31 Oct 2026", "BANK-04", "BANK-02")
BANKS = {"boc": BOC, "hsbc": HSBC}

QUOTA = val("CN-FX-06", "quota_usd")
CASH_LOW = val("CN-FX-06", "cash_out_permit_from_usd")
CASH_HIGH = val("CN-FX-06", "cash_out_permit_to_usd")
ATM_YEAR = val("CN-FX-07", "atm_year_cny")
ATM_DAY = val("CN-FX-07", "atm_day_card_cny")
WISE_PER = val("PROV-01", "per_transfer_cny_bank_app")
FINE = val("CN-FX-01", "fine_pct") / 100
FINE_MAX = val("CN-FX-01", "fine_serious_max_pct") / 100
CARRY_FINE = val("CN-FX-01", "carry_fine_pct") / 100
REF = BOC["mid"]          # reference rate for turning a USD tier into CNY when counting caps


def spread_usd(b, amount):
    return D(amount) * b["spread_pct"]


def commission_cny(b, amount):
    raw = D(amount) * b["sell"] * b["pct"]
    return min(max(raw, b["min"]), b["max"])


def wire_fee_usd(b, amount):
    """Commission plus cable for one wire, in USD at the bank's own selling rate."""
    return (commission_cny(b, amount) + b["cable"]) / b["sell"]


def convert_and_wire(b, amount, pieces=None):
    """Published cost of buying `amount` dollars and wiring them, in one or several wires."""
    pieces = pieces or [amount]
    return spread_usd(b, amount) + sum(wire_fee_usd(b, p) for p in pieces)


def quota_pieces(amount):
    n = ceil_div(amount, QUOTA)
    return [int(QUOTA)] * (n - 1) + [amount - int(QUOTA) * (n - 1)]


def row(method, amount):
    """One cost row.  Keys ending in _usd are money; None means not published."""
    r = {"method": method, "amount": amount, "boc_usd": None, "hsbc_usd": None,
         "count": None, "count_label": "", "low_usd": None, "high_usd": None, "note": ""}
    both = lambda f: (cents(f(BOC)), cents(f(HSBC)))
    if method in ("L01", "L02", "L05", "L06", "L07"):
        r["boc_usd"], r["hsbc_usd"] = both(lambda b: convert_and_wire(b, amount))
        r["count"], r["count_label"] = 1, "wire"
    elif method == "L03":                      # already foreign currency: no conversion, wire fee only
        r["boc_usd"], r["hsbc_usd"] = both(lambda b: wire_fee_usd(b, amount))
        r["count"], r["count_label"] = 1, "wire"
    elif method == "L04":                      # USD 50,000 a year: one wire per calendar year
        p = quota_pieces(amount)
        r["boc_usd"], r["hsbc_usd"] = both(lambda b: convert_and_wire(b, amount, p))
        r["count"], r["count_label"] = len(p), "calendar years"
    elif method == "L08":                      # Wise: fee not published; count transfers at the per-transfer cap
        r["count"], r["count_label"] = ceil_div(D(amount) * REF, WISE_PER), "transfers"
    elif method == "L09":                      # HSBC same-name transfer: fee row unreadable in the tariff PDF
        r["count"], r["count_label"] = 1, "transfer"
    elif method == "L10":                      # overseas ATM: RMB 100,000 per calendar year
        r["count"], r["count_label"] = ceil_div(D(amount) * REF, ATM_YEAR), "calendar years"
        r["note"] = "%d card-days at RMB %s a day" % (ceil_div(D(amount) * REF, ATM_DAY), format(int(ATM_DAY), ","))
    elif method == "L11":                      # cash: margin only; trips at USD 10,000 (permit) and USD 5,000 (no permit)
        r["boc_usd"], r["hsbc_usd"] = both(lambda b: spread_usd(b, amount))
        r["count"], r["count_label"] = ceil_div(amount, CASH_HIGH), "trips with a bank permit"
        r["note"] = "%d trips at USD %s without a permit" % (ceil_div(amount, CASH_LOW), format(int(CASH_LOW), ","))
    elif method == "L12":                      # nothing is converted
        pass
    elif method in ("U1", "U2"):
        r["low_usd"], r["high_usd"] = cents(D(amount) * FINE), cents(D(amount) * FINE_MAX)
    elif method == "U5":
        r["high_usd"] = cents(D(amount) * CARRY_FINE)
    elif method in ("U3", "U4"):
        pass
    else:
        raise KeyError(method)
    for k in ("boc_usd", "hsbc_usd", "low_usd", "high_usd"):
        if r[k] is not None:
            r[k] = str(r[k])
    return r


METHOD_IDS = ["L01", "L02", "L03", "L04", "L05", "L06", "L07", "L08", "L09", "L10", "L11", "L12",
              "U1", "U2", "U3", "U4", "U5"]


def breakdown(b, amount):
    return {"amount": amount,
            "cny_needed": str(cents(D(amount) * b["sell"])),
            "spread_usd": str(cents(spread_usd(b, amount))),
            "commission_cny": str(cents(commission_cny(b, amount))),
            "cable_cny": str(cents(b["cable"])),
            "fees_usd": str(cents(wire_fee_usd(b, amount))),
            "total_usd": str(cents(convert_and_wire(b, amount))),
            "pct": str((convert_and_wire(b, amount) / D(amount) * 100).quantize(D("0.001"), rounding=ROUND_HALF_UP))}


def inputs():
    def b(x):
        return {"name": x["name"], "sell": str(x["sell"]), "buy": str(x["buy"]), "mid": str(x["mid"]),
                "spread_pct": str((x["spread_pct"] * 100).quantize(D("0.0001"), rounding=ROUND_HALF_UP)),
                "pct": str(x["pct"] * 100), "min": str(x["min"]), "max": str(x["max"]), "cable": str(x["cable"]),
                "board": x["board"], "tariff": x["tariff"], "sid_board": x["sid_board"], "sid_tariff": x["sid_tariff"]}
    return {"banks": {k: b(v) for k, v in BANKS.items()},
            "quota_usd": str(QUOTA), "cash_low_usd": str(CASH_LOW), "cash_high_usd": str(CASH_HIGH),
            "atm_year_cny": str(ATM_YEAR), "atm_day_cny": str(ATM_DAY), "wise_per_transfer_cny": str(WISE_PER),
            "fine_pct": str(FINE * 100), "fine_max_pct": str(FINE_MAX * 100), "carry_fine_pct": str(CARRY_FINE * 100),
            "reference_rate": str(REF), "tiers": TIERS}


def main():
    rows = [row(m, a) for m in METHOD_IDS for a in TIERS]
    out = {"inputs": inputs(), "rows": rows,
           "breakdown": {k: [breakdown(v, a) for a in TIERS] for k, v in BANKS.items()}}
    (HERE / "data" / "costs.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("model: %d rows (%d methods x %d tiers)" % (len(rows), len(METHOD_IDS), len(TIERS)))


if __name__ == "__main__":
    main()
