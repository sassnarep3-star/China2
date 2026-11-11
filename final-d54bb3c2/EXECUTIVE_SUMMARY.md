# Getting money out of China — final section d54bb3c2

Session `arena/d54bb3c2-china2`. All figures verified 11 November 2026 against the pages listed in
[`data/sources.json`](data/sources.json) (31 sources, each with the facts taken from it).

## Conclusion

Move the balance with a **documented bank conversion plus a wire to your own US account**, in the largest single
transfer your documents support. There is no tax on the conversion itself. The cost is the bank's FX spread plus a
capped commission, and on the rates read for this section that is **$49.79 on USD 10,000** and **$898.75 on
USD 400,000** (0.225%).

What actually costs money, in order of size:

| Layer | Size | Source |
|---|---|---|
| Bank FX spread, BOC | 0.2094% of the amount | S01 |
| Bank FX spread, HSBC | 0.4979% of the amount | S02 |
| Commission + cable, BOC / HSBC | max CNY 410 / max CNY 620 per wire | S03, S04 |
| US tax on the section 988 currency gain | 6.61% gain in the worked example, first $200 excluded | S07, S27 |
| One willful FBAR year | USD 165,353 | S22 |
| Unlawful conversion treated as evasion | 30% of the amount, up to 100% in serious cases | S09 Art.39 |

## The binding constraint is volume, not tax

| Situation | Route | Source |
|---|---|---|
| Mainland individual, under USD 50,000 a year | Bank conversion inside the annual quota | S08 Art.2 |
| Foreign national with taxed China-source income | Documented purchase against that income | S08 Art.13, S10, S11 |
| Foreign PR/citizenship, hukou cancelled, assets predate it | Emigrant property transfer approval, no SAFE fee | S13, S14 |
| None of the above and a large balance | Split across calendar years, or resolve status first | S08, S14 |

## Cost ladder (cheapest priced route per row)

| Amount | Best route | Cost | % | BOC | HSBC wire | HSBC Premier |
|---|---|---|---|---|---|---|
| $10,000 | M03 | $49.79 | 0.4979% | $53.37 | $82.61 | $49.79 |
| $100,000 | M01 | $270.67 | 0.2707% | $270.67 | $590.35 | $497.85 |
| $200,000 | M01 | $480.03 | 0.24% | $480.03 | $1,088.20 | $995.71 |
| $400,000 | M01 | $898.75 | 0.2247% | $898.75 | $2,083.91 | $1,991.42 |

Full 40-row ladder: [`costs.html`](costs.html) · machine-readable [`data/costs.csv`](data/costs.csv).

## What is not known

17 items are blank or assumed and are listed on [`flagged.html`](flagged.html). The three that move the price most:
correspondent and receiving bank fees (unpublished), the rate HSBC actually applies to Global Transfer (assumption),
and the card FX fee for UnionPay (unpublished).

## Reproduce

```bash
cd final-d54bb3c2
python3 model.py      # costs.csv / costs.json from the board rates
python3 penalties.py  # penalty layers and scenarios
python3 review.py     # mechanical repo review
python3 build.py      # the nine HTML pages
python3 verify.py     # 1,073 checks; exits non-zero on any failure
```

## Pages

`index.html` overview · `summary.html` executive summary · `costs.html` the 40-row ladder ·
`methods.html` 16 routes with pros, cons and steps · `penalty.html` nine cost layers ·
`questions.html` 15 questions with how to answer each · `review.html` repo review ·
`flagged.html` every blank and assumption · `sources.html` the full ledger.
