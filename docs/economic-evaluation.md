# Economic evaluation: Warehouse Humanoid TCO

Pre-build scenario exercise · evaluation date 2026-05-20 · method v2.0 · cost basis v1.1 ([COST_BASIS.md](https://github.com/RafaelBraga-Kribitz/braga-portfolio-docs/blob/main/docs/value-evaluation/COST_BASIS.md))

## Decision

The COO of an Austrian AutoStore-class warehouse (KNAPP-type) decides whether to commit a two-humanoid pilot in one picking cell now or wait. The study is valued as information: the expected loss it avoids in that decision.

## Scale, baseline and horizon

- One cell: 4 pick ports, 120 orders per hour, 8 workers, one 8-hour shift [sourced: `config/autostore_baseline.yaml` at `49c852f`].
- One worker: €18.50 per hour × 1.35 overhead = €50,350 a year, wages +2.5 % a year [sourced: `config/tco_assumptions.yaml` at `49c852f`]; 5-year present value at 5 %: €0.23M [estimate].
- Pilot: 2 humanoids at €120k plus €8k installation, upkeep 8 % a year, €200k cell integration (€100k to €400k) [sourced: same file]; present value €0.54M, no resale [estimate].
- Humanoid speed is the unknown; the first-commit configuration leaves it empty. Robot carts are quoted; a spreadsheet settles them.
- Baseline: wait, €0. Horizon: 5 years, the charter's cost horizon.
- Committed forecasts: "8 to 10 weeks part-time"; hypothesis H1, a human crew beats a humanoid crew at 2026 prices (`PROJECT_CHARTER.md` §1, §7.1 at `49c852f`).

## Scenarios

w = worker-equivalents per humanoid. Pilot value against waiting = 2 × w × €0.23M − €0.54M.

| State of the humanoid offer | w | Pilot value | Probability |
|---|---|---|---|
| Vendor claim holds: worker speed, longer daily availability | 1.5 | +€0.14M | 0.20 [assumption: few humanoids beyond pilots in 2026] |
| Partly true: worker speed only; no usable benefit | 1.0 | −€0.09M | 0.30 [assumption] |
| Inapplicable: half a worker | 0.5 | −€0.31M | 0.35 [assumption: charter rates "dataset proves insufficient" Medium] |
| Adverse: pilot fails, integration €400k | 0 | −€0.74M | 0.15 [assumption: new hardware] |

Break-even: w = 1.19 on one shift.

## Expected value and cost

- EV(pilot) = 0.20 × 0.14 − 0.30 × 0.09 − 0.35 × 0.31 − 0.15 × 0.74 = −€0.22M, so waiting is best without the study.
- Perfect information pilots only in the first state: 0.20 × €0.143M = €28.6k. Expected value of perfect information (EVPI) = €28.6k − €0 = **€28.6k**.
- Realistic fraction f = 0.25 [assumption, sensitivity parameter: public demonstration data, no site telemetry; covers non-use and misleading results]. Expected gross value = 0.25 × €28.6k = **€7.1k**.

Rate: €54 per active hour, the market cost of the role this work needs (data science · senior, advertised minimum, ADJMI snapshot 2026-10-18; ADJMI = Austria Data-Job Market Intelligence), €51 loaded plus €3 AI and equipment. Maintenance: 10 % of build hours a year for 5 years. Implementation: 8 h for one site's wages and quotes [assumption]. Hosting €0.

| Case | Build | Maintenance | Implementation | Total cost | Multiple |
|---|---|---|---|---|---|
| Central, 84 h | €4,536 | €2,268 | €432 | €7,236 | 0.99× |
| 0.5×, 42 h | €2,268 | €1,134 | €432 | €3,834 | 1.9× |
| 1.5×, 126 h | €6,804 | €3,402 | €432 | €10,638 | 0.67× |

## Verdict

**Fails financial hurdle**: 0.99× central against 4×; 0.77× at a rate 30 % higher (€69.3 all-in; the inputs are floors). Even perfect information (€28.6k) is below four times the central cost (€28.9k). Maximum affordable cost: €7.1k ÷ 4 = **€1.8k**.

Break-even driver: identical cells sharing the decision. 1× at 1.0 cell; 4× at 4.1 cells.

Reversing assumptions:

1. The site would otherwise follow a vendor demo and pilot. The study then avoids €28.6k + €218.6k = €247k; gross €62k; 8.5×.
2. Four or more identical cells decide together.

## Recommendation

**Defer** until a site holds a concrete humanoid offer or four or more cells are in scope. Meanwhile the rule is the break-even: no pilot below 1.19 worker-equivalents. Measure: hours spent; use in a named operator's capex decision; measured humanoid picks per hour against 1.19; the pilot's realised cost and savings.

Actuals and lessons: [lessons-learned.md](lessons-learned.md).
