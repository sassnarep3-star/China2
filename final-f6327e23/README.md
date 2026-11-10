# final-f6327e23 — verified single-answer dashboard

A source-linked answer to one question: a US citizen has RMB in a mainland China bank account and
wants USD in the US with the least tax and cost. This directory is the session's deliverable: eight
static pages, a deterministic cost model, and a verifier.

**Live:** https://sassnarep3-star.github.io/China2/final-f6327e23/

## The answer this site reaches

1. **The conversion is not taxed.** The FX Regulations state that "the State does not restrict current
   international payments and transfers" (Art. 5). The conversion rule requires ID plus source-of-funds
   papers *including tax vouchers* (Art. 59) — the tax is on the income, assessed separately. No
   provision imposing a levy on the exchange itself appears in any text verified here; that is an
   absence, and it is flagged (F06), not asserted as a ruling.
2. **The USD 50,000 limit is not a cap on this route.** Art. 54 puts the annual facilitation quota on
   individuals' FX *sales* and *domestic* individuals' *purchases*. Art. 59 handles a non-domestic
   individual's documented current-account purchase with no quota stated. The trap is the opposite
   direction: "no quota" does not mean "no documents" — the bank decides.
3. **The cost is small and mostly a pricing question.** Bank fee (0.1%, floor CNY 100, cap CNY 500,
   plus CNY 120 cable) + measured FX half-spread 0.21% + a USD 16 receiving fee = **0.70% of $10,000**
   and **0.24% of $400,000**.
4. **The real tax risk is US reporting.** §988(e) personal-transaction exclusion fails above **$200**
   of exchange gain; FBAR bites above **$10,000** aggregate; Form 8938 thresholds are higher. The
   penalty ceilings — $16,536 non-willful, $165,353 willful — are triggered by *not filing*, not by
   converting.
5. **Eligibility, not arithmetic, is the binding constraint.** The money's source (salary vs property
   vs gift vs inheritance) and the account holder's PRC residency/hukou history decide which route is
   open. None of these private facts is assumed anywhere.

## Files

| File | What it is |
|---|---|
| `data/sources.json` | 16 primary sources: URL, locator, verbatim quote, retrieval date |
| `data/routes.json` | 15 methods: legal basis, caps, pros, cons, requirements, steps, unverified fields |
| `model.py` | Cost model — all inputs either quoted from a source or labelled an assumption |
| `data/costs.json`, `data/costs.csv` | 440 rows: 11 route-lines × 40 tiers |
| `build.py` | Renders the 8 pages deterministically |
| `verify.py` | 997 checks: structure, per-row citation, links/fragments, arithmetic, CSV parity, blanks, determinism |
| `browser_check.mjs` | Optional real-Chromium pass at 390 px and 1440 px, plus filter/nav interaction |

## Reproduce

```sh
python3 final-f6327e23/model.py
python3 final-f6327e23/build.py
python3 final-f6327e23/verify.py      # 0 failures expected
```

Optional browser pass (test-only dependencies, kept outside Git):

```sh
npm install --prefix .cache/browser --no-save --package-lock=false playwright-core @sparticuz/chromium
python3 -m http.server 8123 --bind 0.0.0.0 &
node final-f6327e23/browser_check.mjs http://127.0.0.1:8123
```

The bundled Chromium needs NSS/NSPR; unpack `al2023.tar.br` from the package into a directory and point
`LD_LIBRARY_PATH` at its `lib/`, then set `CHROME_PATH` to the extracted binary.

## Rules this directory follows

- Every table row carries a source link. Where no official source prices a value, the cell is blank and
  flagged — never inferred, never rendered as `0`.
- Cost figures are labelled *estimates from public price lists*, not quotes. Tax is never folded into a
  cost total.
- Statutory fine ceilings for unlawful routes are shown as ceilings, not expected costs.
- Another session's files are never edited. Scope: this directory, one CI workflow, an append to
  `COORDINATION.md`.

## Known limits

One bank's tariff (HSBC China) and one US bank's receiving fee (Bank of America) are the only published
prices verified. Correspondent-bank deductions, the user's actual FX spread, and a personal tax
computation are all unknown. See `review.html` for the full flag list.

**Research, not tax or legal advice.**
