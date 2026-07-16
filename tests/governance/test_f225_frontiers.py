"""F-225 — frontiers and global sensitivity artifacts remain publishable."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_f_225_frontiers_and_sensitivity_extensions_exist() -> None:
    report = json.loads((ROOT / "reports" / "sensitivity_analysis_report.json").read_text())
    for key in ("sobol_indices", "correlation_sensitivity", "decision_flip_thresholds"):
        assert key in report and report[key], f"missing {key}"

    sobol = report["sobol_indices"]
    assert sobol["estimator"] == "coarse_grid_variance_proxy"
    assert sobol["indices"]["human_wage_eur"]["first_order"] >= 0
    assert "S-future-2028" in report["decision_flip_thresholds"]
    assert "S-lean-hybrid-amr" in report["decision_flip_thresholds"]

    charts = ROOT / "reports" / "executive_charts"
    for name in ("07_frontier_capex_wage.png", "08_frontier_capex_transfer.png"):
        path = charts / name
        assert path.exists() and path.stat().st_size > 1_000

    protocol = (ROOT / "governance" / "SENSITIVITY.md").read_text()
    for phrase in ("One-at-a-time", "Monte Carlo", "common random numbers", "Sobol", "frontier"):
        assert phrase.lower() in protocol.lower()
