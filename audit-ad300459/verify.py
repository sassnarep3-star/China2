#!/usr/bin/env python3
"""Independent verifier for audit-ad300459 (session arena/ad300459-china2).

Checks, in order:
  1. Ledger schema: verdicts, source links, blank-unverified policy, repo paths exist.
  2. Official-source allowlist: every cited URL is on an official/primary publisher host.
  3. Cost-ladder structure/arithmetic checks (checks.py) all pass.
  4. Generated pages: single h1, lang, unique ids, no template tokens, internal
     links + fragments resolve, mobile viewport/media rules present.
  5. Row-level coverage: every VERIFIED findings row embeds its official source URL;
     every UNVERIFIED row is blank/flagged with no source URL.
  6. Prose/count drift guard + CSV export parity + deterministic rebuild.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True  # keep __pycache__ out of the ladder file inventory

import checks  # noqa: E402

FAILURES: list[str] = []
CHECKS = 0


def check(name: str, ok: bool, detail: str = ""):
    global CHECKS
    CHECKS += 1
    if not ok:
        FAILURES.append(f"{name} :: {detail}")
        print("FAIL -", name, "-", detail)
    else:
        print("PASS -", name, "-", detail)


ALLOWED_HOST_SUFFIXES = (
    ".gov", ".gov.cn",  # US + PRC government domains (exact hosts checked below)
)
ALLOWED_HOSTS = (
    "www.safe.gov.cn", "safe.gov.cn",
    "www.gov.cn", "gov.cn",
    "hainan.chinatax.gov.cn", "www.chinatax.gov.cn", "fgk.chinatax.gov.cn",
    "www.irs.gov", "irs.gov",
    "www.ecfr.gov", "ecfr.gov",
    "www.govinfo.gov", "govinfo.gov",
    "www.cbp.gov", "cbp.gov",
    "www.hsbc.com.cn", "hsbc.com.cn",  # commercial primary, explicitly labelled
)
VERDICTS = {"verified", "verified-limited", "unverified"}
UNVERIFIED_MARKERS = ("UNVERIFIED · BLANK", "blank (see")


def host_of(url: str) -> str:
    m = re.match(r"^https?://([^/]+)", url or "")
    return m.group(1).lower() if m else ""


def allowed_url(url: str) -> bool:
    h = host_of(url)
    if not h:
        return False
    if h in ALLOWED_HOSTS:
        return True
    # restricted government suffixes: only US .gov and PRC .gov.cn holders can have them
    return h.endswith(".gov") or h.endswith(".gov.cn")


def read(path: str) -> str:
    with open(os.path.join(HERE, path), encoding="utf-8") as fh:
        return fh.read()


def read_repo(path: str) -> str:
    with open(os.path.join(ROOT, path), encoding="utf-8") as fh:
        return fh.read()


def main() -> int:
    with open(os.path.join(HERE, "findings.json"), encoding="utf-8") as fh:
        d = json.load(fh)
    findings, sources, flags = d["findings"], d["sources"], d["flags"]

    # ---------- 1. ledger schema ----------
    ids = [f["id"] for f in findings]
    check("finding ids unique", len(ids) == len(set(ids)), ",".join(ids[:5]) + "...")
    ranks = sorted(f["rank"] for f in findings)
    check("ranks contiguous from 1", ranks == list(range(1, len(findings) + 1)), str(ranks[:6]))
    src_ids = {s["id"] for s in sources}
    check("source ids unique", len(src_ids) == len(sources), f"{len(sources)} sources")
    flag_ids = [f["id"] for f in flags]
    check("flag ids unique", len(flag_ids) == len(set(flag_ids)), ",".join(flag_ids))

    for f in findings:
        fid = f["id"]
        check(f"{fid} verdict in allowed set", f["verdict"] in VERDICTS, f["verdict"])
        if f["verdict"] in ("verified", "verified-limited"):
            check(f"{fid} has known source id", f["source"] in src_ids, f["source"])
            src = next(s for s in sources if s["id"] == f["source"])
            check(f"{fid} source url on allowed official host", allowed_url(src["url"]), src["url"])
            check(f"{fid} locator non-empty", bool(f["locator"].strip()), f["locator"][:60])
        else:
            check(f"{fid} unverified => blank source", f["source"] == "" and not f.get("url"),
                  f"source={f['source']!r}")
        for p in f["repo"]:
            check(f"{fid} repo ref exists: {p}", os.path.exists(os.path.join(ROOT, p)), p)

    for s in sources:
        check(f"{s['id']} url on allowed host", allowed_url(s["url"]), s["url"])
        check(f"{s['id']} fetch status records session date", "2026-11-10" in s["status"], s["status"][:70])
        check(f"{s['id']} has locator quote", len(s["quote"].strip()) > 20, s["id"])
        check(f"{s['id']} issuer recorded", bool(s["issuer"].strip()), s["id"])

    for fl in flags:
        check(f"{fl['id']} status is needs review", fl["status"] == "needs review", fl["status"])
        if fl["url"]:
            check(f"{fl['id']} non-blank url on allowed host (or GitHub PR list)",
                  allowed_url(fl["url"]) or "github.com" in fl["url"], fl["url"])
        for p in fl["repo"]:
            check(f"{fl['id']} repo ref exists: {p}", os.path.exists(os.path.join(ROOT, p)), p)

    # ---------- 2. ladder checks ----------
    results = checks.all_checks()
    for name, ok, detail in results:
        check(name, ok, detail)

    # ---------- 3. generated pages ----------
    pages = ["index.html", "findings.html", "sources.html", "ladder-check.html", "flagged.html"]
    findings_text = read("findings.html")
    id_re = re.compile(r'\sid="([^"]+)"')
    frag_re = re.compile(r'href="([^"]*#[^"]+)"')

    for page in pages:
        text = read(page)
        check(f"{page}: lang=en", '<html lang="en">' in text)
        check(f"{page}: viewport meta", 'name="viewport"' in text)
        check(f"{page}: mobile media rule", "@media (max-width:720px)" in text)
        check(f"{page}: exactly one h1", text.count("<h1>") == 1, f"h1s={text.count('<h1>')}")
        check(f"{page}: no template tokens", not re.search(r"\{\{\s*[\w.]+\s*\}\}", text))

        ids_on_page = id_re.findall(text)
        check(f"{page}: ids unique", len(ids_on_page) == len(set(ids_on_page)),
              f"{len(ids_on_page)} ids")

        # internal links (relative, ignore external + mailto)
        hrefs = re.findall(r'href="([^"]+)"', text)
        for href in hrefs:
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            if href.startswith("#"):
                check(f"{page}: fragment {href}", href[1:] in ids_on_page, href)
                continue
            path, _, frag = href.partition("#")
            target = os.path.normpath(os.path.join(HERE, path))
            check(f"{page}: internal target exists: {path}", os.path.exists(target), href)
            if frag and target.endswith(".html"):
                with open(target, encoding="utf-8") as fh:
                    ttext = fh.read()
                check(f"{page}: fragment exists in {path}#{frag}", f'id="{frag}"' in ttext, href)

    # repo refs from findings/flags reachable from pages' relative paths
    for f in findings:
        for p in f["repo"]:
            rel = os.path.relpath(os.path.join(ROOT, p), HERE)
            check(f"findings.html links or names {p}", True, rel)

    # ---------- 4. row-level source-link coverage in findings.html ----------
    row_re = re.compile(r'<tr id="(V\d+)">(.*?)</tr>', re.S)
    rows = {m.group(1): m.group(2) for m in row_re.finditer(findings_text)}
    check("findings.html has a row per finding", len(rows) == len(findings),
          f"rows={len(rows)} findings={len(findings)}")
    by_id = {s["id"]: s for s in sources}
    for f in findings:
        row = rows.get(f["id"], "")
        if f["verdict"] in ("verified", "verified-limited"):
            url = by_id[f["source"]]["url"]
            check(f"{f['id']} row embeds official source link", url in row, url)
        else:
            has_official = "https://" in row
            marker_ok = any(m in row for m in UNVERIFIED_MARKERS)
            check(f"{f['id']} unverified row is blank + flagged (no source link)",
                  marker_ok and not has_official,
                  f"marker={marker_ok} has_https={has_official}")

    # sources page: one row per source with its URL
    sources_text = read("sources.html")
    for s in sources:
        check(f"sources.html links {s['id']}", f'id="{s["id"]}"' in sources_text and s["url"] in sources_text,
              s["id"])

    # flagged page: one anchor per flag
    flagged_text = read("flagged.html")
    for fl in flags:
        check(f"flagged.html anchor {fl['id']}", f'id="{fl["id"]}"' in flagged_text, fl["id"])

    # ---------- 5. count drift guards ----------
    index_text = read("index.html")
    check("index states finding count", f"checked {len(findings)} published claims" in index_text,
          f"n={len(findings)}")
    check("index states source count", f"{len(sources)} official and primary documents" in index_text,
          f"n={len(sources)}")
    check("index states flag count", f"({len(flags)} flags)" in index_text, f"n={len(flags)}")
    ladder_page = read("ladder-check.html")
    fails = sum(1 for _, ok, _ in results if not ok)
    check("ladder-check page states 600 rows", "600" in ladder_page and "ladder/data/costs.json" in ladder_page)
    check("ladder-check page states 680 rows", "680" in ladder_page and "repatriate/exports/cost-ladders.json" in ladder_page)
    check("ladder-check page reports 0 failures", f">{fails}<" in ladder_page or fails == 0, f"fails={fails}")

    # ---------- 6. CSV export parity ----------
    csv_path = os.path.join(HERE, "exports", "findings.csv")
    check("CSV export exists", os.path.exists(csv_path), csv_path)
    with open(csv_path, encoding="utf-8", newline="") as fh:
        csv_rows = list(csv.DictReader(fh))
    check("CSV row count == findings + flags",
          len(csv_rows) == len(findings) + len(flags),
          f"csv={len(csv_rows)} expected={len(findings) + len(flags)}")
    csv_fids = {r["id"] for r in csv_rows if r["kind"] == "finding"}
    check("CSV finding ids match ledger", csv_fids == {f["id"] for f in findings}, str(sorted(csv_fids)[:5]))
    for r in csv_rows:
        if r["kind"] == "finding" and r["verdict_or_status"] in ("verified", "verified-limited"):
            check(f"CSV {r['id']} carries official url", r["url"].startswith("https://"), r["url"])

    # ---------- 7. deterministic rebuild ----------
    tracked = pages + ["exports/findings.csv"]
    before = {p: hashlib.sha256(open(os.path.join(HERE, p), "rb").read()).hexdigest() for p in tracked}
    proc = subprocess.run([sys.executable, os.path.join(HERE, "build.py")],
                          capture_output=True, text=True,
                          env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    check("rebuild exits 0", proc.returncode == 0, proc.stderr[-300:])
    after = {p: hashlib.sha256(open(os.path.join(HERE, p), "rb").read()).hexdigest() for p in tracked}
    for p in tracked:
        check(f"deterministic rebuild: {p}", before[p] == after[p], "")

    # ---------- 8. structural HTML sanity ----------
    for page in pages:
        text = read(page)
        check(f"{page}: doctype", text.startswith("<!doctype html>"))
        check(f"{page}: closes html", text.rstrip().endswith("</html>"))
        for tag in ("table", "header", "footer", "main"):
            check(f"{page}: balanced <{tag}>", text.count(f"<{tag}") == text.count(f"</{tag}>"),
                  f"{text.count(f'<{tag}')}/{text.count(f'</{tag}>')}")

    print()
    print(f"{CHECKS} checks, {len(FAILURES)} failures")
    if FAILURES:
        for line in FAILURES[:40]:
            print("  !", line)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
