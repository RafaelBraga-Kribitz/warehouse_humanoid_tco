# Auditor worksheet: S-hybrid-amr

This is a hand recomputation of the committed `S-hybrid-amr` result in
`reports/module_03_tco_report.json`. Config citations use YAML paths; the
result is rounded only for presentation.

## Inputs

| Input | Value | Config citation |
|---|---:|---|
| Humans / humanoids / AMRs | 4 / 1 / 1 | `autostore_baseline.yaml: scenarios[id=S-hybrid-amr].agent_counts` |
| Wage / overhead | €18.50 / 1.35 | `tco_assumptions.yaml: labor.base_hourly_wage_eur`, `labor.overhead_multiplier` |
| Days / shift hours | 252 / 8 | `autostore_baseline.yaml: operations.operating_days_per_year`, `operations.shift_hours` |
| Humanoid capex / installation / training | €120,000 / €8,000 / €5,000 | `tco_assumptions.yaml: humanoid.unit_capex_eur`, `humanoid.installation_cost_per_unit_eur`, `labor.training_cost_per_humanoid_eur` |
| AMR capex | €65,000 | `tco_assumptions.yaml: amr.unit_capex_eur` |
| Discount rate / horizon | 8% / 5 years | `tco_assumptions.yaml: financial.discount_rate`, `financial.horizon_years` |

## Recalculation

The annual human labour cost is `4 × 18.50 × 1.35 × 252 × 8 =
€201,398.40`. The five-year 8% annuity PV factor is
`1/1.08 + … + 1/1.08^5 = 3.992710`.

| Line | Calculation | Discounted cost (€) |
|---|---|---:|
| Humanoid capex | `1 × 120,000` | -120,000.00 |
| Humanoid installation | `1 × 8,000` | -8,000.00 |
| Humanoid training | `1 × 5,000` | -5,000.00 |
| AMR capex | `1 × 65,000` | -65,000.00 |
| Human labour PV | `201,398.40 × 3.992710` | -804,125.41 |
| Humanoid supervision PV | `(0.10 × 1 × 18.50 × 1.35 × 252 × 8) × 3.992710` | -20,103.14 |
| Humanoid maintenance PV | `(1 × 120,000 × 0.08) × 3.992710` | -38,330.02 |
| Humanoid energy PV | `(1 × 8 × 0.22 × 252) × 3.992710` | -1,770.85 |
| AMR maintenance PV | `(1 × 65,000 × 0.06) × 3.992710` | -15,571.57 |
| AMR energy PV | `(1 × 4 × 0.22 × 252) × 3.992710` | -885.42 |
| **Total NPV** | sum of cost lines | **-1,078,786.40** |

The total agrees with the committed report (`-1,078,786.4041`) within €0.01.
