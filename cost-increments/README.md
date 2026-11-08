# cost-increments — CNY→USD cost analysis for $10,000–$400,000

**Session `arena/8a2bd205-china2` · 2026-11-08 · research, not advice.**

Adds the missing quantitative layer to the repo’s existing dashboards: a
line-by-line cost estimate for transferring/converting CNY→USD in
**USD 10,000 increments from $10,000 to $400,000**, for every identified
route, with step-by-step procedures and an official-source link behind
every non-blank figure.

## Contents

- `index.html` — executive summary; cost leaderboard at $100,000; penalty decomposition
- `increments.html` — master matrix + Tables A–D (wire fees, dividend WHT, card/cash feasibility, illustrative spread sensitivity)
- `methods.html` — step-by-step procedure, pros/cons, legality for routes R01–R18
- `flagged-for-review.html` — every unverified item (I-01…I-15) with links and closing conditions
- `verification.html` — methodology, 5-layer penalty breakdown, full source registry, repo spot-audit
- `data.json` — machine-readable computed model (40 rows)
- `model.py` / `build.py` / `verify.py` — deterministic generator + independent verifier (no third-party dependencies)

## Reproduce

```sh
python3 cost-increments/build.py     # regenerate pages + data.json
python3 cost-increments/verify.py    # independent recomputation + link/anchor checks
```

## Verification statement

Every computed cell matches an independent recomputation in `verify.py`.
Every factual claim carries either (a) an https link to an official
source retrieved 2026-11-08 (marked “Fetched this session” in
`verification.html`), (b) a repository-ledger citation labelled “repo”
(not re-retrieved), or (c) an explicit blank flagged on
`flagged-for-review.html`. Nothing was inferred or back-filled. The
reference rate (6.6538 CNY/USD, Federal Reserve H.10, 2026-10-30) is
used only for arithmetic parity, never presented as an executable price.

Key verified anchors: USD 50,000 annual individual FX quota (SAFE) ·
0.1% issuance min CNY100/max CNY500 + CNY120 cable wire fee (HSBC
China tariff eff. 2026-10-31, items 2.2.4.1–2.2.4.2) ·
26 U.S.C. §988(e) $200 personal FX-gain threshold · 2026 FEIE
$132,900 (Rev. Proc. 2025-32) · FBAR penalties $16,536 / $165,353
(31 CFR 1010.821, assessed on/after 2025-01-17) · FBAR threshold
$10,000 · treaty WHT cap 10% dividends/interest/royalties (US–China
convention, IRS) · IIT 3–45% / 20% flat (PRC IIT Law arts. 3, 6) ·
EIT 25% (Art. 4) · overseas card cash withdrawal RMB 100,000/yr /
RMB 10,000/card/day (SAFE Huifa No. 29 [2017] Q&A).

Live site (after merge): https://sassnarep3-star.github.io/China2/cost-increments/
