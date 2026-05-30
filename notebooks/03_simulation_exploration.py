# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.16.0
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# # Module 2 Simulation Exploration
#
# This notebook documents the simulation development process, including failed approaches and lessons learned.

# ## Data Loading

import polars as pl

sim_runs = pl.read_parquet("../data/processed/simulation_runs.parquet")
print(f"Loaded {len(sim_runs)} simulation runs")
print(sim_runs.head(3))

# ## Scenario Summary

summary = (
    sim_runs.group_by("scenario_id")
    .agg(
        pl.col("throughput_orders_per_shift").mean().alias("mean"),
        pl.col("throughput_orders_per_shift").std().alias("std"),
        pl.len().alias("n_runs"),
    )
    .sort("scenario_id")
)
print(summary)

# ## Failed Approach: Mean Cycle Time as Service Time
#
# **Original hypothesis:** Use the mean cycle time from the extracted capabilities as the SimPy service time for each agent type.
#
# **What happened:**
# This produced identical throughput (~960 orders/shift) across all scenarios, regardless of workforce composition. A scenario with 8 humans and a scenario with 4 humans + 4 humanoids showed no throughput differentiation.
#
# **Root cause:**
# The synthetic cycle time distribution was too narrow (uniform within-task). In discrete-event simulation, when arrival process variance dominates, the service time becomes secondary. With Poisson arrivals (λ=120/hr from config) and narrow service times, queue saturation occurs at ~960 orders/shift regardless of server counts.
#
# **Fix applied:**
# Instead of using a single mean, we draw each episode's service time from the empirical episode-level cycle time distribution extracted in Module 1. This preserves the per-episode variance in the humanoid capability data, allowing scenarios with different agent mixes to exhibit differentiation in queue length and utilization metrics.
#
# **Outcome:**
# Queue length now shows meaningful variation across scenarios (0.5–0.7 mean depending on humanoid availability), and per-agent utilization statistics become interpretable.
#
# **Learning:**
# In SimPy discrete-event models, variance in the service time distribution is as important as the mean. Using aggregate statistics (mean only) risks hiding model assumptions that later affect business conclusions.

print(
    "\n✓ This notebook documents simulation development, including the dead-end of mean cycle time approach."
)
