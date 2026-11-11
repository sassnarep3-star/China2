#!/usr/bin/env python3
"""Break the 'conversion penalty' into its actual components and price the
enforcement scenarios from the published penalty rules.

Inputs are constants taken from the source ledger in data/sources.json.
Nothing is estimated; where a rule states a range, both ends are shown.

Run: python3 penalties.py -> writes data/penalties.json
"""

import json
import os

import model

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

# Spreads recomputed from the boards (see model.py).
IRS_YEARLY_AVG_2025 = 7.129        # S07
BOC_SELL = model.BOC_SELL          # S01

# Penalty constants.
SAFE_EVASION_LOW = 0.30            # S09 Art.39
SAFE_EVASION_HIGH = 1.00           # S09 Art.39 (30%-100% band, upper end)
SAFE_CASH_CARRY = 0.20             # S09 Art.42
FBAR_NONWILLFUL = 16536            # S22
FBAR_WILLFUL = 165353              # S22
FORM_8938_BASE = 10000             # S23
FORM_8938_CONTINUED = 50000        # S23
PRC_LATE_SURCHARGE_PER_DAY = 0.0005  # S31 Art.32

SCENARIO_AMOUNTS = [10000, 100000, 400000]


def main():
    fx_gain_pct = (IRS_YEARLY_AVG_2025 / BOC_SELL) - 1.0

    scenarios = []
    for amt in SCENARIO_AMOUNTS:
        boc_cost = model.wires(amt, model.BOC_BUY, model.BOC_SELL, model.BOC_FEE_RATE,
                               model.BOC_FEE_MIN, model.BOC_FEE_MAX, model.BOC_CABLE)["total_usd"]
        scenarios.append({
            "usd": amt,
            "lawful_boc_cost_usd": round(boc_cost, 2),
            "lawful_boc_pct": round(boc_cost / amt * 100, 4),
            "fx_gain_usd": round(amt * fx_gain_pct, 2),
            "fx_gain_pct": round(fx_gain_pct * 100, 2),
            "evasion_fine_low_usd": round(amt * SAFE_EVASION_LOW, 2),
            "evasion_fine_high_usd": round(amt * SAFE_EVASION_HIGH, 2),
            "cash_carry_fine_usd": round(amt * SAFE_CASH_CARRY, 2),
            "fbar_nonwillful_usd": FBAR_NONWILLFUL,
            "fbar_willful_usd": FBAR_WILLFUL,
            "form_8938_usd": FORM_8938_BASE + FORM_8938_CONTINUED,
        })

    layers = [
        {
            "id": "P1",
            "layer": "Bank FX spread",
            "who": "Every conversion, lawful or not, at any bank.",
            "amount": "BOC 0.2094% of the amount converted; HSBC 0.4979%",
            "basis": "Difference between the board sell rate and the midpoint of the board buy and sell rates.",
            "formula": "amount x (sell - mid) / sell",
            "sources": ["S01", "S02"],
            "fixed": True,
        },
        {
            "id": "P2",
            "layer": "Bank commission and cable charge",
            "who": "Every wire.",
            "amount": "BOC: 0.1%, min CNY 50, max CNY 260, plus CNY 150 cable. HSBC: 0.1%, min CNY 100, max CNY 500, plus CNY 120 cable.",
            "basis": "Published tariff, capped, so it falls as a percentage as the amount rises.",
            "formula": "max(min_rate, min(0.1% x CNY amount, max_rate)) + cable",
            "sources": ["S03", "S04"],
            "fixed": True,
        },
        {
            "id": "P3",
            "layer": "Correspondent and receiving bank charges",
            "who": "Every wire.",
            "amount": "Blank - not published on either bank's page.",
            "basis": "Both tariffs state only the sending bank's charge.",
            "formula": "",
            "sources": ["S03", "S04"],
            "fixed": False,
        },
        {
            "id": "P4",
            "layer": "PRC individual income tax on the source income",
            "who": "Anyone whose balance is untaxed income.",
            "amount": "20% on interest, dividends, property transfer and incidental income; 3%-45% on comprehensive income; 5%-35% on business income.",
            "basis": "Statutory rates. This tax is due whether or not you convert, so it is not a cost of converting, but it is the item most often mistaken for one.",
            "formula": "statutory rate x taxable income",
            "sources": ["S20"],
            "fixed": True,
        },
        {
            "id": "P5",
            "layer": "PRC late payment surcharge",
            "who": "Anyone with unpaid PRC tax.",
            "amount": "0.05% of the overdue tax per day.",
            "basis": "Statutory surcharge; the authority can recover tax and surcharge for three years, or five in special cases.",
            "formula": "overdue tax x 0.0005 x days late",
            "sources": ["S31"],
            "fixed": True,
        },
        {
            "id": "P6",
            "layer": "US tax on the currency gain",
            "who": "Every US citizen who converts.",
            "amount": "{:.2f}% gain in the worked example (CNY acquired at the 2025 IRS average of 7.129 and sold at the BOC board sell rate of {:.4f}); taxed at ordinary rates; only the first USD 200 of personal-transaction gain is excluded.".format(fx_gain_pct * 100, BOC_SELL),
            "basis": "Section 988 treats the disposal of nonfunctional currency as an ordinary transaction.",
            "formula": "USD proceeds - USD basis, taxed at your marginal rate",
            "sources": ["S07", "S27"],
            "fixed": True,
        },
        {
            "id": "P7",
            "layer": "US information-return penalties",
            "who": "Anyone who missed an FBAR or Form 8938.",
            "amount": "FBAR non-willful USD 16,536; willful USD 165,353; Form 8938 USD 10,000 plus up to USD 50,000 more after notice.",
            "basis": "Inflation-adjusted statutory maxima and published form penalties.",
            "formula": "per violation, per year",
            "sources": ["S22", "S23"],
            "fixed": True,
        },
        {
            "id": "P8",
            "layer": "PRC enforcement penalties on unlawful routes",
            "who": "Only if the transfer is structured unlawfully.",
            "amount": "Evasion, illegal arbitrage or illegal conversion: 30% of the amount, or 30%-100% in serious cases. Currency carried in violation: warning plus up to 20%.",
            "basis": "State Council Decree No. 532, Articles 39-45.",
            "formula": "rate x amount involved",
            "sources": ["S09"],
            "fixed": True,
        },
        {
            "id": "P9",
            "layer": "Lost access and time",
            "who": "Anyone placed on a watch list or hit by an approval delay.",
            "amount": "Blank - no monetary figure is published.",
            "basis": "Watch-list review lasts two years; approval takes 20 working days plus a possible 10; a card's overseas cash function can be suspended for two years.",
            "formula": "",
            "sources": ["S14", "S15", "S16"],
            "fixed": False,
        },
    ]

    out = {
        "section": "F5",
        "fx_gain_pct": round(fx_gain_pct * 100, 4),
        "layers": layers,
        "scenarios": scenarios,
        "worked_example": {
            "text": "Convert USD 400,000 through BOC. Spread 0.2094% and a capped fee of CNY 410 give a lawful cost of about USD 898.75, i.e. 0.225%. The same USD 400,000 routed through an unlawful channel and treated as evasion under Article 39 would face a fine of USD 120,000, or up to USD 400,000 in the serious band. One missed willful FBAR for one year would be USD 165,353, which is 184 times the lawful conversion cost.",
            "sources": ["S01", "S03", "S09", "S22"],
        },
    }
    with open(os.path.join(DATA, "penalties.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
    print("fx gain %", round(fx_gain_pct * 100, 2))
    for s in scenarios:
        print(s["usd"], s["lawful_boc_cost_usd"], s["evasion_fine_low_usd"], s["evasion_fine_high_usd"])


if __name__ == "__main__":
    main()
