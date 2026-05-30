.PHONY: all setup bootstrap lint test module-01 module-02 module-03 module-04 profile dashboards ci-local clean help \
        audit verify session-start session-end

PYTHON ?= python
# Use ?= so env override (VENV="" in CI workflows) takes precedence over default
VENV ?= . .venv/bin/activate &&

# ── Help ──────────────────────────────────────────────────────────────────────

help:
	@echo "warehouse_humanoid_tco — Makefile targets"
	@echo ""
	@echo "Setup:"
	@echo "  make setup          Install dependencies + venv"
	@echo "  make bootstrap      Install pre-commit hooks (one-time per clone)"
	@echo ""
	@echo "Governance (see governance/AUDIT_PROCEDURE.md):"
	@echo "  make session-start  Generate governance/SESSION_HANDOUT.md (read first each session)"
	@echo "  make audit          Run all check_*.py + write governance/AUDIT_STATE.json"
	@echo "  make verify         audit + tests + closed-finding re-verification"
	@echo "  make session-end    Write governance/SESSION_END.md for next-session handoff"
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
	@echo "  make exec-summary   Re-render reports/Executive_Summary_DE from QMD (requires quarto)"
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
	uv sync --frozen --extra dev
	@echo "✓ Environment ready (locked)"

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
	@$(PYTHON) scripts/write_audit_state.py
	@echo "✓ audit complete — see governance/AUDIT_STATE.json"

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

# Re-render the Executive Summary HTML/PDF from the QMD source.
# Closes the F-020 staleness category: rather than hand-editing the HTML when
# the QMD changes, contributors run this target. Requires `quarto` on PATH.
exec-summary:
	@command -v quarto >/dev/null 2>&1 || { \
		echo "✗ quarto not installed. See https://quarto.org/docs/get-started/"; \
		exit 1; \
	}
	quarto render reports/Executive_Summary_DE.qmd

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
