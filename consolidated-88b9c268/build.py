#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic site generator for consolidated-88b9c268 (final integration 88b9c268).

Reads data/sources.json (34 official documents, same as playbook-c1d73006 verified 2026-11-11),
data/costs.json (17 methods × 40 tiers = 680 rows, Bank of China + HSBC China published inputs),
and data/review.json and writes HTML pages, CSV export, stylesheet, script and EXECUTIVE_SUMMARY.md.

No clock, no network. Every table row carries a direct official-source link; blank means unverified.

Run:  PYTHONDONTWRITEBYTECODE=1 python3 consolidated-88b9c268/build.py
"""
import csv
import html
import io
import json
import sys
from decimal import Decimal as D
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import content as C  # noqa: E402

SOURCES = json.loads((HERE / "data" / "sources.json").read_text(encoding="utf-8"))
SRC = {s["id"]: s for s in SOURCES}
QUOTE = {(s["id"], q["key"]): q for s in SOURCES for q in s["quotes"]}
COSTS = json.loads((HERE / "data" / "costs.json").read_text(encoding="utf-8"))
REVIEW = json.loads((HERE / "data" / "review.json").read_text(encoding="utf-8"))
INP = COSTS["inputs"]
BOC, HSBC = INP["banks"]["boc"], INP["banks"]["hsbc"]
METHOD = {m["id"]: m for m in C.METHODS}
FLAG_IDS = {f[0] for f in C.FLAGS}
STATUS = {"lawful": "Lawful", "conditional": "Lawful if you qualify", "unlawful": "Unlawful"}

NAV = [("index.html", "Overview"), ("summary.html", "Summary"), ("route.html", "Your route"), ("questions.html", "Questions"),
       ("methods.html", "Methods"), ("penalty.html", "The penalty"), ("costs.html", "Costs"), ("review.html", "Repo review"),
       ("flagged.html", "Flagged for Review"), ("sources.html", "Sources")]

e = html.escape


def usd(x, dec=2):
    if x is None:
        return ""
    return "$" + format(D(str(x)), ",.%df" % dec)


ROW = {(r["method"], r["amount"]): r for r in COSTS["rows"]}


def cost_at(method, amount, key):
    return ROW[(method, amount)][key]


FILL = {"boc_100k": usd(cost_at("L01", 100000, "boc_usd")), "hsbc_100k": usd(cost_at("L01", 100000, "hsbc_usd")),
        "boc_400k": usd(cost_at("L01", 400000, "boc_usd")), "hsbc_400k": usd(cost_at("L01", 400000, "hsbc_usd")),
        "boc_10k": usd(cost_at("L01", 10000, "boc_usd")), "hsbc_10k": usd(cost_at("L01", 10000, "hsbc_usd")),
        "boc_spread": "%.2f" % float(BOC["spread_pct"]), "hsbc_spread": "%.2f" % float(HSBC["spread_pct"])}


def fill(s):
    return s.format(**FILL) if "{" in s else s


def link(ptr, compact=False):
    sid, key = ptr.split(":")
    s, q = SRC[sid], QUOTE[(sid, key)]
    if compact:
        return '<a href="%s" rel="noopener">%s</a>' % (e(s["url"]), e(C.SHORT[sid]))
    return ('<a href="%s" rel="noopener">%s, %s</a> <a class="q" href="sources.html#%s-%s" title="The exact words relied on">exact words</a>'
            % (e(s["url"]), e(C.SHORT[sid]), e(q["locator"].split(";")[0][:60]), sid, key))


def src_cell(ptrs, compact=False):
    seen, out = set(), []
    for p in ptrs:
        k = p.split(":")[0] if compact else p
        if k in seen:
            continue
        seen.add(k)
        out.append(link(p, compact))
    assert out, "row without a source"
    return '<td class="src" data-label="Source">%s</td>' % "<br>".join(out)


def flag_link(fid, text=None):
    assert fid in FLAG_IDS, fid
    return '<a class="flag" href="flagged.html#%s">%s</a>' % (fid, e(text or fid))


def td(label, inner, cls=""):
    return '<td data-label="%s"%s>%s</td>' % (e(label), ' class="%s"' % cls if cls else "", inner)


def blank(label, fid, why="Not confirmed"):
    return '<td data-label="%s" class="blank">%s</td>' % (e(label), flag_link(fid, "%s · %s" % (why, fid)))


def table(heads, rows, cls="", tid=""):
    return ('<div class="tw"><table class="%s"%s><thead><tr>%s</tr></thead><tbody>\n%s\n</tbody></table></div>'
            % (cls, ' id="%s"' % tid if tid else "", "".join("<th>%s</th>" % e(h) for h in heads), "\n".join(rows)))


def tr(cells, attrs=""):
    return "<tr%s>%s</tr>" % (attrs, "".join(cells))


def badge(status):
    return '<span class="b b-%s">%s</span>' % (status, STATUS[status])


def page(slug, title, lead, body):
    nav = "".join('<a href="%s"%s>%s</a>' % (h, ' class="on" aria-current="page"' if h == slug else "", e(t)) for h, t in NAV)
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s · China money — consolidated dashboard</title>
<meta name="description" content="%s">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="top">
<div class="wrap">
<a class="brand" href="index.html">China money · Consolidated</a>
<button class="menu" type="button" aria-expanded="false" aria-controls="nav">Menu</button>
<nav id="nav" aria-label="Sections">%s</nav>
</div>
</header>
<main class="wrap">
<p class="crumb"><a href="../index.html">All sections of this site</a> / Consolidated</p>
<h1>%s</h1>
<p class="lead">%s</p>
%s
</main>
<footer class="wrap foot">
<p>Read and checked on %s by session <code>%s</code>. Every row links the page of the institution that published the figure. A blank cell means the figure could not be confirmed; it never means zero. Estimates are arithmetic on published inputs and are not quotes. This is research, not legal or tax advice.</p>
</footer>
<script src="assets/app.js"></script>
</body>
</html>
""" % (e(title), e(lead), nav, e(title), lead, body, C.AS_OF, C.SESSION)


# ------------------------------------------------------------------ pages
def findings_table():
    rows = [tr([td("Finding", "<strong>%s</strong><br>%s" % (e(f[0]), e(fill(f[1])))), td("Standing", e(f[2])), src_cell(f[3])]) for f in C.FINDINGS]
    return table(["Finding", "Standing", "Source"], rows, "cards")


def facts_table():
    rows = []
    for label, value, note, src in C.FACTS:
        v = td("What we have", e(value)) if value else blank("What we have", "FR-01", "Not stated")
        rows.append(tr([td("Item", "<strong>%s</strong>" % e(label)), v, td("Note", e(note)), src_cell(src)]))
    return table(["Item", "What we have", "Note", "Source"], rows, "cards")


def how_many(method, amount):
    n, label, note = cost_at(method, amount, "count"), cost_at(method, amount, "count_label"), cost_at(method, amount, "note")
    if not n:
        return "Not applicable"
    return "%s %s%s" % (format(n, ","), label, "; " + note if note else "")


def ranking_table():
    rows = []
    order = sorted([m for m in C.METHODS if m["status"] != "unlawful"],
                   key=lambda m: (cost_at(m["id"], 100000, "boc_usd") is None, D(cost_at(m["id"], 100000, "boc_usd") or "0"), m["id"]))
    for m in order:
        b, h = cost_at(m["id"], 100000, "boc_usd"), cost_at(m["id"], 100000, "hsbc_usd")
        fid = C.COST_FLAG.get(m["id"], "FR-05")
        cells = [td("Route", '<a href="methods.html#%s">%s · %s</a>' % (m["id"], m["id"], e(m["name"]))),
                 td("Bank of China inputs", "<strong>%s</strong>" % usd(b)) if b else blank("Bank of China inputs", fid, "Not published"),
                 td("HSBC China inputs", usd(h)) if h else blank("HSBC China inputs", fid, "Not published"),
                 td("How many", e(how_many(m["id"], 100000))),
                 td("What limits it", e(m["cap"])),
                 src_cell(C.COST_SRC.get(m["id"], C.COST_SRC["bank"]), True)]
        rows.append(tr(cells))
    return table(["Route", "Published cost at $100,000, Bank of China inputs", "HSBC China inputs", "How many", "What limits it", "Source"], rows, "cards")


def index_page():
    tiles = [("Tax on converting", "None found", "in the Chinese and U.S. texts read", "penalty.html"),
             ("What the bank needs", "Tax vouchers", "plus papers showing where the money came from", "route.html"),
             ("Published cost at $100,000", FILL["boc_100k"], "Bank of China inputs; %s at HSBC China" % FILL["hsbc_100k"], "costs.html"),
             ("Still unknown", "%d questions" % len(C.QUESTIONS), "%d items flagged for review" % len(C.FLAGS), "questions.html")]
    t = "".join('<a class="tile" href="%s"><span class="k">%s</span><span class="v">%s</span><span class="s">%s</span></a>' % (h, e(k), e(v), e(s)) for k, v, s, h in tiles)
    cards = [("summary.html", "Executive summary", "The answer in one page, with what is known and what is not."),
             ("route.html", "Find your route", "Ten origins of the money, and the rule, papers and tax for each."),
             ("questions.html", "Questions to answer first", "%d questions, why each one decides something, and how to find the answer." % len(C.QUESTIONS)),
             ("methods.html", "Every method", "%d ways to turn CNY into USD, with pros, cons and steps." % len(C.METHODS)),
             ("penalty.html", "The penalty, layer by layer", "What the cost of getting money out is really made of."),
             ("costs.html", "Costs from $10,000 to $400,000", "%d rows: every method at every $10,000 step." % len(COSTS["rows"])),
             ("review.html", "Repository review", "Figures in the other sections compared with the official texts."),
             ("flagged.html", "Flagged for Review", "%d items that could not be confirmed, with where to check." % len(C.FLAGS)),
             ("sources.html", "Sources", "%d official documents and the exact words relied on." % len(SOURCES))]
    c = "".join('<a class="card" href="%s"><strong>%s</strong><span>%s</span></a>' % (h, e(a), e(b)) for h, a, b in cards)
    body = """<section class="tiles">%s</section>
<h2>Start here</h2>
<ol class="steps">
<li><strong>Find out where the money came from and whether Chinese tax was paid on it.</strong> Those two facts choose the route. See <a href="questions.html">the questions</a>.</li>
<li><strong>Match it to a route.</strong> <a href="route.html">Ten situations</a>, each with its rule and its papers.</li>
<li><strong>Price it.</strong> <a href="costs.html">Costs at every $10,000 step</a>, built from each bank’s own rate board and fee table.</li>
</ol>
<h2>Findings</h2>
%s
<h2>Sections</h2>
<section class="cards-nav">%s</section>
<h2>What the brief gives us, and what it does not</h2>
%s
""" % (t, findings_table(), c, facts_table())
    return page("index.html", "Getting money out of China as a U.S. citizen — least tax, lowest cost, step by step",
                "A source-checked consolidation for a U.S. citizen with CNY stuck in a mainland bank: the least-tax lawful answer, every conversion route with pros/cons/steps, the 12-layer penalty that hides behind 'considerable taxes', and the $10k→$400k cost at published bank rates.", body)


SUMMARY_PARAS = [
    ("The short answer",
     ["None of the Chinese or U.S. texts read for this section charges a tax for converting CNY to USD or for wiring it abroad. What a mainland bank asks of a foreign passport holder is proof: a passport, papers that show where the money came from and how much, and tax vouchers for it.",
      "So the “considerable taxes” in the brief are most likely tax that was due on the money when it was earned or realised and has not been paid or cannot be shown, or tax on a gain such as a home sale. That cannot be confirmed without the facts in the questions list. If tax really is overdue, the cost is the tax itself, a surcharge of 0.05% for every day it has been late, and possibly a fine of 50% to five times the tax.",
      "Once the papers exist, the cost of the lawful route is small. Using each bank’s own rate board and fee table, buying and wiring $100,000 costs {boc_100k} at Bank of China and {hsbc_100k} at HSBC China, and $400,000 costs {boc_400k} and {hsbc_400k}. Charges by banks in the middle and by the U.S. bank are not published and are left blank."]),
    ("Which route is best",
     ["The best route is the one written for the origin of the money, at the bank that already holds it. Earned income goes through the documented-income rule. Property owned before taking foreign citizenship goes through an emigrant transfer, an inheritance through an inheritance transfer, and a home sale through its own three-paper list. Each ends in the same bank conversion and wire, so each has the same published cost.",
      "Routes that need no papers do not scale. Cash withdrawal abroad on a mainland card stops at RMB 100,000 a year, and the USD 50,000 yearly quota is open to a foreigner only with a Permanent Resident ID Card. Private swaps, false documents, cryptocurrency and splitting across other people’s quotas are unlawful; the fine for the first two is up to 30% of the amount and up to all of it in serious cases."]),
    ("The U.S. side",
     ["A U.S. citizen is taxed on worldwide income, so the tax question in the U.S. is about the income when it arose, not about the transfer. A credit may be available for Chinese income tax, with limits. A mainland account must be reported each year once foreign accounts total more than $10,000, and a gift or inheritance of more than $100,000 from a foreign person must be reported on Form 3520. The maximum penalty for a non-willful failure to file the account report is $16,536."]),
    ("What to do next",
     ["Answer the first three questions: where the money came from, whether Chinese tax was paid with proof, and exactly which tax was demanded and by whom. Ask the bank for its refusal and its reason in writing; the rules require it to give one. Then pick the matching route and take the papers listed for it."]),
]


def summary_page():
    body = ""
    for h, paras in SUMMARY_PARAS:
        body += "<h2>%s</h2>\n%s\n" % (e(h), "".join("<p>%s</p>\n" % e(fill(p)) for p in paras))
    body += "<h2>Findings and their sources</h2>\n" + findings_table()
    body += "<h2>Routes ranked by published cost at $100,000</h2>\n<p>Lawful routes only. A blank cell is a cost no official page publishes.</p>\n" + ranking_table()
    body += "<h2>What we know and do not know</h2>\n" + facts_table()
    body += '<p class="note">The same summary is in <a href="EXECUTIVE_SUMMARY.md">EXECUTIVE_SUMMARY.md</a>.</p>'
    return page("summary.html", "Executive summary", "What the official texts say, what it costs, and what has to be found out first.", body)


def summary_md():
    out = ["# Executive summary — getting money out of China as a U.S. citizen", "",
           "Read and checked on %s by session `%s`. Site: `consolidated-88b9c268/index.html`. Consolidated from `playbook-c1d73006` (34 official documents read 2026-11-11)." % (C.AS_OF, C.SESSION), ""]
    for h, paras in SUMMARY_PARAS:
        out += ["## " + h, ""] + [fill(p) + "\n" for p in paras]
    out += ["## Findings and their sources", "", "| Finding | Standing | Source |", "|---|---|---|"]
    for f in C.FINDINGS:
        links = "; ".join("[%s](%s)" % (C.SHORT[p.split(":")[0]], SRC[p.split(":")[0]]["url"]) for p in f[3])
        out.append("| **%s** %s | %s | %s |" % (f[0], fill(f[1]), f[2], links))
    out += ["", "A blank on the site means a figure could not be confirmed from an official page. It never means zero. This is research, not legal or tax advice.", ""]
    return "\n".join(out)


def route_page():
    rows = []
    for sid, origin, routes, docs, cn, us, first, src, flags in C.SITUATIONS:
        fl = flags[0] if flags else "FR-01"
        r = " ".join('<a href="methods.html#%s">%s</a>' % (m, m) for m in routes)
        cells = [td("If the money is", '<strong id="%s">%s · %s</strong>' % (sid, sid, e(origin))),
                 td("Route", r) if routes else blank("Route", fl),
                 td("Papers", e(docs)) if docs else blank("Papers", fl),
                 td("Chinese tax", e(cn)) if cn else blank("Chinese tax", fl),
                 td("U.S. side", e(us)) if us else blank("U.S. side", fl),
                 td("First step", e(first) + ("".join(" " + flag_link(f) for f in flags))),
                 src_cell(src)]
        rows.append(tr(cells))
    body = """<p>Find the row that matches the money. Where a row is a mix, split the balance by origin and treat each part on its own row.</p>
%s
<h2>Who you are to the bank</h2>
<p>The route also depends on how the bank classes you. The central-bank measures go by the identity document.</p>
%s
""" % (table(["If the money is", "Route", "Papers", "Chinese tax", "U.S. side", "First step", "Source"], rows, "cards"),
       table(["You hold", "The bank treats you as", "What follows", "Source"], [
           tr([td("You hold", "<strong>A U.S. passport only</strong>"), td("The bank treats you as", "A foreign individual"),
               td("What follows", "Conversion on the passport and source-of-funds papers including tax vouchers. No yearly quota."), src_cell(["CN-FX-03:art37_2", "CN-FX-06:art59"])]),
           tr([td("You hold", "<strong>A U.S. passport and a Foreign Permanent Resident ID Card</strong>"), td("The bank treats you as", "A foreign individual with the yearly quota"),
               td("What follows", "USD 50,000 a year on the identity document, and the documented route above that."), src_cell(["CN-FX-05:qa", "CN-FX-06:art54"])]),
           tr([td("You hold", "<strong>A PRC identity card from before you naturalised, still on the account</strong>"), td("The bank treats you as", "A domestic individual, on its records"),
               td("What follows", "The account record no longer matches your status. The emigrant-transfer route is the one written for a former resident who has taken foreign citizenship. " + flag_link("FR-21")), src_cell(["CN-FX-03:art37_1", "CN-FX-10:conditions"])]),
       ], "cards"))
    return page("route.html", "Find your route", "The lawful route is set by where the money came from.", body)


def questions_page():
    rows = []
    for qid, q, have, why, how, src in C.QUESTIONS:
        rows.append(tr([td("Question", '<strong id="%s">%s · %s</strong>' % (qid, qid, e(q))),
                        td("What we have", e(have)) if have else blank("What we have", "FR-01", "Nothing yet"),
                        td("Why it decides something", e(why)), td("How to find out", e(how)), src_cell(src)]))
    body = """<p>No route can reasonably be chosen until the first three are answered. The rest narrow the route, the cost and the U.S. filings.</p>
%s""" % table(["Question", "What we have", "Why it decides something", "How to find out", "Source"], rows, "cards")
    return page("questions.html", "Questions to answer before deciding", "%d questions, built from what the brief says and what it leaves out." % len(C.QUESTIONS), body)


def methods_page():
    rows = []
    for m in C.METHODS:
        b, h = cost_at(m["id"], 100000, "boc_usd"), cost_at(m["id"], 100000, "hsbc_usd")
        lo, hi = cost_at(m["id"], 100000, "low_usd"), cost_at(m["id"], 100000, "high_usd")
        fid = C.COST_FLAG.get(m["id"], "FR-05")
        if m["status"] == "unlawful":
            cost = td("At $100,000", "Fine: %s%s" % ((usd(lo, 0) + " to ") if lo else "up to ", usd(hi, 0)), "bad") if hi else blank("At $100,000", fid, "No figure stated")
        else:
            cost = td("At $100,000", "%s / %s" % (usd(b), usd(h))) if b else blank("At $100,000", fid, "Not published")
        rows.append(tr([td("Method", '<a href="#%s"><strong>%s · %s</strong></a>' % (m["id"], m["id"], e(m["name"]))),
                        td("Standing", badge(m["status"])), cost, td("Who can use it", e(m["who"])),
                        td("Limit", e(m["cap"])) if m["cap"] else td("Limit", "Not applicable"), src_cell(m["src"][:3])]))
    body = """<p>Costs at $100,000 are shown as Bank of China inputs / HSBC China inputs. Unlawful routes are listed with their penalties and without instructions.</p>
%s
<h2>Each method in detail</h2>
""" % table(["Method", "Standing", "At $100,000", "Who can use it", "Limit", "Source"], rows, "cards")
    for m in C.METHODS:
        det = []
        if m["pros"]:
            det.append(tr([td("Part", "<strong>For</strong>"), td("Detail", "<ul>%s</ul>" % "".join("<li>%s</li>" % e(x) for x in m["pros"])), src_cell(m["src"])]))
        det.append(tr([td("Part", "<strong>Against</strong>"), td("Detail", "<ul>%s</ul>" % "".join("<li>%s</li>" % e(x) for x in m["cons"])), src_cell(m["src"])]))
        if m["steps"]:
            det.append(tr([td("Part", "<strong>Steps</strong>"), td("Detail", "<ol>%s</ol>" % "".join("<li>%s</li>" % e(x) for x in m["steps"])), src_cell(m["src"])]))
        else:
            det.append(tr([td("Part", "<strong>Steps</strong>"), td("Detail", "None given. This route is unlawful."), src_cell(m["src"])]))
        det.append(tr([td("Part", "<strong>Cost</strong>"), td("Detail", "%s <a href=\"costs.html#m-%s\">All 40 steps</a>%s" % (
            e(C.COST_NOTE[m["id"]]), m["id"], "".join(" " + flag_link(f) for f in m["flags"]))), src_cell(C.COST_SRC.get(m["id"], C.COST_SRC["bank"]), True)]))
        body += '<section class="method" id="%s"><h3>%s · %s %s</h3><p>%s</p>%s</section>\n' % (
            m["id"], m["id"], e(m["name"]), badge(m["status"]), e(m["who"]), table(["Part", "Detail", "Source"], det, "cards"))
    return page("methods.html", "Every method, with pros, cons and steps", "%d ways to turn CNY into USD: %d lawful or conditional, %d unlawful." % (
        len(C.METHODS), sum(m["status"] != "unlawful" for m in C.METHODS), sum(m["status"] == "unlawful" for m in C.METHODS)), body)


def penalty_page():
    rows = []
    for pid, layer, what, fig, when, src, fl in C.LAYERS:
        figc = td("Published figure", "<strong>%s</strong>" % e(fill(fig))) if fig else (blank("Published figure", fl, "Not published") if fl else td("Published figure", "Not a money amount"))
        rows.append(tr([td("Layer", '<strong id="%s">%s · %s</strong>' % (pid, pid, e(layer))), figc, td("What it is", e(what) + (" " + flag_link(fl) if fl and fig else "")),
                        td("When it applies", e(when)), src_cell(src)]))
    late = D(str(SRC["CN-TAX-05"]["values"]["late_pct_per_day"])) / 100
    fmin = D(str(SRC["CN-TAX-05"]["values"]["fine_min_pct"])) / 100
    fmax = D(str(SRC["CN-TAX-05"]["values"]["fine_max_times"]))
    base = D(100000)
    lrows = []
    for years in (1, 2, 3, 5, 10):
        days = 365 * years
        sur = base * late * days
        lrows.append(tr([td("Late by", "<strong>%d year%s</strong> (%s days)" % (years, "" if years == 1 else "s", format(days, ","))),
                         td("Surcharge", "RMB %s" % format(int(sur), ",")), td("Tax plus surcharge", "RMB %s" % format(int(base + sur), ",")),
                         td("Fine if not filed", "RMB %s to %s" % (format(int(base * fmin), ","), format(int(base * fmax), ","))),
                         src_cell(["CN-TAX-05:art32", "CN-TAX-05:art64"])]))
    t1 = [("Up to 36,000", "3%"), ("36,000 to 144,000", "10%"), ("144,000 to 300,000", "20%"), ("300,000 to 420,000", "25%"),
          ("420,000 to 660,000", "30%"), ("660,000 to 960,000", "35%"), ("Above 960,000", "45%")]
    t2 = [("Up to 30,000", "5%"), ("30,000 to 90,000", "10%"), ("90,000 to 300,000", "20%"), ("300,000 to 500,000", "30%"), ("Above 500,000", "35%")]
    rrows = [tr([td("Kind of income", "<strong>Pay, fees, author’s pay, royalties</strong>"), td("Taxable income in a year, RMB", a), td("Rate", b), src_cell(["CN-TAX-03:table1"])]) for a, b in t1]
    rrows += [tr([td("Kind of income", "<strong>Business income</strong>"), td("Taxable income in a year, RMB", a), td("Rate", b), src_cell(["CN-TAX-03:table2"])]) for a, b in t2]
    rrows.append(tr([td("Kind of income", "<strong>Interest, dividends, rent, gains on property, windfalls</strong>"), td("Taxable income in a year, RMB", "Each receipt; for a sale, the gain"), td("Rate", "20%"), src_cell(["CN-TAX-03:art3", "CN-TAX-03:art6_5"])]))
    rrows.append(tr([td("Kind of income", "<strong>Interest on savings deposits</strong>"), td("Taxable income in a year, RMB", "Interest accrued from 9 October 2008"), td("Rate", "Not collected"), src_cell(["CN-TAX-04:exempt"])]))
    body = """<p>“Penalty” covers several different things. Only three of them apply to every transfer: the paper gate, the bank’s rate margin and the wire fee. The rest apply only if something was left undone.</p>
%s
<h2>If Chinese tax is overdue: what each RMB 100,000 of it grows into</h2>
<p>This table assumes nothing about your money. It applies the surcharge and the fine range in the law to RMB 100,000 of tax, so the result can be scaled to any figure a tax office gives you.</p>
%s
<h2>Chinese income tax rates by kind of income</h2>
<p>The tax falls on income or gain. It is not a percentage of the amount sent abroad.</p>
%s
""" % (table(["Layer", "Published figure", "What it is", "When it applies", "Source"], rows, "cards"),
       table(["Late by", "Surcharge", "Tax plus surcharge", "Fine if not filed", "Source"], lrows, "cards"),
       table(["Kind of income", "Taxable income in a year, RMB", "Rate", "Source"], rrows, "cards"))
    return page("penalty.html", "The penalty, layer by layer", "What the cost of getting money out is actually made of, and which parts apply to you.", body)


def costs_page():
    def inp_row(label, value, ptrs, note=""):
        return tr([td("Input", "<strong>%s</strong>" % e(label)), td("Value", e(value)), td("Note", e(note)) if note else td("Note", "As published"), src_cell(ptrs)])
    irows = [
        inp_row("Bank of China selling rate", "RMB %s per USD" % BOC["sell"], ["BANK-01:usd_row"], "Board of 2026/11/11 10:40:02"),
        inp_row("Bank of China buying rate", "RMB %s per USD" % BOC["buy"], ["BANK-01:usd_row"], "Same board"),
        inp_row("Bank of China margin", "%s%% of the amount" % BOC["spread_pct"], ["BANK-01:usd_row"], "Selling rate against the midpoint of the board (%s). Arithmetic, not a published fee" % BOC["mid"]),
        inp_row("Bank of China commission", "%s%%, at least RMB %s, at most RMB %s" % (BOC["pct"].rstrip("0"), BOC["min"], BOC["max"]), ["BANK-03:tt"], "Table headed “from 1 November 2014”"),
        inp_row("Bank of China cable charge", "RMB %s" % BOC["cable"], ["BANK-03:tt"], "Outside Hong Kong, Macao and Taiwan"),
        inp_row("HSBC China selling rate", "RMB %s per USD" % HSBC["sell"], ["BANK-04:usd_row"], "Board last updated 10 November 2026"),
        inp_row("HSBC China buying rate", "RMB %s per USD" % HSBC["buy"], ["BANK-04:usd_row"], "Same board"),
        inp_row("HSBC China margin", "%s%% of the amount" % HSBC["spread_pct"], ["BANK-04:usd_row"], "Selling rate against the midpoint of the board (%s). Arithmetic, not a published fee" % HSBC["mid"]),
        inp_row("HSBC China commission", "%s%%, at least RMB %s, at most RMB %s" % (HSBC["pct"].rstrip("0"), HSBC["min"], HSBC["max"]), ["BANK-02:tt_issuance"], "Premier and Advance customers. Free for individual Private Banking customers"),
        inp_row("HSBC China cable charge", "RMB %s" % HSBC["cable"], ["BANK-02:cable"], "Premier and Advance customers"),
        inp_row("Yearly quota", "USD %s" % format(int(D(INP["quota_usd"])), ","), ["CN-FX-06:art54"]),
        inp_row("Card cash withdrawal abroad", "RMB %s a year; RMB %s a card a day" % (format(int(D(INP["atm_year_cny"])), ","), format(int(D(INP["atm_day_cny"])), ",")), ["CN-FX-07:annual_cap", "CN-FX-07:daily_cap"]),
        inp_row("Foreign cash carried out", "USD %s with no permit; up to USD %s with a bank permit" % (format(int(D(INP["cash_low_usd"])), ","), format(int(D(INP["cash_high_usd"])), ",")), ["CN-FX-06:art89"]),
        inp_row("Wise, each transfer", "RMB %s" % format(int(D(INP["wise_per_transfer_cny"])), ","), ["PROV-01:per_transfer"]),
        inp_row("Fine on an unlawful route", "%s%% of the amount; up to %s%% in serious cases; %s%% for cash carried against the rules" % (INP["fine_pct"].split(".")[0], INP["fine_max_pct"].split(".")[0], INP["carry_fine_pct"].split(".")[0]), ["CN-FX-01:art45", "CN-FX-01:art42"]),
        inp_row("Federal Reserve rate, 6 November 2026", "RMB 6.6760 per USD", ["US-FX-02:china_row"], "Shown for comparison; not used in the tables"),
        inp_row("IRS average rate for tax year 2025", "RMB 7.129 per USD", ["US-FX-01:china_row"], "For translating income on a tax return; not used in the tables"),
    ]
    brows = []
    for key, b in (("boc", BOC), ("hsbc", HSBC)):
        for x in COSTS["breakdown"][key]:
            brows.append(tr([td("Amount", "<strong>%s</strong>" % usd(x["amount"], 0)), td("Bank", e(b["name"])),
                             td("Published cost", "<strong>%s</strong> (%s%%)" % (usd(x["total_usd"]), x["pct"])),
                             td("Rate margin", usd(x["spread_usd"])), td("Commission", "RMB %s" % x["commission_cny"]), td("Cable", "RMB %s" % x["cable_cny"].split(".")[0]),
                             td("RMB needed", format(D(x["cny_needed"]), ",.2f")), blank("Other banks’ charges", "FR-05", "Not published"),
                             src_cell([b["sid_board"] + ":usd_row", b["sid_tariff"] + (":tt" if key == "boc" else ":tt_issuance")], True)],
                            ' data-amt="%d" data-bank="%s"' % (x["amount"], key)))
    mrows = []
    for r in COSTS["rows"]:
        m = METHOD[r["method"]]
        fid = C.COST_FLAG.get(m["id"], "FR-05")
        unl = m["status"] == "unlawful"
        if unl:
            c1 = td("Fine the regulation allows", "<strong>%s%s</strong>" % ((usd(r["low_usd"], 0) + " to ") if r["low_usd"] else "up to ", usd(r["high_usd"], 0)), "bad") if r["high_usd"] else blank("Fine the regulation allows", fid, "No figure stated")
            c2 = td("HSBC China inputs", "Not applicable")
        else:
            c1 = td("Bank of China inputs", "<strong>%s</strong>" % usd(r["boc_usd"])) if r["boc_usd"] else blank("Bank of China inputs", fid, "Not published")
            c2 = td("HSBC China inputs", usd(r["hsbc_usd"])) if r["hsbc_usd"] else blank("HSBC China inputs", fid, "Not published")
        cnt = how_many(r["method"], r["amount"])
        mrows.append(tr([td("Amount", "<strong>%s</strong>" % usd(r["amount"], 0)), c1, c2, td("How many", e(cnt)),
                         td("Method", '<a href="methods.html#%s">%s</a> %s' % (m["id"], m["id"], e(m["name"]))),
                         td("Not included", flag_link(fid, "Other charges · " + fid) if not unl else "Criminal liability is separate"),
                         src_cell(C.COST_SRC.get(m["id"], C.COST_SRC["bank"]), True)],
                        ' data-m="%s" data-amt="%d"' % (m["id"], r["amount"])))
    opts = "".join('<option value="%s">%s · %s</option>' % (m["id"], m["id"], e(m["name"])) for m in C.METHODS)
    amts = "".join('<option value="%d">%s</option>' % (a, usd(a, 0)) for a in INP["tiers"])
    body = """<p>Every figure is arithmetic on a published rate board or fee table, dated in the inputs below. It is an estimate, not a quote: the bank’s rate on the day governs. Costs that no official page publishes are left blank and linked to the flag that explains why.</p>
<h2>Every method at every $10,000 step</h2>
%s<form class="filter" id="f" onsubmit="return false">
<label>Method <select id="fm"><option value="">All %d methods</option>%s</select></label>
<label>Amount <select id="fa"><option value="">All 40 steps</option>%s</select></label>
<span id="fc" class="count" aria-live="polite"></span>
</form>
%s
<p class="note">Download: <a href="data/costs.csv">costs.csv</a> · <a href="data/costs.json">costs.json</a>.</p>
<h2>The bank route, part by part</h2>
<p>For the routes that end in a conversion and one wire (L01, L02, L05, L06 and L07).</p>
%s
<h2>Inputs</h2>
%s
<h2>How the figures are made</h2>
<ol class="steps">
<li>The margin is the bank’s selling rate less the midpoint of its own buying and selling rates, as a share of the midpoint. For Bank of China that is (%s − %s) ÷ %s = %s%%.</li>
<li>The commission is 0.1%% of the RMB paid, held between the bank’s floor and ceiling. The cable charge is added.</li>
<li>RMB fees are turned into dollars at the same bank’s selling rate, because that is the rate at which the fee uses up dollars.</li>
<li>Capped routes are counted, not priced, where the fee is not published: years at the yearly cap, transfers at the per-transfer cap, trips at the cash limit.</li>
<li>Unlawful routes show the fine the regulation allows, which is not a fee and does not include confiscation or criminal liability.</li>
</ol>
""" % ("".join('<span id="m-%s"></span>' % m["id"] for m in C.METHODS), len(C.METHODS), opts, amts,
       table(["Amount", "Published cost, Bank of China inputs", "HSBC China inputs", "How many", "Method", "Not included", "Source"], mrows, "cards dense", "ct"),
       table(["Amount", "Bank", "Published cost", "Rate margin", "Commission", "Cable", "RMB needed", "Other banks’ charges", "Source"], brows, "cards dense"),
       table(["Input", "Value", "Note", "Source"], irows, "cards"),
       BOC["sell"], BOC["mid"], BOC["mid"], BOC["spread_pct"])
    return page("costs.html", "Costs from $10,000 to $400,000", "%d rows: %d methods at 40 amounts, from published inputs only." % (len(COSTS["rows"]), len(C.METHODS)), body)


def costs_csv():
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["method", "method_name", "standing", "amount_usd", "bank_of_china_inputs_usd", "hsbc_china_inputs_usd", "count", "count_of",
                "extra", "fine_low_usd", "fine_high_usd", "flag_for_blank", "source_urls"])
    for r in COSTS["rows"]:
        m = METHOD[r["method"]]
        urls = " ".join(dict.fromkeys(SRC[p.split(":")[0]]["url"] for p in C.COST_SRC.get(m["id"], C.COST_SRC["bank"])))
        w.writerow([m["id"], m["name"], STATUS[m["status"]], r["amount"], r["boc_usd"] or "", r["hsbc_usd"] or "", r["count"] or "", r["count_label"],
                    r["note"], r["low_usd"] or "", r["high_usd"] or "", C.COST_FLAG.get(m["id"], "FR-05"), urls])
    return buf.getvalue()


RESULT = {
    "RV-01": lambda c: "%d files state $16,536. %d state a different figure." % (c["match_files"], c["differ_files"]),
    "RV-02": lambda c: "%d files state $165,353. %d state a different figure." % (c["match_files"], c["differ_files"]),
    "RV-03": lambda c: "%d files quote $86.97." % c["differ_files"],
    "RV-04": lambda c: "%d files use 7.129 in a cost, fee or rate line." % c["match_files"],
    "RV-05": lambda c: "%d files describe staging without the 2014 change. %d mention the change." % (c["differ_files"], c["match_files"]),
    "RV-06": lambda c: "%d files say dollar-for-dollar with no limiting word on the line. %d qualify it." % (c["differ_files"], c["match_files"]),
    "RV-07": lambda c: "%d files quote $132,900 or $137,300." % c["unverified_files"],
    "RV-08": lambda c: ("No file in any other section mentions it." if c["match_files"] == 0 else "%d files mention it." % c["match_files"]),
    "RV-09": lambda c: "%d files link an official page over http." % c["differ_files"],
}
STANDING = {"RV-01": "Agrees", "RV-02": "Agrees", "RV-03": "Differs by the rate used", "RV-04": "For information", "RV-05": "Out of date in places",
            "RV-06": "Overstated in places", "RV-07": "Not re-verified", "RV-08": "Missing everywhere", "RV-09": "Minor"}


def review_page():
    rows, ex = [], []
    for c in REVIEW["checks"]:
        ptr = "%s:%s" % (c["source"], c["quote"])
        ver = td("Official text says", e(c["verified"])) if c["verified"] else blank("Official text says", "FR-12", "Not re-read")
        secs = ", ".join(c["differ_sections"][:10]) or "None"
        rows.append(tr([td("Figure", '<strong id="%s">%s · %s</strong>' % (c["id"], c["id"], e(c["figure"]))), td("Standing", e(STANDING[c["id"]])), ver,
                        td("Found in the repository", e(RESULT[c["id"]](c["counts"]))), td("Sections to look at", e(secs)), td("How to read it", e(c["how"])), src_cell([ptr])]))
        for x in c["examples"]:
            ex.append(tr([td("Check", '<a href="#%s">%s</a>' % (c["id"], c["id"])),
                          td("File and line", '<a href="%s/blob/main/%s#L%d" rel="noopener">%s, line %d</a>' % (C.REPO, e(x["path"]), x["line"], e(x["path"]), x["line"])),
                          td("Text found", e(x["text"])), src_cell([ptr])]))
    hub = REVIEW["hub"]
    notes = ["The landing page of the site links %d of the %d sections that have their own landing page. Not linked: %s." % (
                 hub["linked_from_hub"], hub["sections_with_landing_page"], ", ".join(hub["not_linked"]) or "none"),
             "audit-92d12752/verify.py compares the repository with a stored snapshot and fails once any page is added elsewhere. No workflow runs it, so the failure is silent. Its snapshot was regenerated on this branch with its own unmodified generator: 129 pages, 10,471 rows, 1,467 rows without a direct official link, none of them in this section.",
             "The landing page still describes that scan as “7,107 rows · 1,384 candidates”, a figure typed into the landing-page generator and not read from the scan.",
             "Four sessions claimed the landing page and its generator on separate branches within half an hour on 11 November 2026. This section added one row and one card to the landing-page generator so that it can be reached, and changed nothing else there.",
             "%d other sections answer the same brief. Their cost tables differ mainly in the rate used to turn RMB fees into dollars (see RV-03 and RV-04), not in the fee formulas." % REVIEW["sections_scanned"]]
    body = """<p>A text search of %d files in %d other sections, as they stood on the main branch at commit <code>%s</code> on %s. A hit is a place for a person to look. The search cannot tell a wrong figure from one quoted in order to correct it, and nothing in another section was changed.</p>
%s
<h2>Places to look</h2>
<p>Up to five per check, one per file.</p>
%s
<h2>Notes about the repository itself</h2>
<ul class="plain">%s</ul>
""" % (REVIEW["files_scanned"], REVIEW["sections_scanned"], e(REVIEW["main_commit"]), e(C.AS_OF),
       table(["Figure", "Standing", "Official text says", "Found in the repository", "Sections to look at", "How to read it", "Source"], rows, "cards"),
       table(["Check", "File and line", "Text found", "Source"], ex, "cards dense"),
       "".join("<li>%s</li>" % e(n) for n in notes))
    return page("review.html", "Repository review", "Figures in the other sections of this repository, compared with the official texts read on %s." % C.AS_OF, body)


def flagged_page():
    rows = [tr([td("Item", '<strong id="%s">%s · %s</strong>' % (f[0], f[0], e(f[1]))), td("Why it is flagged", e(f[2])), td("How to settle it", e(f[3])),
                td("Where it matters", e(f[5])), src_cell(f[4])]) for f in C.FLAGS]
    body = """<p>These items could not be confirmed from an official page, or the official pages disagree. None of them blocks the rest of the site. Where a figure is missing, the cell is left blank and links here.</p>
%s""" % table(["Item", "Why it is flagged", "How to settle it", "Where it matters", "Source"], rows, "cards")
    return page("flagged.html", "Flagged for Review", "%d items that are unverified, unpublished or inconsistent, each with where to check." % len(C.FLAGS), body)


def sources_page():
    rows, groups = [], []
    for s in SOURCES:
        if s["group"] not in groups:
            groups.append(s["group"])
    idx = [tr([td("Document", '<a href="#%s"><strong>%s</strong></a> · %s' % (s["id"], s["id"], e(s["title"]))), td("Publisher", e(s["publisher"])),
               td("Reference", e(s["doc_no"])), td("Read on", e(s["retrieved"])), td("Passages", str(len(s["quotes"]))),
               '<td class="src" data-label="Source"><a href="%s" rel="noopener">Open the official page</a></td>' % e(s["url"])]) for s in SOURCES]
    for s in SOURCES:
        for q in s["quotes"]:
            en = q.get("en")
            words = '<q lang="%s">%s</q>' % (s["lang"], e(q["text"])) + ('<br><span class="en">In English: %s</span>' % e(en) if en else "")
            rows.append(tr([td("Document", '<strong id="%s-%s">%s</strong> · %s' % (s["id"], q["key"], s["id"], e(C.SHORT[s["id"]]))), td("Where", e(q["locator"])),
                            td("Exact words", words), '<td class="src" data-label="Source"><a href="%s" rel="noopener">%s</a></td>' % (e(s["url"]), e(C.SHORT[s["id"]]))]))
    anchors = "".join('<span id="%s"></span>' % s["id"] for s in SOURCES)
    body = """<p>%d documents were opened on %s and %d passages copied from them. Chinese passages are given in the original with a plain English rendering made for this site; where the two differ the original governs. Groups: %s.</p>
%s
<h2>Documents</h2>
%s
<h2>Passages relied on</h2>
%s
""" % (len(SOURCES), C.AS_OF, len(QUOTE), "; ".join(groups), anchors,
       table(["Document", "Publisher", "Reference", "Read on", "Passages", "Source"], idx, "cards"),
       table(["Document", "Where", "Exact words", "Source"], rows, "cards quotes"))
    return page("sources.html", "Sources", "The official documents behind every row, with the exact words relied on.", body)


CSS = """:root{--bg:#f6f7f9;--card:#fff;--ink:#16202b;--mut:#566373;--line:#dfe4ea;--acc:#0b5cab;--good:#1b6b3a;--warn:#8a5a00;--bad:#a12622;--warnbg:#fff6e0}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,"Noto Sans","PingFang SC","Microsoft YaHei",sans-serif}
a{color:var(--acc)}a:focus-visible,button:focus-visible,select:focus-visible{outline:3px solid #f5a623;outline-offset:2px}
.wrap{max-width:1180px;margin:0 auto;padding:0 16px}
.top{background:#10243a;color:#fff;position:sticky;top:0;z-index:5}
.top .wrap{display:flex;align-items:center;gap:12px;flex-wrap:wrap;padding-top:8px;padding-bottom:8px}
.brand{color:#fff;font-weight:700;text-decoration:none;margin-right:auto}
.menu{display:none;background:transparent;color:#fff;border:1px solid #6f8299;border-radius:6px;padding:6px 12px;font:inherit}
nav{display:flex;flex-wrap:wrap;gap:2px}
nav a{color:#d7e2ee;text-decoration:none;padding:6px 9px;border-radius:6px;font-size:14px}
nav a.on,nav a:hover{background:#27425f;color:#fff}
.crumb{font-size:13px;color:var(--mut);margin:14px 0 0}
h1{font-size:28px;line-height:1.2;margin:8px 0 6px}h2{font-size:20px;margin:30px 0 10px}h3{font-size:17px;margin:22px 0 6px}
.lead{color:var(--mut);margin:0 0 16px;max-width:70ch}p{max-width:80ch}
.tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:14px 0}
.tile{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;text-decoration:none;color:inherit;display:flex;flex-direction:column;gap:2px}
.tile .k{font-size:13px;color:var(--mut)}.tile .v{font-size:24px;font-weight:700;color:var(--acc)}.tile .s{font-size:13px;color:var(--mut)}
.cards-nav{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;text-decoration:none;color:inherit;display:flex;flex-direction:column;gap:4px}
.card strong{color:var(--acc)}.card span{font-size:14px;color:var(--mut)}.tile:hover,.card:hover{border-color:var(--acc)}
.steps{padding-left:22px;max-width:80ch}.steps li{margin:6px 0}.plain{max-width:80ch}.plain li{margin:6px 0}
.tw{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:10px}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{text-align:left;vertical-align:top;padding:9px 10px;border-bottom:1px solid var(--line)}
th{background:#eef2f6;font-size:13px;position:sticky;top:0}
tbody tr:last-child td{border-bottom:0}
td ul,td ol{margin:0;padding-left:18px}td li{margin:2px 0}
td.src{font-size:12.5px;min-width:150px}td.src a.q{color:var(--mut);font-size:11.5px}
td.blank{background:var(--warnbg)}a.flag{color:var(--warn);font-weight:600;font-size:12.5px;white-space:nowrap}
td.blank a.flag{white-space:normal}td.bad{color:var(--bad)}
.b{display:inline-block;font-size:12px;font-weight:700;border-radius:999px;padding:2px 9px;white-space:nowrap}
.b-lawful{background:#e3f3e8;color:var(--good)}.b-conditional{background:#e6eefb;color:#1d4f91}.b-unlawful{background:#fbe6e5;color:var(--bad)}
.filter{display:flex;flex-wrap:wrap;gap:12px;align-items:end;margin:10px 0}
.filter label{display:flex;flex-direction:column;font-size:13px;color:var(--mut);gap:3px}
.filter select{font:inherit;padding:8px;border:1px solid #9aa7b5;border-radius:6px;background:#fff;max-width:100%}
.count{font-size:13px;color:var(--mut)}.note{font-size:14px;color:var(--mut)}
q{quotes:"“" "”"}.en{color:var(--mut)}.quotes td:nth-child(3){min-width:320px}
.method{scroll-margin-top:70px}[id]{scroll-margin-top:70px}
.foot{color:var(--mut);font-size:13px;margin-top:34px;padding-bottom:30px}.foot p{max-width:none}
tr[hidden]{display:none}
@media (max-width:900px){.tiles{grid-template-columns:repeat(2,1fr)}.cards-nav{grid-template-columns:repeat(2,1fr)}}
@media (max-width:720px){
h1{font-size:23px}.menu{display:inline-block}nav{display:none;width:100%}nav.open{display:flex;flex-direction:column}
.cards-nav{grid-template-columns:1fr}
.tw{border:0;background:transparent;overflow:visible}
table.cards thead{position:absolute;left:-9999px}
table.cards,table.cards tbody,table.cards tr,table.cards td{display:block;width:100%}
table.cards tr{background:var(--card);border:1px solid var(--line);border-radius:10px;margin:0 0 10px;padding:6px 0}
table.cards td{border:0;padding:5px 12px;min-width:0}
table.cards td::before{content:attr(data-label);display:block;font-size:11.5px;color:var(--mut);text-transform:uppercase;letter-spacing:.03em}
table.cards td:first-child{font-size:16px;padding-top:9px}table.cards td:first-child::before{display:none}
table.cards td.blank{margin:2px 8px;width:auto;border-radius:6px}
.quotes td:nth-child(3){min-width:0}
}
@media print{.top,.filter,.menu{display:none}body{background:#fff}}
"""

JS = """(function(){
var b=document.querySelector('.menu'),n=document.getElementById('nav');
if(b&&n){b.addEventListener('click',function(){var o=n.classList.toggle('open');b.setAttribute('aria-expanded',o?'true':'false');});}
var t=document.getElementById('ct');if(!t){return;}
var fm=document.getElementById('fm'),fa=document.getElementById('fa'),fc=document.getElementById('fc');
var rows=Array.prototype.slice.call(t.tBodies[0].rows);
var q=new URLSearchParams(location.search);
var h=/^#m-(\\w+)$/.exec(location.hash);
if(h){fm.value=h[1];}else if(q.get('m')){fm.value=q.get('m');}else{fm.value='L01';}
if(fm.value===''&&!h&&!q.get('m')){fm.value='L01';}
if(q.get('a')){fa.value=q.get('a');}
function go(){var m=fm.value,a=fa.value,k=0;
rows.forEach(function(r){var ok=(!m||r.getAttribute('data-m')===m)&&(!a||r.getAttribute('data-amt')===a);r.hidden=!ok;if(ok){k++;}});
fc.textContent=k+' of '+rows.length+' rows shown';}
fm.addEventListener('change',go);fa.addEventListener('change',go);
window.addEventListener('hashchange',function(){var x=/^#m-(\\w+)$/.exec(location.hash);if(x){fm.value=x[1];go();}});go();
})();
"""


def main():
    out = {"index.html": index_page(), "summary.html": summary_page(), "route.html": route_page(), "questions.html": questions_page(),
           "methods.html": methods_page(), "penalty.html": penalty_page(), "costs.html": costs_page(), "review.html": review_page(),
           "flagged.html": flagged_page(), "sources.html": sources_page(), "EXECUTIVE_SUMMARY.md": summary_md(),
           "data/costs.csv": costs_csv(), "assets/style.css": CSS, "assets/app.js": JS}
    for name, text in out.items():
        p = HERE / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    print("build: %d files; %d cost rows; %d sources; %d passages" % (len(out), len(COSTS["rows"]), len(SOURCES), len(QUOTE)))


if __name__ == "__main__":
    main()
