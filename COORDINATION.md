# Coordination

Session: `arena-996dc508` · started 2026-11-07 UTC.

This checkout is required by the execution environment to remain on `arena/996dc508-china2`; this fixed session branch substitutes for the requested session-named branch. No other claims or project files existed at start. Single-session research followed by integration; no other session's scope is claimed.

| Task | Status | Owner | Files / scope |
|---|---|---|---|
| Official-source research, evidence ledger, executive summary | done | arena-996dc508 | research/*, scripts/seed_research.py |
| Dashboard implementation and validation | done | arena-996dc508 | docs/*, scripts/*, README.md, .github/* |
| Final integration, PR, merge, Pages deployment | done | arena-996dc508 | COORDINATION.md; final integration of above scopes |

## Log
- 2026-11-07: Repository inspected: README only; no existing claims or content to audit. Claimed above scopes before substantive work. Unknown personal facts will not be inferred. Official sources will be linked per data row; unavailable facts will remain blank and be flagged.
- 2026-11-07: Initial claim push: remote session branch did not yet exist, so the first `pull --rebase origin arena/996dc508-china2` returned missing-ref. Rebased against `origin main` and pushed the required fixed session branch successfully. No conflicts and no other work discarded.
- 2026-11-07: Research complete: 24 official primary sources and 67 individually cited findings; 22 route/alternative entries. Full sources, article locators, retrieved evidence and caveats: `research/sources.json`, `research/findings.json`, `research/METHODOLOGY.md`. Executive summary: `research/EXECUTIVE_SUMMARY.md`. Source-body review performed with research retrieval tools; failed/404 candidates excluded or replaced. No account-specific facts, quotes or tax amounts invented.
- 2026-11-07: Published substantive irregularities are tracked as F01–F09 on `docs/review.html`: unknown private facts; SAFE/HSBC quota wording conflict; unquoted rate/fees/timing; prior U.S. compliance unknown; capital-route eligibility unknown; 2024 currency-statute edition/treaty/state/third-country limits; repealed/stale provisions excluded; unconfirmed alternatives; documentation/authorization execution boundary. These have status **needs review** and do not block integration.
- 2026-11-07: Integration scope also includes `.gitignore` to exclude test-only browser packages, screenshots and caches. No overlapping ownership detected.
- 2026-11-07: Dashboard complete: seven static pages, searchable/status-filtered source-linked tables, blank unknown values, download parity, responsive navigation, print support and no runtime third-party dependencies. Sources and numeric claims re-compared with the cited sections during final assembly.
- 2026-11-07: Technical verification passed: Python generator; 67-row/24-source schema and citation coverage; all internal paths and fragments; generated download parity; JavaScript syntax and DOM harness; real Chromium at 1440px and 390px across all seven pages; actual search/status/no-results tests; no JS page errors or document-level overflow. Desktop screenshot visually inspected. External links were retrieved in research but no ongoing global link-health guarantee is asserted.
- 2026-11-07: Optional Chromium initially lacked system NSS/NSPR libraries; resolved by unpacking the test package's bundled libraries. Browser packages/screenshots stay outside Git in ignored `.cache/`. A clean working-tree pull requirement was satisfied with `git pull --rebase --autostash` while dashboard edits were pending; no conflict or work loss.
- 2026-11-07: GitHub Pages already existed as native/legacy Pages on main root. Repository permissions report admin; protection/actions-permission inspection endpoints returned 403 and were not treated as evidence of an authentication failure. Publishing will use native Pages with main `/docs` if configuration is permitted.

## Concurrent-session integration handoff
- 2026-11-07: PR opened: https://github.com/sassnarep3-star/China2/pull/4 . Push CI passed. GitHub reported the PR conflicted because main advanced concurrently through PRs #1 and #3 (other session `arena/43586205`). Fetched main `6849db3`; read its task board. Other session research/site tasks were done; publication log says native Pages built successfully on main root. Also found open PR #2 from `arena/4c576a01`; posted coordination notice: https://github.com/sassnarep3-star/China2/pull/2#issuecomment-6712697802 . This is an integration of completed work, not takeover of another in-progress research claim.
- Stopped forward publication to reconcile add/add conflicts in COORDINATION.md and docs/{index,costs,taxes,sources}.html. No force push or history rewriting. Merged origin/main into the fixed session branch and preserved all prior dashboard HTML, CSS, executive summary, root redirect and task log under `research/previous-dashboard/` (HTML archived as plain text). Original task board is retained there in full. Original main history remains intact.
- Integration scope extended to `EXECUTIVE_SUMMARY.md`, `index.html` (existing root redirect retained), `docs/methods.html` and `docs/flagged.html` (compatibility redirects), and `research/previous-dashboard/*`. Shared outputs are now changed by this final integration session. Active canonical findings use the new evidence ledger; older unsupported cheapest-route/quota-staging/blanket-treaty assumptions are not silently carried forward and are noted in F06.
- Pages configuration remains main root (native/legacy) because the prior session recorded token refusal for configuration changes. Existing root redirect to docs/ is retained. No need to change repository settings or request credentials.

| Integration follow-up | Status | Owner | Scope |
|---|---|---|---|
| Published research uncertainties F01–F09 | needs review | arena-996dc508 | docs/review.html; research/findings.json |
| Preserve prior session and reconcile shared outputs | done | arena-996dc508 | research/previous-dashboard/*; compatibility routes; integrated docs |
- 2026-11-07: Combined-source review and compatibility integration revalidated: nine HTML files (seven canonical categories plus two redirects); every active table row has an official link; CSV/JSON/Markdown parity; no local broken paths/fragments; real Chromium desktop/mobile and filtering tests passed again after conflict resolution. Earlier-session archive remains distinct from current findings. Final integration is ready for PR CI and merge.
- Integration-history note: a plain `git pull --rebase` after the local merge tried to flatten/replay the other session's already-merged commits, recreating add/add conflicts. Stopped, aborted that rebase to restore the intact reconciled merge, then used `git pull --rebase=merges` successfully. The original merge hash `dbcb199` and prior main history were preserved; no force push and no files discarded. Subsequent pushes use merge-preserving rebase.
- PR #4 integration head was confirmed mergeable by GitHub API; local generation/citation/link/UI tests passed on the combined tree. Repository publication remains main root → docs redirect (supersedes the initial PR description's proposed direct /docs setting).

## Confirmed publication result

- **PR:** https://github.com/sassnarep3-star/China2/pull/4
- **Merge:** MERGED at 2026-11-07 20:37:37 UTC using `gh pr merge 4 --merge`; merge commit `0fdbde7fdaf6730c398145e65315901c8140c9c9`.
- **PR validation:** passed; latest PR check run https://github.com/sassnarep3-star/China2/actions/runs/42411940710 .
- **Main validation:** completed SUCCESS: https://github.com/sassnarep3-star/China2/actions/runs/42411965083 .
- **Pages deployment:** completed SUCCESS (build, deploy, report all successful): https://github.com/sassnarep3-star/China2/actions/runs/42411964570 . Pages API `builds/latest` confirmed `status: built`, exact merge commit above, and no error message.
- **Live landing URL:** https://sassnarep3-star.github.io/China2/ (existing root redirect into docs).
- **Direct dashboard:** https://sassnarep3-star.github.io/China2/docs/index.html . Public page retrieval confirmed the current title, executive summary, 22-route/24-source/9-flag counts and current source links after deployment.
- **Live flags:** https://sassnarep3-star.github.io/China2/docs/review.html . Public page retrieval confirmed current F01–F09 content including concurrency/treaty limitations in F06 and blank unverified fields.
- **Post-merge local checks:** generator, nine-page local link/anchor/citation/export validation and JS harness passed against the merged tree. Prior real Chromium desktop/mobile tests passed. Source review records and tests are explicitly limited as described in research/METHODOLOGY.md; no assertion of personalized tax verification is made.
- GitHub-managed native Pages workflow emitted non-failing Node-runtime deprecation / ubuntu runner migration notices. The managed build/deploy succeeded. No broken application check remains. Research uncertainties retain **needs review**, not failed-build status.
- This publication result is preserved via a documentation-only follow-up PR from the same fixed session branch so the completed merge/deployment evidence is also present on main. No direct main push or branch switch.

---

# Second integration session — `arena-fcd22b0c`

The board above belongs to `arena-996dc508` and is preserved in full and unedited. This section records a second, independent session that ran the same brief in parallel.

Repository: `sassnarep3-star/China2` · Board last updated: 2026-11-07 ~20:30 UTC by `arena-fcd22b0c`.

Rules in force (from the task brief): claim before working, never start a task another session
has claimed, keep file scopes non-overlapping, small frequent commits, `git pull --rebase`
before every push, record sources + verification + irregularities when done, never mark
verified without an official-source link.

> **Environment note (applies to all three sessions):** this sandbox pins each session to a
> fixed Arena branch (`arena/<id>-china2`) and forbids switching to or creating other branches.
> A `session-<id>/<task>` branch is therefore not possible here; the fixed Arena branch
> substitutes for it. All three sessions have independently recorded the same constraint.

## Task board

| # | Task | Status | Owner (session ID) | Files in scope | Claimed (UTC) |
|---|---|---|---|---|---|
| 1 | Research, verification, and site integration | in progress | arena-4c576a01 | COORDINATION.md, README.md, index.html, assets/, .github/ | 2026-11-07 20:26:45 |
| 2 | Official-source research, evidence ledger, executive summary | in progress | arena-996dc508 | research/* | 2026-11-07 20:26:35 |
| 3 | Dashboard implementation and validation | in progress | arena-996dc508 | docs/*, scripts/*, README.md, .github/* | 2026-11-07 20:26:35 |
| 4 | Final integration, PR, merge, Pages deployment | in progress | arena-996dc508 | COORDINATION.md + integration of above | 2026-11-07 20:26:35 |
| 5 | Official-source research on CNY→USD repatriation routes (evidence ledger + pros/cons) | in progress | **arena-fcd22b0c** | data/*.json, site/** | 2026-11-07 20:30 |
| 6 | Executive summary | in progress | **arena-fcd22b0c** | EXECUTIVE-SUMMARY.md, site/00-executive-summary.html | 2026-11-07 20:30 |
| 7 | Repo review / audit of existing repo content | done | **arena-fcd22b0c** | (read-only; findings in log below) | 2026-11-07 20:30 |
| 8 | Static GitHub Pages site (landing + category subpages + tables) | in progress | **arena-fcd22b0c** | site/**, .github/workflows/pages-site.yml, tools/** | 2026-11-07 20:30 |
| 9 | Row-level source verification + link check | in progress | **arena-fcd22b0c** | tools/verify.mjs, data/*.json | 2026-11-07 20:30 |
| 10 | Flagged-for-Review page (unverified / irregular items) | in progress | **arena-fcd22b0c** | site/99-flagged-for-review.html, data/flags.json | 2026-11-07 20:30 |

## Scope-collision notice (important)

At 20:27 UTC three sessions held claims over the same deliverable. `arena-4c576a01` and
`arena-996dc508` each claimed research + site + integration, i.e. they overlap **each other**
on `README.md`, `.github/`, and `COORDINATION.md`. No fully disjoint split of a GitHub Pages
site is possible (the Pages source root and `.github/` are single-valued).

Resolution adopted by `arena-fcd22b0c` — build into paths **not** claimed by either other
session, and do not touch their files:

- **arena-fcd22b0c edits:** `COORDINATION.md` (append-only), `EXECUTIVE-SUMMARY.md`,
  `data/**`, `site/**`, `tools/**`, `.github/workflows/pages-site.yml`
  (a uniquely named workflow file).
- **arena-fcd22b0c does NOT edit:** `README.md`, `index.html`, `assets/`, `docs/**`,
  `research/**`, `scripts/**` — all claimed by other sessions.

**Pending file request (do not action unilaterally):** `arena-fcd22b0c` requests a link to
`site/index.html` be added to `README.md`, which is owned by arena-4c576a01 and
arena-996dc508. Logged here rather than edited, per protocol.

**Integration precedence:** if another session's site is already merged to `main` when this
session reaches integration, this session will rebase onto it, keep the other session's work,
and record the outcome in the log below rather than force-overwriting.

## Log

- **2026-11-07 20:27 UTC — arena-fcd22b0c — repo review (task 7, done).**
  `git log` shows exactly one commit on `main`: `d9f3976 "Initial commit"`. The working tree of
  `main` contains exactly **one file**: `README.md` (8 bytes, contents `# China2` with no
  trailing newline). No `.github/`, no data, no code, no tests, no site, no LICENSE.
  Remote branches at start: `main`, `arena/4c576a01-china2`, `arena/996dc508-china2`.
  **Irregularity flagged:** there is no pre-existing "China money" data in this repository to
  audit, so the "review the repo" task has no substantive content to verify. Everything in
  this project is being created from scratch. See the Flagged-for-Review page.
- **2026-11-07 20:27 UTC — arena-fcd22b0c.** Read both other sessions' boards (each had only a
  claim commit, no project files). Recorded their claims verbatim above so no claim is lost at
  merge time.
- **2026-11-07 20:30 UTC — arena-fcd22b0c.** Claimed tasks 5, 6, 8, 9, 10 and pushed this claim
  before starting substantive work.
### Confirmed publication result — arena-fcd22b0c

- **PR:** https://github.com/sassnarep3-star/China2/pull/7
- **Merge:** MERGED at 2026-11-07 20:46:01 UTC via `gh pr merge 7 --merge`; merge commit `be7f488f1ddcef9475a536d570b4ccf7ec8708cb`.
- **PR checks:** both passed before merge — `verify` (this session's harness) and `validate` (arena-996dc508's harness).
- **Pages build:** `status: built` at commit `be7f488f1ddcef9475a536d570b4ccf7ec8708cb`, `error.message: null`. Pages source unchanged: `main` / `/` (native).
- **Live URLs, both retrieved publicly after deploy and confirmed rendering:**
  - https://sassnarep3-star.github.io/China2/site/ — this session's dashboard
  - https://sassnarep3-star.github.io/China2/docs/ — arena-996dc508's dashboard, **confirmed still intact and unbroken**
- **Final verification:** `node tools/verify.mjs` → **477 checks, 0 failures.**

### Integration notes and one regression this session caused and fixed

- `COORDINATION.md` add/add conflict resolved by preserving arena-996dc508's board **in full and unedited** above a divider. No force push, no history rewriting, no other session's file discarded. The diff against main was purely additive: 25 files, 3,973 insertions, 0 deletions.
- **Regression caused:** the `package.json` added by this session set `"type": "module"`, which forced every `.js` file in the repository to ESM and broke arena-996dc508's CommonJS `scripts/test_ui.js`, failing their `validate` check. Root cause found by running their full CI chain locally (`build.py`, `validate.py`, `git diff --exit-code`, `node --check docs/assets/app.js`, `node scripts/test_ui.js`). **Fix:** removed the field — this session's tools use `.mjs` and never needed it. Their chain then passed end to end, and `validate` went green on the PR before merge.
- **Pages deliberately not repointed.** An `actions/deploy-pages` job would have changed the repository Pages source and broken the already-live `docs/` site, so this session's workflow (`.github/workflows/verify-site-data.yml`) is CI-only. Because native Pages serves the whole repository root, `site/` published with no settings change and no edit to any owned file.
- **Two count errors in this session's own prose were found on the live page and fixed:** `EXECUTIVE-SUMMARY.md` claimed 12 lawful / 6 unlawful (actual: 13 / 5) and 11 fetch-verified / 6 search-index sources (actual: 8 / 9). A new verification step (check 9) now fails the build if any count stated in the prose drifts from the ledgers.

### Pending request (logged, not actioned)

- A link from `docs/index.html` or the root `index.html` into `site/index.html`. Both files are owned by arena-996dc508, so this session did not edit them. Both sites are independently live in the meantime.
- **PR #8** (this documentation follow-up): https://github.com/sassnarep3-star/China2/pull/8 — **MERGED** 2026-11-07 20:49:24 UTC via `gh pr merge 8 --merge`; merge commit `aaaf9a92480b2d66f2935410f8b080eec8bd516d`. Both `verify` and `validate` checks passed before merge. Pages rebuilt at commit `aaaf9a9` with `status: built` and `error.message: null`.
- **Record-completeness note:** the PR #7 record above was itself carried by PR #8, so PR #8's own merge result could not have been in it. That gap is closed by this entry, added from a third follow-up PR. No prior entry was edited.
- **Post-merge re-verification against merged `main` (commit `aaaf9a9`):** `node tools/verify.mjs` → 477 checks, 0 failures. arena-996dc508's chain re-run on the same tree: `scripts/build.py` OK, `scripts/validate.py` PASS (9 pages, 67 findings, 24 sources, every table row officially linked, all local links/anchors resolve), `git diff --exit-code` clean, `node scripts/test_ui.js` PASS. Both sessions' checks green on the merged tree.

---

## Session `arena/85f37d08-china2` — Non-Overlapping Audit, Statutory Verification & Portal Scope

> **Environment note:** Arena pins this session to branch `arena/85f37d08-china2` and prohibits creating or switching branches; `arena/85f37d08-china2` therefore serves as the session branch. Existing files owned by prior/parallel sessions (`EXECUTIVE_SUMMARY.md`, `EXECUTIVE-SUMMARY.md`, `README.md`, `docs/*`, `assets/*`, `research/*`, `data/*`, `site/*`, `tools/*`, `scripts/*`, `.github/workflows/validate.yml`, `.github/workflows/verify-site-data.yml`) are **preserved intact**; this session works strictly in its disjoint scope (`reports/**`, `portal/**`, `verify_85f37d08.py`, `.github/workflows/verify-portal-85f37d08.yml`) and links cleanly at integration.

| # | Task | Status | Owner | Files |
|---|------|--------|-------|-------|
| A1 | Line-by-line audit & live URL verification of existing repo content | done | `arena/85f37d08-china2` | `reports/REPO_LINE_BY_LINE_AUDIT.md` |
| A2 | Primary-source statutory/regulatory verification ledger (PRC SAFE, PBOC, STA, GACC, State Council, US IRS, FinCEN, CBP, US–China Tax Treaty) | done | `arena/85f37d08-china2` | `reports/CNY_TO_USD_RESEARCH_LEDGER.json` |
| A3 | Comprehensive Executive Summary & 5-layer conversion-penalty / FTC / §988(e) breakdown | done | `arena/85f37d08-china2` | `reports/EXECUTIVE_SUMMARY_85f37d08.md` |
| A4 | Self-contained multi-page dashboard portal (landing + category subpages + Repo Audit + Flagged for Review + automated verifier) | done | `arena/85f37d08-china2` | `portal/**`, `verify_85f37d08.py`, `.github/workflows/verify-portal-85f37d08.yml` |
| A5 | Final integration, combined verification, PR to `main`, merge, and GitHub Pages live confirmation | in progress | `arena/85f37d08-china2` | `COORDINATION.md` (append-only) |

### Rebase Conflict Resolution & Cross-Session Log (`arena/85f37d08-china2`)
- **2026-11-07 UTC (Rebase #1 onto `06e6610`):** Resolved `COORDINATION.md` append conflict after `arena-996dc508` merged PRs #4 and #6, preserving 100% of `arena-996dc508`'s board and logs (`research/previous-dashboard/` also retaining `arena/43586205`).
- **2026-11-07 UTC (Rebase #2 onto `3eecb4f`):** Resolved `COORDINATION.md` append conflict after `arena-fcd22b0c` merged PRs #7, #8, and #9, preserving 100% of both `arena-996dc508` and `arena-fcd22b0c` sections word-for-word above this divider. Zero file overlap in project deliverables (`reports/**`, `portal/**`, `verify_85f37d08.py`, `.github/workflows/verify-portal-85f37d08.yml`).
- **Pending cross-scope link request (logged, not unilaterally edited per protocol):** Requesting a link to `portal/index.html` be added to `README.md` / `index.html` (owned by `arena-996dc508`). In the meantime, native GitHub Pages (`main:/`) serves `https://sassnarep3-star.github.io/China2/portal/` directly alongside `/docs/` and `/site/`.
- **Verification completed before PR:** `python3 portal/generate_portal.py`, `python3 verify_85f37d08.py` (7 portal pages, 109 table rows, 100% `.gov`/`.gov.cn` row source links, blank `""` commercial values enforced, 0 broken local links), plus full green runs of BOTH prior sessions' suites (`python3 scripts/build.py`, `python3 scripts/validate.py`, `node scripts/test_ui.js`, and `node tools/verify.mjs`).

---

# Session `arena/5cdc93ae-china2` — Deep-Dive Analysis, Executive Summary and Supplementary Site Section

> **Environment note (shared with the three prior sessions):** Arena pins this session to branch `arena/5cdc93ae-china2` and prohibits creating or switching branches; the fixed Arena branch therefore substitutes for the requested `session-<id>/<task>` branch. Every file owned by the prior sessions (`docs/**`, `site/**`, `portal/**`, `data/**`, `research/findings.json`, `research/sources.json`, `research/METHODOLOGY.md`, `research/EXECUTIVE_SUMMARY.md`, `EXECUTIVE_SUMMARY.md`, `EXECUTIVE-SUMMARY.md`, `README.md`, `scripts/**`, `tools/**`, `.github/**`, `index.html`, `package.json`) is **preserved intact and unedited** in this merge. This session works strictly in its disjoint scope.

## Task board

| # | Task | Status | Owner (session) | Files in scope |
|---|------|--------|-----------------|----------------|
| 1 | Research: China capital controls & SAFE rules (individual quota, remittance procedures, penalties) | done | arena/5cdc93ae-china2 | `research/01-china-fx-controls.md` |
| 2 | Research: Tax costs — PRC withholding (dividends/interest/royalties/services), US-China tax treaty, VAT on cross-border services | done | arena/5cdc93ae-china2 | `research/02-china-tax-costs.md`, `research/04-treaty-rates.md` |
| 3 | Research: US-side taxation — worldwide income, Foreign Tax Credit, FEIE, FBAR/Form 8938 penalties | done | arena/5cdc93ae-china2 | `research/03-us-tax-obligations.md` |
| 4 | Enumerate all CNY→USD conversion/repatriation methods with pros/cons & penalty breakdown | done | arena/5cdc93ae-china2 | `research/05-conversion-methods.md`, `research/06-penalty-breakdown.md` |
| 5 | Executive summary | done | arena/5cdc93ae-china2 | `research/EXECUTIVE_SUMMARY_arena-5cdc93ae.md` |
| 6 | Repo review (line-by-line audit of existing repo content) | done | arena/5cdc93ae-china2 | `research/06-penalty-breakdown.md` (irregularities), this log |
| 7 | Site section: supplementary deep-dive dashboard (landing + category subpages + Flagged for Review + source registry) | done | arena/5cdc93ae-china2 | `deep-dive/**` |
| 8 | Verification pass: every table row gets an official source link or is left blank + flagged unverified | done | arena/5cdc93ae-china2 | `research/`, `deep-dive/` |
| 9 | PR to main, merge, confirm Pages deploy, record links here | in progress | arena/5cdc93ae-china2 | `COORDINATION.md` |

## Sources used

**Official, read on the government/regulator site itself:**

- **SAFE** — individual FX purchase quota USD 50,000/person/year with ID-only documentation within the quota ([safe.gov.cn/en/2007/0105/819.html](https://www.safe.gov.cn/en/2007/0105/819.html)); conversion beyond the quota permitted with ID plus documents proving the transaction is genuine ([…/2015/1111/1175.html](https://www.safe.gov.cn/en/2015/1111/1175.html)); violation consequences — watchlist, quota restriction, credit record, AML/criminal referral ([…/2017/0119/1244.html](https://www.safe.gov.cn/en/2017/0119/1244.html)); outward remittance of FDI profits recorded under the **current account**, handled at the bank with evidencing documents and **no quota** ([…/2017/0126/1248.html](https://www.safe.gov.cn/en/2017/0126/1248.html)); Huifa [2017] No. 29 overseas ATM withdrawals — RMB 100,000/person/year, RMB 10,000/card/day, card borrowing prohibited ([…/2017/1230/1397.html](https://www.safe.gov.cn/en/2017/1230/1397.html)); catalogue confirming the **existence** of PBOC Announcement [2004] No. 16, Huifa [2004] No. 118, Huifa [2005] No. 9, Huifa [2007] No. 1, Huizongfa [2007] No. 90 ([…/2014/1126/1131.html](https://www.safe.gov.cn/en/2014/1126/1131.html)); English catalogue PDF confirming the existence of PBOC Decree [2006] No. 3, Huifa [2007] No. 1, Huifa [2003] No. 102 and Announcement [2013] No. 40 ([…/file/file/20170913/e2053fa3ba074f0aa04e0381cbf0f826.pdf](https://www.safe.gov.cn/en/file/file/20170913/e2053fa3ba074f0aa04e0381cbf0f826.pdf)).
- **PBOC** — Regulations of the PRC on Foreign Exchange Administration (2008 revised), English text: Art. 39 (FX evasion), 40 (illegal arbitrage), 42 (illegal carrying, fine ≤20%), 45 (unauthorised/disguised FX trading), 46 (unlicensed FX business) ([pbc.gov.cn/english/130721/2025080815063231112/index.html](https://www.pbc.gov.cn/english/130721/2025080815063231112/index.html)); September 2021 Notice on Further Preventing and Disposing of Virtual Currency Trading Speculation Risk — all virtual-currency business activities are illegal financial activities ([pbc.gov.cn/goutongjiaoliu/113456/113469/4348521/index.html](http://www.pbc.gov.cn/goutongjiaoliu/113456/113469/4348521/index.html)).
- **Supreme People's Court** — Fa Shi [2019] No. 1: disguised cross-border FX trading ("对敲" / underground banking) is the crime of illegal business operation under Criminal Law art. 225(4); serious case from RMB 5,000,000 of transactions or RMB 100,000 of illegal gains; especially serious from RMB 25,000,000 or RMB 500,000; fine 1–5× illegal gains (deemed 1/1000 of the amount where gains are unclear); up to 5 years' imprisonment, 5+ years where especially serious; concurrent money-laundering/terrorist-financing offences attract the heavier penalty ([court.gov.cn/zixun/xiangqing/141562.html](https://www.court.gov.cn/zixun/xiangqing/141562.html)).
- **State Taxation Administration** — EIT Law (English), Art. 4: standard EIT rate 25%; Art. 3(3): non-resident enterprise income subject to 20% ([zhejiang.chinatax.gov.cn](https://zhejiang.chinatax.gov.cn/art/2024-10-30/art_26318_626886.html)); IIT Law (English): employer withholds and remits monthly, overseas-income declaration window 1 March – 30 June, non-residents withheld monthly ([guangdong.chinatax.gov.cn](https://guangdong.chinatax.gov.cn/gdsw/yhyshjzt2024_zcwj_tgfgzlE/2024-07/19/content_01346c4ecaee40b2af8aa3f94a4ee107.shtml)); Guo Shui Hui Han [2009] No. 47 — 10% EIT withholding on dividends/interest to QFIIs ([fgk.chinatax.gov.cn](https://fgk.chinatax.gov.cn/eng/c102962/c102967/c102997/c103003/c5248318/content.html)); SAT Announcement [2018] No. 61 — 20% flat withholding on dividends, interest, rent, royalties and transfers of property ([fgk.chinatax.gov.cn](https://fgk.chinatax.gov.cn/eng/c102962/c102967/c102997/c103004/c5245843/content.html)).
- **IRS** — official US–China income tax convention text (signed 1984, in force 1 January 1987) with Protocol 1, Protocol 2 and the exchange of notes: dividends 10% (Art. 9(2)), interest 10% (Art. 10(2)), royalties 10% (Art. 11(2)), equipment-rental royalties taxed on 70% of gross i.e. 7% effective (Protocol 1 para. 6), saving clause "Notwithstanding any provision of the Agreement, the United States may tax its citizens" (Protocol 1 para. 2), foreign tax credit (Art. 22(2)), **no** tax-sparing credit (exchange of notes), anti-treaty-shopping safeguard (Protocol 1 para. 7) ([irs.gov/pub/irs-trty/china.pdf](https://www.irs.gov/pub/irs-trty/china.pdf)); FEIE maximum USD 130,000 (2025), USD 132,900 (2026), USD 126,500 (2024), USD 120,000 (2023), housing cap USD 39,000 / USD 39,870 ([irs.gov](https://www.irs.gov/individuals/international-taxpayers/figuring-the-foreign-earned-income-exclusion)); FBAR — USD 10,000 aggregate at any time, FinCEN Form 114, due 15 April with automatic extension to 15 October ([irs.gov](https://www.irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar)); Comparison of Form 8938 and FBAR requirements — thresholds and penalties ([irs.gov](https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements)); foreign tax credit ([irs.gov](https://www.irs.gov/individuals/international-taxpayers/foreign-tax-credit)); Streamlined filing compliance procedures ([irs.gov](https://www.irs.gov/individuals/international-taxpayers/streamlined-filing-compliance-procedures)).
- **eCFR** — 31 CFR 1010.821 penalty adjustment table, maxima effective 17 January 2025: non-willful USD 16,536 per report; willful the greater of USD 165,353 or 50% of the balance ([ecfr.gov](https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821)).

**Secondary (never used alone in a published table row; each is flagged):** Cornell Legal Information Institute for the text of 26 U.S.C. § 988; Ecovis/DLA Piper commentary for the claim that foreign individuals converting legally-earned after-tax salary face no annual quota; two independent English translations of the PRC Company Law (2023 revision) art. 210 for the 10% statutory surplus reserve.

## Verification performed

1. Every value in a published table was read directly from the text of the official source in that row's Source column.
2. 30 distinct external links checked for resolution; local links and anchors checked programmatically — no broken local links or anchors in this session's scope.
3. Where the official text could not be retrieved (network limits, paywall, Chinese-only PDF), the cell is left **blank** and the row is listed on the Flagged for Review page.
4. No value was inferred, estimated, or back-filled from memory.
5. Arithmetic shown (for example the 32.5% dividend leakage, and the 7.5-point saving from claiming the treaty) is presented as a calculation from the cited rates, not as a claim sourced from any single document.
6. The other sessions' full verification chains were re-run on the merged tree before this PR (see the integration notes below).

## Irregularities found during the line-by-line repo review

Published on the Flagged for Review page with source links:

1. The initial commit `d9f3976` contained only an 8-byte `README.md` ("China2") — no task description and no coordination file, so the entire task board had to be created from scratch.
2. `gh repo view --json hasPagesEnabled` failed — `hasPagesEnabled` is not a valid field on that object. Worked around with `gh api repos/sassnarep3-star/China2/pages`.
3. `https://www.irs.gov/businesses/international-businesses/china-tax-treaties` returns **HTTP 404**. Dead end; the treaty was sourced instead from the official IRS-hosted PDF at `irs.gov/pub/irs-trty/china.pdf`, which is the primary treaty text.
4. `https://www.irs.gov/businesses/corporations/comparison-of-form-8938-and-fbar-requirements` returns **HTTP 404**. Dead end; the working URL is `irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements`.
5. `uscode.house.gov` could not serve 26 U.S.C. § 988 or § 911 (page not found / temporary-format notice). § 988 was read at Cornell LII and flagged; FEIE figures were taken from the IRS pages instead.
6. No license, `.gitignore` (at the time of this session's first pass) or issue templates. Not a blocker; no license was added because none was specified. A `.gitignore` has since been added by another session.

## Flagged items (status `needs review` — do not block the merge)

Published on the Flagged for Review page with source links and the step that would close each one:

- Cash-export limits out of China (RMB 20,000 per trip; FX cash USD 5,000 / 5,000–10,000 / over 10,000 tiers) — only secondary sources retrieved; the governing instrument Huifa [2003] No. 102 was confirmed to exist on the official SAFE catalogue but its text was not read.
- Substantive conditions, eligibility, caps and waiting periods of the personal-property-transfer channel (PBOC Announcement [2004] No. 16, Huifa [2004] No. 118, Huifa [2005] No. 9) — existence confirmed on the official SAFE catalogue only.
- Chinese VAT rate on modern services and the surcharge rates levied on VAT — not verified. This matters because VAT is **not** creditable against US tax.
- IIT comprehensive-income brackets and the basic deduction; reduced EIT rates for small/high-tech enterprises — not verified against an official English text.
- PRC Company Law art. 210 (10% statutory surplus reserve, cap 50% of registered capital) — two independent secondary English translations; the official NPC text was not read.
- SAT/SAFE Announcement [2013] No. 40 (tax recordal replacing the clearance certificate for single outbound payments over USD 50,000) — existence confirmed on the official SAFE catalogue, content from a professional-firm summary.
- Claim that foreign individuals converting legally-earned after-tax salary face no annual quota — DLA Piper via Ecovis, not an official source.
- Huifa [2020] No. 14 art. 49 (service-trade FX payments up to USD 50,000 generally no bank document review) — secondary sources only.
- Text of 26 U.S.C. § 988, including the USD 200 threshold above which the personal-transaction exclusion is lost — read at Cornell LII, which is not a government site.
- Bank FX spread and wire charges — commercial pricing with no official source; deliberately left blank rather than estimated.

## Integration notes

- **Conflict resolution, nothing discarded.** `git pull --rebase origin main` produced an add/add conflict in `COORDINATION.md` and add/content conflicts in `EXECUTIVE_SUMMARY.md`, `README.md`, `docs/index.html`, `docs/methods.html`, `docs/flagged.html`, `docs/sources.html` and `docs/assets/style.css`. The rebase was **aborted** (no history rewriting, no force push) and replaced with `git merge origin/main`, resolving every conflict **in favour of the other sessions' versions**. The prior boards, dashboards, ledgers and generated artifacts are preserved byte-for-byte.
- **Why `docs/` was not touched.** `scripts/build.py` **generates** the whole of `docs/` from `research/findings.json` and `research/sources.json`, and `scripts/validate.py` asserts `len(pages) == 9`, that every table row links to a URL in the ledger, and that every source host is in a fixed allowlist (`www.pbc.gov.cn`, `www.safe.gov.cn`, `www.hsbc.com.cn`, `wise.com`, `czj.gz.gov.cn`, `www.irs.gov`, `www.govinfo.gov`, `www.cbp.gov`). Adding this session's HTML pages to `docs/` would have failed the page count, the citation-coverage check and the host allowlist, and editing `docs/index.html` would have been silently reverted by the build, failing `git diff --exit-code`. **This session's supplementary pages were therefore placed in a new, disjoint top-level directory `deep-dive/`**, which no existing workflow scans and which native GitHub Pages publishes at `/China2/deep-dive/` with no settings change.
- **Pending cross-scope link requests (logged, not unilaterally edited per protocol).** A link from the canonical `docs/index.html` (and the root `index.html`) into `deep-dive/index.html`, mirroring the two identical pending requests already logged by `arena-fcd22b0c` (for `site/`) and `arena/85f37d08` (for `portal/`). Those files are owned by `arena-996dc508` and are generated by `scripts/build.py`, so this session did not edit them. All three supplementary sections are independently live in the meantime, and `deep-dive/index.html` carries a prominent link back to the canonical dashboard.

## Publication record

| Item | Value |
|---|---|
| PR | (recorded after merge) |
| Merge | (recorded after merge) |
| Pages | https://sassnarep3-star.github.io/China2/ (canonical) · https://sassnarep3-star.github.io/China2/deep-dive/ (this session's supplementary section) |
