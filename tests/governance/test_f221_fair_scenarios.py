"""F-221 — fair optimizer-sized scenario verification."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import polars as pl
import pytest
import yaml

from _ratchet import ratchet
from warehouse_humanoid_tco.analysis.crew_optimizer import (
    module_02_humanoid_cycle_overrides,
    optimize_crew,
)

ROOT = Path(__file__).resolve().parents[2]
CONFIG = yaml.safe_load((ROOT / "config" / "autostore_baseline.yaml").read_text())
ASSUMPTIONS = yaml.safe_load((ROOT / "config" / "tco_assumptions.yaml").read_text())
LAMBDA_PER_HOUR = CONFIG["operations"]["order_arrival_rate_per_hour"]
SCENARIOS = {scenario["id"]: scenario for scenario in CONFIG["scenarios"]}


def _module_02_cycle_time_override() -> dict[str, tuple[float, float]]:
    """Reproduce Module 2's empirical per-order humanoid cycle time (F-237)."""
    return module_02_humanoid_cycle_overrides(CONFIG, ROOT)


@pytest.mark.parametrize(
    ("scenario_id", "policy", "kwargs"),
    [
        ("S-lean-human", {"human"}, {}),
        ("S-pure-humanoid", {"humanoid"}, {}),
        (
            "S-hybrid-5050",
            {"human", "humanoid"},
            {"balance_agent_types": ("human", "humanoid")},
        ),
        ("S-hybrid-amr", {"human", "humanoid", "amr"}, {}),
        (
            "S-future-2028",
            {"human", "humanoid"},
            {"humanoid_throughput_multiplier": 1.30},
        ),
    ],
)
def test_scenario_counts_match_fair_optimizer(
    scenario_id: str, policy: set[str], kwargs: dict[str, object]
) -> None:
    """Each non-legacy row is a minimum-cost crew with per-class rho <= 0.85."""
    result = optimize_crew(
        policy,
        CONFIG,
        ASSUMPTIONS,
        LAMBDA_PER_HOUR,
        require_each_policy_class=True,
        cycle_time_overrides=_module_02_cycle_time_override(),
        **kwargs,
    )["best"]
    assert SCENARIOS[scenario_id]["agent_counts"] == result["agent_counts"]
    assert all(result["class_rho"][agent_type] <= 0.85 for agent_type in policy)


def test_legacy_baseline_is_explicit_and_exports_are_synchronised() -> None:
    """Keep the eight-human reference while requiring its label and exact exports."""
    assert SCENARIOS["S-baseline-human"]["agent_counts"] == {
        "human": 8,
        "humanoid": 0,
        "amr": 0,
    }
    config_text = (ROOT / "config" / "autostore_baseline.yaml").read_text()
    assert "legacy overstaffed baseline" in config_text

    parquet = pl.read_parquet(ROOT / "data" / "processed" / "tco_scenarios.parquet")
    with (ROOT / "exports" / "tableau_public" / "tco_scenarios.csv").open(newline="") as handle:
        csv_rows = {row["scenario_id"]: row for row in csv.DictReader(handle)}
    assert set(parquet["scenario_id"].to_list()) == set(csv_rows)
    for row in parquet.iter_rows(named=True):
        assert float(csv_rows[row["scenario_id"]]["npv_eur"]) == pytest.approx(row["npv_eur"])


def test_f221_artifacts_document_the_new_headline() -> None:
    """The decision, effect chart, and golden master remain auditable."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    adr = (ROOT / "governance" / "adrs" / "0014-fair-scenario-redesign.md").read_text(
        encoding="utf-8"
    )
    goldens = json.loads((ROOT / "tests" / "golden" / "golden_masters.json").read_text())
    fixed = (
        (ROOT / "reports" / "executive_charts" / "06_effect_decomposition.png").exists()
        and "S-lean-human is cheapest" in readme
        and "Old headline" in adr
        and "New headline" in adr
        and goldens["data/processed/tco_scenarios.parquet"]["finding"] == "F-237"
        and goldens["data/processed/simulation_capacity_ceiling.parquet"]["finding"] == "F-237"
    )
    ratchet("F-221", fixed=fixed, gap_msg="fair-scenario outputs or evidence are incomplete")
