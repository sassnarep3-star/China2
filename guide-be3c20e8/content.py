#!/usr/bin/env python3
"""Editorial content for the be3c20e8 decision guide.

All numeric facts are pulled from data/sources.json with fig()/n(); none are
typed into the prose.  `{{PLACEHOLDER}}` values are computed by build.py from
model outputs and are checked by verify.py.
"""
import json
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEDGER = json.loads((HERE / "data/sources.json").read_text(encoding="utf-8"))
SRC = {s["id"]: s for s in LEDGER["sources"]}
READ = LEDGER["retrieved"]


def fig(sid, key):
    return SRC[sid]["figures"][key]


def n(sid, key):
    return Decimal(str(fig(sid, key)))


def fmt(value, places=""):
    return format(value, "," + places) if places else format(value, ",.0f")


def usd(value):
    value = Decimal(str(value))
    return "$" + fmt(value, ".2f") if value != value.to_integral_value() else "$" + fmt(value, ".0f")


def cny(value):
    value = Decimal(str(value))
    return "CNY " + fmt(value, ".2f") if value != value.to_integral_value() else "CNY " + fmt(value, ".0f")


def pct(value):
    return fmt(Decimal(str(value)), ".2f") + "%"


def rate(value):
    return fmt(Decimal(str(value)), ".4f")


def sell_boc():
    return n("B01", "boc_sell_tt_per100") / n("B01", "per")


def buy_boc():
    return n("B01", "boc_buy_tt_per100") / n("B01", "per")


def sell_hsbc():
    return n("B02", "hsbc_sell_tt")


def buy_hsbc():
    return n("B02", "hsbc_buy_tt")


def cash_buy_hsbc():
    return n("B02", "hsbc_buy_cash")


SUMMARY = [
    {
        "id": "S1", "title": "Least-tax answer first",
        "text": "No PRC provision reviewed here imposes a separate tax on the mere act of converting CNY into USD. That is not a conclusion that your balance is tax-free: PRC individual income tax applies by income type and residence, and a bank can refuse the transaction without lawful-source and tax documents. The least-penalty path is to settle or document any tax on the underlying funds, use one of the lawful bank/approval routes, avoid prohibited workarounds, and meet U.S. reporting duties on time.",
        "sources": ["B08", "B09", "B10", "B19", "B20", "B21", "B27", "B29", "B32"],
    },
    {
        "id": "S2", "title": "The gate is documentary, not a quota trick",
        "text": "For a foreign individual with lawful current-account RMB income, SAFE's rule is valid ID plus transaction-amount source materials including tax documents. A foreign permanent-residence ID card holder may use the annual convenience quota; other foreign individuals generally do not get that quota merely from holding a foreign passport. Emigrant and inheritance property transfers are separate approval routes.",
        "sources": ["B08", "B10", "B11", "B12", "B13", "B14"],
    },
    {
        "id": "S3", "title": "Published known costs, not an all-in quote",
        "text": "At the smallest tier, the lowest published known-component total among routes with a published fee or rate is {{LOW_10_METHOD}} at {{LOW_10_VALUE}}. At the largest tier it is {{LOW_400_METHOD}} at {{LOW_400_VALUE}}. These are arithmetic illustrations from a reference-only board and published tariffs; every all-in total remains blank because correspondent, receiving, future-rate and personal-tax inputs are unpublished.",
        "sources": ["B01", "B02", "B03", "B04", "B07", "B27"],
    },
    {
        "id": "S4", "title": "The exchange spread dominates large transfers",
        "text": "BOC's published USD sell and buy prices imply a midpoint spread of {{BOC_SPREAD_PCT}}; HSBC's published sell and TT buy prices imply {{HSBC_SPREAD_PCT}}. At the largest tier those board spreads are {{BOC_SPREAD_400}} and {{HSBC_SPREAD_400}}. The bank pages say their rates are for reference only, so neither is an executable quote.",
        "sources": ["B01", "B02", "B03", "B04"],
    },
    {
        "id": "S5", "title": "The penalty is a stack, not one number",
        "text": "Separate: tax on the underlying income or asset; the bank's document review; the FX spread; sender/cable/card/cash fees; third-party and receiving-bank charges; PRC fines for evasion, splitting or underground dealing; possible U.S. ordinary gain on personal currency disposition above {{DE_MINIMIS}}; and reporting penalties for missed FBAR, {{FORM8938}}, {{FORM3520}} or CBP forms. Filing compliance is not a conversion tax.",
        "sources": ["B09", "B15", "B18", "B20", "B21", "B23", "B24", "B27", "B28", "B29", "B32"],
    },
    {
        "id": "S6", "title": "Personal facts remain blank",
        "text": "The origin of the CNY, its tax history, your PRC residence and emigration status, acquisition exchange rate, bank's written eligibility decision, U.S. filing history, and FEIE/FTC facts were not supplied. Every one is a gating question with a discovery action on the Questions page; none is inferred. A {{DE_MINIMIS}} personal-transaction threshold and a {{FEIE2026}} exclusion cap are statutory figures, not a personal tax calculation.",
        "sources": ["B07", "B08", "B11", "B14", "B20", "B21", "B23", "B25", "B27", "B30", "B34"],
    },
    {
        "id": "S7", "title": "Flagged items do not block publication",
        "text": "This pass read {{SOURCE_COUNT}} primary sources on {{READ}}, scanned {{SCANNED_FILES}} tracked repository files line by line, and recomputed {{COST_ROWS}} cost rows. Unverifiable cells are blank and all conflicts/open checks are published on the Flagged for Review page with direct official links. Needs review is a status, not a failure or a hidden assumption.",
        "sources": ["B01", "B04", "B05", "B22", "B31", "B33", "B34"],
    },
]

QUESTIONS = [
    {
        "id": "Q01", "question": "What is the legal and economic origin of every CNY in the account?",
        "known": "PRC law taxes enumerated categories including wages, services, business, interest, dividends, rent, property transfer and other income at different rules.",
        "missing": "Your contracts, statements, sale records, gift/inheritance documents and source-of-funds chronology.",
        "why": "The origin decides whether the documented-income, emigrant/inheritance, or another approval route fits, and whether PRC tax was due.",
        "discover": "Download all account statements; assemble employment contracts, payslips, invoices, sale agreements, gift or inheritance papers; ask the bank which source documents it will accept in writing.",
        "user_value": None, "sources": ["B08", "B13", "B14", "B20"],
    },
    {
        "id": "Q02", "question": "Was all PRC tax on the underlying income or asset paid, and is there an official tax certificate?",
        "known": "SAFE's documented-income rule requires source materials including tax documents; property-transfer guides require a tax certificate or tax-payment proof; the tax authority issues a completion certificate and late tax carries a daily surcharge.",
        "missing": "Your 完税证明 / tax certificate and whether any amount is overdue.",
        "why": "Without tax proof a bank may refuse FX purchase; unpaid tax can grow through surcharge and enforcement.",
        "discover": "Request official tax records and a 完税证明 from the competent tax bureau; reconcile them to the source documents; ask a PRC tax professional to certify whether anything remains due.",
        "user_value": None, "sources": ["B10", "B14", "B20", "B32"],
    },
    {
        "id": "Q03", "question": "Are you a PRC tax resident, a foreign individual in China, or a foreign permanent-residence ID holder?",
        "known": "The statute defines a domestic individual to include qualifying foreigners resident for at least {{RESIDENT_DAYS}} days; PRC tax residence uses a {{RESIDENT_DAYS}}-day rule; only foreign permanent-residence ID holders are stated to use the annual purchase convenience quota in the SAFE FAQ.",
        "missing": "Passport, visas, residence records, days present, and permanent-residence card status.",
        "why": "This determines whether the US${{QUOTA}} annual quota, documented-income route, or another route is even available.",
        "discover": "Build a day-count calendar from entry/exit stamps; keep passport, residence permit and permanent-residence card copies; ask the bank to state your classification in writing.",
        "user_value": None, "sources": ["B08", "B09", "B11", "B20"],
    },
    {
        "id": "Q04", "question": "Did you acquire foreign citizenship/permanent residence and cancel a PRC hukou before the funds arose?",
        "known": "Emigrant property transfer is for lawful property owned before the immigration status; the guide lists hukou cancellation and foreign settlement evidence and assigns approval to the original-hukou SAFE office.",
        "missing": "Naturalisation/permanent-residence dates, hukou cancellation certificate and property acquisition dates.",
        "why": "These facts decide whether a one-off emigrant property transfer approval is possible.",
        "discover": "Obtain certified immigration-status and hukou-cancellation documents and a dated property schedule; ask the original-hukou SAFE office whether it will accept an application.",
        "user_value": None, "sources": ["B12", "B13", "B14", "B20"],
    },
    {
        "id": "Q05", "question": "Is any part an inheritance from a person whose hukou was in mainland China?",
        "known": "Inheritance transfer is a distinct route assigned to the deceased's hukou SAFE office; it requires inheritance, title and tax documents and must go to the heir's own overseas account.",
        "missing": "Death certificate, relationship/inheritance proof, title documents, tax certificate and the deceased's hukou location.",
        "why": "Using the ordinary income route for inherited capital would misstate the transaction.",
        "discover": "Collect notarised or officially accepted inheritance and title documents; ask the deceased's hukou SAFE office for its current checklist.",
        "user_value": None, "sources": ["B12", "B13", "B32"],
    },
    {
        "id": "Q06", "question": "Which PRC bank holds the CNY, and exactly whose U.S. account will receive the USD?",
        "known": "The property-transfer rule requires remittance to the applicant's own overseas account; Wise says from-CNY transfers can go only to another account the sender owns; SAFE rules distinguish own-account and cross-border transfers.",
        "missing": "Bank name, branch, account title, your U.S. receiving bank and account ownership evidence.",
        "why": "A third-party recipient, mismatched name or unsupported corridor can stop the transfer or trigger compliance review.",
        "discover": "Get a bank letter with your exact account title and available services; open or confirm a U.S. account in the same name; ask the PRC bank to confirm the receiving-account details it will accept.",
        "user_value": None, "sources": ["B05", "B08", "B13", "B28"],
    },
    {
        "id": "Q07", "question": "What is the exact amount, currency and desired timing?",
        "known": "This guide prices every US${{STEP}} step from the first to the last tier; published rate boards are dated and for reference only.",
        "missing": "Your actual balance, whether interest accrues, and whether you need one payment or staged payments.",
        "why": "Wire caps, annual quota/cash limits, FX movements and future tax years all depend on amount and timing.",
        "discover": "Obtain an official balance letter; decide the target amount in USD; ask the bank whether a single or several remittances are possible and what rate applies on each date.",
        "user_value": None, "sources": ["B01", "B02", "B08", "B14", "B17"],
    },
    {
        "id": "Q08", "question": "Will the bank actually approve this source of funds and what exact rate/fees will it quote?",
        "known": "Banks must reasonably review authenticity; BOC's published fee schedule allows separate agreements, promotions and local differences; its linked promotion page currently returns a 404; HSBC's tariff excludes other institutions' charges and taxes.",
        "missing": "A written bank eligibility decision, executable rate, local fee schedule, correspondent/receiving fees and any monthly account fee.",
        "why": "A published tariff is not approval, a quote, or an all-in cost.",
        "discover": "Ask the branch for a written checklist, an executable rate and a full fee breakdown including intermediary and receiving charges; retain the reply. Do not rely on the web board alone.",
        "user_value": None, "sources": ["B01", "B02", "B03", "B04", "B09", "B31"],
    },
    {
        "id": "Q09", "question": "What prior U.S. foreign-account, asset and gift reports have been filed?",
        "known": "FBAR is required when foreign-account aggregate value exceeds US${{FBAR}} at any time; Form {{FORM8938}} thresholds depend on residence and filing status; Form {{FORM3520}} applies to large foreign gifts/bequests; Streamlined procedures require non-willful certification.",
        "missing": "Prior-year returns, FinCEN filings, account maxima, gift documents and whether the IRS has contacted you.",
        "why": "A low-tax transfer can become expensive if past reporting is missing; penalties are separate from conversion.",
        "discover": "Obtain IRS account transcripts and prior returns; list each foreign account and its annual maximum; give the filing history to a U.S. tax professional before choosing a correction route.",
        "user_value": None, "sources": ["B21", "B23", "B24", "B28", "B30"],
    },
    {
        "id": "Q10", "question": "When and at what CNY/USD rate was the CNY acquired?",
        "known": "The IRS says a spot rate is generally used when an item is received/paid/accrued, has no official exchange rate, and accepts a consistently used posted rate; a personal currency gain above US${{DE_MINIMIS}} is not excluded by §{{SECTION988}}.",
        "missing": "Acquisition dates, exchange rates, basis records and whether the later disposition is a personal transaction.",
        "why": "Currency movement between acquisition and disposition can create U.S. ordinary gain or loss even though principal is not income.",
        "discover": "Reconstruct each deposit's date and CNY/USD rate from bank and payroll records; choose a consistent posted rate with a tax professional; compute potential gain before transferring.",
        "user_value": None, "sources": ["B06", "B07", "B27"],
    },
    {
        "id": "Q11", "question": "Do FEIE, foreign tax credit or a treaty apply to the underlying income?",
        "known": "The {{TAX_YEAR}} FEIE exclusion cap is {{FEIE2026}} and the next-year cap is {{FEIE2027}}; the FTC is limited to qualifying tax on the same income and cannot be claimed on excluded income; treaty effects require the specific treaty text.",
        "missing": "Tax home, abode, bona fide residence/physical presence, foreign tax paid, and treaty residence.",
        "why": "Exclusion and credit rules interact; neither changes the principal, and a wrong election can create double work or penalties.",
        "discover": "Give a U.S. tax professional your travel calendar, foreign tax receipts and income character; read the current treaty publication before claiming a treaty position.",
        "user_value": None, "sources": ["B20", "B25", "B26", "B29", "B34"],
    },
    {
        "id": "Q12", "question": "Is any part a gift or bequest from a foreign person?",
        "known": "A U.S. person reports gifts/bequests from a nonresident alien or foreign estate above {{GIFT_NRA}} and from foreign entities above {{GIFT_ENTITY}} in {{READ}}; related-party gifts are aggregated.",
        "missing": "Donor identity, donor status, relationship, gift documents and aggregation across related parties.",
        "why": "A mistaken gift label affects both Form {{FORM3520}} reporting and PRC source-of-funds review.",
        "discover": "Collect signed gift statements and donor-status evidence; aggregate all related-party gifts for the tax year; ask a U.S. tax professional to review Form {{FORM3520}}.",
        "user_value": None, "sources": ["B13", "B24", "B26"],
    },
    {
        "id": "Q13", "question": "Will any cash or monetary instruments be physically carried?",
        "known": "PRC rules allow up to US${{NO_PERMIT}} without a carry permit, require a bank permit above that up to US${{BANK_PERMIT}}, and generally prohibit more except special SAFE permits; U.S. rules require reporting more than US${{CMIR}} at one time.",
        "missing": "Travel plan, denominations, permits, security arrangements and group totals.",
        "why": "Physical carrying adds permit, reporting, security and deposit/conversion unknowns; families/groups are aggregated for CBP.",
        "discover": "Ask the bank and SAFE what permit is required; obtain the permit; keep purchase and withdrawal memos; file the U.S. report when the collective amount exceeds the threshold.",
        "user_value": None, "sources": ["B08", "B17", "B28"],
    },
    {
        "id": "Q14", "question": "Has the bank/SAFE confirmed a direct cross-border RMB route in writing?",
        "known": "PBOC supports banks handling current-account cross-border RMB settlement for individuals, including lawful salary, under bank due-diligence and AML duties, but publishes no personal fee, rate or general capital/savings route here.",
        "missing": "Written legal basis, permitted purpose, tariff, limit, exchange rate and receiving-bank terms.",
        "why": "A generic policy supporting current-account settlement does not establish a lawful route for moving an accumulated capital balance.",
        "discover": "Ask the bank for the exact rule, permitted transaction category, written approval and full price; if it cannot provide them, leave the route unused and blank.",
        "user_value": None, "sources": ["B09", "B10", "B33"],
    },
]

PENALTY = [
    {
        "id": "P01", "layer": "Separate conversion tax",
        "what": "The reviewed PRC FX statutes impose authenticity, quota and approval rules; none of the reviewed pages identifies a standalone tax on the act of converting CNY into USD. This is not a tax-free certification for the underlying funds.",
        "published": "Not identified", "unknown": None, "sources": ["B08", "B09", "B19", "B20"], "flags": ["F-02", "F-13"],
    },
    {
        "id": "P02", "layer": "PRC tax on the underlying income or asset",
        "what": "Tax follows the income type and residence: comprehensive income {{COMP_MIN}}–{{COMP_MAX}}, business income {{BUS_MIN}}–{{BUS_MAX}}, and a {{FLAT}} rate for interest/dividends/property/other enumerated income. Hukou cancellation requires tax clearance; late tax accrues a daily {{LATE_RATE}} surcharge and evasion can attract a {{EVASION_MIN}}–{{EVASION_MAX}}× fine.",
        "published": "Published rates and enforcement ranges", "unknown": None, "sources": ["B13", "B14", "B20", "B32"], "flags": ["F-02", "F-13"],
    },
    {
        "id": "P03", "layer": "Documentary gate",
        "what": "The practical barrier is often proof, not price: lawful-source materials, a tax certificate, ID and, for property transfers, immigration/inheritance/title documents. Banks must reasonably review authenticity, and SAFE may refuse property with unproven lawful source.",
        "published": "Document lists and review duty", "unknown": None, "sources": ["B08", "B09", "B10", "B12", "B13", "B14"], "flags": ["F-02", "F-20"],
    },
    {
        "id": "P04", "layer": "Exchange spread",
        "what": "Buying USD at a bank's sell price and valuing it at the midpoint of that bank's published buy/sell prices produces a measurable board spread: {{BOC_SPREAD_PCT}} for BOC and {{HSBC_SPREAD_PCT}} for HSBC. The boards themselves are reference-only.",
        "published": "Board-derived illustration", "unknown": None, "sources": ["B01", "B02", "B07"], "flags": ["F-04", "F-05"],
    },
    {
        "id": "P05", "layer": "Sender, cable, card and cash fees",
        "what": "BOC publishes {{BOC_RATE}} (min {{BOC_MIN}}, max {{BOC_MAX}}) plus a {{BOC_CABLE}} cable charge for non-HK/Macau/Taiwan e-banking wires. HSBC publishes a comparable capped TT fee, free notes withdrawal, overseas-ATM charges and Global Transfer charges by segment.",
        "published": "Published tariff components", "unknown": None, "sources": ["B03", "B04", "B16"], "flags": ["F-06", "F-07", "F-23"],
    },
    {
        "id": "P06", "layer": "Intermediary and receiving charges",
        "what": "HSBC's tariff states that its charges exclude other institutions' charges and government taxes; BOC's schedule points to local/agreement differences. Pay Exact is an optional published charge, not a cap on shortfalls. No receiving-bank fee was found.",
        "published": "Exclusion and optional charge", "unknown": None, "sources": ["B03", "B04"], "flags": ["F-01", "F-07"],
    },
    {
        "id": "P07", "layer": "PRC evasion, splitting and prohibited-channel fines",
        "what": "Evasion, fraudulent FX purchase, private/underground FX dealing and disguised capital transfers can attract a fine up to {{FINE}} of the amount, or from {{FINE}} up to an equal amount in serious cases, plus criminal liability. Splitting or borrowing quotas can trigger a watch list; crypto business is declared illegal.",
        "published": "Statutory ranges", "unknown": None, "sources": ["B09", "B15", "B18", "B32"], "flags": ["F-18", "F-21"],
    },
    {
        "id": "P08", "layer": "U.S. §{{SECTION988}} currency gain",
        "what": "Disposition of nonfunctional currency is a §{{SECTION988}} transaction. An individual's personal-transaction gain is not recognized only when the otherwise recognized gain does not exceed {{DE_MINIMIS}}; larger gains are ordinary income/loss. Acquisition basis and the ordinary tax rate are personal facts.",
        "published": "De-minimis threshold and character", "unknown": None, "sources": ["B06", "B07", "B27"], "flags": ["F-14", "F-19"],
    },
    {
        "id": "P09", "layer": "U.S. information-reporting penalties",
        "what": "FBAR uses a {{FBAR}} aggregate-account threshold; Form {{FORM8938}} thresholds depend on residence/status; Form {{FORM3520}} applies to large foreign gifts; CBP uses a {{CMIR}} currency-reporting threshold. These are reporting duties, not taxes on the transfer. The eCFR table gives maximum non-willful and willful penalties but its amendment history ends in {{ECFR_YEAR}}.",
        "published": "Thresholds and inflation-adjusted maxima", "unknown": None, "sources": ["B21", "B22", "B23", "B24", "B28", "B30"], "flags": ["F-15", "F-17"],
    },
    {
        "id": "P10", "layer": "FEIE, FTC and treaty interaction",
        "what": "The {{TAX_YEAR}} FEIE cap is {{FEIE2026}} and the next-year cap is {{FEIE2027}}. A foreign tax credit uses qualifying tax on the same income, cannot be claimed on excluded income, and may be limited by a treaty-reduced rate. Treaty text was not read line by line here.",
        "published": "Caps and interaction rules", "unknown": None, "sources": ["B25", "B26", "B29", "B34"], "flags": ["F-16"],
    },
    {
        "id": "P11", "layer": "Cash and ATM physical constraints",
        "what": "Mainland cards used abroad are capped at {{ATM_YEAR}} per person per calendar year and {{ATM_DAY}} per card per day; carrying foreign notes above {{NO_PERMIT}} needs a bank permit and above {{BANK_PERMIT}} is generally prohibited. Foreign ATM-owner fees, network rates, cash deposit/conversion and security costs are not published.",
        "published": "Caps and issuer ATM fee", "unknown": None, "sources": ["B04", "B16", "B17", "B28"], "flags": ["F-10", "F-11"],
    },
    {
        "id": "P12", "layer": "Time and future-rate exposure",
        "what": "Quota, ATM and cash routes can require multiple calendar years; the property-transfer approval has published acceptance and decision working-day limits. Future bank rates, tax years and approval outcomes are not published, so any multi-year all-in estimate would be invented.",
        "published": "Published time/count limits", "unknown": None, "sources": ["B01", "B06", "B12", "B14", "B16", "B17"], "flags": ["F-01", "F-04", "F-19"],
    },
]

FLAGS = [
    {"id": "F-01", "kind": "blank", "affected": "All-in total for every route and tier", "why": "No executable rate, correspondent/receiving fee, personal tax basis or future rate was published.", "discover": "Request a written executable quote and full fee breakdown from both banks; document tax basis; leave blank until confirmed.", "sources": ["B01", "B02", "B03", "B04", "B07", "B27"]},
    {"id": "F-02", "kind": "blank", "affected": "Source, tax-paid status and 完税证明 for this balance", "why": "No account documents were supplied; the official rules require lawful-source and tax evidence.", "discover": "Obtain statements, contracts and an official tax certificate; ask the bank for its written checklist.", "sources": ["B08", "B10", "B14", "B20", "B32"]},
    {"id": "F-03", "kind": "blank", "affected": "Personal immigration/residence/PR-card/hukou status", "why": "Eligibility for quota, documented-income, emigrant and inheritance routes depends on private status facts.", "discover": "Assemble passport, day count, residence permit, PR card and hukou-cancellation evidence; ask the bank/SAFE to classify in writing.", "sources": ["B08", "B09", "B11", "B12", "B14", "B20"]},
    {"id": "F-04", "kind": "irregularity", "affected": "BOC board at {{BOC_TIME}} versus an earlier same-day reading", "why": "The bank board changes intraday and states it is for reference only.", "discover": "Capture the exact board timestamp with any quote; use the bank's actual transaction rate for execution.", "sources": ["B01"]},
    {"id": "F-05", "kind": "irregularity", "affected": "HSBC board last updated {{HSBC_DATE}}", "why": "It is dated before the BOC board and is subject to change without notice.", "discover": "Ask HSBC for a same-day executable rate before comparing routes.", "sources": ["B02"]},
    {"id": "F-06", "kind": "irregularity", "affected": "HSBC PDF has two effective-date headers", "why": "The cover says one date while embedded table headers say another; the applicable version should be confirmed with the bank.", "discover": "Ask HSBC to confirm the effective tariff for your account and retain the written answer.", "sources": ["B04"]},
    {"id": "F-07", "kind": "blank", "affected": "BOC local/promotional discounts", "why": "The official fee schedule links to a promotion page that now returns a 404; local/agreement differences are acknowledged but not published.", "discover": "Ask the branch for its current local price list and any written discount; leave blank until supplied.", "sources": ["B03", "B31"]},
    {"id": "F-08", "kind": "blank", "affected": "Wise exact fee, conversion rate and personal overall limit", "why": "The provider says to set up a transfer to see exact fees and computes an overall limit from private income/tax records.", "discover": "Use the official setup screen without funding; capture the quoted fee/rate and the assigned limit; do not infer them here.", "sources": ["B05", "B10"]},
    {"id": "F-09", "kind": "blank", "affected": "Bank FX rate and wire fee for emigrant/inheritance transfers", "why": "The SAFE guide publishes no administrative fee but not the bank's conversion rate or remittance charges.", "discover": "After approval, ask the designated bank for a written rate and full fee schedule.", "sources": ["B12", "B13", "B14"]},
    {"id": "F-10", "kind": "blank", "affected": "Foreign ATM-owner fee, network FX rate, cash deposit/conversion cost", "why": "Only the PRC cap and one issuer's ATM fee are published.", "discover": "Ask the card issuer and foreign ATM owner for written fees/rate; keep withdrawal receipts.", "sources": ["B04", "B16"]},
    {"id": "F-11", "kind": "blank", "affected": "Cash-permit fee, security, insurance and U.S. deposit/conversion cost", "why": "The official cash rules publish limits and permits, not these costs.", "discover": "Ask the bank for permit charges and the U.S. bank for cash-deposit terms; do not carry unverified amounts.", "sources": ["B17", "B28"]},
    {"id": "F-12", "kind": "blank", "affected": "Direct cross-border RMB route for an accumulated balance", "why": "PBOC supports current-account RMB settlement but does not publish a general personal savings/capital route, fee, limit or rate.", "discover": "Request written legal basis, purpose, tariff, limit and rate from the bank and SAFE; leave blank otherwise.", "sources": ["B09", "B10", "B33"]},
    {"id": "F-13", "kind": "blank", "affected": "Personal PRC income-tax bill and overdue-tax exposure", "why": "Residence, income type, deductions and payment history are unknown.", "discover": "Give source documents and tax records to a qualified PRC tax professional; obtain written clearance where needed.", "sources": ["B20", "B32"]},
    {"id": "F-14", "kind": "blank", "affected": "Acquisition basis, personal-transaction status and U.S. ordinary tax rate", "why": "§{{SECTION988}} publishes character and a {{DE_MINIMIS}} threshold, not your basis or bracket.", "discover": "Reconstruct acquisition dates/rates and provide them with your U.S. return data to a tax professional.", "sources": ["B06", "B07", "B27"]},
    {"id": "F-15", "kind": "blank", "affected": "Prior FBAR, Form {{FORM8938}}, Form {{FORM3520}} and CBP filing history", "why": "No private filing history was provided; penalties depend on facts and willfulness.", "discover": "Obtain IRS transcripts and prior filings; list every foreign account and annual maximum; seek professional correction advice.", "sources": ["B21", "B23", "B24", "B28", "B30"]},
    {"id": "F-16", "kind": "blank", "affected": "FEIE/FTC eligibility and treaty position", "why": "Tax home, abode, presence tests, foreign tax paid and treaty residence are private; the treaty text was not read line by line here.", "discover": "Provide travel and tax records to a U.S. tax professional and consult the current treaty publication before claiming relief.", "sources": ["B25", "B26", "B29", "B34"]},
    {"id": "F-17", "kind": "irregularity", "affected": "eCFR penalty table amendment history", "why": "The display is current but the quoted amendment history ends with the {{ECFR_YEAR}} Federal Register adjustment; a newer inflation amount was not seen on this page.", "discover": "Check the annual FinCEN inflation-adjustment notice before quoting a penalty maximum.", "sources": ["B21", "B22"]},
    {"id": "F-18", "kind": "conflict", "affected": "Historical staged-emigrant wording", "why": "PBOC {{PBOC_YEAR}} Article {{PBOC_ARTICLE}} says staged remittance, but SAFE {{SAFE_YEAR}} §VI abolished the staged requirement and HQ filing; older repository lines repeat the superseded wording.", "discover": "Use the later SAFE rule; ask the approving SAFE office for its current checklist; correct only in the owning session's files.", "sources": ["B12", "B13"]},
    {"id": "F-19", "kind": "irregularity", "affected": "Fed H.10 latest column versus same-day bank boards", "why": "The weekly release's latest daily rate is dated before the BOC board; it is not a same-day executable rate.", "discover": "Use a consistently applied posted rate for tax translation and record its date; do not mix it silently with a bank quote.", "sources": ["B01", "B06", "B07"]},
    {"id": "F-20", "kind": "blank", "affected": "Bank authenticity-review outcome", "why": "The law imposes a review duty; no bank has been asked about this balance.", "discover": "Submit the document pack and obtain a written acceptance or a written list of deficiencies.", "sources": ["B08", "B09", "B10"]},
    {"id": "F-21", "kind": "blank", "affected": "Numeric penalty for a proposed crypto/stablecoin conversion", "why": "The official notice declares the activity illegal but refers to other rules for penalties.", "discover": "Do not use the route; consult a PRC lawyer for the current enforcement provision if an exposure assessment is needed.", "sources": ["B18"]},
    {"id": "F-22", "kind": "blank", "affected": "U.S.-side Global Transfer availability and terms", "why": "The PRC tariff lists a same-name transfer service but the U.S. receiving entity's terms were not read here.", "discover": "Ask both HSBC entities to confirm corridor availability, account eligibility and charges in writing.", "sources": ["B04", "B05"]},
    {"id": "F-23", "kind": "blank", "affected": "HSBC Premier monthly service fee in an all-route comparison", "why": "The tariff publishes a monthly fee and balance/promotion criteria, but the per-transfer cost excludes it because personal segment and waiver status are unknown.", "discover": "Ask HSBC which segment applies and whether the monthly fee is waived; add it only after a written answer.", "sources": ["B04"]},
]

def _m(id, name, status, pricing, cost_model, short, best_for, pros, cons, steps, sources, flags):
    return {
        "id": id, "name": name, "status": status, "pricing": pricing,
        "cost_model": cost_model, "short": short, "best_for": best_for,
        "pros": pros, "cons": cons, "steps": steps, "sources": sources, "flags": flags,
    }

METHODS = [
    _m("R01", "BOC documented-income online FX purchase + one wire", "lawful · documentary", "complete", "boc_wire",
       "Convert lawful current-account RMB income at BOC and wire USD to your own U.S. account.",
       "Foreign individual with ID, transaction-amount source materials and a tax certificate.",
       ["BOC publishes both a USD board and an e-banking wire tariff.", "One outgoing wire is possible when the bank accepts the documents.", "Own-account remittance is the statutory property-transfer model and Wise's own-account rule is consistent."],
       ["The board is reference-only and changes intraday.", "The bank may refuse documents or apply local/agreement fees.", "Intermediary and receiving fees are unpublished; U.S. reporting and §{{SECTION988}} still apply."],
       ["Ask the PRC bank in writing whether it accepts your passport, lawful-source materials and tax certificate for the documented-income route; keep the answer.", "Review the live BOC board, then obtain an executable quote in online banking or at the branch. The web board says the actual transaction rate governs.", "Buy USD with that actual rate and retain the exchange memo and tax/source pack.", "Submit one cross-border telegraphic transfer to your own U.S. account; compare the bank's quote with BOC's published {{BOC_RATE}} fee, {{BOC_MIN}} minimum, {{BOC_MAX}} maximum and {{BOC_CABLE}} cable charge.", "Before execution, ask for correspondent, intermediary and receiving-bank fees in writing; the tariff excludes charges by other institutions.", "Record acquisition and disposal rates; have FBAR, Form {{FORM8938}}, §{{SECTION988}} and FTC/FEIE effects reviewed before filing."],
       ["B01", "B03", "B08", "B09", "B10", "B21", "B23", "B27", "B29", "B31"], ["F-01", "F-02", "F-04", "F-07", "F-14", "F-15", "F-20"]),
    _m("R02", "BOC own annual-convenience-quota purchase + wires", "conditional · own quota only", "complete", "boc_quota",
       "Use your own annual FX purchase convenience quota, then wire USD; larger amounts need later calendar years.",
       "A qualifying domestic individual or foreign permanent-residence ID card holder who needs a slow, quota-compliant route.",
       ["The annual quota and wire thresholds are published by SAFE.", "The BOC board and e-banking tariff allow a reproducible cost illustration.", "Using only your own quota does not involve borrowed quotas or a watch-list evasion."],
       ["A U.S. passport alone does not establish quota eligibility.", "Amounts above the quota require multiple calendar years and unknown future rates.", "Splitting or borrowing quotas is prohibited and can trigger the watch list."],
       ["Confirm with the bank, in writing, that you hold the foreign permanent-residence ID card or otherwise qualify for the annual convenience quota.", "Use no more than US${{QUOTA}} of your own quota per calendar year; do not borrow another person's quota.", "Obtain the actual bank transaction rate each time rather than relying on a historical board.", "Buy USD and wire from your own FX account to your own overseas account under the published wire rule.", "Repeat only in a later calendar year using your own quota; record each year's rate and documents.", "Keep the exchange memos and complete any FBAR/Form {{FORM8938}} filings triggered by the account balance."],
       ["B01", "B03", "B08", "B11", "B15", "B21", "B23"], ["F-01", "F-03", "F-04", "F-07", "F-15", "F-19"]),
    _m("R03", "BOC CNY→USD purchase and hold in a PRC FX savings account", "lawful · conversion only", "partial", "boc_hold",
       "Convert CNY to USD and deposit it in your own foreign-currency savings account in China; no money leaves China yet.",
       "Someone who needs to stop CNY exposure while documents for a later remittance are assembled.",
       ["SAFE expressly allows purchased FX to be deposited in the person's own FX savings account.", "No outgoing wire fee is incurred at this step.", "The published board still permits a spread illustration."],
       ["This is not repatriation; the funds remain a foreign financial account for U.S. reporting purposes.", "Future remittance rate and bank charges are unknown.", "The BOC board is reference-only."],
       ["Confirm the bank will open or credit your own FX savings account and accept the source/tax documents.", "Obtain an executable USD sell rate; the published board is only a reference.", "Buy USD and credit the USD to the same-name FX savings account; retain the memo.", "Do not treat the conversion as a transfer; continue to document the source and filing obligations.", "When ready to remit, return to a lawful wire/approval route and obtain fresh quotes."],
       ["B01", "B08", "B21", "B23"], ["F-01", "F-04", "F-15", "F-20"]),
    _m("R04", "BOC USD cash purchase + physical carry", "conditional · permits", "partial", "boc_cash",
       "Buy foreign notes at BOC and carry them abroad within the published permit limits.",
       "Small amounts where a lawful cash route is genuinely needed and all permits/reports can be obtained.",
       ["BOC publishes a cash sell price; foreign-currency cash withdrawal rules are published.", "Up to US${{NO_PERMIT}} per trip needs no carry permit; a bank permit covers the next band."],
       ["Cash withdrawal above the daily threshold requires advance SAFE reporting.", "Over US${{BANK_PERMIT}} is generally prohibited except special SAFE permits; CBP aggregates families/groups above US${{CMIR}}.", "Security, deposit, cash-conversion and permit fees are unpublished; repeated trips create future-rate and reporting exposure."],
       ["Ask the bank whether it has the notes and what cash sell rate applies; reserve large withdrawals if required.", "Buy the USD notes with your own funds and keep the purchase memo.", "If the amount is within US${{NO_PERMIT}}, no carry permit is needed; otherwise obtain a bank-issued or, in special cases, SAFE-issued permit before departure.", "Do not exceed the permit amount or validity; keep the permit for inspection.", "On U.S. entry, report collectively carried currency/monetary instruments above the CBP threshold.", "Deposit or convert the cash only after obtaining the receiving institution's written rate and fees."],
       ["B01", "B08", "B17", "B28"], ["F-01", "F-04", "F-11", "F-13", "F-15"]),
    _m("R05", "HSBC China outward telegraphic transfer (Premier/Advance)", "lawful · documentary", "complete", "hsbc_tt",
       "Convert CNY at HSBC China and send a USD telegraphic transfer to your own U.S. account.",
       "A customer with accepted documentation and a Premier/Advance account who wants a published tariff.",
       ["The HSBC board and current tariff are both published.", "The outward TT formula has a clear cap and cable charge.", "The bank's document-review duty is explicit."],
       ["The board is dated and reference-only; the PDF has two effective-date headers.", "Intermediary/receiving fees and taxes are excluded from the tariff.", "Private Banking, Premier Elite and local waivers change the fee; personal eligibility is unknown."],
       ["Ask HSBC China for its written source-of-funds checklist and confirmation that your account segment is Premier or Advance.", "Obtain a same-day executable USD sell rate; do not rely on the web board alone.", "Buy USD and submit the outward TT to your own U.S. account.", "Compare the quoted sender fee with the published {{HSBC_RATE}} formula, {{HSBC_MIN}} minimum, {{HSBC_MAX}} maximum and {{HSBC_CABLE}} cable charge.", "If full beneficiary credit is needed, ask about Pay Exact and the published {{PAY_EXACT}} charge; remember any shortfall can still be collected.", "Obtain written correspondent/receiving charges and keep records for U.S. reporting and currency-gain analysis."],
       ["B02", "B04", "B09", "B10", "B21", "B23", "B27"], ["F-01", "F-05", "F-06", "F-14", "F-15", "F-20", "F-23"]),
    _m("R06", "HSBC China outward telegraphic transfer (Private Banking individual)", "conditional · segment", "complete", "hsbc_pb_tt",
       "Same conversion and wire, using the tariff's free individual Private Banking TT pricing.",
       "A customer whom HSBC confirms is an individual Private Banking customer.",
       ["The tariff says outward TT issuance and cable are free for individual Private Banking customers.", "The published board still permits a spread illustration."],
       ["Private Banking eligibility and any separate account terms were not verified.", "The board is reference-only and the PDF has two date headers.", "Third-party charges and personal tax/reporting exposure remain blank."],
       ["Ask HSBC to confirm in writing that your account is an individual Private Banking account and that the free TT/cable tariff applies.", "Obtain a same-day executable USD sell rate and full source-of-funds approval.", "Buy USD and instruct the TT to your own U.S. account.", "Confirm that no separate cable or issuance charge will be debited; keep the tariff and written confirmation.", "Request all correspondent/receiving charges in writing and complete U.S. reporting/currency-gain checks."],
       ["B02", "B04", "B09", "B21", "B23", "B27"], ["F-01", "F-05", "F-06", "F-14", "F-15", "F-20"]),
    _m("R07", "HSBC same-name Global Transfer (Private Banking/Premier)", "conditional · own HSBC account", "complete", "hsbc_gt_free",
       "Convert CNY and use HSBC Global Transfer to your own HSBC account abroad where the service is available.",
       "A customer with confirmed same-name HSBC accounts in both countries and a free-tariff segment.",
       ["The tariff publishes Global Transfer as free for Private Banking and Premier.", "A same-name transfer fits the own-account theme in the official rules.", "The board still lets the spread be illustrated."],
       ["U.S.-side availability and terms were not independently read here.", "The exchange spread remains; the board is reference-only.", "Premier monthly/waiver status and third-party charges are unknown."],
       ["Ask both HSBC entities in writing whether same-name Global Transfer to your U.S. HSBC account is available and which segment applies.", "Obtain an executable USD conversion rate and written source-of-funds approval.", "Buy USD, then initiate Global Transfer to the same-name account.", "Confirm the free transfer charge from the tariff; do not confuse the education-payment {{EDUCATION_USD}} charge with Global Transfer.", "Keep the exchange memo and written fee confirmations; complete U.S. reporting and §{{SECTION988}} checks."],
       ["B02", "B04", "B05", "B08", "B21", "B23", "B27"], ["F-01", "F-05", "F-06", "F-14", "F-15", "F-20", "F-22", "F-23"]),
    _m("R08", "HSBC same-name Global Transfer (Advance)", "conditional · own HSBC account", "complete", "hsbc_gt_advance",
       "Same route using the Advance segment's published actual Global Transfer charge.",
       "A confirmed Advance customer with same-name HSBC accounts in both countries.",
       ["The tariff publishes the Advance Global Transfer actual charge.", "The exchange spread and transfer fee can be computed from primary pages."],
       ["U.S.-side availability and terms were not independently read here.", "The board is reference-only; third-party charges remain unpublished.", "Advance eligibility has published restrictions and the account segment is a private fact."],
       ["Ask both HSBC entities in writing whether the corridor and your Advance account are eligible.", "Obtain an executable USD conversion rate and written source-of-funds approval.", "Buy USD, then initiate Global Transfer to your same-name U.S. HSBC account.", "Confirm the {{GT_ADVANCE}} actual charge and keep the published tariff page with your records.", "Obtain all other charges in writing and complete U.S. reporting/currency-gain checks."],
       ["B02", "B04", "B05", "B21", "B23", "B27"], ["F-01", "F-05", "F-06", "F-14", "F-15", "F-20", "F-22"]),
    _m("R09", "Wise from-CNY transfer to your own overseas account", "conditional · provider", "blank", "wise",
       "Use a licensed partner's from-CNY product, subject to tax-record verification and an overall limit.",
       "A non-mainland individual with recent official PRC tax records and an account in the same name.",
       ["Wise publishes eligibility, own-account restrictions and per-transfer caps.", "The product uses a PBOC-regulated licensed partner and provides bank-app/Alipay payment routes."],
       ["The exact fee, conversion rate and personal overall limit are not published on the help page.", "Overall limit depends on income and tax paid; this is not a regulator's eligibility guarantee.", "Mainland Chinese nationals are not eligible under the stated rule."],
       ["Confirm in the official product that you are not mainland Chinese, worked in China and have a tax record covering the required recent period.", "Complete first-time verification and upload the official tax record; do not fund before seeing the assigned limit.", "Choose bank-app or Alipay payment and observe the applicable published per-transfer cap.", "Set up the transfer to your own overseas account and capture the exact fee, conversion rate and delivery estimate on screen.", "Keep the quote, tax record and transfer receipt; compare with a bank wire before funding.", "Complete U.S. reporting and currency-gain checks with the documented dates and rates."],
       ["B05", "B08", "B10", "B21", "B23", "B27"], ["F-01", "F-02", "F-03", "F-08", "F-14", "F-15"]),
    _m("R10", "SAFE emigrant property transfer approval", "conditional · approval", "blank", "emigrant",
       "One-off approval to convert and remit lawful property owned before emigration, after hukou cancellation.",
       "A person with foreign citizenship/permanent residence and pre-status lawful property in mainland China.",
       ["The later SAFE rule abolished compulsory staging and HQ filing; the bank may remit once or in instalments within the approved amount.", "The service guide publishes no administrative fee and gives acceptance/decision timelines.", "The route is designed for a full property balance, not an annual quota."],
       ["Eligibility, hukou cancellation, source/title and tax documents are private and strict.", "The approval is single-use and requires an in-person visit in the published guide.", "Bank FX rate, wire fee and third-party charges are blank; future staged rates are unknown."],
       ["Confirm that you obtained the qualifying foreign status and that the property was owned before that status.", "Obtain hukou-cancellation, foreign-settlement, ID, income-source, property-title and tax-certificate documents.", "Apply to the original-hukou SAFE office; ask for its current checklist and whether the single-use approval covers the full amount.", "Wait for the published acceptance and decision periods; do not move funds before approval.", "Take the approval document to the designated bank; obtain a written executable rate and all bank/correspondent/receiving charges.", "Instruct remittance only to your own overseas account; the rule prohibits domestic FX cash withdrawal.", "Keep every document for PRC tax clearance and U.S. reporting/currency-gain analysis."],
       ["B09", "B12", "B13", "B14", "B20", "B21", "B23", "B27", "B32"], ["F-01", "F-02", "F-03", "F-09", "F-14", "F-15", "F-18"]),
    _m("R11", "SAFE inheritance property transfer approval", "conditional · approval", "blank", "inheritance",
       "Separate approval for a foreign citizen or qualifying resident to remit liquidated PRC inheritance.",
       "An heir with official inheritance, title and tax documents.",
       ["The rule defines inheritance transfer separately and abolished separate applications for different decedents and notarisation of listed documents.", "The bank must remit to the heir's own overseas account."],
       ["An inheritance-specific service guide, administrative fee, bank rate and wire charges were not read here.", "Eligibility and document acceptance are private; unproven lawful source is refused."],
       ["Obtain death, relationship/inheritance, property-title and tax-certificate documents.", "Apply to the SAFE office for the deceased's original hukou; ask for its current checklist.", "Do not treat inherited capital as salary or use another person's quota.", "After approval, obtain a written executable rate and all bank/correspondent/receiving charges.", "Instruct the bank to remit to your own overseas account; do not take domestic FX cash.", "Keep documents for U.S. gift/bequest reporting review and currency-basis analysis."],
       ["B09", "B12", "B13", "B20", "B24", "B27", "B32"], ["F-01", "F-02", "F-03", "F-09", "F-12", "F-14", "F-15"]),
    _m("R12", "Overseas ATM withdrawals with a mainland card", "conditional · cash ceiling", "partial", "atm",
       "Withdraw local currency abroad from a mainland card, within annual/daily SAFE ceilings, then deposit/convert it.",
       "Small amounts over time where card and foreign ATM fees/rates are obtained in writing.",
       ["SAFE publishes an annual per-person ceiling and a per-card daily ceiling; one HSBC tariff publishes overseas ATM charges.", "The arithmetic for withdrawals and years is reproducible from those caps."],
       ["The foreign ATM owner's fee, UnionPay/network conversion rate, cash deposit and security costs are blank.", "Exceeding the annual cap blocks overseas withdrawals in the current and second years.", "This is a slow cash route and creates CBP reporting exposure for large collective cash."],
       ["Ask the card issuer for its written overseas ATM fee, network FX rate and daily limit.", "Confirm the SAFE annual and per-card daily ceilings apply to your cards, including supplementary cards.", "Withdraw only within the published caps; keep each receipt and the exact conversion shown.", "Deposit/convert the cash at a U.S. institution only after obtaining its written rate and fees.", "If carrying or sending more than the CBP threshold at one time, file the required report.", "Record every date/rate for U.S. currency-gain and FBAR work."],
       ["B01", "B04", "B16", "B21", "B27", "B28"], ["F-01", "F-10", "F-11", "F-14", "F-15", "F-19"]),
    _m("R13", "Direct cross-border RMB settlement to an overseas account", "unverified · do not assume", "blank", "cross_rmb",
       "A possible bank current-account RMB settlement followed by offshore conversion; not verified for an accumulated savings/capital balance.",
       "Only if a bank and SAFE give a written lawful basis, permitted purpose, limit, rate and tariff.",
       ["PBOC supports current-account cross-border RMB settlement for individuals, including lawful salary, under bank due diligence and AML duties."],
       ["No general personal savings/capital route, fee, exchange rate, limit or receiving-bank term was published on that page.", "A generic policy statement is not approval for your balance."],
       ["Do not start with a transfer; first ask the bank for the exact rule and permitted transaction category in writing.", "Ask SAFE to confirm the classification of your balance if the bank cannot cite a rule.", "Request the full fee, rate, limit and receiving-bank terms in writing.", "If any of those are missing, leave every cost cell blank and use a verified route."],
       ["B09", "B10", "B33"], ["F-01", "F-12", "F-20"]),
    _m("R14", "HSBC USD cash purchase + physical carry", "conditional · permits", "partial", "hsbc_cash",
       "Buy foreign notes at HSBC China, where notes withdrawal is published as free, and carry them under the permit rules.",
       "Small amounts where HSBC has notes and all PRC/U.S. permit and reporting requirements are met.",
       ["HSBC publishes a cash sell/buy board and says foreign-currency notes withdrawal over the counter is free.", "The PRC and U.S. cash limits/reporting rules are published."],
       ["The cash buy/sell spread is larger than the TT spread; the board is reference-only and dated.", "Security, deposit, cash-conversion and permit fees are blank.", "Cash withdrawal and carry permits have advance-notice and amount limits."],
       ["Ask the branch whether it has USD notes, the advance-notice requirement and the actual cash sell rate.", "Buy the notes and keep the purchase and withdrawal memos; confirm the free notes-withdrawal tariff applies.", "Observe the PRC carry-permit rules and the permit validity period.", "Do not exceed the bank/SAFE permit limits; retain the documents for inspection.", "Report collectively carried currency/monetary instruments above the CBP threshold on U.S. entry.", "Obtain written U.S. deposit/conversion terms before depositing."],
       ["B02", "B04", "B08", "B17", "B28"], ["F-01", "F-05", "F-06", "F-11", "F-13", "F-15"]),
    _m("U01", "Quota splitting or borrowing another person's quota", "unlawful", "not-priced", "unlawful",
       "Prohibited workaround using multiple people's quotas to evade quota/authenticity management.",
       "Not a route; listed so the penalty is explicit.",
       ["None; it is prohibited."],
       ["SAFE says individuals must not use splitting to evade quota/authenticity management; borrowing quotas can place a person on the watch list for the listing year and the following two years.", "Documentary checks are stricter during the watch period."],
       ["Do not split the transfer or use another person's quota.", "If offered this route, stop and ask the bank for the lawful documented-income or approval route.", "Give the written offer and your documents to a qualified PRC adviser."],
       ["B08", "B11", "B15"], ["F-18", "F-21"]),
    _m("U02", "Underground swap / private FX dealing", "unlawful", "not-priced", "unlawful",
       "Exchanging CNY for offshore USD through an unlicensed broker or private counterparty.",
       "Not a route; listed so the penalty is explicit.",
       ["None; the activity is prohibited."],
       ["Private, disguised or brokered FX dealing can attract a fine up to {{FINE}} of the amount, or from {{FINE}} up to an equal amount in serious cases, plus confiscation and criminal liability.", "The quoted bank cannot verify the source or rate."],
       ["Do not send funds to an underground counterparty.", "Ask the licensed bank for the written documentary route instead.", "If funds were already sent, consult a PRC lawyer; do not attempt a second transfer to 'fix' it."],
       ["B09", "B18"], ["F-21"]),
    _m("U03", "Crypto / stablecoin conversion", "unlawful", "not-priced", "unlawful",
       "Converting CNY into virtual currency or an RMB-linked stablecoin and moving value offshore.",
       "Not a route; listed so the legal status is explicit.",
       ["None; the activity is prohibited."],
       ["The official notice says fiat-to-virtual-currency exchange and related virtual-currency business are illegal financial activities, strictly prohibited and subject to penalties under other rules; RMB-linked stablecoin issuance is restricted.", "Investment losses from covered conduct are borne by the investor."],
       ["Do not buy virtual currency or use a stablecoin channel for this balance.", "Ask a licensed bank for a written lawful route.", "If an offshore platform offers the service, keep the solicitation and consult a PRC lawyer; no execution steps are provided."],
       ["B09", "B18"], ["F-21"]),
    _m("U04", "False trade/current-transaction label or disguised capital transfer", "unlawful", "not-priced", "unlawful",
       "Using fake invoices or a false payment purpose to buy FX or move capital abroad.",
       "Not a route; listed so the penalty is explicit.",
       ["None; the activity is prohibited."],
       ["Fraudulent FX purchase and evasion/套汇 carry fines, mandatory reversal and possible criminal liability; banks must reasonably review authenticity.", "Mislabelling the source can also corrupt tax records."],
       ["Do not create or sign a false invoice, contract or payment purpose.", "Give the true source documents to the bank and ask which lawful route fits.", "If a prior filing was false, consult PRC and U.S. tax professionals before correcting it."],
       ["B09", "B19", "B20", "B32"], ["F-02", "F-13", "F-21"]),
    _m("U05", "Carrying cash above permit limits or repeated trips to evade", "unlawful", "not-priced", "unlawful",
       "Exceeding the foreign-cash permit rules or structuring trips to avoid them.",
       "Not a route; listed so the penalty is explicit.",
       ["None; the activity is prohibited."],
       ["Carrying FX in violation of the rules can attract a warning and a fine up to {{CASH_FINE}} of the amount; U.S. failure to report more than {{CMIR}} risks seizure and penalties.", "Families/groups are aggregated for U.S. reporting."],
       ["Do not exceed a permit or its validity period and do not structure trips around the thresholds.", "Obtain the proper bank/SAFE permit for a lawful amount, or use a verified wire route.", "File the U.S. currency report whenever the collective amount requires it."],
       ["B09", "B17", "B28"], ["F-11"]),
    _m("U06", "Third-party or straw-man account channel", "unlawful", "not-priced", "unlawful",
       "Sending CNY through someone else's account or to a recipient that is not your own to bypass review.",
       "Not a route; listed so the penalty is explicit.",
       ["None; the activity conflicts with own-account and authenticity rules."],
       ["Property transfers must go to the applicant's own overseas account; Wise permits only own-account from-CNY transfers; banks review authenticity and quota splitting is prohibited.", "A mismatched name can cause refusal and a compliance report."],
       ["Do not send from or to a third party's account to bypass review.", "Open or confirm an account in your own name and use a verified route.", "If a third party already holds funds, get legal advice and a written source trail before any correction."],
       ["B05", "B08", "B09", "B13", "B15"], ["F-20", "F-21"]),
]

# Placeholders are resolved by build.py from source figures and model outputs.
PLACEHOLDERS = {
    "READ": READ,
    "SOURCE_COUNT": len(SRC),
    "RESIDENT_DAYS": fmt(n("B20", "resident_days"), ".0f"),
    "QUOTA": fmt(n("B08", "annual_quota_usd"), ".0f"),
    "STEP": "10,000",
    "FBAR": fmt(n("B21", "fbar_threshold_usd"), ".0f"),
    "FORM8938": "8938",
    "FORM3520": "3520",
    "FORM1116": "1116",
    "FORM2555": "2555",
    "DE_MINIMIS": usd(n("B27", "personal_de_minimis_usd")),
    "SECTION988": fmt(n("B27", "section"), ".0f"),
    "TAX_YEAR": "2026",
    "FEIE2026": usd(n("B25", "feie_2026_usd")),
    "FEIE2027": usd(n("B26", "feie_2027_usd")),
    "GIFT_NRA": usd(n("B24", "gift_nra_usd")),
    "GIFT_ENTITY": usd(n("B24", "gift_entity_2026_usd")),
    "NO_PERMIT": fmt(n("B17", "no_permit_usd"), ".0f"),
    "BANK_PERMIT": fmt(n("B17", "bank_permit_upper_usd"), ".0f"),
    "CMIR": fmt(n("B28", "cmir_threshold_usd"), ".0f"),
    "COMP_MIN": pct(n("B20", "comprehensive_min_pct")),
    "COMP_MAX": pct(n("B20", "comprehensive_max_pct")),
    "BUS_MIN": pct(n("B20", "business_min_pct")),
    "BUS_MAX": pct(n("B20", "business_max_pct")),
    "FLAT": pct(n("B20", "flat_pct")),
    "LATE_RATE": pct(n("B32", "late_daily_rate") * n("B01", "per")),
    "EVASION_MIN": fmt(n("B32", "evasion_fine_min_multiple"), ".1f"),
    "EVASION_MAX": fmt(n("B32", "evasion_fine_max_multiple"), ".1f"),
    "BOC_RATE": pct(n("B03", "boc_tt_rate") * n("B01", "per")),
    "BOC_MIN": cny(n("B03", "boc_tt_min_cny")),
    "BOC_MAX": cny(n("B03", "boc_tt_max_cny")),
    "BOC_CABLE": cny(n("B03", "boc_cable_other_cny")),
    "HSBC_RATE": pct(n("B04", "hsbc_tt_rate") * n("B01", "per")),
    "HSBC_MIN": cny(n("B04", "hsbc_tt_min_cny")),
    "HSBC_MAX": cny(n("B04", "hsbc_tt_max_cny")),
    "HSBC_CABLE": cny(n("B04", "hsbc_cable_cny")),
    "PAY_EXACT": cny(n("B04", "hsbc_pay_exact_cny")),
    "GT_ADVANCE": usd(n("B04", "hsbc_gt_advance_usd")),
    "EDUCATION_USD": usd(n("B04", "hsbc_education_usd")),
    "FINE": pct(n("B09", "fine_standard_pct")),
    "CASH_FINE": pct(n("B09", "cash_violation_pct")),
    "ATM_YEAR": cny(n("B16", "atm_year_cny")),
    "ATM_DAY": cny(n("B16", "atm_day_cny")),
    "BOC_TIME": fig("B01", "published_time"),
    "HSBC_DATE": fig("B02", "board_date"),
    "ECFR_YEAR": str(fig("B22", "latest_fr_year")),
    "PBOC_YEAR": fig("B13", "notice_year"),
    "PBOC_ARTICLE": fig("B13", "article"),
    "SAFE_YEAR": fig("B12", "notice_year"),
}
