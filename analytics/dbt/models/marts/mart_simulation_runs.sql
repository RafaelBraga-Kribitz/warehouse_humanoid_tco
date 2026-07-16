select
    scenario_id,
    run_id,
    throughput_orders_per_shift,
    queue_length_mean,
    rho_predicted,
    pipeline_version,
    seed,
    utilization_human,
    utilization_humanoid,
    utilization_amr
from {{ ref('stg_simulation_runs') }}
order by scenario_id, run_id
