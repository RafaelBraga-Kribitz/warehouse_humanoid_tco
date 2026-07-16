# Model limitations

| Limitation | Bias | Note |
|---|---|---|
| `financial.discount_rate_range` | neutral | Legacy range is not the active sensitivity range. |
| `labor.training_cost_range` | favors_robots | Training range is not sampled. |
| `humanoid.unit_capex_range` | favors_robots | Legacy capex range is not sampled. |
| `humanoid.financing_rate` | favors_humans | Financing costs are not modeled in NPV. |
| `infrastructure.grid_expansion_cost_eur_per_bin` | favors_robots | Grid expansion cost is excluded from TCO. |
| `infrastructure.integration_cost_range` | favors_robots | Integration cost range is not sampled. |
| `layout.grid_columns` | unknown | Grid geometry is not simulated. |
| `layout.grid_rows` | unknown | Grid geometry is not simulated. |
| `layout.bin_depth` | unknown | Bin depth is not simulated. |
| `layout.total_bins` | unknown | Storage capacity is not simulated. |
| `layout.robots_per_port` | unknown | Port assignment is not simulated. |
| `agents.human.error_rate` | favors_robots | Human picking errors are not costed. |
| `agents.human.absence_rate_per_shift` | favors_robots | Human absence is not modeled. |
| `agents.humanoid.error_rate` | favors_robots | Humanoid picking errors are not costed. |
| `agents.amr.error_rate` | favors_robots | AMR errors are not costed. |
| `agents.amr.mtbf_hours` | favors_robots | AMR failure rate is not simulated. |
| `agents.amr.mttr_hours` | favors_robots | AMR repair time is not simulated. |
| `capability_transfer.wbt_to_production_factor.rationale` | neutral | Rationale is documentation rather than a model input. |
| `humanoid_operational.shift_degradation_factor` | favors_robots | Humanoid shift degradation is not simulated. |
| `amr_operational.mtbf_hours` | favors_robots | AMR failure rate is not simulated. |
| `amr_operational.battery_capacity_hours` | favors_robots | AMR battery capacity is not simulated. |
| `amr_operational.recharge_time_hours` | favors_robots | AMR recharge time is not simulated. |
# Known Limitations

These are the current limits of the analysis, expanded from Charter §3.7.
They are disclosures, not corrections applied after the fact.

| Limitation | Bias direction | Magnitude bound |
|---|---|---|
| WBT cycle times are teleoperation demonstrations rather than production telemetry. | Can overstate humanoid throughput and understate TCO. | Transfer factor is 0.70; Monte Carlo samples 0.50–0.90. |
| Source episodes are household demonstrations (plates-into-dishwasher, pillow pickup, clothes-into-washing-machine, and single-/dual-arm DiverseManip), not warehouse tasks. | Domain-transfer risk is the largest external-validity threat; pick-move-place primitives and the 0.50–0.90 speed transfer factor are proxies. | Warehouse-native task telemetry would falsify or repair the proxy. |
| Each scenario has 15 simulation replicas. | Sampling error can change estimated operational metrics. | 15 replicas per scenario; no tighter precision claim is made. |
| No warehouse telemetry is used for calibration. | External validity may be weaker in a specific facility. | Calibration uses public Knapp benchmarks only. |
| Humanoid capex uses public pricing rather than signed quotes. | Can under- or overstate humanoid TCO. | Sensitivity range is €60,000–€180,000 around a €120,000 base point. |
| Austrian collective-agreement wage inputs are estimates. | Can under- or overstate labour savings and TCO. | Monte Carlo wage distribution has mean €18.50/hour and standard deviation €2.00/hour. |
