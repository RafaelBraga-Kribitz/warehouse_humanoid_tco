"""F-245 — direct regression guards for the two bugs found in the August 2026 code audit.

Bug 1 (fixed in fb5b1c7, 2026-05-22): ``pick_order`` had a ``return`` inside its
``for profile in scenario.agent_profiles`` loop, so every order went to the first agent
profile and the other agent types never worked.

Bug 2 (fixed across 191fbcb and d804785): the TCO pipeline did not carry simulated
throughput into its outputs and chose each crew by matching fragments of the scenario
name instead of reading the configured crew counts.

The older guard for Bug 1 compares two scenarios' throughput, which only fails when a
slow agent type is listed second. Nothing guarded Bug 2: reintroducing either half of it
left the full suite green (checked by mutation on 2026-10-26). These tests fail on the
buggy code and pass on the fixed code.
"""

from __future__ import annotations

import copy
import shutil
from pathlib import Path

import polars as pl
import yaml

from warehouse_humanoid_tco.models.simulation import AgentProfile, WarehouseScenario, run_scenario
from warehouse_humanoid_tco.pipelines.module_03_tco import (
    _composition_from_config,
    build_financial_params,
    compute_tco_scenario,
    module_03_main,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


# ── Bug 1: routing ─────────────────────────────────────────────────────────────


def _two_type_scenario(first: str, second: str) -> WarehouseScenario:
    return WarehouseScenario(
        scenario_id="routing-guard",
        architecture="autostore",
        total_agents=8,
        agent_profiles=[
            AgentProfile(first, 60.0, 15.0, count=4, seed=42),
            AgentProfile(second, 60.0, 15.0, count=4, seed=42),
        ],
        order_arrival_rate_per_hour=120.0,
        shift_hours=8.0,
        seed=42,
    )


def test_every_agent_type_with_staff_receives_orders() -> None:
    """With equal counts and speeds, both agent types must do a similar share of the work."""
    result = run_scenario(_two_type_scenario("human", "amr"), run_id=0)
    human = result["utilization_human"]
    amr = result["utilization_amr"]
    assert human > 0 and amr > 0, f"an agent type received no orders: human={human}, amr={amr}"
    # Count-weighted routing sends each type about half the orders; first-profile routing
    # sends all of them to one type. A 0.5 to 2.0 ratio separates the two cleanly.
    assert 0.5 < human / amr < 2.0, f"routing is lopsided: human={human:.3f}, amr={amr:.3f}"


def test_routing_does_not_depend_on_profile_order() -> None:
    """Listing the profiles in the other order must not starve the second type."""
    result = run_scenario(_two_type_scenario("amr", "human"), run_id=0)
    assert result["utilization_human"] > 0
    assert result["utilization_amr"] > 0


# ── Bug 2: TCO pipeline wiring ─────────────────────────────────────────────────


def _project_with_config(tmp_path: Path, throughput: float) -> Path:
    """A scratch project that uses the repository's real config and synthetic runs."""
    (tmp_path / "config").mkdir(parents=True)
    (tmp_path / "data" / "processed").mkdir(parents=True)
    (tmp_path / "reports").mkdir(parents=True)
    for name in ("tco_assumptions.yaml", "autostore_baseline.yaml"):
        shutil.copy(REPO_ROOT / "config" / name, tmp_path / "config" / name)
    scenario_ids = [s["id"] for s in _sim_config()["scenarios"]]
    pl.DataFrame(
        {
            "scenario_id": [sid for sid in scenario_ids for _ in range(3)],
            "run_id": [i for _ in scenario_ids for i in range(3)],
            "throughput_orders_per_shift": [throughput] * (3 * len(scenario_ids)),
        }
    ).write_parquet(tmp_path / "data" / "processed" / "simulation_runs.parquet")
    return tmp_path


def _sim_config() -> dict:
    return yaml.safe_load((REPO_ROOT / "config" / "autostore_baseline.yaml").read_text())


def _results(project: Path) -> dict[str, dict]:
    module_03_main(project)
    frame = pl.read_parquet(project / "data" / "processed" / "tco_scenarios.parquet")
    return {row["scenario_id"]: row for row in frame.to_dicts()}


def test_cost_per_order_uses_simulated_throughput(tmp_path: Path) -> None:
    """Doubling simulated throughput must halve cost per order and leave NPV unchanged.

    NPV is a cost model at fixed demand, so it does not depend on throughput by design;
    throughput enters through cost per order. If the pipeline ignored the simulation
    (the August bug), cost per order would not move.
    """
    low = _results(_project_with_config(tmp_path / "low", 900.0))
    high = _results(_project_with_config(tmp_path / "high", 1800.0))
    for scenario_id, row in low.items():
        assert row["throughput_mean_orders_per_shift"] == 900.0
        assert high[scenario_id]["throughput_mean_orders_per_shift"] == 1800.0
        ratio = row["cost_per_order_eur"] / high[scenario_id]["cost_per_order_eur"]
        assert abs(ratio - 2.0) < 1e-9, f"{scenario_id}: cost per order ignores throughput"
        assert row["npv_eur"] == high[scenario_id]["npv_eur"]


def test_pipeline_npv_uses_configured_crew_counts(tmp_path: Path) -> None:
    """Each scenario's NPV must come from its agent_counts in config, not from its name."""
    results = _results(_project_with_config(tmp_path, 950.0))
    sim_config = _sim_config()
    params = build_financial_params(
        yaml.safe_load((REPO_ROOT / "config" / "tco_assumptions.yaml").read_text()), sim_config
    )
    total_agents = sim_config.get("total_agents", 8)
    for scenario in sim_config["scenarios"]:
        expected = compute_tco_scenario(
            scenario["id"],
            {"throughput_orders_per_shift": 950.0},
            params,
            baseline_annual_opex=0.0,
            composition=_composition_from_config(scenario, total_agents),
        )
        assert abs(results[scenario["id"]]["npv_eur"] - expected["npv_eur"]) < 1e-6, scenario["id"]


def test_changing_crew_counts_in_config_changes_npv(tmp_path: Path) -> None:
    """Editing one scenario's crew in config must move that scenario's NPV."""
    base = _results(_project_with_config(tmp_path / "base", 950.0))
    edited_project = _project_with_config(tmp_path / "edited", 950.0)
    config_path = edited_project / "config" / "autostore_baseline.yaml"
    config = copy.deepcopy(_sim_config())
    target = next(s for s in config["scenarios"] if s["agent_counts"].get("humanoid", 0) > 0)
    target["agent_counts"]["humanoid"] += 1
    config_path.write_text(yaml.safe_dump(config, sort_keys=False))
    edited = _results(edited_project)
    assert edited[target["id"]]["npv_eur"] < base[target["id"]]["npv_eur"]
