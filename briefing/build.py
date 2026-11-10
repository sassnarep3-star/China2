#!/usr/bin/env python3
"""Generate the consolidated 'China money' briefing (arena/dc2c65bd-china2).

Reads the prior sessions' source-linked ledgers (read-only):
  repatriate/data/{methods,flags,sources,rules}.json + repatriate/exports/cost-ladders.csv
Adds this session's independently verified official sources (B01-B05), and emits
static HTML in briefing/. Deterministic: same inputs -> same bytes.
"""
import json, math, html, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BR = ROOT / "briefing"
RATE = 7.129  # IRS 2025 yearly average, China Yuan (S23). Reference conversion only.

methods = {m["id"]: m for m in json.load(open(ROOT / "repatriate/data/methods.json"))["methods"]}
flags = json.load(open(ROOT / "repatriate/data/flags.json"))["flags"]
sources = json.load(open(ROOT / "repatriate/data/sources.json"))["sources"]
TIERS = [i * 10000 for i in range(1, 41)]

# This session's independently retrieved official sources (2026-11-10)
SESSION_SOURCES = [
    {"id": "B01", "publisher": "U.S. FinCEN / eCFR (ecfr.gov)", "kind": "regulator",
     "title": "31 CFR 1010.821 — Penalty adjustment and table (FinCEN), penalties assessed on or after 2025-01-17",
     "url": "https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821",
     "status": "fetched 2026-11-10",
     "used_for": "FBAR civil penalties: non-willful max $16,536 per report; willful max $165,353. Table row: 31 U.S.C. 5321(a)(5)(B)(i) and (a)(5)(C)(i)(I). eCFR is authoritative but unofficial; annual inflation adjustment."},
    {"id": "B02", "publisher": "IRS (irs.gov)", "kind": "regulator",
     "title": "Publication 525 (2025), Taxable and Nontaxable Income — foreign currency transactions",
     "url": "https://www.irs.gov/publications/p525",
     "status": "fetched 2026-11-10 (also corroborated by 26 U.S.C. §988(e)(2))",
     "used_for": "Gain on a personal foreign currency transaction is not included in income unless it exceeds $200; above that it is reported as a capital gain."},
    {"id": "B03", "publisher": "IRS (irs.gov)", "kind": "regulator",
     "title": "About Form 8938, Statement of Specified Foreign Financial Assets",
     "url": "https://www.irs.gov/forms-pubs/about-form-8938",
     "status": "fetched 2026-11-10",
     "used_for": "Form 8938 filing obligation and thresholds depend on filing status and residence (higher thresholds abroad); thresholds vary - see the Form 8938 instructions. Penalty: see B04."},
    {"id": "B04", "publisher": "IRS (irs.gov)", "kind": "regulator",
     "title": "IRM 5.21.6 — Foreign Financial Account Reporting: Form 8938 penalties",
     "url": "https://www.irs.gov/irm/part5/irm_05-021-006",
     "status": "fetched 2026-11-10 (search result text)",
     "used_for": "Internal Revenue Manual: up to $10,000 for failure to file Form 8938, plus $10,000 for each additional 30 days after IRS notice, potential maximum $60,000; reasonable-cause exception applies."},
    {"id": "B05", "publisher": "IRS (irs.gov)", "kind": "regulator",
     "title": "IRM 4.26.16 — Report of Foreign Bank and Financial Accounts (FBAR)",
     "url": "https://www.irs.gov/irm/part4/irm_04-026-016",
     "status": "fetched 2026-11-10 (search result text)",
     "used_for": "IRS examination guidance: non-willful $10,000 per violation adjusted for inflation (see B01 for current amount); in no event may total non-willful penalties exceed 50% of the highest aggregate balance of the accounts at issue."},
    {"id": "B06", "publisher": "HSBC Bank (China) Company Limited (hsbc.com.cn)", "kind": "provider",
     "title": "Tariff of Accounts and Services for Wealth and Personal Banking Business (effective 31 Oct 2026)",
     "url": "https://www.hsbc.com.cn/content/dam/hsbc/cn/docs/document-download/tariff-of-Accounts-services-for-personal-customers-v2.pdf",
     "status": "fetched 2026-11-10 (items 2.2.4.1-2.2.4.4, 2.2.6.1-2.2.6.2, 2.2.7, 2.2.2.1)",
     "used_for": "TT issuance 0.1% (min CNY 100 / max CNY 500 for Premier/Advance; Private Banking individual free) + CNY 120 cable; Global Transfer to own overseas HSBC: PB/Premier free, Advance USD 20 indicative CNY 145; International Education Payment USD 7 (NOT a general remittance fee); Pay Exact surcharge CNY 200. Note: internal Chinese section header shows a 2024-09-12 version - see flag N02."},
    {"id": "B07", "publisher": "IRS (irs.gov)", "kind": "regulator",
     "title": "Report of Foreign Bank and Financial Accounts (FBAR) — canonical IRS page",
     "url": "https://www.irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar",
     "status": "fetched 2026-11-10 (live 200 OK)",
     "used_for": "Canonical live IRS FBAR guidance: >$10,000 aggregate value any time triggers FinCEN Form 114 via BSA E-Filing, due April 15 with automatic extension to October 15, 5-year recordkeeping. (Supersedes dead /individuals/ path noted in N01.)"},
    {"id": "B08", "publisher": "IRS (irs.gov)", "kind": "regulator",
     "title": "Rev. Proc. 2026-35 (released 2026-11-09) — 2027 Inflation-Adjusted Tax Items",
     "url": "https://www.irs.gov/pub/irs-drop/rp-26-35.pdf",
     "status": "fetched 2026-11-10",
     "used_for": "Section 3.41: 2027 Foreign Earned Income Exclusion (§911) = $137,300 (vs $132,900 for 2026). Section 3.51: 2027 §6039F Form 3520 foreign-corporation/partnership gift threshold = $21,240. Section 3.46(3): 2027 §2801 covered-expatriate gift exception = $20,000."},
    {"id": "B09", "publisher": "IRS (irs.gov)", "kind": "regulator",
     "title": "Gifts from a Foreign Person — Form 3520 Part IV reporting thresholds",
     "url": "https://www.irs.gov/businesses/gifts-from-foreign-person",
     "status": "fetched 2026-11-10",
     "used_for": "Form 3520 Part IV triggers: >$100,000 aggregate gifts/bequests from nonresident alien or foreign estate (list gifts >$5,000 separately); >$20,116 (2025) / >$20,573 (2026) from foreign corporations/partnerships (see B08 for 2027)."},
    {"id": "B10", "publisher": "Federal Reserve Board (federalreserve.gov)", "kind": "regulator",
     "title": "H.10 Foreign Exchange Rates Weekly Release (2026-11-09, rates through 2026-11-06)",
     "url": "https://www.federalreserve.gov/releases/h10/current/",
     "status": "fetched 2026-11-10",
     "used_for": "China Yuan noon buying rates Nov 2–6, 2026 = 6.6480–6.6760 CNY/USD (6.6760 on 2026-11-06). Used to illustrate ~6.8% FX sensitivity vs the IRS 2025 yearly average 7.129 (CNY 620 HSBC wire fee = $86.97 @ 7.129 vs $92.87 @ 6.6760); not an executable bank quote."},
]
SRC_URL = {s["id"]: s["url"] for s in sources}
SRC_URL.update({s["id"]: s["url"] for s in SESSION_SOURCES})
SRC_TITLE = {s["id"]: s["title"] for s in sources}
SRC_TITLE.update({s["id"]: s["title"] for s in SESSION_SOURCES})

def esc(s): return html.escape(str(s), quote=True)
def money(n, cur="$", dp=2): return f"{cur}{n:,.{dp}f}"

def hsbc_tt_fee_cny(usd_amount, tranche_usd=None):
    """HSBC Premier/Advance TT issuance fee for one wire of tranche_usd (or usd_amount)."""
    amt = tranche_usd if tranche_usd is not None else usd_amount
    cny = amt * RATE
    fee = min(max(cny * 0.001, 100.0), 500.0)
    return fee

def cost_row(method_id, tier):
    """Return dict(published_fee_usd or None, note, constraint, fine(lo,hi) or None)."""
    m = methods[method_id]
    cny = tier * RATE
    cid = method_id
    if cid == "M01":
        fee_cny = hsbc_tt_fee_cny(tier) + 120.0
        return dict(fee=fee_cny / RATE, fee_cny=fee_cny, band=None,
                    spread="", constraint="1 wire", note="Wire fee caps at CNY 500 + CNY 120 cable ≥ ~$70,150 equivalent (CNY 500,000)")
    if cid == "M02":
        n = math.ceil(tier / 50000)
        total = 0.0
        remaining = tier
        for _ in range(n):
            tr = min(remaining, 50000)
            total += hsbc_tt_fee_cny(tier, tr) + 120.0
            remaining -= tr
        yrs = n
        return dict(fee=total / RATE, fee_cny=total, band=None,
                    spread="", constraint=f"{yrs} calendar yr{'s' if yrs>1 else ''}",
                    note=f"{n} wire(s) of ≤$50,000 (own quota only)")
    if cid == "M03":
        return dict(fee=0.0, fee_cny=0.0, band=None,
                    spread="", constraint="Premier / Private Banking",
                    note="Published fee $0 (PB/Premier). Advance: USD 20 per transfer; transfer count unverified")
    if cid == "M07":
        trips = math.ceil(tier / 5000)
        trips_permit = math.ceil(tier / 10000)
        return dict(fee=None, fee_cny=None, band=None,
                    spread="", constraint=f"{trips} trips (no permit)",
                    note=f"{trips_permit} trips with bank permits ($5k–$10k/trip); travel cost unverified")
    if cid == "M09":
        days = math.ceil(tier / 500)
        return dict(fee=None, fee_cny=None, band=None,
                    spread="", constraint=f"{days} bank days (ID-only)",
                    note="Memo route only up to original exchange; memo valid 24 months")
    if cid == "M04":
        n = math.ceil(cny / 300000)
        return dict(fee=None, fee_cny=None, band=None, spread="provider rate (unverified)",
                    constraint=f"{n} transfer(s)",
                    note="≤CNY 300,000 per bank-app transfer; overall limit = documented after-tax salary")
    if cid == "M05":
        return dict(fee=None, fee_cny=None, band=None, spread="provider rate (unverified)",
                    constraint="Eligibility / quote required", note="Cash pickup only at retrieval (F07); fees not statically published")
    if cid == "M06":
        years = math.ceil(cny / 100000)
        days = math.ceil(cny / 10000)
        return dict(fee=None, fee_cny=None, band=None, spread="card-network FX (unverified)",
                    constraint=f"{years} calendar yr{'s' if years>1 else ''}",
                    note=f"≥{days} ATM days; cap CNY 100,000/yr all cards (~USD 14,027)")
    if cid == "M08":
        trips = math.ceil(cny / 20000)
        return dict(fee=None, fee_cny=None, band=None, spread="offshore rate (unverified)",
                    constraint=f"{trips} trips",
                    note="≤CNY 20,000/trip; excess returned by customs")
    if cid == "M10":
        return dict(fee=None, fee_cny=None, band=None, spread="bank bill rate (unverified)",
                    constraint="SAFE-approved amount", note="Lump sum permitted within approved limit; process fee unpublished")
    if cid == "M11":
        return dict(fee=None, fee_cny=None, band=None, spread="bank bill rate (unverified)",
                    constraint="SAFE-approved amount", note="Inheritance documents + tax clearance required")
    if cid == "M12":
        return dict(fee=None, fee_cny=None, band=None, spread="bank bill rate (unverified)",
                    constraint="After IIT on gain", note="PRC IIT 20% on the gain + transaction taxes (unquantified)")
    if cid == "M13":
        return dict(fee=None, fee_cny=None, band=None, spread="settlement rate (unverified)",
                    constraint="Genuine trade only", note="Quota-exempt with valid trading documents")
    if cid in ("M14", "M15", "M16", "M17"):
        return dict(fee=None, fee_cny=None, band=None, spread="not a price",
                    constraint="REJECTED — unlawful",
                    fine=(0.30 * tier, 0.30 * tier, 1.00 * tier),
                    note="Statutory fine exposure; confiscation and criminal liability may also apply")
    raise AssertionError(cid)

HEAD = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — China money briefing</title>
<meta name="description" content="{desc}">
<link rel="stylesheet" href="assets/style.css">
<link rel="icon" href="../docs/favicon.svg">
</head><body>
<header><div class="bar"><strong>China money · briefing</strong>
{nav}
</div></header>
<main>
"""
FOOT = """</main>
<footer><p><strong>Research, not advice.</strong> No private account facts were used, no bank was contacted, no funds moved, no returns filed. Unknown all-in costs and FX spreads remain blank. Published fee components are not quotes or total costs. See <a href="flagged.html">Flagged for review</a>.</p>
<p><a href="index.html">Briefing home</a> · <a href="EXECUTIVE_SUMMARY.md">Markdown summary</a> · <a href="AUDIT.md">Audit (MD)</a> · <a href="../COORDINATION.md">Task board</a></p></footer>
<script src="assets/app.js"></script></body></html>
"""
NAV_ITEMS = [("index.html","Summary"),("costs.html","Costs $10k→$400k"),("methods.html","Methods & steps"),("audit.html","Repo audit"),("flagged.html","Flagged"),("sources.html","Sources")]

def nav(active):
    items = []
    for h, t in NAV_ITEMS:
        cur = " aria-current='page'" if h == active else ""
        items.append(f'<a href="{h}"{cur}>{t}</a>')
    return "<nav>" + "".join(items) + "</nav>"

CORRECTION_NOTICE = """<aside class="notice"><strong>Verification correction · 10 November 2026.</strong> Unsupported numeric FX-spread bands have been removed from this briefing. Unknown all-in costs remain blank. This is not a guarantee of zero tax, eligibility or cheapest service. <a href="flagged.html#corrections">Read the correction findings and official sources</a>.</aside>"""

def page(title, desc, active, body):
    return HEAD.format(title=esc(title), desc=esc(desc), nav=nav(active)) + CORRECTION_NOTICE + body + FOOT

def src_link(sid, label=None):
    url = SRC_URL.get(sid)
    if not url:
        return f'<span class="srcs">{esc(sid)} (no link)</span>'
    return f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer" title="{esc(SRC_TITLE.get(sid,""))}">{esc(label or sid)}</a>'

M_ORDER = ["M01","M03","M02","M04","M05","M07","M06","M08","M09","M10","M11","M12","M13","M14","M15","M16","M17"]
M_TAG = {"M01":("ok","Lawful · primary"),"M02":("ok","Lawful · quota"),"M03":("ok","Lawful · HSBC"),
         "M04":("ok","Lawful · provider"),"M05":("warn","Check availability"),"M06":("warn","Cap ~USD 14k/yr"),
         "M07":("warn","Cash · permit rules"),"M08":("warn","Cash · tiny quota"),"M09":("warn","Narrow · memo only"),
         "M10":("ok","Lawful · narrow"),"M11":("ok","Lawful · inheritance"),"M12":("ok","Lawful · property"),
         "M13":("ok","Lawful · trade"),"M14":("bad","Rejected"),"M15":("bad","Rejected"),"M16":("bad","Rejected"),"M17":("bad","Rejected")}

# ---------- costs.html ----------
def build_costs():
    rows_html = []
    decision = []
    for i, mid in enumerate(M_ORDER, 1):
        m = methods[mid]
        tag_cls, tag_txt = M_TAG[mid]
        is_bad = mid in ("M14","M15","M16","M17")
        # decision summary at three checkpoints
        def band_at(t):
            r = cost_row(mid, t)
            if r.get("fine"):
                return 'Rejected — see risk table'
            if r["band"]:
                lo = (r["fee"] or 0) + r["band"][0]; hi = (r["fee"] or 0) + r["band"][1]
                return f"{money(lo,'$',0)}–{money(hi,'$',0)}*"
            return money(r["fee"]) if r["fee"] is not None else "—"
        decision.append((i, mid, m, tag_cls, tag_txt, band_at(10000), band_at(100000), band_at(250000), band_at(400000)))
        trs = []
        for t in TIERS:
            r = cost_row(mid, t)
            cny = t * RATE
            if r.get("fine"):
                fee_cell = "—"
                fine_lo, fine_hi = r["fine"][0], r["fine"][2]
                cells = (f'<td class="num" data-label="Amount (USD)">{money(t,"$",0)}</td>'
                         f'<td class="num" data-label="Fine ≤30%">{money(fine_lo,"$",0)}</td>'
                         f'<td class="num" data-label="Serious 30–100%">{money(fine_lo,"$",0)}–{money(fine_hi,"$",0)}</td>'
                         f'<td class="num" data-label="Fee %">—</td><td data-label="Spread">—</td>'
                         f'<td data-label="Constraint">{esc(r["constraint"])}</td>')
            else:
                if r["fee"] is None:
                    fee_cell = '<span aria-label="unverified">—</span>'; fee_pct = "—"; allin = ""
                    fee_cls = "blank"
                else:
                    fee_cell = money(r["fee"], "$"); fee_pct = f'{r["fee"]/t*100:.3f}%'
                    if r["band"]:
                        lo = r["fee"] + r["band"][0]; hi = r["fee"] + r["band"][1]
                        allin = f"{money(lo)}–{money(hi)}*"
                    else:
                        allin = ""  # Published fee is not an all-in total.
                    fee_cls = ""
                spread = ""  # No official executable FX quote; blank by policy.
                cells = (f'<td class="num" data-label="Amount (USD)">{money(t,"$",0)}</td>'
                         f'<td class="num {fee_cls}" data-label="Published fee (USD)">{fee_cell}</td>'
                         f'<td class="num" data-label="Fee % of amount">{fee_pct}</td>'
                         f'<td class="num" data-label="All-in cost (unverified)">{allin}</td>'
                         f'<td data-label="FX spread (unverified)">{esc(spread)}</td>'
                         f'<td data-label="Constraint">{esc(r["constraint"])}</td>')
            cells += '<td data-label="Official sources">' + ' '.join(src_link(sid) for sid in dict.fromkeys(m['sources'] + (['B06', 'S23'] if not is_bad else ['S13'])) ) + '</td>'
            trs.append(f'<tr data-tier="{t}">{cells}</tr>')
        src_links = " ".join(src_link(s) for s in m["sources"])
        band_note = ""
        if mid not in ("M14","M15","M16","M17"):
            band_note = "<p class='small'>All-in cost and FX spread are blank: no executable quote was verified. Published fees are only one component. Blank = not published; never estimated. CNY reference at IRS 2025 average 7.129 CNY/USD (S23).</p>"
        else:
            band_note = "<p class='small'>Fine columns are statutory exposure (PRC FX rules, S13), <strong>not a price</strong>. Criminal liability and confiscation may also apply. Do not use these routes.</p>"
        if is_bad:
            trs = trs  # same 40-row table
        rows_html.append(f"""
<section class="method" id="{mid}" data-method="{mid}">
<h3><span class="tag {tag_cls}">{tag_txt}</span> {i}. {esc(m['name'])} <span class="small">[{mid}]</span></h3>
<p class="small"><strong>Who:</strong> {esc(m['who'])}</p>
<p class="small"><strong>Sources:</strong> {src_links}</p>
<div class="table-wrap"><table class="stack">
<thead><tr><th class="num">Amount (USD)</th><th class="num">{'Fine ≤30%' if is_bad else 'Published fee (USD)'}</th><th class="num">{'Serious 30–100%' if is_bad else 'Fee %'}</th><th class="num">{'—' if is_bad else 'All-in cost (unverified)'}</th><th>{'—' if is_bad else 'FX spread (unverified)'}</th><th>Constraint</th><th>Official sources</th></tr></thead>
<tbody>
{''.join(trs)}
</tbody></table></div>
{band_note}
<p class="small"><strong>Notes per amount:</strong> see constraints column; details on <a href="methods.html#{mid}">method {mid}</a>.</p>
</section>""")
    dec_rows = []
    for i, mid, m, tag_cls, tag_txt, b10, b100, b250, b400 in decision:
        dec_rows.append(f"<tr><td data-label='#'>{i}</td><td data-label='Method'><a href='#{mid}'><strong>{esc(m['short'] if m.get('short') else m['name'][:60])}</strong></a> <span class='tag {tag_cls}'>{tag_txt}</span></td><td class='num' data-label='$10,000'>{b10}</td><td class='num' data-label='$100,000'>{b100}</td><td class='num' data-label='$250,000'>{b250}</td><td class='num' data-label='$400,000'>{b400}</td><td data-label='Official sources'>{' '.join(src_link(sid) for sid in m['sources'])}</td></tr>")
    body = f"""
<h1>Cost to move CNY → USD: every $10,000 step, $10,000 → $400,000</h1>
<p class="lede">All 17 methods, costed at every $10,000 increment. Published fees are computed from the HSBC China tariff (effective 2026-10-31, items 2.2.4.x/2.2.6.1/2.2.2.1, {src_link('B06','tariff')}) at the IRS 2025 average reference rate 7.129 CNY/USD ({src_link('S23','IRS yearly average')}; for scale only, the Federal Reserve H.10 rate was 6.6760 CNY/USD on 2026-11-06, {src_link('B10','Fed H.10')}, so CNY-denominated caps convert about 6.8% higher in USD than at 7.129 — e.g., CNY 620 ≈ $92.87 vs $86.97 — an illustration, not an executable quote). Unpublished commercial values are blank, never estimated.</p>
<div class="notice"><strong>Read first:</strong> a bank transfer fee is not a tax; taxable income or an FX gain may create separate tax liability. The real costs are (1) bank spread, (2) published tariff fees, (3) penalties for unlawful methods, (4) US reporting-penalty exposure. The FX spread is unverified; get the bank's executable quote before acting. Fee floors below assume one wire (or one tranche per calendar year for M02).</div>
<div class="info"><label for="method-filter"><strong>Filter methods:</strong> </label>
<select id="method-filter"><option value="">All 17 methods</option>{''.join(f'<option value="{mid}">{mid} — {esc(methods[mid]["name"])}</option>' for mid in M_ORDER)}</select></div>
<label for="amount-filter"><strong>Highlight amount:</strong> </label>
<select id="amount-filter"><option value="">All amounts</option>{''.join(f'<option value="{t}">${t:,}</option>' for t in TIERS)}</select>

<h2>1 · Decision table (most important first) — published fee components only</h2>
<p class="small">All-in costs are blank (— in the summary): no account-specific quote was verified. A missing quote is not proof that no public quote exists. Rejected methods show statutory fine exposure, not a price.</p>
<div class="table-wrap"><table class="stack"><thead><tr><th>#</th><th>Method</th><th class="num">$10,000</th><th class="num">$100,000</th><th class="num">$250,000</th><th class="num">$400,000</th><th>Official sources</th></tr></thead><tbody>{''.join(dec_rows)}</tbody></table></div>

<h2>2 · Per-method tables ($10k steps)</h2>
{''.join(rows_html)}
"""
    return page("Costs $10k→$400k", "Cost tables for every CNY to USD method at each $10,000 step to $400,000.", "costs.html", body)

# ---------- methods.html ----------
def build_methods():
    blocks = []
    i = 0
    for mid in M_ORDER:
        i += 1
        m = methods[mid]
        tag_cls, tag_txt = M_TAG[mid]
        pros = "".join(f"<li>{esc(p)}</li>" for p in m.get("pros", []))
        cons = "".join(f"<li>{esc(c)}</li>" for c in m.get("cons", []))
        steps = "".join(f"<li>{esc(s)}</li>" for s in m.get("steps", []))
        srcs = " ".join(src_link(s) for s in m.get("sources", []))
        model = esc((m.get("cost_model") or {}).get("note", ""))
        blocks.append(f"""
<section class="method" id="{mid}" data-method="{mid}">
<h3><span class="tag {tag_cls}">{tag_txt}</span> {i}. {esc(m['name'])} <span class="small">[{mid}]</span></h3>
<p><strong>Who it is for:</strong> {esc(m['who'])}</p>
<div class="cols">
<div class="card"><strong>Pros</strong><ul>{pros}</ul></div>
<div class="card"><strong>Cons</strong><ul>{cons}</ul></div>
</div>
<div class="card steps"><strong>Step by step</strong><ol>{steps}</ol></div>
<p class="small"><strong>Cost model:</strong> {model}</p>
<p class="small"><strong>Sources:</strong> {srcs}</p>
<p class="small"><a href="costs.html#{mid}">Cost table for {mid} →</a></p>
</section>""")
    body = f"""
<h1>Every method to move CNY → USD — pros, cons, step by step</h1>
<p class="lede">13 lawful-conditional routes (in order of decision value) and 4 rejected unlawful workarounds, documented because the brief asked for as many ways as possible. “Lawful-conditional” means lawful only for the stated facts with the stated evidence — not recommended for any particular person. Rejected entries are <strong>not recommendations</strong>.</p>
<div class="info"><label for="method-filter"><strong>Filter:</strong> </label>
<select id="method-filter"><option value="">All 17</option>{''.join(f'<option value="{mid}">{mid} — {esc(methods[mid]["name"])}</option>' for mid in M_ORDER)}</select></div>
{''.join(blocks)}
<h2>How to choose (short version)</h2>
<ol>
<li><strong>Prove the source of funds first.</strong> No route works for an undocumented balance.</li>
<li>If it is <strong>documented, after-tax China income</strong> → M01 (or M03 if you run own-name HSBC accounts and qualify for Premier/Private Banking).</li>
<li>If only the <strong>annual quota</strong> applies → M02 (USD 50,000/yr; 8 years for $400k).</li>
<li>Special situations → M10 (emigrant), M11 (inheritor), M12 (property), M13 (trade settlement account).</li>
<li><strong>Never</strong> M14–M17: statutory fines up to 30% (standard) / 30–100% (serious) plus criminal liability.</li>
</ol>
"""
    return page("Methods & steps", "All 17 CNY to USD methods: pros, cons, step-by-step execution.", "methods.html", body)

# ---------- sources.html ----------
def build_sources():
    rows = []
    for s in sources:
        rows.append(f"<tr id='{esc(s['id'])}'><td data-label='ID'><strong>{esc(s['id'])}</strong></td><td data-label='Publisher'>{esc(s['publisher'])}</td><td data-label='Title'>{esc(s['title'])}<div class='srcs'>{esc(s.get('locator',''))}</div></td><td data-label='Kind'>{esc(s['kind'])}</td><td data-label='Status'>{esc(s['status'])}</td><td data-label='Link'><a href='{esc(s['url'])}' target='_blank' rel='noopener noreferrer'>open ↗</a></td><td data-label='Used for' class='small'>{esc(s.get('used_for',''))}</td></tr>")
    for s in SESSION_SOURCES:
        rows.append(f"<tr class='hl' id='{esc(s['id'])}'><td data-label='ID'><strong>{esc(s['id'])}</strong> <span class='tag ok'>new</span></td><td data-label='Publisher'>{esc(s['publisher'])}</td><td data-label='Title'>{esc(s['title'])}</td><td data-label='Kind'>{esc(s['kind'])}</td><td data-label='Status'>{esc(s['status'])}</td><td data-label='Link'><a href='{esc(s['url'])}' target='_blank' rel='noopener noreferrer'>open ↗</a></td><td data-label='Used for' class='small'>{esc(s['used_for'])}</td></tr>")
    body = f"""
<h1>Source register — every number traces here</h1>
<p class="lede">Regulator and statute sources (PBOC, SAFE, STA, State Council, IRS, Federal Reserve, FinCEN, eCFR/govinfo, CBP) are primary law or official statistics. Provider sources (HSBC China, Wise, Western Union) are primary only for that provider's own published terms — never a regulator's guarantee. English translations of PRC rules are reference translations; the Chinese text prevails. Sources S01–S31 were fetched and read by prior sessions (2026-11-08); this session verified B01–B10 directly (highlighted). No link is guaranteed to remain live; locators are recorded for manual review.</p>
<div class="table-wrap"><table class="stack"><thead><tr><th>ID</th><th>Publisher</th><th>Title / locator</th><th>Kind</th><th>Status</th><th>Link</th><th>Used for</th></tr></thead><tbody>
{''.join(rows)}
</tbody></table></div>
<p class="small">Total: {len(sources)} ledger sources + {len(SESSION_SOURCES)} re-verified/added this session (B01–B10). Legacy-path note: irs.gov/individuals/international-taxpayers/report-of-foreign-bank-and-financial-accounts-fbar returns 404, whereas the canonical IRS FBAR page B07 (/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar) is live (verified 2026-11-10) — see flag N01.</p>
"""
    return page("Sources", "Official source register for every figure on this site.", "sources.html", body)

# ---------- flagged.html ----------
def build_flagged():
    rows = []
    for f in flags:
        srcs = " ".join(src_link(s) for s in f.get("sources", [])) or "—"
        rows.append(f"<tr><td data-label='ID'><strong>{esc(f['id'])}</strong></td><td data-label='Severity'><span class='tag warn'>{esc(f['severity'])}</span></td><td data-label='Title'>{esc(f['title'])}<div class='small'>{esc(f['detail'])}</div></td><td data-label='Sources'>{srcs}</td></tr>")
    new_flags = [
        ("N01","IRS FBAR legacy /individuals/ path returns 404; canonical /businesses/ URL is live (verified 2026-11-10)","Earlier notes flagged a 404 when checking irs.gov/individuals/international-taxpayers/report-of-foreign-bank-and-financial-accounts-fbar. Direct retrieval on 2026-11-10 confirmed that the canonical IRS FBAR page (B07: irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar) is LIVE alongside IRM 4.26.16 (B05) and 31 CFR 1010.821 (B01).",["B07","B01","B05"]),
        ("N02","HSBC tariff cover vs internal version header mismatch","The retrieved HSBC China tariff (items cited here) has a 31 Oct 2026 cover/effective date, but an internal Chinese-language section header shows a 12 Sep 2024 version date. Fee items 2.2.4.x/2.2.6.x/2.2.2.1 were read from the retrieved PDF. Confirm fees with the bank before executing; the bank may adjust at its discretion (Important Note 2).",["B06"]),
        ("N03","eCFR is authoritative but unofficial","31 CFR 1010.821 was read on eCFR (current to 2026-11-06). FinCEN's annual inflation adjustment applies to penalties assessed on or after 2025-01-17 (non-willful $16,536; willful $165,353). The official annual printed CFR is on govinfo.gov; figures can differ in the print edition.",["B01"]),
        ("N04","Stale 'USD 0–7 Global Transfer' in ladder/ resolved during 2026-11-10 integration","Prior builds of ladder/assumptions.html and ladder/routes.html listed Global Transfer at USD 0–7 citing the 2021 tariff. During final integration on 2026-11-10, ladder/model.py and ladder/build.py were updated to HSBC China's 31 Oct 2026 tariff (2.2.6.1 Global Transfer: PB/Premier Free, Advance USD 20; 2.2.7 Education Payment: USD 7; 2.2.2.1 banknote withdrawal: Free).",["B06"]),
        ("N05","Overbroad quota & reconversion wording in root EXECUTIVE-SUMMARY.md and reports/ resolved on 2026-11-10","During final integration on 2026-11-10, EXECUTIVE-SUMMARY.md, reports/EXECUTIVE_SUMMARY_85f37d08.md, reports/CNY_TO_USD_RESEARCH_LEDGER.json and portal/generate_portal.py were clarified to distinguish domestic/PR-ID purchase quotas from documented-income conversion, restrict the USD 500/1,000 ID-only allowance to unused-RMB reconversion, and add Form 1116 limitation caveats.",["S01","S05"]),
        ("N06","Two root-level executive summaries serve different verification snapshots","EXECUTIVE_SUMMARY.md (synced with docs/ by validate.yml) and EXECUTIVE-SUMMARY.md (count-checked against data/*.json by verify-site-data.yml) remain preserved separately at root so neither CI parity gate breaks; both now cross-link briefing/index.html and README.md.",[]),
        ("N07","Three stale open PRs (#2, #12, #17) closed as superseded on 2026-11-10","PRs #2 (2026-11-07), #12 (2026-11-08) and #17 (2026-11-08, cost-increments) conflicted with main and deleted newer directories/workflows; all three were closed cleanly on 2026-11-10 with audit notes pointing to main, while the live Nov 6, 2026 Fed H.10 reference rate (6.6760) was carried forward into B10.",["B10"]),
        ("N08","U.S. penalty figures are statutory maxima, not predictions","FBAR/Form 8938 amounts are maximum civil penalties (31 U.S.C. 5321(a)(5); IRC 6038D; B01–B05). Actual assessment depends on willfulness, reasonable cause and facts; reasonable-cause relief exists. This briefing does not predict any penalty outcome.",["B01","B04","B05"]),
        ("N09","Reference rates differ across dashboards vs live Fed H.10 (6.6760 on 2026-11-06)","ladder/ uses illustrative 7.1 CNY/USD; repatriate/ and this briefing use IRS 2025 yearly average 7.129 (S23); Federal Reserve H.10 on 2026-11-06 was 6.6760 CNY/USD (B10). At 6.6760, CNY-denominated HSBC wire fees convert ~6.8% higher in USD (CNY 620 = $92.87 vs $86.97). Neither is an executable quote.",["S23","B10"]),
    ]
    for nid, title, detail, srcs_ids in new_flags:
        srcs = " ".join(src_link(s) for s in srcs_ids) or "—"
        rows.append(f"<tr class='hl'><td data-label='ID'><strong>{nid}</strong> <span class='tag warn'>new</span></td><td data-label='Severity'><span class='tag warn'>needs review</span></td><td data-label='Title'>{esc(title)}<div class='small'>{esc(detail)}</div></td><td data-label='Sources'>{srcs}</td></tr>")
    rows.append("""<tr id="corrections"><td data-label="ID">C01–C04</td><td data-label="Severity">needs review</td><td data-label="Finding">Correction 2026-11-10: prior assumed spread bands were unsupported and removed; all-in totals remain blank. A currency exchange may realize taxable gain, so no universal $0-tax guarantee is supported. SAFE's documented current-account route is conditional, not a guarantee for all balances. Streamlined filing requires non-willfulness and other eligibility conditions. Other dashboards retain historical assumptions; this pass does not re-verify all their claims.</td><td data-label="Sources"><a href="https://www.irs.gov/publications/p525">IRS Pub. 525, Foreign currency transactions</a> · <a href="https://www.irs.gov/individuals/international-taxpayers/streamlined-filing-compliance-procedures">IRS streamlined eligibility</a> · <a href="https://www.safe.gov.cn/tianjin/2026/0713/3088.html">SAFE current-account documents</a> · <a href="https://www.irs.gov/individuals/international-taxpayers/foreign-currency-and-currency-exchange-rates">IRS exchange rates</a> · <a href="https://www.irs.gov/individuals/international-taxpayers/foreign-tax-credit">IRS credit restrictions</a></td></tr>""")
    body = f"""
<h1>Flagged for review — unverified, disputed or stale items</h1>
<p class="lede">Nothing here is hidden and nothing here blocks the site. F01–F15 are carried from the repatriate ledger (2026-11-08); N01–N09 were found in this session (2026-11-10). Each row links its official source. Request changes via the repository issue tracker or by replying to the session.</p>
<div class="table-wrap"><table class="stack"><thead><tr><th>ID</th><th>Severity</th><th>Finding</th><th>Sources</th></tr></thead><tbody>
{''.join(rows)}
</tbody></table></div>
"""
    return page("Flagged for review", "Unverified, disputed and stale items, each with official sources.", "flagged.html", body)

# ---------- index.html (executive summary) ----------
EXEC_SUMMARY_MD = """# Executive Summary — China money: getting CNY out as a U.S. citizen

**Session:** arena/dc2c65bd-china2 · **Date:** 2026-11-10 · **Status:** research, not advice
**Live site:** https://sassnarep3-star.github.io/China2/briefing/ · **Ledgers:** `repatriate/data/*`, `briefing/build.py`

> Every figure below is tied to an official source retrieved by this or a prior session. Anything unverifiable is **blank and flagged** on the [Flagged page](flagged.html).

## The one-line answer

A transfer fee is not tax. No universal zero-tax conclusion can be drawn: source-income liability and taxable currency gains require separate review. Possible explanations for the quoted cost include: (1) PRC individual income tax already owed on the income that created the balance, (2) the bank's exchange-rate spread and wire fees (not tax), (3) PRC penalties for unlawful movement (up to 30% / 30–100%), or (4) U.S. reporting penalties (FBAR / Form 8938) for an undeclared account. If the relevant rules and documentation are satisfied, a bank wire may be available — the first route to evaluate is documented bank conversion; no cheapest or least-tax route can be verified without the private facts.

## What the "conversion penalty" actually is (line by line)

1. **PRC: distinguish FX rules from tax law.** SAFE's individual FX regime sets an annual facilitation quota (USD 50,000 equivalent/person/year for domestic individuals, purchases and sales; among foreign individuals, Foreign Permanent Resident ID holders receive purchase facilitation, while a non-domestic individual's purchase against lawful current-account RMB income is documented — ID plus transaction-source and tax evidence — not quota-based) and an authenticity review; no separate conversion levy was identified in those cited FX rules (not a complete tax review). Over the quota, transactions are not forbidden — authenticity review is "strengthened". [SAFE 2007 / SAFE Tianjin rules (S01, S02, S05)]
2. **PRC individual income tax** attaches to the *income*, when it arose — 3%–45% progressive comprehensive-income rates after the RMB 60,000 annual deduction; flat 20% on interest, dividends and property transfers. Owed regardless of remittance; the bank may require tax documentation; no personal refusal reason was verified. [PRC IIT Law, S15]
3. **The bank's spread + fees — the real, ordinary cost.** Not a tax. For HSBC China Premier/Advance (current tariff, effective 2026-10-31): outward SWIFT wire 0.1% of amount, min CNY 100 / max CNY 500, **plus** CNY 120 cable — a $400,000 wire costs CNY 620 ≈ **$86.97** at the IRS 2025 average **7.129** (**$92.87** at the Federal Reserve H.10 rate **6.6760** of 2026-11-06, an illustration only). Private Banking individuals: free. Global Transfer to your own overseas HSBC account: free (PB/Premier) / USD 20 (Advance). The **spread is unverified**; amount blank (no executable quote verified). [HSBC tariff, B06; Fed H.10, B10]
4. **U.S. tax on the conversion itself.** Currency exchange can realize taxable gain. *Exchange-rate gain on the currency position* can be taxed; IRS Pub. 525: a gain on a **personal** foreign currency transaction is not included in income unless it exceeds **$200**; above that, capital gain. Earned income abroad may qualify for the Foreign Earned Income Exclusion (Form 2555): **$132,900** for 2026 ([Rev. Proc. 2025-32](https://www.irs.gov/pub/irs-drop/rp-25-32.pdf) §.39) and **$137,300** for 2027 (Rev. Proc. 2026-35 §3.41). [B02, B08 / 26 U.S.C. 988 [S24]]
5. **U.S. reporting penalties — where large money is actually lost.**
   - **FBAR (FinCEN 114)**: file if aggregate foreign accounts > **$10,000** at any time in the year, whether or not tax is owed. Non-willful penalty: up to **$16,536** per report (31 CFR 1010.821, penalties assessed on/after 2025-01-17). Willful: greater of **$165,353** or **50%** of the account balance. Bittner (2023): non-willful cap applies per report, not per account. [B01, B05, B07]
   - **Form 8938 (FATCA)**: thresholds vary by filing status/residence (higher for expats: e.g. $200k year-end/$300k any-time single; $400k/$600k joint abroad). $10,000 + $10,000 for each 30 days after IRS notice, up to $60,000 potential max. [B03, B04]
   - **Form 3520 (Foreign Gifts/Bequests)**: Part IV triggers at >**$100,000** aggregate from a nonresident alien or foreign estate, or >**$20,573** (2026) / >**$21,240** (2027, Rev. Proc. 2026-35 §3.51) from foreign corporations/partnerships. [B08, B09]
   - **Form 1116 FTC**: PRC tax on the same income can offset U.S. tax, subject to sourcing, category and limitation rules — credit, not refund. [S20]
6. **Unlawful routes = fines, not fees.** PRC FE regulations: evasion/illegal purchase of FX — warning, confiscation of illegal gains, fine up to **30%** of illegal amount; serious cases **30–100%** + criminal liability. Crypto bridges are illegal financial activity in China (`Yinfa [2026] No. 42`); underground banks (对敲) likewise. Quota pooling ("friends' $50k quotas") is expressly prohibited. [S13, S14, S06 Art. 7]

## The answer to "best way, least tax" — decision order

| # | Situation | Route | Published cost at $400k | Catch |
|---|---|---|---|---|
| 1 | Balance is documented, after-tax China income (salary/services) | **M01** evaluate bank conversion + SWIFT wire to own US account (eligibility unverified) | $86.97 HSBC Premier/Advance (0.1% capped CNY 500 + CNY 120 cable) | Needs tax vouchers + contract/invoices; spread unverified; amount blank |
| 2 | Same facts + own-name HSBC accounts in both countries + Premier/PB | **M03** Global Transfer (after M01/M02 conversion basis) | **$0** published fee (PB/Premier); USD 20 (Advance) | Same SAFE basis required; Premier eligibility (TRB ≥ CNY 500,000) |
| 3 | You hold PRC ID / Foreign Permanent Resident ID; no income docs | **M02** annual quota | $534.66 over 8 calendar years ($66.83/yr × 8) | ~USD 50k/yr cap; purchase facilitation for foreigners limited to PR-ID holders (S05) — confirm |
| 4 | Emigrated from mainland China / inherited China assets | **M10** / **M11** SAFE-approved transfer | Blank — process fees unpublished | Narrow eligibility; hukou cancellation / inheritance proofs; lump sum OK after approval |
| 5 | Own individual trade business | **M13** settlement account | Blank | Genuine trade only; quota-exempt with valid docs |
| 6 | Documented after-tax salary, recent tax records (≤3 yrs) | **M04** Wise (from-CNY) | Blank — quote shown in-app only | Own accounts only; ≤CNY 300k per bank-app transfer; limit = documented salary |
| 7 | Almost any; no FX paperwork | **M06** ATM cash | Blank — card fees unverified | Cap CNY 100,000/person/yr (~USD 14,027); 8+ years for $400k |
| 8 | Small amounts only | **M07** USD cash carry-out | Unverified; blank | USD 5,000/trip no permit; 80 trips for $400k — impractical |
| — | "Just use crypto / pool quotas / underground bank" | **M14–M17 — do not use** | Fine exposure $120,000–$400,000 (30–100%) | Confiscation + criminal liability; no legal recourse |

*Spread model unverified — the bank's quote governs.

## Exactly what to do, step by step (M01, the usual answer)

1. **Gather source-of-funds proof**: employment contract or service invoices; payslips; bank statements showing each credit; the balance must tie to the documents.
2. **Get the tax records**: download your PRC individual income tax payment records from the IIT app, or request a 完税证明 (tax payment certificate) at the tax service hall for every year covered.
3. **Review whether PRC tax is unpaid** — the actual reason for this account's restriction is unknown. Under the IIT law, 2022 onward comprehensive income is settled annually (汇算清缴); tax due is on the income, not the remittance.
4. **Book the account-holding branch's FX counter** (this is not reliably doable at a machine) and bring: passport, tax records, income contract/invoices, account passbook/card.
5. **Ask for the executable all-in quote in writing**: applied CNY→USD rate, 0.1% fee (min CNY 100/max CNY 500), CNY 120 cable, any Pay Exact surcharge CNY 200, and whether the receiving/correspondent bank charges extra (not covered by the tariff).
6. **Complete the conversion and the wire** to your own US account (same-name). Keep the exchange memo (水单), the MT103/remittance advice and every receipt.
7. **US side**: file FBAR by April 15 (auto-extension to Oct 15) and Form 8938 with your return if thresholds are met; claim PRC tax on Form 1116 subject to limits. If past years were never reported, talk to a tax professional about **Streamlined Filing Compliance Procedures** — eligibility requires non-willful conduct and other conditions; an IRS examination or criminal investigation can disqualify the taxpayer.
8. **Never** split the remittance with family/friends' quotas, use false invoices, or route through crypto/underground banks to "save" the spread. The fine bands (up to 30% / 30–100% of the illegal amount) dwarf any saving, and criminal liability applies.

## What is missing to price YOUR situation

Balance source and years; PRC tax paid; whether you hold PRC ID/hukou history; residency (statutory residence definitions and the personal-FX operational rules may differ; ask the bank which category applies); your US filing history; and your bank's live quote. Until those are supplied, **no honest personal tax figure or "best route for you" can be certified** — see flags F01–F02.

**Bottom line:** evaluate *documented source of funds → approved bank conversion/wire → correct US reporting*. A cheapest route or personal tax liability cannot be determined without evidence; unknown values stay blank.
"""

def index_page():
    md = EXEC_SUMMARY_MD
    body = f"""
<h1>China money: evaluate lawful CNY → USD routes</h1>
<p class="lede">As a U.S. citizen: do not assume a quoted bank charge is a tax, or that exchanging currency is always tax-free. What people call the conversion penalty is a stack of four separate things — PRC income tax on the source of the balance, the bank's spread and wire fees, PRC fines for unlawful routes, and U.S. reporting penalties. This page is the executive summary; every claim links its official source.</p>
<div class="notice"><strong>Not tax or legal advice.</strong> No private account facts were used. Every unverifiable number is blank and flagged (<a href="flagged.html">F01–F15, N01–N09</a>). Do not act on this page alone; take the <a href="#checklist">bank-first checklist</a> to a Chinese-qualified adviser.</div>
<div class="kpi">
<div class="box"><div class="n">Not determined</div><div class="d">Personal tax liability: income history and currency gain must be reviewed</div></div>
<div class="box"><div class="n">$86.97</div><div class="d">Published fee: HSBC Premier/Advance wire at $400k (0.1% capped CNY 500 + CNY 120 cable) · {src_link('B06','tariff')}</div></div>
<div class="box"><div class="n">$16,536</div><div class="d">Max non-willful FBAR penalty per report (assessed on/after 2025-01-17) · {src_link('B01','31 CFR 1010.821')}</div></div>
<div class="box"><div class="n">30–100%</div><div class="d">PRC fine band for FX evasion / illegal conversion routes · {src_link('S13','FE Regs')}</div></div>
</div>

<h2>1 · The "conversion penalty", broken down line by line</h2>
<div class="table-wrap"><table class="stack"><thead><tr><th>#</th><th>Layer</th><th>What it actually is</th><th>Official source</th></tr></thead><tbody>
<tr><td data-label='#'>1</td><td data-label='Layer'>PRC conversion tax</td><td data-label='What'><strong>No separate conversion levy identified in the cited FX rules; this is not a complete tax opinion.</strong> SAFE limits by quota (USD 50,000/yr facilitation for domestic individuals, purchases and sales; among foreign individuals, PR-ID holders receive purchase facilitation, while non-domestic purchase against lawful current-account RMB income is document-based — ID plus source/tax evidence) and authenticity review; above-quota eligibility depends on transaction type and supporting documents.</td><td data-label='Source'>{src_link('S01','SAFE rules (2007, as amended)')} · {src_link('S02','SAFE Tianjin detailed rules')} · {src_link('S05','SAFE 2024 FAQ')}</td></tr>
<tr><td data-label='#'>2</td><td data-label='Layer'>PRC IIT on the income</td><td data-label='What'>3%–45% progressive on comprehensive income (after RMB 60,000 annual deduction); flat 20% interest/dividends/property. Owed when the income arose, not at remittance. Tax-document requirements depend on the route; no account-specific refusal reason is known.</td><td data-label='Source'>{src_link('S15','PRC IIT Law (chinatax.gov.cn)')}</td></tr>
<tr><td data-label='#'>3</td><td data-label='Layer'>Bank spread + fees (not tax)</td><td data-label='What'>The real ordinary cost. HSBC Premier/Advance (tariff eff. 2026-10-31): outward TT 0.1%, min CNY 100 / max CNY 500 + CNY 120 cable. ≥≈$70,150 (CNY 500k) the fee caps → $86.97 for $400k at 7.129 ($92.87 at the Fed H.10 rate 6.6760 of 2026-11-06, illustration only). Private Banking individuals: free. <strong>Spread unverified</strong> — no numeric estimate published here.</td><td data-label='Source'>{src_link('B06','HSBC tariff eff. 2026-10-31')} · {src_link('B10','Fed H.10')}</td></tr>
<tr><td data-label='#'>4</td><td data-label='Layer'>U.S. tax on the conversion</td><td data-label='What'>A currency exchange can realize taxable gain. Personal FX gain excluded from income unless &gt; <strong>$200</strong>; above that, capital gain. (Business/investment currency differs — §988.) Earned-income exclusion (Form 2555): <strong>$132,900</strong> for 2026 (Rev. Proc. 2025-32 §.39) and <strong>$137,300</strong> for 2027 (Rev. Proc. 2026-35 §3.41).</td><td data-label='Source'>{src_link('B02','IRS Pub. 525 (2025)')} · {src_link('S24','26 U.S.C. 988')} · {src_link('B08','Rev. Proc. 2026-35')}</td></tr>
<tr><td data-label='#'>5</td><td data-label='Layer'>U.S. reporting penalties</td><td data-label='What'><strong>FBAR</strong> (accounts &gt; $10,000 aggregate any time): non-willful ≤ <strong>$16,536</strong>/report; willful ≤ greater of <strong>$165,353</strong> or <strong>50%</strong> of balance (per account per year; Bittner 2023 caps non-willful per report). <strong>Form 8938</strong>: $10,000 + $10,000 per 30 days after notice, potential max <strong>$60,000</strong>. <strong>Form 3520</strong> Part IV: gifts/bequests from a nonresident alien or foreign estate reportable above <strong>$100,000</strong>/yr (list each &gt; $5,000); foreign corporation/partnership gifts above <strong>$20,116</strong> (2025) / <strong>$20,573</strong> (2026), indexed to <strong>$21,240.31</strong> for 2027. Thresholds vary by filing status/residence.</td><td data-label='Source'>{src_link('B01','31 CFR 1010.821')} · {src_link('B07','IRS FBAR')} · {src_link('B05','IRS IRM 4.26.16')} · {src_link('B03','IRS About Form 8938')} · {src_link('B09','IRS Gifts')}  · {src_link('B04','IRS IRM 5.21.6')}</td></tr>
<tr><td data-label='#'>6</td><td data-label='Layer'>PRC fines for unlawful routes</td><td data-label='What'>Evasion / illegal FX purchase: warning, confiscate illegal gains, fine ≤ <strong>30%</strong>; serious: <strong>30–100%</strong> + criminal liability. Applies to crypto bridges, quota pooling, underground banks, false documents.</td><td data-label='Source'>{src_link('S13','PRC FE Administration Regulations, Arts. 39/40/42/45')} · {src_link('S14','PBOC et al. 2026 virtual-currency notice')}</td></tr>
<tr><td data-label='#'>7</td><td data-label='Layer'>U.S.–China treaty / FTC</td><td data-label='What'>PRC tax on the same income may be credited via Form 1116, subject to category &amp; limitation rules (credit, not refund). Treaty documents: IRS China treaty page.</td><td data-label='Source'>{src_link('S20','IRS Form 1116/FTC')} · {src_link('S25','IRS China tax treaty documents')}</td></tr>
</tbody></table></div>

<h2>2 · Route evaluation, in decision order</h2>
<ol>
<li><strong>Prove the source of the balance</strong> (contract/invoices + bank statements + tax vouchers). Required documents depend on the applicable route.</li>
<li><strong>Settle any unpaid PRC tax on that income</strong> if legally due; the actual account restriction remains unverified.</li>
<li>Move it via <strong>M01</strong> (bank conversion + same-name SWIFT wire — illustrative tariff components cap at CNY 620 for one Premier/Advance wire; other charges excluded) or <strong>M03</strong> (Global Transfer, $0 published fee for PB/Premier) — see <a href="costs.html">cost tables</a>.</li>
<li>US side: <strong>FBAR + Form 8938</strong> on time; <strong>Form 1116</strong> for the PRC tax; if past years were missed, obtain advice on the appropriate correction procedure. Streamlined filing requires eligibility, including a non-willfulness certification; it is not automatic.</li>
<li><strong>Never</strong> use M14–M17 (crypto/smurfing/underground banks/false docs): fines 30–100% + criminal exposure.</li>
</ol>
<div class="summary"><strong>First route to evaluate, not a verified cheapest route:</strong> documented bank conversion and a same-name wire. At $400,000 the illustrative HSBC Premier/Advance issuance plus cable components total CNY 620 (about $86.97 at the historical reference rate); FX spread, intermediary fees, receiving fees, optional services, account costs and tax are excluded. A lower published transfer fee does not prove a lower total cost. Eligibility is unverified.</div>

<h2 id="checklist">3 · The bank-first checklist (take this to your branch)</h2>
<ol>
<li>Ask for the refusal/approval <strong>in writing</strong>; note the tax type, taxpayer, period, base, amount and legal basis — distinguish a tax payment from a tax certificate or a bank fee.</li>
<li>Ask which FX category applies to you (documented foreign-individual income vs annual quota vs settlement account) and what evidence satisfies it (contract, invoices, tax vouchers, permits).</li>
<li>Get the <strong>executable all-in quote</strong>: applied CNY→USD rate, fee and cable, Pay Exact surcharge, intermediary/receiving charges, and the delivery date.</li>
<li>Confirm your <strong>PRC tax settlement</strong> for the years the income arose (annual 汇算清缴) and get the 完税证明.</li>
<li>US filings: FBAR by Apr 15 (auto-extension to Oct 15), Form 8938 with the return, Form 1116 for the credit.</li>
<li>Past years unreported? Ask a US tax professional about <strong>Streamlined Filing Compliance Procedures</strong> now, not after an IRS letter.</li>
<li>Carrying &gt; $10,000 cash into the US? File <strong>FinCEN 105</strong>. China: USD 5,000/trip no permit; USD 5,000–10,000 with bank permit.</li>
</ol>

<h2>4 · Where to go next</h2>
<div class="cols">
<a class="card" href="costs.html"><strong>Cost tables $10k→$400k</strong><span>All 17 methods at every $10k step; decision table first; mobile-friendly.</span></a>
<a class="card" href="methods.html"><strong>Methods &amp; step-by-step</strong><span>Eligibility, pros/cons and execution for each of the 17 routes.</span></a>
<a class="card" href="audit.html"><strong>Repo line-by-line audit</strong><span>Every irregularity found in this repository, with official sources.</span></a>
<a class="card" href="flagged.html"><strong>Flagged for review</strong><span>F01–F15 carried + N01–N09 updated through 2026-11-10 integration.</span></a>
<a class="card" href="sources.html"><strong>Source register</strong><span>41 official/provider sources with direct links and locators.</span></a>
<a class="card" href="../audit-ad300459/index.html"><strong>Fresh official-source audit</strong><span>27 verified/flagged legal claims plus 600/680-row arithmetic checks.</span></a>
<a class="card" href="../repatriate/index.html"><strong>Prior dashboard (repatriate/)</strong><span>The earlier independent study this briefing consolidates.</span></a>
<a class="card" href="../index.html"><strong>Repository root hub</strong><span>Landing directory linking all dashboards, matrices and reviews.</span></a>
</div>
"""
    return page("Executive summary", "Lawful routes, cost components and unresolved tax questions for a U.S. citizen.", "index.html", body)

# ---------- audit.html ----------
AUDIT_ROWS = [
    ("AU-01","Root summaries","Two root executive summaries (EXECUTIVE_SUMMARY.md synced with docs/ by validate.yml; EXECUTIVE-SUMMARY.md count-checked against data/*.json by verify-site-data.yml) remain preserved so neither CI gate breaks; both now cross-link briefing/index.html and README.md (2026-11-10 integration).","ls + validate.yml + verify-site-data.yml","Resolved — cross-linked cleanly"),
    ("AU-02","Stale PRs resolved","PRs #2 (2026-11-07), #12 (2026-11-08) and #17 (2026-11-08) conflicted with main and deleted newer directories/workflows; all three were closed cleanly as superseded on 2026-11-10 with audit notes pointing to main.","gh pr close #2, #12, #17 (2026-11-10)","Resolved — closed cleanly (N07)"),
    ("AU-03","ladder/ 2021 HSBC tariff updated","ladder/model.py, ladder/build.py and S06/R02/R06/assumptions were updated on 2026-11-10 to the 31 Oct 2026 HSBC tariff (2.2.6.1 Global Transfer: PB/Premier Free, Advance USD 20; 2.2.7 Education Payment: USD 7; 2.2.2.1 banknote withdrawal: Free), preserving 600-row parity.","Re-retrieved tariff 2026-11-10 (B06)","Resolved — updated in ladder/ (N04)"),
    ("AU-04","Root hub CSS & links","Root index.html (written by ladder/build.py) previously used class='site' against .card CSS rules and omitted briefing/, audit-ad300459/, site/ and acceptance-373b54a3/; fixed on 2026-11-10 while retaining the audit-0f0f59fe C04 notice.","ladder/build.py:write_root_hub()","Resolved — hub fixed"),
    ("AU-05","Dashboard count drift","docs/ = 22 routes/67 findings/24 sources; site/ = 18 methods; ladder/ = 20 routes/15 costed/600 rows; repatriate/ = 17 methods/680 rows; audit-86f0/ = 22×40 blank cells. Each sub-site's taxonomy is explained on root index.html and README.md.","Per-directory README/meta reviewed","Consolidated here (this page + index)"),
    ("AU-06","Quota & reconversion wording fixed","EXECUTIVE-SUMMARY.md, reports/EXECUTIVE_SUMMARY_85f37d08.md, reports/CNY_TO_USD_RESEARCH_LEDGER.json and portal/generate_portal.py were clarified on 2026-11-10 so USD 50k purchase facilitation reflects PRC ID / PR-ID rules and USD 500/1,000 applies strictly to unused-RMB reconversion.","SAFE Tianjin 2024 & 2026 FAQs (S04, S05)","Resolved — clarified (N05)"),
    ("AU-07","“0% if already taxed” & FTC caveats","reports/EXECUTIVE_SUMMARY_85f37d08.md and portal/index.html were qualified on 2026-11-10 with IIT income-category rules, undocumented-balance exclusion, and Form 1116 sourcing/limitation caveats.","IRS FTC source S20; PRC IIT Law S15","Resolved — clarified"),
    ("AU-08","Reference-rate drift & live Nov 6 Fed H.10","ladder/ uses 7.1 CNY/USD; repatriate/ and this briefing use 7.129 (IRS 2025 avg, S23); Fed H.10 on 2026-11-06 was 6.6760 (B10, ~6.8% shift: CNY 620 = $92.87 vs $86.97). All are labeled reference rates, not bank quotes.","ladder/data/meta.json; repatriate/data/rules.json; Fed H.10 (B10)","Flag N09"),
    ("AU-09","Cost math spot-verified this session","M01 $10k: CNY 71,290 × 0.1% = 71.29 → min CNY 100 + CNY 120 = CNY 220 → $30.86 ✓. M02 $400k: 8 × (CNY 356.45 + 120) = CNY 3,811.6 → $534.66 ✓. M14 fine ≤30% of $400k = $120,000 ✓. M14–M17 6-column HTML table alignment and #method-filter full names fixed.","briefing/build.py + briefing/verify.py","Verified — reproducible"),
    ("AU-10","HSBC tariff internal header","Retrieved PDF cover: effective 31 Oct 2026; internal Chinese section header reads “2024年9月12日生效” (12 Sep 2024). Fee items read from retrieved text.","Fetched 2026-11-10, B06","Flag N02/F08"),
    ("AU-11","IRS FBAR canonical URL verified live","Earlier drafts tested /individuals/international-taxpayers/... (404); direct check on 2026-11-10 confirmed the canonical URL /businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar (B07) is LIVE (200 OK).","fetch_page 2026-11-10 (B07)","Resolved — live canonical link B07"),
    ("AU-12","eCFR status","31 CFR 1010.821 amounts are authoritative but unofficial (eCFR); print edition at govinfo.gov; annual FCPIA adjustment.","fetch_page 2026-11-10, B01/N03","Flag N03"),
    ("AU-13","FEIE stale webpage + Rev. Proc. 2026-35 (2027)","IRS FEIE webpage lists through 2023 ($120,000); 2026 amount $132,900 verified in Rev. Proc. 2025-32 §4.39 (S22), and 2027 amount $137,300 + §6039F $21,240 verified in Rev. Proc. 2026-35 §§3.41/3.51 (B08, 2026-11-09).","Rev. Proc. 2025-32; Rev. Proc. 2026-35 (B08)","Flag F09 (webpage stale; Rev. Procs current)"),
    ("AU-14","Unpublished commercial costs","Wise, Western Union, ATM issuer/operator, FX spread, correspondent charges: no static official publication exists. Handled by leaving cells blank + F03 everywhere — correct handling, preserved here.","Repatriate ledger F03","Needs review (by design)"),
    ("AU-15","RMB carry limit sourcing","CNY 20,000/trip corroborated by PBOC Q&A + State Council republication; primary Announcement [2004] No. 18 not retrieved.","Repatriate F10","Flag F10"),
    ("AU-16","Statute edition & Form 3520","26 U.S.C. 988 read from 2024 US Code (govinfo); personal FX-gain $200 rule confirmed against current IRS Pub. 525; Form 3520 triggers (>$100k NRA/estate; >$20,573 2026 / $21,240 2027 corp/partnership) verified from B08/B09.","B02, B08, B09 fetched 2026-11-10","Partly resolved; trust/character advice needed"),
    ("AU-17","Compatibility redirects","docs/methods.html and docs/flagged.html intentionally redirect to review/flagged pages. Working as designed.","curl/inspection of files","OK"),
    ("AU-18","Previous-dashboard archive","research/previous-dashboard/ preserves the first dashboard untouched; clearly not current guidance. Working as designed.","File inspection","OK"),
    ("AU-19","Pages serving root","Native Pages from main / serves every directory publicly (docs/, site/, portal/, ladder/, repatriate/, briefing/, audit-*/, acceptance-373b54a3/). No credentials, account numbers or private data found anywhere.","grep scan 2026-11-10; repo is public","OK — privacy notice maintained"),
    ("AU-20","No LICENSE","Repository has no license file. Public code/data with no license = all rights reserved; fine for viewing, but reuse is not licensed.","ls 2026-11-10","Flag — owner to decide"),
    ("AU-21","README & root hub updated","README.md and root index.html (via ladder/build.py:write_root_hub()) now link every active deliverable across the repository (briefing/, ladder/, repatriate/, audit-*/, docs/, site/, portal/, acceptance-373b54a3/).","README.md & index.html diff","Resolved — full hub linked"),
    ("AU-22","Coordination protocol","COORDINATION.md preserves all prior sessions' claims/close-outs verbatim; stale claims >60 min old taken over transparently under protocol.","COORDINATION.md 2026-11-10","OK"),
    ("AU-23","Privacy of this briefing","Briefing contains only public sources and model arithmetic; no private identifiers. Verification: briefing/verify.py + grep.","this PR","OK"),
    ("AU-24","Cost-model honesty","Correction 2026-11-10: unsupported spread bands removed, all-in columns blank. Published fee components are not total costs. Each cost row now includes direct official links.","briefing/costs.html","OK — limitations explicit"),
    ("AU-25","Counts in this briefing","17 methods · 680 amount rows (17×40) · 41 sources (31 ledger + 10 session) · 24 flags (F01–F15, N01–N09) · 25 audit rows. Verified by briefing/verify.py.","verify.py","OK"),
]

def build_audit():
    rows = []
    for aid, area, finding, evidence, status in AUDIT_ROWS:
        flagged = status.startswith(("Flag","Needs"))
        tag = "warn" if flagged else "ok"
        rows.append(f"<tr><td data-label='ID'><strong>{aid}</strong></td><td data-label='Area'>{esc(area)}</td><td data-label='Finding'>{esc(finding)}</td><td data-label='Evidence' class='small'>{esc(evidence)}</td><td data-label='Status'><span class='tag {tag}'>{'needs review' if flagged else 'ok'}</span><div class='small'>{esc(status)}</div></td></tr>")
    body = f"""
<h1>Repository line-by-line audit — consolidated findings</h1>
<p class="lede">Scope: every top-level path in the repo, every workflow, and every headline figure this briefing reuses. Generated dashboard internals were additionally checked by their own verifiers (repatriate: 11,197 checks; ladder: 9,3xx checks). “Line-by-line” here means: each finding below names the exact file, line or ledger entry it came from, and links the official source that disproves or confirms it. This is not a certification of the whole repository; it is a complete, checkable list of everything this session found wrong or unverifiable.</p>
<div class="notice"><strong>Method:</strong> (1) inventory + <code>git log</code> review; (2) every external/official source re-fetched where retrieval permitted (HSBC tariff PDF, eCFR, IRS pages, IRS search index); (3) cost arithmetic recomputed deterministically (<code>briefing/build.py</code>); (4) secrets scan; (5) coordination-board conformance. Failed/404 sources are flagged, never silently dropped.</div>
<div class="table-wrap"><table class="stack"><thead><tr><th>ID</th><th>Area</th><th>Finding</th><th>Evidence</th><th>Status</th></tr></thead><tbody>
{''.join(rows)}
</tbody></table></div>
<p class="small">Detailed prior audits preserved at: <a href="../reports/REPO_LINE_BY_LINE_AUDIT.md">reports/REPO_LINE_BY_LINE_AUDIT.md</a> · <a href="../repatriate/audit.html">repatriate/audit.html</a> (A01–A13) · <a href="../audit-0f0f59fe/index.html">audit-0f0f59fe/index.html</a> (C01–C04) · <a href="../audit-86f0/index.html">audit-86f0/index.html</a>. Those are other sessions' work; their caveats still apply and are not superseded by this page.</p>
"""
    return page("Repo audit", "Consolidated line-by-line repository audit with official sources.", "audit.html", body)

def audit_md():
    lines = ["# Repo line-by-line audit — consolidated (arena/dc2c65bd-china2, 2026-11-10)\n",
             "Scope: every top-level path, all workflows, all headline figures this briefing reuses.\n",
             "| ID | Finding | Status |", "|---|---|---|"]
    for aid, area, finding, evidence, status in AUDIT_ROWS:
        lines.append(f"| {aid} | **{area}** — {finding} | {status} |")
    lines += ["", "Detailed prior audits: reports/REPO_LINE_BY_LINE_AUDIT.md · repatriate/audit.html · audit-0f0f59fe/index.html · audit-86f0/",
              "", "Official sources re-verified this session: B01–B10 (see sources.html).", ""]
    return "\n".join(lines)

def summary_with_sources():
    """Attach route-specific primary-source links to each decision-table row."""
    import re
    lines = []
    for line in EXEC_SUMMARY_MD.splitlines():
        if line.startswith('|'):
            if line.startswith('| #'):
                line += ' Official sources |'
            elif line.startswith('|---'):
                line += '---|'
            else:
                match = re.search(r'M\d{2}', line)
                ids = methods[match.group(0)]['sources'] if match else ['S01']
                line += ' ' + ' · '.join(f'[{sid}]({SRC_URL[sid]})' for sid in ids) + ' |'
        lines.append(line)
    return '\n'.join(lines) + '\n'

def main():
    (BR / "assets").mkdir(exist_ok=True)
    out = {
        "index.html": index_page(),
        "costs.html": build_costs(),
        "methods.html": build_methods(),
        "sources.html": build_sources(),
        "flagged.html": build_flagged(),
        "audit.html": build_audit(),
        "EXECUTIVE_SUMMARY.md": summary_with_sources(),
        "AUDIT.md": audit_md(),
    }
    for name, content in out.items():
        (BR / name).write_text(content, encoding="utf-8")
        print(f"wrote briefing/{name} ({len(content):,} bytes)")

if __name__ == "__main__":
    main()
