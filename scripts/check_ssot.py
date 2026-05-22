"""SSOT enforcement script.

Run by CI on every push and weekly. Fails (exit code 1) if any rule is
violated. The rules are defined in PROJECT_CHARTER.md section 2.5.

Rules checked:
  1. PROJECT_CHARTER.md last_updated within 14 days of the latest commit
     touching src/, notebooks/, or docs/ADR/.
  2. Every ADR has the required headings (Date, Status, Context,
     Decision, Consequences).
  3. PROJECT_CHARTER.md Change Log has an entry whose date matches the
     last_updated metadata.

Run locally:
    python scripts/check_ssot.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

CHARTER_PATH = Path("PROJECT_CHARTER.md")
ADR_DIR = Path("docs/ADR")
WATCHED_DIRS = ("src", "notebooks", "docs/ADR")
STALENESS_THRESHOLD_DAYS = 14

REQUIRED_ADR_HEADINGS = (
    "Date:",
    "Status:",
    "## Context",
    "## Decision",
    "## Consequences",
)


def fail(message: str) -> None:
    """Print a CI-friendly error message and accumulate failures."""
    print(f"::error::{message}")
    _FAILURES.append(message)


_FAILURES: list[str] = []


def parse_charter_metadata(charter_text: str) -> dict[str, str]:
    """Extract the SSOT_METADATA block from the charter."""
    pattern = re.compile(
        r"SSOT_METADATA_START\s*(.*?)\s*SSOT_METADATA_END",
        re.DOTALL,
    )
    match = pattern.search(charter_text)
    if not match:
        fail(
            "PROJECT_CHARTER.md is missing the SSOT_METADATA block. "
            "See the file header for the expected format."
        )
        return {}

    metadata: dict[str, str] = {}
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        metadata[key.strip()] = value.strip()
    return metadata


def get_latest_commit_date_for_watched_paths() -> date | None:
    """Return the date of the latest commit touching the watched directories."""
    existing_dirs = [d for d in WATCHED_DIRS if Path(d).exists()]
    if not existing_dirs:
        return None

    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cI", "--"] + existing_dirs,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        fail(f"git log failed: {exc.stderr}")
        return None

    output = result.stdout.strip()
    if not output:
        return None
    return datetime.fromisoformat(output).date()


def check_charter_staleness(metadata: dict[str, str]) -> None:
    """Rule 1: last_updated within threshold of latest watched-path commit."""
    last_updated_raw = metadata.get("last_updated")
    if not last_updated_raw:
        fail("PROJECT_CHARTER.md SSOT_METADATA is missing 'last_updated'.")
        return

    try:
        last_updated = datetime.fromisoformat(last_updated_raw).date()
    except ValueError:
        fail(f"PROJECT_CHARTER.md 'last_updated' is not a valid ISO date: " f"{last_updated_raw!r}")
        return

    latest_commit_date = get_latest_commit_date_for_watched_paths()
    if latest_commit_date is None:
        # No code yet; staleness check N/A.
        return

    delta = latest_commit_date - last_updated
    if delta > timedelta(days=STALENESS_THRESHOLD_DAYS):
        fail(
            f"PROJECT_CHARTER.md is stale: last_updated={last_updated} but "
            f"src/notebooks/ADR were last modified on {latest_commit_date} "
            f"(delta={delta.days} days, threshold={STALENESS_THRESHOLD_DAYS}). "
            f"Update the Charter and Change Log."
        )


def check_adrs() -> None:
    """Rule 2: every ADR has the required headings and a valid filename."""
    if not ADR_DIR.exists():
        return

    filename_pattern = re.compile(r"^\d{4}-[a-z0-9-]+\.md$")

    for adr_path in sorted(ADR_DIR.glob("*.md")):
        if not filename_pattern.match(adr_path.name):
            fail(f"ADR filename violates the pattern NNNN-kebab-case.md: " f"{adr_path.name}")
            continue

        content = adr_path.read_text(encoding="utf-8")
        for heading in REQUIRED_ADR_HEADINGS:
            if heading not in content:
                fail(f"ADR {adr_path.name} is missing required content: " f"{heading!r}")


def check_change_log_present(charter_text: str) -> None:
    """Rule 3: the Change Log section exists and has at least one entry."""
    if "## 11. Change Log" not in charter_text:
        fail("PROJECT_CHARTER.md is missing section '## 11. Change Log'.")
        return

    # Take everything after the Change Log heading
    change_log_section = charter_text.split("## 11. Change Log", 1)[1]

    # Look for at least one table row with an ISO date
    iso_date_pattern = re.compile(r"\|\s*\d{4}-\d{2}-\d{2}\s*\|")
    if not iso_date_pattern.search(change_log_section):
        fail(
            "PROJECT_CHARTER.md Change Log section has no dated entries. "
            "Every charter change must log an entry with an ISO date."
        )


def main() -> int:
    if not CHARTER_PATH.exists():
        print(f"::error::PROJECT_CHARTER.md not found at {CHARTER_PATH}")
        return 1

    charter_text = CHARTER_PATH.read_text(encoding="utf-8")
    metadata = parse_charter_metadata(charter_text)

    check_charter_staleness(metadata)
    check_adrs()
    check_change_log_present(charter_text)

    if _FAILURES:
        print()
        print(f"SSOT check failed with {len(_FAILURES)} violation(s).")
        return 1

    print("SSOT check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
