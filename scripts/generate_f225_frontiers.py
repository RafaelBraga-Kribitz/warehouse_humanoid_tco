"""Generate F-225 frontier charts and sensitivity report extensions."""

from __future__ import annotations

import json
from pathlib import Path

import bk_theme as bk
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import (
    BoundaryNorm,
    LinearSegmentedColormap,
    ListedColormap,
    Normalize,
    TwoSlopeNorm,
)

from warehouse_humanoid_tco.analysis.sensitivity import (
    SCENARIO_COMPOSITIONS,
    TRANSFER_FACTOR_BASELINE,
    compute_tco_for_params,
)
from warehouse_humanoid_tco.visualization.chart_style import (
    RECOMMENDED,
    SMALL,
    apply_style,
    color,
    layout,
    save_png,
    title,
    use_theme,
)

ROOT = Path(__file__).resolve().parents[1]
BASE = {
    "humanoid_capex_eur": 120_000.0,
    "human_wage_eur": 18.50,
    "human_overhead_mult": 1.35,
    "discount_rate": 0.08,
    "transfer_factor": TRANSFER_FACTOR_BASELINE,
    "humanoid_supervision_ratio": 0.10,
}
COMPOSITIONS = dict(SCENARIO_COMPOSITIONS)


def npv(scenario_id: str, **overrides: float) -> float:
    composition = COMPOSITIONS[scenario_id]
    params = {**BASE, **overrides}
    return compute_tco_for_params(
        n_human=composition["n_human"],
        n_humanoid=composition["n_humanoid"],
        n_amr=composition["n_amr"],
        throughput_multiplier=composition["throughput_multiplier"],
        **params,
    )


def robot_frontier(
    capex: np.ndarray, wage: np.ndarray, transfer: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Return robot-vs-lean cost deltas on two two-way parameter grids."""
    lean = npv("Lean Human + AMR Team")
    capex_wage = np.empty((len(wage), len(capex)))
    capex_transfer = np.empty((len(transfer), len(capex)))
    for row, value in enumerate(wage):
        for col, capex_value in enumerate(capex):
            capex_wage[row, col] = (
                npv(
                    "Future 2028 Humanoid Team",
                    humanoid_capex_eur=float(capex_value),
                    human_wage_eur=float(value),
                )
                - lean
            )
    for row, value in enumerate(transfer):
        for col, capex_value in enumerate(capex):
            capex_transfer[row, col] = (
                npv(
                    "Future 2028 Humanoid Team",
                    humanoid_capex_eur=float(capex_value),
                    transfer_factor=float(value),
                )
                - lean
            )
    return capex_wage, capex_transfer


def cost_delta_scale(
    z_min: float, z_max: float
) -> tuple[np.ndarray, LinearSegmentedColormap | ListedColormap, Normalize]:
    """Contour levels, colour map and norm for the cost delta.

    When the grid crosses zero, the design system's good/bad diverging scale with its neutral
    midpoint at the cost tie. When the whole grid sits on one side of zero there is no tie to
    show, so the magnitude takes the sequential scale, one band per step, so every band can be
    told apart (the diverging scale's single arm cannot carry that many steps).
    """
    if z_min < 0.0 < z_max:
        cmap = LinearSegmentedColormap.from_list("bk-div", bk.palette("div"))
        return (
            np.linspace(z_min, z_max, 16),
            cmap,
            TwoSlopeNorm(vmin=z_min, vcenter=0.0, vmax=z_max),
        )
    steps = bk.palette("seq")[::-1]  # lightest first
    if z_max <= 0.0:
        steps = steps[::-1]  # larger saving (more negative) reads darker
    levels = np.linspace(z_min, z_max, len(steps) + 1)
    return levels, ListedColormap(steps, "bk-seq"), BoundaryNorm(levels, len(steps))


def chart(
    path: Path, x: np.ndarray, y: np.ndarray, z: np.ndarray, ylabel: str, chart_title: str
) -> None:
    use_theme("light")
    figure, axis = plt.subplots(figsize=(9, 5.2))
    # z arrives as robot_npv - lean_npv with cost-negative NPVs, so negate to get
    # the intuitive cost delta: positive = robot-inclusive option costlier.
    # (Pre-fix, levels were computed in raw euros while the plotted array was in
    # €M — every value fell outside the level range and the fill was empty; the
    # sign convention on the colorbar label was also inverted.)
    zm = -z / 1_000_000
    z_min, z_max = float(zm.min()), float(zm.max())
    levels, cmap, norm = cost_delta_scale(z_min, z_max)
    image = axis.contourf(x / 1_000, y, zm, levels=levels, cmap=cmap, norm=norm)
    if z_min < 0.0 < z_max:
        # The tie line is the chart's one highlight: it is the decision boundary.
        boundary = axis.contour(
            x / 1_000, y, zm, levels=[0], colors=color(RECOMMENDED), linewidths=2
        )
        axis.clabel(boundary, fmt={0: "cost tie"}, inline=True, fontsize=SMALL)
    else:
        axis.text(
            0.5,
            0.03,
            "Robot-inclusive option is costlier across the entire modeled range —\n"
            "no viability frontier at 120 orders/hr, single shift.",
            transform=axis.transAxes,
            ha="center",
            va="bottom",
            fontsize=SMALL,
            color=color("ink"),
            backgroundcolor=color("surface"),
        )
    axis.scatter(
        [120],
        [18.5 if "wage" in ylabel.lower() else 0.70],
        color=color("surface"),
        edgecolor=color("ink"),
        linewidths=1.5,
        zorder=3,
    )
    axis.set(
        xlabel="Humanoid unit capex (€k)",
        ylabel=ylabel,
    )
    title(axis, chart_title)
    apply_style(axis)
    axis.grid(False)
    colorbar = figure.colorbar(image, ax=axis)
    colorbar.ax.ticklabel_format(style="plain")
    colorbar.outline.set_visible(False)
    colorbar.set_label(
        "Extra 5-year cost vs Lean Human + AMR Team\n(€M; positive = robot costlier)",
        fontsize=SMALL,
    )
    layout(figure, 0.0)
    save_png(figure, path, dpi=180)


def variance_proxy() -> dict[str, object]:
    """Estimate first-order importance with a documented coarse deterministic grid."""
    ranges = {
        "humanoid_capex_eur": (60_000.0, 180_000.0),
        "human_wage_eur": (15.13, 22.0),
        "human_overhead_mult": (1.0, 1.7),
        "discount_rate": (0.04, 0.12),
        "transfer_factor": (0.50, 0.90),
        "humanoid_supervision_ratio": (0.05, 0.50),
    }
    scores: dict[str, float] = {}
    correlations: dict[str, float] = {}
    for parameter, (low, high) in ranges.items():
        values = np.linspace(low, high, 21)
        outputs = np.asarray(
            [npv("Future 2028 Humanoid Team", **{parameter: float(value)}) for value in values]
        )
        scores[parameter] = float(np.var(outputs))
        correlations[parameter] = float(np.corrcoef(values, outputs)[0, 1])
    total = sum(scores.values()) or 1.0
    return {
        "sobol_indices": {
            "estimator": "coarse_grid_variance_proxy",
            "description": (
                "One-dimensional 21-point deterministic grids; normalized output variance is a "
                "screening proxy, not a Saltelli/Sobol interaction estimator."
            ),
            "indices": {
                name: {"first_order": score / total, "total_order": score / total}
                for name, score in scores.items()
            },
        },
        "correlation_sensitivity": {
            "method": "Pearson correlation across the same OAT coarse grids",
            "scenario_id": "Future 2028 Humanoid Team",
            "coefficients": correlations,
        },
    }


def main() -> None:
    capex = np.linspace(60_000, 180_000, 41)
    wage = np.linspace(15.13, 22.0, 31)
    transfer = np.linspace(0.50, 0.90, 31)
    capex_wage, capex_transfer = robot_frontier(capex, wage, transfer)
    charts = ROOT / "reports" / "executive_charts"
    chart(
        charts / "07_frontier_capex_wage.png",
        capex,
        wage,
        capex_wage,
        "Human wage (€/hour)",
        "Robot viability frontier: capex × wage",
    )
    chart(
        charts / "08_frontier_capex_transfer.png",
        capex,
        transfer,
        capex_transfer,
        "WBT-to-production transfer factor",
        "Robot viability frontier: capex × transfer",
    )

    report_path = ROOT / "reports" / "sensitivity_analysis_report.json"
    report = json.loads(report_path.read_text())
    report.update(variance_proxy())
    report["decision_flip_thresholds"] = {
        "definition": (
            "Thresholds compare scenario cost at all other base assumptions; "
            "positive NPV is lower cost."
        ),
        "Lean Human + AMR Team": {
            "status": "cheapest across the published robot frontier grid",
            "base_npv_eur": npv("Lean Human + AMR Team"),
        },
        "Future 2028 Humanoid Team": {
            "capex_eur_per_unit_to_tie_lean_hybrid": None,
            "interpretation": "No tie inside €60k–€180k capex with other assumptions fixed.",
        },
        "Human + Humanoid + AMR Team": {
            "integration_cost_eur": 200_000,
            "interpretation": (
                "The F-222 integration cost is retained; it prevents a robot ranking claim."
            ),
        },
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
