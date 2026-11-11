#!/usr/bin/env python3
"""Independent verifier for guide-be3c20e8.

This deliberately does not import model.py or build.py.  It recomputes every
cost row from data/sources.json, checks blanks/flags, checks the generated
HTML, local links and anchors, checks every substantive table row for an
official source link, and verifies each review finding against its file:line
text.  `--structure` runs only the structural/browser-facing checks.

Run: python3 verify.py  [--structure]
"""
import csv
import json
import re
import sys
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = HERE / "data"
ASSETS = HERE / "assets"
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE))
import content  # noqa: E402  (editorial ledger only; not the model or builder)

STRUCTURE_ONLY = "--structure" in sys.argv
FAIL = []
COUNT = 0

def check(cond, message):
    global COUNT
    COUNT += 1
    if not cond:
        FAIL.append(message)

def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))

LEDGER = load("sources.json")
S = {s["id"]: s for s in LEDGER["sources"]}
F = {sid: s["figures"] for sid, s in S.items()}
COSTS = load("costs.json")
PEN_COSTS = load("penalty_costs.json")
REVIEW = load("review.json")
D = lambda x: Decimal(str(x))
Q2 = lambda x: x.quantize(D("0.01"), rounding=ROUND_HALF_UP)
Q4 = lambda x: x.quantize(D("0.0001"), rounding=ROUND_HALF_UP)
F2 = lambda x: float(Q2(x))
F4 = lambda x: float(Q4(x))
TIERS = list(range(10000, 400001, 10000))

def ceil_div(a, b):
    return int((a / b).to_integral_value(rounding=ROUND_CEILING))

def close(a, b, tol="0.005"):
    return abs(D(str(a)) - D(str(b))) <= D(tol)

# ---------------------------------------------------------------------------
# Ledger, exports and editorial template checks
# ---------------------------------------------------------------------------
check(len(S) == 34, f"source ledger should contain 34 sources, found {len(S)}")
check(len({s["id"] for s in LEDGER["sources"]}) == len(S), "source ids must be unique")
for s in LEDGER["sources"]:
    check(s["url"].startswith("https://"), f"{s['id']}: URL must be https")
    check(bool(s["publisher"] and s["title"] and s["locator"] and s["quote"] and s["reading"] and s["limits"]), f"{s['id']}: required fields present")
    check("..." not in s["quote"], f"{s['id']}: quote must not contain an ellipsis placeholder")
    check(isinstance(s["figures"], dict), f"{s['id']}: figures object")

source_tokens = set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", (HERE / "content.py").read_text(encoding="utf-8")))
extra_keys = {
    "PLACEHOLDER", "SOURCE_COUNT", "READ", "SCANNED_FILES", "COST_ROWS",
    "BOC_SPREAD_PCT", "HSBC_SPREAD_PCT", "BOC_SPREAD_400", "HSBC_SPREAD_400",
    "LOW_10_METHOD", "LOW_10_VALUE", "LOW_400_METHOD", "LOW_400_VALUE",
}
known_keys = set(content.PLACEHOLDERS) | extra_keys
check(source_tokens <= known_keys, f"unmapped content tokens: {sorted(source_tokens - known_keys)}")
for sid, key in set(re.findall(r'\b(?:fig|n)\("(B\d+)",\s*"([^"]+)"\)', (HERE / "content.py").read_text(encoding="utf-8"))):
    check(sid in F and key in F[sid], f"content figure {sid}/{key} missing from source ledger")

exports = sorted(DATA.glob("*.json")) + sorted(DATA.glob("*.csv"))
for p in exports:
    text = p.read_text(encoding="utf-8")
    check("{{" not in text, f"{p.name}: unresolved template token")
    check("http://" not in text, f"{p.name}: insecure http URL in export")
    if p.suffix == ".json":
        json.loads(text)
check(len(exports) >= 13, f"expected at least 13 data exports, found {len(exports)}")

methods_export = load("methods.json")["methods"]
questions_export = load("questions.json")["questions"]
layers_export = load("penalty_layers.json")["layers"]
flags_export = load("flags.json")["flags"]
summary_export = load("summary.json")["items"]
check(len(methods_export) == 20, "methods export should contain 20 routes")
check(len(questions_export) == 14, "questions export should contain 14 gates")
check(len(layers_export) == 12, "penalty export should contain 12 layers")
check(len(flags_export) == 23, "flags export should contain 23 items")
check(len(summary_export) == 7, "summary export should contain 7 conclusions")
for m in methods_export:
    if m["id"].startswith("U"):
        check(len(m["steps"]) == 0, f"{m['id']}: prohibited route must have no execution steps")
    check(set(m["sources"]) <= set(S), f"{m['id']}: unknown source id")
    check(set(m["flags"]) <= {f["id"] for f in content.FLAGS}, f"{m['id']}: unknown flag id")

# ---------------------------------------------------------------------------
# Independent cost arithmetic (full mode only)
# ---------------------------------------------------------------------------
if not STRUCTURE_ONLY:
    BOC_BUY = D(F["B01"]["boc_buy_tt_per100"]) / D(F["B01"]["per"])
    BOC_SELL = D(F["B01"]["boc_sell_tt_per100"]) / D(F["B01"]["per"])
    BOC_CASH_BUY = D(F["B01"]["boc_buy_cash_per100"]) / D(F["B01"]["per"])
    BOC_CASH_SELL = D(F["B01"]["boc_sell_cash_per100"]) / D(F["B01"]["per"])
    HSBC_BUY = D(F["B02"]["hsbc_buy_tt"])
    HSBC_SELL = D(F["B02"]["hsbc_sell_tt"])
    HSBC_CASH_BUY = D(F["B02"]["hsbc_buy_cash"])
    HSBC_CASH_SELL = D(F["B02"]["hsbc_sell_cash"])
    BOC_RATE, BOC_MIN, BOC_MAX, BOC_CABLE = (D(F["B03"][k]) for k in ("boc_tt_rate", "boc_tt_min_cny", "boc_tt_max_cny", "boc_cable_other_cny"))
    HSBC_RATE, HSBC_MIN, HSBC_MAX, HSBC_CABLE = (D(F["B04"][k]) for k in ("hsbc_tt_rate", "hsbc_tt_min_cny", "hsbc_tt_max_cny", "hsbc_cable_cny"))
    GT_USD = D(F["B04"]["hsbc_gt_advance_usd"])
    QUOTA = D(F["B08"]["annual_quota_usd"])
    WISE_BANK = D(F["B05"]["wise_bank_per_transfer_cny"])
    WISE_ALIPAY = D(F["B05"]["wise_alipay_per_transfer_cny"])
    CASH_FREE = D(F["B17"]["no_permit_usd"])
    CASH_BANK = D(F["B17"]["bank_permit_upper_usd"])
    ATM_YEAR = D(F["B16"]["atm_year_cny"])
    ATM_DAY = D(F["B16"]["atm_day_cny"])
    SAFE_DAYS = D(F["B14"]["accept_working_days"]) + D(F["B14"]["decision_working_days"])
    ADMIN_FEE = D(F["B14"]["admin_fee"])

    def sp(u, buy, sell):
        mid = (buy + sell) / 2
        return u * (sell - mid) / sell

    def cap(cny, rate, lo, hi, cable):
        return min(max(cny * rate, lo), hi) + cable

    def expected(usd, model):
        u = D(usd)
        cb, ch = u * BOC_SELL, u * HSBC_SELL
        sb, sh = sp(u, BOC_BUY, BOC_SELL), sp(u, HSBC_BUY, HSBC_SELL)
        if model == "boc_wire":
            fee = cap(cb, BOC_RATE, BOC_MIN, BOC_MAX, BOC_CABLE)
            return Q2(sb + fee / BOC_SELL), {"cny_debited": F2(cb), "spread_usd": F2(sb), "sender_fee_cny": F2(fee), "sender_fee_usd": F2(fee / BOC_SELL)}
        if model == "boc_quota":
            first = min(u, QUOTA)
            fee = cap(first * BOC_SELL, BOC_RATE, BOC_MIN, BOC_MAX, BOC_CABLE)
            return None, {"calendar_years": ceil_div(u, QUOTA), "first_transfer_usd": int(first), "first_transfer_known_usd": F2(sp(first, BOC_BUY, BOC_SELL) + fee / BOC_SELL)}
        if model == "boc_hold":
            return Q2(sb), {"cny_debited": F2(cb), "spread_usd": F2(sb)}
        if model == "boc_cash":
            sc = sp(u, BOC_CASH_BUY, BOC_CASH_SELL)
            return Q2(sc), {"spread_usd": F2(sc), "trips_no_permit": ceil_div(u, CASH_FREE), "trips_bank_permit": ceil_div(u, CASH_BANK)}
        if model == "hsbc_tt":
            fee = cap(ch, HSBC_RATE, HSBC_MIN, HSBC_MAX, HSBC_CABLE)
            return Q2(sh + fee / HSBC_SELL), {"cny_debited": F2(ch), "spread_usd": F2(sh), "sender_fee_cny": F2(fee), "sender_fee_usd": F2(fee / HSBC_SELL)}
        if model == "hsbc_pb_tt":
            return Q2(sh), {"cny_debited": F2(ch), "spread_usd": F2(sh), "sender_fee_cny": 0}
        if model == "hsbc_gt_free":
            return Q2(sh), {"cny_debited": F2(ch), "spread_usd": F2(sh), "transfer_fee_usd": 0}
        if model == "hsbc_gt_advance":
            return Q2(sh + GT_USD), {"cny_debited": F2(ch), "spread_usd": F2(sh), "transfer_fee_usd": F2(GT_USD)}
        if model == "wise":
            return None, {"cny_equivalent_at_boc_sell_reference_only": F2(cb), "transfers_bank_app": ceil_div(cb, WISE_BANK), "transfers_alipay": ceil_div(cb, WISE_ALIPAY)}
        if model == "emigrant":
            return None, {"admin_fee_cny": int(ADMIN_FEE), "max_working_days": int(SAFE_DAYS), "approval_uses": int(F["B14"]["approval_uses"])}
        if model == "inheritance":
            return None, {}
        if model == "atm":
            return None, {"cny_equivalent_at_boc_sell_reference_only": F2(cb), "calendar_years": ceil_div(cb, ATM_YEAR), "card_days": ceil_div(cb, ATM_DAY), "published_issuer_fee_cap_cny": int(F["B04"]["hsbc_atm_max_cny"])}
        if model == "cross_rmb":
            return None, {}
        if model == "hsbc_cash":
            sc = sp(u, HSBC_CASH_BUY, HSBC_CASH_SELL)
            return Q2(sc), {"spread_usd": F2(sc), "trips_no_permit": ceil_div(u, CASH_FREE), "trips_bank_permit": ceil_div(u, CASH_BANK), "notes_withdrawal_fee_cny": 0}
        if model == "unlawful":
            return None, {}
        raise AssertionError(model)

    EXPECTED_BLANKS = {
        "boc_wire": {"all_in_usd", "intermediary_fee_usd", "receiving_fee_usd", "personal_tax_usd"},
        "boc_quota": {"all_in_usd", "future_rate_usd", "future_wire_fees_usd", "intermediary_fee_usd", "receiving_fee_usd", "personal_tax_usd"},
        "boc_hold": {"all_in_usd", "future_remittance_fee_usd", "intermediary_fee_usd", "receiving_fee_usd", "personal_tax_usd"},
        "boc_cash": {"all_in_usd", "cash_handling_fee_usd", "permit_fee_usd", "security_insurance_usd", "deposit_conversion_fee_usd", "personal_tax_usd"},
        "hsbc_tt": {"all_in_usd", "pay_exact_shortfall_usd", "intermediary_fee_usd", "receiving_fee_usd", "premier_monthly_fee_usd", "personal_tax_usd"},
        "hsbc_pb_tt": {"all_in_usd", "private_banking_eligibility_fee_usd", "intermediary_fee_usd", "receiving_fee_usd", "personal_tax_usd"},
        "hsbc_gt_free": {"all_in_usd", "u_s_receiving_terms_usd", "intermediary_fee_usd", "receiving_fee_usd", "premier_monthly_fee_usd", "personal_tax_usd"},
        "hsbc_gt_advance": {"all_in_usd", "u_s_receiving_terms_usd", "intermediary_fee_usd", "receiving_fee_usd", "personal_tax_usd"},
        "wise": {"wise_fee_usd", "wise_rate_spread_usd", "overall_limit_usd", "all_in_usd", "intermediary_fee_usd", "receiving_fee_usd", "personal_tax_usd"},
        "emigrant": {"bank_fx_spread_usd", "bank_wire_fee_usd", "all_in_usd", "intermediary_fee_usd", "receiving_fee_usd", "personal_tax_usd"},
        "inheritance": {"admin_fee_cny", "bank_fx_spread_usd", "bank_wire_fee_usd", "all_in_usd", "intermediary_fee_usd", "receiving_fee_usd", "personal_tax_usd"},
        "atm": {"all_in_usd", "atm_owner_fee_usd", "network_fx_rate_spread_usd", "cash_deposit_fee_usd", "security_usd", "personal_tax_usd"},
        "cross_rmb": {"all_in_usd", "direct_rmb_fee_usd", "direct_rmb_rate_usd", "direct_rmb_limit_usd", "intermediary_fee_usd", "receiving_fee_usd", "personal_tax_usd"},
        "hsbc_cash": {"all_in_usd", "cash_handling_fee_usd", "permit_fee_usd", "security_insurance_usd", "deposit_conversion_fee_usd", "personal_tax_usd"},
        "unlawful": {"all_in_usd", "fine_usd", "criminal_exposure_usd", "personal_tax_usd"},
    }
    valid_flags = {f["id"] for f in content.FLAGS}
    rows = COSTS["rows"]
    check(len(rows) == 800, f"cost rows should be 800, found {len(rows)}")
    check(sorted({r["usd"] for r in rows}) == TIERS, "cost rows must cover exactly 40 USD 10,000 tiers")
    check(sorted({r["method_id"] for r in rows}) == sorted({m["id"] for m in content.METHODS}), "cost rows must cover every method")
    for r in rows:
        label = f"{r['method_id']}@{r['usd']}"
        exp_total, exp_known = expected(r["usd"], r["cost_model"])
        if exp_total is None:
            check(r["total_known_usd"] is None and r["total_known_pct"] is None, f"{label}: unpublished total must be null")
        else:
            check(r["total_known_usd"] is not None and close(r["total_known_usd"], F2(exp_total)), f"{label}: total known recomputation")
            exp_pct = F4(exp_total / D(r["usd"]) * 100)
            check(r["total_known_pct"] is not None and close(r["total_known_pct"], exp_pct, "0.00005"), f"{label}: pct recomputation")
        check(r["all_in_usd"] is None, f"{label}: all-in must be blank")
        check(set(r["source_ids"]) <= set(S), f"{label}: unknown source id")
        check(set(r["flag_ids"]) <= valid_flags, f"{label}: unknown flag id")
        actual_known = {k["field"]: k["value"] for k in r["known"]}
        check(set(actual_known) == set(exp_known), f"{label}: known component set")
        for field, value in exp_known.items():
            check(field in actual_known and close(actual_known[field], value, "0.005"), f"{label}: known {field}")
        for k in r["known"]:
            check(set(k["source_ids"]) <= set(S), f"{label}: known component {k['field']} source ids")
        blank_fields = {b["field"] for b in r["blanks"]}
        check(blank_fields == EXPECTED_BLANKS[r["cost_model"]], f"{label}: blank component set")
        for b in r["blanks"]:
            check(b["value"] is None, f"{label}: blank {b['field']} must be null")
            check(bool(b["reason"]), f"{label}: blank {b['field']} needs a reason")
            check(bool(b["flag_ids"]) and set(b["flag_ids"]) <= valid_flags, f"{label}: blank {b['field']} needs valid flags")

    # Penalty statutory ceilings recomputed from published percentages / amounts.
    fine = D(F["B09"]["fine_standard_pct"]) / 100
    cash_fine = D(F["B09"]["cash_violation_pct"]) / 100
    fixed = [D(F["B22"]["nonwillful_usd"]), D(F["B22"]["willful_usd"]), D(F["B23"]["form8938_max_penalty_usd"])]
    pen_rows = PEN_COSTS["rows"]
    check(len(pen_rows) == 40, f"penalty rows should be 40, found {len(pen_rows)}")
    for r in pen_rows:
        u = D(r["usd"])
        vals = [c["value_usd"] for c in r["published_ceilings"]]
        expected_vals = [F2(u * fine), F2(u), F2(u * cash_fine), F2(fixed[0]), F2(fixed[1]), F2(fixed[2])]
        for i, (actual, exp) in enumerate(zip(vals, expected_vals)):
            check(close(actual, exp), f"penalty@{r['usd']}: ceiling {i}")
        for c in r["published_ceilings"]:
            check(set(c["source_ids"]) <= set(S), f"penalty@{r['usd']}: official source id")
        check(any(b["field"] == "actual_total_penalty_usd" and b["value"] is None for b in r["blanks"]), f"penalty@{r['usd']}: actual total blank")
        for b in r["blanks"]:
            check(b["value"] is None and b["flag_ids"] and set(b["flag_ids"]) <= valid_flags, f"penalty@{r['usd']}: blank {b['field']}")

    with (DATA / "costs.csv").open(newline="", encoding="utf-8") as fh:
        crows = list(csv.DictReader(fh))
    check(len(crows) == 800, "costs.csv must contain 800 rows")
    check(all(r["all_in_usd"] == "" for r in crows), "costs.csv all-in column must be blank")
    with (DATA / "penalty_costs.csv").open(newline="", encoding="utf-8") as fh:
        prows = list(csv.DictReader(fh))
    check(len(prows) == 40, "penalty_costs.csv must contain 40 rows")
    check(all(r["actual_total_penalty_usd"] == "" for r in prows), "penalty_costs.csv actual penalty column must be blank")

# ---------------------------------------------------------------------------
# Generated HTML / links / review line checks
# ---------------------------------------------------------------------------
HTML_FILES = sorted(HERE.glob("*.html"))
check(len(HTML_FILES) == 9, f"expected 9 HTML pages, found {len(HTML_FILES)}")
OFFICIAL_HOSTS = {urlparse(s["url"]).hostname for s in LEDGER["sources"] if urlparse(s["url"]).hostname}

def official(url):
    if not url.startswith("https://"):
        return False
    host = urlparse(url).hostname or ""
    return any(host == h or host.endswith("." + h) for h in OFFICIAL_HOSTS)

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.links = []
        self.row_links = []
        self.in_tr = False
        self.has_td = False
        self.current_row = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag in ("a", "link", "script", "img"):
            href = a.get("href") or a.get("src")
            if href:
                self.links.append(href)
            if self.in_tr and tag == "a" and href:
                self.current_row.append(href)
        if tag == "tr":
            self.in_tr = True
            self.has_td = False
            self.current_row = []
        elif tag == "td" and self.in_tr:
            self.has_td = True
    def handle_endtag(self, tag):
        if tag == "tr" and self.in_tr:
            if self.has_td:
                self.row_links.append(self.current_row)
            self.in_tr = False
            self.has_td = False
            self.current_row = []

def ids_for(path):
    parser = PageParser()
    parser.feed(Path(path).read_text(encoding="utf-8"))
    return parser.ids

ID_CACHE = {}
def cached_ids(path):
    rp = str(Path(path).resolve())
    if rp not in ID_CACHE:
        ID_CACHE[rp] = ids_for(rp)
    return ID_CACHE[rp]

def resolve_link(base, href):
    path_part, sep, frag = href.partition("#")
    if not path_part:
        target = base
    else:
        target = (base.parent / path_part).resolve()
    return target, (frag if sep else None)

for page in HTML_FILES:
    text = page.read_text(encoding="utf-8")
    check(text.count("<main") == 1, f"{page.name}: exactly one main")
    check(text.count("</html>") == 1, f"{page.name}: balanced html")
    check('name="viewport"' in text, f"{page.name}: viewport meta")
    check("{{" not in text, f"{page.name}: unresolved template token")
    check("http://" not in text, f"{page.name}: insecure external URL")
    check("localhost" not in text.lower() and "127.0.0.1" not in text, f"{page.name}: no localhost references")
    parser = PageParser()
    parser.feed(text)
    ID_CACHE[str(page.resolve())] = parser.ids
    for hrefs in parser.row_links:
        check(any(official(h) for h in hrefs), f"{page.name}: substantive table row lacks an official source link")
    for href in parser.links:
        if href.startswith(("https://", "mailto:", "data:", "javascript:")):
            continue
        if href.startswith("http://"):
            check(False, f"{page.name}: insecure link {href}")
            continue
        target, frag = resolve_link(page, href)
        check(target.exists(), f"{page.name}: broken local link {href}")
        if frag and target.exists():
            if target.suffix.lower() in (".html", ".htm"):
                check(frag in cached_ids(target), f"{page.name}: missing fragment #{frag} in {href}")
            else:
                check(False, f"{page.name}: fragment on non-HTML target {href}")

# Markdown executive summary links.
md_path = HERE / "EXECUTIVE_SUMMARY.md"
md = md_path.read_text(encoding="utf-8")
check("{{" not in md, "EXECUTIVE_SUMMARY.md: unresolved template token")
check("http://" not in md, "EXECUTIVE_SUMMARY.md: insecure URL")
for target in re.findall(r"\]\(([^)]+)\)", md):
    if target.startswith(("https://", "mailto:")):
        continue
    path, _, frag = target.partition("#")
    check((HERE / path).exists(), f"EXECUTIVE_SUMMARY.md: broken local link {target}")

# CSS and browser script checks.
css = (ASSETS / "style.css").read_text(encoding="utf-8")
js = (ASSETS / "app.js").read_text(encoding="utf-8")
check(css.count("{") == css.count("}"), "style.css: balanced braces")
check("http://" not in css and "localhost" not in css.lower(), "style.css: no insecure or localhost URL")
check("http://" not in js and "localhost" not in js.lower() and "127.0.0.1" not in js, "app.js: no insecure or localhost URL")
check('"use strict"' in js, "app.js: strict mode")
check((ASSETS / "style.css").exists() and (ASSETS / "app.js").exists(), "assets present")

# Every review finding must point at a real line and an official source.
check(REVIEW["scan"]["lines_read"] > 200000, "repo audit must read the repository line by line")
check(len(REVIEW["findings"]) >= 20, "repo audit should contain at least 20 findings")
for f in REVIEW["findings"]:
    p = ROOT / f["file"]
    check(p.exists(), f"{f['id']}: file exists")
    if not p.exists():
        continue
    lines = p.read_text(encoding="utf-8").splitlines()
    check(1 <= f["line"] <= len(lines), f"{f['id']}: line number in range")
    if 1 <= f["line"] <= len(lines):
        actual = " ".join(lines[f["line"] - 1].split())
        excerpt = " ".join(f["excerpt"].split())
        check(excerpt[:100] in actual or actual[:100] in excerpt, f"{f['id']}: excerpt matches file:line")
    check(bool(f["status"] and f["finding"] and f["reviewer_note"]), f"{f['id']}: status/finding/note present")
    check(set(f["source_ids"]) <= set(S), f"{f['id']}: official source ids")
    check(all(official(u["url"]) for u in f["official_urls"]), f"{f['id']}: official URLs")

# Model params / headline values are consistent with the recomputed rows.
P = COSTS["params"]
check(P["tiers"] == 40 and P["methods"] == 20 and P["cost_rows"] == 800, "model params counts")
check(P["source_count"] == len(S) and P["flags"] == len(content.FLAGS), "model params source/flag counts")
check(P["boc_board_timestamp"] == F["B01"]["published_time"], "BOC timestamp from source ledger")
check(P["hsbc_board_date"] == F["B02"]["board_date"], "HSBC board date from source ledger")

if FAIL:
    print(f"FAILED {len(FAIL)} of {COUNT} assertions:")
    for msg in FAIL[:60]:
        print(" -", msg)
    if len(FAIL) > 60:
        print(f" ... and {len(FAIL) - 60} more")
    sys.exit(1)
print(f"PASS: {COUNT} assertions, 0 failures" + (" (structure only)" if STRUCTURE_ONLY else ""))
