# Getting CNY out of China: executive summary

Independent source review · final integration pass · 2026-11-11 · session `arena/3347ca0a-china2`

**Not tax or legal advice.** No account facts were supplied, no bank was contacted, no funds moved and no return was filed.

---

## 1. The single most important finding

**There is no PRC tax on the act of converting renminbi into dollars in the instruments reviewed.** What those rules
impose is a *documentary* test: the bank must see your ID and evidence of where the money came from — including the
PRC tax record. (Checks V01, V02, V03 in the [verification ledger](index.html).)

What people experience as a "conversion penalty" is one of five other things, and they are priced very differently:

| Layer | What it actually is | Size, as far as the sources go |
|---|---|---|
| Tax on the conversion | none found in the reviewed FX regulations | **$0** |
| Tax on the origin of the money | PRC individual income tax already withheld, or still owed (3%–45% comprehensive / 20% / treaty 10%) | fact-specific — **not computed here** |
| Bank fee | HSBC China telegraphic transfer 0.1% (min CNY 100, max CNY 500) + CNY 120 cable | **$32.88** at $10,000 → **$92.66** at $400,000 |
| Exchange margin | the bank's own buying/selling gap | **≤ 0.42%** — $1,679.84 at $400,000, i.e. ~18× the wire fee |
| U.S. reporting | FBAR / Form 8938 / Form 3520 exposure | depends on balances and history — **not computed here** |

The last two lines are the practical answer to "what is the least-tax way": the tax is not the lever. The **documentary
gate** decides whether you can move the money at all, and the **exchange margin** is the largest published cost.

## 2. Cost at the milestone tiers

Published sender fee converted at the Bank of China USD board of 2026-11-11 10:25:02 (6.6911 CNY/USD), plus the
exchange-margin bound (the full board gap, 0.42%). Intermediary, correspondent and receiving-bank fees are not
published by the bank and are **left blank**.

| USD | CNY needed | Route | Sender fee (Premier / Advance) | Sender fee (Private Banking / Premier Elite) | Margin bound | Indicative total |
|---|---|---|---|---|---|---|
| $10,000 | 66,911 | M01 documented bank wire | $32.88 | $0.00 | ≤ $42.00 | $74.88 |
| $50,000 | 334,555 | M01 documented bank wire | $67.93 | $0.00 | ≤ $209.98 | $277.91 |
| $100,000 | 669,110 | M01 documented bank wire | $92.66 | $0.00 | ≤ $419.96 | $512.62 |
| $200,000 | 1,338,220 | M01 documented bank wire | $92.66 | $0.00 | ≤ $839.92 | $932.58 |
| $400,000 | 2,676,440 | M01 documented bank wire | $92.66 | $0.00 | ≤ $1,679.84 | $1,772.50 |

The dollar fee stops rising after roughly $70,000 because the renminbi cap (CNY 500 + CNY 120) binds.

Same tiers under the routes that carry a cap:

| Route | Fee | Constraint |
|---|---|---|
| M02 HSBC Global Transfer to a self-named U.S. HSBC account | $0.00 (Private Banking / Premier), $20.00 (Advance) | needs HSBC accounts in both countries and Premier/Elite status (V12) |
| M06 USD-50,000 annual total + wire | as M01 per wire | PRC-ID / permanent-resident holders only; 1 wire per calendar year — 8 years for $400,000 (V04) |
| M15 overseas ATM cash | issuer fees unpublished | hard cap RMB 100,000/year and RMB 10,000/card/day → **27 calendar years** and 268 withdrawals for $400,000 (V19) |
| M17 physical USD banknotes | $0.00 bank fee | USD 5,000 per trip permit-free → **80 trips** for $400,000; FinCEN Form 105 above USD 10,000 (V17) |
| M03 Wise from CNY | only shown in-app — blank here | CNY 300,000 per transfer, tax record within the last 3 years, own-name account only (V14) |

*Why these numbers differ from older pages in this repository:* those tables convert renminbi fees at 7.129 CNY/USD, the
IRS 2025 yearly average used for tax translation. At the 2026-11-11 retail board the same CNY 620 fee is $92.66, not
$86.97 — a 6.5% difference. Both rates are legitimate for their own purpose; see finding IR-05.

## 3. What the answer depends on — and what is missing

Twelve private facts gate any recommendation. The first six:

- **Q01 — What is the legal origin of the balance?** (salary / rent / royalties / business profit / property sale /
  inheritance / pre-emigration assets / untaxed receipts). *How to find out:* pull five years of bank statements, list
  each large credit with its payer, contract and tax slip, and classify each tranche before choosing a route.
- **Q02 — Was PRC individual income tax actually withheld and is it on record?** *How to find out:* download the
  个人所得税纳税记录 (individual income-tax payment record) from the tax app or office for each year.
- **Q03 — How does SAFE classify you** — 境内个人 (domestic individual) or 境外个人 (overseas individual), and do you
  still hold a PRC ID? The annual-total rule attaches to the former (V04).
- **Q04 — When was each tranche acquired, and what is its USD basis?** This decides whether the § 988(e)(2) $200
  de minimis applies (V15).
- **Q05 — What is your U.S. offshore reporting history?** (FBAR, Form 8938, Form 3520.) Unfiled years are usually the
  largest financial exposure in the whole problem.
- **Q06 — What executable rate and all-in quote will the bank actually give?** Ask in writing, with the rate,
  commission, cable, correspondent and receiving charges shown separately.

The full checklist, with what we know, what we do not know and how to discover it for each, is in
`transfer-guide/questions.html`.

## 4. What is verified, and what is not

- **20 of 22** load-bearing sentences were re-fetched from their official hosts on 2026-11-11 and the exact text is
  published beside each one (PRC State Council, SAFE Beijing/Tianjin/Henan, HSBC China tariff effective 31 Oct 2026,
  IRS, GPO, CBP, Bank of China, Wise).
- **2 of 22** were retrieved but not read out line by line — the FBAR penalty table (31 CFR 1010.821) and the PRC IIT
  schedule / treaty dividend article. They are marked **NOT RE-CHECKED** and the figures are *not* republished here as
  verified.
- **18 open flags** remain in the canonical transfer guide. None blocks publication; all are visible on the site.
- No personal tax amount, no "cheapest route" and no eligibility determination is asserted anywhere.

## 5. Repository irregularities found in this pass

Full detail, with evidence and file links, in `irregularities.html`.

- **IR-01** Twenty separate research sites (111 pages) in one repository; the root page previously offered sixteen of
  them as equal choices.
- **IR-02** The method count differs between sites: 15, 17, 22 and 23.
- **IR-03** The cost-ladder row count differs: 600, 680 and 920.
- **IR-04** Source registers and flag counts differ: 16 / 24 / 40 sources; 9 / 16 / 18 / 31 flags.
- **IR-05** Two rate bases (7.129 tax translation vs 7.10 model assumption) are used as if they were costs; at the
  2026-11-11 board the dollar fee is 6.5% higher.
- **IR-06** 1,423 table rows on 36 pages lack a direct primary-domain URL in their own row (structural scan; 15 are this
  page's declared navigational rows, 7 cite repository files).
- **IR-07** Four different review dates (7, 10 and 11 November 2026) across pages.
- **IR-08** The export's rate column says 7.13 while the fee text in the same row says 7.129.
- **IR-09** Resolved: the superseded "USD 0–7" same-name transfer wording now appears only where it is being corrected.
- **IR-10** Resolved: the HSBC fee arithmetic reproduces the tariff exactly at both rate bases.
- **IR-11** Open: the USD 50,000 figure is described inconsistently (rule text vs bank guidance) — material to route
  choice, unresolved for any specific bank.
- **IR-12** Resolved: Article 39 of Hui Fa [2007] No. 1 is repealed and must not be cited for penalty amounts.

## 6. The recommended sequence

1. **Establish what the money is.** Tax records plus contracts for every year that funded the balance.
2. **Ask the bank in writing** what it will accept, and for an all-in quote with each charge on its own line.
3. **Only then choose** between M01 (documented wire), M02 (same-name book transfer) and M03 (Wise) on price.
4. **Check U.S. reporting** for the year the balance crossed the thresholds — a transfer does not erase it.
5. **Keep every exchange memo.** It is the only thing that lets you reverse an unspent remainder, and only for 24
   months (V05).

## 7. Sources

- This pass's ledger, with exact quotes and limits: `verification-3347ca0a/index.html` and `data/checks.json`.
- Full register (40 documents, with locators): `transfer-guide/sources.html`.
- Open flags: `transfer-guide/flagged.html`.
- Repository audit: `verification-3347ca0a/irregularities.html`.
