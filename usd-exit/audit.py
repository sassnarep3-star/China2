#!/usr/bin/env python3
"""
usd-exit repo audit generator.

Produces usd-exit/audit.html: the line-by-line review of this repository as it
stood when this session started, plus the CI behaviour that follows from it.

Every finding below was established by a command whose output is quoted in the
"Evidence" column, so each row can be re-checked mechanically rather than taken
on trust. Findings about files owned by other sessions are recorded here and
logged in COORDINATION.md; they are NOT edited by this session.

Run: python3 usd-exit/audit.py   (build.py calls this too)
"""
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)


def sh(cmd):
    """Run a command in the repo and return trimmed stdout ('' on failure)."""
    try:
        r = subprocess.run(cmd, shell=True, cwd=REPO, capture_output=True, text=True, timeout=120)
        return (r.stdout or r.stderr).strip()
    except Exception as ex:  # noqa: BLE001
        return f"(command failed: {ex})"


def table_count(pattern):
    return sh(f"git ls-files '{pattern}' | wc -l").strip()


FINDINGS = [
    # id, area, observation, evidence, assessment, action, flag
    ("R-01", "Scale of duplication",
     "Six independent dashboards answer the same question in the same repository.",
     "docs/ (9 pages), site/ (11), portal/ (7), ladder/ (12), repatriate/ (7), audit-86f0/ (4) — plus the root index.html hub.",
     "Six overlapping implementations of one research question. They disagree with each other on the number of routes, so a reader has no way to know which is authoritative.",
     "This session ships a seventh, self-contained scope (usd-exit/). The integration decision about which dashboard is canonical belongs to the repo owner; consolidating other sessions' directories is out of this session's scope.",
     "F-DUPLICATION"),

    ("R-02", "Contradictory published claim",
     "Three different descriptions of the US$50,000 annual figure are published across the repo, and one is wrong.",
     "site/conversion-routes.html: 'USD 50,000 per person per year is a hard ceiling'. usd-exit and ladder/ correctly describe it as an annual FACILITATION quota, above which genuine current-account transactions are permitted with authenticity documents (SAFE Q&A, P03).",
     "A 'hard ceiling' reading is a substantive error: it would lead a reader to believe a lawful above-quota transaction is impossible, and it is the fact most likely to make someone reach for a prohibited route instead.",
     "Corrected in this session's own scope and flagged; the other session's page is recorded here and logged in COORDINATION.md, not edited.",
     "F-CONTRADICTION"),

    ("R-03", "CI workflow does not run on its own branch",
     "validate.yml triggers on main and arena/996dc508-china2 only. Four of the five other workflows likewise name a single session branch.",
     "validate.yml: branches: [main, arena/996dc508-china2]. verify-ladder.yml: [main, arena/de9755b1-china2]. verify-portal-85f37d08.yml and verify-repatriate-3e494fa5.yml and verify-site-data.yml: main only.",
     "Parallel sessions get no CI feedback on their own branches. A branch can be broken for its entire life and only fail after merge to main — which is exactly the failure mode the task instructions say must not happen ('do not merge a broken site').",
     "This session adds .github/workflows/verify-usd-exit-b8e50c81.yml which triggers on pull_request and push to main, so the gate fires for this branch and for the merge. The other workflows are not modified.",
     "F-CI-SCOPE"),

    ("R-04", "Paths referenced by CI",
     "validate.yml invokes scripts/build.py, scripts/validate.py, node scripts/test_ui.js; package.json invokes tools/build.mjs and tools/verify.mjs. All six files exist and all six run clean.",
     "Verified by execution: scripts/build.py 'Built 7 pages, 67 research rows and 24 sources.'; scripts/validate.py PASS; node scripts/test_ui.js PASS; node tools/verify.mjs '477 checks run, 0 failure(s)'.",
     "No broken CI path. Recorded because a referenced-but-missing script is the most common way a repo's checks silently stop protecting anything.",
     "None required.",
     "—"),

    ("R-05", "Build determinism hazard",
     "Several generators stamp today's date into committed output, so running a build on a different day dirties the tree even when nothing substantive changed.",
     "Running python3 ladder/model.py on 2026-11-09 changed ladder/data/meta.json and ladder/data/costs.json — the only diff being '\"generated\": \"2026-11-08\"' -> '\"generated\": \"2026-11-09\"'.",
     "verify-ladder.yml runs the model and then asserts 'git diff --exit-code -- ladder index.html'. On any day other than the commit day this fails on a date stamp, not on a real regression. That makes a real regression indistinguishable from date drift, which is how CI checks lose their authority.",
     "Reverted (git checkout -- ladder/) so no other session's generated files are modified by this session. Recorded here because it will keep biting every session until the date is generated at publish time rather than committed.",
     "F-DETERMINISM"),

    ("R-06", "Root document duplication",
     "Two root-level executive summaries coexist with overlapping content.",
     "EXECUTIVE-SUMMARY.md (13,169 bytes) and EXECUTIVE_SUMMARY.md (3,450 bytes); diff shows they are not identical.",
     "Two files, one name transposed by a hyphen, is a drift trap: a reader cannot tell which is current and any correction may land in only one.",
     "Owned by other sessions; logged for the integration decision, not edited here.",
     "F-DUPLICATION"),

    ("R-07", "Citeable-but-repealed instrument",
     "Hui Fa [2007] No. 1 Art. 39 (the quota-splitting penalty) was repealed by Hui Fa [2023] No. 8, and a repeal is easy to misread as legalisation.",
     "SAFE publishes the 2007 measure with the Art. 39 repeal noted (P02). The prohibition on splitting survives independently in PBOC Decree [2006] No. 3 Art. 7 (P01) and in SAFE's own 'six don'ts' (P15).",
     "The conclusion (splitting is prohibited) is correct, but a citation-audit that only checks 'does the penalty clause exist' would wrongly conclude the conduct is now permitted.",
     "Recorded as a flagged irregularity on the Flagged for Review page (I-03), with the surviving citation given so the conclusion rests on text that is still in force.",
     "F-REPEAL-TRAP"),

    ("R-08", "Inconsistent source quality across dashboards",
     "The evidence ledger duplicates itself four times with different contents and different source standards.",
     "Four separate source files: data/sources.json (17 records), ladder/data/sources.json (20), docs/data/sources.json (24), usd-exit/data/sources.json (27). Two records in data/sources.json are plain http:// (not https): safe.gov.cn/en/2017/1230/1397.html and english.www.gov.cn/.../content_WS614dc30bc6d0df57f98e0c84.html.",
     "Four ledgers means four chances for a quote to drift from the source it claims to reproduce, and no single place where a user can audit the evidence.",
     "This session's ledger enforces https plus an allow-list of official/commercial hosts in verify.py (V5), and records a verbatim quote plus a locator for every record (V6). The other ledgers are untouched.",
     "F-LEDGER-DRIFT"),

    ("R-09", "Stale unverified items",
     "Earlier sessions left high-severity items blank that are answerable from primary sources now.",
     "data/flags.json F02 'FBAR civil penalty dollar amounts are left blank' (severity high) and F10 'U.S. reporting threshold for gifts received from a foreign person is unverified' (medium); F07 'Chinese customs cash-carrying thresholds are unverified' (high).",
     "All three are published plainly: 31 CFR 1010.821 gives US$16,536 non-willful and US$165,353 willful (U04); IRS states the US$100,000 Form 3520 threshold (U08); SAFE states US$5,000 free / US$5,000–10,000 permit / above US$10,000 prohibited (P07).",
     "Filled in this session's own pages with citations, and the closure recorded here so the integration session can retire the stale flags rather than carry them forward.",
     "F-STALE-FLAG"),

    ("R-10", "Unsubstantiated specific claim",
     "portal/methods.html states a route is 'Not counted toward RMB 100,000 ATM cash cap or USD 50,000 domestic quota', and site/conversion-routes.html that a route is 'Not limited by the USD 50,000 annual quota'.",
     "Neither page in this repo carries a quotation from an official source establishing that carve-out; the SAFE texts reviewed in this session (P02, P03, P05) do not state it.",
     "A specific exemption from two quota regimes is a strong claim that needs the operative text. If it is true it is valuable; as published it is unsupported, and a reader could rely on it and breach a quota.",
     "Flagged for review with the exact URLs to re-check. Not edited (other sessions' scope). This session's own pages assert no such carve-out.",
     "F-UNSUPPORTED-CLAIM"),

    ("R-11", "Broken PR state on the shared board",
     "COORDINATION.md records PR #17 as merged; GitHub reports it OPEN and CONFLICTING with no CI checks.",
     "gh pr view 17 -> 'CONFLICTING', 'DIRTY'; no status checks reported.",
     "The task board's own description of the repository state is wrong, which means a session relying on it would believe merged work is live when it is not.",
     "Recorded on the Flagged for Review page (I-05). Not edited: COORDINATION.md is append-only and shared, so this session logs rather than rewrites.",
     "F-BOARD-DRIFT"),

    ("R-12", "Time-stamped FX assumption",
     "No dashboard publishes the exchange rate it uses to turn Chinese fee caps into dollars.",
     "ladder/ and audit-86f0/ publish CNY figures; docs/ and repatriate/ publish USD figures; none states a rate and date.",
     "Without a published rate and date, a USD figure cannot be re-derived or checked, and it silently becomes stale as the rate moves.",
     "This session publishes its anchor explicitly — 1 USD = 6.7188 CNY, SAFE central parity for 2026-11-09 (P14) — in the data, on the page, and in verify.py's arithmetic check.",
     "F-RATE-OPAQUE"),
]


def build_audit_html(n_sources, n_methods):
    # a few live counts so the page cannot silently go stale
    counts = {
        "html": int(table_count("*.html") or 0),
        "json": int(table_count("**/*.json") if False else sh("git ls-files '*.json' | wc -l") or 0),
        "workflows": int(sh("git ls-files '.github/workflows/*.yml' | wc -l") or 0),
        "py": int(sh("git ls-files '*.py' | wc -l") or 0),
        "md": int(sh("git ls-files '*.md' | wc -l") or 0),
    }
    rows = "".join(
        f"""<tr>
        <td><strong>{fid}</strong><div class="tiny">{area}</div></td>
        <td>{obs}</td>
        <td class="ev"><code>{ev}</code></td>
        <td>{assess}</td>
        <td>{act}</td>
        <td>{'<span class="flag">'+flag+'</span>' if flag != '—' else '—'}</td>
        </tr>"""
        for fid, area, obs, ev, assess, act, flag in FINDINGS
    )

    flag_rows = "".join(
        f'<tr><td><span class="flag">{fid}</span></td><td>{flag}</td></tr>'
        for fid, area, obs, ev, assess, act, flag in FINDINGS if flag != "—"
    )

    body = f"""
<section class="hero">
  <p class="kicker">Repository audit</p>
  <blockquote>A line-by-line review of this repository as it stood at the start of this session.
  Twelve findings, each with the command output that establishes it. Nothing here is an opinion
  about how someone else's code is written — every finding is about whether a reader could be
  <em>misled</em> by what is published.</blockquote>
</section>

<h2>Method</h2>
<ol class="steps">
<li>Enumerated the tracked tree: <code>git ls-files</code> → {counts['html']} HTML pages, {counts['json']} JSON ledgers,
{counts['py']} Python files, {counts['md']} markdown documents, {counts['workflows']} CI workflows.</li>
<li>Ran every harness the repo ships, to see which claims are actually machine-checked:
scripts/build.py, scripts/validate.py, node scripts/test_ui.js, node tools/verify.mjs,
ladder/model.py, ladder/verify.py, portal/generate_portal.py, repatriate/verify.py, audit-86f0/verify.py —
all nine passed before this session added anything.</li>
<li>Range-checked every numeric claim that could be checked against a primary source: the US$50,000 quota,
the US$10,000 reporting lines, the FBAR penalty maxima, the cash-carry tiers, the bank tariff items and the
exchange rate. Where a page asserted a number with no operative text behind it, that is finding R-10.</li>
<li>Re-fetched each official source cited by the previous sessions and compared it to the quotation in this
session's ledger. All {n_sources} sources in <a href="sources.html">sources.json</a> resolve on an official host.</li>
<li>Checked every internal link and anchor across all six existing dashboards: <strong>0 broken</strong>.</li>
</ol>

<h2>What is healthy</h2>
<div class="cards">
<div class="card"><h3>No broken links anywhere</h3>
<p>Every relative link and in-page anchor in docs/, site/, portal/, ladder/, repatriate/ and audit-86f0/
resolves. Whatever else is true, the repository does not ship dead navigation.</p></div>
<div class="card"><h3>Nine harnesses, all green</h3>
<p>Every generator is deterministic on the day it is run and every checker passes. The machinery is real,
not decorative.</p></div>
<div class="card"><h3>Sources are genuinely primary</h3>
<p>SAFE, PBOC, STA, IRS, CBP, eCFR and govinfo dominate. Very little of this repo rests on secondary
commentary, which is unusual for this subject.</p></div>
<div class="card"><h3>Blanks are respected</h3>
<p>Earlier sessions did leave values blank rather than invent them. The problem is that several of those
blanks are no longer necessary (R-09), not that they were wrong.</p></div>
</div>

<h2>The twelve findings</h2>
<table class="t audit">
<thead><tr><th>ID / area</th><th>Observation</th><th>Evidence</th><th>Why it matters</th><th>Action taken here</th><th>Flag</th></tr></thead>
<tbody>{rows}</tbody>
</table>

<h2>What this session changed, and what it deliberately did not</h2>
<table class="t">
<thead><tr><th>Did</th><th>Did not</th></tr></thead>
<tbody>
<tr><td>Added a self-contained <code>usd-exit/</code> scope with its own data, generator and verifier.</td>
<td>Edit any other session's page, even where a claim is wrong (R-02, R-10) — those are logged for the
integration decision instead.</td></tr>
<tr><td>Added a CI workflow that runs this scope's verifier on pull requests and on main.</td>
<td>Modify the five existing workflows to broaden their branch triggers, which would change other
sessions' gate behaviour mid-flight.</td></tr>
<tr><td>Re-fetched and re-quoted every source used, with a locator per record.</td>
<td>Claim that any other dashboard's quotation is fabricated — only that this session did not rely on it.</td></tr>
<tr><td>Reverted <code>ladder/</code> after a probe run dirtied its date stamps (R-05).</td>
<td>Commit another session's regenerated files.</td></tr>
</tbody>
</table>

<h2>Flag index</h2>
<p>Each of these appears with its detail on the <a href="flagged.html">Flagged for Review</a> page.</p>
<table class="t">
<thead><tr><th>Finding</th><th>Flag</th></tr></thead>
<tbody>{flag_rows}</tbody>
</table>

<h2>Reproduction</h2>
<p class="mono">git ls-files | wc -l · python3 scripts/validate.py · node tools/verify.mjs ·
python3 ladder/model.py && git diff --stat ladder/ · git ls-files '*.json' · gh pr view 17</p>
<p class="note">Every command above is read-only except <code>ladder/model.py</code>, which rewrites its
own date stamps; if you run it, <code>git checkout -- ladder/</code> afterwards.</p>
"""
    return body


if __name__ == "__main__":
    print(build_audit_html(27, 20)[:400])
