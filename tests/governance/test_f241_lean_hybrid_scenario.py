"""F-241 — frontier lean hybrid scenario + informative chart 09."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import yaml
from _ratchet import ratchet

ROOT = Path(__file__).resolve().parents[2]


def test_f241_lean_hybrid_scenario_and_chart09() -> None:
    config = yaml.safe_load(
        (ROOT / "config" / "autostore_baseline.yaml").read_text(encoding="utf-8")
    )
    scenarios = {row["id"]: row for row in config["scenarios"]}
    hybrid = scenarios.get("S-lean-hybrid-amr")
    counts_ok = hybrid is not None and hybrid.get("agent_counts") == {
        "human": 1,
        "humanoid": 0,
        "amr": 3,
    }

    with (ROOT / "exports" / "tableau_public" / "tco_scenarios.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        rows = {row["scenario_id"]: row for row in csv.DictReader(handle)}
    hybrid_npv = (
        float(rows["S-lean-hybrid-amr"]["npv_eur"]) if "S-lean-hybrid-amr" in rows else None
    )
    lean_npv = float(rows["S-lean-human"]["npv_eur"]) if "S-lean-human" in rows else None
    cheapest_ok = (
        hybrid_npv is not None
        and lean_npv is not None
        and hybrid_npv >= lean_npv  # less-negative / higher NPV = lower cost
    )

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    charter = (ROOT / "PROJECT_CHARTER.md").read_text(encoding="utf-8")
    narrative_ok = (
        "S-lean-hybrid-amr" in readme
        and "S-lean-hybrid-amr" in charter
        and "queued follow-up" not in readme.lower()
    )

    frontier = json.loads((ROOT / "reports" / "demand_frontier.json").read_text(encoding="utf-8"))
    series = {
        shifts: [
            row["npv_eur"] / 1_000_000 for row in frontier["results"] if row["shifts"] == shifts
        ]
        for shifts in (1, 2, 3)
    }
    pairs_differ = series[1] != series[2] and series[1] != series[3] and series[2] != series[3]
    chart_path = ROOT / "reports" / "executive_charts" / "09_robot_entry_frontier.png"
    chart_ok = chart_path.exists() and chart_path.stat().st_size > 1_000

    crew_optimizer = (
        ROOT / "src" / "warehouse_humanoid_tco" / "analysis" / "crew_optimizer.py"
    ).read_text(encoding="utf-8")
    style_ok = "chart_style" in crew_optimizer and "EURO_MILLIONS" in crew_optimizer

    tco_report = json.loads(
        (ROOT / "reports" / "module_03_tco_report.json").read_text(encoding="utf-8")
    )
    vs_lean = tco_report["breakeven_thresholds"]["vs_lean_human"]
    breakeven_ok = (
        vs_lean.get("no_breakeven_in_search_range") is True
        and vs_lean.get("capex_eur_per_unit") is None
        and "S-lean-hybrid-amr" in vs_lean.get("methodology", "")
    )

    fixed = (
        counts_ok
        and cheapest_ok
        and narrative_ok
        and pairs_differ
        and chart_ok
        and style_ok
        and breakeven_ok
    )
    ratchet(
        "F-241",
        fixed=fixed,
        gap_msg=(
            "S-lean-hybrid-amr missing/mis-sized, not cheapest, narrative incomplete, "
            "chart 09 series identical, or vs_lean not recomputed vs hybrid"
        ),
    )
