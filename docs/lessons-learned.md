# Lessons learned: Warehouse Humanoid TCO

Evaluation: [economic-evaluation.md](economic-evaluation.md).

## Expectations against actuals (as of 2026-10-30)

| Item | Expected (evaluation) | Actual | Evidence |
|---|---|---|---|
| Effort | 180 h central (90 to 270 h), the charter's 8 to 10 part-time weeks | Unmeasured: no time log. Commit days × 4 h gives 84 h; the session-span check gives 38 h | cost basis v1.2, hours table |
| Total cost | €11,124 central, with one year of maintenance and 8 h implementation | Unmeasured; maintenance and implementation not yet incurred | same |
| Technical performance | A service-checked crew size for the cell and a humanoid speed estimate that separates the four pilot states | Model built. The lean mix (1 worker + 3 robot carts) is cheapest in 99.8 % of 10,000 draws; no all-humanoid crew matches it at any capex from €10k to €500k. | `README.md`; `reports/module_03_tco_report.json` |
| Adoption | Inside f = 0.25 | Unmeasured: no operator decision on record | none |
| Operational outcome | Re-size the crew where a surplus exists; avoid a losing pilot | Unmeasured | none |
| Attributable value | €53k gross expected | Unmeasured | none |

## Lessons

**L-WHT-1. Compute the break-even performance from the configuration before building a simulator.** Scope: technology and procurement evaluations. The first-commit prices alone put the humanoid break-even at 1.19 worker-equivalents per unit on one shift. The simulation then found no all-humanoid crew at parity with the lean mix. It added confidence, not a new decision. Evidence: `config/tco_assumptions.yaml` at `49c852f`; `reports/module_03_tco_report.json` (`breakeven_thresholds`). Date: 2026-10-30.

**L-WHT-2. Put crew size in the state table, not only the technology.** Scope: workforce-mix decisions. The largest saving came from fewer workers with robot carts, against an 8-worker reference the README calls overstaffed. Evidence: `README.md`, "What the numbers say". Date: 2026-10-30.

**L-WHT-3. Value every action the charter names.** Scope: decision studies. The humanoid pilot alone carries €28.6k of perfect-information value, below four times the cost; the crew-size decision the charter also names (FR-03, FR-05) carries €184k. Evidence: this evaluation; `PROJECT_CHARTER.md` at `49c852f`. Date: 2026-10-30.