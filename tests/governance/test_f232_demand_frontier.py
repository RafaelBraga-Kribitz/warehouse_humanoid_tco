"""F-232 — demand frontier verification."""
from __future__ import annotations

import json
from pathlib import Path

from _ratchet import ratchet


def test_f_232_demand_frontier_grid_and_chart_exist() -> None:
    root = Path(__file__).resolve().parents[2]
    try:
        report = json.loads((root / "reports" / "demand_frontier.json").read_text(encoding="utf-8"))
        results = report["results"]
        grid = {(row["lambda_per_hour"], row["shifts"]) for row in results}
        fixed = (
            grid == {(demand, shifts) for demand in (120, 200, 300, 400) for shifts in (1, 2, 3)}
            and report["night_shift_premium"] == 1.5
            and (root / "reports" / "executive_charts" / "09_robot_entry_frontier.png").exists()
        )
    except (FileNotFoundError, KeyError, json.JSONDecodeError, TypeError):
        fixed = False
    ratchet("F-232", fixed=fixed, gap_msg="frontier grid, premium, or chart is missing")
