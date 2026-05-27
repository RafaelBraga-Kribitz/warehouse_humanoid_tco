"""Generate OAT sensitivity tornado chart from sensitivity_oat_results.parquet."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl

PARAM_LABELS = {
    "humanoid_capex_eur": "Humanoid Capex (€/unit)",
    "human_wage_eur": "Labor Cost (€/hr)",
    "human_overhead_mult": "Labor Overhead Multiplier",
    "discount_rate": "Discount Rate",
    "transfer_factor": "WBT→Production Transfer Factor",
}

BASELINE_NPV = -1078786.0  # S-hybrid-amr central estimate (post T0.1 opex fix)


def main() -> None:
    project_root = Path(__file__).parent.parent
    oat_path = project_root / "data" / "processed" / "sensitivity_oat_results.parquet"
    out_path = project_root / "reports" / "executive_charts" / "04_sensitivity_tornado.png"

    df = pl.read_parquet(oat_path)

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

    labels = [PARAM_LABELS.get(p, p) for p in params]

    fig, ax = plt.subplots(figsize=(10, 6))

    y_pos = range(len(params))

    for i, (low, high, _label) in enumerate(zip(npv_low, npv_high, labels, strict=True)):
        # Low side (more negative = higher cost)
        ax.barh(i, low - BASELINE_NPV, left=BASELINE_NPV, color="#E07B39", alpha=0.85, height=0.5)
        # High side (less negative = lower cost)
        ax.barh(i, high - BASELINE_NPV, left=BASELINE_NPV, color="#4A90D9", alpha=0.85, height=0.5)

    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(labels, fontsize=11)
    ax.axvline(BASELINE_NPV, color="black", linewidth=1.2, linestyle="--", alpha=0.6)

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
        "S-hybrid-amr scenario · OAT across config ranges · baseline NPV = €-1,079K",
        transform=ax.transAxes,
        ha="center",
        fontsize=9,
        color="gray",
    )

    # Format x-axis in EUR millions
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"€{x/1e6:.1f}M"))

    from matplotlib.patches import Patch

    legend_elements = [
        Patch(facecolor="#E07B39", alpha=0.85, label="Parameter at low end (higher cost)"),
        Patch(facecolor="#4A90D9", alpha=0.85, label="Parameter at high end (lower cost)"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=9)

    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"Saved tornado chart → {out_path}")


if __name__ == "__main__":
    main()
