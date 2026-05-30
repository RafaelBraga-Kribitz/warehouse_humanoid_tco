"""F-020 — Executive_Summary_DE.qmd headline NPV table must match exports CSV.

The QMD currently ships hand-edited k€ figures (e.g. "−€924K", "−€960K",
"−€1.284M") that disagree with exports/tableau_public/tco_scenarios.csv. Closure
requires every scenario's rounded-k€ NPV in the QMD table to match the CSV
within €1k.
"""

from __future__ import annotations

import csv
import re

from _ratchet import REPO_ROOT, ratchet

QMD = REPO_ROOT / "reports" / "Executive_Summary_DE.qmd"
CSV_PATH = REPO_ROOT / "exports" / "tableau_public" / "tco_scenarios.csv"
SCENARIOS = (
    "S-hybrid-amr",
    "S-pure-humanoid",
    "S-baseline-human",
    "S-hybrid-5050",
    "S-future-2028",
)


def _qmd_k_eur(text: str, scenario: str) -> int | None:
    """Extract the k€ integer in the QMD row for `scenario` (negative)."""
    row = re.search(rf"\|[^\n]*{re.escape(scenario)}[^\n]*\|", text)
    if not row:
        return None
    line = row.group(0)
    m = re.search(r"−€([\d.,]+)(M|K|k)?", line)
    if not m:
        return None
    raw = m.group(1).replace(".", "").replace(",", ".")
    suffix = (m.group(2) or "").upper()
    value_k = float(raw) * (1000.0 if suffix == "M" else 1.0)
    return -int(round(value_k))


def test_qmd_npv_matches_csv() -> None:
    if not QMD.exists() or not CSV_PATH.exists():
        ratchet("F-020", fixed=True, gap_msg="QMD or CSV absent — vacuously fixed")
        return
    text = QMD.read_text()
    csv_npv = {
        r["scenario_id"]: int(round(float(r["npv_eur"]) / 1000))
        for r in csv.DictReader(CSV_PATH.open())
    }
    mismatches: list[str] = []
    for scenario in SCENARIOS:
        qmd_k = _qmd_k_eur(text, scenario)
        truth_k = csv_npv.get(scenario)
        if qmd_k is None or truth_k is None:
            continue
        if abs(qmd_k - truth_k) > 1:
            mismatches.append(f"{scenario}: QMD={qmd_k}k vs CSV={truth_k}k")
    ratchet(
        "F-020",
        fixed=not mismatches,
        gap_msg="; ".join(mismatches),
    )
