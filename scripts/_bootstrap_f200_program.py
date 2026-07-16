"""One-shot generator for F-200 Quality Transformation Program bootstrap.

Creates QUALITY_BLUEPRINT.md, finding YAMLs F-200..F-236, and stub verification
scripts. Run from repo root: python scripts/_bootstrap_f200_program.py
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FINDINGS = REPO / "governance" / "findings"
TODAY = "2026-07-16"

# id -> (title, category, kind, verification_script, evidence, acceptance)
FINDING_SPECS: dict[str, tuple[str, str, str, str, str, str]] = {
    "F-200": (
        "Quality Transformation Program filed as F-201+ queue + QUALITY_BLUEPRINT.md",
        "governance_gaps",
        "recurrence_invariant",
        "scripts/check_program_filed.py",
        "Program not yet filed as machine-readable findings.",
        "Every ID in {F-201..F-207, F-210..F-219, F-220..F-230, F-231..F-236} has YAML with evidence + verification_script; QUALITY_BLUEPRINT.md exists.",
    ),
    "F-201": (
        "Hero banner: integrate user-provided Figma banner (text-free of typos)",
        "fake_completion",
        "recurrence_invariant",
        "tests/governance/test_f201_banner.py",
        "docs/assets/hero-banner.png shows SEENITIVITY typo and garbled robot-chest text.",
        "PNG width>=1600; size 20KB-1.6MB; finding notes contain text-transcription:; no misspelled above-fold text. BLOCKED-ON-USER for Figma file.",
    ),
    "F-202": (
        "Charter documentation index truth + internal link gate",
        "documentation_entropy",
        "recurrence_invariant",
        "scripts/check_internal_links.py",
        "PROJECT_CHARTER.md indexes 11 nonexistent governance/*.md files.",
        "Zero dead internal links in Charter/README/CLAUDE.md/governance; load-bearing docs restored; consolidations ADR'd.",
    ),
    "F-203": (
        "Single ADR home at governance/adrs/",
        "fragmented_standards",
        "recurrence_invariant",
        "scripts/check_single_adr_home.py",
        "The legacy ADR directory and governance/adrs/ diverge with differing shared content.",
        "Legacy ADR directory absent; zero legacy ADR refs; governance/adrs/ has >=12 md files.",
    ),
    "F-204": (
        "Empty taxonomy review CSV resolved (delete + honest rule-based description)",
        "fake_completion",
        "recurrence_invariant",
        "tests/governance/test_f204_taxonomy_provenance.py",
        "The former manual taxonomy review CSV had 0 data rows but claimed provenance.",
        "CSV gone; docs/taxonomy_rules.md has >=4 rules; README says rule-based; no remaining refs.",
    ),
    "F-205": (
        "Decorative config triage — unmodeled_parameters partition with signed bias",
        "dead_artifacts",
        "recurrence_invariant",
        "scripts/check_config_consumption.py",
        "MTBF/battery/integration/wage_growth/residual etc. in config but unread by src/.",
        "Every leaf config key consumed in src/ OR listed in unmodeled_parameters with bias.",
    ),
    "F-206": (
        "DE executive summary metric alignment to total-cost NPV reduction",
        "numeric_drift",
        "recurrence_invariant",
        "tests/governance/test_f206_de_metric.py",
        "Executive_Summary_DE.qmd presents opex-only Kostenersparnis contradicting README.",
        "QMD % matches CSV total_cost_reduction; no 70%-class opex savings claim; date>=2026-07-01.",
    ),
    "F-207": (
        "Absolute paths scrubbed from committed reports",
        "fragmented_standards",
        "recurrence_invariant",
        "scripts/check_no_abs_paths.py",
        "reports/*.json embed /home/user/warehouse_humanoid_tco/ absolute paths.",
        "Zero absolute path matches in reports/ and exports/; writers use repo_relative().",
    ),
    "F-210": (
        "Canonical decision statement in Charter + README Decision summary",
        "missing_artifact",
        "missing_artifact",
        "scripts/check_decision_statement.py",
        "No named decision owner/options/trigger; results bury the recommendation.",
        "DECISION_STATEMENT delimiters in Charter; README quotes >=120 chars verbatim; labor scarcity sentence; capex trigger matches breakeven JSON.",
    ),
    "F-211": (
        "EXPERIMENTS.md H1-H4 with numeric rules and machine-checked verdicts",
        "missing_artifact",
        "missing_artifact",
        "scripts/check_hypothesis_verdicts.py",
        "Charter references EXPERIMENTS.md H1-H4 but file is missing/stub.",
        "4 VERDICT H lines; H2/H3/H4 recomputed from artifacts match stated verdicts.",
    ),
    "F-212": (
        "Add S-lean-human scenario sized by rho<=0.85 rule",
        "methodology_drift",
        "recurrence_invariant",
        "tests/governance/test_f212_lean_human.py",
        "S-hybrid-amr fields 6 units vs 8-human baseline; no lean-human comparator.",
        "S-lean-human in config/CSV/README; human<=7; rho(N)<=0.85 recomputed.",
    ),
    "F-213": (
        "External validity — household UnifoLM tasks disclosed in README",
        "methodology_drift",
        "recurrence_invariant",
        "tests/governance/test_f213_validity_disclosure.py",
        "Empirical capabilities claim omits that source episodes are household tasks.",
        "README External validity section with household; LIMITATIONS domain-transfer row.",
    ),
    "F-214": (
        "Chart design system + regenerated executive charts with uncertainty",
        "stale_generated_outputs",
        "recurrence_invariant",
        "tests/governance/test_f214_chart_system.py",
        "Charts use matplotlib defaults, negative NPV axes, no MC whiskers, inverted colors.",
        "chart_style.py palette hexes; module_04 imports chart_style; whiskers wired; manifest hashes.",
    ),
    "F-215": (
        "README decision-first rewrite with persona paths and positioning",
        "documentation_entropy",
        "recurrence_invariant",
        "tests/governance/test_f215_readme_structure.py",
        "Buried lede; DA/BI self-label; no decision box; recruiter path broken.",
        "<=200 lines; Decision summary in first 30 lines; no DA/BI phrase; How this was built; 3 persona links.",
    ),
    "F-216": (
        "Rendered DE PDF + recruiter link to PDF not QMD",
        "fake_completion",
        "recurrence_invariant",
        "tests/governance/test_f216_recruiter_artifact.py",
        "Recruiter link lands on raw .qmd source.",
        "PDF exists with %PDF magic; README recruiter link ends .pdf.",
    ),
    "F-217": (
        "Property-test lattice + golden masters for TCO kernels",
        "governance_gaps",
        "recurrence_invariant",
        "tests/test_tco_properties.py",
        "No property tests before Phase-2 model rewires.",
        ">=6 property invariants; golden_masters.json + test; assertion audit table in notes.",
    ),
    "F-218": (
        "UnifoLM license compliance memo",
        "missing_artifact",
        "missing_artifact",
        "scripts/check_license_memo.py",
        "Committed LFS data has no redistrib/license audit artifact.",
        "LICENSE_COMPLIANCE.md has one row per dataset with recognized license token.",
    ),
    "F-219": (
        "Analytical SQL layer via DuckDB for published Tableau CSVs",
        "missing_artifact",
        "missing_artifact",
        "tests/governance/test_f219_sql_parity.py",
        "duckdb declared but unused; Tableau CSVs from opaque polars passthrough.",
        "SQL files + parity test; module_04 uses DuckDB SQL path; numeric parity on tco sum.",
    ),
    "F-220": (
        "Crew-size enumerator — min-cost integer crews subject to rho",
        "missing_artifact",
        "missing_artifact",
        "tests/governance/test_f220_optimizer.py",
        "Crew sizes hand-picked; no optimization module.",
        "crew_optimizer.py; neighborhood optimality test; determinism.",
    ),
    "F-221": (
        "Fair scenario redesign using optimizer + effect decomposition",
        "methodology_drift",
        "recurrence_invariant",
        "tests/governance/test_f221_fair_scenarios.py",
        "Headline comparison confounds headcount with technology.",
        "All agent_counts match optimizer; chart 06 exists; README decomposition; golden masters updated.",
    ),
    "F-222": (
        "Material realism — availability, integration, wage growth, residual, supervision",
        "methodology_drift",
        "recurrence_invariant",
        "tests/governance/test_f222_realism.py",
        "Config promises MTBF/battery/integration/wage_growth but model ignores them.",
        "Availability derates cycle time; integration in capex; wage growth; residual salvage; supervision in OAT/MC.",
    ),
    "F-223": (
        "Cost taxonomy + euro-exact reconciliation + auditor worksheet",
        "missing_artifact",
        "missing_artifact",
        "tests/governance/test_f223_reconciliation.py",
        "No taxonomized cost lines reconciling to NPV; hardcoded baseline opex fallback.",
        "cost_line_breakdown sums to NPV within EUR1; auditors_worksheet.md; no _BASELINE_ANNUAL_OPEX.",
    ),
    "F-224": (
        "Common random numbers + P(rank 1) + operational MC input",
        "methodology_drift",
        "recurrence_invariant",
        "tests/governance/test_f224_crn.py",
        "Per-scenario independent MC inflates rank noise; no P(rank 1).",
        "CRN identity; rank_probabilities sum to 1; convergence; cycle-time MC input; infeasible_sample_count.",
    ),
    "F-225": (
        "Breakeven frontiers + Sobol + SENSITIVITY.md v2",
        "missing_artifact",
        "missing_artifact",
        "tests/governance/test_f225_frontiers.py",
        "No two-way frontiers or Sobol; SENSITIVITY.md incomplete.",
        "Charts 07/08; sobol_indices; correlation_sensitivity; decision_flip_thresholds.",
    ),
    "F-226": (
        "Generated assumption register machine-enforced",
        "dead_artifacts",
        "recurrence_invariant",
        "scripts/check_assumption_register.py",
        "No generated register; decorative-config risk returns without CI.",
        "ASSUMPTION_REGISTER.md regenerates clean; stale diff fails when closed.",
    ),
    "F-227": (
        "Bilingual decision memos + Challenge this analysis FAQ",
        "missing_artifact",
        "missing_artifact",
        "tests/governance/test_f227_memo_faq.py",
        "No decision memo shape; no objection FAQ; DE/EN twin missing.",
        ">=8 FAQ Qs with links; both PDFs; EN/DE % equal; data_lineage >=2 mermaid.",
    ),
    "F-228": (
        "Exhibit deck generated and pinned",
        "missing_artifact",
        "missing_artifact",
        "tests/governance/test_f228_deck.py",
        "No consulting-grade exhibit deck.",
        "exhibit_deck.qmd <=12 slides; python chunks for numbers; PDF exists.",
    ),
    "F-229": (
        "dbt-duckdb validation layer over processed parquet",
        "missing_artifact",
        "missing_artifact",
        "tests/governance/test_f229_dbt_parity.py",
        "No dbt validation layer for analytics-engineering signal.",
        "dbt build green; mart parity vs Tableau CSVs; CI wired.",
    ),
    "F-230": (
        "Third-party reproduction log",
        "missing_artifact",
        "missing_artifact",
        "scripts/check_repro_log.py",
        "Charter stranger-clone claim never evidenced by a committed log. BLOCKED-ON-USER.",
        "REPRODUCTION_LOG.md with date, OS, >=4 hashes, discrepancies section.",
    ),
    "F-231": (
        "EVPI / value of information per MC parameter",
        "missing_artifact",
        "missing_artifact",
        "tests/governance/test_f231_evpi.py",
        "No value-of-information framing for procurement triggers.",
        "evpi_eur in sensitivity report; all >=0; README ranks uncertainty.",
    ),
    "F-232": (
        "Multi-shift + demand frontier where robots enter optimal mix",
        "missing_artifact",
        "missing_artifact",
        "tests/governance/test_f232_demand_frontier.py",
        "Single demand/shift world; no robot entry frontier.",
        "Frontier JSON + chart 09; grid via optimizer; night premium wired.",
    ),
    "F-233": (
        "Case study + CITATION.cff + DOI release checklist",
        "missing_artifact",
        "missing_artifact",
        "scripts/check_publication_pack.py",
        "No submission-ready case study pack. Partially BLOCKED-ON-USER for external review.",
        "case_study.qmd; CITATION.cff; RELEASE_CHECKLIST.md present.",
    ),
    "F-234": (
        "Framework packaging + MAINTENANCE.md annual refresh policy",
        "missing_artifact",
        "missing_artifact",
        "tests/governance/test_f234_packaging.py",
        "No installable quickstart without LFS; no maintenance calendar.",
        "examples/quickstart.py exits 0 without data/; MAINTENANCE.md; version 1.0.0.",
    ),
    "F-235": (
        "Pyright strict ratchet + coverage >=90%",
        "fragmented_standards",
        "recurrence_invariant",
        "scripts/check_pyright_strict.py",
        "pyright basic; CONTRIBUTING historically overclaimed strict.",
        "Strict header count non-decreasing; cov-fail-under>=90; make lint green.",
    ),
    "F-236": (
        "Claims ledger + citation spot audit",
        "governance_gaps",
        "recurrence_invariant",
        "scripts/check_claims_ledger.py",
        "No total claims-evidence contract across narrative artifacts.",
        "CLAIMS_LEDGER regenerates clean; CITATION_AUDIT >=5 rows; zero untagged euros/%.",
    ),
}

REQUIRED_IDS = [
    "F-201",
    "F-202",
    "F-203",
    "F-204",
    "F-205",
    "F-206",
    "F-207",
    "F-210",
    "F-211",
    "F-212",
    "F-213",
    "F-214",
    "F-215",
    "F-216",
    "F-217",
    "F-218",
    "F-219",
    "F-220",
    "F-221",
    "F-222",
    "F-223",
    "F-224",
    "F-225",
    "F-226",
    "F-227",
    "F-228",
    "F-229",
    "F-230",
    "F-231",
    "F-232",
    "F-233",
    "F-234",
    "F-235",
    "F-236",
]

BLUEPRINT = """# Quality Transformation Program — Blueprint

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
"""


def write_yaml(fid: str) -> None:
    title, category, kind, script, evidence, acceptance = FINDING_SPECS[fid]
    status = "closed" if fid == "F-200" else "open"
    closed = f"closed_at: {TODAY}" if fid == "F-200" else "closed_at: null"
    text = f"""id: {fid}
title: "{title}"
category: {category}
kind: {kind}
status: {status}
opened_at: {TODAY}
{closed}
recurrence_count: 0
evidence: |
  {evidence}
verification_script: {script}
notes: |
  ACCEPTANCE CRITERIA:
  - {acceptance}
  LOCKED DECISIONS: see QUALITY_BLUEPRINT.md and Execution Spec v2 plan.
"""
    if fid == "F-200":
        text += f"""
  Closed by bootstrap: filed {len(REQUIRED_IDS)} program findings + QUALITY_BLUEPRINT.md.
  F-040 re-verification recorded in bootstrap session notes.
"""
    (FINDINGS / f"{fid}.yaml").write_text(text, encoding="utf-8")


def stub_check(name: str, finding_id: str, ok_when: str) -> Path:
    path = REPO / "scripts" / name
    if path.exists() and finding_id != "F-200":
        return path
    path.write_text(
        f'''"""{finding_id} — stub/real check (ratchet while open)."""
from __future__ import annotations

import sys

from _governance_check import REPO_ROOT, gate


def main() -> int:
    # Condition evaluated for real; open finding → [GAP]/exit 0.
    ok = {ok_when}
    return gate(
        "{name}",
        "{finding_id}",
        ok=ok,
        ok_msg="{finding_id} condition satisfied",
        gap_msg="{finding_id} not yet remediated — see finding YAML",
    )


if __name__ == "__main__":
    sys.exit(main())
''',
        encoding="utf-8",
    )
    return path


def stub_pytest(rel: str, finding_id: str) -> Path:
    path = REPO / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return path
    # Prefer ratchet xfail while open so suite stays green.
    if rel.startswith("tests/governance/"):
        body = f'''"""{finding_id} — verification (ratchet while open)."""
from __future__ import annotations

from _ratchet import ratchet


def test_{finding_id.lower().replace("-", "_")}_pending() -> None:
    ratchet("{finding_id}", fixed=False, gap_msg="{finding_id} not yet remediated")
'''
    else:
        body = f'''"""{finding_id} — property / kernel tests (ratchet via finding status)."""
from __future__ import annotations

import pytest
import yaml
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FINDING = REPO / "governance" / "findings" / "{finding_id}.yaml"


def _closed() -> bool:
    data = yaml.safe_load(FINDING.read_text()) or {{}}
    return data.get("status") in {{"closed", "closed_historical"}}


def test_{finding_id.lower().replace("-", "_")}_pending() -> None:
    if not _closed():
        pytest.xfail("{finding_id} open — implemented at remediation time")
    pytest.fail("{finding_id} closed but tests not implemented")
'''
    path.write_text(body, encoding="utf-8")
    return path


def main() -> None:
    (REPO / "governance" / "QUALITY_BLUEPRINT.md").write_text(BLUEPRINT, encoding="utf-8")

    # Real F-200 checker
    (REPO / "scripts" / "check_program_filed.py").write_text(
        '''"""F-200 — Quality Transformation Program findings filed."""
from __future__ import annotations

import sys

import yaml
from _governance_check import REPO_ROOT, gate

REQUIRED = [
    "F-201", "F-202", "F-203", "F-204", "F-205", "F-206", "F-207",
    "F-210", "F-211", "F-212", "F-213", "F-214", "F-215", "F-216",
    "F-217", "F-218", "F-219", "F-220", "F-221", "F-222", "F-223",
    "F-224", "F-225", "F-226", "F-227", "F-228", "F-229", "F-230",
    "F-231", "F-232", "F-233", "F-234", "F-235", "F-236",
]
FINDINGS = REPO_ROOT / "governance" / "findings"
BLUEPRINT = REPO_ROOT / "governance" / "QUALITY_BLUEPRINT.md"


def main() -> int:
    problems: list[str] = []
    if not BLUEPRINT.exists() or BLUEPRINT.stat().st_size < 200:
        problems.append("QUALITY_BLUEPRINT.md missing or too short")
    for fid in REQUIRED:
        path = FINDINGS / f"{fid}.yaml"
        if not path.exists():
            problems.append(f"{fid}.yaml missing")
            continue
        data = yaml.safe_load(path.read_text()) or {}
        if not (data.get("evidence") or "").strip():
            problems.append(f"{fid}: empty evidence")
        if not data.get("verification_script"):
            problems.append(f"{fid}: empty verification_script")
    return gate(
        "check_program_filed.py",
        "F-200",
        ok=not problems,
        ok_msg=f"{len(REQUIRED)} program findings + blueprint present",
        gap_msg="; ".join(problems),
    )


if __name__ == "__main__":
    sys.exit(main())
''',
        encoding="utf-8",
    )

    for fid in ["F-200", *REQUIRED_IDS]:
        write_yaml(fid)

    # Stub check scripts with real-enough conditions where cheap
    stub_check(
        "check_internal_links.py",
        "F-202",
        "False  # remediated in F-202",
    )
    stub_check(
        "check_single_adr_home.py",
        "F-203",
        "(REPO_ROOT / 'docs' / 'ADR').exists() is False and len(list((REPO_ROOT / 'governance' / 'adrs').glob('*.md'))) >= 12",
    )
    stub_check(
        "check_config_consumption.py",
        "F-205",
        "False  # remediated in F-205",
    )
    stub_check(
        "check_no_abs_paths.py",
        "F-207",
        "False  # remediated in F-207",
    )
    stub_check(
        "check_decision_statement.py",
        "F-210",
        "False  # remediated in F-210",
    )
    stub_check(
        "check_hypothesis_verdicts.py",
        "F-211",
        "False  # remediated in F-211",
    )
    stub_check(
        "check_license_memo.py",
        "F-218",
        "(REPO_ROOT / 'governance' / 'LICENSE_COMPLIANCE.md').exists()",
    )
    stub_check(
        "check_assumption_register.py",
        "F-226",
        "(REPO_ROOT / 'governance' / 'ASSUMPTION_REGISTER.md').exists()",
    )
    stub_check(
        "check_repro_log.py",
        "F-230",
        "(REPO_ROOT / 'governance' / 'REPRODUCTION_LOG.md').exists()",
    )
    stub_check(
        "check_publication_pack.py",
        "F-233",
        "(REPO_ROOT / 'CITATION.cff').exists() and (REPO_ROOT / 'docs' / 'case_study.qmd').exists()",
    )
    stub_check(
        "check_pyright_strict.py",
        "F-235",
        "False  # remediated in F-235",
    )
    stub_check(
        "check_claims_ledger.py",
        "F-236",
        "(REPO_ROOT / 'governance' / 'CLAIMS_LEDGER.md').exists()",
    )
    stub_check(
        "check_chart_manifest.py",
        "F-214",
        "(REPO_ROOT / 'reports' / 'executive_charts' / 'chart_data_manifest.json').exists()",
    )

    # Pytest stubs
    for fid, script in [
        ("F-201", "tests/governance/test_f201_banner.py"),
        ("F-204", "tests/governance/test_f204_taxonomy_provenance.py"),
        ("F-206", "tests/governance/test_f206_de_metric.py"),
        ("F-212", "tests/governance/test_f212_lean_human.py"),
        ("F-213", "tests/governance/test_f213_validity_disclosure.py"),
        ("F-214", "tests/governance/test_f214_chart_system.py"),
        ("F-215", "tests/governance/test_f215_readme_structure.py"),
        ("F-216", "tests/governance/test_f216_recruiter_artifact.py"),
        ("F-217", "tests/test_tco_properties.py"),
        ("F-219", "tests/governance/test_f219_sql_parity.py"),
        ("F-220", "tests/governance/test_f220_optimizer.py"),
        ("F-221", "tests/governance/test_f221_fair_scenarios.py"),
        ("F-222", "tests/governance/test_f222_realism.py"),
        ("F-223", "tests/governance/test_f223_reconciliation.py"),
        ("F-224", "tests/governance/test_f224_crn.py"),
        ("F-225", "tests/governance/test_f225_frontiers.py"),
        ("F-227", "tests/governance/test_f227_memo_faq.py"),
        ("F-228", "tests/governance/test_f228_deck.py"),
        ("F-229", "tests/governance/test_f229_dbt_parity.py"),
        ("F-231", "tests/governance/test_f231_evpi.py"),
        ("F-232", "tests/governance/test_f232_demand_frontier.py"),
        ("F-234", "tests/governance/test_f234_packaging.py"),
    ]:
        stub_pytest(script, fid)

    print(f"Wrote blueprint + {1 + len(REQUIRED_IDS)} findings + stubs")


if __name__ == "__main__":
    main()
