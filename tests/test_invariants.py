from __future__ import annotations

import ast
from decimal import Decimal
from pathlib import Path

from wiptally.csv_io import load_mapping, read_contracts
from wiptally.csvsafe import guard
from wiptally.model import Schedule
from wiptally.schedule import measure

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples" / "sample_contracts.csv"
ENGINE = ROOT / "wiptally"


def test_money_fields_are_decimal_not_float() -> None:
    contracts = read_contracts(SAMPLE, load_mapping(None))
    for contract in contracts:
        position = measure(contract)
        for name, value in vars(position).items():
            if isinstance(value, float):
                raise AssertionError(f"{name} is a float")
            if isinstance(value, Decimal):
                assert type(value) is Decimal


def test_engine_source_does_not_call_float() -> None:
    banned = {"float"}
    for path in ENGINE.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in banned:
                raise AssertionError(f"{path.name} names float()")
            if isinstance(node, ast.Constant) and isinstance(node.value, float):
                raise AssertionError(f"{path.name} contains a float literal")


def test_formula_injection_is_escaped() -> None:
    assert guard("=cmd") == "'=cmd"
    assert guard("-00123") == "-00123"
    assert guard("-A1") == "'-A1"


def test_schedule_totals_do_not_net() -> None:
    contracts = read_contracts(SAMPLE, load_mapping(None))
    schedule = Schedule(
        as_at="2026-08-31",
        positions=[measure(contract) for contract in contracts],
        source_name=SAMPLE.name,
    )
    assert schedule.total_contract_assets > 0
    assert schedule.total_contract_liabilities > 0
    net = schedule.total_contract_assets - schedule.total_contract_liabilities
    assert net != schedule.total_contract_assets
    assert net != schedule.total_contract_liabilities
