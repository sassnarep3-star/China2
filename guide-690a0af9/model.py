#!/usr/bin/env python3
"""Cost model for guide-690a0af9: every method at each USD 10,000 step from 10,000 to 400,000.

Inputs come only from figures recorded in data/sources.json (published rates/fees read 2026-11-11).
Values that no official page states are written as None (blank) — never estimated.
Writes data/costs.json and data/costs.csv.  Run: python3 guide-690a0af9/model.py
"""
import csv
import json
import math
import os
from decimal import Decimal as D, ROUND_HALF_UP, ROUND_CEILING

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = {s["id"]: s for s in json.load(open(os.path.join(HERE, "data", "sources.json"), encoding="utf-8"))}
TIERS = list(range(10000, 400001, 10000))


def fig(sid, key):
    return D(str(SRC[sid]["figures"][key]))


def c2(x):
    return float(D(x).quantize(D("0.01"), rounding=ROUND_HALF_UP))


def ceil(x):
    return int(D(x).to_integral_value(rounding=ROUND_CEILING))


# Published inputs
BOC_SELL = fig("S01", "usd_sell_tt_per100") / 100
BOC_BUY = fig("S01", "usd_buy_tt_per100") / 100
BOC_CASH_SELL = fig("S01", "usd_sell_cash_per100") / 100
BOC_MID = (BOC_SELL + BOC_BUY) / 2
HS_SELL = fig("S02", "usd_sell_tt")
HS_BUY = fig("S02", "usd_buy_tt")
HS_MID = (HS_SELL + HS_BUY) / 2
FED = fig("S06", "nov6")
IRS25 = fig("S07", "y2025")
IRS24 = fig("S07", "y2024")
BOC_FEE = dict(pct=fig("S03", "pct"), lo=fig("S03", "min_cny"), hi=fig("S03", "max_cny"), cable=fig("S03", "cable_other_cny"))
HS_FEE = dict(pct=fig("S04", "pct"), lo=fig("S04", "min_cny"), hi=fig("S04", "max_cny"), cable=fig("S04", "cable_cny"))
WISE_BANK = fig("S05", "published_cny_amount")
WISE_ALI = fig("S05", "published_cny_amount")
ATM_YEAR = fig("S16", "annual_cny")
ATM_DAY = fig("S16", "daily_card_cny")
CASH_FREE = fig("S17", "free_usd")
CASH_PERMIT = fig("S17", "bank_permit_usd")
FINE_ORD = fig("S09", "fine_ordinary_max")
WISE_RATE = fig("S05", "rate_usd_per_cny")
WISE_FEE = fig("S05", "fee_cny_at_200k")
WISE_FEE_BAL = fig("S05", "fee_cny_at_200k_balance")
WISE_AMT = fig("S05", "published_cny_amount")
RMIT_PCT = fig("S31", "rate_pct")
FINE_SER = fig("S09", "fine_serious_max")
SAFE_DAYS = fig("S14", "accept_days") + fig("S14", "decide_days")


def wire(t, sell, mid, fee):
    usd = D(t)
    cny_principal = usd * sell
    pct_fee = min(max(cny_principal * fee["pct"], fee["lo"]), fee["hi"])
    fee_cny = pct_fee + fee["cable"]
    fee_usd = fee_cny / sell
    margin_usd = usd * (sell - mid) / sell
    known = fee_usd + margin_usd
    return dict(
        usd=t, total_known_usd=c2(known), total_known_pct=float((known / usd * 100).quantize(D("0.001"), rounding=ROUND_HALF_UP)),
        fee_cny=c2(fee_cny), fee_usd=c2(fee_usd), margin_usd=c2(margin_usd),
        cny_debited=c2(cny_principal + fee_cny), gap_to_fed_usd=c2(usd * (sell - FED) / sell),
        intermediary_fee=None, receiving_fee=None,
    )


def gt_premier(t):
    usd = D(t)
    margin_usd = usd * (HS_SELL - HS_MID) / HS_SELL
    return dict(usd=t, total_known_usd=c2(margin_usd),
                total_known_pct=float((margin_usd / usd * 100).quantize(D("0.001"), rounding=ROUND_HALF_UP)),
                fee_cny=0.0, fee_usd=0.0, margin_usd=c2(margin_usd), cny_debited=c2(usd * HS_SELL),
                gap_to_fed_usd=c2(usd * (HS_SELL - FED) / HS_SELL), intermediary_fee=None, receiving_fee=None)


def main():
    rows = {"M01": [], "M02": [], "M03": [], "M04": [], "M05": [], "M06": [], "M07": [],
            "U01": [], "U02": [], "U03": [], "U04": [], "USTAX": [], "REMITTANCE_TAX": []}
    for t in TIERS:
        usd = D(t)
        rows["M01"].append(wire(t, BOC_SELL, BOC_MID, BOC_FEE))
        rows["M02"].append(wire(t, HS_SELL, HS_MID, HS_FEE))
        rows["M03"].append(gt_premier(t))
        cny_ref = usd * FED
        cny_wise = usd / WISE_RATE
        fee_wise = WISE_FEE * cny_wise / WISE_AMT
        fee_wise_bal = WISE_FEE_BAL * cny_wise / WISE_AMT
        rows["M04"].append(dict(usd=t, cny_at_fed=c2(cny_ref), cny_at_wise_rate=c2(cny_wise),
                                transfers_bank_app=ceil(cny_wise / WISE_BANK), transfers_alipay=ceil(cny_wise / WISE_ALI),
                                fee_cny_published_scale=c2(fee_wise), fee_cny_published_scale_balance=c2(fee_wise_bal),
                                fee_usd_published_scale=c2(fee_wise * WISE_RATE), fee_pct=float((fee_wise / cny_wise * 100).quantize(D("0.001"))),
                                rate=float(WISE_RATE), rate_source="published panel", fee_is_extrapolated=True,
                                fee=c2(fee_wise)))
        rows["M05"].append(dict(usd=t, safe_fee_cny=0.0, safe_max_working_days=int(SAFE_DAYS), bank_fee=None, fx_margin=None))
        rows["M06"].append(dict(usd=t, cny_at_fed=c2(cny_ref), calendar_years=ceil(cny_ref / ATM_YEAR),
                                card_days=ceil(cny_ref / ATM_DAY), atm_fee=None))
        margin_cash = usd * (BOC_CASH_SELL - BOC_MID) / BOC_CASH_SELL
        rows["M07"].append(dict(usd=t, trips_no_permit=ceil(usd / CASH_FREE), trips_bank_permit=ceil(usd / CASH_PERMIT),
                                fx_margin_usd=c2(margin_cash), withdrawal_fee=None))
        rows["U01"].append(dict(usd=t, fine_ordinary_usd=None, fine_serious_usd=None, consequence="Watch list: year of listing + 2 years (S15)"))
        rows["U02"].append(dict(usd=t, fine_ordinary_usd=c2(usd * FINE_ORD), fine_serious_usd=None, consequence="Art. 45 (S09)"))
        rows["U03"].append(dict(usd=t, fine_ordinary_usd=None, fine_serious_usd=None, consequence="Illegal activity (S18)"))
        rows["U04"].append(dict(usd=t, fine_ordinary_usd=c2(usd * FINE_ORD), fine_serious_usd=c2(usd * FINE_SER), consequence="Art. 39 (S09)"))
        cny_spent = usd * BOC_SELL
        rows["REMITTANCE_TAX"].append(dict(usd=t, pct=float(RMIT_PCT), tax_if_taxable_usd=c2(usd * RMIT_PCT / 100),
                                           tax_if_wire_or_platform_usd=None))
        rows["USTAX"].append(dict(usd=t, cny_converted=c2(cny_spent),
                                  gain_if_basis_2025=c2(usd - cny_spent / IRS25),
                                  gain_if_basis_2024=c2(usd - cny_spent / IRS24), tax_on_gain=None))
    params = dict(
        boc_sell=float(BOC_SELL), boc_buy=float(BOC_BUY), boc_mid=float(BOC_MID),
        boc_spread_pct=float(((BOC_SELL - BOC_MID) / BOC_SELL * 100).quantize(D("0.0001"))),
        hsbc_sell=float(HS_SELL), hsbc_buy=float(HS_BUY), hsbc_mid=float(HS_MID),
        hsbc_spread_pct=float(((HS_SELL - HS_MID) / HS_SELL * 100).quantize(D("0.0001"))),
        fed=float(FED), irs2025=float(IRS25), irs2024=float(IRS24),
        gain_pct_2025=float(((1 - BOC_SELL / IRS25) * 100).quantize(D("0.01"))),
        boc_fee_cap_cny=float(BOC_FEE["hi"] + BOC_FEE["cable"]), hsbc_fee_cap_cny=float(HS_FEE["hi"] + HS_FEE["cable"]),
        hsbc_cap_usd=c2((HS_FEE["hi"] + HS_FEE["cable"]) / HS_SELL), boc_cap_usd=c2((BOC_FEE["hi"] + BOC_FEE["cable"]) / BOC_SELL),
    )
    out = dict(generated="2026-11-11", tiers=TIERS, params=params, rows=rows)
    with open(os.path.join(HERE, "data", "costs.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    with open(os.path.join(HERE, "data", "costs.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["method", "usd", "known_cost_usd", "known_cost_pct", "bank_fee_cny", "fx_margin_usd", "cny_debited",
                    "gap_to_fed_h10_usd", "intermediary_fee", "receiving_fee"])
        for m in ("M01", "M02", "M03"):
            for r in rows[m]:
                w.writerow([m, r["usd"], f'{r["total_known_usd"]:.2f}', f'{r["total_known_pct"]:.3f}', f'{r["fee_cny"]:.2f}',
                            f'{r["margin_usd"]:.2f}', f'{r["cny_debited"]:.2f}', f'{r["gap_to_fed_usd"]:.2f}', "", ""])
    print("wrote costs.json:", {k: len(v) for k, v in rows.items()})
    print("M01 10k", rows["M01"][0]["total_known_usd"], "400k", rows["M01"][-1]["total_known_usd"], rows["M01"][-1]["total_known_pct"])
    print("M02 10k", rows["M02"][0]["total_known_usd"], "400k", rows["M02"][-1]["total_known_usd"])
    print("params", params)


if __name__ == "__main__":
    main()
