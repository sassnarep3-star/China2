# China Money · China2

A source-linked research dashboard about lawful mainland China CNY→USD conversion and repatriation for a U.S. citizen. **Research, not personalized tax/legal advice.** No funds moved or returns filed.

**Website:** https://sassnarep3-star.github.io/China2/
**Cost ladder (start here):** [ladder/index.html](ladder/index.html) — every route priced at each $10,000 step from $10,000 to $400,000, with a source link per row and unverified values left blank and flagged.
**Executive summary:** [research/EXECUTIVE_SUMMARY.md](research/EXECUTIVE_SUMMARY.md)
**Verification and limitations:** [research/METHODOLOGY.md](research/METHODOLOGY.md)
**Task board / publication record:** [COORDINATION.md](COORDINATION.md)

## What's included

- 22 legal routes, delivery options, conditional alternatives and rejected workarounds—not 22 independent quotas.
- 67 source-linked research rows, 24 official primary sources and nine published review flags.
- Separate pages for routes, conversion costs, Chinese/U.S. tax/reporting, execution checklist, flags and evidence.
- Searchable tables, status filters, print support and CSV/JSON/Markdown downloads.
- Unknown numerical values left blank. Analytical conclusions labeled separately from source-described rules.

**Key conclusion:** start by establishing ownership and the legal source of the balance. For qualifying documented lawful China employment income, investigate the authorized bank conversion/remittance route; compare eligible provider channels using executable all-in quotes. Do not conflate source-income tax, FX restrictions, spread, transfer fees, FX gains and reporting penalties. No cheapest provider or individual tax amount can be certified from the private facts supplied so far.

## Reproduce

Python 3.11+ and Node 20+; no install required for the standard build/tests:

```sh
python scripts/build.py
python scripts/validate.py
node --check docs/assets/app.js
node scripts/test_ui.js
python -m http.server 8000 --bind 0.0.0.0 --directory docs
```

Open the served site. All paths are relative, so the same output works at the GitHub Pages `/China2/` project subpath. No browser-facing localhost API calls exist.

Canonical research data is in `research/findings.json` and `research/sources.json`. `scripts/seed_research.py` preserves the manually reviewed initial ledger; **do not rerun it over subsequent editorial changes** unless updating the seed too. The build reads the canonical JSON directly, not the seed. Edit content there and rebuild. Product source evidence must not be treated as a regulator's guarantee.

Optional real-browser test (test-only dependencies, not site dependencies):

```sh
npm install --prefix .cache/browser --no-save --package-lock=false playwright-core @sparticuz/chromium
# with the local server running:
node scripts/browser_test.cjs
```

The test unpacks its Chromium libraries into the temporary directory. Large dependencies and screenshots are ignored; they are not deployed.

## Publishing

GitHub Pages uses the repository's existing native **`main` root** build. Root `index.html` redirects to the checked-in **`docs/` dashboard**; no settings change is needed. The validation workflow runs for pull requests and pushes. Legacy `docs/methods.html` and `docs/flagged.html` remain as compatibility redirects. Prior-session material is preserved, not endorsed as current advice, in `research/previous-dashboard/`. Generated files are checked in so Pages has no package-install/build dependency. Branch work remains on the Arena-assigned `arena/996dc508-china2` branch.

Every research table row links to an official source. CI checks citation coverage and local links; external source availability is not continuously checked. See the source ledger for what was actually read and the Flagged for Review page for discrepancies and unconfirmed values.

**Privacy:** This repository and Pages site are public. Never add passports, account numbers, bank statements, tax IDs, signed authorizations or private tax records.

---

## Supplementary deep-dive analysis (session `arena/5cdc93ae-china2`)

An independent, deeper analysis section lives in [`deep-dive/`](deep-dive/index.html), published at
**https://sassnarep3-star.github.io/China2/deep-dive/**. It is **supplementary** — the canonical
dashboard is the one served at the repository root.

- [Supplementary dashboard](deep-dive/index.html) — headline finding, ranked routes, the five layers of the conversion penalty
- [Conversion methods catalogue](deep-dive/methods.html) — 12 lawful channels and 7 prohibited ones, each with cost, legal risk, pros and cons
- [China FX rules](deep-dive/china-rules.html) — quotas, penalties, criminal thresholds
- [Tax costs & treaty](deep-dive/tax-costs.html) — Chinese rates and every verified US–China treaty rate
- [US obligations](deep-dive/us-obligations.html) — FEIE, FTC, FBAR, Form 8938, § 988(e)
- [Penalty analysis](deep-dive/analysis.html) — the conversion penalty in five separable layers, with worked scenarios
- [Flagged for review](deep-dive/flagged.html) — unverified values, with the best source found and what would close each one
- [Source registry](deep-dive/sources.html) — every source used, with its status

Research files: [`research/00-source-registry.md`](research/00-source-registry.md) … [`research/06-penalty-breakdown.md`](research/06-penalty-breakdown.md), indexed at [`research/README.md`](research/README.md). Executive summary: [`research/EXECUTIVE_SUMMARY_arena-5cdc93ae.md`](research/EXECUTIVE_SUMMARY_arena-5cdc93ae.md).

**Headline finding (as corrected on integration review 2026-11-10):** SAFE states officially that individual FX amounts **above** the USD 50,000 annual facilitation limit can be handled at banks with ID plus supporting materials when the transaction background is true ([SAFE, 2015 press-conference Q&A](https://www.safe.gov.cn/en/2015/1111/1175.html)), so the USD 50,000 figure behaves largely as a *documentation* threshold rather than an absolute ceiling — **but** eligibility for the facility depends on individual status: the 2007 SAFE rules tie FX *purchases* to *domestic* individuals, and State Council Decree No. 532 art. 52(2) counts foreign nationals resident in China ≥1 year as 境内个人 (see `ladder/flagged.html` F02). If the money is personal, lawfully-earned and its source already subjected to PRC income tax in the correct category, **the conversion itself adds no further PRC income tax** — that is not a personalized tax ruling: outcome depends on income category, source, residency and U.S. foreign-tax-credit limits, none of which are determined here. The bank's FX spread and any U.S. currency gain above USD 200 under 26 U.S.C. § 988(e) still apply. Any "0% / cheapest" labels in this supplementary section are modelled comparisons, not personalized rankings — see [Flagged for Review](deep-dive/flagged.html).

`deep-dive/` is plain static HTML with no build step and no runtime dependencies. Since the 2026-11-10 integration it is scanned by CI (`verify-deep-dive`): local links and anchors, HTML parse, table-row source links, and the integration-review correction markers. Every table row carries an official source link; unconfirmed values are left blank and flagged.
