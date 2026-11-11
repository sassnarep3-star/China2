# China money — delivery audit

Audit date: 11 November 2026. Session: `arena/9e90af86-china2`.

## Live deliverables

- [Dashboard](https://sassnarep3-star.github.io/China2/)
- [Executive summary](https://sassnarep3-star.github.io/China2/playbook-c1d73006/summary.html)
- [Questions and missing information](https://sassnarep3-star.github.io/China2/playbook-c1d73006/questions.html)
- [Methods, pros/cons and workflows](https://sassnarep3-star.github.io/China2/playbook-c1d73006/methods.html)
- [Costs: every USD 10,000 step through USD 400,000](https://sassnarep3-star.github.io/China2/playbook-c1d73006/costs.html)
- [Conversion penalty breakdown](https://sassnarep3-star.github.io/China2/playbook-c1d73006/penalty.html)
- [Flagged for Review](https://sassnarep3-star.github.io/China2/playbook-c1d73006/flagged.html)
- [Repository irregularities](https://sassnarep3-star.github.io/China2/playbook-c1d73006/review.html)
- [Official source ledger and exact passages](https://sassnarep3-star.github.io/China2/playbook-c1d73006/sources.html)

These are existing integrated deliverables, not new research authored by this audit session. The root page links the playbook. Adding another competing dashboard would increase duplication and is not needed.

## Executive decision boundary

The first route to investigate for lawful current-account RMB income of an overseas individual is an authorized bank conversion using valid identity and source-of-funds documents including tax vouchers. This is conditional, not confirmation that this account qualifies. SAFE's employment-income answer was independently retrieved in this session: [SAFE Tianjin, 13 July 2026](https://www.safe.gov.cn/tianjin/2026/0713/3088.html). Its operative words are “凭本人有效身份证件和有交易额的购汇资金来源材料（含税务凭证）在银行办理购汇”.

No personal tax bill or cheapest executable route can be determined from the brief. The actual source of the balance, identity classification, tax already paid, bank's written explanation and current quotes are missing. Do not treat an absence of a conversion tax in reviewed texts as proof that no tax can arise: underlying income and currency gains are separate questions. The existing summary's suggestion that unpaid tax is the most likely explanation is a hypothesis, not a verified personal fact.

The [IRS foreign tax credit page](https://www.irs.gov/individuals/international-taxpayers/foreign-tax-credit), independently retrieved in this session, says a credit or deduction **may** be available for qualifying foreign taxes. It also says no credit may be claimed on excluded income and a treaty-reduced tax may limit the qualifying amount. A credit is not an automatic full refund of Chinese tax.

The [IRS FBAR page](https://www.irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar), independently retrieved in this session through its penalties and delinquent-filing sections, uses **aggregate foreign accounts exceeding USD 10,000 at any time during the calendar year**. It does not use the size of a transfer as the trigger. Its penalty section states that maxima adjust annually; a static historical dollar amount must not be taken as a guaranteed current penalty or as an assessment against this user.

## Checks actually performed

- `python3 playbook-c1d73006/verify.py`: **24,050 checks, zero failures**, covering stored evidence structure, 1,259 table rows with publisher links, blank flags, local links, and independent arithmetic on the stored inputs.
- `python3 playbook-c1d73006/model.py` and `python3 playbook-c1d73006/build.py`: rebuilt 680 cost rows (17 methods × 40 amounts) and generated pages. `git diff --exit-code -- playbook-c1d73006` passed: byte-for-byte reproducible.
- `node --check playbook-c1d73006/assets/app.js`: passed.
- `python3 scripts/validate.py`: passed for nine older dashboard pages, 67 findings, 24 sources, official-link presence, local paths/anchors and download parity.
- `node scripts/test_ui.js`: passed search, filter, empty-state, print-action and overview harness checks. This is not a fresh real-browser mobile test.
- GitHub Pages API initially reported `built`, serving `main` root, with commit `1146dd2b1e41a46ba73b39db0cfb76747d26fa09`, no build error. Publication of this audit is recorded in COORDINATION.md after merge.

## Limits and irregularities retained for review

The script results do **not** independently prove the truth or current applicability of every statement. Only the three official pages named above were freshly retrieved during this audit. Other source passages remain prior sessions' evidence, not a new line-by-line external verification by this session.

The existing 40-tier bank estimates are reproducible illustrations using recorded board rates and tariffs, not bank quotes. Their spread component uses each bank's own bid/ask midpoint: that is a model benchmark, not an independently verified executable interbank rate. Unknown intermediary/receiving charges and personal taxes are not zero. Provider methods with unpublished inputs remain unpriced; it would violate the evidence requirement to manufacture estimates for them.

The existing Flagged for Review and repository review pages retain conflicting quota definitions, old tariff dates, outdated emigrant-staging language in older sections, historic annual-average FX conversions used for fees, and inconsistent tax-credit wording. Older sections are not silently certified by this audit. Formal legal conclusions, personal eligibility, historical filing compliance and a full all-in executable comparison remain unresolved.

No bank account was accessed, transfer initiated, tax return filed or private document inferred. Research and publication can be completed without user input; account-specific execution cannot.
