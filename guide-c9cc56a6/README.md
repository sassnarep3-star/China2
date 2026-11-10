# CNY → USD repatriation guide (`guide-c9cc56a6`)

A consolidated, source-linked answer to one question: **what is the cheapest lawful way to get
renminbi out of a Chinese bank account into USD, and what does it really cost in tax and fees?**

Live: <https://sassnarep3-star.github.io/China2/guide-c9cc56a6/>

## Pages

| Page | What is on it |
| --- | --- |
| `index.html` | Executive summary: the six things that decide the answer, ranked routes, order of operations |
| `methods.html` | 24 routes — lawful, conditional and unlawful — with pros, cons, documents and exact steps |
| `costs.html` | All-in cost at every USD 10,000 step from 10,000 to 400,000, per route, plus statutory fine ranges for the unlawful ones |
| `taxes.html` | The four exposures usually conflated: PRC income tax, the section 988 exchange difference, US reporting penalties, PRC foreign-exchange fines |
| `flagged.html` | Every unverified value, every irregularity found in the repo, and every assumption the tables rest on |
| `sources.html` | 32 sources with how each was verified and what it was used for |
| `audit.html` | Line-by-line audit of the repository and of this guide's own arithmetic |

## The finding in one paragraph

There is no tax on converting CNY to USD, in either jurisdiction. China taxes nine listed categories of
income; a conversion is not one of them. The United States taxes worldwide income at the rate in effect when
it is earned, so a later conversion can only produce a section 988 exchange difference — and at the IRS's own
yearly averages the yuan has weakened since 2021, so an older balance shows an exchange *loss* on conversion,
not a gain. The published bank cost of the cheapest lawful route is 0.1% of the amount with a floor of CNY 100
and a cap of CNY 500, plus a CNY 120 cable fee: USD 30.99 on 10,000 and USD 87.32 on 400,000. The binding
constraint is documentation, not tax, and the expensive mistakes are the shortcuts — 30% to 100% of the amount
in fines.

## Reproduce

```bash
python3 guide-c9cc56a6/build.py     # writes the 7 pages, assets/style.css and data/costs.json
python3 guide-c9cc56a6/verify.py    # 483 checks: sources, links, flags, fee arithmetic, tier coverage
```

`verify.py` fails if a table row lacks a source link, if a blank cell lacks a flag, if a flag id does not
exist on the Flagged page, if a dollar figure cites an unverified source, if the published fee at any of the
40 tiers disagrees with a fresh computation from the tariff, or if a page contains a rendering artifact.

## How to read the cost tables

* **Published bank fee** — exact, from a published tariff (HSBC China, effective 31 October 2026). Verifiable.
* **FX margin (assumed)** — the gap between the rate the bank deals on and the market. **No bank publishes
  this.** It is shown as a labelled band, never as a fact. See flag **F01**.
* **All-in estimate** — the sum. An order of magnitude with a known floor, not a quote.

## Scope and coordination

This session's scope was `guide-c9cc56a6/**` plus
`.github/workflows/verify-guide-c9cc56a6.yml`, recorded in `COORDINATION.md` before any file was written.
No file outside that scope was edited. The pre-existing ladder's stale Global Transfer fee is reported as
flag **F02** rather than fixed, because `ladder/**` belongs to another session.

This is research, not tax or legal advice. Three blanks are deliberate: the FX margin (F01), your own PRC tax
liability (F08), and the character of a section 988 gain above USD 200 (F04).
