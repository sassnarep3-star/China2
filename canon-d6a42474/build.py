#!/usr/bin/env python3
"""Canonical CNY->USD dashboard, built only from sources read on 2026-11-11.

Every number below is either (a) copied from canon-d6a42474/data/sources.json,
(b) arithmetic on those numbers, or (c) blank with a flag id. Nothing is inferred.

Run:  python3 canon-d6a42474/build.py
Out:  canon-d6a42474/*.html, data/costs.csv, data/repo-scan.json
"""
from __future__ import annotations

import csv
import json
import math
import os
import re
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
DATA = ROOT / "data"
BUILD_DATE = "2026-11-11"

# --------------------------------------------------------------------------
# Published inputs. Each is copied from a source in sources.json.
# --------------------------------------------------------------------------
BOARD = {
    "buy": F("666.06"),      # S07 美元 现汇买入价
    "sell": F("668.86"),     # S07 美元 现汇卖出价
    "conversion": F("671.91"),  # S07 中行折算价 (NOT a midpoint; not used)
    "stamp": "2026-11-11 15:30:04",
    "source": "S07",
}
MID = (BOARD["buy"] + BOARD["sell"]) / 2
CNY_PER_USD = BOARD["sell"] / 100
ONEWAY_MARGIN = (BOARD["sell"] - MID) / MID          # cost of buying USD vs mid
ROUNDTRIP_SPREAD = (BOARD["sell"] - BOARD["buy"]) / MID

HSBC_TT_MIN, HSBC_TT_MAX, HSBC_CABLE = F(100), F(500), F(120)
HSBC_PAY_EXACT = F(200)
BOC_TT_MIN, BOC_TT_MAX, BOC_CABLE = F(50), F(260), F(150)
HSBC_GT_ADVANCE_USD = F(20)
QUOTA_USD = F(50_000)

TIERS = [F(t * 10_000) for t in range(1, 41)]


def q(x: F, places: str = "0.01") -> Decimal:
    d = Decimal(x.numerator) / Decimal(x.denominator)
    return d.quantize(Decimal(places), rounding=ROUND_HALF_UP)


def usd(x: F) -> str:
    return "${:,.2f}".format(q(x))


def pct(x: F) -> str:
    return "{:.3f}%".format(float(x * 100))


def cny(x: F) -> str:
    return "CNY {:,.2f}".format(q(x))


def cny_int(x: F) -> str:
    return "{:,}".format(int(q(x, "1")))


def cny_for(amount: F) -> F:
    return amount * BOARD["sell"] / 100


def margin_usd(amount: F) -> F:
    return amount * ONEWAY_MARGIN


def hsbc_fee_cny(amount: F) -> F:
    raw = cny_for(amount) / 1000
    return min(max(raw, HSBC_TT_MIN), HSBC_TT_MAX) + HSBC_CABLE


def boc_fee_cny(amount: F) -> F:
    raw = cny_for(amount) / 1000
    return min(max(raw, BOC_TT_MIN), BOC_TT_MAX) + BOC_CABLE


def fee_in_usd(fee_cny: F) -> F:
    return fee_cny / CNY_PER_USD


# --------------------------------------------------------------------------
# Routes. status: lawful | conditional | unlawful
# price: key into PRICERS, or None when no published fee exists.
# --------------------------------------------------------------------------
ROUTES = [
    dict(
        id="M01", name="Documented current-account income: HSBC Premier/Advance, one telegraphic transfer",
        group="Bank wire", status="lawful", price="hsbc_tt",
        who="An overseas individual (境外个人) converting legitimate current-account RMB income in mainland China, or a domestic individual with the documented-income file.",
        cap="No annual cap published for this document-based conversion. The USD 50,000 annual total in S02 Art. 2 applies to settlement and to a domestic individual's purchase, not to an overseas individual's documented current-account income (S06).",
        papers="Valid ID + source-of-funds documents including the tax voucher (S02 Art. 13(1); S06). Contract or payslips matching the credits.",
        prc_tax="No tax on the exchange itself. Tax was due when the income arose: 3%–45% comprehensive, 5%–35% business, 20% flat on property transfer, interest, dividends and royalties (S17 Art. 3).",
        us_side="Principal is not income. Exchange gain on a personal transaction is ignored only up to $200 (S12). FBAR if the account exceeded $10,000 at any time (S10).",
        steps=[
            "Obtain the tax record for every year the balance represents (个人所得税 App / 完税证明) and the contracts or payslips that match each large credit.",
            "Ask the bank, in writing, for the conversion rate it will apply, the fee in CNY, the cable fee, the correspondent charge and the receiving-bank charge. The tariff publishes only the first three (S09).",
            "Convert CNY to USD at the bank's selling rate (board: 668.86 per 100 USD on 2026-11-11 15:30:04, S07) and keep the exchange memo (兑换水单) — it is the only way to reverse an unspent remainder, within 24 months (S02 Art. 13(2)).",
            "Send one telegraphic transfer to your own U.S. account. Premier/Advance: 0.1% min CNY 100 max CNY 500 + CNY 120 cable (S09 2.2.4.1–2.2.4.2).",
            "File Form 114 (FBAR) by 15 April with automatic extension to 15 October if the aggregate balance crossed $10,000 (S10).",
        ],
        pros=["Published fee schedule; no quota; one wire for the whole amount.", "Current-account payments are not restricted by statute (S01 Art. 5)."],
        cons=["The bank decides whether the documents are sufficient; no published checklist binds it.", "Correspondent and receiving-bank charges are not published (F13)."],
        sources=["S01", "S02", "S06", "S07", "S09"],
    ),
    dict(
        id="M02", name="Same route at HSBC Private Banking (individual)",
        group="Bank wire", status="conditional", price="hsbc_pb",
        who="An individual HSBC China Private Banking customer.",
        cap="No annual cap published for the document-based conversion; the banking relationship itself is the gate.",
        papers="As M01.",
        prc_tax="As M01.",
        us_side="As M01.",
        steps=[
            "Confirm in writing that the account is an individual Private Banking account (the tariff's individual columns are what make the fee zero).",
            "Obtain the tax records and source documents (S02 Art. 13(1)).",
            "Convert at the bank's selling rate and keep the exchange memo.",
            "Remit: telegraphic transfer issuance and cable are listed as Free for an individual Private Banking customer (S09 2.2.4.1, 2.2.4.2).",
            "File the U.S. reports the balance triggers (S10).",
        ],
        pros=["The only published fee of zero for a wire in the two tariffs read here.", "Same documentation route as M01."],
        cons=["Private Banking eligibility and minimum balance are not published in the tariff read here (F18).", "Zero fee still leaves the exchange margin, which is the larger number."],
        sources=["S07", "S09", "S02"],
    ),
    dict(
        id="M03", name="Documented income: Bank of China, one cross-border wire",
        group="Bank wire", status="lawful", price="boc_tt",
        who="Any individual with a Bank of China account and the documented-income file.",
        cap="No annual cap published for the document-based conversion; the same documentary gate as M01.",
        papers="As M01, plus the bank's own cross-border remittance form.",
        prc_tax="As M01.",
        us_side="As M01.",
        steps=[
            "Assemble the tax records and source documents (S02 Art. 13(1); S06).",
            "Ask for the executed rate in writing: the board is indicative and the bank's own note says the executed rate governs (S07).",
            "Convert and remit in one instruction; the published fee is 0.1% min CNY 50 max CNY 260 plus CNY 150 cable outside Hong Kong/Macau/Taiwan (S08).",
            "Keep the exchange memo and the remittance advice.",
            "File the U.S. reports the balance triggers (S10).",
        ],
        pros=["Lower published fee ceiling than HSBC (CNY 410 all-in vs CNY 620).", "Same board, same statutory basis."],
        cons=["Fee schedule is headed 1 November 2014; no newer published version was located in this pass (F06).", "Branch-level practice and documentation demands are not published."],
        sources=["S02", "S06", "S07", "S08"],
    ),
    dict(
        id="M04", name="HSBC Global Transfer to your own overseas HSBC account (Premier / Private Banking)",
        group="Bank transfer", status="conditional", price=None,
        who="HSBC China Premier or Private Banking customer with a self-named HSBC account in a country where Global Transfer to Self is offered.",
        cap="Not published. Currency and destination limits are set by the receiving country's HSBC entity.",
        papers="Same documentary gate as M01; the receiving account must be in your name.",
        prc_tax="As M01.",
        us_side="As M01; the receiving HSBC entity may also report locally.",
        steps=[
            "Confirm both accounts are eligible for Global Transfer to Self (S09 remark).",
            "Complete the same source-of-funds file as M01.",
            "Convert and transfer; the tariff lists the fee as Free for Private Banking and Premier (S09 2.2.6.1).",
            "Obtain the exchange rate applied, in writing — the tariff does not publish it (F14).",
        ],
        pros=["Published fee of zero for Premier and Private Banking.", "Avoids a correspondent chain."],
        cons=["Exchange rate applied is not published, so the all-in cost cannot be computed from official sources (F14).", "Requires an HSBC account on both ends."],
        sources=["S09"],
    ),
    dict(
        id="M05", name="HSBC Global Transfer to your own overseas HSBC account (Advance)",
        group="Bank transfer", status="conditional", price=None,
        who="HSBC China Advance customer moving to a self-named HSBC account abroad.",
        cap="Not published.",
        papers="As M04.",
        prc_tax="As M01.",
        us_side="As M01.",
        steps=[
            "Confirm Advance eligibility for the destination (S09 2.2.6.1 remark).",
            "Complete the source-of-funds file.",
            "Transfer; the tariff's indication charge is USD 20 per transaction (S09 2.2.6.1).",
            "Ask for the rate applied in writing (F14).",
        ],
        pros=["A published, flat USD 20 fee.", "No correspondent chain."],
        cons=["Flat fee only; the exchange rate is not published.", "Advance account opening is restricted from 18 March 2026 (S09 note 4)."],
        sources=["S09"],
    ),
    dict(
        id="M06", name="USD 50,000 annual purchase total, one wire per year (domestic individual)",
        group="Quota", status="conditional", price="quota",
        who="A domestic individual (境内个人): a PRC citizen, or a foreign national continuously resident in China for one year or more (S01 Art. 52(2)). A U.S. citizen living abroad is normally an overseas individual, not this category.",
        cap="USD 50,000 per person per calendar year (S02 Art. 2).",
        papers="Valid ID within the annual total (S02 Art. 2).",
        prc_tax="As M01; the tax on the income that created the balance is unchanged.",
        us_side="As M01.",
        steps=[
            "Establish whether the bank classifies you as a domestic individual; get the answer in writing (see F12 for the two official definitions).",
            "Use at most USD 50,000 of your own annual purchase total per calendar year.",
            "Convert and remit in that year; do not use another person's total to accelerate this (see U01).",
            "Repeat in later years only within your own total.",
            "File the U.S. reports the balance triggers (S10).",
        ],
        pros=["Simple documentary test within the annual total.", "Predictable."],
        cons=["Eight calendar years for USD 400,000 at USD 50,000 a year.", "Currency exposure and bank-policy change over that period are unpriced."],
        sources=["S01", "S02", "S07", "S09"],
    ),
    dict(
        id="M07", name="Emigrant property transfer (移民财产转移) after cancelling PRC household registration",
        group="Capital account", status="conditional", price="boc_tt",
        who="A natural person who emigrated from mainland China (or settled in Hong Kong/Macau) and is converting lawful pre-emigration property.",
        cap="No USD cap published. One application for the whole amount; SAFE approval at the original household-registration location (S03 Art. 6; S04 VI).",
        papers="Written application, status form, ID, cancelled household-registration certificate, proof of settlement abroad, property-rights documents, and a PRC tax certificate or payment voucher (S03 Art. 8). Notarisation of the property documents and the agency agreement is no longer required (S04 VI(4)).",
        prc_tax="Pre-departure tax settlement before cancelling household registration (S17 Art. 10(5)); property-transfer IIT at 20% of the gain (S17 Art. 3).",
        us_side="Principal is not income; the property gain is a PRC-taxed event and may need U.S. reporting and a foreign tax credit — not quantified here.",
        steps=[
            "Complete the pre-departure tax settlement before the household registration is cancelled (S17 Art. 10(5)).",
            "File one application with the SAFE branch where the household was registered, with the S03 Art. 8 documents.",
            "Obtain the approval letter and the capital-account approval document (核准件).",
            "Take the approval to the bank, convert and remit; the bank fee is the ordinary wire fee (S08 or S09).",
            "Keep the approval, the tax certificate and the exchange memo.",
        ],
        pros=["Designed for exactly this fact pattern: lawful pre-emigration property.", "No USD cap; staged remittance no longer required (S04)."],
        cons=["Requires cancellation of PRC household registration — a status change, not a paperwork step.", "SAFE approval is discretionary on the documents; no published processing time or SAFE fee."],
        sources=["S01", "S03", "S04", "S08", "S17"],
    ),
    dict(
        id="M08", name="Inheritance property transfer (继承财产转移)",
        group="Capital account", status="conditional", price="boc_tt",
        who="A foreign citizen (or Hong Kong/Macau resident) who has lawfully inherited mainland property.",
        cap="No USD cap published; SAFE approval at the deceased's former household-registration location (S03 Art. 5; S04 VI).",
        papers="Application, status form, ID, proof of settlement abroad, inheritance documents, the deceased's property documents and a tax certificate or payment voucher (S03 Art. 9).",
        prc_tax="PRC tax on the inheritance and on the sale of the inherited property must be evidenced by a tax certificate (S03 Art. 8(6), 9(5)). The rate is not computed here.",
        us_side="A bequest from a foreign person above $100,000 is reportable on Form 3520 (S15).",
        steps=[
            "Obtain the inheritance documents and the PRC tax certificate for the estate and the property.",
            "File one application with SAFE where the deceased was registered (S03 Art. 5).",
            "Obtain the approval and the 核准件.",
            "Convert and remit at the bank; ordinary wire fee (S08).",
            "File Form 3520 if the bequest exceeds $100,000 (S15).",
        ],
        pros=["Lawful route for inherited property.", "One application; no staging (S04)."],
        cons=["Probate and tax documentation can take longer than the transfer itself.", "SAFE approval is not published as automatic."],
        sources=["S03", "S04", "S08", "S15"],
    ),
    dict(
        id="M09", name="Carry foreign-currency cash (with the CBP declaration)",
        group="Cash", status="conditional", price="cash",
        who="Anyone able to withdraw foreign-currency notes in China and carry them.",
        cap="Withdrawal above USD 10,000 equivalent in one day needs prior SAFE filing (S02 Art. 30). Entry to or exit from the U.S. above USD 10,000 must be reported to CBP (S16).",
        papers="ID for the withdrawal; FinCEN Form 105 for the U.S. leg (S16).",
        prc_tax="As M01; carrying cash does not change the tax on the income.",
        us_side="Report above USD 10,000 at one time; failure risks forfeiture and seizure (S16).",
        steps=[
            "If withdrawing more than USD 10,000 equivalent in a day, file with SAFE in advance (S02 Art. 30).",
            "Convert to notes at the bank; the notes rate on the board equals the exchange rate (S07).",
            "Declare at the U.S. border above USD 10,000 using FinCEN Form 105 (S16).",
            "Do not split the amount among travellers to stay under the line (see U05).",
        ],
        pros=["No wire fee; only the exchange margin.", "Settles instantly."],
        cons=["40 trips for USD 400,000 at USD 10,000 a trip, with the associated risk and cost unpriced.", "Physical loss and seizure risk."],
        sources=["S02", "S07", "S16"],
    ),
    dict(
        id="M10", name="Remit from an existing foreign-currency savings account (no new conversion)",
        group="Bank wire", status="conditional", price="fxacct",
        who="Someone whose money is already USD (or another foreign currency) inside a Chinese bank.",
        cap="Overseas individual: remit from the FX savings account on ID (S02 Art. 15(1)). Domestic individual: up to USD 50,000 a day on ID, above that with authenticity documents (S02 Art. 14).",
        papers="Valid ID; authenticity documents above the daily line for a domestic individual.",
        prc_tax="None on the remittance itself; the tax on the income is unchanged.",
        us_side="As M01.",
        steps=[
            "Confirm the balance is already foreign currency, not RMB.",
            "Remit from the FX savings account with ID (S02 Art. 15(1)).",
            "Pay the wire fee; there is no new exchange margin because no new conversion happens.",
        ],
        pros=["Cheapest published arithmetic: the wire fee only, no exchange margin.", "No conversion decision."],
        cons=["Only works if the money is already in foreign currency — the conversion already happened at some earlier rate.", "Bank may still ask for source documents."],
        sources=["S02", "S09"],
    ),
    dict(
        id="M11", name="Card or ATM cash withdrawal abroad",
        group="Cash", status="conditional", price=None,
        who="Holder of a PRC-issued bank card with an overseas cash facility.",
        cap="Not verified in this pass (F15).",
        papers="Card and ID.",
        prc_tax="Not applicable to the withdrawal itself.",
        us_side="Cash arriving in the U.S. is still subject to the CBP line (S16).",
        steps=["Not priced here: the issuer's overseas cash limit and fee were not read from an official page in this pass (F15)."],
        pros=[], cons=["Limit and fee unverified; cannot be costed from official sources here."],
        sources=[],
    ),
    dict(
        id="M12", name="Keep the RMB in China and convert later",
        group="Timing", status="lawful", price=None,
        who="Anyone not forced to move the money now.",
        cap="Not applicable.",
        papers="None.",
        prc_tax="The tax on the income is unchanged by waiting.",
        us_side="U.S. reporting follows the balance, not the transfer (S10).",
        steps=[
            "Keep the balance where it is.",
            "Continue to file FBAR and any other U.S. reports the balance triggers (S10).",
            "Re-read the PRC rules before acting; they change (S04 and S02 both carry amendment notes).",
        ],
        pros=["Costs nothing today.", "Keeps every route open."],
        cons=["Currency exposure is unpriced and can exceed every fee discussed here.", "Rules can tighten; the balance stays exposed to PRC enforcement."],
        sources=["S10"],
    ),
    dict(
        id="M13", name="Third-party remittance platform (e.g. Wise) from a CNY balance",
        group="Platform", status="conditional", price=None,
        who="Depends on the platform's own eligibility and on the Chinese bank's willingness to debit a CNY balance for this purpose.",
        cap="Not verified in this pass (F16).",
        papers="Platform KYC plus the Chinese bank's source-of-funds file.",
        prc_tax="As M01.",
        us_side="The platform reports according to its own licences; U.S. reporting is still yours (S10).",
        steps=["Not priced here: the platform's CNY limits and fees were not read from an official page in this pass (F16)."],
        pros=[], cons=["No official confirmation read in this pass that a mainland CNY balance can be used this way."],
        sources=[],
    ),
    dict(
        id="M14", name="Qualified institutional investment channel (QDII and similar)",
        group="Investment", status="conditional", price=None,
        who="A domestic investor eligible for the scheme.",
        cap="Not verified in this pass (F17).",
        papers="Scheme documentation; not a remittance of your existing balance.",
        prc_tax="Depends on the product.",
        us_side="U.S. reporting on the foreign fund/account still applies.",
        steps=["Not priced here: scheme caps and eligibility were not read from an official page in this pass (F17)."],
        pros=[], cons=["This is an investment, not a way to move an existing balance out."],
        sources=[],
    ),
    dict(
        id="U01", name="Split the amount across relatives' annual totals",
        group="Unlawful", status="unlawful", price=None,
        who="—",
        cap="—",
        papers="—",
        prc_tax="—",
        us_side="—",
        steps=["No steps are given. This is listed so it is not re-discovered as an idea."],
        pros=[], cons=["Evasion-type conduct attracts a fine of up to 30% of the amount, or 30% up to the equivalent amount in serious cases (S01 Arts. 39–40). Using another person's annual total is also a false declaration to the bank."],
        sources=["S01", "S02"],
    ),
    dict(
        id="U02", name="Underground bank / 变相买卖外汇 (offshore swap with an onshore counterparty)",
        group="Unlawful", status="unlawful", price=None,
        who="—", cap="—", papers="—", prc_tax="—", us_side="—",
        steps=["No steps are given."],
        pros=[], cons=["Private or disguised trading in foreign exchange is sanctioned under S01 Art. 45: warning, confiscation of the proceeds, a fine of up to 30% of the amount, or 30% up to the equivalent amount in serious cases, plus criminal liability."],
        sources=["S01"],
    ),
    dict(
        id="U03", name="Crypto bridge (buy a stablecoin in CNY, sell it abroad)",
        group="Unlawful", status="unlawful", price=None,
        who="—", cap="—", papers="—", prc_tax="—", us_side="—",
        steps=["No steps are given."],
        pros=[], cons=["Virtual-currency business activity is an illegal financial activity in mainland China, and a mainland CNY-to-virtual-currency exchange is expressly prohibited (S05 I(1)). The civil act is void and the loss falls on the investor (S05 VI(19))."],
        sources=["S05"],
    ),
    dict(
        id="U04", name="False invoices, contracts or vouchers to pass the bank's authenticity check",
        group="Unlawful", status="unlawful", price=None,
        who="—", cap="—", papers="—", prc_tax="—", us_side="—",
        steps=["No steps are given."],
        pros=[], cons=["Purchasing foreign exchange with false or invalid transaction documents is sanctioned under S01 Art. 40: forced reconversion, a fine of up to 30% of the amount, or 30% up to the equivalent amount in serious cases."],
        sources=["S01"],
    ),
    dict(
        id="U05", name="Structure cash across travellers or trips to stay under the USD 10,000 line",
        group="Unlawful", status="unlawful", price=None,
        who="—", cap="—", papers="—", prc_tax="—", us_side="—",
        steps=["No steps are given."],
        pros=[], cons=["CBP's published consequence for a false or missing report is forfeiture and seizure, with civil or criminal penalties (S16). The specific anti-structuring provision was not re-read in this pass and is flagged (F20)."],
        sources=["S16"],
    ),
]

PRICED = {"hsbc_tt", "hsbc_pb", "boc_tt", "quota", "cash", "fxacct"}


def price_route(route: dict, amount: F) -> dict | None:
    """Return the published-input cost for one route at one amount, or None."""
    key = route.get("price")
    if key is None:
        return None
    base = dict(fee_cny=None, fee_usd=F(0), margin=F(0), total=F(0), years=1,
                note="", partial=False)
    if key == "hsbc_tt":
        fee_c = hsbc_fee_cny(amount)
        base.update(fee_cny=fee_c, fee_usd=fee_in_usd(fee_c), margin=margin_usd(amount))
        base["total"] = base["fee_usd"] + base["margin"]
    elif key == "hsbc_pb":
        base.update(fee_cny=F(0), fee_usd=F(0), margin=margin_usd(amount))
        base["total"] = base["margin"]
    elif key == "boc_tt":
        fee_c = boc_fee_cny(amount)
        base.update(fee_cny=fee_c, fee_usd=fee_in_usd(fee_c), margin=margin_usd(amount))
        base["total"] = base["fee_usd"] + base["margin"]
    elif key == "quota":
        years = math.ceil(float(amount / QUOTA_USD))
        per = min(amount, QUOTA_USD)
        fee_c = hsbc_fee_cny(per)
        fee_all = fee_c * years
        base.update(fee_cny=fee_c, fee_usd=fee_in_usd(fee_all), margin=margin_usd(amount),
                    years=years, note="%d annual tranche%s" % (years, "" if years == 1 else "s"))
        base["total"] = base["fee_usd"] + base["margin"]
    elif key == "cash":
        base.update(fee_cny=F(0), fee_usd=F(0), margin=margin_usd(amount),
                    note="%d trips at USD 10,000" % math.ceil(float(amount / F(10_000))))
        base["total"] = base["margin"]
    elif key == "fxacct":
        fee_c = hsbc_fee_cny(amount)
        base.update(fee_cny=fee_c, fee_usd=fee_in_usd(fee_c), margin=F(0),
                    note="No new conversion")
        base["total"] = base["fee_usd"]
    # Publish cents that add up: round each component, then sum (see flag F22).
    base["fee_usd"] = F(q(base["fee_usd"]))
    base["margin"] = F(q(base["margin"]))
    base["total"] = base["fee_usd"] + base["margin"]
    return base


# --------------------------------------------------------------------------
# Questions, flags, layers
# --------------------------------------------------------------------------
QUESTIONS = [
    ("Q01", "Where did the RMB come from, tranche by tranche?",
     "Nothing in this repo establishes it. The brief says only that the money is 'stuck'.",
     "Classify every large credit as salary, business profit, property sale, inheritance, pre-emigration property, dividend/interest, gift or something else. Pull five years of statements.",
     "The origin decides the route (M01 vs M07 vs M08) and the PRC tax rate (S17 Art. 3). Nothing can be computed without it.", ["S17"]),
    ("Q02", "Has PRC tax already been paid on the income, and do you hold the tax record?",
     "Not known. The bank's gate under S02 Art. 13(1) and S06 is a source-of-funds file that includes tax vouchers.",
     "Download the 个人所得税 App payment records for each earning year; request 完税证明 at the tax hall.",
     "This is the actual gate on the cheap route. Without it no bank will run M01.", ["S02", "S06"]),
    ("Q03", "Are you a 境内个人 or a 境外个人 for FX purposes?",
     "Unknown. Two official texts define 'domestic individual' differently (F12).",
     "Ask the bank in writing which category it uses for your account, and whether a Foreign Permanent Resident ID changes the answer.",
     "It decides whether the USD 50,000 annual total (M06) applies to your purchase at all.", ["S01", "S02"]),
    ("Q04", "When was each tranche acquired, and at what USD basis?",
     "Unknown. IRS reference averages are published: 7.129 (2025), 7.189 (2024), 7.075 (2023), 6.730 (2022), 6.452 (2021) (S13).",
     "Export bank credits by date and convert each with a consistently applied posted rate.",
     "It decides whether there is an exchange gain above the $200 personal-transaction line (S12).", ["S12", "S13"]),
    ("Q05", "What is your U.S. offshore reporting history?",
     "Unknown. FBAR is required above $10,000 aggregate at any time (S10); maximum civil penalties are $16,536 non-willful and $165,353 willful (S11).",
     "Pull the peak balance for each calendar year and compare with the FBAR/8938/3520 filings actually made.",
     "Unfiled reports are the largest quantified risk in the whole file — larger than any bank fee.", ["S10", "S11"]),
    ("Q06", "What will the bank actually charge and at what rate?",
     "Only published tariffs are known: HSBC 0.1% min CNY 100 max CNY 500 + CNY 120 cable (S09); BOC 0.1% min CNY 50 max CNY 260 + CNY 150 cable (S08); board 668.86 per 100 USD at 15:30:04 on 2026-11-11 (S07).",
     "Request a written quote showing the applied rate, commission, cable, correspondent and receiving-bank charges.",
     "The published spread and fees are a floor; the executed quote is the number that binds.", ["S07", "S08", "S09"]),
    ("Q07", "What do the correspondent and receiving banks charge?",
     "Not published by either Chinese bank (F13).",
     "Ask both banks for the intermediary and beneficiary-bank charge, or use an OUR/'Pay Exact' instruction (CNY 200 at HSBC, S09) and check the credit.",
     "It is the only part of the wire cost that no official page in this repo quantifies.", ["S09"]),
    ("Q08", "Can someone in China run the formalities if you are abroad?",
     "The rules allow an agent for the annual-total operations and for the property-transfer application (S02 Art. 4; S03 Art. 7), with ID, authorisation and, for relatives, proof of relationship.",
     "Ask the bank and the SAFE branch what authorisation they will accept; the notarisation requirement for property documents was removed (S04 VI(4)).",
     "It determines whether you must travel or can execute remotely.", ["S02", "S03", "S04"]),
    ("Q09", "Is your PRC household registration still active?",
     "Unknown.",
     "Check the hukou status. The emigrant property route (M07) requires cancellation and a pre-departure tax settlement (S03 Art. 8; S17 Art. 10(5)).",
     "It rules the emigrant route in or out.", ["S03", "S17"]),
    ("Q10", "Is any part of the balance an inheritance?",
     "Unknown.",
     "Identify the deceased, the will/probate documents and the PRC tax certificate for the estate.",
     "Inheritance has its own route and its own documents (M08) and triggers Form 3520 above $100,000 (S15).", ["S03", "S15"]),
    ("Q11", "What exactly is the 'considerable tax' you were quoted?",
     "Not identified anywhere in this repo. No reviewed text taxes the act of converting CNY to USD (F01).",
     "Ask for the assessment or quote in writing and identify whether it is IIT on the income, a penalty, a withholding, or a bank charge.",
     "If it is IIT on the origin, no conversion route avoids it; if it is a penalty, the facts and dates decide the exposure.", ["S01", "S17"]),
    ("Q12", "Which U.S. account will receive the USD, and in whose name?",
     "Unknown.",
     "Confirm the receiving bank's incoming-wire details, the name match, and whether it charges.",
     "A third-party name on the receiving end breaks the 'own account' logic of every lawful route here.", ["S02"]),
    ("Q13", "Why is the money 'stuck' today?",
     "Unknown: bank refusal, missing documents, quota, a freeze, or a compliance review are different problems.",
     "Ask the bank for the refusal in writing, with the rule it relies on.",
     "It decides whether this is a documentation problem or a legal one.", ["S02"]),
    ("Q14", "How much is in the account, and in what currency?",
     "Unknown. Only the brief's range of USD 10,000 to USD 400,000 is used for the cost tables.",
     "State the balance and currency composition.",
     "The fixed fee stops mattering above roughly USD 74,754, while the margin grows linearly — the mix changes with size.", ["S07", "S09"]),
    ("Q15", "How urgent is the transfer?",
     "Unknown.",
     "Set a deadline and a rate tolerance.",
     "Waiting is free of fees but keeps full currency exposure (M12).", ["S07"]),
    ("Q16", "Who is authorised to advise you in each country?",
     "Unknown. This repo is research, not advice.",
     "Engage a PRC tax adviser and a U.S. cross-border CPA; give each the facts from Q01–Q05.",
     "The two tax systems interact; the answer needs both.", ["S17", "S12"]),
]

FLAGS = [
    ("F01", "blocking", "No conversion tax was found — the 'considerable tax' is unidentified",
     "None of the 18 documents read in this pass imposes a tax on converting CNY into USD. Decree 532 Art. 5 says current international payments and transfers are not restricted, and the tax texts attach to income, not to exchange. Until the assessment you were quoted is produced, no tax figure can be verified or computed.",
     ["S01", "S17", "S18"], "Open — needs your document"),
    ("F02", "blocking", "The origin of the balance is unknown, so no tax can be computed",
     "PRC IIT rates differ by income type (3–45%, 5–35%, 20%) and the route differs too (documented income vs emigrant property vs inheritance). With no origin, any tax number would be an invention.",
     ["S17"], "Open — needs Q01/Q02"),
    ("F03", "material", "The USD 50,000 figure is not a universal ceiling",
     "S02 Art. 2 applies the annual total to settlement and to a domestic individual's purchase (境内个人购汇). S06 confirms the document-based purchase route for an overseas individual's legitimate current-account income. Treating USD 50,000 as a blanket cap on an overseas individual's documented income is not supported by those texts — but bank practice was not tested here.",
     ["S01", "S02", "S06"], "Partially resolved by text; practice unverified"),
    ("F04", "material", "Earlier sections express the CNY 620 HSBC cap as $86.97",
     "CNY 620 at the IRS 2025 yearly average of 7.129 is $86.97. At the bank's own published selling rate on 2026-11-11 (668.86 per 100 USD) the same CNY 620 is $92.70. Both are arithmetic on published numbers, but only the second is the rate a customer would pay. The repository count of files using each figure is on the audit page.",
     ["S07", "S09", "S13"], "Published; both bases shown"),
    ("F05", "material", "HSBC's tariff has two effective dates",
     "The English cover reads 'Effective from 31 Oct 2026' while the Chinese section header reads '2024年9月12日生效'. The fee rows used here were read from the English table. Which text governs a dispute is a legal question this pass cannot answer.",
     ["S09"], "Open — ask HSBC"),
    ("F06", "material", "Bank of China's fee schedule is headed 1 November 2014",
     "The schedule is the personal <em>e-banking</em> transfer fee table, not a counter tariff; no newer published version was located in this pass. The fee arithmetic uses the 2014 table and the 2026-11-11 board. A branch or the counter may apply a different, locally posted fee.",
     ["S08"], "Open — ask BOC"),
    ("F07", "note", "The BOC 'conversion rate' column is not a midpoint",
     "The board prints 671.91 as 中行折算价 while its own selling rate is 668.86, so the conversion column cannot be used to derive a spread. The margin here is measured against the midpoint of the buying and selling rates (667.46).",
     ["S07"], "Resolved by method"),
    ("F08", "note", "The eCFR penalty table has a dated column heading",
     "The page is displayed as current to 9 November 2026, but the adjusted column is headed by the last amendment date, 17 January 2025 (90 FR 5630). The $16,536 and $165,353 figures are read from that table.",
     ["S11"], "Published as read"),
    ("F09", "material", "The standing IRS exclusion page stops at 2023",
     "The FEIE page lists $107,600 (2020) to $120,000 (2023) only. The 2026 figure of $132,900 comes from IR-2025-103, which carries an 'archival or historical document' banner. Both are IRS pages; they are not the same vintage.",
     ["S14"], "Published with both links"),
    ("F10", "material", "The 2004 property-transfer staging was abolished",
     "S03 Art. 6 required half, then half, then the remainder over two years; S04 VI(2) cancels the staged-remittance requirement and VI(1) cancels the above-RMB-500,000 head-office filing. Any page that cites S03 alone is out of date. The count of repository files that still describe staging is on the audit page.",
     ["S03", "S04"], "Resolved by S04; older pages flagged"),
    ("F11", "material", "Art. 39 of the 2007 rules was repealed",
     "The amendment note on S02 records that Art. 39 was repealed by Hui Fa [2023] No. 8. Penalties must therefore be cited to Decree 532 (Arts. 39–45), not to the 2007 rules.",
     ["S01", "S02"], "Resolved"),
    ("F12", "material", "Two official definitions of 'domestic individual' disagree",
     "Decree 532 Art. 52(2) counts a foreign national continuously resident for one year or more; the PBOC's 2006 individual FX measures use an identity-document test. The 2006 measures were not re-read in this pass, so this is flagged rather than resolved.",
     ["S01"], "Open — not re-read this pass"),
    ("F13", "material", "Correspondent and receiving-bank charges are unpublished",
     "Neither tariff publishes third-party charges, and both disclaim them. The all-in totals here therefore exclude a real cost.",
     ["S08", "S09"], "Open — ask the banks"),
    ("F14", "material", "HSBC Global Transfer's exchange rate is not published",
     "The fee is published (Free for Premier/Private Banking, USD 20 for Advance), but the rate applied is not, so no all-in estimate can be computed for M04/M05. They are left blank.",
     ["S09"], "Blank by design"),
    ("F15", "material", "Card and ATM overseas cash limits were not verified",
     "No official page for the overseas cash limit or fee was read in this pass, so M11 has no price and no cap.",
     [], "Blank by design"),
    ("F16", "material", "Third-party platform limits were not verified",
     "No official page for the platform's CNY limits or fees was read in this pass, so M13 has no price and no cap.",
     [], "Blank by design"),
    ("F17", "material", "Investment-scheme caps were not verified",
     "QDII and similar schemes are not a transfer route for an existing balance; their caps were not read, so M14 is unpriced.",
     [], "Blank by design"),
    ("F18", "note", "Private Banking eligibility is not in the tariff",
     "The tariff defines Premier by a CNY 500,000 relationship balance but does not publish the Private Banking threshold. The zero fee in M02 assumes you already qualify.",
     ["S09"], "Open"),
    ("F19", "note", "Treaty article numbering is easy to get wrong",
     "In the U.S.–China treaty, dividends are Article 9, interest Article 10 and royalties Article 11. Each is capped at 10% of the gross amount. Pages that cite 'Article 10' for dividends are mis-citing.",
     ["S18"], "Resolved"),
    ("F20", "material", "The anti-structuring statute was not re-read",
     "CBP's page states the forfeiture and penalty consequences of a false or missing report. The specific provision on structuring was not re-read in this pass, so it is referred to generically.",
     ["S16"], "Open — not re-read this pass"),
    ("F21", "material", "Sections quote different same-day Bank of China snapshots",
     "The root hub quotes 666.30 / 669.11 at 10:25:02; the board read for this page is 666.06 / 668.86 at 15:30:04. The audit page counts the files using each. Both were true when read; only the later one matches this page's tables.",
     ["S07"], "Published; newer snapshot used here"),
    ("F22", "note", "Rounding",
     "Fees are computed in exact fractions from the published CNY figures, converted at 668.86 per 100 USD, and rounded half-up to the cent. A row can therefore differ by one cent from a calculation done in a different order.",
     ["S07", "S08", "S09"], "Method note"),
    ("F23", "blocking", "No personal fact was verified and no advice is given",
     "Account balance, residence, citizenship history, tax payments, state of residence and the bank's actual statements are all unknown. Nothing here is a tax, legal or investment determination.",
     [], "Standing limitation"),
    ("F24", "material", "The documents a bank will actually accept are not published",
     "S02 and S06 say 'source-of-funds documents including tax vouchers'; no official page read here lists the exact accepted documents or their age. Bank-level requirements remain unverified.",
     ["S02", "S06"], "Open — ask the bank"),
]

LAYERS = [
    ("L1", "PRC income tax on where the money came from", "PRC", "S17 Art. 3",
     "3%–45% comprehensive; 5%–35% business; 20% flat on property transfer, interest, dividends, royalties",
     "Rate published; amount depends on Q01/Q02", "S17"),
    ("L2", "PRC pre-departure tax settlement", "PRC", "S17 Art. 10(5)",
     "Settlement before cancelling household registration; amount not computable",
     "Applies only if you cancel the hukou (M07)", "S17"),
    ("L3", "PRC penalty for evasion-type conduct", "PRC (SAFE)", "S01 Arts. 39–40",
     "Up to 30% of the amount; 30% up to the equivalent amount in serious cases",
     "Only if the route is unlawful", "S01"),
    ("L4", "PRC penalty for private/disguised FX trading", "PRC (SAFE)", "S01 Art. 45",
     "Warning, confiscation, up to 30%; 30% up to the equivalent amount in serious cases",
     "Only if the route is unlawful", "S01"),
    ("L5", "Bank exchange margin", "Bank", "S07 (666.06 / 668.86)",
     "One-way cost versus the board midpoint: 0.210%",
     "Unavoidable on any conversion", "S07"),
    ("L6", "Bank wire fee", "Bank", "S09 2.2.4.1–2.2.4.2; S08",
     "HSBC: 0.1% min CNY 100 max CNY 500 + CNY 120 cable. BOC: 0.1% min CNY 50 max CNY 260 + CNY 150 cable",
     "Published", "S08"),
    ("L7", "Correspondent / receiving-bank charge", "Banks", "not published",
     "", "Blank — ask both banks (F13)", ""),
    ("L8", "U.S. tax on the exchange itself", "IRS", "S12 § 988(e)(2)",
     "Personal-transaction exchange gain ignored up to $200; the exception does not apply above that",
     "Published", "S12"),
    ("L9", "FBAR", "FinCEN / IRS", "S10; S11",
     "File above $10,000 aggregate at any time; maximum civil penalty $16,536 non-willful, $165,353 willful",
     "Published", "S10"),
    ("L10", "Form 8938 (FATCA)", "IRS", "not verified this pass",
     "", "Blank — threshold not re-read (F23)", ""),
    ("L11", "Form 3520 for a foreign gift or bequest", "IRS", "S15",
     "Above $100,000 aggregate from a nonresident alien or foreign estate; $20,573 for 2026 from foreign corporations/partnerships",
     "Published", "S15"),
    ("L12", "Foreign earned income exclusion", "IRS", "S14",
     "$132,900 for tax year 2026; $130,000 for 2025",
     "Only for qualifying foreign earned income, not for principal", "S14"),
    ("L13", "Foreign tax credit", "IRS", "not verified this pass",
     "", "Blank — not re-read (F23)", ""),
    ("L14", "Treaty withholding ceilings", "PRC, under treaty", "S18 Arts. 9(2), 10(2), 11(2)",
     "10% of the gross amount for dividends, interest and royalties",
     "Published", "S18"),
    ("L15", "U.S. currency reporting at the border", "CBP", "S16",
     "Report above $10,000 at one time; failure risks forfeiture and seizure",
     "Only for physical cash", "S16"),
]


# --------------------------------------------------------------------------
# Repository scan (reproducible; numbers on the audit page come from here)
# --------------------------------------------------------------------------
SCAN_PATTERNS = [
    ("86.97", "HSBC CNY 620 converted at the IRS 2025 average (7.129)", ["S09", "S13"]),
    ("92.43", "HSBC CNY 620 converted at a 2026-11-10 board rate", ["S07"]),
    ("92.70", "HSBC CNY 620 at the 2026-11-11 15:30:04 selling rate used here", ["S07"]),
    ("666.30", "BOC buy price in the 10:25:02 snapshot", ["S07"]),
    ("669.11", "BOC sell price in the 10:25:02 snapshot", ["S07"]),
    ("666.06", "BOC buy price in the 15:30:04 snapshot", ["S07"]),
    ("668.86", "BOC sell price in the 15:30:04 snapshot", ["S07"]),
    ("132,900", "2026 foreign earned income exclusion", ["S14"]),
    ("137,300", "a 2027 exclusion figure", ["S14"]),
    ("0.42%", "round-trip spread, used as a one-way 'bound' by some pages", ["S07"]),
    ("0.210%", "one-way margin versus the midpoint used here", ["S07"]),
    ("分次汇出", "staged remittance language superseded by Hui Fa [2014] No. 2", ["S03", "S04"]),
    ("2024年9月12日", "the Chinese effective-date header in HSBC's tariff", ["S09"]),
    ("7.129", "IRS 2025 yearly average CNY/USD", ["S13"]),
]
SKIP_DIRS = {".git", "__pycache__", ".cache", "node_modules", "canon-d6a42474"}
TEXT_EXT = {".html", ".htm", ".md", ".py", ".json", ".csv", ".txt", ".yml", ".yaml"}


def scan_repo() -> dict:
    hits = {p: [] for p, _d, _s in SCAN_PATTERNS}
    files = 0
    pages = 0
    sections = []
    for dirpath, dirnames, filenames in os.walk(REPO):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in sorted(filenames):
            path = Path(dirpath) / fn
            rel = path.relative_to(REPO).as_posix()
            if fn.endswith((".html", ".htm")):
                pages += 1
            if path.suffix.lower() not in TEXT_EXT:
                continue
            files += 1
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for pat, _desc, _srcs in SCAN_PATTERNS:
                if pat in text:
                    hits[pat].append(rel)
    for _pat in hits:
        hits[_pat].sort()
    for entry in sorted(REPO.iterdir()):
        if entry.is_dir() and entry.name not in SKIP_DIRS and (entry / "index.html").exists():
            sections.append(entry.name)
    return {
        "files_scanned": files,
        "html_pages": pages,
        "sections_with_index": sections,
        "patterns": [{"pattern": p, "description": d, "sources": s,
                      "file_count": len(hits[p]), "examples": hits[p][:6]}
                     for p, d, s in SCAN_PATTERNS],
    }


# --------------------------------------------------------------------------
# HTML
# --------------------------------------------------------------------------
NAV = [
    ("index.html", "Answer"), ("costs.html", "Costs"), ("methods.html", "Methods"),
    ("taxes.html", "Tax &amp; penalties"), ("questions.html", "Questions"),
    ("flags.html", "Flagged"), ("sources.html", "Sources"), ("audit.html", "Repo audit"),
]

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="theme-color" content="#0f1f1a">
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site"><div class="wrap">
  <a class="brand" href="index.html"><span class="mark">¥</span><span>China Money<small>CNY → USD · consolidated desk</small></span></a>
  <div class="site-meta">Every figure read from an official page on 2026-11-11 · research, not tax or legal advice</div>
</div></header>
<nav class="site" aria-label="Sections"><div class="wrap">
{nav}
</div></nav>
<main id="main"><div class="wrap">
"""

FOOT = """</div></main>
<footer class="footer"><div class="wrap">
  <p><strong>Scope.</strong> This desk prices published bank fees and the published exchange spread, and reports the
  statutes it read. It does not compute your tax, does not know your facts, and is not advice. Blank means
  “not verified”, never zero. Every table row links to the document it came from; unverified values are on the
  <a href="flags.html">Flagged for review</a> page.</p>
  <p>Built {date} from <a href="sources.html">18 official sources</a> read that day ·
  <a href="data/costs.csv">cost table (CSV)</a> ·
  <a href="audit.html">repository audit</a> ·
  <a href="../index.html">all repository sections</a></p>
</div></footer>
</body>
</html>
"""


def page(slug: str, title: str, desc: str, body: str) -> str:
    nav = "\n".join(
        '<a href="%s"%s>%s</a>' % (href, ' aria-current="page"' if href == slug else "", label)
        for href, label in NAV
    )
    html = HEAD.format(title=title, desc=desc, nav=nav) + body + FOOT.format(date=BUILD_DATE)
    (ROOT / slug).write_text(html, encoding="utf-8")
    return html


def src_link(sid: str) -> str:
    return '<a href="sources.html#%s">%s</a>' % (sid, sid)


def blank(flag: str, label: str = "not published") -> str:
    return '<a class="blank" href="flags.html#%s">%s ⚑%s</a>' % (flag, label, flag)


def price_cell(route: dict, amount: F) -> dict | None:
    return price_route(route, amount)


def money_row(amount: F, p: dict) -> str:
    return (usd(amount), cny_int(cny_for(amount)), usd(p["fee_usd"]), usd(p["margin"]),
            usd(p["total"]), pct(p["total"] / amount))


def build_index(scan: dict) -> None:
    # cheapest at each milestone among M01/M02/M03
    picks = []
    for amount in [F(10_000), F(50_000), F(100_000), F(200_000), F(400_000)]:
        best = None
        for rid in ("M01", "M03"):
            route = next(r for r in ROUTES if r["id"] == rid)
            p = price_route(route, amount)
            if best is None or p["total"] < best[1]["total"]:
                best = (route, p)
        route, p = best
        picks.append((amount, route, p))

    rows = []
    for amount, route, p in picks:
        rows.append(
            "<tr>"
            f'<td data-label="Amount"><strong>{usd(amount)}</strong></td>'
            f'<td data-label="Cheapest published route">{route["id"]} · {route["name"].split(":")[0]}</td>'
            f'<td class="num" data-label="Bank fee">{usd(p["fee_usd"])}</td>'
            f'<td class="num" data-label="Exchange margin">{usd(p["margin"])}</td>'
            f'<td class="num" data-label="All-in"><strong>{usd(p["total"])}</strong></td>'
            f'<td class="num" data-label="% of amount">{pct(p["total"]/amount)}</td>'
            f'<td class="src" data-label="Source">{src_link("S07")} {src_link("S09") if route["id"]!="M03" else src_link("S08")}</td>'
            "</tr>"
        )

    p400 = price_route(next(r for r in ROUTES if r["id"] == "M01"), F(400_000))
    p400b = price_route(next(r for r in ROUTES if r["id"] == "M03"), F(400_000))
    p400pb = price_route(next(r for r in ROUTES if r["id"] == "M02"), F(400_000))

    body = f"""
<span class="eyebrow">Consolidated answer · read {BUILD_DATE}</span>
<h1>The tax is rarely the problem. The evidence is.</h1>
<p class="lede">For a U.S. citizen with RMB in a mainland bank, the cheapest lawful route that moves the whole
balance in <em>one instruction</em> is one documented conversion and one wire: about
<strong>{usd(p400b["total"])}</strong> on <strong>$400,000</strong> at Bank of China's published e-banking fee and
board, or <strong>{usd(p400["total"])}</strong> at HSBC Premier/Advance. Almost all of it is the bank's exchange
margin. Carrying cash is marginally cheaper in fees but needs 40 declared trips; a balance already in USD would
need only the wire. No tax on the conversion itself appears in any text read here — what the bank gates is
<em>proof of where the money came from</em>.</p>

<div class="notice"><strong>Read this first.</strong> Your balance, its origin, your tax payments, your PRC
residence status and your U.S. filing history are all unknown here. Nothing on this site is a determination for
you, and no tax amount is shown, because none can be verified without those facts (flags F02, F23).
Values that are not published are blank and marked ⚑, never filled in.</div>

<div class="kpis">
  <div class="kpi"><p class="label">Tax on converting CNY→USD</p><div class="value">$0 found</div>
    <p class="sub">No exchange tax in the PRC texts read; they impose a document test instead. {src_link("S01")} {src_link("S02")}</p></div>
  <div class="kpi"><p class="label">All-in on $400,000, one instruction</p><div class="value">{usd(p400b["total"])}</div>
    <p class="sub">M03 BOC: {pct(p400b["total"]/F(400_000))} of the amount ({usd(p400b["fee_usd"])} fee + {usd(p400b["margin"])} margin). Private Banking would be {usd(margin_usd(F(400_000)))}. {src_link("S07")} {src_link("S08")}</p></div>
  <div class="kpi"><p class="label">The bigger number: exchange margin</p><div class="value">{pct(ONEWAY_MARGIN)}</div>
    <p class="sub">One-way cost versus the board midpoint (666.06 / 668.86 per 100 USD). At $400,000 that is {usd(margin_usd(F(400_000)))}. {src_link("S07")}</p></div>
  <div class="kpi"><p class="label">Published wire fee, $10k → $400k</p><div class="value">$32.89 → $92.70</div>
    <p class="sub">HSBC Premier/Advance. Private Banking individuals: $0.00. BOC: $32.43 → $61.30. {src_link("S09")} {src_link("S08")}</p></div>
</div>

<h2 id="answer">Answer first</h2>
<div class="grid2">
  <div class="card">
    <h3>If the RMB is already-taxed salary or business income</h3>
    <p>One documented bank conversion plus one wire is the route to assess first (<a href="methods.html#M01">M01</a> /
    <a href="methods.html#M03">M03</a>). The statute does not restrict current-account payments {src_link("S01")},
    and SAFE's 2026 guidance confirms an overseas individual converts legitimate current-account RMB income on
    ID plus source-of-funds documents including tax vouchers {src_link("S06")}. The gate is the tax record, not a tax.</p>
  </div>
  <div class="card">
    <h3>If the money is pre-emigration property or an inheritance</h3>
    <p>Use the property-transfer route (<a href="methods.html#M07">M07</a> / <a href="methods.html#M08">M08</a>):
    one application to SAFE where the household was registered, with the tax certificate and the ownership
    documents {src_link("S03")}. The staged remittance and the above-RMB-500,000 head-office filing were abolished
    in 2014 {src_link("S04")} — pages that still describe staging are out of date (F10).</p>
  </div>
  <div class="card">
    <h3>If the income was never taxed in China</h3>
    <p>No route removes the PRC tax on the income. Rates are 3%–45% comprehensive, 5%–35% business and 20% flat
    on property, interest, dividends and royalties {src_link("S17")}. Settle or document it first; a bank will ask
    for the tax record anyway {src_link("S02")}.</p>
  </div>
  <div class="card">
    <h3>What not to do</h3>
    <p>Splitting across relatives' annual totals, underground swaps and crypto bridges are unlawful. The FX statute
    prices evasion at up to 30% of the amount, or 30%–100% in serious cases {src_link("S01")}; virtual-currency
    exchange is an illegal financial activity and the civil act is void {src_link("S05")}. They are listed, without
    instructions, so they are not re-discovered as ideas.</p>
  </div>
</div>

<div class="notice"><strong>The U.S. side is reporting, not a transfer tax.</strong> Moving your own principal is not
income. Exchange gain on a personal transaction is ignored unless it exceeds $200 {src_link("S12")}; the 2026 foreign
earned income exclusion is $132,900 for qualifying earned income {src_link("S14")}. The expensive mistakes are
unreported accounts and unfiled forms: FBAR above $10,000 aggregate, with maximum civil penalties of $16,536
(non-willful) and $165,353 (willful) {src_link("S10")} {src_link("S11")}.</div>

<h2 id="costs">What it costs to move the money</h2>
<p>Published sender fees converted at HSBC's and BOC's own renminbi tariffs, plus the full one-way exchange margin
from the Bank of China board of {BOARD['stamp']} (668.86 CNY per USD). The margin is measured against the board
midpoint of {q(MID)}. Intermediary, receiving-bank and U.S. adviser costs are <em>not</em> included; they are not
published by these banks (F13).</p>
<div class="tbl-wrap"><div class="tbl-scroll"><table>
<caption>Five milestones · cheapest route on an ordinary account (M03 vs M01)</caption>
<thead><tr><th>Amount</th><th>Route</th><th class="num">Bank fee</th><th class="num">Exchange margin</th>
<th class="num">All-in</th><th class="num">% of amount</th><th>Source</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div></div>
<p class="muted">“All-in” = published sender fee + the full one-way margin. It excludes tax on the income, any
intermediary or receiving-bank charge, and any U.S. professional cost. Full 40-tier tables for every priced route:
<a href="costs.html">Costs</a>.</p>

<h2 id="methods">Every method, and whether it can be priced</h2>
<p>Fourteen lawful or conditional methods and five rejected ones. Eight of the lawful set have a published fee and can be
costed to the cent; the rest are blank with a flag, because no official page read here publishes their price
(F14–F17).</p>
<div class="tbl-wrap"><div class="tbl-scroll"><table>
<caption>Route status at a glance</caption>
<thead><tr><th>ID</th><th>Method</th><th>Status</th><th>Priceable from official pages?</th><th>Source</th></tr></thead>
<tbody>
{''.join(f'<tr><td data-label="ID"><a href="methods.html#{r["id"]}">{r["id"]}</a></td><td data-label="Method">{r["name"]}</td>'
         f'<td data-label="Status"><span class="pill {"bad" if r["status"]=="unlawful" else ("warn" if r["status"]=="conditional" else "")}">{r["status"]}</span></td>'
         f'<td data-label="Priceable">{"Yes — priced" if r["price"] else blank("F14" if r["id"] in ("M04","M05") else ("F15" if r["id"]=="M11" else ("F16" if r["id"]=="M13" else ("F17" if r["id"]=="M14" else "F23"))))}</td>'
         f'<td class="src" data-label="Source">{" ".join(src_link(s) for s in r["sources"]) if r["sources"] else blank("F23")}</td></tr>'
         for r in ROUTES)}
</tbody></table></div></div>

<h2 id="questions">What has to be answered before a decision</h2>
<p>Sixteen gating facts. Each one has a way to find out — that is the point of listing it. The first four decide
which route is even available; the fifth is the largest quantified risk in the file.</p>
<div class="tbl-wrap"><div class="tbl-scroll"><table>
<caption>First six of sixteen questions</caption>
<thead><tr><th>ID</th><th>Question</th><th>How to find out</th><th>Source</th></tr></thead>
<tbody>
{''.join(f'<tr><td data-label="ID"><a href="questions.html#{q[0]}">{q[0]}</a></td><td data-label="Question">{q[1]}</td>'
         f'<td data-label="How to find out">{q[3]}</td><td class="src" data-label="Source">{src_link(q[5][0]) if q[5] else blank("F23")}</td></tr>'
         for q in QUESTIONS[:6])}
</tbody></table></div></div>
<p><a href="questions.html">All sixteen questions, with what is known, what is missing and why it decides →</a></p>

<h2 id="flags">What could not be verified</h2>
<p>{len(FLAGS)} published flags. Three are blocking: the “considerable tax” you were quoted cannot be identified
(F01), the origin of the balance is unknown (F02), and no personal fact was verified (F23). Nothing on this page
depends on filling them in.</p>
<div class="card">
  <div class="flagrow"><span class="flagid">F01</span><div><strong>No conversion tax found.</strong>
    No reviewed text taxes CNY→USD exchange. Until the assessment is produced, no tax figure can be verified.</div></div>
  <div class="flagrow"><span class="flagid">F04</span><div><strong>Two ways to express the same CNY 620 cap.</strong>
    $86.97 at the IRS 2025 average (7.129) versus $92.70 at the bank's own 2026-11-11 selling rate. The audit page
    counts how many repository files use each.</div></div>
  <div class="flagrow"><span class="flagid">F21</span><div><strong>Same-day board snapshots differ.</strong>
    The root hub quotes 666.30 / 669.11 at 10:25:02; this page uses 666.06 / 668.86 at 15:30:04.</div></div>
</div>
<p><a href="flags.html">Every flag, with source links →</a></p>

<h2 id="verification">What was verified, and how</h2>
<div class="grid2">
  <div class="card"><h3>Read in this session</h3>
    <p>18 official documents, opened on {BUILD_DATE}, with the exact words relied on, a locator and the retrieval
    time on <a href="sources.html">Sources</a>. Fees are recomputed from those words with exact fractions; the
    verifier re-does every row independently.</p></div>
  <div class="card"><h3>Not asserted</h3>
    <p>That the pages still read the same tomorrow; any legal or tax conclusion for your facts; any figure not
    published by the institution itself. The repository contains {len(scan['sections_with_index'])} other dashboard
    sections; their disagreements are counted on the <a href="audit.html">audit page</a> rather than merged silently.</p></div>
</div>
"""
    page("index.html", "China money · CNY to USD, priced and sourced",
         "A consolidated, source-linked answer for moving lawful CNY out of mainland China: published bank fees and the exchange margin at every $10,000 step to $400,000, the documentary gate, tax layers, and what is still unverified.",
         body)


def build_costs() -> list[dict]:
    rows = []
    detail_blocks = []
    for route in ROUTES:
        if not route.get("price"):
            continue
        trs = []
        for amount in TIERS:
            p = price_route(route, amount)
            fee_src = "S09" if route["price"] in ("hsbc_tt", "hsbc_pb", "fxacct", "quota") else "S08"
            if route["price"] == "cash":
                fee_src = "S07"
            trs.append(
                "<tr>"
                f'<td data-label="Amount"><strong>{usd(amount)}</strong></td>'
                f'<td class="num" data-label="CNY needed">{cny_int(cny_for(amount))}</td>'
                f'<td class="num" data-label="Bank fee">{usd(p["fee_usd"]) if p["fee_usd"] else "$0.00"}</td>'
                f'<td class="num" data-label="FX margin">{usd(p["margin"]) if p["margin"] else "$0.00"}</td>'
                f'<td class="num" data-label="All-in"><strong>{usd(p["total"])}</strong></td>'
                f'<td class="num" data-label="% of amount">{pct(p["total"]/amount)}</td>'
                f'<td class="src" data-label="Source">{src_link(fee_src)} {src_link("S07")}</td>'
                "</tr>"
            )
            rows.append({
                "route": route["id"], "name": route["name"], "status": route["status"],
                "amount_usd": str(q(amount)), "cny_needed": str(q(cny_for(amount))),
                "fee_usd": str(q(p["fee_usd"])), "margin_usd": str(q(p["margin"])),
                "total_usd": str(q(p["total"])), "pct": str(q(p["total"] / amount * 100, "0.001")),
                "years": p["years"], "note": p["note"],
                "fee_source": fee_src, "rate_source": "S07",
            })
        note = ""
        if route["id"] == "M01":
            note = ("The CNY 500 cap binds from about USD 74,754 upward, which is why the fee stops rising. "
                    "Add CNY 200 if you instruct Pay Exact (S09).")
        elif route["id"] == "M03":
            note = "The CNY 260 cap plus CNY 150 cable binds from about USD 38,876 upward."
        elif route["id"] == "M06":
            note = ("One wire per calendar year: the fee column is the total of the annual wires, the margin is "
                    "charged on the whole amount. This route is only available to a domestic individual (S01 Art. 52(2)).")
        elif route["id"] == "M09":
            note = "No wire fee; the margin is paid on the notes rate, which the board prints equal to the exchange rate."
        elif route["id"] == "M10":
            note = "No new conversion, so no new margin; only the wire fee applies."
        elif route["id"] == "M02":
            note = "Individual Private Banking columns: issuance and cable both listed Free (S09 2.2.4.1–2.2.4.2)."
        elif route["id"] in ("M07", "M08"):
            note = ("Bank leg only. SAFE approval is required (S03, S04) and no SAFE fee is published, so the "
                    "approval cost is excluded and flagged.")
        detail_blocks.append(f"""
<details id="{route['id']}">
  <summary><span>{route['id']} · {route['name']}</span><span class="pill">{route['status']}</span></summary>
  <div class="body">
    <p class="muted">{note} Intermediary and receiving-bank charges are excluded (F13).</p>
    <div class="tbl-wrap"><div class="tbl-scroll"><table>
      <caption>40 tiers · USD 10,000 to 400,000 in 10,000 steps</caption>
      <thead><tr><th>Amount</th><th class="num">CNY needed</th><th class="num">Bank fee</th>
      <th class="num">FX margin</th><th class="num">All-in</th><th class="num">% of amount</th><th>Source</th></tr></thead>
      <tbody>{''.join(trs)}</tbody>
    </table></div></div>
  </div>
</details>""")

    with (DATA / "costs.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    milestones = []
    for amount in [F(10_000), F(50_000), F(100_000), F(200_000), F(400_000)]:
        cells = []
        for rid in ("M02", "M03", "M01", "M06", "M09", "M10"):
            route = next(r for r in ROUTES if r["id"] == rid)
            p = price_route(route, amount)
            cells.append(p)
        milestones.append((amount, cells))

    morder = ("M02", "M03", "M01", "M06", "M09", "M10")
    mrows = []
    for amount, cells in milestones:
        cells_html = "".join('<td class="num" data-label="%s">%s</td>' % (rid, usd(c["total"]))
                             for rid, c in zip(morder, cells))
        src_col = src_link("S07") + " " + src_link("S09") + " " + src_link("S08")
        mrows.append('<tr><td data-label="Amount"><strong>%s</strong></td>%s<td class="src" data-label="Source">%s</td></tr>'
                     % (usd(amount), cells_html, src_col))

    unpriced = [r for r in ROUTES if not r.get("price")]
    urows = ""
    for r in unpriced:
        if r["sources"]:
            sl = " ".join(src_link(s) for s in r["sources"])
        else:
            sl = blank("F15" if r["id"] == "M11" else ("F16" if r["id"] == "M13" else "F17"))
        urows += (f'<tr><td data-label="ID"><a href="methods.html#{r["id"]}">{r["id"]}</a></td>'
                  f'<td data-label="Method">{r["name"]}</td>'
                  f'<td data-label="Status"><span class="pill {"bad" if r["status"]=="unlawful" else "warn"}">{r["status"]}</span></td>'
                  f'<td data-label="Why not priced">{r["cons"][0] if r["cons"] else "No published price"}</td>'
                  f'<td class="src" data-label="Source">{sl}</td></tr>')

    _m400 = margin_usd(F(400_000))
    _fh = price_route(next(r for r in ROUTES if r["id"] == "M01"), F(400_000))["fee_usd"]
    _fb = price_route(next(r for r in ROUTES if r["id"] == "M03"), F(400_000))["fee_usd"]
    ratio_h = int(round(float(_m400 / _fh)))
    ratio_b = int(round(float(_m400 / _fb)))

    body = f"""
<span class="eyebrow">Costs · every published fee at every $10,000 step</span>
<h1>What it costs, from $10,000 to $400,000</h1>
<p class="lede">Two published inputs, one board: the banks' own fee tables and the Bank of China rate board read at
{BOARD['stamp']} (666.06 buy / 668.86 sell per 100 USD). Eight routes can be costed from those words. The rest are
blank and flagged, because official pages do not publish their price.</p>

<div class="notice"><strong>What “all-in” means here.</strong> Published sender fee + the full one-way exchange
margin versus the board midpoint ({q(MID)}). It does <em>not</em> include tax on the income, any correspondent or
receiving-bank charge, or any U.S. professional cost. It is an estimate from a board that the bank itself says is
indicative — the executed rate governs (S07).</div>

<div class="toc"><a href="#milestones">Milestones</a><a href="#compare">Route comparison</a>
<a href="#ladder">40-tier tables</a><a href="#unpriced">Not priceable</a><a href="#method">Method</a></div>

<h2 id="milestones">The five amounts that matter</h2>
<div class="tbl-wrap"><div class="tbl-scroll"><table>
<caption>All-in cost by route · USD</caption>
<thead><tr><th>Amount</th><th class="num">M02 Private Banking</th><th class="num">M03 BOC</th>
<th class="num">M01 HSBC Premier</th><th class="num">M06 50k/year</th><th class="num">M09 cash</th>
<th class="num">M10 already-USD</th><th>Source</th></tr></thead>
<tbody>{''.join(mrows)}</tbody></table></div></div>
<p class="muted">M06's figure is the fee of all annual wires plus the margin on the whole amount; it takes
<strong>8 calendar years</strong> at $400,000. M09 needs 40 trips. M10 only applies if the balance is already USD.</p>

<h2 id="compare">Where the money actually goes at $400,000</h2>
<div class="grid3">
  <div class="card"><h3>M03 · Bank of China</h3>
    <p class="code">{usd(p400b_fee := price_route(next(r for r in ROUTES if r['id']=='M03'), F(400_000))['fee_usd'])} fee<br>
    + {usd(price_route(next(r for r in ROUTES if r['id']=='M03'), F(400_000))['margin'])} margin<br>
    = <strong>{usd(price_route(next(r for r in ROUTES if r['id']=='M03'), F(400_000))['total'])}</strong></p>
    <p class="muted">0.1% capped at CNY 260 + CNY 150 cable (S08).</p></div>
  <div class="card"><h3>M02 · HSBC Private Banking</h3>
    <p class="code">$0.00 fee<br>+ {usd(margin_usd(F(400_000)))} margin<br>
    = <strong>{usd(margin_usd(F(400_000)))}</strong></p>
    <p class="muted">Individual PB columns are Free for issuance and cable (S09).</p></div>
  <div class="card"><h3>M01 · HSBC Premier/Advance</h3>
    <p class="code">{usd(price_route(next(r for r in ROUTES if r['id']=='M01'), F(400_000))['fee_usd'])} fee<br>
    + {usd(margin_usd(F(400_000)))} margin<br>
    = <strong>{usd(price_route(next(r for r in ROUTES if r['id']=='M01'), F(400_000))['total'])}</strong></p>
    <p class="muted">CNY 500 cap + CNY 120 cable (S09).</p></div>
</div>
<p>The wire fee is <em>not</em> the story: at $400,000 the exchange margin is roughly
<strong>{ratio_h}×</strong>
the HSBC fee and {ratio_b}× the BOC fee. At $10,000 the fixed fee dominates instead — which is why the percentage cost
falls as the amount rises.</p>

<h2 id="ladder">Every tier, every priceable route</h2>
<p>Tap a route to open its 40-tier table. Each row is arithmetic on the two published inputs and links to both.
The same numbers are in <a href="data/costs.csv">data/costs.csv</a>.</p>
{''.join(detail_blocks)}

<h2 id="unpriced">Routes that cannot be priced from official pages</h2>
<div class="tbl-wrap"><div class="tbl-scroll"><table>
<caption>Blank by design — not zero</caption>
<thead><tr><th>ID</th><th>Method</th><th>Status</th><th>Why it is blank</th><th>Source</th></tr></thead>
<tbody>{urows}</tbody></table></div></div>

<h2 id="method">Method and limits</h2>
<ul>
  <li><strong>Rate.</strong> Bank of China board of {BOARD['stamp']}: USD 666.06 buy / 668.86 sell per 100 USD.
  A customer buying USD pays the selling price. The board is indicative; the executed rate governs {src_link("S07")}.</li>
  <li><strong>Margin.</strong> (668.86 − 667.46) ÷ 667.46 = {pct(ONEWAY_MARGIN)} one way. The full buy–sell gap is
  {pct(ROUNDTRIP_SPREAD)}; using the full gap on a one-way conversion double-counts it, which is why the figure here
  is half of it (see F07, F21).</li>
  <li><strong>HSBC fee.</strong> 0.1% of the remittance amount, minimum CNY 100, maximum CNY 500, plus CNY 120 cable
  for Premier/Advance; individual Private Banking is Free on both lines {src_link("S09")}.</li>
  <li><strong>BOC fee.</strong> 0.1%, minimum CNY 50, maximum CNY 260, plus CNY 150 cable outside Hong Kong/Macau/Taiwan
  {src_link("S08")}. This is the personal <em>e-banking</em> schedule, headed 1 November 2014; a counter tariff may
  differ (F06).</li>
  <li><strong>Excluded.</strong> Correspondent and receiving-bank charges (F13), tax on the income (F02), U.S.
  professional fees, and any tax penalty.</li>
</ul>
"""
    page("costs.html", "Costs · CNY to USD at every $10,000 step, $10k–$400k",
         "Published bank fees plus the one-way exchange margin for every priceable CNY-to-USD route, at each $10,000 step from $10,000 to $400,000, with source links and blanks where nothing is published.",
         body)
    return rows


def build_methods() -> None:
    rows = []
    for r in ROUTES:
        p100 = price_route(r, F(100_000))
        link = f'<a href="#{r["id"]}">{r["id"]}</a>'
        status = f'<span class="pill {"bad" if r["status"]=="unlawful" else ("warn" if r["status"]=="conditional" else "")}">{r["status"]}</span>'
        price = usd(p100["total"]) if p100 else blank(
            "F14" if r["id"] in ("M04", "M05") else "F15" if r["id"] == "M11"
            else "F16" if r["id"] == "M13" else "F17" if r["id"] == "M14" else "F23")
        src = " ".join(src_link(s) for s in r["sources"]) if r["sources"] else blank("F23")
        rows.append(f'<tr><td data-label="ID">{link}</td><td data-label="Method">{r["name"]}</td>'
                    f'<td data-label="Status">{status}</td><td data-label="All-in at $100k">{price}</td>'
                    f'<td class="src" data-label="Source">{src}</td></tr>')
    blocks = []
    for r in ROUTES:
        p100 = price_route(r, F(100_000))
        steps = "".join(f"<li>{s}</li>" for s in r["steps"])
        pros = "".join(f"<li>{s}</li>" for s in r["pros"]) or "<li>—</li>"
        cons = "".join(f"<li>{s}</li>" for s in r["cons"]) or "<li>—</li>"
        price_line = (f'All-in at $100,000: <strong>{usd(p100["total"])}</strong> '
                      f'({usd(p100["fee_usd"])} fee + {usd(p100["margin"])} margin) — '
                      f'<a href="costs.html#{r["id"]}">all 40 tiers</a>') if p100 else blank(
            "F14" if r["id"] in ("M04", "M05") else "F15" if r["id"] == "M11"
            else "F16" if r["id"] == "M13" else "F17" if r["id"] == "M14" else "F23")
        blocks.append(f"""
<details id="{r['id']}">
  <summary><span>{r['id']} · {r['name']}</span>
    <span class="pill {'bad' if r['status']=='unlawful' else ('warn' if r['status']=='conditional' else '')}">{r['status']}</span></summary>
  <div class="body">
    <p>{price_line}</p>
    <div class="grid2">
      <div><h3>Who can use it</h3><p>{r['who']}</p>
        <h3>Limit</h3><p>{r['cap']}</p>
        <h3>Documents</h3><p>{r['papers']}</p></div>
      <div><h3>PRC tax</h3><p>{r['prc_tax']}</p>
        <h3>U.S. side</h3><p>{r['us_side']}</p></div>
    </div>
    <h3>Step by step</h3><ol class="steps">{steps}</ol>
    <div class="grid2"><div><h3>Pros</h3><ul>{pros}</ul></div><div><h3>Cons</h3><ul>{cons}</ul></div></div>
    <p class="muted">Sources: {" ".join(src_link(s) for s in r['sources']) if r['sources'] else 'none — unpriced and unverified'}</p>
  </div>
</details>""")

    body = f"""
<span class="eyebrow">Methods · 14 lawful or conditional, 5 rejected</span>
<h1>Every way to turn CNY into USD that was found</h1>
<p class="lede">Two bank-wire routes do the work for a documented balance. Property transfer covers pre-emigration
property and inheritance. Cash and already-USD balances are edge cases. The unlawful ones are listed with their
statutory penalties and without instructions.</p>
<div class="notice"><strong>No route here is recommended for you.</strong> Which one is available depends on facts
nobody has established yet — the origin of the money, your PRC status, your tax records and your U.S. filing history.
Start with the <a href="questions.html">sixteen questions</a>.</div>

<div class="tbl-wrap"><div class="tbl-scroll"><table>
<caption>All 19 catalogued methods</caption>
<thead><tr><th>ID</th><th>Method</th><th>Status</th><th>All-in at $100k</th><th>Source</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div></div>
<p class="muted">“All-in at $100k” = published sender fee + one-way margin from the 2026-11-11 board. Blank means
no official price was found — not zero.</p>

<h2>Details, steps and trade-offs</h2>
{''.join(blocks)}
"""
    page("methods.html", "Methods · every CNY-to-USD route, with steps and trade-offs",
         "Fifteen lawful or conditional ways to convert CNY to USD plus five rejected ones, each with who can use it, the cap, the documents, the PRC and U.S. treatment, numbered steps, pros and cons.",
         body)


def build_taxes() -> None:
    rows = []
    for lid, name, who, cite, amount, status, sid in LAYERS:
        rows.append(
            f'<tr><td data-label="ID">{lid}</td><td data-label="Layer"><strong>{name}</strong></td>'
            f'<td data-label="Imposed by">{who}</td><td data-label="Rule">{cite}</td>'
            f'<td data-label="Amount">{amount if amount else blank("F13")}</td>'
            f'<td data-label="Status">{status}</td>'
            f'<td class="src" data-label="Source">{src_link(sid) if sid else blank("F23")}</td></tr>')

    p100b = price_route(next(r for r in ROUTES if r["id"] == "M03"), F(100_000))
    body = f"""
<span class="eyebrow">Tax and penalties · what is a tax, a fee, a fine</span>
<h1>Breaking down the “conversion penalty”</h1>
<p class="lede">Four different things are usually called a conversion penalty. Only one is a tax, and it attaches to
where the money came from — not to the exchange. The rest are a bank margin, a bank fee, and U.S. reporting
obligations with penalties of their own.</p>

<div class="notice"><strong>No tax amount is shown for your balance.</strong> The PRC rate depends on the type of
income, and nobody has established what your balance is made of (F01, F02). Any dollar figure for “the tax” would be
invented.</div>

<div class="tbl-wrap"><div class="tbl-scroll"><table>
<caption>Fifteen layers · what each one is and whether it is published</caption>
<thead><tr><th>ID</th><th>Layer</th><th>Imposed by</th><th>Rule</th><th>Amount</th><th>Status</th><th>Source</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div></div>

<h2>1 · The tax is on the income, not the exchange</h2>
<p>PRC individual income tax applies by income type: 3%–45% progressive on comprehensive income (salary, labour
remuneration, author's remuneration, royalties), 5%–35% on business income, and a flat 20% on interest, dividends,
property rental, property transfer and incidental income {src_link("S17")}. The law contains no tax on converting
RMB into foreign currency. Decree 532 states that current international payments and transfers are not restricted
{src_link("S01")}; what it requires is a genuine, lawful transaction basis, which the bank checks.</p>
<p>If you cancel PRC household registration to emigrate, the law requires a tax settlement <em>before</em> the
cancellation {src_link("S17")} — that is the point at which a PRC tax bill on pre-emigration property becomes
concrete.</p>

<h2>2 · The bank margin is the largest published cost</h2>
<p>At the board read today the customer buys USD at 668.86 and the midpoint is {q(MID)}. That is
<strong>{pct(ONEWAY_MARGIN)}</strong> one way. On $100,000 it is {usd(margin_usd(F(100_000)))}; on $400,000 it is
{usd(margin_usd(F(400_000)))}. It is not a tax, it is not itemised on the tariff, and it is unavoidable on any
conversion {src_link("S07")}.</p>

<h2>3 · The published fees are small by comparison</h2>
<p>On $100,000: BOC {usd(p100b["fee_usd"])}, HSBC Premier/Advance {usd(price_route(next(r for r in ROUTES if r['id']=='M01'), F(100_000))['fee_usd'])},
HSBC individual Private Banking {usd(F(0))} {src_link("S08")} {src_link("S09")}. Both tariffs cap the percentage fee
in renminbi, so the fee stops growing while the margin does not.</p>

<h2>4 · The U.S. side is reporting</h2>
<ul>
  <li><strong>§988.</strong> Exchange gain on an individual's personal transaction is ignored unless it exceeds
  $200 {src_link("S12")}. Above that the exception does not apply.</li>
  <li><strong>FBAR.</strong> Required above $10,000 aggregate at any time in the year; due 15 April with an automatic
  extension to 15 October {src_link("S10")}. Current civil maximums: $16,536 non-willful, $165,353 willful
  {src_link("S11")}.</li>
  <li><strong>Form 3520.</strong> A foreign gift or bequest above $100,000 aggregate from a nonresident alien or
  foreign estate must be reported {src_link("S15")}.</li>
  <li><strong>FEIE.</strong> $132,900 for tax year 2026, $130,000 for 2025 — for qualifying foreign earned income,
  not for principal {src_link("S14")}.</li>
  <li><strong>Treaty.</strong> PRC withholding on dividends (Art. 9), interest (Art. 10) and royalties (Art. 11) is
  capped at 10% of the gross amount {src_link("S18")}.</li>
</ul>
<p class="muted">Form 8938 thresholds and the foreign tax credit mechanics were not re-read in this pass and are left
blank rather than paraphrased from memory (F23).</p>

<h2>5 · Penalties apply to unlawful routes, not to converting</h2>
<p>Evasion-type conduct (Arts. 39–40) and private or disguised FX trading (Art. 45) carry a fine of up to 30% of the
amount, or 30% up to the equivalent amount in serious cases, plus possible criminal liability {src_link("S01")}.
Buying foreign exchange with false documents falls under Art. 40. Virtual-currency exchange is an illegal financial
activity, the civil act is void and the loss falls on the investor {src_link("S05")}. None of these is a cost of a
lawful conversion.</p>

<h2>What a $100,000 transfer costs, layer by layer</h2>
<div class="tbl-wrap"><div class="tbl-scroll"><table>
<caption>M03 (Bank of China) at $100,000 — only published layers</caption>
<thead><tr><th>Layer</th><th class="num">Amount</th><th>Source</th></tr></thead>
<tbody>
<tr><td data-label="Layer">Bank fee (0.1%, min 50, max 260 + 150 cable)</td><td class="num" data-label="Amount">{usd(p100b['fee_usd'])}</td><td class="src" data-label="Source">{src_link("S08")}</td></tr>
<tr><td data-label="Layer">Exchange margin versus midpoint</td><td class="num" data-label="Amount">{usd(p100b['margin'])}</td><td class="src" data-label="Source">{src_link("S07")}</td></tr>
<tr><td data-label="Layer">Correspondent / receiving bank</td><td class="num" data-label="Amount">{blank("F13")}</td><td class="src" data-label="Source">none</td></tr>
<tr><td data-label="Layer">PRC tax on the income</td><td class="num" data-label="Amount">{blank("F02")}</td><td class="src" data-label="Source">{src_link("S17")} rate only</td></tr>
<tr><td data-label="Layer">U.S. federal tax on the transfer</td><td class="num" data-label="Amount">$0.00 <span class="muted">(principal; §988 gain ≤ $200 ignored)</span></td><td class="src" data-label="Source">{src_link("S12")}</td></tr>
<tr><td data-label="Layer"><strong>Total of the published layers</strong></td><td class="num" data-label="Amount"><strong>{usd(p100b['total'])}</strong></td><td class="src" data-label="Source">{src_link("S07")} {src_link("S08")}</td></tr>
</tbody></table></div></div>
"""
    page("taxes.html", "Tax and penalties · the four layers behind a “conversion penalty”",
         "PRC income tax on the origin, the bank's exchange margin and fees, PRC FX penalties, and U.S. reporting obligations — each with the exact rule and source, and blanks where an amount cannot be verified.",
         body)


def build_questions() -> None:
    cards = []
    for qid, q, known, how, why, srcs in QUESTIONS:
        cards.append(f"""
<details id="{qid}">
  <summary><span>{qid} · {q}</span><span class="pill gray">gating</span></summary>
  <div class="body">
    <h3>What we know</h3><p>{known}</p>
    <h3>How to find out</h3><p>{how}</p>
    <h3>Why it decides something</h3><p>{why}</p>
    <p class="muted">Source: {" ".join(src_link(s) for s in srcs) if srcs else "none — this is an unknown"}</p>
  </div>
</details>""")
    body = f"""
<span class="eyebrow">Decision register · 16 questions</span>
<h1>What has to be answered before any decision</h1>
<p class="lede">Each question below is gating: the route or the cost changes depending on the answer. None of them is
answered by this repository, because every one depends on private facts. Each has a stated way to find out.</p>
<div class="notice"><strong>How to use this page.</strong> Answer Q01–Q05 first. Until Q01 (origin) and Q02 (PRC tax
status) are answered, no route can be selected and no tax figure can be computed. Q05 is the largest quantified
risk in the file: unfiled U.S. reports carry penalties far larger than any bank fee.</div>
<div class="tbl-wrap"><div class="tbl-scroll"><table>
<caption>All sixteen, in order</caption>
<thead><tr><th>ID</th><th>Question</th><th>Status</th><th>Source</th></tr></thead>
<tbody>
{''.join(f'<tr><td data-label="ID"><a href="#{q[0]}">{q[0]}</a></td><td data-label="Question">{q[1]}</td><td data-label="Status">{blank("F02" if q[0] in ("Q01","Q02") else "F23")}</td><td class="src" data-label="Source">{src_link(q[5][0]) if q[5] else blank("F23")}</td></tr>' for q in QUESTIONS)}
</tbody></table></div></div>
<h2>The register</h2>
{''.join(cards)}
"""
    page("questions.html", "Questions · the 16 gating facts before any CNY-to-USD decision",
         "The sixteen facts that must be established before a route or a tax figure can be chosen, each with what is known, what is missing, how to find out, and why it decides something.",
         body)


def build_flags() -> None:
    rows = []
    for fid, sev, title, detail, srcs, status in FLAGS:
        pill = "bad" if sev == "blocking" else ("warn" if sev == "material" else "gray")
        rows.append(f"""
<div class="flagrow" id="{fid}">
  <div class="flagid">{fid}<br><span class="pill {pill}">{sev}</span></div>
  <div>
    <h3>{title}</h3>
    <p class="small">{detail}</p>
    <p class="small muted">Status: {status} · Sources: {" ".join(src_link(s) for s in srcs) if srcs else "none — nothing was read for this item"}</p>
  </div>
</div>""")
    body = f"""
<span class="eyebrow">Flagged for review · {len(FLAGS)} items</span>
<h1>What is unverified, conflicting or blank</h1>
<p class="lede">These are published rather than resolved. A flag is not a failed check: it marks a place where an
official source is silent, where two official sources disagree, or where the repository contains conflicting figures.
Nothing here blocks use of the pages; it blocks treating a blank as zero.</p>
<div class="notice"><strong>Three blocking items.</strong> F01: no conversion tax was found, so the “considerable tax”
you were quoted cannot be verified. F02: the origin of the balance is unknown, so no tax can be computed. F23: no
personal fact was verified and nothing here is advice.</div>
<div class="tbl-wrap"><div class="tbl-scroll"><table>
<caption>Index</caption>
<thead><tr><th>ID</th><th>Severity</th><th>Item</th><th>Status</th><th>Source</th></tr></thead>
<tbody>
{''.join(f'<tr><td data-label="ID"><a href="#{f[0]}">{f[0]}</a></td><td data-label="Severity"><span class="pill {"bad" if f[1]=="blocking" else ("warn" if f[1]=="material" else "gray")}">{f[1]}</span></td><td data-label="Item">{f[2]}</td><td data-label="Status">{f[5]}</td><td class="src" data-label="Source">{" ".join(src_link(s) for s in f[4]) if f[4] else blank("F23")}</td></tr>' for f in FLAGS)}
</tbody></table></div></div>
<h2>The register</h2>
{''.join(rows)}
"""
    page("flags.html", "Flagged for review · unverified and conflicting items",
         "Every unverified, blank or conflicting item behind the CNY-to-USD research, with severity, status and the official sources that were read.",
         body)


def build_sources() -> None:
    sources = json.loads((DATA / "sources.json").read_text(encoding="utf-8"))["sources"]
    blocks = []
    for s in sources:
        quotes = "".join(
            f'<blockquote><span class="zh">{q["text"]}</span><br><span class="muted">{q["locator"]}</span></blockquote>'
            for q in s["quotes"])
        blocks.append(f"""
<details id="{s['id']}">
  <summary><span>{s['id']} · {s['title']}</span><span class="pill gray">{s['language']}</span></summary>
  <div class="body">
    <p class="small"><strong>{s['publisher']}</strong> · locator: {s['locator']} · read {s['retrieved_utc']}</p>
    <p class="small"><a href="{s['url']}" rel="noopener">{s['url']}</a></p>
    {quotes}
    <p class="small muted">Used for: {s['used_for']}</p>
  </div>
</details>""")
    body = f"""
<span class="eyebrow">Sources · {len(sources)} official documents</span>
<h1>Every document read, with the exact words</h1>
<p class="lede">Each source was opened on 2026-11-11. The quotations are copied from the page, with the article or
table row. Figures elsewhere on this site are computed only from these quotations. A page that could not be opened
or that does not publish a value is not listed as if it did.</p>
<div class="notice"><strong>What a source establishes.</strong> That the publisher wrote this on this date. It does not
establish that the rule will still read the same tomorrow, and it does not make the rule apply to your facts.</div>
<div class="tbl-wrap"><div class="tbl-scroll"><table>
<caption>Register</caption>
<thead><tr><th>ID</th><th>Publisher</th><th>Document</th><th>Locator</th><th>Language</th><th>Official page</th></tr></thead>
<tbody>
{''.join(f'<tr><td data-label="ID"><a href="#{s["id"]}">{s["id"]}</a></td><td data-label="Publisher">{s["publisher"]}</td><td data-label="Document">{s["title"]}</td><td data-label="Locator">{s["locator"]}</td><td data-label="Language">{s["language"]}</td><td class="src" data-label="Official page"><a href="{s["url"]}" rel="noopener">open ↗</a></td></tr>' for s in sources)}
</tbody></table></div></div>
<h2>The documents</h2>
{''.join(blocks)}
"""
    page("sources.html", "Sources · 18 official documents read on 2026-11-11",
         "The eighteen official PRC, bank and U.S. documents behind the CNY-to-USD dashboard, each with its URL, locator, retrieval time and the exact words relied on.",
         body)


def build_audit(scan: dict) -> None:
    prows = []
    for p in scan["patterns"]:
        ex = ", ".join(p["examples"][:3]) if p["examples"] else "—"
        prows.append(f'<tr><td data-label="Pattern"><span class="mono">{p["pattern"]}</span></td>'
                     f'<td data-label="Meaning">{p["description"]}</td>'
                     f'<td class="num" data-label="Files">{p["file_count"]}</td>'
                     f'<td class="mono" data-label="Examples">{ex}</td>'
                     f'<td class="src" data-label="Source">{" ".join(src_link(s) for s in p["sources"])}</td></tr>')
    secs = " ".join(f'<span class="pill gray">{s}</span>' for s in scan["sections_with_index"])
    body = f"""
<span class="eyebrow">Repository audit · generated {BUILD_DATE}</span>
<h1>What the repository contains, and where it disagrees</h1>
<p class="lede">The counts on this page are produced by scanning the repository at build time and are re-checked by
<code>verify.py</code>. Nothing here is typed by hand. The point is not to shame earlier sections — they are
independent research runs — but to show which of them quote a superseded figure and where the same fact appears in
two forms.</p>

<div class="kpis">
  <div class="kpi"><p class="label">Text files scanned</p><div class="value">{scan['files_scanned']:,}</div>
    <p class="sub">excluding .git, caches and this section</p></div>
  <div class="kpi"><p class="label">HTML pages</p><div class="value">{scan['html_pages']:,}</div>
    <p class="sub">including earlier dashboards</p></div>
  <div class="kpi"><p class="label">Sections with an index</p><div class="value">{len(scan['sections_with_index'])}</div>
    <p class="sub">each an independent research run</p></div>
  <div class="kpi"><p class="label">Sources read here</p><div class="value">18</div>
    <p class="sub">this session, 2026-11-11</p></div>
</div>

<h2 id="patterns">The same fact, in different forms</h2>
<div class="tbl-wrap"><div class="tbl-scroll"><table>
<caption>Reproducible text scan · file counts</caption>
<thead><tr><th>Pattern</th><th>What it represents</th><th class="num">Files</th><th>Examples</th><th>Source</th></tr></thead>
<tbody>{''.join(prows)}</tbody></table></div></div>
<p class="muted">A file count is not an error count: a section may quote two rates deliberately, to show a
discrepancy. What the scan establishes is that a reader will meet more than one version of the same number.</p>

<h2>The findings that follow from it</h2>
<ul>
  <li><strong>The CNY 620 HSBC cap appears as both $86.97 and $92.43</strong> (and now $92.70 here). The first is the
  cap converted at the IRS 2025 yearly average (7.129); the second at a 2026-11-10 board rate; the third at the
  board read for this page. All three are arithmetic, but only one matches the rate a customer would pay on the day
  (F04, F21).</li>
  <li><strong>Same-day Bank of China snapshots differ.</strong> The 10:25:02 board (666.30 / 669.11) and the
  15:30:04 board (666.06 / 668.86) both appear. The tables here use the later one and say so.</li>
  <li><strong>The 2026 exclusion appears as $132,900 and $137,300.</strong> The first is published in IR-2025-103;
  the second is not in any IRS page read for this pass and is therefore not used (F09).</li>
  <li><strong>Staged emigrant remittance survives in older text.</strong> Files still containing 分次汇出 describe a
  requirement cancelled by Hui Fa [2014] No. 2 §VI(2) (F10).</li>
  <li><strong>The HSBC tariff carries two effective dates</strong> (English cover 31 October 2026, Chinese header
  12 September 2024), and the scan finds the Chinese date in the file itself (F05).</li>
  <li><strong>Root-hub counts mix sections.</strong> The landing page combines method counts, row counts and source
  counts that come from different research runs; they are all individually sourced but do not describe one dataset.</li>
</ul>

<h2>What this session changed</h2>
<p>Only added: this section and one navigation card. No other section's content was edited, and no figure from
another section was carried over without being re-read. Where the same fact differs, both versions are published
here and the one used is named.</p>

<h2>Verification performed</h2>
<ul>
  <li>Every cost row is recomputed from the published CNY figures by <code>verify.py</code> with exact fractions and
  compared cell by cell with the HTML and the CSV.</li>
  <li>Every table row on every page is checked for a link to the publishing institution's own page.</li>
  <li>Every blank cell is checked to link to a flag.</li>
  <li>All local links and anchors are resolved; the scan above is re-run and compared with <code>data/repo-scan.json</code>.</li>
  <li>Each source quotation is checked to appear in <code>data/sources.json</code> and each cited source id to exist.</li>
</ul>

<h2>Other sections in this repository</h2>
<p>{secs}</p>
<p class="muted">They remain online as independent runs. This section does not claim they are wrong; it claims only
what it re-read itself.</p>
"""
    page("audit.html", "Repository audit · conflicts, duplicates and reproducible counts",
         "A build-time scan of the repository showing where the same figure appears in conflicting forms, with file counts, examples and the sources behind the version used here.",
         body)


def write_favicon() -> None:
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
           '<rect width="64" height="64" rx="14" fill="#0f1f1a"/>'
           '<text x="32" y="45" font-size="36" text-anchor="middle" fill="#7fd4bd" '
           'font-family="system-ui,sans-serif" font-weight="700">¥</text></svg>')
    (ROOT / "assets" / "favicon.svg").write_text(svg, encoding="utf-8")


def main() -> None:
    DATA.mkdir(exist_ok=True)
    scan = scan_repo()
    (DATA / "repo-scan.json").write_text(json.dumps(scan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    build_index(scan)
    build_costs()
    build_methods()
    build_taxes()
    build_questions()
    build_flags()
    build_sources()
    build_audit(scan)
    write_favicon()
    print("built: index, costs, methods, taxes, questions, flags, sources, audit")
    print("scan: %d files, %d pages, %d sections" % (scan["files_scanned"], scan["html_pages"],
                                                     len(scan["sections_with_index"])))
    print("one-way margin %s; round-trip spread %s" % (pct(ONEWAY_MARGIN), pct(ROUNDTRIP_SPREAD)))
    for amount in (F(10_000), F(100_000), F(400_000)):
        for rid in ("M02", "M03", "M01"):
            p = price_route(next(r for r in ROUTES if r["id"] == rid), amount)
            print(rid, usd(amount), "fee", usd(p["fee_usd"]), "margin", usd(p["margin"]), "total", usd(p["total"]))


if __name__ == "__main__":
    main()
