from __future__ import annotations

import csv
from pathlib import Path

from wiptally.cli import main

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples" / "sample_contracts.csv"


def _rows(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return {row["contract_id"]: row for row in csv.DictReader(handle)}


def test_sample_schedule_pins_the_worked_examples(tmp_path: Path) -> None:
    out = tmp_path / "wip-schedule.csv"
    code = main(["schedule", str(SAMPLE), "-o", str(out), "--as-at", "2026-08-31"])
    assert code == 2
    rows = _rows(out)
    assert len(rows) == 5

    hunter = rows["HUNTER-CIVIL-01"]
    assert hunter["revenue_to_date"] == "500000.00"
    assert hunter["contract_asset"] == "50000.00"
    assert hunter["contract_liability"] == "0.00"
    assert hunter["percent_complete"] == "0.5"

    faded = rows["HUNTER-CIVIL-02"]
    assert faded["revenue_to_date"] == "466666.67"
    assert faded["contract_liability"] == "33333.33"
    assert "profit_fade" in faded["flags"]
    assert "stale_cost_to_complete" in faded["flags"]

    mine = rows["MINE-ROM-01"]
    assert mine["transaction_price"] == "2200000.00"
    assert mine["variable_consideration_excluded"] == "300000.00"
    assert mine["revenue_to_date"] == "1650000.00"

    power = rows["POWER-CIVIL-01"]
    assert power["revenue_to_date"] == "371000.00"
    assert power["contract_asset"] == "71000.00"
    assert "onerous_contract_review_aasb_137" in power["flags"]

    early = rows["EXPLORATORY-01"]
    assert early["revenue_to_date"] == "100000.00"
    assert early["percent_complete"] == "0.00"


def test_portfolio_totals_are_not_netted(tmp_path: Path) -> None:
    out = tmp_path / "wip-schedule.csv"
    main(["schedule", str(SAMPLE), "-o", str(out), "--as-at", "2026-08-31"])
    rows = _rows(out)
    assets = sum(float(row["contract_asset"]) for row in rows.values())
    liabilities = sum(float(row["contract_liability"]) for row in rows.values())
    # The test uses float only to assert the two sides both exist. The engine
    # never does. A netted  one-line "WIP" figure would cancel these.
    assert assets > 0
    assert liabilities > 0


def test_refuses_to_overwrite_the_source(tmp_path: Path) -> None:
    source = tmp_path / "contracts.csv"
    source.write_text(SAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
    assert main(["schedule", str(source), "-o", str(source)]) == 1


def test_review_pack_binds_source_hash(tmp_path: Path) -> None:
    schedule = tmp_path / "wip-schedule.csv"
    pack = tmp_path / "practitioner-review.md"
    assert main(["schedule", str(SAMPLE), "-o", str(schedule), "--as-at", "2026-08-31"]) == 2
    assert main(
        [
            "review-pack",
            str(schedule),
            "--source",
            str(SAMPLE),
            "-o",
            str(pack),
            "--as-at",
            "2026-08-31",
        ]
    ) == 2
    text = pack.read_text(encoding="utf-8")
    assert "AASB 15" in text
    assert "Do not offset the two sides." in text
    assert "HUNTER-CIVIL-02" in text
    assert "Source SHA-256" in text


def test_mapping_file_renames_columns(tmp_path: Path) -> None:
    contracts = tmp_path / "jobs.csv"
    contracts.write_text(
        "Job,Contract sum,Cost to date,ETC,Certified to date,committed_outstanding\n"
        "MAP-1,1000.00,400.00,400.00,450.00,380.00\n",
        encoding="utf-8",
    )
    mapping = tmp_path / "map.json"
    mapping.write_text(
        ROOT.joinpath("examples", "mapping.example.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    out = tmp_path / "wip-schedule.csv"
    assert main(
        ["schedule", str(contracts), "-o", str(out), "--mapping-file", str(mapping)]
    ) == 0
    rows = _rows(out)
    assert rows["MAP-1"]["revenue_to_date"] == "500.00"
    assert rows["MAP-1"]["contract_asset"] == "50.00"
