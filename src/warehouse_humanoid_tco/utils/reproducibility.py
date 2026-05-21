"""Reproducibility utilities: seeding, version recording.

See PROJECT_CHARTER.md §8.4 Determinism Requirements.
"""

from __future__ import annotations

import random

import numpy as np


def seed_all(seed: int) -> None:
    """Seed all random sources with the given seed."""
    random.seed(seed)
    np.random.seed(seed)
