# Quality Transformation Program — Blueprint

Condensed executable charter for Phases 0–3. Full execution detail lives in
`.cursor/plans/quality_transformation_program_d1a0e443.plan.md` (Execution Spec v2).
Audit grounding: commit `d284a99`.

## Operating model

Reuse `governance/AUDIT_PROCEDURE.md` only. One open finding per PR. Verification
script before closure. Adversary re-runs closed scripts forever. Number-changing
PRs regenerate presentation artifacts (`make presentation` / F-043).

## Phase table

| Phase | Findings | Goal |
|---|---|---|
| Bootstrap | F-200 | File queue + this blueprint |
| 0 Credibility | F-201–F-207 | Kill five-minute trust leaks |
| 1 Highest ROI | F-210–F-219 | Decision-first packaging + SQL layer |
| 2 Consulting | F-220–F-230, F-236 | Fair model + memos + deck + claims |
| 3 World class | F-231–F-235 | EVPI, frontiers, publication, packaging |

## Finding queue (one-line goals)

- **F-201** Hero banner (user Figma) — BLOCKED-ON-USER
- **F-202** Charter link-truth + `check_internal_links.py`
- **F-203** Single ADR home (`governance/adrs/`)
- **F-204** Delete empty taxonomy CSV; publish rule-based taxonomy
- **F-205** `unmodeled_parameters` partition with signed bias
- **F-206** DE summary uses total-cost NPV reduction
- **F-207** Repo-relative paths in report JSON
- **F-210** Canonical decision statement + labor scarcity
- **F-211** EXPERIMENTS.md H1–H4 machine-checked verdicts
- **F-212** `S-lean-human` fair comparator
- **F-213** Household→warehouse external validity disclosure
- **F-214** Chart design system + MC whiskers + manifest
- **F-215** README decision-first rewrite + positioning
- **F-216** Recruiter PDF (not `.qmd`)
- **F-217** Property tests + golden masters
- **F-218** LICENSE_COMPLIANCE.md
- **F-219** DuckDB SQL provenance for Tableau CSVs
- **F-220** Crew-size enumerator
- **F-221** Fair scenario redesign + decomposition chart
- **F-222** Availability / integration / wage growth / residual
- **F-223** Cost taxonomy + €1 reconciliation
- **F-224** CRN + P(rank 1) + cycle-time MC
- **F-225** Frontiers + Sobol + SENSITIVITY.md v2
- **F-226** Generated ASSUMPTION_REGISTER.md
- **F-227** DE/EN decision memos + challenge FAQ
- **F-228** Exhibit deck (Quarto)
- **F-229** dbt-duckdb validation layer
- **F-230** Third-party REPRODUCTION_LOG — BLOCKED-ON-USER
- **F-231** EVPI per MC parameter
- **F-232** Multi-shift / demand frontier
- **F-233** Case study + CITATION.cff — partial USER
- **F-234** Packaging + MAINTENANCE.md
- **F-235** Pyright strict + coverage ≥90%
- **F-236** Claims ledger + citation audit

## Success definition

Hostile reader cannot find: banner typo, dead SSOT links, dual ADRs, empty fake
provenance, decorative config without signed bias, opex/NPV savings contradiction,
or unfair 8-vs-6 crew comparison. Every published CSV has SQL provenance (F-219).
Recommendation + viability trigger + dominant risk are answer-first in README and DE PDF.

## BLOCKED-ON-USER

F-201 (Figma banner), F-215 (Tableau screenshot), F-221 (Tableau republish),
F-230 (stranger reproduction), F-233 (external reviewer). Agent completes all
non-blocked work first; blocked findings stay `open` under the ratchet.
