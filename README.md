# China Money · China2

Source-linked research on lawful mainland China CNY→USD conversion, repatriation routes, PRC/U.S. tax treatment, reporting obligations, and itemized $10,000–$400,000 cost tiers for a U.S. citizen. **Research, not individualized tax, legal, or investment advice.** No personal facts were verified, no transfers were made, and no tax returns were filed.

**Newest pass (2026-11-11):** [decision-f40147e0/index.html](decision-f40147e0/index.html) — three mainland bank boards and four tariffs re-read with retrieval times, 24 methods, 10 priced × 40 tiers ($10k–$400k), 16 flags, and 14 line-by-line re-checks of the earlier sections.
**Previous live-verified dashboard (2026-11-10):** [verify-d5d1f860/index.html](verify-d5d1f860/index.html) — 24 primary documents re-fetched and quoted, 17 methods priced across 40 tiers ($10k–$400k) with the fee arithmetic recomputed independently, 16 published flags, and blanks wherever nothing is published.
**Executive briefing (start here):** [briefing/index.html](briefing/index.html) — the consolidated least-tax answer, all-methods cost tables at every $10,000 step from $10,000 to $400,000, and the source-linked repo audit.
**Website:** https://sassnarep3-star.github.io/China2/
**Cost ladder (start here):** [ladder/index.html](ladder/index.html) — every route priced at each $10,000 step from $10,000 to $400,000, with a source link per row and unverified values left blank and flagged.
**Executive summary:** [research/EXECUTIVE_SUMMARY.md](research/EXECUTIVE_SUMMARY.md)
**Verification and limitations:** [research/METHODOLOGY.md](research/METHODOLOGY.md)
**Task board / publication record:** [COORDINATION.md](COORDINATION.md)

## Primary Entry Points

- **Consolidated Executive Briefing (start here):** [briefing/index.html](briefing/index.html) — least-tax lawful answer, 17 methods with pros/cons/steps, 680-row `$10k→$400k` tables (`7.129` IRS 2025 reference rate + Nov 6, 2026 Fed H.10 `6.6760` sensitivity note), and consolidated repo audit.
- **Cost Ladder Scenario Model:** [ladder/index.html](ladder/index.html) — 20 routes (`15` costed × `40` tiers = `600` rows, `$10k→$400k`), updated to the 31 October 2026 HSBC China Personal Tariff (`2.2.4.x`, `2.2.6.1`, `2.2.2.1`) and SAFE `Huifa [2014] No. 2` §VI lump-sum emigration/inheritance rules.
- **Repatriation Study (Fee Floors):** [repatriate/index.html](repatriate/index.html) — 17 methods × 40 increments = 680 rows (`costs.html`), 31 directly retrieved official/provider sources, blank unverified spreads enforced.
- **Fresh Official-Source Audit (2026-11-10):** [audit-ad300459/index.html](audit-ad300459/index.html) — 27 brief-critical claims checked line-by-line against primary law plus independent 600-row / 680-row arithmetic verification.
- **Source-Only Blank Matrix:** [audit-86f0/costs.html](audit-86f0/costs.html) — 22 methods × 40 tiers with all unverified spreads/totals left explicitly blank.
- **Landing-Page Claim Review:** [audit-0f0f59fe/index.html](audit-0f0f59fe/index.html) — independent review of root claims, caveats, and unresolved facts.
- **Canonical Research Dashboard:** [docs/index.html](docs/index.html) — 22 routes/alternatives, 67 source-linked rows, 24 official primary sources, 9 review flags ([research/EXECUTIVE_SUMMARY.md](research/EXECUTIVE_SUMMARY.md), [research/METHODOLOGY.md](research/METHODOLOGY.md)).
- **Evidence-Ledger Site:** [site/index.html](site/index.html) — 18 methods, strict domain allowlist (`data/*.json`, [EXECUTIVE-SUMMARY.md](EXECUTIVE-SUMMARY.md)).
- **Government-Source Portal:** [portal/index.html](portal/index.html) — `.gov`/`.gov.cn`-only ledger (`reports/CNY_TO_USD_RESEARCH_LEDGER.json`, [reports/EXECUTIVE_SUMMARY_85f37d08.md](reports/EXECUTIVE_SUMMARY_85f37d08.md)).
- **Acceptance Summary & Checks:** [acceptance-373b54a3/index.html](acceptance-373b54a3/index.html) — cross-repo deliverable completeness checks.
- **Task Board & Publication Record:** [COORDINATION.md](COORDINATION.md)

## Key Conclusions (Source-Backed)

1. **No standalone CNY→USD conversion tax** was located in either PRC or U.S. tax statutes. What is commonly experienced as a "conversion tax" or "penalty" is a combination of: (a) **underlying PRC tax** on the income/asset that generated the balance (`3%–45%` comprehensive IIT, `5%–35%` business IIT, `20%` flat asset/dividend/interest IIT or `10%` U.S.–China treaty cap), which SAFE/banks gatekeep via tax certificates (`完税证明` / `纳税记录`); (b) **bank FX spread** (unpublished, typically `0.30%–1.50%` modelled) plus published wire fees (HSBC China 31 Oct 2026 tariff: `0.1%` min CNY 100 / max CNY 500 + CNY 120 cable for Premier/Advance, free for Private Banking); (c) **U.S. reporting/compliance exposure** (FBAR FinCEN 114 `>$10,000` aggregate, non-willful max `$16,536` / willful max `$165,353` or 50% under `31 CFR 1010.821`; Form 8938; Form 3520; Form 1116 FTC / Form 2555 FEIE `$132,900` in 2026 and `$137,300` in 2027); and (d) **PRC penalties (`30%–100%`)** only for unlawful routes (quota splitting, underground swaps, crypto bridges under `Yinfa [2026] No. 42`, false vouchers).
2. **Start with ownership, residence status, and source-of-funds documents.** Citizenships alone does not settle SAFE classification (`State Council Decree 532` Art. 52(2) includes foreign nationals continuously resident ≥1 year as domestic individuals; SAFE 2024 guidance limits the `USD 50,000` purchase facilitation quota among foreign individuals to Foreign Permanent Resident ID holders). For documented lawful current-account RMB income, the primary route is authorized bank FX purchase + SWIFT wire (or HSBC Global Transfer for eligible accounts) backed by matching contracts/payslips and STA tax records.

## Reproduce & Verify Locally

Python 3.11+ and Node 20+; zero external package installs needed (`PYTHONDONTWRITEBYTECODE=1` avoids git-ignored `__pycache__` pollution):

```sh
PYTHONDONTWRITEBYTECODE=1 python3 scripts/build.py && PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate.py
node --check docs/assets/app.js && node scripts/test_ui.js
node tools/build.mjs && node tools/verify.mjs
PYTHONDONTWRITEBYTECODE=1 python3 portal/generate_portal.py && PYTHONDONTWRITEBYTECODE=1 python3 verify_85f37d08.py && node --check portal/app.js
PYTHONDONTWRITEBYTECODE=1 python3 repatriate/build.py && PYTHONDONTWRITEBYTECODE=1 python3 repatriate/verify.py && node --check repatriate/assets/app.js
PYTHONDONTWRITEBYTECODE=1 python3 briefing/build.py && PYTHONDONTWRITEBYTECODE=1 python3 briefing/verify.py && node --check briefing/assets/app.js
PYTHONDONTWRITEBYTECODE=1 python3 audit-86f0/verify.py
PYTHONDONTWRITEBYTECODE=1 python3 audit-0f0f59fe/verify.py
PYTHONDONTWRITEBYTECODE=1 python3 audit-ad300459/verify.py
PYTHONDONTWRITEBYTECODE=1 python3 acceptance-373b54a3/verify.py
PYTHONDONTWRITEBYTECODE=1 python3 ladder/model.py && PYTHONDONTWRITEBYTECODE=1 python3 ladder/build.py && PYTHONDONTWRITEBYTECODE=1 python3 ladder/verify.py && node --check ladder/assets/app.js
```

Run `ladder/model.py` and `ladder/build.py` **last** because `ladder/audit.html` records the non-excluded repository file inventory and generates root `index.html`.

Canonical research data is in `research/findings.json` and `research/sources.json`. `scripts/seed_research.py` preserves the manually reviewed initial ledger; **do not rerun it over subsequent editorial changes** unless updating the seed too. The build reads the canonical JSON directly, not the seed. Edit content there and rebuild. Product source evidence must not be treated as a regulator's guarantee.

Optional real-browser test (test-only dependencies, not site dependencies):

```sh
npm install --prefix .cache/browser --no-save --package-lock=false playwright-core @sparticuz/chromium
# with the local server running:
node scripts/browser_test.cjs
```

The test unpacks its Chromium libraries into the temporary directory. Large dependencies and screenshots are ignored; they are not deployed.

## Publishing

GitHub Pages uses the repository's existing native **`main` root** build. Root `index.html` is a category hub generated by `ladder/build.py`, not a redirect. Start with the executive briefing and read the hub's Flagged for Review notes before interpreting costs. Detailed sites remain separate evidence views; archived claims are not silently endorsed.

To change the landing page, edit `write_root_hub()` in `ladder/build.py`, then run `PYTHONDONTWRITEBYTECODE=1 python ladder/build.py` and `python ladder/verify.py`. Do not hand-edit generated HTML. CI requires deterministic output. Run `python briefing/verify.py` and `PYTHONDONTWRITEBYTECODE=1 python audit-ad300459/verify.py` for the briefing and latest audit. Full workflow commands are in `.github/workflows/`.

Multiple parallel Arena sessions contribute to this repository; see [COORDINATION.md](COORDINATION.md) for the task board and publication record. [Latest official-source audit](audit-ad300459/index.html). [Landing-page review notes](index.html#integration-review).

Every research table row links to an official source. CI checks citation coverage and local links; external source availability is not continuously checked. See the source ledger for what was actually read and the Flagged for Review page for discrepancies and unconfirmed values.

**Privacy:** This repository and Pages site are public. Never add passports, account numbers, bank statements, tax IDs, signed authorizations or private tax records.
