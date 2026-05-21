"""Module 2 runner: SimPy warehouse simulation.

See PROJECT_CHARTER.md §4 CRISP-DM Phase: Modeling.
Requires data/processed/humanoid_capabilities_per_episode.parquet from Module 1.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from warehouse_humanoid_tco.utils.logging import get_logger

logger = get_logger(__name__)


def main() -> None:
    logger.info("Module 2: warehouse simulation — not yet implemented")
    logger.info("Requires Module 1 outputs first")


if __name__ == "__main__":
    main()
