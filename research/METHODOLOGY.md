# Research and verification record

Reviewed 2026-11-07 UTC by session `arena-996dc508`.

## Scope and starting repository

The repository at baseline commit `d9f397649f6601d0907184e7f16c9e03e5ca6d74` contained only `README.md` with `# China2`. There were no existing research claims, data rows, navigation or application code to audit. No other coordination claims existed. This session performed research, implementation and final integration sequentially on the Arena-fixed branch.

This study concerns lawful mainland China CNY funds held by a U.S. citizen, not a conclusion about a specific account. Citizenship is user-provided, not independently verified. The amount, source, owner, bank, residence history and alleged tax demand were not supplied. No private facts are invented. No financial transaction, client authorization, tax filing, professional engagement or account-access action was performed.

## Evidence and line-level review

- `sources.json` records 24 official primary sources: government/regulator material and banks/providers describing their own services. Product evidence is not government approval or a guarantee of service.
- `findings.json` contains 67 individually identified rows. Each has official-source IDs and a section/article locator, plus an explicit status. The site renders these IDs directly as official links.
- The full row text, its numerical field, pros/cons and limitations were compared against the passages retrieved with the research `fetch_page` tool. Chinese passages were read in Chinese and summarized in English. Translations are not certified.
- Source-backed status means the stated rule/category was found in the cited source. It is not a personal eligibility determination. Pros/cons, recommended workflow and comparison formulas are analysis, labeled accordingly in the UI.
- Unknown numerical values are the empty string in the canonical JSON and empty cells in the published tables/CSV. Blank does not mean zero. Conditional statutory or historical-edition figures are explicitly qualified; no current live FX rate or personalized cost/tax result is supplied.
- All six overview decision-table rows also link directly to official context. Every source-ledger row links to its own official document.
- Search results were discovery only. Search blogs, aggregators, marketing quote examples, inferred provider availability and third-party tax rates were not used as final evidence.
- Official HTML was read through the relevant body sections; PDFs were read through the sections listed in each source's limitation/locator. No assertion that an entire long PDF, all government law or every conceivable transfer product was exhaustively audited is made.

## Specific irregularities and exclusions

1. **F02 / quota wording:** HSBC's non-mainland individual guide describes settlement and purchase as subject to a USD50,000 facilitation quota. SAFE Art.2 distinguishes individual settlement from domestic-individual purchase, and its 2026 FAQ restates the documented lawful-income route for overseas individuals. The differing wording is published rather than silently reconciled. No ID-only USD50,000 purchase entitlement is promised to this user.
2. **F07 / repealed Chinese fine provision:** SAFE Tianjin's amended republication still displays Article 39 but explicitly repeals it in its amendment note. The obsolete fine numbers are not used.
3. **F07 / crypto source currency:** PBOC Yinfa [2026] 42 expressly repeals Yinfa [2021] 237. The current 2026 notice, not the repealed notice, is the source for the warning. No claim that mere possession is automatically criminal is made.
4. **F04 / inflation-adjusted FBAR penalties:** No current maximum was verified. The IRS comparison table's old numbers are deliberately not presented as current.
5. **F06 / currency statute:** The GPO 2024 edition of 26 USC 988 was retrieved, including subsections (a), (c)(1)(C) and (e). Later amendment status and individualized application are not independently established. The narrow USD200 personal-disposition language is edition-qualified and flagged, not treated as a universal annual exemption.
6. **F06 / treaty:** The IRS treaty index was checked; the actual treaty provisions were not applied. No reduced dividend, capital gain or other treaty rate, savings-clause exception, or state/third-country conclusion is invented.
7. **F03 / fees:** The HSBC tariff effective 2026-10-31 was read at Important Notes and the Premier column of item 2.2.4.1. That limited issuance example is not an all-in bank price. Cable, spread, correspondent and receiver costs remain unquoted. No extrapolation from corporate, Macau, Hong Kong or Australian tariffs is used.
8. **F03 / provider:** Wise's FROM-CNY help requirements were used rather than the unrelated inbound-to-China product limits. Its bank-app and Alipay funding options are not separate overall allowances. No account-specific fee or acceptance was verified.
9. **F09 / no-input boundary:** Research and publishing require no questionnaire. Actual bank execution necessarily requires private documentation and authorization; the study cannot remove that requirement.

## Retrieval failures handled without false verification

Some guessed/older IRS URLs for FBAR, the Form 8938 comparison, foreign gifts and delinquent FBAR procedures returned explicit 404 page bodies. Successful official replacements were retrieved for FBAR, Form 8938 and foreign gifts and are the only URLs included in the evidence ledger. A delinquent-FBAR penalty-waiver claim was not included; no successful substantive source body was obtained for that separate procedure.

The NPC English law page returned HTTP 500. The current 2018-amended individual income-tax text was instead retrieved from Guangzhou Finance Bureau's official government republication, including the schedules and amendment history. An attempted current US Code viewer link returned a not-found body; the accessible GPO 2024 edition was used with its edition limitation published.

External pages may subsequently move or change. A successful research retrieval on the review date is not a continuous availability guarantee. Shell outbound networking is allowlisted; official material was retrieved using the research tools. No artificial HTTP-success labels or universal link-health assertions are generated.

## Build and tests

- Deterministic Python standard-library generator; no runtime framework, CDN, tracking, cookies or personal-data inputs.
- `python scripts/build.py`: renders seven fully static HTML pages and matching JSON/CSV/Markdown downloads.
- `python scripts/validate.py`: checks canonical data, source domains, unique IDs, per-row citations, blank fields for Unverified rows, generated-download parity, all local paths/anchors and expected row/page counts.
- `node scripts/test_ui.js`: dependency-free harness tests filtering, case handling, status selection, no-results messages, ledger behavior, print and overview safety.
- `node scripts/browser_test.cjs`: optional real Chromium checks seven pages at 1440px and 390px widths, actual row counts, search/status/no-results interactions, JavaScript errors and document-level overflow. Test-only dependencies and screenshots remain in ignored `.cache/`.
- Desktop screenshot inspected visually. Mobile rendering tested for page-level overflow; wide research tables intentionally scroll within their labeled containers rather than collapsing evidence columns.

These technical tests do not replace qualified Chinese/U.S. legal or tax review. Open substantive limitations are intentionally published on `docs/review.html` and do not block release.
