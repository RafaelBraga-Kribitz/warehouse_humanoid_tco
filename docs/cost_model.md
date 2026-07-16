# TCO cost model taxonomy

`reports/module_03_tco_report.json` records each line below as a signed
discounted cost (`npv_eur`). The scenario NPV is the sum of those values; costs
are negative because the model contains no revenue stream.

| Cost line | Formula | Config source | Applies to | Modeled in |
|---|---|---|---|---|
| `humanoid_unit_capex` | `-effective_humanoids × unit_capex_eur` | `tco_assumptions.yaml: humanoid.unit_capex_eur` | Humanoid scenarios | Year 0 NPV |
| `humanoid_installation` | `-effective_humanoids × installation_cost_per_unit_eur` | `tco_assumptions.yaml: humanoid.installation_cost_per_unit_eur` | Humanoid scenarios | Year 0 NPV |
| `humanoid_training` | `-effective_humanoids × training_cost_per_humanoid_eur` | `tco_assumptions.yaml: labor.training_cost_per_humanoid_eur` | Humanoid scenarios | Year 0 NPV |
| `amr_unit_capex` | `-AMRs × unit_capex_eur` | `tco_assumptions.yaml: amr.unit_capex_eur` | AMR scenarios | Year 0 NPV |
| `human_labor` | `-humans × wage × overhead × days × hours × PV factor` | `tco_assumptions.yaml: labor.*`; `autostore_baseline.yaml: operations.*` | All scenarios with humans | Years 1–5 NPV |
| `humanoid_supervision_labor` | `-(effective_humanoids × supervision_ratio) × wage × overhead × days × hours × PV factor` | `autostore_baseline.yaml: humanoid_operational.supervision_ratio`; labor and operations inputs above | Humanoid scenarios | Years 1–5 NPV |
| `humanoid_maintenance` | `-effective_humanoids × unit_capex × annual_maintenance_fraction × PV factor` | `tco_assumptions.yaml: humanoid.*` | Humanoid scenarios | Years 1–5 NPV |
| `humanoid_energy` | `-effective_humanoids × kWh_per_shift × €/kWh × operating_days × PV factor` | `autostore_baseline.yaml: agents.humanoid.energy_kwh_per_shift`; `tco_assumptions.yaml: humanoid.energy_cost_eur_per_kwh` | Humanoid scenarios | Years 1–5 NPV |
| `amr_maintenance` | `-AMRs × unit_capex × annual_maintenance_fraction × PV factor` | `tco_assumptions.yaml: amr.*` | AMR scenarios | Years 1–5 NPV |
| `amr_energy` | `-AMRs × kWh_per_shift × €/kWh × operating_days × PV factor` | `autostore_baseline.yaml: agents.amr.energy_kwh_per_shift`; `tco_assumptions.yaml: humanoid.energy_cost_eur_per_kwh` | AMR scenarios | Years 1–5 NPV |

`effective_humanoids` equals the configured humanoid count divided by
`humanoid_throughput_multiplier` (when positive). The five-year PV factor is
`Σ(1 + discount_rate)^-year` for years 1 through 5.
