# Citation spot audit

This spot audit checks the externally sourced or externally contextualized
inputs that most affect the model. `PARTIAL` means the linked public page
supports the source category but does not independently verify the exact
numeric assumption; it is not evidence that the modeled value is factual.

| Claim / parameter | Source | What the source says | Verdict |
| --- | --- | --- | --- |
| WKO BG-III labor range (€15.13–€22.00/hr) | [WKO collective agreements](https://www.wko.at/service/kollektivvertrag/) | WKO is the canonical publisher for Austrian collective agreements. The accessible index did not expose the dated BG-III wage table, so the exact range needs a preserved agreement PDF. | PARTIAL |
| Annual wage growth (2.5%) | [Statistik Austria wages and salaries](https://www.statistik.at/statistiken/arbeitsmarkt/loehne-und-gehaelter) | Statistik Austria publishes wages and salary statistics. The linked page did not resolve in this environment, and no exact 2020–2025 series was captured. | PARTIAL |
| Knapp AutoStore operating context | [Knapp AutoStore solutions](https://www.knapp.com/en/solutions/products/autostore/) | Knapp publishes AutoStore as a warehouse solution. The page did not resolve in this environment; it supports context only, not the model's 960-orders/shift demand assumption. | PARTIAL |
| Unitree G1 public price and hardware capability | [Unitree G1](https://www.unitree.com/g1) | The product page states a starting price of US $13.5K and lists 23–43 joint motors; it also warns that specifications may vary by configuration. This does not validate the modeled €120K deployed capex. | PASS |
| WBT-to-production transfer factor (0.50–0.90) | `config/tco_assumptions.yaml` and [Unitree G1](https://www.unitree.com/g1) | Unitree describes a general-purpose humanoid and imitation-learning features, but provides no warehouse productivity benchmark. The transfer range remains an explicit internal scenario assumption. | PARTIAL |
