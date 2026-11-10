#!/usr/bin/env python3
"""Build the cny-usd-6869721b site from data/*.json.

Deterministic: no clock, no network. Run from anywhere:
    PYTHONDONTWRITEBYTECODE=1 python3 cny-usd-6869721b/build.py
Inputs : data/sources.json, data/inputs.json, data/content.json (hand-authored)
Outputs: data/ladder.json, data/ladder.csv, *.html, EXECUTIVE_SUMMARY.md
"""
import csv
import html
import json
import os
from decimal import Decimal as D, ROUND_HALF_UP, ROUND_CEILING

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


SRC = load("sources.json")
INP = load("inputs.json")
CON = load("content.json")
SOURCES = {s["id"]: s for s in SRC["sources"]}
RETRIEVED = "10 November 2026"

# ---------------------------------------------------------------- arithmetic
def q2(x):
    return D(x).quantize(D("0.01"), rounding=ROUND_HALF_UP)


def ceil_int(x):
    return int(D(x).to_integral_value(rounding=ROUND_CEILING))


def clamp(x, lo, hi):
    return max(D(lo), min(D(hi), x))


RATE = {}
for k, r in INP["rates"].items():
    buy, sell = D(r["buy"]) / 100, D(r["sell"]) / 100
    mid = (buy + sell) / 2
    RATE[k] = {"buy": buy, "sell": sell, "mid": mid, "half": (sell - mid) / mid, "src": r["source"], "name": r["name"], "as_of": r["as_of"], "buy_s": r["buy"], "sell_s": r["sell"]}
PARITY = D(INP["parity"]["value"]) / 100
IRS = {y: D(v["value"]) for y, v in INP["irs_avg"]["years"].items()}
AMOUNTS = list(range(INP["amounts_usd"]["start"], INP["amounts_usd"]["end"] + 1, INP["amounts_usd"]["step"]))
BOC = RATE["BOC"]
QUOTA = D(INP["quota"]["usd_per_year"]) * 10000
EMI_CAP = D(INP["emigrant"]["single_cap_cny"]) * 10000
ATM_DAY = D(INP["atm"]["per_card_day_cny"]) * 10000
ATM_YEAR = D(INP["atm"]["per_person_year_cny"]) * 10000


def wire(bank, usd):
    """Convert and wire `usd` dollars at `bank`: spread against the bank's own midpoint, plus tariff."""
    r, f = RATE[bank], INP["wire_fees"][bank]
    usd = D(usd)
    cny = usd * r["sell"]
    fee_cny = clamp(cny * D(f["permille"]) / 1000, f["min"], f["max"]) + D(f["cable"])
    spread = usd * r["half"]
    fee_usd = fee_cny / r["sell"]
    return {"cny": cny, "spread": spread, "fee_cny": fee_cny, "fee_usd": fee_usd, "total": spread + fee_usd}


def build_ladder():
    rows = []
    fh = INP["wire_fees"]["HSBC"]
    atm = INP["atm"]
    for a in AMOUNTS:
        A = D(a)
        b, c = wire("BOC", A), wire("ABC", A)
        h_cny = clamp(A * PARITY * D(fh["permille"]) / 1000, fh["min"], fh["max"]) + D(fh["cable"])
        # emigrant staging (Art. 6): half, half of the rest after a year, balance after two years
        if b["cny"] <= EMI_CAP:
            e_parts = [A]
        else:
            e_parts = [A / 2, A / 4, A / 4]
        e_total = sum(wire("BOC", p)["total"] for p in e_parts)
        # yearly quota: one wire per calendar year, at most USD 50,000 each
        n_full, rem = divmod(A, QUOTA)
        q_total = n_full * wire("BOC", QUOTA)["total"] + (wire("BOC", rem)["total"] if rem else 0)
        # ATM: CNY 10,000 per withdrawal, fee CNY 12 + 1% capped at CNY 112
        full, last = divmod(b["cny"], ATM_DAY)
        atm_fee = full * D(atm["per_wd_max"])
        if last:
            atm_fee += min(D(atm["per_wd_fixed"]) + last * D(atm["per_wd_pct"]) / 100, D(atm["per_wd_max"]))
        row = {
            "amount": a,
            "boc_cny": q2(b["cny"]), "boc_spread": q2(b["spread"]), "boc_fee_cny": q2(b["fee_cny"]), "boc_fee_usd": q2(b["fee_usd"]),
            "boc_total": q2(b["total"]), "boc_pct": q2(b["total"] / A * 100), "boc_full_total": q2(b["total"] + D(INP["wire_fees"]["BOC"]["full_amount_usd"])),
            "abc_cny": q2(c["cny"]), "abc_spread": q2(c["spread"]), "abc_fee_cny": q2(c["fee_cny"]), "abc_fee_usd": q2(c["fee_usd"]),
            "abc_total": q2(c["total"]), "abc_pct": q2(c["total"] / A * 100),
            "hsbc_fee_cny": q2(h_cny), "hsbc_fee_usd": q2(h_cny / PARITY),
            "emigrant_wires": len(e_parts), "emigrant_first": q2(e_parts[0]), "emigrant_total": q2(e_total), "emigrant_years": 0 if len(e_parts) == 1 else 2,
            "quota_years": ceil_int(A / QUOTA), "quota_total": q2(q_total),
            "atm_years": ceil_int(b["cny"] / ATM_YEAR), "atm_withdrawals": int(full) + (1 if last else 0), "atm_fee_cny": q2(atm_fee), "atm_fee_usd": q2(atm_fee / BOC["sell"]),
            "cash_trips_5k": ceil_int(A / D(INP["cash"]["no_permit_usd"])), "cash_trips_10k": ceil_int(A / D(INP["cash"]["bank_permit_usd"])), "cash_spread": q2(b["spread"]),
            "recon_days": ceil_int(A / D(INP["reconversion"]["id_only_usd_per_day"])),
            "wise_transfers": ceil_int(b["cny"] / D(INP["wise"]["bank_app_cny"].replace(",", ""))),
            "wu_counter": ceil_int(A / (D(INP["wu"]["counter_usd"]) * 10000)), "wu_online": ceil_int(A / D(INP["wu"]["online_usd"])),
        }
        for y in sorted(IRS, reverse=True):
            row["gain_" + y] = q2(A * (1 - BOC["sell"] / IRS[y]))
        rows.append(row)
    return rows


LADDER = build_ladder()
BY_AMT = {r["amount"]: r for r in LADDER}

# ---------------------------------------------------------------- formatting
E = html.escape


def usd(x, cents=True):
    x = D(x)
    s = f"{abs(x):,.2f}" if cents else f"{abs(x):,.0f}"
    return ("-$" if x < 0 else "$") + s


def cny(x):
    return f"CNY {D(x):,.2f}"


def pct(x, n=2):
    return f"{D(x):.{n}f}%"


def src(ids):
    out = []
    for i in ids:
        s = SOURCES[i]
        out.append(f'<a href="{E(s["url"], quote=True)}" rel="noopener" title="{E(s["publisher"] + " — " + s["title"], quote=True)}">{i}</a>')
    return '<span class="src">' + " ".join(out) + "</span>"


def table(headers, rows, cls=""):
    th = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="tw"><table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>'


NAV = [("index.html", "Summary"), ("costs.html", "Costs"), ("methods.html", "Methods"), ("tax.html", "Tax and penalties"),
       ("review.html", "Repo review"), ("flagged.html", "Flagged for Review"), ("sources.html", "Sources")]


def page(fname, title, lead, body):
    nav = "".join('<a href="%s"%s>%s</a>' % (f, ' class="on" aria-current="page"' if f == fname else "", E(t)) for f, t in NAV)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)} — yuan to dollars</title>
<meta name="description" content="{E(lead, quote=True)}">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header><div class="wrap"><a class="brand" href="index.html">Yuan to dollars</a><nav aria-label="Sections">{nav}</nav></div></header>
<main class="wrap">
<h1>{E(title)}</h1>
<p class="lead">{lead}</p>
{body}
</main>
<footer><div class="wrap"><p>Research, not legal or tax advice. Figures come from official pages read on {RETRIEVED}; each row links to its source. Blank means no official figure was found. <a href="flagged.html">Flagged for Review</a> lists every open item. <a href="../index.html">Back to the project hub</a>.</p></div></footer>
</body>
</html>
"""


def write(name, text):
    with open(os.path.join(HERE, name), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


BLANK = '<span class="blank" title="No official figure found">blank</span>'
STATUS = {"lawful": ("ok", "Lawful, documents needed"), "lawful-approval": ("ok", "Lawful, SAFE approval needed"), "lawful-small": ("ok", "Lawful, small amounts"),
          "conditional": ("warn", "Conditional"), "unlawful": ("bad", "Unlawful")}
VERDICT = {"confirmed": "ok", "confirmed, narrower": "warn", "stale": "bad", "not checked": "warn", "contradicted in part": "bad",
           "confirmed text, unsettled effect": "warn", "superseded": "bad", "incomplete": "warn"}


def badge(kind, text):
    return f'<span class="b {kind}">{E(text)}</span>'


R10, R400 = BY_AMT[10000], BY_AMT[400000]
SELL = BOC["sell"]
KEY = [10000, 50000, 100000, 200000, 300000, 400000]

# ---------------------------------------------------------------- shared blocks
def scenario_table():
    rows = [[f'<b>{E(s["situation"])}</b>', E(s["route"]), E(s["documents"]) or BLANK, E(s["prc_tax"]) or BLANK, E(s["us_side"]) or BLANK, src(s["sources"])] for s in CON["scenarios"]]
    return table(["Your situation", "Route", "Papers", "PRC tax", "US side", "Source"], rows, "wide")


def layer_table():
    rows = [[f'<b>{E(p["layer"])}</b>', E(p["amount"]), E(p["who"]), src(p["sources"])] for p in CON["penalty_layers"]]
    return table(["Layer", "What it costs", "Who takes it", "Source"], rows)


def gain_table(amounts):
    years = sorted(IRS, reverse=True)
    rows = []
    for a in amounts:
        r = BY_AMT[a]
        rows.append([usd(a, False)] + [usd(r["gain_" + y], False) if r["gain_" + y] > 0 else f'<span class="neg">{usd(r["gain_" + y], False)}</span>' for y in years] + [src(["R6", "R2", "A2"])])
    return table(["You receive"] + [f"Yuan from {y}<br><small>avg {IRS[y]}</small>" for y in years] + ["Source"], rows, "num")


def glance_table():
    rows = []
    for a in KEY:
        r = BY_AMT[a]
        rows.append([usd(a, False), f'{usd(r["boc_total"])}<br><small>{pct(r["boc_pct"])}</small>', f'{usd(r["abc_total"])}<br><small>{pct(r["abc_pct"])}</small>',
                     f'{usd(r["emigrant_total"])}<br><small>{r["emigrant_wires"]} wire{"s" if r["emigrant_wires"] > 1 else ""}, {r["emigrant_years"]} yr</small>',
                     f'{r["atm_years"]} yr<br><small>{usd(r["atm_fee_usd"])} fee</small>', f'{r["cash_trips_5k"]} trips', src(["R2", "F1", "R4", "F3", "L8", "L11", "L12"])])
    return table(["You send", "Bank of China wire", "Agricultural Bank wire", "Emigrant transfer", "ATM abroad", "Cash, $5,000 a trip", "Source"], rows, "num glance")


# ---------------------------------------------------------------- index
def build_index():
    kp = [
        (usd(R400["abc_total"]), f'to convert and wire $400,000 at Agricultural Bank of China ({pct(R400["abc_pct"])})', ["R4", "F3"]),
        (usd(R400["boc_total"]), f'the same at Bank of China ({pct(R400["boc_pct"])}); $10,000 costs {usd(R10["abc_total"])} to {usd(R10["boc_total"])}', ["R2", "F1"]),
        (pct(BOC["half"] * 100), "exchange-rate spread at both banks, measured from their own midpoint", ["R2", "R4"]),
        (usd(R400["gain_2024"], False), "exchange-rate gain on $400,000 if the yuan dates from 2024; reportable in the US above $200", ["R6", "A2"]),
    ]
    cards = "".join(f'<div class="kpi"><div class="v">{v}</div><div class="t">{E(t)}</div><div>{src(s)}</div></div>' for v, t, s in kp)
    lead = (f"If you hold a US passport and can show where the yuan came from, the cheapest lawful route found is an ordinary bank conversion and wire. "
            f"At the rates and tariffs published on {RETRIEVED}, $400,000 costs {usd(R400['abc_total'])} at Agricultural Bank of China or {usd(R400['boc_total'])} at Bank of China; "
            f"$10,000 costs {usd(R10['abc_total'])} or {usd(R10['boc_total'])}.")
    body = f"""
<section class="kpis">{cards}</section>
<section class="note"><h2>Three things decide the outcome</h2>
<ol>
<li><b>Papers, not price.</b> A foreign-passport holder has no USD 50,000 yearly quota. The bank sells dollars against your passport plus documents showing the source and amount of the money, including tax vouchers. {src(["L1", "L3", "L4"])}</li>
<li><b>The route follows the source of the money.</b> Pay earned in China, pre-emigration savings, an inheritance and a housing sale each have their own rule. Find your row in the table below. {src(["L1", "L8", "L9"])}</li>
<li><b>The largest tax exposure found is in the US.</b> China taxes the income behind the money, not the transfer. The US treats a gain from exchange-rate movement above $200 as capital gain. At {SELL} yuan per dollar that gain is {pct((1 - SELL / IRS["2024"]) * 100)} of the dollars received for yuan acquired at the 2024 average rate, and {pct((1 - SELL / IRS["2025"]) * 100)} at the 2025 average. {src(["T1", "A2", "R6"])}</li>
</ol></section>
<h2>Which situation is yours?</h2>
<p>Each row names the route written for that source of money. Blank cells are listed on the <a href="flagged.html">Flagged for Review</a> page.</p>
{scenario_table()}
<h2>What the “conversion penalty” is made of</h2>
<p>There is no single penalty. Nine separate layers can take money or time; the first four are prices, the rest are tax, enforcement and waiting.</p>
{layer_table()}
<h2>Cost at a glance</h2>
<p>Published cost of the spread plus bank fees, per method, at six sizes. All 40 steps from $10,000 to $400,000 are on the <a href="costs.html">Costs</a> page.</p>
{glance_table()}
<h2>What to do next</h2>
<ol class="steps">
<li>Find your row in the situation table. The route depends on the source of the money and on the ID the bank holds for you.</li>
<li>Collect the papers for that route before you visit the bank, starting with PRC tax payment records.</li>
<li>Ask the bank for its selling rate and wire fee that day and compare them with the <a href="costs.html">Costs</a> page.</li>
<li>Wire to an account in your own name. At Bank of China, USD 25 buys full-amount arrival.</li>
<li>Before converting, work out what each tranche of yuan was worth in dollars when you received it. A gain above $200 goes on your US return.</li>
<li>Check FBAR, Form 8938 and Form 3520 for every year the account was open.</li>
<li>Stay away from the five routes marked unlawful on the <a href="methods.html">Methods</a> page.</li>
</ol>
<h2>Pages</h2>
<section class="cards">
<a class="card" href="costs.html"><b>Costs</b><span>Every $10,000 step to $400,000 for each priced method, bank comparison, receiving-bank fees.</span></a>
<a class="card" href="methods.html"><b>Methods</b><span>{len(CON["methods"])} routes with who can use them, limits, pros, cons and steps.</span></a>
<a class="card" href="tax.html"><b>Tax and penalties</b><span>PRC tax by source of money, US exchange-rate gain, reporting penalties, PRC fines.</span></a>
<a class="card" href="review.html"><b>Repo review</b><span>{len(CON["claims"])} claims in this repository checked against the sources read today.</span></a>
<a class="card" href="flagged.html"><b>Flagged for Review</b><span>{len(CON["flags"])} open items: blanks, stale tables and unsettled readings.</span></a>
<a class="card" href="sources.html"><b>Sources</b><span>{len(SOURCES)} official sources with the exact text relied on.</span></a>
</section>
"""
    write("index.html", page("index.html", "Getting yuan out of China as dollars", lead, body))


# ---------------------------------------------------------------- costs
def build_costs():
    bank_rows = []
    for k in ["BOC", "ABC"]:
        r, f = RATE[k], INP["wire_fees"][k]
        lo, hi = D(f["min"]) + D(f["cable"]), D(f["max"]) + D(f["cable"])
        bank_rows.append([f'<b>{E(r["name"])}</b>', r["sell_s"], r["buy_s"], pct(r["half"] * 100, 4), f'{cny(lo)} to {cny(hi)}', usd(BY_AMT[400000][k.lower() + "_total"]), src([r["src"], f["source"]])])
    fh = INP["wire_fees"]["HSBC"]
    bank_rows.append(["<b>HSBC China</b> (Premier, Advance)", BLANK, BLANK, BLANK, f'{cny(D(fh["min"]) + D(fh["cable"]))} to {cny(D(fh["max"]) + D(fh["cable"]))}', BLANK, src(["F4"])])
    for ob in CON["other_banks"]:
        if ob["rate_key"]:
            r = RATE[ob["rate_key"]]
            cells = [r["sell_s"], r["buy_s"], pct(r["half"] * 100, 4)]
        else:
            cells = [BLANK, BLANK, BLANK]
        bank_rows.append([f'<b>{E(ob["bank"])}</b>'] + cells + [BLANK + f'<br><small class="wn">{E(ob["fee_note"])}</small>', BLANK, src(ob["sources"])])
    banks = table(["Bank", "Sells $100 for", "Buys $100 for", "Spread from midpoint", "Fee per wire", "All-in at $400,000", "Source"], bank_rows, "num")

    def ladder(cols, fn, sources):
        return table(cols + ["Source"], [fn(r) + [src(sources)] for r in LADDER], "num")

    boc = ladder(["You send", "Cost", "% lost", "Spread", "Bank fee", "Fee in yuan", "Yuan needed", "With full-amount arrival"],
                 lambda r: [usd(r["amount"], False), f'<b>{usd(r["boc_total"])}</b>', pct(r["boc_pct"]), usd(r["boc_spread"]), usd(r["boc_fee_usd"]), cny(r["boc_fee_cny"]), cny(r["boc_cny"]), usd(r["boc_full_total"])], ["R2", "F1"])
    abc = ladder(["You send", "Cost", "% lost", "Spread", "Bank fee", "Fee in yuan", "Yuan needed"],
                 lambda r: [usd(r["amount"], False), f'<b>{usd(r["abc_total"])}</b>', pct(r["abc_pct"]), usd(r["abc_spread"]), usd(r["abc_fee_usd"]), cny(r["abc_fee_cny"]), cny(r["abc_cny"])], ["R4", "F3"])
    hsbc = ladder(["You send", "Bank fee", "Fee in yuan", "Spread", "All-in cost"],
                  lambda r: [usd(r["amount"], False), f'<b>{usd(r["hsbc_fee_usd"])}</b>', cny(r["hsbc_fee_cny"]), BLANK, BLANK], ["F4", "R1"])
    emi = ladder(["You send", "Cost", "Wires", "First wire", "Years to finish"],
                 lambda r: [usd(r["amount"], False), f'<b>{usd(r["emigrant_total"])}</b>', str(r["emigrant_wires"]), usd(r["emigrant_first"], False), str(r["emigrant_years"])], ["L8", "R2", "F1"])
    quo = ladder(["You send", "Calendar years", "Cost"],
                 lambda r: [usd(r["amount"], False), f'<b>{r["quota_years"]}</b>', usd(r["quota_total"])], ["L4", "L3", "R2", "F1"])
    atm = ladder(["You send", "Calendar years", "Withdrawals", "Card fee", "Fee in yuan", "Network rate and ATM surcharge"],
                 lambda r: [usd(r["amount"], False), f'<b>{r["atm_years"]}</b>', str(r["atm_withdrawals"]), usd(r["atm_fee_usd"]), cny(r["atm_fee_cny"]), BLANK], ["L11", "F1", "R2"])
    cash = ladder(["You send", "Trips, no permit", "Trips, bank permit", "Spread", "Travel cost"],
                  lambda r: [usd(r["amount"], False), f'<b>{r["cash_trips_5k"]}</b>', str(r["cash_trips_10k"]), usd(r["cash_spread"]), BLANK], ["L12", "R2", "A7"])
    rec = ladder(["You send", "Days at USD 500 a day", "Fee"],
                 lambda r: [usd(r["amount"], False), f'<b>{r["recon_days"]}</b>', BLANK], ["L2"])
    wis = ladder(["You send", "Transfers from a bank app", "Fee"],
                 lambda r: [usd(r["amount"], False), f'<b>{r["wise_transfers"]}</b>', BLANK], ["F13", "R2"])
    wu = ladder(["You send", "Counter transactions", "Online transactions", "Fee"],
                lambda r: [usd(r["amount"], False), f'<b>{r["wu_counter"]}</b>', str(r["wu_online"]), BLANK], ["F12"])
    recv = table(["US institution", "Fee to receive a wire", "Source"],
                 [["Chase", "$15", src(["U1"])], ["Bank of America", "$15", src(["U2"])], ["Charles Schwab", "No fee", src(["U3"])], ["Fidelity", "No fee", src(["U4"])]])

    def det(i, title, note, tbl, open_=False):
        return f'<details id="{i}"{" open" if open_ else ""}><summary>{E(title)}</summary><p>{note}</p>{tbl}</details>'

    f1, f3 = INP["wire_fees"]["BOC"], INP["wire_fees"]["ABC"]
    body = f"""
<section class="note"><h2>How each number is made</h2>
<ul>
<li><b>Spread</b> = dollars sent × (selling rate − midpoint) ÷ midpoint, using the bank's own buy and sell rates. {src(["R2", "R4"])}</li>
<li><b>Bank fee</b> = 0.1% of the yuan paid, held between the tariff's minimum and maximum, plus the cable fee, turned into dollars at the selling rate. {src(["F1", "F3"])}</li>
<li><b>Cost</b> = spread + bank fee. It leaves out intermediary-bank deductions and your US bank's fee, which are shown separately.</li>
<li>Rates are a snapshot from {RETRIEVED}, about 17:40 to 17:51 Beijing time. The central parity that day was {INP["parity"]["value"]}; banks sold dollars below it. {src(["R1"])}</li>
</ul></section>
<h2>Banks compared</h2>
{banks}
<h2>Every $10,000 step to $400,000</h2>
<p>Open a method to see all 40 rows. The first column after the amount is the one that matters most for that method.</p>
{det("boc", "Bank of China wire — M1, M4, M5", f"Rate {BOC['sell_s']} per $100. Fee {f1['permille']}‰, min CNY {f1['min']}, max CNY {f1['max']}, plus CNY {f1['cable']} cable. The fee stops rising at {cny(D(f1['max']) * 1000)}, about {usd(D(f1['max']) * 1000 / SELL, False)}.", boc, True)}
{det("abc", "Agricultural Bank of China wire", f"Rate {RATE['ABC']['sell_s']} per $100. Fee 0.1%, min CNY {f3['min']}, max CNY {f3['max']}, plus CNY {f3['cable']} cable.", abc)}
{det("hsbc", "HSBC China wire, Premier or Advance — M7", f"Fee 0.1%, min CNY {fh['min']}, max CNY {fh['max']}, plus CNY {fh['cable']} cable, turned into dollars at the central parity because HSBC's own rate was not retrieved. Private Banking individuals pay nothing for the wire.", hsbc)}
{det("emigrant", "Emigrant property transfer — M3", f"Above {cny(EMI_CAP)} the transfer goes in three wires: half, then half of the rest after one year, then the balance after two. Each wire is priced at Bank of China.", emi)}
{det("quota", "USD 50,000 yearly quota — M6", "One wire of at most USD 50,000 per calendar year, priced at Bank of China. Open only to holders of a Foreign Permanent Resident ID Card and to domestic individuals.", quo)}
{det("atm", "ATM withdrawals abroad — M11", f"CNY 10,000 per card per day and CNY 100,000 per person per year. Bank of China charges CNY {INP['atm']['per_wd_fixed']} plus {INP['atm']['per_wd_pct']}%, max CNY {INP['atm']['per_wd_max']}, per withdrawal. Years and withdrawals are counted at the Bank of China selling rate.", atm)}
{det("cash", "Carrying dollar banknotes — M12", "USD 5,000 per trip with no permit, USD 10,000 with a bank permit. Bank of China sells banknotes at the same rate as wire dollars.", cash)}
{det("recon", "Passport-only conversion — M14", "USD 500 a day on passport alone.", rec)}
{det("wise", "Wise from yuan — M8", "At most CNY 300,000 per transfer from a China bank app.", wis)}
{det("wu", "Western Union through an agent bank — M10", "At most USD 10,000 per transaction at the counter, USD 5,000 online.", wu)}
<h2>Receiving the wire in the US</h2>
{recv}
"""
    write("costs.html", page("costs.html", "What it costs, $10,000 to $400,000",
                              f"Converting and wiring through the two banks priced in full costs between {pct(R400['abc_pct'])} and {pct(R10['boc_pct'])} of the amount. Other methods cost time rather than money: years of ATM withdrawals or dozens of trips.", body))


# ---------------------------------------------------------------- methods
def build_methods():
    rows = []
    for m in CON["methods"]:
        k, t = STATUS[m["status"]]
        rows.append([f'<a href="#{m["id"]}"><b>{m["id"]}</b> {E(m["name"])}</a>', badge(k, t), E(m["limit"]) or BLANK, E(m["cost"]) or BLANK, src(m["sources"])])
    summary = table(["Method", "Status", "Limit", "Published cost", "Source"], rows, "wide")
    secs = []
    for m in CON["methods"]:
        k, t = STATUS[m["status"]]
        kv = [["Who can use it", E(m["who"])], ["Limit", E(m["limit"]) or BLANK], ["Published cost", E(m["cost"]) or BLANK], ["Time", E(m["time"]) or BLANK]]
        if m["pros"]:
            kv.append(["For", "<ul>" + "".join(f"<li>{E(x)}</li>" for x in m["pros"]) + "</ul>"])
        kv.append(["Against", "<ul>" + "".join(f"<li>{E(x)}</li>" for x in m["cons"]) + "</ul>"])
        if m["steps"]:
            kv.append(["Steps", "<ol>" + "".join(f"<li>{E(x)}</li>" for x in m["steps"]) + "</ol>"])
        if m["ladder"]:
            kv.append(["All 40 amounts", f'<a href="costs.html#{m["ladder"]}">Open the cost ladder</a>'])
        tbl = table(["Field", "Detail", "Source"], [[f"<b>{a}</b>", b, src(m["sources"])] for a, b in kv], "kv")
        secs.append(f'<section id="{m["id"]}" class="m"><h3>{m["id"]} · {E(m["name"])} {badge(k, t)}</h3>{tbl}</section>')
    body = f"""
<h2>All routes at a glance</h2>
{summary}
<h2>Each route in detail</h2>
<p>Unlawful routes are listed so you can recognise them. They carry the penalty provision and no steps.</p>
{"".join(secs)}
"""
    n_ok = sum(1 for m in CON["methods"] if m["status"] != "unlawful")
    write("methods.html", page("methods.html", "Every route, with limits and steps",
                                f"{n_ok} lawful or conditional routes and {len(CON['methods']) - n_ok} unlawful ones. The bank wire of documented money is the only route that carries a large sum in one step.", body))


# ---------------------------------------------------------------- tax
def build_tax():
    u = INP["us"]
    us_rows = [
        ["<b>Exchange-rate gain</b>", f"A gain above ${u['gain_threshold_usd']} on a personal foreign-currency transaction is reported as capital gain. Held over a year it is long-term: 0%, 15% or 20%.", src(["A2", "A1", "A3"])],
        ["<b>Exchange-rate loss</b>", BLANK + " Whether a personal loss is deductible was not confirmed from a source read here.", src(["A3"])],
        ["<b>FBAR penalty</b>", f"Up to ${u['fbar_nonwillful']} for a non-willful violation and ${u['fbar_willful']} for a willful one, for penalties assessed on or after 17 January 2025.", src(["A4"])],
        ["<b>Form 8938</b>", f"Required above $50,000 of foreign financial assets at year end if you live in the US and file singly, $200,000 if you live abroad. Penalty ${u['f8938_penalty']}, plus up to ${u['f8938_more']} after IRS notice.", src(["A5"])],
        ["<b>Form 3520</b>", f"Required if gifts or bequests from a nonresident alien or foreign estate exceed ${u['f3520_threshold']} in the year. Penalty 5% a month, up to 25%.", src(["A6"])],
        ["<b>Carrying cash into the US</b>", "No limit, but more than $10,000 must be reported on FinCEN Form 105; unreported cash can be seized.", src(["A7"])],
        ["<b>Rate to use on the return</b>", "The spot rate when you receive the item. The IRS has no official rate and accepts any posted rate used consistently.", src(["R6"])],
    ]
    cn_rows = [
        ["<b>Converting and remitting</b>", "Not one of the nine taxable categories in the Individual Income Tax Law. The bank checks that tax on the underlying income was paid.", src(["T1", "L1"])],
        ["<b>Pay earned in China</b>", "3% to 45% on comprehensive income.", src(["T1"])],
        ["<b>Property-transfer income</b>", "Flat 20%.", src(["T1"])],
        ["<b>Interest, dividends</b>", "Flat 20% by law; tax on savings-deposit interest has been temporarily not levied since 9 October 2008.", src(["T1", "T2"])],
        ["<b>Inheritance</b>", "No inheritance tax is levied (Ministry of Finance, 2017). Housing passing to heirs carries no individual income tax.", src(["T3", "T4"])],
        ["<b>Housing given to close family</b>", "No individual income tax for spouse, parents, children, grandparents, grandchildren and siblings.", src(["T4"])],
        ["<b>Single payment above USD 50,000</b>", "Domestic payers file with the tax authority first for listed items. Overseas individuals follow the individual FX rules instead.", src(["L18"])],
    ]
    pen_rows = [
        ["<b>Moving foreign exchange abroad against the rules</b>", "Ordered to bring it back; fine up to 30% of the amount, or 30% up to the full amount in serious cases.", src(["L6"])],
        ["<b>Obtaining foreign exchange with false papers</b>", "Ordered to convert back; same fine scale; criminal liability where a crime.", src(["L6"])],
        ["<b>Private or disguised currency trading</b>", "Warning, confiscation of gains, same fine scale.", src(["L6"])],
        ["<b>Crime of illegal business operation</b>", "From CNY 5 million of turnover or CNY 100,000 of gains; especially serious from CNY 25 million or CNY 500,000.", src(["L14"])],
        ["<b>Splitting or borrowing quotas</b>", "Watch list for the current year and the next two; every purchase then needs documents.", src(["L7"])],
        ["<b>Exceeding the ATM cap</b>", "Overseas withdrawals suspended for that year and the next.", src(["L11"])],
        ["<b>Virtual currency</b>", "Exchange for legal tender is prohibited; contracts may be void and losses are yours.", src(["L15"])],
    ]
    g24, g25, g21 = (1 - SELL / IRS["2024"]) * 100, (1 - SELL / IRS["2025"]) * 100, (1 - SELL / IRS["2021"]) * 100
    body = f"""
<h2>By source of money</h2>
{scenario_table()}
<h2>Tax in China</h2>
{table(["Item", "Rule", "Source"], cn_rows)}
<h2>Tax and reporting in the US</h2>
{table(["Item", "Rule", "Source"], us_rows)}
<h2>Exchange-rate gain, $10,000 to $400,000</h2>
<p>Gain = dollars received × (1 − {SELL} ÷ the rate when the yuan was acquired). The IRS yearly average stands in for the acquisition rate; your own figure is the spot rate on the day you received each amount. Yuan from 2024 shows a gain of {pct(g24)}, from 2025 {pct(g25)}; yuan from 2021 shows a loss of {pct(-g21)}. Negative numbers are losses. No average exists yet for 2026.</p>
{gain_table(AMOUNTS)}
<p>Tax on the gain = gain × your capital-gains rate. The rate depends on your income and on how long you held the yuan, which this site does not know.</p>
<h2>Penalties in China for unlawful routes</h2>
{table(["Conduct", "Consequence", "Source"], pen_rows)}
<h2>All nine layers together</h2>
{layer_table()}
"""
    write("tax.html", page("tax.html", "Tax and penalties",
                            f"China taxes the income behind the money, not the transfer. The US taxes exchange-rate gain above $200: {usd(R400['gain_2024'], False)} of gain on $400,000 if the yuan dates from 2024.", body))


# ---------------------------------------------------------------- review, flagged, sources
def build_review():
    rows = [[f'<b>{c["id"]}</b> {E(c["claim"])}', badge(VERDICT[c["verdict"]], c["verdict"]), E(c["finding"]), f'<code>{E(c["repo_ref"])}</code>', src(c["sources"])] for c in CON["claims"]]
    n_bad = sum(1 for c in CON["claims"] if VERDICT[c["verdict"]] == "bad")
    n_ok = sum(1 for c in CON["claims"] if c["verdict"] == "confirmed")
    irr = [
        ["<b>I1</b> Emigrant transfers described as lump sum", "Three files say a lump sum is allowed; the rule stages amounts above CNY 200,000 over two years; a fourth file in the repository states the staging.", src(["L8"])],
        ["<b>I2</b> Dollar figures divide by a tax-reporting average", "Published fees were turned into dollars at 7.129, the IRS 2025 average. Banks sold dollars at about 6.685 on 10 Nov 2026, so every such dollar figure is about 6.6% low.", src(["R6", "R2"])],
        ["<b>I3</b> Spread treated as unknowable", "Sixty-five files leave the spread blank. Four banks publish both sides of the quote.", src(["R2", "R3", "R4", "R5"])],
        ["<b>I4</b> One bank priced", "Cost tables price HSBC China only. Two state banks publish lower fee caps.", src(["F1", "F3", "F4"])],
        ["<b>I5</b> Repealed notice still cited", "ladder/data/sources.json lists the 2021 virtual-currency notice, which the 2026 notice repeals.", src(["L15"])],
        ["<b>I6</b> Two root summaries", "EXECUTIVE_SUMMARY.md and EXECUTIVE-SUMMARY.md differ. Neither is edited by this session; this directory carries its own summary.", src(["L1"])],
        ["<b>I7</b> Quota described without the ID test", "Pages cite the USD 50,000 quota without saying it is tied to a PRC resident ID or a Foreign Permanent Resident ID Card.", src(["L3", "L4", "L5"])],
    ]
    body = f"""
<h2>Claims checked</h2>
<p>File and line numbers refer to commit <code>748b608</code> of <code>main</code>. “Confirmed” means the claim matches text this session read on {RETRIEVED}.</p>
{table(["Claim", "Verdict", "Finding", "Where in the repository", "Source"], rows, "wide")}
<h2>Irregularities</h2>
{table(["Irregularity", "Detail", "Source"], irr)}
<p>These files belong to other sessions and are not edited here. Each item is logged in <code>COORDINATION.md</code> for its owner.</p>
"""
    write("review.html", page("review.html", "Repository review",
                               f"{len(CON['claims'])} load-bearing claims were checked against sources read today: {n_ok} confirmed outright, {n_bad} stale, superseded or contradicted, and the rest confirmed with limits or not checked.", body))


def build_flagged():
    rows = [[f'<b>{f["id"]}</b> {E(f["item"])}', E(f["why"]), src(f["sources"])] for f in CON["flags"]]
    body = f"""
<h2>Open items</h2>
{table(["Item", "Why it is flagged", "Source"], rows)}
<p>Flagged items do not block publication. A blank cell anywhere on this site corresponds to one of these rows.</p>
"""
    write("flagged.html", page("flagged.html", "Flagged for Review",
                                f"{len(CON['flags'])} items could not be confirmed from an official source, are stale, or need a professional reading. Values stay blank until confirmed.", body))


def build_sources():
    acc = {"fetched": ("ok", "page read"), "excerpt": ("warn", "excerpt")}
    rows = []
    for s in SRC["sources"]:
        k, t = acc[s["access"]]
        q = f'<q lang="{"en" if s["group"] in ("fee-us", "law-us") or s["id"] in ("R2", "R6", "F4", "F13") else "zh"}">{E(s["quote"])}</q>'
        if s.get("en"):
            q += f'<br><small>{E(s["en"])}</small>'
        if s.get("note"):
            q += f'<br><small><b>Note:</b> {E(s["note"])}</small>'
        rows.append([f'<b id="{s["id"]}">{s["id"]}</b>', f'<a href="{E(s["url"], quote=True)}" rel="noopener">{E(s["publisher"])}<br>{E(s["title"])}</a>', badge(k, t), E(s["as_of"]), q])
    n_f = sum(1 for s in SRC["sources"] if s["access"] == "fetched")
    body = f"""
<section class="note"><p><b>Page read</b>: this session retrieved the page and read the text quoted. <b>Excerpt</b>: the text is what the search index returned for that official address; the page itself was not opened, so confirm it by following the link.</p></section>
{table(["ID", "Source", "How read", "Dated", "Text relied on"], rows, "wide srcs")}
"""
    write("sources.html", page("sources.html", "Sources",
                                f"{len(SOURCES)} official sources, all retrieved on {RETRIEVED}: {n_f} pages read in full and {len(SOURCES) - n_f} read as search excerpts.", body))


# ---------------------------------------------------------------- exports
def build_exports():
    with open(os.path.join(DATA, "ladder.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"note": "Generated by build.py from inputs.json. Dollar and yuan values are strings with two decimals.",
                   "rows": [{k: (str(v) if isinstance(v, D) else v) for k, v in r.items()} for r in LADDER]}, f, indent=1)
        f.write("\n")
    with open(os.path.join(DATA, "ladder.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        keys = list(LADDER[0].keys())
        w.writerow(keys)
        for r in LADDER:
            w.writerow([r[k] for k in keys])
    link = lambda i: f"[{i}]({SOURCES[i]['url']})"
    lines = [
        "# Executive summary — getting yuan out of China as dollars",
        "",
        f"Session `arena/6869721b-china2`. Sources retrieved {RETRIEVED}. Research, not legal or tax advice. Generated by `build.py`; do not edit by hand.",
        "",
        "## The answer",
        "",
        f"- **Cheapest lawful route found:** convert and wire through a bank against documents. At the rates and tariffs published that day, $400,000 costs **{usd(R400['abc_total'])} ({pct(R400['abc_pct'])})** at Agricultural Bank of China or **{usd(R400['boc_total'])} ({pct(R400['boc_pct'])})** at Bank of China; $10,000 costs {usd(R10['abc_total'])} or {usd(R10['boc_total'])}. {link('R4')} {link('F3')} {link('R2')} {link('F1')}",
        f"- **The gate is papers, not price.** A foreign-passport holder has no USD 50,000 yearly quota; the bank sells dollars against passport plus source-of-funds documents including tax vouchers. {link('L1')} {link('L3')}",
        f"- **The route follows the source of the money:** pay earned in China, pre-emigration savings (staged over two years above CNY 200,000), inheritance, housing sale, or unused exchanged yuan. {link('L1')} {link('L8')} {link('L9')} {link('L2')}",
        f"- **China taxes the income behind the money, not the transfer.** Pay 3%-45%, property transfer 20%, savings interest not levied, no inheritance tax. {link('T1')} {link('T2')} {link('T3')}",
        f"- **The largest tax exposure found is in the US.** Exchange-rate gain above $200 is capital gain. On $400,000 the gain is **{usd(R400['gain_2024'], False)}** if the yuan dates from 2024 and {usd(R400['gain_2025'], False)} if from 2025. {link('A2')} {link('R6')}",
        f"- **Reporting penalties are larger than any fee:** FBAR up to $16,536 non-willful and $165,353 willful; Form 8938 $10,000 plus up to $50,000; Form 3520 5% a month up to 25%. {link('A4')} {link('A5')} {link('A6')}",
        f"- **Shortcuts are unlawful:** borrowed quotas, underground banks, crypto and false papers carry fines up to 30%, or 30% to 100% in serious cases. {link('L6')} {link('L7')} {link('L15')}",
        "",
        "## Cost at six sizes",
        "",
        "| You send | Bank of China wire | Agricultural Bank wire | Emigrant transfer | ATM abroad | Cash at $5,000 a trip | Source |",
        "|---|---|---|---|---|---|---|",
    ]
    for a in KEY:
        r = BY_AMT[a]
        lines.append(f"| {usd(a, False)} | {usd(r['boc_total'])} ({pct(r['boc_pct'])}) | {usd(r['abc_total'])} ({pct(r['abc_pct'])}) | {usd(r['emigrant_total'])}, {r['emigrant_wires']} wire(s), {r['emigrant_years']} yr | {r['atm_years']} yr, {usd(r['atm_fee_usd'])} card fee | {r['cash_trips_5k']} trips | {link('R2')} {link('F1')} {link('R4')} {link('F3')} {link('L8')} {link('L11')} {link('L12')} |")
    lines += ["", "## Pages", "",
              "- [Summary](index.html) · [Costs](costs.html) · [Methods](methods.html) · [Tax and penalties](tax.html) · [Repo review](review.html) · [Flagged for Review](flagged.html) · [Sources](sources.html)",
              "", f"{len(CON['flags'])} items are flagged and left blank; see `flagged.html`.", ""]
    write("EXECUTIVE_SUMMARY.md", "\n".join(lines))


if __name__ == "__main__":
    build_index(); build_costs(); build_methods(); build_tax(); build_review(); build_flagged(); build_sources(); build_exports()
    print(f"built 7 pages, {len(LADDER)} ladder rows, {len(SOURCES)} sources, {len(CON['methods'])} methods, {len(CON['claims'])} claims, {len(CON['flags'])} flags")
