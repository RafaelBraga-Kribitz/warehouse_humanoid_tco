"""F-214 — chart design system and data-manifest verification."""

from __future__ import annotations

import json
from pathlib import Path

from _ratchet import ratchet

from warehouse_humanoid_tco.visualization import chart_style

ROOT = Path(__file__).resolve().parents[2]


def test_f_214_chart_design_system_and_manifest() -> None:
    palette_ok = (
        chart_style.RECOMMENDED,
        chart_style.BASELINE,
        chart_style.OTHER,
        chart_style.ADVERSE,
    ) == (
        "#1f77b4",
        "#7f7f7f",
        "#a6c8e0",
        "#d62728",
    )
    try:
        manifest = json.loads(
            (ROOT / "reports" / "executive_charts" / "chart_data_manifest.json").read_text(
                encoding="utf-8"
            )
        )
        manifest_ok = (
            manifest["hash_algorithm"] == "sha256"
            and {
                "01_tco_npv_ranking",
                "02_cost_breakdown",
                "03_simulation_throughput",
                "05_cost_per_order",
            }
            <= manifest["charts"].keys()
            and all(len(digest) == 64 for digest in manifest["charts"].values())
        )
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        manifest_ok = False
    ratchet(
        "F-214",
        fixed=palette_ok and manifest_ok,
        gap_msg="locked chart palette or plotted-value manifest is incomplete",
    )
