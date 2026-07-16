"""F-236 — verify narrative claims have reproducible evidence."""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

from _governance_check import REPO_ROOT, gate

LEDGER_PATH = REPO_ROOT / "governance" / "CLAIMS_LEDGER.md"
CITATION_AUDIT = REPO_ROOT / "governance" / "CITATION_AUDIT.md"
README_PATH = REPO_ROOT / "README.md"
NUMERIC_CLAIM_RE = re.compile(r"€[\d,.]+[KM]?|\d+(?:\.\d+)?%")
VERDICT_RE = re.compile(r"\b(?:PASS|PARTIAL)\b")


def _ledger_is_current() -> bool:
    """Regenerate the ledger to a temporary path and compare it byte-for-byte."""
    with tempfile.TemporaryDirectory() as temp_dir:
        generated = Path(temp_dir) / "CLAIMS_LEDGER.md"
        result = subprocess.run(
            [sys.executable, "scripts/generate_claims_ledger.py", "--output", str(generated)],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        return (
            result.returncode == 0
            and LEDGER_PATH.exists()
            and generated.read_bytes() == LEDGER_PATH.read_bytes()
        )


def _has_untagged_numeric_claims(text: str) -> bool:
    """Detect monetary and percentage claims without an inline evidence tag."""
    in_fence = False
    for line in text.splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence and NUMERIC_CLAIM_RE.search(line) and "<!-- claim:" not in line:
            return True
    return False


def _citation_audit_is_complete() -> bool:
    """Require five source rows and a PASS/PARTIAL verdict for each."""
    if not CITATION_AUDIT.exists():
        return False
    rows = [
        line
        for line in CITATION_AUDIT.read_text(encoding="utf-8").splitlines()
        if line.startswith("|") and "---" not in line
    ]
    data_rows = rows[1:] if rows else []
    return len(data_rows) >= 5 and all(VERDICT_RE.search(row) for row in data_rows)


def main() -> int:
    ok = (
        _ledger_is_current()
        and not _has_untagged_numeric_claims(README_PATH.read_text(encoding="utf-8"))
        and _citation_audit_is_complete()
    )
    return gate(
        "check_claims_ledger.py",
        "F-236",
        ok=ok,
        ok_msg="claims ledger, numeric tags, and citation spot audit are complete",
        gap_msg=(
            "claims ledger is stale, a README numeric claim is untagged, "
            "or citation audit is incomplete"
        ),
    )


if __name__ == "__main__":
    sys.exit(main())
