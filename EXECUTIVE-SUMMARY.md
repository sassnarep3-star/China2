# Executive Summary — Getting Money Out of China as a U.S. Citizen

**Session:** `arena-fcd22b0c` · **Date:** 2026-11-07 · **Status:** complete, 463 automated checks passing
**Live site:** see GitHub Pages link in `COORDINATION.md` · **Ledgers:** `data/*.json`

> Research only. Not tax or legal advice. Every figure below is tied to a primary official
> document. Anything that could not be confirmed from an official source is **left blank and
> flagged**, never estimated.

---

## The one thing that changes the answer

**The premise in the question is wrong, and correcting it is the most valuable part of this work.**

There is no such thing as a "conversion tax." Neither the United States nor China taxes the act
of turning CNY into USD.

- **United States.** The IRS requires all income tax determinations to be made in the functional
  currency, and the U.S. dollar is the functional currency for all taxpayers except some
  qualified business units. What can be taxed is *exchange-rate gain on the currency position* —
  and IRS Publication 525 states that a gain on a **personal** foreign currency transaction is
  not included in income unless it exceeds **$200**; above that it is reported as a capital gain.
  Converting money you already own is not income.
- **China.** SAFE's individual foreign-exchange regime imposes a **quota** and an **authenticity
  review**. It imposes no tax on buying or selling foreign exchange. Chinese individual income
  tax attaches to the *income* when it arises — 3%–45% progressive on comprehensive income after
  the RMB 60,000 deduction, and a flat 20% on interest, dividends and property transfers.

**So what is the "considerable amount of taxes"?** Almost certainly one of three different
things, none of which is a conversion tax:

1. Chinese individual income tax on the earnings that created the balance — owed when the income
   arose, not when it is remitted.
2. The bank's exchange-rate **spread** plus wire and correspondent fees — not tax at all, and
   usually the single largest real cost. **No official figure exists for this**, so none is
   published here (flag **F05**).
3. **U.S. reporting penalties** for an account that was never declared. This is where large money
   is actually lost.

---

## The real bottleneck is a quota, not a tax rate

| Constraint | Verified value | Source |
|---|---|---|
| Individual FX facilitation quota | **USD 50,000 equivalent per individual per year**, covering purchases *and* sales, for domestic *and* foreign individuals | [SAFE, 2007](https://www.safe.gov.cn/en/2007/0105/819.html) |
| Above the quota | Formalities inside the quota are "drastically simplified"; above it, "examination of the authenticity of transactions ... shall be strengthened" | [SAFE, 2007](https://www.safe.gov.cn/en/2007/0105/819.html) |
| Detection | SAFE runs a bank-to-SAFE management information system through which banks verify the authenticity of materials individuals provide | [SAFE, 2007](https://www.safe.gov.cn/en/2007/0105/819.html) |
| Escape valve 1 — genuine individual trade | Purchases and sales under an individual **foreign-exchange settlement account** are *not* subject to the annual quota, "regardless of the amount," against valid trading documents | [SAFE, 2007](https://www.safe.gov.cn/en/2007/0105/819.html) |
| Escape valve 2 — emigration or inheritance | **Emigrant** and **inheritor** asset transfers are approved by SAFE outside the quota; since the 2014 circular the installment requirement was cancelled and a lump-sum remittance is permitted within the approved limit | [PBOC](https://www.pbc.gov.cn/english/130721/2025080815062856255/index.html) · [SAFE, 2014](https://www.safe.gov.cn/en/2014/0801/741.html) |
| Parallel cash channel | Overseas card cash withdrawals: **RMB 100,000 equivalent per individual per civil year**, **RMB 10,000 equivalent per card per day** — a separate limit that does not contradict the USD 50,000 quota | [SAFE Huifa 29 (2017)](http://www.safe.gov.cn/en/2017/1230/1397.html) |

---

## The largest financial exposure is U.S. reporting

A U.S. citizen is inside the U.S. reporting net the moment the Chinese account exists — before a
single yuan is converted.

| Obligation | Trigger | Source |
|---|---|---|
| **FBAR** — FinCEN Form 114 | Aggregate value of foreign financial accounts exceeded **$10,000 at any time** in the calendar year. Filed with FinCEN, due April 15, automatic extension to October 15. Whether the account produced income is irrelevant. | [IRS](https://www.irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar) |
| **Form 8938** | >$50,000 at year-end or >$75,000 at any time (unmarried, in the U.S.); >$200,000 / >$300,000 living abroad. Not required if no return filing is required. | [IRS](https://www.irs.gov/businesses/corporations/summary-of-fatca-reporting-for-us-taxpayers) |
| Both can apply | "Form 8938 does not relieve filers of FBAR filing requirements." | [IRS](https://www.irs.gov/businesses/corporations/summary-of-fatca-reporting-for-us-taxpayers) |
| **FinCEN Form 105 (CMIR)** | More than **$10,000** in currency or monetary instruments transported into or out of the United States | [IRS IRM 4.26.9](https://www.irs.gov/irm/part4/irm_04-026-009) · [FinCEN portal](https://fincen105.cbp.dhs.gov/) |

**FBAR penalty amounts are deliberately not stated.** The official IRS page says only that civil
maximums in Title 31 U.S.C. are adjusted annually for inflation under 31 CFR 1010.821 and warns
its own figures may not be current. Widely quoted numbers come from commercial tax sites. Flag **F02**.

---

## Routes ranked by lawful cost

18 routes were catalogued: **12 lawful or conditionally lawful**, **6 unlawful**. Full detail with
pros, cons, limits and tax treatment is in `data/methods.json` and on the site.

| Rank | Route | Why |
|---|---|---|
| 1 | **R01** Wire inside the USD 50,000 quota | No approval needed, no conversion tax, cleanest documentary trail. Costs only bank spread and fees. |
| 2 | **R03** Emigrant asset transfer | The only route that can lawfully move an arbitrarily large personal balance in one process, outside the quota. Requires foreign permanent residence or citizenship, and only covers assets obtained *before* that status. |
| 3 | **R07** Individual FX settlement account for genuine trade | Expressly not subject to the annual quota at all — but requires real trade documents, and business use removes the $200 U.S. personal-transaction exclusion. |
| 4 | **R02** Above-quota wire on authenticity documents | The general lawful answer for any amount, at the price of slower processing and a real possibility of refusal. |
| 5 | **R05** Overseas card cash withdrawals | Supplement only. RMB 100,000/year, and exceeding it costs you the current *and* following year. |

---

## Routes to reject outright

| Route | Official basis for rejection |
|---|---|
| **R13** Cryptocurrency | All virtual-currency-related business activities are illegal in China; offshore exchanges serving mainland residents are illegal financial activity. [gov.cn](http://english.www.gov.cn/statecouncil/ministries/202109/24/content_WS614dc30bc6d0df57f98e0c84.html) |
| **R14** Splitting / pooling relatives' quotas | SAFE states the quota system exists partly to prevent avoiding administration, including repeated purchases and sales in installments; banks verify authenticity via the SAFE-linked system. [SAFE](https://www.safe.gov.cn/en/2007/0105/819.html) |
| **R15** Underground banking | PBOC requires assets transferred abroad to be lawful, owned, undisputed and documented; false documents are penalized under the PRC Foreign Exchange Administration Regulations. [PBOC](https://www.pbc.gov.cn/english/130721/2025080815062856255/index.html) |
| **R16** Fabricated trade invoicing | Business under a settlement account must be conducted with **valid** trading documents regardless of amount. [SAFE](https://www.safe.gov.cn/en/2007/0105/819.html) |
| **R17** False documents in an asset-transfer application | Expressly penalized under the PRC Foreign Exchange Administration Regulations. [PBOC](https://www.pbc.gov.cn/english/130721/2025080815062856255/index.html) |

---

## What the conversion penalty actually consists of

| # | Component | Verified amount |
|---|---|---|
| 1 | Tax on the conversion itself | **$0** in China. U.S.: $0 if the personal gain is ≤$200 per transaction; above that, tax on the gain as a capital gain. |
| 2 | Tax on the income that created the balance | 3%–45% progressive after RMB 60,000; flat 20% on interest, dividends, property transfers |
| 3 | Bank spread and transfer fees | **UNVERIFIED — no official source exists** (F05) |
| 4 | Time cost of the quota | Balance ÷ USD 50,000 = calendar years |
| 5 | U.S. non-compliance exposure | **UNVERIFIED** — inflation-adjusted, not retrieved from eCFR (F02) |
| 6 | Chinese non-compliance exposure | Penalty under the PRC FX Administration Regulations; schedule **UNVERIFIED** (F11) |
| 7 | Treaty withholding on dividends / interest / royalties | Capped at **10% of gross** where the recipient is the beneficial owner — [treaty Arts. 9(2), 10(2), 11(2)](https://www.irs.gov/pub/irs-trty/china.pdf) |
| 8 | Relief against #2 and #7 | Foreign tax credit in the country of residence, per the treaty |

**Conclusion.** If Chinese tax on the income is already settled, the lawful cost of conversion is
component **3 + 4** only. The cheapest lawful strategy is therefore not to hunt for a tax shelter.
It is to: settle component 2 so the authenticity review passes; claim component 8 so it is not paid
twice; minimise component 3 with competing written quotes; and shorten component 4 by qualifying
for the emigrant asset transfer or a genuine trade settlement account, both of which sit outside
the quota. Every "cheap" alternative attacks component 4 by breaking the law and converts a modest
quantifiable cost into components 5 and 6.

---

## Do this before moving anything

1. **File or catch up every missed FBAR.** Required whether or not the account earned income; the
   IRS directs late filers to file as soon as possible to keep potential penalties to a minimum.
2. **Establish how the balance arose and whether Chinese tax was withheld.** Tax certificates or
   tax payment vouchers are a *required document* for the personal-asset outbound transfer application.
3. **Decide whether the immigration route is open to you.** Emigrant asset transfer needs foreign
   permanent residence or citizenship, and only covers assets obtained beforehand.
4. **Claim the foreign tax credit** for Chinese tax paid — the treaty provides for it.
5. **Do not split the quota** across relatives to fund one transfer.
6. **Do not touch cryptocurrency or underground banking.**

---

## What could not be verified

16 flags are published on the **Flagged for Review** page. The most consequential:

| Flag | Item |
|---|---|
| **F01** | The $200 personal FX exclusion was read from IRS-hosted Publication 525 text via the search index; the live page was confirmed to be the 2025 edition but the paragraph was not re-read in-session. |
| **F02** | FBAR civil penalty dollar amounts — left blank. |
| **F03** | **The repository contained no pre-existing data to audit.** `main` held one commit and one 8-byte `README.md`. |
| **F04** | No personal facts were supplied (balance size, personal vs. corporate, origin of funds, tax residency, immigration status), so every recommendation is conditional. **Nothing was inferred.** |
| **F05** | Bank spread, wire and card fees — no official source exists; left blank. |
| **F07** | Chinese customs cash-carrying thresholds — no official customs source located; left blank rather than repeating travel-blog figures. |
| **F15** | SAFE, PBOC and STA English translations are all expressly non-authoritative; the Chinese text prevails. |

---

## Verification performed

`node tools/verify.mjs` — **463 checks, 0 failures.** It confirms that every rendered data row
carries a link to an official source or is explicitly badged UNVERIFIED; that no data field is
blank; that every source URL is on an official domain allowlist (`irs.gov`, `ecfr.gov`,
`cbp.dhs.gov`, `treas.gov`, `loc.gov`, `safe.gov.cn`, `pbc.gov.cn`, `chinatax.gov.cn`,
`www.gov.cn`, `customs.gov.cn`, `github.com`); that no internal link or anchor is broken; and
that `meta-row` markup is not being used to escape the source-link rule.

**17 official sources.** 11 were retrieved in full this session and their supporting sentences
read verbatim on the page; 6 are marked `search-index` because the value came from a search-index
extract of that exact official URL without a separate in-session retrieval. That distinction is
displayed on every row and on the source register.

**Outbound HTTP from this build sandbox is restricted to a small allowlist that excludes irs.gov
and safe.gov.cn**, so external URLs cannot be re-requested at build time. External verification
was done during research, page by page; internal links and anchors *are* checked mechanically on
every build.
