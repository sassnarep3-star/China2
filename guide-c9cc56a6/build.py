#!/usr/bin/env python3
"""Build the consolidated CNY -> USD repatriation guide (guide-c9cc56a6).

Every figure in the output is either
  (a) taken verbatim from a published official or commercial tariff and tagged with
      the source id that carries it, or
  (b) computed in this file from (a) by arithmetic that verify.py re-derives, or
  (c) left blank and marked with a flag id.

Nothing is inferred silently. Run:  python3 guide-c9cc56a6/build.py
"""
from __future__ import annotations

import html
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
DATA = ROOT / "data"

BUILD_DATE = "2026-11-10"
FX = 7.10                      # CNY per USD, conversion convenience only (F12)
TIERS = list(range(10_000, 400_001, 10_000))

# ---------------------------------------------------------------- inputs ----
SOURCES = {s["id"]: s for s in json.load(open(DATA / "sources.json", encoding="utf-8"))["sources"]}
ANALYSIS = json.load(open(DATA / "analysis.json", encoding="utf-8"))
LADDER_ROUTES = json.load(open(REPO / "ladder" / "data" / "routes.json", encoding="utf-8"))

# ladder source ids -> this guide's ids (1:1; see data/sources.json)
SRC_MAP = {
    "S01": "G01", "S02": "G04", "S03": "G06", "S04": "G05", "S05": "G07",
    "S06": "G08", "S07": "G09", "S08": "G27", "S09": "G28", "S13": "G20",
    "S15": "G29", "S16": "G21", "S17": "G03", "S18": "G30", "S20": "G31",
}

# ------------------------------------------------------------ cost model ----
SPREAD_BAND = {           # model assumptions, see F01 / A1-A4
    "wire": (0.30, 1.50),
    "cash": (0.80, 3.00),
    "card": (0.00, 3.00),
    "cnh":  (0.20, 1.00),
}
SPREAD_FLAG = {"wire": "A1", "cash": "A2", "card": "A3", "cnh": "A4"}


def tt_fee(amount_usd: float) -> float:
    """HSBC China tariff 2.2.4.1 + 2.2.4.2 (G08): 0.1% min CNY 100 max CNY 500, plus CNY 120 cable."""
    cny_commission = 0.001 * amount_usd * FX
    cny_commission = max(100.0, min(500.0, cny_commission))
    return (cny_commission + 120.0) / FX


def quota_fee(amount_usd: float) -> tuple[float, int]:
    """USD 50,000/calendar-year quota (G02): one wire per year tranche."""
    years = math.ceil(amount_usd / 50_000)
    return tt_fee(min(amount_usd, 50_000)) * years, years


# --------------------------------------------------------------- channels ---
def ch_from_route(r: dict, idx: int) -> dict:
    basis = [SRC_MAP[s] for s in r.get("basis", []) if s in SRC_MAP]
    return {
        "id": f"C{idx:02d}",
        "name": r["name"],
        "short": r["short"],
        "group": r["group"],
        "status": r["status"],
        "who": r["who"],
        "fee": r["fee"],
        "cap": r.get("cap"),
        "spread": r.get("spread"),
        "time": r["time"],
        "tax_note": r.get("tax_note", ""),
        "docs": r.get("docs", []),
        "steps": r.get("steps", []),
        "pros": r.get("pros", []),
        "cons": r.get("cons", []),
        "src": basis,
        "note": "",
    }


CHANNELS = [ch_from_route(r, i + 1) for i, r in enumerate(LADDER_ROUTES)]

SUPPLEMENT = [
    {
        "id": "C21",
        "name": "Bank FX purchase inside the USD 50,000/year facilitation quota",
        "short": "50,000 quota purchase",
        "group": "Lawful · primary",
        "status": "lawful",
        "who": "A PRC-identity individual or a foreign national holding the PRC Foreign Permanent Resident ID Card. For most foreign passport holders the documented-income route (C01) is the one that applies.",
        "fee": "quota",
        "spread": "wire",
        "time": "1-10 business days per tranche",
        "tax_note": "No PRC tax arises on converting money that has already borne PRC tax. The quota is an administrative limit, not a tax.",
        "docs": ["Passport plus PRC ID or Foreign Permanent Resident ID Card", "Bank card and account documents"],
        "steps": [
            "Confirm you hold a PRC ID or the Foreign Permanent Resident ID Card; without one this route is generally not open to you.",
            "At the bank, purchase USD with renminbi inside the remaining annual quota, quoting your ID number - no transaction documents are required inside the quota.",
            "Remit to your own US account; keep the exchange memo and the wire advice.",
            "If the balance exceeds USD 50,000, repeat in later calendar years, or use C01 for the excess in the same year.",
            "File FBAR and Form 8938 if the thresholds are met; claim PRC tax on Form 1116.",
        ],
        "pros": ["Least paperwork of any lawful route - identity only inside the quota.",
                 "Same published tariff as C01, so the fee is known in advance."],
        "cons": ["USD 50,000 per person per year: USD 400,000 needs eight calendar years.",
                 "Not available to most foreign passport holders without the permanent resident card.",
                 "Using other people's quotas to move one balance is prohibited splitting (see C18)."],
        "src": ["G02", "G04", "G08"],
        "note": "One wire per calendar-year tranche of up to USD 50,000.",
    },
    {
        "id": "C22",
        "name": "Wise (from-CNY) transfer to your own US account",
        "short": "Wise from CNY",
        "group": "Licensed provider · conditional",
        "status": "conditional",
        "who": "Non-mainland-Chinese individuals with PRC tax records for the last three years, sending their own funds to their own account. Provider terms, not a regulator's rule (G24).",
        "fee": "blank",
        "spread": None,
        "time": "1-3 business days after pay-in",
        "tax_note": "Same analysis as C01: the income was taxed when earned; conversion adds no PRC tax.",
        "docs": ["Passport", "PRC tax records (tax paid within the last three years)", "Own-name US account"],
        "steps": [
            "Create a Wise personal account and complete verification.",
            "Upload PRC tax records so the provider can set your sending limit.",
            "Set up a CNY to USD transfer to your own US account and read the in-app fee and rate before sending.",
            "Pay from your own Chinese bank app to the pay-in account the provider names, or by Alipay within its lower limit.",
            "Keep the receipt; file FBAR and Form 8938 if the thresholds are met.",
        ],
        "pros": ["Fee shown before you send, unlike a bank counter.",
                 "No calendar-year staging if the documented-income limit is large enough."],
        "cons": ["Provider eligibility and limits are commercial terms, not published law - flagged (G24).",
                 "Own accounts only; no third-party recipients.",
                 "No statically published fee, so no cost cell can be filled (F03)."],
        "src": ["G24"],
        "note": "Every cost cell is blank and flagged: the provider publishes no static fee schedule (F03).",
    },
    {
        "id": "C23",
        "name": "Western Union from China via a partner bank",
        "short": "Western Union",
        "group": "Licensed provider · conditional",
        "status": "conditional",
        "who": "Residents of China sending through a partner bank's app or counter, with cash pickup abroad. Provider terms (G25).",
        "fee": "blank",
        "spread": None,
        "time": "Minutes to a few business days",
        "tax_note": "The agent bank remains subject to PRC foreign exchange rules; the conversion basis still has to be lawful.",
        "docs": ["Passport", "Partner-bank account or card", "Recipient details"],
        "steps": [
            "Register a profile with a partner bank, or visit a branch with your passport.",
            "Quote the purpose and the recipient; pay from your account or card plus the quoted fee.",
            "Send the control number to the recipient only.",
            "The recipient collects cash with identity documents, then deposits it in the US.",
            "Keep the receipt; carrying more than USD 10,000 across the border requires FinCEN Form 105 (G20).",
        ],
        "pros": ["Fast and available in cash where a bank wire is not.",
                 "Useful for small amounts."],
        "cons": ["Fees and per-transfer limits are not published statically - blank and flagged (F03).",
                 "Cash pickup creates a physical-carry reporting problem above USD 10,000 (G20).",
                 "The agent bank's own foreign exchange controls still apply."],
        "src": ["G25", "G20"],
        "note": "Every cost cell is blank and flagged: no published static fee (F03).",
    },
    {
        "id": "C24",
        "name": "Individual foreign-trade settlement account (genuine trade)",
        "short": "Trade settlement account",
        "group": "Lawful · capital account",
        "status": "conditional",
        "who": "An individual carrying on genuine foreign trade through a settlement account. SAFE states such funds are exempt from the quota on presentation of valid documents (G02).",
        "fee": "blank",
        "spread": "wire",
        "time": "1-10 business days",
        "tax_note": "Trade income is business income; PRC tax is assessed on the income itself (5%-35%).",
        "docs": ["Business licence or registration", "Customs and contract documents", "Tax records"],
        "steps": [
            "Establish the trade account with the bank under the individual foreign trade rules.",
            "Assemble the customs declarations, contracts and invoices for the shipment.",
            "Convert and remit from the settlement account, which is quota-exempt on valid documents.",
            "Keep the file; report the business income and file the US reports.",
        ],
        "pros": ["Quota-exempt on valid documents (G02).",
                 "Designed for exactly this pattern - goods invoiced in foreign currency."],
        "cons": ["Only genuine trade; using it for a personal balance is a misrepresentation.",
                 "Whether an individual (rather than an entity) can hold one was not established - F10.",
                 "Bank fees for this account type were not retrieved - blank and flagged."],
        "src": ["G02"],
        "note": "Cost cells blank: no published tariff for this account type was retrieved (F10).",
    },
]
CHANNELS.extend(SUPPLEMENT)

NOTES = {
    "C01": "The tariff quotes the issuance fee as free for Private Banking individual customers and 0.1% (min CNY 100, max CNY 500) plus CNY 120 cable for Premier and Advance. The model applies the Premier/Advance formula to everyone, so if anything it overstates the fee rather than understates it.",
    "C02": "Published fee is zero for Private Banking and Premier customers and USD 20 per transaction for Advance, so the range's lower edge assumes the free tier. Premier requires a total relationship balance of CNY 500,000 or equivalent.",
    "C04": "The counter's own commission on a small-amount conversion is not in any tariff retrieved, so the published-fee column is blank and the route is priced on the FX margin only (F03).",
    "C05": "Port-side counters publish no tariff in any source retrieved; blank fee, FX margin only (F03).",
    "C06": "Cash carriage has no bank fee but a hard physical limit per trip, plus a US declaration duty above USD 10,000 (G20). The band below prices the bank's cash margin only.",
    "C11": "Issuer and ATM-operator fees are not published in any source retrieved - blank, flagged F03. The real constraint is the RMB 100,000/year and RMB 10,000/day caps (G06).",
    "C12": "Card-scheme settlement margin and issuer foreign-transaction fees are not published - blank, flagged F03.",
    "C14": "The onshore leg is priced from the tariff; the offshore conversion and its own fees are not published, so the total is a floor.",
    "C20": "Nothing is converted, so nothing is paid - and nothing leaves China. The balance stays exposed to future exchange-rate and policy risk instead.",
}
for _c in CHANNELS:
    if _c["id"] in NOTES and not _c.get("note"):
        _c["note"] = NOTES[_c["id"]]


# display order: primary lawful first, then capital account, then small/cash, then
# spending, then conditional, then unlawful, then do-nothing.
ORDER = ["C01", "C21", "C02", "C03", "C07", "C08", "C09", "C10", "C24",
         "C04", "C05", "C06", "C11", "C12", "C13", "C14", "C22", "C23",
         "C15", "C16", "C17", "C18", "C19", "C20"]
BY_ID = {c["id"]: c for c in CHANNELS}
CHANNELS = [BY_ID[i] for i in ORDER]


def staging(c: dict, amount: float) -> tuple[str, str]:
    """(text, source ids) for how many operations / years a route needs."""
    cid = c["id"]
    if cid == "C21":
        y = math.ceil(amount / 50_000)
        return (f"{y} wire{'s' if y > 1 else ''} over {y} calendar year{'s' if y > 1 else ''}", "G02")
    if cid == "C04":
        d = math.ceil(amount / 500)
        return (f"{d} counter day{'s' if d > 1 else ''} at USD 500/day", "G03")
    if cid == "C05":
        d = math.ceil(amount / 1_000)
        return (f"{d} departure{'s' if d > 1 else ''} at USD 1,000/day", "G03")
    if cid == "C06":
        t = math.ceil(amount / 5_000)
        return (f"{t} trip{'s' if t > 1 else ''} at USD 5,000/trip", "G29")
    if cid == "C11":
        years = math.ceil(amount * FX / 100_000)
        return (f"{years} calendar year{'s' if years > 1 else ''} (RMB 100,000/yr cap)", "G06")
    if cid in ("C07", "C08"):
        return ("Approval, then 3 staged remittances over 2 years", "G07")
    if cid == "C20":
        return ("no transfer - the balance stays in China", "G08")
    if cid == "C22":
        return ("provider-set limit, not published", "G24")
    if cid == "C23":
        return ("provider-set limit, not published", "G25")
    if cid == "C24":
        return ("per shipment, on valid trade documents", "G02")
    return ("1 wire", "G08")


def build_rows():
    rows = []
    for c in CHANNELS:
        st = c["status"]
        if st == "unlawful":
            for A in TIERS:
                rows.append({
                    "id": c["id"], "amount": A, "mode": "penalty",
                    "exposure_lo": 0.30 * A, "exposure_hi": 1.00 * A,
                    "src": "G05",
                })
            continue

        for A in TIERS:
            fee_kind = c["fee"]
            stage_text, stage_src = staging(c, A)
            if fee_kind == "wire":
                fee = tt_fee(A); fee_status = "published"
            elif fee_kind == "quota":
                fee, _ = quota_fee(A); fee_status = "published"
            elif fee_kind == "global":
                fee = None; fee_status = "range"
            elif fee_kind == "none":
                fee = 0.0; fee_status = "zero"
            else:
                fee = None; fee_status = "blank"

            band = SPREAD_BAND.get(c["spread"]) if c["spread"] else None
            if fee_status == "zero":
                rows.append({"id": c["id"], "amount": A, "mode": "cost", "fee_status": "zero",
                             "fee": 0.0, "lo": 0.0, "hi": 0.0, "pct_lo": 0.0, "pct_hi": 0.0,
                             "stage": stage_text, "stage_src": stage_src, "src": "G08", "flag": ""})
                continue
            if band is None or (fee is None and fee_status != "range"):
                rows.append({"id": c["id"], "amount": A, "mode": "blank",
                             "fee_status": fee_status, "stage": stage_text,
                             "stage_src": stage_src, "src": c["src"][0] if c["src"] else "G08"})
                continue

            if fee_status == "range":            # Global Transfer: free Premier/PB, USD 20 Advance
                lo = 0.0 + band[0] / 100 * A
                hi = 20.0 + band[1] / 100 * A
            else:
                lo = fee + band[0] / 100 * A
                hi = fee + band[1] / 100 * A
            rows.append({
                "id": c["id"], "amount": A, "mode": "cost", "fee_status": fee_status,
                "fee": fee, "lo": lo, "hi": hi,
                "pct_lo": lo / A * 100, "pct_hi": hi / A * 100,
                "stage": stage_text, "stage_src": stage_src,
                "src": "G08", "flag": SPREAD_FLAG.get(c["spread"], ""),
            })
    return rows


ROWS = build_rows()

# ------------------------------------------------ 988 exchange-gain table ---
CNY_ANNUAL = {2021: 6.452, 2022: 6.730, 2023: 7.075, 2024: 7.189, 2025: 7.129}
CONVERT_YEAR = 2025


def fx_gain(amount: float, acq_year: int) -> float:
    """USD gain/loss on `amount` of USD received now, for CNY acquired at the acq_year average."""
    cny = amount * CNY_ANNUAL[CONVERT_YEAR]
    basis = cny / CNY_ANNUAL[acq_year]
    return amount - basis

# ------------------------------------------------------------------ html ----
NAV = [
    ("index.html", "Overview"),
    ("methods.html", "Methods"),
    ("costs.html", "Costs"),
    ("taxes.html", "Tax &amp; penalties"),
    ("flagged.html", "Flagged"),
    ("sources.html", "Sources"),
    ("audit.html", "Repo audit"),
]


def e(x) -> str:
    return html.escape(str(x), quote=True)


def money(v, dp=0) -> str:
    if v is None:
        return ""
    if abs(v) >= 100 or dp == 0:
        return f"${v:,.0f}"
    return f"${v:,.2f}"


def rng(lo, hi, dp=0) -> str:
    return f"{money(lo, dp)} – {money(hi, dp)}"


def src_links(ids, short=False) -> str:
    out = []
    for i in ids:
        s = SOURCES.get(i)
        if not s:
            continue
        label = i if short else f"{i} · {s['authority'].split('(')[0].strip()}"
        cls = "chip warn" if s["verification_level"] == "unverified" else "chip"
        out.append(f'<a class="{cls}" href="{e(s["url"])}" rel="noopener" title="{e(s["title"])}">{e(label)}</a>')
    return " ".join(out)


def page(slug: str, title: str, lead: str, body: str) -> str:
    on = ' class="on"'
    nav = "".join(
        '<a href="%s"%s>%s</a>' % (h, on if h == slug else "", t) for h, t in NAV
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} · CNY → USD guide</title>
<meta name="description" content="{e(lead)[:180]}">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="top">
  <a class="brand" href="index.html">CNY → USD<span>repatriation guide</span></a>
  <nav>{nav}</nav>
</header>
<main>
<h1>{title}</h1>
<p class="lead">{lead}</p>
{body}
</main>
<footer>
  <p>Built {BUILD_DATE} by session <code>arena/c9cc56a6-china2</code>. Every figure is either taken from a
  published official or commercial source (linked) or computed from one by arithmetic this repo re-checks
  in <code>verify.py</code>. Anything that could not be confirmed is blank and listed on the
  <a href="flagged.html">Flagged for Review</a> page. This is research, not tax or legal advice.</p>
  <p><a href="sources.html">32 sources</a> · <a href="audit.html">repo audit</a> ·
  <a href="https://github.com/sassnarep3-star/China2">repository</a></p>
</footer>
</body>
</html>
"""


# ------------------------------------------------------------------ pages ---
def badge(status: str) -> str:
    m = {"lawful": ("ok", "lawful"), "conditional": ("warn", "conditional"),
         "unlawful": ("bad", "unlawful · rejected")}
    cls, label = m.get(status, ("warn", status))
    return f'<span class="badge {cls}">{label}</span>'


def page_index():
    ex = ANALYSIS["exec"]
    bullets = "".join(
        f'<article class="card"><h3>{e(b["t"])}</h3><p>{e(b["d"])}</p>'
        f'<p class="src">{src_links(b["src"])}</p></article>'
        for b in ex["bullets"]
    )

    rank_rows = ""
    for r in ANALYSIS["ranking"]:
        c = BY_ID[r["method"]]
        rank_rows += (
            f'<tr data-src="{" ".join(r["src"])}">'
            f'<td data-label="#">{r["rank"]}</td>'
            f'<td data-label="Route"><a href="methods.html#{c["id"]}">{e(c["short"])}</a>'
            f'<div class="muted">{e(r["method"])}</div></td>'
            f'<td data-label="Why">{e(r["why"])}</td>'
            f'<td data-label="Watch">{e(r["watch"])}</td>'
            f'<td data-label="Source">{src_links(r["src"], short=True)}</td></tr>'
        )

    # headline: published fee only, verified from G08, for the top route family
    tiers = [10_000, 25_000, 50_000, 100_000, 250_000, 400_000]
    head_cells = "".join(f"<th>${t//1000}k</th>" for t in tiers)
    r1 = "".join(f'<td data-label="${t//1000}k">{money(tt_fee(t), 2)}</td>' for t in tiers)
    r1pct = "".join(f'<td data-label="${t//1000}k %">{tt_fee(t)/t*100:.3f}%</td>' for t in tiers)
    rq = "".join(f'<td data-label="${t//1000}k">{money(quota_fee(t)[0], 2)}</td>' for t in tiers)

    body = f"""
<div class="hero">
  <p class="kicker">Executive summary</p>
  <h2>{e(ex['headline'])}</h2>
  <p class="big">{e(ex['bottom_line'])}</p>
</div>

<div class="stats">
  <div class="stat"><b>{money(tt_fee(10_000), 2)}</b><span>published bank cost on $10,000</span></div>
  <div class="stat"><b>{money(tt_fee(400_000), 2)}</b><span>published bank cost on $400,000</span></div>
  <div class="stat"><b>0%</b><span>PRC tax on a conversion as such</span></div>
  <div class="stat"><b>5</b><span>unlawful routes priced as fines, not fees</span></div>
</div>

<h2>Six things that decide the answer</h2>
<section class="grid">{bullets}</section>

<h2>The conversion cost, as published</h2>
<p>The only dollar figure a bank will commit to in advance is its published tariff. For the documented-income
wire (C01) that is 0.1% of the amount, minimum CNY 100, maximum CNY 500, plus a CNY 120 cable fee
({src_links(["G08"], short=True)}). The cap is why the percentage falls as the amount rises: the fee stops
growing at USD 70,423 of principal.</p>
<div class="scroll">
<table class="tight">
<thead><tr><th>Route</th>{head_cells}</tr></thead>
<tbody>
<tr data-src="G08"><td>Bank wire fee (C01, C03, C07-C10, C13)</td>{r1}</tr>
<tr data-src="G08"><td class="muted">…as % of the amount</td>{r1pct}</tr>
<tr data-src="G02 G08"><td>50,000-quota route (C21) — one wire a year</td>{rq}</tr>
</tbody></table>
</div>
<p class="note">These are published fees only. The FX margin the bank deals on is not published, so the
all-in estimate is higher — see <a href="costs.html">Costs</a>, where the margin is shown as a labelled
assumption (F01).</p>

<h2>If it were your money: the order of operations</h2>
<ol class="steps">
  <li><b>Get the tax record first.</b> Download your PRC individual income tax payment record for the years
  the balance was earned. It is both the thing that proves the money is after-tax and the document the bank
  will ask for {src_links(["G03"], short=True)}.</li>
  <li><b>Fix any unpaid PRC tax.</b> If the income was never taxed, that is income tax on the income — 3%-45%
  comprehensive or 20% flat depending on the category {src_links(["G09"], short=True)} — and it is owed
  whether or not you move the money.</li>
  <li><b>Convert with documents, not with the quota.</b> C01 has no annual ceiling in the published rules;
  the quota route C21 stops at USD 50,000 a year {src_links(["G01", "G02"], short=True)}.</li>
  <li><b>Get an executable all-in quote before signing.</b> Ask for the USD selling rate, the commission with
  its floor and cap, and the cable fee, in one number.</li>
  <li><b>File the US reports on time.</b> FBAR by 15 April (automatic to 15 October) above USD 10,000
  aggregate {src_links(["G10"], short=True)}; Form 8938 above the FATCA thresholds
  {src_links(["G11"], short=True)}; Form 1116 to credit the PRC tax {src_links(["G12"], short=True)}.</li>
  <li><b>Compute the section 988 difference, don't fear it.</b> At official IRS yearly averages the yuan has
  weakened since 2021, so a 2021-2023 acquisition shows an exchange <em>loss</em> on conversion
  {src_links(["G19", "G17"], short=True)}. See <a href="taxes.html">Tax &amp; penalties</a>.</li>
</ol>

<h2>Ranked: best first</h2>
<div class="scroll">
<table>
<thead><tr><th>#</th><th>Route</th><th>Why it wins</th><th>What to watch</th><th>Source</th></tr></thead>
<tbody>{rank_rows}</tbody></table>
</div>

<h2>What this page will not do</h2>
<p>It will not quote you a rate, because no bank publishes the customer rate it will deal on — that gap is
flag F01. It will not put a number on your PRC tax, because that depends on facts this repo does not have
(F08). And it will not tell you whether a section 988 gain above USD 200 is capital or ordinary, because the
statute does not say and the IRS publication that is usually quoted could not be verified verbatim here
(F04). Those three blanks are deliberate.</p>
"""
    return page("index.html", "Getting money out of China with the least tax penalty",
                "A verified, source-linked guide to converting CNY into USD: 24 routes, a USD 10,000-400,000 cost "
                "ladder, the actual tax and penalty exposure, and every gap marked as a gap.", body)


def page_methods():
    counts = {}
    for c in CHANNELS:
        counts[c["status"]] = counts.get(c["status"], 0) + 1

    summary = ""
    for c in CHANNELS:
        summary += (
            f'<tr data-src="{" ".join(c["src"])}">'
            f'<td data-label="ID"><a href="#{c["id"]}">{c["id"]}</a></td>'
            f'<td data-label="Route">{e(c["short"])}</td>'
            f'<td data-label="Status">{badge(c["status"])}</td>'
            f'<td data-label="Group">{e(c["group"])}</td>'
            f'<td data-label="Time">{e(c["time"])}</td>'
            f'<td data-label="Source">{src_links(c["src"][:3], short=True)}</td></tr>'
        )

    cards = ""
    for c in CHANNELS:
        pros = "".join(f"<li>{e(p)}</li>" for p in c["pros"])
        cons = "".join(f"<li>{e(p)}</li>" for p in c["cons"])
        steps = "".join(f"<li>{e(s)}</li>" for s in c["steps"])
        docs = "".join(f"<li>{e(d)}</li>" for d in c["docs"]) or "<li>—</li>"
        cards += f"""
<article class="card method" id="{c['id']}">
  <div class="methodhead">
    <h3><span class="mid">{c['id']}</span> {e(c['name'])}</h3>
    {badge(c['status'])}
  </div>
  <p class="who">{e(c['who'])}</p>
  <div class="cols">
    <div><h4>Advantages</h4><ul class="pros">{pros}</ul></div>
    <div><h4>Disadvantages</h4><ul class="cons">{cons}</ul></div>
  </div>
  <h4>Step by step</h4><ol class="steps">{steps}</ol>
  <div class="cols">
    <div><h4>Documents the bank will want</h4><ul>{docs}</ul></div>
    <div><h4>Timing and tax</h4>
      <p>Time: {e(c['time'])}</p>
      <p>{e(c['tax_note'])}</p>
      {f'<p class="flagline">⚑ {e(c["note"])}</p>' if c['note'] else ''}
    </div>
  </div>
  <p class="src">{src_links(c['src'])}</p>
</article>"""

    body = f"""
<div class="stats">
  <div class="stat"><b>{counts.get('lawful',0)}</b><span>lawful</span></div>
  <div class="stat"><b>{counts.get('conditional',0)}</b><span>conditional / provider terms</span></div>
  <div class="stat"><b>{counts.get('unlawful',0)}</b><span>unlawful — documented so you can see why</span></div>
  <div class="stat"><b>{len(CHANNELS)}</b><span>routes in total</span></div>
</div>
<p>The five unlawful routes are listed on purpose. A guide that silently omits them cannot explain why the
"fast" options cost 30%-100% of the amount in fines {src_links(["G05"], short=True)}.</p>
<div class="scroll">
<table>
<thead><tr><th>ID</th><th>Route</th><th>Status</th><th>Group</th><th>Time</th><th>Source</th></tr></thead>
<tbody>{summary}</tbody></table>
</div>
<h2>Every route, with pros, cons and steps</h2>
{cards}
"""
    return page("methods.html", "Every way to get CNY out of China",
                "Twenty-four routes: what each one is, who can use it, what it costs, the advantages and "
                "disadvantages, and the exact sequence of steps.", body)


def page_costs():
    # at-a-glance: lawful routes at five tiers
    glance_tiers = [10_000, 50_000, 100_000, 200_000, 400_000]
    rows = ""
    for c in CHANNELS:
        if c["status"] == "unlawful":
            continue
        cells = ""
        for t in glance_tiers:
            r = next(x for x in ROWS if x["id"] == c["id"] and x["amount"] == t)
            if r["mode"] == "cost":
                v = money(r["lo"], 0) if r["lo"] == r["hi"] else money(r["lo"], 0) + " – " + money(r["hi"], 0)
                if r["pct_lo"] > 0:
                    v += f'<span class="pc">{r["pct_lo"]:.2f}–{r["pct_hi"]:.2f}%</span>'
                cells += f"<td data-label=\"${t//1000}k\">{v}</td>"
            else:
                cells += f'<td data-label="${t//1000}k" class="blank" data-flag="F03">unverified</td>'
        rows += (f'<tr data-src="{" ".join(c["src"])}">'
                 f'<td data-label="Route"><a href="#{c["id"]}-l">{e(c["short"])}</a></td>{cells}</tr>')

    unlawful = ""
    for c in CHANNELS:
        if c["status"] != "unlawful":
            continue
        cells = ""
        for t in glance_tiers:
            cells += f'<td data-label="${t//1000}k" class="nb">{money(0.3*t)} – {money(t)}</td>'
        unlawful += (f'<tr data-src="G05"><td data-label="Route"><a href="#{c["id"]}-l">{e(c["short"])}</a></td>'
                     f'{cells}</tr>')

    ladders = ""
    for c in CHANNELS:
        ladders += f'<section class="ladder" id="{c["id"]}-l"><h3>{c["id"]} · {e(c["short"])} {badge(c["status"])}</h3>'
        ladders += f'<p class="muted">{e(c["name"])}</p>'
        if c["status"] == "unlawful":
            ladders += ('<div class="scroll"><table class="tight"><thead><tr><th>Amount</th>'
                        '<th>Statutory fine exposure 30%–100%</th><th>Basis</th><th>Source</th></tr></thead><tbody>')
            for A in TIERS:
                ladders += (f'<tr data-src="G05"><td>{money(A)}</td>'
                            f'<td class="nb">{money(0.3*A)} – {money(A)}</td>'
                            f'<td class="muted">30% of the amount; 30% to 100% if serious</td>'
                            f'<td>{src_links(["G05"], short=True)}</td></tr>')
            ladders += "</tbody></table></div></section>"
            continue

        ladders += ('<div class="scroll"><table class="tight"><thead><tr><th>Amount</th>'
                    '<th>Published bank fee</th><th>FX margin (assumed)</th><th>All-in estimate</th>'
                    '<th>% of amount</th><th>Staging</th><th>Source</th></tr></thead><tbody>')
        for A in TIERS:
            r = next(x for x in ROWS if x["id"] == c["id"] and x["amount"] == A)
            if r["mode"] != "cost":
                _bl = SPREAD_BAND.get(c["spread"]) if c["spread"] else None
                _bt = f"{_bl[0]:.2f}%–{_bl[1]:.2f}%" if _bl else "—"
                ladders += (f'<tr data-src="{r["src"]}"><td>{money(A)}</td>'
                            f'<td class="blank" data-flag="F03">—</td>'
                            f'<td class="est">{_bt}</td>'
                            f'<td class="blank" data-flag="F03">unverified</td><td class="blank" data-flag="F03">—</td>'
                            f'<td>{e(r["stage"])}</td><td>{src_links([r["src"]], short=True)}</td></tr>')
                continue
            if c["fee"] == "global":
                fee_cell = "0 – " + money(20)
            elif c["fee"] == "none":
                fee_cell = "$0"
            else:
                fee_cell = money(r["fee"], 2)
            _b = SPREAD_BAND.get(c["spread"]) if c["spread"] else None
            band_txt = f"{_b[0]:.2f}%–{_b[1]:.2f}%" if _b else "—"
            ladders += (f'<tr data-src="{r["src"]}" data-flag="{r.get("flag","")}"><td>{money(A)}</td>'
                        f'<td>{fee_cell}</td>'
                        f'<td class="est">{band_txt}</td>'
                        f'<td><b>{(money(r["lo"], 0) if abs(r["lo"] - r["hi"]) < 0.005 else money(r["lo"], 0) + " – " + money(r["hi"], 0))}</b></td>'
                        f'<td>{r["pct_lo"]:.2f}%–{r["pct_hi"]:.2f}%</td>'
                        f'<td>{e(r["stage"])}</td><td>{src_links([r["src"]], short=True)}</td></tr>')
        ladders += "</tbody></table></div></section>"

    assumptions = "".join(
        f'<li><b>{a["id"]}</b> — {e(a["text"])} <span class="tag">{a["status"]}</span></li>'
        for a in ANALYSIS["assumptions"]
    )

    body = f"""
<div class="callout">
  <p><b>Read this before the tables.</b> Two different things are shown in every row:</p>
  <ol>
    <li><b>Published bank fee</b> — an exact number from a published tariff ({src_links(["G08"], short=True)}).
    This is verifiable and it is small.</li>
    <li><b>FX margin</b> — the gap between the rate the bank deals on and the market. <b>No bank publishes
    this</b>, so it is shown as a labelled band (0.30%-1.50% for wires), not as a fact. See flag F01.</li>
  </ol>
  <p>The "all-in estimate" adds the two. Treat it as an order of magnitude with a known bottom edge, not a quote.</p>
</div>

<h2>At a glance: all-in estimate by amount</h2>
<div class="scroll">
<table class="glance">
<thead><tr><th>Route</th><th>$10k</th><th>$50k</th><th>$100k</th><th>$200k</th><th>$400k</th></tr></thead>
<tbody>{rows}</tbody></table>
</div>
<p class="note">Percentages under each figure are the cost as a share of the amount. Empty cells marked
"unverified" mean no published fee exists for that route — they are not zero.</p>

<h2>What the unlawful routes actually cost</h2>
<p>These are not fees. They are the statutory fine ranges for the violation each route commits
({src_links(["G05"], short=True)}): up to 30% of the amount, or 30% to 100% where serious.</p>
<div class="scroll">
<table class="glance">
<thead><tr><th>Route</th><th>$10k</th><th>$50k</th><th>$100k</th><th>$200k</th><th>$400k</th></tr></thead>
<tbody>{unlawful}</tbody></table>
</div>

<h2>The full ladder, $10,000 to $400,000 in $10,000 steps</h2>
<p>Each route has its own 40-row table. The amount is the USD you want to end up with in the US.</p>
{ladders}

<h2>Assumptions used in every table</h2>
<ul class="assumptions">{assumptions}</ul>
"""
    return page("costs.html", "What each route costs, $10,000 to $400,000",
                "Published bank fees are exact and linked. The FX margin is an assumption and is labelled as one "
                "on every row. Unlawful routes are priced as statutory fine ranges, not fees.", body)


def page_taxes():
    fw = "".join(
        f'<tr data-src="{" ".join(x["src"])}"><td data-label="Stage"><b>{e(x["stage"])}</b></td>'
        f'<td data-label="China">{e(x["prc"])}</td><td data-label="US">{e(x["us"])}</td>'
        f'<td data-label="Source">{src_links(x["src"], short=True)}</td></tr>'
        for x in ANALYSIS["tax"]["framework"]
    )
    prc = "".join(
        f'<tr data-src="{" ".join(r["src"])}"><td data-label="Category">{e(r["category"])}</td>'
        f'<td data-label="Rate">{e(r["rate"]) or "<span class=blank>blank</span>"}</td>'
        f'<td data-label="Note">{e(r["note"])}</td>'
        f'<td data-label="Source">{src_links(r["src"], short=True)}</td></tr>'
        for r in ANALYSIS["tax"]["prc_rates"]
    )
    us = "".join(
        f'<tr data-src="{" ".join(r["src"])}"><td data-label="Item">{e(r["item"])}</td>'
        f'<td data-label="Threshold">{e(r["threshold"])}</td>'
        f'<td data-label="Consequence">{e(r["consequence"]) or "<span class=blank>blank</span>"}</td>'
        f'<td data-label="Due">{e(r["due"])}</td>'
        f'<td data-label="Source">{src_links(r["src"], short=True)}</td></tr>'
        for r in ANALYSIS["tax"]["us_reporting"]
    )
    pen = "".join(
        f'<tr data-src="{" ".join(p["src"])}"><td data-label="Route">{e(p["route"])}</td>'
        f'<td data-label="Instrument">{e(p["instrument"])}</td>'
        f'<td data-label="Penalty">{e(p["penalty"]) or "<span class=blank>blank</span>"}</td>'
        f'<td data-label="Source">{src_links(p["src"], short=True)}</td></tr>'
        for p in ANALYSIS["penalties"]
    )

    year_cells = "".join(f"<th>{y}</th>" for y in sorted(CNY_ANNUAL))
    rate_cells = "".join(f"<td>{r:.3f}</td>" for _, r in sorted(CNY_ANNUAL.items()))
    gain_rows = ""
    for y in sorted(CNY_ANNUAL):
        g = fx_gain(10_000, y)
        cells = "".join(
            f'<td data-label="${a//1000}k">{"" if abs(fx_gain(a, y)) < 0.5 else ("+" if fx_gain(a, y) > 0 else "−") + money(abs(fx_gain(a, y)))}</td>'
            for a in (10_000, 100_000, 400_000)
        )
        cls = "pos" if g >= 0 else "neg"
        gain_rows += (f'<tr data-src="G19"><td data-label="Acquired">{y} <span class="muted">@ {CNY_ANNUAL[y]}</span></td>'
                      f'{cells}<td data-label="% of amount" class="{cls}">{fx_gain(10_000, y)/10_000*100:+.2f}%</td></tr>')

    threshold = 200 / (fx_gain(10_000, 2024) / 10_000)

    body = f"""
<div class="hero small">
  <p class="kicker">Where the "considerable tax" actually comes from</p>
  <h2>Four different things are being confused with each other</h2>
</div>

<h2>1. The conversion itself</h2>
<p><b>China:</b> nothing. The Individual Income Tax Law lists nine categories of taxable income; converting
your own renminbi is not one of them {src_links(["G09"], short=True)}.</p>
<p><b>United States:</b> only the exchange-rate difference since you acquired the currency — section 988.
For an individual's personal transaction, no gain is recognised at all if the exchange gain is USD 200 or
less {src_links(["G17"], short=True)}. The income itself was translated to dollars when it was earned
{src_links(["G18"], short=True)}, so it cannot be taxed a second time by moving it.</p>

<h2>2. The income behind the balance</h2>
<p>This is the large number, and it is not caused by the conversion. If the balance has already borne PRC
tax, there is nothing left to pay in China. If it was never taxed, the exposure is the PRC rate on the
income, plus the US rate on the same income net of the foreign tax credit.</p>
<div class="scroll">
<table>
<thead><tr><th>Category</th><th>Rate</th><th>Note</th><th>Source</th></tr></thead>
<tbody>{prc}</tbody></table>
</div>

<h2>3. The section 988 exchange difference, computed from official rates</h2>
<p>The IRS publishes yearly average rates for the yuan and states it has no official rate of its own, generally
accepting any posted rate used consistently {src_links(["G19"], short=True)}.</p>
<div class="scroll">
<table class="tight">
<thead><tr><th>CNY per USD</th>{year_cells}</tr></thead>
<tbody><tr data-src="G19"><td>CNY per USD (IRS yearly average)</td>{rate_cells}</tr></tbody>
</table>
</div>
<p>Now the arithmetic that matters. Take USD 10,000, USD 100,000 and USD 400,000 received by converting at
the {CONVERT_YEAR} average of {CNY_ANNUAL[CONVERT_YEAR]}, and ask what the same renminbi was worth in dollars
on the day it was acquired:</p>
<div class="scroll">
<table>
<thead><tr><th>CNY acquired in</th><th>$10k converted</th><th>$100k converted</th><th>$400k converted</th><th>As % of amount</th></tr></thead>
<tbody>{gain_rows}</tbody></table>
</div>
<p class="note">Negative means an exchange <em>loss</em> — renminbi acquired in 2021-2023 and converted at the
2025 average buys fewer dollars than its basis. Only a 2024 acquisition shows a gain, at
{fx_gain(10_000, 2024)/10_000*100:.2f}% of the amount, which crosses the USD 200 line at roughly
{money(threshold)} converted. All of this is arithmetic on the published IRS rates; your own dates are the
missing input.</p>
<div class="callout warn">
  <p><b>Flagged (F04):</b> the statute does not say whether a section 988 gain above USD 200 is capital or
  ordinary. {e(ANALYSIS['tax']['us988_note'])}</p>
</div>

<h2>4. Reporting failure — the only place the penalties really live</h2>
<div class="scroll">
<table>
<thead><tr><th>Item</th><th>Threshold</th><th>Consequence</th><th>Due</th><th>Source</th></tr></thead>
<tbody>{us}</tbody></table>
</div>
<p>Every figure in the consequence column is a maximum from the current penalty table
{src_links(["G15"], short=True)}. Where no official amount was retrieved, the cell is blank — Form 8938's
penalty is the example (F09).</p>

<h2>Every penalty in one table</h2>
<div class="scroll">
<table>
<thead><tr><th>Route</th><th>Instrument breached</th><th>Penalty</th><th>Source</th></tr></thead>
<tbody>{pen}</tbody></table>
</div>

<h2>The four stages, side by side</h2>
<div class="scroll">
<table>
<thead><tr><th>Stage</th><th>China</th><th>United States</th><th>Source</th></tr></thead>
<tbody>{fw}</tbody></table>
</div>

<h2>Relief, not penalty: the credit and the exclusion</h2>
<p>PRC tax already paid on income that the US also taxes can be claimed as a credit on Form 1116 — a
dollar-for-dollar reduction of US tax, not a deduction {src_links(["G12"], short=True)}. Separately, a US
citizen with a tax home abroad who meets the bona fide residence test or the 330-day physical presence test
may exclude foreign earned income {src_links(["G14"], short=True)}. The two interact: foreign tax on
excluded income cannot also be credited.</p>
"""
    return page("taxes.html", "The conversion penalty, broken down",
                "There is no conversion tax. There are four separate exposures — PRC income tax, the section 988 "
                "exchange difference, US reporting penalties and PRC foreign-exchange fines — and they are "
                "usually confused with each other.", body)


def page_flagged():
    cards = ""
    for f in ANALYSIS["flags"]:
        cards += f"""
<article class="card flag">
  <div class="methodhead"><h3><span class="mid">{e(f['id'])}</span> {e(f['topic'])}</h3>
  <span class="badge {"bad" if f["status"] in ("unverified","irregularity") else "warn"}">{e(f['status'])}</span></div>
  <p>{e(f['detail'])}</p>
  <p class="action"><b>To resolve:</b> {e(f['action'])}</p>
  <p class="src">{src_links(f['src'])}</p>
</article>"""
    body = f"""
<div class="callout">
  <p>Nothing on this page blocks publication; it exists so the gaps are visible instead of hidden. Each item
  says what could not be confirmed, what was done instead, and what would settle it.</p>
</div>
<h2>Open items</h2>
{cards}
<h2>Assumptions the tables rest on</h2>
<ul class="assumptions">{"".join(
  f'<li><b>{a["id"]}</b> — {e(a["text"])} <span class="tag">{a["status"]}</span></li>'
  for a in ANALYSIS["assumptions"])}</ul>
<h2>Sources that are explicitly not verified</h2>
<p>The following are linked for review but were never used to support a filled cell:</p>
<ul class="assumptions">{"".join(
  f'<li><b>{s["id"]}</b> — {e(s["title"])} · <span class="tag warn">{s["verification_level"]}</span> '
  f'<a href="{e(s["url"])}">open</a></li>'
  for s in SOURCES.values() if s["verification_level"] == "unverified")}</ul>
"""
    return page("flagged.html", "Flagged for Review",
                "Every value that could not be confirmed from an official source, every inconsistency found in "
                "the repository, and the assumptions the cost tables rest on.", body)


def page_sources():
    order = {"fetched-this-session": 0, "inherited": 1, "unverified": 2}
    rows = ""
    for s in sorted(SOURCES.values(), key=lambda x: (order[x["verification_level"]], x["id"])):
        cls = {"fetched-this-session": "ok", "inherited": "warn", "unverified": "bad"}[s["verification_level"]]
        rows += (f'<tr data-src="{s["id"]}">'
                 f'<td data-label="ID"><b>{s["id"]}</b></td>'
                 f'<td data-label="Authority">{e(s["authority"])}</td>'
                 f'<td data-label="Document"><a href="{e(s["url"])}" rel="noopener">{e(s["title"])}</a>'
                 f'<div class="muted">{e(s["locator"])}</div></td>'
                 f'<td data-label="Jurisdiction">{e(s["jur"])}</td>'
                 f'<td data-label="Verification"><span class="badge {cls}">{e(s["verification_level"])}</span></td></tr>')
    counts = {}
    for s in SOURCES.values():
        counts[s["verification_level"]] = counts.get(s["verification_level"], 0) + 1
    body = f"""
<div class="stats">
  <div class="stat"><b>{counts.get('fetched-this-session',0)}</b><span>fetched and read this session</span></div>
  <div class="stat"><b>{counts.get('inherited',0)}</b><span>verified by an earlier session</span></div>
  <div class="stat"><b>{counts.get('unverified',0)}</b><span>unverified — never used for a value</span></div>
  <div class="stat"><b>{len(SOURCES)}</b><span>sources in total</span></div>
</div>
<p>"Fetched this session" means the page or PDF body was retrieved and the quoted passage read on
{BUILD_DATE}. "Inherited" means an earlier repo session verified it and the URL is official, but this session
did not re-open it. "Unverified" means no official body was obtained: those sources are linked so you can
check them, and no number on this site depends on them.</p>
<div class="scroll">
<table>
<thead><tr><th>ID</th><th>Authority</th><th>Document</th><th>Jurisdiction</th><th>Verification</th></tr></thead>
<tbody>{rows}</tbody></table>
</div>
<h2>Quotations relied on</h2>
{"".join(
  f'<blockquote><p>{e(s["quote"])}</p><cite>{s["id"]} · <a href="{e(s["url"])}">{e(s["locator"])}</a> · used for: {e(s["used_for"])}</cite></blockquote>'
  for s in SOURCES.values() if s["verification_level"] == "fetched-this-session")}
"""
    return page("sources.html", "Sources and verification levels",
                "Thirty-two official and commercial sources, each tagged with how it was verified and what it "
                "was used for.", body)


def page_audit():
    rows = ""
    for a in ANALYSIS["audit"]:
        rows += (f'<tr data-src="{" ".join(a["src"])}"><td data-label="ID">{a["id"]}</td>'
                 f'<td data-label="Target"><code>{e(a["target"])}</code></td>'
                 f'<td data-label="Finding">{e(a["finding"])}</td>'
                 f'<td data-label="Verdict">{a["verdict"]}</td>'
                 f'<td data-label="Source">{src_links(a["src"], short=True)}</td></tr>')
    checks = "".join(f"<li>{e(c)}</li>" for c in ANALYSIS["verify_checks"])
    audit_notes = "".join(f"<li><b>{e(n['id'])}</b> — {e(n['text'])}</li>" for n in ANALYSIS.get("audit_notes", []))
    body = f"""
<div class="callout">
  <p>The repository already holds five overlapping dashboards. This session's scope was
  <code>guide-c9cc56a6/**</code>, so nothing outside it was edited. The audit below records what was checked,
  what was found, and what was deliberately left alone.</p>
</div>
<h2>Line-by-line audit</h2>
<div class="scroll">
<table>
<thead><tr><th>ID</th><th>Target</th><th>Finding</th><th>Verdict</th><th>Source</th></tr></thead>
<tbody>{rows}</tbody></table>
</div>
<h2>Checked but outside the table</h2>
<ul class="assumptions">{audit_notes}</ul>
<h2>What <code>verify.py</code> enforces on every build</h2>
<ol class="steps">{checks}</ol>
<h2>Arithmetic spot-checks against the published tariff</h2>
<div class="scroll">
<table class="tight">
<thead><tr><th>Amount</th><th>Computed fee</th><th>Hand check</th><th>Result</th></tr></thead>
<tbody>
<tr data-src="G08"><td>$10,000</td><td>{money(tt_fee(10_000),2)}</td><td>0.1% = CNY 71 &lt; floor CNY 100; 100 + 120 cable = CNY 220 ÷ 7.10</td><td>match</td></tr>
<tr data-src="G08"><td>$50,000</td><td>{money(tt_fee(50_000),2)}</td><td>0.1% = CNY 355; 355 + 120 = CNY 475 ÷ 7.10</td><td>match</td></tr>
<tr data-src="G08"><td>$100,000</td><td>{money(tt_fee(100_000),2)}</td><td>0.1% = CNY 710 &gt; cap CNY 500; 500 + 120 = CNY 620 ÷ 7.10</td><td>match</td></tr>
<tr data-src="G08"><td>$400,000</td><td>{money(tt_fee(400_000),2)}</td><td>cap applies again: CNY 620 ÷ 7.10</td><td>match</td></tr>
</tbody></table>
</div>
<p class="note">The same four amounts reproduce the fee column in <code>ladder/data/costs.csv</code>
(30.99 / 66.90 / 87.32 / 87.32), so the two independent models agree on the published-fee component. They
agree on the Global Transfer fee as well, both resting on the 31 October 2026 tariff after commit 8a2f69d — see F02.</p>
"""
    return page("audit.html", "Repository audit",
                "What was re-verified line by line, which pre-existing artefacts agree with the official sources, "
                "and which ones carry a stale input.", body)


# ------------------------------------------------------------------ write ---
def main():
    (ROOT / "assets").mkdir(exist_ok=True)
    (ROOT / "assets" / "style.css").write_text(CSS, encoding="utf-8")
    pages = {
        "index.html": page_index(),
        "methods.html": page_methods(),
        "costs.html": page_costs(),
        "taxes.html": page_taxes(),
        "flagged.html": page_flagged(),
        "sources.html": page_sources(),
        "audit.html": page_audit(),
    }
    for name, html_text in pages.items():
        (ROOT / name).write_text(html_text, encoding="utf-8")

    json.dump({"built": BUILD_DATE, "fx": FX, "tiers": TIERS, "rows": ROWS},
              open(DATA / "costs.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"wrote {len(pages)} pages, {len(ROWS)} cost rows, {len(CHANNELS)} channels")


CSS = """:root{
  --bg:#f7f8fa; --panel:#fff; --ink:#14181f; --muted:#5d6b7a; --line:#e2e7ed;
  --accent:#0b6b53; --accent2:#e8f3ef; --bad:#a4232b; --warn:#8a5a00; --nb:#fdecec;
  --shadow:0 1px 2px rgba(16,24,40,.06),0 1px 3px rgba(16,24,40,.05);
}
@media (prefers-color-scheme:dark){:root{
  --bg:#0f1318; --panel:#161c23; --ink:#e8edf3; --muted:#9aa8b6; --line:#25303b;
  --accent:#5fd0ac; --accent2:#12241f; --bad:#ff8b93; --warn:#f0b95a; --nb:#2a1618;
  --shadow:0 1px 2px rgba(0,0,0,.4);
}}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);
  font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
header.top{position:sticky;top:0;z-index:20;display:flex;flex-wrap:wrap;gap:.75rem 1.25rem;
  align-items:center;justify-content:space-between;padding:.7rem 1.1rem;background:var(--panel);
  border-bottom:1px solid var(--line)}
.brand{font-weight:700;font-size:1.02rem;color:var(--ink);display:flex;gap:.5rem;align-items:baseline}
.brand span{font-weight:400;color:var(--muted);font-size:.78rem;letter-spacing:.02em}
header nav{display:flex;gap:.15rem;flex-wrap:wrap}
header nav a{padding:.3rem .6rem;border-radius:8px;color:var(--muted);font-size:.9rem}
header nav a:hover{background:var(--accent2);color:var(--accent);text-decoration:none}
header nav a.on{background:var(--accent2);color:var(--accent);font-weight:600}
main{max-width:1080px;margin:0 auto;padding:1.6rem 1.1rem 3rem}
h1{font-size:clamp(1.5rem,3.4vw,2.15rem);line-height:1.2;margin:.2rem 0 .5rem;letter-spacing:-.015em}
h2{font-size:clamp(1.15rem,2.2vw,1.4rem);margin:2.2rem 0 .7rem;letter-spacing:-.01em}
h3{font-size:1.02rem;margin:0 0 .45rem}
h4{margin:1rem 0 .35rem;font-size:.82rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
p{margin:.55rem 0}
.lead{color:var(--muted);font-size:1.02rem;max-width:70ch}
.hero{background:var(--panel);border:1px solid var(--line);border-left:4px solid var(--accent);
  border-radius:12px;padding:1.1rem 1.2rem;box-shadow:var(--shadow);margin:1.2rem 0 1.4rem}
.hero h2{margin:.15rem 0 .5rem;font-size:clamp(1.2rem,2.6vw,1.55rem)}
.hero .big{margin:0;color:var(--ink)}
.hero.small{padding:.9rem 1.1rem}
.kicker{margin:0;text-transform:uppercase;letter-spacing:.09em;font-size:.72rem;color:var(--accent);font-weight:700}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:.7rem;margin:1.2rem 0}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:.8rem .9rem;box-shadow:var(--shadow)}
.stat b{display:block;font-size:1.35rem;letter-spacing:-.02em}
.stat span{font-size:.78rem;color:var(--muted);line-height:1.35;display:block}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:.85rem}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:1rem 1.1rem;
  box-shadow:var(--shadow);margin:.85rem 0}
.card h3{font-size:1rem}
.card p{margin:.35rem 0}
.methodhead{display:flex;gap:.6rem;align-items:flex-start;justify-content:space-between;flex-wrap:wrap}
.mid{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.78rem;color:var(--muted);
  background:var(--accent2);padding:.1rem .35rem;border-radius:5px}
.who{color:var(--muted);font-size:.93rem}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:1rem}
@media(max-width:720px){.cols{grid-template-columns:1fr}}
ul,ol{margin:.3rem 0 .3rem 1.15rem;padding:0}
li{margin:.2rem 0}
.pros li::marker{color:var(--accent)}
.cons li::marker{color:var(--bad)}
.steps li{margin:.35rem 0}
.badge{display:inline-block;font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;
  padding:.16rem .45rem;border-radius:99px;border:1px solid transparent;white-space:nowrap}
.badge.ok{background:var(--accent2);color:var(--accent);border-color:var(--accent)}
.badge.warn{background:#fff6e5;color:var(--warn);border-color:#e9c46a}
.badge.bad{background:var(--nb);color:var(--bad);border-color:var(--bad)}
@media (prefers-color-scheme:dark){.badge.warn{background:#2b2213;border-color:#6b5522}}
.chip{display:inline-block;font-size:.7rem;padding:.1rem .38rem;border:1px solid var(--line);
  border-radius:6px;color:var(--muted);margin:.1rem .15rem .1rem 0;background:var(--bg)}
.chip.warn{border-color:#e9c46a;color:var(--warn)}
.src{margin-top:.7rem;padding-top:.6rem;border-top:1px dashed var(--line)}
.scroll{overflow-x:auto;overscroll-behavior-x:contain;-webkit-overflow-scrolling:touch;border:1px solid var(--line);border-radius:12px;
  background:var(--panel);box-shadow:var(--shadow);margin:1rem 0}
table{border-collapse:collapse;width:100%;font-size:.9rem}
.scroll>table{min-width:520px}
th,td{text-align:left;padding:.55rem .7rem;border-bottom:1px solid var(--line);vertical-align:top}
th{background:var(--bg);font-size:.72rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);
  position:sticky;top:0;white-space:nowrap}
tbody tr:last-child td{border-bottom:0}
tbody tr:hover{background:var(--accent2)}
table.tight{font-size:.84rem;min-width:640px}
table.tight th,table.tight td{padding:.35rem .55rem;white-space:nowrap}
table.glance{font-size:.86rem;min-width:600px}
table.glance td:first-child{min-width:190px}
td.blank,span.blank{color:var(--muted);font-style:italic}
td.est{color:var(--warn)}
td.nb{color:var(--bad);font-variant-numeric:tabular-nums}
.pos{color:var(--accent)}
.neg{color:var(--bad)}
.pc{display:block;font-size:.72rem;color:var(--muted)}
.muted{color:var(--muted);font-size:.82rem}
.note{color:var(--muted);font-size:.88rem}
.callout{background:var(--panel);border:1px solid var(--line);border-left:4px solid var(--accent);
  border-radius:10px;padding:.85rem 1rem;margin:1.1rem 0}
.callout.warn{border-left-color:#e9c46a;background:#fffdf6}
@media (prefers-color-scheme:dark){.callout.warn{background:#221d12}}
.callout p:first-child{margin-top:0}
.ladder{margin:1.6rem 0}
.ladder h3{font-size:.98rem;display:flex;gap:.5rem;align-items:center;flex-wrap:wrap}
.assumptions li{font-size:.9rem}
.tag{font-size:.68rem;text-transform:uppercase;letter-spacing:.05em;border:1px solid var(--line);
  border-radius:99px;padding:.05rem .4rem;color:var(--muted)}
.tag.warn{color:var(--warn);border-color:#e9c46a}
.flagline{color:var(--warn);font-size:.86rem}
.action{font-size:.9rem;color:var(--muted)}
blockquote{margin:.8rem 0;padding:.7rem .9rem;background:var(--panel);border-left:3px solid var(--line);border-radius:8px}
blockquote p{margin:0 0 .4rem;font-size:.92rem}
blockquote cite{font-size:.78rem;color:var(--muted);font-style:normal}
code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.86em;background:var(--accent2);
  padding:.05rem .28rem;border-radius:4px}
footer{max-width:1080px;margin:0 auto;padding:1.4rem 1.1rem 3rem;color:var(--muted);font-size:.82rem;
  border-top:1px solid var(--line)}
@media(max-width:700px){
  body{font-size:15px}
  main{padding:1.1rem .75rem 2.5rem}
  th,td{padding:.45rem .5rem}
  header.top{padding:.55rem .75rem}
  .brand span{display:none}
  .table-glance,table.glance{font-size:.8rem}
}
"""

if __name__ == "__main__":
    main()
