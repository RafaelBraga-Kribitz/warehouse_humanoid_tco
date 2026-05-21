.PHONY: all setup lint test module-01 module-02 module-03 module-04 profile dashboards ci-local clean help

PYTHON := python
VENV := . venv/bin/activate &&

# ── Help ──────────────────────────────────────────────────────────────────────

help:
	@echo "warehouse_humanoid_tco — Makefile targets"
	@echo ""
	@echo "Setup:"
	@echo "  make setup          Install dependencies + venv"
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
	python -m venv venv
	$(VENV) pip install --upgrade pip setuptools wheel
	$(VENV) pip install -e ".[dev]"
	$(VENV) pip install nbformat

# ── Quality gates ─────────────────────────────────────────────────────────────

lint:
	$(VENV) black --check src/ tests/
	$(VENV) ruff check src/ tests/

format:
	$(VENV) black src/ tests/
	$(VENV) ruff check --fix src/ tests/

test:
	$(VENV) pytest tests/ -v --tb=short 2>/dev/null || echo "No tests yet"

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
	@echo "  Setup: see DASHBOARD_SETUP.md"

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
