# China money: what it costs to get yuan out and into dollars

Session `arena/b03f272a-china2` · figures as of 10 November 2026 · sources read 10 November 2026 · research, not personal tax or legal advice.

Live pages: https://sassnarep3-star.github.io/China2/landed-cost-b03f272a/

## The answer

The cheapest lawful way is a bank conversion and one wire to your own U.S. account, backed by proof of where the money came from and that Chinese tax was paid. The U.S. taxes only the exchange gain since you received the yuan. Penalties arise only where the Chinese account went unreported.

| # | Finding | In numbers | Official sources |
|---|---|---|---|
| 1 | Cheapest lawful route: bank conversion against documents, one wire (A1) | $53.38 on $10,000 (0.534%); $270.75 on $100,000 (0.271%); $899.01 on $400,000 (0.225%) at Bank of China's published prices; receiving-bank charges extra (blank, F01) | [S16](https://www.boc.cn/sourcedb/whpj/enindex_1619.html) [S19](https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html) [S01](https://www.safe.gov.cn/tianjin/2026/0713/3088.html) |
| 2 | Send one wire, not many: the fee is capped per wire | One $400,000 wire: ¥410.00 in fees; forty $10,000 wires: ¥8,674.00 | [S19](https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html) [S05](https://www.pbc.gov.cn/english/130733/2025080815071447034/index.html) |
| 3 | No $50,000 ceiling for documented income of a non-domestic individual | The yearly facility is for domestic individuals and permanent-resident ID holders; otherwise the documents decide (F07) | [S01](https://www.safe.gov.cn/tianjin/2026/0713/3088.html) [S04](https://www.safe.gov.cn/tianjin/2024/0430/2464.html) [S02](https://www.safe.gov.cn/tianjin/2024/0621/2529.html) |
| 4 | U.S. tax on conversion = tax on the exchange gain | Yuan from 2023–2025: gain 5.59% to 7.10% of the amount ($5,590 to $7,096 per $100,000; $839 to $1,064 tax at 15%). Yuan from 2011–2016, 2018, 2021: a loss, nothing to tax (F14, F16) | [S30](https://www.govinfo.gov/content/pkg/USCODE-2024-title26/html/USCODE-2024-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm) [S31](https://www.irs.gov/publications/p525) [S32](https://www.irs.gov/taxtopics/tc409) [S23](https://www.federalreserve.gov/releases/g5a/current/) |
| 5 | Penalties come from an unreported account, not the transfer | Filed: $0. Streamlined from abroad: $0. Streamlined in the U.S.: 5% ($5,000 per $100,000). Otherwise up to $16,536 per missed report; willful: greater of $165,353 or 50% per year (F20, F22) | [S38](https://www.irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar) [S46](https://www.irs.gov/individuals/international-taxpayers/us-taxpayers-residing-outside-the-united-states) [S45](https://www.irs.gov/individuals/international-taxpayers/us-taxpayers-residing-in-the-united-states) [S39](https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821) [S40](https://www.govinfo.gov/content/pkg/USCODE-2024-title31/html/USCODE-2024-title31-subtitleIV-chap53-subchapII-sec5321.htm) |
| 6 | Unlawful routes (others' quotas, underground swaps, crypto, false documents) | Chinese fine up to 30% ($30,000 on $100,000), up to 100% in serious cases, criminal liability | [S06](https://www.safe.gov.cn/safe/2008/0806/5321.html) [S05](https://www.pbc.gov.cn/english/130733/2025080815071447034/index.html) [S13](https://www.pbc.gov.cn/tiaofasi/144941/3581332/2026020619591971323/index.html) |

## Pages

- `index.html` summary · `routes.html` 23 methods · `costs.html` every method at every $10,000 step · `penalty.html` the nine layers and U.S. penalty exposure by balance
- `fx-gain.html` exchange gain for 2001 to 2025 · `steps.html` exact steps · `audit.html` 12 repository checks · `flagged.html` 37 open items · `sources.html` 55 official pages

## Limits

Nothing personal is assumed. Source of the money, acquisition dates, residence, filing history and bank are unknown; where the answer depends on them every case is shown. Values with no official source are blank and listed on `flagged.html`. Exchange rates are a snapshot of 10 November 2026 and move daily.

Reproduce: `python3 landed-cost-b03f272a/build.py && python3 landed-cost-b03f272a/verify.py`.
