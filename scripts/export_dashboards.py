"""Module 4 runner: export to Tableau Public CSV and Power BI parquet.

See PROJECT_CHARTER.md §4 CRISP-DM Phase: Deployment.
See ADR-0004 for dual-publish rationale.
Requires data/processed/tco_scenarios.parquet from Module 3.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from warehouse_humanoid_tco.utils.logging import get_logger

logger = get_logger(__name__)


def main() -> None:
    logger.info("Module 4: dashboard export — not yet implemented")
    logger.info("Requires Module 3 outputs first")


if __name__ == "__main__":
    main()
