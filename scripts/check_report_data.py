"""Report-data freshness contract (Phase 1 stub).

Will assert reports/*.qmd has a `params:` block, mtime <= input mtime, and
numeric literals trace to declared JSON sources.
"""

from _governance_stub import main_stub

if __name__ == "__main__":
    main_stub("check_report_data.py", finding_id="F-005")
