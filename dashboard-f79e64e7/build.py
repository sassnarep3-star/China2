#!/usr/bin/env python3
"""Build the dashboard pages, data dumps and exports from content.py.

Deterministic: no clock, no network. Run:
    PYTHONDONTWRITEBYTECODE=1 python3 dashboard-f79e64e7/build.py
"""
import csv
import html
import io
import json
import sys
from decimal import Decimal as D, ROUND_HALF_UP, ROUND_CEILING
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import content as C  # noqa: E402

E = html.escape
SRC = {s["id"]: s for s in C.SOURCES}
SELL, BUY = D(C.BOC_SELL), D(C.BOC_BUY)
MID = (SELL + BUY) / 2
HALF = SELL - MID                      # RMB per dollar, half the posted buy-sell gap
TIERS = [D(n) for n in range(10000, 400001, 10000)]
CENT = D("0.01")


def q2(x):
    return x.quantize(CENT, rounding=ROUND_HALF_UP)


def ceil(x):
    return int(x.to_integral_value(rounding=ROUND_CEILING))


def clamp(x, lo, hi):
    return max(D(lo), min(D(hi), x))


def boc_fee(usd):
    """Bank of China wire fee in RMB for one wire of `usd` dollars (S18)."""
    return clamp(usd * SELL * D(C.BOC_PCT), C.BOC_MIN, C.BOC_MAX) + D(C.BOC_CABLE)


def hsbc_fee(usd):
    return clamp(usd * SELL * D(C.HSBC_PCT), C.HSBC_MIN, C.HSBC_MAX) + D(C.HSBC_CABLE)


def plural(n, word):
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def money(x, dp=2):
    if x is None:
        return ""
    return f"${q2(x):,.2f}" if dp == 2 else f"${int(x):,}"


def rmb(x):
    return "" if x is None else f"¥{q2(x):,.2f}"


def row_for(method, usd):
    """One cost row. Every numeric field is arithmetic on published inputs or blank."""
    m = method["model"]
    r = dict(method=method["id"], usd=int(usd), est_cost_usd=None, pct=None, rmb_in=None,
             count="", time="", spread_usd=None, fee_usd=None, tax_usd=None,
             fine_ordinary_max_usd=None, fine_serious_max_usd=None, basis="", excluded="")
    spread_cny = usd * HALF

    def wires(amounts, time, count=None):
        fee = sum(boc_fee(a) for a in amounts)
        r.update(spread_usd=q2(spread_cny / SELL), fee_usd=q2(fee / SELL),
                 est_cost_usd=q2((spread_cny + fee) / SELL), rmb_in=q2(usd * SELL + fee),
                 count=count or plural(len(amounts), "wire"), time=time,
                 basis="Bank of China spread and wire fees",
                 excluded="Intermediary and receiving bank fees; any tax")

    if m == "one_wire":
        wires([usd], method.get("time", "One transaction"))
    elif m == "quota_wires":
        n = ceil(usd / C.QUOTA_USD)
        amounts = [D(C.QUOTA_USD)] * (n - 1) + [usd - D(C.QUOTA_USD) * (n - 1)]
        wires(amounts, plural(n, "calendar year"))
    elif m == "reconvert":
        wires([usd], "One transaction with the memo",
              count=f"1 wire, or {ceil(usd / 500):,} days at $500 a day on ID alone")
    elif m == "hsbc_fee":
        r.update(fee_usd=q2(hsbc_fee(usd) / SELL), count="1 wire", time="One transaction",
                 basis="HSBC Premier or Advance wire fee only, shown at Bank of China's rate",
                 excluded="HSBC exchange spread (not read); other banks' fees; any tax")
    elif m == "wise":
        n = ceil(usd * SELL / C.WISE_PER_TRANSFER_CNY)
        r.update(count=plural(n, "transfer"), time="Not published",
                 basis="Transfer count only", excluded="Wise fee and rate (quote only)")
    elif m == "atm":
        r.update(count=f"{ceil(usd * SELL / C.ATM_DAY_CNY):,} card-days",
                 time=plural(ceil(usd * SELL / C.ATM_YEAR_CNY), "calendar year"),
                 basis="Year count only", excluded="Card, ATM and network charges (not read)")
    elif m == "cash":
        r.update(spread_usd=q2(spread_cny / SELL), est_cost_usd=q2(spread_cny / SELL),
                 rmb_in=q2(usd * SELL),
                 count=f"{ceil(usd / C.CASH_BANK_PERMIT)} with permit, {ceil(usd / C.CASH_NO_PERMIT)} without",
                 time="One exit per trip", basis="Bank of China cash spread only",
                 excluded="Travel, time and loss risk")
    elif m == "dividend":
        tax = usd / 9          # 10% of a gross dividend of usd / 0.9
        r.update(tax_usd=q2(tax), est_cost_usd=q2(tax), rmb_in=q2(usd / D("0.9") * SELL),
                 count="1 dividend", time="One transaction",
                 basis="PRC dividend tax at the 10% treaty cap",
                 excluded="Company tax, bank spread and fees (not read)")
    elif m == "stay":
        r.update(est_cost_usd=D("0.00"), count="No transfer", time="No waiting",
                 basis="No conversion", excluded="Exchange-rate movement; yearly U.S. filings continue")
    elif m == "fine":
        r.update(fine_ordinary_max_usd=q2(usd * D(C.FINE_ORDINARY)),
                 fine_serious_max_usd=q2(usd * D(C.FINE_SERIOUS)),
                 count="Prohibited", time="Prohibited", basis="Fine exposure under the Regulations",
                 excluded="Watch list, confiscation, criminal liability, counterparty loss")
    elif m == "blank":
        r.update(count="Prohibited", time="Prohibited", basis="No figure read",
                 excluded="Legal exposure not quantified in the notice")
    else:
        raise ValueError(m)
    if r["est_cost_usd"] is not None:
        r["pct"] = (r["est_cost_usd"] / usd * 100).quantize(D("0.001"), rounding=ROUND_HALF_UP)
    return r


COSTS = {m["id"]: [row_for(m, t) for t in TIERS] for m in C.METHODS}
METHOD = {m["id"]: m for m in C.METHODS}


def headline(r):
    if r["fine_ordinary_max_usd"] is not None:
        return f"Fine up to {money(r['fine_ordinary_max_usd'], 0)}"
    return money(r["est_cost_usd"]) if r["est_cost_usd"] is not None else ""


def breakdown(r):
    parts = []
    if r["spread_usd"] is not None:
        parts.append(f"spread {money(r['spread_usd'])}")
    if r["fee_usd"] is not None:
        parts.append(f"fees {money(r['fee_usd'])}")
    if r["tax_usd"] is not None:
        parts.append(f"tax {money(r['tax_usd'])}")
    if r["fine_serious_max_usd"] is not None:
        parts.append(f"serious cases up to {money(r['fine_serious_max_usd'], 0)}")
    return " + ".join(parts) if r["fine_serious_max_usd"] is None else "; ".join(parts)


# --------------------------------------------------------------------------- html helpers
NAV = [("index.html", "Summary"), ("questions.html", "Decide"), ("methods.html", "Methods"),
       ("costs.html", "Costs"), ("taxes.html", "Tax and penalties"), ("sources.html", "Sources"),
       ("flagged.html", "Flagged for Review"), ("repo-review.html", "Repo review")]
KIND = {"lawful": ("ok", "Lawful"), "conditional": ("cond", "Conditional"),
        "none": ("none", "No conversion"), "unlawful": ("bad", "Prohibited")}


def chips(ids):
    return " ".join(
        f'<a class="src" href="{E(SRC[i]["url"])}" title="{E(SRC[i]["issuer"] + ": " + SRC[i]["title"])}" '
        f'rel="noopener noreferrer">{i}</a>' for i in ids)


def td(label, inner, cls=""):
    c = f' class="{cls}"' if cls else ""
    return f'<td data-label="{E(label)}"{c}>{inner}</td>'


def blank():
    return '<span class="blank" title="Not confirmed from an official source">—</span>'


def cell(text):
    return E(text) if text else blank()


def table(headers, rows, cls="cards"):
    head = "".join(f"<th scope=\"col\">{E(h)}</th>" for h in headers)
    return f'<div class="tw"><table class="{cls}"><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


def page(fname, title, lede, body):
    cur = ' aria-current="page"'
    nav = "".join(f'<a href="{h}"{cur if h == fname else ""}>{E(t)}</a>' for h, t in NAV)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)} · China money</title>
<meta name="description" content="{E(lede)}">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="top">
<a class="brand" href="index.html">China money</a>
<nav aria-label="Sections">{nav}</nav>
</header>
<main>
<h1>{E(title)}</h1>
<p class="lede">{E(lede)}</p>
{body}
</main>
<footer>
<p>Research, not tax or legal advice. Sources read {C.READ_DATE}. Dollar figures use Bank of China's posted rate at 10:25:02 Beijing time that day and change when the rate does. A dash means the value was not confirmed from an official source.</p>
<p><a href="../index.html">All views in this repository</a> · <a href="flagged.html">Flagged for Review</a> · <a href="sources.html">Sources</a></p>
</footer>
<script src="assets/app.js"></script>
</body>
</html>
"""


def cost_rows(mid, tiers=None, with_method=False):
    out = []
    for r in COSTS[mid]:
        if tiers and r["usd"] not in tiers:
            continue
        m = METHOD[mid]
        step = "" if r["usd"] % 50000 == 0 else ' class="minor"'
        cells = [td("Amount", f"<strong>${r['usd']:,}</strong>")]
        if with_method:
            cells.append(td("Method", f'<a href="methods.html#{mid}">{E(m["name"])}</a>'))
        cells += [
            td("Estimated cost", E(headline(r)) if headline(r) else blank(), "num key"),
            td("Share of amount", f"{r['pct']}%" if r["pct"] is not None else blank(), "num"),
            td("RMB you pay in", E(rmb(r["rmb_in"])) if r["rmb_in"] is not None else blank(), "num"),
            td("Transfers", cell(r["count"])),
            td("Time", cell(r["time"])),
            td("Made up of", cell(breakdown(r))),
            td("Sources", chips(m["src"])),
        ]
        out.append(f"<tr{step}>{''.join(cells)}</tr>")
    return out


COST_HEAD = ["Amount", "Estimated cost", "Share of amount", "RMB you pay in", "Transfers", "Time", "Made up of", "Sources"]
MILESTONES = [10000, 50000, 100000, 200000, 300000, 400000]


def compare_rows(tiers):
    """Amount by route: the fully priced lawful routes beside the fine for a prohibited one."""
    out = []
    for t in tiers:
        idx = t // 10000 - 1
        a, b, d, f = (COSTS[k][idx] for k in ("M01", "M02", "M06", "M14"))
        step = "" if t % 50000 == 0 else ' class="minor"'
        out.append(
            f"<tr{step}>" + td("Amount", f"<strong>${t:,}</strong>")
            + td("One documented wire", f"{E(headline(a))}<small>{a['pct']}%</small>", "num key")
            + td("Yearly quota wires", f"{E(headline(b))}<small>{E(b['time'])}</small>", "num")
            + td("Cash, spread only", f"{E(headline(d))}<small>{E(d['count'])}</small>", "num")
            + td("Prohibited route", f"{E(headline(f))}<small>30% of the amount</small>", "num bad")
            + td("RMB needed", E(rmb(D(t) * SELL)), "num")
            + td("Sources", chips(["S17", "S18", "S06"])) + "</tr>")
    return out


COMPARE_HEAD = ["Amount", "One documented wire", "Yearly quota wires", "Cash, spread only", "Prohibited route", "RMB needed", "Sources"]


# --------------------------------------------------------------------------- pages
def p_index():
    c10, c100, c400 = COSTS["M01"][0], COSTS["M01"][9], COSTS["M01"][39]
    kpis = f"""<div class="kpis">
<div class="kpi"><p class="k">Tax on converting</p><p class="v">None found</p><p class="s">The bank wants proof of source and of tax paid on the income. {chips(['S01', 'S06'])}</p></div>
<div class="kpi"><p class="k">Bank of China sells dollars at</p><p class="v">¥{SELL} per $1</p><p class="s">Posted 11 Nov 2026, 10:25 Beijing. {chips(['S17'])}</p></div>
<div class="kpi"><p class="k">Cost to send $100,000</p><p class="v">{money(c100['est_cost_usd'])}</p><p class="s">{c100['pct']}% by one documented wire; {money(c10['est_cost_usd'])} for $10,000, {money(c400['est_cost_usd'])} for $400,000. {chips(['S17', 'S18'])}</p></div>
<div class="kpi warn"><p class="k">Biggest unknown</p><p class="v">Source of the money</p><p class="s">It decides the route and whether any PRC tax is still owed. <a href="questions.html">See the questions</a></p></div>
</div>"""
    answer = f"""<section class="panel">
<h2>The short answer</h2>
<ol class="answer">
<li><strong>Converting is not what gets taxed.</strong> Nothing in the PRC exchange rules read today taxes the exchange itself. Banks convert a foreigner's lawful income on ID plus papers that show the amount, including tax vouchers. {chips(['S01', 'S06'])}</li>
<li><strong>The tax, if any, is PRC income tax on how the money was earned:</strong> 3% to 45% on wages, 20% on dividends, rent and asset sales, and none at present on bank interest. If it was already withheld, converting adds no PRC tax. {chips(['S14', 'S15'])}</li>
<li><strong>The cheapest lawful route is one documented bank wire.</strong> At Bank of China's posted rate and fees it costs about 0.2% to 0.5% of the amount, before any fees taken by other banks. {chips(['S17', 'S18'])}</li>
<li><strong>The U.S. taxes the income when earned and credits PRC tax paid on it.</strong> Moving the money is not a new taxable event, but a currency gain above $200 is recognised, and the yuan is stronger now than in 2023 to 2025. {chips(['S28', 'S34', 'S21', 'S29'])}</li>
<li><strong>The large U.S. penalties are for missed forms, not for the transfer:</strong> FBAR, Form 8938 and Form 3520. Bring those up to date first. {chips(['S22', 'S23', 'S24', 'S25'])}</li>
</ol>
</section>"""
    top = []
    for mid, why in (("M01", "Lowest cost; the whole amount at once if the income papers exist."),
                     ("M04", "Same salary-and-tax-record case, done online; cost shown only in a quote."),
                     ("M02", "ID only, but only for Chinese citizens and permanent resident card holders, and slow."),
                     ("M08", "For an inheritance; needs SAFE approval."),
                     ("M07", "For former mainland residents moving pre-emigration assets; needs SAFE approval."),
                     ("M06", "Small sums only; many trips for large ones.")):
        m, r = METHOD[mid], COSTS[mid][9]
        k = KIND[m["kind"]]
        top.append("<tr>" + td("Route", f'<a href="methods.html#{mid}"><strong>{E(m["name"])}</strong></a>')
                   + td("Status", f'<span class="chip {k[0]}">{k[1]}</span>')
                   + td("Cost for $100,000", E(headline(r)) if headline(r) else blank(), "num key")
                   + td("Time for $100,000", cell(r["time"]))
                   + td("Why", E(why)) + td("Sources", chips(m["src"])) + "</tr>")
    ranked = "<section><h2>Routes worth considering, in order</h2>" + table(
        ["Route", "Status", "Cost for $100,000", "Time for $100,000", "Why", "Sources"], top) + \
        '<p class="note">All 17 routes, including the four prohibited ones, are on the <a href="methods.html">Methods</a> page.</p></section>'
    costs = "<section><h2>What it costs at Bank of China's published prices</h2>" + table(
        COMPARE_HEAD, compare_rows(MILESTONES), "wide") + \
        '<p class="note">Spread plus wire fees. Not included: fees taken by intermediary and receiving banks, and any tax. Every $10,000 step for every route is on the <a href="costs.html">Costs</a> page.</p></section>'
    need = "".join(
        "<tr>" + td("Question", f'<strong>{E(x["q"])}</strong>') + td("How to find out", E(x["find"]))
        + td("Sources", chips(x["src"])) + "</tr>" for x in C.QUESTIONS[:5])
    needs = "<section><h2>What has to be answered before deciding</h2>" + table(
        ["Question", "How to find out", "Sources"], [need]) + \
        f'<p class="note">The full list of {len(C.QUESTIONS)} questions, with what is known and unknown, is on the <a href="questions.html">Decide</a> page.</p></section>'
    tiles = "".join(f'<a class="tile" href="{h}"><strong>{E(t)}</strong><span>{E(d)}</span></a>' for h, t, d in (
        ("questions.html", "Decide", f"{len(C.QUESTIONS)} questions: known, unknown, how to find out"),
        ("methods.html", "Methods", f"{len(C.METHODS)} routes with pros, cons and steps"),
        ("costs.html", "Costs", "Every $10,000 from $10,000 to $400,000"),
        ("taxes.html", "Tax and penalties", f"{len(C.LAYERS)} layers of the conversion penalty"),
        ("sources.html", "Sources", f"{len(C.SOURCES)} official pages read today"),
        ("flagged.html", "Flagged for Review", f"{len(C.FLAGS)} open items and blanks"),
        ("repo-review.html", "Repo review", f"{len(C.REVIEW)} earlier claims rechecked"),
    ))
    return page("index.html", "Getting money out of China as a U.S. citizen",
                "What blocks the conversion, the cheapest lawful way through, and what it costs from $10,000 to $400,000.",
                kpis + answer + ranked + costs + needs + f'<section><h2>Sections</h2><div class="tiles">{tiles}</div></section>')


def p_questions():
    rows = ["<tr id=\"%s\">" % x["id"] + td("Question", f'<strong>{E(x["q"])}</strong>')
            + td("What we know", E(x["known"])) + td("What we do not know", E(x["unknown"]))
            + td("How to find out", E(x["find"])) + td("Sources", chips(x["src"])) + "</tr>" for x in C.QUESTIONS]
    return page("questions.html", "Questions to answer before deciding",
                "No route or tax figure is personal until these are answered. Each has what the sources say, what is missing and how to get it.",
                table(["Question", "What we know", "What we do not know", "How to find out", "Sources"], rows))


def p_methods():
    rows, cards = [], []
    for m in C.METHODS:
        k, r = KIND[m["kind"]], COSTS[m["id"]][9]
        rows.append("<tr>" + td("Route", f'<a href="#{m["id"]}"><strong>{E(m["name"])}</strong></a>')
                    + td("Status", f'<span class="chip {k[0]}">{k[1]}</span>')
                    + td("Who it fits", E(m["fits"])) + td("Limit", E(m["limit"]))
                    + td("Cost for $100,000", E(headline(r)) if headline(r) else blank(), "num key")
                    + td("Sources", chips(m["src"])) + "</tr>")
        pros = "".join(f"<li>{E(x)}</li>" for x in m["pros"]) or "<li>None.</li>"
        cons = "".join(f"<li>{E(x)}</li>" for x in m["cons"])
        steps = "".join(f"<li>{E(x)}</li>" for x in m["steps"])
        cards.append(f"""<article class="method" id="{m['id']}">
<h3>{E(m['name'])} <span class="chip {k[0]}">{k[1]}</span></h3>
<p><strong>Who it fits:</strong> {E(m['fits'])} <strong>Limit:</strong> {E(m['limit'])}</p>
<div class="pc"><div><h4>For</h4><ul>{pros}</ul></div><div><h4>Against</h4><ul>{cons}</ul></div></div>
<h4>Step by step</h4><ol>{steps}</ol>
<p class="note">Sources: {chips(m['src'])} · <a href="costs.html#cost-{m['id']}">Cost at every $10,000 step</a></p>
</article>""")
    return page("methods.html", "Every way to turn RMB into dollars",
                f"{len(C.METHODS)} routes: {sum(1 for m in C.METHODS if m['kind'] != 'unlawful')} lawful or conditional and {sum(1 for m in C.METHODS if m['kind'] == 'unlawful')} prohibited, with who each fits, its limit, and the steps.",
                table(["Route", "Status", "Who it fits", "Limit", "Cost for $100,000", "Sources"], rows)
                + '<h2>Pros, cons and steps</h2>' + "".join(cards))


def p_costs():
    inputs = [
        ("Dollar selling rate", f"¥{SELL} per $1", "Bank of China board, 11 Nov 2026 10:25:02 Beijing", ["S17"]),
        ("Dollar buying rate", f"¥{BUY} per $1", "Same board", ["S17"]),
        ("Spread charged to a buyer", f"¥{HALF} per $1 ({(HALF / MID * 100).quantize(D('0.001'))}%)", "Half the gap between the two posted rates", ["S17"]),
        ("Wire commission", f"0.1%, at least ¥{C.BOC_MIN}, at most ¥{C.BOC_MAX}", "Bank of China personal e-banking table", ["S18"]),
        ("Cable fee", f"¥{C.BOC_CABLE} per wire", "Outside Hong Kong, Macao and Taiwan", ["S18"]),
        ("Yearly quota", f"${C.QUOTA_USD:,} per person", "Domestic individuals and permanent resident card holders", ["S07", "S02"]),
        ("Overseas ATM cap", f"¥{C.ATM_YEAR_CNY:,} a year, ¥{C.ATM_DAY_CNY:,} a day per card", "Per person across all cards", ["S04"]),
        ("Cash per exit", f"${C.CASH_NO_PERMIT:,} without a permit, ${C.CASH_BANK_PERMIT:,} with a bank permit", "", ["S05"]),
        ("Wise per transfer", f"¥{C.WISE_PER_TRANSFER_CNY:,}", "From a Chinese bank app", ["S20"]),
        ("HSBC China wire fee", f"0.1%, at least ¥{C.HSBC_MIN}, at most ¥{C.HSBC_MAX}, plus ¥{C.HSBC_CABLE} cable", "Premier and Advance; free for Private Banking individuals", ["S19"]),
        ("Emigrant and inheritance transfers", "One payment or several after SAFE approval", "Instalment rule removed in 2014", ["S32", "S11"]),
        ("Dividend tax cap", "10% of the gross dividend", "U.S.–China treaty, Article 9", ["S30"]),
        ("Fines for prohibited routes", "Up to 30%; 30% to 100% if serious", "Regulations, Articles 39, 40, 45", ["S06"]),
    ]
    irows = ["<tr>" + td("Input", f"<strong>{E(a)}</strong>") + td("Value", E(b), "num key") + td("Note", cell(c))
             + td("Sources", chips(s)) + "</tr>" for a, b, c, s in inputs]
    opts = "".join(f'<option value="cost-{m["id"]}">{m["id"]} · {E(m["name"])}</option>' for m in C.METHODS)
    blocks = []
    for i, m in enumerate(C.METHODS):
        k = KIND[m["kind"]]
        r = COSTS[m["id"]][0]
        blocks.append(
            f'<details class="costblock" id="cost-{m["id"]}"{" open" if i == 0 else ""}>'
            f'<summary><span class="chip {k[0]}">{k[1]}</span> <strong>{E(m["name"])}</strong>'
            f'<small>{E(r["basis"])}. Not included: {E(r["excluded"].lower())}.</small></summary>'
            + table(COST_HEAD, cost_rows(m["id"]), "wide") + "</details>")
    body = f"""<section><h2>Priced routes side by side</h2>
<p class="note">Spread plus wire fees at Bank of China's published prices, beside the fine the Regulations allow for a prohibited route. Not included: fees taken by intermediary and receiving banks, and any tax. Scroll the table sideways for more columns.</p>
<p class="controls"><label><input type="checkbox" id="only50"> Show every $50,000 only</label>
<a class="btn" href="exports/costs.csv">Download all rows (CSV)</a></p>
{table(COMPARE_HEAD, compare_rows([int(t) for t in TIERS]), 'wide')}</section>
<section><h2>Every route, every $10,000</h2>
<p class="controls"><label>Jump to a route <select id="jump"><option value="">Choose…</option>{opts}</select></label></p>
{''.join(blocks)}</section>
<section class="panel"><h2>How the estimate is made</h2>
<p>For each amount, the cost is the bank's exchange spread plus its wire fees, using only prices the bank publishes. The spread is half the gap between the posted buying and selling rates. Fees taken by intermediary and receiving banks are not published, so they are left out and flagged, as is any tax. Where a provider publishes no price, the cost is a dash and only the number of transfers or the time is shown.</p></section>
<section><h2>Inputs</h2>{table(['Input', 'Value', 'Note', 'Sources'], irows)}</section>"""
    return page("costs.html", "Cost of moving $10,000 to $400,000",
                f"{len(C.METHODS)} routes at {len(TIERS)} amounts, priced from Bank of China's posted rate and fee table on 11 November 2026.", body)


def p_taxes():
    rows = ["<tr>" + td("Layer", f'<strong>{E(x["layer"])}</strong>') + td("Charged by", E(x["who"]))
            + td("Amount", E(x["amount"]), "key") + td("What it means", E(x["note"]))
            + td("Sources", chips(x["src"])) + "</tr>" for x in C.LAYERS]
    grows = []
    for y in ("2025", "2024", "2023", "2022", "2021"):
        rate = D(C.IRS_AVG[y])
        basis = D(100000) * SELL / rate
        gain = D(100000) - basis
        grows.append("<tr>" + td("RMB received in", f"<strong>{y}</strong>") + td("IRS average rate", f"¥{rate} per $1", "num")
                     + td("Dollar value when received", money(basis), "num")
                     + td("Gain on converting $100,000 today", money(gain) if gain > 0 else "No gain", "num key")
                     + td("U.S. tax on the gain", blank())
                     + td("Sources", chips(["S29", "S17", "S21"])) + "</tr>")
    body = f"""<section><h2>The conversion penalty, layer by layer</h2>
{table(['Layer', 'Charged by', 'Amount', 'What it means', 'Sources'], rows)}</section>
<section><h2>Currency gain: a worked illustration</h2>
<p>RMB {q2(D(100000) * SELL):,.2f} buys $100,000 at today's Bank of China rate. If that RMB was received in an earlier year, its dollar value then was lower when the yuan was weaker. The difference is the gain. The year averages stand in for your actual deposit dates, which are unknown; the tax depends on your return and is left blank.</p>
{table(['RMB received in', 'IRS average rate', 'Dollar value when received', 'Gain on converting $100,000 today', 'U.S. tax on the gain', 'Sources'], grows, 'wide')}</section>
<section class="panel"><h2>How to keep the total lowest</h2>
<ol class="answer">
<li>Prove the PRC tax already paid rather than paying again: collect the tax records for the years the income was earned. {chips(['S01'])}</li>
<li>Use one documented bank wire instead of many small transfers; the fee is capped per wire. {chips(['S18'])}</li>
<li>Claim PRC income tax as a foreign tax credit on the U.S. return for the year the income was earned. {chips(['S34', 'S28'])}</li>
<li>Record the dollar value of each deposit on its date so the currency gain is measured, not guessed. {chips(['S21', 'S29'])}</li>
<li>File any missing FBAR, Form 8938 or Form 3520 before the money moves; the streamlined procedures cap the cost for non-wilful cases. {chips(['S22', 'S24', 'S25', 'S31', 'S33'])}</li>
<li>Stay away from the prohibited routes: a 30% fine is more than fifty times the lawful cost. {chips(['S06'])}</li>
</ol></section>"""
    return page("taxes.html", "Tax and penalties",
                "Where the cost of getting money out really comes from: the tax on the income, the bank's charges, U.S. tax and reporting, and fines for prohibited routes.", body)


def p_sources():
    how = {"fetched": "Opened; quoted passage checked", "partial": "Opened; read in part (see F18)"}
    rows = [f'<tr id="{s["id"]}">' + td("ID", f"<strong>{s['id']}</strong>")
            + td("Source", f'<a href="{E(s["url"])}" rel="noopener noreferrer">{E(s["title"])}</a><small>{E(s["issuer"])} · {E(s["date"])}</small>')
            + td("What it says", E(s["means"])) + td("Text read", f'<q>{E(s["quote"])}</q>')
            + td("How read today", E(how[s["how"]])) + "</tr>" for s in C.SOURCES]
    nf = sum(1 for s in C.SOURCES if s["how"] == "fetched")
    return page("sources.html", "Sources",
                f"{len(C.SOURCES)} official pages opened on 11 November 2026, with the sentence each claim rests on. {len(C.SOURCES) - nf} long documents were read in part. Follow each link to check it yourself.",
                table(["ID", "Source", "What it says", "Text read", "How read today"], rows))


def p_flagged():
    rows = [f'<tr id="{x["id"]}">' + td("ID", f"<strong>{x['id']}</strong>") + td("Item", E(x["item"]))
            + td("Status", f'<span class="chip cond">{E(x["status"])}</span>') + td("Detail", E(x["detail"]))
            + td("Sources", chips(x["src"])) + "</tr>" for x in C.FLAGS]
    return page("flagged.html", "Flagged for Review",
                f"{len(C.FLAGS)} items that are unknown, left blank, or not fully confirmed today. None of them blocks using the rest of the site.",
                table(["ID", "Item", "Status", "Detail", "Sources"], rows))


def p_review():
    cls = lambda r: "ok" if r == "Confirmed" else ("bad" if r == "Irregular" else "cond")
    rows = [f'<tr id="{x["id"]}">' + td("ID", f"<strong>{x['id']}</strong>") + td("Where", E(x["where"]))
            + td("Claim in the repo", E(x["claim"])) + td("Result", f'<span class="chip {cls(x["result"])}">{E(x["result"])}</span>')
            + td("Note", E(x["note"])) + td("Sources", chips(x["src"])) + "</tr>" for x in C.REVIEW]
    n_ok = sum(1 for x in C.REVIEW if x["result"] == "Confirmed")
    return page("repo-review.html", "Repo review",
                f"{len(C.REVIEW)} load-bearing claims from earlier work in this repository, rechecked against the pages read today: {n_ok} confirmed as written, {len(C.REVIEW) - n_ok} with a correction, caveat or irregularity.",
                table(["ID", "Where", "Claim in the repo", "Result", "Note", "Sources"], rows))


def summary_md():
    c = COSTS["M01"]
    lines = [
        "# Executive summary", "",
        f"Sources read {C.READ_DATE}. Research, not tax or legal advice. Full site: [index.html](index.html).", "",
        "## Bottom line", "",
        "1. No tax on the act of converting RMB to dollars was found in the PRC exchange rules read. Banks convert a foreigner's lawful China income on ID plus papers showing the amount, including tax vouchers ([SAFE](" + SRC["S01"]["url"] + ")).",
        "2. The tax that matters is PRC income tax on how the money was earned: 3%–45% on wages, 20% on dividends, rent and asset sales, none at present on bank interest ([tax law](" + SRC["S14"]["url"] + ")). If it was withheld already, converting adds none.",
        f"3. Cheapest lawful route: one documented bank wire. At Bank of China's posted rate (¥{SELL} per $1, 11 Nov 2026 10:25 Beijing) and fee table it costs {money(c[0]['est_cost_usd'])} for $10,000, {money(c[9]['est_cost_usd'])} for $100,000 and {money(c[39]['est_cost_usd'])} for $400,000, before other banks' fees ([rate]({SRC['S17']['url']}), [fees]({SRC['S18']['url']})).",
        "4. The U.S. taxes worldwide income when earned and credits PRC tax on it; currency gain above $200 on conversion is recognised ([IRS](" + SRC["S28"]["url"] + "), [foreign tax credit](" + SRC["S34"]["url"] + "), [26 U.S.C. 988(e)](" + SRC["S21"]["url"] + ")).",
        "5. The large U.S. penalties are for missed FBAR, Form 8938 and Form 3520 filings, not for the transfer.", "",
        "## Cost by amount (one documented wire, Bank of China published prices)", "",
        "| Amount | Estimated cost | Share | RMB you pay in |", "|---|---|---|---|",
    ]
    for t in MILESTONES:
        r = c[t // 10000 - 1]
        lines.append(f"| ${t:,} | {money(r['est_cost_usd'])} | {r['pct']}% | {rmb(r['rmb_in'])} |")
    lines += ["", "## Still unknown", ""] + [f"- {x['q']} {x['find']}" for x in C.QUESTIONS[:6]]
    lines += ["", f"See [flagged.html](flagged.html) for {len(C.FLAGS)} open items and [repo-review.html](repo-review.html) for {len(C.REVIEW)} rechecked claims.", ""]
    return "\n".join(lines)


def main():
    pages = {"index.html": p_index(), "questions.html": p_questions(), "methods.html": p_methods(),
             "costs.html": p_costs(), "taxes.html": p_taxes(), "sources.html": p_sources(),
             "flagged.html": p_flagged(), "repo-review.html": p_review()}
    for name, text in pages.items():
        (HERE / name).write_text(text, encoding="utf-8")
    (HERE / "EXECUTIVE_SUMMARY.md").write_text(summary_md(), encoding="utf-8")
    data, exp = HERE / "data", HERE / "exports"
    data.mkdir(exist_ok=True)
    exp.mkdir(exist_ok=True)

    def dump(path, obj):
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")

    dump(data / "sources.json", C.SOURCES)
    dump(data / "methods.json", C.METHODS)
    dump(data / "layers.json", C.LAYERS)
    dump(data / "questions.json", C.QUESTIONS)
    dump(data / "flags.json", C.FLAGS)
    dump(data / "review.json", C.REVIEW)
    dump(data / "inputs.json", {k: getattr(C, k) for k in dir(C) if k.isupper() and k not in (
        "SOURCES", "METHODS", "LAYERS", "QUESTIONS", "FLAGS", "REVIEW")})
    flat = []
    for m in C.METHODS:
        for r in COSTS[m["id"]]:
            flat.append({**r, "method_name": m["name"], "status": m["kind"],
                         "source_urls": " ".join(SRC[i]["url"] for i in m["src"])})
    dump(exp / "costs.json", flat)
    cols = ["usd", "method", "method_name", "status", "est_cost_usd", "pct", "rmb_in", "count", "time",
            "spread_usd", "fee_usd", "tax_usd", "fine_ordinary_max_usd", "fine_serious_max_usd",
            "basis", "excluded", "source_urls"]
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    for r in flat:
        w.writerow({k: ("" if r[k] is None else r[k]) for k in cols})
    (exp / "costs.csv").write_text(buf.getvalue(), encoding="utf-8")
    print(f"wrote {len(pages)} pages, {len(flat)} cost rows, {len(C.SOURCES)} sources")


if __name__ == "__main__":
    main()
