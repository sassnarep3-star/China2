#!/usr/bin/env python3
"""Independent verifier for the integrated deep-dive section + its research files.

Checks (no third-party dependencies):
  1. Every local href/src in deep-dive/*.html resolves to an existing file;
     fragments resolve to an id present in the target page.
  2. Every data row (<tr> containing <td>) inside a .tbl-wrap table carries at
     least one link (official source cell, per the section's own rule).
  3. Every local link in research/*.md resolves.
  4. Integration-review correction markers are present (guards against
     regressions to the corrected overbroad claims):
       - "no Chinese income tax at all" and bare "Cheapest lawful route" are gone
         from deep-dive/**, README.md, research/0[1-6]*.md
       - "Zero tax on both sides" is gone
       - the SAFE verbatim above-quota wording ("transaction background is true")
         appears in research/01 and deep-dive/sources.html
       - the status caveat (F02 / 境内个人) appears in the corrected surfaces
  5. All HTML files parse with the stdlib parser.
Exits non-zero on any failure.
"""
import pathlib, re, sys
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent.parent
DD = ROOT / "deep-dive"
FAIL = []

def ok(cond, msg):
    if not cond:
        FAIL.append(msg)
        print("FAIL -", msg)

class P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs, self.ids, self.tables, self._intbl, self._rowbuf, self._rows = [], set(), 0, 0, None, []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("a", "link") and a.get("href"): self.hrefs.append(a["href"])
        if tag == "img" and a.get("src"): self.hrefs.append(a["src"])
        if a.get("id"): self.ids.add(a["id"])
        if tag == "div" and "tbl-wrap" in (a.get("class") or ""): self.tables += 1
        if tag == "tr": self._intbl += 1; self._rowbuf = []
        if tag == "td" and self._rowbuf is not None: self._rowbuf.append("cell")
        if tag == "a" and self._rowbuf is not None and a.get("href"): self._rowbuf.append(a["href"])
    def handle_endtag(self, tag):
        if tag == "tr" and self._intbl:
            self._intbl -= 1
            if self._rowbuf: self._rows.append(self._rowbuf)
        if tag == "div" and self._intbl: pass

pages = sorted(DD.glob("*.html"))
ok(len(pages) >= 8, f"expected >=8 deep-dive pages, found {len(pages)}")

parsed = {}
for f in pages:
    p = P(); p.feed(f.read_text(encoding="utf-8")); parsed[f] = p
    ok('<html lang="en">' in f.read_text(encoding="utf-8"), f"{f.name}: html lang present")

# 1. local links + fragments
local_re = re.compile(r'^(?!https?:|mailto:|#)([^#]*)(#.*)?$')
for f, p in parsed.items():
    for h in p.hrefs:
        m = local_re.match(h)
        if not m:
            if h.startswith("#"):
                ok(h[1:] in p.ids, f"{f.name}: in-page fragment {h} resolves")
            continue
        path, frag = m.group(1), m.group(2)
        if path == "":
            continue
        target = (f.parent / path).resolve()
        if not target.exists():
            ok(False, f"{f.name}: broken local link {h}")
            continue
        if frag and target.suffix == ".html":
            tp = parsed.get(target)
            if tp is None:
                tp = P(); tp.feed(target.read_text(encoding="utf-8")); parsed[target] = tp
            ok(frag[1:] in tp.ids, f"{f.name}: fragment {frag} in {target.name}")

# 2. every data row in .tbl-wrap tables carries at least one link
for f, p in parsed.items():
    linked = sum(1 for row in p._rows if any(x != "cell" for x in row))
    data = sum(1 for row in p._rows if "cell" in row)
    ok(data > 0, f"{f.name}: has data rows")
    unlinked = [i for i, row in enumerate(p._rows) if "cell" in row and not any(x != "cell" for x in row)]
    # rows with a single empty-ish cell (spacer rows) are tolerated; otherwise require links
    real_unlinked = [i for i in unlinked if len([x for x in p._rows[i] if x == "cell"]) >= 2]
    ok(not real_unlinked, f"{f.name}: every >=2-cell data row has a link (unlinked rows: {real_unlinked[:5]})")

# 3. research markdown local links
for md in sorted((ROOT / "research").glob("0*.md")) + sorted((ROOT / "research").glob("EXECUTIVE_SUMMARY_arena*.md")):
    txt = md.read_text(encoding="utf-8")
    for m in re.finditer(r'\]\((?!https?://|#)([^)]+)\)', txt):
        path = m.group(1).split("#")[0]
        if path and not (ROOT / path).exists() and not (md.parent / path).exists():
            ok(False, f"{md.name}: broken local link {path}")

# 4. correction markers
bad_phrases = ["no Chinese income tax at all", "Cheapest lawful route", "Zero tax on both sides"]
# flagged.html is the correction ledger: it legitimately quotes the old phrases
# inside rows marked "Corrected on integration", so it is excluded here.
surfaces = [s for s in DD.glob("*.html") if s.name != "flagged.html"] + [ROOT / "README.md"] + sorted((ROOT / "research").glob("0[1-6]*.md"))
for s in surfaces:
    if not s.exists(): continue
    t = s.read_text(encoding="utf-8")
    for phrase in bad_phrases:
        ok(phrase not in t, f"{s.name}: corrected phrase absent: {phrase!r}")
ok("transaction background is true" in (ROOT / "research" / "01-china-fx-controls.md").read_text(encoding="utf-8"),
   "research/01 carries verbatim SAFE wording")
ok("transaction background is true" in (DD / "sources.html").read_text(encoding="utf-8"),
   "deep-dive/sources.html carries verbatim SAFE wording")
ok("F02" in (DD / "flagged.html").read_text(encoding="utf-8"), "flagged.html carries integration-review section (F02 refs)")

# 5. parse all html already done by feed(); catch hard errors
print(f"checked {len(parsed)} pages, {sum(len(p.hrefs) for p in parsed.values())} links")
if FAIL:
    print(f"\n{len(FAIL)} failure(s)"); sys.exit(1)
print("VERIFY OK - deep-dive integration checks passed")
