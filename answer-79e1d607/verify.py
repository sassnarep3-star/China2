#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Independent checks for answer-79e1d607. Standard library only; no network.

    python3 answer-79e1d607/verify.py

What it proves: structure, traceability and arithmetic. Every figure and statement names captured words;
every table row links to a publisher's page in the ledger; costs are recomputed here with exact fractions,
separately from build.py; blanks stay blank; local links resolve; the pages on disk match the generator.
What it does NOT prove: that a law is still in force, that a bank will deal at its board rate, or anything
about a particular person's tax position. Those need a human, the bank and an adviser."""
import csv, json, os, re, subprocess, sys
from fractions import Fraction as F
from html.parser import HTMLParser
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import content as C  # noqa: E402

fails, checks = [], 0


def ok(cond, msg):
    global checks
    checks += 1
    if not cond:
        fails.append(msg)


def read(rel):
    return open(os.path.join(HERE, rel), encoding="utf-8").read()


# 1 ---------------------------------------------------------------- ledger, parsed here on its own
ledger, cur = {}, None
for line in read("data/capture-log.md").split("\n"):
    m = re.match(r"^### ([A-Z]{2}-\d\d) ", line)
    if m:
        ok(m.group(1) not in ledger, "duplicate ledger id " + m.group(1))
        cur = ledger.setdefault(m.group(1), {"url": None, "quotes": []})
    elif line.startswith("## "):
        cur = None
    elif cur is not None and line.startswith("> "):
        cur["quotes"].append(line[2:])
    elif cur is not None and cur["url"] is None and re.match(r"^https?://\S+$", line):
        cur["url"] = line
HOSTS = {"CN": (".gov.cn",), "US": (".gov",),
         "BK": ("boc.cn", "cmbchina.com", "hsbc.com.cn", "abchina.com", "icbc.com.cn"),
         "PV": ("wise.com", "bankofamerica.com"),
         "NR": ("icbc.com.cn", "abchina.com", "ccb.com", "safe.gov.cn", "westernunion.com")}
for sid, s in ledger.items():
    ok(bool(s["url"]), sid + " has no URL")
    host = urlparse(s["url"] or "").hostname or ""
    ok(any(host == h.lstrip(".") or host.endswith(h if h.startswith(".") else "." + h) or host.endswith(h) for h in HOSTS[sid[:2]]),
       "%s host %s is not in the expected publisher list" % (sid, host))
    if sid.startswith("NR"):
        ok(not s["quotes"], sid + " is marked unreadable but carries quotes")
    else:
        ok(len(s["quotes"]) >= 1, sid + " has no captured words")
built = json.loads(read("data/sources.json"))
ok({b["id"] for b in built} == set(ledger), "sources.json ids differ from the capture log")
for b in built:
    ok(b["url"] == ledger[b["id"]]["url"] and b["quotes"] == ledger[b["id"]]["quotes"], b["id"] + " differs between sources.json and the capture log")
URLS = {s["url"] for s in ledger.values()}


# 2 ---------------------------------------------------------------- every statement names captured words
def needle(sid, nd, where):
    ok(sid in ledger, "%s cites unknown source %s" % (where, sid))
    if sid in ledger and nd:
        ok(any(nd in qt for qt in ledger[sid]["quotes"]), "%s: words not found in %s: %r" % (where, sid, nd[:60]))
    if sid in ledger and not nd:
        ok(sid.startswith("NR"), "%s cites %s with no words" % (where, sid))


TOKENS = {"千分之一": "0.001", "1‰": "0.001", "0.1％": "0.001", "0.1%": "0.001", "万分之五": "0.0005", "Free": "0"}


def price(p, where):
    needle(p["sid"], p["needle"], where)
    ok(p["token"] in p["needle"], "%s: token %r not inside its own words" % (where, p["token"]))
    if re.fullmatch(r"[0-9.]+", p["value"]):
        shown = TOKENS.get(p["token"], p["token"].replace(",", ""))
        ok(F(shown) == F(p["value"]), "%s: value %s differs from captured %s" % (where, p["value"], p["token"]))


for b in C.BANKS:
    for k in ("sell", "buy", "pct", "min", "max", "cable", "stamp"):
        price(b[k], "BANKS/%s/%s" % (b["id"], k))
for name, r in (("ICBC_RATE", C.ICBC_RATE), ("NOTE_RATE", C.NOTE_RATE)):
    for k in ("sell", "buy"):
        price(r[k], name + "/" + k)
for k, p in C.CAPS.items():
    price(p, "CAPS/" + k)
needle(C.IRS_SRC[0], C.IRS_SRC[1], "IRS_SRC")
for y, r in C.IRS_RATES:
    ok("%s: %s" % (y, r) in C.IRS_SRC[1], "IRS rate %s %s not in captured row" % (y, r))
for i, (head, text, pairs) in enumerate(C.SUMMARY):
    for sid, nd in ([] if pairs == "COST" else pairs):
        needle(sid, nd, "SUMMARY/%d" % i)
for row in C.REGISTER:
    ok(len(row[6]) >= 1, row[0] + " has no source")
    for sid, nd in row[6]:
        needle(sid, nd, "REGISTER/" + row[0])
for m in C.METHODS:
    ok(len(m["src"]) >= 1, m["id"] + " has no source")
    for sid, nd in m["src"]:
        needle(sid, nd, "METHODS/%s/src" % m["id"])
    for t, sid, nd in m["steps"]:
        needle(sid, nd, "METHODS/%s/step" % m["id"])
    if m["group"] == "X":
        ok(m["steps"] == [] and m["pros"] == [], m["id"] + " is unlawful but has steps or advantages listed")
for row in C.LAYERS:
    for sid, nd in row[4]:
        needle(sid, nd, "LAYERS/" + row[0])
    ok(row[3] != "" or row[0] in C.BLANK_NOTES, row[0] + " is blank without a note")
flag_ids = [f[0] for f in C.FLAGS]
ok(len(set(flag_ids)) == len(flag_ids), "duplicate flag id")
for row in C.FLAGS:
    for sid, nd in row[5]:
        needle(sid, nd, "FLAGS/" + row[0])
for row in C.REVIEW_RULES:
    re.compile(row[1])
    for sid, nd in row[4]:
        needle(sid, nd, "REVIEW/" + row[0])
for x in C.BLANKS:
    ok(x["flag"] in flag_ids, x["id"] + " blank without a flag")
    for sid, nd in x["src"]:
        needle(sid, nd, "BLANKS/" + x["id"])

# 3 ---------------------------------------------------------------- arithmetic, recomputed with exact fractions
ok(C.AMOUNTS == [10000 * i for i in range(1, 41)], "amounts are not $10,000 steps to $400,000")


def cents(x, places=2):
    scale = 10 ** places
    n = x * scale
    r = (abs(n) * 2 + 1) // 2
    return (r if n >= 0 else -r), scale


def same(x, shown, places=2):
    r, scale = cents(x, places)
    return F(int(r), scale) == F(shown)


def sb(r):
    if r["unit"] == "inverse":
        return 1 / F(r["sell"]["value"]), 1 / F(r["buy"]["value"])
    return F(r["sell"]["value"]) / F(r["unit"]), F(r["buy"]["value"]) / F(r["unit"])


costs = json.loads(read("data/costs.json"))
best = {}
for b in C.BANKS:
    s, bu = sb(b)
    mid = (s + bu) / 2
    ok(s > bu > 0, b["id"] + " selling rate is not above buying rate")
    rows = costs["routes"][b["id"]]
    ok([r["amount_usd"] for r in rows] == C.AMOUNTS, b["id"] + " does not have all 40 amounts")
    for r in rows:
        x = F(r["amount_usd"])
        pct = F(b["pct"]["value"])
        fee = F(0) if pct == 0 else min(max(x * s * pct, F(b["min"]["value"])), F(b["max"]["value"])) + F(b["cable"]["value"])
        cost = (x * (s - bu) / 2 + fee) / mid
        tag = "%s $%d" % (b["id"], r["amount_usd"])
        ok(same(cost, r["cost_usd"]), tag + " cost")
        ok(same(cost / x * 100, r["cost_pct"], 3), tag + " percent")
        ok(same(x * (s - bu) / 2 / mid, r["spread_usd"]), tag + " margin")
        ok(same(fee, r["fee_cny"]) and same(fee / mid, r["fee_usd"]), tag + " fee")
        ok(same(x * s + fee, r["cny_needed"]), tag + " yuan needed")
        if r["amount_usd"] not in best or cost < best[r["amount_usd"]][1]:
            best[r["amount_usd"]] = (b["id"], cost)
for low in costs["lowest"]:
    ok(best[low["amount_usd"]][0] == low["route"] and same(best[low["amount_usd"]][1], low["cost_usd"]), "lowest at $%d" % low["amount_usd"])
ns, nb = sb(C.NOTE_RATE)
bs, _ = sb(next(b for b in C.BANKS if b["id"] == "BOC"))
for r in costs["capped"]:
    x = r["amount_usd"]
    ok(r["trips_10k"] == -(-x // 10000) and r["trips_5k"] == -(-x // 5000), "cash trips at $%d" % x)
    ok(same(F(x) * (ns - nb) / 2 / ((ns + nb) / 2), r["note_margin_usd"]), "note margin at $%d" % x)
    cny = F(x) * bs
    ok(r["card_years"] == -(-cny // 100000) and r["card_withdrawals"] == -(-cny // 10000), "card arithmetic at $%d" % x)
for r in costs["currency_gain"]:
    g = 100000 * (1 - bs / F(r["irs_rate"]))
    ok(same(g, r["gain_per_100k"]) and same(4 * g, r["gain_at_400k"]) and same(100000 * bs / F(r["irs_rate"]), r["basis_per_100k"]), "currency gain " + r["year"])
for r in costs["late_surcharge"]:
    ok(same(100 * F(C.CAPS["late_daily"]["value"]) * r["days"], r["surcharge_per_100"]), "late surcharge %d days" % r["days"])
rows = list(csv.DictReader(read("data/costs.csv").splitlines()))
ok(len(rows) == 40 * (len(C.BANKS) + len(C.BLANKS)), "costs.csv row count")
for r in rows:
    if r["route"] in [x["id"] for x in C.BLANKS]:
        ok(all(r[k] == "" for k in ("cost_usd", "cost_pct", "spread_usd", "fee_usd", "fee_cny", "cny_needed")), "blank route %s has a value" % r["route"])


# 4 ---------------------------------------------------------------- pages
class P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows, self.row, self.links, self.ids, self.cells = [], None, [], set(), 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "tr":
            self.row = {"td": 0, "hrefs": []}
        if tag == "td" and self.row is not None:
            self.row["td"] += 1
        if tag in ("a", "link") and a.get("href"):
            self.links.append(a["href"])
            if self.row is not None:
                self.row["hrefs"].append(a["href"])

    def handle_endtag(self, tag):
        if tag == "tr" and self.row is not None:
            if self.row["td"]:
                self.rows.append(self.row)
            self.row = None


PAGES = ["index.html", "decide.html", "methods.html", "costs.html", "penalty.html", "flagged.html", "sources.html", "review.html"]
parsed, total_rows = {}, 0
for pg in PAGES:
    ok(os.path.exists(os.path.join(HERE, pg)), pg + " missing")
    p = P()
    p.feed(read(pg))
    parsed[pg] = p
    ok(len(p.rows) > 0, pg + " has no table rows")
    for i, r in enumerate(p.rows):
        total_rows += 1
        ok(any(h in URLS for h in r["hrefs"]), "%s row %d has no link to a publisher's page in the ledger" % (pg, i + 1))
    txt = read(pg)
    ok('name="viewport"' in txt and 'class="tw"' in txt, pg + " is not set up for small screens")
    for banned in ("tax-free", "tax free", "guarantee", "no tax is due", "loophole"):
        ok(banned not in txt.lower(), "%s uses the phrase %r" % (pg, banned))
for pg, p in parsed.items():
    for h in p.links:
        if h.startswith(("http://", "https://", "mailto:")):
            continue
        path, _, frag = h.partition("#")
        target = pg if path == "" else path
        if target.startswith("../"):
            ok(os.path.exists(os.path.normpath(os.path.join(HERE, target))), "%s links to missing %s" % (pg, target))
            continue
        ok(os.path.exists(os.path.join(HERE, target)), "%s links to missing %s" % (pg, target))
        if frag and target in parsed:
            ok(frag in parsed[target].ids, "%s links to missing anchor %s#%s" % (pg, target, frag))
ctxt = read("costs.html")
for x in C.AMOUNTS:
    ok('<td data-l="Send">$%s</td>' % format(x, ",") in ctxt, "costs.html lacks the $%d row" % x)
ok(ctxt.count('class="blank"') >= 3 * 40, "blank cells missing for routes with no readable price")
ok(all(('id="%s"' % f) in read("flagged.html") for f in flag_ids), "a flag is not published on the Flagged page")
ok(all(('id="%s"' % s) in read("sources.html") for s in ledger), "a source is not published on the Sources page")
ok(all(('id="%s"' % m["id"]) in read("methods.html") for m in C.METHODS), "a method is not published")

# 5 ---------------------------------------------------------------- generator parity
r = subprocess.run([sys.executable, os.path.join(HERE, "build.py"), "--check"], capture_output=True, text=True,
                   env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
ok(r.returncode == 0, "generated files differ from build.py output: " + r.stdout.strip())

if fails:
    print("FAILED %d of %d checks" % (len(fails), checks))
    for f in fails[:60]:
        print(" -", f)
    sys.exit(1)
print("OK %d checks: %d ledger entries, %d table rows each linked to a publisher's page, %d cost rows recomputed, %d flags published"
      % (checks, len(ledger), total_rows, 40 * len(C.BANKS), len(flag_ids)))
