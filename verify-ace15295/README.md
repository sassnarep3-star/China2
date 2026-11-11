# verify-ace15295 — CNY → USD: verified cost engine, questions register, line-by-line audit

Session `arena/ace15295-china2`. Sources captured **11 November 2026**. Research, not tax or legal advice.

Live: <https://sassnarep3-star.github.io/China2/verify-ace15295/index.html>

## What this section adds

| Page | What it answers |
|---|---|
| [`index.html`](index.html) | The single answer, the four things "tax" is being used for, and the executive summary table |
| [`costs.html`](costs.html) | All-in cost at every USD 10,000 step from 10,000 to 400,000, per method — mobile-first |
| [`methods.html`](methods.html) | 10 route types (not 23): eligibility, pros, cons, exact steps; unlawful ones priced, not instructed |
| [`penalties.html`](penalties.html) | The "conversion penalty" split into 7 layers, with which are avoidable |
| [`taxes.html`](taxes.html) | PRC IIT · U.S. §988 · FBAR · Form 8938 · FinCEN 105, with thresholds |
| [`questions.html`](questions.html) | 14 decision gates: what is unknown, why it blocks, how to discover it |
| [`audit.html`](audit.html) | 9 findings against what earlier sessions published |
| [`flagged.html`](flagged.html) | 16 flagged gaps — every value left blank and why |
| [`sources.html`](sources.html) | 31 documents, retrieval date, and the exact words relied on |

## Method

- **Every figure is arithmetic on a published input.** The government's or the bank's own number is quoted with a link, then the arithmetic is shown. Nothing is assumed.
- **A blank stays blank.** If the publisher does not print a value (CMB's remittance tariff, ICBC's board, the receiving bank's inward fee, your dollar basis), the cell is blank and is listed on the Flagged page. No value is filled in by inference, and none is carried over from an earlier session's snapshot.
- **Rate boards are reference rates.** All three boards used carry the publisher's own disclaimer, so every total is a labelled lower bound.
- **No personal tax figure is asserted.** The PRC layer is a flat-20% illustration; the U.S. layer is a statutory-rate illustration with no other income. Basis, residency, filing status and the source of the balance are unknown.

## The headline result

| Item | Value | Source |
|---|---|---|
| Cheapest published all-in cost at USD 400,000 | **$901.20 (0.225%)** — Bank of China | [BOC board](https://www.boc.cn/sourcedb/whpj/) · [BOC tariff](https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html) |
| HSBC "free wire" at the same amount | **$2,082.26 (0.521%)** — the spread is 2.4× wider | [HSBC board](https://www.services.cn-banking.hsbc.com.cn/PublicContent/common/rate/zh/exchange-rates.html) · [HSBC tariff](https://www.hsbc.com.cn/content/dam/hsbc/cn/docs/document-download/tariff-of-Accounts-services-for-personal-customers-v2.pdf) |
| Tax imposed on the act of converting | **None found** in any of the 31 documents | see `penalties.html` |
| U.S. tax on a personal currency gain | **$0 if the gain is ≤ $200** | [26 U.S.C. §988(e)(2)](https://www.law.cornell.edu/uscode/text/26/988) |
| Largest figure in the project | **$165,353** — maximum per *willful* FBAR violation | [31 CFR 1010.821](https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821) |

## Reproduce it

```bash
python3 model.py     # recompute data/costs.json from the captured inputs
python3 build.py     # regenerate the 9 pages
python3 verify.py    # 4,156 independent checks; must print FAILURES: 0
```

CI: `.github/workflows/verify-ace15295.yml` runs all three and fails if the committed output
differs from a fresh build, or if any published row lacks a link to the publisher's own host.

## Files

```
model.py            cost engine — inputs are quoted with their source id
build.py            static page generator (no external scripts, no CDN)
verify.py           independent recomputation + link/citation/blank enforcement
data/sources.json   31 sources: publisher, URL, retrieval date, exact propositions relied on
data/findings.json  9 audit findings (AK-01 … AK-09)
data/questions.json 14 decision gates (Q01 … Q14)
data/costs.json     generated: 200 route rows, 40 penalty tiers
```
