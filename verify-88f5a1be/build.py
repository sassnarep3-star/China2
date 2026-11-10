#!/usr/bin/env python3
"""Deterministic builder for verify-88f5a1be/ (arena/88f5a1be-china2).

Reads sources.json / findings.json (this session's fetched ledger) and the
read-only inputs repatriate/exports/cost-ladders.csv + ladder/data/costs.csv
for the reconciliation table. Recomputes every published-fee floor from the
HSBC tariff formula (S20 items 2.2.4.1-2.2.4.2) at the IRS 2025 yearly
average reference rate 7.129 (S19). Unpublished values stay blank.

Run: PYTHONDONTWRITEBYTECODE=1 python3 verify-88f5a1be/build.py
"""
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
RATE = 7.129  # S19 IRS 2025 yearly average, CNY per USD (reference only)
TIERS = list(range(10000, 400001, 10000))

sources = json.loads((HERE / "sources.json").read_text())["sources"]
findings = json.loads((HERE / "findings.json").read_text())["findings"]
SRC = {s["id"]: s for s in sources}


def hsbc_tt_fee_usd(amount_usd: float) -> float:
    """HSBC Premier/Advance outward TT: 0.1% min CNY100 max CNY500 + CNY120 cable (S20)."""
    cny = amount_usd * RATE
    issuance = min(max(0.001 * cny, 100.0), 500.0)
    return (issuance + 120.0) / RATE


def quota_fee_usd(amount_usd: float):
    """M02: one wire per calendar-year tranche of <=USD 50,000 (S01 Art. 2)."""
    n = math.ceil(amount_usd / 50000)
    total = 0.0
    remaining = amount_usd
    for _ in range(n):
        t = min(50000, remaining)
        total += hsbc_tt_fee_usd(t)
        remaining -= t
    return total, n


def compute_costs():
    rows = []
    for amt in TIERS:
        cny = amt * RATE
        m01 = hsbc_tt_fee_usd(amt)
        m02, m02_n = quota_fee_usd(amt)
        # split-wire sensitivity: same math as M02 tranches, same year
        split8 = m02
        rows.append({
            "amount_usd": amt,
            "amount_cny_ref": round(cny, 2),
            "m01_fee_usd": round(m01, 2),
            "m01_fee_cny": round(m01 * RATE, 2),
            "m02_fee_usd": round(m02, 2),
            "m02_wires": m02_n,
            "m02_years": m02_n,
            "m03_premier_fee_usd": 0.0,
            "m03_advance_fee_usd": None,
            "m04_transfers": math.ceil(cny / 300000),
            "m04_fee_usd": None,
            "m05_fee_usd": None,
            "m06_years": math.ceil(cny / 100000),
            "m06_days": math.ceil(cny / 10000),
            "m06_fee_usd": None,
            "m07_trips": math.ceil(amt / 5000),
            "m07_fee_usd": 0.0,
            "m08_trips": math.ceil(cny / 20000),
            "m08_fee_usd": None,
            "m09_days": math.ceil(amt / 500),
            "m09_fee_usd": None,
            "fine_standard_max_usd": round(0.30 * amt, 2),
            "fine_serious_min_usd": round(0.30 * amt, 2),
            "fine_serious_max_usd": round(1.00 * amt, 2),
            "split_wire_fee_usd": round(split8, 2),
        })
    return rows


COSTS = compute_costs()

# --- reconciliation inputs (read-only) ---
rep = {}
with open(ROOT / "repatriate/exports/cost-ladders.csv", newline="") as f:
    for r in csv.DictReader(f):
        if r["method"] == "M01":
            rep[int(r["amount_usd"])] = float(r["published_fee_usd"])
lad = {}
with open(ROOT / "ladder/data/costs.csv", newline="") as f:
    for r in csv.DictReader(f):
        if r["route"] == "R01":
            lad[int(r["tier"])] = float(r["fixed_fee"])

recon = []
for row in COSTS:
    amt = row["amount_usd"]
    recon.append({
        "amount_usd": amt,
        "ours": row["m01_fee_usd"],
        "repatriate": rep.get(amt),
        "ladder": round(lad.get(amt, 0), 2) if amt in lad else None,
        "diff_repatriate": round(row["m01_fee_usd"] - rep.get(amt, 0), 2) if amt in rep else None,
        "diff_ladder": round(row["m01_fee_usd"] - lad.get(amt, 0), 2) if amt in lad else None,
    })

costs_doc = {
    "meta": {
        "scope": "arena/88f5a1be-china2",
        "retrieved": "2026-11-10",
        "reference_rate": {"cny_per_usd": RATE, "basis": "IRS 2025 yearly average (S19)", "note": "Reference conversion for comparing published CNY fees only. Not an executable quote."},
        "fee_formula": "HSBC Premier/Advance TT (S20 2.2.4.1-2.2.4.2): min(max(0.1% x CNY amount, CNY 100), CNY 500) + CNY 120 cable, per transaction.",
        "policy": "Only published tariff floors are computed. FX spread, correspondent charges, Wise/WU fees are unpublished -> blank + flagged (F02/F03). Fine bands are statutory maxima, not prices.",
    },
    "rows": COSTS,
    "reconciliation": recon,
}
(HERE / "costs.json").write_text(json.dumps(costs_doc, indent=1) + "\n")

# exports
with open(HERE / "exports/costs.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(COSTS[0].keys()))
    w.writeheader()
    w.writerows(COSTS)
(HERE / "exports/costs.json").write_text(json.dumps(COSTS, indent=1) + "\n")

# --- methods synthesis (pros/cons/steps; sourced, no new facts) ---
METHODS = [
    ("M01", "Bank SWIFT wire of documented after-tax China income (foreign individual)", "lawful-conditional",
     "US citizen with lawful current-account RMB income earned in China + tax vouchers. The key route for money stuck in a China account.",
     ["No annual numeric cap stated for documented lawful income (S02/S03); the $50k quota is a different channel.",
      "Bank handles conversion + remittance in one documented process.",
      "Published fee caps at CNY 620/wire (CNY 500 + CNY 120) regardless of size (S20) — large wires are cheap in fixed-fee terms.",
      "Current transfers not restricted in principle (S05 Art. 5)."],
     ["Requires ID + source-of-funds materials including tax vouchers (S02); undocumented balances cannot use it.",
      "Unpaid PRC tax on source income must be resolved first — income tax, not conversion tax (S08).",
      "FX spread + correspondent charges unpublished (F02) — all-in cost cannot be verified in advance.",
      "Bank authenticity review; bank may request more documents or split the wire (F09)."],
     ["Assemble passport/ID, employment contract or income proof, and PRC tax records covering the amount.",
      "If tax on source income is unpaid, resolve it first and obtain tax records (S08).",
      "At your China bank, apply to purchase USD with the documented RMB income (S02).",
      "Instruct outward SWIFT remittance to your own US account (SWIFT/BIC, account, address).",
      "Pay published tariff (0.1% min CNY 100 max CNY 500 + CNY 120 cable; optional Pay Exact CNY 200) (S20).",
      "Keep receipts + tax records for US reporting (FBAR/8938 if thresholds met) (S11/S15)."],
     "S01;S02;S20"),
    ("M02", "Bank wire within the USD 50,000/year facilitation quota (PRC ID or Foreign Permanent Resident ID holders)", "lawful-conditional",
     "PRC domestic individuals; foreign individuals ONLY with PRC Foreign Permanent Resident ID Card (S03). Most US citizens use M01 instead.",
     ["ID-only formalities within quota — no transaction documents (S01 Art. 2).",
      "Same bank infrastructure as M01; published tariff applies.",
      "Spreading your OWN funds over calendar years is lawful (one person, one quota)."],
     ["USD 50,000/person/year (S01 Art. 2): USD 400,000 needs 8 calendar years on this route alone.",
      "Not available to most foreign passport holders (S03).",
      "Using other people's quotas for one beneficiary is prohibited splitting (S04 Art. 7; see M15).",
      "Spread still applies and is unpublished (F02)."],
     ["Confirm you hold a PRC ID or Foreign Permanent Resident ID Card (S03).",
      "Purchase USD within remaining annual quota with ID (S01 Art. 2).",
      "Remit abroad: domestic <=USD 50,000/day from FX savings account with ID; above with authenticity documents (S01 Art. 14).",
      "Repeat in later calendar years for amounts above the quota, or use document-based routes for the excess.",
      "Keep receipts; comply with US reporting (S11/S15)."],
     "S01;S03;S20"),
    ("M03", "HSBC Global Transfer to your own overseas HSBC account", "lawful-conditional",
     "Customers with HSBC China + own-name HSBC accounts in the destination country. CNY→USD conversion still needs a lawful basis (M01/M02).",
     ["Published fee: Free for Private Banking and Premier; Advance USD 20/transaction (S20 2.2.6.1).",
      "Own-name transfer; simple audit trail.",
      "No correspondent-fee uncertainty for the HSBC-internal leg (Note 7 still excludes other institutions/government charges)."],
     ["Requires HSBC accounts in both countries; Premier eligibility (e.g., TRB >=CNY 500,000) applies (S20 Note 3).",
      "Does not bypass SAFE conversion rules — purchase still needs quota or documents (S01/S02).",
      "FX spread unpublished (F02); per-transaction limits not in tariff (F02)."],
     ["Open/confirm own-name HSBC accounts in China and the US (eligibility per S20).",
      "Convert CNY to USD inside HSBC China on a lawful basis (M01 documents or M02 quota).",
      "Send via Global Transfer to your own US HSBC account (S20 2.2.6.1).",
      "Keep records; US reporting applies (S11/S15)."],
     "S20;S01;S02"),
    ("M04", "Wise (from-CNY) to your own foreign account", "lawful-conditional",
     "Non-mainland-Chinese individuals with PRC tax records (tax paid within last 3 years); personal accounts; own-account transfers only.",
     ["Provider states overall limit = documented after-China-tax salary, does not expire — no $50k/year staging within that limit.",
      "Single transfer up to CNY 300,000 via bank-app pay-in.",
      "Regulated partner pay-in flow; transparent in-app quote before sending."],
     ["Only your own accounts as recipient; no third-party payments.",
      "Requires recent tax records; undocumented balances do not qualify.",
      "Fees shown only at setup — not statically published, so no verified cost table is possible (F03).",
      "Mainland Chinese nationals cannot use from-CNY sending."],
     ["Create a Wise personal account; complete first-time verification.",
      "Upload PRC tax records; Wise assigns an overall limit from them.",
      "Set up CNY→USD transfer to your own US account; review the in-app fee and rate quote.",
      "Pay from your own Chinese bank app to the regulated partner account (<=CNY 300,000/transfer).",
      "Wise converts and pays out; keep records for US reporting."],
     "S02 (provider terms not re-fetched this session — see F03)"),
    ("M05", "Western Union from China (partner-bank online or in-person, cash pickup abroad)", "lawful-conditional",
     "Residents of China sending via WU partner banks. Passport accepted; bank account may be required.",
     ["Cash pickup abroad in minutes; large location network.",
      "Online sending via several partner-bank apps after registration.",
      "US is on PSBC's whitelist."],
     ["Transfers to recipient bank accounts were 'temporarily unavailable' at retrieval — cash pickup only (F03).",
      "Fees and per-transfer limits not statically published (F03).",
      "Agents are banks subject to local FX rules — SAFE conversion basis still applies.",
      "Cash pickup >USD 10,000 then deposited in the US may trigger bank reporting; carrying cash across the US border needs FinCEN 105 (S18)."],
     ["Register a WU profile with a partner bank (online) or visit a partner-bank branch with passport.",
      "Provide receiver details and purpose; pay from debit card/account plus quoted fee.",
      "Receive MTCN; share only with your intended receiver.",
      "Receiver picks up cash with ID at a WU location.",
      "Keep records; US reporting applies to the underlying account/income (S11/S15)."],
     "S01 (provider terms not re-fetched this session — see F03)"),
    ("M06", "Overseas ATM cash withdrawals with a China-issued bank card", "lawful-conditional",
     "Holders of domestic (mainland-issued) bank cards withdrawing cash abroad. Parallel cash channel, separate from the $50k quota.",
     ["No tax documents needed at the ATM; card network converts automatically.",
      "Useful for small amounts; RMB 10,000/card/day ceiling (S06)."],
     ["Hard cap RMB 100,000/person/calendar year across ALL cards (~USD 14,027 at reference rate) (S06).",
      "Exceeding it suspends overseas withdrawals current AND following year (S06).",
      "ATM operator + issuer fees and card-network FX margin unpublished (F02).",
      "USD 400,000 would take ~29 calendar years — impractical (computed).",
      "Borrowing others' cards to evade is prohibited (S06)."],
     ["Use your own mainland-issued card at an overseas ATM.",
      "Track cumulative withdrawals across all cards: <=RMB 100,000/year, <=RMB 10,000/card/day (S06).",
      "Deposit withdrawn cash into your US account; keep records.",
      "For physical carry into the US >USD 10,000 at one time, file FinCEN 105 (S18)."],
     "S06;S18"),
    ("M07", "Buy USD cash in China and carry it out (within customs permit rules)", "lawful-conditional",
     "Travelers exiting China. <=USD 5,000 no permit; USD 5,000-10,000 with bank permit; >USD 10,000 in principle not allowed (S07).",
     ["No permit needed <=USD 5,000/trip (S07).",
      "HSBC counter banknote withdrawal published Free (S20 2.2.2.1).",
      "US entry with <=USD 10,000 needs no FinCEN 105; above is legal WITH reporting (S18)."],
     ["USD 400,000 = 80 permit-free trips (computed) — travel costs and risk dominate; repeat-traveler rules cut limits to USD 500/1,000 (S07 Art. 6).",
      "Notes buy/sell board rates apply (spread unpublished, F02); >=USD 5,000 withdrawal needs 3 working days' notice at HSBC (S20).",
      "Unlawful carrying: warning + fine up to 20% (S05 Art. 42); US non-declaration risks forfeiture (S18)."],
     ["Purchase USD cash on a lawful basis (M01/M02) at the bank counter.",
      "Carry out within per-trip limit; obtain bank carrying permit for USD 5,000-10,000 (S07).",
      "Enter the US; file FinCEN 105 if carrying >USD 10,000 (S18).",
      "Deposit into your US account; keep records."],
     "S07;S20;S18"),
    ("M08", "Carry RMB banknotes out (<=CNY 20,000/trip) and convert abroad", "lawful-conditional",
     "Travelers carrying RMB cash within the per-trip limit and converting abroad.",
     ["Simple for small amounts within the limit.",
      "No conversion needed before departure."],
     ["~USD 2,806/trip at reference rate; USD 400,000 = ~143 trips (computed) — impractical.",
      "Offshore RMB conversion rates/fees unpublished (F02).",
      "Excess RMB is returned by customs; penalties for non-declaration; unlawful carrying fine up to 20% (S05 Art. 42)."],
     ["Withdraw <=CNY 20,000 cash.",
      "Exit China within the limit; declare if required.",
      "Convert RMB to USD at a bank/exchange abroad (offshore rate).",
      "US entry >USD 10,000 equivalent: FinCEN 105 (S18)."],
     "S05;S18 (RMB 20,000 limit not re-fetched this session — see F03)"),
    ("M09", "Reconvert unused RMB previously exchanged from foreign currency", "lawful-conditional",
     "Foreign individuals holding RMB previously converted FROM foreign currency and left unused, with the original exchange memo (24-month validity) (S01 Art. 13(2)).",
     ["With original memo: reconversion up to memo amount, no tax documents (S01).",
      "ID-only small reconversions: <=USD 500/day onshore, <=USD 1,000/day airside before departure (S01)."],
     ["ONLY for previously exchanged unused RMB — not a general route for salary/savings (S01).",
      "Memo expires 24 months after original exchange (S01).",
      "USD 400,000 via ID-only USD 500/day = 800 bank days (computed) — impractical; memo route limited to original amount."],
     ["Locate the original exchange memo from when you converted USD→CNY.",
      "Within 24 months, present ID + memo at the bank; reconvert up to the unused memo amount (S01).",
      "Without a memo, only ID-only daily small-amount reconversion applies (<=USD 500 onshore / <=USD 1,000 airside).",
      "Remit the reconvened FX abroad with ID (S01 Art. 15)."],
     "S01"),
    ("M10", "Emigrant personal asset transfer (SAFE-approved capital transfer)", "lawful-conditional",
     "Individuals who EMIGRATED FROM Mainland China (assets obtained before immigration permission) — typically former PRC residents, not US-born citizens (S09).",
     ["SAFE approval allows lump-sum remittance of the approved amount — no $50k/year staging (per 2014 amendment, NOT re-fetched — F04).",
      "Covers assets beyond salary (property, savings) if lawful, owned and undisputed (S09)."],
     ["Eligibility is narrow: emigrants from Mainland China with hukou cancellation/immigration proofs (S09); most US citizens born abroad do not qualify.",
      "SAFE application at original registered residence; documentary burden; approval amount limits the transfer (S09).",
      "Tax clearance on underlying assets required; emigration triggers a PRC tax return.",
      "No published fee schedule (F02)."],
     ["Confirm emigrant status (immigration permission + PRC hukou cancellation proofs) (S09).",
      "Settle PRC tax on the assets; emigration tax return.",
      "Apply to SAFE at the original registered-residence branch with written application, ID, asset-source proofs (S09).",
      "After approval, bank purchases FX and remits within the approved limit.",
      "US reporting: FBAR/8938 for the China account; the transfer itself is not US-taxable income (moving own funds)."],
     "S09;S01"),
    ("M11", "Inheritor asset transfer (foreign citizen inheriting China assets)", "lawful-conditional",
     "Foreign citizens (and HK/Macau residents) inheriting assets located in China from a decedent (S09).",
     ["One application per decedent; lump sum or installments within SAFE approval (S09).",
      "No $50k quota staging for the approved inheritance."],
     ["Requires inheritance legal documents/notarization and tax clearance; SAFE approval at decedent's original registered residence (S09).",
      "Only inherited assets — not a route for your own savings.",
      "Process fees/timeline unpublished (F02)."],
     ["Obtain inheritance legal documents or notarial deeds.",
      "Settle applicable PRC taxes on the estate/assets.",
      "Apply to SAFE where the decedent's residence was registered (S09).",
      "Bank remits the approved amount lump sum or in batches.",
      "US: inheritance from a nonresident alien >USD 100,000 triggers Form 3520 reporting; FBAR/8938 may apply while funds are in China."],
     "S09"),
    ("M12", "Remit proceeds of selling China commercial property (foreign individual)", "lawful-conditional",
     "Non-domestic individuals who owned and sold commercial housing in China (own-use principle at purchase).",
     ["PBOC rules explicitly allow converting and remitting sale proceeds.",
      "No $50k quota staging for documented sale proceeds."],
     ["PRC IIT 20% on the GAIN (proceeds minus original value and reasonable expenses) plus other transaction taxes/fees not quantified here (S08 Art. 3(3); F02).",
      "Requires sale contract, tax vouchers, property documents; bank authenticity review.",
      "Only if you actually own sellable property — not applicable to a plain bank balance."],
     ["Complete the property sale; pay PRC IIT on the gain and transaction taxes (S08).",
      "Obtain tax vouchers and sale documents.",
      "At the bank, convert the after-tax RMB proceeds to USD and remit with ID + documents.",
      "US: report the sale and any gain on your US return; FTC for PRC tax may apply subject to limits (S17); FBAR/8938 while funds are in China."],
     "S08;S17"),
    ("M13", "Individual foreign-trade settlement account (genuine trade, quota-exempt)", "lawful-conditional",
     "Registered individual foreign-trade operators with genuine trade activity.",
     ["Purchases/sales under the settlement account are NOT subject to the annual quota, regardless of amount, with valid trading documents."],
     ["Requires genuine registered trade — fabricating contracts to move savings is prohibited (S04 Art. 7; S05 Art. 40; see M17).",
      "Not a route for an existing personal bank balance with no trade background.",
      "Trade compliance, customs and tax obligations attach."],
     ["Register as an individual foreign-trade operator.",
      "Open a foreign-exchange settlement account (managed as an institutional account).",
      "Conduct genuine trade; settle FX with valid trading documents regardless of amount.",
      "Pay applicable trade taxes; keep documents."],
     "S01;S04;S05"),
    ("M14", "Crypto / stablecoin bridge (CNY → USDT → USD)", "rejected-unlawful",
     "Not recommended. Documented because the brief asks for as many ways as possible.",
     ["(None endorsed.)"],
     ["Virtual-currency-related business is illegal financial activity in China; fiat-crypto exchange strictly prohibited (S10).",
      "Financial institutions may not provide accounts/transfers/settlement for it (S10).",
      "Overseas providers may not illegally serve domestic subjects; assisting is punishable (S10).",
      "Civil acts contrary to public order are void — losses borne by the investor (S10).",
      "If treated as evasion/illegal dealing: fines up to 30%; serious 30-100% + criminal (S05 Arts. 39/45)."],
     ["Do not use. The lawful alternatives are M01-M13."],
     "S10;S05"),
    ("M15", "Quota splitting / pooling friends' and relatives' USD 50k quotas ('smurfing')", "rejected-unlawful",
     "Not recommended.",
     ["(None endorsed.)"],
     ["Explicitly prohibited: no evading limit administration by splitting large amounts into small batches (S04 Art. 7).",
      "SAFE's bank-SAFE information system is designed to detect repeated installment purchases.",
      "Evasion/fraudulent purchase fines up to 30%; serious 30-100% + criminal liability (S05 Arts. 39-40).",
      "Participants' own quotas and banking access can be affected."],
     ["Do not use. Lawful staging is your OWN quota across calendar years (M02) or the documented-income route (M01)."],
     "S04;S05"),
    ("M16", "Underground banks / matched domestic-offshore swaps", "rejected-unlawful",
     "Not recommended.",
     ["(None endorsed.)"],
     ["Private/indirect FX trading is illegal: warning, confiscation of illegal gains, fine up to 30%; serious 30-100%; criminal liability (S05 Art. 45).",
      "No legal recourse if the operator absconds; counterparty risk is total.",
      "US side: receiving funds from unknown third parties creates AML/tax complications."],
     ["Do not use."],
     "S05"),
    ("M17", "Fabricated contracts / false documents to pass bank authenticity review", "rejected-unlawful",
     "Not recommended.",
     ["(None endorsed.)"],
     ["Prohibited: no tampering with authenticity administration using fabricated commercial bills/vouchers (S04 Art. 7).",
      "Fraudulent FX purchase: fine up to 30%; serious 30-100%; criminal liability (S05 Art. 40).",
      "Banks verify through the SAFE system; detection risk is structural."],
     ["Do not use."],
     "S04;S05"),
]

methods_doc = {"meta": {"scope": "arena/88f5a1be-china2", "retrieved": "2026-11-10",
    "policy": "Pros/cons/steps summarize the cited sources; analysis is labeled. Rejected entries are documented because the brief asks for as many ways as possible — they are NOT recommendations."},
    "methods": [{"id": m[0], "name": m[1], "status": m[2], "who": m[3], "pros": m[4], "cons": m[5], "steps": m[6], "sources": m[7]} for m in METHODS]}
(HERE / "methods.json").write_text(json.dumps(methods_doc, indent=1) + "\n")

flags_doc = {"meta": {"scope": "arena/88f5a1be-china2", "retrieved": "2026-11-10"},
    "flags": [
        {"id": "F01", "title": "Private facts unknown", "detail": "Balance source, years, PRC tax paid, residence/hukou history, U.S. filing history, and bank quote were not supplied. No personal tax amount, route eligibility, or all-in cost is computed.", "status": "needs review"},
        {"id": "F02", "title": "FX spread and correspondent charges unpublished", "detail": "No bank publishes a CNY/USD customer spread. All spread cells are blank. Ladder's 0.30-1.50% band is an explicit assumption, not a quote. Advance Global Transfer total is blank because the per-transaction limit is unpublished.", "status": "needs review"},
        {"id": "F03", "title": "Wise / Western Union / RMB-carry terms not re-fetched", "detail": "Provider terms for M04/M05 and the RMB 20,000/trip limit (M08) were not re-fetched this session. Their fee cells are blank; their existence/eligibility summaries rest on prior sessions' ledgers and must be re-verified before use.", "status": "needs review"},
        {"id": "F04", "title": "2014 emigrant lump-sum amendment not re-fetched", "detail": "Only the 2004 PBOC installment text (S09) was verified this session. The 2014 cancellation of installments is asserted by prior sessions but left blank here until the circular is fetched.", "status": "needs review"},
        {"id": "F05", "title": "Treaty withholding percentages not verified", "detail": "The 1984 treaty documents page (S21) was fetched, but withholding articles were not. No treaty withholding rate is asserted in this session.", "status": "needs review"},
        {"id": "F06", "title": "Old CBP URL returns 404 (corrected)", "detail": "https://www.cbp.gov/travel/international-visitors/bringing-money-or-monetary-instruments returns 404 (fetched this session). Correct page is S18. Prior dashboards linking the old URL should be updated by their owners.", "status": "needs review"},
        {"id": "F07", "title": "Ladder R02 USD 7 step is stale; Bittner per-report rule search-surfaced", "detail": "Ladder R02 cites USD 7 as a general Global Transfer price; current tariff USD 7 is education-payment only (S20 2.2.7). Separately, the Bittner per-report non-willful rule is cited from the IRM 4.26.16 transmittal via search, not a direct body fetch this session.", "status": "needs review"},
        {"id": "F08", "title": "Reference-rate sensitivity (7.129 vs 7.1)", "detail": "This session and repatriate/briefing use IRS 2025 average 7.129 (S19); ladder uses 7.1. Same CNY 620 cap → $86.97 vs $87.32. Difference is purely the reference rate, explained in the reconciliation table.", "status": "needs review"},
        {"id": "F09", "title": "Bank wire-splitting practice unknown", "detail": "M01 assumes one wire. If the bank splits a large remittance into N wires, the fee is N x per-wire fee (see split-wire sensitivity column). No source publishes a per-transfer ceiling for documented-income wires.", "status": "needs review"},
        {"id": "F10", "title": "Stale open PRs #2 / #12 / #17", "detail": "Three PRs from other sessions remain OPEN (checked 2026-11-10 via gh). This session inspects and logs only; it does not merge or close them. Their cost-increment request is already published on main (repatriate 680 rows, ladder 600 rows).", "status": "needs review"},
    ]}
(HERE / "flags.json").write_text(json.dumps(flags_doc, indent=1) + "\n")

print(f"costs: {len(COSTS)} tiers; methods: {len(METHODS)}; findings: {len(findings)}; sources: {len(sources)}")
print(f"recon max |diff vs repatriate|: {max(abs(r['diff_repatriate']) for r in recon):.2f}")
print(f"recon max |diff vs ladder|: {max(abs(r['diff_ladder']) for r in recon):.2f}")
