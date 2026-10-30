# Economic evaluation: Warehouse Humanoid TCO

Pre-build scenario exercise · evaluation date 2026-05-20 · method v2.0 · cost basis v1.2 ([COST_BASIS.md](https://github.com/RafaelBraga-Kribitz/braga-portfolio-docs/blob/main/docs/value-evaluation/COST_BASIS.md))

## Decision

The COO of an Austrian AutoStore-class warehouse (KNAPP-type) makes two staffing decisions for one picking cell: how many pickers it needs, and whether to pilot two humanoids now or wait. The study is valued as information: the expected loss it avoids in both.

## Scale, baseline and horizon

- One cell: 4 ports, 120 orders an hour, 2.5 lines an order, 25 s a line, 8 workforce units [sourced: `config/autostore_baseline.yaml` at `49c852f`]. Picking alone needs about 2.1 picker-hours an hour (120 × 2.5 × 25 s), against 8 units [estimate].
- One worker: €50,350 a year; 5-year present value at 5 % about €0.23M [sourced: `config/tco_assumptions.yaml` at `49c852f`; estimate].
- Humanoid pilot: present value €0.54M; break-even 1.19 worker-equivalents per unit [sourced: same file; estimate].
- Staffing and crew mix were in scope from the start [sourced: `PROJECT_CHARTER.md` FR-03, FR-05 at `49c852f`].
- Baseline: keep the crew and wait, €0. Best cheap alternative: an 8-hour utilisation spreadsheet. Horizon: 5 years.

## Scenarios

Crew states: the cell's real surplus against need. Without evidence a cautious COO keeps the crew (works council, peak service).

| State | Value of acting on it | Probability |
|---|---|---|
| Surplus of 2 or more workers | cut 2: +€0.46M | 0.25 [assumption: 8 units for about 2.1 picker-hours of picking] |
| Surplus of 1 worker | cut 1: +€0.23M | 0.30 [assumption] |
| Right-sized; no usable benefit | keep: €0 | 0.30 [assumption] |
| Adverse: short at peaks; a cut would fail service | keep: €0, a cut loses | 0.15 [assumption] |

Humanoid states: vendor claim holds (0.20, pilot +€0.14M), partly true (0.30, −€0.09M), half a worker (0.35, −€0.31M), pilot fails (0.15, −€0.74M). Waiting is the uninformed choice.

## Expected value and cost

- Expected value of perfect information (EVPI) on crew size: 0.25 × €0.46M + 0.30 × €0.23M = **€184k**. EVPI on the pilot: **€28.6k**.
- Fraction a simulation recovers, f = 0.25 [assumption, sensitivity parameter: public benchmarks, no site data; covers non-use and misleading results]. Expected gross value = 0.25 × (€184k + €28.6k) = **€53k**.
- Spreadsheet alternative: f = 0.10 on crew size, nothing on peaks or the pilot: €18k gross for €432.

Rate: €54 per active hour, the market cost of the role this work needs (data science · senior, advertised minimum, ADJMI snapshot 2026-10-18; ADJMI = Austria Data-Job Market Intelligence), €51 loaded plus €3 AI and equipment. Hours: the charter's 8 to 10 part-time weeks, about 180 h [estimate]. Maintenance: 10 % of build hours for the one year of use. Implementation: 8 h for site wages and quotes. Hosting €0.

| Case | Hours (build + maintenance + implementation) | Total cost | Multiple |
|---|---|---|---|
| Central | 180 + 18 + 8 | €11,124 | 4.8× |
| 0.5× hours | 90 + 9 + 8 | €5,778 | 9.2× |
| 1.5× hours | 270 + 27 + 8 | €16,470 | 3.2× |

## Verdict

**Passes financial hurdle** at the central case, 4.8×, conditional on the illustrative probabilities. It fails at 1.5× hours (3.2×) and at a rate 30 % higher (3.7×; the inputs are floors). Maximum affordable cost: €53k ÷ 4 = **€13.3k**.

Break-even driver, the fraction f on crew size: 0.02 for 1×, 0.20 for 4×.

Decision advantage over the spreadsheet: +€24k expected net. The extra €10.7k of cost buys €35k of extra value, 3.2× on the increment.

Reversing assumptions:

1. The real cell is already right-sized, so the crew states carry little weight.
2. The build runs past about 215 h at this rate.

## Recommendation

**Build**, capped at the charter's 180 h, after the 8-hour spreadsheet confirms a likely surplus. Measure: hours; whether a named operator re-sizes a crew or decides on a pilot using the result; workers changed against the 8-unit reference; measured humanoid picks per hour against 1.19.

Actuals and lessons: [lessons-learned.md](lessons-learned.md).
