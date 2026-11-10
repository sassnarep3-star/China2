#!/usr/bin/env python3
"""Static site generator for estimate-facf2fe9.

Inputs : data/*.json (sources, inputs, methods, tax, flags, repo_review,
         repo_scan) and data/costs.json written by model.py.
Outputs: index.html, costs.html, methods.html, tax.html, sources.html,
         repo-review.html, flagged.html, exports/costs.csv.

Deterministic: same inputs -> same bytes. No clock, no network.
"""
import csv
import html
import io
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
REPO = "https://github.com/sassnarep3-star/China2/blob/main/"


def load(name):
    with open(DATA / name, encoding="utf-8") as fh:
        return json.load(fh)


SOURCES = load("sources.json")
SRC = {s["id"]: s for s in SOURCES["sources"]}
INPUTS = load("inputs.json")
METHODS = load("methods.json")
TAX = load("tax.json")
FLAGS = load("flags.json")["flags"]
FLAG = {f["id"]: f for f in FLAGS}
REVIEW = load("repo_review.json")["findings"]
SCAN = load("repo_scan.json")
COSTS = load("costs.json")
META = COSTS["meta"]
ROWS = COSTS["rows"]
BY = {(r["method"], r["tier"]): r for r in ROWS}
M = {m["id"]: m for m in METHODS["methods"]}
CHECK = [10000, 50000, 100000, 200000, 400000]

SHORT = {
    "B01": "BOC rates", "B02": "ICBC rates", "B03": "CCB rates", "B04": "ABC rates", "B05": "CMB rates",
    "B06": "HSBC rates", "B07": "BoCom rates", "B08": "SAFE parity", "T01": "BOC fees", "T02": "ABC fees",
    "T03": "CMB fees", "T04": "CCB 2016 page", "T05": "CCB product page", "T06": "ICBC price list",
    "T07": "HSBC tariff", "T08": "CMB FAQ", "T09": "Wise guide", "T10": "Western Union",
    "R01": "FX Regulations", "R02": "PBOC Decree 3", "R03": "SAFE detailed rules", "R04": "SAFE FAQ 08",
    "R05": "SAFE Q&A 9", "R06": "SAFE FAQ 10", "R07": "SAFE card circular", "R08": "Cash-carry measures",
    "R09": "PBOC notice 18", "R10": "Tax-filing rule", "R11": "Tax-filing interpretation",
    "R12": "PBOC notice 16", "R13": "SAFE housing draft", "R14": "SAFE emigrant guide", "R15": "Yin Fa 42",
    "R16": "SAFE Shanghai", "X01": "Income Tax Law", "X02": "Cai Shui 132", "U01": "26 USC 988",
    "U02": "IRS rates", "U03": "IRS Pub. 525", "U04": "31 CFR 1010.821", "U05": "IRS FBAR",
    "U06": "IRS Form 8938", "U07": "IRS Form 3520", "U08": "CBP", "U09": "IRS Pub. 514",
    "U10": "IRS Form 2555", "U11": "IRS manual",
}
ROW_SRC = {
    "M01": ["B01", "T01"], "M02": ["B04", "T02"], "M03": ["B05", "T03"], "M04": ["B06", "T07"],
    "M05": ["B06", "T07"], "M06": ["B02", "T06"], "M07": ["B03", "T05"], "M08": ["B07"], "M09": ["T07"],
    "M10": ["R05", "R03", "B01", "T01"], "M11": ["R06", "B01", "T01"], "M12": ["R02", "B01", "T01"],
    "M13": ["R12", "B01", "T01"], "M14": ["R12", "B01", "T01"], "M15": ["T09"], "M16": ["R07", "T08"],
    "M17": ["R08", "B01"], "M18": ["R09"], "M19": ["T10"], "M20": ["R02"], "M21": ["R07"],
    "M22": ["X02", "U05"], "M23": ["R01"],
}
STATUS = {
    "estimated": ("ok", "Estimated"), "partial": ("warn", "Part published"),
    "unverified": ("bad", "Unverified"), "no transaction": ("mute", "No transaction"),
    "penalty exposure": ("bad", "Penalty exposure"), "verified": ("ok", "Verified"),
    "verified-limited": ("warn", "Verified, limited"), "reading": ("warn", "Reading"),
    "irregularity": ("bad", "Irregularity"), "gap": ("warn", "Gap"), "consistent": ("ok", "Consistent"),
    "needs review": ("warn", "Needs review"), "note": ("mute", "Note"),
}
NAV = [("index.html", "Overview"), ("costs.html", "Costs"), ("methods.html", "Methods"), ("tax.html", "Tax"),
       ("sources.html", "Sources"), ("repo-review.html", "Repo review"), ("flagged.html", "Flagged for Review")]


def esc(s):
    return html.escape(str(s), quote=True)


def ext(url, label):
    return f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(label)}</a>'


def links(ids):
    return " · ".join(ext(SRC[i]["url"], SHORT[i]) for i in ids)


def pill(status):
    cls, label = STATUS[status]
    return f'<span class="pill {cls}">{esc(label)}</span>'


def flag_links(ids):
    return " ".join(f'<a class="flag" href="flagged.html#{i}">{i}</a>' for i in ids)


def usd(v, cents=True):
    if v is None:
        return None
    x = float(v)
    s = f"{abs(x):,.2f}" if cents else f"{abs(x):,.0f}"
    return ("-$" if x < 0 else "$") + s


def pct2(v):
    return f"{float(v):.2f}%"


def blank():
    return '<td class="blank" title="Not confirmed from an official source: left blank">—</td>'


SINGULAR = {
    "calendar years, one wire each": "calendar year, one wire",
    "wires over two years": "wire",
    "transfers of at most ¥300,000": "transfer of at most ¥300,000",
    "calendar years at ¥100,000 a year": "calendar year at ¥100,000 a year",
    "trips with a bank permit": "trip with a bank permit",
    "trips at ¥20,000 a trip": "trip at ¥20,000 a trip",
}


def count_text(r):
    if not r["count"]:
        return None
    unit = SINGULAR.get(r["count_unit"], r["count_unit"]) if r["count"] == 1 else r["count_unit"]
    return f'{r["count"]} {unit}'


def cell(v, cls="num"):
    return blank() if v is None or v == "" else f'<td class="{cls}">{esc(v)}</td>'


def table(head, body_rows, cls=""):
    th = "".join(f"<th scope=\"col\">{esc(h)}</th>" for h in head)
    return (f'<div class="table-wrap"><table class="{cls}"><thead><tr>{th}</tr></thead>'
            f'<tbody>{"".join(body_rows)}</tbody></table></div>')


def page(fname, title, lede, body):
    cur = ' aria-current="page"'
    nav = "".join(f'<a href="{h}"{cur if h == fname else ""}>{esc(t)}</a>' for h, t in NAV)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · China money, published-rate estimates</title>
<meta name="description" content="{esc(lede)}">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="top">
<div class="wrap">
<p class="brand"><a href="index.html">China money</a> <span>published-rate estimates</span></p>
<nav aria-label="Sections">{nav}</nav>
</div>
</header>
<main class="wrap">
<h1>{esc(title)}</h1>
<p class="lede">{esc(lede)}</p>
{body}
</main>
<footer class="wrap">
<p>General information, not tax or legal advice. Rates and fees were read from the publishers' own pages on 10 November 2026 and will change. Nothing here is a quote from a bank. A value that could not be confirmed from an official page is left blank and listed under <a href="flagged.html">Flagged for Review</a>.</p>
<p><a href="../index.html">All sections of this site</a> · Session <code>arena/facf2fe9-china2</code> · <a href="exports/costs.csv">Download the cost table (CSV)</a></p>
</footer>
<script src="assets/app.js"></script>
</body>
</html>
"""


def cheapest(tier):
    best = None
    for m in METHODS["methods"]:
        if m["category"] != "A":
            continue
        r = BY[(m["id"], tier)]
        if r["status"] == "estimated" and (best is None or float(r["total_usd"]) < float(best[1]["total_usd"])):
            best = (m, r)
    return best


def short_name(m):
    return m["name"].split(" — ")[0]


# ------------------------------------------------------------------ index
def build_index():
    fx = {f["year"]: f for f in COSTS["fx_gain"]}
    c10, c100, c400 = cheapest(10000), cheapest(100000), cheapest(400000)
    n_flags = len(FLAGS)
    n_blank = sum(1 for r in ROWS if r["total_usd"] is None and r["status"] in ("partial", "unverified"))
    n_est = sum(1 for r in ROWS if r["status"] == "estimated")
    boc, abc_, cmb, hs = (BY[("M01", 400000)], BY[("M02", 400000)], BY[("M03", 400000)], BY[("M04", 400000)])
    cards = f"""
<section class="cards" aria-label="Key figures">
<div class="card"><p class="k">Cheapest published wire, $10,000</p><p class="v">{usd(c10[1]['total_usd'])}</p><p class="s">{esc(short_name(c10[0]))} · {pct2(c10[1]['pct'])} all-in</p></div>
<div class="card"><p class="k">Cheapest published wire, $100,000</p><p class="v">{usd(c100[1]['total_usd'])}</p><p class="s">{esc(short_name(c100[0]))} · {pct2(c100[1]['pct'])} all-in</p></div>
<div class="card"><p class="k">Cheapest published wire, $400,000</p><p class="v">{usd(c400[1]['total_usd'])}</p><p class="s">{esc(short_name(c400[0]))} · {pct2(c400[1]['pct'])} all-in</p></div>
<div class="card alert"><p class="k">US exchange gain inside $400,000</p><p class="v">{usd(fx['2024']['per_400k'], False)}</p><p class="s">If the renminbi dates from 2024. Illustration — see <a href="tax.html#gain">Tax</a></p></div>
</section>"""
    summary = f"""
<section>
<h2>Summary</h2>
<ul class="points">
<li><strong>No Chinese tax on converting or wiring was found.</strong> What stops a conversion is missing proof that tax on the income was paid. A foreign passport holder may buy dollars with lawful renminbi income on showing ID and source papers that include tax vouchers ({links(['R04'])}). That tax is owed whether or not the money leaves. {flag_links(['F20'])}</li>
<li><strong>The cheapest lawful route is a documented wire from the bank that holds the money.</strong> At the rates and fees the banks published on 10 November 2026, $400,000 costs {usd(abc_['total_usd'])} at Agricultural Bank ({pct2(abc_['pct'])}), {usd(boc['total_usd'])} at Bank of China ({pct2(boc['pct'])}), {usd(cmb['total_usd'])} at China Merchants Bank ({pct2(cmb['pct'])}) and {usd(hs['total_usd'])} at HSBC China Premier ({pct2(hs['pct'])}). Almost all of it is the exchange-rate margin, not the fee.</li>
<li><strong>The larger number is on the US side.</strong> The yuan now trades near {META['gain_rate']} per dollar; the IRS yearly averages for 2023-2025 were 7.075-7.189. Of every $10,000 received today, about {usd(fx['2023']['per_10k'], False)}-{usd(fx['2024']['per_10k'], False)} would be exchange gain on renminbi acquired in those years — {usd(fx['2023']['per_400k'], False)}-{usd(fx['2024']['per_400k'], False)} on $400,000. How it is taxed depends on your facts ({links(['U01', 'U02'])}). {flag_links(['F21'])}</li>
<li><strong>Chinese income tax already paid is not lost.</strong> It can be credited against US tax on the same income, within limits ({links(['U09'])}). Interest on Chinese bank savings is currently exempt from Chinese income tax, but it is still US income ({links(['X02', 'U11'])}).</li>
<li><strong>Unlawful channels cost more than any tax.</strong> The fine is up to 30% of the amount, and 30%-100% in serious cases — up to $120,000 and $400,000 on $400,000 — with possible criminal liability ({links(['R01'])}).</li>
<li><strong>Report the account in the US.</strong> FBAR above $10,000 in total; Form 8938 above its thresholds; Form 3520 for a foreign bequest above $100,000. The FBAR penalty table runs to $16,536 per non-willful violation ({links(['U05', 'U04', 'U07'])}).</li>
<li><strong>Capped routes do not scale.</strong> ATM withdrawals stop at ¥100,000 a year (27 years for $400,000); cash stops at $10,000 a trip with a bank permit (40 trips); the $50,000 yearly quota is only for holders of a Chinese Foreign Permanent Resident ID (8 years).</li>
</ul>
</section>"""
    fit = [
        ("Pay or fees earned in China, tax withheld", "M01", "Documented wire from your own bank", "Chinese tax already paid; creditable in the US within limits", ["R04", "X01", "U09"]),
        ("Same, and you prefer an app", "M15", "Wise, to your own account", "Limit is after-tax salary on your tax records", ["T09"]),
        ("Money you brought in and exchanged within 24 months", "M11", "Convert it back with the original memo", "Not Chinese income", ["R06"]),
        ("Proceeds of selling housing", "M12", "Documented wire after title passes", "20% on the gain; cap is price less taxes", ["R02", "X01", "R13"]),
        ("Inherited assets", "M13", "SAFE approval, then wire", "US Form 3520 above $100,000", ["R12", "U07"]),
        ("Savings from before you emigrated", "M14", "Emigrant transfer, staged over two years", "Tax certificates for the assets", ["R12"]),
        ("You hold a Foreign Permanent Resident ID", "M10", "$50,000 a year on ID alone", "No tax on the purchase itself", ["R05", "R03"]),
        ("Income with unpaid tax or no papers", "", "Settle with the tax office first, then wire", "Tax is recovered with penalties if unpaid", ["R10"]),
        ("A few thousand dollars", "M16", "ATM abroad or cash within the limits", "No tax point; watch the yearly cap", ["R07", "R08"]),
    ]
    rows = []
    for sit, mid, route, taxpt, s in fit:
        cost = ""
        if mid and BY[(mid, 100000)]["status"] == "estimated":
            r = BY[(mid, 100000)]
            cost = f"{usd(r['total_usd'])} ({pct2(r['pct'])})"
        mlink = f'<a href="methods.html#{mid}">{esc(route)}</a>' if mid else esc(route)
        rows.append(f"<tr><td>{esc(sit)}</td><td>{mlink}</td>{cell(cost)}<td>{esc(taxpt)}</td><td class=\"src\">{links(s)}</td></tr>")
    fit_tbl = table(["Where the money came from", "Route", "Cost at $100,000", "Tax point", "Source"], rows)
    tiles = f"""
<section>
<h2>Sections</h2>
<div class="tiles">
<a class="tile" href="costs.html"><strong>Costs</strong><span>{len(M)} methods at every $10,000 step to $400,000. {n_est} cells estimated from published rates and fees.</span></a>
<a class="tile" href="methods.html"><strong>Methods</strong><span>Who may use each one, limits, steps, pros and cons.</span></a>
<a class="tile" href="tax.html"><strong>Tax</strong><span>Chinese tax by where the money came from; US rules; exchange-gain illustration.</span></a>
<a class="tile" href="sources.html"><strong>Sources</strong><span>{len(SRC)} official pages with the sentences relied on.</span></a>
<a class="tile" href="repo-review.html"><strong>Repo review</strong><span>{len(REVIEW)} findings from re-checking {SCAN['scanned_files']} files against today's readings.</span></a>
<a class="tile" href="flagged.html"><strong>Flagged for Review</strong><span>{n_flags} flags; {n_blank} cost cells left blank.</span></a>
</div>
</section>"""
    body = cards + summary + f"""
<section>
<h2>Which route fits</h2>
<p>The route is decided by where the renminbi came from, because that decides which papers exist. Cost is shown for Bank of China where a bank wire is used.</p>
{fit_tbl}
</section>""" + tiles + f"""
<section>
<h2>How the estimates are made</h2>
<p>Cost in dollars = amount × (the bank's dollar selling rate ÷ reference mid − 1) + (commission + cable fee in renminbi) ÷ reference mid. The reference mid, {META['reference_mid']} yuan per dollar, is the average of the mid-points of the five mainland boards read; it is arithmetic, not a published rate. Charges by intermediary banks and by your US bank are not included because the sending banks do not publish them.</p>
</section>"""
    return page("index.html", "Getting renminbi out of China: the cost at today's published rates",
                "For a US citizen with renminbi in a Chinese bank account. Bank rates and fees read on 10 November 2026, priced at every $10,000 step to $400,000, with the tax rules that decide the real cost.", body)


# ------------------------------------------------------------------ costs
VARYING_NOTE = {m["id"] for m in METHODS["methods"]
                if len({BY[(m["id"], t)]["note"] for t in META["tiers"]}) > 1}


def cost_row(m, r):
    c = []
    c.append(f'<th scope="row" class="num">{usd(r["tier"], False)}</th>')
    c.append(cell(usd(r["total_usd"])))
    c.append(cell(r["pct"] + "%" if r["pct"] is not None else None))  # three decimals in the ladder
    c.append(cell(f'¥{float(r["cny_needed"]):,.0f}' if r["cny_needed"] else None))
    c.append(cell(usd(r["spread_usd"])))
    c.append(cell(usd(r["fee_usd"])))
    c.append(cell(count_text(r), "txt"))
    fl = flag_links(m["flags"]) if r["status"] in ("partial", "unverified") else ""
    note = f' <span class="note">{esc(r["note"])}</span>' if r["note"] and m["id"] in VARYING_NOTE else ""
    c.append(f'<td class="txt">{pill(r["status"])} {fl}{note}</td>')
    c.append(f'<td class="src">{links(ROW_SRC[m["id"]])}</td>')
    return "<tr>" + "".join(c) + "</tr>"


def build_costs():
    brows = []
    for b in COSTS["boards"]:
        fl = {"HSBC": "F01", "BOCOM": "F02"}.get(b["key"], "")
        st = pill(b["status"]) + (" " + flag_links([fl]) if fl else "")
        brows.append("<tr>" + f'<th scope="row">{esc(b["bank"])}</th>' + cell(b["sell"]) + cell(b["buy"])
                     + cell(b["half_spread_pct"] + "%" if b["half_spread_pct"] else None)
                     + cell(b["sell_vs_ref_pct"] + "%" if b["sell_vs_ref_pct"] else None)
                     + cell(b["stamp"], "txt") + f'<td class="txt">{st}</td><td class="src">{links([b["source"]])}</td></tr>')
    boards = table(["Bank", "Sells $1 for (¥)", "Buys $1 for (¥)", "Margin over its own mid", "Selling rate vs reference mid",
                    "Published", "Status", "Source"], brows)
    tname = {"BOC": "Bank of China", "ABC": "Agricultural Bank of China", "CMB": "China Merchants Bank",
             "HSBC_PA": "HSBC China, Premier and Advance", "HSBC_PB": "HSBC China, Private Banking individual",
             "ICBC": "ICBC", "CCB": "China Construction Bank", "BOCOM": "Bank of Communications"}
    tflag = {"BOC": "F05", "ABC": "F06", "CMB": "F06", "ICBC": "F03", "CCB": "F04", "BOCOM": "F02"}
    trows = []
    for t in INPUTS["tariffs"]:
        has = t["pct"] is not None
        fl = tflag.get(t["key"], "")
        trows.append("<tr>" + f'<th scope="row">{esc(tname[t["key"]])}</th>'
                     + cell(f'{t["pct"] * 100:.1f}%' if has else None)
                     + cell(f'¥{t["min"]:,}' if has else None) + cell(f'¥{t["max"]:,}' if has else None)
                     + cell(f'¥{t["cable"]:,}' if has else None) + cell(t["as_of"], "txt")
                     + f'<td class="txt">{pill(t["status"])} {flag_links([fl]) if fl else ""}</td>'
                     + f'<td class="src">{links([t["source"]])}</td></tr>')
    tariffs = table(["Bank", "Commission", "Minimum", "Maximum", "Cable fee", "As of", "Status", "Source"], trows)

    crow = []
    rank = {"estimated": 0, "no transaction": 1, "partial": 2, "unverified": 3, "penalty exposure": 4}
    order = sorted(METHODS["methods"], key=lambda m: (rank[BY[(m["id"], 100000)]["status"]],
                                                      float(BY[(m["id"], 100000)]["total_usd"] or 0), m["id"]))
    for m in order:
        cells = [f'<th scope="row"><a href="#{m["id"]}">{esc(m["name"])}</a></th>']
        for t in CHECK:
            r = BY[(m["id"], t)]
            cells.append(cell(f'{usd(r["total_usd"], False)} · {float(r["pct"]):.2f}%' if r["total_usd"] is not None else None))
        r = BY[(m["id"], 100000)]
        fl = flag_links(m["flags"][:3]) if r["status"] in ("partial", "unverified") else ""
        cells.append(f'<td class="txt">{pill(r["status"])} {fl}</td>')
        cells.append(f'<td class="src">{links(ROW_SRC[m["id"]])}</td>')
        crow.append("<tr>" + "".join(cells) + "</tr>")
    compare = table(["Method", "$10,000", "$50,000", "$100,000", "$200,000", "$400,000", "Status", "Source"], crow, "compare")

    opts = "".join(f'<option value="{m["id"]}">{esc(m["id"] + " · " + m["name"])}</option>' for m in METHODS["methods"])
    blocks = []
    head = ["Amount", "All-in cost", "% of amount", "Renminbi needed", "Rate margin", "Bank fees", "How many, how long", "Status", "Source"]
    for m in METHODS["methods"]:
        rows = [cost_row(m, BY[(m["id"], t)]) for t in META["tiers"]]
        common = BY[(m["id"], 10000)]["note"] if m["id"] not in VARYING_NOTE else ""
        common = f' <span class="note">{esc(common)}</span>' if common else ""
        blocks.append(f'<details class="method" id="{m["id"]}"><summary><span class="mid">{m["id"]}</span> {esc(m["name"])}</summary>'
                      f'<p>{esc(m["summary"])}{common} <a href="methods.html#{m["id"]}">Steps, pros and cons</a></p>'
                      + table(head, rows, "ladder") + "</details>")
    body = f"""
<section>
<h2>Rates the banks published</h2>
<p>Yuan per US dollar, read from each bank's own board. The selling rate is what you pay to buy dollars. Reference mid: {META['reference_mid']} ({esc(META['reference_formula'])}). For context, the official central parity that day was {META['parity_cny_per_usd']} ({links(['B08'])}); every selling rate was below it, so the parity is not used as a yardstick.</p>
{boards}
</section>
<section>
<h2>Fees the banks published</h2>
<p>Personal outward telegraphic transfer, per wire, charged in renminbi.</p>
{tariffs}
</section>
<section>
<h2>All methods compared</h2>
<p>All-in cost and its share of the amount, cheapest first at $100,000. A blank cell means an input could not be confirmed from an official page; the flag says which.</p>
{compare}
</section>
<section>
<h2>Every $10,000 step, method by method</h2>
<p><label for="pick">Jump to a method</label> <select id="pick"><option value="">Choose…</option>{opts}</select> <button type="button" id="openall">Open all</button></p>
{"".join(blocks)}
</section>"""
    return page("costs.html", "What each method costs, $10,000 to $400,000",
                "Arithmetic on rates and fees the banks themselves published on 10 November 2026. Not a quote: the rate at the moment of the transaction prevails.", body)


# ------------------------------------------------------------------ methods
def build_methods():
    cats = METHODS["categories"]
    lawful = {"yes": ("ok", "Lawful"), "conditional": ("warn", "Conditional"), "no": ("bad", "Unlawful")}
    rows = []
    for m in METHODS["methods"]:
        cls, lab = lawful[m["lawful"]]
        r = BY[(m["id"], 100000)]
        cost = f'{usd(r["total_usd"], False)} · {float(r["pct"]):.2f}%' if r["total_usd"] is not None else None
        rows.append(f'<tr><th scope="row"><a href="#{m["id"]}">{esc(m["name"])}</a></th>'
                    f'<td class="txt"><span class="pill {cls}">{lab}</span></td>' + cell(cost)
                    + cell(m["limit"], "txt") + f'<td>{esc(m["pros"][0])}</td><td>{esc(m["cons"][0])}</td>'
                    f'<td class="src">{links(ROW_SRC[m["id"]])}</td></tr>')
    summary = table(["Method", "Status", "Cost at $100,000", "Limit", "Main advantage", "Main drawback", "Source"], rows)
    blocks = []
    for ck, cname in cats.items():
        blocks.append(f'<h2 id="cat-{ck}">{esc(cname)}</h2>')
        for m in [x for x in METHODS["methods"] if x["category"] == ck]:
            cls, lab = lawful[m["lawful"]]
            steps = "".join(f"<li>{esc(s)}</li>" for s in m["steps"])
            pros = "".join(f"<li>{esc(s)}</li>" for s in m["pros"])
            cons = "".join(f"<li>{esc(s)}</li>" for s in m["cons"])
            fl = f'<p class="flags">Flags: {flag_links(m["flags"])}</p>' if m["flags"] else ""
            limit = f"<p><strong>Limit.</strong> {esc(m['limit'])}</p>" if m["limit"] else ""
            blocks.append(f"""<article class="mcard" id="{m['id']}">
<h3><span class="mid">{m['id']}</span> {esc(m['name'])} <span class="pill {cls}">{lab}</span></h3>
<p>{esc(m['summary'])}</p>
<p><strong>Who.</strong> {esc(m['who'])}</p>
{limit}
<h4>Steps</h4><ol>{steps}</ol>
<div class="two"><div><h4>For</h4><ul>{pros}</ul></div><div><h4>Against</h4><ul>{cons}</ul></div></div>
<p class="src"><strong>Sources.</strong> {links(m['sources'])}</p>
{fl}
<p><a href="costs.html#{m['id']}">Cost at every $10,000 step</a></p>
</article>""")
    body = f"""
<section>
<h2>At a glance</h2>
{summary}
</section>
{"".join(blocks)}"""
    return page("methods.html", "Every way to turn renminbi into dollars, and how each works",
                f"{len(M)} entries: bank wires priced bank by bank, special legal routes, small-ticket routes, doing nothing, and the unlawful channels to refuse.", body)


# ------------------------------------------------------------------ tax
def build_tax():
    def rows_of(items, cols):
        out = []
        for it in items:
            tds = []
            for i, c in enumerate(cols):
                v = it.get(c, "")
                tds.append(f'<th scope="row">{esc(v)}</th>' if i == 0 else cell(v, "txt"))
            fl = flag_links([it["flag"]]) if it.get("flag") else ""
            tds.append(f'<td class="txt">{pill(it["status"])} {fl}</td>')
            tds.append(f'<td class="src">{links(it["sources"])}</td>')
            out.append("<tr>" + "".join(tds) + "</tr>")
        return out
    head = table(["Question", "Answer", "Status", "Source"], rows_of(TAX["headline"], ["q", "a"]))
    prc = table(["Where the money came from", "Chinese income tax", "Taxed on", "To convert it the bank needs", "Status", "Source"],
                rows_of(TAX["prc_by_source"], ["source", "tax", "base", "to_convert"]))
    proc = table(["Item", "Rule", "Figure", "Status", "Source"], rows_of(TAX["prc_procedure"], ["item", "rule", "number"]))
    us = table(["Item", "Rule", "Figure", "Status", "Source"], rows_of(TAX["us_rules"], ["item", "rule", "number"]))
    grows = []
    for f in COSTS["fx_gain"]:
        grows.append(f'<tr><th scope="row">{f["year"]}</th>' + cell(f["irs_avg"]) + cell(f["gain_pct"] + "%")
                     + cell(usd(f["per_10k"], False)) + cell(usd(f["per_100k"], False)) + cell(usd(f["per_400k"], False))
                     + f'<td class="txt">{pill("reading")} {flag_links(["F21"])}</td><td class="src">{links(["U02", "B01", "U01"])}</td></tr>')
    gain = table(["Year the renminbi was acquired", "IRS yearly average (¥ per $)", "Gain as share of dollars received",
                  "Per $10,000", "Per $100,000", "Per $400,000", "Status", "Source"], grows)
    body = f"""
<section>
<h2>The short answers</h2>
{head}
</section>
<section>
<h2>Chinese tax, by where the money came from</h2>
<p>The bank does not tax the conversion. It checks that the tax below was paid on the income, and limits the purchase to the documented amount.</p>
{prc}
</section>
<section>
<h2>Chinese procedure</h2>
{proc}
</section>
<section>
<h2>US rules</h2>
{us}
</section>
<section id="gain">
<h2>Exchange gain: an illustration</h2>
<p>You hold yuan; your tax currency is the dollar. If the yuan is worth more dollars on the day you convert than on the day you got it, the difference is an exchange gain. Gain = dollars received × (1 − {META['gain_rate']} ÷ the rate when acquired), using Bank of China's selling rate of {META['gain_rate']} for today and the IRS yearly average as a stand-in for the acquisition rate. A negative figure is a loss. This is not a tax bill: it shows the size of the amount the US rules apply to.</p>
{gain}
<p>Two rules decide the treatment ({links(['U01', 'U03'])}). In a personal transaction a gain of $200 or less is ignored and a larger one is reported as a capital gain. Otherwise disposing of a foreign-currency bank deposit is a section 988 transaction and the gain is ordinary income. Which applies depends on why the money was held; take the actual dates and rates to a US tax adviser.</p>
</section>"""
    return page("tax.html", "Tax: what is actually charged, and on what",
                "Converting and wiring are not taxed in themselves. The income behind the balance is, in China when earned and in the US as worldwide income, and the US also looks at exchange gain.", body)


# ------------------------------------------------------------------ sources
def build_sources():
    rows = []
    for s in SOURCES["sources"]:
        if s["method"].startswith("full"):
            st = '<span class="pill ok">Full page read</span>'
        elif s["method"].startswith("excerpt"):
            st = '<span class="pill warn">Excerpt</span> ' + flag_links(["F28"])
        else:
            st = '<span class="pill bad">Not read</span>'
        quotes = "".join(f"<blockquote>{esc(qt)}</blockquote>" for qt in s["quotes"]) or '<span class="blank">—</span>'
        note = f'<p class="note">{esc(s["note"])}</p>' if s["note"] else ""
        rows.append(f'<tr id="{s["id"]}"><th scope="row">{s["id"]}</th><td>{esc(s["publisher"])}<br>{ext(s["url"], s["title"])}</td>'
                    f'<td class="txt">{st}</td><td class="quote">{quotes}{note}</td><td class="src">{ext(s["url"], SHORT[s["id"]])}</td></tr>')
    n_full = sum(1 for s in SOURCES["sources"] if s["method"].startswith("full"))
    n_exc = sum(1 for s in SOURCES["sources"] if s["method"].startswith("excerpt"))
    body = f"""
<section>
<p>{len(SRC)} sources, all on the publisher's own site: {n_full} read in full, {n_exc} read as excerpts, {len(SRC) - n_full - n_exc} not read and used for nothing. Read on {esc(SOURCES['retrieved'])}. The words shown are the words relied on; follow the link to check them.</p>
{table(["ID", "Publisher and page", "How read", "Words relied on", "Link"], rows, "sources")}
<p>The raw capture log is kept at <a href="data/capture-log.md">data/capture-log.md</a>.</p>
</section>"""
    return page("sources.html", "Sources, with the sentences relied on",
                "Bank boards and tariffs, Chinese foreign-exchange and tax rules, and US tax and reporting rules, each linked to the official page.", body)


# ------------------------------------------------------------------ flagged
def build_flagged():
    rows = []
    for f in FLAGS:
        rows.append(f'<tr id="{f["id"]}"><th scope="row">{f["id"]}</th><td>{esc(f["title"])}</td><td>{esc(f["detail"])}</td>'
                    f'<td class="txt"><span class="pill warn">{esc(f["type"])}</span></td><td class="src">{links([f["source"]])}</td></tr>')
    brow = []
    for m in METHODS["methods"]:
        rs = [BY[(m["id"], t)] for t in META["tiers"]]
        nb = sum(1 for r in rs if r["total_usd"] is None)
        if nb and m["cost_model"] != "penalty":
            brow.append(f'<tr><th scope="row"><a href="costs.html#{m["id"]}">{esc(m["name"])}</a></th>' + cell(str(nb))
                        + f'<td>{esc(rs[0]["note"] or m["summary"])}</td><td class="txt">{flag_links(m["flags"]) or pill("unverified")}</td>'
                        f'<td class="src">{links(ROW_SRC[m["id"]])}</td></tr>')
    body = f"""
<section>
<h2>Flags</h2>
<p>Everything on this list is unverified, limited or an assumption. Nothing here blocks publication; all of it should be checked by a person before money moves.</p>
{table(["ID", "What", "Why it is flagged", "Type", "Check here"], rows, "flags")}
</section>
<section>
<h2>Cost cells left blank</h2>
<p>All-in cost is blank wherever an input was not confirmed from an official page. Published parts of the cost are still shown in the cost tables.</p>
{table(["Method", "Blank all-in cells (of 40)", "What is missing", "Flags", "Check here"], brow)}
</section>"""
    return page("flagged.html", "Flagged for Review",
                "Unverified values, limited sources, assumptions and conflicts between official texts, each with the page to check.", body)


# ------------------------------------------------------------------ repo review
def build_review():
    scan = {p["key"]: p for p in SCAN["patterns"]}
    rows = []
    for f in REVIEW:
        where = []
        for k in f["scan"]:
            p = scan[k]
            tops = ", ".join(ext(f'{REPO}{h["file"]}#L{h["first_line"]}', f'{h["file"]}:{h["first_line"]}') for h in p["top"][:3])
            where.append(f'{esc(p["label"])}: {p["lines"]} lines in {p["files"]} files' + (f" — {tops}" if tops else ""))
        wh = "<br>".join(where) if where else '<span class="note">Compared by reading; no pattern scan.</span>'
        rows.append(f'<tr id="{f["id"]}"><th scope="row">{f["id"]}</th><td>{esc(f["area"])}</td><td>{esc(f["finding"])}</td>'
                    f'<td class="txt">{pill(f["verdict"])}</td><td class="where">{wh}</td><td class="src">{links(f["sources"])}</td></tr>')
    srow = []
    for p in SCAN["patterns"]:
        tops = "<br>".join(ext(f'{REPO}{h["file"]}#L{h["first_line"]}', f'{h["file"]}:{h["first_line"]} ({h["count"]})') for h in p["top"])
        srow.append(f'<tr><th scope="row">{esc(p["label"])}</th>' + cell(str(p["files"])) + cell(str(p["lines"]))
                    + f'<td class="where">{tops or "—"}</td><td class="txt"><code>{esc(p["regex"])}</code></td>'
                    f'<td class="src">{links(p["sources"])}</td></tr>')
    body = f"""
<section>
<h2>Findings</h2>
<p>Every tracked text file outside this section was scanned line by line ({SCAN['scanned_files']} files, {SCAN['lines']:,} lines, at main commit <code>{esc(SCAN['main_commit'])}</code>) for the figures re-read today, and the figures were compared with the official pages. Other sessions' files were not edited; the findings are for their owners and for manual review.</p>
{table(["ID", "Area", "Finding", "Verdict", "Where in the repository", "Official source"], rows, "review")}
</section>
<section>
<h2>Scan detail</h2>
<p>Lines matching each pattern, with the files that contain most of them. The links open the first matching line on GitHub.</p>
{table(["What was searched for", "Files", "Lines", "Most matches (first line, count)", "Pattern", "Official figure"], srow)}
</section>"""
    return page("repo-review.html", "Repository re-check against today's official readings",
                "Where the existing pages agree with the official sources, where they have gone stale, and what they leave out.", body)


# ------------------------------------------------------------------ exports
def build_csv():
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["method_id", "method", "amount_usd", "all_in_cost_usd", "pct_of_amount", "cny_needed", "rate_margin_usd",
                "bank_fees_usd", "bank_fees_cny", "count", "count_unit", "status", "note", "flags", "source_urls"])
    for r in ROWS:
        m = M[r["method"]]
        fl = " ".join(m["flags"]) if r["status"] in ("partial", "unverified") else ""
        w.writerow([r["method"], m["name"], r["tier"], r["total_usd"] or "", r["pct"] or "", r["cny_needed"] or "",
                    r["spread_usd"] or "", r["fee_usd"] or "", r["fee_cny"] or "", r["count"] or "", r["count_unit"],
                    r["status"], r["note"], fl, " ".join(SRC[i]["url"] for i in ROW_SRC[r["method"]])])
    return buf.getvalue()


def main():
    pages = {"index.html": build_index(), "costs.html": build_costs(), "methods.html": build_methods(),
             "tax.html": build_tax(), "sources.html": build_sources(), "flagged.html": build_flagged(),
             "repo-review.html": build_review()}
    for name, text in pages.items():
        (HERE / name).write_text(text, encoding="utf-8")
    (HERE / "exports").mkdir(exist_ok=True)
    (HERE / "exports" / "costs.csv").write_text(build_csv(), encoding="utf-8")
    print(f"built {len(pages)} pages + exports/costs.csv ({len(ROWS)} rows)")


if __name__ == "__main__":
    main()
