#!/usr/bin/env python3
"""Line-level figure audit of the whole repository against official text read on 2026-11-11.

Scans every tracked text file outside this section, finds each place a load-bearing figure or
claim appears, and classifies it against the official source recorded in data/sources.json.
Writes data/review.json. It is a point-in-time snapshot: CI reads the stored snapshot and does
not rescan, because other sessions keep adding files (the same convention as playbook-c1d73006).

Run:  python3 guide-fb2f2562/audit.py
"""
import json
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SELF = os.path.basename(HERE) + "/"
EXT = re.compile(r"\.(html|md|json|py|js|mjs|csv|txt|yml)$")
W = 170  # characters of context either side of a match

# Each rule: id, title, official source ids, what the official text says, the trigger regex,
# and a classifier returning (verdict, why) for the context window around a match.
#   verdict ∈ {"conflict", "check", "consistent", "corrected"}
CORRECTION = re.compile(r"abolish|no longer|removed|supersed|取消|废止|repeal|2014\]\s*2|2014〕2|2014\)\s*No\.?\s*2|"
                        r"\[2014\] ?No\. ?2|outdated|old rule|earlier rule|was dropped|scrapped|no staging|not staged|cancel|lump[- ]sum|"
                        r"one or (several|more)|[一1]次或分次", re.I)
# Text that reports someone else's claim (audit logs, review snapshots) rather than asserting it.
META_FILE = re.compile(r"(^COORDINATION\.md$|review\.(json|html)$|repo-review|findings\.json$|/AUDIT\.md$|irregularities|claims?\.json$)")
META_WIN = re.compile(r"existing (summary|claim)|\"claim\"|claim=|older (summaries|pages|sets)|earlier (pages|sets|editions)|"
                      r"files (say|call|describe)|\"text\": |\"path\": ", re.I)


def has(pattern, text):
    return re.search(pattern, text, re.I) is not None


def r_staging(win, m):
    if not has(r"emigra|移民|财产转移|property transfer|emigrant", win):
        return None
    if CORRECTION.search(win):
        return ("corrected", "Mentions staging together with its removal.")
    return ("conflict", "Describes emigrant transfers as staged; 汇发[2014]2号 §VI abolished staged remittance.")


def r_ftc(win, m):
    if not has(r"credit|1116|FTC", win[W - 70: W + 90]):
        return None
    if has(r"\bnot\b|n't|overstat|\bmay\b|limit|\bno\b|flag|RV-06|C05|exaggerat|misleading|incorrect|wrong", win):
        return ("corrected", "The phrase appears with a limiting or correcting word.")
    return ("conflict", "Calls the credit dollar-for-dollar; the IRS page limits it (no credit on FEIE-excluded income; only tax actually owed after treaty).")


def r_feie27(win, m):
    hit = m.group(0)
    if "137,300" in hit or "137300" in hit:
        near = win[W - 80: W + len(hit) + 80]
        if has(r"unverified|not verified|secondary|not yet (read|seen|confirmed)|unconfirmed|press only|not seen", near):
            return ("check", "Gives USD 137,300 but marks it unverified; Rev. Proc. 2026-35 §3.41 now confirms it.")
        return ("consistent", "USD 137,300 matches Rev. Proc. 2026-35 §3.41.")
    return ("check", "Says the 2027 exclusion is not published/seen; Rev. Proc. 2026-35 §3.41 publishes USD 137,300.")


def r_feie26(win, m):
    hit = m.group(0)
    if "132,900" in hit:
        return ("consistent", "USD 132,900 matches the Form 2555 instructions.")
    near = win[W - 60: W + len(hit) + 15]
    if not has(r"exclusion|FEIE|2555|911", win[W - 90: W + 90]):
        return None
    if "2026" in near and not has(r"2025|2024|2023", near):
        return ("conflict", "A different amount is given as the 2026 exclusion; the official 2026 amount is USD 132,900.")
    return None


def r_hsbc(win, m):
    hit = m.group(0)
    if not has(r"620|HSBC|汇丰|cap|max", win):
        return None
    if hit.startswith("86.97"):
        return ("check", "CNY 620 converted at the IRS 2025 average (7.129), not at HSBC's dealing rate; HSBC's 2026-11-10 sell rate 6.7053746 gives USD 92.46.")
    return ("consistent", "CNY 620 converted at an HSBC/BOC board rate (≈ USD 92.4–92.7 depending on the day).")


def r_crypto(win, m):
    if has(r"illegal|unlawful|prohibit|\bban|非法|禁止|reject|not lawful|do not|don't|avoid|42号|No\. ?42|"
           r"not a lawful|excluded|not allowed|forbid|\brisk|violat|outlaw|penalt|crime|criminal|❌|✗|unsafe", win):
        return ("consistent", "Crypto is mentioned with its prohibited / unlawful status.")
    return ("check", "Crypto is mentioned without saying it is illegal in China; 银发〔2026〕42号 bans all virtual-currency business, stablecoins included.")


def r_fbar(win, m):
    hit = m.group(0)
    if "16,536" in hit:
        return ("consistent", "USD 16,536 matches 31 CFR 1010.821 (non-wilful maximum).")
    before = win[W - 45: W]
    if not has(r"non-?\s?wil+ful", before) or has(r"aggregate|exceed|threshold|accounts? (over|above|>)", win[W - 45: W + 40]):
        return None
    if has(r"adjusted for inflation|inflation[- ]adjusted|16,536", win):
        return ("corrected", "Gives the USD 10,000 statutory base together with its inflation adjustment.")
    return ("conflict", "Uses USD 10,000 as the non-wilful FBAR maximum; the inflation-adjusted figure in 31 CFR 1010.821 is USD 16,536.")


def r_3520(win, m):
    hit = m.group(0)
    if not has(r"corporat|partnership|3520|6039F|foreign person", win):
        return None
    if re.match(r"\s*\(?(2025|2024|2023)", win[W + len(hit): W + len(hit) + 8]):
        return ("consistent", "An earlier year's threshold, labelled with its year.")
    if hit.startswith("20,573") or hit.startswith("21,240"):
        return ("consistent", "Matches the IRS 2026 (USD 20,573) or Rev. Proc. 2026-35 2027 (USD 21,240.31) threshold.")
    return ("check", "An older foreign-corporation gift threshold; 2026 is USD 20,573 and 2027 is USD 21,240.31.")


def r_quota(win, m):
    if not has(r"quota|额度|annual ?limit|yearly|per (person|individual)( per)?( calendar)? year", win[W - 40: W + len(m.group(0)) + 40]):
        return None
    if not has(r"foreign(er)?s?\b|U\.?S\.? citizen|American|境外|non-?resident|overseas individual", win):
        return None
    if has(r"domestic|境内|not apply|doesn.t apply|does not|not a (universal|blanket)|facilitation|便利|unresolved|flag|Art\. ?13|第十三条|universal|misconception|do not|go beyond|residence|"
           r"permanent|PR card|resident", win):
        return ("consistent", "Ties the USD 50,000 figure to domestic individuals or flags its scope.")
    return ("check", "Applies the USD 50,000 annual figure to a foreign individual without qualification; Art. 2 of 汇发[2007]1号 frames it for domestic individuals and Art. 13 governs foreigners.")


VERDICTS = ("conflict", "check", "consistent", "corrected", "quoted")

RULES = [
    dict(id="RA-01", title="Emigrant transfers described as staged", sources=["S12", "S13"],
         official="汇发[2014]2号 §VI abolished staged remittance; one or several remittances are allowed.",
         pattern=r"\bstaged\b|in stages|instal+ments?|分次|分期|50% ?/ ?25% ?/ ?25%", fn=r_staging),
    dict(id="RA-02", title="Foreign tax credit called “dollar-for-dollar”", sources=["S29"],
         official="Credit only for foreign income tax actually owed (after treaty); none on FEIE-excluded income.",
         pattern=r"dollar[- ]for[- ]dollar", fn=r_ftc),
    dict(id="RA-03", title="2027 foreign earned income exclusion", sources=["S26"],
         official="USD 137,300 for tax years beginning in 2027 (Rev. Proc. 2026-35 §3.41).",
         pattern=r"137,300|2027 (amount |figure |exclusion )?(is )?not (yet )?(published|announced|seen|available)|2027 not seen", fn=r_feie27),
    dict(id="RA-04", title="2026 foreign earned income exclusion", sources=["S25"],
         official="USD 132,900 for 2026 (Form 2555 instructions).",
         pattern=r"132,900|126,500|130,000", fn=r_feie26),
    dict(id="RA-05", title="HSBC CNY 620 wire-fee cap in USD", sources=["S04", "S02", "S07"],
         official="Cap CNY 500 + cable CNY 120 = CNY 620; at HSBC's 2026-11-10 sell rate 6.7053746 that is USD 92.46.",
         pattern=r"86\.97|92\.4\d|92\.70", fn=r_hsbc),
    dict(id="RA-06", title="Crypto / stablecoin routes", sources=["S18"],
         official="银发〔2026〕42号: all virtual-currency business, stablecoins included, is illegal financial activity.",
         pattern=r"USDT|stablecoin|crypto(currency)?\b|bitcoin|虚拟货币|稳定币", fn=r_crypto),
    dict(id="RA-07", title="FBAR non-wilful penalty amount", sources=["S22"],
         official="31 CFR 1010.821: non-wilful maximum USD 16,536; wilful USD 165,353.",
         pattern=r"16,536|\$ ?10,000", fn=r_fbar),
    dict(id="RA-08", title="Form 3520 foreign-corporation gift threshold", sources=["S24", "S26"],
         official="USD 20,573 for 2026 (IRS); USD 21,240.31 for 2027 (Rev. Proc. 2026-35 §3.51).",
         pattern=r"20,573|21,240(\.31)?|20,116|19,570|18,567", fn=r_3520),
    dict(id="RA-09", title="USD 50,000 annual figure applied to a foreigner", sources=["S08", "S09", "S10"],
         official="Art. 2 sets USD 50,000 each for domestic individuals' settlement and purchase; Art. 13 lets foreigners buy FX for lawful income with ID and income/tax proof.",
         pattern=r"(USD|US\$|\$) ?50,000|50,000 (USD|dollars)|5万美元", fn=r_quota),
]


def tracked_files():
    out = subprocess.check_output(["git", "ls-files"], cwd=ROOT).decode("utf-8").splitlines()
    return sorted(f for f in out if f and not f.startswith(SELF) and EXT.search(f)
                  and os.path.isfile(os.path.join(ROOT, f)))


def section_of(path):
    return path.split("/", 1)[0] if "/" in path else "(root files)"


def clean(s):
    s = re.sub(r"<[^>]{0,400}>", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def main():
    files = tracked_files()
    findings = []
    for f in files:
        with open(os.path.join(ROOT, f), encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        line_starts = [0] + [i + 1 for i, c in enumerate(text) if c == "\n"]
        for rule in RULES:
            for m in re.finditer(rule["pattern"], text, re.I):
                a = max(0, m.start() - W)
                win = text[a: m.end() + W]
                pad = W - (m.start() - a)
                win = " " * pad + win  # keep the match at index W
                res = rule["fn"](win, m)
                if res is None:
                    continue
                verdict, why = res
                if verdict in ("conflict", "check") and (META_FILE.search(f) or META_WIN.search(win)):
                    verdict, why = "quoted", "Reports another file's wording (audit or review text); not itself an assertion."
                # line number via binary search
                lo, hi = 0, len(line_starts) - 1
                while lo < hi:
                    mid = (lo + hi + 1) // 2
                    if line_starts[mid] <= m.start():
                        lo = mid
                    else:
                        hi = mid - 1
                ex = clean(text[max(0, m.start() - 90): m.end() + 90])
                findings.append(dict(rule=rule["id"], file=f, section=section_of(f), line=lo + 1,
                                     col=m.start() - line_starts[lo] + 1, match=m.group(0),
                                     excerpt=ex[:260], verdict=verdict, why=why))
    # collapse repeated hits of the same rule on the same line (e.g. minified HTML)
    seen, uniq = set(), []
    for x in findings:
        k = (x["rule"], x["file"], x["line"], x["verdict"])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(x)
    findings = uniq
    for x in findings:  # keep the snapshot small: excerpts only where a reader must act
        if x["verdict"] not in ("conflict", "check"):
            x["excerpt"] = ""
    sections = sorted({section_of(f) for f in files})
    grid = {}
    for s in sections:
        grid[s] = {}
        for r in RULES:
            hits = [x for x in findings if x["section"] == s and x["rule"] == r["id"]]
            grid[s][r["id"]] = {v: sum(1 for x in hits if x["verdict"] == v)
                                for v in VERDICTS}
    head = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT).decode().strip()
    out = dict(
        generated="2026-11-11", scanned_at_commit=head, scanned_files=len(files),
        excluded=SELF + "** (this section)",
        rules=[{k: v for k, v in r.items() if k not in ("fn",)} for r in RULES],
        totals={v: sum(1 for x in findings if x["verdict"] == v) for v in VERDICTS},
        sections=grid, findings=findings,
    )
    with open(os.path.join(HERE, "data", "review.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print(f"scanned {len(files)} files · {len(findings)} findings · {out['totals']}")
    for r in RULES:
        c = [x for x in findings if x["rule"] == r["id"]]
        print(r["id"], {v: sum(1 for x in c if x["verdict"] == v) for v in VERDICTS})


if __name__ == "__main__":
    main()
