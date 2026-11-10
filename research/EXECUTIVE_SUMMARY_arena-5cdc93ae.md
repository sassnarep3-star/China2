# Executive Summary — Getting CNY Out of China as a US Citizen

**Prepared:** 2026-11-07 · **Repository:** `sassnarep3-star/China2` · **Branch:** `arena/5cdc93ae-china2`

Every figure below is sourced to an official government page. The full source registry is in [`research/00-source-registry.md`](research/00-source-registry.md). Values that could not be confirmed from an official source are left blank and listed on the site's [Flagged for Review](docs/flagged.html) page.

---

## 1. The headline answer

**If the CNY sitting in the mainland bank account is personal, lawfully-earned money that has already been taxed in China, converting it to USD carries no Chinese income tax at all.** The only costs are the bank's FX spread and, on the US side, any currency gain above USD 200 under 26 U.S.C. § 988(e).

China's individual FX rules set a **USD 50,000 per person per year** documentation threshold, not a legal ceiling. SAFE states explicitly that conversion beyond the quota is permitted with valid ID plus documents proving the transaction is genuine. Outward remittance of company profits is a **current-account** item handled directly at the bank with evidencing documents and **no quota**.

The "considerable amount of taxes" comes from one of three specific places, and each has a different fix:

| Source of the tax | Size | Fix |
|---|---|---|
| Company-level EIT + dividend withholding on untaxed WFOE profit | **32.5%** | Claim the treaty rate (10%, not the 20% statutory rate) and the US foreign tax credit |
| US currency gain under § 988(e) on converting CNY that has appreciated | **Up to 100% of the gain** | Model it before converting; consider converting in tranches across tax years |
| Chinese VAT on service fees / royalties | *Not verified* | Prefer routes with no VAT |

---

## 2. The five layers of the "conversion penalty"

| Layer | What it is | Can it be avoided? |
|---|---|---|
| **1. Chinese tax already paid** | Salary and interest are already taxed at source. | Nothing further to pay — this layer is zero for personal money. |
| **2. Chinese withholding on the payment** | Dividends, interest, royalties. | **Yes** — the treaty halves it. Dividends 20% → **10%**; interest 20% → **10%**; royalties 20% → **10%**; equipment rental 20% → **7%** effective. |
| **3. Chinese corporate income tax** | 25% EIT on company profit before distribution. | No, if the money is company profit. Avoidable by keeping the money personal in the first place. |
| **4. US currency gain (§ 988(e))** | FX gain on disposing of nonfunctional currency in a personal transaction. | **Partly.** Gains up to USD 200 are free; above USD 200 the *entire* gain is ordinary income. There is **no Chinese tax credit** for it, because China does not tax the gain. |
| **5. Penalty exposure** | FBAR up to **USD 16,536** non-willful per report; willful **the greater of USD 165,353 or 50% of the balance**; Form 8938 up to **USD 60,000**; China fines up to 30–100% of the amount plus criminal liability. | **Yes — fully.** File correctly and stay inside the rules. |

**The most important structural insight:** layer 5 dwarfs layers 1–4. A willful FBAR penalty can exceed the entire balance being repatriated. Optimising tax while risking a penalty is the wrong trade.

---

## 3. Recommended route, ranked by total leakage

| Rank | Method | China tax | US tax | Conditions |
|---|---|---|---|---|
| **1** | **Pay genuine overseas expenses directly from the CNY account** | **0%** | **0%** | You must have real overseas obligations. Tax-free on both sides. |
| **2** | **Direct bank remittance of already-taxed personal CNY, with documentation** | **0%** | § 988(e) gain only | The money must be provably lawful and already taxed. SAFE permits beyond-quota conversion with documents. |
| **3** | **After-tax salary remittance while employed in China** | **0%** | FEIE may zero it (up to **USD 130,000** in 2025) | You must still qualify under the bona fide residence or 330-day physical presence test. |
| **4** | **Equipment rental royalties** | **7% effective** | Largely offset by FTC | Requires a genuine equipment lease. |
| **5** | **Royalties / interest** | **10% WHT** + VAT | Largely offset by FTC | Requires genuine IP or a genuine loan. |
| **6** | **WFOE dividend** | **32.5%** | Largely offset by FTC (Form 1116) | The standard route for company profit. |
| **7** | Personal property transfer abroad | *unverified* | § 988(e) | The designed channel for emigrating; **get the conditions verified before relying on it.** |
| **✗** | Underground banking, crypto, splitting, borrowed quotas | — | — | **Criminal. Never.** |

### Why the treaty matters so much
The US–China treaty caps dividend withholding at **10%** versus the 20% statutory domestic rate. On a USD 500,000 dividend that is USD 50,000 saved. Combined with the 25% EIT, the effective total leakage is **32.5%** with the treaty versus **40.0%** without it. Banks will not always apply the treaty rate automatically — you must claim it.

### Why the foreign tax credit matters
The treaty's saving clause states plainly: *"Notwithstanding any provision of the Agreement, the United States may tax its citizens."* The treaty does **not** switch off US tax, and it contains **no tax-sparing credit**. Relief comes only from the foreign tax credit on Form 1116, which credits the Chinese income tax dollar-for-dollar against US tax on the same income.

---

## 4. What you must do regardless of which route you pick

| Obligation | Requirement | Source |
|---|---|---|
| **FBAR (FinCEN Form 114)** | Required if the aggregate value of foreign accounts exceeded **USD 10,000 at any time** in the calendar year. Due 15 April, automatic extension to 15 October. Filed with FinCEN, not with the return. Taxability is irrelevant. | [IRS](https://www.irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar) |
| **Form 8938** | Required if specified foreign financial assets exceed **USD 200,000** (unmarried, living abroad) or **USD 400,000** (married filing jointly, living abroad) on the last day of the year. Independent of, and in addition to, the FBAR. | [IRS](https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements) |
| **Worldwide income reporting** | Interest on the Chinese account is taxable in the US even if already taxed in China at 20%. | [IRS](https://www.irs.gov/individuals/international-taxpayers/foreign-tax-credit) |
| **Past non-compliance** | Streamlined Foreign Offshore Procedures are available for non-willful failures, but not once the IRS has opened a civil exam or criminal investigation. | [IRS](https://www.irs.gov/individuals/international-taxpayers/streamlined-filing-compliance-procedures) |

---

## 5. Channels that must not be used

| Channel | Status | Exposure |
|---|---|---|
| Underground banking / 对敲 | **Criminal** — illegal business operation | Criminal from **RMB 5,000,000** of transactions or **RMB 100,000** of gains; fine 1–5× gains; up to 5 years' imprisonment ([SPC](https://www.court.gov.cn/zixun/xiangqing/141562.html)) |
| Cryptocurrency | **Prohibited** — all virtual-currency business is illegal financial activity | Criminal liability pursued ([PBOC](http://www.pbc.gov.cn/goutongjiaoliu/113456/113469/4348521/index.html)) |
| Splitting / borrowed quotas | Prohibited | Watchlist, quota restriction, credit-record entry, AML/criminal referral ([SAFE](https://www.safe.gov.cn/en/2017/0119/1244.html)) |
| Card lending to lift the ATM cap | Prohibited | Card barred for the current and following year ([SAFE](https://www.safe.gov.cn/en/2017/1230/1397.html)) |
| Carrying cash | Restricted | Warning + fine up to **20%** of the amount ([PBOC](https://www.pbc.gov.cn/english/130721/2025080815063231112/index.html)) |

---

## 6. Practical sequence

1. **Establish what the money is.** Personal taxed salary, or company profit? This single fact decides everything.
2. **Get the documentation in order before approaching the bank.** Employment contract, IIT payment records, tax recordal form, source-of-funds evidence covering the whole period the money has been in the account.
3. **Clear the US compliance position first.** File outstanding FBARs and Forms 8938, or use the Streamlined procedures if there is non-willful past non-compliance. **Do this before moving large sums** — the penalty for a willful FBAR failure can exceed the entire balance.
4. **Model the § 988(e) gain.** Compare the CNY acquisition cost against the conversion rate. If the gain exceeds USD 200, the whole gain is ordinary income with no foreign tax credit.
5. **If it is company profit, claim the treaty** — 10%, not 20% — and file Form 1116 for the credit.
6. **Prefer paying overseas obligations directly** where you have genuine ones. It is the only route that is tax-free on both sides.
7. **Get the personal-property-transfer channel verified** if you are emigrating. Its existence is confirmed on the official SAFE catalogue; its substantive conditions are not verified here.

---

## 7. Open items — flagged, not blocking

These are published on the [Flagged for Review](docs/flagged.html) page and are **not** verified from an official source:

| Item | Why it is open |
|---|---|
| Cash-export limits (RMB 20,000 / USD 5,000 / USD 10,000 tiers) | Only secondary sources retrieved |
| Huifa [2020] No. 14 art. 49 — USD 50,000 bank document-review threshold for service-trade payments | Only secondary sources retrieved |
| Substantive conditions of the personal property transfer channel (Announcement [2004] No. 16, Huifa [2004] No. 118, Huifa [2005] No. 9) | Existence confirmed on the official SAFE catalogue; text not read |
| Chinese VAT rate on services and the surcharge rate | Not verified |
| Chinese IIT brackets and the RMB 60,000 basic deduction | Not verified against an official English text |
| No annual quota on after-tax salary remittance for foreign individuals | Professional commentary (DLA Piper via Ecovis), not an official source |
| Announcement [2013] No. 40 substance | Existence confirmed on the official SAFE catalogue; content from a professional-firm summary |
| Company Law art. 210 (10% statutory surplus reserve) | Two independent English translations; official NPC text not read |
| 26 U.S.C. § 988 text | Read at Cornell LII, which is not a government site; the official uscode.house.gov page could not be loaded from this environment |
