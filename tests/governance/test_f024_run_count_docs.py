"""F-024 — setup docs + Makefile help must not claim the stale 15 runs/scenario figure."""

from __future__ import annotations

import re

from _ratchet import REPO_ROOT, ratchet

PATTERNS = [
    (REPO_ROOT / "docs" / "TABLEAU_PUBLIC_SETUP.md", r"75 simulation runs|15 per scenario"),
    (REPO_ROOT / "docs" / "POWER_BI_SETUP.md", r"15 runs\s*×"),
    (REPO_ROOT / "Makefile", r"Warehouse simulation \(15 runs\)"),
]


def test_no_stale_run_counts() -> None:
    hits: list[str] = []
    for path, pat in PATTERNS:
        if not path.exists():
            continue
        text = path.read_text()
        if re.search(pat, text):
            hits.append(f"{path.name}:/{pat}/")
    ratchet(
        "F-024",
        fixed=not hits,
        gap_msg=f"stale run-count claims still present: {hits}",
    )
