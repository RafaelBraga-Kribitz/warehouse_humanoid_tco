"""F-204 — taxonomy provenance verification."""

from __future__ import annotations

import subprocess
from pathlib import Path

from _ratchet import ratchet

REPO_ROOT = Path(__file__).resolve().parents[2]
CSV_NAME = "manual_taxonomy" + "_review.csv"


def test_taxonomy_provenance_is_rule_based() -> None:
    """Taxonomy provenance is documented without a fabricated review CSV."""
    csv_absent = not (REPO_ROOT / "data/labels" / CSV_NAME).exists()
    rules_path = REPO_ROOT / "docs/taxonomy_rules.md"
    rules_text = rules_path.read_text(encoding="utf-8") if rules_path.exists() else ""
    rule_rows = [
        line
        for line in rules_text.splitlines()
        if line.startswith("|") and "features/taxonomy.py" in line
    ]
    readme_text = (REPO_ROOT / "README.md").read_text(encoding="utf-8").lower()
    tracked = subprocess.run(
        ["git", "ls-files"],  # noqa: S607
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    remaining_refs = [
        path
        for relative in tracked
        if (path := REPO_ROOT / relative).is_file()
        and CSV_NAME.removesuffix(".csv") in path.read_text(encoding="utf-8", errors="ignore")
    ]
    ratchet(
        "F-204",
        fixed=(
            csv_absent
            and len(rule_rows) >= 4
            and "rule-based" in readme_text
            and not remaining_refs
        ),
        gap_msg="taxonomy review CSV or its references remain, or rules are undocumented",
    )
