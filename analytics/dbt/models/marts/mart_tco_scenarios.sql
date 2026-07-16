select
    scenario_id,
    npv_eur,
    cost_reduction_vs_baseline_pct,
    opex_reduction_vs_baseline_pct,
    payback_years,
    total_capex_eur,
    total_opex_5yr_eur_nominal,
    total_opex_5yr_eur_pv,
    pipeline_version,
    cost_per_order_eur,
    n_simulation_runs,
    throughput_mean_orders_per_shift,
    throughput_std_orders_per_shift,
    total_cost_reduction_vs_baseline_pct
from {{ ref('stg_tco_scenarios') }}
order by scenario_id
