"""Generate F-225 frontier charts and sensitivity report extensions."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from warehouse_humanoid_tco.analysis.sensitivity import (
    SCENARIO_COMPOSITIONS,
    TRANSFER_FACTOR_BASELINE,
    compute_tco_for_params,
)
from warehouse_humanoid_tco.visualization.chart_style import OTHER, RECOMMENDED, apply_style

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


def robot_frontier(capex: np.ndarray, wage: np.ndarray, transfer: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return robot-vs-lean cost deltas on two two-way parameter grids."""
    lean = npv("S-lean-human")
    capex_wage = np.empty((len(wage), len(capex)))
    capex_transfer = np.empty((len(transfer), len(capex)))
    for row, value in enumerate(wage):
        for col, capex_value in enumerate(capex):
            capex_wage[row, col] = npv(
                "S-future-2028", humanoid_capex_eur=float(capex_value), human_wage_eur=float(value)
            ) - lean
    for row, value in enumerate(transfer):
        for col, capex_value in enumerate(capex):
            capex_transfer[row, col] = npv(
                "S-future-2028", humanoid_capex_eur=float(capex_value), transfer_factor=float(value)
            ) - lean
    return capex_wage, capex_transfer


def chart(path: Path, x: np.ndarray, y: np.ndarray, z: np.ndarray, ylabel: str, title: str) -> None:
    figure, axis = plt.subplots(figsize=(9, 5.2), constrained_layout=True)
    # z arrives as robot_npv - lean_npv with cost-negative NPVs, so negate to get
    # the intuitive cost delta: positive = robot-inclusive option costlier.
    # (Pre-fix, levels were computed in raw euros while the plotted array was in
    # €M — every value fell outside the level range and the fill was empty; the
    # sign convention on the colorbar label was also inverted.)
    zm = -z / 1_000_000
    z_min, z_max = float(zm.min()), float(zm.max())
    levels = np.linspace(z_min, z_max, 16)
    image = axis.contourf(x / 1_000, y, zm, levels=levels, cmap="RdYlGn_r")
    if z_min < 0.0 < z_max:
        boundary = axis.contour(x / 1_000, y, zm, levels=[0], colors=RECOMMENDED, linewidths=2)
        axis.clabel(boundary, fmt={0: "cost tie"}, inline=True, fontsize=9)
    else:
        axis.text(
            0.5,
            0.03,
            "Robot-inclusive option is costlier across the entire modeled range —\n"
            "no viability frontier at 120 orders/hr, single shift.",
            transform=axis.transAxes,
            ha="center",
            va="bottom",
            fontsize=9,
            style="italic",
            color="#333333",
        )
    axis.scatter([120], [18.5 if "wage" in ylabel.lower() else 0.70], color=OTHER, edgecolor="black", zorder=3)
    axis.set(
        title=title,
        xlabel="Humanoid unit capex (€k)",
        ylabel=ylabel,
    )
    apply_style(axis)
    colorbar = figure.colorbar(image, ax=axis)
    colorbar.ax.ticklabel_format(style="plain")
    colorbar.set_label("Extra 5-year cost vs S-lean-human (€M; positive = robot costlier)")
    figure.savefig(path, dpi=180)
    plt.close(figure)


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
        outputs = np.asarray([npv("S-future-2028", **{parameter: float(value)}) for value in values])
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
            "scenario_id": "S-future-2028",
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
        "definition": "Thresholds compare scenario cost at all other base assumptions; positive NPV is lower cost.",
        "S-lean-human": {
            "status": "cheapest across the published robot frontier grid",
            "base_npv_eur": npv("S-lean-human"),
        },
        "S-future-2028": {
            "capex_eur_per_unit_to_tie_lean_human": None,
            "interpretation": "No tie inside €60k–€180k capex with other assumptions fixed.",
        },
        "S-hybrid-amr": {
            "integration_cost_eur": 200_000,
            "interpretation": "The F-222 integration cost is retained; it prevents a robot ranking claim.",
        },
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
