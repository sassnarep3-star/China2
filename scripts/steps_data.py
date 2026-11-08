#!/usr/bin/env python3
"""Step-by-step execution plans. Each step states only what an official source
requires, and marks bank-specific practice as such."""

# key -> (heading, intro, [(step title, what to do, source ids)])
STEPS = {
 "m01": ("M01 — Documented income conversion and wire", "The primary lawful route for money that came from documented, taxed PRC income. No annual USD ceiling is stated for a non-domestic individual; the bank's document review is the gate.", [
   ("Assemble the identity file", "Passport and the bank's customer records. The bank must verify the validity of the identity document and the authenticity of the other materials.", ["S01", "S02"]),
   ("Assemble the source file", "The contract, payroll records, award letter, lease or sale contract that produced the RMB, plus the PRC tax payment certificate or the employer's withholding records. Art. 13(1) expressly lists tax vouchers among the documents.", ["S02"]),
   ("Ask the bank to confirm your category in writing", "Ask whether you will be recorded as 境外个人 (non-domestic) or 境内个人 (domestic) for this transaction. Decree 532 Art. 52(2) counts a foreigner resident in China for one year as 境内个人, which changes the applicable rule set. Record the answer.", ["S11", "S02"]),
   ("Request the all-in quote before signing anything", "Ask for: the spread against the PBOC central parity, the outgoing wire fee, the intermediary lift, and the receiving US bank's fee. No official source publishes these, so the number must come from the bank in writing.", ["S01"]),
   ("Convert and remit in one instruction where possible", "A conversion followed by a separate remittance day creates a second FX exposure and can trigger a second fee. Art. 13 covers conversion; Art. 15(1) covers remittance from an FX savings account with valid ID.", ["S01", "S02"]),
   ("Keep the paper trail for both jurisdictions", "Retain the conversion slip, the wire confirmation and the tax certificate. These are the evidence that the money was already taxed and that no gain needs recognising under §988(e).", ["S06", "S08"]),
   ("File the US information returns", "FBAR if the aggregate account balance exceeded USD 10,000 at any time; Form 8938 if the published thresholds were met; no income is reported merely because the money arrived.", ["S08", "S09", "S06"]),
 ]),

 "m02": ("M02 — Re-conversion against the original exchange memo", "The only route that can avoid tax documents entirely, but only for RMB that came from an earlier conversion of foreign currency, and only for 24 months.", [
   ("Find the original exchange memo (原兑换水单)", "Without the memo this route does not exist. The 24-month clock runs from the date of the original conversion.", ["S02"]),
   ("Compare the memo amount with the balance", "Only the amount covered by the memo can be re-converted this way; any excess falls back to the M01 documentation route.", ["S02"]),
   ("Present ID and the memo at the counter", "Art. 13(2) requires valid ID plus the original exchange memo.", ["S02"]),
   ("Watch the 24-month expiry", "If the memo is older, the bank can refuse; plan the conversion before the window closes.", ["S02"]),
   ("Report on the US side as a non-event", "Returning your own previously converted principal is not income; a personal-transaction FX movement is outside §988 unless the gain would exceed $200.", ["S06"]),
 ]),

 "m03": ("M03 — Small-amount walk-in conversion with ID only", "A safety valve for small sums; it cannot move a large balance in any reasonable time.", [
   ("Confirm the same-day ceiling", "USD 500 equivalent per day, or USD 1,000 at pre-departure port outlets, with ID only.", ["S02"]),
   ("Keep each day below the ceiling", "The rule is drawn per same-day cumulative amount, not per transaction.", ["S02"]),
   ("Do not recruit other people", "Splitting across people or cards to evade limits is expressly prohibited and carries the penalty scale in Art. 39-45 of Decree 532.", ["S01", "S11"]),
 ]),

 "m04": ("M04 — Remit an existing FX savings-account balance", "The cheapest route when it is available: no conversion is needed, so no spread is paid.", [
   ("Check the currency of the balance", "This route applies only if the money is already in foreign currency inside the account, not RMB.", ["S02"]),
   ("Present ID and request the outward remittance", "Art. 15(1) requires valid ID for a non-domestic individual's outward remittance from an FX savings account.", ["S02"]),
   ("Confirm whether the bank applies the domestic-individual daily rule", "Art. 14 sets a USD 50,000 per day ID-only threshold for domestic individuals; banks sometimes apply the stricter rule to everyone. Ask which applies to you.", ["S02"]),
   ("File the US information returns", "FBAR and Form 8938 thresholds are unchanged by the transfer itself.", ["S08", "S09"]),
 ]),

 "m05": ("M05 — Overseas ATM withdrawals", "Fast, small, and hard-capped. Useful for spending money, not for repatriating a balance.", [
   ("Confirm the card is enabled for overseas use", "The issuer must have the cross-border switch on.", ["S03"]),
   ("Stay inside RMB 10,000 per card per day", "The per-card daily ceiling was adjusted from USD 1,000 to RMB 10,000 equivalent.", ["S03"]),
   ("Track the annual ceiling", "RMB 100,000 equivalent per individual per civil year across all cards. Exceeding it suspends overseas cash withdrawal for the current and the following year.", ["S03"]),
   ("Do not borrow or lend cards", "Art. I expressly prohibits borrowing or lending cards to evade the rule.", ["S03"]),
   ("Declare cash if it crosses the US border", "More than USD 10,000 in currency at one time must be reported on FinCEN Form 105, aggregated across a family or group.", ["S14"]),
 ]),

 "m06": ("M06 — Overseas card spending for genuine consumption", "Converts RMB into goods and services abroad rather than into USD you can hold.", [
   ("Keep it genuine", "Travel, tuition, hotels and retail are the intended uses; cash extraction through a merchant is prohibited.", ["S03", "S11"]),
   ("Keep the receipts", "They evidence that the spend was personal consumption if the issuer asks.", ["S01"]),
 ]),

 "m07": ("M07 — Physical cash across the border", "High risk and small capacity. Included for completeness, not recommended.", [
   ("Check the PRC declaration rules on the day you travel", "The GACC limits are cited here from a prior session and were not re-verified, so no figure is stated. Read the current passenger guide.", ["S22"]),
   ("File FinCEN Form 105 before entering or leaving the US with over USD 10,000", "The threshold applies to the total carried by a family or group at one time.", ["S14"]),
   ("Do not structure the cash to stay under the threshold", "Failure to report risks forfeiture and seizure, and structuring is itself an offence.", ["S14"]),
 ]),

 "m08": ("M08 — Sale of PRC property, then remit the after-tax proceeds", "The largest and slowest of the personal capital routes, and the one where the tax base matters most.", [
   ("Establish the acquisition cost and date", "PRC IIT on an asset transfer is charged on the gain, and the USD basis drives the §988 analysis.", ["S04", "S06"]),
   ("Settle PRC tax on the transfer", "The flat rate for income from transfer of assets is 20% of the taxable gain after the original value and reasonable expenses.", ["S04"]),
   ("Obtain the tax payment certificate", "This is the document the bank will want when the proceeds are converted.", ["S02"]),
   ("Apply the property-specific FX rules", "Property purchases by non-domestic individuals are governed by the separate property-market FX rules referenced in Art. 21 of the implementing rules.", ["S02"]),
   ("Convert and remit, keeping the sale file", "Sale contract, tax certificate, conversion slip and wire confirmation belong together.", ["S01", "S02"]),
 ]),

 "m09": ("M09 — Inheritance outbound transfer", "A procedure, not a rate. Expect multiple agencies and long timelines.", [
   ("Obtain the inheritance documents", "Notarised inheritance documents or the court instrument establishing your entitlement.", ["S02"]),
   ("Settle the estate's PRC tax position", "The certificate of tax payment is part of the file the bank and SAFE will review.", ["S02"]),
   ("Apply under the individual-property transfer procedure", "Art. 20 of the implementing rules refers emigration and foreign-inheritance transfers to the dedicated 2004 measures.", ["S02", "S17"]),
   ("Convert and remit after approval", "The approval, not the exchange rate, sets the timeline.", ["S01"]),
 ]),

 "m10": ("M10 — Emigrant asset transfer (former PRC residents)", "Only for people who actually emigrated from mainland China and can evidence it.", [
   ("Confirm eligibility", "You must be a former PRC resident with pre-emigration assets and a cancelled household registration; a lifetime US citizen does not qualify.", ["S02", "S17"]),
   ("Assemble proof of emigration and asset ownership", "Household-registration cancellation and ownership documents.", ["S02"]),
   ("Apply to SAFE for the transfer", "The transfer is approved rather than quoted.", ["S17"]),
 ]),

 "m11": ("M11 — The USD 50,000 annual quota (domestic individuals)", "The rule most often quoted online, and the one most often misapplied to US passport holders.", [
   ("Establish which category the bank will use", "Art. 9 of Decree 2006 No. 3 ties the annual limit to an individual's FX sales and to domestic individuals' purchases. Art. 52(2) of Decree 532 counts a foreigner resident in China for one year as 境内个人. Ask the bank in writing.", ["S01", "S11"]),
   ("Use it only for your own money", "Borrowing other people's quotas is the prohibited M18 route.", ["S01", "S11"]),
   ("Expect the system record", "Every quota transaction is recorded in the SAFE personal FX system, so the ceiling is enforced automatically.", ["S02"]),
 ]),

 "m12": ("M12 — Transfers between immediate relatives' FX accounts", "Lawful for genuine family support; unlawful the moment it is used to split one person's money.", [
   ("Establish the relationship", "Parents, children and spouse, with a household register, marriage certificate or notarised proof.", ["S02"]),
   ("Keep it domestic", "A transfer between a domestic and a non-domestic individual's account is treated as a cross-border transaction, not a family transfer.", ["S02"]),
   ("Do not use it to evade the annual limit", "Art. 7 of Decree 2006 No. 3 prohibits splitting to evade limits.", ["S01"]),
 ]),

 "m13": ("M13 — Employer pays your US account directly", "Usually the cleanest trail, because the employer already withholds and files.", [
   ("Confirm the employer will remit abroad", "This is a commercial decision by the employer, not a right.", ["S19"]),
   ("Keep the withholding records", "They are the proof that PRC tax was paid, which is what the bank and the IRS both need.", ["S04"]),
   ("Report the wage on your US return", "Worldwide income is reported; the foreign tax credit is claimed on Form 1116, subject to the limitation rules.", ["S13"]),
 ]),

 "m14": ("M14 — Dividend and profit repatriation", "Two tax layers before your money moves: corporate, then withholding.", [
   ("Distribute after corporate tax", "Only after-tax profits can be distributed.", ["S04"]),
   ("Settle withholding on the dividend", "The statutory rate for dividends is a flat 20%; a treaty rate may reduce it, but that was not re-verified here.", ["S04", "S16"]),
   ("File the outbound-payment tax record where required", "Prior sessions cited a filing before outbound payments above USD 50,000; not re-verified here.", ["S19"]),
   ("Remit with the resolution and tax certificates", "The bank will want the corporate and withholding records.", ["S01"]),
 ]),

 "m15": ("M15 — Equity transfer or liquidation proceeds", "Valuation is the usual battleground.", [
   ("Obtain a defensible valuation", "The taxable gain is the transfer price less the original investment and reasonable expenses.", ["S04"]),
   ("Settle PRC tax on the gain", "20% flat on the gain for an individual transferor.", ["S04"]),
   ("Register the change and remit", "Equity changes and capital-account remittances require registration before the money moves.", ["S11"]),
 ]),

 "m16": ("M16 — Genuine services, royalties or IP licensing", "Perfectly lawful when the work is real; a criminal exposure when it is not.", [
   ("Deliver the work and document it", "Deliverables, invoices and correspondence establish that the transaction is genuine.", ["S01"]),
   ("Settle withholding", "Royalties fall under the 20% flat category; services may be treated differently.", ["S04"]),
   ("File the outbound-payment tax record where required", "Prior-cited threshold: USD 50,000; not re-verified here.", ["S19"]),
   ("Never fabricate a contract", "That is the M21 violation, with the 30%-100% penalty scale.", ["S11"]),
 ]),

 "m17": ("M17 — Individual FX settlement accounts and licensed payment institutions", "A business channel, not a personal one.", [
   ("Register the business activity", "An individual FX settlement account requires foreign-trade registration or an equivalent licence.", ["S01", "S02"]),
   ("Keep business and personal funds separate", "Using a business channel for personal money is a violation, not an optimisation.", ["S01"]),
 ]),
}

CAPTIONS = {
 "none": "No annual USD cap is stated for this route; one documented operation can cover the whole amount.",
 "oneoff": "A single documented event; no published annual cap.",
 "perday": "Daily ceiling applies.",
 "peryear": "Annual ceiling applies.",
 "unverified": "No verified cap, or the cap is a personal fact not published anywhere.",
 "na": "This channel does not turn the balance into USD you can hold.",
 "illegal": "Prohibited. The 'cost' is a penalty of up to 30% of the amount, or 30%-100% if serious.",
}
