"""Shared model for the CNY->USD cost-increment analysis.
Computes every figure programmatically; nothing is hand-typed into the tables.
All constants cite their official source in build.py."""
import math

RATE_CNY_PER_USD = 6.6538  # Federal Reserve H.10, week of Oct 26-30 2026, Oct 30 noon buying rate (CNY per USD)
CABLE_CNY = 120            # HSBC China Tariff eff. 2026-10-31, item 2.2.4.2 (Premier/Advance)
ISSUANCE_MIN_CNY = 100     # item 2.2.4.1
ISSUANCE_MAX_CNY = 500     # item 2.2.4.1 (Premier/Advance)
ISSUANCE_RATE = 0.001      # 0.1% of remittance amount, item 2.2.4.1
RECEIVING_USD = 15         # Chase published schedule example: incoming wires $15/transfer (varies by account type; other banks unverified)
ANNUAL_QUOTA_USD = 50_000  # SAFE Detailed Rules: USD 50,000 per individual per calendar year (SAFE 2007 Q&A)
CARD_ANNUAL_CAP_RMB = 100_000     # SAFE Huifa 2017 (see repo data/china-rules.json; cross-border card cash withdrawals)
CARD_DAILY_CAP_RMB = 10_000       # same circular, per card per day
DIVIDEND_WHT = 0.10        # US-China treaty Arts. 9/10/11/12- equivalent 10% cap on dividends/interest/royalties (beneficial owner)
IIT_INTEREST_DIVIDENDS = 0.20  # PRC IIT Law Art. 3(3), flat 20% (resident & non-resident alike)
STEP = 10_000
INCREMENTS = list(range(STEP, 400_000 + STEP, STEP))

def wire_fee_cny(a_usd):
    cny = a_usd * RATE_CNY_PER_USD
    issuance = min(ISSUANCE_MAX_CNY, max(ISSUANCE_MIN_CNY, ISSUANCE_RATE * cny))
    return issuance, issuance + CABLE_CNY

def usd(cny):
    return cny / RATE_CNY_PER_USD

def quota_years(a_usd):
    return math.ceil(a_usd / ANNUAL_QUOTA_USD) if a_usd else 0

def row(a):
    issuance_cny, total_cny = wire_fee_cny(a)
    wire_usd = usd(total_cny)
    subtotal = wire_usd + RECEIVING_USD
    return {
        "usd": a,
        "cny": round(a * RATE_CNY_PER_USD, 2),
        "issuance_cny": round(issuance_cny, 2),
        "cable_cny": CABLE_CNY,
        "wire_fee_cny": round(total_cny, 2),
        "wire_fee_usd": round(wire_usd, 2),
        "receiving_usd": RECEIVING_USD,
        "known_subtotal_usd": round(subtotal, 2),
        "known_pct": round(100 * subtotal / a, 3),
        "dividend_wht_usd": round(a * DIVIDEND_WHT, 2),
        "quota_years": quota_years(a),
        "within_one_year_quota": a <= ANNUAL_QUOTA_USD,
    }

ROWS = [row(a) for a in INCREMENTS]

if __name__ == "__main__":
    for r in ROWS:
        print(f"${r['usd']:>7,}  CNY {r['cny']:>13,.2f}  wire ${r['wire_fee_usd']:>6.2f}  known ${r['known_subtotal_usd']:>7.2f} ({r['known_pct']}%)  quota yrs {r['quota_years']}")
