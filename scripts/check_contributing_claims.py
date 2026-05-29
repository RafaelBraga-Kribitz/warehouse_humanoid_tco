"""Parse CONTRIBUTING.md pyright claim; assert pyproject.toml matches (Phase 1 stub)."""

from _governance_stub import main_stub

if __name__ == "__main__":
    main_stub("check_contributing_claims.py", finding_id="F-006")
