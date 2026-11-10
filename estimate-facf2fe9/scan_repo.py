#!/usr/bin/env python3
"""Line-by-line scan of the repository for values this session re-read today.

Writes data/repo_scan.json (a dated snapshot). It is run by hand, not in CI:
other sessions keep adding files, so a live re-scan would not be reproducible.
"""
import json, re, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PATTERNS = [
    ("rate_7129", r"7\.129", "CNY per USD 7.129 (IRS 2025 yearly average) used as a conversion rate or cited"),
    ("rate_710", r"7\.10(?![0-9])", "CNY per USD 7.10 model assumption"),
    ("rate_69", r"(?<![0-9.])6\.9(?![0-9])", "CNY per USD 6.9 convention"),
    ("spread_band", r"0\.30?\s?%\s?[-–]\s?1\.50?\s?%", "modelled wire spread band 0.3%-1.5%"),
    ("usd_8697", r"86\.97", "USD 86.97 = HSBC fee cap of CNY 620 restated at 7.129"),
    ("usd_3086", r"30\.86", "USD 30.86 = HSBC minimum fee of CNY 220 restated at 7.129"),
    ("boards", r"boc\.cn|icbc\.com\.cn|abchina\.com|cmbchina\.com|wealth\.ccb\.com|bankcomm\.com", "any citation of a mainland bank's own site"),
    ("ann40", r"2013年第40号|Announcement 2013 No\. ?40|税务备案", "outbound tax-filing rule (SAT/SAFE 2013 No. 40)"),
    ("emigrant", r"移民财产|emigrant", "emigrant asset-transfer route"),
    ("s988", r"§\s?988|section 988|Section 988|26 U\.?S\.?C\.? ?§? ?988", "26 USC 988 mentions"),
]
PATTERN_SOURCES = {'rate_7129': ['U02', 'B01'], 'rate_710': ['B01'], 'rate_69': ['B01'], 'spread_band': ['B01', 'B04'], 'usd_8697': ['T07', 'B06'], 'usd_3086': ['T07', 'B06'], 'boards': ['B01', 'B02', 'B03', 'B04', 'B05'], 'ann40': ['R10'], 'emigrant': ['R12'], 's988': ['U01']}
EXT = {".md", ".json", ".html", ".py", ".js", ".mjs", ".csv", ".txt", ".yml", ".css"}
files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split("\n")
# ladder/audit.html is a generated inventory of every file in the repository (including this section),
# so it is left out: scanning it would make this snapshot depend on itself.
SKIP = {"ladder/audit.html"}
files = sorted(f for f in files if f and not f.startswith("estimate-facf2fe9/") and f not in SKIP and Path(f).suffix in EXT)
out = {"scanned_files": len(files), "lines": 0, "patterns": []}
texts = {}
for f in files:
    try:
        texts[f] = (ROOT / f).read_text(encoding="utf-8", errors="replace").split("\n")
    except OSError:
        continue
    out["lines"] += len(texts[f])
for key, rx, label in PATTERNS:
    cre = re.compile(rx)
    hits = []
    for f, lines in texts.items():
        ln = [i + 1 for i, l in enumerate(lines) if cre.search(l)]
        if ln:
            hits.append({"file": f, "count": len(ln), "first_line": ln[0]})
    hits.sort(key=lambda h: (-h["count"], h["file"]))
    out["patterns"].append({"key": key, "label": label, "regex": rx, "sources": PATTERN_SOURCES[key], "files": len(hits),
                            "lines": sum(h["count"] for h in hits), "top": hits[:8]})
head = subprocess.run(["git", "rev-parse", "--short", "origin/main"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
out["main_commit"] = head
with open(HERE / "data" / "repo_scan.json", "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1); fh.write("\n")
print(out["scanned_files"], "files,", out["lines"], "lines, main", head)
for p in out["patterns"]:
    print(f'{p["key"]:12s} files={p["files"]:3d} lines={p["lines"]:5d}  top: ' + ", ".join(f'{h["file"]}:{h["first_line"]}({h["count"]})' for h in p["top"][:4]))
