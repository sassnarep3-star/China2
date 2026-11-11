#!/usr/bin/env python3
"""Cost engine for verify-ace15295.

Every input below was read by this session from the publisher's own page on
2026-11-11 and is recorded with its source id in data/sources.json. Nothing is
assumed, and anything not published is None -> rendered blank and flagged.

Arithmetic only. No personal tax liability is computed or asserted.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"

# ---------------------------------------------------------------- inputs ----
# Bank FX boards: CNY per 100 units of foreign currency, as published.
# "buy" = the rate at which the BANK buys USD from you (you sell USD);
# "sell" = the rate at which the BANK sells USD to you (you buy USD).
BOARDS = {
    # id: (label, buy, sell, as_of, source)
    "BOC": ("Bank of China", 666.30, 669.11, "2026-11-11 10:25:02 Beijing", "S24"),
    "CMB": ("China Merchants Bank", 666.295, 669.199, "2026-11-10 10:28:44 Beijing", "S26"),
    "HSBC": ("HSBC China", 664.11822, 670.79204, "2026-11-10 (page date)", "S27"),
}

# Published personal outward-remittance tariffs (telegraphic transfer).
# fee_bp: basis points of the remitted amount; min/max in CNY; cable in CNY.
TARIFFS = {
    "BOC": {
        "label": "Bank of China (electronic banking personal tariff)",
        "fee_bp": 10,            # 1 per mille
        "min_cny": 50, "max_cny": 260,
        "cable_cny": 150,        # non-HK/Macao/Taiwan destination
        "source": "S25",
        "note": "1 per mille, min CNY 50 / max CNY 260, plus CNY 150 cable for non-HK/Macao/Taiwan.",
    },
    "HSBC_PREMIER": {
        "label": "HSBC China - Premier",
        "fee_bp": 10,
        "min_cny": 100, "max_cny": 500,
        "cable_cny": 120,
        "source": "S28",
        "note": "Prepaid as 0.1%, min CNY 100 / max CNY 500 (item 2.2.4.1) plus CNY 120 cable (item 2.2.4.2).",
    },
    "HSBC_PRIVATE": {
        "label": "HSBC China - Private Banking",
        "fee_bp": 0,
        "min_cny": 0, "max_cny": 0,
        "cable_cny": 0,
        "source": "S28",
        "note": "Individual customer: telegraphic transfer issuance free, cable free (items 2.2.4.1-2.2.4.2). Tariff note 7 excludes other institutions' charges.",
    },
    "HSBC_GLOBAL": {
        "label": "HSBC China - Global Transfer to own overseas HSBC account",
        "flat_usd": 20.0,        # Advance: "actual charge per transaction will be USD20"
        "fee_bp": 0, "min_cny": 0, "max_cny": 0, "cable_cny": 0,
        "source": "S28",
        "note": "Item 2.2.6.1: free for Private Banking and Premier; Advance is USD 20 actual per transaction (CNY 145 indicative).",
    },
}

# Illustrative tax-layer inputs (never a personal liability).
US = {
    "single": {  # 2026, Rev. Proc. 2025-32 Table 3
        "brackets": [(12400, .10), (50400, .12), (105700, .22), (201775, .24),
                     (256225, .32), (640600, .35), (float("inf"), .37)],
        "std_deduction": 16100,
    },
    "mfj": {  # Table 1
        "brackets": [(24800, .10), (100800, .12), (211400, .22), (403550, .24),
                     (512450, .32), (768700, .35), (float("inf"), .37)],
        "std_deduction": 32200,
    },
    "source": "S22",
}
SEC988_PERSONAL_THRESHOLD = 200.0   # 26 U.S.C. 988(e)(2) / Pub. 525  -> S20, S19
PRC_IIT = {
    "comprehensive_max": 0.45, "flat_other": 0.20,
    "note": "PRC IIT Law Art. 3: comprehensive income 3%-45%; interest, dividends, rent, property transfer 20%. A tax on the income, not on the conversion.",
    "source": "S31",
}

TIERS = [10_000 * i for i in range(1, 41)]   # USD 10,000 .. 400,000


def board_mid(buy: float, sell: float) -> float:
    return (buy + sell) / 2.0


def half_spread(buy: float, sell: float) -> float:
    """Effective cost of crossing the published spread, as a fraction of mid."""
    return (sell - buy) / 2.0 / board_mid(buy, sell)


def tariff_fee_cny(code: str, usd: float, sell_cny_per_usd: float) -> float | None:
    t = TARIFFS[code]
    if "flat_usd" in t:
        return t["flat_usd"] * sell_cny_per_usd
    fee = usd * sell_cny_per_usd * t["fee_bp"] / 10_000.0
    fee = max(fee, t["min_cny"])
    fee = min(fee, t["max_cny"])
    return fee + t["cable_cny"]


def route_rows(bank: str, tariff: str) -> list[dict]:
    """Documented current-account conversion at one bank with its own tariff."""
    label, buy, sell, as_of, src = BOARDS[bank]
    sell_rate = sell / 100.0            # CNY per USD the bank sells at
    mid = board_mid(buy, sell) / 100.0
    hs = half_spread(buy, sell)
    rows = []
    for usd in TIERS:
        cny_needed = usd * sell_rate
        # Extra CNY paid over mid, expressed as dollars at the same selling rate:
        # a fraction (sell-mid)/sell of the dollars actually delivered.
        spread_cost_cny = usd * (sell_rate - mid)
        fee_cny = tariff_fee_cny(tariff, usd, sell_rate)
        total_cny = spread_cost_cny + (fee_cny or 0.0)
        total_usd = total_cny / sell_rate
        pct = total_usd / usd * 100.0
        rows.append(dict(
            usd=usd, bank=bank, route_id="R1", tariff=tariff,
            rate=sell_rate, mid=mid, half_spread_pct=hs * 100.0,
            cny_needed=cny_needed, spread_usd=spread_cost_cny / sell_rate,
            fee_usd=(fee_cny / sell_rate) if fee_cny is not None else None,
            fee_cny=fee_cny, total_usd=total_usd, pct=pct,
            board_as_of=as_of, rate_source=src,
            fee_source=TARIFFS[tariff]["source"],
        ))
    return rows


def prc_iit_illustration(income_cny: float) -> dict:
    """Flat 20% illustration for interest/dividend/rent/property-transfer income.

    Deliberately the simplest published line (PRC IIT Law Art. 3(3)). The
    progressive 3%-45% table depends on deductions that are unknown, so it is
    not applied here.
    """
    return dict(income_cny=income_cny, rate=PRC_IIT["flat_other"],
                tax_cny=income_cny * PRC_IIT["flat_other"], source=PRC_IIT["source"])


def us_tax_on_gain(gain_usd: float, status: str = "single",
                   other_taxable: float = 0.0) -> dict:
    """Statutory-rate illustration of U.S. tax on an ordinary §988 gain.

    Uses the 2026 brackets on (other taxable income + gain) minus tax on other
    taxable income alone. Not a return, not advice: basis, residency, filing
    status and other income are all unknown for the user.
    """
    b = US[status]
    def tax(t):
        t = max(t, 0.0); prev = 0.0; acc = 0.0
        for cap, rate in b["brackets"]:
            if t > prev:
                acc += (min(t, cap) - prev) * rate
                prev = cap
            else:
                break
        return acc
    if gain_usd <= SEC988_PERSONAL_THRESHOLD:
        return dict(taxable=False, tax_usd=0.0, marginal=0.0,
                    rule="gain does not exceed USD 200; personal-transaction exclusion applies",
                    source="S20")
    base = tax(other_taxable)
    total = tax(other_taxable + gain_usd)
    return dict(taxable=True, tax_usd=total - base,
                marginal=(total - base) / gain_usd * 100.0,
                rule="gain exceeds USD 200; 988(e)(2) exclusion does not apply; ordinary treatment under 988(a)(1)(A)",
                source="S20")


def build() -> dict:
    routes = []
    for bank, tariff in [("BOC", "BOC"),
                         ("HSBC", "HSBC_PREMIER"),
                         ("HSBC", "HSBC_PRIVATE"),
                         ("HSBC", "HSBC_GLOBAL"),
                         ("CMB", None)]:
        if tariff is None:
            # rate board captured, fee schedule not captured -> fee and total blank
            label, buy, sell, as_of, src = BOARDS[bank]
            sell_rate = sell / 100.0
            mid = board_mid(buy, sell) / 100.0
            for usd in TIERS:
                routes.append(dict(
                    usd=usd, bank=bank, route_id="R1", tariff="UNPUBLISHED",
                    rate=sell_rate, mid=mid,
                    half_spread_pct=half_spread(buy, sell) * 100.0,
                    cny_needed=usd * sell_rate,
                    spread_usd=usd * (sell_rate - mid) / sell_rate,
                    fee_usd=None, fee_cny=None, total_usd=None, pct=None,
                    board_as_of=as_of, rate_source=src, fee_source=None))
        else:
            routes.extend(route_rows(bank, tariff))

    penalties = []
    for usd in TIERS:
        import math
        penalties.append(dict(
            usd=usd,
            # (1) PRC spread, shoppable: best published half-spread vs worst, at this tier
            spread_best_usd=usd * min(half_spread(*BOARDS[b][1:3]) for b in BOARDS),
            spread_worst_usd=usd * max(half_spread(*BOARDS[b][1:3]) for b in BOARDS),
            # (2) sender fee, published: BOC tariff at tier vs HSBC Private (free)
            fee_boc_usd=tariff_fee_cny("BOC", usd, BOARDS["BOC"][2] / 100.0) / (BOARDS["BOC"][2] / 100.0),
            fee_zero_usd=0.0,
            # (3) tax recordal: rateable at zero until a published fee is found
            recordal_usd=None,
            # (4) PRC IIT on income: flat 20% illustration on the CNY equivalent
            prc_iit_usd=usd * PRC_IIT["flat_other"],
            # (5) U.S. currency gain: needs a basis, so blank
            us_988_gain_usd=None,
            # (6) U.S. reporting penalty maxima, from the official table
            fbar_nonwillful_max_usd=16536.0,
            fbar_willful_max_usd=165353.0,
            # (7) unlawful-route exposure under Regulation 532, 30% of the amount
            unlawful_30pct_usd=usd * 0.30,
            unlawful_max_usd=usd * 1.00,
        ))

    # Reconversion ceiling: CNY 200,000 one-off (Announcement 2004 No.16 Art.6)
    reconv = dict(
        cny_cap=200_000.0,
        usd_cap_at_boc=200_000.0 / (BOARDS["BOC"][2] / 100.0),
        source="S11",
        note="Emigrant/inheritance transfer of the equivalent of CNY 200,000 or less may be remitted in one go after approval; above that it is staged over two years and above CNY 500,000 needs SAFE headquarters approval.",
    )

    out = dict(
        meta=dict(
            project="verify-ace15295", computed="2026-11-11",
            tiers=len(TIERS), tier_min=TIERS[0], tier_max=TIERS[-1],
            route_rows=len(routes),
            rule="All figures are arithmetic on published inputs captured 2026-11-11. Boards are reference rates carrying the publisher's own disclaimer, so every total is a LOWER BOUND. Blank = the input is not published and was not inferred.",
            tiers_note="USD amount is the amount the beneficiary should receive; CNY needed is computed at the bank's published selling rate.",
        ),
        boards={k: dict(label=v[0], buy=v[1], sell=v[2], as_of=v[3], source=v[4],
                        mid=board_mid(v[1], v[2]),
                        half_spread_pct=half_spread(v[1], v[2]) * 100.0,
                        sell_cny_per_usd=v[2] / 100.0)
                for k, v in BOARDS.items()},
        tariffs={k: dict(v) for k, v in TARIFFS.items()},
        routes=routes, penalties=penalties, reconversion=reconv,
        cheapest_by_tier={t: min([r for r in routes if r["usd"] == t and r["total_usd"]],
                                 key=lambda r: r["total_usd"])["tariff"]
                          for t in TIERS},
        us=dict(tax=US, sec988_threshold=SEC988_PERSONAL_THRESHOLD,
                illo_6227_gain=us_tax_on_gain(6226.68, "single", 0.0),
                illo_50k_gain=us_tax_on_gain(50_000.0, "single", 0.0),
                illo_400k_gain=us_tax_on_gain(400_000.0, "single", 0.0),
                illo_small_gain=us_tax_on_gain(150.0, "single", 0.0)),
        prc_iit=dict(PRC_IIT, illo_400k=prc_iit_illustration(400_000 * BOARDS["BOC"][2] / 100.0)),
    )
    DATA.mkdir(exist_ok=True)
    (DATA / "costs.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


if __name__ == "__main__":
    d = build()
    print("route rows:", len(d["routes"]), "| tiers:", d["meta"]["tiers"])
    for k, v in d["boards"].items():
        print(f"  {k:5s} sell {v['sell_cny_per_usd']:.4f}  half-spread {v['half_spread_pct']:.4f}%")
    for r in d["routes"]:
        if r["usd"] in (10_000, 400_000):
            t = "blank" if r["total_usd"] is None else f"${r['total_usd']:,.2f} ({r['pct']:.3f}%)"
            print(f"  {r['bank']:5s} {r['tariff']:14s} ${r['usd']:>7,} -> {t}")
