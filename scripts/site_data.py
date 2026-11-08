#!/usr/bin/env python3
"""Verified data for the unified China CNY->USD dashboard.

Every fact used in a computed cell is attached to a source entry below with
status "verified-this-session" (the page body was fetched and read during the
2026-11-08 session) or "cited-prior-session" (carried from an earlier session's
ledger and NOT re-fetched here). Values that no official source states are left
as None and rendered blank with an "unverified" marker.
"""

SESSION = "arena/21827432-china2"
SESSION_DATE = "2026-11-08"

# ---------------------------------------------------------------- constants
FX_RATE_DATE = "2026-11-06"
FX_CNY_PER_USD = 6.7168  # PBOC / CFETS central parity, 1 USD = 6.7168 CNY

# PRC Individual Income Tax, comprehensive income, resident, annual (RMB)
PRC_IIT_BRACKETS = [
    (36000, 0.03, 0),
    (144000, 0.10, 2520),
    (300000, 0.20, 16920),
    (420000, 0.25, 31920),
    (660000, 0.30, 52920),
    (960000, 0.35, 85920),
    (float("inf"), 0.45, 181920),
]
PRC_IIT_ANNUAL_DEDUCTION_CNY = 60000
PRC_FLAT_RATE = 0.20

# US federal income tax, single filer, 2026 (Rev. Proc. 2025-32, Table 3)
# Quick deductions so that tax = rate * taxable_income - quick_deduction.
# Derived from the cumulative "The Tax Is" column of S07 Table 3:
# cumulative tax at bracket floor = rate * floor - quick_deduction.
US_2026_SINGLE = [
    (12400, 0.10, 0.0),
    (50400, 0.12, 248.0),
    (105700, 0.22, 5288.0),
    (201775, 0.24, 7402.0),
    (256225, 0.32, 23544.0),
    (640600, 0.35, 31230.75),
    (float("inf"), 0.37, 44042.75),
]
US_2026_STANDARD_DEDUCTION_SINGLE = 16100
US_2026_FEIE = 132900
US_2026_GIFT_ANNUAL_EXCLUSION = 19000
US_2026_FOREIGN_GIFT_CORP_THRESHOLD = 20573

# verified PRC quantitative limits
PRC_QUOTA_USD_PER_YEAR = 50000          # 汇发[2007]1号 art. 2 (domestic individuals' purchases)
ATM_CNY_PER_YEAR = 100000               # 汇发[2017]29号 art. I
ATM_CNY_PER_CARD_PER_DAY = 10000        # 汇发[2017]29号 art. IV
WALKIN_USD_PER_DAY = 500                # 汇发[2007]1号 art. 13(2)
PORT_USD_PER_DAY = 1000                 # 汇发[2007]1号 art. 13(2)
EXCHANGE_MEMO_MONTHS = 24               # 汇发[2007]1号 art. 13(2)

ATM_USD_PER_YEAR = ATM_CNY_PER_YEAR / FX_CNY_PER_USD

TIERS = list(range(10000, 400001, 10000))  # 40 amounts: $10,000 .. $400,000

# ---------------------------------------------------------------- sources
# status: "V" = fetched and read in this session; "P" = cited by a prior session,
# linked for review, not re-fetched here.
S = {}


def src(i, authority, title, url, locator, evidence, status, note=""):
    S[i] = {
        "id": i, "authority": authority, "title": title, "url": url,
        "locator": locator, "evidence": evidence, "status": status, "note": note,
    }


src("S01", "People's Bank of China", "Administrative Rules on Individual's Foreign Exchange (PBOC Decree [2006] No.3, English)",
    "https://www.pbc.gov.cn/english/130733/2025080815071447034/index.html",
    "Arts. 7, 9, 13, 14, 15",
    "Art. 9 imposes an annual limit on an individual's FX sales and on domestic individuals' FX purchases. Art. 13: a non-domestic individual may convert legitimate RMB current-account income and remit abroad with valid ID and relevant documents. Art. 7 prohibits evading limits by splitting amounts or fabricating vouchers.",
    "V")

src("S02", "State Administration of Foreign Exchange (SAFE)", "Implementing Rules for the Administrative Rules on Individual's Foreign Exchange (汇发[2007]1号), 2024 republication with amendments",
    "https://www.safe.gov.cn/tianjin/2024/0430/2464.html",
    "Arts. 2, 11, 13, 14, 15, 20, 28, 30, 39",
    "Art. 2: annual total of USD 50,000 equivalent per person per year for individual FX sales and domestic individuals' FX purchases. Art. 13(1): non-domestic individual converting lawful current-account RMB income presents ID plus supporting documents including tax vouchers (含税务凭证). Art. 13(2): unused RMB from an original conversion may be re-converted against the original exchange memo, valid 24 months; same-day amounts of USD 500 or less (USD 1,000 or less at pre-departure port outlets) need only ID. Art. 15(1): a non-domestic individual remitting FX abroad from an FX savings account presents valid ID. Art. 20: emigration asset transfer and foreign inheritance transfer follow the separate 2004 rules. Footnote: Art. 39 was repealed by 汇发[2023]8号.",
    "V")

src("S03", "State Administration of Foreign Exchange (SAFE)", "Circular on Regulating Large-sum Overseas Cash Withdrawals with Bank Cards (汇发[2017]29号, English)",
    "https://www.safe.gov.cn/en/2017/1230/1397.html",
    "Arts. I, II, IV, VII",
    "Withdrawals with a domestic bank card shall not exceed the equivalent of RMB 100,000 in every civil year per individual across all cards; excess triggers a ban on overseas cash withdrawal in the current and the second year. Per-card daily ceiling adjusted from USD 1,000 to RMB 10,000; RMB cards remain at RMB 10,000 per card per day. Borrowing or lending cards to evade the rule is prohibited. Effective 1 January 2018.",
    "V")

src("S04", "State Taxation Administration (STA)", "Individual Income Tax Law of the PRC (English translation, 2018 amendment)",
    "https://www.chinatax.gov.cn/eng/c102962/c102967/c102997/c103004/c5245849/content.html",
    "Arts. 2, 3, 6, 16 and Schedules",
    "Art. 2 lists the nine taxable income categories; there is no category for 'converting your own money'. Art. 3: comprehensive income 3%-45%; business income 5%-35%; interest/dividends, asset leasing, asset transfer and incidental income a flat 20%. Art. 6: resident comprehensive income deducts RMB 60,000 per year; non-resident wages deduct RMB 5,000 per month. Art. 16: foreign-currency income is converted at the central parity rate. The rate schedules themselves are published as images on this page.",
    "V")

src("S05", "Shanghai Municipal Tax Service, STA", "个人所得税税率表 (comprehensive income rate schedule, official text)",
    "https://shanghai.chinatax.gov.cn/zcfw/zcfgk/grsds/201809/t441789.html",
    "Schedule 1, seven brackets",
    "Text of the seven annual brackets used for the computation: 36,000 / 144,000 / 300,000 / 420,000 / 660,000 / 960,000 RMB at 3/10/20/25/30/35/45% with quick deductions 0/2,520/16,920/31,920/52,920/85,920/181,920.",
    "V", "Chinese-language official text; used because S04's schedule is an image.")

src("S06", "United States Code (GovInfo)", "26 U.S.C. §988 — Treatment of certain foreign currency transactions",
    "https://www.govinfo.gov/content/pkg/USCODE-2024-title26/html/USCODE-2024-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm",
    "§988(a)(1)(A), §988(e)(1)-(3)",
    "§988(a)(1)(A): foreign currency gain or loss on a §988 transaction is computed separately and treated as ORDINARY income or loss. §988(e)(1): the section does not apply to a §988 transaction entered into by an individual which is a personal transaction. §988(e)(2): on disposition of nonfunctional currency in a personal transaction no gain is recognized by reason of exchange-rate changes, unless the gain would exceed $200.",
    "V")

src("S07", "Internal Revenue Service", "Rev. Proc. 2025-32 — 2026 inflation-adjusted amounts",
    "https://www.irs.gov/pub/irs-drop/rp-25-32.pdf",
    "§4.01 Table 3; §4.14; §4.39; §4.42; §4.47",
    "2026 single-filer brackets (10% to $12,400; 12% to $50,400; 22% to $105,700; 24% to $201,775; 32% to $256,225; 35% to $640,600; 37% above). 2026 standard deduction single $16,100. Foreign earned income exclusion $132,900. Gift annual exclusion $19,000. §6039F large-gift reporting threshold from foreign corporations/partnerships $20,573.",
    "V")

src("S08", "Internal Revenue Service", "Report of Foreign Bank and Financial Accounts (FBAR)",
    "https://www.irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar",
    "Who must file; When to file",
    "A U.S. person must file FinCEN Form 114 if the aggregate value of foreign financial accounts exceeded $10,000 at any time during the calendar year, whether or not the account produced taxable income. Due 15 April with an automatic extension to 15 October.",
    "V")

src("S09", "Internal Revenue Service", "Do I need to file Form 8938?",
    "https://www.irs.gov/businesses/corporations/do-i-need-to-file-form-8938-statement-of-specified-foreign-financial-assets",
    "Reporting thresholds",
    "Unmarried taxpayer living in the US: more than $50,000 on the last day of the year or more than $75,000 at any time. Taxpayer living abroad filing a non-joint return: more than $200,000 on the last day or $300,000 at any time; joint $400,000 / $600,000.",
    "V")

src("S10", "Internal Revenue Service", "Gifts from foreign person (Form 3520 Part IV)",
    "https://www.irs.gov/businesses/gifts-from-foreign-person",
    "Reporting requirements",
    "A foreign gift or bequest is an amount the recipient treats as a gift or bequest and EXCLUDES FROM GROSS INCOME. Reporting on Form 3520 Part IV is required when aggregate gifts from a nonresident alien or foreign estate exceed $100,000 in the year; for foreign corporations/partnerships the threshold is $20,116 (2025) and $20,573 (2026). Penalties are under IRC §6039F(c) absent reasonable cause.",
    "V")

src("S11", "State Council of the PRC", "Regulations of the PRC on Foreign Exchange Administration (State Council Decree No. 532)",
    "https://www.gov.cn/gongbao/content/2008/content_1071846.htm",
    "Arts. 39, 40, 42, 45, 48, 52(2)",
    "Art. 39 (evading FX controls by moving domestic FX or capital abroad): fine up to 30% of the amount; if serious, 30% up to the equivalent of the amount; criminal liability possible. Art. 40 (illegal FX arbitrage, including fraudulent purchase with false or invalid documents): same 30% / 30%-100% scale. Art. 42 (breaching cash-carry rules): warning and fine up to 20%. Art. 45 (private or disguised FX trading): warning, confiscation, up to 30%, or 30%-100% if serious. Art. 48: individuals up to RMB 50,000 for, among other things, failing to submit valid documents. Art. 52(2) defines 境内个人 as Chinese citizens AND foreigners who have continuously resided in China for one full year (diplomats excluded).",
    "V")

src("S12", "People's Bank of China / CFETS", "RMB central parity rate announcement, 6 November 2026",
    "https://www.pbc.gov.cn/zhengcehuobisi/125207/125217/125925/2026110608563230207/index.html",
    "Announcement body",
    "Interbank central parity on 2026-11-06: USD 1 = CNY 6.7168. Used only to express RMB statutory thresholds in USD; the rate changes daily.",
    "V")

src("S13", "Internal Revenue Service", "Foreign Tax Credit",
    "https://www.irs.gov/individuals/international-taxpayers/foreign-tax-credit",
    "Qualifying foreign taxes; Compliance issues",
    "A credit may be claimed only for foreign taxes imposed on income that is also subject to US tax; no credit is allowed for taxes on income excluded from US gross income (for example under the foreign earned income exclusion); where a treaty reduces the foreign tax, only the reduced amount qualifies.",
    "V")

src("S14", "U.S. Customs and Border Protection / FinCEN", "Money and Other Monetary Instruments (FinCEN Form 105, CMIR)",
    "https://www.cbp.gov/travel/international-visitors/money-monetary-instruments",
    "Federal mandate; Who must file",
    "Anyone who brings, sends or receives more than $10,000 in currency or monetary instruments at one time into or out of the United States must report it; the threshold applies to the total carried by a family or group, not per person. Failure risks forfeiture and seizure plus civil or criminal penalties.",
    "V")

src("S15", "Internal Revenue Service", "Instructions for Form 3520 (12/2025)",
    "https://www.irs.gov/instructions/i3520",
    "When and where to file; Penalties",
    "Form 3520 is due the 15th day of the 4th month after the tax year end, extended to the 15th day of the 10th month; a penalties section covers §6677, §6039F and §6662(j). The individual penalty percentages are not reproduced here.",
    "V")

src("S16", "Internal Revenue Service", "United States–China Income Tax Treaty (1984, with protocol)",
    "https://www.irs.gov/pub/irs-trty/china.pdf",
    "Arts. 9-11 (dividends, interest, royalties)",
    "Prior sessions reported a 10% maximum withholding rate for dividends, interest and royalties for beneficial owners resident in the United States. NOT re-fetched in this session; treated as a flag, not as a computed input.",
    "P")

src("S17", "People's Bank of China", "Measures for the Administration of the Sale and Purchase of Foreign Exchange and the Transfer Abroad of Individual Property (PBOC Notice [2004] No.16)",
    "https://nanjing.pbc.gov.cn/en/3688110/3688172/4048353/2025080817545423092/index.html",
    "Emigration and inheritance transfers",
    "Prior sessions cited this notice for the separate emigration/inheritance asset-transfer procedures referenced by S02 Art. 20. Not re-fetched in this session.",
    "P")

src("S18", "State Administration of Foreign Exchange (SAFE)", "2026 personal foreign exchange FAQ (employment remuneration)",
    "https://www.safe.gov.cn/tianjin/2026/0713/3088.html",
    "Answer on employment income conversion",
    "Prior sessions cited this FAQ for the documented salary conversion route. Not re-fetched in this session.",
    "P")

src("S19", "STA / SAFE", "Tax filing form for outbound payments of services, trade and other items (服务贸易等项目对外支付税务备案)",
    "https://fgk.chinatax.gov.cn/eng/c102962/c102967/c102997/c103016/c5250711/content.html",
    "Filing requirement",
    "Prior sessions cited a mandatory tax record filing before outbound payments above USD 50,000 by domestic institutions and individuals. Not re-fetched in this session.",
    "P")

src("S20", "State Administration of Foreign Exchange (SAFE)", "2015 Q3 balance-of-payments press conference transcript (English)",
    "https://www.safe.gov.cn/en/2015/1111/1175.html",
    "Statement on split transactions",
    "Prior sessions cited this for enforcement against splitting transactions to evade limits (with S01 Art. 7). Not re-fetched in this session.",
    "P")

src("S21", "PBOC and eight other authorities", "Notice on further preventing and handling speculation risks in virtual currency trading",
    "https://www.pbc.gov.cn/tiaofasi/144941/3581332/2026020619591971323/index.html",
    "Prohibitions",
    "Prior sessions cited this joint notice for the prohibition on virtual-currency related business activity in mainland China. Not re-fetched in this session.",
    "P")

src("S22", "General Administration of Customs (GACC)", "Passenger guide (English)",
    "http://english.customs.gov.cn/statics/88707c1e-aa4e-40ca-a968-bdbdbb565e4f.html",
    "Currency declaration limits",
    "Prior sessions cited the passenger guide for PRC cash-carry declaration limits. Not re-fetched in this session; the official host only serves plain HTTP.",
    "P")


def sv(*ids):
    """Render source chips."""
    out = []
    for i in ids:
        s = S[i]
        flag = "" if s["status"] == "V" else " (prior)"
        out.append(
            '<a class="src" href="{u}" target="_blank" rel="noopener noreferrer" '
            'title="{t} — {a}">{i}{f}</a>'.format(
                u=s["url"], t=s["title"].replace('"', "&quot;"), a=s["authority"], i=i, f=flag))
    return "".join(out)


# ---------------------------------------------------------------- methods
# cap: how the channel scales. ("none"|"oneoff"|"perday"|"peryear"|"unverified"|"na"|"illegal", value)
M = []


def method(**kw):
    M.append(kw)


method(
    id="M01", name="Documented after-tax RMB income → bank conversion → SWIFT wire",
    cat="Personal current account", legal="lawful", who="US citizen holding a mainland account",
    mechanism="Present valid ID plus documents proving the amount and the lawful RMB source (including PRC tax vouchers) at an authorised bank; the bank converts RMB to USD and remits it to your US account.",
    limit="No annual USD cap is stated for a non-domestic individual's conversion of lawful current-account income; the bank reviews authenticity. The USD 50,000 annual total in Art. 2 is expressly tied to domestic individuals' purchases and to all individuals' FX sales.",
    docs=["Passport / valid ID", "Income-source documents (contract, payroll, award letter, rental contract, sale contract)", "PRC tax payment certificate (完税证明) or equivalent tax vouchers", "Bank's own authenticity-review forms"],
    steps=["m01"],
    cost="0% PRC tax on the conversion itself (S04 Art. 2 lists no such category); the tax is on the underlying income.",
    cap=("none", None), srcs=["S01", "S02", "S04"], risk="Low, if the source trail is complete.",
    note="This is the route the research points to first for documented, already-taxed money.")

method(
    id="M02", name="Re-conversion of unused RMB from an earlier FX conversion (original exchange memo)",
    cat="Personal current account", legal="lawful", who="Anyone who previously converted FX into RMB in China",
    mechanism="Convert the leftover RMB back to the original currency against the original exchange memo (原兑换水单); the memo is valid for 24 months from the conversion date.",
    limit="Bounded by the amount on the original memo and the 24-month validity window.",
    docs=["Valid ID", "Original exchange memo (原兑换水单)"],
    steps=["m02"],
    cost="0% tax: this is a return of your own previously converted principal, not new income.",
    cap=("unverified", None), srcs=["S02"], risk="Low, but only if the memo exists and is within 24 months.",
    note="Amounts on the memo are personal facts and are not published anywhere; left unverified.")

method(
    id="M03", name="Walk-in small-amount re-conversion with ID only",
    cat="Personal current account", legal="lawful", who="Non-domestic individuals",
    mechanism="Same-day conversion up to the equivalent of USD 500 (or USD 1,000 at pre-departure port outlets) needs only valid ID, with no tax or exchange documents.",
    limit="USD 500 per day; USD 1,000 per day at port outlets; per person.",
    docs=["Valid ID"],
    steps=["m03"],
    cost="0% tax. Commercial spread/fee unverified.",
    cap=("perday", WALKIN_USD_PER_DAY), srcs=["S02"], risk="Impractical for large balances: at USD 500/day, USD 400,000 takes 800 counter visits.",
    note="A safety valve, not a repatriation plan.")

method(
    id="M04", name="Remit an existing FX savings-account balance abroad",
    cat="Personal current account", legal="lawful", who="Non-domestic individuals",
    mechanism="If the money is already USD (or another foreign currency) inside a PRC FX savings account, remit it abroad by presenting valid ID.",
    limit="Art. 15(1) states no annual amount for a non-domestic individual's outward remittance from an FX savings account. (Domestic individuals are handled under Art. 14: USD 50,000/day with ID, above that with authenticity documents.)",
    docs=["Valid ID", "Account details"],
    steps=["m04"],
    cost="0% PRC tax; 0% US tax on moving your own funds.",
    cap=("oneoff", None), srcs=["S02"], risk="Low, but requires the balance to already be FX.",
    note="The cheapest lawful path when it applies: no conversion spread, because no conversion is needed.")

method(
    id="M05", name="Overseas ATM cash withdrawals with a PRC bank card",
    cat="Card channels", legal="lawful", who="Holder of a cross-border-enabled PRC debit card",
    mechanism="Withdraw USD cash from ATMs abroad using the PRC card; the issuer converts at its own rate.",
    limit="RMB 100,000 equivalent per individual per civil year across all cards; RMB 10,000 equivalent per card per day. Exceeding the annual cap suspends overseas cash withdrawal for the current and the following year.",
    docs=["PRC bank card", "Card issuer's cross-border switch enabled"],
    steps=["m05"],
    cost="0% tax. Commercial: issuer conversion rate, out-of-network ATM surcharges - unverified.",
    cap=("peryear", ATM_USD_PER_YEAR), srcs=["S03"], risk="Medium: hard annual wall, cash handling, US side must be declared if carried over USD 10,000.",
    note="Also note the US CMIR rule if physical cash crosses the border (S14).")

method(
    id="M06", name="Overseas merchant / POS spending with a PRC card",
    cat="Card channels", legal="lawful", who="Cardholder",
    mechanism="Pay genuine foreign merchants (travel, tuition, hotels, retail) directly with the PRC card, so the RMB is consumed abroad rather than converted and repatriated.",
    limit="No published fixed amount; spending must be genuine personal consumption and the card's own limit applies.",
    docs=["PRC bank card"],
    steps=["m06"],
    cost="0% tax. Not a way to obtain USD cash for other purposes.",
    cap=("na", None), srcs=["S03", "S01"], risk="Low but it does not produce movable USD; using it to extract cash is prohibited (M22).",
    note="Counts as a legitimate consumption channel only.")

method(
    id="M07", name="Carry physical cash across the border",
    cat="Cash", legal="lawful-conditional", who="Travellers",
    mechanism="Withdraw RMB or USD cash in China and carry it out within customs limits.",
    limit="PRC declaration limits: not re-verified in this session (prior sessions cited the GACC passenger guide, S22). US side verified: more than USD 10,000 must be reported on FinCEN Form 105, aggregated across a family or group.",
    docs=["FinCEN Form 105 if over USD 10,000", "PRC customs declaration as required"],
    steps=["m07"],
    cost="0% tax if declared. Seizure risk if not declared (S14).",
    cap=("unverified", None), srcs=["S22", "S14"], risk="High: physical loss, theft, seizure, and repeated trips are visible to customs.",
    note="A last resort for small amounts.")

method(
    id="M08", name="Sale of PRC real estate by a foreign individual, then remit after-tax proceeds",
    cat="Capital events", legal="lawful-conditional", who="Owner of lawfully acquired PRC property",
    mechanism="Sell the property, settle PRC taxes on the transfer, then convert and remit the net proceeds with the sale and tax documents.",
    limit="No fixed cap; documentation-driven. Real-estate FX handling is governed by the separate property rules referenced in S02 Art. 21.",
    docs=["Sale contract and title documents", "PRC tax payment certificates for the transfer", "Bank authenticity documents"],
    steps=["m08"],
    cost="PRC IIT on the transfer gain at 20% (S04 Art. 3(3)); 0% tax on the act of conversion.",
    cap=("oneoff", None), srcs=["S01", "S02", "S04"], risk="Medium: tax base and cost-basis proof determine the real cost.",
    note="The 'conversion penalty' people feel is usually this 20% on the gain, already owed before any conversion.")

method(
    id="M09", name="Inheritance outbound transfer (继承财产转移)",
    cat="Capital events", legal="lawful-conditional", who="US citizen inheriting mainland assets",
    mechanism="Apply under the separate individual-property transfer rules referenced by S02 Art. 20, then convert and remit the inherited proceeds.",
    limit="Procedure-based; the amount follows the estate documents. The 2004 notice is cited from a prior session (S17) and not re-fetched here.",
    docs=["Notarised inheritance documents", "PRC tax clearance for the estate", "SAFE application"],
    steps=["m09"],
    cost="PRC IIT treatment of inherited assets depends on the asset and the estate's tax position; not quantified here.",
    cap=("oneoff", None), srcs=["S02", "S17"], risk="Medium-high: multi-agency approval, slow.",
    note="Documentation and approvals, not a tax rate, are the binding constraint.")

method(
    id="M10", name="Emigrant personal-asset transfer (移民财产转移) — former PRC residents only",
    cat="Capital events", legal="lawful-conditional", who="Naturalised US citizens / PRs who emigrated from mainland China",
    mechanism="Former PRC residents who have emigrated may transfer pre-emigration domestic assets abroad under the dedicated procedure.",
    limit="Procedure-based, one-time in principle; tied to assets held before emigration and to the household-registration cancellation.",
    docs=["Proof of emigration and household-registration cancellation", "Asset ownership documents", "SAFE approval"],
    steps=["m10"],
    cost="PRC taxes on the underlying assets as applicable; 0% on conversion.",
    cap=("oneoff", None), srcs=["S02", "S17"], risk="Medium-high; unavailable if you never held PRC residence.",
    note="Not available to a US citizen who never emigrated from mainland China.")

method(
    id="M11", name="PRC-citizen USD 50,000/year facilitated FX purchase quota",
    cat="Quota", legal="lawful-conditional", who="Domestic individuals (境内个人)",
    mechanism="Within the annual total, a domestic individual buys FX at a bank with valid ID and no transaction documents; the SAFE system records it.",
    limit="USD 50,000 equivalent per person per calendar year (S02 Art. 2; S01 Art. 9).",
    docs=["PRC resident identity document", "Personal FX system record"],
    steps=["m11"],
    cost="0% tax on the purchase itself.",
    cap=("peryear", PRC_QUOTA_USD_PER_YEAR), srcs=["S01", "S02", "S11"], risk="Medium: hard annual ceiling, and eligibility for a US passport holder is contested (see F02).",
    note="S11 Art. 52(2) defines 境内个人 as including foreigners resident in China for one full year, which conflicts with the narrower reading used by an earlier session. Flagged, not resolved.")

method(
    id="M12", name="Transfer between FX savings accounts of immediate relatives",
    cat="Quota", legal="lawful-conditional", who="Account holders with parents/spouse/children in China",
    mechanism="Domestic transfer of FX between the account holder and immediate relatives, with both IDs and a relationship certificate.",
    limit="Domestic FX-account transfers only; a transfer between a domestic and a non-domestic individual's account is treated as a cross-border transaction (S02 Art. 28(3)).",
    docs=["Both IDs", "Relationship certificate (household register, marriage certificate, notarised proof)"],
    steps=["m12"],
    cost="0% tax on the transfer; the receiving relative's own quota and tax position then apply.",
    cap=("unverified", None), srcs=["S02"], risk="Medium: using relatives' quotas to split amounts is expressly prohibited (M18).",
    note="Lawful for genuine family support; unlawful if used to evade limits.")

method(
    id="M13", name="PRC employer pays salary directly to your US account",
    cat="Employment and business", legal="lawful-conditional", who="Employees of a PRC entity",
    mechanism="The employer withholds PRC IIT, then remits net salary abroad through its own bank channels.",
    limit="No personal cap; the employer's remittance rules and the tax record filing apply.",
    docs=["Employment contract", "PRC IIT withholding records", "Employer's remittance documentation"],
    steps=["m13"],
    cost="PRC IIT withheld at source (3%-45% comprehensive, S04); 0% on the remittance.",
    cap=("unverified", None), srcs=["S04", "S19"], risk="Low for the employee; depends entirely on the employer.",
    note="Often the cleanest paper trail.")

method(
    id="M14", name="Dividends / profit repatriation from a PRC company you own",
    cat="Employment and business", legal="lawful-conditional", who="Foreign shareholder of a PRC enterprise",
    mechanism="Distribute after-tax profits, settle withholding, then remit the dividend.",
    limit="No personal cap; corporate tax and withholding must be settled first.",
    docs=["Board/shareholder resolution", "PRC enterprise income tax records", "Withholding tax payment certificates", "Audited accounts"],
    steps=["m14"],
    cost="PRC withholding on dividends at the 20% statutory flat rate (S04 Art. 3(3)); a treaty rate may reduce this but was not re-verified here (F04).",
    cap=("oneoff", None), srcs=["S04", "S16"], risk="Medium: requires a compliant company and audited accounts.",
    note="Corporate-level tax is a separate, earlier layer.")

method(
    id="M15", name="Equity transfer or company liquidation proceeds",
    cat="Employment and business", legal="lawful-conditional", who="Foreign investor exiting",
    mechanism="Transfer the equity or liquidate, settle PRC taxes on the gain, register the change, then remit.",
    limit="No fixed cap; the taxable gain and approvals drive the timing.",
    docs=["Transfer agreement", "Valuation", "PRC tax clearance on the transfer", "SAFE registration"],
    steps=["m15"],
    cost="PRC IIT on the transfer gain at 20% (S04 Art. 3(3)); 0% on conversion.",
    cap=("oneoff", None), srcs=["S04", "S11"], risk="Medium-high: valuation disputes are the usual delay.",
    note="")

method(
    id="M16", name="Genuine cross-border service fees, royalties or IP licensing",
    cat="Employment and business", legal="lawful-conditional", who="US individual or entity invoicing PRC clients",
    mechanism="Invoice a PRC payer for real services; the payer withholds tax, files the outbound-payment tax record where required, and remits.",
    limit="No cap; arm's-length pricing and genuine delivery are required.",
    docs=["Contract", "Invoices", "Withholding tax records", "Outbound payment tax filing above the threshold (prior-cited)"],
    steps=["m16"],
    cost="PRC withholding on royalties at the 20% statutory flat rate (S04); VAT may also apply (not re-verified).",
    cap=("oneoff", None), srcs=["S04", "S19"], risk="High if the arrangement is not genuine: fabricating contracts is a criminal-adjacent violation (M21).",
    note="")

method(
    id="M17", name="Individual FX settlement account / licensed payment institutions",
    cat="Employment and business", legal="lawful-conditional", who="Registered individual traders and businesses",
    mechanism="Route trade-related receipts through an individual FX settlement account or a licensed cross-border payment institution.",
    limit="Requires foreign-trade registration or a licensed institution; not a personal remittance channel.",
    docs=["Business registration / foreign-trade filing", "Trade documents"],
    steps=["m17"],
    cost="0% tax on conversion; business income tax applies to the underlying profit.",
    cap=("na", None), srcs=["S01", "S02"], risk="Medium: misusing a business channel for personal funds is a violation.",
    note="")

for mid, name, how, cite, fine, srcids in [
    ("M18", "Splitting amounts across friends' or relatives' USD 50,000 quotas (smurfing)",
     "Using multiple people's annual quotas, or multiple cards, to move one person's money.",
     "S01 Art. 7; S02 Art. 28/13; S03 Art. I", "Up to 30% of the amount, or 30%-100% if serious, plus confiscation and possible criminal liability (S11 Arts. 39-45).", ["S01", "S02", "S11"]),
    ("M19", "Underground banks and informal onshore/offshore RMB-USD swaps (对敲)",
     "Paying RMB to an intermediary in China and receiving USD abroad from an unrelated party.",
     "S11 Arts. 39, 45", "Up to 30%, or 30%-100% if serious, plus confiscation (S11 Art. 45).", ["S11"]),
    ("M20", "Crypto / stablecoin OTC bridge",
     "Buying a stablecoin in China and selling it abroad to obtain USD.",
     "S21 (prior-cited)", "Virtual-currency business activity is prohibited; FX and criminal exposure also apply. Not re-fetched here.", ["S21", "S11"]),
    ("M21", "Fabricated or over-invoiced trade / consulting contracts",
     "Inventing a transaction to justify a purchase of foreign exchange.",
     "S11 Art. 40; S01 Art. 7", "Illegal FX arbitrage: up to 30%, or 30%-100% if serious (S11 Art. 40).", ["S11", "S01"]),
    ("M22", "Overseas POS cash-out, or borrowing other people's bank cards",
     "Extracting cash from a card abroad or using third-party cards to move money.",
     "S03 Art. I-II; S11 Art. 45", "Card use is suspended and fines follow; borrowing or lending cards to evade the rules is expressly prohibited (S03).", ["S03", "S11"]),
]:
    method(
        id=mid, name=name, cat="Prohibited", legal="unlawful", who="—",
        mechanism=how, limit="Not lawful — no limit applies because the channel itself is prohibited.",
        docs=["—"], steps=[], cost="Not a cost: a penalty. " + fine,
        cap=("illegal", None), srcs=srcids,
        risk="Do not use.", note=cite)

LAWFUL = [m for m in M if m["legal"] != "unlawful"]
UNLAWFUL = [m for m in M if m["legal"] == "unlawful"]

# ---------------------------------------------------------------- penalty layers
LAYERS = [
    dict(id="L1", name="PRC tax on the act of converting",
         rule="0%", verified="No income category exists for converting your own money (S04 Art. 2 lists nine categories, none of which is a currency conversion). No conversion tax appears in S01/S02.",
         basis="Statute (verified)", srcs=["S04", "S01", "S02"],
         what="The single most important finding: China does not tax the conversion. It taxes the income that produced the money, and the bank checks that tax was paid."),
    dict(id="L2", name="PRC income tax on the money's source (if not yet paid)",
         rule="3%-45% progressive on comprehensive income; 5%-35% business; 20% flat on dividends, interest, asset leasing, asset transfer and incidental income",
         verified="S04 Art. 3; bracket schedule S05. Resident comprehensive income deducts RMB 60,000/year (S04 Art. 6(1)); non-resident wages deduct RMB 5,000/month (S04 Art. 6(2)).",
         basis="Statute (verified)", srcs=["S04", "S05"],
         what="This is the real 'considerable tax' people encounter, and it is owed on the income regardless of whether the money ever leaves China."),
    dict(id="L3", name="Documentary gatekeeper (the bank's authenticity review)",
         rule="Tax vouchers plus income-source documents required for a non-domestic individual's conversion of lawful RMB income",
         verified="S02 Art. 13(1) requires ID and supporting documents 'including tax vouchers' (含税务凭证). S01 Art. 13 requires ID and relevant documents. S01 Art. 7 prohibits fabricated vouchers.",
         basis="Regulation (verified)", srcs=["S02", "S01"],
         what="A missing tax certificate is not a tax - it is a refusal to process, which is why balances can appear 'stuck'. The fix is paperwork, not a payment."),
    dict(id="L4", name="US tax on moving the money",
         rule="0%",
         verified="Moving your own funds between your own accounts is not a realization event. For foreign currency, §988(e)(1) excludes an individual's personal transactions from §988 entirely, and §988(e)(2) recognises no gain from exchange-rate changes on a personal transaction unless the gain would exceed $200 (S06).",
         basis="Statute (verified)", srcs=["S06"],
         what="A wire from your Chinese account to your US account is not income and not a taxable sale."),
    dict(id="L5", name="US residual tax after the foreign tax credit",
         rule="Often 0%, but not always",
         verified="The credit is limited to foreign tax on income also subject to US tax, and no credit is allowed against excluded income (S13). Computed per amount in the tables, using 2026 single-filer brackets (S07).",
         basis="Computed model on statutory inputs", srcs=["S13", "S07"],
         what="Where the PRC rate exceeds the US rate, the credit usually erases the US tax. Where it does not (for example a 20% PRC rate against a higher US bracket), a residual can remain."),
    dict(id="L6", name="Commercial spread and transfer fees",
         rule="UNVERIFIED - no official publication",
         verified="No PRC or US government source publishes a bank's customer spread, cable fee or intermediary charge. Left blank everywhere on this site.",
         basis="Not verifiable from official sources", srcs=["S01", "S03"],
         what="The one layer that genuinely needs a quote from your own bank. The site's calculator stays empty until you enter one."),
    dict(id="L7", name="Reporting obligations (no tax if complied with)",
         rule="FBAR over $10,000; Form 8938 from $50,000/$75,000; Form 3520 from $100,000 of gifts; CMIR over $10,000 in cash",
         verified="S08, S09, S10, S14.",
         basis="Statute (verified)", srcs=["S08", "S09", "S10", "S14"],
         what="These are information returns. Their cost is zero when filed and potentially severe when not."),
    dict(id="L8", name="Penalty exposure on prohibited channels",
         rule="Up to 30% of the amount; 30%-100% if serious; up to 20% for cash-carry breaches; up to RMB 50,000 for individuals failing document requirements",
         verified="S11 Arts. 39, 40, 42, 45, 48.",
         basis="Statute (verified)", srcs=["S11"],
         what="This is the only layer where a percentage of the whole balance can legally vanish. Every prohibited route multiplies risk by the size of the transfer."),
]

# ---------------------------------------------------------------- reporting rules
US_RULES = [
    ("FBAR (FinCEN Form 114)", "Aggregate foreign accounts over $10,000 at any time in the calendar year", "April 15, automatic extension to October 15", "S08"),
    ("Form 8938", "Unmarried, living in the US: over $50,000 on December 31 or over $75,000 at any time. Living abroad, non-joint: $200,000 / $300,000.", "Filed with the income tax return", "S09"),
    ("Form 3520, Part IV (foreign gift)", "Aggregate gifts over $100,000 from a nonresident alien or foreign estate; $20,573 (2026) for foreign corporations/partnerships", "15th day of the 4th month; extended to the 15th day of the 10th month", "S10"),
    ("FinCEN Form 105 (CMIR)", "More than $10,000 in currency or monetary instruments crossing the US border at one time, aggregated for a family or group", "At the time of transport", "S14"),
    ("§988 foreign-currency gain", "Personal transaction: excluded; no gain recognised unless it would exceed $200", "n/a", "S06"),
    ("Foreign tax credit (Form 1116)", "Credit limited to foreign tax on income also subject to US tax; none against excluded income", "With the return", "S13"),
    ("Foreign earned income exclusion", "$132,900 for 2026", "Form 2555 with the return", "S07"),
    ("Gift annual exclusion", "$19,000 per donee for 2026", "Form 709 only above the exclusion", "S07"),
]

PRC_RULES = [
    ("Annual FX total (domestic individuals' purchases; all individuals' sales)", "USD 50,000 equivalent per person per year", "S02"),
    ("Non-domestic individual converting lawful RMB income", "No USD cap stated; ID plus documents including tax vouchers", "S02"),
    ("Re-conversion against original exchange memo", "Valid 24 months; ID-only same-day amounts of USD 500 (USD 1,000 at port outlets)", "S02"),
    ("Overseas ATM cash withdrawal", "RMB 100,000 equivalent per person per civil year; RMB 10,000 per card per day", "S03"),
    ("IIT, comprehensive income", "3%-45% progressive; RMB 60,000 annual deduction for residents; RMB 5,000 monthly for non-resident wages", "S04"),
    ("IIT, dividends/interest/asset transfer/incidental", "20% flat", "S04"),
    ("IIT, business income", "5%-35% progressive", "S04"),
    ("FX circumvention fines", "Up to 30% of the amount; 30%-100% if serious", "S11"),
    ("Cash-carry breach", "Warning and up to 20% of the amount", "S11"),
    ("Individual document/registration failures", "Up to RMB 50,000", "S11"),
]

# ---------------------------------------------------------------- flags
FLAGS = [
    dict(id="F01", level="Unverified commercial layer", title="Bank spread, cable fees and intermediary charges are not published anywhere official",
         detail="Every all-in dollar figure on this site excludes the commercial layer. No PRC or US regulator publishes a bank's customer spread or wire fee, so those cells are blank by design. Obtain an executable quote from your own bank and enter it in the calculator.",
         srcs=["S01", "S03"], action="Ask the bank for the all-in price in writing: spread versus the central parity, outgoing fee, intermediary lift, and the US receiving fee."),
    dict(id="F02", level="Conflicting definitions", title="Who counts as a 境内个人? Two official texts point different ways",
         detail="Two official texts point different ways. State Council Decree 532 Art. 52(2) defines 境内个人 as Chinese citizens AND foreigners who have continuously resided in China for one full year; an earlier session's portal asserted flatly that the USD 50,000 quota is never available to a US passport holder. The implementing rules do not restate the definition. Note the direction of the risk: being classified as 境内个人 would IMPOSE the USD 50,000 annual cap on purchases rather than remove it, whereas the Art. 13 documented route for a non-domestic individual states no dollar cap. So the bank's classification decision changes whether a large balance can move in one cycle or needs eight years.",
         srcs=["S11", "S02", "S01"], action="Ask the specific bank, in writing, which category it will record you under, and keep that answer."),
    dict(id="F03", level="Model assumption", title="Resident vs non-resident IIT computation changes the answer",
         detail="The computed PRC figures assume resident status: annual brackets with a RMB 60,000 deduction. A non-resident is computed monthly with a RMB 5,000 deduction and a monthly-converted schedule (S04 Art. 2 and 6(2)). No personal residency facts were supplied, so the resident case is used and labelled.",
         srcs=["S04", "S05"], action="If you spent fewer than 183 days in China in each tax year concerned, the non-resident computation may apply."),
    dict(id="F04", level="Prior-session claim, not re-verified", title="Treaty 10% cap on dividends, interest and royalties",
         detail="An earlier session reported a 10% treaty maximum under Articles 9-11 and warned that only the treaty-reduced tax is creditable. The IRS page on the credit supports the second half (S13). The treaty text itself was not re-fetched in this session, so no computed cell relies on the 10% rate; the 20% statutory rate is used.",
         srcs=["S16", "S13", "S04"], action="Confirm the article and the limitation-on-benefits wording before relying on a treaty rate."),
    dict(id="F05", level="Unknown personal fact", title="Whether the PRC tax on the income has already been paid",
         detail="This single fact decides whether the cost is 0% or 3%-45%. A 完税证明 or the withholding records settle it. Nothing in the repository can infer it.",
         srcs=["S02", "S04"], action="Locate the tax payment certificate or the employer's withholding records before visiting the bank."),
    dict(id="F06", level="Unknown personal fact", title="Cost basis and acquisition date are unknown",
         detail="The PRC 20% on an asset transfer applies to the gain, and the US §988 result depends on the USD basis at acquisition. Neither is known, so gains are modelled on the gross amount only as an upper bound.",
         srcs=["S04", "S06"], action="Reconstruct acquisition dates, RMB amounts and the exchange rate on each date."),
    dict(id="F07", level="Unknown compliance history", title="Prior US filing compliance cannot be assessed",
         detail="If FBAR or Form 8938 obligations were missed in earlier years, the penalty exposure may dwarf every fee discussed here, and it cannot be quantified without the account history.",
         srcs=["S08", "S09"], action="Check filing history for every year the account exceeded the thresholds before moving a large balance."),
    dict(id="F08", level="Unknown personal fact", title="Whether original exchange memos exist and are within 24 months",
         detail="The exchange-memo route is the only one that needs no tax certificate at all, but it is limited to RMB that came from a prior conversion and expires after 24 months.",
         srcs=["S02"], action="Search bank records for 原兑换水单 before treating this route as available."),
    dict(id="F09", level="Prior-session claim, not re-verified", title="PRC cash-carry declaration limits",
         detail="The GACC passenger-guide limits are cited from a prior session and were not re-fetched here, so no cash-carry figure is stated on this site. The US side (over USD 10,000 on FinCEN Form 105) is verified.",
         srcs=["S22", "S14"], action="Read the current GACC passenger guide and the airline/customs rules before carrying cash."),
    dict(id="F10", level="Model assumption", title="One exchange rate is used throughout",
         detail="All RMB thresholds are converted at the PBOC central parity of 2026-11-06 (USD 1 = CNY 6.7168). The rate changes daily, and IIT Law Art. 16 requires foreign-currency income to be converted at the central parity rate on the relevant date.",
         srcs=["S12", "S04"], action="Re-run the arithmetic with the central parity for the date that actually applies."),
    dict(id="F11", level="Scope limit", title="State tax, local tax and future law changes are out of scope",
         detail="The model covers US federal tax only. State income tax, the Netherlands or other residence-country rules, and any change in PRC or US law after 2026-11-08 are not modelled.",
         srcs=["S07"], action="Add your state's treatment before relying on a net figure."),
    dict(id="F12", level="Model assumption", title="No other income, single filer, standard deduction",
         detail="The US residual column assumes a single filer with no other income and the 2026 standard deduction of $16,100. Real returns stack this income on top of other income, which usually raises the US rate and can change the residual.",
         srcs=["S07"], action="Ask a preparer to run your actual return with and without the conversion."),
    dict(id="F13", level="Prior-session claim, not re-verified", title="Form 3520 penalty percentages",
         detail="The Form 3520 instructions contain a penalties section, but the percentages were not extracted in this session, so none are stated. An earlier portal attributed the 35% trust penalty (§6677) to foreign gifts generally, which is a mislabel: gifts fall under §6039F(c).",
         srcs=["S15", "S10"], action="Read the current instructions for the penalty that applies to the specific part of the form."),
    dict(id="F14", level="Prior-session claim, not re-verified", title="Crypto prohibition and outbound-payment tax filing threshold",
         detail="The virtual-currency prohibition (S21) and the USD 50,000 outbound-payment tax filing threshold (S19) are cited from prior sessions and were not re-fetched here. They are described, not quantified.",
         srcs=["S21", "S19"], action="Read the linked notices directly before acting."),
    dict(id="F15", level="Repository irregularity", title="Three separate dashboards disagreed with each other",
         detail="Earlier sessions published docs/, site/ and portal/ as parallel dashboards with different route counts (18 entries in data/methods.json versus 22 in portal/ and research/), two executive summaries, and incompatible source standards (one cited commercial bank and fintech pages). See the audit page for the row-by-row review.",
         srcs=["S01"], action="This dashboard is now the entry point; the three earlier dossiers are preserved unchanged under their original paths."),
    dict(id="F16", level="Repository irregularity", title="Earlier entries mischaracterised §988 and Form 3520",
         detail="data/methods.json stated that a personal FX gain above $200 is reported as capital gain; §988(a)(1)(A) makes it ordinary. portal/ applied the §6677 trust penalty to foreign gifts generally; gifts are reported under §6039F. Both are corrected here and flagged for review.",
         srcs=["S06", "S10", "S15"], action="Do not rely on those two earlier statements."),
]
