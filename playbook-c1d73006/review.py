#!/usr/bin/env python3
"""Read-only review of the other sections of this repository against the figures
this session read on official pages (data/sources.json).

It only searches text.  A hit is a place for a person to look, not a ruling: the
script cannot tell a wrong figure from a figure quoted in order to correct it.
Nothing outside playbook-c1d73006/ is written.

The result is a dated snapshot (data/review.json).  build.py and verify.py read
the snapshot and never rescan, so later changes elsewhere in the repository
cannot break this section's checks.

Run:  PYTHONDONTWRITEBYTECODE=1 python3 playbook-c1d73006/review.py <YYYY-MM-DD>
"""
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
EXT = {".html", ".json", ".md", ".py", ".csv", ".mjs", ".js", ".txt"}
SKIP_PREFIX = ("playbook-c1d73006/", ".github/")
SKIP_FILES = {"COORDINATION.md"}
MAX_EXAMPLES = 5


def tracked():
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    for p in sorted(out.splitlines()):
        if p.startswith(SKIP_PREFIX) or p in SKIP_FILES or Path(p).suffix not in EXT:
            continue
        yield p


def text_lines(path):
    """Visible text per line; long generated HTML lines are split at tag boundaries first."""
    raw = (ROOT / path).read_text(encoding="utf-8", errors="replace")
    if path.endswith(".html"):
        raw = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", raw)
        raw = re.sub(r"(?i)</(tr|p|li|h[1-6]|div|section|td|th)>", "\n", raw)
        raw = re.sub(r"<[^>]+>", " ", raw)
    for n, line in enumerate(raw.splitlines(), 1):
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            yield n, line[:2000]


def section(path):
    return path.split("/")[0] if "/" in path else "(repository root)"


def clip(line, m):
    a = max(0, m.start() - 70)
    b = min(len(line), m.end() + 70)
    return ("…" if a else "") + line[a:b] + ("…" if b < len(line) else "")


def money(s):
    return int(s.replace(",", ""))


# Each check: id, what is compared, the verified value and its source, and a function line -> (kind, match) or None.
def chk_fbar_nonwillful(line):
    if not re.search(r"(?i)non[\s‑-]?willful", line):
        return None
    for m in re.finditer(r"\$\s?(1\d,\d{3})(?![\d,])", line):
        v = money(m.group(1))
        if v != 10000:
            return ("match" if v == 16536 else "differs", m)
    return None


def chk_fbar_willful(line):
    if not re.search(r"(?i)(?<!non[\s‑-])(?<!non)willful", line):
        return None
    for m in re.finditer(r"\$\s?(1\d\d,\d{3})(?![\d,])", line):
        v = money(m.group(1))
        if v not in (100000, 150000):
            return ("match" if v == 165353 else "differs", m)
    return None


def chk_hsbc_usd(line):
    m = re.search(r"\$\s?86\.97\b", line)
    return ("differs", m) if m else None


def chk_rate_basis(line):
    m = re.search(r"(?<![\d.])7\.129(?!\d)", line)
    if m and re.search(r"(?i)cost|fee|estimate|convert|per usd|cny/usd|rate", line):
        return ("match", m)
    return None


def chk_staging(line):
    if not re.search(r"(?i)emigra|移民", line):
        return None
    m = re.search(r"(?i)\bhalf\b|一半|50\s?%\s?(?:in|the)?\s?(?:first|year)|instal+ments?|in stages|分步|分次", line)
    if not m:
        return None
    fixed = re.search(r"(?i)2014|abolish|cancel|remov|no longer|取消|one payment|single", line)
    return ("match" if fixed else "differs", m)


def chk_ftc(line):
    m = re.search(r"(?i)dollar[\s-]for[\s-]dollar", line)
    if not m:
        return None
    hedged = re.search(r"(?i)\bnot\b|\bno\b|limit|may\b|overstat|subject to|up to|\bcap|qualif|automatic|\?|never|unless|only", line)
    return ("match" if hedged else "differs", m)


def chk_feie(line):
    m = re.search(r"\$\s?13[27],[39]00\b", line)
    return ("unverified", m) if m else None


def chk_late(line):
    m = re.search(r"(?i)0\.05\s?%\s?(?:per|a|each|/)\s?day|万分之五|0\.05% daily|daily[^.]{0,30}0\.05\s?%", line)
    return ("match", m) if m else None


def chk_http(line):
    m = re.search(r"http://(?:m\.|www\.)?(?:safe\.gov\.cn|pbc\.gov\.cn|chinatax\.gov\.cn|irs\.gov|customs\.gov\.cn|cmbchina\.com)[^\s\"'<>)]*", line)
    return ("differs", m) if m else None


CHECKS = [
    ("RV-01", "FBAR maximum civil penalty, non-willful", "$16,536", "US-RPT-03", "nonwillful", chk_fbar_nonwillful,
     "A different dollar figure on a line about the non-willful penalty."),
    ("RV-02", "FBAR civil penalty, willful (fixed-dollar limb)", "$165,353", "US-RPT-03", "willful", chk_fbar_willful,
     "A different dollar figure on a line about the willful penalty."),
    ("RV-03", "HSBC China wire fee cap expressed in dollars", "CNY 500 + CNY 120 = CNY 620; $92.43 at HSBC's own selling rate of 6.7080734", "BANK-02", "tt_issuance", chk_hsbc_usd,
     "The figure $86.97 is CNY 620 divided by 7.129, the IRS average rate for tax year 2025. The fee is charged in CNY at the time of the wire, so the dollar value moves with the bank's current rate."),
    ("RV-04", "Rate used to turn CNY into USD in cost tables", "7.129 is the IRS yearly average for 2025 (a tax-return translation rate); the Federal Reserve H.10 rate for 6 Nov 2026 is 6.6760", "US-FX-01", "china_row", chk_rate_basis,
     "Lines that use 7.129 in a cost, fee or rate context. Not an error in itself: it shows which sections price a 2026 transfer at the 2025 average."),
    ("RV-05", "Emigrant property transfer paid out in stages", "Staging was abolished in 2014; the bank may remit in one payment or several", "CN-FX-11", "vi_2", chk_staging,
     "Lines that describe halves, instalments or stages for an emigrant transfer without mentioning the 2014 change."),
    ("RV-06", "Foreign tax credit described as dollar-for-dollar", "The IRS says a credit \"may\" be available, only qualifying taxes count, and only the treaty-reduced tax qualifies", "US-TAX-02", "treaty_limit", chk_ftc,
     "Lines that say dollar-for-dollar with no limiting word on the same line."),
    ("RV-07", "Foreign earned income exclusion amount for 2026 / 2027", "", "US-TAX-04", "amounts", chk_feie,
     "The IRS page read in this session lists the amount only for 2020 to 2023. The figures $132,900 and $137,300 were not re-read here."),
    ("RV-08", "PRC late-payment surcharge on overdue tax", "0.05% of the overdue tax per day", "CN-TAX-05", "art32", chk_late,
     "Counts where the surcharge is mentioned. A section that discusses unpaid PRC tax without it leaves out a cost that grows every day."),
    ("RV-09", "Official pages linked over http instead of https", "Same pages are served over https", "CN-FX-12", "q18", chk_http,
     "Plain-http links to official hosts."),
]


def main():
    as_of = sys.argv[1] if len(sys.argv) > 1 else ""
    commit = subprocess.run(["git", "rev-parse", "--short", "origin/main"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    files = list(tracked())
    res = {c[0]: {"id": c[0], "figure": c[1], "verified": c[2], "source": c[3], "quote": c[4], "how": c[6],
                  "match_files": set(), "differ_files": set(), "unverified_files": set(),
                  "differ_sections": set(), "match_sections": set(), "examples": []} for c in CHECKS}
    sections = set()
    for path in files:
        sections.add(section(path))
        for n, line in text_lines(path):
            for cid, _f, _v, _s, _q, fn, _h in CHECKS:
                hit = fn(line)
                if not hit:
                    continue
                kind, m = hit
                r = res[cid]
                r[{"match": "match_files", "differs": "differ_files", "unverified": "unverified_files"}[kind]].add(path)
                (r["match_sections"] if kind == "match" else r["differ_sections"]).add(section(path))
                want = "match" if cid in ("RV-04", "RV-08") else kind
                if kind == want and kind != "match" or (cid in ("RV-04", "RV-08") and kind == "match"):
                    seen = {e["path"] for e in r["examples"]}
                    if path not in seen and len(r["examples"]) < MAX_EXAMPLES:
                        r["examples"].append({"path": path, "line": n, "text": clip(line, m)})
    # sections whose landing page is not linked from the root hub
    hub = (ROOT / "index.html").read_text(encoding="utf-8", errors="replace")
    linked = set(re.findall(r'href="\.?/?([A-Za-z0-9_.-]+)/', hub))
    tops = sorted({p.split("/")[0] for p in subprocess.run(["git", "ls-files", "*/index.html"], cwd=ROOT, capture_output=True, text=True).stdout.splitlines()
                   if p.count("/") == 1 and not p.startswith(SKIP_PREFIX)})
    unlinked = [t for t in tops if t not in linked]
    out = {"as_of": as_of, "main_commit": commit, "files_scanned": len(files), "sections_scanned": len(sections),
           "hub": {"sections_with_landing_page": len(tops), "linked_from_hub": len([t for t in tops if t in linked]), "not_linked": unlinked},
           "checks": []}
    for cid, *_ in CHECKS:
        r = res[cid]
        for k in ("match_files", "differ_files", "unverified_files", "differ_sections", "match_sections"):
            r[k] = sorted(r[k])
        r["counts"] = {"match_files": len(r["match_files"]), "differ_files": len(r["differ_files"]),
                       "unverified_files": len(r["unverified_files"])}
        for k in ("match_files", "differ_files", "unverified_files"):
            del r[k]
        out["checks"].append(r)
    (HERE / "data" / "review.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("review: %d files in %d sections at main %s" % (len(files), len(sections), commit))
    for r in out["checks"]:
        print(" ", r["id"], r["counts"], "differ in:", ", ".join(r["differ_sections"][:8]))
    print("  hub:", out["hub"])


if __name__ == "__main__":
    main()
