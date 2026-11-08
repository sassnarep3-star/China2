#!/usr/bin/env python3
"""Deterministic U.S. currency-basis workbook model.

No personal facts or commercial quotes are invented. The only computed numeric
column is a labeled CNY reference amount using an official Treasury reporting
rate. Tax, gain, basis, fees and total cost remain blank until verified inputs
exist.
"""
from __future__ import annotations

import csv
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def money(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def build_rows() -> list[dict]:
    inputs = load("inputs.json")
    rate = Decimal(inputs["reference_rate"]["value"])
    start = int(inputs["target_usd_start"])
    end = int(inputs["target_usd_end"])
    step = int(inputs["target_usd_step"])
    if step <= 0 or (end - start) % step != 0:
        raise ValueError("invalid increment configuration")

    rows = []
    for index, target in enumerate(range(start, end + 1, step), start=1):
        usd = Decimal(target)
        rows.append(
            {
                "row_id": f"W{index:03d}",
                "target_usd": target,
                "total_cost_usd": "",
                "federal_tax_usd": "",
                "execution_fees_usd": "",
                "cny_reference": money(usd * rate),
                "acquisition_basis_usd": "",
                "realized_gain_usd": "",
                "taxable_gain_usd": "",
                "status": "unverified-costs; reference computation only",
                "source_ids": ["S02", "S01", "S12", "S09"],
            }
        )
    return rows


def write_outputs() -> None:
    inputs = load("inputs.json")
    sources = {s["id"]: s for s in load("sources.json")}
    rows = build_rows()
    payload = {
        "scenario": inputs["scenario"],
        "as_of_utc": inputs["as_of_utc"],
        "reference_rate": inputs["reference_rate"],
        "personal_gain_exclusion_usd": inputs["personal_gain_exclusion_usd"],
        "unknown_personal_facts": inputs["unknown_personal_facts"],
        "rows": rows,
    }
    (DATA / "workbook.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    fields = [
        "row_id",
        "target_usd",
        "total_cost_usd",
        "federal_tax_usd",
        "execution_fees_usd",
        "cny_reference",
        "acquisition_basis_usd",
        "realized_gain_usd",
        "taxable_gain_usd",
        "status",
        "source_ids",
        "source_urls",
    ]
    with (DATA / "workbook.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            out = dict(row)
            out["source_ids"] = ";".join(row["source_ids"])
            out["source_urls"] = " | ".join(sources[s]["url"] for s in row["source_ids"])
            writer.writerow(out)


if __name__ == "__main__":
    write_outputs()
    print(f"Wrote {len(build_rows())} workbook rows to {DATA / 'workbook.json'} and workbook.csv")
