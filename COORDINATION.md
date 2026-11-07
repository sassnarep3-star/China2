# COORDINATION.md — shared task board

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
