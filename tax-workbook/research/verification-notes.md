# Verification notes — arena-524bd78a

Date: 2026-11-08 UTC. Scope: U.S. personal foreign-currency disposition / tax-basis workbook only. General route catalogue and cost matrices are owned by other active sessions and are not duplicated here.

## Official sources read directly

- IRS Publication 525 (2025), “Foreign currency transactions”: personal foreign-currency gain is not included unless more than $200; if more than $200, report as capital gain. https://www.irs.gov/publications/p525#en_US_2025_publink1000229538
- 26 U.S.C. § 988 (2024 ed.), GovInfo: §988(a)(1)(A) ordinary default; §988(c)(1)(C) disposition of nonfunctional currency; §988(e)(1)-(3) personal-transaction exception and $200 cliff. https://www.govinfo.gov/content/pkg/USCODE-2024-title26/html/USCODE-2024-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm
- IRS LB&I Concept Unit FCU/CU/C-18.2.1_04 (2016): disposition gain/loss measured between acquisition and disposition; personal-transaction exception. Training material, not law. https://www.irs.gov/pub/fatca/int_practice_units/fcu_cu_c_18_2_1_04.pdf
- IRS Publication 551 (12/2025): basis is investment in property; cost basis usually cost; keep accurate records. https://www.irs.gov/publications/p551
- IRS Topic 409: capital gain/loss = amount realized minus adjusted basis; personal-use losses nondeductible; holding period >1 year long-term; 2025 capital-gain rate thresholds. https://www.irs.gov/taxtopics/tc409
- IRS Schedule D instructions (2025): basis/recordkeeping and holding-period rules. https://www.irs.gov/instructions/i1040sd
- IRS Form 1116 instructions (2025): carry back 1 year and forward 10 years; limitations; no carryover for §951A category; election restrictions. https://www.irs.gov/instructions/i1116
- IRS Foreign Tax Credit page: qualifying taxes, same income, no credit on excluded income, treaty-reduced rate limitation; the general “10 years” refund paragraph on that page is specifically French CSG/CRDS, not a general PRC FTC refund window. https://www.irs.gov/individuals/international-taxpayers/foreign-tax-credit
- IRS yearly average exchange rates: IRS has no official exchange rate; generally accepts any posted rate used consistently; spot rate generally applies when receiving/paying/accruing; 2025 China yuan average 7.129. https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates
- IRS FBAR page: aggregate foreign accounts >$10,000 at any time; April 15 / automatic October 15; records generally five years. https://www.irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar
- IRS Form 8938 threshold page: exact U.S./abroad and filing-status thresholds. https://www.irs.gov/businesses/corporations/do-i-need-to-file-form-8938-statement-of-specified-foreign-financial-assets
- Treasury Reporting Rates of Exchange dataset: official quarterly reporting rates, not current transaction rates; amendments may appear online; exceptions include foreign currencies sold for dollars. https://fiscaldata.treasury.gov/datasets/treasury-reporting-rates-exchange/
- Treasury Reporting Rates of Exchange PDF, September 30, 2026: China-Renminbi 6.7050 foreign currency units per U.S. dollar. The PDF excludes online amendments. https://fiscaldata.treasury.gov/static-data/published-reports/exchange-rates/Rates_of_Exchange_09302026.pdf
- IRS Publication 54 (12/2025): U.S. citizens/resident aliens generally taxed on worldwide income regardless of residence. https://www.irs.gov/publications/p54
- IRS Foreign currency and currency exchange rates: U.S. return amounts in USD; functional currency generally USD unless required otherwise; use rate prevailing when receiving/paying/accruing. https://www.irs.gov/individuals/international-taxpayers/foreign-currency-and-currency-exchange-rates
- 26 U.S.C. § 165(c) (2024 ed.), GovInfo: individual loss deductions limited to business, profit-seeking and specified casualty/theft losses. https://www.govinfo.gov/content/pkg/USCODE-2024-title26/html/USCODE-2024-title26-subtitleA-chap1-subchapB-partVI-sec165.htm

## Failed / excluded candidates

- https://www.irs.gov/individuals/international-taxpayers/foreign-tax-credit-carryover-and-carryback — HTTP 404; replaced by Form 1116 instructions.
- https://www.irs.gov/individuals/international-taxpayers/us-citizens-and-residents-abroad — HTTP 404; replaced by Publication 54 / IRS newsroom guidance.
- IRS international FAQ page says answers are not citable as legal authority; not used as a table-row authority.

## Policy

No personal account facts, acquisition dates, basis, filing status, taxable income, bank quotes, or live FX rates were supplied. Those fields remain blank and are flagged. The only numeric scenario inputs are the user-requested $10,000 increments and Treasury's published 2026-09-30 official reporting rate 6.7050 CNY/USD, clearly labeled as a reference rather than an executable quote. The IRS 2025 yearly-average China rate 7.129 is recorded as a separate reference and is not used in the workbook arithmetic. Arithmetic derived from the Treasury reference is labeled “computed reference,” not a verified transfer cost.
