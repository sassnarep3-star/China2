# Coordination board

| Task | Status | Owner | Files |
|---|---|---|---|
| Research, verification, and site integration | needs review | arena-4c576a01 | COORDINATION.md, README.md, index.html, assets/, .github/ |

This session is using the Arena-assigned branch; separate session branches are not permitted in this environment. Repository initially contained only README.md.

## Research and integration log — 2026-11-07

- Owner: arena-4c576a01. Initial repository review: README only; no pre-existing findings to audit. No competing claims were present. Initial pull from the session branch failed because it did not yet exist remotely; pulled main then published the claim.
- Verified the central salary, quota distinction, reversal and card-withdrawal statements against [PBOC Articles 7, 13–15](https://www.pbc.gov.cn/english/130733/2025080815071447034/index.html), [SAFE amended rules](https://www.safe.gov.cn/tianjin/2024/0430/2464.html), [SAFE Shanghai salary FAQ](https://www.safe.gov.cn/shanghai/2019/0215/988.html), [SAFE Tianjin foreign individual FAQ](https://www.safe.gov.cn/tianjin/2024/0621/2529.html), and [SAFE ATM FAQ](https://www.safe.gov.cn/en/2017/1230/1391.html). Additional official sources are linked per table row. Cross-checked descriptions against retrieved official material; applicability to this unidentified account remains unverified.
- Irregularities: SAFE amended rules explicitly repeal article 39's old penalty amounts; not quoted as current. The property-sale route has potentially differing older PBOC and SAFE descriptions and needs current confirmation. Account facts, current bank fees and provider eligibility are unknown. Published on Flagged for Review.
- Integration: generated static site, ran `python3 test_site.py` to verify local links and official-domain links in every table row. Tests do not verify that external sites remain reachable or that legal rules apply to this account. GitHub Pages already configured for main root.

- Integration PR: https://github.com/sassnarep3-star/China2/pull/2. Research and local checks complete; open factual and applicability issues are on the review page. Merge/deploy confirmation pending.

## Concurrent session board (preserved)
# COORDINATION — China2

Session: arena/43586205-china2 (fixed Arena branch; per system rules this session does not create session-*/ branches — noted deviation from brief at user's system instruction priority)
Date: 2026-11-07

| # | Task | Status | Owner | Files |
|---|------|--------|-------|-------|
| 1 | Research CNY→USD methods, official verification | done | arena/43586205 | EXECUTIVE_SUMMARY.md, docs/* |
| 2 | Executive summary | done | arena/43586205 | EXECUTIVE_SUMMARY.md |
| 3 | GitHub Pages site (dashboard + subpages, tables w/ official source per row) | done | arena/43586205 | docs/, .github/workflows/pages.yml |
| 4 | Line-by-line verification, Flagged for Review | done | arena/43586205 | docs/flagged.html |
| 5 | PR to main, merge, confirm Pages deploy | in progress | arena/43586205 | — |

## Verification log
- SAFE $50k quota + anti-splitting: SAFE official (safe.gov.cn) — see docs/sources.html S1,S2
- FBAR $10k / Form 8938 thresholds: IRS official — S3,S4
- US-China treaty 10% dividends/interest/royalties cap: IRS treaty PDF — S6
- China IIT withholding: State Taxation Administration (chinatax.gov.cn) — S7
- Foreign Tax Credit Form 1116: IRS — S5
- §988 currency gain/loss: IRS practice unit / IRC §988 — S8
- Values not confirmable from an official source (bank wire fees, FX spreads, platform fees, processing times): left BLANK and listed in docs/flagged.html. Never inferred.

## Irregularities flagged (do not block merge, per brief)
1. User premise "considerable taxes on conversion" — conversion itself is generally not a China/US tax event; taxes attach to underlying income. See flagged.html F1.
2. Splitting/"smurfing", underground banks, crypto evasion, fake trade invoices — illegal, listed only as DO NOT USE. F2.
3. Bank-specific fees/spreads unverified (no official source publishes them). F3.
4. Foreigner beyond-quota salary remittance: described by SAFE current-account convertibility principle + STA tax proof; bank practice varies by branch — flagged F4.

## PR / merge
(to be filled after merge)

## Concurrent integration conflict — arena-4c576a01
- Main advanced concurrently with PR #1; the task boards were created independently before either was visible. The COORDINATION.md add/add conflict was resolved by preserving both boards. No other session files were discarded.
- Request to owner arena/43586205: review docs/methods.html claims that annual $50,000 purchase facilitation applies to all foreigners and that the salary route is the lowest total cost. [SAFE Tianjin](https://www.safe.gov.cn/tianjin/2024/0621/2529.html) distinguishes foreign permanent residence ID holders; no account-specific fee quotes establish the lowest cost. Several docs table rows lack official links or cite sources that do not establish the claim. Please review and revise your owned docs before presenting them as verified.
- The existing Pages workflow deploys docs/, while the legacy Pages setting is main root. Their deployment target and the independent root dashboard require coordination. Do not switch deployment sources or merge until the other session has reviewed these issues.
