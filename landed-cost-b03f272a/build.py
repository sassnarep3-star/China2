#!/usr/bin/env python3
"""Build the landed-cost-b03f272a section (session arena/b03f272a-china2).

Reads data/sources.json, data/inputs.json, data/routes.json, data/flags.json and data/audit.json and
writes the static pages, the model exports (data/model.json, data/*.csv) and EXECUTIVE_SUMMARY.md.

Rules this generator enforces by construction:
  * a number is printed only if it is quoted in the source ledger or is arithmetic on such numbers;
  * a value with no official source is printed as an empty cell with a flag link (class "blank");
  * every body row of every table carries at least one direct link to an official page.
Output is deterministic: no clock, no network, no randomness.
"""
import csv
import html
import io
import json
from decimal import Decimal as D, ROUND_CEILING, ROUND_HALF_UP
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


SOURCES = load("sources.json")["sources"]
SRC = {s["id"]: s for s in SOURCES}
IN = load("inputs.json")
ROUTEDATA = load("routes.json")
ROUTES = ROUTEDATA["routes"]
GROUPS = ROUTEDATA["groups"]
FLAGLIST = load("flags.json")["flags"]
FLAGS = {f["id"]: f for f in FLAGLIST}
AUDIT = load("audit.json")

AS_OF = IN["as_of"]
TIERS = list(range(IN["tiers"]["from"], IN["tiers"]["to"] + 1, IN["tiers"]["step"]))

# ----------------------------------------------------------------------------------------------
# Model: arithmetic on published inputs only
# ----------------------------------------------------------------------------------------------
SELL = D(IN["boc_sell_per_100"]["v"]) / 100        # RMB the customer pays per USD bought
BUY = D(IN["boc_buy_per_100"]["v"]) / 100
MID = (SELL + BUY) / 2                             # mid-point of the bank's own two prices
MARGIN_PER_USD = SELL - MID                        # RMB per USD: what the selling price adds to the mid
MARGIN_PCT = (MARGIN_PER_USD / MID * 100)

BW = {k: D(IN["boc_wire"][k]) for k in ("pct", "min", "max", "cable")}
HT = {k: D(IN["hsbc_tt"][k]) for k in ("pct", "min", "max", "cable", "pay_exact")}
HSBC_GT_ADV = D(IN["hsbc_gt_advance_usd"]["v"])
HSBC_EDU_ADV = D(IN["hsbc_edu_advance_usd"]["v"])
WISE_MAX = D(IN["wise_max_cny"]["v"])
QUOTA = int(IN["quota_usd"]["v"])
ATM_YEAR = D(IN["atm_year_cny"]["v"])
ATM_DAY = D(IN["atm_day_cny"]["v"])
CASH_FREE = D(IN["cash_usd_free"]["v"])
CASH_PERMIT = D(IN["cash_usd_permit"]["v"])
CASH_RMB = D(IN["cash_rmb_trip"]["v"])
RECONV_DAY = D(IN["reconv_day_usd"]["v"])
FINE = D(IN["prc_fine_pct"]["v"])
FINE_SERIOUS = D(IN["prc_fine_serious_pct"]["v"])
FINE_CARRY = D(IN["prc_carry_fine_pct"]["v"])
FBAR_TH = int(IN["fbar_threshold"]["v"])
FBAR_NW = int(IN["fbar_nonwillful"]["v"])
FBAR_W = int(IN["fbar_willful_floor"]["v"])
FBAR_W_PCT = D(IN["fbar_willful_pct"]["v"])
F8938 = [("U.S., not joint", int(IN["f8938_us_single"]["v"])), ("U.S., joint", int(IN["f8938_us_joint"]["v"])),
         ("abroad, not joint", int(IN["f8938_abroad_single"]["v"])), ("abroad, joint", int(IN["f8938_abroad_joint"]["v"]))]
F3520_TH = int(IN["f3520_threshold"]["v"])
F3520_PCT = D(IN["f3520_max_pct"]["v"])
SDO_PCT = D(IN["sdo_pct"]["v"])
EXCL = int(IN["gain_exclusion_usd"]["v"])
YEARS = sorted(IN["fed_g5a"].keys(), reverse=True)          # newest first: most relevant first
RATE = {y: D(IN["fed_g5a"][y]["v"]) for y in YEARS}
RATE_SRC = {y: IN["fed_g5a"][y]["src"] for y in YEARS}
IRS_AVG = {y: v for y, v in IN["irs_avg"].items() if y != "src"}
G5_SRCS = sorted(set(RATE_SRC.values()))


def q2(x):
    return D(x).quantize(D("0.01"), rounding=ROUND_HALF_UP)


def q0(x):
    return int(D(x).quantize(D("1"), rounding=ROUND_HALF_UP))


def q3(x):
    return D(x).quantize(D("0.001"), rounding=ROUND_HALF_UP)


def ceil_div(a, b):
    return int((D(a) / D(b)).to_integral_value(rounding=ROUND_CEILING))


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def boc(usd):
    """Bank of China: buy `usd` at the published selling rate and send it in one wire."""
    usd = D(usd)
    principal = q2(usd * SELL)
    fee = q2(clamp(principal * BW["pct"], BW["min"], BW["max"])) + BW["cable"]
    margin = q2(usd * MARGIN_PER_USD)
    total_cny = fee + margin
    total_usd = q2(total_cny / SELL)
    return {"principal_cny": principal, "fee_cny": fee, "margin_cny": margin, "total_cny": total_cny,
            "total_usd": total_usd, "pct": q3(total_usd / usd * 100), "debit_cny": principal + fee,
            "margin_usd": q2(margin / SELL), "fee_usd": q2(fee / SELL)}


def hsbc_tt(usd):
    """HSBC China Premier/Advance wire charges. RMB equivalents use the BOC selling rate (flag F02)."""
    usd = D(usd)
    issue = q2(clamp(usd * SELL * HT["pct"], HT["min"], HT["max"]))
    fee = issue + HT["cable"]
    fee_usd = q2(fee / SELL)
    return {"issue_cny": issue, "cable_cny": HT["cable"], "fee_cny": fee, "fee_usd": fee_usd,
            "pct": q3(fee_usd / usd * 100), "with_exact_usd": q2((fee + HT["pay_exact"]) / SELL)}


def quota(usd):
    """USD 50,000 a year: one BOC wire per calendar year."""
    years = ceil_div(usd, QUOTA)
    chunks = [QUOTA] * (years - 1) + [usd - QUOTA * (years - 1)]
    fee = sum((boc(c)["fee_cny"] for c in chunks), D("0"))
    margin = q2(D(usd) * MARGIN_PER_USD)
    total_usd = q2((fee + margin) / SELL)
    return {"years": years, "fee_cny": fee, "margin_cny": margin, "total_usd": total_usd,
            "pct": q3(total_usd / D(usd) * 100)}


def us_exposure(bal):
    """U.S. reporting position for an unreported balance `bal` (USD)."""
    fbar = bal > FBAR_TH
    return {"fbar": fbar,
            "sfo": 0,
            "sdo": q0(D(bal) * SDO_PCT / 100),
            "nonwillful": FBAR_NW if fbar else None,
            "willful": max(FBAR_W, q0(D(bal) * FBAR_W_PCT / 100)) if fbar else None,
            "f8938": [name for name, th in F8938 if bal > th],
            "f3520": q0(D(bal) * F3520_PCT / 100) if bal > F3520_TH else None}


def gain_fraction(year):
    return 1 - SELL / RATE[year]


def gain(usd, year):
    return q0(D(usd) * gain_fraction(year))


def build_model():
    rows = []
    for t in TIERS:
        b, h, qd = boc(t), hsbc_tt(t), quota(t)
        cny = D(t) * SELL
        rows.append({
            "tier": t,
            "boc": {k: str(v) for k, v in b.items()},
            "hsbc_tt": {k: str(v) for k, v in h.items()},
            "hsbc_gt": {"premier_usd": "0.00", "advance_usd": str(q2(HSBC_GT_ADV)), "advance_pct": str(q3(HSBC_GT_ADV / D(t) * 100))},
            "quota": {k: (v if isinstance(v, int) else str(v)) for k, v in qd.items()},
            "wise_transfers": ceil_div(cny, WISE_MAX),
            "atm_years": ceil_div(cny, ATM_YEAR), "atm_days": ceil_div(cny, ATM_DAY),
            "cash_trips_free": ceil_div(t, CASH_FREE), "cash_trips_permit": ceil_div(t, CASH_PERMIT),
            "rmb_trips": ceil_div(cny, CASH_RMB),
            "reconv_days": ceil_div(t, RECONV_DAY),
            "fine30": q0(D(t) * FINE / 100), "fine100": q0(D(t) * FINE_SERIOUS / 100), "fine20": q0(D(t) * FINE_CARRY / 100),
            "us": us_exposure(t),
            "gain": {y: gain(t, y) for y in YEARS},
        })
    return {"as_of": AS_OF, "sell": str(SELL), "buy": str(BUY), "mid": str(MID), "margin_per_usd": str(MARGIN_PER_USD),
            "margin_pct": str(q3(MARGIN_PCT)), "gain_pct": {y: str(q2(gain_fraction(y) * 100)) for y in YEARS},
            "rows": rows}


MODEL = build_model()
ROW = {r["tier"]: r for r in MODEL["rows"]}

# ----------------------------------------------------------------------------------------------
# HTML helpers
# ----------------------------------------------------------------------------------------------
NAV = [("index.html", "Summary"), ("routes.html", "Methods"), ("costs.html", "Costs"),
       ("penalty.html", "Conversion penalty"), ("fx-gain.html", "Exchange gain"), ("steps.html", "Step by step"),
       ("audit.html", "Repo review"), ("flagged.html", "Flagged for Review"), ("sources.html", "Sources")]


def esc(s):
    return html.escape(str(s), quote=True)


def usd(x, cents=True):
    x = D(str(x))
    sign = "−" if x < 0 else ""
    x = abs(x)
    return sign + ("${:,.2f}".format(x) if cents else "${:,.0f}".format(x))


def cny(x):
    return "¥{:,.2f}".format(D(str(x)))


def S(*ids, short=False):
    """Direct links to the official pages behind a row."""
    out = []
    for i in ids:
        s = SRC[i]
        if short:   # dense $10,000-step tables: keep each row small
            out.append('<a class="src" href="%s">%s</a>' % (esc(s["url"]), i))
        else:
            out.append('<a class="src" href="%s" target="_blank" rel="noopener noreferrer" title="%s">%s</a>' % (
                esc(s["url"]), esc(s["publisher"] + " — " + s["title"]), i))
    return "".join(out)


def FL(*ids):
    return "".join('<a class="flag" href="flagged.html#%s" title="%s">%s</a>' % (i, esc(FLAGS[i]["item"]), i) for i in ids)


def FLs(fid):
    """Compact flag link for dense tables."""
    return '<a class="flag" href="flagged.html#%s">%s</a>' % (fid, fid)


class Blank(str):
    """Marker for an empty, flagged cell."""


def BL(fid):
    return Blank(fid)


def chip(text, kind):
    return '<span class="chip %s">%s</span>' % (kind, esc(text))


STATUS_CHIP = {"lawful": ("Lawful", "ok"), "conditional": ("Lawful if you qualify", "info"), "capped": ("Lawful, capped", "info"),
               "needs review": ("Needs review", "warn"), "do not use": ("Unlawful — do not use", "bad")}


def table(caption, cols, rows, cls="", small="", tid=""):
    """cols: list of (header, cell class). rows: list of (tr attributes, cells). A cell is inner HTML or BL(flag)."""
    dense = "wide" in cls.split()
    head = "".join('<th scope="col"%s>%s</th>' % (' class="%s"' % c if c and not dense else "", esc(h)) for h, c in cols)
    body = []
    for attrs, cells in rows:
        tds = []
        for (h, c), cell in zip(cols, cells):
            if isinstance(cell, Blank):
                label = "" if dense else ' data-label="%s"' % esc(h)
                tds.append('<td class="blank"%s><span class="vh">blank, unverified: </span>%s</td>' % (label, FLs(str(cell)) if dense else FL(str(cell))))
            elif dense:
                tds.append("<td>%s</td>" % cell)
            else:
                tds.append('<td%s data-label="%s">%s</td>' % (' class="%s"' % c if c else "", esc(h), cell))
        body.append("<tr%s>%s</tr>" % ((" " + attrs) if attrs else "", "".join(tds)))
    # The visible title sits above the scroll box so that it never scrolls sideways with a wide table.
    cap = '<div class="cap"><strong>%s</strong>%s</div>' % (esc(caption), "<small>%s</small>" % small if small else "")
    return '<div class="tblock">%s<div class="tw"><table%s%s><caption class="vh">%s</caption><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div></div>' % (
        cap, ' id="%s"' % tid if tid else "", ' class="%s"' % cls if cls else "", esc(caption), head, "\n".join(body))


def shell(page, title, body, lead="", script_model=False):
    nav = "".join('<a href="%s"%s>%s</a>' % (u, ' aria-current="page"' if u == page else "", esc(t)) for u, t in NAV)
    model_json = ""
    if script_model:
        js = {"sell": float(SELL), "mid": float(MID), "exclusion": EXCL,
              "boc": {k: float(v) for k, v in BW.items()}, "years": {y: float(RATE[y]) for y in YEARS}}
        model_json = '<script type="application/json" id="model">%s</script>' % json.dumps(js, sort_keys=True)
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s · China money: landed cost</title>
<meta name="description" content="Source-linked cost of moving yuan from a mainland China bank account into U.S. dollars: bank fees, exchange-rate margin, U.S. exchange-gain tax and reporting penalties at every $10,000 step to $400,000.">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top"><div class="top-in">
<a class="brand" href="index.html">China money <small>· what it costs</small></a>
<nav class="nav" aria-label="Sections">%s<a href="../index.html">All project sites</a></nav>
</div></header>
<main id="main">
<p class="asof">Prices and sources as of %s</p>
<h1>%s</h1>
%s
<p class="legend"><span class="src">S16</span> opens the official page behind a figure · <span class="flag">F01</span> marks something not confirmed, explained under <a href="flagged.html">Flagged for Review</a></p>
%s
<details class="terms"><summary>Terms used on this site</summary><div class="pad"><ul class="tight">
<li><strong>Yuan, CNY, RMB, ¥</strong>: the same currency. <strong>$</strong> and USD: U.S. dollars.</li>
<li><strong>SAFE</strong>: State Administration of Foreign Exchange, China's currency regulator. <strong>PBOC</strong>: People's Bank of China, the central bank.</li>
<li><strong>Non-domestic individual</strong> (境外个人): the exchange rules' term for a foreign individual. Under the Regulations a foreigner who has lived in China continuously for a year counts as a domestic individual; see flag <a href="flagged.html#F07">F07</a>.</li>
<li><strong>Exchange-rate margin</strong>: how much worse the bank's price is than the mid-point between its own buying and selling prices.</li>
<li><strong>FBAR</strong>: the yearly U.S. report of foreign accounts (FinCEN Form 114). <strong>Form 8938</strong>: statement of foreign financial assets attached to the tax return. <strong>Form 3520</strong>: report of large foreign gifts or bequests.</li>
<li><strong>Streamlined procedures</strong>: the IRS route for fixing non-willful failures to report foreign accounts and income.</li>
</ul></div></details>
</main>
<footer>Research for one question, not personal tax or legal advice. No bank was contacted, no money was moved and no return was filed.
Every table row links to the official page it rests on; an empty hatched cell means the value could not be confirmed and is listed under
<a href="flagged.html">Flagged for Review</a>. Built by <code>build.py</code> from <code>data/*.json</code> · session <code>arena/b03f272a-china2</code>.</footer>
%s<script src="assets/app.js" defer></script>
</body>
</html>
""" % (esc(title), nav, esc(AS_OF), esc(title), ('<p class="lead">%s</p>' % lead) if lead else "", body, model_json)


def tier_picker():
    opts = "".join('<option value="%d"%s>$%s</option>' % (t, " selected" if t == 100000 else "", "{:,}".format(t)) for t in TIERS)
    return ('<div class="tool"><label>Highlight an amount in the tables<select id="pick-amount">%s</select></label>'
            '<span class="note">Works without JavaScript too: every amount from $10,000 to $400,000 is a row.</span></div>' % opts)


def li(items):
    return '<ul class="tight">%s</ul>' % "".join("<li>%s</li>" % esc(i) for i in items) if items else ""


# ----------------------------------------------------------------------------------------------
# Derived facts used in prose (always computed, never typed)
# ----------------------------------------------------------------------------------------------
GAIN_PCT = {y: q2(gain_fraction(y) * 100) for y in YEARS}
LOSS_YEARS = sorted(y for y in YEARS if GAIN_PCT[y] < 0)
GAIN_YEARS = sorted(y for y in YEARS if GAIN_PCT[y] > 0)
MAX_GAIN_Y = max(YEARS, key=gain_fraction)        # unrounded, so ties in the rounded figure do not matter
MIN_GAIN_Y = min(YEARS, key=gain_fraction)
RECENT = ["2025", "2024", "2023"]
REC_LO = min(RECENT, key=lambda y: GAIN_PCT[y])
REC_HI = max(RECENT, key=lambda y: GAIN_PCT[y])
B10, B100, B400 = boc(10000), boc(100000), boc(400000)
H10, H400 = hsbc_tt(10000), hsbc_tt(400000)
FORTY_SMALL = B10["fee_cny"] * 40


def pct(x, places=2):
    return ("{:.%df}%%" % places).format(D(str(x)))


def year_runs(years):
    """['2011','2012','2013','2016'] -> '2011–2013, 2016'."""
    ys = sorted(int(y) for y in years)
    runs, start, prev = [], None, None
    for y in ys:
        if start is None:
            start = prev = y
        elif y == prev + 1:
            prev = y
        else:
            runs.append((start, prev))
            start = prev = y
    if start is not None:
        runs.append((start, prev))
    return ", ".join(str(a) if a == b else "%d–%d" % (a, b) for a, b in runs)


# ----------------------------------------------------------------------------------------------
# Page: summary (landing)
# ----------------------------------------------------------------------------------------------
def page_index():
    g_lo, g_hi = gain(100000, REC_LO), gain(100000, REC_HI)
    kpis = """<div class="kpis">
<div class="kpi"><b>%s</b><span>Bank cost of one $100,000 wire at Bank of China (%s of the amount): wire fee plus exchange-rate margin.</span><div class="srcs">%s</div></div>
<div class="kpi"><b>%s</b><span>Yuan per dollar: Bank of China's published selling price, %s.</span><div class="srcs">%s</div></div>
<div class="kpi"><b>%s to +%s</b><span>Exchange loss or gain as a share of the amount, by the year the yuan was received (%s to %s). Only a gain is taxed in the U.S.</span><div class="srcs">%s</div></div>
<div class="kpi"><b>$0 · 5%% · up to 50%%</b><span>U.S. penalty if the account was never reported: streamlined filing from abroad · streamlined filing in the U.S. · willful ceiling per year.</span><div class="srcs">%s</div></div>
</div>""" % (usd(B100["total_usd"]), pct(B100["pct"], 3), S("S16", "S19"),
             SELL, esc(IN["boc_pub_time"]["v"]), S("S16"),
             pct(GAIN_PCT[MIN_GAIN_Y]).replace("-", "−"), pct(GAIN_PCT[MAX_GAIN_Y]), YEARS[-1], YEARS[0], S("S16", "S23", "S29"),
             S("S46", "S45", "S40"))

    rows = [
        ("", ["1", "The wire is not what gets taxed. What is taxed is the income when it was earned and, in the U.S., any exchange gain when the yuan is converted.",
              "A U.S. citizen is taxed on worldwide income wherever the money sits. A Chinese bank converts a non-domestic individual's income against documents that include tax certificates. %s" % FL("F29"),
              S("S35", "S30", "S01")]),
        ("", ["2", "Cheapest lawful route: buy dollars at the bank against documents and send one wire to your own U.S. account (route A1).",
              "%s on $10,000 (%s) · %s on $100,000 (%s) · %s on $400,000 (%s) at Bank of China's published prices. Receiving-bank charges are extra. %s" % (
                  usd(B10["total_usd"]), pct(B10["pct"], 3), usd(B100["total_usd"]), pct(B100["pct"], 3), usd(B400["total_usd"]), pct(B400["pct"], 3), FL("F01", "F03")),
              S("S16", "S19", "S01")]),
        ("", ["3", "Send one wire, not many. The fee is capped per wire, and splitting to get round a limit is prohibited.",
              "One $400,000 wire: %s in fees. Forty $10,000 wires: %s. The exchange-rate margin is the same either way. %s" % (
                  cny(B400["fee_cny"]), cny(FORTY_SMALL), FL("F27")),
              S("S19", "S05")]),
        ("", ["4", "No $50,000 ceiling applies to documented income of a non-domestic individual. The ceiling is your paperwork.",
              "The $50,000 yearly facility belongs to domestic individuals and holders of a Foreign Permanent Resident ID. Above it, or outside it, the bank converts what the source and tax documents support. %s" % FL("F07"),
              S("S01", "S04", "S02")]),
        ("", ["5", "The U.S. tax on conversion is the exchange gain since you received the yuan. It depends on the year.",
              "Yuan received in %s: a gain of %s to %s of the amount, i.e. %s to %s per $100,000, or %s to %s of tax at the 15%% long-term rate — more than the bank charges. Yuan received in %s converts at a loss: no gain to tax. %s" % (
                  year_runs(RECENT), pct(GAIN_PCT[REC_LO]), pct(GAIN_PCT[REC_HI]), usd(g_lo, False), usd(g_hi, False),
                  usd(q0(D(g_lo) * 15 / 100), False), usd(q0(D(g_hi) * 15 / 100), False), year_runs(LOSS_YEARS), FL("F14", "F16")),
              S("S30", "S31", "S32", "S23")]),
        ("", ["6", "Penalties come from an unreported account, not from the transfer.",
              "Reports filed every year: $0. Not filed, non-willful, living abroad: $0 penalty through the streamlined foreign procedure. Living in the U.S.: 5%% of the highest year-end balance (%s per $100,000). Outside those procedures: up to %s per missed yearly report, and for willful cases the greater of %s or 50%% of the balance per year. %s" % (
                  usd(us_exposure(100000)["sdo"], False), usd(FBAR_NW, False), usd(FBAR_W, False), FL("F22", "F20")),
              S("S38", "S46", "S45", "S39", "S40")]),
        ("", ["7", "Do not use other people's quotas, underground or private swaps, crypto, or false documents.",
              "Chinese fine of up to 30%% of the amount (%s on $100,000), 30%% up to the full amount in serious cases, and criminal liability." % usd(ROW[100000]["fine30"], False),
              S("S06", "S05", "S13")]),
    ]
    t1 = table("The answer in seven lines", [("#", "n"), ("Finding", "key"), ("In numbers", ""), ("Official sources", "")], rows, cls="stack",
               small="Each line is supported by the pages linked in its last column. Hatched flags mark what is still unconfirmed.")

    fit = [
        ("", ["Salary or fees earned in China, Chinese tax paid", "A1 Bank of China or A2–A4 HSBC China; A5 Wise if your tax records are from the last 3 years",
              "Passport, contract and pay records, Chinese tax payment record", S("S01", "S04", "S21")]),
        ("", ["Sale of your home in mainland China", "C1 property-sale route, then one wire", "Sale contract, tax-paid certificate for the transfer, foreign-exchange purchase application", S("S12")]),
        ("", ["Inheritance from a relative in China", "C2 inheritance route (SAFE approval), then one wire; U.S. Form 3520 if over $100,000",
              "Inheritance and ownership documents, tax-payment certificate, passport", S("S10", "S11", "S43")]),
        ("", ["Assets you owned before you emigrated from China", "C3 emigrant-asset route (SAFE approval); lump sum allowed since 2014",
              "Proof that mainland residence was cancelled, ownership documents, tax-payment certificate", S("S10", "S11")]),
        ("", ["Foreign currency you brought in, exchanged into yuan and did not spend", "B5 change it back", "Original exchange memo, less than 24 months old", S("S03")]),
        ("", ["You cannot show where the money came from, or that Chinese tax was paid", "No lawful conversion route was found in the rules read. Get the tax and source records first; until then the money stays in China (D1).",
              "Tax payment records from the Chinese tax authority; contracts; bank history", S("S01", "S10")]),
    ]
    t2 = table("Which route fits your money?", [("Where the yuan came from", "key"), ("Route", ""), ("Documents to have", ""), ("Official sources", "")], fit, cls="stack")

    order = [
        ("", ["1", "Check your U.S. filings for the China account first: FBAR for every year the foreign accounts were over $10,000, Form 8938 if over its threshold, interest reported.",
              "If something is missing and it was not willful, the streamlined procedures cost $0 (abroad) or 5% (in the U.S.). They close once the IRS starts an examination.", S("S38", "S42", "S44", "S46", "S45")]),
        ("", ["2", "Assemble the Chinese paper trail for the whole amount: source of the money and Chinese tax paid.", "Without it the bank cannot convert; with it there is no fixed quota for a non-domestic individual.", S("S01", "S04")]),
        ("", ["3", "Work out the exchange gain before choosing the date: the dollar value of the yuan when you received it against today's rate.", "A loss year means no U.S. tax on conversion; a recent gain year means a gain taxed at 0%, 15% or 20% if it is a capital gain held over a year.", S("S30", "S31", "S32", "S22")]),
        ("", ["4", "Convert and send in one wire to your own U.S. account; keep the purchase slip and the wire receipt.", "Fee is capped per wire. Ask the receiving bank what it charges.", S("S19", "S20")]),
        ("", ["5", "Report the exchange gain on that year's return and keep filing the FBAR while any foreign account stays over $10,000.", "A gain of $200 or less on a personal transaction is not recognised.", S("S30", "S38")]),
    ]
    t3 = table("Order of work", [("Step", "n"), ("Do this", "key"), ("Why", ""), ("Official sources", "")], order, cls="stack")

    cards = """<div class="cards">
<a class="card" href="routes.html"><strong>Methods</strong><span>%d ways to get yuan into dollars: who each fits, limits, pros and cons. Unlawful ones are listed so you can recognise them.</span></a>
<a class="card" href="costs.html"><strong>Costs · $10,000 to $400,000</strong><span>Every method at every $10,000 step: fee, exchange-rate margin, number of transfers or years needed.</span></a>
<a class="card" href="penalty.html"><strong>Conversion penalty</strong><span>The layers that make up the "penalty", and U.S. reporting-penalty exposure at every $10,000 step.</span></a>
<a class="card" href="fx-gain.html"><strong>Exchange gain</strong><span>The taxable gain or loss for every year the yuan could have been received, 2001 to 2025.</span></a>
<a class="card" href="steps.html"><strong>Step by step</strong><span>Exact steps and documents for each lawful method.</span></a>
<a class="card" href="audit.html"><strong>Repo review</strong><span>%d checks of what the repository says against the official text, with file and line.</span></a>
<a class="card" href="flagged.html"><strong>Flagged for Review</strong><span>%d open items: every blank value and every statement that could not be confirmed.</span></a>
<a class="card" href="sources.html"><strong>Sources</strong><span>%d official pages read on %s, with the quoted passage and a direct link.</span></a>
</div>""" % (len(ROUTES), len(AUDIT["findings"]), len(FLAGLIST), len(SOURCES), esc(AS_OF))

    lead = ("The cheapest lawful way to turn yuan in a mainland account into dollars in the U.S. is a bank conversion and one wire, backed by proof of "
            "where the money came from and that Chinese tax was paid. On published prices that costs %s to %s of the amount. Tax is a separate matter: "
            "the U.S. taxes only the exchange gain since you received the yuan, and penalties arise only where the Chinese account was not reported."
            % (pct(B400["pct"], 2), pct(B10["pct"], 2)))
    body = kpis + t1 + "<h2>Find your case</h2>" + t2 + "<h2>What to do, in order</h2>" + t3 + "<h2>Go deeper</h2>" + cards + (
        '<div class="box warn"><strong>What this page does not know.</strong> Where the money came from, when you received it, where you live, '
        'what you have filed and which bank holds it. Nothing personal is assumed: where an answer depends on those facts, every case is shown '
        'side by side, and %d items are listed under <a href="flagged.html">Flagged for Review</a>.</div>' % len(FLAGLIST))
    return shell("index.html", "Getting yuan out of China and into dollars: what it costs", body, lead)


# ----------------------------------------------------------------------------------------------
# Page: methods
# ----------------------------------------------------------------------------------------------
def headline_value(r, t):
    m, row = r["model"], ROW[t]
    if m == "boc":
        return "%s (%s)" % (usd(row["boc"]["total_usd"]), pct(row["boc"]["pct"], 3))
    if m == "hsbc_tt":
        return "%s (%s)" % (usd(row["hsbc_tt"]["fee_usd"]), pct(row["hsbc_tt"]["pct"], 3))
    if m == "hsbc_gt":
        return "$0.00 / %s" % usd(row["hsbc_gt"]["advance_usd"])
    if m == "hsbc_pb":
        return "$0.00"
    if m == "wise":
        return "%d transfer%s" % (row["wise_transfers"], "" if row["wise_transfers"] == 1 else "s")
    if m == "quota50k":
        return "%d yr · %s" % (row["quota"]["years"], usd(row["quota"]["total_usd"]))
    if m == "atm":
        return "%d yr" % row["atm_years"]
    if m == "cash_usd":
        return "%d trips" % row["cash_trips_free"]
    if m == "cash_rmb":
        return "%d trips" % row["rmb_trips"]
    if m == "reconv":
        return "%d days" % row["reconv_days"]
    if m == "edu":
        return "$0.00 / %s" % usd(HSBC_EDU_ADV)
    if m == "zero":
        return "$0.00"
    if m == "fine30":
        return "up to %s" % usd(row["fine30"], False)
    if m == "fine20":
        return "up to %s" % usd(row["fine20"], False)
    return None


def page_routes():
    rows = []
    for r in ROUTES:
        lab, kind = STATUS_CHIP[r["status"]]
        hv = headline_value(r, 100000)
        cost = ("<strong>%s</strong><br><span class=\"small\">%s</span>" % (esc(hv), esc(r["headline"]))) if hv is not None else None
        flags = FL(*r["flags"]) if r["flags"] else ""
        cells = ['<strong id="%s">%s</strong> <a href="costs.html#%s">%s</a>' % (r["id"], r["id"], r["id"], esc(r["name"])),
                 chip(lab, kind), esc(r["fits"]), esc(r["limit"]),
                 cost if cost is not None else BL(r["flags"][0]),
                 li(r["pros"]) or "None.", li(r["cons"]),
                 S(*r["sources"]) + flags]
        rows.append(('data-group="%s"' % r["group"], cells))
    cols = [("Method", "key"), ("Status", ""), ("Fits", ""), ("Limit", ""), ("On $100,000", ""), ("For", ""), ("Against", ""), ("Official sources · flags", "")]
    filt = '<div class="filters" data-target="routes-table"><button type="button" data-group="all" aria-pressed="true">All %d</button>%s</div>' % (
        len(ROUTES), "".join('<button type="button" data-group="%s" aria-pressed="false">%s</button>' % (g, esc(name)) for g, name in GROUPS.items()))
    counts = {s: sum(1 for r in ROUTES if r["status"] == s) for s in STATUS_CHIP}
    kpis = '<div class="kpis">%s</div>' % "".join(
        '<div class="kpi"><b>%d</b><span>%s</span></div>' % (counts[s], esc(STATUS_CHIP[s][0])) for s in STATUS_CHIP if counts[s])
    lead = ("%d ways people use or consider to turn yuan in a mainland account into dollars abroad. Lawful ones come first, with who they fit, "
            "their limit and their published price on $100,000. The last group is unlawful: it is listed so the offers can be recognised and refused, "
            "with the penalty and no instructions." % len(ROUTES))
    body = kpis + filt + table("All methods", cols, rows, cls="stack", tid="routes-table",
                               small="Method codes link to the cost table for that method. Steps are on the Step by step page.") + (
        '<p class="note">Not evaluated and therefore not listed: Western Union, MoneyGram, Alipay or WeChat outward remittance, card purchases abroad, '
        'Stock Connect, Wealth Management Connect and QDII products. No official source for them was read. %s</p>' % FL("F28"))
    return shell("routes.html", "Methods: every way to turn yuan into dollars", body, lead)


# ----------------------------------------------------------------------------------------------
# Page: costs
# ----------------------------------------------------------------------------------------------
def n(x):
    return "{:,}".format(x)


# The official pages each method's figures are computed from (linked on every row of its table).
PRICE_SRC = {"A1": ("S16", "S19"), "A2": ("S20",), "A3": ("S20",), "A4": ("S20",), "A5": ("S21",), "A6": ("S14",),
             "B1": ("S04", "S16", "S19"), "B2": ("S07",), "B3": ("S08", "S16"), "B4": ("S09",), "B5": ("S03", "S16"), "B6": ("S20",),
             "C1": ("S12", "S16", "S19"), "C2": ("S10", "S16", "S19"), "C3": ("S11", "S16", "S19"), "D1": ("S38",), "D2": ("S17",),
             "E1": ("S05", "S06"), "E2": ("S06",), "E3": ("S13",), "E4": ("S06",), "E5": ("S06", "S50"), "E6": ("S07",)}


def detail_table(r):
    m = r["model"]
    src = S(*PRICE_SRC[r["id"]], short=True)
    rows = []
    for t in TIERS:
        row, amt = ROW[t], "<strong>$%s</strong>" % n(t)
        if m == "boc":
            b = row["boc"]
            cells = [amt, "<strong>%s</strong>" % usd(b["total_usd"]), pct(b["pct"], 3), cny(b["fee_cny"]), cny(b["margin_cny"]), cny(b["debit_cny"]), BL("F01"), src]
        elif m == "hsbc_tt":
            h = row["hsbc_tt"]
            cells = [amt, "<strong>%s</strong>" % usd(h["fee_usd"]), pct(h["pct"], 3), cny(h["issue_cny"]), cny(h["cable_cny"]), usd(h["with_exact_usd"]), BL("F02"), src]
        elif m == "hsbc_gt":
            g = row["hsbc_gt"]
            cells = [amt, "<strong>$0.00</strong>", "<strong>%s</strong>" % usd(g["advance_usd"]), pct(g["advance_pct"], 3), BL("F02"), src]
        elif m == "hsbc_pb":
            cells = [amt, "<strong>$0.00</strong>", BL("F02"), BL("F01"), src]
        elif m == "wise":
            cells = [amt, "<strong>%d</strong>" % row["wise_transfers"], cny(D(t) * SELL), BL("F05"), BL("F05"), src]
        elif m == "quota50k":
            qd = row["quota"]
            cells = [amt, "<strong>%d</strong>" % qd["years"], usd(qd["total_usd"]), pct(qd["pct"], 3), cny(qd["fee_cny"]), cny(qd["margin_cny"]), src]
        elif m == "atm":
            cells = [amt, "<strong>%d</strong>" % row["atm_years"], n(row["atm_days"]), cny(D(t) * SELL), BL("F08"), src]
        elif m == "cash_usd":
            cells = [amt, "<strong>%d</strong>" % row["cash_trips_free"], str(row["cash_trips_permit"]), usd(row["boc"]["margin_usd"]), src]
        elif m == "cash_rmb":
            cells = [amt, "<strong>%d</strong>" % row["rmb_trips"], cny(D(t) * SELL), BL("F30"), src]
        elif m == "reconv":
            cells = [amt, "<strong>%s</strong>" % n(row["reconv_days"]), usd(row["boc"]["margin_usd"]), src]
        elif m == "edu":
            cells = [amt, "<strong>$0.00</strong>", "<strong>%s</strong>" % usd(HSBC_EDU_ADV), BL("F02"), src]
        elif m == "zero":
            cells = [amt, "<strong>$0.00</strong>", "Yes" if row["us"]["fbar"] else "Only above $10,000", src]
        elif m == "fine30":
            cells = [amt, "<strong>%s</strong>" % usd(row["fine30"], False), usd(row["fine100"], False), "Yes", src]
        elif m == "fine20":
            cells = [amt, "<strong>%s</strong>" % usd(row["fine20"], False), "Yes, above $10,000", src]
        elif m == "fine_blank":
            cells = [amt, BL("F34"), "Yes", src]
        else:  # blank
            cells = [amt, BL(r["flags"][0]), src]
        rows.append(('data-tier="%d"' % t, cells))
    cols = {
        "boc": [("Amount sent", "n"), ("All-in bank cost", "n key"), ("% of amount", "n"), ("Wire fee", "n"), ("Rate margin", "n"), ("Yuan debited", "n"), ("Other banks' charges", ""), ("Sources", "")],
        "hsbc_tt": [("Amount sent", "n"), ("Bank charges", "n key"), ("% of amount", "n"), ("Issuance fee", "n"), ("Cable", "n"), ("With Pay Exact", "n"), ("HSBC rate margin", ""), ("Sources", "")],
        "hsbc_gt": [("Amount sent", "n"), ("Premier / Private Banking", "n key"), ("Advance", "n key"), ("Advance, % of amount", "n"), ("HSBC rate margin", ""), ("Sources", "")],
        "hsbc_pb": [("Amount sent", "n"), ("Bank charges", "n key"), ("HSBC rate margin", ""), ("Other banks' charges", ""), ("Sources", "")],
        "wise": [("Amount sent", "n"), ("Transfers needed", "n key"), ("Yuan to send", "n"), ("Wise fee", ""), ("Wise exchange rate", ""), ("Sources", "")],
        "quota50k": [("Amount sent", "n"), ("Calendar years needed", "n key"), ("All-in bank cost", "n"), ("% of amount", "n"), ("Wire fees", "n"), ("Rate margin", "n"), ("Sources", "")],
        "atm": [("Amount", "n"), ("Calendar years needed", "n key"), ("Withdrawal days, one card", "n"), ("Yuan equivalent", "n"), ("Card rate and ATM fees", ""), ("Sources", "")],
        "cash_usd": [("Amount", "n"), ("Trips, no permit", "n key"), ("Trips with bank permit", "n"), ("Rate margin", "n"), ("Sources", "")],
        "cash_rmb": [("Amount", "n"), ("Trips needed", "n key"), ("Yuan to carry", "n"), ("Exchange cost abroad", ""), ("Sources", "")],
        "reconv": [("Amount", "n"), ("Days at $500 a day", "n key"), ("Rate margin", "n"), ("Sources", "")],
        "edu": [("Payment", "n"), ("Premier / Private Banking", "n key"), ("Advance", "n key"), ("HSBC rate margin", ""), ("Sources", "")],
        "zero": [("Balance kept", "n"), ("Conversion cost", "n key"), ("FBAR still due each year", ""), ("Sources", "")],
        "fine30": [("Amount", "n"), ("Fine: up to 30%", "n key"), ("Serious case: up to 100%", "n"), ("Criminal liability possible", ""), ("Sources", "")],
        "fine20": [("Amount", "n"), ("Fine: up to 20%", "n key"), ("U.S. seizure risk if undeclared", ""), ("Sources", "")],
        "fine_blank": [("Amount", "n"), ("Fine", ""), ("Prohibited", ""), ("Sources", "")],
        "blank": [("Amount", "n"), ("Cost", ""), ("Sources", "")],
    }[m]
    return table("%s · %s" % (r["id"], r["name"]), cols, rows, cls="wide", small=esc(r["cost_basis"]))


def page_costs():
    inputs = [
        ("", ["Price of a dollar at the bank", "<strong>%s yuan</strong>" % SELL, "Bank of China's selling rate: what you pay per dollar bought. Published %s." % esc(IN["boc_pub_time"]["v"]), S("S16") + FL("F03")]),
        ("", ["Bank's mid-point", "%s yuan" % q3(MID) if MID != MID.quantize(D("0.0001")) else "%s yuan" % MID.quantize(D("0.0001")),
              "Half-way between the bank's buying rate (%s) and selling rate (%s)." % (BUY, SELL), S("S16")]),
        ("", ["Exchange-rate margin", "<strong>%s</strong> (%s yuan per dollar)" % (pct(MARGIN_PCT, 2), MARGIN_PER_USD.quantize(D("0.0001"))),
              "Selling rate minus mid-point, divided by the mid-point. The official central parity that day was %s; the New York rate on 6 Nov was %s." % (
                  D(IN["safe_parity_per_100"]["v"]) / 100, IN["fed_h10_latest"]["v"]), S("S16", "S17", "S18")]),
        ("", ["Bank of China wire fee", "<strong>¥200 to ¥410</strong> per wire", "0.1% of the amount, minimum ¥50, maximum ¥260, plus ¥150 cable fee.", S("S19") + FL("F04")]),
        ("", ["HSBC China wire fee (Premier, Advance)", "<strong>¥220 to ¥620</strong> per wire", "0.1% of the amount, minimum ¥100, maximum ¥500, plus ¥120 cable. Optional Pay Exact ¥200. Private Banking individuals: free.", S("S20")]),
        ("", ["HSBC China Global Transfer", "<strong>$0</strong> or <strong>$20</strong>", "To your own HSBC account abroad: free for Private Banking and Premier, $20 for Advance.", S("S20") + FL("F31")]),
        ("", ["HSBC China exchange-rate margin", BL("F02"), "HSBC's rate board could not be read.", S("S53")]),
        ("", ["Wise fee and rate", BL("F05"), "Shown only when a transfer is set up. Limit: ¥300,000 per transfer.", S("S21")]),
        ("", ["Intermediary and receiving-bank charges", BL("F01"), "Not in any published price read; HSBC's tariff says its charges exclude other institutions.", S("S20")]),
    ]
    t_in = table("The published prices everything is computed from", [("Input", "key"), ("Value", ""), ("What it is", ""), ("Official source", "")], inputs, cls="stack")

    # comparison matrix: most useful columns first
    rows = []
    for t in TIERS:
        row = ROW[t]
        rows.append(('data-tier="%d"' % t, [
            "<strong>$%s</strong>" % n(t),
            "<strong>%s</strong> · %s" % (usd(row["boc"]["total_usd"]), pct(row["boc"]["pct"], 2)),
            usd(row["hsbc_tt"]["fee_usd"]),
            "$0 / $20",
            str(row["wise_transfers"]),
            "%d yr · %s" % (row["quota"]["years"], usd(row["quota"]["total_usd"])),
            "%d yr" % row["atm_years"],
            "%d" % row["cash_trips_free"],
            "≤ %s" % usd(row["fine30"], False),
            S("S16", "S19", "S20", "S21", "S04", "S07", "S08", "S06", short=True)]))
    cols = [("Amount", "n"), ("A1 Bank of China, all-in", "n key"), ("A2 HSBC wire, charges", "n"), ("A3 HSBC Global Transfer", "n"), ("A5 Wise, transfers", "n"),
            ("B1 $50,000 a year", "n"), ("B2 ATM abroad", "n"), ("B3 cash trips", "n"), ("E unlawful: fine", "n"), ("Sources", "")]
    t_cmp = table("All methods side by side, every $10,000 to $400,000", cols, rows, cls="wide",
                  small="A1 is the only all-in figure (fee + exchange-rate margin). HSBC columns are bank charges only, because HSBC's margin is blank. "
                        "Counts show how many transfers, calendar years or trips a capped method needs. The fine column is the Chinese penalty exposure of the unlawful routes.")

    details = []
    for g, gname in GROUPS.items():
        details.append("<h3>%s</h3>" % esc(gname))
        for r in ROUTES:
            if r["group"] != g:
                continue
            lab, kind = STATUS_CHIP[r["status"]]
            flags = FL(*r["flags"]) if r["flags"] else ""
            opened = " open" if r["id"] == "A1" else ""
            details.append('<details id="%s"%s><summary>%s · %s %s <small>— %s</small></summary>%s<div class="pad note">Limit: %s %s · <a href="steps.html#steps-%s">steps</a></div></details>' % (
                r["id"], opened, r["id"], esc(r["name"]), chip(lab, kind), esc(r["headline"]), detail_table(r), esc(r["limit"]), flags, r["id"]))

    calc = ('<form class="tool" id="cost-calc" onsubmit="return false"><label>Amount in USD<input id="cc-usd" type="number" min="1" step="1000" value="100000" inputmode="numeric"></label>'
            '<div class="out"><output id="cc-out">Bank of China, one wire of $100,000: %s (%s).</output></div></form>' % (usd(B100["total_usd"]), pct(B100["pct"], 3)))
    kpis = """<div class="kpis">
<div class="kpi"><b>%s</b><span>All-in at Bank of China on $10,000 (%s)</span></div>
<div class="kpi"><b>%s</b><span>All-in at Bank of China on $100,000 (%s)</span></div>
<div class="kpi"><b>%s</b><span>All-in at Bank of China on $400,000 (%s)</span></div>
<div class="kpi"><b>%s</b><span>Exchange-rate margin at Bank of China's published prices</span></div>
</div>""" % (usd(B10["total_usd"]), pct(B10["pct"], 3), usd(B100["total_usd"]), pct(B100["pct"], 3), usd(B400["total_usd"]), pct(B400["pct"], 3), pct(MARGIN_PCT, 2))
    lead = ("What each method costs at every $10,000 step from $10,000 to $400,000. Each figure is arithmetic on a published price: the formula is "
            "amount × selling rate for the yuan needed, the bank's fee rule for the wire, and selling rate minus mid-point for the margin. "
            "Where a price is not published the cell is empty and flagged.")
    body = (kpis + t_in + "<h2>Compare</h2>" + tier_picker() + calc + t_cmp + "<h2>Each method in full</h2>"
            '<p class="note">One table per method, 40 rows each. Downloads: <a href="data/costs.csv">costs.csv</a> · <a href="data/model.json">model.json</a>.</p>'
            + "".join(details))
    return shell("costs.html", "Costs at every $10,000 step to $400,000", body, lead, script_model=True)


# ----------------------------------------------------------------------------------------------
# Page: conversion penalty
# ----------------------------------------------------------------------------------------------
# Who had to file Form 8938 once the balance passes 0, 1, 2, 3 or 4 of the published thresholds (S42).
F8938_WORDS = ["No one", "U.S. residents filing alone", "All U.S. residents", "All U.S. residents; abroad if filing alone", "Everyone"]


def page_penalty():
    g24 = gain(100000, "2024")
    e100 = us_exposure(100000)
    layers = [
        ("", ["1", "Chinese tax on the income itself", "Chinese tax authority", "%s on wages and fees; %s on interest, dividends, rent, asset sales" % (IN["prc_iit_wage"]["v"], IN["prc_iit_flat"]["v"]),
              BL("F13"), "Has to be paid and evidenced before a bank converts. Not caused by the conversion.", S("S15", "S01")]),
        ("", ["2", "Chinese charge on converting", "—", BL("F29"), BL("F29"), "The rules read describe documents and limits, not a levy on conversion.", S("S01", "S04")]),
        ("", ["3", "Exchange-rate margin", "The bank", "%s at Bank of China" % pct(MARGIN_PCT, 2), usd(boc(100000)["margin_usd"]), "On every conversion. Moves daily.", S("S16") + FL("F03")]),
        ("", ["4", "Wire fee", "The bank", "Bank of China ¥200–¥410 · HSBC ¥220–¥620 (Private Banking free)", "%s · %s" % (usd(boc(100000)["fee_usd"]), usd(hsbc_tt(100000)["fee_usd"])),
              "Per wire, capped: one large wire is cheapest.", S("S19", "S20")]),
        ("", ["5", "Intermediary and receiving-bank charges", "Other banks", BL("F01"), BL("F01"), "Per wire; ask the receiving bank.", S("S20")]),
        ("", ["6", "U.S. tax on the income itself", "IRS", "Worldwide income is taxed when earned; credit for Chinese tax paid; exclusion up to %s (2025) / %s (2026) of foreign earned income" % (
            usd(IN["feie_2025"]["v"], False), usd(IN["feie_2026"]["v"], False)), BL("F37"), "Arises in the year the income was earned, whether or not the money is ever moved.", S("S35", "S36", "S37")]),
        ("", ["7", "U.S. tax on the exchange gain", "IRS", "Gain = amount × (1 − today's rate ÷ rate when received); 0%, 15% or 20% if a long-term capital gain, up to 37% if ordinary",
              "Yuan from 2024: gain %s → %s at 15%%" % (usd(g24, False), usd(q0(D(g24) * 15 / 100), False)),
              "Only when you convert, only on a gain, and not at all if the gain on a personal transaction is $200 or less.", S("S30", "S31", "S32", "S23") + FL("F14", "F16")]),
        ("", ["8", "U.S. reporting penalties", "FinCEN and IRS", "$0 if reports were filed; 0%% or 5%% under the streamlined procedures; otherwise up to %s per missed report, willful up to the greater of %s or 50%%" % (
            usd(FBAR_NW, False), usd(FBAR_W, False)), "$0 · $0 · %s" % usd(e100["sdo"], False), "Only if the FBAR, Form 8938 or Form 3520 was missed.", S("S38", "S39", "S40", "S45", "S46")]),
        ("", ["9", "Chinese penalties", "SAFE", "Fine up to 30% of the amount; 30% to 100% in serious cases; criminal liability", usd(ROW[100000]["fine30"], False), "Only if an unlawful route is used.", S("S06")]),
    ]
    t1 = table("The conversion penalty, layer by layer", [("#", "n"), ("Layer", "key"), ("Charged by", ""), ("Published figure", ""), ("On $100,000", ""), ("When it applies", ""), ("Official sources", "")],
               layers, cls="stack", small="Layers 3 to 5 are the cost of converting and sending. Layers 1 and 6 are tax on the income, due whether or not you move it. Layer 7 is the only tax the conversion itself triggers. Layers 8 and 9 are avoidable.")

    rows = []
    for t in TIERS:
        u = ROW[t]["us"]
        need = F8938_WORDS[len(u["f8938"])]
        rows.append(('data-tier="%d"' % t, [
            "<strong>$%s</strong>" % n(t), "<strong>$0</strong>", "<strong>$0</strong>", "<strong>%s</strong>" % usd(u["sdo"], False),
            usd(u["nonwillful"], False) if u["fbar"] else "Not due",
            usd(u["willful"], False) if u["fbar"] else "Not due",
            esc(need),
            usd(u["f3520"], False) if u["f3520"] is not None else "Not due",
            S("S38", "S46", "S45", "S39", "S40", "S42", "S43", short=True)]))
    cols = [("Balance not reported", "n"), ("If every report was filed", "n key"), ("Fix now, living abroad", "n key"), ("Fix now, living in the U.S. (5%)", "n key"),
            ("FBAR non-willful maximum, per missed year", "n"), ("FBAR willful ceiling, per year", "n"), ("Form 8938 was required if you are", ""),
            ("Form 3520 maximum if it was a gift or bequest (25%)", "n"), ("Sources", "")]
    t2 = table("U.S. reporting-penalty exposure at every $10,000 step", cols, rows, cls="wide",
               small="Read left to right: nothing is owed if the reports were filed; the next two columns are what the IRS's streamlined procedures charge to fix a "
                     "non-willful failure (plus the tax and interest on unreported income); the right-hand columns are legal maximums outside those procedures, not predictions. "
                     "The 5% applies to assets that should have been reported, or whose income was not reported. \"Not due\": an FBAR is due only above $10,000, "
                     "and Form 3520 only for gifts or bequests above $100,000. Form 8938 is required above $50,000 (living in the U.S., not filing jointly), "
                     "$100,000 (U.S., joint), $200,000 (abroad, not joint) or $400,000 (abroad, joint) at year end.")

    pos = [
        ("", ["FBARs and Form 8938 filed, interest reported", "Nothing to fix.", "<strong>$0</strong>", S("S38", "S42")]),
        ("", ["Income reported, only FBARs missed, no IRS contact", "File the late FBARs now with the reason for lateness. No penalty where there was reasonable cause and the balance is properly reported; otherwise up to %s per report. %s" % (usd(FBAR_NW, False), FL("F23")),
              "<strong>$0</strong> to %s per report" % usd(FBAR_NW, False), S("S38", "S40", "S39", "S41")]),
        ("", ["Income not fully reported, not willful, living abroad", "Streamlined Foreign Offshore Procedures: 3 years of returns, 6 years of FBARs, pay the tax and interest. Needs no U.S. abode and 330 full days outside the U.S. in at least one of the last 3 years. %s" % FL("F22", "F35"),
              "<strong>$0</strong> penalty", S("S46", "S44")]),
        ("", ["Income not fully reported, not willful, living in the U.S.", "Streamlined Domestic Offshore Procedures: 3 years of amended returns, 6 years of FBARs, pay the tax and interest plus 5%% of the highest year-end balance. %s" % FL("F22", "F35"),
              "<strong>5%</strong> of the balance", S("S45", "S44")]),
        ("", ["Only an information form is late (Form 8938 or 3520), income was reported", "File it through the normal procedure with a reasonable-cause statement. Penalties may still be assessed.",
              "Up to %s (8938); 5%% a month up to 25%% (3520)" % usd(IN["f8938_penalty"]["v"], False), S("S47", "S42", "S43")]),
        ("", ["Conduct might be seen as willful", "The streamlined procedures are not available. The IRS points to its Criminal Investigation Voluntary Disclosure Practice. Take legal advice before any filing. %s" % FL("F20"),
              "Ceiling: greater of %s or 50%% of the balance, per year" % usd(FBAR_W, False), S("S44", "S48", "S40")]),
        ("", ["The IRS has already opened an examination", "The streamlined procedures are closed to you.", "Normal penalties apply", S("S44")]),
    ]
    t3 = table("Which position are you in?", [("Your position", "key"), ("What the IRS procedure is", ""), ("Penalty", ""), ("Official sources", "")], pos, cls="stack")

    prc = [
        ("", ["Moving money out against the rules, or by deception (逃汇)", "Art. 39", "Fine up to 30% of the amount; 30% up to the full amount in serious cases; criminal liability", S("S06")]),
        ("", ["Getting foreign exchange with false or invalid documents (非法套汇)", "Art. 40", "Fine up to 30% of the amount; 30% up to the full amount in serious cases; criminal liability", S("S06")]),
        ("", ["Carrying foreign exchange across the border against the rules", "Art. 42", "Warning; fine up to 20% of the amount", S("S06", "S08")]),
        ("", ["Private or disguised buying and selling of foreign exchange", "Art. 45", "Warning, confiscation of gains, fine up to 30%; 30% up to the full amount in serious cases; criminal liability", S("S06")]),
        ("", ["Submitting untrue documents", "Art. 48", "Warning; an individual may be fined up to ¥50,000", S("S06")]),
        ("", ["Splitting a large amount into small ones to evade the limit", "PBOC Decree [2006] No. 3, Art. 7", "Prohibited for banks and individuals; penalised under the Regulations above", S("S05", "S06")]),
        ("", ["Exchanging yuan for virtual currency", "Yin Fa [2026] No. 42", "Illegal financial activity; banks may not serve it; criminal liability where a crime is constituted", S("S13")]),
    ]
    t4 = table("Chinese penalties if an unlawful route is used", [("Conduct", "key"), ("Provision", ""), ("Penalty", ""), ("Official source", "")], prc, cls="stack")

    kpis = """<div class="kpis">
<div class="kpi"><b>%s</b><span>Cost of converting and sending $100,000 (layers 3 and 4, Bank of China)</span></div>
<div class="kpi"><b>%s</b><span>U.S. tax at 15%% on the exchange gain of $100,000 of 2024 yuan (layer 7)</span></div>
<div class="kpi"><b>%s</b><span>5%% streamlined penalty on an unreported $100,000 balance, living in the U.S. (layer 8)</span></div>
<div class="kpi"><b>%s</b><span>Chinese fine ceiling (30%%) on $100,000 through an unlawful route (layer 9)</span></div>
</div>""" % (usd(B100["total_usd"]), usd(q0(D(g24) * 15 / 100), False), usd(e100["sdo"], False), usd(ROW[100000]["fine30"], False))
    lead = ("\"Conversion penalty\" is not one charge. It is nine separate layers, charged by different bodies for different reasons. Three are the price of converting, "
            "two are income tax that exists whether or not you move the money, one is the tax the conversion itself triggers, and the largest two are penalties that are avoidable.")
    body = (kpis + t1 + "<h2>U.S. penalties by balance</h2>" + tier_picker() + t2 + "<h2>How to fix a missed U.S. report</h2>" + t3 + "<h2>Chinese side</h2>" + t4 +
            '<p class="note">Download: <a href="data/penalty.csv">penalty.csv</a>. State tax is not covered %s; the U.S.–China tax treaty was not read %s.</p>' % (FL("F25"), FL("F26")))
    return shell("penalty.html", "The conversion penalty, broken down", body, lead)


# ----------------------------------------------------------------------------------------------
# Page: exchange gain
# ----------------------------------------------------------------------------------------------
def page_fx():
    rows = []
    for y in YEARS:
        gp = GAIN_PCT[y]
        g = gain(100000, y)
        irs = IRS_AVG.get(y)
        if gp > 0:
            cells = [y, str(RATE[y]), irs if irs else "Not listed", "<strong>+%s</strong>" % pct(gp), "<strong>%s</strong>" % usd(g, False),
                     usd(q0(D(g) * 15 / 100), False), usd(q0(D(g) * 20 / 100), False), usd(q0(D(g) * 37 / 100), False), S(RATE_SRC[y], "S16") + (S("S22") if irs else "")]
            attrs = ""
        else:
            cells = [y, str(RATE[y]), irs if irs else "Not listed", "<strong>%s</strong>" % pct(gp).replace("-", "−"), "Loss of %s" % usd(-g, False),
                     "$0", "$0", "$0", S(RATE_SRC[y], "S16") + (S("S22") if irs else "") + FL("F17")]
            attrs = ""
        rows.append((attrs, cells))
    rows.insert(0, ("", ["2026", BL("F14"), "Not listed", BL("F14"), BL("F14"), BL("F14"), BL("F14"), BL("F14"), S("S22")]))
    cols = [("Year the yuan was received", "key"), ("Yuan per dollar that year (Federal Reserve)", "n"), ("IRS yearly average", "n"), ("Gain or loss if converted now", "n key"),
            ("Per $100,000 converted", "n key"), ("Tax at 15%", "n"), ("Tax at 20%", "n"), ("Tax at 37%", "n"), ("Official sources", "")]
    t1 = table("Exchange gain by the year the yuan was received", cols, rows, cls="wide",
               small="Gain = amount × (1 − %s ÷ that year's rate). %s is Bank of China's selling rate on %s. 15%% and 20%% are long-term capital-gain rates; 37%% is the top ordinary rate, "
                     "the most that could apply if the gain is ordinary or short-term. Use the actual rate on the dates you received the money where you know them." % (SELL, SELL, esc(AS_OF)))

    mrows = []
    for t in TIERS:
        cells = ["<strong>$%s</strong>" % n(t)]
        for y in YEARS:
            g = ROW[t]["gain"][y]
            if g > EXCL:
                cells.append(usd(g, False))
            elif g > 0:
                cells.append("%s*" % usd(g, False))
            else:
                cells.append('<span class="loss">%s</span>' % usd(g, False))
        cells.append(S("S16", *G5_SRCS, short=True))
        mrows.append(('data-tier="%d"' % t, cells))
    mcols = [("Amount converted", "n")] + [(y, "n") for y in YEARS] + [("Sources", "")]
    t2 = table("Exchange gain or loss in dollars: every $10,000 step × every year", mcols, mrows, cls="wide",
               small="Newest years first. A minus sign is a loss. An asterisk marks a gain of $%d or less, which is not recognised on a personal transaction." % EXCL)

    rules = [
        ("", ["What counts", "Converting yuan, including a yuan bank deposit, into dollars is a disposal of foreign currency.", S("S30")]),
        ("", ["How the gain is measured", "Dollars received, minus the dollar value of the same yuan at the rate when you received it. The IRS accepts any posted rate used consistently.", S("S22", "S30") + FL("F15")]),
        ("", ["The $200 rule", "On a personal transaction no gain is recognised unless it exceeds $200. Above $200 the whole gain counts; $200 is a threshold, not an allowance.", S("S30", "S31")]),
        ("", ["Rate if it is a personal transaction", "Reported as a capital gain. Held more than a year: 0%, 15% or 20% depending on taxable income (0% up to $48,350 single in 2025). Held a year or less: ordinary rates.", S("S31", "S32")]),
        ("", ["Rate if it is not personal", "A deposit held for investment or business falls under section 988: ordinary income, 10%% to 37%%. %s" % FL("F16"), S("S30", "S33")]),
        ("", ["Extra 3.8%", "The net investment income tax can apply to net gains above the income thresholds ($200,000 single, $250,000 joint). Not included in the columns. %s" % FL("F18"), S("S34")]),
        ("", ["Losses", "No U.S. tax arises on a loss. Whether the loss can be deducted is not confirmed. %s" % FL("F17"), S("S32", "S30")]),
        ("", ["Two official 2025 averages", "IRS: %s. Federal Reserve: %s. This page uses the Federal Reserve series for every year. %s" % (IRS_AVG["2025"], RATE["2025"], FL("F15")), S("S22", "S23")]),
    ]
    t3 = table("The rules behind the numbers", [("Rule", "key"), ("What it says", ""), ("Official sources", "")], rules, cls="stack")

    opts = "".join('<option value="%s"%s>%s</option>' % (y, " selected" if y == "2024" else "", y) for y in YEARS)
    calc = ('<form class="tool" id="gain-calc" onsubmit="return false"><label>Amount converted, USD<input id="gc-usd" type="number" min="1" step="1000" value="100000" inputmode="numeric"></label>'
            '<label>Year the yuan was received<select id="gc-year">%s</select></label>'
            '<label>Tax rate<select id="gc-rate"><option value="0">0%%</option><option value="15" selected>15%%</option><option value="20">20%%</option><option value="37">37%%</option></select></label>'
            '<div class="out"><output id="gc-out">Exchange gain of %s. Tax at 15%%: %s.</output></div></form>' % (opts, usd(gain(100000, "2024"), False), usd(q0(D(gain(100000, "2024")) * 15 / 100), False)))
    kpis = """<div class="kpis">
<div class="kpi"><b>+%s</b><span>Largest gain: yuan received in %s (%s per dollar then, %s now)</span></div>
<div class="kpi"><b>%s</b><span>Largest loss: yuan received in %s (%s per dollar then)</span></div>
<div class="kpi"><b>%d of %d</b><span>years from %s to %s in which converting now gives a gain; %d give a loss</span></div>
<div class="kpi"><b>$%d</b><span>Gain on a personal transaction at or below which nothing is recognised</span></div>
</div>""" % (pct(GAIN_PCT[MAX_GAIN_Y]), MAX_GAIN_Y, RATE[MAX_GAIN_Y], SELL, pct(GAIN_PCT[MIN_GAIN_Y]).replace("-", "−"), MIN_GAIN_Y, RATE[MIN_GAIN_Y],
             len(GAIN_YEARS), len(YEARS), YEARS[-1], YEARS[0], len(LOSS_YEARS), EXCL)
    lead = ("The only U.S. tax that converting triggers is on the exchange gain: how many more dollars the yuan buys today than when you received it. "
            "The date you received the yuan is not known here, so every year from %s to %s is shown. Find your year, or weight several years by how much arrived in each."
            % (YEARS[-1], YEARS[0]))
    body = (kpis + calc + t1 + "<h2>Every amount, every year</h2>" + tier_picker() + t2 + "<h2>Rules</h2>" + t3 +
            '<p class="note">Download: <a href="data/fx_gain.csv">fx_gain.csv</a>. Loss years: %s. Gain years: %s.</p>' % (year_runs(LOSS_YEARS), year_runs(GAIN_YEARS)))
    return shell("fx-gain.html", "U.S. tax on the exchange gain, by year", body, lead, script_model=True)


# ----------------------------------------------------------------------------------------------
# Page: step by step
# ----------------------------------------------------------------------------------------------
def page_steps():
    out = []
    for g, gname in GROUPS.items():
        out.append("<h2>%s</h2>" % esc(gname))
        for r in ROUTES:
            if r["group"] != g:
                continue
            lab, kind = STATUS_CHIP[r["status"]]
            rows = [("", [str(i), esc(text), esc(proof), S(*srcs)]) for i, (text, proof, srcs) in enumerate(r["steps"], 1)]
            hv = headline_value(r, 100000)
            cost_line = "On $100,000: <strong>%s</strong> (%s)." % (esc(hv), esc(r["headline"])) if hv is not None else "On $100,000: no published price %s." % FL(r["flags"][0])
            out.append('<h3 id="steps-%s">%s · %s %s</h3><p class="note">%s Limit: %s <a href="costs.html#%s">Cost table</a> %s</p>' % (
                r["id"], r["id"], esc(r["name"]), chip(lab, kind), cost_line, esc(r["limit"]), r["id"], FL(*r["flags"]) if r["flags"] else ""))
            out.append(table("Steps for %s" % r["id"], [("Step", "n"), ("Do this", ""), ("Have ready", ""), ("Official sources", "")], rows, cls="stack"))
    lead = ("Exact steps for each lawful method, with the document each step needs and the official page it rests on. "
            "Unlawful methods have no steps: the row says so and links to the penalty.")
    toc = '<p class="note">Jump to: %s</p>' % " · ".join('<a href="#steps-%s">%s</a>' % (r["id"], r["id"]) for r in ROUTES)
    return shell("steps.html", "Step by step, method by method", toc + "".join(out), lead)


# ----------------------------------------------------------------------------------------------
# Page: repo review
# ----------------------------------------------------------------------------------------------
VERDICT_CHIP = {"irregularity": ("Irregularity", "bad"), "needs review": ("Needs review", "warn"), "consistent": ("Matches official text", "ok"),
                "resolved": ("Now verified", "ok"), "gap filled": ("Gap, now filled", "info")}


def page_audit():
    rows = []
    for a in AUDIT["findings"]:
        w = a["where"]
        where = ("%d lines in %d files, e.g. %s" % (w["hits"], w["files"], ", ".join("<code>%s</code>" % esc(e) for e in w["examples"]))) if w["hits"] else "No occurrence in the files scanned"
        lab, kind = VERDICT_CHIP[a["verdict"]]
        rows.append(("", ["<strong id=\"%s\">%s</strong>" % (a["id"], a["id"]), chip(lab, kind),
                          "<strong>%s</strong><br>%s<br><span class=\"small\">Where: %s</span>" % (esc(a["title"]), esc(a["repo_says"]), where),
                          esc(a["official_says"]), esc(a["assessment"]), S(*a["sources"])]))
    cols = [("ID", "n"), ("Result", ""), ("What the repository says", ""), ("What the official text says", ""), ("Assessment", ""), ("Official sources", "")]
    counts = {}
    for a in AUDIT["findings"]:
        counts[a["verdict"]] = counts.get(a["verdict"], 0) + 1
    kpis = '<div class="kpis">%s</div>' % "".join('<div class="kpi"><b>%d</b><span>%s</span></div>' % (counts[v], esc(VERDICT_CHIP[v][0])) for v in VERDICT_CHIP if v in counts)
    t = table("Claims in the repository checked against the official text", cols, rows, cls="stack",
              small="Scanned %d text files of all other sessions on main at commit %s on %s. Other sessions' files were read, not edited." % (
                  AUDIT["files_scanned"], esc(AUDIT["scanned_commit"]), esc(AUDIT["scanned_on"])))
    struct = "<h2>Structural observations</h2><p class=\"note\">These concern how the repository is organised; no official source applies, so they are a list, not table rows.</p><ul>%s</ul>" % "".join(
        "<li>%s</li>" % esc(s) for s in AUDIT["structural"])
    how = ('<h2>How the review was done</h2><p class="note">Each official page in <a href="sources.html">Sources</a> was fetched and read on %s. Each claim pattern was then searched '
           'line by line across the repository at the commit above; counts and example locations are recorded in <code>data/audit.json</code>. '
           'Findings about other sessions\' files are published here and on the task board rather than edited into their files.</p>' % esc(AS_OF))
    lead = ("The load-bearing statements already published in this repository, checked line by line against the official pages read for this section. "
            "Two are stale and still published, three need a caveat, and the rest match.")
    return shell("audit.html", "Repo review against official sources", kpis + t + struct + how, lead)


# ----------------------------------------------------------------------------------------------
# Page: flagged for review
# ----------------------------------------------------------------------------------------------
def page_flagged():
    rows = [("", ['<strong id="%s">%s</strong>' % (f["id"], f["id"]), chip("Needs review", "warn"), "<strong>%s</strong>" % esc(f["item"]), esc(f["why"]), esc(f["resolve"]), S(*f["sources"])])
            for f in FLAGLIST]
    t1 = table("Flagged for Review: open items", [("ID", "n"), ("Status", ""), ("Item", "key"), ("Why it is flagged", ""), ("What would settle it", ""), ("Official sources", "")], rows, cls="stack",
               small="Status \"needs review\" means the item is published here and blocks nothing. Values tied to these items are left blank on the other pages.")
    nr = [s for s in SOURCES if s["status"] != "verified"]
    rows2 = [("", ["<strong>%s</strong>" % s["id"], esc(s["publisher"]), esc(s["title"]), esc(s["note"]), S(s["id"])]) for s in nr]
    t2 = table("Sources that could not be fully relied on", [("ID", "n"), ("Publisher", ""), ("Page", "key"), ("Problem", ""), ("Link", "")], rows2, cls="stack")
    aud = [a for a in AUDIT["findings"] if a["verdict"] in ("irregularity", "needs review")]
    rows3 = [("", ['<a href="audit.html#%s">%s</a>' % (a["id"], a["id"]), chip(*VERDICT_CHIP[a["verdict"]]), esc(a["title"]), esc(a["assessment"]), S(*a["sources"])]) for a in aud]
    t3 = table("Irregularities found in the repository", [("ID", "n"), ("Result", ""), ("Finding", "key"), ("Assessment", ""), ("Official sources", "")], rows3, cls="stack",
               small="Full detail with file and line on the Repo review page.")
    kpis = """<div class="kpis">
<div class="kpi"><b>%d</b><span>open items, each with what would settle it</span></div>
<div class="kpi"><b>%d</b><span>sources read but not fully relied on (dead, stale or indirect)</span></div>
<div class="kpi"><b>%d</b><span>irregularities or caveats in the repository's earlier pages</span></div>
</div>""" % (len(FLAGLIST), len(nr), len(aud))
    lead = ("Everything that could not be confirmed from an official source, in one place. Nothing here was filled in by inference: the related values are blank on the other pages. "
            "These items do not block publication; they tell you what to check before acting.")
    return shell("flagged.html", "Flagged for Review", kpis + t1 + "<h2>Problem sources</h2>" + t2 + "<h2>Repository irregularities</h2>" + t3, lead)


# ----------------------------------------------------------------------------------------------
# Page: sources
# ----------------------------------------------------------------------------------------------
def page_sources():
    rows = []
    for s in SOURCES:
        st = chip("Read and quoted", "ok") if s["status"] == "verified" else chip("Needs review", "warn")
        quotes = "".join("<li>“%s”</li>" % esc(q) for q in s["quotes"])
        rows.append(("", ['<strong id="%s">%s</strong>' % (s["id"], s["id"]), st, "%s<br><span class=\"small\">%s · %s</span>" % (esc(s["title"]), esc(s["publisher"]), esc(s["kind"])),
                          esc(s["supports"]) + (" <em>%s</em>" % esc(s["note"]) if s["note"] else ""), '<ul class="tight">%s</ul><span class="small">Where: %s</span>' % (quotes, esc(s["locator"])),
                          S(s["id"]) + '<br><a href="%s" target="_blank" rel="noopener noreferrer">Open the page ↗</a>' % esc(s["url"])]))
    cols = [("ID", "n"), ("Status", ""), ("Page", "key"), ("Used for", ""), ("Passage relied on (as fetched)", "small"), ("Link", "")]
    kinds = {}
    for s in SOURCES:
        kinds[s["kind"]] = kinds.get(s["kind"], 0) + 1
    kpis = '<div class="kpis"><div class="kpi"><b>%d</b><span>official pages read on %s</span></div><div class="kpi"><b>%d</b><span>read and quoted</span></div><div class="kpi"><b>%d</b><span>need review (dead, stale, indirect or partly read)</span></div></div>' % (
        len(SOURCES), esc(AS_OF), sum(1 for s in SOURCES if s["status"] == "verified"), sum(1 for s in SOURCES if s["status"] != "verified"))
    t = table("Source ledger", cols, rows, cls="stack",
              small="Government, central-bank and court pages are primary law or official guidance. Bank and provider pages are primary only for that institution's own prices and terms.")
    how = ('<h2>What "verified" means here</h2><p class="note">A page is marked "Read and quoted" only if it was fetched on %s and the passage shown was read in the fetched text. '
           'The quoted passage is kept so that anyone can open the link and find it. The automated checks (<code>verify.py</code>) test that every table row links to one of these pages, '
           'that blank cells are flagged and that the arithmetic can be reproduced; they do not re-read the live pages. Chinese-language quotes are left in the original.</p>' % esc(AS_OF))
    lead = "Every official page this section rests on, with the passage relied on and a direct link for manual review."
    return shell("sources.html", "Sources and verification", kpis + t + how, lead)


# ----------------------------------------------------------------------------------------------
# Exports
# ----------------------------------------------------------------------------------------------
def write_csv(name, header, rows):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    w.writerows(rows)
    (DATA / name).write_text(buf.getvalue(), encoding="utf-8")


def exports():
    (DATA / "model.json").write_text(json.dumps(MODEL, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    rows = []
    for t in TIERS:
        r = ROW[t]
        rows.append([t, r["boc"]["total_usd"], r["boc"]["pct"], r["boc"]["fee_cny"], r["boc"]["margin_cny"], r["boc"]["debit_cny"],
                     r["hsbc_tt"]["fee_usd"], r["hsbc_tt"]["fee_cny"], r["hsbc_tt"]["with_exact_usd"], "0.00", r["hsbc_gt"]["advance_usd"], "0.00",
                     r["wise_transfers"], "", r["quota"]["years"], r["quota"]["total_usd"], r["atm_years"], r["atm_days"], "",
                     r["cash_trips_free"], r["cash_trips_permit"], r["rmb_trips"], r["reconv_days"], r["fine30"], r["fine100"], r["fine20"], ""])
    write_csv("costs.csv", ["usd", "A1_boc_all_in_usd", "A1_pct", "A1_fee_cny", "A1_margin_cny", "A1_debit_cny", "A2_hsbc_charges_usd", "A2_hsbc_charges_cny",
                            "A2_with_pay_exact_usd", "A3_gt_premier_usd", "A3_gt_advance_usd", "A4_pb_charges_usd", "A5_wise_transfers", "A5_wise_fee_blank_F05",
                            "B1_years", "B1_all_in_usd", "B2_atm_years", "B2_atm_days", "B2_fee_blank_F08", "B3_trips_no_permit", "B3_trips_permit", "B4_rmb_trips",
                            "B5_days", "E_fine_30pct_usd", "E_fine_100pct_usd", "E5_fine_20pct_usd", "other_bank_charges_blank_F01"], rows)
    rows = []
    for t in TIERS:
        u = ROW[t]["us"]
        rows.append([t, 0, 0, u["sdo"], u["nonwillful"] if u["fbar"] else "", u["willful"] if u["fbar"] else "", "; ".join(u["f8938"]), u["f3520"] if u["f3520"] is not None else ""])
    write_csv("penalty.csv", ["balance_usd", "if_filed_usd", "streamlined_foreign_penalty_usd", "streamlined_domestic_5pct_usd", "fbar_nonwillful_max_per_year_usd",
                              "fbar_willful_ceiling_per_year_usd", "form_8938_required_for", "form_3520_max_25pct_usd"], rows)
    write_csv("fx_gain.csv", ["usd"] + ["gain_usd_%s" % y for y in YEARS], [[t] + [ROW[t]["gain"][y] for y in YEARS] for t in TIERS])


def executive_summary_md():
    g_lo, g_hi = gain(100000, REC_LO), gain(100000, REC_HI)
    def link(i):
        return "[%s](%s)" % (i, SRC[i]["url"])
    lines = [
        "# China money: what it costs to get yuan out and into dollars",
        "",
        "Session `arena/b03f272a-china2` · figures as of %s · sources read %s · research, not personal tax or legal advice." % (AS_OF, AS_OF),
        "",
        "Live pages: https://sassnarep3-star.github.io/China2/landed-cost-b03f272a/",
        "",
        "## The answer",
        "",
        "The cheapest lawful way is a bank conversion and one wire to your own U.S. account, backed by proof of where the money came from and that Chinese tax was paid. "
        "The U.S. taxes only the exchange gain since you received the yuan. Penalties arise only where the Chinese account went unreported.",
        "",
        "| # | Finding | In numbers | Official sources |",
        "|---|---|---|---|",
        "| 1 | Cheapest lawful route: bank conversion against documents, one wire (A1) | %s on $10,000 (%s); %s on $100,000 (%s); %s on $400,000 (%s) at Bank of China's published prices; receiving-bank charges extra (blank, F01) | %s %s %s |" % (
            usd(B10["total_usd"]), pct(B10["pct"], 3), usd(B100["total_usd"]), pct(B100["pct"], 3), usd(B400["total_usd"]), pct(B400["pct"], 3), link("S16"), link("S19"), link("S01")),
        "| 2 | Send one wire, not many: the fee is capped per wire | One $400,000 wire: %s in fees; forty $10,000 wires: %s | %s %s |" % (cny(B400["fee_cny"]), cny(FORTY_SMALL), link("S19"), link("S05")),
        "| 3 | No $50,000 ceiling for documented income of a non-domestic individual | The yearly facility is for domestic individuals and permanent-resident ID holders; otherwise the documents decide (F07) | %s %s %s |" % (link("S01"), link("S04"), link("S02")),
        "| 4 | U.S. tax on conversion = tax on the exchange gain | Yuan from %s: gain %s to %s of the amount (%s to %s per $100,000; %s to %s tax at 15%%). Yuan from %s: a loss, nothing to tax (F14, F16) | %s %s %s %s |" % (
            year_runs(RECENT), pct(GAIN_PCT[REC_LO]), pct(GAIN_PCT[REC_HI]), usd(g_lo, False), usd(g_hi, False), usd(q0(D(g_lo) * 15 / 100), False), usd(q0(D(g_hi) * 15 / 100), False),
            year_runs(LOSS_YEARS), link("S30"), link("S31"), link("S32"), link("S23")),
        "| 5 | Penalties come from an unreported account, not the transfer | Filed: $0. Streamlined from abroad: $0. Streamlined in the U.S.: 5%% (%s per $100,000). Otherwise up to %s per missed report; willful: greater of %s or 50%% per year (F20, F22) | %s %s %s %s %s |" % (
            usd(us_exposure(100000)["sdo"], False), usd(FBAR_NW, False), usd(FBAR_W, False), link("S38"), link("S46"), link("S45"), link("S39"), link("S40")),
        "| 6 | Unlawful routes (others' quotas, underground swaps, crypto, false documents) | Chinese fine up to 30%% (%s on $100,000), up to 100%% in serious cases, criminal liability | %s %s %s |" % (
            usd(ROW[100000]["fine30"], False), link("S06"), link("S05"), link("S13")),
        "",
        "## Pages",
        "",
        "- `index.html` summary · `routes.html` %d methods · `costs.html` every method at every $10,000 step · `penalty.html` the nine layers and U.S. penalty exposure by balance" % len(ROUTES),
        "- `fx-gain.html` exchange gain for %s to %s · `steps.html` exact steps · `audit.html` %d repository checks · `flagged.html` %d open items · `sources.html` %d official pages" % (
            YEARS[-1], YEARS[0], len(AUDIT["findings"]), len(FLAGLIST), len(SOURCES)),
        "",
        "## Limits",
        "",
        "Nothing personal is assumed. Source of the money, acquisition dates, residence, filing history and bank are unknown; where the answer depends on them every case is shown. "
        "Values with no official source are blank and listed on `flagged.html`. Exchange rates are a snapshot of %s and move daily." % AS_OF,
        "",
        "Reproduce: `python3 landed-cost-b03f272a/build.py && python3 landed-cost-b03f272a/verify.py`.",
        "",
    ]
    (HERE / "EXECUTIVE_SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    pages = {"index.html": page_index(), "routes.html": page_routes(), "costs.html": page_costs(), "penalty.html": page_penalty(),
             "fx-gain.html": page_fx(), "steps.html": page_steps(), "audit.html": page_audit(), "flagged.html": page_flagged(), "sources.html": page_sources()}
    for name, text in pages.items():
        (HERE / name).write_text(text, encoding="utf-8")
    exports()
    executive_summary_md()
    print("built %d pages, %d tiers, %d routes, %d sources, %d flags" % (len(pages), len(TIERS), len(ROUTES), len(SOURCES), len(FLAGLIST)))


if __name__ == "__main__":
    main()
