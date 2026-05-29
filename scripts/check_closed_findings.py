"""Closed-finding re-verification (Phase 1 stub).

Will load every closed finding, run its verification_script, and reopen +
fail CI on regression.
"""

from _governance_stub import main_stub

if __name__ == "__main__":
    main_stub("check_closed_findings.py", finding_id=None)
