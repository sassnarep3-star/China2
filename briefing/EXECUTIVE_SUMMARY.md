# Executive Summary — China money: getting CNY out as a U.S. citizen

**Session:** arena/dc2c65bd-china2 · **Date:** 2026-11-10 · **Status:** research, not advice
**Live site:** https://sassnarep3-star.github.io/China2/briefing/ · **Ledgers:** `repatriate/data/*`, `briefing/build.py`

> Every figure below is tied to an official source retrieved by this or a prior session. Anything unverifiable is **blank and flagged** on the [Flagged page](flagged.html).

## The one-line answer

There is **no tax on converting CNY into USD** — not in China, not in the U.S. The "considerable taxes" people describe are almost always one of four different things: (1) PRC individual income tax already owed on the income that created the balance, (2) the bank's exchange-rate spread and wire fees (not tax), (3) PRC penalties for unlawful movement (up to 30% / 30–100%), or (4) U.S. reporting penalties (FBAR / Form 8938) for an undeclared account. Fix those, and a documented, after-tax balance moves out lawfully via a bank wire — the least-tax path is paperwork, not cleverness.

## What the "conversion penalty" actually is (line by line)

1. **PRC: no conversion tax.** SAFE's individual FX regime sets an annual facilitation quota (USD 50,000 equivalent/person/year for domestic individuals, purchases and sales) and an authenticity review; it levies no tax on buying/selling FX. Over the quota, transactions are not forbidden — authenticity review is "strengthened". [SAFE 2007 / SAFE Tianjin rules (S01, S02)]
2. **PRC individual income tax** attaches to the *income*, when it arose — 3%–45% progressive comprehensive-income rates after the RMB 60,000 annual deduction; flat 20% on interest, dividends and property transfers. Owed regardless of remittance; if unpaid, the bank route stalls until the tax certificate exists. [PRC IIT Law, S15]
3. **The bank's spread + fees — the real, ordinary cost.** Not a tax. For HSBC China Premier/Advance (current tariff, effective 2026-10-31): outward SWIFT wire 0.1% of amount, min CNY 100 / max CNY 500, **plus** CNY 120 cable — a $400,000 wire costs CNY 620 ≈ **$86.97** in published fees. Private Banking individuals: free. Global Transfer to your own overseas HSBC account: free (PB/Premier) / USD 20 (Advance). The **spread is unpublished** and is the largest cost component; modelled band 0.30–1.50% (unverified assumption). [HSBC tariff, B06]
4. **U.S. tax on the conversion itself.** None on the exchange. Only *exchange-rate gain on the currency position* can be taxed; IRS Pub. 525: a gain on a **personal** foreign currency transaction is not included in income unless it exceeds **$200**; above that, capital gain. [B02 / 26 U.S.C. 988 [S24]]
5. **U.S. reporting penalties — where large money is actually lost.**
   - **FBAR (FinCEN 114)**: file if aggregate foreign accounts > **$10,000** at any time in the year, whether or not tax is owed. Non-willful penalty: up to **$16,536** per report (31 CFR 1010.821, penalties assessed on/after 2025-01-17). Willful: greater of **$165,353** or **50%** of the account balance. Bittner (2023): non-willful cap applies per report, not per account. [B01, B05]
   - **Form 8938 (FATCA)**: thresholds vary by filing status/residence (higher for expats: e.g. $200k year-end/$300k any-time single; $400k/$600k joint abroad). $10,000 + $10,000 for each 30 days after IRS notice, up to $60,000 potential max. [B03, B04]
   - **Form 1116 FTC**: PRC tax on the same income can offset U.S. tax, subject to category and limitation rules — credit, not refund. [S20]
6. **Unlawful routes = fines, not fees.** PRC FE regulations: evasion/illegal purchase of FX — warning, confiscation of illegal gains, fine up to **30%** of illegal amount; serious cases **30–100%** + criminal liability. Crypto bridges are illegal financial activity in China; underground banks (对敲) likewise. Quota pooling ("friends' $50k quotas") is expressly prohibited. [S13, S14, S06 Art. 7]

## The answer to "best way, least tax" — decision order

| # | Situation | Route | Published cost at $400k | Catch |
|---|---|---|---|---|
| 1 | Balance is documented, after-tax China income (salary/services) | **M01** bank conversion + SWIFT wire to own US account | $86.97 HSBC Premier/Advance (0.1% capped CNY 500 + CNY 120 cable) | Needs tax vouchers + contract/invoices; spread unverified (model 0.30–1.50% ≈ $1,200–$6,000) |
| 2 | Same facts + own-name HSBC accounts in both countries + Premier/PB | **M03** Global Transfer (after M01/M02 conversion basis) | **$0** published fee (PB/Premier); USD 20 (Advance) | Same SAFE basis required; Premier eligibility (TRB ≥ CNY 500,000) |
| 3 | You hold PRC ID / Foreign Permanent Resident ID; no income docs | **M02** annual quota | $534.66 over 8 calendar years ($66.83/yr × 8) | ~USD 50k/yr cap; purchase facilitation for foreigners limited to PR-ID holders (S05) — confirm |
| 4 | Emigrated from mainland China / inherited China assets | **M10** / **M11** SAFE-approved transfer | Blank — process fees unpublished | Narrow eligibility; hukou cancellation / inheritance proofs; lump sum OK after approval |
| 5 | Own individual trade business | **M13** settlement account | Blank | Genuine trade only; quota-exempt with valid docs |
| 6 | Documented after-tax salary, recent tax records (≤3 yrs) | **M04** Wise (from-CNY) | Blank — quote shown in-app only | Own accounts only; ≤CNY 300k per bank-app transfer; limit = documented salary |
| 7 | Almost any; no FX paperwork | **M06** ATM cash | Blank — card fees unverified | Cap CNY 100,000/person/yr (~USD 14,027); 8+ years for $400k |
| 8 | Small amounts only | **M07** USD cash carry-out | $0 published; spread 0.80–3.00%* | USD 5,000/trip no permit; 80 trips for $400k — impractical |
| — | "Just use crypto / pool quotas / underground bank" | **M14–M17 — do not use** | Fine exposure $120,000–$400,000 (30–100%) | Confiscation + criminal liability; no legal recourse |

*Spread model unverified — the bank's quote governs.

## Exactly what to do, step by step (M01, the usual answer)

1. **Gather source-of-funds proof**: employment contract or service invoices; payslips; bank statements showing each credit; the balance must tie to the documents.
2. **Get the tax records**: download your PRC individual income tax payment records from the IIT app, or request a 完税证明 (tax payment certificate) at the tax service hall for every year covered.
3. **Fix any unpaid PRC tax first** — this is the step that stalls $400k balances. Under the IIT law, 2022 onward comprehensive income is settled annually (汇算清缴); tax due is on the income, not the remittance.
4. **Book the account-holding branch's FX counter** (this is not reliably doable at a machine) and bring: passport, tax records, income contract/invoices, account passbook/card.
5. **Ask for the executable all-in quote in writing**: applied CNY→USD rate, 0.1% fee (min CNY 100/max CNY 500), CNY 120 cable, any Pay Exact surcharge CNY 200, and whether the receiving/correspondent bank charges extra (not covered by the tariff).
6. **Complete the conversion and the wire** to your own US account (same-name). Keep the exchange memo (水单), the MT103/remittance advice and every receipt.
7. **US side**: file FBAR by April 15 (auto-extension to Oct 15) and Form 8938 with your return if thresholds are met; claim PRC tax on Form 1116 subject to limits. If past years were never reported, talk to a tax professional about **Streamlined Filing Compliance Procedures** — coming forward before the IRS contacts you is categorically better than after.
8. **Never** split the remittance with family/friends' quotas, use false invoices, or route through crypto/underground banks to "save" the spread. The fine bands (up to 30% / 30–100% of the illegal amount) dwarf any saving, and criminal liability applies.

## What is missing to price YOUR situation

Balance source and years; PRC tax paid; whether you hold PRC ID/hukou history; residency (a foreign national resident in China ≥1 full year counts as a "domestic individual" under State Council Decree 532 Art. 52); your US filing history; and your bank's live quote. Until those are supplied, **no honest personal tax figure or "best route for you" can be certified** — see flags F01–F02.

**Bottom line:** the cheapest lawful path is almost always *documented source of funds → one big wire → correct US reporting*. The "tax penalty" is a paperwork problem: unpaid PRC tax on the income and unfiled US foreign-account reports — both fixable, both far costlier to ignore.
