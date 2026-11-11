#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic generator for answer-79e1d607 (no network, no clock, standard library only).

    python3 answer-79e1d607/build.py          # write pages and data
    python3 answer-79e1d607/build.py --check  # fail if any generated file differs from disk

Inputs: content.py (facts and needles), data/capture-log.md (exact words captured 2026-11-11),
data/repo-scan.json (point-in-time scan written by scan.py). Arithmetic uses decimal.Decimal."""
import csv, html, io, json, math, os, re, sys
from decimal import Decimal as D, ROUND_HALF_UP

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import content as C  # noqa: E402

esc = html.escape
KIND = {"CN": "PRC government or regulator", "US": "US government", "BK": "Bank's own published page or feed",
        "PV": "Private company's own published terms", "NR": "Not readable or not read"}


# ---------------------------------------------------------------- ledger
def parse_log():
    out, cur = [], None
    for line in open(os.path.join(HERE, "data", "capture-log.md"), encoding="utf-8").read().split("\n"):
        m = re.match(r"^### ((?:CN|US|BK|PV|NR)-\d\d) (.*)$", line)
        if m:
            head = m.group(2)
            title, _, read = head.partition(" — ")
            cur = {"id": m.group(1), "title": title.strip(), "read": read.strip(), "url": "", "quotes": [],
                   "notes": [], "kind": KIND[m.group(1)[:2]]}
            out.append(cur)
        elif line.startswith("## "):
            cur = None
        elif cur is not None:
            if line.startswith("> "):
                cur["quotes"].append(line[2:])
            elif re.match(r"^https?://\S+$", line) and not cur["url"]:
                cur["url"] = line
            elif line.strip():
                cur["notes"].append(line.strip())
    return out


LEDGER = parse_log()
BYID = {s["id"]: s for s in LEDGER}
NREAD = sum(1 for s in LEDGER if not s["id"].startswith("NR"))


def needle_ok(sid, needle):
    return sid in BYID and (needle == "" or any(needle in q for q in BYID[sid]["quotes"]))


def src(pairs):
    """Source cell: a link to the publisher's own page plus a link to the exact words in the ledger."""
    seen, bits = [], []
    for sid, _ in pairs:
        if sid in seen:
            continue
        seen.append(sid)
        s = BYID[sid]
        bits.append('<span class="src"><a href="%s" rel="noopener">%s&nbsp;↗</a> <a class="w" href="sources.html#%s">words</a></span>'
                    % (esc(s["url"]), sid, sid))
    return " ".join(bits)


# ---------------------------------------------------------------- arithmetic
def q(x, places="0.01"):
    return x.quantize(D(places), ROUND_HALF_UP)


def rates(b):
    if b["unit"] == "inverse":
        s, bu = D(1) / D(b["sell"]["value"]), D(1) / D(b["buy"]["value"])
    else:
        s, bu = D(b["sell"]["value"]) / D(b["unit"]), D(b["buy"]["value"]) / D(b["unit"])
    return s, bu, (s + bu) / 2


def fee_cny(b, cny):
    pct = D(b["pct"]["value"])
    if pct == 0:
        return D(0)
    return min(max(cny * pct, D(b["min"]["value"])), D(b["max"]["value"])) + D(b["cable"]["value"])


def cost_row(b, x):
    s, bu, mid = rates(b)
    x = D(x)
    principal = x * s
    fee = fee_cny(b, principal)
    spread = x * (s - bu) / 2
    cost = spread + fee
    return {"amount_usd": int(x), "cny_needed": q(principal + fee), "spread_usd": q(spread / mid), "fee_cny": q(fee),
            "fee_usd": q(fee / mid), "cost_usd": q(cost / mid), "cost_pct": q(cost / mid / x * 100, "0.001"),
            "_raw": cost / mid}


COSTS = {b["id"]: [cost_row(b, x) for x in C.AMOUNTS] for b in C.BANKS}
BEST = []
for i, x in enumerate(C.AMOUNTS):
    bid = min(C.BANKS, key=lambda b: COSTS[b["id"]][i]["_raw"])["id"]
    BEST.append((bid, COSTS[bid][i]))
BNAME = {b["id"]: b for b in C.BANKS}


def money(d):
    return "$" + format(d, ",.2f")


def bank_srcs(b):
    return [(b[k]["sid"], b[k]["needle"]) for k in ("sell", "buy", "pct", "min", "max", "cable")]


NS, NB, NM = rates(C.NOTE_RATE)
BOC_S = rates(BNAME["BOC"])[0]
ATM_YEAR, ATM_DAY = D(C.CAPS["atm_year"]["value"]), D(C.CAPS["atm_day"]["value"])


def cap_row(x):
    xd = D(x)
    cny = xd * BOC_S
    return {"amount_usd": x, "trips_10k": math.ceil(x / int(C.CAPS["cash_permit"]["value"])),
            "trips_5k": math.ceil(x / int(C.CAPS["cash_free"]["value"])),
            "note_margin_usd": q(xd * (NS - NB) / 2 / NM),
            "card_years": int((cny / ATM_YEAR).to_integral_value(rounding="ROUND_CEILING")),
            "card_withdrawals": int((cny / ATM_DAY).to_integral_value(rounding="ROUND_CEILING"))}


CAPROWS = [cap_row(x) for x in C.AMOUNTS]
FXROWS = []
for year, r in C.IRS_RATES:
    gain = D(100000) * (1 - BOC_S / D(r))
    FXROWS.append({"year": year, "irs_rate": r, "basis_per_100k": q(D(100000) * BOC_S / D(r)),
                   "gain_per_100k": q(gain), "gain_at_400k": q(gain * 4)})
LATE = [{"days": d, "years": y, "surcharge_per_100": q(D(100) * D(C.CAPS["late_daily"]["value"]) * d)}
        for y, d in ((1, 365), (3, 1095), (5, 1825))]


def half_spread_pct(r):
    s, bu, mid = rates(r)
    return q((s - bu) / 2 / mid * 100, "0.001")


SPREADS = [(b["id"], half_spread_pct(b)) for b in C.BANKS if b["id"] != "HSBC-GT"] + [("ICBC", half_spread_pct(C.ICBC_RATE))]
SPREAD_TXT = ("Half of each bank's own buy–sell gap on today's board: "
              + ", ".join("%s %s%%" % (i.replace("-TT", ""), p) for i, p in SPREADS) + " of the amount.")

try:
    SCAN = json.load(open(os.path.join(HERE, "data", "repo-scan.json"), encoding="utf-8"))
except FileNotFoundError:
    SCAN = None

# ---------------------------------------------------------------- html
NAV = [("index.html", "Answer"), ("decide.html", "Decide"), ("methods.html", "Methods"), ("costs.html", "Costs"),
       ("penalty.html", "Penalty"), ("flagged.html", "Flagged"), ("sources.html", "Sources"), ("review.html", "Repo review")]


def page(fn, title, lead, body):
    nav = "".join('<a href="%s"%s>%s</a>' % (f, ' class="on" aria-current="page"' if f == fn else "", t) for f, t in NAV)
    return ("""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s · China money</title><link rel="stylesheet" href="assets/style.css"></head><body>
<header><a class="brand" href="index.html">China money · yuan to dollars</a><nav aria-label="Sections">%s</nav></header>
<main><h1>%s</h1><p class="lead">%s</p>
%s
</main><footer><p>Read from the publishers' own pages on %s. Estimates are arithmetic on published figures, not quotes.
Not legal or tax advice. Nothing here is a fact about you: your own tax position must be confirmed with the bank, the tax office and a qualified adviser.</p>
<p><a href="../index.html">All sections of this project</a> · <a href="flagged.html">Flagged for Review</a> · <a href="sources.html">Sources</a></p></footer></body></html>
""" % (esc(title), nav, esc(title), lead, body, C.READ_DATE))


def table(head, rows, cls=""):
    th = "".join("<th>%s</th>" % h for h in head)
    lab = [esc(re.sub(r"<[^>]+>", "", str(h))) for h in head]
    tr = "".join("<tr>" + "".join('<td data-l="%s">%s</td>' % (lab[i], c) for i, c in enumerate(r)) + "</tr>" for r in rows)
    return '<div class="tw"><table class="%s"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (cls, th, tr)


BLANK = '<span class="blank" title="Not confirmed from an official source">—</span>'


def blank(flag=None):
    return BLANK + (' <a class="flag" href="flagged.html#%s">%s</a>' % (flag, flag) if flag else ' <span class="flag">unverified</span>')


def flagify(text):
    return re.sub(r"\b(F\d\d)\b", r'<a class="flag" href="flagged.html#\1">\1</a>', esc(text))


def ul(items):
    return "<ul>" + "".join("<li>%s</li>" % flagify(i) for i in items) + "</ul>" if items else BLANK


b10, b400 = BEST[0], BEST[-1]
FILL = {"best_name": "%s wire" % BNAME[b10[0]]["name"], "best_lo": money(b10[1]["cost_usd"]), "best_hi": money(b400[1]["cost_usd"]),
        "best_pct_lo": "%s%%" % b10[1]["cost_pct"], "best_pct_hi": "%s%%" % b400[1]["cost_pct"]}
COST_SRC = bank_srcs(BNAME[b10[0]])


def summary_rows():
    rows = []
    for head, text, pairs in C.SUMMARY:
        if pairs == "COST":
            pairs = COST_SRC
        rows.append(("<strong>%s</strong>" % esc(head.format(**FILL)), esc(text.format(**FILL)), src(pairs)))
    return rows


def p_index():
    tiles = [("Tax on the exchange itself", "None found", "in the rules read; the bank's condition is paperwork", "penalty.html"),
             ("Cheapest computed route", "%s → %s" % (FILL["best_lo"], FILL["best_hi"]), "on $10,000 → $400,000, %s" % esc(FILL["best_name"]), "costs.html"),
             ("What unlocks the bank", "ID + tax record", "source-of-funds papers that show the amounts", "decide.html"),
             ("Open items", "%d flagged" % len(C.FLAGS), "left blank, not guessed", "flagged.html")]
    t = "".join('<a class="tile" href="%s"><span class="k">%s</span><span class="v">%s</span><span class="n">%s</span></a>' % (h, esc(k), esc(v), n)
                for k, v, n, h in tiles)
    cards = [("decide.html", "Decide", "%d questions to answer before choosing a route, and how to answer each." % len(C.REGISTER)),
             ("methods.html", "Methods", "%d ways to turn yuan into dollars: who can use each, limits, pros, cons, exact steps." % len(C.METHODS)),
             ("costs.html", "Costs", "Every $10,000 step to $400,000, most important number first."),
             ("penalty.html", "Penalty", "The so-called conversion penalty split into %d layers." % len(C.LAYERS)),
             ("flagged.html", "Flagged for Review", "%d items left blank or irregular, each with a source link." % len(C.FLAGS)),
             ("sources.html", "Sources", "%d pages read on %s with the exact words relied on; %d more could not be read." % (NREAD, C.READ_DATE, len(LEDGER) - NREAD)),
             ("review.html", "Repo review", "Every line of the repository scanned for figures that today's reading contradicts.")]
    c = "".join('<a class="card" href="%s"><h3>%s</h3><p>%s</p></a>' % (h, esc(a), esc(b)) for h, a, b in cards)
    key = [C.AMOUNTS.index(a) for a in (10000, 50000, 100000, 200000, 300000, 400000)]
    krows = [("$%s" % format(C.AMOUNTS[i], ","), "<strong>%s</strong>" % money(BEST[i][1]["cost_usd"]), "%s%%" % BEST[i][1]["cost_pct"],
              esc(BNAME[BEST[i][0]]["name"]), src(bank_srcs(BNAME[BEST[i][0]]))) for i in key]
    body = ('<section class="tiles">%s</section><h2>Executive summary</h2>%s'
            '<h2>Lowest computed cost at six sizes</h2>%s<p class="note">Exchange margin plus the sending bank\'s fee. Not included: intermediary and receiving bank fees, any tax. <a href="costs.html">All 40 rows and every route</a>.</p>'
            '<h2>Choose a category</h2><section class="cards">%s</section>'
            '<h2>What only you can supply</h2><p>Where the yuan came from, whether tax was paid on it and can be shown, how your bank records you, and your dollar cost basis. '
            'Until those are known no route can be chosen and no personal tax figure can be stated. <a href="decide.html">Open the decision register</a>.</p>'
            % (t, table(["Finding", "What it means", "Sources"], summary_rows(), "wide"),
               table(["Send", "Lowest cost", "% of amount", "Route", "Sources"], krows), c))
    return page("index.html", "Getting yuan out of China as a US citizen",
                "Short answer: nothing in the rules read taxes the conversion itself. At the cheapest bank read today the cost is the bank's margin and fee, %s to %s of the amount, once you can show where the money came from and that Chinese tax on it was paid." % (FILL["best_pct_hi"], FILL["best_pct_lo"]), body)


def p_decide():
    rows = [("<strong>%s</strong> %s" % (i, esc(qn)), esc(why), esc(known), esc(miss), esc(how), src(pairs))
            for i, qn, why, known, miss, how, pairs in C.REGISTER]
    return page("decide.html", "Decision register",
                "Questions that must be answered before any route is chosen. The middle columns separate what the rules say from what this project does not have.",
                table(["Question", "Why it decides the outcome", "What the rules say", "What we do not have", "How to find out", "Sources"], rows, "wide"))


def status(m):
    return {"A": "Lawful", "B": "Lawful, conditional", "C": "Lawful, capped", "D": "Lawful", "E": "Not confirmed", "X": "Unlawful"}[m["group"]]


def p_methods():
    out = []
    for g, gname in C.GROUPS.items():
        ms = [m for m in C.METHODS if m["group"] == g]
        rows = [('<a href="#%s"><strong>%s</strong></a> %s' % (m["id"], m["id"], esc(m["name"])),
                 '<span class="st %s">%s</span>' % (g, status(m)), flagify(m["cost"]) if m["cost"] else blank(),
                 esc(m["limit"]) if m["limit"] else blank(), src(m["src"])) for m in ms]
        out.append("<h2>%s</h2>%s" % (esc(gname), table(["Method", "Status", "Cost", "Limit", "Sources"], rows, "wide")))
    out.append("<h2>Each method in detail</h2>")
    for m in C.METHODS:
        s0 = src(m["src"])
        rows = [("Who can use it", esc(m["who"]) if m["who"] else blank(), s0), ("Limit", esc(m["limit"]) if m["limit"] else blank(), s0),
                ("Cost", flagify(m["cost"]) if m["cost"] else blank(), s0), ("For", ul(m["pros"]), s0), ("Against", ul(m["cons"]), s0)]
        rows += [("Step %d" % (n + 1), esc(t), src([(sid, nd)])) for n, (t, sid, nd) in enumerate(m["steps"])]
        out.append('<h3 id="%s">%s · %s <span class="st %s">%s</span></h3>%s'
                   % (m["id"], m["id"], esc(m["name"]), m["group"], status(m), table(["", "Detail", "Sources"], rows, "kv")))
    return page("methods.html", "Every way to turn yuan into dollars",
                "Lawful routes first, with who can use them, limits, costs, points for and against, and the steps. Unlawful routes are listed only so their penalties are visible; no steps are given for them.",
                "".join(out))


def p_costs():
    ids = [b["id"] for b in C.BANKS]
    allsrc = []
    for b in C.BANKS:
        allsrc += bank_srcs(b)
    head = ["Send", "Lowest cost", "Route"] + [esc(b["label"]) for b in C.BANKS] + ["ICBC", "CCB", "Wise", "Sources"]
    rows = []
    for i, x in enumerate(C.AMOUNTS):
        bid, r = BEST[i]
        rows.append(["$%s" % format(x, ","), "<strong>%s</strong> <small>%s%%</small>" % (money(r["cost_usd"]), r["cost_pct"]), esc(BNAME[bid]["label"])]
                    + [money(COSTS[j][i]["cost_usd"]) for j in ids] + [blank("F05"), blank("F06"), blank("F08"), src(bank_srcs(BNAME[bid]))])
    out = ["<h2>All routes, every $10,000 step</h2>", table(head, rows, "num sticky"),
           '<p class="note">Cost = half the bank\'s own buy–sell gap on the amount, plus the bank\'s published wire fee, turned into dollars at that bank\'s midpoint. '
           'A blank means the price could not be read from the publisher and is flagged, never zero.</p>']
    inc = [("In the figure", "Exchange margin: half the gap between the bank's selling and buying rate for dollars.", src([(b["sell"]["sid"], "") for b in C.BANKS])),
           ("In the figure", "The sending bank's commission and cable fee.", src([(b["pct"]["sid"], "") for b in C.BANKS])),
           ("Not in the figure", "Fees taken by intermediary banks and by the receiving bank. %s" % blank("F10"), src([("BK-04", ""), ("PV-02", "")])),
           ("Not in the figure", "Any Chinese or US tax. See the penalty page.", src([("CN-12", ""), ("US-08", "")])),
           ("Caveat", "Boards are indicative; the live dealing rate applies. %s" % blank("F23").replace(BLANK + " ", ""), src([("BK-01", "")]))]
    out += ["<h2>What is and is not in the figure</h2>", table(["", "Item", "Sources"], inc, "kv")]
    brow = []
    for b in C.BANKS:
        s, bu, mid = rates(b)
        feetxt = ("0.1%% of the amount, minimum CNY %s, maximum CNY %s, plus cable CNY %s" % (b["min"]["value"], b["max"]["value"], b["cable"]["value"])
                  if D(b["pct"]["value"]) else "No transfer fee (Premier)")
        brow.append(("<strong>%s</strong> %s<br><small>%s</small>" % (b["id"], esc(b["name"]), esc(b["route"])), "%s" % q(s, "0.00001"), "%s" % q(bu, "0.00001"),
                     "%s%%" % half_spread_pct(b), esc(feetxt), esc(b["stamp"]["value"]), flagify(b["caveat"]), src(bank_srcs(b) + [(b["stamp"]["sid"], "")])))
    out += ["<h2>The published prices behind each route</h2>",
            table(["Route", "Bank sells $1 for (CNY)", "Bank buys $1 for (CNY)", "Margin, one way", "Wire fee", "Board time", "Caveat", "Sources"], brow, "wide")]
    for b in C.BANKS:
        rws = [("$%s" % format(r["amount_usd"], ","), "<strong>%s</strong>" % money(r["cost_usd"]), "%s%%" % r["cost_pct"], money(r["spread_usd"]),
                money(r["fee_usd"]), "¥%s" % format(r["cny_needed"], ",.2f"), src(bank_srcs(b))) for r in COSTS[b["id"]]]
        out.append('<details><summary>%s · %s · %s</summary>%s</details>'
                   % (b["id"], esc(b["name"]), esc(b["route"]),
                      table(["Send", "Total cost", "% of amount", "of which margin", "of which fee", "Yuan needed", "Sources"], rws, "num sticky")))
    crow = [("$%s" % format(r["amount_usd"], ","), r["trips_10k"], r["trips_5k"], money(r["note_margin_usd"]), r["card_years"], format(r["card_withdrawals"], ","),
             blank(), src([(C.CAPS["cash_permit"]["sid"], ""), (C.CAPS["atm_year"]["sid"], ""), ("BK-01", "")])) for r in CAPROWS]
    out += ["<h2>Capped routes: how long they take</h2>",
            table(["Send", "Cash trips at $10,000 (bank permit each)", "Cash trips at $5,000 (no permit)", "Margin on notes at Bank of China",
                   "Card cash abroad: calendar years at the RMB 100,000 yearly cap", "Card withdrawals at RMB 10,000", "Travel, ATM and card fees", "Sources"], crow, "num sticky"),
            '<p class="note">Card years use Bank of China\'s selling rate today as a stand-in; the card scheme\'s own rate was not read. A second trip within 15 days is limited to US$1,000 in notes.</p>']
    nrows = [("<strong>%s</strong>" % esc(x["name"]), esc(x["have"]) if x["have"] else blank(), esc(x["missing"]), blank(x["flag"]), src(x["src"])) for x in C.BLANKS]
    out += ["<h2>Routes with no readable price</h2>", table(["Route", "What was read", "What is missing", "Cost", "Sources"], nrows, "wide")]
    return page("costs.html", "What it costs to convert and send",
                "Estimated from each bank's own rate board and fee sheet read on %s. Amount first, lowest computed cost next, then every route." % C.READ_DATE, "".join(out))


def p_penalty():
    rows = []
    for i, name, when, size, pairs in C.LAYERS:
        if size == "COST_SPREAD":
            cell = esc(SPREAD_TXT)
        elif size == "":
            cell = BLANK + " " + flagify(C.BLANK_NOTES[i])
        else:
            cell = esc(size)
        rows.append(("<strong>%s</strong> %s" % (i, esc(name)), esc(when), cell, src(pairs)))
    lsrc = src([(C.CAPS["late_daily"]["sid"], "")])
    lrows = [("%d year%s (%s days)" % (r["years"], "" if r["years"] == 1 else "s", format(r["days"], ",")), "CNY %s" % r["surcharge_per_100"], "CNY 50 to 500", lsrc) for r in LATE]
    fsrc = src([C.IRS_SRC, ("BK-01", ""), ("US-02", "")])
    frows = [(r["year"], r["irs_rate"], money(r["basis_per_100k"]), ("gain " if r["gain_per_100k"] >= 0 else "loss ") + money(abs(r["gain_per_100k"])),
              ("gain " if r["gain_at_400k"] >= 0 else "loss ") + money(abs(r["gain_at_400k"])), fsrc) for r in FXROWS]
    body = ("<h2>The layers</h2>" + table(["Layer", "Applies when", "Size", "Sources"], rows, "wide")
            + "<h2>If Chinese tax was never paid: how the bill grows</h2>"
            + table(["Time since the tax was due", "Surcharge per CNY 100 of unpaid tax", "Possible fine per CNY 100 of unpaid tax", "Sources"], lrows)
            + '<p class="note">Arithmetic on the daily rate in the law (0.05% × days). The fine range is what the law allows for not filing, not a prediction. Whether either applies to you depends on facts not known here.</p>'
            + "<h2>US currency gain: why converting now can show a profit in dollars</h2>"
            + table(["If the yuan was received in", "IRS average rate that year (yuan per $)", "Dollar cost of the yuan that buys $100,000 today", "Dollar gain or loss per $100,000 sent", "At $400,000", "Sources"], frows)
            + '<p class="note">Uses Bank of China\'s selling rate today (%s yuan per dollar) and the IRS yearly averages. Dollars of gain or loss, not tax. The real basis is the rate on each day the yuan was received (%s); how a gain above $200 is taxed is not in the words read (%s).</p>'
            % (q(BOC_S, "0.0001"), '<a class="flag" href="flagged.html#F22">F22</a>', '<a class="flag" href="flagged.html#F19">F19</a>'))
    return page("penalty.html", "What the conversion penalty is made of",
                "There is no single penalty. There are layers, and most apply only in particular cases. The two that always apply are the bank's margin and its fee.", body)


def p_flagged():
    rows = [('<strong id="%s">%s</strong>' % (i, i), '<span class="st %s">%s</span>' % ("X" if kind == "Irregularity" else "E", kind), esc(what), esc(eff), esc(do), src(pairs))
            for i, kind, what, eff, do, pairs in C.FLAGS]
    nr = [("<strong>%s</strong> %s" % (s["id"], esc(s["title"])), esc(s["read"]), src([(s["id"], "")])) for s in LEDGER if s["id"].startswith("NR")]
    body = ("<h2>Flagged items</h2>" + table(["#", "Kind", "What", "Effect on the published tables", "What a person should do", "Sources"], rows, "wide")
            + "<h2>Pages that could not be read</h2>" + table(["Page", "What happened", "Link"], nr, "wide")
            + '<p class="note">Flagged items do not block publication. Each blank cell on this site links back to its flag here.</p>')
    return page("flagged.html", "Flagged for Review",
                "Everything that could not be confirmed from the publisher's own page, and every irregularity found. Values in these rows are left blank on the other pages.", body)


def p_sources():
    rows = []
    for s in LEDGER:
        qs = "".join("<blockquote>%s</blockquote>" % esc(x) for x in s["quotes"]) or BLANK
        ns = "".join('<p class="note">%s</p>' % esc(x) for x in s["notes"])
        rows.append(('<strong id="%s">%s</strong>' % (s["id"], s["id"]), "%s<br><small>%s</small>" % (esc(s["title"]), esc(s["kind"])),
                     esc(s["read"]), qs + ns, '<a href="%s" rel="noopener">open&nbsp;↗</a>' % esc(s["url"])))
    n = {k: sum(1 for s in LEDGER if s["id"].startswith(k)) for k in KIND}
    lead = ("%d pages: %d PRC government or regulator, %d US government, %d bank pages or feeds, %d private companies, %d not readable or not read. "
            "Fetched %s; the exact words relied on are shown so each can be checked against the live page." % (len(LEDGER), n["CN"], n["US"], n["BK"], n["PV"], n["NR"], C.READ_DATE))
    return page("sources.html", "Sources and exact words", lead,
                table(["ID", "Page", "How much was read", "Exact words relied on, and notes", "Link"], rows, "wide"))


def p_review():
    if not SCAN:
        return page("review.html", "Repo review", "Scan not yet run.", "<p>Run <code>python3 answer-79e1d607/scan.py</code>.</p>")
    rows = []
    for rid, _, what, finding, pairs in C.REVIEW_RULES:
        r = SCAN["rules"][rid]
        ex = "".join("<li><code>%s:%d</code> %s</li>" % (esc(e["file"]), e["line"], esc(e["text"])) for e in r["examples"])
        top = ", ".join("<code>%s</code> (%d)" % (esc(f), n) for f, n in r["top_files"])
        rows.append(("<strong>%s</strong> %s" % (rid, esc(what)), esc(finding), "%d lines in %d files" % (r["lines"], r["files"]),
                     (top or "none") + ("<ul>%s</ul>" % ex if ex else ""), src(pairs)))
    m = SCAN["meta"]
    body = ("<p>Scope: every line of every tracked text file at commit <code>%s</code> — %s files, %s lines — except this section itself, the task board and generated exports. "
            "A hit means the line matches a pattern, not that it is wrong; each row says what today's reading shows so a person can judge. Other sessions' files were not edited.</p>"
            % (esc(m["commit"]), format(m["files"], ","), format(m["lines"], ","))
            + table(["What was looked for", "What today's reading shows", "Hits", "Where (most hits first) and examples", "Sources"], rows, "wide")
            + '<p class="note">Point-in-time scan; it is not re-run by the checks, so later changes elsewhere in the repository do not alter this page.</p>')
    return page("review.html", "Repo review, line by line", "Figures elsewhere in this repository checked against what the official pages said on %s." % C.READ_DATE, body)


def exec_md():
    out = ["# China money — executive summary (answer-79e1d607)", "",
           "Read from the publishers' own pages on %s. Estimates are arithmetic on published figures, not quotes. Not legal or tax advice." % C.READ_DATE, ""]
    for head, text, pairs in C.SUMMARY:
        pairs = COST_SRC if pairs == "COST" else pairs
        links = " ".join("[%s](%s)" % (sid, BYID[sid]["url"]) for sid in dict.fromkeys(s for s, _ in pairs))
        out.append("- **%s** %s Sources: %s" % (head.format(**FILL), text.format(**FILL), links))
    out += ["", "Site: `answer-79e1d607/index.html`. Open items: `answer-79e1d607/flagged.html`.", ""]
    return "\n".join(out)


def strip(rows):
    return [{k: (str(v) if isinstance(v, D) else v) for k, v in r.items() if not k.startswith("_")} for r in rows]


def outputs():
    o = {"index.html": p_index(), "decide.html": p_decide(), "methods.html": p_methods(), "costs.html": p_costs(),
         "penalty.html": p_penalty(), "flagged.html": p_flagged(), "sources.html": p_sources(), "review.html": p_review(),
         "EXECUTIVE_SUMMARY.md": exec_md()}
    o["data/sources.json"] = json.dumps(LEDGER, ensure_ascii=False, indent=1) + "\n"
    costs = {"read_date": C.READ_DATE, "method": "cost_usd = (amount*(sell-buy)/2 + fee_cny) / mid; fee_cny = clamp(amount*sell*pct, min, max) + cable",
             "routes": {b["id"]: strip(COSTS[b["id"]]) for b in C.BANKS},
             "lowest": [{"amount_usd": x, "route": BEST[i][0], "cost_usd": str(BEST[i][1]["cost_usd"])} for i, x in enumerate(C.AMOUNTS)],
             "capped": strip(CAPROWS), "currency_gain": strip(FXROWS), "late_surcharge": strip(LATE),
             "blank_routes": [x["id"] for x in C.BLANKS]}
    o["data/costs.json"] = json.dumps(costs, ensure_ascii=False, indent=1) + "\n"
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["amount_usd", "route", "cost_usd", "cost_pct", "spread_usd", "fee_usd", "fee_cny", "cny_needed"])
    for b in C.BANKS:
        for r in COSTS[b["id"]]:
            w.writerow([r["amount_usd"], b["id"], r["cost_usd"], r["cost_pct"], r["spread_usd"], r["fee_usd"], r["fee_cny"], r["cny_needed"]])
    for x in C.BLANKS:
        for a in C.AMOUNTS:
            w.writerow([a, x["id"], "", "", "", "", "", ""])
    o["data/costs.csv"] = buf.getvalue()
    return o


def main():
    bad = []
    outs = outputs()
    for rel, txt in sorted(outs.items()):
        path = os.path.join(HERE, rel)
        if "--check" in sys.argv:
            if not os.path.exists(path) or open(path, encoding="utf-8").read() != txt:
                bad.append(rel)
        else:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(txt)
    if bad:
        print("STALE:", ", ".join(bad))
        sys.exit(1)
    print("%s %d files; %d ledger entries (%d read); lowest cost %s at $10,000, %s at $400,000 (%s)"
          % ("checked" if "--check" in sys.argv else "wrote", len(outs), len(LEDGER), NREAD, FILL["best_lo"], FILL["best_hi"], FILL["best_name"]))


if __name__ == "__main__":
    main()
