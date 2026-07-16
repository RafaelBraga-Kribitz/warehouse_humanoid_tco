"""Verify that governance/adrs is the only ADR directory."""

from __future__ import annotations

import subprocess
import sys

from _governance_check import REPO_ROOT, gate

LEGACY_REFERENCE = "docs" + "/ADR"


def _tracked_adr_references() -> list[str]:
    """Return tracked Markdown/Python files that still name the legacy ADR home."""
    result = subprocess.run(
        ["git", "grep", "-n", LEGACY_REFERENCE, "--", "*.md", "*.py"],  # noqa: S607
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError(result.stderr)
    return [line for line in result.stdout.splitlines() if line]


def main() -> int:
    legacy_dir = REPO_ROOT / "docs" / "ADR"
    canonical_count = len(list((REPO_ROOT / "governance" / "adrs").glob("*.md")))
    references = _tracked_adr_references()
    ok = not legacy_dir.exists() and not references and canonical_count >= 12
    return gate(
        "check_single_adr_home.py",
        "F-203",
        ok=ok,
        ok_msg=f"governance/adrs is the only ADR home ({canonical_count} files)",
        gap_msg=(
            f"legacy directory exists={legacy_dir.exists()}; "
            f"legacy references={references}; canonical ADR count={canonical_count}"
        ),
    )


if __name__ == "__main__":
    sys.exit(main())
