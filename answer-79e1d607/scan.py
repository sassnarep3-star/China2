#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Point-in-time, line-by-line scan of the repository for figures that today's official reading contradicts.

    python3 answer-79e1d607/scan.py     # writes answer-79e1d607/data/repo-scan.json

Reads every line of every tracked text file (git ls-files) except this section, the task board and
bulk exports. A hit is a pattern match, not a verdict. Run by hand; build.py only renders the stored result,
so later changes elsewhere in the repository do not make this section stale in CI."""
import html, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import content as C  # noqa: E402

SKIP_PREFIX = ("answer-79e1d607/", ".github/")
SKIP_FILES = ("COORDINATION.md", "package-lock.json")
SKIP_EXT = (".png", ".jpg", ".jpeg", ".gif", ".ico", ".woff", ".woff2", ".pdf", ".zip", ".csv")


def main():
    files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split("\n")
    commit = subprocess.run(["git", "rev-parse", "--short", "origin/main"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    rules = {rid: {"rx": re.compile(rx), "lines": 0, "per": {}, "examples": []} for rid, rx, *_ in C.REVIEW_RULES}
    nfiles = nlines = 0
    for f in sorted(x for x in files if x):
        if f.startswith(SKIP_PREFIX) or f in SKIP_FILES or f.lower().endswith(SKIP_EXT) or "/exports/" in f:
            continue
        try:
            text = open(os.path.join(ROOT, f), encoding="utf-8").read()
        except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
            continue
        nfiles += 1
        for n, line in enumerate(text.split("\n"), 1):
            nlines += 1
            if len(line) > 20000:
                continue
            for rid, r in rules.items():
                m = r["rx"].search(line)
                if not m:
                    continue
                r["lines"] += 1
                r["per"][f] = r["per"].get(f, 0) + 1
                if len(r["examples"]) < 4 and r["per"][f] == 1:
                    plain = html.unescape(re.sub(r"<[^>]*>", " ", line))
                    pm = r["rx"].search(plain)
                    if pm:
                        snippet = plain[max(0, pm.start() - 70):pm.end() + 70]
                    else:
                        snippet = line[max(0, m.start() - 70):m.end() + 70]
                    r["examples"].append({"file": f, "line": n, "text": re.sub(r"\s+", " ", snippet).strip()[:170]})
    out = {"meta": {"commit": commit, "files": nfiles, "lines": nlines,
                    "skipped": "this section, .github/, COORDINATION.md, package-lock.json, */exports/*, images and CSV"},
           "rules": {rid: {"lines": r["lines"], "files": len(r["per"]),
                           "top_files": sorted(r["per"].items(), key=lambda kv: (-kv[1], kv[0]))[:6],
                           "examples": r["examples"]} for rid, r in rules.items()}}
    with open(os.path.join(HERE, "data", "repo-scan.json"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print("scanned %d files, %d lines at %s" % (nfiles, nlines, commit))
    for rid, r in out["rules"].items():
        print(" ", rid, r["lines"], "lines in", r["files"], "files")


if __name__ == "__main__":
    main()
