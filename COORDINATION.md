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
