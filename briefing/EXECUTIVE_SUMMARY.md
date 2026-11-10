# Executive Summary — China money: getting CNY out as a U.S. citizen

**Session:** arena/dc2c65bd-china2 · **Date:** 2026-11-10 · **Status:** research, not advice
**Live site:** https://sassnarep3-star.github.io/China2/briefing/ · **Ledgers:** `repatriate/data/*`, `briefing/build.py`

> Every figure below is tied to an official source retrieved by this or a prior session. Anything unverifiable is **blank and flagged** on the [Flagged page](flagged.html).

## The one-line answer

A transfer fee is not tax. No universal zero-tax conclusion can be drawn: source-income liability and taxable currency gains require separate review. Possible explanations for the quoted cost include: (1) PRC individual income tax already owed on the income that created the balance, (2) the bank's exchange-rate spread and wire fees (not tax), (3) PRC penalties for unlawful movement (up to 30% / 30–100%), or (4) U.S. reporting penalties (FBAR / Form 8938) for an undeclared account. If the relevant rules and documentation are satisfied, a bank wire may be available — the first route to evaluate is documented bank conversion; no cheapest or least-tax route can be verified without the private facts.

## What the "conversion penalty" actually is (line by line)

1. **PRC: distinguish FX rules from tax law.** SAFE's individual FX regime sets an annual facilitation quota (USD 50,000 equivalent/person/year for domestic individuals, purchases and sales) and an authenticity review; no separate conversion levy was identified in those cited FX rules (not a complete tax review). Over the quota, transactions are not forbidden — authenticity review is "strengthened". [SAFE 2007 / SAFE Tianjin rules (S01, S02)]
2. **PRC individual income tax** attaches to the *income*, when it arose — 3%–45% progressive comprehensive-income rates after the RMB 60,000 annual deduction; flat 20% on interest, dividends and property transfers. Owed regardless of remittance; the bank may require tax documentation; no personal refusal reason was verified. [PRC IIT Law, S15]
3. **The bank's spread + fees — the real, ordinary cost.** Not a tax. For HSBC China Premier/Advance (current tariff, effective 2026-10-31): outward SWIFT wire 0.1% of amount, min CNY 100 / max CNY 500, **plus** CNY 120 cable — a $400,000 wire costs CNY 620 ≈ **$86.97** in published fees. Private Banking individuals: free. Global Transfer to your own overseas HSBC account: free (PB/Premier) / USD 20 (Advance). The **spread is unverified**; amount blank (no executable quote verified). [HSBC tariff, B06]
4. **U.S. tax on the conversion itself.** Currency exchange can realize taxable gain. *Exchange-rate gain on the currency position* can be taxed; IRS Pub. 525: a gain on a **personal** foreign currency transaction is not included in income unless it exceeds **$200**; above that, capital gain. [B02 / 26 U.S.C. 988 [S24]]
5. **U.S. reporting penalties — where large money is actually lost.**
   - **FBAR (FinCEN 114)**: file if aggregate foreign accounts > **$10,000** at any time in the year, whether or not tax is owed. Non-willful penalty: up to **$16,536** per report (31 CFR 1010.821, penalties assessed on/after 2025-01-17). Willful: greater of **$165,353** or **50%** of the account balance. Bittner (2023): non-willful cap applies per report, not per account. [B01, B05]
   - **Form 8938 (FATCA)**: thresholds vary by filing status/residence (higher for expats: e.g. $200k year-end/$300k any-time single; $400k/$600k joint abroad). $10,000 + $10,000 for each 30 days after IRS notice, up to $60,000 potential max. [B03, B04]
   - **Form 1116 FTC**: PRC tax on the same income can offset U.S. tax, subject to category and limitation rules — credit, not refund. [S20]
6. **Unlawful routes = fines, not fees.** PRC FE regulations: evasion/illegal purchase of FX — warning, confiscation of illegal gains, fine up to **30%** of illegal amount; serious cases **30–100%** + criminal liability. Crypto bridges are illegal financial activity in China; underground banks (对敲) likewise. Quota pooling ("friends' $50k quotas") is expressly prohibited. [S13, S14, S06 Art. 7]

## The answer to "best way, least tax" — decision order

| # | Situation | Route | Published cost at $400k | Catch | Official sources |
|---|---|---|---|---|---|
| 1 | Balance is documented, after-tax China income (salary/services) | **M01** evaluate bank conversion + SWIFT wire to own US account (eligibility unverified) | $86.97 HSBC Premier/Advance (0.1% capped CNY 500 + CNY 120 cable) | Needs tax vouchers + contract/invoices; spread unverified; amount blank | [S03](https://www.safe.gov.cn/tianjin/2026/0713/3088.html) · [S05](https://www.safe.gov.cn/tianjin/2024/0621/2529.html) · [S01](https://www.safe.gov.cn/tianjin/2024/0430/2464.html) · [S06](https://www.pbc.gov.cn/english/130733/2025080815071447034/index.html) · [S29](https://www.hsbc.com.cn/content/dam/hsbc/cn/docs/document-download/tariff-of-Accounts-services-for-personal-customers-v2.pdf) |
| 2 | Same facts + own-name HSBC accounts in both countries + Premier/PB | **M03** Global Transfer (after M01/M02 conversion basis) | **$0** published fee (PB/Premier); USD 20 (Advance) | Same SAFE basis required; Premier eligibility (TRB ≥ CNY 500,000) | [S29](https://www.hsbc.com.cn/content/dam/hsbc/cn/docs/document-download/tariff-of-Accounts-services-for-personal-customers-v2.pdf) · [S03](https://www.safe.gov.cn/tianjin/2026/0713/3088.html) · [S01](https://www.safe.gov.cn/tianjin/2024/0430/2464.html) |
| 3 | You hold PRC ID / Foreign Permanent Resident ID; no income docs | **M02** annual quota | $534.66 over 8 calendar years ($66.83/yr × 8) | ~USD 50k/yr cap; purchase facilitation for foreigners limited to PR-ID holders (S05) — confirm | [S01](https://www.safe.gov.cn/tianjin/2024/0430/2464.html) · [S02](https://www.safe.gov.cn/en/2007/0105/819.html) · [S05](https://www.safe.gov.cn/tianjin/2024/0621/2529.html) · [S29](https://www.hsbc.com.cn/content/dam/hsbc/cn/docs/document-download/tariff-of-Accounts-services-for-personal-customers-v2.pdf) |
| 4 | Emigrated from mainland China / inherited China assets | **M10** / **M11** SAFE-approved transfer | Blank — process fees unpublished | Narrow eligibility; hukou cancellation / inheritance proofs; lump sum OK after approval | [S09](https://www.pbc.gov.cn/english/130721/2025080815062856255/index.html) · [S08](https://www.safe.gov.cn/en/2014/0801/741.html) · [S01](https://www.safe.gov.cn/tianjin/2024/0430/2464.html) · [S15](https://fgk.chinatax.gov.cn/eng/c102962/c102967/c102997/c103004/c5245849/content.html) |
| 5 | Own individual trade business | **M13** settlement account | Blank | Genuine trade only; quota-exempt with valid docs | [S01](https://www.safe.gov.cn/tianjin/2024/0430/2464.html) · [S02](https://www.safe.gov.cn/en/2007/0105/819.html) · [S06](https://www.pbc.gov.cn/english/130733/2025080815071447034/index.html) |
| 6 | Documented after-tax salary, recent tax records (≤3 yrs) | **M04** Wise (from-CNY) | Blank — quote shown in-app only | Own accounts only; ≤CNY 300k per bank-app transfer; limit = documented salary | [S30](https://wise.com/help/articles/2955298/guide-to-cny-transfers) |
| 7 | Almost any; no FX paperwork | **M06** ATM cash | Blank — card fees unverified | Cap CNY 100,000/person/yr (~USD 14,027); 8+ years for $400k | [S07](https://www.safe.gov.cn/en/2017/1230/1397.html) · [S13](https://www.safe.gov.cn/beijing/2018/1221/1010.html) |
| 8 | Small amounts only | **M07** USD cash carry-out | Unverified; blank | USD 5,000/trip no permit; 80 trips for $400k — impractical | [S10](https://www.gov.cn/gongbao/content/2004/content_63085.htm) · [S02](https://www.safe.gov.cn/en/2007/0105/819.html) · [S28](https://www.cbp.gov/travel/international-visitors/money-monetary-instruments) · [S29](https://www.hsbc.com.cn/content/dam/hsbc/cn/docs/document-download/tariff-of-Accounts-services-for-personal-customers-v2.pdf) · [S13](https://www.safe.gov.cn/beijing/2018/1221/1010.html) |
| — | "Just use crypto / pool quotas / underground bank" | **M14–M17 — do not use** | Fine exposure $120,000–$400,000 (30–100%) | Confiscation + criminal liability; no legal recourse | [S14](https://www.pbc.gov.cn/tiaofasi/144941/3581332/2026020619591971323/index.html) · [S13](https://www.safe.gov.cn/beijing/2018/1221/1010.html) |

*Spread model unverified — the bank's quote governs.

## Exactly what to do, step by step (M01, the usual answer)

1. **Gather source-of-funds proof**: employment contract or service invoices; payslips; bank statements showing each credit; the balance must tie to the documents.
2. **Get the tax records**: download your PRC individual income tax payment records from the IIT app, or request a 完税证明 (tax payment certificate) at the tax service hall for every year covered.
3. **Review whether PRC tax is unpaid** — the actual reason for this account's restriction is unknown. Under the IIT law, 2022 onward comprehensive income is settled annually (汇算清缴); tax due is on the income, not the remittance.
4. **Book the account-holding branch's FX counter** (this is not reliably doable at a machine) and bring: passport, tax records, income contract/invoices, account passbook/card.
5. **Ask for the executable all-in quote in writing**: applied CNY→USD rate, 0.1% fee (min CNY 100/max CNY 500), CNY 120 cable, any Pay Exact surcharge CNY 200, and whether the receiving/correspondent bank charges extra (not covered by the tariff).
6. **Complete the conversion and the wire** to your own US account (same-name). Keep the exchange memo (水单), the MT103/remittance advice and every receipt.
7. **US side**: file FBAR by April 15 (auto-extension to Oct 15) and Form 8938 with your return if thresholds are met; claim PRC tax on Form 1116 subject to limits. If past years were never reported, talk to a tax professional about **Streamlined Filing Compliance Procedures** — eligibility requires non-willful conduct and other conditions; an IRS examination or criminal investigation can disqualify the taxpayer.
8. **Never** split the remittance with family/friends' quotas, use false invoices, or route through crypto/underground banks to "save" the spread. The fine bands (up to 30% / 30–100% of the illegal amount) dwarf any saving, and criminal liability applies.

## What is missing to price YOUR situation

Balance source and years; PRC tax paid; whether you hold PRC ID/hukou history; residency (statutory residence definitions and the personal-FX operational rules may differ; ask the bank which category applies); your US filing history; and your bank's live quote. Until those are supplied, **no honest personal tax figure or "best route for you" can be certified** — see flags F01–F02.

**Bottom line:** evaluate *documented source of funds → approved bank conversion/wire → correct US reporting*. A cheapest route or personal tax liability cannot be determined without evidence; unknown values stay blank.
