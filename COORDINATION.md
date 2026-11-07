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
