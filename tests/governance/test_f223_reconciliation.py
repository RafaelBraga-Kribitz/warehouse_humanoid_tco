"""F-223 — cost lines must reconcile to each committed scenario NPV."""
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT = REPO_ROOT / "reports" / "module_03_tco_report.json"
MODULE = REPO_ROOT / "src" / "warehouse_humanoid_tco" / "pipelines" / "module_03_tco.py"


def test_cost_lines_reconcile_to_npv_and_audit_artifacts_exist() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    breakdowns = report.get("cost_line_breakdown")
    assert isinstance(breakdowns, dict) and breakdowns

    for scenario_id, lines in breakdowns.items():
        assert isinstance(lines, list) and lines, scenario_id
        line_total = sum(float(line["npv_eur"]) for line in lines)
        npv = next(
            item["npv_eur"]
            for item in report["scenario_results"]
            if item["scenario_id"] == scenario_id
        )
        assert abs(line_total - float(npv)) <= 1.0, scenario_id

    assert (REPO_ROOT / "docs" / "cost_model.md").is_file()
    assert (REPO_ROOT / "docs" / "auditors_worksheet.md").is_file()
    assert "_BASELINE_ANNUAL_OPEX" not in MODULE.read_text(encoding="utf-8")
