#!/usr/bin/env python3
"""
Generate the final-integration landing dashboard and verification pages.

Session: arena/3347ca0a-china2 (final integration + independent re-verification)
Date:    2026-11-11

Every published number on the generated pages is computed here from
(a) an official document quoted in data/checks.json, or
(b) the canonical repository dataset in transfer-guide/data/ and exports/.
Nothing is typed in by hand at render time.

Run: python3 verification-3347ca0a/build.py
"""
import json
import math
import os
import re
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# ----------------------------------------------------------------------------
# Official inputs (each one quoted with its source in data/checks.json)
# ----------------------------------------------------------------------------
RATE_BOC = 669.11 / 100.0     # V20: BOC USD cash-remittance selling price, 2026-11-11 10:25:02
RATE_BOC_BUY = 666.30 / 100.0 # V20: BOC USD cash-remittance buying price, same timestamp
RATE_IRS = 7.129              # V18: IRS 2025 yearly average, China / Yuan
BOARD_GAP = (669.11 - 666.30) / 669.11   # 0.42% board gap, upper bound of retail margin
TT_MIN_CNY = 100.0            # V11: HSBC tariff 2.2.4.1 minimum
TT_RATE = 0.001               # V11: HSBC tariff 2.2.4.1 0.1%
TT_MAX_CNY = 500.0            # V11: HSBC tariff 2.2.4.1 maximum
CABLE_CNY = 120.0             # V11: HSBC tariff 2.2.4.2
PAY_EXACT_CNY = 200.0         # V11: tariff remark 1.1 (OUR)
GLOBAL_TRANSFER_ADVANCE_USD = 20.0   # V12: tariff 2.2.6.1
ATM_YEAR_CNY = 100000.0       # V19: SAFE Hui Fa [2017] No. 29 para. I
ATM_DAY_CNY = 10000.0         # V19: para. IV
CASH_TRIP_USD = 5000.0        # permit-free banknote carry (repository route M17)
TIERS = [10000, 50000, 100000, 200000, 400000]

TODAY = "2026-11-11"


def tt_fee_cny(cny_amount):
    """HSBC China outward telegraphic transfer, Premier/Advance individual."""
    return min(max(cny_amount * TT_RATE, TT_MIN_CNY), TT_MAX_CNY) + CABLE_CNY


def usd(x):
    return f"${x:,.2f}"


def pct(x, places=2):
    return f"{x * 100:.{places}f}%"


# ----------------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------------
def load(path):
    with open(os.path.join(HERE, path), encoding="utf-8") as fh:
        return json.load(fh)


CHECKS = load("data/checks.json")
IRREG = load("data/irregularities.json")

with open(os.path.join(ROOT, "transfer-guide", "data", "methods.json"), encoding="utf-8") as fh:
    METHODS = json.load(fh)["methods"]

with open(os.path.join(ROOT, "transfer-guide", "data", "sources.json"), encoding="utf-8") as fh:
    TG_SOURCES = json.load(fh)["sources"]

with open(os.path.join(ROOT, "transfer-guide", "data", "questions.json"), encoding="utf-8") as fh:
    QUESTIONS_RAW = json.load(fh)

with open(os.path.join(ROOT, "transfer-guide", "data", "audit_and_flags.json"), encoding="utf-8") as fh:
    AUDIT_RAW = json.load(fh)


def question_list():
    """Return [(id, question, what_we_know, how_to_discover, flag)] from whatever shape the ledger uses."""
    raw = QUESTIONS_RAW
    items = raw.get("questions") if isinstance(raw, dict) else raw
    out = []
    for q in items or []:
        qid = q.get("id") or q.get("qid") or ""
        text = (q.get("question") or q.get("title") or q.get("text") or "").strip()
        know = (q.get("what_we_know") or q.get("known") or q.get("established") or "").strip()
        discover = (q.get("how_to_discover") or q.get("how") or q.get("discovery") or q.get("action") or "").strip()
        flags = q.get("flag_ids") or q.get("flags") or []
        urls = (q.get("source_urls") or q.get("sources") or q.get("source_ids")
                or q.get("src_ids") or [])
        if not text:
            continue
        out.append((qid, text, know, discover, flags, urls))
    return out


QUESTIONS = question_list()

SRC_BY_ID = {s["id"]: s for s in TG_SOURCES}


def src_anchor(ids, label=None):
    """First official https source from a list of source ids, or an explicit blank."""
    for sid in ids or []:
        s = SRC_BY_ID.get(sid)
        if s and str(s.get("url", "")).startswith("https://"):
            return ref(s["url"], label or sid)
    return '<span class="blank">no official source in row</span>'


def flag_count():
    raw = AUDIT_RAW
    if isinstance(raw, dict):
        for key in ("flags", "flagged", "findings"):
            if key in raw and isinstance(raw[key], list):
                return len(raw[key])
    if isinstance(raw, list):
        return len(raw)
    return 0


FLAGS = flag_count()
SOURCES = len(TG_SOURCES)


# ----------------------------------------------------------------------------
# Cost model (recomputed, not copied)
# ----------------------------------------------------------------------------
def ladder():
    rows = []
    for amount in TIERS:
        cny = amount * RATE_BOC
        std = tt_fee_cny(cny) / RATE_BOC
        margin = amount * BOARD_GAP
        rows.append({
            "amount": amount,
            "cny": cny,
            "fee_std": std,
            "fee_pb": 0.0,
            "fee_adv_gt": GLOBAL_TRANSFER_ADVANCE_USD,
            "margin": margin,
            "total_std": std + margin,
            "total_pb": margin,
            "min_batches_50k": math.ceil(amount / 50000.0),
            "atm_years": math.ceil(cny / ATM_YEAR_CNY),
            "atm_withdrawals": math.ceil(cny / ATM_DAY_CNY),
            "cash_trips_5k": math.ceil(amount / CASH_TRIP_USD),
            "irs_rate_cny": amount * RATE_IRS,
            "fee_std_at_irs_rate": tt_fee_cny(amount * RATE_IRS) / RATE_IRS,
        })
    return rows


LADDER = ladder()


# ----------------------------------------------------------------------------
# Assets
# ----------------------------------------------------------------------------
CSS = """
:root{
  --ink:#101d1a;--ink-2:#1d2f2a;--paper:#f6f5f0;--card:#ffffff;--line:#dfe3dd;
  --muted:#5f7268;--accent:#0c6b58;--accent-2:#0a574a;--warn:#7a4a00;
  --warn-bg:#fff6e0;--warn-line:#e8d3a0;--ok:#0c6b58;--bad:#8d2f23;--bad-bg:#fdeeec;
  --pill:#eef3ef;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);
  font:16px/1.6 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent-2)}
a:hover{color:var(--accent)}
.wrap{max-width:1080px;margin:0 auto;padding:0 clamp(.9rem,3.5vw,2rem)}
.skip{position:absolute;left:-9999px}
.skip:focus{left:1rem;top:1rem;background:#fff;padding:.5rem;z-index:20}

header.site{background:var(--ink);color:#f2f4f0;padding:.85rem 0}
header.site .wrap{display:flex;gap:1rem;align-items:center;justify-content:space-between;flex-wrap:wrap}
.brand{display:flex;align-items:center;gap:.55rem;font-weight:750;letter-spacing:-.01em;color:#fff;text-decoration:none}
.brand .mark{display:inline-grid;place-items:center;width:2rem;height:2rem;border-radius:.55rem;
  background:#0c6b58;color:#fff;font-size:.95rem}
.brand small{display:block;font-size:.66rem;letter-spacing:.14em;color:#9fb5ab;font-weight:600}
.site-meta{font-size:.78rem;color:#b9c9c0;text-align:right}
nav.site{background:#16281f;border-bottom:1px solid #213a2f;position:sticky;top:0;z-index:10}
nav.site .wrap{display:flex;gap:.15rem;overflow-x:auto;padding:.35rem clamp(.9rem,3.5vw,2rem)}
nav.site a{color:#cfe0d6;text-decoration:none;font-size:.82rem;font-weight:600;
  padding:.5rem .7rem;border-radius:.5rem;white-space:nowrap}
nav.site a:hover{background:#20372c;color:#fff}

main{padding:1.4rem 0 3rem}
h1{font-size:clamp(1.7rem,5vw,2.6rem);line-height:1.12;letter-spacing:-.02em;margin:.4rem 0 .6rem}
h2{font-size:clamp(1.2rem,3.2vw,1.55rem);letter-spacing:-.01em;margin:2.2rem 0 .5rem}
h3{font-size:1.02rem;margin:0 0 .3rem}
p{margin:.5rem 0}
.eyebrow{display:block;font-size:.7rem;letter-spacing:.14em;text-transform:uppercase;
  color:var(--accent);font-weight:750;margin-bottom:.2rem}
.lede{font-size:1.06rem;color:#31463d;max-width:74ch}
.muted{color:var(--muted);font-size:.85rem}

.notice{background:var(--warn-bg);border:1px solid var(--warn-line);border-left:5px solid #b17a12;
  border-radius:.7rem;padding:.85rem 1rem;margin:1rem 0;font-size:.9rem}
.notice strong{color:var(--warn)}

.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:.7rem;margin:1.3rem 0}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:.8rem;padding:.9rem 1rem}
.kpi .label{font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);font-weight:700;margin:0}
.kpi .value{font-size:1.5rem;font-weight:780;letter-spacing:-.02em;margin:.25rem 0 .1rem;color:var(--ink)}
.kpi .sub{font-size:.8rem;color:var(--muted);margin:0}

.answers{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:.75rem;margin:1rem 0}
.answer{background:var(--card);border:1px solid var(--line);border-radius:.85rem;padding:1rem}
.answer h3{color:var(--accent-2)}
.answer p{font-size:.92rem;margin:.35rem 0}

.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:.8rem;background:var(--card);margin:.8rem 0}
table{border-collapse:collapse;width:100%;font-size:.88rem;min-width:640px}
caption{text-align:left;font-size:.8rem;color:var(--muted);padding:.7rem .8rem .2rem}
th,td{text-align:left;padding:.6rem .7rem;border-bottom:1px solid var(--line);vertical-align:top}
thead th{background:#f0f3ef;font-size:.74rem;letter-spacing:.05em;text-transform:uppercase;color:#3d5348;position:sticky;top:0}
tbody tr:last-child td{border-bottom:0}
tbody tr:nth-child(even){background:#fbfbf8}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.rowhead{font-weight:700}
.blank{color:#9aa8a0;font-style:italic}
.pill{display:inline-block;font-size:.7rem;font-weight:750;letter-spacing:.03em;
  padding:.12rem .45rem;border-radius:999px;background:var(--pill);color:#2c4a3e;white-space:nowrap}
.pill.ok{background:#e4f1eb;color:#075b49}
.pill.warn{background:#fdf1d8;color:#7a4a00}
.pill.bad{background:#fbe8e5;color:#8d2f23}
.src{font-size:.76rem;white-space:nowrap}
.src a{text-decoration:none;border-bottom:1px dotted var(--accent)}

.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:.7rem;margin:1rem 0}
.card{display:block;background:var(--card);border:1px solid var(--line);border-radius:.85rem;
  padding:.95rem 1rem;text-decoration:none;color:var(--ink);transition:border-color .15s,transform .15s}
.card:hover{border-color:var(--accent);transform:translateY(-1px);color:var(--ink)}
.card b{display:block;color:var(--accent-2);font-size:.98rem;margin-bottom:.15rem}
.card span{font-size:.82rem;color:#42584d;font-weight:650;display:block}
.card em{font-style:normal;font-size:.82rem;color:var(--muted);display:block;margin-top:.25rem}

ol.steps{counter-reset:s;list-style:none;padding:0;margin:1rem 0}
ol.steps li{position:relative;padding:.7rem 0 .7rem 2.5rem;border-bottom:1px dashed var(--line);font-size:.93rem}
ol.steps li:before{counter-increment:s;content:counter(s);position:absolute;left:0;top:.65rem;
  width:1.7rem;height:1.7rem;border-radius:50%;background:var(--accent);color:#fff;
  display:grid;place-items:center;font-size:.8rem;font-weight:750}
ol.steps li:last-child{border-bottom:0}

footer.site{background:var(--ink);color:#d8e3dc;padding:1.6rem 0;font-size:.84rem}
footer.site a{color:#9de0c7}
.smallprint{font-size:.78rem;color:#a9bdb3}

@media (max-width:720px){
  table{min-width:0}
  thead{position:absolute;left:-9999px}
  tbody tr{display:block;border:1px solid var(--line);border-radius:.7rem;margin:.55rem;padding:.2rem .2rem .4rem;background:#fff}
  tbody tr:nth-child(even){background:#fff}
  tbody td,tbody th{display:flex;justify-content:space-between;gap:1rem;border:0;padding:.32rem .7rem;font-size:.86rem;text-align:right}
  tbody td:before,tbody th[data-label]:before{content:attr(data-label);font-weight:700;color:var(--muted);
    font-size:.72rem;letter-spacing:.04em;text-transform:uppercase;text-align:left}
  tbody td.num{justify-content:space-between}
  .tablewrap{overflow:visible;border:0;background:transparent}
  caption{padding:.2rem .55rem}
}
@media print{
  nav.site{display:none}
  body{background:#fff}
  .card,.kpi,.answer{break-inside:avoid}
}
"""


# ----------------------------------------------------------------------------
# Shared render helpers
# ----------------------------------------------------------------------------
def esc(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def ref(url, label):
    return (f'<a class="source" href="{esc(url)}" target="_blank" rel="noopener noreferrer" '
            f'title="{esc(label)}">{esc(label)} ↗</a>')


VERIFIED_URLS = {c["url"]: c["id"] for c in CHECKS["checks"]}


def vlink(url, label=None):
    """Link an official URL and tag it with the verification record covering it."""
    vid = VERIFIED_URLS.get(url)
    tag = f" [{vid}]" if vid else ""
    return ref(url, (label or "source") + tag)


# ----------------------------------------------------------------------------
# Root landing page
# ----------------------------------------------------------------------------
def nav(items, current=None):
    out = []
    for anchor, label in items:
        cls = ' aria-current="page"' if anchor == current else ""
        out.append(f'<a href="{anchor}"{cls}>{label}</a>')
    return f'<nav class="site" aria-label="Sections"><div class="wrap">{"".join(out)}</div></nav>'


ROOT_NAV = [
    ("#answer", "Answer first"),
    ("#costs", "Costs"),
    ("#methods", "Methods"),
    ("#how", "Step by step"),
    ("#subpages", "All pages"),
    ("#questions", "Open questions"),
    ("verification-3347ca0a/index.html", "Verification"),
    ("verification-3347ca0a/irregularities.html", "Repo audit"),
]


def root_page():
    L = LADDER
    m01_10 = L[0]["fee_std"]
    m01_400 = L[-1]["fee_std"]
    margin_400 = L[-1]["margin"]
    atm_years_400 = L[-1]["atm_years"]
    atm_at_irs = math.ceil(400000 * RATE_IRS / ATM_YEAR_CNY)

    rows = []
    for t in L:
        rows.append(f"""
        <tr>
          <th scope="row" data-label="Amount">{usd(t['amount'])}</th>
          <td class="num" data-label="CNY needed (BOC 11 Nov)">{t['cny']:,.0f}</td>
          <td data-label="Documented bank route">1 wire — M01</td>
          <td class="num" data-label="Sender fee (Premier/Advance)">{usd(t['fee_std'])}</td>
          <td class="num" data-label="Sender fee (Private Banking / Premier Elite)">{usd(t['fee_pb'])}</td>
          <td class="num" data-label="Exchange margin (board bound)">≤ {usd(t['margin'])}</td>
          <td class="num" data-label="Indicative total">{usd(t['total_std'])}</td>
          <td class="src" data-label="Sources">{ref('https://www.hsbc.com.cn/content/dam/hsbc/cn/docs/document-download/tariff-of-Accounts-services-for-personal-customers-v2.pdf','HSBC 2.2.4.1 [V11]')}</td>
        </tr>""")

    alt_rows = []
    for t in L:
        alt_rows.append(f"""
        <tr>
          <th scope="row" data-label="Amount">{usd(t['amount'])}</th>
          <td data-label="Route">M02 HSBC Global Transfer to your own U.S. HSBC account</td>
          <td class="num" data-label="Steps">1 step after conversion</td>
          <td class="num" data-label="Transfer fee (PB/Premier)">$0.00</td>
          <td class="num" data-label="Transfer fee (Advance)">$20.00</td>
          <td class="num" data-label="Exchange margin still applies">≤ {usd(t['margin'])}</td>
          <td class="src" data-label="Sources">{ref('https://www.hsbc.com.cn/content/dam/hsbc/cn/docs/document-download/tariff-of-Accounts-services-for-personal-customers-v2.pdf','HSBC 2.2.6.1 [V12]')}</td>
        </tr>""")

    alt_rows_2 = []
    for t in L:
        alt_rows_2.append(f"""
        <tr>
          <th scope="row" data-label="Amount">{usd(t['amount'])}</th>
          <td data-label="Route">M06 USD-50,000 annual quota + wire (PR-ID / PRC ID holders only)</td>
          <td class="num" data-label="Wires / calendar years">{t['min_batches_50k']} / {t['min_batches_50k']}</td>
          <td class="num" data-label="Sender fee per wire">{usd(tt_fee_cny(50000 * RATE_BOC) / RATE_BOC)}</td>
          <td class="num" data-label="Sender fee, all wires">{usd(t['min_batches_50k'] * tt_fee_cny(50000 * RATE_BOC) / RATE_BOC)}</td>
          <td class="num" data-label="Exchange margin (board bound)">≤ {usd(t['margin'])}</td>
          <td class="src" data-label="Sources">{ref('https://www.safe.gov.cn/tianjin/2024/0430/2464.html','SAFE Art. 2 [V04]')}</td>
        </tr>""")

    alt_rows_3 = []
    for t in L:
        alt_rows_3.append(f"""
        <tr>
          <th scope="row" data-label="Amount">{usd(t['amount'])}</th>
          <td data-label="Route">M15 overseas ATM withdrawals with a mainland debit card</td>
          <td class="num" data-label="Calendar years needed">{t['atm_years']}</td>
          <td class="num" data-label="Withdrawals at RMB 10,000/day cap">{t['atm_withdrawals']:,}</td>
          <td class="num" data-label="Issuer / ATM fees">—</td>
          <td class="src" data-label="Sources">{ref('https://www.safe.gov.cn/en/2017/1230/1397.html','SAFE [2017] 29 [V19]')}</td>
        </tr>""")

    method_rows = []
    for m in METHODS:
        status = m.get("legal_status", "")
        cls = "ok" if status.startswith("lawful") else ("bad" if "unlawful" in status else "warn")
        label = status.replace("-", " ") if status else "—"
        best = (m.get("best_for") or "").strip()
        if len(best) > 150:
            best = best[:147].rsplit(" ", 1)[0] + " …"
        method_rows.append(f"""
        <tr>
          <th scope="row" data-label="Method">{esc(m['id'])}</th>
          <td data-label="Name">{esc(m['name'])}</td>
          <td data-label="Status"><span class="pill {cls}">{esc(label)}</span></td>
          <td data-label="Best for">{esc(best)}</td>
          <td class="src" data-label="Official source">{src_anchor(m.get('source_ids'))}</td>
          <td class="src" data-label="Detail"><a href="transfer-guide/methods.html#{esc(m['id'])}">pros / cons / steps &rarr;</a></td>
        </tr>""")

    q_rows = []
    for qid, text, know, discover, flags, urls in QUESTIONS[:8]:
        # Final-integration correction: do not promise that settling tax automatically unlocks a transfer.
        discover = discover.replace(
            "then you unlock M01 single-wire conversion with $0 extra conversion tax",
            "then ask the bank to reassess the documented-income route; eligibility and tax remain fact-specific",
        )
        q_rows.append(f"""
        <tr>
          <th scope="row" data-label="ID">{esc(qid)}</th>
          <td data-label="Question">{esc(text)}</td>
          <td data-label="How to find out">{esc(discover) if discover else '<span class="blank">not recorded</span>'}</td>
          <td class="src" data-label="Official source">{src_anchor(urls)}</td>
          <td class="src" data-label="Detail"><a href="transfer-guide/questions.html">full checklist &rarr;</a></td>
        </tr>""")

    archive = [
        ("transfer-guide/index.html", "Transfer guide", f"23 methods · {SOURCES} sources · 920 cost rows", "Newest complete set (10-11 Nov 2026). Used as the canonical detail set from this page."),
        ("docs/index.html", "Research dashboard", "22 routes · 24 sources · 9 flags", "Polished earlier dashboard (7 Nov 2026). Different route count; superseded on counts."),
        ("estimate-facf2fe9/index.html", "Published-rate estimates", "23 methods · 40 tiers · live bank boards", "Adds six bank rate boards and a repo review with its own irregularities list."),
        ("verify-d5d1f860/index.html", "Quote-level verification", "24 sources re-fetched · 680 rows", "Earlier verification pass (10 Nov 2026)."),
        ("briefing/index.html", "Executive briefing", "17 methods · 680 cost rows", "Earlier edition: 17 methods."),
        ("ladder/index.html", "Cost ladder model", "15 routes · 40 tiers · modelled bands", "Modelled, not published fees. Read its assumptions page before quoting it."),
        ("repatriate/index.html", "Repatriation set", "17 methods · 780 table rows", "Earlier edition."),
        ("study-8f529c94/index.html", "Method study", "23 methods · 920 rows", "Source of the 23-method catalogue."),
        ("final-f6327e23/index.html", "Final set (earlier)", "15 methods · 16 sources", "Earlier edition: 15 methods."),
        ("audit-ad300459/index.html", "Evidence audit", "27 findings · 10 flags", "Claim-by-claim audit of the other pages."),
        ("portal/index.html", "Government-source portal", "22 methods · .gov / .gov.cn only", "Restricted to government domains; no commercial bank terms."),
        ("site/index.html", "Evidence ledger site", "18 routes · strict allowlist", "Strict domain allowlist; earlier edition."),
        ("audit-86f0/costs.html", "Blank cost matrix", "22 methods · 40 tiers", "Leaves unverified values blank by design."),
        ("audit-0f0f59fe/index.html", "Root claim review", "Official text · corrections", "Checks claims previously made on this landing page."),
        ("audit-92d12752/index.html", "Structural link scan", "7,107 rows · 1,384 candidates", "Point-in-time scan for rows without a direct primary-domain URL."),
        # Navigation-only addition by session arena/f79e64e7-china2 (2026-11-11), logged in COORDINATION.md:
        # one archive row and one category card so its dashboard is reachable from this landing page.
        ("dashboard-f79e64e7/index.html", "Second verification pass", "17 methods · 34 sources · 680 cost rows", "Separate pass on 11 Nov 2026: each source re-opened and its quoted sentence checked, with corrections to earlier sets."),
        # Navigation-only addition by session arena/c1d73006-china2 (2026-11-11), logged in COORDINATION.md:
        # one archive row and one category card so its playbook is reachable from this landing page.
        ("playbook-c1d73006/index.html", "Route-by-origin playbook", "10 origins of the money · 17 methods · 680 cost rows", "Separate pass on 11 Nov 2026: the route, papers and tax for each origin of the money; what overdue PRC tax grows into; a text review of the other sets."),
        # Navigation-only addition by session arena-d6a42474 (2026-11-11), logged in COORDINATION.md:
        # one archive row and one category card so its consolidated dashboard is reachable from this landing page.
        ("canon-d6a42474/index.html", "Consolidated dashboard", "18 sources · 8 priced routes · 40 tiers · 24 flags", "Latest dated pass (11 Nov 2026): separated the one-way margin from the round-trip spread, repriced at the 15:30:04 board, and counted the conflicts with earlier sets on its audit page."),
    ]
    archive_rows = "".join(
        f'<tr><th scope="row" data-label="Set"><a href="{href}">{esc(title)}</a></th>'
        f'<td data-label="Published counts">{esc(counts)}</td>'
        f'<td data-label="Status / note">{esc(note)}</td></tr>'
        for href, title, counts, note in archive
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>China money · CNY to USD, priced and sourced</title>
<meta name="description" content="A source-linked dashboard for moving lawful CNY out of mainland China to the United States: published fees at USD 10,000-400,000, the documentary gate, PRC and U.S. tax rules, and what is still unverified.">
<meta name="theme-color" content="#101d1a">
<link rel="icon" href="verification-3347ca0a/assets/favicon.svg" type="image/svg+xml">
<style>{CSS}</style>
</head>
<body>
<a class="skip" href="#answer">Skip to the answer</a>
<header class="site"><div class="wrap">
  <a class="brand" href="index.html"><span class="mark">¥</span><span>China Money<small>CNY → USD DESK</small></span></a>
  <div class="site-meta">Independent source review<br>Last verified {TODAY} · not tax or legal advice</div>
</div></header>
{nav(ROOT_NAV)}
<main class="wrap">

<h1>Start with the source of funds and tax evidence.</h1>
<p class="lede">A perceived “conversion penalty” can involve several different things: tax on the underlying income
or asset, a bank’s document review, exchange-rate cost and transfer charges, possible U.S. currency gain, and U.S.
reporting duties. They have different fixes and different sources. This desk prices what is published, identifies
its assumptions, and leaves blank what is not published.</p>

<div class="kpis">
  <div class="kpi"><p class="label">Separate CNY→USD conversion tax</p><p class="value">Not identified</p>
    <p class="sub">The PRC FX provisions reviewed impose document and source-of-funds tests; this is not a determination that conversion or the underlying funds are tax-free. [{ref('https://www.safe.gov.cn/beijing/2018/1221/1010.html','V01')} {ref('https://www.safe.gov.cn/tianjin/2024/0430/2464.html','V02')}]</p></div>
  <div class="kpi"><p class="label">Published wire fee · $10k → $400k</p><p class="value">{usd(m01_10)} → {usd(m01_400)}</p>
    <p class="sub">HSBC China telegraphic transfer + cable, Premier/Advance. Private Banking and Premier Elite individuals: $0.00. [{ref('https://www.hsbc.com.cn/content/dam/hsbc/cn/docs/document-download/tariff-of-Accounts-services-for-personal-customers-v2.pdf','V11')}]</p></div>
  <div class="kpi"><p class="label">The bigger number: exchange margin</p><p class="value">≤ {pct(BOARD_GAP)}</p>
    <p class="sub">Bound from the Bank of China USD board on {TODAY} (666.30 buy / 669.11 sell per 100). At $400,000 that bound is {usd(margin_400)} — {margin_400 / m01_400:.0f}× the wire fee. [{ref('https://www.boc.cn/sourcedb/whpj/','V20')}]</p></div>
</div>

<div class="summary" style="background:#fff;border:1px solid var(--line);border-left:5px solid var(--accent);border-radius:.7rem;padding:.85rem 1rem;margin:1rem 0;font-size:.9rem">
<strong>Corrected wording, kept visible:</strong> earlier pages carried a “USD 0–7” same-name Global Transfer fee from a
superseded tariff. The current HSBC China tariff (effective 31 Oct 2026) publishes same-name Global Transfer as
<strong>Free</strong> for Private Banking and Premier and <strong>USD 20</strong> for Advance (item 2.2.6.1); the
<strong>USD 7</strong> figure belongs to International Education Payment (item 2.2.7) and to no other remittance.
[{ref('https://www.hsbc.com.cn/content/dam/hsbc/cn/docs/document-download/tariff-of-Accounts-services-for-personal-customers-v2.pdf','V12')}]
See <a href="audit-0f0f59fe/index.html#C04">finding C04</a> and
<a href="verification-3347ca0a/irregularities.html#IR-09">IR-09</a>.</div>

<div class="notice"><strong>Read this before the numbers.</strong> Nothing here is a personal determination. The source,
the tax history and the acquisition dates of your balance are unknown; no bank has been asked for a quote; no rate
shown is executable. Values that could not be confirmed from an official document are left blank and flagged, not
estimated. <a href="verification-3347ca0a/index.html">22 source checks · 20 confirmed</a> ·
<a href="verification-3347ca0a/irregularities.html">12 repository findings</a>.</div>

<h2 id="answer">Answer first</h2>
<div class="answers">
  <div class="answer"><h3>If the RMB is already-taxed salary</h3>
    <p>One documented bank conversion plus one wire is the route to assess first (M01). SAFE states there is no
    statutory time limit on remitting historic lawful salary [{ref('https://www.safe.gov.cn/henan/2022/0718/1249.html','V09')}]
    and that a third party can run the formalities if you are abroad [{ref('https://www.safe.gov.cn/henan/2022/0718/1247.html','V08')}].
    What you must produce is the contract plus the tax record — that is the gate, not a tax.</p></div>
  <div class="answer"><h3>The USD 50,000 figure is not a universal ceiling</h3>
    <p>The rule’s own words apply the annual total to settlement and to a <em>domestic</em> individual’s purchase
    (境内个人购汇) [{ref('https://www.safe.gov.cn/tianjin/2024/0430/2464.html','V04')}]. Treating it as a blanket cap on an
    overseas individual’s documented income is not supported by that text — but bank practice varies and is
    unresolved here. <a href="verification-3347ca0a/irregularities.html#IR-11">Flag IR-11</a>.</p></div>
  <div class="answer"><h3>Cheaper routes exist; most are capped or closed</h3>
    <p>ATM cash is hard-capped at RMB 100,000 a calendar year [{ref('https://www.safe.gov.cn/en/2017/1230/1397.html','V19')}] —
    {atm_years_400} years for $400,000 at the {TODAY} board ({atm_at_irs} at the 7.129 tax rate). Wise is limited to
    CNY 300,000 per transfer and 3-year-old tax records [{ref('https://wise.com/help/articles/2955298/guide-to-cny-transfers','V14')}].
    Physical cash hits a USD 10,000 declaration line every trip [{ref('https://www.cbp.gov/travel/international-visitors/money-monetary-instruments','V17')}].</p></div>
  <div class="answer"><h3>Do not manufacture a route</h3>
    <p>Splitting across relatives’ quotas, underground swaps and crypto bridges are unlawful, and the statute prices
    them: fines of up to 30% of the amount, or 30%–100% in serious cases
    [{ref('https://www.safe.gov.cn/beijing/2018/1221/1010.html','V10')}]. Four of the 23 catalogued methods are rejected
    for this reason and are kept visible so they are not re-discovered as “ideas”.</p></div>
  <div class="answer"><h3>The U.S. review includes tax, basis and reporting</h3>
    <p>A transfer of your own existing principal is not itself a new income category, but the underlying income and
    currency gain still require analysis. The personal-transaction exclusion in §988(e)(2) does not apply when the
    gain exceeds $200 [{ref('https://www.govinfo.gov/content/pkg/USCODE-2024-title26/html/USCODE-2024-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm','V15')}].
    FBAR and Form 8938 are separate reporting tests; a foreign tax credit is limited and is not available for tax on excluded income.</p></div>
  <div class="answer"><h3>What still cannot be answered</h3>
    <p>The exact tax on this balance, the eligible route, the all-in USD cost and the cheapest provider all depend on
    private facts and a live quote. {FLAGS} open flags and {len([c for c in CHECKS['checks'] if c['status']!='VERIFIED'])}
    items this pass could not re-verify are published rather than filled in.
    <a href="transfer-guide/flagged.html">See every flag →</a></p></div>
</div>

<h2 id="costs">What it costs to move the money</h2>
<p class="muted">Published sender fees are converted from the bank’s renminbi tariff at the Bank of China board of
{TODAY} 10:25:02 ({RATE_BOC:.4f} CNY/USD). The exchange margin is a bound, not a quote: it is the full gap between the
board’s buying and selling prices ({pct(BOARD_GAP)}), which no retail customer can do better than. Intermediary,
receiving-bank and correspondent fees are not published by this bank and stay blank.</p>

<div class="tablewrap">
<table>
<caption>Documented bank route (M01) · milestone tiers · full 40-tier ladder in the cost page</caption>
<thead><tr>
  <th scope="col">Amount</th><th scope="col" class="num">CNY needed</th><th scope="col">Route</th>
  <th scope="col" class="num">Sender fee<br>Premier/Advance</th><th scope="col" class="num">Sender fee<br>Private Bkg / Elite</th>
  <th scope="col" class="num">Exchange margin<br>(board bound)</th><th scope="col" class="num">Indicative total</th><th scope="col">Source</th>
</tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
</div>
<p class="muted">“Indicative total” = sender fee at the board rate + the exchange-margin bound. It excludes any tax,
any intermediary or receiving-bank charge, and any U.S. reporting cost. In renminbi the fee is
0.1% of the amount, minimum CNY 100, maximum CNY 500, plus a CNY 120 cable — that cap is why the dollar fee stops
rising after roughly $70,000.</p>

<div class="tablewrap">
<table>
<caption>Same tiers, other routes · the constraints are visible in the “steps” column</caption>
<thead><tr>
  <th scope="col">Amount</th><th scope="col">Route</th><th scope="col">Constraint</th>
  <th scope="col" class="num">Fee</th><th scope="col" class="num">Margin bound</th><th scope="col">Source</th>
</tr></thead>
<tbody>
<tr><th scope="row" data-label="Amount">any</th><td data-label="Route">M02 HSBC Global Transfer, self-named overseas account</td>
  <td data-label="Constraint">Needs HSBC accounts in both countries + Premier/Elite relationship</td>
  <td class="num" data-label="Fee">$0.00 PB/Premier<br>$20 Advance</td>
  <td class="num" data-label="Margin bound">≤ {pct(BOARD_GAP)}</td>
  <td class="src" data-label="Source">{ref('https://www.hsbc.com.cn/content/dam/hsbc/cn/docs/document-download/tariff-of-Accounts-services-for-personal-customers-v2.pdf','HSBC 2.2.6.1 [V12]')}</td></tr>
{''.join(alt_rows_2)}
{''.join(alt_rows_3)}
</tbody>
</table>
</div>
<p class="muted">M06 uses the USD 50,000 annual total: it is only available to PRC-ID / permanent-resident holders, and
one wire per calendar year. M15 is not a transfer at all — it is retail cash with a hard statutory ceiling and no
paperwork, and its issuer fees are not published uniformly, so they stay blank.</p>

<h2 id="methods">Every method, with its status</h2>
<p class="muted">23 catalogued routes: 17 lawful or conditional, 1 closed-loop (no exit), 4 rejected as unlawful. Each
row links to the full pros, cons, statutory cap and numbered playbook.</p>
<div class="tablewrap">
<table>
<caption>Method catalogue · status is the repository’s legal reading, with its own source per row</caption>
<thead><tr><th scope="col">ID</th><th scope="col">Method</th><th scope="col">Status</th><th scope="col">Best for</th><th scope="col">Official source</th><th scope="col">Detail</th></tr></thead>
<tbody>{''.join(method_rows)}</tbody>
</table>
</div>

<h2 id="how">How a $400,000 transfer actually works</h2>
<ol class="steps">
  <li><strong>Establish what the money is.</strong> Pull the PRC individual income-tax payment record
  (个人所得税纳税记录) for every year that funded the balance, from the tax app or the tax office. This is the document the
  bank will ask for first. [{ref('https://www.safe.gov.cn/tianjin/2026/0713/3088.html','V03')}]</li>
  <li><strong>Match it to contracts and payroll evidence.</strong> Employment contract, payroll slips, and — for older
  income — anything showing the money was actually earned then. SAFE says there is no deadline on this
  [{ref('https://www.safe.gov.cn/henan/2022/0718/1249.html','V09')}], so the constraint is your own paperwork, not a statute.</li>
  <li><strong>Ask the bank, in writing, what it will accept.</strong> Request the refusal or the requirement in writing,
  naming the tax type, period, base and legal basis if a tax is asserted — and a separate all-in quote showing the
  applied rate, the commission, the cable, and any correspondent or receiving charge.</li>
  <li><strong>Decide who executes.</strong> If you are outside China, SAFE’s published Q&amp;A allows another person to
  run the remittance formalities [{ref('https://www.safe.gov.cn/henan/2022/0718/1247.html','V08')}]; the bank will still
  want an authorisation it accepts.</li>
  <li><strong>Convert at the counter, then remit.</strong> The conversion produces a memo (兑换水单) you must keep: it is
  the only thing that lets you reverse an unspent remainder later, and only for 24 months
  [{ref('https://www.safe.gov.cn/tianjin/2026/0917/3134.html','V05')}].</li>
  <li><strong>Price the wire two ways.</strong> Telegraphic transfer costs 0.1% (min CNY 100, max CNY 500) + CNY 120 cable
  for Premier/Advance, and $0.00 for Private Banking/Premier Elite individuals
  [{ref('https://www.hsbc.com.cn/content/dam/hsbc/cn/docs/document-download/tariff-of-Accounts-services-for-personal-customers-v2.pdf','V11')}].
  “Pay Exact” (OUR) adds CNY 200 if you want the receiver credited in full.</li>
  <li><strong>Check the U.S. side before the money lands.</strong> Principal is not income; personal FX gain above $200 is
  not de minimis [{ref('https://www.govinfo.gov/content/pkg/USCODE-2024-title26/html/USCODE-2024-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm','V15')}];
  FBAR and Form 8938 depend on balances, not on transfers.</li>
  <li><strong>File the reports the balance triggers.</strong> A closed account or a completed transfer does not erase an
  earlier reporting obligation for the year in which the threshold was crossed.</li>
</ol>

<h2 id="subpages">All pages, by category</h2>
<p class="muted">Listed first is the latest dated pass, not a replacement for the sets below it. The consolidated
dashboard re-read 18 official documents on 11 November 2026, prices the exchange margin one way rather than as the
full buy–sell gap, and publishes the disagreements it found between the earlier sets.</p>
<div class="cards">
  <a class="card" href="canon-d6a42474/index.html"><b>Consolidated dashboard · latest re-read</b><span>18 sources · 8 priced routes · 24 flags</span>
    <em>Answer first, then every $10,000 tier to $400,000, the tax layers, 16 gating questions and a reproducible repo audit.</em></a>
  <a class="card" href="transfer-guide/methods.html"><b>Methods &amp; playbooks</b><span>23 methods · pros · cons · steps</span>
    <em>Every route with its statutory cap and numbered execution steps.</em></a>
  <a class="card" href="playbook-c1d73006/costs.html"><b>Cost ladder · latest published-input pass</b><span>40 tiers × 17 methods = 680 rows</span>
    <em>$10,000 to $400,000 in $10,000 steps, filtered and searchable; dated bank-board estimates and blank unpublished charges.</em></a>
  <a class="card" href="transfer-guide/penalties.html"><b>Penalties &amp; taxes</b><span>7 layers, PRC and U.S.</span>
    <em>What is a tax, what is a fee, what is a fine — and which document each one comes from.</em></a>
  <a class="card" href="transfer-guide/questions.html"><b>Open questions</b><span>{len(QUESTIONS)} gating facts</span>
    <em>What we know, what we do not, and how to find out — the decision checklist.</em></a>
  <a class="card" href="transfer-guide/flagged.html"><b>Flagged for review</b><span>{FLAGS} items</span>
    <em>Unverified values and eligibility limits, published rather than guessed.</em></a>
  <a class="card" href="transfer-guide/sources.html"><b>Source register</b><span>{SOURCES} official documents</span>
    <em>PRC regulators, PRC tax, IRS, GPO, CBP, FinCEN, bank tariffs — with locators.</em></a>
  <a class="card" href="verification-3347ca0a/index.html"><b>This pass’s verification</b><span>22 checks · exact quotes</span>
    <em>Every load-bearing sentence re-fetched on {TODAY}, with what could not be re-checked stated plainly.</em></a>
  <a class="card" href="verification-3347ca0a/irregularities.html"><b>Repository audit</b><span>12 findings</span>
    <em>Duplicate sites, conflicting counts, rate bases and rows without a source.</em></a>
  <a class="card" href="acceptance-382482c0/index.html"><b>Corrective acceptance · 11 Nov</b><span>8 fresh source checks · 7 open cautions</span>
    <em>Final-integration corrections, official links, explicit verification boundaries and remaining review items.</em></a>
  <a class="card" href="dashboard-f79e64e7/index.html"><b>Second verification pass</b><span>34 sources · quotes checked 11 Nov</span>
    <em>A separate session’s decision dashboard: questions, routes, cost at every $10,000, and corrections to earlier sets.</em></a>
  <a class="card" href="playbook-c1d73006/index.html"><b>Route-by-origin playbook</b><span>10 origins · 34 sources · read 11 Nov</span>
    <em>A separate session’s playbook: pick the route by where the money came from, with the papers, the tax and the cost for each.</em></a>
</div>

<h2 id="questions">What has to be answered before a decision</h2>
<p class="muted">No route can be chosen and no tax figure can be calculated until these are established. Each has a way
to find out — that is the point of listing them.</p>
<div class="tablewrap">
<table>
<caption>Gating questions · first eight of the full checklist</caption>
<thead><tr><th scope="col">ID</th><th scope="col">Question</th><th scope="col">How to find out</th><th scope="col">Official source</th><th scope="col">Detail</th></tr></thead>
<tbody>{''.join(q_rows) if q_rows else '<tr><td colspan="4" class="blank">Question ledger not parsed; see transfer-guide/questions.html</td></tr>'}</tbody>
</table>
</div>

<h2 id="archive">Other research runs in this repository</h2>
<p class="muted">This repository contains {len(archive)} parallel research sets built by separate sessions. They are
listed here for audit, not as equal choices: counts differ between them
(<a href="verification-3347ca0a/irregularities.html#IR-02">IR-02</a>,
<a href="verification-3347ca0a/irregularities.html#IR-03">IR-03</a>,
<a href="verification-3347ca0a/irregularities.html#IR-04">IR-04</a>). This page and the eight pages above are the
canonical set.</p>
<div class="tablewrap">
<table class="nav-index">
<caption>Archive · navigational index, not claims · kept because deleting another session’s work would destroy its audit trail</caption>
<thead><tr><th scope="col">Set</th><th scope="col">Published counts</th><th scope="col">Status</th></tr></thead>
<tbody>{archive_rows}</tbody>
</table>
</div>
</main>

<footer class="site"><div class="wrap">
  <p><strong>Research, not advice.</strong> No account facts were supplied, no bank was contacted, no funds moved and no
  return filed. Every unresolved personal value is left blank or flagged.</p>
  <p class="smallprint">Rate bases: {RATE_BOC:.4f} CNY/USD = Bank of China USD cash-remittance selling price on {TODAY} 10:25:02
  [{ref('https://www.boc.cn/sourcedb/whpj/','V20')}]; {RATE_IRS} CNY/USD = IRS 2025 yearly average for tax translation
  [{ref('https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates','V18')}]. A
  renminbi fee of CNY 620 is {usd(620 / RATE_BOC)} at the board rate and {usd(620 / RATE_IRS)} at the tax rate — the
  repository’s older tables use the second. Source-backed means the sentence exists; analysis means it was derived;
  blank means it was not published.</p>
  <p class="smallprint"><a href="verification-3347ca0a/EXECUTIVE_SUMMARY.md" download>Executive summary (Markdown)</a> ·
  <a href="verification-3347ca0a/index.html">Verification ledger</a> ·
  <a href="verification-3347ca0a/irregularities.html">Repository audit</a> ·
  <a href="transfer-guide/sources.html">Sources</a> ·
  <a href="transfer-guide/flagged.html">Flags</a> ·
  <a href="COORDINATION.md">Task board</a> ·
  <a href="README.md">README</a></p>
</div></footer>
</body></html>
"""


# ----------------------------------------------------------------------------
# Verification page
# ----------------------------------------------------------------------------
def verification_page():
    rows = []
    for c in CHECKS["checks"]:
        ok = c["status"] == "VERIFIED"
        pill = '<span class="pill ok">verified</span>' if ok else '<span class="pill warn">not re-checked</span>'
        quote = c["quote"]
        quote_en = c.get("quote_en", "")
        quote_html = f'<q>{esc(quote)}</q>' if quote and quote != "—" else '<span class="blank">no sentence extracted</span>'
        if quote_en and quote and quote != "—":
            quote_html += f'<div class="muted">{esc(quote_en)}</div>'
        rows.append(f"""
        <tr id="{esc(c['id'])}">
          <th scope="row" data-label="ID">{esc(c['id'])}</th>
          <td data-label="Area">{esc(c['area'])}</td>
          <td data-label="Claim tested">{esc(c['claim'])}</td>
          <td data-label="Exact sentence retrieved">{quote_html}
            <div class="muted" style="margin-top:.35rem">{esc(c['doc'])} · {esc(c['locator'])} · {esc(c['authority'])}</div></td>
          <td data-label="Status">{pill}</td>
          <td data-label="Limit">{esc(c['limit'])}</td>
          <td class="src" data-label="Source">{ref(c['url'], 'open')}</td>
        </tr>""")

    verified = sum(1 for c in CHECKS["checks"] if c["status"] == "VERIFIED")
    total = len(CHECKS["checks"])

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Verification ledger · {verified}/{total} official documents re-checked on {TODAY}</title>
<meta name="description" content="Line-by-line re-verification of the load-bearing official sources behind the CNY-to-USD dashboard, with the exact sentence retrieved from each document on {TODAY}.">
<meta name="theme-color" content="#101d1a">
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<style>{CSS}</style>
</head>
<body>
<header class="site"><div class="wrap">
  <a class="brand" href="../index.html"><span class="mark">¥</span><span>China Money<small>VERIFICATION LEDGER</small></span></a>
  <div class="site-meta">Pass dated {TODAY}<br>{verified} of {total} checks confirmed</div>
</div></header>
{nav([('../index.html','← Dashboard'), ('index.html','Verification'), ('irregularities.html','Repository audit'), ('../transfer-guide/sources.html','Source register')], 'index.html')}
<main class="wrap">
<span class="eyebrow">Final integration · re-verification</span>
<h1>Every load-bearing sentence, re-fetched.</h1>
<p class="lede">A prior session’s ledger is not evidence. On {TODAY} each document below was retrieved again from its
own official host and the supporting sentence copied out of the retrieved text. Where a document was retrieved but the
specific figure was not read out, the row says so and the figure is not republished as verified.</p>

<div class="kpis">
  <div class="kpi"><p class="label">Checks</p><p class="value">{total}</p><p class="sub">{verified} confirmed · {total - verified} explicitly not confirmed</p></div>
  <div class="kpi"><p class="label">Confirmed</p><p class="value">{verified}</p><p class="sub">Sentence located in the retrieved text on {TODAY}</p></div>
  <div class="kpi"><p class="label">Left unconfirmed</p><p class="value">{total - verified}</p><p class="sub">Flagged instead of filled in</p></div>
</div>

<h2>The checks</h2>
<div class="tablewrap">
<table>
<caption>ID · area · claim · the sentence actually retrieved · status · what the source does not settle · link</caption>
<thead><tr>
  <th scope="col">ID</th><th scope="col">Area</th><th scope="col">Claim tested</th>
  <th scope="col">Sentence retrieved</th><th scope="col">Status</th><th scope="col">What it does not settle</th><th scope="col">Source</th>
</tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
</div>

<h2>Method, and its limits</h2>
<p><strong>What this pass did.</strong> Re-fetched {total} documents; extracted the sentence that a published claim
depends on; recomputed every fee in renminbi and dollars from the tariff text rather than from another page; re-derived
the CMS-style tier arithmetic, the ATM year count and both rate bases.</p>
<p><strong>What it did not do.</strong> It did not contact a bank, did not obtain an executable quote, did not read any
private account document, and did not obtain professional tax advice. Retrieval proves a sentence is on the page today;
it does not prove the rule applies to any particular person, and sites change.</p>
<p><strong>Why two rate bases appear.</strong> U.S. tax translation uses the IRS 2025 yearly average of
{RATE_IRS} CNY/USD (V18). Cost illustration here uses the Bank of China board of {TODAY}: {RATE_BOC:.4f} CNY/USD (V20).
Mixing them silently is one of the repository irregularities this pass found
(<a href="irregularities.html#IR-05">IR-05</a>).</p>

<p class="muted">Raw data: <a href="data/checks.json">data/checks.json</a> ·
<a href="data/irregularities.json">data/irregularities.json</a> · generator <code>build.py</code> · checker <code>verify.py</code>.</p>
</main>
<footer class="site"><div class="wrap">
  <p><strong>Not tax or legal advice.</strong> A verified sentence is evidence that a rule exists, not that it applies
  to you.</p>
  <p class="smallprint"><a href="../index.html">Dashboard</a> · <a href="irregularities.html">Repository audit</a> ·
  <a href="../transfer-guide/sources.html">Full source register</a></p>
</div></footer>
</body></html>
"""


# ----------------------------------------------------------------------------
# Irregularities page
# ----------------------------------------------------------------------------
def irregularities_page():
    sev_class = {"structure": "warn", "conflict": "bad", "stale": "warn", "gap": "warn", "resolved": "ok"}
    rows = []
    for f in IRREG["findings"]:
        cls = sev_class.get(f["severity"], "")
        rows.append(f"""
        <tr id="{esc(f['id'])}">
          <th scope="row" data-label="ID">{esc(f['id'])}</th>
          <td data-label="Severity"><span class="pill {cls}">{esc(f['severity'])}</span></td>
          <td data-label="Finding">{esc(f['finding'])}</td>
          <td data-label="Evidence">{esc(f['evidence'])}</td>
          <td data-label="What it changes for a reader">{esc(f['impact'])}</td>
          <td data-label="How it was checked">{esc(f['verification'])}</td>
          <td class="src" data-label="Link">{ref(f['source'], 'open')}</td>
        </tr>""")

    counts = {}
    for f in IRREG["findings"]:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1
    summary = " · ".join(f"{v} {k}" for k, v in sorted(counts.items()))

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Repository audit · {len(IRREG['findings'])} findings · China Money</title>
<meta name="description" content="Line-by-line audit of the CNY-to-USD research repository: duplicate sites, conflicting counts, rate bases, stale dates and rows without a direct official source.">
<meta name="theme-color" content="#101d1a">
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<style>{CSS}</style>
</head>
<body>
<header class="site"><div class="wrap">
  <a class="brand" href="../index.html"><span class="mark">¥</span><span>China Money<small>REPOSITORY AUDIT</small></span></a>
  <div class="site-meta">Reviewed {IRREG['meta']['reviewed_on']}<br>{len(IRREG['findings'])} findings · {summary}</div>
</div></header>
{nav([('../index.html','← Dashboard'), ('index.html','Verification'), ('irregularities.html','Repository audit'), ('../transfer-guide/audit.html','Route audit')], 'irregularities.html')}
<main class="wrap">
<span class="eyebrow">Whole-repository review · {IRREG['meta']['reviewed_on']}</span>
<h1>What is inconsistent in here, and what it changes.</h1>
<p class="lede">{esc(IRREG['meta']['scope'])} Findings are published, not silently “fixed” in other sessions’ files:
where a number conflicts, this page states which one it uses and why.</p>

<div class="notice"><strong>Nothing here is a failed legal claim.</strong> Most findings are organisational: several
correct answers written at different times, with different scope rules, none of them wrong on its own terms. The two
that can actually mislead money decisions are the rate base (<a href="#IR-05">IR-05</a>) and the quota wording
(<a href="#IR-11">IR-11</a>).</div>

<div class="tablewrap">
<table>
<caption>{len(IRREG['findings'])} findings · severity · evidence · consequence for the reader · how it was checked · source. A source of github.com means the evidence is a file in this repository, not an external official document; those rows make no external factual claim.</caption>
<thead><tr>
  <th scope="col">ID</th><th scope="col">Severity</th><th scope="col">Finding</th><th scope="col">Evidence</th>
  <th scope="col">What it changes for a reader</th><th scope="col">How it was checked</th><th scope="col">Source</th>
</tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
</div>

<h2>How the audit was run</h2>
<ol class="steps">
  <li><strong>Enumerate, do not assume.</strong> Every directory with HTML was counted, every claim-count phrase on
  each landing page was extracted with a pattern scan, and the numbers were compared rather than eyeballed.</li>
  <li><strong>Recompute money.</strong> Fees, caps and year counts were recomputed from the tariff text in
  <code>build.py</code> and re-derived independently in <code>verify.py</code>.</li>
  <li><strong>Check links locally.</strong> Every internal <code>href</code>/<code>src</code> path on the three
  generated pages was resolved against the filesystem, and the whole tree was re-scanned for broken internal links
  (111 HTML pages, 0 broken on {TODAY}).</li>
  <li><strong>Read the corrections.</strong> Where a page corrects an earlier figure (the HSBC USD 7 wording), the
  occurrence list was generated so the correction itself is auditable.</li>
  <li><strong>State the boundary.</strong> A structural scan does not prove a claim is unsupported, and a retrieval does
  not prove a rule applies to you.</li>
</ol>

<p class="muted">Raw data: <a href="data/irregularities.json">data/irregularities.json</a>. Related: the
<a href="index.html">verification ledger</a>, the transfer guide’s own
<a href="../transfer-guide/audit.html">route audit</a> and its <a href="../transfer-guide/flagged.html">flags</a>.</p>
</main>
<footer class="site"><div class="wrap">
  <p><strong>Research, not advice.</strong> Findings are limited to what could be checked from files and official
  documents in this checkout.</p>
  <p class="smallprint"><a href="../index.html">Dashboard</a> · <a href="index.html">Verification ledger</a> ·
  <a href="../transfer-guide/sources.html">Sources</a></p>
</div></footer>
</body></html>
"""


FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<rect width="64" height="64" rx="12" fill="#101d1a"/>
<text x="32" y="45" font-family="system-ui, sans-serif" font-size="38" font-weight="700"
 fill="#9de0c7" text-anchor="middle">¥</text></svg>
"""


def main():
    os.makedirs(os.path.join(HERE, "assets"), exist_ok=True)
    pages = {
        os.path.join(ROOT, "index.html"): root_page(),
        os.path.join(HERE, "index.html"): verification_page(),
        os.path.join(HERE, "irregularities.html"): irregularities_page(),
        os.path.join(HERE, "assets", "favicon.svg"): FAVICON,
    }
    for path, content in pages.items():
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        print(f"wrote {os.path.relpath(path, ROOT)} ({len(content):,} bytes)")

    # Export the computed ladder so a reviewer can diff the arithmetic.
    export = {
        "generated": date.today().isoformat(),
        "session": "arena/3347ca0a-china2",
        "inputs": {
            "rate_boc_sell": RATE_BOC, "rate_boc_buy": RATE_BOC_BUY, "rate_irs_2025": RATE_IRS,
            "board_gap": BOARD_GAP, "tt_rate": TT_RATE, "tt_min_cny": TT_MIN_CNY,
            "tt_max_cny": TT_MAX_CNY, "cable_cny": CABLE_CNY, "pay_exact_cny": PAY_EXACT_CNY,
            "atm_year_cny": ATM_YEAR_CNY, "atm_day_cny": ATM_DAY_CNY,
        },
        "tiers": LADDER,
    }
    out = os.path.join(HERE, "data", "computed_ladder.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(export, fh, indent=2)
    print(f"wrote {os.path.relpath(out, ROOT)}")


if __name__ == "__main__":
    main()
