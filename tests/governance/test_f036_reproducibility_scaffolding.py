"""F-036 — reproducibility scaffolding must be wired or removed (no orphan config).

A wiring is a reference to seed_all / order_arrival_seed / etc. in the pipeline
or scripts — *not* the definition site itself. This test excludes
utils/reproducibility.py (where seed_all is defined) and the seeds.yaml file
(where the keys are declared) from the wiring search.
"""

from __future__ import annotations

import re
from pathlib import Path

from _ratchet import REPO_ROOT, ratchet

SRC = REPO_ROOT / "src" / "warehouse_humanoid_tco"
SCRIPTS = REPO_ROOT / "scripts"
SEEDS_YAML = REPO_ROOT / "config" / "seeds.yaml"
REPRO_DEF = REPO_ROOT / "src" / "warehouse_humanoid_tco" / "utils" / "reproducibility.py"
ORPHAN_KEYS = (
    "seed_all",
    "order_arrival_seed",
    "cycle_time_sampling_seed",
    "downtime_seed",
    "worker_absence_seed",
)


def _grep_wirings(roots: tuple[Path, ...], patterns: tuple[str, ...]) -> list[str]:
    hits: list[str] = []
    rx = re.compile("|".join(re.escape(p) for p in patterns))
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            if path.resolve() == REPRO_DEF.resolve():
                continue
            try:
                if rx.search(path.read_text()):
                    hits.append(str(path.relative_to(REPO_ROOT)))
            except OSError:
                pass
    return hits


def test_reproducibility_wired_or_removed() -> None:
    if not SEEDS_YAML.exists():
        ratchet("F-036", fixed=True, gap_msg="config/seeds.yaml removed")
        return
    wired = _grep_wirings((SRC, SCRIPTS), ORPHAN_KEYS)
    ratchet(
        "F-036",
        fixed=bool(wired),
        gap_msg="config/seeds.yaml + seed_all defined but no src/ or scripts/ consumer wires them",
    )
