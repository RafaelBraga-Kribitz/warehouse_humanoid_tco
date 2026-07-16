"""F-212 — lean all-human comparator remains correctly sized and published."""

from __future__ import annotations

import csv
from pathlib import Path

import yaml
from _ratchet import ratchet

from warehouse_humanoid_tco.models.simulation import (
    AgentProfile,
    WarehouseScenario,
    predict_utilisation,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _lean_scenario() -> tuple[dict, dict]:
    config = yaml.safe_load((REPO_ROOT / "config" / "autostore_baseline.yaml").read_text())
    scenario = next(
        (candidate for candidate in config["scenarios"] if candidate.get("id") == "S-lean-human"),
        None,
    )
    assert scenario is not None
    return config, scenario


def test_lean_human_is_sized_to_the_utilisation_rule() -> None:
    config, entry = _lean_scenario()
    counts = entry.get("agent_counts", {})
    human_count = counts.get("human", 0)
    valid_composition = (
        entry.get("human_fraction") == 1.0
        and human_count <= 7
        and counts.get("humanoid") == 0
        and counts.get("amr") == 0
    )
    human = config["agents"]["human"]
    operations = config["operations"]
    scenario = WarehouseScenario(
        scenario_id="S-lean-human",
        architecture=config["architecture"],
        total_agents=human_count,
        agent_profiles=[
            AgentProfile(
                "human",
                human["cycle_time_mean_seconds"],
                human["cycle_time_std_seconds"],
                human_count,
            )
        ],
        order_arrival_rate_per_hour=operations["order_arrival_rate_per_hour"],
        shift_hours=operations["shift_hours"],
    )
    ratchet(
        "F-212",
        fixed=valid_composition and predict_utilisation(scenario) <= 0.85,
        gap_msg="S-lean-human is absent, non-human, oversized, or exceeds rho <= 0.85",
    )


def test_lean_human_is_in_published_tco_and_readme() -> None:
    with (REPO_ROOT / "exports" / "tableau_public" / "tco_scenarios.csv").open(
        newline=""
    ) as handle:
        csv_ids = {row["scenario_id"] for row in csv.DictReader(handle)}
    readme = (REPO_ROOT / "README.md").read_text()
    ratchet(
        "F-212",
        fixed="S-lean-human" in csv_ids and "S-lean-human" in readme,
        gap_msg="S-lean-human is missing from the Tableau TCO CSV or README",
    )
