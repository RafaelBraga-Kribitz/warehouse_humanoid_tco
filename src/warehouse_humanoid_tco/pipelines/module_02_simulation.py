"""Module 2: Discrete-Event Simulation Pipeline

Orchestrates:
1. Load Module 1 humanoid capability outputs
2. Load architecture config (AutoStore baseline)
3. Populate agent profiles with empirical data
4. Run SimPy simulation for each scenario × N runs
5. Export simulation_runs parquet

Entry point: main()
See PROJECT_CHARTER.md §4 Module 2 for spec.
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl
import yaml

from warehouse_humanoid_tco.models.simulation import (
    AgentProfile,
    WarehouseScenario,
    run_scenario,
)


def module_02_main(
    project_root: Path,
    config_path: Path | None = None,
    capability_summary_path: Path | None = None,
    n_runs: int = 15,
    seed: int = 42,
) -> dict[str, Path]:
    """Run Module 2 end-to-end.

    Returns dict mapping {'simulation_runs': ..., 'validation_report': ...}
    """
    # Load config
    if config_path is None:
        config_path = project_root / "config" / "autostore_baseline.yaml"

    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Load humanoid capabilities summary
    if capability_summary_path is None:
        capability_summary_path = (
            project_root / "data" / "processed" / "humanoid_capabilities_summary.parquet"
        )

    data_processed = project_root / "data" / "processed"
    data_processed.mkdir(parents=True, exist_ok=True)

    print(f"[Setup] Loading config from {config_path}...")
    print(f"[Setup] Loading humanoid capabilities from {capability_summary_path}...")

    if capability_summary_path.exists():
        summary_df = pl.read_parquet(capability_summary_path)
        print(f"  ✓ Loaded capability summary for {len(summary_df)} task categories")
    else:
        print(f"  ⚠ Capability summary not found. Using placeholder values.")
        summary_df = pl.DataFrame()

    # Extract humanoid cycle time from summary (using first row with valid std)
    humanoid_cycle_mean = 30.0
    humanoid_cycle_std = 10.0

    if len(summary_df) > 0:
        # Find first row with non-null cycle_time_std
        for i in range(len(summary_df)):
            if summary_df["cycle_time_std"][i] is not None:
                humanoid_cycle_mean = float(summary_df["cycle_time_mean"][i])
                humanoid_cycle_std = float(summary_df["cycle_time_std"][i])
                break
        # Fallback to first row's mean if no std available
        if humanoid_cycle_std == 10.0 and summary_df["cycle_time_mean"][0] is not None:
            humanoid_cycle_mean = float(summary_df["cycle_time_mean"][0])
        print(f"  Using humanoid cycle time: {humanoid_cycle_mean:.1f}±{humanoid_cycle_std:.1f}s")

    # ========== Run Simulations ==========
    all_runs = []
    scenarios = config.get("scenarios", [])
    total_agents = config.get("total_agents", 8)

    for scenario_config in scenarios:
        scenario_id = scenario_config["id"]
        human_frac = scenario_config.get("human_fraction", 0.0)
        humanoid_frac = scenario_config.get("humanoid_fraction", 0.0)
        amr_frac = scenario_config.get("amr_fraction", 0.0)
        throughput_mult = scenario_config.get("humanoid_throughput_multiplier", 1.0)

        print(f"\n[Scenario] {scenario_id}")
        print(f"  Composition: {human_frac:.1%} human, {humanoid_frac:.1%} humanoid, {amr_frac:.1%} AMR")

        # Create agent profiles
        agent_profiles = []

        if human_frac > 0:
            human_count = max(1, int(total_agents * human_frac))
            agent_profiles.append(
                AgentProfile(
                    agent_type="human",
                    cycle_time_mean=config["agents"]["human"]["cycle_time_mean_seconds"],
                    cycle_time_std=config["agents"]["human"]["cycle_time_std_seconds"],
                    count=human_count,
                    seed=seed,
                )
            )

        if humanoid_frac > 0:
            humanoid_count = max(1, int(total_agents * humanoid_frac))
            agent_profiles.append(
                AgentProfile(
                    agent_type="humanoid",
                    cycle_time_mean=humanoid_cycle_mean / throughput_mult,
                    cycle_time_std=humanoid_cycle_std / throughput_mult,
                    count=humanoid_count,
                    seed=seed,
                )
            )

        if amr_frac > 0:
            amr_count = max(1, int(total_agents * amr_frac))
            agent_profiles.append(
                AgentProfile(
                    agent_type="amr",
                    cycle_time_mean=config["agents"]["amr"]["cycle_time_mean_seconds"],
                    cycle_time_std=config["agents"]["amr"]["cycle_time_std_seconds"],
                    count=amr_count,
                    seed=seed,
                )
            )

        # Create scenario
        scenario = WarehouseScenario(
            scenario_id=scenario_id,
            architecture=config["architecture"],
            total_agents=total_agents,
            agent_profiles=agent_profiles,
            order_arrival_rate_per_hour=config["operations"]["order_arrival_rate_per_hour"],
            shift_hours=config["operations"]["shift_hours"],
            seed=seed,
        )

        # Run multiple realizations
        print(f"  Running {n_runs} simulation(s)...")
        for run_id in range(n_runs):
            result = run_scenario(scenario, run_id=run_id)
            all_runs.append(result)
            throughput = result["throughput_orders_per_shift"]
            queue_mean = result["queue_length_mean"]
            print(f"    Run {run_id}: {throughput:.0f} orders/shift, queue={queue_mean:.1f}")

    # ========== Export ==========
    print("\n[Export] Writing parquets...")

    if all_runs:
        runs_df = pl.DataFrame(all_runs)
        runs_path = data_processed / "simulation_runs.parquet"
        runs_df.write_parquet(runs_path)
        print(f"  ✓ {runs_path}")
    else:
        runs_df = pl.DataFrame()
        runs_path = None

    # ========== Validation Report ==========
    validation_report = {
        "phase": "module_02_simulation",
        "total_runs": len(all_runs),
        "scenarios_tested": len(scenarios),
        "n_runs_per_scenario": n_runs,
        "simulation_runs_path": str(runs_path) if runs_path else None,
    }

    report_path = project_root / "reports" / "module_02_simulation_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(validation_report, f, indent=2)

    print(f"\n✓ Module 2 complete. {len(all_runs)} runs across {len(scenarios)} scenarios.")
    print(f"  Report: {report_path}")

    return {
        "simulation_runs": runs_path,
        "validation_report": report_path,
    }


if __name__ == "__main__":
    import sys

    project_root = Path(__file__).parent.parent.parent.parent

    try:
        paths = module_02_main(project_root, n_runs=15)
        print(f"\n✓ Success. Outputs: {paths}")
    except Exception as e:
        print(f"\n✗ Failed: {e}", file=sys.stderr)
        sys.exit(1)
