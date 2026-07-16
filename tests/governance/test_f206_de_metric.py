"""F-206 — German executive summary uses total-cost NPV reductions."""
from __future__ import annotations

import csv
import re
from datetime import date
from pathlib import Path

from _ratchet import ratchet

REPO_ROOT = Path(__file__).resolve().parents[2]
QMD_PATH = REPO_ROOT / "reports" / "Executive_Summary_DE.qmd"
CSV_PATH = REPO_ROOT / "exports" / "tableau_public" / "tco_scenarios.csv"


def _summary_reductions(qmd: str) -> dict[str, float]:
    reductions: dict[str, float] = {}
    for line in qmd.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 3 or not cells[0].lstrip("*").startswith("S-"):
            continue
        scenario = cells[0].replace("*", "")
        match = re.search(r"(-?\d+(?:,\d+)?)%", cells[2])
        if match:
            reductions[scenario] = float(match.group(1).replace(",", "."))
    return reductions


def test_f_206_de_metric_alignment() -> None:
    qmd = QMD_PATH.read_text(encoding="utf-8")
    with CSV_PATH.open(encoding="utf-8", newline="") as handle:
        expected = {
            row["scenario_id"]: float(row["total_cost_reduction_vs_baseline_pct"])
            for row in csv.DictReader(handle)
        }

    actual = _summary_reductions(qmd)
    rows_match = all(
        scenario == "S-baseline-human" or abs(actual.get(scenario, float("inf")) - value) <= 0.1
        for scenario, value in expected.items()
    )
    date_match = re.search(r'^date:\s*"(\d{4}-\d{2}-\d{2})"', qmd, re.MULTILINE)
    current_date = date.fromisoformat(date_match.group(1)) if date_match else date.min
    fixed = (
        "Gesamtkosten-Reduktion vs. Baseline (NPV)" in qmd
        and rows_match
        and "70,1" not in qmd
        and "70%" not in qmd
        and current_date >= date(2026, 7, 1)
    )
    ratchet("F-206", fixed=fixed, gap_msg="QMD does not match the NPV reduction export")
