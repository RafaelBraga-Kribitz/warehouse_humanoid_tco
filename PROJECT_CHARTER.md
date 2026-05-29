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
| 4 | [📚 Full Documentation Index](#4-full-documentation-index) | Where to find detailed specs, ADRs, and version history |

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

## 2. 📋 Documentation Discipline

**This file is the SSOT.** No parallel requirements, spec, or design documents. State it once, link everywhere else. Every scope change needs an ADR in `governance/adrs/`. Every content change needs a `governance/CHANGELOG.md` entry and a `last_updated` bump. CI enforces staleness (≤14 days), Markdown sprawl, and ADR structure on every push.

Full rules: `CONTRIBUTING.md` and `governance/AUDIT_PROCEDURE.md`.

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
| **Market Signal** | ≥1 documented response from Austrian industrial firm (LinkedIn/recruiter/interview) within 4 weeks of release | Tracked in `governance/CHANGELOG.md` |
| **Doc Quality** | SSOT is sole authority; CI passes ≥30 days post-release with zero sprawl | CI stats in weekly reproducibility report |

### 3.4 Stakeholders

| Stakeholder | Role | Engagement |
|---|---|---|
| Rafael Braga | Owner, sole contributor | Daily |
| Recruiters at Knapp AG | Primary audience for portfolio | Targeted via LinkedIn post + repo link |
| Recruiters at TGW Logistics | Primary audience for portfolio | Targeted via LinkedIn post + repo link |
| Recruiters at Magna Steyr | Secondary audience | Reached via LinkedIn organic |
| Robotics Network Austria (JOANNEUM RESEARCH, Graz) | Potential amplifier | Direct outreach after v1.0 |
| Betriebsrat (Works Council) — *simulated* | Co-determination authority under ArbVG §96 (1) 3; treats Betriebsrat sign-off as a deployment precondition | Simulated review at every doc commit |

### 3.5 Business Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Project takes longer than 10 weeks | High | Medium | Hard scope cap at AutoStore-only v1.0; stub configs for other architectures |
| Recruiters do not engage | Medium | High | LinkedIn-first launch strategy; German one-pager; direct outreach to specific company recruiters |
| Dataset proves insufficient | Medium | High | Module 0 de-risk notebook validates before commit; fallback to synthetic supplementation with full disclosure |
| Substitution-framing causes backlash | Low (mitigated by framing) | Critical | Framing locked: "augmentation + ROI", never "replacement"; Betriebsrat-aware language audit at every doc commit |
| Betriebsrat veto under ArbVG §96 (1) 3 | Medium | **Critical** | No monitoring features; augmentation framing; pre-pilot consultation assumed; TCO surfaces labor-cost-share for council review |
| Project becomes too ambitious mid-flight | High | High | Scope Guardrails §9 enforced ruthlessly |

### 3.6 Out of Scope (v1.0)

No human activity sensing, RuView, or CSI. No Stingray / Magna full calibration (stubs only). No ML capability prediction, real-time data ingestion, or live system integrations. Adding any of these requires an ADR + scope-change review. Full list: `governance/SCOPE_LOCKS.md`.

### 3.7 Known Limitations

Key constraints: WBT cycle times are teleoperation demos (0.70× transfer factor applied; range 0.50–0.90× in Monte Carlo); 15 simulation replicas per scenario; no real warehouse telemetry (calibrated against Knapp public benchmarks); humanoid capex ±40% (public pricing, not contracts); Austrian KV 2026 estimated ±10%. Full table: `governance/LIMITATIONS.md`.

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
| **Repository Structure (canonical)** | Canonical layout with every subdirectory explained | `governance/REPO_STRUCTURE.md` |
| **SRS + CLI + Testing + Logging** | Modules 0–4, CLI spec, test strategy, determinism requirements | `governance/MODULE_SPECS.md` |

### 4.4 🛡️ Governance & Scope

Three hard scope locks (L1: AutoStore-only; L2: no human sensing; L3: empirical capabilities). 5-question anti-creep checklist. Sprawl/shiny-new-thing tripwires. Full rules: `governance/SCOPE_LOCKS.md`.

### 4.5 📝 Version History & ADRs

| Document | Purpose | Location |
|---|---|---|
| **Project Change Log** | Version history, audit fixes, module completions | `governance/CHANGELOG.md` |
| **ADRs (0001–0007+)** | Immutable, append-only decision log with status & YAML frontmatter | `governance/adrs/` |

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
