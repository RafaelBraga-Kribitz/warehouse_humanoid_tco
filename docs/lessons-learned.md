# Lessons learned: Warehouse Humanoid TCO

Evaluation: [economic-evaluation.md](economic-evaluation.md).

## Expectations against actuals (as of 2026-10-30)

| Item | Expected (evaluation) | Actual | Evidence |
|---|---|---|---|
| Effort | 84 h central (42 to 126 h) | 84 h by the commit-day convention; session-span check 38 h; no time log | cost basis v1.1, hours table |
| Total cost | €7,236 central, with 5 years of maintenance and 8 h implementation | €4,536 build to date; maintenance and implementation not yet incurred | same |
| Technical performance | A humanoid speed estimate that separates the four states | Model built. No all-humanoid crew matches the lean mix (1 worker + 3 robot carts) at any capex from €10k to €500k; the lean mix is cheapest in 99.8 % of 10,000 draws. Speed rests on household tasks, not warehouse picks | `README.md`; `reports/module_03_tco_report.json` |
| Adoption | Inside f = 0.25 | Unmeasured: no operator decision on record | none |
| Operational outcome | Avoid a losing pilot, or find one that pays | Unmeasured | none |
| Attributable value | €7.1k gross expected | Unmeasured | none |

## Lessons

**L-WHT-1. Compute the break-even performance from the configuration before building a simulator.** Scope: technology and procurement evaluations. The first-commit prices alone put the humanoid break-even at 1.19 worker-equivalents per unit on one shift. The simulation then found no all-humanoid crew at parity with the lean mix. It added confidence, not a new decision. Evidence: `config/tco_assumptions.yaml` at `49c852f`; `reports/module_03_tco_report.json` (`breakeven_thresholds`). Date: 2026-10-30.

**L-WHT-2. Put crew size in the state table, not only the technology.** Scope: workforce-mix decisions. The largest saving came from fewer workers with robot carts, against an 8-worker reference the README calls overstaffed. Evidence: `README.md`, "What the numbers say". Date: 2026-10-30.

**L-WHT-3. Check whether perfect information clears the hurdle first.** Scope: one-off decisions at one site. Even perfect information (€28.6k) was below four times the cost (€28.9k), so no data quality could rescue the case at one cell. Evidence: this evaluation; `reports/sensitivity_analysis_report.json` (`evpi_eur` about €0 for the lean mix). Date: 2026-10-30.
