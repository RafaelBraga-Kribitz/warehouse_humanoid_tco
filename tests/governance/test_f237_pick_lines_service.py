"""F-237 — pick_lines_per_order scales line cycle times to per-order service."""

from __future__ import annotations

import math

import pytest
import yaml
from _ratchet import REPO_ROOT, ratchet

from warehouse_humanoid_tco.models.simulation import (
    AgentProfile,
    WarehouseScenario,
    predict_utilisation,
    scale_line_cycle_to_order,
)


def test_scale_helper_and_one_human_saturates() -> None:
    mean, std = scale_line_cycle_to_order(25.0, 8.0, 2.5)
    assert mean == pytest.approx(62.5)
    assert std == pytest.approx(8.0 * math.sqrt(2.5))

    scaled = WarehouseScenario(
        scenario_id="one-human-scaled",
        architecture="autostore",
        total_agents=1,
        agent_profiles=[
            AgentProfile(agent_type="human", cycle_time_mean=mean, cycle_time_std=std, count=1)
        ],
        order_arrival_rate_per_hour=120.0,
    )
    unscaled = WarehouseScenario(
        scenario_id="one-human-unscaled",
        architecture="autostore",
        total_agents=1,
        agent_profiles=[
            AgentProfile(agent_type="human", cycle_time_mean=25.0, cycle_time_std=8.0, count=1)
        ],
        order_arrival_rate_per_hour=120.0,
    )
    rho_scaled = predict_utilisation(scaled)
    rho_unscaled = predict_utilisation(unscaled)
    assert rho_unscaled < 1.0  # negative control: the pre-F-237 bug state
    ratchet(
        "F-237",
        fixed=rho_scaled > 1.0,
        gap_msg=f"scaled 1-human rho={rho_scaled:.3f} should exceed 1.0 at 120/hr",
    )


def test_lean_human_crew_at_least_three() -> None:
    cfg = yaml.safe_load(
        (REPO_ROOT / "config" / "autostore_baseline.yaml").read_text(encoding="utf-8")
    )
    lean = next(s for s in cfg["scenarios"] if s["id"] == "S-lean-human")
    n_human = int(lean["agent_counts"]["human"])
    ratchet(
        "F-237",
        fixed=n_human >= 3 and lean["agent_counts"].get("humanoid", 0) == 0,
        gap_msg=f"S-lean-human human={n_human} must be ≥3 after pick-lines scaling",
    )


def test_wiring_reads_pick_lines() -> None:
    mod02 = (
        REPO_ROOT / "src" / "warehouse_humanoid_tco" / "pipelines" / "module_02_simulation.py"
    ).read_text(encoding="utf-8")
    opt = (
        REPO_ROOT / "src" / "warehouse_humanoid_tco" / "analysis" / "crew_optimizer.py"
    ).read_text(encoding="utf-8")
    cfg = (REPO_ROOT / "config" / "autostore_baseline.yaml").read_text(encoding="utf-8")
    unmodeled = cfg.split("unmodeled_parameters:")[-1]
    wired = (
        "scale_line_cycle_to_order" in mod02
        and "pick_lines_per_order" in mod02
        and "scale_line_cycle_to_order" in opt
        and "operations.pick_lines_per_order" not in unmodeled
    )
    ratchet("F-237", fixed=wired, gap_msg="Module 2 / optimizer not wired to pick_lines scaling")


def test_pure_amr_policy_rejected() -> None:
    from warehouse_humanoid_tco.analysis.crew_optimizer import _normalise_policy

    try:
        _normalise_policy({"amr"})
        ok = False
    except ValueError:
        ok = True
    ratchet("F-237", fixed=ok, gap_msg="pure-AMR policy was not rejected")
