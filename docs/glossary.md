# Glossary

Three-language reference: English — German — Portuguese.  
Terms are listed in English alphabetical order. Non-expert definitions below; keep project docs linked here for first-use terms.

Anchors used by README first-use links: <a id="amr"></a><a id="npv"></a><a id="tco"></a><a id="oat"></a><a id="utilisation"></a><a id="transfer-factor"></a><a id="kollektivvertrag"></a><a id="monte-carlo"></a>

| English | German | Portuguese | Definition |
|---|---|---|---|
| 1σ (One Standard Deviation) | 1σ (eine Standardabweichung) | 1σ (um desvio padrão) | Statistical measure of how spread out values are. Here, how much predicted financial costs may bounce above or below the average estimate. |
| 1H+3A | 1H+3A (1 Mensch + 3 AMR) | 1H+3A (1 humano + 3 RMA) | Shorthand for the lean winning mix: 1 human worker and 3 AMRs (Autonomous Mobile Robots). |
| 8% Discount Rate | 8%-Diskontsatz | Taxa de desconto de 8% | Financial rule that money today is worth more than money later. Future 5-year costs are discounted 8% per year when computing NPV. |
| ADR (Architecture Decision Record) | ADR (Architekturentscheidungsprotokoll) | ADR (Registro de Decisão de Arquitetura) | Formal log of significant build choices, with context and consequences, so future readers know why a decision was made. |
| Agent Surrogate | Agenten-Surrogat | Surrogato de agente | Automated AI assistant (e.g. Claude or Cursor) that stands in for a human coder to verify or reproduce project data. |
| AI Coding Agents (Claude, Cursor Agent, Copilot) | KI-Coding-Agenten | Agentes de coding com IA | AI tools used as digital assistants to help write code, verify math, and document the project. |
| AMR | AMR (Autonomer Mobiler Roboter) | RMA (Robô Móvel Autônomo) | Autonomous Mobile Robot. Moves goods in a warehouse automatically; typically a wheeled cart or flat platform, not a humanoid with arms and legs. Used by Knapp and TGW today. |
| Audit State / QUALITY_BLUEPRINT | Audit-Status / QUALITY_BLUEPRINT | Estado de auditoria / QUALITY_BLUEPRINT | Governance documents that track quality control so an outsider can verify the code was tested rigorously and numbers were not invented. |
| AutoStore | AutoStore | AutoStore | Cube-storage warehouse architecture. Robots retrieve bins from a 3D grid. Reference architecture for v1.0 simulation. |
| Availability Derating | Verfügbarkeitsabschlag | Derating de disponibilidade | Realistic adjustment so robots are not assumed available 100% of the time (breakdowns, charging, maintenance). |
| Baseline / S-baseline-human | Baseline / S-baseline-human | Linha de base / S-baseline-human | Starting point for comparison. **S-baseline-human** is an older, inefficient warehouse overstaffed with 8 human workers. |
| Betriebsrat | Betriebsrat | Conselho de Trabalhadores | Austrian works council. Has co-determination rights under §96 ArbVG over technical worker-monitoring measures. |
| Binding Constraint | Bindende Restriktion | Restrição vinculante | Primary bottleneck in a scenario. Here, humanoid Capex is not the binding constraint; demand (orders per hour) is. |
| Branches, Commits, and Tags | Branches, Commits und Tags | Branches, commits e tags | Git version-control terms: a commit is a saved change; a branch is an isolated workspace; a tag marks a release (e.g. v0.5.0). |
| Capacity Ceilings | Kapazitätsobergrenzen | Tetos de capacidade | Absolute maximum work a warehouse can finish in one shift before humans or robots max out (about 970–3,133 orders per shift by scenario). |
| Capex | Investitionsausgaben (Capex) | Capex (despesa de capital) | Capital expenditure: large upfront cost to buy physical assets such as humanoid robots or AMRs. |
| CI / CI-tested Parity | CI / CI-getestete Parität | CI / paridade testada por CI | Continuous Integration: automated quality checks on every change so new edits do not break rules or historical accuracy. |
| CI/CD | CI/CD (Kontinuierliche Integration/Bereitstellung) | CI/CD (Integração/Entrega Contínua) | Continuous Integration / Continuous Deployment. Here: every code update triggers automated tests for rules and historical accuracy. |
| Cost Parity | Kostenparität | Paridade de custos | Break-even where total robot cost equals total human-labor cost. |
| Cost Stack Chart | Kostenstapeldiagramm | Gráfico de pilha de custos | Dashboard chart stacking expense types (wages, electricity, licenses, maintenance) so readers see what makes up operating cost. |
| Cost/Order (€/order) | Kosten/Auftrag (€/Auftrag) | Custo/pedido (€/pedido) | Cost to process, pack, and ship one customer order. Simulation cheapest finding: €0.374 per order. |
| CRISP-DM | CRISP-DM | CRISP-DM | Cross-Industry Standard Process for Data Mining. Project methodology backbone. |
| CSI | Kanalzustandsinformation | Informação de Estado do Canal | Channel State Information. WiFi sensing primitive. Excluded from this project per Lock L2. |
| CSV | CSV (kommagetrennte Werte) | CSV (valores separados por vírgula) | Simple table file format (like a spreadsheet). Generated here so data can be imported into visual dashboards. |
| Cycle Time | Zykluszeit | Tempo de ciclo | Total time for a worker or robot to finish one repeating task end-to-end (e.g. pick an item and place it in a box). |
| Decision-Analysis Framework | Entscheidungsanalyse-Rahmen | Estrutura de análise de decisão | Structured approach using data, probabilities, and costs to choose between robots and humans instead of guessing. |
| Demand-Bound / Demand Frontier | Nachfragegebunden / Demand Frontier | Limitado pela demanda / fronteira de demanda | Constraint where operations are limited by customer orders (e.g. 120/hour), not by how fast robots can move. |
| Derisk Inspection Report | Derisk-Inspektionsbericht | Relatório de inspeção Derisk | Project file (`derisk_inspection_report.json`) reviewing data origins to show data is safe, traceable, and usable. |
| Determinism / Strict Reproducibility | Determinismus / strenge Reproduzierbarkeit | Determinismo / reprodutibilidade estrita | Core rule: the same math and code must yield the exact same results every time, with no random drift. |
| Discrete-Event Simulation | Ereignisdiskrete Simulation | Simulação de eventos discretos | Modeling that mimics a warehouse as a sequence of events (order arrives, robot moves, item placed). |
| DiverseManip Tasks | DiverseManip-Aufgaben | Tarefas DiverseManip | Complex varied physical actions in the robot dataset (e.g. two-arm handling of irregular objects), used as a warehouse proxy. |
| Docker / Dockerfile | Docker / Dockerfile | Docker / Dockerfile | Tool that packs code and settings into a container so the project runs the same way on any machine. |
| DOF | Freiheitsgrad | Grau de Liberdade | Degrees of Freedom. Unitree G1 has ~37 actuated DOF. |
| Domain-Transfer Risk | Domänentransfer-Risiko | Risco de transferência de domínio | Danger that data from one setting (e.g. home cleaning) may not match another (warehouse speeds). |
| DuckDB | DuckDB | DuckDB | In-process analytical database used to manage and query large tabular datasets. |
| Effect Decomposition | Effektzerlegung | Decomposição de efeitos | Breaking a result into separate causes (e.g. savings from cutting excess headcount vs. robots working faster). |
| Episode | Episode | Episódio | Single continuous recording of a robot executing a task. Unit of analysis in Module 1. |
| EVPI (Expected Value of Perfect Information) | EWPI (Erwartungswert perfekter Information) | VEIP (Valor Esperado da Informação Perfeita) | Monetary value of removing uncertainty: how much research is worth before buying robots. |
| evpi_eur | evpi_eur | evpi_eur | Code variable for EVPI in euros; used in the sensitivity report to rank which uncertainties are worth investigating. |
| External Validity | Externe Validität | Validade externa | Whether study results hold in the real world. Biggest threat here: treating household robot chores as warehouse performance. |
| F- (Finding Prefix) | F- (Finding-Präfix) | F- (prefixo de finding) | Internal IDs for audited findings (e.g. F-241, F-222, F-230). |
| Failure-Mode Taxonomy | Fehlermodus-Taxonomie | Taxonomia de modos de falha | Structured list of ways the math, code, or assumptions could be wrong or misleading. |
| Fair-Sizing Redesign (ADR-0014) | Fair-Sizing-Neudesign (ADR-0014) | Redesenho de dimensionamento justo (ADR-0014) | Documented change so optimized robots are compared to a lean human team, not an overstaffed legacy crew. |
| Frontier-Optimal / Lean Mix | Frontier-optimal / Lean-Mix | Mistura lean / frontier-ótimo | Most efficient, cost-effective worker–machine mix found by the simulation. |
| FTE / Headcount Assumptions | FTE / Personalannahmen | FTE / pressupostos de headcount | Full-Time Equivalent = one full-time employee. Changing headcount assumptions moves the financial math more than robot sticker price. |
| GitHub Actions / reproducibility.yml | GitHub Actions / reproducibility.yml | GitHub Actions / reproducibility.yml | GitHub automation for quality checks; `reproducibility.yml` runs a weekly determinism check. |
| Integration Cost | Integrationskosten | Custo de integração | Secondary costs to fit robots into a human environment (software, layout changes, training); included in the simulation. |
| Intralogistics | Intralogistik | Intralogística | Moving, packing, and tracking goods *inside* a warehouse or distribution center. |
| IRR | Interner Zinsfuß (IZF) | TIR (Taxa Interna de Retorno) | Internal Rate of Return. Financial metric in Module 3. |
| Jerk | Ruck | Jerk | Third derivative of position (derivative of acceleration). High jerk = rough motion = mechanical wear indicator. |
| Jupyter Notebook | Jupyter Notebook | Jupyter Notebook | Interactive document for code, narrative, and charts. |
| Knapp AG | Knapp AG | Knapp AG | Major intralogistics company near the author’s home in Austria; the project targets the math analysts at firms like Knapp face in 2026. |
| Kollektivvertrag (KV) | Kollektivvertrag (KV) | Convenção coletiva (KV) | Austrian sector-wide collective wage agreement. Source of legally mandated labor cost inputs used vs. robot costs. |
| Learning Curve | Lernkurve | Curva de aprendizado | Performance improving with practice. A 12-month robot learning curve is noted as a future accuracy upgrade. |
| Legacy-Overstaffed Reference | Legacy-Überbesetzung | Referência legacy sobredimensionada | The 8-human baseline: an inefficient overstaffed start. Comparing robots to it makes robots look artificially good. |
| LeRobot V2.0+ | LeRobot V2.0+ | LeRobot V2.0+ | Hugging Face standard dataset format for robot learning. Used by UnifoLM-WBT-Dataset. |
| Makefile / pyproject.toml / requirements.txt | Makefile / pyproject.toml / requirements.txt | Makefile / pyproject.toml / requirements.txt | Python project config files that define how to build the project and which package versions to install. |
| Modules 1–3 | Module 1–3 | Módulos 1–3 | Three sequential pipeline stages: extract timing from robot videos, run warehouse simulation, compute financial TCO. |
| Monte Carlo | Monte-Carlo-Simulation | Simulação de Monte Carlo | Runs the same scenario many times (10,000 here) with randomized inputs to estimate probabilities of financial outcomes. |
| Multi-Label Taxonomy | Multi-Label-Taxonomie | Taxonomia multi-rótulo | Categorization where one item can carry several labels under a strict rule set. |
| Multi-Shift Operation | Mehrschichtbetrieb | Operação em múltiplos turnos | Consecutive crews over 24 hours. Robots lose on a single shift today; multi-shift may look more favorable. |
| NPV | Kapitalwert (KW) / NPV | VPL (Valor Presente Líquido) | Net Present Value: present value of future costs/earnings at 8% discount. Here, total warehouse cost over 5 years; primary TCO decision metric. |
| OAT | Ein-Faktor-Sensitivität | OAT | One-at-a-time sensitivity: vary one parameter across its range while holding others fixed. |
| Open Source | Open Source / Quelloffen | Código aberto | Model where code, math, and data are public for anyone to inspect, copy, verify, or improve. |
| Opex | Betriebsausgaben (Opex) | Opex (despesa operacional) | Ongoing day-to-day costs: wages, robot maintenance, electricity, software subscriptions. |
| Opex-Only % | Opex-only-% | % somente Opex | Metric that shows day-to-day savings while ignoring Capex. Warned against: it makes pure-robot warehouses look falsely profitable. |
| p5–p95 (90% Output Interval) | p5–p95 (90%-Ausgabeintervall) | p5–p95 (intervalo de saída de 90%) | Range covering 90% of simulated outcomes, dropping the extreme best/worst 5% tails. |
| Pandera | Pandera | Pandera | Python library for DataFrame schema validation. Used for all data contracts. |
| Pick Tasks vs. Place Tasks | Pick- vs. Place-Aufgaben | Tarefas pick vs. place | Pick = grabbing an item (noisier, harder); Place = setting it down (easier), per intralogistics timings. |
| Pick-Lines Scaling / Per-Order Service-Time Scaling | Pick-Lines-Skalierung / Servicezeit pro Auftrag | Escala de pick-lines / tempo de serviço por pedido | Rules so complex orders take more pack time; not every order is treated as identical. |
| Pick-Move-Place Primitives | Pick-Move-Place-Primitive | Primitivas pick-move-place | Basic physical actions: grab, move, put down. |
| Pip install | pip install | pip install | Terminal command to download and install Python libraries. |
| Probability Mass | Wahrscheinlichkeitsmasse | Massa de probabilidade | Where most likely outcomes land. “Rank probability mass concentrated” means most of 10,000 runs point to one winner. |
| Provenance / Data Lineage | Provenienz / Datenherkunft | Proveniência / linhagem de dados | Trail of where each datum came from, how it was processed, and how it reached the report. |
| Proxy | Proxy / Ersatzmaß | Proxy / medida substituta | Substitute measure when exact data is missing; household robot chores proxy for warehouse humanoids. |
| Pull Request (PR) | Pull Request (PR) | Pull request (PR) | Request to merge changes into the main project; every PR is CI-tested before acceptance. |
| ρ (Rho) / ρ-Feasible / ρ≤0.85 Sizing Rule | ρ (Rho) / ρ-machbar / ρ≤0,85-Regel | ρ (rô) / ρ-viável / regra ρ≤0,85 | Utilization capacity. Plan humans/robots at most at 85% of max speed as a bottleneck buffer. |
| Replicas (Simulation Replicas) | Replikate (Simulationsreplikate) | Réplicas (de simulação) | Each of 7 scenarios is run 15 identical times so one random fluke does not dominate the average. |
| Reproduction Log | Reproduktionsprotokoll | Log de reprodução | Step-by-step record (`REPRODUCTION_LOG.md`) that the full simulation re-ran from scratch with the same numbers. |
| S- (Scenario Prefix) | S- (Szenario-Präfix) | S- (prefixo de cenário) | “S-” marks one of the seven human/robot configurations tested in the simulation. |
| S-future-2028 | S-future-2028 | S-future-2028 | 2028 scenario assuming cheaper, better humanoids; most viable humanoid-inclusive option, still loses to lean humans. |
| S-hybrid-5050 | S-hybrid-5050 | S-hybrid-5050 | Scenario with a 50/50 mix of human workers and robots. |
| S-hybrid-amr | S-hybrid-amr | S-hybrid-amr | Mix of humans, humanoids, and flat AMRs. |
| S-lean-human | S-lean-human | S-lean-human | Optimized team of 3 humans; fair baseline vs. robots (not the overstaffed 8-human warehouse). |
| S-lean-hybrid-amr | S-lean-hybrid-amr | S-lean-hybrid-amr | Most cost-effective scenario overall: 1 human + 3 AMRs, no humanoids. |
| S-pure-humanoid | S-pure-humanoid | S-pure-humanoid | All human workers replaced by humanoid robots. |
| SimPy | SimPy | SimPy | Python discrete-event simulation library. Powers Module 2 warehouse simulation. |
| SSOT | Einzige Informationsquelle (SSOT) | FÚVF (Fonte Única da Verdade) | Single Source of Truth. Ultimate rulebook (`PROJECT_CHARTER.md`); resolves disagreements on process. |
| Stingray | Stingray | Stingray | TGW shuttle-based warehouse architecture. Stub config in v1.0; full calibration v1.1. |
| success_rate=1.0 | success_rate=1.0 | success_rate=1.0 | Source videos only show successful completions; simulation assumes robots never drop or fail (optimistic). |
| Tableau Public | Tableau Public | Tableau Public | Public visual dashboard tool used to draw project graphs. |
| TCO | Gesamtbetriebskosten (GBK) / TCO | TCO (Custo Total de Propriedade) | Total Cost of Ownership: direct and indirect costs over 5 years (purchase, integration, maintenance, facility changes)—not just sticker price. |
| Technology-Mix Effects vs. Legacy-Crew Sizing Effects | Technologie-Mix- vs. Legacy-Besetzungseffekte | Efeitos de mix tecnológico vs. dimensionamento legacy | Savings split: legacy-crew = firing excess humans from overstaffing; technology-mix = gains/losses from introducing robots. |
| Telemetry | Telemetrie | Telemetria | Live machine-recorded work data. Warehouse-native task telemetry (not home chores) is the top future-model need. |
| Teleoperation | Fernsteuerung | Teleoperação | Remote operation of a robot by a human pilot. UnifoLM-WBT is teleoperated data. |
| Third-Party Stranger-Clone Verification | Fremdverifikation durch Dritte | Verificação clone por terceiro estranho | Independent outsider downloads and runs the code. Not done yet; only an AI agent surrogate has verified so far. |
| Throughput Benchmarks | Durchsatz-Benchmarks | Benchmarks de throughput | Real performance records (e.g. boxes/hour at Knapp). Real benchmarks would improve future versions. |
| Tornado Chart | Tornado-Diagramm | Gráfico tornado | Bar chart showing which inputs (electricity vs. wages, etc.) move total cost the most. |
| Transfer factor | Transferfaktor | Fator de transferência | Multiplier (0.50–0.90) slowing household-chore robot timings to reflect harder warehouse box handling. |
| UnifoLM / UnifoLM-WBT | UnifoLM / UnifoLM-WBT | UnifoLM / UnifoLM-WBT | Unitree open whole-body teleoperation dataset (~2,359 episodes) used for robot speed estimates; primary data source. |
| Unit Economics | Stückkostenrechnung / Unit Economics | Unit economics | Direct costs/revenues per business unit (one order). Focuses on math reality over humanoid hype. |
| Utilisation (ρ) | Auslastung (ρ) | Utilização (ρ) | Queueing utilisation ρ = λ·E[S]/c. Scenarios are gated at ρ ≤ 0.85 for capacity ceilings. |
| uv | uv | uv | Tool that installs and locks language/package versions needed to run the project. |
| Wage Arbitrage | Lohnarbitrage | Arbitragem salarial | Replacing workers to chase cheaper labor. In Austrian warehouses the driver is unfillable vacancies more than expensive wages. |
