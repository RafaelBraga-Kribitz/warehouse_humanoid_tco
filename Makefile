.PHONY: all setup bootstrap lint test module-01 module-02 module-03 module-04 profile dashboards ci-local clean help \
        audit verify session-start session-end presentation assumptions-register dbt exec-summary lock-export

PYTHON ?= python
# Use ?= so env override (VENV="" in CI workflows) takes precedence over default
VENV ?= . .venv/bin/activate &&

# ── Help ──────────────────────────────────────────────────────────────────────

help:
	@echo "warehouse_humanoid_tco — Makefile targets"
	@echo ""
	@echo "Setup:"
	@echo "  make setup          Install deps via uv sync --frozen (dev + analytics)"
	@echo "  make lock-export    Refresh uv.lock + requirements.txt from pyproject"
	@echo "  make bootstrap      Install pre-commit hooks (one-time per clone)"
	@echo ""
	@echo "Governance (see governance/AUDIT_PROCEDURE.md):"
	@echo "  make session-start  Generate governance/SESSION_HANDOUT.md (read first each session)"
	@echo "  make audit          Run all check_*.py + write governance/AUDIT_STATE.json"
	@echo "  make verify         audit + tests + closed-finding re-verification"
	@echo "  make session-end    Write governance/SESSION_END.md for next-session handoff"
	@echo "  make assumptions-register  Regenerate governance/ASSUMPTION_REGISTER.md"
	@echo "                            Python: python scripts/generate_assumption_register.py"
	@echo ""
	@echo "Pipeline (full run):"
	@echo "  make all            Run modules 0-4 (data → dashboards)"
	@echo "  make module-01      Capability extraction (2,359 episodes)"
	@echo "  make module-02      Warehouse simulation (15 runs)"
	@echo "  make module-03      TCO analysis (NPV rankings)"
	@echo "  make module-04      Dashboard exports (Tableau + charts)"
	@echo ""
	@echo "Analysis:"
	@echo "  make profile        Generate data profiling notebook"
	@echo "  make dashboards     Generate Tableau/Power BI exports + charts"
	@echo "  make dbt            Build dbt-duckdb validation marts from processed parquet"
	@echo "  make exec-summary   Quarto typst PDFs: DE/EN memos + exhibit deck (requires quarto)"
	@echo "  make presentation   Regenerate module-04 charts + Quarto typst decision PDFs"
	@echo ""
	@echo "Quality:"
	@echo "  make lint           Black + Ruff + Pyright"
	@echo "  make format         Auto-format code"
	@echo "  make test           Run pytest suite"
	@echo "  make ci-local       lint + test (local CI check)"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          Remove __pycache__, .pyc, eggs"

# ── Bootstrap ────────────────────────────────────────────────────────────────

setup:
	uv venv .venv
	uv sync --frozen --extra dev --extra analytics
	@echo "✓ Environment ready (locked; dev + analytics)"

# Refresh lock + main-only requirements.txt after pyproject dependency edits.
lock-export:
	uv lock
	uv export --format requirements-txt --no-hashes --no-emit-project -o requirements.txt
	@echo "✓ uv.lock and requirements.txt refreshed"

bootstrap: setup
	$(VENV) pre-commit install
	$(VENV) pre-commit run --all-files || true
	@echo "✓ pre-commit hooks installed (.git/hooks/pre-commit)"

# ── Governance — see governance/AUDIT_PROCEDURE.md ───────────────────────────

# Phase 1 audit pipeline: every check_*.py runs the real invariant. Open findings
# print [GAP] and exit 0 (ratchet); they flip to [FAIL] when their finding closes.
# See scripts/_governance_check.py for the ratchet contract.
audit:
	@echo "── make audit ─────────────────────────────────────────────"
	@$(PYTHON) scripts/check_ssot_registry.py
	@$(PYTHON) scripts/check_charter_size.py
	@$(PYTHON) scripts/check_contributing_claims.py
	@$(PYTHON) scripts/check_migrations.py
	@$(PYTHON) scripts/check_deprecations.py
	@$(PYTHON) scripts/check_adr_linkage.py
	@$(PYTHON) scripts/check_todo_dir.py
	@$(PYTHON) scripts/check_makefile_numerics.py
	@$(PYTHON) scripts/check_claude_md.py
	@$(PYTHON) scripts/check_workflow_registry.py
	@$(PYTHON) scripts/check_workflow_escapes.py
	@$(PYTHON) scripts/check_manifest_sha256.py
	@$(PYTHON) scripts/check_png_prefix_collisions.py
	@$(PYTHON) scripts/check_qmd_dates.py
	@$(PYTHON) scripts/check_notebook_sequence.py
	@$(PYTHON) scripts/check_ssot_scope.py
	@$(PYTHON) scripts/check_finding_coverage.py
	@$(PYTHON) scripts/check_report_data.py
	@$(PYTHON) scripts/check_program_filed.py
	@$(PYTHON) scripts/check_internal_links.py
	@$(PYTHON) scripts/check_single_adr_home.py
	@$(PYTHON) scripts/check_config_consumption.py
	@$(PYTHON) scripts/check_no_abs_paths.py
	@$(PYTHON) scripts/check_decision_statement.py
	@$(PYTHON) scripts/check_hypothesis_verdicts.py
	@$(PYTHON) scripts/check_license_memo.py
	@$(PYTHON) scripts/check_assumption_register.py
	@$(PYTHON) scripts/check_repro_log.py
	@$(PYTHON) scripts/check_publication_pack.py
	@$(PYTHON) scripts/check_pyright_strict.py
	@$(PYTHON) scripts/check_claims_ledger.py
	@$(PYTHON) scripts/check_chart_manifest.py
	@$(PYTHON) scripts/write_audit_state.py
	@echo "✓ audit complete — see governance/AUDIT_STATE.json"

assumptions-register:
	@$(PYTHON) scripts/generate_assumption_register.py

# verify = audit + tests + closed-finding re-verification
verify: audit
	@echo "── make verify ────────────────────────────────────────────"
	$(VENV) pytest tests/ -v --tb=short
	@$(PYTHON) scripts/check_closed_findings.py
	@echo "✓ verify complete"

session-start: audit
	@$(PYTHON) scripts/session_start.py
	@echo ""
	@echo "→ Read governance/SESSION_HANDOUT.md before choosing work."

session-end:
	@$(PYTHON) scripts/write_audit_state.py
	@$(PYTHON) scripts/session_end.py
	@echo ""
	@echo "→ Edit free-text fields in governance/SESSION_END.md, then commit."

# ── Quality gates ─────────────────────────────────────────────────────────────

lint:
	$(VENV) black --check src/ tests/
	$(VENV) ruff check src/ tests/

format:
	$(VENV) black src/ tests/
	$(VENV) ruff check --fix src/ tests/

test:
	$(VENV) pytest tests/ -v --tb=short

ci-local: lint test
	@echo "✓ Local CI checks passed"

# ── Pipeline modules (run via Python -m) ──────────────────────────────────────

module-01:
	$(VENV) python -m warehouse_humanoid_tco.pipelines.module_01_capability_extraction

module-02:
	$(VENV) python -m warehouse_humanoid_tco.pipelines.module_02_simulation

module-03:
	$(VENV) python -m warehouse_humanoid_tco.pipelines.module_03_tco

module-04:
	$(VENV) python -m warehouse_humanoid_tco.pipelines.module_04_dashboards

all: module-01 module-02 module-03 module-04
	@echo "✓ All modules complete"

# ── Report Rendering ──────────────────────────────────────────────────────────

# Quarto typst PDFs for recruiter artifacts (F-238). No TeX required.
# Hard-fails without quarto — do not substitute ReportLab for committed PDFs.
exec-summary:
	@command -v quarto >/dev/null 2>&1 || { \
		echo "✗ quarto required. See https://quarto.org/docs/get-started/"; \
		exit 1; \
	}
	quarto render reports/Executive_Summary_DE.qmd --to typst
	quarto render reports/Executive_Summary_DE.qmd --to html
	quarto render reports/Executive_Summary_EN.qmd --to typst
	quarto render reports/exhibit_deck.qmd --to typst

# Regenerate presentation-layer artifacts after data / methodology changes.
# Closes F-043: charts and QMD-rendered HTML diverge from CSV/JSON outputs
# unless module-04 + quarto are explicitly re-run. Decision PDFs use typst
# (same as exec-summary). Does NOT re-run modules 01-03; those live under
# `make all`. Never calls scripts/render_decision_pdfs.py.
presentation: module-04
	@if command -v quarto >/dev/null 2>&1; then \
		$(MAKE) exec-summary; \
		for qmd in reports/*.qmd; do \
			case "$$qmd" in \
				*/Executive_Summary_DE.qmd|*/Executive_Summary_EN.qmd|*/exhibit_deck.qmd) continue ;; \
			esac; \
			[ -f "$$qmd" ] || continue; \
			echo "Rendering $$qmd..."; \
			quarto render "$$qmd"; \
		done; \
	else \
		echo "⚠ quarto not installed — skipping QMD renders. Charts regenerated."; \
		echo "  See https://quarto.org/docs/get-started/ to enable HTML/PDF renders."; \
	fi
	@echo "✓ presentation artifacts refreshed"

# ── Analysis & Profiling ──────────────────────────────────────────────────────

profile:
	$(VENV) python -c "\
from pathlib import Path; \
from warehouse_humanoid_tco.analysis.profile_outputs import generate_profile_notebook; \
generate_profile_notebook(\
    Path('data/processed'),\
    Path('reports/derisk_inspection_report.json'),\
    Path('notebooks/01_data_profile_summary.ipynb')\
)"

dashboards: module-01 module-02 module-03 module-04
	@echo "✓ Dashboard data ready"
	@echo "  Tableau: exports/tableau_public/*.csv"
	@echo "  Charts: reports/executive_charts/*.png"
	@echo "  Setup: see docs/DASHBOARD_SETUP.md"

# dbt source paths are relative to the repository root; keep this invocation here.
dbt:
	$(VENV) dbt build --project-dir analytics/dbt --profiles-dir analytics/dbt

# ── Notebooks ─────────────────────────────────────────────────────────────────

notebooks:
	$(VENV) jupytext --sync notebooks/*.py 2>/dev/null || echo "Jupytext not installed"

# ── Cleanup ───────────────────────────────────────────────────────────────────

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache .pyright
	@echo "✓ Cleaned"
