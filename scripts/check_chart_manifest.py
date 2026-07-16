"""F-214 — enforce the chart design-system artifact contract."""

from __future__ import annotations

import json
import sys

from _governance_check import REPO_ROOT, gate


def main() -> int:
    manifest_path = REPO_ROOT / "reports" / "executive_charts" / "chart_data_manifest.json"
    style_path = REPO_ROOT / "src" / "warehouse_humanoid_tco" / "visualization" / "chart_style.py"
    required_charts = {
        "01_tco_npv_ranking",
        "02_cost_breakdown",
        "03_simulation_throughput",
        "05_cost_per_order",
    }
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        chart_hashes = manifest["charts"]
        ok = (
            manifest["hash_algorithm"] == "sha256"
            and required_charts <= chart_hashes.keys()
            and all(len(value) == 64 for value in chart_hashes.values())
            and style_path.exists()
        )
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        ok = False
    return gate(
        "check_chart_manifest.py",
        "F-214",
        ok=ok,
        ok_msg="chart manifest hashes and shared style are present",
        gap_msg="chart manifest or style contract is incomplete",
    )


if __name__ == "__main__":
    sys.exit(main())
