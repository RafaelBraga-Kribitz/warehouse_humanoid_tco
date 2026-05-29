<!--
================================================================================
PROJECT CHARTER: Single Source of Truth (SSOT)
================================================================================
This document is the ONLY authoritative source for project goals, scope,
requirements, and design decisions.

RULES (enforced by CI):
  1. Any project decision that is not in this document or in docs/ADR/ does
     not exist.
  2. Changes to anything in this file require a corresponding ADR entry.
  3. README.md, notebooks, and code docstrings MAY summarize from this file
     but MUST link back here for authority.
  4. The metadata block below is machine-read by .github/workflows/docs-ssot-check.yml.
     Do not edit the metadata format without updating the workflow.

DO NOT create separate Charter.md, Requirements.md, SRS.md, etc.
Sprawl is forbidden. If a section here gets too large, split into a sibling
file under docs/, link it from the Table of Contents, and add an ADR.
================================================================================
-->

<!-- SSOT_METADATA_START
version: 1.1.4
status: active
last_updated: 2026-05-27
last_reviewed: 2026-05-27
owner: Rafael Braga
project_codename: warehouse_humanoid_tco
crisp_dm_phase: evaluation
module_status: Modules 0–4 complete on real data (2,359 episodes); Tableau Public and LinkedIn outreach pending
SSOT_METADATA_END -->

# 📋 Project Charter: Warehouse Humanoid TCO Analyzer

> **🎯 This is the Single Source of Truth (SSOT)** for the project. If you are looking for what the project is, what it does, what it does not do, or why a decision was made, **the answer is here or it is in [`docs/ADR/`](./docs/ADR/).** Nowhere else. CI enforces this discipline.

## Table of Contents

| # | Section | Purpose |
|---|---------|---------|
| 1 | [⚡ Quick Facts](#1-quick-facts) | Project metadata at a glance |
| 2 | [📋 Documentation Discipline](#2-documentation-discipline-read-this-first) | SSOT rules, CI enforcement, ADR format |
| 3 | [🎯 Business Case / Charter](#3-business-case--project-charter) | Goals, success criteria, stakeholders, risks |
| 4 | [📚 Full Documentation Index](#4-full-documentation-index) | Where to find detailed specs, ADRs, and change log |

---

## 1. ⚡ Quick Facts

| Field | Value |
|---|---|
| Project codename | `warehouse_humanoid_tco` |
| Owner | Rafael Braga, Seiersberg-Pirka, Austria |
| Primary goal | Build a recruiter-ready DA/BI portfolio piece for Austrian industrial employers (Knapp AG, TGW Logistics, Magna Steyr) |
| Secondary goal | Produce a reproducible analytical framework for humanoid robot TCO that has analytical value beyond the portfolio |
| Time budget | 8 to 10 weeks part-time |
| Status | v1.0 complete. All 4 modules shipped with real data (2,359 episodes). Tableau Public publication and external outreach pending. |
| Repo structure | See SRS §8 |

---

## 2. 📋 Documentation Discipline (read this first)

### 2.1 🎯 Single Source of Truth (SSOT) Rule

**This file is the SSOT.** The README, notebooks, and code comments may reference it, but must not duplicate it. **Duplication creates drift. Drift creates lies.**

Allowed:
- `README.md` may quote 1 to 2 sentences from this file and link to the relevant section.
- Notebook markdown cells may state the objective of the notebook and link here for context.
- Docstrings may reference function-level intent and link to relevant sections.

Forbidden:
- Standalone "requirements.md", "spec.md", "design.md", or any document that duplicates content present here.
- Re-stating the project goal in multiple places. State it once, link everywhere else.

### 2.2 Change Discipline

Every change to this file requires:

1. A new ADR in `docs/ADR/` if the change alters scope, requirements, or architecture.
2. An entry in the [Change Log](#11-change-log) at the bottom of this file.
3. An update of the `last_updated` metadata at the top of this file.
4. A passing CI check (`.github/workflows/docs-ssot-check.yml`).

Trivial fixes (typos, formatting, link repair) do not require an ADR but DO require a Change Log entry.

### 2.3 🏛️ ADR Format (Immutable Decision Log)

ADRs are numbered, dated, **immutable**, and **append-only**. Format:

```
docs/ADR/NNNN-kebab-case-title.md
```

**Required sections:** Title, Date, Status (`proposed`/`accepted`/`superseded`), Context, Decision, Consequences, References.

**Key rule:** Once accepted, an ADR is **never edited**. If superseded, write a **new** ADR referencing the old one. This preserves decision history for recruiters and your future self.

### 2.4 Anti-Sprawl Rules

If you catch yourself doing any of these, stop:

| Anti-pattern | What to do instead |
|---|---|
| Creating a new `.md` file for a new topic | Add a section to this file or write an ADR |
| Repeating the project goal in 3 places | State it once here, link from elsewhere |
| Putting design decisions in commit messages | Write an ADR |
| Putting requirements in GitHub Issues | Write them here, link the issue |
| Storing tribal knowledge in your head | Write it here within 24 hours or it does not exist |
| Adding a "TODO" comment | Add it to the [Backlog](#52-backlog) section here |

### 2.5 🤖 Automated Enforcement via CI

CI runs [`.github/workflows/docs-ssot-check.yml`](./.github/workflows/docs-ssot-check.yml) on **every push**:

| Check | Rule | Failure |
|-------|------|---------|
| **Staleness** | `last_updated` ≤ 14 days old | Build fails |
| **Sprawl** | No `.md` files outside allowlist | Build fails |
| **ADR structure** | Every ADR has required headings | Build fails |
| **Change Log** | Every SSOT edit has a log entry | Build fails |

**Philosophy:** The CI is the SSOT's immune system. Do not disable it. If CI is blocking you, the block is telling you something true about your change.

---

## 3. 🎯 Business Case / Project Charter

### 3.1 Problem Statement

Austrian intralogistics and manufacturing leaders (Knapp AG, TGW Logistics, voestalpine, Magna Steyr) are evaluating humanoid robots from Unitree, Apptronik, Figure, and Agility for warehouse and production tasks. As of 2026, there is no publicly available, reproducible analytical framework that:

1. Grounds humanoid capabilities in observed empirical data rather than vendor marketing.
2. Translates those capabilities into operational simulations under realistic Austrian conditions.
3. Quantifies financial impact (TCO, NPV, IRR, payback) given Austrian labor cost structures (Kollektivvertrag) and capital cost assumptions.
4. Surfaces results in a BI dashboard accessible to non-technical decision-makers.

### 3.2 Project Goal

Build that framework, end-to-end, using only public data sources, and publish it as open-source under MIT license.

### 3.3 ✅ Success Criteria

The project succeeds if **all four** of these are true at completion:

| Criterion | Measurement | Verification |
|---|---|---|
| **Reproducibility** | Stranger clones repo, runs `make all`, reproduces every artifact bit-for-bit | CI weekly determinism test |
| **Analytical Credibility** | TCO model exposes every assumption as configurable param; top 6 drivers identified | `reports/sensitivity_analysis_report.json` + tornado chart |
| **Market Signal** | ≥1 documented response from Austrian industrial firm (LinkedIn/recruiter/interview) within 4 weeks of release | Tracked in Change Log §11 |
| **Doc Quality** | SSOT is sole authority; CI passes ≥30 days post-release with zero sprawl | CI stats in weekly reproducibility report |

### 3.4 Stakeholders

| Stakeholder | Role | Engagement |
|---|---|---|
| Rafael Braga | Owner, sole contributor | Daily |
| Recruiters at Knapp AG | Primary audience for portfolio | Targeted via LinkedIn post + repo link |
| Recruiters at TGW Logistics | Primary audience for portfolio | Targeted via LinkedIn post + repo link |
| Recruiters at Magna Steyr | Secondary audience | Reached via LinkedIn organic |
| Robotics Network Austria (JOANNEUM RESEARCH, Graz) | Potential amplifier | Direct outreach after v1.0 |
| Betriebsrat (Works Council) — *simulated* | Co-determination authority over deployment of worker-monitoring or workforce-substitution technology under **ArbVG §96 (1) 3**. No active engagement in v1.0 (simulated stakeholder); model framing and language audit (§NFR-10) treats Betriebsrat sign-off as a deployment precondition. | Simulated review at every doc commit |

### 3.5 Business Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Project takes longer than 10 weeks | High | Medium | Hard scope cap at AutoStore-only v1.0; stub configs for other architectures |
| Recruiters do not engage | Medium | High | LinkedIn-first launch strategy; German one-pager; direct outreach to specific company recruiters |
| Dataset proves insufficient | Medium | High | Module 0 de-risk notebook validates before commit; fallback to synthetic supplementation with full disclosure |
| Substitution-framing causes backlash | Low (mitigated by framing) | Critical | Framing locked: "augmentation + ROI", never "replacement"; Betriebsrat-aware language audit at every doc commit |
| **Deployment blocked by Betriebsrat veto under ArbVG §96 (1) 3** (Austrian Labour Constitution Act — co-determination rights over the introduction of control / monitoring systems affecting worker dignity, and over workforce-substitution measures) | Medium | **Critical** | (1) No worker-monitoring features in v1.0 (Out-of-Scope §3.6); (2) framing locked to "augmentation, not replacement"; (3) deployment plan assumes Betriebsrat consultation phase BEFORE any pilot; (4) TCO model surfaces labor-cost-share alongside humanoid-capex so the works council can verify no net headcount cut is required for the business case to hold |
| Project becomes too ambitious mid-flight | High | High | Scope Guardrails §9 enforced ruthlessly |

### 3.6 Out of Scope (v1.0)

The following are explicitly excluded from v1.0. Adding any of these requires an ADR and a scope-change review:

- Worker activity sensing (WiFi CSI, RuView integration, any human monitoring)
- Stingray / FlashPick architecture full calibration (stub only)
- Magna automotive line architecture full calibration (stub only)
- Real-time data ingestion
- Multi-language UI beyond English + a single-page German executive summary
- ML-based capability prediction (capabilities are extracted empirically, not predicted)
- Live integration with company systems (SAP, ERP, WMS)
- Mobile app
- Web service deployment of the model (it ships as a repo + dashboards only)

### 3.7 Known Limitations and External Validity Boundaries

| Limitation | Impact | Mitigation |
|---|---|---|
| WBT teleoperation cycle times ≠ production throughput | Overestimates humanoid speed by unknown factor | Applied 0.70× transfer factor (configurable; see `config/autostore_baseline.yaml`); Monte Carlo range covers 0.50–0.90× |
| 15-replica simulation runs | Moderate variance in scenario comparison | 90% CI reported on all throughput metrics; sufficient for portfolio-level comparison |
| No real warehouse telemetry | Cannot validate against actual Knapp operations | Baseline calibrated against public Knapp AutoStore throughput benchmarks (§7.5) |
| Humanoid capex from public pricing, not contracts | ±40% cost uncertainty | Full Monte Carlo range €80K–€200K/unit; tornado chart shows sensitivity |
| Austrian Kollektivvertrag 2026 estimated, not official | ±10% labor cost uncertainty | Documented range in `config/tco_assumptions.yaml`; dominant sensitivity driver |
| No human fatigue modeling | Overestimates human baseline throughput | Acknowledged; absence_rate_per_shift partially compensates |
| WBT dataset is teleoperation demos, not autonomous ops | Transfer to autonomous production unknown | 0.70× factor; this is the single largest assumption — see §2A |

---

## 4. 📚 Full Documentation Index

This section points to everything beyond the executive summary. **The SSOT rule still applies**: if it's not here or in an ADR, it does not exist.

### 4.1 🎯 Requirements & Specification

| Document | Purpose | Location |
|---|---|---|
| **CRISP-DM Phase Mapping** | How each module maps to the CRISP-DM lifecycle | `governance/adrs/0001-*.md` |
| **Functional Requirements (FR-01 to FR-15)** | All Must/Should/Could/Won't requirements with MoSCoW priority | `governance/REQUIREMENTS.md` |
| **Non-Functional Requirements** | Reproducibility, quality, performance, documentation, ethics | `governance/REQUIREMENTS.md` |
| **Backlog (BL-01 to BL-05)** | Future scope, managed via ADR | `governance/REQUIREMENTS.md` |
| **Technology Stack (locked)** | Python 3.11, uv, polars, SimPy, Tableau, Quarto, etc. | `governance/TECH_STACK.md` |
| **Coding Standards** | snake_case, type hints, docstrings, no magic numbers | `CONTRIBUTING.md` |

### 4.2 📊 Data & Experiment Design

| Document | Purpose | Location |
|---|---|---|
| **Data Sources (authoritative list)** | WBT datasets, DiverseManip, reference data, all SHAs pinned | `governance/DATA_SOURCES.md` |
| **Data Storage Layout** | `data/raw/`, `data/interim/`, `data/processed/` structure | `governance/DATA_STORAGE.md` |
| **Pandera Schemas** | `EpisodeMetadataSchema`, `HumanoidCapabilityPerEpisodeSchema`, etc. | `src/warehouse_humanoid_tco/data/schemas.py` |
| **Experiment Hypotheses (H1–H4)** | Four testable hypotheses with decision rules and status | `governance/EXPERIMENTS.md` |
| **Scenarios (S-baseline-human, S-hybrid-amr, etc.)** | Five workforce composition scenarios | `governance/EXPERIMENTS.md` |
| **Sensitivity Analysis Protocol** | OAT + Monte Carlo, 5 continuous parameters, common random numbers | `governance/SENSITIVITY.md` |
| **References (7 peer-reviewed sources)** | Knapp, Kimms & Schade, Unitree, Boston Dynamics, Wächter, Statistik Austria, WKO | `governance/REFERENCES.md` |

### 4.3 💻 Software Design

| Document | Purpose | Location |
|---|---|---|
| **Repository Structure (canonical)** | 500+ line canonical layout with every subdirectory explained | `governance/REPO_STRUCTURE.md` |
| **SRS Module Descriptions** | Modules 0–4 with entry points and expected outputs | `governance/MODULE_SPECS.md` |
| **CLI Interface (Should, not Must)** | Seven `python -m warehouse_humanoid_tco` commands | `governance/CLI_SPEC.md` |
| **Testing Strategy** | Unit, schema, reproducibility, smoke tests; 70%+ coverage target | `governance/TESTING.md` |
| **Logging & Observability** | Structured JSON logging via `utils/logging.py` | `governance/LOGGING.md` |
| **Determinism Requirements** | Byte-for-byte reproducibility, seeded RNG, weekly hash comparison | `governance/DETERMINISM.md` |

### 4.4 🛡️ Governance & Scope

| Document | Purpose | Location |
|---|---|---|
| **Scope Guardrails (L1–L3)** | Three hard locks: AutoStore-only, no sensing, empirical capabilities | `governance/SCOPE_LOCKS.md` |
| **Anti-Creep Checklist** | 5-question checklist before adding any feature | `governance/SCOPE_LOCKS.md` |
| **Shiny New Thing Rule** | When new tools/datasets appear: add to Backlog, don't code | `governance/SCOPE_LOCKS.md` |
| **Documentation Sprawl Tripwire** | "Design doc" / "README subfolder" / "separate spec" = forbidden | `governance/SCOPE_LOCKS.md` |

### 4.5 📝 Change Log & Decision History

| Document | Purpose | Location |
|---|---|---|
| **Project Change Log (v1.0.0–v1.1.4)** | Version history, audit fixes, module completions | `governance/CHANGELOG.md` |
| **Architecture Decision Records (ADR-0001+)** | Immutable, append-only decision log with status & references | `governance/adrs/` |
| **ADR-0001: Use SSOT Charter** | Why this document is the single source of truth | `governance/adrs/0001-use-ssot-charter.md` |
| **ADR-0002: Ethics Boundary** | No PII, no human-activity sensing, Betriebsrat-aware framing | `governance/adrs/0002-ethics-boundary.md` |
| **ADR-0003: AutoStore-Only v1.0** | Stingray & Magna as stubs only; scope lock L1 | `governance/adrs/0003-autostore-only-v1.md` |
| **ADR-0004: Dual Publish (Tableau + Power BI)** | Why both dashboards; justification for upload overhead | `governance/adrs/0004-dual-publish-dashboards.md` |
| **ADR-0005–0007** | Additional decisions as they arise (see `governance/adrs/` directory) | `governance/adrs/` |

### 4.6 📚 Quick Reference

| Document | Purpose | Location |
|---|---|---|
| **Glossary (German-English-Portuguese)** | AMR, AutoStore, Betriebsrat, CRISP-DM, CSI, Kollektivvertrag, LeRobot, SSOT, TCO, UnifoLM-WBT | `docs/glossary.md` |
| **README (≤200 lines)** | Quick start, badge links, pointer to this SSOT | `README.md` |
| **CONTRIBUTING.md** | How to contribute; links to SSOT and governance/ | `CONTRIBUTING.md` |

### 4.7 Configuration Reference

All project parameters live in `config/`:

| File | Contents |
|---|---|
| `seeds.yaml` | All RNG seeds for reproducibility |
| `autostore_baseline.yaml` | AutoStore simulation parameters (layout, shift, order arrival λ) |
| `tco_assumptions.yaml` | Financial assumptions (discount rate, MTBF, labor costs, capex ranges) |
| `stingray_stub.yaml` | Stingray architecture (stub, not calibrated in v1.0) |
| `magna_stub.yaml` | Magna automotive line (stub, not calibrated in v1.0) |
| `dataset_manifest.yaml` | HF dataset SHAs, versions, accessibility, size |

---

<!-- END OF SSOT. Any content below this line is a violation. -->
