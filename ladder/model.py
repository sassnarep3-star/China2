#!/usr/bin/env python3
"""Deterministic CNY->USD cost ladder, $10,000 to $400,000 in $10,000 steps.

Every published figure carries a source id. Every figure that is NOT published
is either None (rendered blank) or lives in ASSUMPTIONS with an explicit
"model assumption" status. Nothing is inferred silently.

Run:  python3 ladder/model.py
Out:  ladder/data/sources.json, routes.json, costs.json, costs.csv, meta.json
"""
from __future__ import annotations

import csv
import json
import math
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
RETRIEVED = "2026-11-10"

# ---------------------------------------------------------------------------
# FX handling. All tables are in USD. CNY amounts appear only in bank tariffs,
# so they are converted with a *stated* rate; the ladder itself never depends
# on a live exchange rate.
# ---------------------------------------------------------------------------
FX = {"rate": 7.10, "low": 6.80, "high": 7.40,
      "note": "Illustrative CNY per USD, used only to express CNY-denominated "
              "fee caps in USD. Not a quote (IRS 2025 avg is 7.129; Fed H.10 "
              "noon buying rate on 2026-11-06 was 6.6760). Ladder tiers are "
              "USD-denominated, so no exchange-rate forecast is embedded."}

TIERS = list(range(10_000, 400_001, 10_000))


def cny(v: float, rate: float = FX["rate"]) -> float:
    """CNY -> USD at the stated illustrative rate."""
    return v / rate


# ---------------------------------------------------------------------------
# SOURCES. retrieval: "direct" = page/PDF body retrieved in this session;
# "search" = official-domain document surfaced with quoted body text but not
# re-fetched end-to-end in this session.
# ---------------------------------------------------------------------------
SOURCES = [
    dict(id="S01", jur="PRC", authority="People's Bank of China (PBOC)",
         title="Administrative Rules on Individuals' Foreign Exchange, PBOC Decree [2006] No. 3",
         url="https://www.pbc.gov.cn/english/130733/2025080815071447034/index.html",
         lang="EN", retrieval="direct", status="verified",
         locator="Arts. 2, 7, 9, 13, 14, 15, 22",
         quote="Art. 7: banks and individuals “must not evade limit administration by splitting "
               "large amount into small batches or tamper with authenticity administration by using "
               "fabricated commercial bills or vouchers.” Art. 13: a non-domestic individual may "
               "convert legitimate RMB current-account income and remit it abroad on presenting valid "
               "ID and relevant documents.",
         used_for="Legal basis for the documented-income route; anti-splitting prohibition."),
    dict(id="S02", jur="PRC", authority="State Administration of Foreign Exchange (SAFE)",
         title="Implementation Rules of the Measures for the Administration of Individual Foreign Exchange (Hui Fa [2007] No. 1, as amended)",
         url="https://www.safe.gov.cn/tianjin/2024/0430/2464.html",
         lang="ZH", retrieval="direct", status="verified",
         locator="Arts. 2, 10, 11, 13, 14, 15, 20, 30, 31; repeal note for Art. 39",
         quote="Art. 2: annual aggregate of USD 50,000 per person applies to individuals' FX sales and "
               "to domestic individuals' FX purchases. Art. 13(1): non-domestic individual converting "
               "lawful RMB current-account income must present ID plus transaction-amount documents "
               "(including tax vouchers). Art. 20: emigration/inheritance transfers follow the separate "
               "2004 measure.",
         used_for="50k quota scope, non-domestic conversion paperwork, cash deposit/withdrawal limits."),
    dict(id="S03", jur="PRC", authority="SAFE",
         title="Notice on Regulating Large Cash Withdrawals Abroad with Bank Cards (Hui Fa [2017] No. 29)",
         url="https://www.safe.gov.cn/safe/2017/1230/8116.html",
         lang="ZH", retrieval="direct", status="verified",
         locator="Arts. 1, 4",
         quote="Art. 1: aggregate overseas cash withdrawals on a person's domestic bank cards may not "
               "exceed the equivalent of RMB 100,000 per calendar year. Art. 4: per card per day capped "
               "at the equivalent of RMB 10,000.",
         used_for="Card/ATM route caps."),
    dict(id="S04", jur="PRC", authority="State Council of the PRC",
         title="Regulations of the PRC on Foreign Exchange Administration (State Council Decree No. 532)",
         url="https://www.safe.gov.cn/safe/2008/0806/5321.html",
         lang="ZH", retrieval="direct", status="verified",
         locator="Arts. 12, 39, 40, 42, 45, 48, 52",
         quote="Art. 39: evasion of FX control — fine of up to 30% of the amount, or 30% up to the "
               "equivalent amount if serious. Art. 42: illegal carriage of FX across the border — warning "
               "and fine of up to 20%. Art. 45: private/illegal FX trading — confiscation plus fine up to "
               "30%, or 30% to 100% if serious. Art. 52(2): “domestic individual” includes a foreign "
               "national who has resided continuously in China for one year or more.",
         used_for="Penalty exposure for unlawful routes; residence-based definition of 境内个人."),
    dict(id="S05", jur="PRC", authority="PBOC / SAFE",
         title="Provisional Rules for Personal Asset Outbound Transfers (PBOC [2004] No. 16) as simplified by SAFE Huifa [2014] No. 2",
         url="https://www.pbc.gov.cn/english/130721/2025080815062856255/index.html",
         lang="EN", retrieval="direct", status="verified",
         locator="PBOC [2004] Arts. 2, 6, 8–11; simplified by SAFE Huifa [2014] No. 2 §VI (safe.gov.cn/en/2014/0801/741.html)",
         quote="PBOC [2004] Arts. 2–11 cover pre-emigration and inherited assets with local SAFE "
               "approval and direct bank remittance to the applicant's overseas account. SAFE Huifa "
               "[2014] No. 2 §VI cancelled the >RMB 500,000 SAFE head-office filing and cancelled the "
               "multi-installment requirement so banks may remit in a lump sum or in batches within the "
               "approved limit.",
         used_for="Emigration and inheritance transfer routes, lump-sum remittance and local SAFE approval."),
    dict(id="S06", jur="PRC (commercial)", authority="HSBC Bank (China) Company Limited",
         title="Account and Service Tariff, Personal Customers (effective 1 January 2021)",
         url="https://www.hsbc.com.cn/content/dam/hsbc/cn/docs/document-download/account-service-rates-cn.pdf",
         lang="ZH", retrieval="direct", status="verified",
         locator="Items 5.1.1.1, 5.1.1.2, 5.1.1.3, 5.1.1.4, 5.3.1, 3.1.1",
         quote="5.1.1.1 outward telegraphic transfer: 0.1% of the remittance amount, minimum CNY 100, "
               "maximum CNY 500 per transaction, plus cable fee. 5.1.1.2 cable fee: CNY 120 per "
               "transaction. 5.1.1.4 cash-to-remittance conversion: 1% of the foreign-currency amount "
               "(waived for Premier). 5.3.1 same-name HSBC Global Transfer: free for Premier; reference "
               "CNY 50, actual USD 7 per transaction. 3.1.1 foreign cash withdrawal: 0.25%-0.4%, "
               "minimum CNY 40.",
         used_for="Superseded for the wire, cable, cash-notes and Global Transfer items by S21 "
                 "(effective 31 Oct 2026). Retained verbatim for the audit trail. A commercial tariff, "
                 "not a regulator's figure, and not a quote for any specific account."),
    dict(id="S07", jur="PRC", authority="National People's Congress / State Taxation Administration",
         title="Individual Income Tax Law of the PRC (2018 revision)",
         url="https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html",
         lang="ZH", retrieval="direct", status="verified",
         locator="Arts. 1, 2, 3, 6, 10, 15",
         quote="Art. 3: comprehensive income 3%-45% progressive; business income 5%-35%; interest, "
               "dividends, property leasing, property transfer and incidental income 20% flat. Art. 15: "
               "on transfer of immovable property the tax authority verifies IIT and the registration "
               "body checks the tax payment certificate.",
         used_for="PRC tax rates that can arise before (not because of) a conversion."),
    dict(id="S08", jur="PRC", authority="State Taxation Administration",
         title="Enterprise Income Tax Law of the PRC",
         url="https://fgk.chinatax.gov.cn/eng/c102962/c102967/c102997/c103003/c5245840/content.html",
         lang="EN", retrieval="direct", status="verified",
         locator="Arts. 3, 4",
         quote="Art. 4: “The rate of enterprise income tax shall be 25 percent.” Non-resident enterprises "
               "without an establishment are taxed at 20% on China-sourced income.",
         used_for="Company-level tax that precedes a dividend repatriation."),
    dict(id="S09", jur="US / PRC", authority="US Treasury / Internal Revenue Service",
         title="United States - People's Republic of China Income Tax Convention (1984, protocols 1986)",
         url="https://www.irs.gov/pub/irs-trty/china.pdf",
         lang="EN", retrieval="direct", status="verified",
         locator="Arts. 9, 10, 11, 22",
         quote="Dividends, interest and royalties derived by a resident of the other contracting state "
               "are taxed at no more than 10 percent.",
         used_for="Treaty ceiling on dividend/interest/royalty withholding; FTC relief."),
    dict(id="S10", jur="US", authority="Internal Revenue Service",
         title="Report of Foreign Bank and Financial Accounts (FBAR)",
         url="https://www.irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar",
         lang="EN", retrieval="direct", status="verified",
         locator="“Who must file”",
         quote="A U.S. person must file an FBAR if the aggregate value of foreign financial accounts "
               "“exceeded $10,000 at any time during the calendar year reported.”",
         used_for="US reporting obligation triggered by holding the account, not by converting."),
    dict(id="S11", jur="US", authority="Internal Revenue Service",
         title="Do I need to file Form 8938, Statement of Specified Foreign Financial Assets?",
         url="https://www.irs.gov/businesses/corporations/do-i-need-to-file-form-8938-statement-of-specified-foreign-financial-assets",
         lang="EN", retrieval="search", status="verified",
         locator="Reporting thresholds",
         quote="Unmarried taxpayer living in the US: more than $50,000 on the last day of the tax year "
               "or more than $75,000 at any time. Married filing jointly living in the US: more than "
               "$100,000 / $150,000.",
         used_for="Second US asset-reporting threshold set."),
    dict(id="S12", jur="US", authority="Internal Revenue Service",
         title="Publication 514, Foreign Tax Credit for Individuals",
         url="https://www.irs.gov/publications/p514",
         lang="EN", retrieval="search", status="verified",
         locator="Limit on the credit",
         quote="The foreign tax credit “can only reduce U.S. taxes on foreign source income; it cannot "
               "reduce U.S. taxes on U.S. source income,” and is limited by the Form 1116 fraction.",
         used_for="Why PRC tax already paid usually does not create a second US tax on the same income."),
    dict(id="S13", jur="US", authority="US Customs and Border Protection",
         title="Money and Other Monetary Instruments",
         url="https://www.cbp.gov/travel/international-visitors/money-monetary-instruments",
         lang="EN", retrieval="direct", status="verified",
         locator="Federal mandate to report currency exceeding $10,000",
         quote="Anyone who brings, sends or receives currency or monetary instruments totalling more "
               "than $10,000 at one time into or out of the United States must report it on FinCEN "
               "Form 105. Failure risks forfeiture and civil or criminal penalties.",
         used_for="Physical-cash route reporting duty (a report, not a tax)."),
    dict(id="S14", jur="US", authority="FinCEN / eCFR",
         title="31 CFR 1010.350 — Reports of foreign financial accounts",
         url="https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-C/section-1010.350",
         lang="EN", retrieval="direct", status="verified",
         locator="(a), (b), (e)",
         quote="Each United States person with a financial interest in, or signature authority over, a "
               "foreign bank, securities or other financial account must report that relationship.",
         used_for="Statutory basis of FBAR, including accounts held in the person's own name."),
    dict(id="S15", jur="PRC", authority="SAFE / General Administration of Customs",
         title="Provisional Measures on Carrying Foreign Currency Cash Across the Border (Hui Fa [2003] No. 102)",
         url="https://www.safe.gov.cn/safe/2003/0828/5444.html",
         lang="ZH", retrieval="direct", status="verified",
         locator="Point II",
         quote="Carrying out foreign cash up to the equivalent of USD 5,000 requires no permit; "
               "USD 5,000-10,000 requires a bank-issued carrying certificate; in principle no more than "
               "the equivalent of USD 10,000 may be carried out except in listed special cases approved "
               "by SAFE.",
         used_for="Cash-carrying route cap."),
    dict(id="S16", jur="PRC", authority="PBOC and seven other departments",
         title="Notice on Further Preventing and Handling Risks Related to Virtual Currency (Yin Fa [2026] No. 42)",
         url="https://www.pbc.gov.cn/tiaofasi/144941/3581332/2026020619591971323/index.html",
         lang="ZH", retrieval="direct", status="verified",
         locator="Points (1), (2), (6); final article",
         quote="Virtual currency has no legal-tender status; exchanging legal tender for virtual currency "
               "is an illegal financial activity and is strictly prohibited; financial institutions may "
               "not provide account, settlement or transfer services for it. This notice repeals Yin Fa "
               "[2021] No. 237.",
         used_for="Why crypto/USDT off-ramps are not a lawful route out of CNY."),
    dict(id="S17", jur="PRC", authority="SAFE Tianjin branch",
         title="2026 FX administration Q&A, individual FX (10): conversion back of unused RMB",
         url="https://www.safe.gov.cn/tianjin/2026/0917/3134.html",
         lang="ZH", retrieval="direct", status="verified",
         locator="Answer citing Guideline Hui Fa [2020] No. 14, Art. 60",
         quote="A non-domestic individual may convert unused RMB back to FX on presenting valid ID and "
               "the original exchange memo, valid for 24 months from the exchange date; same-day "
               "conversions up to USD 500 (or USD 1,000 at a port-side location before departure) may be "
               "handled on ID alone.",
         used_for="Current restatement of the re-conversion rule and the 500/1,000 documentary "
                 "exemptions."),
    dict(id="S18", jur="PRC", authority="SAFE",
         title="Notice on Further Improving Individual Foreign Exchange Administration (Hui Fa [2015] No. 49)",
         url="https://www.safe.gov.cn/safe/2015/1231/5442.html",
         lang="ZH", retrieval="search", status="needs review",
         locator="Art. 2; “watch list”",
         quote="Individuals may not evade quota or authenticity administration by splitting. Borrowing "
               "another person's quota leads to a “watch list”, which lasts the current year plus two "
               "years.",
         used_for="Consequences of quota-splitting. STATUS NOTE: a SAFE mirror page labels this notice "
                 "“已废止” (repealed) while another SAFE page still publishes it without that label; the "
                 "anti-splitting rule itself is independently stated in S01 Art. 7 and S04.",
         flag="F03"),
    dict(id="S19", jur="PRC", authority="SAFE",
         title="Catalogue of Currently Effective Major Foreign Exchange Regulations (as at 30 June 2026)",
         url="https://www.safe.gov.cn/safe/file/file/20260805/d2d0d6ce1441436eadc8bc600eb79c43.pdf",
         lang="ZH", retrieval="direct", status="verified",
         locator="Items 1-3, 18-19, 30, 38, 97",
         quote="Lists State Council Decree No. 532, PBOC Decree [2006] No. 3, Hui Fa [2007] No. 1, "
               "Hui Fa [2003] No. 102, Hui Fa [2020] No. 14, Hui Fa [2014] No. 2, and PBOC Announcement "
               "[2004] No. 16 as currently effective.",
         used_for="Confirms the core FX instruments and capital-account simplifications remain in force as at mid-2026."),
    dict(id="S20", jur="PRC", authority="SAFE Beijing branch",
         title="Current-account FAQ: how a non-domestic individual purchases FX",
         url="https://www.safe.gov.cn/beijing/file/file/20191127/b29df7fa63504266b9ccb23429185d40.pdf",
         lang="ZH", retrieval="search", status="verified",
         locator="Question 5",
         quote="A non-domestic individual purchasing FX for lawful RMB current-account income presents "
               "valid ID plus documents proving the transaction amount, including tax vouchers; unused "
               "RMB is converted back against the original exchange memo.",
         used_for="Corroborates the documentary requirement in S02 Art. 13.",
         flag=None),
    dict(id="S21", jur="PRC (commercial)", authority="HSBC Bank (China) Company Limited",
         title="Tariff of Accounts and Services for Wealth and Personal Banking Business (effective 31 Oct 2026)",
         url="https://www.hsbc.com.cn/content/dam/hsbc/cn/docs/document-download/tariff-of-Accounts-services-for-personal-customers-v2.pdf",
         lang="EN", retrieval="direct", status="verified",
         locator="Items 2.2.2.1, 2.2.2.2, 2.2.4.1-2.2.4.4, 2.2.6.1, 2.2.6.2, 2.2.7",
         quote="2.2.4.1 Telegraphic Transfer Issuance: Private Banking individuals — Free; PB entity 0.1% min CNY100/max CNY1,000; Premier and Advance — 0.1% of remittance amount, minimum CNY100/equivalent, maximum CNY500/equivalent per transaction, plus cable charge. 2.2.4.2 cable charges: PB individuals Free; PB entity CNY140/equivalent per cable; Premier and Advance CNY120/equivalent per cable. 2.2.4.3 additional cable messages: PB individuals Free; otherwise CNY100/equivalent per page. 2.2.4.4 amendment/cancellation: PB individuals Free; otherwise up to 5 cables CNY200/equivalent, each additional cable CNY40/equivalent, plus overseas bank charge. 2.2.2.1 Foreign Currency Notes Withdrawal over the counter: Free for PB, Premier and Advance; for USD/HKD, withdrawals of at least USD5,000 equivalent need at least three working days' advance notice. 2.2.2.2 Cash Exchange (foreign-currency notes): PB Free; Premier and Advance Free for HSBC Group customers (self-named HSBC card/statement). 2.2.6.1 Global Transfer to self-name HSBC accounts in other countries/territories: Free (PB), Free (Premier); Advance CNY145 per transaction (indicative — actual charge USD20 or equivalent). Service available only in countries/territories offering Global Transfer to Self (tariff remark lists Canada, US, UK, Australia and Hong Kong SAR); not applicable to PB entity customers. 2.2.6.2 Global Transfer to Family (same HSBC Premier Family): Free / Free / Not applicable. 2.2.7 HSBC International Education Payment: Free / Free / Advance CNY50 indicative (actual USD7) — a platform-specific item, not a general same-name remittance fee. Charges exclude other institutions and authorities.",
         used_for="Current (31 Oct 2026) schedule used for cost modelling; supersedes the affected items in S06. A commercial tariff; excludes other institutions' charges and is not a quote for any specific account."),
]

# ---------------------------------------------------------------------------
# MODEL ASSUMPTIONS. These are NOT published figures. They are printed on the
# site as assumptions, with a range, so a reader can reject them.
# ---------------------------------------------------------------------------
ASSUMPTIONS = [
    dict(id="A1", topic="CNY/USD used to express CNY fee caps",
         value="7.10 CNY per USD (band 6.80-7.40)", status="model assumption",
         why="Bank tariffs are denominated in CNY. Only the CNY 100 / 500 / 120 caps are affected; "
             "at 400,000 USD the whole cap swing is under 15 USD (IRS 2025 avg = 7.129; Fed H.10 "
             "noon buying rate 2026-11-06 = 6.6760). No rate forecast is used anywhere."),
    dict(id="A2", topic="FX spread on a bank wire", value="0.30%-1.50% of principal",
         status="model assumption",
         why="No published executable CNY/USD customer quote was obtained for any account, so a band is "
             "modelled instead of a number. This is the single largest cost component and must be "
             "replaced by the bank's own executable quote before acting."),
    dict(id="A3", topic="FX spread on cash / counter conversion", value="0.80%-3.00%",
         status="model assumption",
         why="Banknote spreads are wider than telegraphic spreads; no published cash quote was obtained."),
    dict(id="A4", topic="FX spread on card / ATM settlement", value="0.00%-3.00%",
         status="model assumption",
         why="Card scheme settlement rates and issuer foreign-transaction fees vary; none was verified "
             "for this account."),
    dict(id="A5", topic="FX spread offshore (CNH) before USD", value="0.20%-1.00%",
         status="model assumption",
         why="Offshore spreads are narrower in normal conditions; eligibility for an individual to move "
             "RMB offshore was not verified (see F05)."),
    dict(id="A6", topic="Fixed fees at banks other than HSBC China",
         value="same as the HSBC China published tariff", status="model assumption",
         why="Modelling uses S21 (HSBC China tariff effective 31 Oct 2026); S06 (effective 2021-01-01) "
             "is retained for audit history. Other banks publish different tariffs; substitute your own "
             "bank's schedule."),
    dict(id="A7", topic="Number of wires per tier", value="one wire per tranche",
         status="model assumption",
         why="No per-transfer ceiling for a non-domestic individual remittance was verified, so the "
             "model does not invent one. If your bank splits a large remittance, multiply the fixed fee."),
    dict(id="A8", topic="US side cost of compliance", value="not modelled (blank)",
         status="unverified - left blank",
         why="Preparer fees for FBAR / Form 8938 / Form 1116 vary by provider and were not verified. "
             "Filing itself has no fee. The exposure is the penalty for not filing."),
    dict(id="A9", topic="PRC tax actually payable on the balance", value="not modelled (blank)",
         status="unverified - left blank",
         why="Tax depends on the character of the underlying income and on what was already withheld. "
             "The ladder shows statutory rates and marks the resulting cell as exposure, not a bill."),
]

# ---------------------------------------------------------------------------
# USEFUL CHANNEL PRIMITIVES, all traceable to S21 (HSBC China tariff, effective 31 Oct 2026).
# ---------------------------------------------------------------------------
WIRE_PCT = 0.001          # S21 item 2.2.4.1 (Premier/Advance); PB individuals are Free
WIRE_MIN = cny(100)       # S21 item 2.2.4.1
WIRE_MAX = cny(500)       # S21 item 2.2.4.1 (PB entity max is CNY1,000; modelled segments are Premier/Advance)
CABLE = cny(120)          # S21 item 2.2.4.2 (PB individuals Free)
GLOBAL_XFER = 0.00        # S21 item 2.2.6.1: Free for PB and Premier same-name Global Transfer to
                          # self-name overseas HSBC accounts. Advance pays CNY145 indicative per
                          # transaction (actual USD20); the modelled route requires Premier.
                          # (S06 item 5.3.1 "USD 7" was the 2021 reference price tied to International
                          # Education Payment; superseded by S21 item 2.2.7.)
NOTES_WITHDRAWAL_FEE = 0.00  # S21 item 2.2.2.1: foreign-currency notes withdrawal over the counter Free
                             # (PB/Premier/Advance). USD/HKD >= USD5,000 equivalent needs >=3 working
                             # days' advance notice.

ATM_YEAR_CAP = cny(100_000)   # S03 Art. 1  (RMB 100k/person/year)
ATM_DAY_CAP = cny(10_000)     # S03 Art. 4  (RMB 10k/card/day)
CASH_EXPORT_CAP = 5_000       # S15
SPLIT_DAILY_CAP = 500         # S17
AIRPORT_DAILY_CAP = 1_000     # S17


def wire_fee(amount: float) -> float:
    """One outward telegraphic transfer, HSBC China tariff as in S21 (items 2.2.4.1-2.2.4.2)."""
    return min(max(WIRE_PCT * amount, WIRE_MIN), WIRE_MAX) + CABLE


# ---------------------------------------------------------------------------
# ROUTES. fee="wire" / "global" / "cash" / "atm" / "card" / "none".
# cap = documented per-transaction or per-period ceiling in USD (None = none found).
# tax = (low, high) statutory PRC rate on the underlying amount, or None.
# ---------------------------------------------------------------------------
ROUTES = [
    dict(
        id="R01", name="Documented after-tax income: bank FX conversion + SWIFT wire",
        short="Documented income → SWIFT",
        group="Lawful · primary",
        status="lawful",
        who="A US citizen who can prove the RMB came from lawful current-account income on which PRC "
            "individual income tax was already paid or withheld.",
        basis=["S01", "S02", "S20"], fee="wire", cap=None,
        spread="wire", tax=(0.0, 0.0), tax_note="No PRC tax arises from converting money that has "
        "already borne PRC tax. Additional PRC tax is due only if the underlying income was never taxed.",
        time="1-10 business days", time_days=(1, 10),
        docs=["Passport", "Employment contract or service invoice/payment proof", "PRC IIT payment "
              "record / tax certificate (完税证明 / 纳税记录)", "Bank card and account opening documents",
              "Source-of-funds statement for the receiving US bank"],
        steps=[
            "Download your personal IIT payment record from the PRC individual income tax app or "
            "request a 完税证明 at the tax service hall for the years the balance was earned.",
            "Assemble the income file: contract or invoices, payslips, bank statements showing the "
            "credits, and the tax record. Amounts must tie to the balance.",
            "Book a counter appointment at the account-holding branch (foreign-exchange business is "
            "not reliably transacted at a machine for this category).",
            "Ask for an executable all-in quote: the USD selling rate applied, the 0.1% commission "
            "with its CNY 100/500 floor and cap, and the CNY 120 cable fee (Private Banking "
            "individuals: issuance and cable are Free under the 31 Oct 2026 tariff).",
            "Complete the FX purchase; keep the exchange memo (水单) — it is the document that proves "
            "the conversion was authorised and is needed for any later re-conversion.",
            "Instruct the wire to your own US account. Keep the SWIFT MT103 / remittance advice.",
            "File FBAR (FinCEN 114) by 15 April and Form 8938 with your return if thresholds are met; "
            "claim PRC tax on Form 1116.",
        ],
        pros=["No USD 50,000 ceiling: the cap is the size of the documented lawful income.",
              "Zero incremental PRC tax once the underlying tax is paid; PRC tax already paid is "
              "creditable in the US on Form 1116.",
              "Clean audit trail for both SAFE and the receiving US bank."],
        cons=["Requires tax and income paperwork that many people have never collected.",
              "Counter review is discretionary; a thin file is refused.",
              "You bear the bank's spread, which is not published in advance."],
    ),
    dict(
        id="R02", name="Documented income routed through same-name HSBC Global Transfer",
        short="Documented income → Global Transfer",
        group="Lawful · primary",
        status="lawful",
        who="As R01, but you already hold, or can open, an HSBC account in the US and an HSBC China "
            "Premier relationship.",
        basis=["S01", "S02", "S21"], fee="global", cap=None,
        spread="wire", tax=(0.0, 0.0),
        tax_note="Same tax analysis as R01: conversion of already-taxed income adds no PRC tax.",
        time="1-5 business days", time_days=(1, 5),
        docs=["Everything in R01", "HSBC US account in the same name", "Eligible HSBC China tier "
              "(Private Banking / Premier / Advance) confirmed on both sides"],
        steps=[
            "Confirm both accounts are in exactly the same name and that Global Transfer is enabled "
            "for the China-US corridor.",
            "Complete the R01 documentation and FX conversion inside HSBC China.",
            "Use Global Transfer to move the USD to your own HSBC US account: free for Private Banking "
            "and Premier under the tariff effective 31 Oct 2026 (item 2.2.6.1). Advance pays CNY145 "
            "indicative per transaction (actual USD20 or equivalent). Available only where Global "
            "Transfer to Self is offered — the tariff remark lists Canada, US, UK, Australia and Hong "
            "Kong SAR.",
            "Keep the transfer confirmation as the audit trail; the receiving bank still needs a "
            "source-of-funds note.",
            "File FBAR / Form 8938 / Form 1116 as in R01.",
        ],
        pros=["No published fixed fee for a Private Banking/Premier same-name Global Transfer (Free "
              "under the current tariff, item 2.2.6.1).",
              "Same-bank transfer reduces correspondent-bank deductions and intermediary questions."],
        cons=["Requires an eligible HSBC relationship on both sides; Premier has balance conditions.",
              "The spread on the CNY→USD leg is unchanged and remains the dominant cost.",
              "Account opening for a US person at a Chinese bank is subject to enhanced due diligence."],
    ),
    dict(
        id="R03", name="Re-conversion of unused RMB bought with foreign currency (original exchange memo)",
        short="Re-conversion with exchange memo",
        group="Lawful · conditional",
        status="lawful",
        who="A US citizen whose RMB came from converting USD or another currency inside China, and who "
            "still holds the original exchange memo, within 24 months.",
        basis=["S02", "S17"], fee="wire", cap=None,
        spread="wire", tax=(0.0, 0.0),
        tax_note="Return of previously settled principal; no PRC income tax and no tax voucher is "
        "required for this category.",
        time="1-10 business days", time_days=(1, 10),
        docs=["Passport", "Original exchange memo (原兑换水单), within 24 months", "Bank statements "
              "showing the original conversion"],
        steps=[
            "Locate the original exchange memo for each conversion you now want to reverse.",
            "Check the date: the memo is valid for 24 months from the exchange date.",
            "Present the passport and memo at the counter and request conversion back to the original "
            "currency, then remit.",
            "Keep the new memo; it is the receipt for the outbound leg.",
        ],
        pros=["No tax certificate needed — the cleanest documentary path when it applies.",
              "No cap other than the amount of the original conversion."],
        cons=["Only works to the extent you converted FX into RMB in the first place.",
              "Strict 24-month window; expired memos push you back to R01.",
              "You pay a round-trip spread, so this is a recovery route, not a way to move earned income."],
    ),
    dict(
        id="R04", name="Passport-only small-amount unused-RMB reconversion at a bank counter",
        short="Small-amount unused-RMB reconversion (USD 500/day)",
        group="Lawful · small balance only",
        status="lawful",
        who="A non-domestic individual reconverting unused RMB that was previously exchanged from "
            "foreign currency (Guidelines Art. 60 / Hui Fa [2007] Art. 13(2) — NOT a general allowance "
            "for salary or savings).",
        basis=["S02", "S17"], fee="cash", cap=SPLIT_DAILY_CAP,
        spread="cash", tax=(0.0, 0.0),
        tax_note="No tax at the counter, but the exemption is strictly for reconverting unused RMB "
        "previously converted from FX; it does not make untaxed earned income eligible.",
        time="one banking day per USD 500", time_days=None,
        docs=["Passport"],
        steps=[
            "Confirm the RMB represents unused funds from an earlier FX-to-RMB conversion.",
            "Attend a branch counter with your passport.",
            "Request reconversion of no more than the equivalent of USD 500 in one day (or present "
            "the original exchange memo within 24 months under R03 for larger unused amounts).",
            "Do not repeat small daily conversions to evade documentation or limits on earned RMB: "
            "S01 Art. 7 and S04 prohibit splitting transactions to evade control.",
        ],
        pros=["No exchange memo required up to USD 500/day when reconverting unused RMB.",
              "Immediate settlement."],
        cons=["Applies only to previously exchanged unused RMB, NOT earned RMB wages or savings.",
              "USD 500 per day: 20 banking days for USD 10,000 and 800 for USD 400,000; cash spreads "
              "are wide, and repeated splitting to evade controls violates S01 Art. 7."],
    ),
    dict(
        id="R05", name="Airside pre-departure unused-RMB reconversion at a port-side counter",
        short="Airport-side unused-RMB reconversion (USD 1,000/day)",
        group="Lawful · small balance only",
        status="lawful",
        who="A departing non-domestic individual reconverting unused previously exchanged RMB at a "
            "port-side counter before departure (境内关外).",
        basis=["S17"], fee="cash", cap=AIRPORT_DAILY_CAP,
        spread="cash", tax=(0.0, 0.0),
        tax_note="Same unused-RMB reconversion rule as R04.",
        time="one departure per USD 1,000", time_days=None,
        docs=["Passport", "boarding pass"],
        steps=[
            "Reconvert no more than the equivalent of USD 1,000 of unused RMB in a single day at a "
            "port-side counter before departure.",
            "Declare the cash to US CBP on FinCEN Form 105 if you arrive with more than USD 10,000 in "
            "total (S13).",
            "Do not treat repeated trips as a transfer mechanism.",
        ],
        pros=["Higher daily reconversion limit than an onshore counter."],
        cons=["Applies only to unused previously exchanged RMB; USD 1,000 per departure trip.",
              "Requires physically moving cash, with CBP reporting and seizure risk for errors."],
    ),
    dict(
        id="R06", name="Withdraw USD cash in China and carry it out",
        short="Carry USD cash out",
        group="Lawful · capped, impractical",
        status="lawful",
        who="Any individual, up to the cash-carrying ceiling.",
        basis=["S21", "S15", "S13"], fee="cashcarry", cap=CASH_EXPORT_CAP,
        spread="cash", tax=(0.0, 0.0),
        tax_note="Carrying cash is not a taxable event in itself; it also does not discharge any "
        "unpaid PRC or US tax.",
        time="one trip per USD 5,000", time_days=None,
        docs=["Passport", "Bank withdrawal slip", "Carrying certificate for USD 5,000-10,000",
              "FinCEN Form 105 on arrival above USD 10,000"],
        steps=[
            "Convert or withdraw USD notes at the counter. Under the tariff effective 31 Oct 2026, "
            "foreign-currency notes withdrawal over the counter is Free for Private Banking, Premier and "
            "Advance (item 2.2.2.1); USD/HKD withdrawals of at least USD5,000 equivalent need at least "
            "three working days' advance notice. CNY-to-notes conversion uses the notes buy/sell board "
            "rates, whose margin is the modelled cash spread above.",
            "Above USD 5,000 and up to USD 10,000, obtain a bank carrying certificate before departure.",
            "Above USD 10,000 a SAFE-issued certificate is required and is granted only in listed "
            "special cases.",
            "Declare to CBP on arrival above USD 10,000 in aggregate.",
            "Deposit in the US and keep the withdrawal and declaration records.",
        ],
        pros=["$0 published counter withdrawal fee (S06 item 2.2.2.1) and no tax certificate for "
              "already-held FX cash.", "Works within USD 5,000/trip without an outbound permit."],
        cons=["USD 5,000 per trip without a certificate: 80 trips for USD 400,000 (repeat exits face "
              "stricter Huifa [2003] No. 102 limits).",
              "Physical risk plus US forfeiture exposure for failing to file FinCEN 105 (S13).",
              "Widest spread of any channel (notes buy/sell board rate applies for cross-currency)."],
    ),
    dict(
        id="R07", name="Emigration asset transfer (移民财产转移)",
        short="Emigration transfer",
        group="Lawful · capital account",
        status="lawful",
        who="A natural person who emigrated from mainland China (or moved to Hong Kong/Macao) and is "
            "transferring lawful pre-emigration assets (requires household-registration cancellation; "
            "most US-born individuals without former PRC hukou do not qualify).",
        basis=["S05", "S02"], fee="wire", cap=None, staged=False,
        spread="wire", tax=(0.0, 0.0),
        tax_note="The transfer itself is not a tax; the tax authority's clearance on the realised "
        "assets is required and the applicable rate depends on the asset (for property, 20% of the gain "
        "under S07 Art. 3(3)).",
        time="1-6 months (lump sum or batches after local SAFE approval)", time_days=(30, 180),
        docs=["Written application stating the reason and a full account of source and realisation",
              "Proof of emigration status and PRC household-registration (hukou) cancellation",
              "Proof of ownership and realisation of the assets",
              "PRC tax clearance certificate for the assets"],
        steps=[
            "Apply once, to the local SAFE branch where your pre-emigration household registration was, "
            "for the whole amount you intend to move.",
            "Settle the PRC tax position on the realised assets and obtain the tax certificate.",
            "Obtain local SAFE branch approval: SAFE Circular Huifa [2014] No. 2 §VI cancelled the "
            "prior requirement to escalate amounts above RMB 500,000 to SAFE head office.",
            "Remit via the designated bank directly to your own overseas account: Huifa [2014] No. 2 "
            "§VI also cancelled the 2004 multi-stage installment rule, so the bank may remit in a lump "
            "sum or in batches within the approved limit (no domestic cash payout allowed).",
            "Keep every approval and remittance advice for the US side.",
        ],
        pros=["The only route designed to move a whole pre-emigration balance outside the annual quota.",
              "Lump-sum remittance permitted within the local SAFE branch's approved limit (Huifa [2014] "
              "No. 2 §VI)."],
        cons=["Requires actual emigration from Mainland China with hukou cancellation and asset "
              "realisation — generally inapplicable to US-born individuals who never held PRC hukou.",
              "Documentary and tax-clearance burden is heavy."],
    ),
    dict(
        id="R08", name="Inheritance asset transfer (继承财产转移)",
        short="Inheritance transfer",
        group="Lawful · capital account",
        status="lawful",
        who="A foreign citizen (including a US citizen) who has inherited assets in mainland China.",
        basis=["S05"], fee="wire", cap=None,
        spread="wire", tax=(0.0, 0.0),
        tax_note="China has no inheritance tax in the instruments verified here; the estate's own tax "
        "clearance is required and is checked before conversion.",
        time="1-6 months", time_days=(30, 180),
        docs=["Written application describing the relationship and the estate",
              "Application form signed by you or your agent", "Passport plus a certificate of overseas "
              "residence issued or authenticated by a Chinese embassy/consulate",
              "Proof of inheritance", "Proof of the deceased's title to the assets",
              "Tax certificate or payment proof issued by the tax authority where the assets are"],
        steps=[
            "Obtain the inheritance and title documents (Huifa [2014] No. 2 §VI(IV) simplified prior "
            "notarization rules for certain property-right/agency documents; confirm branch checklist).",
            "Obtain the tax certificate from the tax authority where the assets are located.",
            "File at the local SAFE branch where the decedent's household registration was (combined "
            "filing allowed for multiple decedents under Huifa [2014] No. 2 §VI(III)).",
            "Remit in one go or in batches once approved.",
            "Report the bequest in the US on Form 3520 if >$100,000 from a foreign estate/NRA (F07).",
        ],
        pros=["No annual quota; lump sum permitted; combined filing available across decedents."],
        cons=["Consular residence verification and estate tax clearance take time.",
              "Requires local SAFE approval and source/title documentation."],
    ),
    dict(
        id="R09", name="Sale proceeds of PRC residential property",
        short="Property sale proceeds",
        group="Lawful · capital account",
        status="lawful",
        who="A US citizen selling a property they own in mainland China.",
        basis=["S01", "S07"], fee="wire", cap=None,
        spread="wire", tax=(0.20, 0.20),
        tax_note="Property transfer income is taxed at 20% of the gain (proceeds less original value "
        "and reasonable costs) under S07 Arts. 3(3) and 6(5). Whether a exemption applies to a "
        "particular flat was not verified (F06).",
        time="3-12 months", time_days=(90, 365),
        docs=["Title certificate", "Sale contract and completion documents", "PRC tax payment "
              "certificate for the transfer (checked at registration under S07 Art. 15)",
              "Proof the property was self-use where an exemption is claimed"],
        steps=[
            "Complete the sale and settle PRC IIT: the registration authority will not transfer title "
            "without the tax clearance certificate (S07 Art. 15).",
            "Apply to the bank/SAFE for conversion of the net proceeds under the property rules.",
            "Convert and remit to your own US account.",
            "Report the disposition in the US and claim the PRC tax on Form 1116.",
        ],
        pros=["Moves a large sum in one transaction once the tax is settled.",
              "Tax is on the gain, not the price."],
        cons=["The 20% gain tax is the largest single number in this study.",
              "Specific FX paperwork for a non-domestic vendor's property proceeds was not verified "
              "in this session (F06).",
              "Months of process."],
    ),
    dict(
        id="R10", name="Dividends from a PRC company you own",
        short="Dividend repatriation",
        group="Lawful · capital account",
        status="lawful",
        who="A US citizen shareholder of a PRC company with distributable after-tax profits.",
        basis=["S08", "S07", "S09"], fee="wire", cap=None,
        spread="wire", tax=(0.10, 0.20),
        tax_note="Company-level EIT at 25% comes first (S08 Art. 4). The dividend then bears 20% "
        "domestic IIT, reduced to a 10% treaty ceiling for a US resident (S09 Arts. 9-11, S07 Art. 3(3)).",
        time="3-12 months", time_days=(90, 365),
        docs=["Audited financial statements and profit distribution resolution", "EIT payment proof",
              "Treaty residence certification for the 10% rate", "Tax withholding payment certificate"],
        steps=[
            "Confirm distributable profits after 25% EIT and statutory reserves.",
            "Pass the distribution resolution and withhold dividend tax at the treaty rate with the "
            "residence certificate in place.",
            "Obtain the withholding payment certificate.",
            "Convert and remit through the company's bank with the resolution and tax documents.",
            "Claim the 10% withholding on Form 1116 in the US.",
        ],
        pros=["Efficient once the company has already paid EIT.",
              "Treaty caps the dividend tax at 10%."],
        cons=["25% EIT plus 10% withholding is a combined burden on the profits.",
              "Excess withholding above the treaty rate is not creditable in the US.",
              "Requires a company, audited accounts and a board process."],
    ),
    dict(
        id="R11", name="Overseas ATM withdrawals on a PRC bank card",
        short="Overseas ATM withdrawals",
        group="Lawful · spending channel",
        status="lawful",
        who="Anyone holding a PRC-issued bank card.",
        basis=["S03"], fee="atm", cap=ATM_DAY_CAP,
        spread="card", tax=(0.0, 0.0),
        tax_note="No PRC tax at withdrawal; it does not discharge unpaid tax on the underlying income.",
        time="about 14,000 USD per calendar year per person", time_days=None,
        docs=["PRC bank card", "Passport for the receiving bank's KYC"],
        steps=[
            "Withdraw abroad within RMB 10,000 equivalent per card per day.",
            "Stay within RMB 100,000 equivalent per person per calendar year.",
            "Deposit the USD and keep the ATM receipts.",
        ],
        pros=["No application and no tax certificate.", "Useful for living costs, not for a balance."],
        cons=["RMB 100,000 a year is about USD 14,000: 29 years for USD 400,000.",
              "Exceeding the cap suspends overseas cash access for the rest of that year and the next.",
              "ATM operator fees were not verified (F08)."],
    ),
    dict(
        id="R12", name="Spend the RMB directly on overseas purchases with a PRC card",
        short="Card spending abroad",
        group="Lawful · spending channel",
        status="lawful",
        who="Anyone holding a PRC-issued card, for genuine current-account spending.",
        basis=["S02"], fee="card", cap=None,
        spread="card", tax=(0.0, 0.0),
        tax_note="Spending is not conversion income; it also does not settle unpaid tax on the source.",
        time="as you spend", time_days=None,
        docs=["PRC bank card", "Merchant receipts"],
        steps=[
            "Pay genuine overseas expenses (tuition, medical, travel, suppliers) directly with the card.",
            "Keep invoices: the merchant is being paid, so the underlying purpose is visible.",
        ],
        pros=["No quota and no application.", "Converts at the card scheme rate as you spend."],
        cons=["Only works if you have a matching expense stream.",
              "Not a way to obtain USD savings.",
              "Round-tripping purchases to extract cash can breach the cash-withdrawal rules."],
    ),
    dict(
        id="R13", name="Pay US obligations directly from the China account",
        short="Direct payment of US bills",
        group="Lawful · current account",
        status="lawful",
        who="Anyone with a genuine US invoice or obligation (tuition, hospital, tax, supplier).",
        basis=["S01", "S02", "S04"], fee="wire", cap=None,
        spread="wire", tax=(0.0, 0.0),
        tax_note="A current-account payment, not a transfer of your own savings; the tax sits with the "
        "underlying income, not with the payment.",
        time="1-10 business days", time_days=(1, 10),
        docs=["Invoice or tuition statement", "Proof of the obligation", "Passport", "The bank's "
              "current-account payment form"],
        steps=[
            "Obtain the genuine invoice from the US payee.",
            "Present it at the counter with your passport; current-account payments are convertible "
            "against the underlying document (S04 Art. 12, S02 Art. 11).",
            "Instruct the wire to the payee, not to yourself.",
            "Keep the invoice and payment advice together.",
        ],
        pros=["No quota and low friction when the document is genuine.",
              "Reduces the balance you ever need to repatriate."],
        cons=["Does not put money in your own account.",
              "Only limited by how much genuine US spending you actually have."],
    ),
    dict(
        id="R14", name="Move RMB offshore as CNH, then convert",
        short="Offshore RMB (CNH) then convert",
        group="Conditional · eligibility unverified",
        status="conditional",
        who="Potentially an individual eligible for cross-border RMB remittance. Eligibility for a "
            "non-resident US citizen was NOT verified in this session.",
        basis=["S02", "S21"], fee="wire", cap=None,
        spread="cnh", tax=(0.0, 0.0),
        tax_note="Conversion offshore does not create PRC tax, and does not cure an untaxed onshore "
        "balance. Moving RMB out still requires a compliant onshore basis.",
        time="unknown", time_days=None,
        docs=["Not established in this session - see F05"],
        steps=[
            "Do not act on this route until the onshore basis for moving RMB to Hong Kong is confirmed "
            "in writing by the bank and, if needed, SAFE.",
            "If a basis exists, convert in the offshore market and remit USD to the US.",
        ],
        pros=["Offshore spreads are typically narrower.", "HSBC group transfers can be free for Premier."],
        cons=["Eligibility for a non-resident individual was not verified.",
              "Guessing the basis is exactly how people end up in an Art. 39 or Art. 45 case.",
              "Separate offshore account opening and KYC."],
    ),
    dict(
        id="R15", name="Sell RMB privately to someone who wants USD (private FX swap)",
        short="Private FX swap",
        group="Unlawful · rejected",
        status="unlawful",
        who="Not lawful for anyone.",
        basis=["S04"], fee="rejected", cap=None, spread=None, tax=(0.0, 0.0),
        tax_note="Not a tax question.",
        time="n/a", time_days=None, docs=[],
        steps=["Do not do this. S04 Art. 45 covers private, disguised and brokered FX trading: "
               "confiscation of the proceeds plus a fine of up to 30% of the amount, or 30%-100% if "
               "serious, with criminal liability for larger cases."],
        pros=["None that survives contact with Art. 45."],
        cons=["Confiscation plus a fine up to the value of the amount.", "Criminal exposure.",
              "Counterparty risk with no recourse."],
    ),
    dict(
        id="R16", name="Underground bank / 'huipiao' (offshore RMB, onshore settlement)",
        short="Underground bank",
        group="Unlawful · rejected",
        status="unlawful",
        who="Not lawful for anyone.",
        basis=["S04"], fee="rejected", cap=None, spread=None, tax=(0.0, 0.0),
        tax_note="Not a tax question.",
        time="n/a", time_days=None, docs=[],
        steps=["Do not do this. It is the paradigm case of Art. 39 evasion and Art. 45 illegal FX "
               "trading, and is prosecuted as illegal business operation at scale."],
        pros=["None."],
        cons=["Funds are typically seized.", "Fines of 30%-100% and criminal liability.",
              "No legal recourse if the operator disappears."],
    ),
    dict(
        id="R17", name="Buy crypto or USDT in China and sell abroad",
        short="Crypto / USDT off-ramp",
        group="Unlawful · rejected",
        status="unlawful",
        who="Not lawful for anyone in China.",
        basis=["S16"], fee="rejected", cap=None, spread=None, tax=(0.0, 0.0),
        tax_note="Not a tax question.",
        time="n/a", time_days=None, docs=[],
        steps=["Do not do this. Yin Fa [2026] No. 42 (which replaced Yin Fa [2021] No. 237) states that "
               "exchanging legal tender for virtual currency is an illegal financial activity, that "
               "institutions may not provide settlement services for it, and that losses are borne by "
               "the participant."],
        pros=["None that is lawful."],
        cons=["Illegal financial activity", "No recourse, and exchanges are blocked from RMB rails.",
              "Creates a US tax and reporting mess on top."],
    ),
    dict(
        id="R18", name="Borrow a relative's or friend's USD 50,000 quota",
        short="Borrow someone's quota",
        group="Unlawful · rejected",
        status="unlawful",
        who="Not lawful for anyone.",
        basis=["S01", "S18", "S04"], fee="rejected", cap=None, spread=None, tax=(0.0, 0.0),
        tax_note="Not a tax question.",
        time="n/a", time_days=None, docs=[],
        steps=["Do not do this. S01 Art. 7 prohibits splitting to evade limits and S04 Arts. 39–40 "
               "supply statutory fines up to 30% (30%–100% if serious) plus criminal liability. Note: "
               "the older 'watch list' notice S18 has conflicting active/repealed mirror labels (F03), "
               "so S01 Art. 7 and S04 are the operative authorities."],
        pros=["None."],
        cons=["Statutory fines up to the amount involved and refusal of bank counter service.",
              "Both sides exposed, including your relative.",
              "The annual purchase quota may not even apply to you (see F02)."],
    ),
    dict(
        id="R19", name="Present fabricated contracts or invoices to the bank",
        short="Fabricated documents",
        group="Unlawful · rejected",
        status="unlawful",
        who="Not lawful for anyone.",
        basis=["S01", "S04"], fee="rejected", cap=None, spread=None, tax=(0.0, 0.0),
        tax_note="Not a tax question.",
        time="n/a", time_days=None, docs=[],
        steps=["Do not do this. S01 Art. 7 prohibits tampering with authenticity administration using "
               "fabricated vouchers; S04 Arts. 39-40 provide fines of up to 30% (or 30%-100% if "
               "serious) plus criminal liability."],
        pros=["None."],
        cons=["Fines up to the value of the amount moved.", "Criminal record.",
              "The bank keeps the documents for at least five years."],
    ),
    dict(
        id="R20", name="Keep the money in China and use it as a spending account",
        short="Keep it in China (do nothing)",
        group="Lawful · do nothing",
        status="lawful",
        who="Anyone — this is the baseline every other route must beat.",
        basis=["S02", "S03"], fee="none", cap=None, spread=None, tax=(0.0, 0.0),
        tax_note="No conversion, no PRC conversion cost. US reporting duties (FBAR/8938) still apply.",
        time="immediate", time_days=(0, 0),
        docs=["Passport for account maintenance", "FBAR / Form 8938 filings"],
        steps=[
            "Keep the balance and spend it on trips, cards and obligations paid from China.",
            "File FBAR and Form 8938 every year the thresholds are met.",
            "Revisit only if you need the capital in USD.",
        ],
        pros=["Zero conversion cost and zero spread.", "Reversible at any time."],
        cons=["Currency and country risk stay with you.", "US reporting continues regardless.",
              "The problem is deferred, not solved."],
    ),
]

# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------
SPREADS = {
    "wire": (0.0030, 0.0150),
    "cash": (0.0080, 0.0300),
    "card": (0.0000, 0.0300),
    "cnh": (0.0020, 0.0100),
    "none": (0.0, 0.0),
    "rejected": (0.0, 0.0),
}


def fixed_and_cap(route: dict, tier: float):
    """Return (transactions, fixed_cost, fixed_status, per_txn_cap)."""
    kind, cap = route["fee"], route["cap"]
    n = math.ceil(tier / cap) if cap else 1
    per = tier / n
    if kind == "wire":
        return n, n * wire_fee(per), "published", cap
    if kind == "global":
        return n, n * GLOBAL_XFER, "published", cap
    if kind == "cashcarry":
        # S21 item 2.2.2.1: foreign-currency notes withdrawal over the counter is Free.
        return n, n * NOTES_WITHDRAWAL_FEE, "published", cap
    if kind in ("cash", "atm", "card"):
        return n, None, "unpublished", cap
    return 1, 0.0, "none", cap


def time_label(route: dict, tier: float) -> str:
    cap = route["cap"]
    if route["id"] in ("R04", "R05", "R06") and cap:
        n = math.ceil(tier / cap)
        if route["id"] == "R06":
            return f"{n} trips"
        return f"{n} banking days"
    if route["id"] == "R11":
        years = math.ceil(tier / ATM_YEAR_CAP)
        return f"{years} calendar years" if years > 1 else "within 1 calendar year"
    return route["time"]


def build_rows():
    rows = []
    for r in ROUTES:
        if r["status"] == "unlawful":
            continue
        for t in TIERS:
            n, fixed, fstatus, cap = fixed_and_cap(r, t)
            lo_s, hi_s = SPREADS.get(r["spread"] or "none", (0.0, 0.0))
            spread_lo, spread_hi = t * lo_s, t * hi_s
            partial = fixed is None
            if isinstance(fixed, tuple):
                tot_lo, tot_hi = fixed[0] + spread_lo, fixed[1] + spread_hi
            elif fixed is None:
                # No published fixed fee was obtained for this channel. The estimate is the
                # spread alone and is labelled PARTIAL rather than silently completed.
                tot_lo, tot_hi = spread_lo, spread_hi
            else:
                tot_lo, tot_hi = fixed + spread_lo, fixed + spread_hi
            tax_lo, tax_hi = (r["tax"] if r["tax"] else (None, None))
            rows.append(dict(
                route=r["id"], name=r["short"], group=r["group"], status=r["status"],
                tier=t, transactions=n, fixed_fee=fixed, fixed_status=fstatus,
                partial=partial,
                spread_lo=round(spread_lo, 2), spread_hi=round(spread_hi, 2),
                total_lo=None if tot_lo is None else round(tot_lo, 2),
                total_hi=None if tot_hi is None else round(tot_hi, 2),
                pct_lo=None if tot_lo is None else round(100 * tot_lo / t, 3),
                pct_hi=None if tot_hi is None else round(100 * tot_hi / t, 3),
                prc_tax_pct_lo=tax_lo, prc_tax_pct_hi=tax_hi,
                time=time_label(r, t),
            ))
    return rows


def main():
    DATA.mkdir(exist_ok=True)
    rows = build_rows()
    meta = dict(
        generated=date.today().isoformat(), retrieved=RETRIEVED,
        tiers=TIERS, rate=FX, source_count=len(SOURCES),
        route_count=len([r for r in ROUTES]),
        costed_route_count=len([r for r in ROUTES if r["status"] != "unlawful"]),
        assumption_count=len(ASSUMPTIONS), row_count=len(rows),
    )
    (DATA / "sources.json").write_text(json.dumps(SOURCES, indent=2, ensure_ascii=False))
    (DATA / "routes.json").write_text(json.dumps(ROUTES, indent=2, ensure_ascii=False))
    (DATA / "assumptions.json").write_text(json.dumps(ASSUMPTIONS, indent=2, ensure_ascii=False))
    (DATA / "costs.json").write_text(json.dumps(dict(meta=meta, rows=rows), indent=2))
    (DATA / "meta.json").write_text(json.dumps(meta, indent=2))
    with (DATA / "costs.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for row in rows:
            w.writerow({k: ("" if v is None else v) for k, v in row.items()})
    print(f"{len(rows)} rows · {len(ROUTES)} routes · {len(SOURCES)} sources · {len(ASSUMPTIONS)} assumptions")


if __name__ == "__main__":
    main()
