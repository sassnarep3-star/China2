# Executive summary — CNY → USD for a US citizen

**Prepared:** 8 November 2026 · **Session:** `arena/21827432-china2` · **Live site:** https://sassnarep3-star.github.io/China2/

Research, not legal, tax or investment advice. No funds were moved and no returns were filed.

---

## 1. The premise needs correcting

The starting assumption was that converting CNY to USD triggers a considerable tax. The statutes do not support that.

- **PRC side.** Article 2 of the Individual Income Tax Law taxes nine categories of income. Converting RMB to USD is not one of them; there is no FX-conversion tax in the law or in the SAFE rules.
- **US side.** Moving your own money between your own accounts is not a realisation event. For currency, §988(e)(1) excludes an individual's personal transactions from §988 and §988(e)(2) recognises no gain on a personal transaction unless the gain would exceed $200.

**Verified statutory cost of converting documented, already-taxed money: $0 at every amount from $10,000 to $400,000.**

## 2. Where the money actually goes

| Layer | What it is | Verified position | Source |
|---|---|---|---|
| L1 | PRC tax on the conversion | 0% | IIT Law Art. 2 |
| L2 | PRC income tax on the money's source | 3%–45% progressive · 5%–35% business · 20% flat | IIT Law Arts. 3, 6 + rate schedule |
| L3 | Document gate at the bank | ID + source documents **including tax vouchers** | Implementing Rules Art. 13(1) |
| L4 | US tax on moving your own funds | 0% | 26 U.S.C. §988(e) |
| L5 | US residual after the foreign tax credit | usually $0; computed per amount | IRC §904 / IRS FTC page |
| L6 | Bank spread and wire fees | **unverified — no official publication** | none exists |
| L7 | Reporting duties (FBAR, 8938, 3520, CMIR) | $0 if filed | IRS / FinCEN / CBP |
| L8 | Fines on prohibited channels | up to 30%, or 30%–100% if serious | Decree 532 Arts. 39–45 |

The "considerable tax" is almost always L2 — tax owed on the income whether or not the money ever leaves China — or L3, a bank refusing to process without the certificate. Neither is a fee for converting.

## 3. The numbers at $400,000

| Scenario | Amount |
|---|---|
| A. Already-taxed money: verified statutory cost | **$0** |
| B. Entire balance untaxed labour income: PRC IIT | **$148,896** |
| C. Entire balance an asset gain at 20%: PRC tax | **$80,000** |
| US residual after credit in case C | **$23,134** |
| US residual after credit in case B | **$0** |
| Years needed at the USD 50,000 quota, if it applies | **8** |
| Years needed through the ATM channel (RMB 100,000/yr) | **27** |
| Fine if a prohibited channel were used (low / serious) | **$120,000 / $400,000** |

Full 40-row table: `costs.html`. Method-by-amount matrix: `matrix.html`.

## 4. The route, in order

1. Establish ownership and the lawful source of the balance; locate the tax evidence (完税证明 or withholding records).
2. If the money came from an earlier FX conversion, use the original exchange memo (M02) — the only route needing no tax documents, valid 24 months.
3. If the balance is already in foreign currency, remit it from the FX savings account (M04) — no conversion means no spread.
4. Otherwise use M01: documented conversion plus wire, with the full document set.
5. Ask the bank, in writing, for the all-in price **and** for which category it will record you under.
6. File the US information returns for every year the thresholds were met.

## 5. The two findings that change a recommendation

- **The USD 50,000 quota is not the controlling rule for a US citizen converting documented lawful income.** Article 13 of the implementing rules sets documents, not a dollar cap. But the classification is genuinely contested: Decree 532 Art. 52(2) counts a foreigner resident in China for one year as 境内个人, which would *impose* the cap rather than remove it. Flagged as F02; the bank's written answer decides it.
- **The prohibited routes are priced as a percentage of the whole amount.** At $400,000 the fine range is $120,000 to $400,000 plus confiscation — against a lawful cost of $0 in tax plus an unpublished commercial spread.

## 6. What cannot be certified

No provider is named cheapest, because no official source publishes spreads. No personal tax amount is stated, because the personal facts are unknown. No commercial fee is filled in. No individual eligibility conclusion is drawn. Sixteen items are published on `flagged.html`, each with the source that limits it: unknown personal facts (tax paid, cost basis, filing history, exchange memos), prior-session claims not re-fetched (treaty rate, cash-carry limits, crypto notice, outbound-payment filing, Form 3520 percentages), model assumptions (resident status, single filer, one exchange rate, US federal only), and three repository irregularities.

## 7. What was verified, and how

22 official sources; 16 re-read in this session and 6 carried from earlier sessions with their status marked. Every dollar figure in the tables is recomputed by `scripts/verify_site.py`, which does not import the builder and re-derives taxes from bracket tables transcribed as the official publications print them. 2,539 checks pass; 143 real-browser checks pass at 1440px and 390px. Two errors in earlier repository data were found and corrected: a §988 gain described as capital (it is ordinary) and the §6677 trust penalty attributed to foreign gifts (they fall under §6039F).

## 8. First action

Before any bank visit: establish whether the PRC tax on the income was paid and obtain the certificate. That single document decides whether this is a 0% transaction or a 3%–45% one.
