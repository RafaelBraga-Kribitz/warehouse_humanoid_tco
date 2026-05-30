"""F-024 — doc run-counts must agree with the simulation report.

Closure model: this is a recurrence invariant, not a one-time drift fix. The
canonical source is reports/module_02_simulation_report.json (`total_runs`,
`n_runs_per_scenario`, `scenarios_tested`). Every run-count claim in the
canonical docs must be **context-appropriate**: a "per scenario" claim must
equal `n_runs_per_scenario`; a "total" claim must equal `total_runs`; a
"× M scenarios" claim must equal `scenarios_tested`. Pooling all three into
one set would let "75 per scenario" or "15 runs total" pass silently.

Monte Carlo lines (10,000 samples × 5 scenarios = 50,000) describe a
different artifact and are filtered out before pattern matching.
"""

from __future__ import annotations

import json
import re

from _ratchet import REPO_ROOT, ratchet

CANONICAL = REPO_ROOT / "reports" / "module_02_simulation_report.json"
DOCS = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "docs" / "TABLEAU_PUBLIC_SETUP.md",
    REPO_ROOT / "docs" / "POWER_BI_SETUP.md",
    REPO_ROOT / "Makefile",
]

# Lines containing any of these tokens describe MC samples, not simulation runs,
# and are skipped by the pattern matcher.
MC_TOKENS = ("Monte Carlo", " MC ", "(MC ", "MC:", "MC samples")

# Each rule maps a regex with named groups to the canonical key each group must
# equal. Groups not in the role map are ignored (e.g. trailing numbers that
# describe something else). "(?<![\d,])" stops matches inside "10,000".
PATTERN_RULES: list[tuple[re.Pattern[str], dict[str, str]]] = [
    # "N simulation runs (M per scenario)"
    (
        re.compile(
            r"(?<![\d,])(?P<total>\d+)\s+simulation runs\s*\(" r"(?P<per>\d+)\s+per scenario\)"
        ),
        {"total": "total_runs", "per": "n_runs_per_scenario"},
    ),
    # "N runs total across M (warehouse )?scenarios"
    (
        re.compile(
            r"(?<![\d,])(?P<total>\d+)\s+runs total across\s+"
            r"(?P<scn>\d+)\s+(?:warehouse\s+)?scenarios"
        ),
        {"total": "total_runs", "scn": "scenarios_tested"},
    ),
    # "N runs total" (without "across")
    (
        re.compile(r"(?<![\d,])(?P<total>\d+)\s+runs total\b(?!\s+across)"),
        {"total": "total_runs"},
    ),
    # "N runs × M scenarios" — N is per scenario, M is scenarios.
    # NOTE: MC lines like "10,000 runs × 5 scenarios" are filtered upstream.
    (
        re.compile(r"(?<![\d,])(?P<per>\d+)\s+runs\s*[×x]\s*(?P<scn>\d+)\s+scenarios"),
        {"per": "n_runs_per_scenario", "scn": "scenarios_tested"},
    ),
    # "N replicas? per scenario" / "N simulation replicas? per scenario"
    (
        re.compile(r"(?<![\d,])(?P<per>\d+)\s+(?:simulation\s+)?replicas?\s+per\s+scenario"),
        {"per": "n_runs_per_scenario"},
    ),
    # "N runs per scenario"
    (
        re.compile(r"(?<![\d,])(?P<per>\d+)\s+runs\s+per\s+scenario"),
        {"per": "n_runs_per_scenario"},
    ),
    # Makefile help: "Warehouse simulation (N runs)" — per-scenario by convention.
    (
        re.compile(r"Warehouse simulation\s*\((?P<per>\d+)\s+runs\)"),
        {"per": "n_runs_per_scenario"},
    ),
    # TABLEAU_PUBLIC_SETUP measure note: "average across N runs" — per scenario.
    (
        re.compile(r"average across\s+(?P<per>\d+)\s+runs"),
        {"per": "n_runs_per_scenario"},
    ),
    # TABLEAU_PUBLIC_SETUP expected note: "N runs per scenario" / "N each".
    (
        re.compile(r"should be\s+(?P<per>\d+)\s+each"),
        {"per": "n_runs_per_scenario"},
    ),
]


def _scan(text: str, canonical: dict[str, int]) -> list[str]:
    """Return a list of mismatch descriptions for `text` against `canonical`."""
    mismatches: list[str] = []
    for line in text.splitlines():
        if any(tok in line for tok in MC_TOKENS):
            continue
        for pattern, role_map in PATTERN_RULES:
            for match in pattern.finditer(line):
                for group_name, canonical_key in role_map.items():
                    value = int(match.group(group_name))
                    expected = canonical[canonical_key]
                    if value != expected:
                        mismatches.append(
                            f'"{line.strip()[:80]}" — group '
                            f"{group_name}={value} vs canonical "
                            f"{canonical_key}={expected}"
                        )
    return mismatches


def test_doc_run_counts_match_report() -> None:
    if not CANONICAL.exists():
        ratchet("F-024", fixed=True, gap_msg="canonical report absent — vacuously fixed")
        return
    data = json.loads(CANONICAL.read_text())
    canonical = {
        "total_runs": int(data["total_runs"]),
        "n_runs_per_scenario": int(data["n_runs_per_scenario"]),
        "scenarios_tested": int(data["scenarios_tested"]),
    }
    all_mismatches: list[str] = []
    for path in DOCS:
        if not path.exists():
            continue
        rel = path.relative_to(REPO_ROOT)
        for msg in _scan(path.read_text(), canonical):
            all_mismatches.append(f"{rel}: {msg}")
    ratchet(
        "F-024",
        fixed=not all_mismatches,
        gap_msg="; ".join(all_mismatches),
    )
