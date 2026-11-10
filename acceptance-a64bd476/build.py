#!/usr/bin/env python3
"""Generate acceptance pages from findings.json / sources.json / checks.json.
Deterministic: same inputs -> same bytes. Run verify.py first for checks.json.
"""
import html, json
from pathlib import Path

ACC = Path(__file__).resolve().parent
findings = json.load(open(ACC / "findings.json"))["findings"]
sources = json.load(open(ACC / "sources.json"))["sources"]
checks = json.load(open(ACC / "checks.json")) if (ACC / "checks.json").exists() else {"checks_run": 0, "failures": ["checks.json missing — run verify.py first"], "html_pages_crawled": 0}
src = {s["id"]: s for s in sources}

def esc(s): return html.escape(str(s), quote=True)

NAV = [("index.html", "Acceptance home"), ("findings.html", "Findings"),
       ("sources.html", "Sources"), ("checks.html", "Structural checks"),
       ("flagged.html", "Flagged for Review")]

def page(title, body):
    nav = "".join(f'<a href="{h}">{esc(t)}</a>' for h, t in NAV)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · China money acceptance audit</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<header><strong>China money · acceptance audit</strong><p>Session arena/a64bd476-china2 · re-verified 10 November 2026 · research, not tax or legal advice</p></header>
<nav>{nav}</nav>
<main>
{body}
</main>
<footer><p>Research, not advice. No private account facts entered, no bank contacted, no funds moved, no tax return filed. Unverified values are blank and flagged.</p>
<p><a href="../index.html">Landing hub</a> · <a href="../briefing/index.html">Executive briefing</a> · <a href="../briefing/costs.html">Cost tables $10k–$400k</a> · <a href="../briefing/flagged.html">Briefing flags</a></p></footer>
<script src="app.js"></script>
</body>
</html>
"""

def src_link(sid):
    s = src.get(sid)
    if not s: return "— (blank, unverified)"
    return f'<a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">{esc(s["publisher"])}</a>'

# index
n_ver = sum(1 for f in findings if f["status"] == "verified")
n_lim = sum(1 for f in findings if f["status"] == "verified-limited")
n_unv = sum(1 for f in findings if f["status"] == "unverified-blank")
index_body = f"""
<h1>Acceptance audit: what was freshly re-verified, what stays blank</h1>
<p class="lede">This session re-fetched six official sources on 10 November 2026 and re-checked the published cost tables arithmetically. It does not re-verify every inherited claim in the repository, and it does not compute a personal tax bill.</p>
<div class="status">
  <div class="status-card"><p class="label">Findings verified</p><p class="value">{n_ver}</p><p class="small">Confirmed in official text retrieved this session.</p></div>
  <div class="status-card"><p class="label">Verified-limited</p><p class="value">{n_lim}</p><p class="small">Confirmed with a stated limit.</p></div>
  <div class="status-card"><p class="label">Unverified-blank</p><p class="value">{n_unv}</p><p class="small">Left blank by design; see Flagged for Review.</p></div>
  <div class="status-card"><p class="label">Structural checks</p><p class="value">{checks['checks_run']}</p><p class="small">{len(checks['failures'])} failures · {checks['html_pages_crawled']} pages crawled.</p></div>
</div>
<div class="notice"><strong>Bottom line for a U.S. citizen with CNY in China:</strong> the lawful path is documentation-first — prove the source of the balance, settle any PRC tax on the income that created it, then convert and wire through the bank. There is no separate PRC tax on the act of exchanging currency in the SAFE guidance retrieved, but that is not a guarantee of no taxable income or currency gain on the U.S. side. Published HSBC wire fees are small (see Findings A05); the unpublished spread and the paperwork are the real costs. Your exact tax and all-in cost remain blank until the bank quotes and your facts are known.</div>
<h2>Start here</h2>
<div class="grid">
<a class="card" href="findings.html"><strong>Findings</strong><span>Every claim with its official source link</span></a>
<a class="card" href="sources.html"><strong>Sources</strong><span>What was actually retrieved this session</span></a>
<a class="card" href="checks.html"><strong>Structural checks</strong><span>Links, fragments, row counts, fee arithmetic</span></a>
<a class="card" href="flagged.html"><strong>Flagged for Review</strong><span>Blanks, limits and irregularities</span></a>
<a class="card" href="../briefing/index.html"><strong>Executive briefing</strong><span>Least-tax path, decision order, bank checklist</span></a>
<a class="card" href="../briefing/costs.html"><strong>Cost tables $10k–$400k</strong><span>17 methods × 40 tiers, mobile-friendly</span></a>
</div>
"""
(ACC / "index.html").write_text(page("Acceptance home", index_body))

# findings
rows = ""
for f in findings:
    rows += (f'<tr><td data-label="ID">{esc(f["id"])}</td><td data-label="Claim">{esc(f["claim"])}<br><span class="small">{esc(f["detail"])}</span></td>'
             f'<td data-label="Status">{esc(f["status"])}</td><td data-label="Locator">{esc(f["locator"]) or "—"}</td>'
             f'<td data-label="Official source">{src_link(f["source_id"])}</td></tr>\n')
findings_body = f"""
<h1>Findings (fresh pass, 10 November 2026)</h1>
<p>Every verified row links to an official source retrieved this session. Unverified rows are blank by design.</p>
<div class="table-wrap"><table class="stack"><thead><tr><th>ID</th><th>Claim</th><th>Status</th><th>Locator</th><th>Official source</th></tr></thead><tbody>
{rows}</tbody></table></div>
"""
(ACC / "findings.html").write_text(page("Findings", findings_body))

# sources
srows = ""
for s in sources:
    srows += (f'<tr><td data-label="ID">{esc(s["id"])}</td><td data-label="Publisher">{esc(s["publisher"])}</td>'
              f'<td data-label="Title">{esc(s["title"])}<br><span class="small">{esc(s["used_for"])}</span></td>'
              f'<td data-label="Status">{esc(s["status"])}</td>'
              f'<td data-label="Link"><a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">{esc(s["url"])}</a></td></tr>\n')
sources_body = f"""
<h1>Sources retrieved this session</h1>
<p>Only sources actually fetched on 10 November 2026 are listed. Carried prior-session sources are not presented as fresh.</p>
<div class="table-wrap"><table class="stack"><thead><tr><th>ID</th><th>Publisher</th><th>Title / use</th><th>Status</th><th>Link</th></tr></thead><tbody>
{srows}</tbody></table></div>
"""
(ACC / "sources.html").write_text(page("Sources", sources_body))

# checks
fails = checks["failures"]
fail_rows = "".join(f"<li>{esc(x)}</li>" for x in fails) if fails else "<li>None.</li>"
checks_body = f"""
<h1>Structural checks</h1>
<p>{checks['checks_run']} checks run; {len(fails)} failures. These establish link integrity, row counts and fee arithmetic only — not legal correctness or personal eligibility.</p>
<ul>{fail_rows}</ul>
<h2>What was checked</h2>
<ul>
<li>Findings/sources schema; every verified finding has an official (.gov/.gov.cn/bank) URL.</li>
<li>Repo crawl: every HTML page parses; local links and fragments resolve; viewport meta present; no dev-server references.</li>
<li>HSBC M01 fee recomputed from tariff formula at 7.129 for all 40 tiers vs repatriate CSV; $10,000 → $30.86, $400,000 → $86.97.</li>
<li>Row counts: briefing 680, repatriate CSV 680, ladder costs.json 600; tiers $10k–$400k step $10k.</li>
</ul>
"""
(ACC / "checks.html").write_text(page("Structural checks", checks_body))

# flagged
flagged_body = """
<h1>Flagged for Review</h1>
<p>These items are published here rather than filled in by inference. They do not block publication.</p>
<div class="table-wrap"><table class="stack"><thead><tr><th>ID</th><th>Item</th><th>Why it is flagged</th><th>Source / link</th></tr></thead><tbody>
<tr><td data-label="ID">G01</td><td data-label="Item">Pub. 525 $200 personal-FX figure</td><td data-label="Why">Table of contents retrieved this session; the specific $200 text was not re-read. Figure is carried from prior sessions, not freshly verified here.</td><td data-label="Source"><a href="https://www.irs.gov/publications/p525" target="_blank" rel="noopener noreferrer">IRS Pub. 525 (2025)</a></td></tr>
<tr><td data-label="ID">G02</td><td data-label="Item">HSBC tariff version header</td><td data-label="Why">Cover states effective 31 Oct 2026; an internal Chinese section header shows 2024-09-12. Fee items cited were read in the 2026-effective document.</td><td data-label="Source"><a href="https://www.hsbc.com.cn/content/dam/hsbc/cn/docs/document-download/tariff-of-Accounts-services-for-personal-customers-v2.pdf" target="_blank" rel="noopener noreferrer">HSBC tariff (eff. 31 Oct 2026)</a></td></tr>
<tr><td data-label="ID">G03</td><td data-label="Item">Spread bands and 7.129 illustrations</td><td data-label="Why">Modelled spreads (e.g. 0.30–1.50%) are assumptions, not published quotes. 7.129 is the IRS 2025 yearly average, not an executable bank rate. All-in costs remain blank.</td><td data-label="Source"><a href="https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates" target="_blank" rel="noopener noreferrer">IRS yearly average rates</a></td></tr>
<tr><td data-label="ID">G04</td><td data-label="Item">Landing-hub briefing links (PR #30 pending)</td><td data-label="Why">On main at claim time, the root hub did not yet link the briefing. PR #30 (arena/e62a2cd8-china2) integrates those links; this session did not edit the generator-owned hub.</td><td data-label="Source"><a href="https://github.com/sassnarep3-star/China2/pull/30" target="_blank" rel="noopener noreferrer">PR #30</a></td></tr>
<tr><td data-label="ID">G05</td><td data-label="Item">Personal tax / best route / all-in cost</td><td data-label="Why">Source of funds, residency, account type and filing history unknown. Values intentionally blank (Findings A09–A10).</td><td data-label="Source">— (no source can confirm unknown private facts)</td></tr>
</tbody></table></div>
"""
(ACC / "flagged.html").write_text(page("Flagged for Review", flagged_body))
print("built acceptance pages")
