.PHONY: all setup lint test module-01 module-02 module-03 module-04 ci-local clean

PYTHON := python3
UV := uv

# ── Bootstrap ────────────────────────────────────────────────────────────────

setup:
	$(UV) venv .venv
	$(UV) pip install -e ".[dev,notebooks]"
	pre-commit install

# ── Quality gates ─────────────────────────────────────────────────────────────

lint:
	black --check src/ tests/ scripts/
	ruff check src/ tests/ scripts/
	pyright src/

format:
	black src/ tests/ scripts/ notebooks/
	ruff check --fix src/ tests/ scripts/

test:
	pytest tests/ -v

ci-local: lint test
	python scripts/check_ssot.py

# ── Pipeline modules ──────────────────────────────────────────────────────────

module-01:
	$(PYTHON) scripts/run_module_01.py

module-02:
	$(PYTHON) scripts/run_module_02.py

module-03:
	$(PYTHON) scripts/run_module_03.py

module-04:
	$(PYTHON) scripts/export_dashboards.py

all: module-01 module-02 module-03 module-04

# ── Notebooks ─────────────────────────────────────────────────────────────────

notebooks:
	jupytext --sync notebooks/*.py

# ── Cleanup ───────────────────────────────────────────────────────────────────

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
