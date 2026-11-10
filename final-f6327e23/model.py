#!/usr/bin/env python3
"""Deterministic cost model for final-f6327e23.

Every input is either (a) a figure quoted from a source in data/sources.json, or
(b) an explicitly labelled model assumption in ASSUMPTIONS. Nothing else is used.

Run:  python3 final-f6327e23/model.py
Out:  final-f6327e23/data/costs.json, final-f6327e23/data/meta.json
"""
import json
import os
from decimal import Decimal, ROUND_HALF_UP

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

# ---------------------------------------------------------------- inputs
# S16 Bank of China quotation, page timestamp 2026/11/10 17:39:58, CNY per 100 USD.
BOC = {
    "spot_buy": Decimal("665.71") / 100,    # bank buys USD from customer
    "spot_sell": Decimal("668.51") / 100,   # bank sells USD to customer  <- CNY->USD
    # 折算价 is BOC's own accounting conversion rate (6.7167), NOT a mid-market rate,
    # so it is recorded but deliberately not used as the spread reference.
    "reference": Decimal("671.67") / 100,
}
# Observable retail markup when a customer buys USD: half of the published bid/ask
# spread. Pure arithmetic on one dated quotation (S16), not an assumption.
BOC_MID = (BOC["spot_buy"] + BOC["spot_sell"]) / 2
SPREAD_PCT = (BOC["spot_sell"] - BOC_MID) / BOC_MID

# S14 HSBC China tariff, effective 31 Oct 2026.
HSBC_TT_PCT = Decimal("0.001")     # 2.2.4.1: 0.1% of remittance amount
HSBC_TT_MIN_CNY = Decimal("100")   # 2.2.4.1 minimum
HSBC_TT_MAX_CNY = Decimal("500")   # 2.2.4.1 maximum (Premier/Advance)
HSBC_CABLE_CNY = Decimal("120")    # 2.2.4.2 cable charge
HSBC_PAY_EXACT_CNY = Decimal("200")  # 2.2.4.1 remark 1.1
HSBC_GLOBAL_TRANSFER_USD = Decimal("20")  # 2.2.6.1 Advance: actual USD 20

# S15 Bank of America clarity statement: incoming international wire USD 16.
RECEIVE_USD = Decimal("16")

# S06 card cash cap: CNY 100,000 per person per calendar year.
ATM_ANNUAL_CAP_CNY = Decimal("100000")

# S02 penalty ceilings (statutory maxima, not predictions).
EVASION_MAX_PCT = Decimal("0.30")
PRIVATE_TRADING_MAX_PCT = Decimal("0.30")

# ------------------------------------------------------------------------
ASSUMPTIONS = [
    {
        "id": "A01",
        "text": "The USD amount is the amount to be received in the US. The CNY converted is "
                "USD x the BOC spot selling rate on 2026-11-10 (S16).",
        "why": "Fees are charged in CNY; a rate is needed to express them in USD.",
        "impact": "Moves the fixed-fee USD figure by <0.3% for a +/-2% rate change.",
        "status": "model assumption",
    },
    {
        "id": "A02",
        "text": "FX markup on the CNY->USD leg is 0.2098%, the half-spread between BOC's published "
                "spot selling rate (6.6851) and the midpoint of its published bid/ask (6.6711).",
        "why": "No regulator publishes a spread; this is arithmetic on one dated official quotation.",
        "impact": "Directly scales with amount: USD 20.98 per USD 10,000. A bank quoting 1% would "
                  "cost about 5x this line.",
        "status": "measured snapshot, not a quote",
    },
    {
        "id": "A03",
        "text": "The HSBC China Advance/Premier telegraphic-transfer tariff applies (0.1%, min "
                "CNY 100, max CNY 500, plus CNY 120 cable).",
        "why": "It is the only dated, published per-transfer fee schedule verified in this session.",
        "impact": "Fixed CNY 220 at the low end; capped at CNY 620 above ~CNY 500,000 of principal.",
        "status": "one bank only",
    },
    {
        "id": "A04",
        "text": "The receiving US bank charges USD 16 per incoming international wire (BofA "
                "Interest Checking, S15). No intermediary-bank deduction is included.",
        "why": "Intermediary deductions are not published anywhere I could verify.",
        "impact": "Understates the true deduction if a correspondent bank takes a fee.",
        "status": "one bank, one account type; intermediary fees excluded",
    },
    {
        "id": "A05",
        "text": "No tax is included in the all-in cost columns.",
        "why": "A conversion tax depends on acquisition rates and filing history that are private facts.",
        "impact": "See taxes.html for the conditional section 988 layer; it is shown separately, never merged.",
        "status": "deliberate exclusion",
    },
    {
        "id": "A06",
        "text": "Statutory penalty ceilings (30% of amount) are shown only for unlawful routes, as "
                "the legal maximum, never as an expected cost.",
        "why": "The statutes set a range up to 30% (30%-100% if serious); no authority publishes an average.",
        "impact": "A ceiling, not a forecast.",
        "status": "legal maximum",
    },
]

TIERS = list(range(10_000, 400_001, 10_000))
USD = Decimal("0.01")


def q(x):
    return Decimal(x).quantize(USD, rounding=ROUND_HALF_UP)


def hsbc_tt(amount_usd):
    """HSBC China TT issuance + cable, in USD, per S14 2.2.4.1/2.2.4.2."""
    remit_cny = Decimal(amount_usd) * BOC["spot_sell"]
    raw = remit_cny * HSBC_TT_PCT
    capped = min(max(raw, HSBC_TT_MIN_CNY), HSBC_TT_MAX_CNY)
    total_cny = capped + HSBC_CABLE_CNY
    return {
        "raw_cny": q(raw),
        "fee_cny": q(capped),
        "cable_cny": q(HSBC_CABLE_CNY),
        "total_cny": q(total_cny),
        "usd": q(total_cny / BOC["spot_sell"]),
        "capped": bool(capped != raw),
    }


def spread_usd(amount_usd):
    return q(Decimal(amount_usd) * SPREAD_PCT)


def build_rows():
    rows = []
    for tier in TIERS:
        a = Decimal(tier)
        # R01 documented conversion + wire
        tt = hsbc_tt(a)
        sp = spread_usd(a)
        all_in = tt["usd"] + sp + RECEIVE_USD
        rows.append({
            "route": "R01", "amount": tier,
            "fx_fee_usd": str(tt["usd"]), "fx_fee_cny": str(tt["total_cny"]),
            "spread_usd": str(sp), "receive_usd": str(RECEIVE_USD),
            "all_in_usd": str(q(all_in)), "pct": str(q(all_in / a * 100)),
            "note": ("at the CNY 500 maximum" if tt["capped"] and tt["fee_cny"] == HSBC_TT_MAX_CNY
                     else "at the CNY 100 minimum" if tt["capped"] and tt["fee_cny"] == HSBC_TT_MIN_CNY
                     else "0.1% of the CNY remitted"),
        })
        # R02 remit existing FX: no conversion spread
        r2 = tt["usd"] + RECEIVE_USD
        rows.append({
            "route": "R02", "amount": tier,
            "fx_fee_usd": str(tt["usd"]), "fx_fee_cny": str(tt["total_cny"]),
            "spread_usd": "0.00", "receive_usd": str(RECEIVE_USD),
            "all_in_usd": str(q(r2)), "pct": str(q(r2 / a * 100)),
            "note": "requires an existing foreign-currency balance",
        })
        # R03 Global Transfer
        r3 = HSBC_GLOBAL_TRANSFER_USD + sp + RECEIVE_USD
        rows.append({
            "route": "R03", "amount": tier,
            "fx_fee_usd": str(q(HSBC_GLOBAL_TRANSFER_USD)), "fx_fee_cny": "n/a (USD-denominated)",
            "spread_usd": str(sp), "receive_usd": str(RECEIVE_USD),
            "all_in_usd": str(q(r3)), "pct": str(q(r3 / a * 100)),
            "note": "HSBC Advance tier; Premier tier is free (S14 2.2.6.1)",
        })
        # R06/R07/R08/R09 documented transfer under capital-account / entrustment rules
        for rid in ("R06", "R07", "R08", "R09"):
            rows.append({
                "route": rid, "amount": tier,
                "fx_fee_usd": str(tt["usd"]), "fx_fee_cny": str(tt["total_cny"]),
                "spread_usd": str(sp), "receive_usd": str(RECEIVE_USD),
                "all_in_usd": str(q(all_in)), "pct": str(q(all_in / a * 100)),
                "note": "same bank mechanics as R01; eligibility and staging differ",
            })
        # R04 ATM: capped; no verified fee
        cap_usd = q(ATM_ANNUAL_CAP_CNY / BOC["spot_sell"])
        capable = a <= Decimal(cap_usd)
        rows.append({
            "route": "R04", "amount": tier,
            "fx_fee_usd": "", "fx_fee_cny": "",
            "spread_usd": "", "receive_usd": "",
            "all_in_usd": "", "pct": "",
            "capability": "capable" if capable else "cap exceeded",
            "note": f"annual cap CNY 100,000 = USD {cap_usd}; ATM/card fees unpublished (flagged)",
        })
        # R12 cash: spread only, travel excluded
        rows.append({
            "route": "R12", "amount": tier,
            "fx_fee_usd": "0.00", "fx_fee_cny": "0.00",
            "spread_usd": str(sp), "receive_usd": "0.00",
            "all_in_usd": str(sp), "pct": str(q(sp / a * 100)),
            "note": "legal only up to USD 10,000 per trip (S05); travel/insurance excluded",
        })
        # R10 quota splitting: statutory ceiling
        rows.append({
            "route": "R10", "amount": tier,
            "fx_fee_usd": "", "fx_fee_cny": "",
            "spread_usd": "", "receive_usd": "",
            "all_in_usd": str(q(a * EVASION_MAX_PCT)), "pct": "30.00",
            "note": "statutory maximum fine under 条例 Art. 39, plus watchlist; not an expected cost",
        })
        # R11 underground: statutory ceiling
        rows.append({
            "route": "R11", "amount": tier,
            "fx_fee_usd": "", "fx_fee_cny": "",
            "spread_usd": "", "receive_usd": "",
            "all_in_usd": str(q(a * PRIVATE_TRADING_MAX_PCT)), "pct": "30.00",
            "note": "statutory maximum fine under 条例 Art. 45 plus confiscation; not an expected cost",
        })
    return rows


def build_tax_layer():
    """Conditional section 988 gain, using only published rates (S12, S16)."""
    scenarios = []
    conv = BOC["spot_sell"]
    for label, acq in [
        ("CNY acquired at the 2025 IRS yearly average (7.129)", Decimal("7.129")),
        ("CNY acquired at the 2024 IRS yearly average (7.189)", Decimal("7.189")),
        ("CNY acquired at the 2023 IRS yearly average (7.075)", Decimal("7.075")),
        ("CNY acquired at the 2021 IRS yearly average (6.452)", Decimal("6.452")),
    ]:
        pct = (1 - conv / acq) * 100
        scenarios.append({
            "label": label,
            "acq_rate": str(acq),
            "conv_rate": str(conv),
            "gain_pct": str(q(pct)),
            "gain_on_10k": str(q(Decimal(10000) * pct / 100)),
            "gain_on_100k": str(q(Decimal(100000) * pct / 100)),
            "gain_on_400k": str(q(Decimal(400000) * pct / 100)),
            "crosses_200": str(q(Decimal(10000) * pct / 100)) != "0.00" and
                           Decimal(10000) * pct / 100 > 200,
        })
    return {
        "conversion_rate": str(conv),
        "threshold_usd": "200",
        "scenarios": scenarios,
        "formula": "gain = USD received x (1 - conversion_rate / acquisition_rate)",
        "note": "Rate history is from S12; the conversion rate is the dated BOC selling rate in S16. "
                "These are illustrations of the arithmetic, not a tax computation for any person.",
    }


def main():
    rows = build_rows()
    tax = build_tax_layer()
    costs = {
        "generated": "2026-11-10",
        "rate": {
            "source": "S16",
            "spot_sell": str(BOC["spot_sell"]),
            "spot_buy": str(BOC["spot_buy"]),
            "reference_uncja": str(BOC["reference"]),
            "mid": str(BOC_MID),
            "spread_pct": str(q(SPREAD_PCT * 100)),
            "timestamp": "2026/11/10 17:39:58 (page timestamp)",
        },
        "tiers": TIERS,
        "rows": rows,
        "assumptions": ASSUMPTIONS,
        "tax_layer": tax,
    }
    meta = {
        "generated": "2026-11-10",
        "tiers": len(TIERS),
        "row_count": len(rows),
        "costed_route_count": 8,
        "source_count": len(json.load(open(os.path.join(DATA, "sources.json")))),
        "route_count": len(json.load(open(os.path.join(DATA, "routes.json")))),
        "spread_pct": str(q(SPREAD_PCT * 100)),
        "rate": str(BOC["spot_sell"]),
        "receipt_10000": str(q(hsbc_tt(10000)["usd"] + spread_usd(10000) + RECEIVE_USD)),
        "receipt_400000": str(q(hsbc_tt(400000)["usd"] + spread_usd(400000) + RECEIVE_USD)),
    }
    with open(os.path.join(DATA, "costs.json"), "w") as f:
        json.dump(costs, f, indent=1)
    with open(os.path.join(DATA, "meta.json"), "w") as f:
        json.dump(meta, f, indent=1)
    print(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()
