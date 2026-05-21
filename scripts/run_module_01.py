"""Module 1 runner: capability extraction from UnifoLM-WBT-Dataset.

See PROJECT_CHARTER.md §4 CRISP-DM Phase: Data Preparation.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from warehouse_humanoid_tco.utils.logging import get_logger

logger = get_logger(__name__)


def main() -> None:
    logger.info("Module 1: capability extraction — not yet implemented")
    logger.info("Run 00_derisk_dataset_inspection.py notebook first")
    logger.info("See PROJECT_CHARTER.md §4.2 for Module 1 exit criteria")


if __name__ == "__main__":
    main()
