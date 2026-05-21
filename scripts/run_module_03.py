"""Module 3 runner: TCO financial model + sensitivity analysis.

See PROJECT_CHARTER.md §4 CRISP-DM Phase: Evaluation.
Requires data/processed/simulation_runs.parquet from Module 2.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from warehouse_humanoid_tco.utils.logging import get_logger

logger = get_logger(__name__)


def main() -> None:
    logger.info("Module 3: TCO model — not yet implemented")
    logger.info("Requires Module 2 outputs first")


if __name__ == "__main__":
    main()
