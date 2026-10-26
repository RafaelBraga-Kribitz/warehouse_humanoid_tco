"""Generate OAT sensitivity tornado chart from sensitivity_oat_results.parquet."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl

from warehouse_humanoid_tco.visualization.chart_style import (
    ADVERSE,
    BASELINE,
    EURO_THOUSANDS,
    RECOMMENDED,
    apply_style,
)

# Plain-language name and unit formatter for each OAT parameter in
# config/tco_assumptions.yaml::sensitivity.oat. Every OAT parameter needs an entry;
# tests/governance/test_f243_euro_axis_ticks.py fails if one is missing.
PARAM_LABELS: dict[str, tuple[str, Callable[[float], str]]] = {
    "humanoid_capex_eur": ("Humanoid robot price", lambda v: f"€{v / 1000:,.0f}K"),
    "human_wage_eur": ("Hourly wage", lambda v: f"€{v:,.2f}"),
    "human_overhead_mult": ("Employer costs on top of wage", lambda v: f"×{v:.2f}"),
    "discount_rate": ("Discount rate", lambda v: f"{v * 100:.0f}%"),
    "transfer_factor": (
        "Share of lab robot skill that works in a warehouse",
        lambda v: f"{v * 100:.0f}%",
    ),
    "humanoid_supervision_ratio": (
        "Full-time supervisors per humanoid robot",
        lambda v: f"{v:.2f}",
    ),
}


def parameter_label(parameter: str, low: float, high: float) -> str:
    """Readable axis label for one OAT parameter, with the range it was moved over."""
    name, fmt = PARAM_LABELS[parameter]
    return f"{name}\n({fmt(low)} to {fmt(high)})"


def main(project_root: Path | None = None) -> Path:
    project_root = project_root or Path(__file__).parent.parent
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
        .sort(["npv_range", "parameter"], descending=[True, False])
    )

    params = summary["parameter"].to_list()
    npv_low = summary["npv_low"].to_list()
    npv_high = summary["npv_high"].to_list()

    ranges = report["oat_parameter_ranges"]
    labels = [parameter_label(p, *ranges[p]) for p in params]

    fig, ax = plt.subplots(figsize=(11, 6.5))

    y_pos = range(len(params))

    span = max(npv_high) - min(npv_low)
    for i, (param, low, high) in enumerate(zip(params, npv_low, npv_high, strict=True)):
        # Low side (more negative = higher cost)
        ax.barh(i, low - baseline_npv, left=baseline_npv, color=ADVERSE, alpha=0.85, height=0.5)
        # High side (less negative = lower cost)
        ax.barh(
            i, high - baseline_npv, left=baseline_npv, color=RECOMMENDED, alpha=0.85, height=0.5
        )
        if high - low < 1.0:
            note = "No effect: this crew has no humanoid robots"
            ax.text(baseline_npv + span * 0.02, i, note, va="center", fontsize=9, color=BASELINE)
        else:
            swing = f"€{(high - low) / 1000:,.0f}K swing · elasticity {elasticities[param]:.2f}"
            ax.text(high + span * 0.02, i, swing, va="center", fontsize=9, color=BASELINE)

    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(labels, fontsize=11)
    ax.axvline(baseline_npv, color=BASELINE, linewidth=1.2, linestyle="--", alpha=0.8)

    ax.set_xlabel(
        "Five-year net present value (€; costs are negative, further right is cheaper)",
        fontsize=11,
    )
    ax.set_title(
        "Which assumptions move the five-year cost most?",
        fontsize=13,
        fontweight="bold",
        pad=12,
    )
    ax.text(
        0.5,
        1.01,
        f"{report['scenario_id']} · one assumption changed at a time · "
        f"base case €{baseline_npv / 1000:,.0f}K (dashed line)",
        transform=ax.transAxes,
        ha="center",
        fontsize=9,
        color="gray",
    )

    apply_style(ax)
    ax.xaxis.set_major_formatter(EURO_THOUSANDS)
    ax.set_xlim(min(npv_low) - span * 0.05, max(npv_high) + span * 0.40)

    from matplotlib.patches import Patch

    legend_elements = [
        Patch(facecolor=ADVERSE, alpha=0.85, label="Assumption at its costlier end"),
        Patch(facecolor=RECOMMENDED, alpha=0.85, label="Assumption at its cheaper end"),
    ]
    ax.legend(
        handles=legend_elements,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.12),
        ncol=2,
        frameon=False,
        fontsize=9,
    )

    fig.text(
        0.01,
        -0.04,
        "Source: sensitivity_analysis_report.json · ranges from config/tco_assumptions.yaml · "
        "elasticity = % change in cost per % change in the assumption",
        fontsize=7,
        color=BASELINE,
    )
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved tornado chart → {out_path}")
    return out_path


if __name__ == "__main__":
    main()
