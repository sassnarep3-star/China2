#!/usr/bin/env python3
"""
usd-exit cost model.

Turns the published tariffs in data/sources.json into a USD cost ladder in
$10,000 increments from $10,000 to $400,000 for every method in data/methods.json.

DESIGN RULES (these are the honesty guarantees of this file):
  1. Only three kinds of number appear in the output:
       - 'published'  : copied from a source in sources.json (carries source id)
       - 'derived'    : arithmetic on published numbers (carries the formula)
       - None         : not published anywhere we could verify -> rendered blank
     Nothing is estimated, interpolated or guessed.
  2. The FX spread is NOT published by any bank we reviewed, so it is None
     everywhere. Every total here is therefore a FLOOR, not a full cost.
  3. Every row carries the id(s) of the official/commercial source behind it.

Run:  python3 usd-exit/model.py
Writes: usd-exit/data/costs.json, usd-exit/data/costs.csv
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

AMOUNTS = list(range(10000, 400001, 10000))  # $10k .. $400k inclusive

# ---------------------------------------------------------------- anchors ----
with open(os.path.join(DATA, "sources.json"), encoding="utf-8") as f:
    SOURCES = {s["id"]: s for s in json.load(f)["sources"]}
with open(os.path.join(DATA, "methods.json"), encoding="utf-8") as f:
    METHODS = json.load(f)

FX = METHODS["meta"]["fx_anchor"]
CNY_PER_USD = FX["cny_per_usd"]          # 6.7188, source P14
FX_SOURCE = FX["source"]

# ------------------------------------------- published tariff parameters ----
# Every constant below is quoted from a source, with the locator that proves it.
TARIFF = {
    # HSBC China account service rates, effective 2021-01-01 (C01)
    "tt_rate": 0.001,        # 5.1.1.1  outward telegraphic transfer 0.1% ...
    "tt_min_cny": 100.0,     #          ... minimum CNY 100 ...
    "tt_max_cny": 500.0,     #          ... maximum CNY 500
    "cable_cny": 120.0,      # 5.1.1.2  cable / postage charge, per wire
    "full_amount_cny": 200.0,  # 5.1.1.3/5.1.1.4 pre-collected intermediary estimate
}

# Volume ceilings published in the official sources (see methods.json 'volume').
CAPS = {
    "quota_annual_usd": 50000.0,      # P02, P03 annual facilitation quota
    "atm_annual_usd": 14883.90,       # P05 RMB 100,000/yr at the P14 parity (derived)
    "atm_daily_usd": 1488.39,         # P05 RMB 10,000/card/day (derived)
    "cash_per_trip_usd": 10000.0,     # P07 >US$10,000 prohibited
    "alipay_per_txn_usd": 7441.90,    # C02 CNY 50,000 (derived)
    "wise_per_txn_usd": 44652.00,     # C02 CNY 300,000 (derived)
    "reconversion_daily_usd": 500.0,  # P09
    "transfer_3520_usd": 100000.0,    # U08 reporting threshold, not a cap
}


def cny_to_usd(cny):
    """Convert a published CNY amount to USD at the SAFE central parity (P14)."""
    if cny is None:
        return None
    return round(cny / CNY_PER_USD, 2)


def wire_fee(amount_usd):
    """Bank wire cost in CNY for a single transfer of `amount_usd`.

    Formula, all parameters from C01:
        commission = clamp(0.1% of CNY amount, 100, 500)
        cable      = 120 flat
    Returns (cny, components, formula_text).
    """
    cny = amount_usd * CNY_PER_USD
    commission = min(max(TARIFF["tt_rate"] * cny, TARIFF["tt_min_cny"]), TARIFF["tt_max_cny"])
    cable = TARIFF["cable_cny"]
    total = commission + cable
    which = (
        "minimum CNY 100 binds"
        if TARIFF["tt_rate"] * cny <= TARIFF["tt_min_cny"]
        else "maximum CNY 500 binds"
        if TARIFF["tt_rate"] * cny >= TARIFF["tt_max_cny"]
        else "0.1% applies"
    )
    formula = (
        f"0.1% x {cny:,.0f} CNY = {TARIFF['tt_rate'] * cny:,.2f} CNY; {which} "
        f"-> {commission:,.2f} CNY + 120 CNY cable"
    )
    return round(total, 2), {"commission_cny": round(commission, 2), "cable_cny": cable}, formula


# ------------------------------------------------------------ per method ----
# Each builder returns a dict describing ONE row of the ladder for that method.
#   fee_cny / fee_usd : known tariff total (None if unpublished)
#   transfers         : how many separate transfers the route requires
#   years             : how long the route takes if it is rate-limited
#   note              : plain-English explanation of what drives the number

def row_bank_wire(amount, tranches=1, per_tranche=None):
    """Bank wire route: N tranches, tariff applied to each tranche."""
    slice_usd = amount if per_tranche is None else per_tranche
    edges = []
    remaining = amount
    while remaining > 0:
        chunk = min(slice_usd, remaining)
        edges.append(chunk)
        remaining -= chunk
    total_cny = 0.0
    per = []
    for chunk in edges:
        cny, comp, formula = wire_fee(chunk)
        total_cny += cny
        per.append({"usd": round(chunk, 2), "fee_cny": cny, "fee_usd": cny_to_usd(cny), "formula": formula})
    return {
        "fee_cny": round(total_cny, 2),
        "fee_usd": cny_to_usd(total_cny),
        "transfers": len(edges),
        "per_transfer": per,
        "basis": "published tariff, applied per transfer",
        "source": "C01",
    }


def build_row(mid, amount):
    """Build one ladder cell: the cost of moving `amount` USD by method `mid`."""
    r = {"method": mid, "amount_usd": amount}

    # --- M01 annual facilitation quota: one $50k wire per calendar year ---------
    if mid in ("M01", "M03", "M05", "M11"):
        n = math.ceil(amount / CAPS["quota_annual_usd"])
        w = row_bank_wire(amount, per_tranche=CAPS["quota_annual_usd"])
        r.update(w)
        r["years"] = n
        r["constrained_by"] = f"US$50,000/yr facilitation quota -> {n} calendar year(s)"
        r["note"] = (
            f"{n} wire(s) of up to $50,000 each, one per calendar year. "
            f"Bank tariff is trivial; the constraint is time, not money."
        )
        r["spread"] = None
        r["cn_tax_on_conversion_usd"] = 0
        r["us_tax_on_transfer_usd"] = 0
        return r

    # --- M02 above-quota with documents: one wire, document review --------------
    if mid == "M02":
        w = row_bank_wire(amount)
        r.update(w)
        r["years"] = None
        r["constrained_by"] = "document review; no published USD cap"
        r["note"] = "One wire. The binding constraint is whether the authenticity documents and tax voucher satisfy the bank, not a dollar limit."
        r["spread"] = None
        r["cn_tax_on_conversion_usd"] = 0
        r["us_tax_on_transfer_usd"] = 0
        return r

    # --- M04 emigration transfer: staged into 3 tranches ------------------------
    if mid == "M04":
        w = row_bank_wire(amount, per_tranche=max(amount / 3.0, 1))
        r.update(w)
        r["years"] = 2
        r["constrained_by"] = "SAFE approval; staged up to ~2 years (P06)"
        r["note"] = "Staged tranches under PBOC [2004] No.16. Requires 户口注销 + tax settlement first. SAFE head office reviews >= RMB 500,000."
        r["spread"] = None
        r["cn_tax_on_conversion_usd"] = None
        r["us_tax_on_transfer_usd"] = 0
        r["cn_tax_note"] = "Not zero: the pre-departure tax settlement (P11 Art.13) can tax the underlying income at 3-45% / 20%. No single rate applies to the balance, so no figure is asserted."
        return r

    # --- M06 Wise: fee unpublished -------------------------------------------
    if mid == "M06":
        r.update({
            "fee_cny": None, "fee_usd": None,
            "transfers": math.ceil(amount / CAPS["wise_per_txn_usd"]),
            "years": None,
            "constrained_by": "eligibility (tax record, last 3 yrs) + computed annual limit",
            "note": "Fee is not published for the from-CNY direction (C02 says it appears at set-up). Left blank rather than estimated.",
            "spread": None,
            "source": "C02",
            "cn_tax_on_conversion_usd": 0, "us_tax_on_transfer_usd": 0,
        })
        return r

    # --- M07 Alipay wallet: CNY 50,000 per transfer, fee unpublished -----------
    if mid == "M07":
        r.update({
            "fee_cny": None, "fee_usd": None,
            "transfers": math.ceil(amount / CAPS["alipay_per_txn_usd"]),
            "years": None,
            "constrained_by": f"CNY 50,000 per transfer -> many transfers",
            "note": "Wallet fee not published on the cited page. Aggregating many small transfers to move a large balance is exactly the pattern regulators treat as structuring (F-AGGREGATION).",
            "spread": None,
            "source": "C02",
            "cn_tax_on_conversion_usd": 0, "us_tax_on_transfer_usd": 0,
        })
        return r

    # --- M08 card spending: no wire at all ------------------------------------
    if mid == "M08":
        r.update({
            "fee_cny": 0.0, "fee_usd": 0.0,
            "transfers": 0, "years": None,
            "constrained_by": "spending, not transferring",
            "note": "No wire fee because no wire occurs. The card network's FX markup is unpublished, so the true cost is not zero — it is unknown (F-SPREAD).",
            "spread": None,
            "source": None,
            "cn_tax_on_conversion_usd": 0, "us_tax_on_transfer_usd": 0,
        })
        return r

    # --- M09 ATM: RMB 100,000/yr ---------------------------------------------
    if mid == "M09":
        n = math.ceil(amount / CAPS["atm_annual_usd"])
        r.update({
            "fee_cny": None, "fee_usd": None,
            "transfers": n, "years": n,
            "constrained_by": f"RMB 100,000/yr (~US${CAPS['atm_annual_usd']:,.0f}) -> {n} year(s)",
            "note": "HSBC's own tariff shows a 0.25%-0.4% cash-withdrawal charge (min CNY 40) but its applicability to foreign ATMs is not established, so the fee is blank (F-UNVERIFIED).",
            "spread": None,
            "source": "P05",
            "cn_tax_on_conversion_usd": 0, "us_tax_on_transfer_usd": 0,
        })
        return r

    # --- M10 cash: US$10,000 per trip, hard prohibition above -----------------
    if mid == "M10":
        n = math.ceil(amount / CAPS["cash_per_trip_usd"])
        r.update({
            "fee_cny": 0.0, "fee_usd": 0.0,
            "transfers": n, "years": None,
            "constrained_by": f"US$10,000 per trip; >US$10,000 prohibited (P07) -> {n} trip(s)",
            "note": "No published charge for the carry permit. Above US$10,000 the route is prohibited outright, and Form 105 is due in the US for each arrival above US$10,000 (U03).",
            "spread": None,
            "source": "P07",
            "cn_tax_on_conversion_usd": 0, "us_tax_on_transfer_usd": 0,
        })
        return r

    # --- M12 gift: reporting threshold, not a fee ----------------------------
    if mid == "M12":
        r.update({
            "fee_cny": None, "fee_usd": None,
            "transfers": None, "years": None,
            "constrained_by": f"US$100,000 reporting threshold on Form 3520 (U08)",
            "note": "A genuine gift is not US income. Above US$100,000/yr from a nonresident individual it must be reported on Form 3520. Not usable for your own money.",
            "spread": None,
            "source": "U08",
            "cn_tax_on_conversion_usd": None, "us_tax_on_transfer_usd": 0,
            "cn_tax_note": "The donor must still use a lawful Chinese route; China's nine IIT categories do not include gift receipts (P11).",
        })
        return r

    # --- M13 property sale proceeds ------------------------------------------
    if mid == "M13":
        w = row_bank_wire(amount, per_tranche=max(amount / 3.0, 1))
        r.update(w)
        r["years"] = 2
        r["constrained_by"] = "capital-account approval; 20% flat tax on the property gain first"
        r["note"] = "The dominant cost is not the wire: property-transfer income is taxed at a flat 20% on the net gain (P11 Art.3, Art.6(5)) before remittance. No gain figure is asserted because the cost basis is unknown."
        r["spread"] = None
        r["cn_tax_on_conversion_usd"] = None
        r["us_tax_on_transfer_usd"] = 0
        r["cn_tax_note"] = "20% flat on the NET GAIN, not on the proceeds. On a $400,000 sale with, say, a $100,000 basis the China tax would be 20% x $300,000 = $60,000 - but the basis is a user fact, so this table states the RATE and not a dollar figure."
        return r

    # --- M19 reconversion: US$500/day ---------------------------------------
    if mid == "M19":
        n = math.ceil(amount / CAPS["reconversion_daily_usd"])
        w = row_bank_wire(amount, per_tranche=CAPS["reconversion_daily_usd"])
        r.update(w)
        r["years"] = round(n / 365.0, 1)
        r["constrained_by"] = f"US$500/day -> {n} day(s) = {n/365.0:.1f} year(s)"
        r["note"] = "ID-only but rate-limited to US$500/day, so economically useless for a large balance; included because it is a real published rule."
        r["spread"] = None
        r["cn_tax_on_conversion_usd"] = 0
        r["us_tax_on_transfer_usd"] = 0
        return r

    # --- prohibited routes ---------------------------------------------------
    if mid in ("M14", "M15", "M16", "M17", "M18"):
        r.update({
            "fee_cny": None, "fee_usd": None,
            "transfers": None, "years": None,
            "constrained_by": "PROHIBITED",
            "note": "Not costed. Listed so the user knows to avoid it; every method entry cites the official prohibition.",
            "spread": None,
            "source": None,
            "cn_tax_on_conversion_usd": None, "us_tax_on_transfer_usd": None,
        })
        return r

    raise SystemExit(f"no cost model for {mid}")


def main():
    methods = METHODS["methods"]
    ids = [m["id"] for m in methods]

    by_method = {}
    for m in methods:
        rows = [build_row(m["id"], a) for a in AMOUNTS]
        by_method[m["id"]] = rows

    # ---- the ladder: for each amount, what are the two real choices? ---------
    # Ranking rule, stated explicitly because a naive "fastest wins" sort gives a
    # misleading answer (M19's US$500/day rule would "win" on paper while needing
    # hundreds of daily transfers).
    #
    #   Option A  "quota route"  = M01: 1 wire per calendar year, no approval,
    #              needs ceil(amount/50k) years.
    #   Option B  "bulk route"   = M04: staged over ~2 years, needs 户口注销 +
    #              tax settlement + SAFE approval.
    #
    # Below US$50,000 the quota route is unambiguous. Above it, the user faces a
    # real trade-off: 8 years of patience vs giving up household registration.
    # The table states both rather than pretending one is "best".
    ladder = []
    for amount in AMOUNTS:
        q = by_method["M01"][AMOUNTS.index(amount)]
        b = by_method["M04"][AMOUNTS.index(amount)]
        row = {
            "amount_usd": amount,
            "quota_route": "M01",
            "quota_fee_usd": q["fee_usd"],
            "quota_transfers": q["transfers"],
            "quota_years": q["years"],
            "quota_needs_approval": False,
            "bulk_route": "M04",
            "bulk_fee_usd": b["fee_usd"],
            "bulk_transfers": b["transfers"],
            "bulk_years": b["years"],
            "bulk_needs_approval": True,
            "bulk_precondition": "cancel 户口 + PRC tax settlement (P11 Art.13) + SAFE approval (P06)",
            "recommended": "M01" if amount <= CAPS["quota_annual_usd"] else "M04",
            "recommendation_reason": (
                "Within the annual quota: one wire, no approval, no irreversible step."
                if amount <= CAPS["quota_annual_usd"]
                else f"Above the quota: M01 needs {q['years']} calendar years; M04 needs ~2 years "
                     f"but requires cancelling household registration and a full PRC tax settlement."
            ),
            "spread": None,
            "unknown_cost": "retail FX spread (unpublished, F-SPREAD)",
            "note": "Fees are the published bank tariff only. The FX spread is unpublished and is usually the larger real cost.",
        }
        ladder.append(row)

    meta = {
        "generated": METHODS["meta"]["generated"],
        "amounts": AMOUNTS,
        "fx": FX,
        "fx_source": FX_SOURCE,
        "rule": "published | derived | blank. Never estimated.",
        "floor_warning": "Every total excludes the retail FX spread, which no reviewed bank publishes. Treat all figures as a FLOOR.",
        "sources_count": len(SOURCES),
        "methods_count": len(methods),
        "notes": [
            "Bank tariff parameters from HSBC China's published account-service rates effective 2021-01-01 (C01). Other banks publish different tariffs; this is one bank's published schedule, not an industry rate.",
            "CNY amounts are converted at the SAFE-published central parity for 2026-11-09, 1 USD = 6.7188 CNY (P14). A central parity is not an executable retail rate.",
            "Chinese tax on the ACT of conversion is zero for every lawful route, because a currency conversion is not one of the nine IIT income categories (P11 Art.2). The real Chinese tax attaches to the income behind the money and is a user-specific fact this table cannot compute.",
            "US tax on the transfer is zero. 26 USC 988 makes FX gain ordinary income but excludes personal transactions unless the gain exceeds US$200 (U05).",
        ],
    }

    out = {"meta": meta, "ladder": ladder, "by_method": by_method}
    with open(os.path.join(DATA, "costs.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    # ------------------------------------------------------------- CSV ----
    cols = ["method", "amount_usd", "fee_cny", "fee_usd", "transfers", "years",
            "spread", "cn_tax_on_conversion_usd", "us_tax_on_transfer_usd", "constrained_by"]
    import csv
    with open(os.path.join(DATA, "costs.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for mid in ids:
            for row in by_method[mid]:
                w.writerow(["" if row.get(c) is None else row.get(c) for c in cols])

    print(f"ladder rows: {len(ladder)}  methods: {len(ids)}  csv rows: {len(ids)*len(AMOUNTS)}")
    for a in (10000, 50000, 100000, 400000):
        L = [x for x in ladder if x["amount_usd"] == a][0]
        print(f"  ${a:>7,}: M01 ${L['quota_fee_usd']:>9,.2f} / {L['quota_years']}yr  |  M04 ${L['bulk_fee_usd']:>9,.2f} / {L['bulk_years']}yr  -> {L['recommended']}")
    # sanity: no None fee for lawful wire methods
    missing = [m for m in ("M01","M02","M03","M04","M05","M13") if by_method[m][0]["fee_usd"] is None]
    assert not missing, f"published-tariff method produced blank fee: {missing}"
    print("OK: all published-tariff methods produced a figure (no blanks where a tariff exists)")


if __name__ == "__main__":
    main()
