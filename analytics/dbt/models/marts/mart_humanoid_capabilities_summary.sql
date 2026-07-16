select
    task_category,
    n_episodes,
    cycle_time_p50,
    cycle_time_p95,
    cycle_time_mean,
    cycle_time_std,
    reach_mean_meters,
    reach_max_meters,
    energy_proxy_mean,
    success_rate,
    insufficient_sample
from {{ ref('stg_humanoid_capabilities_summary') }}
order by task_category
