# Challenge this analysis

This FAQ names the objections that could change the decision. It links evidence
and assumptions directly so a reader can reproduce or dispute each claim.

## Q1. Is S-lean-human an unfairly small crew?

No. It is explicitly sized to the per-policy-class ρ≤0.85 rule and has its
simulation result in the [authoritative scenario export](../exports/tableau_public/tco_scenarios.csv).

## Q2. Why is the eight-human baseline retained?

It is a labelled legacy-overstaffed reference, not the technology comparator;
see the [decision statement](../README.md#decision-summary).

## Q3. Do the robot data actually come from a warehouse?

No. They are household demonstrations. The transfer limitation and its range
are documented in [data lineage](data_lineage.md#how-the-tco-result-is-actually-driven).

## Q4. Could wages make humanoids cheaper?

The capex × wage frontier tests that directly; inspect
[chart 07](../reports/executive_charts/07_frontier_capex_wage.png).

## Q5. Could better transfer performance change the result?

The capex × transfer frontier is published as
[chart 08](../reports/executive_charts/08_frontier_capex_transfer.png), with its
estimator described in [SENSITIVITY.md](../governance/SENSITIVITY.md).

## Q6. Why is S-hybrid-amr not the robot recommendation?

It retains the F-222 €200K system-integration cost and is more expensive than
S-future-2028 in the [TCO report](../reports/module_03_tco_report.json).

## Q7. Are Monte Carlo probabilities evidence for the current ranking?

No. The retained Monte Carlo scenario set predates fair crew resizing. Its
status and paired-CRN method are disclosed in the
[sensitivity report](../reports/sensitivity_analysis_report.json).

## Q8. What would justify a procurement decision?

A local warehouse pilot should replace the transfer proxy, validate availability,
and measure integration effort; the [assumption register](../governance/ASSUMPTION_REGISTER.md)
identifies the decision-sensitive inputs.

## Q9. Can I inspect the financial arithmetic?

Yes. The scenario-level capex, opex, NPV and cost-per-order fields are exported
in [tco_scenarios.csv](../exports/tableau_public/tco_scenarios.csv), with SQL
provenance in [analytics/sql](../analytics/sql/tco_scenarios.sql).
