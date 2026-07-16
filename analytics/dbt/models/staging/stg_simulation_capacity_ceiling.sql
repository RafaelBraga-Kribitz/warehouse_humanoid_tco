select
    scenario_id,
    target_rho,
    total_agents,
    bottleneck_agent_type,
    bottleneck_cycle_time_seconds,
    lambda_max_per_hour,
    capacity_orders_per_shift,
    observed_throughput_mean,
    observed_throughput_std,
    n_runs_at_ceiling
from {{ source('processed', 'simulation_capacity_ceiling') }}
