#!/usr/bin/env python3
"""Build the audit-ad300459 verification pages from findings.json (deterministic)."""
from __future__ import annotations

import csv
import html
import json
import os

import checks

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "findings.json")

CSS = """
:root{color-scheme:light;--ink:#15221d;--muted:#5a6b63;--line:#dbe3dd;--bg:#f4f6f3;--card:#fff;
--ok:#0d6b3f;--ok-bg:#e5f4ea;--lim:#8a5200;--lim-bg:#fff2d9;--bad:#a3282a;--bad-bg:#fdeaea;
--link:#0a5ea6;--accent:#0b705e}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
header{background:#122620;color:#f2f6f3;padding:.9rem clamp(1rem,4vw,2.2rem)}
header strong{font-size:1.05rem}
header p{margin:.15rem 0 0;color:#b9cfc5;font-size:.8rem}
main{max-width:1120px;margin:0 auto;padding:clamp(1rem,3.5vw,2.2rem) clamp(.85rem,3.5vw,2rem) 3rem}
h1{font-size:clamp(1.55rem,4.6vw,2.35rem);line-height:1.12;letter-spacing:-.02em;margin:.3rem 0 .55rem}
h2{margin:2rem 0 .6rem;font-size:clamp(1.15rem,3vw,1.45rem)}
h3{margin:1.2rem 0 .4rem;font-size:1rem}
.lede{color:#33473e;max-width:78ch}
.nav{display:flex;flex-wrap:wrap;gap:.5rem;margin:.9rem 0}
.nav a{background:#fff;border:1px solid var(--line);border-radius:999px;padding:.38rem .8rem;
text-decoration:none;color:var(--ink);font-size:.86rem;font-weight:650}
.nav a:hover{border-color:var(--accent)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:.7rem;margin:1rem 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:.8rem .9rem}
.card .k{font-size:1.6rem;font-weight:800;margin:.1rem 0}
.card .l{font-size:.74rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin:0}
.card .s{font-size:.8rem;color:var(--muted);margin:.2rem 0 0}
.k.ok{color:var(--ok)}.k.lim{color:var(--lim)}.k.bad{color:var(--bad)}
.notice{background:var(--lim-bg);border:1px solid #ecd4a0;border-left:5px solid #b07b17;
border-radius:10px;padding:.8rem .95rem;margin:1rem 0;font-size:.92rem}
.summary{background:var(--card);border:1px solid var(--line);border-left:5px solid var(--accent);
border-radius:12px;padding:.85rem 1rem;margin:1rem 0}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch;background:var(--card);
border:1px solid var(--line);border-radius:12px;margin:.8rem 0}
table{border-collapse:collapse;width:100%;font-size:.9rem;min-width:640px}
th,td{border-bottom:1px solid var(--line);padding:.55rem .6rem;text-align:left;vertical-align:top}
th{background:#eef3ef;font-size:.78rem;text-transform:uppercase;letter-spacing:.04em;color:#3c544a}
tr:last-child td{border-bottom:none}
td.id{font-weight:750;white-space:nowrap}
a{color:var(--link)}
.src{font-size:.86rem;word-break:break-word}
.badge{display:inline-block;border-radius:999px;padding:.12rem .55rem;font-size:.74rem;font-weight:750;white-space:nowrap}
.b-ok{background:var(--ok-bg);color:var(--ok)}
.b-lim{background:var(--lim-bg);color:var(--lim)}
.b-bad{background:var(--bad-bg);color:var(--bad)}
.note{font-size:.84rem;color:#41564c;margin:.25rem 0 0}
.refs{font-size:.78rem;color:var(--muted);margin:.2rem 0 0;word-break:break-word}
details{margin:.35rem 0}
summary{cursor:pointer;font-size:.84rem;color:var(--link)}
.quote{font-size:.83rem;background:#f2f5f2;border-left:3px solid var(--accent);
padding:.5rem .65rem;border-radius:6px;margin:.35rem 0;white-space:pre-wrap;word-break:break-word}
.flag{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:.85rem 1rem;margin:.7rem 0}
.flag h3{margin:.15rem 0 .3rem}
.checks li{margin:.28rem 0;font-size:.92rem}
.checks .pass{color:var(--ok);font-weight:750}
footer{background:#122620;color:#cfe0d8;padding:1.2rem clamp(1rem,4vw,2.2rem);font-size:.84rem}
footer a{color:#9fd9c4}
@media (max-width:720px){
 table,thead,tbody,tr,th,td{display:block}
 thead{display:none}
 .scroll{border:none;background:transparent}
 tr{background:var(--card);border:1px solid var(--line);border-radius:12px;margin:.6rem 0;padding:.35rem .2rem}
 td{border-bottom:1px dashed var(--line);padding:.42rem .6rem}
 td:last-child{border-bottom:none}
 td::before{content:attr(data-label);display:block;font-size:.68rem;text-transform:uppercase;
 letter-spacing:.05em;color:var(--muted);font-weight:750;margin-bottom:.1rem}
 td.id::before{display:none}
}
@media print{header,footer{background:#fff;color:#000}.nav{display:none}}
"""

VERDICT_BADGE = {
    "verified": ("b-ok", "VERIFIED"),
    "verified-limited": ("b-lim", "VERIFIED · LIMITED"),
    "unverified": ("b-bad", "UNVERIFIED · BLANK"),
}


def load():
    with open(LEDGER, encoding="utf-8") as fh:
        return json.load(fh)


def esc(s):
    return html.escape(str(s), quote=True)


def page(title, body, desc):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<style>{CSS}</style>
</head>
<body>
<header><strong>China money · independent verification (audit-ad300459)</strong>
<p>Session arena/ad300459-china2 · sources re-fetched 2026-11-10 · research verification, not tax or legal advice</p></header>
<main>
{body}
</main>
<footer>Every verified row below links the official document re-read in this session. Blank = unverified, never inferred.
No personal account facts were used. <a href="../index.html">Project hub</a> ·
<a href="findings.html">Findings</a> · <a href="flagged.html">Flagged</a> ·
<a href="../COORDINATION.md">Task board</a></footer>
</body>
</html>
"""


def nav(active):
    items = [
        ("index", "Summary", "index.html"),
        ("findings", "Findings", "findings.html"),
        ("sources", "Sources", "sources.html"),
        ("ladder-check", "Ladder check", "ladder-check.html"),
        ("flagged", "Flagged", "flagged.html"),
    ]
    parts = []
    for key, label, href in items:
        cur = ' aria-current="page"' if key == active else ""
        parts.append(f'<a href="{href}"{cur}>{label}</a>')
    return f'<nav class="nav" aria-label="Pages">{"".join(parts)}</nav>'


def verdict_counts(findings):
    out = {"verified": 0, "verified-limited": 0, "unverified": 0}
    for f in findings:
        out[f["verdict"]] += 1
    return out


def build_index(d):
    findings, sources, flags = d["findings"], d["sources"], d["flags"]
    c = verdict_counts(findings)
    layers = [
        ("1 · FX spread / executable rate",
         "No official source publishes a customer spread — BLANK", "V25", "bad"),
        ("2 · Bank transfer fee (published example)",
         "HSBC China: 0.1% (min CNY 100, max CNY 500) + CNY 120 cable, eff. 31 Oct 2026", "V24", "ok"),
        ("3 · Intermediary / beneficiary bank fees",
         "Excluded from the tariff; not published anywhere official — BLANK", "V26", "bad"),
        ("4 · PRC tax",
         "No conversion tax located in reviewed instruments; income taxed 3%–45% / 20%", "V16 · V14", "ok"),
        ("5 · US tax",
         "Worldwide taxation; personal FX gain exempt ≤ $200 (§988(e)); FTC/FEIE available", "V17 · V18 · V21", "ok"),
        ("6 · Cross-border reporting",
         "FBAR > $10k aggregate; Form 8938 thresholds; FinCEN 105 for >$10k cash", "V19 · V20 · V23", "ok"),
        ("7 · Control-violation penalties",
         "PRC fines up to 30% (30%–$400k = $120k illustration); unlicensed FX business CNY 0.5–2M", "V12 · V07", "lim"),
    ]
    rows = "".join(
        f'<tr><td data-label="Layer"><strong>{esc(name)}</strong></td>'
        f'<td data-label="What the fetched sources establish">{esc(what)}</td>'
        f'<td data-label="Finding" class="id"><a href="findings.html#{fid.split()[0]}">{esc(fid)}</a></td></tr>'
        for name, what, fid, _tone in layers
    )
    body = f"""{nav("index")}
<h1>Fresh official-source verification of the CNY → USD claims</h1>
<p class="lede">This pass re-read {len(sources)} official and primary documents end to end during this session and
checked {len(findings)} published claims line by line against them. Anything that could not be confirmed
from a fetched source is left blank and flagged ({len(flags)} flags) — never filled in by inference.</p>
<div class="cards">
  <article class="card"><p class="l">Verified</p><p class="k ok">{c["verified"]}</p><p class="s">claim matches fetched text</p></article>
  <article class="card"><p class="l">Verified · limited</p><p class="k lim">{c["verified-limited"]}</p><p class="s">holds only with stated scope caveats</p></article>
  <article class="card"><p class="l">Unverified · blank</p><p class="k bad">{c["unverified"]}</p><p class="s">no official source — blank + flagged</p></article>
  <article class="card"><p class="l">Flags open</p><p class="k">{len(flags)}</p><p class="s">needs review, published openly</p></article>
</div>
<div class="notice"><strong>Most important limits:</strong> no live FX spread or executable rate was verifiable
(FL01/FL08); the user's source of funds, residence duration and tax history are unknown, so no personalized
tax, eligibility or all-in cost is computed anywhere here (FL05). Modeled ladders elsewhere in the repo remain
scenarios, not quotes. Ladder structure/arithmetic was independently re-checked —
<a href="ladder-check.html">600 + 680 rows</a> — that check does not validate real-world meaning.</div>
<h2>Conversion-penalty breakdown — most important first</h2>
<div class="scroll"><table>
<thead><tr><th>Penalty layer</th><th>What the fetched official sources establish</th><th>Finding</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<div class="summary"><h3 style="margin-top:0">Best lawful path supported by the fetched text (not personalized advice)</h3>
<p>1) Establish lawful source of funds and PRC tax documentation (V03 — Art. 59 purchase against source
materials incl. tax voucher). 2) Confirm your PRC classification: ≥1 year continuous residence = domestic
individual with the USD 50,000 annual facility, below that = overseas individual converting against income
documents (V02, V01, V03). 3) Remit outward with the bank: account FX for overseas individuals needs ID only
(V05); keep every remittance inside the same documented purpose (V07). 4) Expect tax to attach to income
(3%–45% PRC; worldwide US taxation with FTC/§988(e) relief), never to the conversion act itself (V14, V16,
V17, V18). 5) Get a current executable all-in quote — spread and intermediary fees are the only large
unverified cost layers (V25, V26). 6) Never split transactions to dodge thresholds — watch-list on the PRC
side, structuring rules on the US side (V07, V23).</p></div>
<h2>How this was verified</h2>
<p class="note">Sources were fetched live on 2026-11-10 from official government publishers (SAFE, State Council
Gazette, STA, IRS, eCFR, govinfo, CBP) plus two primary non-government documents explicitly labelled as such
(HSBC China tariff; US treaty PDF hosted by IRS). Each finding row names the exact article/section read.
Structural validators elsewhere in this repo prove links and arithmetic — this pass additionally re-read the
law text itself. <a href="sources.html">Open the source register →</a></p>
"""
    return page("China money · independent verification summary", body,
                "Source-linked verification of CNY-to-USD repatriation claims: verdict counts, conversion-penalty layers, limits.")


def build_findings(d):
    findings, sources = d["findings"], d["sources"]
    by_id = {s["id"]: s for s in sources}
    rows = []
    for f in sorted(findings, key=lambda x: x["rank"]):
        cls, label = VERDICT_BADGE[f["verdict"]]
        if f["verdict"] == "unverified":
            src_cell = '<span class="badge b-bad">— · blank (see <a href="flagged.html">flags</a>)</span>'
        else:
            s = by_id[f["source"]]
            src_cell = (f'<a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">'
                        f'{esc(f["source"])} · {esc(s["issuer"].split(",")[0])}</a><br>'
                        f'<span class="note">{esc(f["locator"])}</span>')
        repo = ", ".join(f'<code>{esc(p)}</code>' for p in f["repo"])
        rows.append(
            f'<tr id="{f["id"]}">'
            f'<td data-label="Rank / ID" class="id">#{f["rank"]} · {f["id"]}</td>'
            f'<td data-label="Topic"><strong>{esc(f["topic"])}</strong><div class="note">{esc(f["id"])} — {esc(f["claim"])}</div></td>'
            f'<td data-label="Verdict"><span class="badge {cls}">{label}</span></td>'
            f'<td data-label="Official source (re-fetched 2026-11-10)" class="src">{src_cell}</td>'
            f'<td data-label="Verification note">{esc(f["note"])}<div class="refs">appears in: {repo}</div></td>'
            f"</tr>"
        )
    body = f"""{nav("findings")}
<h1>Findings — claim by claim</h1>
<p class="lede">{len(findings)} findings in decision order (most important first). Every VERIFIED row links the
official document re-fetched in this session and names the exact article or section read. UNVERIFIED rows carry
no source link and a blank value on purpose — they are cross-listed on the <a href="flagged.html">Flagged page</a>.</p>
<div class="scroll"><table>
<thead><tr><th>ID</th><th>Topic &amp; claim as verified</th><th>Verdict</th><th>Official source + locator</th><th>Verification note &amp; where it appears</th></tr></thead>
<tbody>
{"".join(rows)}
</tbody></table></div>
<p class="note">Re-fetch date for all cited documents: 2026-11-10. Repo paths listed per row are the pages
where the claim is published; this pass verified the claim text, not every sentence of those host pages.</p>
"""
    return page("Findings — claim-by-claim verification", body,
                "Every verified claim with its official source link, locator, verdict and repo locations.")


def build_sources(d):
    sources = d["sources"]
    rows = []
    for s in sources:
        gov = "ok" if s["id"] not in ("S16",) else "lim"
        rows.append(
            f'<tr id="{s["id"]}">'
            f'<td data-label="ID" class="id">{s["id"]}</td>'
            f'<td data-label="Issuer &amp; document"><strong>{esc(s["issuer"])}</strong>'
            f'<div class="note">{esc(s["title"])}</div>'
            f'<div class="refs">published / effective: {esc(s["date"])}</div></td>'
            f'<td data-label="Link" class="src"><a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">{esc(s["url"])}</a>'
            f'<div class="refs"><span class="badge b-{gov}">{esc(s["status"])}</span></div></td>'
            f'<td data-label="What was read (quote from the fetched document)">'
            f"<details><summary>Show locator quote</summary><div class=\"quote\">{esc(s['quote'])}</div></details></td>"
            f"</tr>"
        )
    body = f"""{nav("sources")}
<h1>Source register — {len(sources)} documents re-fetched this session</h1>
<p class="lede">Each document below was retrieved and read during this session (2026-11-10). Government
publishers are listed first in ID order; the HSBC tariff (S16) is a commercial primary source and is
labelled as such. Links open the official document for manual review.</p>
<div class="scroll"><table>
<thead><tr><th>ID</th><th>Issuer &amp; document</th><th>Link + fetch status</th><th>Locator / quote</th></tr></thead>
<tbody>
{"".join(rows)}
</tbody></table></div>
"""
    return page("Source register — documents re-fetched 2026-11-10", body,
                "Register of the 17 official and primary sources fetched and read during this verification session.")


def build_ladder_check(d):
    lc = d["ladder_check"]
    ladder_results = checks.ladder_checks()
    rep_results = checks.repatriate_checks()

    def render(results):
        items = []
        for name, ok, detail in results:
            mark = '<span class="pass">PASS</span>' if ok else '<span class="badge b-bad">FAIL</span>'
            items.append(f"<li>{mark} — {esc(name)} <span class=\"note\">({esc(detail)})</span></li>")
        return "".join(items)

    l = lc["ladder"]
    r = lc["repatriate"]
    body = f"""{nav("ladder-check")}
<h1>Cost-ladder structure check (independent, read-only)</h1>
<p class="lede">{esc(lc["label"])}. Two published ladders were re-parsed from their checked-in data files and
recomputed: <strong>ladder/ 600 rows</strong> (15 costed routes × 40 tiers, $10,000 → $400,000 in $10,000 steps)
and <strong>repatriate/ 680 rows</strong> (17 methods × the same 40 amounts). Results below are produced by
<code>audit-ad300459/checks.py</code> at build time and re-run independently by <code>verify.py</code> in CI.</p>
<div class="cards">
  <article class="card"><p class="l">Ladder rows</p><p class="k ok">600</p><p class="s">{esc(l["file"])}</p></article>
  <article class="card"><p class="l">Repatriate rows</p><p class="k ok">680</p><p class="s">{esc(r["file"])}</p></article>
  <article class="card"><p class="l">Tiers</p><p class="k">40</p><p class="s">$10,000 → $400,000, step $10,000</p></article>
  <article class="card"><p class="l">Failures</p><p class="k {'ok' if all(o for _, o, _ in ladder_results + rep_results) else 'bad'}">{sum(1 for _, o, _ in ladder_results + rep_results if not o)}</p><p class="s">of {len(ladder_results) + len(rep_results)} checks</p></article>
</div>
<h2>ladder/data/costs.json — {l["expected_rows"]} expected rows</h2>
<ul class="checks">{render(ladder_results)}</ul>
<h2>repatriate/exports/cost-ladders.json — {r["expected_rows"]} expected rows</h2>
<ul class="checks">{render(rep_results)}</ul>
<div class="notice"><strong>What this does NOT prove:</strong> {esc(lc["conclusion"])}</div>
<h2>Published check definitions (from the ledger)</h2>
<h3>ladder/</h3><ul class="checks">{" ".join(f"<li>{esc(x)}</li>" for x in l["checks"])}</ul>
<h3>repatriate/</h3><ul class="checks">{" ".join(f"<li>{esc(x)}</li>" for x in r["checks"])}</ul>
"""
    return page("Cost-ladder structure check", body,
                "Independent read-only structure and arithmetic checks of the 600-row and 680-row cost ladders.")


def build_flagged(d):
    flags = d["flags"]
    cards = []
    for fl in flags:
        repo = ", ".join(f'<code>{esc(p)}</code>' for p in fl["repo"])
        if fl["url"]:
            link = (f'<p class="refs">reference: <a href="{esc(fl["url"])}" '
                    f'target="_blank" rel="noopener noreferrer">{esc(fl["url"])}</a></p>')
        else:
            link = '<p class="refs">source: <strong>— (blank: unverified, not inferred)</strong></p>'
        cards.append(
            f'<article class="flag" id="{fl["id"]}">'
            f'<span class="badge b-bad">{esc(fl["status"].upper())}</span> '
            f'<span class="badge b-lim">{fl["id"]}</span>'
            f"<h3>{esc(fl['title'])}</h3>"
            f"<p>{esc(fl['detail'])}</p>{link}"
            f'<p class="refs">appears in: {repo}</p></article>'
        )
    body = f"""{nav("flagged")}
<h1>Flagged for review — unverified values and carried-forward issues</h1>
<p class="lede">{len(flags)} open items. Blank means unverified, never zero. None of these block the published
verification above; they are the honest edges of what fetched sources can establish right now.</p>
{"".join(cards)}
"""
    return page("Flagged for review — audit-ad300459", body,
                "Unverified values, blank fields and carried-forward wording issues from this verification pass.")


def build_csv(d):
    path = os.path.join(HERE, "exports", "findings.csv")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    by_id = {s["id"]: s for s in d["sources"]}
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["kind", "id", "rank", "topic_or_title", "verdict_or_status",
                    "claim_or_detail", "source_id", "url", "locator"])
        for f in sorted(d["findings"], key=lambda x: x["rank"]):
            url = by_id[f["source"]]["url"] if f["source"] else ""
            w.writerow(["finding", f["id"], f["rank"], f["topic"], f["verdict"],
                        f["claim"], f["source"], url, f["locator"]])
        for fl in d["flags"]:
            w.writerow(["flag", fl["id"], "", fl["title"], fl["status"],
                        fl["detail"], "", fl["url"], ""])


def main():
    d = load()
    outputs = {
        "index.html": build_index(d),
        "findings.html": build_findings(d),
        "sources.html": build_sources(d),
        "ladder-check.html": build_ladder_check(d),
        "flagged.html": build_flagged(d),
    }
    for name, text in outputs.items():
        with open(os.path.join(HERE, name), "w", encoding="utf-8") as fh:
            fh.write(text)
    build_csv(d)
    print(f"built {len(outputs)} pages + exports/findings.csv")


if __name__ == "__main__":
    main()
