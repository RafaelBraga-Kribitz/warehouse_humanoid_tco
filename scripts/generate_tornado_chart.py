"""Generate OAT sensitivity tornado chart from sensitivity_oat_results.parquet."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl

from warehouse_humanoid_tco.visualization.chart_style import (
    ADVERSE,
    BASELINE,
    EURO_MILLIONS,
    RECOMMENDED,
    apply_style,
)

PARAM_LABELS = {
    "humanoid_capex_eur": "Humanoid Capex (€/unit)",
    "human_wage_eur": "Labor Cost (€/hr)",
    "human_overhead_mult": "Labor Overhead Multiplier",
    "discount_rate": "Discount Rate",
    "transfer_factor": "WBT→Production Transfer Factor",
}


def main() -> None:
    project_root = Path(__file__).parent.parent
    oat_path = project_root / "data" / "processed" / "sensitivity_oat_results.parquet"
    out_path = project_root / "reports" / "executive_charts" / "04_sensitivity_tornado.png"
    report = json.loads((project_root / "reports" / "sensitivity_analysis_report.json").read_text())
    elasticities = {
        item["parameter"]: item["peak_elasticity"] for item in report["oat_elasticity_ranking"]
    }

    df = pl.read_parquet(oat_path)

    # Baseline NPV is the OAT pivot, derived from the data (npv - delta_vs_base
    # is constant across rows) rather than hardcoded — so the chart cannot drift
    # from the model when the scenario NPV changes (audit Risk #5).
    baseline_npv = float((df["npv_eur"] - df["delta_vs_base"])[0])

    # For each parameter compute low/high NPV (min/max of npv_eur)
    summary = (
        df.group_by("parameter")
        .agg(
            pl.col("npv_eur").min().alias("npv_low"),
            pl.col("npv_eur").max().alias("npv_high"),
        )
        .with_columns((pl.col("npv_high") - pl.col("npv_low")).abs().alias("npv_range"))
        .sort("npv_range", descending=True)
    )

    params = summary["parameter"].to_list()
    npv_low = summary["npv_low"].to_list()
    npv_high = summary["npv_high"].to_list()

    labels = [f"{PARAM_LABELS.get(p, p)}  (ε≈{elasticities[p]:.2f})" for p in params]

    fig, ax = plt.subplots(figsize=(10, 6))

    y_pos = range(len(params))

    for i, (low, high, _label) in enumerate(zip(npv_low, npv_high, labels, strict=True)):
        # Low side (more negative = higher cost)
        ax.barh(i, low - baseline_npv, left=baseline_npv, color=ADVERSE, alpha=0.85, height=0.5)
        # High side (less negative = lower cost)
        ax.barh(
            i, high - baseline_npv, left=baseline_npv, color=RECOMMENDED, alpha=0.85, height=0.5
        )

    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(labels, fontsize=11)
    ax.axvline(baseline_npv, color=BASELINE, linewidth=1.2, linestyle="--", alpha=0.8)

    ax.set_xlabel("5-Year NPV (€)", fontsize=11)
    ax.set_title(
        "Sensitivity Analysis: What drives 5-year TCO most?",
        fontsize=13,
        fontweight="bold",
        pad=12,
    )
    ax.text(
        0.5,
        1.01,
        "S-hybrid-amr scenario · OAT across config ranges · "
        f"baseline NPV = €{baseline_npv/1000:,.0f}K",
        transform=ax.transAxes,
        ha="center",
        fontsize=9,
        color="gray",
    )

    apply_style(ax)
    ax.xaxis.set_major_formatter(EURO_MILLIONS)

    from matplotlib.patches import Patch

    legend_elements = [
        Patch(facecolor=ADVERSE, alpha=0.85, label="Parameter at adverse end (higher cost)"),
        Patch(facecolor=RECOMMENDED, alpha=0.85, label="Parameter at favorable end (lower cost)"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=9)

    fig.text(
        0.01,
        0.01,
        "Source: sensitivity_analysis_report.json · ε≈normalised elasticity",
        fontsize=7,
        color=BASELINE,
    )
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"Saved tornado chart → {out_path}")


if __name__ == "__main__":
    main()
