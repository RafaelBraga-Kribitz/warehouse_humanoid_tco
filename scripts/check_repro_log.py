"""F-230 — verify the reproduction log contains auditable evidence."""

from __future__ import annotations

import re
import sys

from _governance_check import REPO_ROOT, gate

LOG_PATH = REPO_ROOT / "governance" / "REPRODUCTION_LOG.md"
DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
OS_RE = re.compile(r"\b(?:Windows|macOS|Linux|Ubuntu|Debian)\b", re.IGNORECASE)
SHA256_RE = re.compile(r"\b[a-fA-F0-9]{64}\b")
DISCREPANCIES_RE = re.compile(r"^##?\s*Discrepancies\s*:", re.IGNORECASE | re.MULTILINE)


def main() -> int:
    content = LOG_PATH.read_text(encoding="utf-8") if LOG_PATH.exists() else ""
    ok = (
        bool(DATE_RE.search(content))
        and bool(OS_RE.search(content))
        and len(SHA256_RE.findall(content)) >= 4
        and bool(DISCREPANCIES_RE.search(content))
    )
    return gate(
        "check_repro_log.py",
        "F-230",
        ok=ok,
        ok_msg="reproduction log contains date, OS, hashes, and discrepancies",
        gap_msg="log needs a date, OS, four SHA-256 hashes, and discrepancies section",
    )


if __name__ == "__main__":
    sys.exit(main())
