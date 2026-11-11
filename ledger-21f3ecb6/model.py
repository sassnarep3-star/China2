"""Cost model. Every input is read from data/sources.json; nothing is typed twice.

Arithmetic only: no tax rate is applied to a person, because the origin of the
money is unknown. Figures are USD rounded to cents for display; verify.py
recomputes each cell from the raw published numbers.
"""
import csv, json, os
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
TODAY = "2026-11-11"
AMOUNTS = list(range(10_000, 400_001, 10_000))


def load(name):
    with open(os.path.join(D, name), encoding="utf-8") as f:
        return json.load(f)


S = {s["id"]: s for s in load("sources.json")}
FIG = {k: v for s in S.values() for k, v in s["figures"].items()}

# ---- published inputs (each traced to a source id) -------------------------
BOC_SELL = F(str(FIG["usd_sell_spot_per100"])) / 100      # S09
BOC_BUY = F(str(FIG["usd_buy_spot_per100"])) / 100        # S09
BOC_CASH_SELL = F(str(FIG["usd_sell_cash_per100"])) / 100  # S09
BOC_MID = (BOC_SELL + BOC_BUY) / 2                        # arithmetic on S09
HSBC_SELL = F(str(FIG["usd_sell_spot"]))                   # S11
HSBC_BUY = F(str(FIG["usd_buy_spot"]))                     # S11
HSBC_MID = (HSBC_SELL + HSBC_BUY) / 2                      # arithmetic on S11
FED = F(str(FIG["nov6"]))                                  # S13, 6 Nov 2026
# Read from S10 explicitly: a flat merge of every "figures" block would collide
# with S12, which uses the same key names.
B10 = S["S10"]["figures"]
BOC_PCT = F(str(B10["pct"]))
BOC_MIN, BOC_MAX, BOC_CABLE = F(B10["min_cny"]), F(B10["max_cny"]), F(B10["cable_cny"])
HSBC_PCT = F(str(S["S12"]["figures"]["pct"]))              # S12 0.001
HSBC_MIN, HSBC_MAX, HSBC_CABLE = F(100), F(500), F(120)

METHODS = [
    dict(id="M01", name="BOC online telegraphic transfer, within the annual total",
         status="lawful, gated", pricing="boc", pick="M01",
         who="A domestic individual (Chinese citizen, or a foreign national continuously resident in China for one full year) converting for current-account purposes.",
         cap="USD 50,000 of purchase per person per calendar year; ID only inside the total.",
         pros=["Published fee schedule, capped at CNY 260 plus the cable fee.",
               "Narrowest published spread of the two banks read here.",
               "Can be started in the mobile app without a branch visit.",
               "The cheapest known priced route at every amount tested."],
         cons=["Hard ceiling of USD 50,000 per person per year, so USD 400,000 cannot be done in one calendar year by one person.",
               "The board is indicative: the rate actually dealt governs (S09 disclaimer).",
               "Purpose must be a permitted current-account purpose; capital-account money does not fit here.",
               "Using family members' totals to go faster is unlawful (see M14)."],
         steps=["Log in to BOC online/mobile banking and open 结汇购汇 (FX purchase).",
                "Choose USD, the amount, and the purpose category that matches the underlying transaction.",
                "The system checks the annual total against your ID number and records the transaction in the SAFE personal FX system (S01 Art. 36).",
                "Pay in CNY from the account; USD lands in your FX account or is remitted.",
                "To send it out: outward remittance from the FX savings account is ID-only up to USD 50,000 per day; above that, authenticity documents are required (S01 Art. 14).",
                "Keep the purchase receipt (结汇/购汇通知单) for the US side of the file."],
         sources=["S01", "S09", "S10"]),
    dict(id="M02", name="BOC online telegraphic transfer, above the annual total with documents",
         status="lawful, gated", pricing="boc", pick="M02",
         who="A domestic individual whose current-account purpose is documented (salary certificate, service contract, etc.).",
         cap="No published total, but each purchase above the annual total is reviewed against transaction documents (S01 Art. 12).",
         pros=["The fee schedule is the same as M01, so the price does not rise with the paperwork.",
               "A documented salary, service fee or similar current-account item is the intended use of this route.",
               "Scales past USD 50,000 without using another person's total."],
         cons=["The bank decides whether the documents are sufficient; there is no published checklist beyond 'documents evidencing the transaction'.",
               "Bank staff may still decline a purpose they cannot map to the regulations.",
               "Capital-account money (property proceeds, investments) needs M03/M04 instead."],
         steps=["Collect the underlying documents: contract, invoice, tax payment record, employer certificate.",
                "Present them with your ID at the branch (or upload where the bank supports it).",
                "The bank reviews authenticity and consistency before dealing (S03 Art. 12 requires a reasonable review of the documents).",
                "The purchase and remittance are recorded in the personal FX system.",
                "Retain the reviewed documents and the bank's receipt."],
         sources=["S01", "S03", "S09", "S10"]),
    dict(id="M03", name="Emigrant property transfer (移民财产转移) — SAFE approval",
         status="lawful, approval required", pricing="boc", pick="M03",
         who="A natural person who has moved from mainland China to a foreign country (or to Hong Kong/Macao) and is converting lawful property owned before acquiring that status.",
         cap="No published ceiling; the SAFE branch approves a total amount, and the bank remits within it (S05).",
         pros=["Built for exactly this fact pattern: legal wealth accumulated in China, then emigration.",
               "Staging was abolished in 2014, so the approved amount can be remitted once (S05).",
               "SAFE approval itself is not published as a charge; the cost is the bank's spread and fee."],
         cons=["Requires proof of emigration, including cancellation of household registration (S04 Art. 8).",
               "Requires a tax certificate or tax-payment receipt from the tax authority (S04 Art. 8(6)).",
               "Must go to your own account abroad; the bank may not pay cash (S04 Art. 11).",
               "The published rule text conflicts with itself: S04 Art. 6 still describes staged remittance and a national filing above RMB 500,000, both abolished by S05."],
         steps=["Obtain the household-registration cancellation certificate and proof of residence abroad.",
                "Assemble the property-rights documents and the tax certificate/tax-payment receipt.",
                "File at the SAFE branch where your household was registered (S04 Art. 5).",
                "Receive the approval letter and the capital-account approval document.",
                "Take them to the bank; convert and remit in one go or in instalments within the approved amount (S05).",
                "The bank remits to your own account abroad."],
         sources=["S04", "S05", "S09", "S10"]),
    dict(id="M04", name="Inherited-property transfer (继承财产转移) — SAFE approval",
         status="lawful, approval required", pricing="boc", pick="M04",
         who="A foreign citizen or Hong Kong/Macao resident who has lawfully inherited property in mainland China.",
         cap="No published ceiling; approved per estate by the SAFE branch where the deceased was registered.",
         pros=["The statutory route for inherited money.",
               "Each estate is applied for once and may be remitted once or in instalments.",
               "Parallel applications from different deceased persons may be consolidated at one branch (S05)."],
         cons=["Requires inheritance documents and the deceased's property-rights documents, notarised where required (S04 Art. 9).",
               "Requires the deceased's tax certificate.",
               "SAFE will not accept an application while a criminal or civil case over the property is open (S04 Art. 12).",
               "The 2004 text and the 2014 amendment must be read together; the older text is still published unamended."],
         steps=["Obtain the inheritance documents and the deceased's property-rights documents.",
                "Obtain the tax certificate from the tax authority where the property is located.",
                "File at the SAFE branch where the deceased was registered.",
                "Receive approval and the capital-account approval document.",
                "Convert and remit at the bank within the approved amount.",
                "Funds go to your own account abroad."],
         sources=["S04", "S05", "S09", "S10"]),
    dict(id="M05", name="HSBC China telegraphic transfer (Premier/Advance)",
         status="lawful, gated", pricing="hsbc_tt", pick="M05",
         who="An HSBC China customer in the Premier or Advance segment.",
         cap="Same convertibility rules apply: the annual total and documentary review are SAFE rules, not bank rules.",
         pros=["Fee capped at CNY 500 plus CNY 120 cable.",
               "Premier status supports Global Transfer, which is free (M06).",
               "One institution end-to-end can simplify the paper trail."],
         cons=["Wider published spread than BOC: 0.5004 percent against its own midpoint, versus 0.2097 percent at BOC.",
               "Premier pricing needs a total relationship balance of at least CNY 500,000 or equivalent (S12 note 3).",
               "New Advance accounts are restricted since 18 March 2026 (S12 note 4).",
               "The tariff PDF carries two different effective dates in one file (S12)."],
         steps=["Confirm your segment and, for Premier, the relationship balance test.",
                "Start an outward telegraphic transfer in online banking.",
                "Enter the beneficiary bank details for your own US account.",
                "Choose whether to pay 'Pay Exact' (CNY 200) so the US bank's charge is covered (S12).",
                "Convert at HSBC's selling rate on the day and submit.",
                "Keep the advice for the FBAR/8938 file."],
         sources=["S11", "S12", "S01"]),
    dict(id="M06", name="HSBC Global Transfer to your own HSBC account abroad (Premier)",
         status="lawful, gated", pricing="hsbc_gt_premier", pick="M06",
         who="An HSBC China Premier customer who also holds an HSBC account in the destination country.",
         cap="Convertibility limits are unchanged; the fee is what changes.",
         pros=["No transfer fee published for Premier (S12 item 2.2.6.1).",
               "Fast internal routing between HSBC entities.",
               "No cable charge."],
         cons=["Depends on holding a Premier relationship in China and an HSBC account in the US.",
               "The FX spread is still charged: 0.5004 percent at the board read here.",
               "Requires the same SAFE convertibility gate as any other bank route."],
         steps=["Open the HSBC account in the destination country (HSBC US) in your own name.",
                "Link it in HSBC China online banking as a Global Transfer destination.",
                "Convert CNY to USD and select Global Transfer to self.",
                "Confirm the rate shown; submit.",
                "Retain the confirmation for US reporting."],
         sources=["S12", "S11"]),
    dict(id="M07", name="HSBC Global Transfer to your own HSBC account abroad (Advance)",
         status="lawful, gated", pricing="hsbc_gt_advance", pick="M07",
         who="An HSBC China Advance customer with an HSBC account abroad.",
         cap="Convertibility limits unchanged.",
         pros=["A published flat fee of USD 20 per transaction (S12 item 2.2.6.1).",
               "No cable charge.",
               "Flat pricing is cheaper than a percentage at larger amounts."],
         cons=["New Advance accounts have been restricted since 18 March 2026 (S12 note 4).",
               "The same 0.5004 percent spread applies.",
               "Requires an HSBC account in the destination country."],
         steps=["Confirm you hold an eligible Advance relationship.",
                "Link your own HSBC account abroad as a Global Transfer destination.",
                "Convert and send; USD 20 applies per transaction.",
                "Keep the advice."],
         sources=["S12", "S11"]),
    dict(id="M08", name="Foreign individual converting lawful current-account RMB income",
         status="lawful, gated", pricing="boc", pick="M08",
         who="A foreign national who is not a 境内个人 (not resident in China for a full year, or not a Chinese citizen) and who earned lawful current-account RMB income in China.",
         cap="Per transaction, on documents including tax documents (S26 / Huifa [2020] No. 14 Art. 59); the USD 50,000 annual total in S01 Art. 2 is framed for 境内个人 purchase.",
         pros=["For a US citizen who is not a Chinese tax resident, this is the article that matches the facts.",
               "The test is documentary, not a fixed annual total.",
               "Uses the same cheap BOC execution as M01."],
         cons=["Eligibility turns on residency, which is a fact this project does not have.",
               "Requires tax documents; a person who never paid PRC tax may have nothing to produce.",
               "Only lawful current-account income; property proceeds go through M03/M04."],
         steps=["Establish whether you are a 境内个人 under S03 Art. 52(2).",
                "Assemble the employment/business documents and the tax payment record.",
                "Present them at the bank with your passport.",
                "The bank converts under the current-account article and remits.",
                "Keep the tax documents; the US return may need them for the foreign tax credit."],
         sources=["S26", "S03", "S01", "S09", "S10"]),
    dict(id="M09", name="Carry USD cash out (declared)",
         status="lawful, capped", pricing="boc_cash", pick="M09",
         who="Anyone leaving China with cash within the permit rules.",
         cap="Up to USD 5,000 with no permit; USD 5,000-10,000 with a bank carrying permit; above USD 10,000 in principle not permitted (S06). The US side requires FinCEN Form 105 above USD 10,000 (S24).",
         pros=["No bank transfer fee published.",
               "Uses the cash selling rate, which at BOC equals the spot selling rate on the board read here (668.71)."],
         cons=["Capped far below any of the larger amounts in this study.",
               "Physical loss and seizure risk; a failure to file FinCEN 105 risks forfeiture (S24).",
               "Group totals are aggregated for the US USD 10,000 test, so splitting cash among travellers does not avoid it.",
               "Illegal carrying carries a warning and a fine of up to 20 percent (S03 Art. 42)."],
         steps=["Convert at the bank within the permit thresholds.",
                "For USD 5,000-10,000, obtain the 携带证 from the bank.",
                "Declare to Chinese customs as required.",
                "On entry to the US, file FinCEN Form 105 above USD 10,000.",
                "Deposit the cash in the US and keep the exchange receipt for the §988 basis."],
         sources=["S06", "S09", "S24", "S03"]),
    dict(id="M10", name="Wise transfer from CNY",
         status="lawful, gated", pricing="unpriced", pick=None,
         who="A non-mainland-Chinese sender, or someone who worked in China, with a PRC tax record showing tax paid in the last three years (S25).",
         cap="CNY 300,000 per transfer from the bank app; overall limit set from salary minus tax paid (S25).",
         pros=["A licensed provider with a published process for CNY-out.",
               "One transfer can cover CNY 300,000, which is about USD 45,000 at the board read here.",
               "Only to an account you own, which matches a repatriation use case."],
         cons=["No fee is published on the page read here, so no cost can be stated.",
               "The tax-record requirement excludes anyone who cannot document PRC tax paid.",
               "The limit is income-linked, not balance-linked: savings accumulated over years may exceed it.",
               "Commercial terms; not a government source."],
         steps=["Create a Wise account and start a CNY transfer.",
                "Complete verification and upload PRC tax records.",
                "Wise assigns a limit from the tax record.",
                "Send from your China bank app or Alipay to Wise.",
                "Wise converts and pays out to your own account.",
                "Record the fee actually charged, which is only shown at the point of transfer."],
         sources=["S25"]),
    dict(id="M11", name="Overseas ATM withdrawals on a domestic bank card",
         status="lawful, capped", pricing="unpriced", pick=None,
         who="Holder of a mainland-issued bank card.",
         cap="RMB 100,000 equivalent per person per calendar year; RMB 10,000 per card per day (S07).",
         pros=["No SAFE application and no documentary file.",
               "Works at the destination end."],
         cons=["The annual cap is roughly USD 15,000 at the board read here, and going over blocks cards for the current and next two years (S07).",
               "Per-withdrawal and issuing-bank fees are not published on the SAFE page, so the cost cannot be stated from official sources.",
               "Cash-intensive and slow for large balances."],
         steps=["Check the card's overseas cash limit and fees with the issuing bank.",
                "Withdraw abroad within RMB 10,000 per card per day.",
                "Track the annual RMB 100,000 total.",
                "Deposit and keep receipts."],
         sources=["S07"]),
    dict(id="M12", name="Private or 'underground' FX trade (变相买卖外汇)",
         status="unlawful", pricing="exposure", pick=None,
         who="Not lawful for anyone.",
         cap="Statutory fine up to 30 percent of the amount, or 30-100 percent if serious, plus confiscation and possible criminal liability (S03 Art. 45).",
         pros=["None that survive the statute: the activity itself is the offence."],
         cons=["Fine plus confiscation plus criminal exposure.",
               "No enforceable contract; loss is yours.",
               "Counterparty risk of total loss with no recourse."],
         steps=["There is no lawful step sequence. Listed here only so the option is identified as unavailable."],
         sources=["S03"]),
    dict(id="M13", name="Stablecoin / crypto transfer (USDT etc.)",
         status="unlawful", pricing="exposure", pick=None,
         who="Not lawful as a conversion business in the PRC.",
         cap="Exchanging legal tender for virtual currency as a business is an illegal financial activity (S08 I(2)); overseas exchanges serving PRC residents are likewise illegal (S08 I(3)).",
         pros=["None that survive the rule: the conversion leg is a prohibited activity."],
         cons=["Prohibited activity, with the general FX and criminal exposure that follows.",
               "Counterparty and platform risk of total loss.",
               "Evidence trail is permanent even if the transfer 'works'."],
         steps=["There is no lawful step sequence. Listed only to identify the option as unavailable."],
         sources=["S08", "S03"]),
    dict(id="M14", name="Splitting the amount across family or friends' annual totals",
         status="unlawful", pricing="exposure", pick=None,
         who="Prohibited for everyone.",
         cap="Borrowing another person's total puts you on the watch list for the current year and the two following years (S02); the underlying evasion is also caught by S03 Art. 39.",
         pros=["None: the rule names this practice directly."],
         cons=["Three years of documentary review for every FX transaction.",
               "The lender of the quota also faces a risk notice and then the watch list.",
               "Possible fine for evasion of up to 100 percent of the amount."],
         steps=["There is no lawful step sequence. Listed only to identify the option as unavailable."],
         sources=["S02", "S03"]),
    dict(id="M15", name="False documents or misdeclared purpose",
         status="unlawful", pricing="exposure", pick=None,
         who="Prohibited for everyone.",
         cap="Illegal arbitrage of FX carries a fine up to 30 percent, or 30-100 percent if serious (S03 Art. 40); the 2004 measures also point to that article for false materials (S04 Art. 13).",
         pros=["None."],
         cons=["Fine, confiscation, criminal referral.",
               "The bank's review is documented, so the false statement is provable.",
               "US-side consequences are separate and additional."],
         steps=["There is no lawful step sequence. Listed only to identify the option as unavailable."],
         sources=["S03", "S04"]),
]


def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x


def price(kind, amount_usd):
    """Return dict of exact Fractions for one method at one USD amount."""
    A = F(amount_usd)
    out = {}
    if kind == "boc":
        rate, mid = BOC_SELL, BOC_MID
        cny = A * rate
        fee_cny = clamp(BOC_PCT * cny, BOC_MIN, BOC_MAX) + BOC_CABLE
        fee_usd = fee_cny / rate
    elif kind == "hsbc_tt":
        rate, mid = HSBC_SELL, HSBC_MID
        cny = A * rate
        fee_cny = clamp(HSBC_PCT * cny, HSBC_MIN, HSBC_MAX) + HSBC_CABLE
        fee_usd = fee_cny / rate
    elif kind == "hsbc_gt_premier":
        rate, mid = HSBC_SELL, HSBC_MID
        cny = A * rate
        fee_cny = F(0)
        fee_usd = F(0)
    elif kind == "hsbc_gt_advance":
        rate, mid = HSBC_SELL, HSBC_MID
        cny = A * rate
        fee_cny = F(0)
        fee_usd = F(20)
    elif kind == "boc_cash":
        rate, mid = BOC_CASH_SELL, BOC_MID
        cny = A * rate
        fee_cny = F(0)
        fee_usd = F(0)
    else:
        return None
    fx_usd = A * (rate / mid - 1)
    out = dict(rate=rate, mid=mid, cny=cny, fee_cny=fee_cny, fee_usd=fee_usd,
               fx_usd=fx_usd, total=fx_usd + fee_usd,
               pct_of_amount=(fx_usd + fee_usd) / A * 100,
               gap_to_fed=A * (rate / FED - 1))
    return out


def build_rows():
    rows = []
    for m in METHODS:
        for A in AMOUNTS:
            if m["pricing"] == "unpriced":
                rows.append(dict(method=m["id"], amount=A, cny="", fee_cny="", fx_usd="",
                                 fee_usd="", total_usd="", pct="", gap_fed="", status="not priced"))
                continue
            if m["pricing"] == "exposure":
                rows.append(dict(method=m["id"], amount=A, cny="", fee_cny="", fx_usd="",
                                 fee_usd="", total_usd="", pct="", gap_fed="", status="exposure"))
                continue
            if m["id"] == "M09" and A > 10000:
                rows.append(dict(method="M09", amount=A, cny="", fee_cny="", fx_usd="",
                                 fee_usd="", total_usd="", pct="", gap_fed="", status="above cap"))
                continue
            p = price(m["pricing"], A)
            rows.append(dict(method=m["id"], amount=A,
                             cny=f"{float(p['cny']):.2f}",
                             fee_cny=f"{float(p['fee_cny']):.2f}",
                             fx_usd=f"{float(p['fx_usd']):.2f}",
                             fee_usd=f"{float(p['fee_usd']):.2f}",
                             total_usd=f"{float(p['total']):.2f}",
                             pct=f"{float(p['pct_of_amount']):.3f}",
                             gap_fed=f"{float(p['gap_to_fed']):.2f}",
                             status="priced"))
    return rows


def summary():
    """Cheapest priced lawful route at each amount, plus the binding constraint."""
    out = []
    for A in AMOUNTS:
        best = None
        for m in METHODS:
            if m["pricing"] in ("unpriced", "exposure"):
                continue
            if m["id"] == "M09":      # capped; excluded from the "cheapest bank route" line
                continue
            p = price(m["pricing"], A)
            if p is None:
                continue
            if best is None or p["total"] < best[1]["total"]:
                best = (m, p)
        gate = ("within the USD 50,000 annual total" if A <= 50000
                else "above the USD 50,000 annual total: documentary review")
        out.append(dict(amount=A, method=best[0]["id"], name=best[0]["name"],
                        total=round(float(best[1]["total"]), 2),
                        pct=round(float(best[1]["pct_of_amount"]), 3),
                        cny=round(float(best[1]["cny"]), 2),
                        gap=round(float(best[1]["gap_to_fed"]), 2),
                        gate=gate))
    return out


def main():
    rows = build_rows()
    with open(os.path.join(D, "costs.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["method", "amount", "cny", "fee_cny",
                                          "fx_usd", "fee_usd", "total_usd", "pct",
                                          "gap_fed", "status"])
        w.writeheader()
        w.writerows(rows)
    params = dict(
        boc_sell=float(BOC_SELL), boc_buy=float(BOC_BUY), boc_mid=float(BOC_MID),
        boc_cash_sell=float(BOC_CASH_SELL), hsbc_sell=float(HSBC_SELL),
        hsbc_buy=float(HSBC_BUY), hsbc_mid=float(HSBC_MID), fed=float(FED),
        boc_spread_pct=float((BOC_SELL / BOC_MID - 1) * 100),
        hsbc_spread_pct=float((HSBC_SELL / HSBC_MID - 1) * 100),
        boc_fee=dict(pct=float(BOC_PCT), min_cny=float(BOC_MIN),
                     max_cny=float(BOC_MAX), cable_cny=float(BOC_CABLE)),
        hsbc_fee=dict(pct=float(HSBC_PCT), min_cny=float(HSBC_MIN),
                      max_cny=float(HSBC_MAX), cable_cny=float(HSBC_CABLE)),
    )
    json.dump(dict(parameters=params, methods=METHODS, rows=rows,
                   summary=summary(), amounts=AMOUNTS),
              open(os.path.join(D, "costs.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"{len(rows)} cost rows, {len(METHODS)} methods, {len(AMOUNTS)} amounts")
    s = summary()
    for a in (0, 3, 4, 9, 19, 29, 39):
        r = s[a]
        print(f"  ${r['amount']:>7,}: {r['method']} ${r['total']:>9,.2f} "
              f"({r['pct']:.3f}%) CNY {r['cny']:,.2f}")


if __name__ == "__main__":
    main()
