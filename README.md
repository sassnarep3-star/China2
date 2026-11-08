# China Money — USD repatriation research for a US citizen

**Live dashboard:** https://sassnarep3-star.github.io/China2/

One question, answered with sources: what does it cost to turn RMB in a mainland Chinese bank account into USD in a US account, from **$10,000 to $400,000** — and what is the cheapest lawful way to do it?

Everything numeric is either stated by an official PRC or US publication or computed from one, with the arithmetic and assumptions printed next to it. Anything that no official source states is **left blank and flagged**, never inferred.

---

## Headline finding

**There is no Chinese tax on converting your own money.** The PRC Individual Income Tax Law taxes nine categories of income; a currency conversion is not one of them. What people experience as a "conversion penalty" is one of six other layers:

| Layer | What it is | Verified position |
|---|---|---|
| L1 | PRC tax on the conversion itself | **0%** |
| L2 | PRC income tax on the money's source | 3%–45% progressive, 5%–35% business, 20% flat |
| L3 | Documentary gate at the bank | ID + source documents **including tax vouchers** |
| L4 | US tax on moving your own funds | **0%** (§988(e) personal transaction) |
| L5 | US residual after the foreign tax credit | usually **$0**, computed per amount |
| L6 | Bank spread and wire fees | **unverified** — no official publication exists |
| L7 | Reporting duties (FBAR, 8938, 3520, CMIR) | $0 if filed |
| L8 | Fines on prohibited channels | up to 30%, or 30%–100% if serious |

At $400,000: statutory cost of converting already-taxed money **$0**; PRC tax if the balance were untaxed labour income **$148,896**; PRC tax if it were an asset gain at 20% **$80,000**, leaving **$23,134** of US tax after the credit; fine exposure on a prohibited channel **$120,000 to $400,000**.

The single fact that decides which number applies is whether the PRC tax on the income was already paid and can be evidenced.

## What is on the site

| Page | Contents |
|---|---|
| `index.html` | Landing overview, decision table, headline numbers |
| `costs.html` | **40-tier cost table, $10,000 → $400,000 in $10,000 steps**, cost by method, optional all-in calculator |
| `matrix.html` | Method × amount matrix: operations or years needed for every lawful channel at every tier |
| `methods.html` | All 22 methods, including 5 prohibited ones, with verified limits, costs and sources |
| `steps.html` | Step-by-step execution for each lawful route, tied to the rule that requires each step |
| `penalty.html` | Six-layer decomposition of the "conversion penalty", in rates and in dollars |
| `taxes.html` | Verified PRC and US tax and reporting thresholds |
| `flagged.html` | 16 flagged items: unverified values, unknown personal facts, repository irregularities |
| `sources.html` | 22-source official registry, marked for what was re-read this session |
| `audit.html` | Line-by-line audit of the three earlier dashboards in this repo |
| `summary.html` | Executive summary |

Machine-readable: `data/cost-model.json`, `data/cost-tiers.csv`, `data/repatriation-methods.csv`.

## Reproduce and verify

Python 3.9+ only; no install, no network at build time.

```sh
python3 scripts/build_site.py     # deterministic HTML + JSON + CSV
python3 scripts/verify_site.py    # 2,539 independent checks
```

The verifier deliberately does not import the builder. It re-derives every figure from bracket tables transcribed the way the official publications print them, then checks the rendered HTML, the JSON and the CSV against those figures, confirms every external link sits on an official domain, resolves every local link and fragment, and fails if any stated count drifts from the data.

Optional real-browser test (test-only dependencies; the site itself has no runtime dependencies):

```sh
npm install --no-save --package-lock=false playwright-core @sparticuz/chromium
LD_LIBRARY_PATH=<unpacked-libs> node .cache/browser-test.cjs   # 143 checks, desktop + 390px
```

## Method and limits

- **Official sources only.** No commercial bank, fintech or forum page is used for any value. Two earlier dashboards in this repository did use them; that is flagged in `audit.html` (A05) rather than repeated.
- **Blank means blank.** Commercial spreads and fees are empty at every amount. If you want a total, enter your own quote in the calculator.
- **Model arithmetic is labelled.** The PRC and US columns are arithmetic on statutory rates under stated assumptions (resident status, single filer, no other income, one exchange rate). They are illustrations, not determinations.
- **Personal facts are declared unknown**, not assumed: whether tax was paid, the cost basis, prior US filing compliance, whether exchange memos exist.
- **Rate date.** All RMB↔USD conversions use the PBOC central parity of 2026-11-06 (USD 1 = CNY 6.7168). The rate moves daily.

## Earlier research in this repository

`docs/`, `site/` and `portal/` are three independent dashboards from earlier sessions. They are preserved unchanged and remain live at their original paths. They disagree in places — different route counts, different source standards, and two substantive mischaracterisations corrected here (§988 gain is ordinary, not capital; the 35% Form 3520 penalty belongs to trusts, not gifts). The audit page lists every finding with its source.

## Publishing

GitHub Pages serves this repository natively from `main` at the repository root. `index.html` at the root is the landing page; `.nojekyll` is present. CI runs `build_site.py` + `verify_site.py` plus the three earlier sessions' suites on every pull request and on `main`.

**Research, not legal, tax or investment advice.** No funds were moved and no returns were filed. This repository is public: never add passports, account numbers, bank statements, tax IDs or private tax records.
