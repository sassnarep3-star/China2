#!/usr/bin/env python3
"""Mechanical line-by-line repository review for guide-be3c20e8.

Reads every tracked text file outside this section line by line, counts the
scan, then re-locates a finite list of representative claims by regex so each
finding carries a current file:line excerpt.  It does not edit another
session's files and is not a certification of every legal sentence in the
repository.  Every finding is tied to a primary source read this session.

Run: python3 audit.py   -> writes data/review.json
"""
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = HERE / "data"
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE))
import content  # noqa: E402

LEDGER = json.loads((DATA / "sources.json").read_text(encoding="utf-8"))
S = {s["id"]: s for s in LEDGER["sources"]}
EXCLUDE_DIRS = {"guide-be3c20e8", ".git", "node_modules", "__pycache__"}

# (id, file, regex, category, status, finding, source ids, reviewer note)
RULES = [
    ("RV-01", "verification-3347ca0a/build.py", r"RATE_BOC = 669\.11", "bank board", "conflict · historical snapshot", "The root landing-page generator still prices BOC at 6.6911 from a 10:25:02 board.", ["B01"], "The fresh 21:00:05 board prints 6.6871 for the USD sell price; this section uses the fresh reading and does not edit the other session's rate model."),
    ("RV-02", "dashboard-f79e64e7/content.py", r'quote="USD \| Buying Rate 666\.3', "bank board", "conflict · historical snapshot", "A quoted BOC board records buying 666.3 / selling 669.11 per 100 USD at 10:25:02.", ["B01"], "A dated snapshot, not today's board; the discrepancy is published rather than silently corrected here."),
    ("RV-03", "guide-fb2f2562/build.py", r"Bank of China board 666\.06 / 668\.86", "bank board", "conflict · historical snapshot", "An older guide's cost page states a BOC board of 666.06 / 668.86 per 100 USD at 15:30.", ["B01"], "The fresh board prints 665.91 / 668.71 per 100 USD at 21:00:05; both are dated reference-only boards."),
    ("RV-04", "guide-fb2f2562/content.py", r"BOC sells USD at 668\.86", "bank board", "conflict · historical snapshot", "An older summary derives a 0.21% midpoint gap from the 668.86 BOC sell price.", ["B01"], "The fresh board gives 668.71 and a 0.2094% midpoint spread; the historical figure remains in its owning section."),
    ("RV-05", "guide-fb2f2562/audit.py", r"CNY 620 converted at the IRS 2025 average", "rate base", "rate-base conflict · needs review", "The HSBC CNY 620 fee cap is translated at the IRS 2025 yearly average of 7.129 rather than a bank dealing rate.", ["B02", "B04", "B07"], "CNY 620 = CNY 500 cap + CNY 120 cable; a tax-translation average is not an executable bank rate."),
    ("RV-06", "verification-3347ca0a/build.py", r"renminbi fee of CNY 620", "rate base", "rate-base conflict · needs review", "The root generator compares CNY 620 at both a board rate and the IRS yearly-average rate.", ["B01", "B04", "B07"], "The published tariff's cap and cable charge are correctly summed, but the two rate bases should not be presented as one all-in cost."),
    ("RV-07", "COORDINATION.md", r"cites a 2027 foreign earned income exclusion of USD 137,300", "tax figure", "corrected here · now verified", "A prior board line says the 2027 FEIE of USD 137,300 was not confirmed.", ["B26"], "Rev. Proc. 2026-35 §3.41 explicitly publishes USD 137,300 for tax years beginning in 2027; this session verifies it."),
    ("RV-08", "COORDINATION.md", r"59 files quote a foreign earned income exclusion", "tax figure", "corrected here · now verified", "A prior review says USD 132,900 / USD 137,300 were unverified and left blank.", ["B25", "B26"], "2026 Form 2555 instructions publish USD 132,900; Rev. Proc. 2026-35 publishes USD 137,300 for 2027."),
    ("RV-09", "estimate-facf2fe9/data/sources.json", r"第六条 移民转移必须一次性申请.*分步汇出", "superseded rule", "superseded · needs review", "A historical source ledger repeats PBOC 2004 Article 6's compulsory staged-emigrant-remittance wording.", ["B12", "B13"], "SAFE 汇发〔2014〕2号 §VI abolished the staged requirement and HQ filing; the later rule governs."),
    ("RV-10", "dashboard-f79e64e7/content.py", r"取消移民财产转移分次汇出的要求", "superseded rule", "verified · corrected in that section", "A later dashboard quotes the SAFE rule abolishing compulsory staged emigrant remittance.", ["B12"], "The quoted rule matches the official 2014 notice read this session."),
    ("RV-11", "audit-0f0f59fe/findings.json", r"not automatic or necessarily dollar-for-dollar", "foreign tax credit", "verified · corrected in that section", "A prior finding says the foreign tax credit is not automatic or necessarily dollar-for-dollar.", ["B29"], "IRS FTC guidance says the qualifying credit may be less than withholding and no credit is allowed on excluded income."),
    ("RV-12", "guide-fb2f2562/audit.py", r"Calls the credit dollar-for-dollar", "foreign tax credit", "conflict · corrected by audit", "An older audit rule identifies a line calling the foreign tax credit dollar-for-dollar.", ["B29"], "The official FTC page states limits and a treaty-reduced-tax rule; this section does not repeat the overstatement."),
    ("RV-13", "COORDINATION.md", r"fiat↔virtual currency business is illegal financial activity", "prohibited channel", "verified · current", "The board records that fiat-to-virtual-currency business is illegal financial activity.", ["B18"], "PBOC 银发〔2026〕42号 says such business is strictly prohibited; actual numeric penalties remain blank."),
    ("RV-14", "briefing/AUDIT.md", r"HSBC tariff internal header", "tariff irregularity", "verified-limited · needs review", "A prior audit records two effective-date headers inside the HSBC tariff PDF.", ["B04"], "The cover says 31 Oct 2026 while embedded Chinese headers say 12 Sep 2024; the bank should confirm the applicable version."),
    ("RV-15", "final-d54bb3c2/model.py", r"Bank of China board, 2026/11/11 20:39:19", "bank board", "historical · snapshot", "A final-section model records the 20:39:19 BOC board timestamp.", ["B01"], "The USD row was unchanged at the 21:00:05 re-read; this section uses the later timestamp."),
    ("RV-16", "COORDINATION.md", r"non-willful USD 16,536 / willful USD 165,353", "penalty table", "verified-limited · needs review", "The board records the eCFR FBAR penalty amounts with a 2025 amendment citation.", ["B21", "B22"], "The eCFR table is displayed current to 11/09/2026 but its quoted amendment history ends at 90 FR 5630 (17 Jan 2025)."),
    ("RV-17", "verification-3347ca0a/build.py", r"Rev\. Proc\. 2026-35 FEIE \$137,300", "tax figure", "verified · current", "The root generator's archive note cites the 2027 FEIE of USD 137,300 from Rev. Proc. 2026-35.", ["B26"], "The figure is explicitly published in §3.41 of the official revenue procedure."),
    ("RV-18", "README.md", r"Rev\. Proc\. 2026-35 §3\.41 FEIE `\$137,300`", "tax figure", "verified · current", "The README entry for an earlier guide cites the 2027 FEIE of USD 137,300.", ["B26"], "The figure is now verified; the 2026 cap of USD 132,900 is a different tax year."),
    ("RV-19", "final-d54bb3c2/data/review.json", r"The guide records the BOC board as buy 666\.06", "bank board", "verified · historical comparison", "A prior review compares an older BOC/HSBC board with its own 20:39 reading.", ["B01", "B02"], "This is a documented comparison, not a live quote; the fresh 21:00:05 BOC board and 10 Nov HSBC board are used here."),
    ("RV-20", "guide-fb2f2562/data/sources.json", r"6\.7053746", "bank board", "conflict · historical snapshot", "An older source ledger records an HSBC sell rate of 6.7053746.", ["B02"], "The fresh HSBC board prints 6.7030239 sell and 6.6362813 TT buy; the board is dated 10 Nov and reference-only."),
]

def tracked_files():
    raw = subprocess.check_output(["git", "-C", str(ROOT), "ls-files", "-z"], text=False).decode("utf-8")
    out = []
    for name in raw.split("\0"):
        if not name:
            continue
        parts = Path(name).parts
        if any(part in EXCLUDE_DIRS for part in parts):
            continue
        p = ROOT / name
        if p.is_file():
            out.append((name, p))
    return sorted(out)

def scan_all(files):
    text_files = 0
    lines_read = 0
    substantive = 0
    bytes_read = 0
    for name, p in files:
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        text_files += 1
        bytes_read += len(text.encode("utf-8"))
        for line in text.splitlines():
            lines_read += 1
            if len(line.strip()) >= 20:
                substantive += 1
    return {"tracked_files_considered": len(files), "text_files": text_files, "lines_read": lines_read, "substantive_lines": substantive, "bytes_read": bytes_read}

def locate(files, name, pattern):
    rx = re.compile(pattern)
    for fname, p in files:
        if fname != name:
            continue
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            break
        for i, line in enumerate(lines, 1):
            if rx.search(line):
                return i, " ".join(line.split())[:300]
    raise RuntimeError(f"audit pattern not found in {name}: {pattern}")

def main():
    files = tracked_files()
    scan = scan_all(files)
    findings = []
    for rid, name, pattern, category, status, finding, source_ids, note in RULES:
        assert all(s in S for s in source_ids), (rid, source_ids)
        line, excerpt = locate(files, name, pattern)
        findings.append({
            "id": rid, "file": name, "line": line, "excerpt": excerpt,
            "category": category, "status": status, "finding": finding,
            "reviewer_note": note, "source_ids": source_ids,
            "official_urls": [{"id": s, "url": S[s]["url"], "publisher": S[s]["publisher"]} for s in source_ids],
        })
    out = {
        "generated_by": "guide-be3c20e8/audit.py",
        "retrieved": LEDGER["retrieved"],
        "scope": "All tracked text files outside guide-be3c20e8 were read line by line. Findings are a finite, representative pattern review, not a certification of every legal sentence.",
        "scan": scan,
        "findings": findings,
        "limitations": "Other sessions' files were not edited. Line numbers are re-located at build time. A matching line is a review candidate; the official link supports the comparison, not every word in the historical file.",
    }
    (DATA / "review.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"scanned {scan['text_files']} text files / {scan['lines_read']} lines; {len(findings)} findings")

if __name__ == "__main__":
    main()
