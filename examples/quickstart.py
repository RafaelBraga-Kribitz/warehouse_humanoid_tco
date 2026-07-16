"""Run a synthetic TCO calculation without the repository data directory."""
from __future__ import annotations

from pathlib import Path

import yaml

from warehouse_humanoid_tco.pipelines.module_03_tco import compute_tco_scenario


def main() -> None:
    config = yaml.safe_load(
        (Path(__file__).with_name("synthetic_config.yaml")).read_text(encoding="utf-8")
    )
    assumptions = {
        "human_hourly_wage_eur": config["labor"]["base_hourly_wage_eur"],
        "human_overhead_multiplier": config["labor"]["overhead_multiplier"],
        "humanoid_capex_eur": config["humanoid"]["unit_capex_eur"],
        "humanoid_installation_cost_eur": config["humanoid"]["installation_cost_per_unit_eur"],
        "humanoid_annual_maintenance_fraction": config["humanoid"]["annual_maintenance_fraction"],
        "amr_capex_eur": config["amr"]["unit_capex_eur"],
        "amr_annual_maintenance_fraction": config["amr"]["annual_maintenance_fraction"],
    }
    result = compute_tco_scenario(
        "synthetic-hybrid",
        {"throughput_orders_per_shift": 960},
        assumptions,
        baseline_annual_opex=500_000,
        years=config["financial"]["horizon_years"],
        discount_rate=config["financial"]["discount_rate"],
        composition={"n_human": 2, "n_humanoid": 1, "n_amr": 1},
    )
    print(f"Synthetic five-year NPV: €{result['npv_eur']:,.0f}")


if __name__ == "__main__":
    main()
