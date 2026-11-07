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

## Update 2026-11-07 (integration fix)
- PR #1 merged: https://github.com/sassnarep3-star/China2/pull/1
- Custom Actions Pages workflow failed (Pages is legacy build_type main:/, token cannot switch to workflow - 403). Removed workflow, added root index.html redirect to docs/, relying on legacy Pages deploy which reported status=built. Live: https://sassnarep3-star.github.io/China2/

## Coordination events

- 2026-11-07: This session initially inspected a stale local base (`d9f3976`) that contained only `README.md` and no board, then made a provisional claim. Before any research or site files were changed, the required `git pull --rebase origin main` found main had advanced to merge commit `2fd31b8` from session `arena/43586205-china2`. Rebase encountered an add/add conflict in this file. Resolution preserved that session's board, completed work, verification notes, and ownership. This session did not change their research or site files.
- 2026-11-07: Read-only integration check against main `6849db3` found no broken local HTML links, but the following data rows have no external official-source hyperlink: `docs/costs.html` (bank FX spread, SWIFT fee, platform fee), `docs/flagged.html` (F3, F5, F6), `docs/index.html` (bank wire fee), `docs/methods.html` (cash-carry and emigration channels), and `docs/taxes.html` (standalone conversion-tax row). Values are blank/flagged where applicable. Review request to the existing owner: add a relevant official authority link or make the source gap explicit on Flagged for Review while keeping unverified amounts blank. Also review “cheapest” / “lowest total cost” in `EXECUTIVE_SUMMARY.md` and `docs/methods.html`: no comparable official bank/platform price data was available in the pages to substantiate that superlative.
- 2026-11-07: Read-only GitHub checks confirmed PR #1 and PR #3 are merged; GitHub Pages API reports the site as public and built at `https://sassnarep3-star.github.io/China2/`, and the latest deployment for main commit `6849db3` reported success (deployment `7626626462`). The feature-branch workflow run from this session (`42411197897`) failed with zero jobs and no run log; the main Pages build/deploy succeeded after the legacy Pages integration fix. No site or workflow files were changed by this session.
