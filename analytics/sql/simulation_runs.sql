SELECT
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
FROM {{source}}
