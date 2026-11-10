# 6. Breakdown of the Conversion Penalty

**Research date:** 2026-11-07

The user's premise is "no way to convert it into USD without paying a considerable amount of taxes." That premise is true for some kinds of money and false for others. This file decomposes the penalty into its five separable layers, because **the cheapest solution depends on which layer you are actually paying.**

---

## Layer 1 — Was the money already taxed in China?

This is the single most important question, and it determines almost everything else.

| Origin of the CNY | Already taxed in China? | Additional China tax to convert | Source |
|---|---|---|---|
| Salary / wages | Yes — IIT withheld at source by the employer | **None** | [STA IIT Law](https://guangdong.chinatax.gov.cn/gdsw/yhyshjzt2024_zcwj_tgfgzlE/2024-07/19/content_01346c4ecaee40b2af8aa3f94a4ee107.shtml) |
| Bank interest | Yes — 20% withheld | **None** on the principal; the interest itself is US-taxable too | [Ann. 61/2018](https://fgk.chinatax.gov.cn/eng/c102962/c102967/c102997/c103004/c5245843/content.html) |
| Sale of personal assets | Partially — depends on the asset | Depends | — |
| **WFOE / company profit** | **No — not yet at the shareholder level** | **25% EIT + 10% WHT = 32.5%** | [EIT Law Art. 4](https://zhejiang.chinatax.gov.cn/art/2024-10-30/art_26318_626886.html) · [treaty Art. 9(2)](https://www.irs.gov/pub/irs-trty/china.pdf) |
| Dividend from a Chinese company | Yes at the company level | 10% WHT at your level | [treaty Art. 9(2)](https://www.irs.gov/pub/irs-trty/china.pdf) |
| Unproven / undocumented origin | Unknown | Bank will refuse | [SAFE](https://www.safe.gov.cn/en/2015/1111/1175.html) |

**Key finding.** If the balance is personal, lawfully-earned, already-taxed money in a personal account, **there is no Chinese tax on converting it at all.** The only Chinese-side cost is the bank's FX spread. The "considerable amount of taxes" the question describes is almost certainly either (a) company-level EIT and WHT that have not yet been paid, or (b) the US-side currency gain under § 988(e), or (c) a professional's estimate based on assuming the money is untaxed corporate profit.

## Layer 2 — Chinese withholding on the payment itself

| Channel | Domestic statutory rate | Treaty-capped rate | Effective | Source |
|---|---|---|---|---|
| Dividend | 20% | **10%** | 10% | [treaty Art. 9(2)](https://www.irs.gov/pub/irs-trty/china.pdf) |
| Interest | 20% | **10%** | 10% | [treaty Art. 10(2)](https://www.irs.gov/pub/irs-trty/china.pdf) |
| Royalties | 20% | **10%** | 10% | [treaty Art. 11(2)](https://www.irs.gov/pub/irs-trty/china.pdf) |
| Equipment rental royalties | 20% | **10% on 70% of gross** | **7%** | [Protocol 1 para. 6](https://www.irs.gov/pub/irs-trty/china.pdf) |
| Services | VAT + surcharges | — | *VAT not verified* | [treaty Art. 7](https://www.irs.gov/pub/irs-trty/china.pdf) |

**Key finding.** The US–China treaty halves the withholding rate on every passive income stream and cuts equipment rental to an effective 7%. Not claiming treaty benefits — which many banks will not do for you automatically — costs 10 percentage points. This is the single largest easily-avoidable leakage in the whole exercise.

## Layer 3 — Chinese corporate income tax on the profit before distribution

| Item | Rate | Source |
|---|---|---|
| EIT on China-source profit | 25% | [EIT Law Art. 4](https://zhejiang.chinatax.gov.cn/art/2024-10-30/art_26318_626886.html) |
| Statutory surplus reserve that must be appropriated from after-tax profit before distribution | 10% of the profit, until the reserve reaches 50% of registered capital | *Secondary translation of Company Law Art. 210 — flagged* |

## Layer 4 — The US currency gain, § 988(e)

| Rule | Effect | Source |
|---|---|---|
| § 988(e)(1) — the section does not apply to an individual's personal transactions | FX gains are not automatically ordinary income | [§ 988](https://www.law.cornell.edu/uscode/text/26/988) |
| § 988(e)(2) — no gain recognised on exchange-rate movement in a personal transaction **unless the gain exceeds USD 200** | Below USD 200: free. Above USD 200: **the entire gain is taxable ordinary income** | [§ 988](https://www.law.cornell.edu/uscode/text/26/988) |

**Key finding — this is the hidden penalty.** Two points matter:

1. The USD 200 threshold is a *cliff*, not a de minimis allowance. Cross it by one dollar and the whole gain is in income, not just the excess.
2. **There is no Chinese tax credit available against it.** China does not tax a currency gain, so the US tax on it is pure incremental cost. For someone who acquired CNY years ago at a strong rate and converts today, this can be a double-digit percentage of the balance — with no offsetting credit.

This is often the real reason a large conversion "costs a lot", and it is invisible unless you specifically check § 988(e).

## Layer 5 — Compliance and penalty exposure if things go wrong

| Exposure | Amount | Source |
|---|---|---|
| FBAR, non-willful, per report (effective 17 Jan 2025) | USD 16,536 | [eCFR 31 CFR 1010.821](https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821) |
| FBAR, willful, per account per year | greater of USD 165,353 or 50% of the balance | [eCFR 31 CFR 1010.821](https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821) |
| Form 8938 failure to disclose | USD 10,000 + USD 10,000 per 30 days after notice, max USD 60,000 | [IRS comparison page](https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements) |
| China: illegal carrying of FX | warning + fine up to 20% | [PBOC FX Regs art. 42](https://www.pbc.gov.cn/english/130721/2025080815063231112/index.html) |
| China: FX evasion | repatriation + fine up to 30% (30–100% if serious) | [PBOC FX Regs art. 39](https://www.pbc.gov.cn/english/130721/2025080815063231112/index.html) |
| China: disguised FX trading | repatriation + fine up to 30% (30–100% if serious) | [PBOC FX Regs art. 45](https://www.pbc.gov.cn/english/130721/2025080815063231112/index.html) |
| China: underground banking | RMB 5m threshold; fine 1–5× illegal gains; up to 5 years' imprisonment | [SPC Fa Shi [2019] No. 1](https://www.court.gov.cn/zixun/xiangqing/141562.html) |

**Key finding.** The downside of doing this wrong is an order of magnitude larger than the upside of doing it cheaply. A willful FBAR penalty alone (greater of USD 165,353 or 50% of the balance) exceeds any tax saving available from any method in this catalogue.

---

## Cost comparison — one worked scenario

Assumption: USD 500,000 of CNY, and the money is **already-taxed personal salary** in a personal mainland account.

| Route | China tax | US tax | Total leakage | Verdict |
|---|---|---|---|---|
| A1 — bank remittance with documents | 0% | § 988(e) gain only, if CNY appreciated | Bank spread only | **Cheapest lawful route** |
| A3 — restructure as WFOE dividend | 32.5% | offset by FTC | 32.5% + spread | Only if the money really is company profit |
| A8 — pay overseas expenses directly | 0% | 0% | 0% | Best of all, but limited to genuine obligations |
| B — underground banking | n/a | n/a | Criminal exposure | Never |

**Assumption: USD 500,000 of CNY that is untaxed WFOE profit.**

| Route | China tax | US tax | Total leakage | Verdict |
|---|---|---|---|---|
| A3 — dividend with treaty benefit | 32.5% | offset by FTC (Form 1116) | 32.5% | Standard, lawful |
| A3 — dividend **without** treaty benefit | 40.0% | offset by FTC | 40.0% | 7.5 points worse — always claim the treaty |
| A7 — capital reduction / liquidation | EIT on gain only | FTC on the EIT | Lower than 32.5% on the capital element | Worth considering if closing the entity |
| A6 — equipment rental | 7% effective | offset by FTC | 7% + VAT | Lowest rate available, but needs a genuine lease |

---

## What actually drives the answer

1. **Is the money already taxed in China?** If yes, the conversion itself is essentially tax-free in China and the only leakage is the US § 988(e) gain and the bank spread.
2. **Is the money company profit?** If yes, the leakage is 32.5% — but claim the treaty (10% not 20%) and the FTC, and the net US cost is usually zero.
3. **Do you have genuine overseas obligations?** Paying them directly from the CNY account is the only route that is tax-free on *both* sides.
4. **Are you still employed in China and qualifying for the FEIE?** If yes, salary remittance is tax-free on both sides up to USD 130,000 (2025).
5. **Are you emigrating or leaving China?** The personal-property-transfer channel exists for exactly this — get it verified before using it.
6. **Never** use underground banking, crypto, splitting, or borrowed quotas. The criminal and penalty exposure dwarfs any tax saving.
