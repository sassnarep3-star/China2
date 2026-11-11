# guide-be3c20e8 · executive summary

Independent CNY-to-USD decision guide read on 2026-11-11. Research, not individualized tax, legal or investment advice. No private account facts were supplied, no bank was contacted, no funds moved and no tax return was filed.

## Least-penalty answer

No PRC provision reviewed here imposes a separate tax on the mere act of converting CNY into USD. That is not a conclusion that your balance is tax-free: PRC individual income tax applies by income type and residence, and a bank can refuse the transaction without lawful-source and tax documents. The least-penalty path is to settle or document any tax on the underlying funds, use one of the lawful bank/approval routes, avoid prohibited workarounds, and meet U.S. reporting duties on time.

## What is published

- 34 primary sources with exact quotes, locators, figures and limitations: [sources.html](sources.html).
- 20 distinguishable routes, including 14 gating questions and 12 penalty layers: [methods.html](methods.html), [questions.html](questions.html), [penalties.html](penalties.html).
- 800 cost rows: every 10,000 step from $10,000 to $400,000 for every method: [costs.html](costs.html), [costs.csv](data/costs.csv), [costs.json](data/costs.json).
- 23 flagged items, all **needs review / non-blocking**: [flagged.html](flagged.html).
- A mechanical line-by-line audit of 416 tracked text files and 235,815 lines: [review.html](review.html).

## Headline arithmetic, with limits

BOC's reference-only board implies a 0.2094% midpoint spread; HSBC's dated board implies 0.4979%. Among priced one-transfer bank routes, the lowest published known-component illustration is **$49.79** at $10,000 (HSBC China outward telegraphic transfer (Private Banking individual)) and **$898.75** at $400,000 (BOC documented-income online FX purchase + one wire). Every all-in total, intermediary/receiving charge, executable rate, future rate, personal tax and eligibility outcome is **blank and flagged**. Bank of China's page says the actual transaction rate governs; the web board is for reference only: https://www.boc.cn/sourcedb/whpj/

## Decision sequence

1. Establish the origin, tax-paid status and 完税证明 for every CNY in the account.
2. Classify PRC status, residence, emigration/hukou and foreign permanent-residence ID facts.
3. Ask the bank in writing for its eligibility decision, executable rate and full fee schedule.
4. Compare a documented-income wire, the applicable approval route and any provider route using the cost ladder's blanks.
5. Reconstruct acquisition dates/rates for U.S. §988 and review FBAR, Form 8938, Form 3520 and CBP filing history before filing.
6. Do not use quota splitting, underground swaps, crypto, false labels, excess cash or third-party straw-man channels.

## Reproduce

```sh
PYTHONDONTWRITEBYTECODE=1 python3 guide-be3c20e8/data/make_sources.py
PYTHONDONTWRITEBYTECODE=1 python3 guide-be3c20e8/audit.py
PYTHONDONTWRITEBYTECODE=1 python3 guide-be3c20e8/model.py
PYTHONDONTWRITEBYTECODE=1 python3 guide-be3c20e8/build.py
PYTHONDONTWRITEBYTECODE=1 python3 guide-be3c20e8/verify.py
node --check guide-be3c20e8/assets/app.js
```

The build is deterministic: no clock, network call or random value is used. `verify.py` independently recomputes every cost row from `sources.json`, checks every blank/flag, every official link in every substantive table row, all local links and anchors, and each review finding against its file:line text.
