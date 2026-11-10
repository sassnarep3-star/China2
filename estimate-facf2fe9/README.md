# estimate-facf2fe9 — published-rate cost estimates

Session `arena/facf2fe9-china2`. Live at <https://sassnarep3-star.github.io/China2/estimate-facf2fe9/>.

What this section adds to the repository: the cost of moving renminbi to US dollars worked out from the
rates and fees that the banks themselves published on 10 November 2026, instead of a modelled spread or a blank.

| Page | Content |
|---|---|
| `index.html` | Summary, key figures, which route fits which source of funds |
| `costs.html` | Bank rates and fees as read; 23 methods at every USD 10,000 step to USD 400,000 |
| `methods.html` | Who may use each method, limits, steps, pros and cons |
| `tax.html` | Chinese tax by source of funds, US rules, exchange-gain illustration |
| `sources.html` | 47 official pages with the sentences relied on |
| `repo-review.html` | Re-check of the rest of the repository against today's readings |
| `flagged.html` | Flagged for Review: unverified values, limits, assumptions |

## Rules followed

- Every table row links directly to an official page (bank, regulator, tax authority, statute).
- A value that was not confirmed from an official page is blank and flagged. Nothing is inferred.
- Arithmetic is declared: cost = amount × (selling rate ÷ reference mid − 1) + fees ÷ reference mid.
  The reference mid is the average mid-point of the five mainland boards read; it is not a published rate.
- General information, not tax or legal advice.

## Rebuild and check

```
PYTHONDONTWRITEBYTECODE=1 python3 estimate-facf2fe9/model.py    # data/costs.json
PYTHONDONTWRITEBYTECODE=1 python3 estimate-facf2fe9/build.py    # pages and exports/costs.csv
PYTHONDONTWRITEBYTECODE=1 python3 estimate-facf2fe9/verify.py   # independent checks
```

`scan_repo.py` writes `data/repo_scan.json`, a dated snapshot of a line-by-line scan of the other
sections. It is run by hand, not in CI, because other sessions keep adding files.

## Data

`data/sources.json` (ledger with quotes), `data/inputs.json` (rates, fees, limits), `data/methods.json`,
`data/tax.json`, `data/flags.json`, `data/repo_review.json`, `data/repo_scan.json`, `data/costs.json`
(generated), `data/capture-log.md` (raw notes taken while reading the pages).
