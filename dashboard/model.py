#!/usr/bin/env python3
"""
Deterministic cost model: CNY -> USD, $10,000 to $400,000 in $10,000 steps.

Every input below is either
  (a) a figure published by a cited source that this session fetched, or
  (b) explicitly marked as modelled/assumed and published on the Flagged page.

Nothing is inferred. Where no official figure exists the cell is left blank.

Sources referenced by id are in dashboard/data/sources.json.
Run:  python3 dashboard/model.py
"""
import json
import math
import os
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

# ---------------------------------------------------------------- inputs
# S24: PBoC/CFETS central parity, USD/CNY, 2026-11-09 09:15.  CNY per 1 USD.
PARITY = 6.7188
PARITY_DATE = "2026-11-09"

# S26 BOC board 2026-11-09 09:15:45 (CNY per 100 USD): bid 666.38, ask 669.19
BOC_BID, BOC_ASK = 6.6638, 6.6919
# S27 CMB board 2026-11-09 09:34:38 (CNY per 100 USD): bid 666.375, ask 669.279
CMB_BID, CMB_ASK = 6.66375, 6.69279

# Verified one-way conversion cost = half the bank's own bid/offer spread,
# measured against the bank's own board mid. Both banks agree to ~1bp.
_TWO = []
for bid, ask in ((BOC_BID, BOC_ASK), (CMB_BID, CMB_ASK)):
    mid = (bid + ask) / 2.0
    _TWO.append((( mid - bid) / mid) * 100.0)   # cost of a CNY->USD sale vs mid
SPREAD_LOW = round(min(_TWO), 4)     # 0.2104 %
SPREAD_HIGH = round(max(_TWO), 4)    # 0.2174 %
# Sensitivity: against the PBoC parity rather than the bank's own mid.
# Cost of selling USD to the bank (i.e. obtaining CNY) vs parity, and of buying
# USD from the bank vs parity. Both are published rates for the same day.
_SELL_VS_PARITY = (PARITY - BOC_BID) / PARITY * 100.0   # selling USD gives fewer CNY than parity
_BUY_VS_PARITY = (PARITY - BOC_ASK) / PARITY * 100.0
SPREAD_VS_PARITY_LOW = round(min(_SELL_VS_PARITY, _BUY_VS_PARITY), 4)    # 0.4004
SPREAD_VS_PARITY_HIGH = round(max(_SELL_VS_PARITY, _BUY_VS_PARITY), 4)   # 0.8184

# S14 HSBC China personal tariff (published, effective 2021-01-01)
WIRE_PCT = 0.001            # 0.1% of remittance amount
WIRE_MIN_CNY = 100.0        # floor
WIRE_MAX_CNY = 500.0        # cap
CABLE_CNY = 120.0           # telegraphic charge, per item 6.1.2.2
GLOBAL_REF_USD = 7.0        # item 5.3.1: CNY 50 reference price, actual USD 7/item
CASH_WITHDRAW_PCT = (0.0025, 0.0040)   # item 3.1.1, 0.25%-0.4%
CASH_WITHDRAW_MIN_CNY = 40.0           # item 3.1.1 floor
ATM_OVERSEAS_CNY = 20.0                # item 8.7, + 1% of amount
ATM_OVERSEAS_PCT = 0.01

# S08: cash carriage ceiling out of China, USD equivalent per trip.
CASH_PER_TRIP_USD = 10000.0
# Modelled: assumed ATM withdrawal size. Not a published figure.
ATM_WITHDRAW_USD = 1000.0

# S09: RMB 100,000/year overseas card withdrawal ceiling, expressed in USD
# at the verified parity. Converted, not quoted.
CARD_ANNUAL_CAP_USD = 100000.0 / PARITY

TIERS = [i * 10000 for i in range(1, 41)]


def cny_to_usd(cny):
    return cny / PARITY


def wire_fee(amount_usd):
    """S14 6.1.2.1 + 6.1.2.2. Returned in USD."""
    commission = min(max(WIRE_PCT * amount_usd * PARITY, WIRE_MIN_CNY), WIRE_MAX_CNY)
    return cny_to_usd(commission + CABLE_CNY)


def pct(x, base):
    return round(x / base * 100.0, 4)


# ---------------------------------------------------------------- method cost rules
# fee: (low, high) in USD; spread: (low, high) in percent or None when unverified
def cost_row(amount):
    rows = {}

    # ---- M01 documented income, bank FX + SWIFT wire
    f = wire_fee(amount)
    rows["M01"] = dict(fee=(f, f), spread=(SPREAD_LOW, SPREAD_HIGH),
                       status="verified",
                       note="0.1% commission clamped to CNY 100-500 plus CNY 120 cable, plus the verified bank spread.")

    # ---- M02 same-name global transfer
    rows["M02"] = dict(fee=(0.0, GLOBAL_REF_USD), spread=(SPREAD_LOW, SPREAD_HIGH),
                       status="verified",
                       note="HSBC lists same-name Global Transfer free on the top tier and CNY 50 (reference price USD 7) on the next.")

    # ---- M03 emigration asset transfer: identical bank mechanics to M01
    rows["M03"] = dict(fee=(f, f), spread=(SPREAD_LOW, SPREAD_HIGH),
                       status="verified_fees",
                       note="Bank fees identical to M01. Adds a mandatory PRC tax settlement before deregistration, shown separately as tax exposure, not as a fee.")

    # ---- M04 keep the RMB in China
    rows["M04"] = dict(fee=(0.0, 0.0), spread=(0.0, 0.0),
                       status="no_conversion",
                       note="Nothing is converted, so there is no conversion cost. The money does not reach the US and the annual US reporting duty continues.")

    # ---- M05 return of foreign currency by the original route
    rows["M05"] = dict(fee=(f, f), spread=(0.0, 0.0),
                       status="verified",
                       note="No FX spread because the balance is already USD. Only applies to money that originally came from abroad or to unused RMB within the 24-month reconversion window.")

    # ---- M06 genuine family gift
    rows["M06"] = dict(fee=(f, f), spread=(SPREAD_LOW, SPREAD_HIGH),
                       status="verified",
                       note="Same bank mechanics as M01, incurred by the sending relative. Lawful only if the money is genuinely theirs. Form 3520 above USD 100,000 a year.")

    # ---- M07 cash carriage: fee per trip, spread unverified
    trips = math.ceil(amount / CASH_PER_TRIP_USD)
    trip_amt = amount / trips
    lo = max(CASH_WITHDRAW_PCT[0] * trip_amt, cny_to_usd(CASH_WITHDRAW_MIN_CNY))
    hi = max(CASH_WITHDRAW_PCT[1] * trip_amt, cny_to_usd(CASH_WITHDRAW_MIN_CNY))
    rows["M07"] = dict(fee=(lo * trips, hi * trips), spread=None,
                       status="partial",
                       note=f"Requires {trips} trips at the USD 10,000 statutory ceiling. Cash withdrawal charge 0.25%-0.4% (min CNY 40) per trip, published. The cash exchange rate itself is not published, so the spread is blank.")

    # ---- M08 card / ATM abroad
    n = amount / ATM_WITHDRAW_USD
    lo = n * (ATM_OVERSEAS_PCT * ATM_WITHDRAW_USD + cny_to_usd(ATM_OVERSEAS_CNY))
    rows["M08"] = dict(fee=(lo, lo), spread=None,
                       status="partial",
                       note=f"CNY 20 + 1% per overseas withdrawal, published, at an assumed USD {ATM_WITHDRAW_USD:,.0f} withdrawal. Settlement spread not published. Hard ceiling of about USD {CARD_ANNUAL_CAP_USD:,.0f}/year (RMB 100,000) makes this unusable for large balances in one year.")

    # ---- M09 QDII: nothing verified
    rows["M09"] = dict(fee=None, spread=None, status="unverified",
                       note="No official fee or eligibility figure was verified this session, so the cost is left blank rather than estimated.")

    # ---- M11 sell the asset locally: bank mechanics identical to M01
    rows["M11"] = dict(fee=(f, f), spread=(SPREAD_LOW, SPREAD_HIGH),
                       status="verified_fees",
                       note="Bank fees identical to M01. The 20% PRC tax on the gain is a tax exposure shown separately.")

    # ---- M12 US reporting layer
    rows["M12"] = dict(fee=(0.0, 0.0), spread=(0.0, 0.0),
                       status="mandatory_no_fee",
                       note="No government filing fee. Professional preparation cost was not verified and is left blank.")

    out = {}
    for mid, r in rows.items():
        if r["fee"] is None or r["spread"] is None:
            out[mid] = dict(fee_low="", fee_high="", spread_low="", spread_high="",
                            total_low="", total_high="", pct_low="", pct_high="",
                            status=r["status"], note=r["note"])
            continue
        sp_lo = (r["spread"][0] / 100.0) * amount
        sp_hi = (r["spread"][1] / 100.0) * amount
        t_lo = r["fee"][0] + sp_lo
        t_hi = r["fee"][1] + sp_hi
        out[mid] = dict(
            fee_low=round(r["fee"][0], 2), fee_high=round(r["fee"][1], 2),
            spread_low=round(sp_lo, 2), spread_high=round(sp_hi, 2),
            total_low=round(t_lo, 2), total_high=round(t_hi, 2),
            pct_low=pct(t_lo, amount), pct_high=pct(t_hi, amount),
            status=r["status"], note=r["note"])
    return out


# PRC income tax exposure if the income behind the balance never bore PRC tax.
# S05 Art. 3: 3%-45% progressive on comprehensive income; flat 20% on the
# interest/dividend/rent/property-transfer/incidental categories.
def tax_exposure(amount):
    return dict(
        comprehensive_low=round(amount * 0.03, 2),
        comprehensive_high=round(amount * 0.45, 2),
        flat_20=round(amount * 0.20, 2),
        note="Statutory rate applied to the whole amount as an exposure band, NOT an estimate of this person's liability. "
             "The actual figure depends on the character of the income, what was already withheld, and the CNY 60,000 "
             "annual allowance plus deductions. Repeating this: this is a rate applied to a principal, not a computed tax.")
 
# Late fee if the PRC tax is paid late. S29 Art. 32: 0.05% per day.
def late_fee(tax_amount, days):
    return round(tax_amount * 0.0005 * days, 2)


def main():
    rows = []
    for t in TIERS:
        for mid, r in cost_row(t).items():
            row = dict(tier=t, method=mid)
            row.update(r)
            rows.append(row)

    matrix = {}
    for t in TIERS:
        matrix[t] = cost_row(t)

    meta = dict(
        generated=str(date.today()),
        parity=PARITY,
        parity_date=PARITY_DATE,
        tiers=TIERS,
        tier_count=len(TIERS),
        row_count=len(rows),
        method_count=len(set(r["method"] for r in rows)),
        spread_low=SPREAD_LOW,
        spread_high=SPREAD_HIGH,
        spread_vs_parity_low=SPREAD_VS_PARITY_LOW,
        spread_vs_parity_high=SPREAD_VS_PARITY_HIGH,
        boc=dict(bid=BOC_BID, ask=BOC_ASK),
        cmb=dict(bid=CMB_BID, ask=CMB_ASK),
        wire=dict(pct=WIRE_PCT, min_cny=WIRE_MIN_CNY, max_cny=WIRE_MAX_CNY, cable_cny=CABLE_CNY),
        card_annual_cap_usd=round(CARD_ANNUAL_CAP_USD, 2),
        cash_per_trip_usd=CASH_PER_TRIP_USD,
        atm_withdraw_usd=ATM_WITHDRAW_USD,
        headroom=dict(
            note="Anchors used only to frame the size of the problem; not part of the fee estimate.",
            two_years_of_50k=100000.0,
            card_two_years=round(CARD_ANNUAL_CAP_USD * 2, 2),
        ),
    )

    with open(os.path.join(DATA, "costs.json"), "w") as fh:
        json.dump(dict(meta=meta, rows=rows, matrix={str(k): v for k, v in matrix.items()}), fh, indent=1)

    # CSV: one row per tier per method, blank cells kept blank
    import csv
    cols = ["tier", "method", "fee_low", "fee_high", "spread_low", "spread_high",
            "total_low", "total_high", "pct_low", "pct_high", "status", "note"]
    with open(os.path.join(DATA, "costs.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in cols})

    with open(os.path.join(DATA, "tax-exposure.json"), "w") as fh:
        json.dump(dict(
            meta=dict(generated=str(date.today()),
                      rates="S05 Art. 3: 3%-45% progressive (comprehensive income); 20% flat (interest, dividends, rent, property transfer, incidental)."),
            rows=[dict(tier=t, **tax_exposure(t)) for t in TIERS],
            late_fee=dict(rate_per_day=0.0005,
                          source="S29 Art. 32",
                          examples=[dict(tax=10000, days=365, fee=late_fee(10000, 365)),
                                    dict(tax=50000, days=365, fee=late_fee(50000, 365)),
                                    dict(tax=100000, days=365, fee=late_fee(100000, 365))]),
        ), fh, indent=1)

    # ---- self-checks
    assert len(rows) == 40 * len(matrix[TIERS[0]]), len(rows)
    for r in rows:
        if r["total_low"] != "":
            assert r["total_low"] <= r["total_high"], r
            assert r["fee_low"] <= r["fee_high"], r
    print(f"rows={len(rows)} tiers={len(TIERS)} methods={meta['method_count']}")
    print(f"spread verified {SPREAD_LOW}%-{SPREAD_HIGH}%  (vs parity sensitivity {SPREAD_VS_PARITY_LOW}%-{SPREAD_VS_PARITY_HIGH}%)")
    print(f"card annual cap ~ USD {CARD_ANNUAL_CAP_USD:,.2f}")
    for t in (10000, 50000, 100000, 200000, 400000):
        m = matrix[t]["M01"]
        print(f"  M01 ${t:>7,}: total ${m['total_low']:>9,.2f} - ${m['total_high']:>9,.2f}  ({m['pct_low']}% - {m['pct_high']}%)")
        m2 = matrix[t]["M02"]
        print(f"  M02 ${t:>7,}: total ${m2['total_low']:>9,.2f} - ${m2['total_high']:>9,.2f}  ({m2['pct_low']}% - {m2['pct_high']}%)")


if __name__ == "__main__":
    main()
