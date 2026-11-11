#!/usr/bin/env python3
"""
dashboard-c6309933/model.py

Builds the $10,000 -> $400,000 cost ladder (40 tiers) for every costed method.

Hard rule: the ONLY numbers this model is allowed to use are
  (a) the fee schedule transcribed from HSBC Bank (China)'s published tariff
      effective 2026-10-31 (source S09), and
  (b) the IRS 2025 yearly average CNY/USD rate of 7.129 (source S03).

Nothing else. No FX spread, no correspondent fee, no receiving-bank fee and no
PRC or U.S. tax rate is asserted, modelled or guessed. Any such component is
emitted as None and rendered BLANK by build.py.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


def dump(name, obj):
    with open(os.path.join(DATA, name), "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def tiers():
    """USD 10,000 .. 400,000 in USD 10,000 steps -> 40 tiers."""
    return list(range(10_000, 400_001, 10_000))


def cny_fee(formula, amount_cny):
    """
    Compute the HSBC published charge in CNY from the transcribed tariff formula.

    pct-clamped-plus-flat:
        tariff 2.2.4.1 - 0.1% of the remittance amount,
                         minimum RMB 100 or equivalent,
                         maximum RMB 500 or equivalent
        tariff 2.2.4.2 - plus the flat cable charge (RMB 120, or 320 when the
                         RMB 200 OUR pre-charge in the 2.2.4.1 remarks applies)
    flat:
        a single published flat charge (RMB 0 where the tariff says 免费)
    """
    if formula is None:
        return None
    kind = formula["kind"]
    if kind == "flat":
        return float(formula["cny"])
    if kind == "pct-clamped-plus-flat":
        pct_part = amount_cny * formula["pct"]
        pct_part = max(float(formula["minCny"]), pct_part)
        pct_part = min(float(formula["maxCny"]), pct_part)
        return round(pct_part + float(formula["flatCny"]), 2)
    raise ValueError("unknown fee formula kind: %r" % kind)


def build():
    methods_doc = load("methods.json")
    rate = methods_doc["referenceRate"]["cnyPerUsd"]
    rate_src = methods_doc["referenceRate"]["sourceId"]

    rows = []
    for m in methods_doc["methods"]:
        if not m.get("costed"):
            # Non-costed methods still get 40 rows so the table is complete and
            # every cost cell is explicitly BLANK rather than silently absent.
            for usd in tiers():
                rows.append({
                    "methodId": m["id"],
                    "methodName": m["name"],
                    "tierUsd": usd,
                    "cnyAtReferenceRate": round(usd * rate, 2),
                    "verifiedBankFeeCny": None,
                    "verifiedBankFeeUsd": None,
                    "verifiedBankFeePct": None,
                    "fxSpreadCny": None,
                    "fxSpreadUsd": None,
                    "correspondentFeeUsd": None,
                    "receivingBankFeeUsd": None,
                    "prcTaxUsd": None,
                    "usTaxUsd": None,
                    "totalVerifiedCostUsd": None,
                    "totalCostUsd": None,
                    "sourceId": m.get("sourceId"),
                    "feeBasis": m.get("feeBasis"),
                })
            continue

        for usd in tiers():
            amount_cny = round(usd * rate, 2)
            fee_cny = cny_fee(m["feeFormula"], amount_cny)
            fee_usd = round(fee_cny / rate, 2)
            rows.append({
                "methodId": m["id"],
                "methodName": m["name"],
                "tierUsd": usd,
                "cnyAtReferenceRate": amount_cny,
                "verifiedBankFeeCny": fee_cny,
                "verifiedBankFeeUsd": fee_usd,
                "verifiedBankFeePct": round(fee_usd / usd * 100, 4),
                # --- components NOT verified this session: left BLANK ---
                "fxSpreadCny": None,
                "fxSpreadUsd": None,
                "correspondentFeeUsd": None,
                "receivingBankFeeUsd": None,
                "prcTaxUsd": None,
                "usTaxUsd": None,
                # Total of what IS verified. Deliberately NOT a total cost.
                "totalVerifiedCostUsd": fee_usd,
                "totalCostUsd": None,
                "sourceId": m.get("sourceId"),
                "feeBasis": m.get("feeBasis"),
            })

    costed = [m["id"] for m in methods_doc["methods"] if m.get("costed")]
    blanks = sum(1 for r in rows if r["verifiedBankFeeCny"] is None)
    out = {
        "generated": "2026-11-11",  # research snapshot date, not the build date
        "referenceRateCnyPerUsd": rate,
        "referenceRateSourceId": rate_src,
        "tiers": tiers(),
        "tierCount": len(tiers()),
        "methodCount": len(methods_doc["methods"]),
        "costedMethodIds": costed,
        "costedMethodCount": len(costed),
        "rowCount": len(rows),
        "blankCostCellCount": blanks,
        "unverifiedComponents": [
            "fxSpreadCny", "fxSpreadUsd", "correspondentFeeUsd",
            "receivingBankFeeUsd", "prcTaxUsd", "usTaxUsd", "totalCostUsd",
        ],
        "rows": rows,
    }
    dump("costs.json", out)
    return out


if __name__ == "__main__":
    o = build()
    print("dashboard-c6309933 model: %d rows = %d methods x %d tiers "
          "(%d costed, %d blank cost cells)"
          % (o["rowCount"], o["methodCount"], o["tierCount"],
             o["costedMethodCount"], o["blankCostCellCount"]))
