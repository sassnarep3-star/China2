# Executive summary — CNY to USD, verified 2026-11-11

Session `arena/9fe02cf5-china2`. Every figure below is traced to a document re-fetched on 2026-11-11;
the site in this directory is the rendered version and the [verification ledger](verification.html)
carries the quoted sentence and link for each statement.

## The diagnosis

1. **No PRC tax on the act of converting currency was found** in the FX regulations or their implementing
   rules (claim C03, status PARTIAL — an absence-of-evidence result, not a guarantee).
2. **The bank is asking for source-of-funds and tax documents, not a conversion levy.** For a foreign
   individual, the rule requires ID plus transaction materials *including tax documents* (C06).
3. **The expensive layer is PRC income tax on untaxed money**: 3%–45% comprehensive, 5%–35% business,
   flat 20% on interest, dividends, asset transfers and incidental income (C14). Whether it applies here
   is unknown (F10).
4. **Where the money was already taxed and documented, the cost is a bank spread plus a small capped
   wire fee.** At the tariff read today the sender fee is free for Private Banking individuals and capped
   at $92.66 for Premier/Advance at $400,000, including cable (C23).
5. **The spread is the cost that scales, and it is not published.** A dated published benchmark
   (Bank of China's own buy/sell band, 0.420%, 2026-11-11 10:25:02) puts $400,000 at
   about $1,679.84. It is a benchmark, not this account's rate (F03, F12).

## Headline arithmetic (benchmark, not a quote)

| Amount | CNY needed | Published sender fee (M01) | Benchmark spread | Benchmark all-in | % of principal |
|---|---|---|---|---|---|
| $10,000.00 | CNY 66,911.00 | $32.88 | $42.00 | **$74.88** | 0.75% |
| $50,000.00 | CNY 334,555.00 | $67.93 | $209.98 | **$277.91** | 0.56% |
| $100,000.00 | CNY 669,110.00 | $92.66 | $419.96 | **$512.62** | 0.51% |
| $200,000.00 | CNY 1,338,220.00 | $92.66 | $839.92 | **$932.58** | 0.47% |
| $400,000.00 | CNY 2,676,440.00 | $92.66 | $1,679.84 | **$1,772.50** | 0.44% |

All-in at the smallest tier: $74.88 (0.75%). At the largest: $1,772.50 (0.44%).

## What a decision still needs

Twelve questions, each of which changes which routes exist: origin of the balance, PRC tax paid and
documented, SAFE category (domestic individual vs foreign individual vs PR ID holder), acquisition dates
and USD basis, US reporting history, the bank's executable itemised quote, capital-account documents,
proxy vs in person, liquidity need, the holding bank's tariff, whether any 'quick' route was offered,
and the US credit/FEIE plan. See [questions](questions.html) and `data/questions.json`.

## Methods

Twelve routes are catalogued with pros, cons, caps and exact steps: ten lawful or conditional and two
rejected (crypto/USDT and underground or quota-splitting). Rejected routes are penalised at up to 30% of
the amount, or more in serious cases (C26), and RMB-to-virtual-currency business is classified as illegal
financial activity (C16).

## Verification performed

- 21 sources re-fetched over HTTPS on 2026-11-11; excerpts quoted verbatim.
- 27 statements checked: 26 verified verbatim, 1 partial. No statement depends on an inferred private fact.
- 400 cost rows recomputed independently by `verify.py`; 7,000+ structural and arithmetic checks.
- 16 items published on [Flagged for review](flagged.html): unverified values,
  corrections and repository irregularities. None blocks publication.

## Not advice

No personal tax position is asserted, no bank was contacted, no funds moved and no return filed. The
spread and third-party charges for this account remain unknown until an itemised executable quote is
obtained.
