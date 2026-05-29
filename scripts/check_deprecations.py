"""F-004 — deprecated symbols must be gone once their sunset date passes.

Structural invariant: for each entry in governance/DEPRECATIONS.yaml, if today is
past `sunset_date` and the symbol's leaf name still appears anywhere under src/,
the deprecation is overdue and fails. Before the sunset date it is informational.
"""

from __future__ import annotations

import sys
from datetime import date

import yaml
from _governance_check import REPO_ROOT, gate

DEPRECATIONS = REPO_ROOT / "governance" / "DEPRECATIONS.yaml"
SRC = REPO_ROOT / "src"


def _as_date(value: object) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def _symbol_present(leaf: str) -> bool:
    return any(leaf in p.read_text() for p in SRC.rglob("*.py"))


def main() -> int:
    data = yaml.safe_load(DEPRECATIONS.read_text()) or {}
    entries = data.get("deprecations", []) or []
    today = date.today()
    overdue: list[str] = []
    pending: list[str] = []
    for entry in entries:
        symbol = entry.get("symbol", "")
        leaf = symbol.rsplit(".", 1)[-1]
        sunset = _as_date(entry.get("sunset_date"))
        present = _symbol_present(leaf) if leaf else False
        if sunset and today > sunset and present:
            overdue.append(f"{symbol} (sunset {sunset}, still present)")
        elif present:
            pending.append(f"{leaf}→{sunset}")
    pending_summary = ", ".join(pending) or "none"
    return gate(
        "check_deprecations.py",
        None,
        ok=not overdue,
        ok_msg=f"{len(entries)} deprecation(s), none overdue (pending: {pending_summary})",
        gap_msg="; ".join(overdue),
    )


if __name__ == "__main__":
    sys.exit(main())
