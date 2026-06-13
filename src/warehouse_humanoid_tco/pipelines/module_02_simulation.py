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
    DEFAULT_CAPACITY_CEILING_RHO,
    AgentProfile,
    WarehouseScenario,
    run_scenario,
    simulate_at_capacity,
)
from warehouse_humanoid_tco.utils.reproducibility import seed_all


def _select_humanoid_cycle_time(
    summary_df: pl.DataFrame,
    reference_task: str,
    default_mean: float = 30.0,
    default_std: float = 10.0,
) -> tuple[float, float]:
    """Return (cycle_time_mean, cycle_time_std) for the named task category.

    Selection is explicit (``task_category == reference_task``), not positional,
    so it is invariant to the row order of the capability summary. The previous
    "first row with a non-null std" logic silently depended on the alphabetical
    sort of category names and selected ``bimanual_handling`` — the slowest,
    two-handed task — rather than the modelled warehouse pick. Falls back to a
    documented default only when the summary is empty; a present-but-missing
    reference task fails loud rather than mis-modelling silently.
    """
    if summary_df is None or len(summary_df) == 0:
        return default_mean, default_std
    match = summary_df.filter(pl.col("task_category") == reference_task)
    if len(match) == 0:
        raise ValueError(
            f"reference_task {reference_task!r} not in capability summary; "
            f"available: {summary_df['task_category'].to_list()}"
        )
    mean = match["cycle_time_mean"][0]
    std = match["cycle_time_std"][0]
    if mean is None or std is None:
        raise ValueError(f"reference_task {reference_task!r} has null cycle_time mean/std")
    return float(mean), float(std)


def _load_global_seed(project_root: Path) -> int | None:
    """Load `simulation.global_seed` from config/seeds.yaml if present.

    F-036: this wires the canonical seed source (config/seeds.yaml) into the
    simulation pipeline. Returns None if the file is missing — caller falls
    back to the function default. The 4 previous granular per-RNG-stream
    keys (order_arrival_seed et al.) were removed because no pipeline code
    consumed them; SimPy + numpy use one Generator per (scenario, run_id)
    seeded from this single value.
    """
    seeds_path = project_root / "config" / "seeds.yaml"
    if not seeds_path.exists():
        return None
    try:
        data = yaml.safe_load(seeds_path.read_text()) or {}
    except yaml.YAMLError:
        return None
    sim = data.get("simulation") or {}
    raw = sim.get("global_seed")
    return int(raw) if isinstance(raw, int) else None


def module_02_main(
    project_root: Path,
    config_path: Path | None = None,
    capability_summary_path: Path | None = None,
    n_runs: int = 15,
    seed: int | None = None,
    capacity_target_rho: float = DEFAULT_CAPACITY_CEILING_RHO,
    capacity_n_runs: int = 5,
) -> dict[str, Path | None]:
    """Run Module 2 end-to-end.

    Returns dict mapping {'simulation_runs': ..., 'validation_report': ...}.
    F-036: `seed` defaults to None — the function loads config/seeds.yaml
    `simulation.global_seed` and falls back to 42 if absent. seed_all is
    called once so any non-Generator random consumers (random, np.random)
    are also reproducible from the same seed source.
    """
    if seed is None:
        seed = _load_global_seed(project_root)
        if seed is None:
            seed = 42
    seed_all(seed)

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
        print("  ⚠ Capability summary not found. Using placeholder values.")
        summary_df = pl.DataFrame()

    # Humanoid cycle time fed to the simulation:
    #   (1) Select an explicit, warehouse-relevant task category (config
    #       agents.humanoid.reference_task) — invariant to summary row order.
    #   (2) Apply the WBT->production transfer factor so the simulated humanoid
    #       runs at production speed, not raw teleoperation-demo speed. The
    #       charter calls this the single largest methodological assumption; it
    #       must reach the simulation, not only the cost model.
    reference_task = config["agents"]["humanoid"].get("reference_task", "pick_medium_object")
    transfer_factor = (
        config.get("capability_transfer", {})
        .get("wbt_to_production_factor", {})
        .get("point_estimate", 0.70)
    )
    if transfer_factor <= 0:
        raise ValueError(f"wbt_to_production_factor must be > 0; got {transfer_factor}")
    demo_cycle_mean, demo_cycle_std = _select_humanoid_cycle_time(summary_df, reference_task)
    humanoid_cycle_mean = demo_cycle_mean / transfer_factor
    humanoid_cycle_std = demo_cycle_std / transfer_factor
    print(
        f"  Humanoid cycle time: demo {demo_cycle_mean:.1f}±{demo_cycle_std:.1f}s "
        f"(task={reference_task}) -> production {humanoid_cycle_mean:.1f}"
        f"±{humanoid_cycle_std:.1f}s (transfer={transfer_factor:.2f})"
    )

    # ========== Run Simulations ==========
    all_runs = []
    built_scenarios: list[WarehouseScenario] = []
    scenarios = config.get("scenarios", [])
    total_agents = config.get("total_agents", 8)

    for scenario_config in scenarios:
        scenario_id = scenario_config["id"]
        throughput_mult = scenario_config.get("humanoid_throughput_multiplier", 1.0)

        # Explicit integer crew sizes are the SSOT (config agent_counts). This
        # replaces `int(total_agents * fraction)`, which silently truncated
        # fractional crews (60/20/20 of 8 -> 4 + 1 + 1 = 6, not 8). Fall back to
        # rounded fractions only for legacy configs/tests without agent_counts.
        counts = scenario_config.get("agent_counts")
        if counts is None:
            counts = {
                "human": round(total_agents * scenario_config.get("human_fraction", 0.0)),
                "humanoid": round(total_agents * scenario_config.get("humanoid_fraction", 0.0)),
                "amr": round(total_agents * scenario_config.get("amr_fraction", 0.0)),
            }
        human_count = int(counts.get("human", 0))
        humanoid_count = int(counts.get("humanoid", 0))
        amr_count = int(counts.get("amr", 0))

        print(f"\n[Scenario] {scenario_id}")
        print(
            f"  Crew: {human_count} human, {humanoid_count} humanoid, "
            f"{amr_count} AMR ({human_count + humanoid_count + amr_count} units)"
        )

        # Create agent profiles
        agent_profiles = []

        if human_count > 0:
            agent_profiles.append(
                AgentProfile(
                    agent_type="human",
                    cycle_time_mean=config["agents"]["human"]["cycle_time_mean_seconds"],
                    cycle_time_std=config["agents"]["human"]["cycle_time_std_seconds"],
                    count=human_count,
                    seed=seed,
                )
            )

        if humanoid_count > 0:
            agent_profiles.append(
                AgentProfile(
                    agent_type="humanoid",
                    cycle_time_mean=humanoid_cycle_mean / throughput_mult,
                    cycle_time_std=humanoid_cycle_std / throughput_mult,
                    count=humanoid_count,
                    seed=seed,
                )
            )

        if amr_count > 0:
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
        built_scenarios.append(scenario)

        # Run multiple realizations
        print(f"  Running {n_runs} simulation(s)...")
        for run_id in range(n_runs):
            result = run_scenario(scenario, run_id=run_id)
            all_runs.append(result)
            throughput = result["throughput_orders_per_shift"]
            queue_mean = result["queue_length_mean"]
            print(f"    Run {run_id}: {throughput:.0f} orders/shift, queue={queue_mean:.1f}")

    # ========== Capacity Ceiling Sweep (F-044) ==========
    # The fixed-arrival runs above measure throughput in a demand-bound regime
    # (rho ~ 0.1-0.34); they don't differentiate scenarios because the Poisson
    # arrival process is the binding constraint, not capacity. The capacity
    # ceiling sweep ramps each scenario's arrival rate to lambda_max(target_rho)
    # using the per-agent-type stability formula, then validates with finite-
    # horizon simulation. Result is the discriminative chart 03 data.
    print(
        f"\n[Capacity] Computing capacity ceiling at rho={capacity_target_rho} "
        f"({capacity_n_runs} validation runs/scenario)..."
    )
    capacity_rows: list[dict[str, object]] = []
    for scenario in built_scenarios:
        result = simulate_at_capacity(
            scenario,
            target_rho=capacity_target_rho,
            n_runs=capacity_n_runs,
        )
        capacity_rows.append(result)
        print(
            f"  {scenario.scenario_id}: bottleneck={result['bottleneck_agent_type']} "
            f"({result['bottleneck_cycle_time_seconds']:.1f}s), "
            f"capacity={result['capacity_orders_per_shift']:.0f}/shift, "
            f"observed={result['observed_throughput_mean']:.0f}"
            f"±{result['observed_throughput_std']:.0f}"
        )

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

    if capacity_rows:
        capacity_df = pl.DataFrame(capacity_rows)
        capacity_path: Path | None = data_processed / "simulation_capacity_ceiling.parquet"
        capacity_df.write_parquet(capacity_path)
        print(f"  ✓ {capacity_path}")
    else:
        capacity_path = None

    # ========== Validation Report ==========
    validation_report = {
        "phase": "module_02_simulation",
        "total_runs": len(all_runs),
        "scenarios_tested": len(scenarios),
        "n_runs_per_scenario": n_runs,
        "simulation_runs_path": str(runs_path) if runs_path else None,
        "capacity_ceiling_path": str(capacity_path) if capacity_path else None,
        "capacity_target_rho": capacity_target_rho,
        "capacity_n_runs_per_scenario": capacity_n_runs,
    }

    report_path = project_root / "reports" / "module_02_simulation_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(validation_report, f, indent=2)

    print(f"\n✓ Module 2 complete. {len(all_runs)} runs across {len(scenarios)} scenarios.")
    print(f"  Report: {report_path}")

    return {
        "simulation_runs": runs_path,
        "capacity_ceiling": capacity_path,
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
