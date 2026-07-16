"""F-211 — recompute artifact-backed experiment verdicts."""

from __future__ import annotations

import csv
import json
import sys

from _governance_check import REPO_ROOT, gate


def verdict_line(text: str, hypothesis: str, supported: bool) -> bool:
    verdict = "SUPPORTED" if supported else "REJECTED"
    return f"VERDICT {hypothesis}: {verdict} —" in text


def main() -> int:
    experiments = (REPO_ROOT / "governance" / "EXPERIMENTS.md").read_text(encoding="utf-8")
    with (REPO_ROOT / "exports" / "tableau_public" / "tco_scenarios.csv").open(
        encoding="utf-8", newline=""
    ) as csv_file:
        scenarios = list(csv.DictReader(csv_file))
    tco_report = json.loads(
        (REPO_ROOT / "reports" / "module_03_tco_report.json").read_text(encoding="utf-8")
    )
    sensitivity_report = json.loads(
        (REPO_ROOT / "reports" / "sensitivity_analysis_report.json").read_text(encoding="utf-8")
    )

    h2_supported = any(
        row["scenario_id"] not in {"S-baseline-human", "S-lean-human"}
        and float(row["total_cost_reduction_vs_baseline_pct"]) > 0
        for row in scenarios
    )
    breakeven = tco_report["breakeven_thresholds"]
    h3_supported = (
        breakeven["capex_eur_per_unit"] >= 120000
        and breakeven["capex_eur_per_unit"] >= breakeven["current_capex_eur_per_unit"]
    )
    summaries = sensitivity_report["mc_summary_per_scenario"]
    winner_id = max(summaries, key=lambda scenario_id: summaries[scenario_id]["npv_mean"])
    h4_supported = summaries[winner_id]["npv_p5"] > summaries["S-baseline-human"]["npv_mean"]
    ok = (
        all(f"## H{number} " in experiments for number in range(1, 5))
        and verdict_line(experiments, "H2", h2_supported)
        and verdict_line(experiments, "H3", h3_supported)
        and verdict_line(experiments, "H4", h4_supported)
    )
    return gate(
        "check_hypothesis_verdicts.py",
        "F-211",
        ok=ok,
        ok_msg=f"H2–H4 verdicts match artifacts (winner: {winner_id})",
        gap_msg="H1–H4 headings or recomputed H2–H4 verdicts are missing/mismatched",
    )


if __name__ == "__main__":
    sys.exit(main())
