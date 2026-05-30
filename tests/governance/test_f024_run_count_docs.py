"""F-024 — every doc citing simulation run-counts must agree with the canonical pipeline output.

The parallel session's evidence claimed README cites 150 runs / 30 per scenario while
docs/Makefile cite 75/15 — a drift across the repo. Actual state at ingestion time:
everything cites 15 runs/scenario (75 total). The real risk this finding guards
against is drift between `reports/module_02_simulation_report.json` (the canonical
source) and the user-facing docs. The test reads the JSON and asserts that any doc
that mentions the run count uses a number consistent with the JSON.
"""

from __future__ import annotations

import json
import re

from _ratchet import REPO_ROOT, ratchet

REPORT = REPO_ROOT / "reports" / "module_02_simulation_report.json"

DOCS = (
    REPO_ROOT / "README.md",
    REPO_ROOT / "docs" / "TABLEAU_PUBLIC_SETUP.md",
    REPO_ROOT / "docs" / "POWER_BI_SETUP.md",
    REPO_ROOT / "Makefile",
)

# Patterns that contain a run-count claim. Each captures the integer.
PATTERNS = (
    re.compile(r"(?<![\d,])(\d+)\s+simulation\s+(runs|replicas)\s+per\s+scenario", re.IGNORECASE),
    re.compile(r"(?<![\d,])(\d+)\s+runs?\s+per\s+scenario", re.IGNORECASE),
    re.compile(r"(?<![\d,])(\d+)\s+simulation\s+runs?\b", re.IGNORECASE),
    re.compile(r"(?<![\d,])(\d+)\s+runs?\s*[×x]\s*\d+\s+scenarios", re.IGNORECASE),
    re.compile(r"Warehouse\s+simulation\s*\((\d+)\s+runs?\)", re.IGNORECASE),
    re.compile(r"(?<![\d,])(\d+)\s+replications?\s+per\s+scenario", re.IGNORECASE),
)


def _extract_claims(text: str) -> list[int]:
    out: list[int] = []
    for pat in PATTERNS:
        for m in pat.finditer(text):
            out.append(int(m.group(1)))
    return out


def test_doc_run_counts_match_report() -> None:
    if not REPORT.exists():
        ratchet("F-024", fixed=True, gap_msg="simulation report absent — vacuously fixed")
        return
    data = json.loads(REPORT.read_text())
    canonical_per_scenario = int(data.get("n_runs_per_scenario", 0))
    canonical_total = int(data.get("total_runs", 0))
    valid = {canonical_per_scenario, canonical_total}
    valid.discard(0)
    if not valid:
        ratchet("F-024", fixed=True, gap_msg="no canonical run counts in report — vacuously fixed")
        return
    mismatches: list[str] = []
    for path in DOCS:
        if not path.exists():
            continue
        for claim in _extract_claims(path.read_text()):
            if claim not in valid:
                mismatches.append(f"{path.relative_to(REPO_ROOT)}: {claim} (canonical {sorted(valid)})")
    ratchet(
        "F-024",
        fixed=not mismatches,
        gap_msg="; ".join(mismatches),
    )
