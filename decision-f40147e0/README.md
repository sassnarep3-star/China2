# decision-f40147e0 — fresh dated verification pass and decision dashboard

Session `arena-f40147e0`. This section is additive: it does not edit any other section's files, and it
states which existing pages it re-read.

**What it answers.** Whether a U.S. citizen can move a CNY balance out of mainland China lawfully, what
that costs at every USD 10,000 step from USD 10,000 to USD 400,000, what the "conversion penalty"
actually consists of, and what must be known before a route can be chosen.

## Files

| File | Purpose |
|---|---|
| `data/sources.json` | 26 pages fetched on 2026-11-11, each with the exact words relied on, a working translation, the retrieval time and a stated limit |
| `data/methods.json` | 24 methods: status, pricing spec (or `null`), pros, cons, step-by-step, sources, flags |
| `data/flags.json` | 16 unresolved items, with what would close each one |
| `model.py` | recomputes every cell from the ledgers; writes `data/costs.json` and `exports/` |
| `build.py` | renders 9 pages; no number is typed into the HTML |
| `verify.py` | independent re-derivation and 4,347 checks |
| `exports/cost-ladder.csv` / `.json` | the same rows with their source URLs |

## Reproduce

```sh
PYTHONDONTWRITEBYTECODE=1 python3 decision-f40147e0/model.py
PYTHONDONTWRITEBYTECODE=1 python3 decision-f40147e0/build.py
PYTHONDONTWRITEBYTECODE=1 python3 decision-f40147e0/verify.py
node --check decision-f40147e0/assets/app.js
```

CI: `.github/workflows/verify-decision-f40147e0.yml` rebuilds and re-verifies on every pull request and on
pushes to `main`.

## Method, stated plainly

1. **Read the publisher, not a summary.** Every rate and fee comes from the bank's own board or tariff page,
   or from the statute/regulation on a government domain. Quotes and retrieval times are in `sources.json`.
2. **Price only what is published.** A method with a published selling rate and a published fee formula is
   priced: `amount x (sell / reference mid - 1) + clamp(0.1% x CNY, floor, cap) + cable`, all divided by the
   reference mid. Anything else stays blank with the reason recorded.
3. **Blank is not zero.** ICBC, ABC and CCB could not be read at all (script-rendered boards); their rows are
   blank and flagged F04. Wise publishes no CNY fee table (F07). The U.S. receiving fee could not be verified
   (F06).
4. **Illegal routes are listed, not described.** Four prohibited channels appear with their statutory penalty
   and no instructions.
5. **The reference mid is arithmetic.** SAFE's parity table is script-rendered and returned no rows, so the
   reference is the mean of the three readable bank mids (6.6763571 CNY/USD) — flagged F01.

## What this section does not do

It does not compute anyone's tax, certify eligibility, quote a provider, or assert that a particular route
will be accepted for a particular account. It does not re-verify every source cited elsewhere in the
repository (F16); see `audit.html` for exactly which load-bearing numbers were re-checked.
