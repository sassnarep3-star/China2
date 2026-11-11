#!/usr/bin/env python3
"""Deterministic published-input cost model for guide-be3c20e8.

All inputs come from data/sources.json.  A "known" total is the sum of the
published board-spread illustration and published transfer fees only.  It is
not an all-in quote, not an eligibility determination and not a personal tax
bill.  Every unpublished component is represented by a null value and a flag.

Run: python3 model.py
Writes data/costs.json, data/costs.csv, data/penalty_costs.json,
data/penalty_costs.csv and data/model_params.json.
"""
import csv
import json
import math
import sys
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE))
import content  # noqa: E402  (editorial ledger, not another cost model)

DATA = HERE / "data"
LEDGER = json.loads((DATA / "sources.json").read_text(encoding="utf-8"))
S = {s["id"]: s for s in LEDGER["sources"]}
F = {sid: s["figures"] for sid, s in S.items()}
D = lambda x: Decimal(str(x))
Q2 = lambda x: x.quantize(D("0.01"), rounding=ROUND_HALF_UP)
Q4 = lambda x: x.quantize(D("0.0001"), rounding=ROUND_HALF_UP)
F2 = lambda x: float(Q2(x))
F4 = lambda x: float(Q4(x))

TIERS = list(range(10000, 400001, 10000))
METHODS = content.METHODS
METHOD_NAMES = {m["id"]: m["name"] for m in METHODS}
FLAG_IDS = {f["id"] for f in content.FLAGS}
SOURCE_IDS = set(S)

# Explicit blank-field reasons and their flag IDs.  A blank is never zero.
BLANK_REASONS = {
    "all_in_usd": ("No all-in quote: executable rate, third-party fees, personal tax and future inputs are unpublished.", ["F-01"]),
    "intermediary_fee_usd": ("The published tariff excludes correspondent and intermediary-bank charges.", ["F-01", "F-06"]),
    "receiving_fee_usd": ("The U.S. receiving bank's charge was not published in the sources read.", ["F-01", "F-22"]),
    "personal_tax_usd": ("Personal income character, tax-paid status, acquisition basis and U.S. ordinary rate are unknown.", ["F-02", "F-13", "F-14"]),
    "future_rate_usd": ("A future dated bank board is not published; today's reference board is not an executable quote.", ["F-04", "F-19"]),
    "future_wire_fees_usd": ("Wire fees and local discounts in later calendar years are unpublished.", ["F-07", "F-19"]),
    "future_remittance_fee_usd": ("The later remittance's bank rate and charge are unpublished.", ["F-01", "F-19"]),
    "cash_handling_fee_usd": ("Cash purchase, permit and handling charges are not published in the cash rules read.", ["F-11"]),
    "permit_fee_usd": ("The cash-carry permit's fee, if any, was not published on the official page.", ["F-11"]),
    "security_insurance_usd": ("Physical cash security and insurance costs are private facts, not published tariffs.", ["F-11"]),
    "deposit_conversion_fee_usd": ("The U.S. cash deposit/conversion charge and rate were not published.", ["F-11"]),
    "pay_exact_shortfall_usd": ("Pay Exact's published charge does not cap a later overseas-bank shortfall.", ["F-01", "F-06"]),
    "premier_monthly_fee_usd": ("Premier segment and waiver status are private; the monthly fee is excluded from per-transfer cost.", ["F-23"]),
    "private_banking_eligibility_fee_usd": ("Private Banking eligibility and any separate account terms were not verified.", ["F-23"]),
    "u_s_receiving_terms_usd": ("U.S. receiving-account terms and corridor details were not read line by line here.", ["F-22"]),
    "wise_fee_usd": ("Wise's exact from-CNY fee is shown only in the transfer setup, not on the help page read.", ["F-08"]),
    "wise_rate_spread_usd": ("Wise's executable conversion rate was not published on the help page read.", ["F-08"]),
    "overall_limit_usd": ("Wise's overall limit depends on private income and PRC tax records.", ["F-08"]),
    "bank_fx_spread_usd": ("The designated bank's executable FX rate after approval was not published.", ["F-09"]),
    "bank_wire_fee_usd": ("The designated bank's wire charge after approval was not published.", ["F-09"]),
    "admin_fee_cny": ("An inheritance-specific service guide and fee were not read here.", ["F-09"]),
    "atm_owner_fee_usd": ("The foreign ATM owner's charge was not published in the sources read.", ["F-10"]),
    "network_fx_rate_spread_usd": ("The card network's conversion rate was not published.", ["F-10"]),
    "cash_deposit_fee_usd": ("The U.S. cash-deposit charge was not published.", ["F-10", "F-11"]),
    "security_usd": ("Physical cash security costs are private facts.", ["F-10"]),
    "direct_rmb_fee_usd": ("No bank tariff for a direct personal cross-border RMB transfer of savings was published.", ["F-12"]),
    "direct_rmb_rate_usd": ("No executable RMB conversion rate for that unverified route was published.", ["F-12"]),
    "direct_rmb_limit_usd": ("No personal limit for a direct cross-border RMB savings route was published.", ["F-12"]),
    "fine_usd": ("A statutory range is published, but the actual fine depends on facts and is not a cost estimate.", ["F-21"]),
    "criminal_exposure_usd": ("Criminal exposure cannot be priced from the sources read.", ["F-21"]),
    "actual_prc_fine_usd": ("Whether an evasion, cash or underground-dealing violation occurred is a private fact.", ["F-21"]),
    "prc_income_tax_usd": ("Income character, residence and tax-paid status are unknown.", ["F-02", "F-13"]),
    "us_section988_gain_usd": ("Acquisition dates/rates and personal-transaction status are unknown.", ["F-14"]),
    "us_ordinary_tax_usd": ("The taxpayer's ordinary rate is not published here.", ["F-14"]),
    "actual_fbar_penalty_usd": ("Willfulness and filing history are private facts.", ["F-15", "F-17"]),
    "actual_form8938_penalty_usd": ("Filing history and IRS notices are private facts.", ["F-15"]),
    "actual_total_penalty_usd": ("Personal facts cannot be combined into a penalty bill.", ["F-01"]),
}

def blank(field, method_flags):
    reason, flags = BLANK_REASONS[field]
    flags = [f for f in flags if f in method_flags] or flags
    assert set(flags) <= FLAG_IDS, (field, flags)
    return {"field": field, "value": None, "reason": reason, "flag_ids": flags}

def known(field, value, unit, sources):
    assert set(sources) <= SOURCE_IDS
    return {"field": field, "value": value, "unit": unit, "source_ids": sources}

def ceil_div(a, b):
    return int((a / b).to_integral_value(rounding=ROUND_CEILING))

def spread(usd, buy, sell):
    mid = (buy + sell) / 2
    return usd * (sell - mid) / sell

def spread_pct(buy, sell):
    mid = (buy + sell) / 2
    return D(100) * (sell - mid) / sell

def capped_fee(cny, rate, lo, hi, cable):
    return min(max(cny * rate, lo), hi) + cable

# Published primary inputs, all traced to source IDs.
BOC_BUY = D(F["B01"]["boc_buy_tt_per100"]) / D(F["B01"]["per"])
BOC_SELL = D(F["B01"]["boc_sell_tt_per100"]) / D(F["B01"]["per"])
BOC_CASH_BUY = D(F["B01"]["boc_buy_cash_per100"]) / D(F["B01"]["per"])
BOC_CASH_SELL = D(F["B01"]["boc_sell_cash_per100"]) / D(F["B01"]["per"])
HSBC_BUY = D(F["B02"]["hsbc_buy_tt"])
HSBC_SELL = D(F["B02"]["hsbc_sell_tt"])
HSBC_CASH_BUY = D(F["B02"]["hsbc_buy_cash"])
HSBC_CASH_SELL = D(F["B02"]["hsbc_sell_cash"])
BOC_RATE, BOC_MIN, BOC_MAX, BOC_CABLE = (D(F["B03"][k]) for k in ("boc_tt_rate", "boc_tt_min_cny", "boc_tt_max_cny", "boc_cable_other_cny"))
HSBC_RATE, HSBC_MIN, HSBC_MAX, HSBC_CABLE = (D(F["B04"][k]) for k in ("hsbc_tt_rate", "hsbc_tt_min_cny", "hsbc_tt_max_cny", "hsbc_cable_cny"))
GT_USD = D(F["B04"]["hsbc_gt_advance_usd"])
QUOTA = D(F["B08"]["annual_quota_usd"])
WISE_BANK = D(F["B05"]["wise_bank_per_transfer_cny"])
WISE_ALIPAY = D(F["B05"]["wise_alipay_per_transfer_cny"])
CASH_NO_PERMIT = D(F["B17"]["no_permit_usd"])
CASH_BANK_PERMIT = D(F["B17"]["bank_permit_upper_usd"])
ATM_YEAR = D(F["B16"]["atm_year_cny"])
ATM_DAY = D(F["B16"]["atm_day_cny"])
SAFE_DAYS = D(F["B14"]["accept_working_days"]) + D(F["B14"]["decision_working_days"])
ADMIN_FEE_CNY = D(F["B14"]["admin_fee"])

def components(usd, model):
    u = D(usd)
    cny_boc = u * BOC_SELL
    cny_hsbc = u * HSBC_SELL
    s_boc = spread(u, BOC_BUY, BOC_SELL)
    s_hsbc = spread(u, HSBC_BUY, HSBC_SELL)
    if model == "boc_wire":
        fee_cny = capped_fee(cny_boc, BOC_RATE, BOC_MIN, BOC_MAX, BOC_CABLE)
        return [
            known("cny_debited", F2(cny_boc), "CNY", ["B01"]),
            known("spread_usd", F2(s_boc), "USD", ["B01", "B07"]),
            known("sender_fee_cny", F2(fee_cny), "CNY", ["B03"]),
            known("sender_fee_usd", F2(fee_cny / BOC_SELL), "USD", ["B01", "B03"]),
        ], Q2(s_boc + fee_cny / BOC_SELL), ["all_in_usd", "intermediary_fee_usd", "receiving_fee_usd", "personal_tax_usd"]
    if model == "boc_quota":
        years = ceil_div(u, QUOTA)
        first = min(u, QUOTA)
        fee_cny = capped_fee(first * BOC_SELL, BOC_RATE, BOC_MIN, BOC_MAX, BOC_CABLE)
        first_known = Q2(spread(first, BOC_BUY, BOC_SELL) + fee_cny / BOC_SELL)
        return [
            known("calendar_years", years, "years", ["B08"]),
            known("first_transfer_usd", int(first), "USD", ["B08"]),
            known("first_transfer_known_usd", F2(first_known), "USD", ["B01", "B03", "B08"]),
        ], None, ["all_in_usd", "future_rate_usd", "future_wire_fees_usd", "intermediary_fee_usd", "receiving_fee_usd", "personal_tax_usd"]
    if model == "boc_hold":
        return [
            known("cny_debited", F2(cny_boc), "CNY", ["B01"]),
            known("spread_usd", F2(s_boc), "USD", ["B01", "B07"]),
        ], Q2(s_boc), ["all_in_usd", "future_remittance_fee_usd", "intermediary_fee_usd", "receiving_fee_usd", "personal_tax_usd"]
    if model == "boc_cash":
        s_cash = spread(u, BOC_CASH_BUY, BOC_CASH_SELL)
        return [
            known("spread_usd", F2(s_cash), "USD", ["B01", "B07"]),
            known("trips_no_permit", ceil_div(u, CASH_NO_PERMIT), "trips", ["B17"]),
            known("trips_bank_permit", ceil_div(u, CASH_BANK_PERMIT), "trips", ["B17"]),
        ], Q2(s_cash), ["all_in_usd", "cash_handling_fee_usd", "permit_fee_usd", "security_insurance_usd", "deposit_conversion_fee_usd", "personal_tax_usd"]
    if model == "hsbc_tt":
        fee_cny = capped_fee(cny_hsbc, HSBC_RATE, HSBC_MIN, HSBC_MAX, HSBC_CABLE)
        return [
            known("cny_debited", F2(cny_hsbc), "CNY", ["B02"]),
            known("spread_usd", F2(s_hsbc), "USD", ["B02", "B07"]),
            known("sender_fee_cny", F2(fee_cny), "CNY", ["B04"]),
            known("sender_fee_usd", F2(fee_cny / HSBC_SELL), "USD", ["B02", "B04"]),
        ], Q2(s_hsbc + fee_cny / HSBC_SELL), ["all_in_usd", "pay_exact_shortfall_usd", "intermediary_fee_usd", "receiving_fee_usd", "premier_monthly_fee_usd", "personal_tax_usd"]
    if model == "hsbc_pb_tt":
        return [
            known("cny_debited", F2(cny_hsbc), "CNY", ["B02"]),
            known("spread_usd", F2(s_hsbc), "USD", ["B02", "B07"]),
            known("sender_fee_cny", 0, "CNY", ["B04"]),
        ], Q2(s_hsbc), ["all_in_usd", "private_banking_eligibility_fee_usd", "intermediary_fee_usd", "receiving_fee_usd", "personal_tax_usd"]
    if model == "hsbc_gt_free":
        return [
            known("cny_debited", F2(cny_hsbc), "CNY", ["B02"]),
            known("spread_usd", F2(s_hsbc), "USD", ["B02", "B07"]),
            known("transfer_fee_usd", 0, "USD", ["B04"]),
        ], Q2(s_hsbc), ["all_in_usd", "u_s_receiving_terms_usd", "intermediary_fee_usd", "receiving_fee_usd", "premier_monthly_fee_usd", "personal_tax_usd"]
    if model == "hsbc_gt_advance":
        return [
            known("cny_debited", F2(cny_hsbc), "CNY", ["B02"]),
            known("spread_usd", F2(s_hsbc), "USD", ["B02", "B07"]),
            known("transfer_fee_usd", F2(GT_USD), "USD", ["B04"]),
        ], Q2(s_hsbc + GT_USD), ["all_in_usd", "u_s_receiving_terms_usd", "intermediary_fee_usd", "receiving_fee_usd", "personal_tax_usd"]
    if model == "wise":
        return [
            known("cny_equivalent_at_boc_sell_reference_only", F2(cny_boc), "CNY", ["B01", "B05"]),
            known("transfers_bank_app", ceil_div(cny_boc, WISE_BANK), "transfers", ["B05"]),
            known("transfers_alipay", ceil_div(cny_boc, WISE_ALIPAY), "transfers", ["B05"]),
        ], None, ["wise_fee_usd", "wise_rate_spread_usd", "overall_limit_usd", "all_in_usd", "intermediary_fee_usd", "receiving_fee_usd", "personal_tax_usd"]
    if model == "emigrant":
        return [
            known("admin_fee_cny", int(ADMIN_FEE_CNY), "CNY", ["B14"]),
            known("max_working_days", int(SAFE_DAYS), "working days", ["B14"]),
            known("approval_uses", int(F["B14"]["approval_uses"]), "uses", ["B14"]),
        ], None, ["bank_fx_spread_usd", "bank_wire_fee_usd", "all_in_usd", "intermediary_fee_usd", "receiving_fee_usd", "personal_tax_usd"]
    if model == "inheritance":
        return [], None, ["admin_fee_cny", "bank_fx_spread_usd", "bank_wire_fee_usd", "all_in_usd", "intermediary_fee_usd", "receiving_fee_usd", "personal_tax_usd"]
    if model == "atm":
        return [
            known("cny_equivalent_at_boc_sell_reference_only", F2(cny_boc), "CNY", ["B01", "B16"]),
            known("calendar_years", ceil_div(cny_boc, ATM_YEAR), "years", ["B16"]),
            known("card_days", ceil_div(cny_boc, ATM_DAY), "days", ["B16"]),
            known("published_issuer_fee_cap_cny", int(F["B04"]["hsbc_atm_max_cny"]), "CNY per withdrawal", ["B04"]),
        ], None, ["all_in_usd", "atm_owner_fee_usd", "network_fx_rate_spread_usd", "cash_deposit_fee_usd", "security_usd", "personal_tax_usd"]
    if model == "cross_rmb":
        return [], None, ["all_in_usd", "direct_rmb_fee_usd", "direct_rmb_rate_usd", "direct_rmb_limit_usd", "intermediary_fee_usd", "receiving_fee_usd", "personal_tax_usd"]
    if model == "hsbc_cash":
        s_cash = spread(u, HSBC_CASH_BUY, HSBC_CASH_SELL)
        return [
            known("spread_usd", F2(s_cash), "USD", ["B02", "B07"]),
            known("trips_no_permit", ceil_div(u, CASH_NO_PERMIT), "trips", ["B17"]),
            known("trips_bank_permit", ceil_div(u, CASH_BANK_PERMIT), "trips", ["B17"]),
            known("notes_withdrawal_fee_cny", 0, "CNY", ["B04"]),
        ], Q2(s_cash), ["all_in_usd", "cash_handling_fee_usd", "permit_fee_usd", "security_insurance_usd", "deposit_conversion_fee_usd", "personal_tax_usd"]
    if model == "unlawful":
        return [], None, ["all_in_usd", "fine_usd", "criminal_exposure_usd", "personal_tax_usd"]
    raise ValueError(model)

def cost_rows():
    rows = []
    for m in METHODS:
        for usd in TIERS:
            k, total, blank_fields = components(usd, m["cost_model"])
            blanks = [blank(f, set(m["flags"])) for f in blank_fields]
            rows.append({
                "method_id": m["id"],
                "method_name": m["name"],
                "status": m["status"],
                "pricing": m["pricing"],
                "cost_model": m["cost_model"],
                "usd": usd,
                "total_known_usd": F2(total) if total is not None else None,
                "total_known_pct": F4(total / D(usd) * 100) if total is not None else None,
                "all_in_usd": None,
                "known": k,
                "blanks": blanks,
                "source_ids": m["sources"],
                "flag_ids": m["flags"],
            })
    return rows

def penalty_rows():
    out = []
    fine = D(F["B09"]["fine_standard_pct"]) / 100
    cash_fine = D(F["B09"]["cash_violation_pct"]) / 100
    serious = D(1)
    fbar_non = D(F["B22"]["nonwillful_usd"])
    fbar_will = D(F["B22"]["willful_usd"])
    form8938_max = D(F["B23"]["form8938_max_penalty_usd"])
    for usd in TIERS:
        u = D(usd)
        out.append({
            "usd": usd,
            "published_ceilings": [
                {"layer": "P07", "name": "PRC evasion/fraudulent FX purchase standard fine ceiling", "value_usd": F2(u * fine), "source_ids": ["B09"], "note": "Statutory ceiling of 30% of the amount; not a predicted fine."},
                {"layer": "P07", "name": "PRC serious evasion/fraudulent FX purchase fine ceiling", "value_usd": F2(u * serious), "source_ids": ["B09"], "note": "Statutory ceiling up to an equal amount in serious cases; not a predicted fine."},
                {"layer": "P11", "name": "Improper cash-carry fine ceiling", "value_usd": F2(u * cash_fine), "source_ids": ["B09"], "note": "Statutory ceiling of 20% of the amount; not a predicted fine."},
                {"layer": "P09", "name": "FBAR non-willful adjusted maximum", "value_usd": F2(fbar_non), "source_ids": ["B21", "B22"], "note": "Adjusted statutory maximum; personal willfulness and filing history are unknown."},
                {"layer": "P09", "name": "FBAR willful adjusted maximum", "value_usd": F2(fbar_will), "source_ids": ["B21", "B22"], "note": "Adjusted statutory maximum; not a personal penalty determination."},
                {"layer": "P09", "name": "Form 8938 failure-to-disclose maximum", "value_usd": F2(form8938_max), "source_ids": ["B23"], "note": "Published maximum after IRS notice; not a personal penalty determination."},
            ],
            "blanks": [
                blank("actual_prc_fine_usd", {"F-21"}),
                blank("prc_income_tax_usd", {"F-02", "F-13"}),
                blank("us_section988_gain_usd", {"F-14"}),
                blank("us_ordinary_tax_usd", {"F-14"}),
                blank("actual_fbar_penalty_usd", {"F-15", "F-17"}),
                blank("actual_form8938_penalty_usd", {"F-15"}),
                blank("actual_total_penalty_usd", {"F-01"}),
            ],
        })
    return out

def params(rows):
    published_transfer = {"R01", "R05", "R06", "R07", "R08"}
    first = [r for r in rows if r["usd"] == TIERS[0] and r["method_id"] in published_transfer and r["total_known_usd"] is not None]
    last = [r for r in rows if r["usd"] == TIERS[-1] and r["method_id"] in published_transfer and r["total_known_usd"] is not None]
    low10 = min(first, key=lambda r: (r["total_known_usd"], r["method_id"]))
    low400 = min(last, key=lambda r: (r["total_known_usd"], r["method_id"]))
    return {
        "boc_buy": F4(BOC_BUY), "boc_sell": F4(BOC_SELL), "boc_mid": F4((BOC_BUY + BOC_SELL) / 2),
        "hsbc_buy": F4(HSBC_BUY), "hsbc_sell": F4(HSBC_SELL), "hsbc_mid": F4((HSBC_BUY + HSBC_SELL) / 2),
        "boc_spread_pct": F4(spread_pct(BOC_BUY, BOC_SELL)),
        "hsbc_spread_pct": F4(spread_pct(HSBC_BUY, HSBC_SELL)),
        "boc_spread_400_usd": F2(spread(D(TIERS[-1]), BOC_BUY, BOC_SELL)),
        "hsbc_spread_400_usd": F2(spread(D(TIERS[-1]), HSBC_BUY, HSBC_SELL)),
        "low_10_method_id": low10["method_id"], "low_10_method": low10["method_name"], "low_10_value_usd": low10["total_known_usd"],
        "low_400_method_id": low400["method_id"], "low_400_method": low400["method_name"], "low_400_value_usd": low400["total_known_usd"],
        "tiers": len(TIERS), "methods": len(METHODS), "cost_rows": len(rows), "penalty_rows": len(penalty_rows()),
        "source_count": len(S), "flags": len(FLAG_IDS), "questions": len(content.QUESTIONS), "penalty_layers": len(content.PENALTY),
        "boc_board_timestamp": F["B01"]["published_time"], "hsbc_board_date": F["B02"]["board_date"],
    }

def write_csv(path, fieldnames, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow(r)

def main():
    rows = cost_rows()
    pen = penalty_rows()
    p = params(rows)
    (DATA / "costs.json").write_text(json.dumps({"meta": {"generated_by": "guide-be3c20e8/model.py", "retrieved": LEDGER["retrieved"], "formula": "known total = board spread to midpoint + published sender/transfer fees; all-in remains null", "all_in_is_blank": True}, "params": p, "rows": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (DATA / "penalty_costs.json").write_text(json.dumps({"meta": {"generated_by": "guide-be3c20e8/model.py", "retrieved": LEDGER["retrieved"], "note": "Published statutory ceilings only; actual personal penalty is null"}, "rows": pen}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (DATA / "model_params.json").write_text(json.dumps(p, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_csv(DATA / "costs.csv", ["method_id", "usd", "total_known_usd", "total_known_pct", "all_in_usd", "known_components", "blank_fields", "source_urls", "flag_ids"], [
        {
            "method_id": r["method_id"], "usd": r["usd"],
            "total_known_usd": "" if r["total_known_usd"] is None else f'{r["total_known_usd"]:.2f}',
            "total_known_pct": "" if r["total_known_pct"] is None else f'{r["total_known_pct"]:.4f}',
            "all_in_usd": "",
            "known_components": "; ".join(f'{k["field"]}={k["value"]}{k["unit"]}' for k in r["known"]),
            "blank_fields": "; ".join(b["field"] for b in r["blanks"]),
            "source_urls": "; ".join(S[x]["url"] for x in r["source_ids"]),
            "flag_ids": "; ".join(r["flag_ids"]),
        } for r in rows
    ])
    write_csv(DATA / "penalty_costs.csv", ["usd", "prc_standard_fine_ceiling_usd", "prc_serious_fine_ceiling_usd", "prc_cash_fine_ceiling_usd", "fbar_nonwillful_max_usd", "fbar_willful_max_usd", "form8938_max_usd", "actual_total_penalty_usd", "source_urls"], [
        {
            "usd": r["usd"],
            "prc_standard_fine_ceiling_usd": f'{r["published_ceilings"][0]["value_usd"]:.2f}',
            "prc_serious_fine_ceiling_usd": f'{r["published_ceilings"][1]["value_usd"]:.2f}',
            "prc_cash_fine_ceiling_usd": f'{r["published_ceilings"][2]["value_usd"]:.2f}',
            "fbar_nonwillful_max_usd": f'{r["published_ceilings"][3]["value_usd"]:.2f}',
            "fbar_willful_max_usd": f'{r["published_ceilings"][4]["value_usd"]:.2f}',
            "form8938_max_usd": f'{r["published_ceilings"][5]["value_usd"]:.2f}',
            "actual_total_penalty_usd": "",
            "source_urls": "; ".join(sorted({S[x]["url"] for c in r["published_ceilings"] for x in c["source_ids"]})),
        } for r in pen
    ])
    print(f"wrote {len(rows)} cost rows ({p['tiers']} tiers x {p['methods']} methods) and {len(pen)} penalty rows")
    print(f"10k low {p['low_10_method_id']} ${p['low_10_value_usd']:.2f}; 400k low {p['low_400_method_id']} ${p['low_400_value_usd']:.2f}")
    print(f"BOC spread {p['boc_spread_pct']:.4f}%; HSBC spread {p['hsbc_spread_pct']:.4f}%")

if __name__ == "__main__":
    main()
