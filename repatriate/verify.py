#!/usr/bin/env python3
"""Independent verifier for repatriate/ (session arena/3e494fa5-china2).

Does NOT import build.py. Recomputes every published number from the raw JSON
inputs, enforces the blank-if-unverified policy, checks that every table row
carries an external source link from the allowlist, and resolves every local
link/anchor in the generated HTML. Exit code 0 = pass.
"""
import csv
import json
import math
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
ERRORS = []
CHECKS = [0]


def check(cond, msg):
    CHECKS[0] += 1
    if not cond:
        ERRORS.append(msg)


def load(name):
    return json.loads((ROOT / "data" / name).read_text())


sources_doc = load("sources.json")
rules_doc = load("rules.json")
methods_doc = load("methods.json")
flags_doc = load("flags.json")
audit_doc = load("audit.json")
SOURCES = {s["id"]: s for s in sources_doc["sources"]}
RULES = {p["id"]: p for p in rules_doc["parameters"]}
METHODS = methods_doc["methods"]
FLAGS = {f["id"]: f for f in flags_doc["flags"]}
RATE = rules_doc["reference_rate"]["cny_per_usd"]

OFFICIAL_HOSTS = (
    "safe.gov.cn", "www.safe.gov.cn", "pbc.gov.cn", "www.pbc.gov.cn",
    "gov.cn", "www.gov.cn", "gqb.gov.cn", "www.gqb.gov.cn",
    "fgk.chinatax.gov.cn", "chinatax.gov.cn", "www.chinatax.gov.cn",
    "irs.gov", "www.irs.gov", "cbp.gov", "www.cbp.gov",
    "govinfo.gov", "www.govinfo.gov", "ecfr.gov", "www.ecfr.gov",
    "fincen.gov", "www.fincen.gov",
)
PROVIDER_HOSTS = ("hsbc.com.cn", "www.hsbc.com.cn", "wise.com", "westernunion.com", "www.westernunion.com")
REPO_HOSTS = ("github.com",)

# 1. Source registry integrity
check(RATE == 7.129, "reference rate must be the fetched IRS 2025 average 7.129")
for sid, s in SOURCES.items():
    check(s["status"] == "fetched", f"{sid}: source must be fetched, got {s['status']}")
    host = urlparse(s["url"]).hostname or ""
    check(host in OFFICIAL_HOSTS or host in PROVIDER_HOSTS, f"{sid}: non-allowlisted host {host}")
    check(s["url"].startswith("https://"), f"{sid}: source URL must be https")
    check(bool(s.get("locator")) and bool(s.get("facts")), f"{sid}: missing locator/facts")
check(len(SOURCES) >= 25, "expected >=25 fetched sources")

# 2. Cross-references
def check_refs(ids, where):
    for sid in ids:
        check(sid in SOURCES, f"{where}: unknown source id {sid}")

for p in rules_doc["parameters"]:
    check(p["source"] in SOURCES, f"rule {p['id']}: bad source")
for m in METHODS:
    check_refs(m["sources"], m["id"])
    check(m["status"] in ("lawful-conditional", "rejected-unlawful"), f"{m['id']}: bad status")
    check(len(m["steps"]) >= 1 and len(m["pros"]) >= 1 and len(m["cons"]) >= 1, f"{m['id']}: missing steps/pros/cons")
for f in flags_doc["flags"]:
    check_refs(f["sources"], f["id"])
for a in audit_doc["findings"]:
    check_refs(a["sources"], a["id"])
    check(urlparse(a["repo"]).hostname in REPO_HOSTS, f"{a['id']}: repo link must be github.com")

# 3. Independent recomputation of every ladder row
exports = json.loads((ROOT / "exports" / "cost-ladders.json").read_text())
rows = exports["rows"]
check(len(rows) == len(METHODS) * 40, f"expected {len(METHODS)*40} rows, got {len(rows)}")
by_method = {m["id"]: m for m in METHODS}
seen = set()


def tt_fee_cny(cny_amount):
    return min(max(cny_amount * 0.001, 100.0), 500.0) + 120.0


for r in rows:
    mid, a = r["method"], r["amount_usd"]
    key = (mid, a)
    check(key not in seen, f"duplicate row {key}")
    seen.add(key)
    m = by_method[mid]
    check(a % 10000 == 0 and 10000 <= a <= 400000, f"{key}: bad increment")
    check(r["sources"] and all(s in SOURCES for s in r["sources"]), f"{key}: row missing valid sources")
    cny = a * RATE
    check(abs(r["amount_cny_ref"] - round(cny, 2)) < 0.011, f"{key}: cny reference mismatch")
    t = m["cost_model"]["type"]
    if t == "hsbc_tt":
        expect = round(tt_fee_cny(cny) / RATE, 2)
        check(r["published_fee_usd"] == expect, f"{key}: fee {r['published_fee_usd']} != recomputed {expect}")
    elif t == "hsbc_tt_quota":
        years = math.ceil(a / 50000)
        rem, total = a, 0.0
        while rem > 0:
            tr = min(rem, 50000)
            total += tt_fee_cny(tr * RATE)
            rem -= tr
        check(r["published_fee_usd"] == round(total / RATE, 2), f"{key}: quota fee mismatch")
        check(r["constraint"].startswith(f"{years} calendar year"), f"{key}: quota years mismatch")
    elif t == "global_transfer":
        check(r["published_fee_usd"] == 0.0, f"{key}: GT Premier/PB must be 0")
        check("unknown" in r["constraint_detail"], f"{key}: Advance uncertainty must be disclosed")
    elif t == "wise":
        check(r["published_fee_usd"] is None, f"{key}: Wise fee must stay blank")
        check(r["constraint"].startswith(f"{math.ceil(cny / 300000)} transfer"), f"{key}: Wise transfer count mismatch")
    elif t == "atm":
        check(r["published_fee_usd"] is None, f"{key}: ATM fee must stay blank")
        check(r["constraint"].startswith(f"{math.ceil(cny / 100000)} calendar year"), f"{key}: ATM years mismatch")
        check(f"{math.ceil(cny / 10000)} withdrawal days" in r["constraint_detail"], f"{key}: ATM days mismatch")
    elif t == "cash_carry":
        check(r["published_fee_usd"] == 0.0, f"{key}: HSBC notes withdrawal published fee is 0")
        check(r["constraint"] == f"{math.ceil(a / 5000)} trips (no permit)", f"{key}: carry trips mismatch")
        check(f"{math.ceil(a / 10000)} trips with bank permits" in r["constraint_detail"], f"{key}: permit trips mismatch")
    elif t == "rmb_carry":
        check(r["published_fee_usd"] is None, f"{key}: offshore conversion must stay blank")
        check(r["constraint"] == f"{math.ceil(cny / 20000)} trips", f"{key}: RMB trips mismatch")
    elif t == "reconversion":
        check(r["published_fee_usd"] is None, f"{key}: reconversion fee must stay blank")
        check(r["constraint"].startswith(f"{math.ceil(a / 500)} bank days"), f"{key}: reconversion days mismatch")
    elif t == "penalty":
        check(r["published_fee_usd"] is None, f"{key}: rejected method must not have a price")
        check(r["fine_standard_max_usd"] == round(a * 0.30, 2), f"{key}: fine 30% mismatch")
        check(r["fine_serious_min_usd"] == round(a * 0.30, 2), f"{key}: serious min mismatch")
        check(r["fine_serious_max_usd"] == round(a * 1.00, 2), f"{key}: serious max mismatch")
        check(m["status"] == "rejected-unlawful", f"{key}: penalty model on lawful method")
    else:
        check(r["published_fee_usd"] is None, f"{key}: unknown model must stay blank")

for m in METHODS:
    amounts = sorted(r["amount_usd"] for r in rows if r["method"] == m["id"])
    check(amounts == list(range(10000, 400001, 10000)), f"{m['id']}: must have exactly 40 increments")

# 4. Spot-check headline numbers against values read from the fetched sources
check(RULES["P01"]["value"] == 50000, "quota must be 50000 (S01)")
check(RULES["P04"]["value"] == 100000, "ATM annual cap must be RMB100000 (S07)")
check(RULES["P08"]["value"] == 20000, "RMB carry must be 20000 (S11)")
check(RULES["P22"]["value"] is None, "correspondent charges must stay null")
check(RULES["P29"]["value"] == 132900, "FEIE 2026 must be 132900 (S22)")
check(RULES["P30"]["value"]["non_willful_usd"] == 16536, "FBAR non-willful 16536 (S19)")
check(RULES["P30"]["value"]["willful_usd"] == 165353, "FBAR willful 165353 (S19)")
check(RULES["P19"]["value"] is None and RULES["P20"]["value"] is None, "Wise/WU fees must stay null")

# 5. CSV parity
with (ROOT / "exports" / "cost-ladders.csv").open() as fh:
    csv_rows = list(csv.DictReader(fh))
check(len(csv_rows) == len(rows), "CSV row count must equal JSON")
for cr in csv_rows:
    if cr["published_fee_usd"] == "":
        continue
    jr = next(r for r in rows if r["method"] == cr["method"] and r["amount_usd"] == int(cr["amount_usd"]))
    check(abs(float(cr["published_fee_usd"]) - jr["published_fee_usd"]) < 0.001, f"CSV/JSON fee mismatch {cr['method']} {cr['amount_usd']}")

# 6. HTML checks: every table row has an external allowlisted link; local links resolve
PAGES = ["index.html", "methods.html", "costs.html", "taxes.html", "sources.html", "audit.html", "flagged.html"]
page_text = {}
for p in PAGES:
    path = ROOT / p
    check(path.exists(), f"missing page {p}")
    text = path.read_text()
    page_text[p] = text
    check('name="viewport"' in text, f"{p}: missing mobile viewport")
    check('assets/style.css' in text, f"{p}: missing stylesheet")
    for href in re.findall(r'href="([^"#]+?)(?:#[^"]*)?"', text):
        if href.startswith(("http://", "https://", "mailto:")):
            continue
        target = (ROOT / href.split("#")[0])
        check(target.exists(), f"{p}: broken local link {href}")
    for anchor_page, anchor in re.findall(r'href="([a-z-]+\.html)#([^"]+)"', text):
        check(anchor_page in page_text or (ROOT / anchor_page).exists(), f"{p}: link to missing page {anchor_page}")
    # every tbody row carries >=1 external link
    tbodies = re.findall(r"<tbody>(.*?)</tbody>", text, flags=re.S)
    for tb in tbodies:
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", tb, flags=re.S):
            links = re.findall(r'href="(https://[^"]+)"', tr)
            check(len(links) >= 1, f"{p}: table row without external source link: {tr[:120]}")
            for link in links:
                host = urlparse(link).hostname or ""
                check(host in OFFICIAL_HOSTS or host in PROVIDER_HOSTS or host in REPO_HOSTS,
                      f"{p}: row link outside allowlist: {host}")
    # flag references exist
    for fid in re.findall(r'flagged\.html#(F\d+)', text):
        check(fid in FLAGS, f"{p}: unknown flag {fid}")

# anchors resolve after all pages loaded
for p, text in page_text.items():
    for anchor_page, anchor in re.findall(r'href="([a-z-]+\.html)#([^"]+)"', text):
        check(f'id="{anchor}"' in page_text.get(anchor_page, ""), f"{p}: broken anchor {anchor_page}#{anchor}")
    for anchor in re.findall(r'href="#([^"]+)"', text):
        check(f'id="{anchor}"' in text, f"{p}: broken same-page anchor #{anchor}")

# cost page must contain all 680 rows and blank markers for unverified cells
cost_rows = re.findall(r"<tr[^>]*>", page_text["costs.html"].split("<tbody>", 1)[-1]) if "<tbody>" in page_text["costs.html"] else []
n_cost_trs = sum(len(re.findall(r"<tr[^>]*>", tb)) for tb in re.findall(r"<tbody>(.*?)</tbody>", page_text["costs.html"], flags=re.S))
check(n_cost_trs == len(METHODS) * 40, f"costs.html must render {len(METHODS)*40} rows, got {n_cost_trs}")
check('class="blank"' in page_text["costs.html"], "costs.html must render blank markers for unverified cells")
check("fee floors, not all-in costs" in page_text["costs.html"], "costs.html must carry the fee-floor caveat")
check("Rejected" in page_text["methods.html"] and "not</strong> recommendations" in page_text["methods.html"], "rejected methods must be labeled non-recommendations")

# 7. Policy strings that must be present
check("blank is never a zero" in page_text["flagged.html"], "flagged page must state blank != zero")
check("not advice" in page_text["index.html"], "index must carry research-not-advice tag")
for m in METHODS:
    if m["status"] == "rejected-unlawful":
        check(f'id="{m["id"]}"' in page_text["methods.html"], f"rejected method {m['id']} missing from catalogue")

if ERRORS:
    print(f"FAIL: {len(ERRORS)} of {CHECKS[0]} checks failed")
    for err in ERRORS[:40]:
        print(" -", err)
    sys.exit(1)
print(f"PASS verify-repatriate: {CHECKS[0]} checks; {len(SOURCES)} fetched sources; "
      f"{len(METHODS)} methods x 40 increments = {len(rows)} cost rows independently recomputed; "
      f"every table row source-linked; blanks enforced; local links/anchors resolved.")
