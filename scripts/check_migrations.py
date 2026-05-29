"""Migration staleness gate — in_progress migrations must not exceed their budget.

Structural invariant: any migration with status `in_progress` whose elapsed days
since `started_at` exceed `max_days_in_progress` is a stalled refactor and fails.
"""

from __future__ import annotations

import sys
from datetime import date

import yaml
from _governance_check import REPO_ROOT, gate

MIGRATIONS = REPO_ROOT / "governance" / "migrations"


def _as_date(value: object) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def main() -> int:
    problems: list[str] = []
    count = 0
    for path in sorted(MIGRATIONS.glob("*.yaml")):
        data = yaml.safe_load(path.read_text()) or {}
        count += 1
        if data.get("status") != "in_progress":
            continue
        started = _as_date(data.get("started_at"))
        budget = data.get("max_days_in_progress")
        if started is None or not isinstance(budget, int):
            continue
        elapsed = (date.today() - started).days
        if elapsed > budget:
            problems.append(f"{path.name}: {elapsed}d in_progress (budget {budget}d)")
    return gate(
        "check_migrations.py",
        None,
        ok=not problems,
        ok_msg=f"{count} migration(s), none stalled",
        gap_msg="; ".join(problems),
    )


if __name__ == "__main__":
    sys.exit(main())
