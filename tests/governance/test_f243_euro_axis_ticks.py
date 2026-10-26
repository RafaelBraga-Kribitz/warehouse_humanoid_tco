"""F-243 — euro axis tick labels must show the plotted value, not value / 1e6 twice.

Charts 06 and 09 once plotted values already in €M while the axis formatter divided
by 1,000,000 again, so every tick read ``€0.0M`` / ``€-0.0M``. Charts that use
``EURO_MILLIONS`` must plot raw euros. This test renders the real chart code, reads the
tick labels Matplotlib actually produced, and compares each to its tick position.
"""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
from collections.abc import Callable
from pathlib import Path

import matplotlib
import polars as pl
import pytest

matplotlib.use("Agg")

from matplotlib.figure import Figure  # noqa: E402

from warehouse_humanoid_tco.analysis.crew_optimizer import generate_demand_frontier  # noqa: E402
from warehouse_humanoid_tco.pipelines.module_04_dashboards import (  # noqa: E402
    generate_executive_charts,
)
from warehouse_humanoid_tco.visualization.chart_style import euro_millions  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
EURO_LABEL = re.compile(r"^€(-?[\d,]+\.\d)M$")


def _install_tick_spy(
    monkeypatch: pytest.MonkeyPatch,
) -> Callable[[], list[list[tuple[float, float]]]]:
    """Record (label value in €M, tick position in €M) pairs for every euro-labelled axis."""
    axes_seen: list[list[tuple[float, float]]] = []
    original = Figure.savefig

    def spy(self: Figure, *args: object, **kwargs: object) -> None:
        self.canvas.draw()
        for ax in self.axes:
            for axis in (ax.xaxis, ax.yaxis):
                low, high = sorted(axis.get_view_interval())
                pairs = []
                for loc, tick in zip(axis.get_majorticklocs(), axis.get_major_ticks(), strict=True):
                    match = EURO_LABEL.match(tick.label1.get_text())
                    if match and low <= loc <= high:
                        pairs.append((float(match.group(1).replace(",", "")), loc / 1_000_000))
                if pairs:
                    axes_seen.append(pairs)
        original(self, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(Figure, "savefig", spy)
    return lambda: axes_seen


def _assert_ticks_match_positions(axes_seen: list[list[tuple[float, float]]]) -> None:
    assert axes_seen, "no euro-labelled axis was rendered"
    for pairs in axes_seen:
        for label_value, position in pairs:
            assert (
                abs(label_value - position) <= 0.051
            ), f"tick at €{position:.2f}M is labelled €{label_value:.1f}M"
        labels = [label for label, _ in pairs]
        assert len(set(labels)) == len(labels), f"duplicate tick labels: {labels}"


def test_euro_millions_formatter_takes_raw_euros() -> None:
    assert euro_millions(2_500_000, 0) == "€2.5M"
    assert euro_millions(-1_000_000, 0) == "€-1.0M"
    assert euro_millions(0, 0) == "€0.0M"


def test_chart_06_effect_decomposition_ticks_show_plotted_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    processed = tmp_path / "processed"
    processed.mkdir()
    pl.DataFrame(
        {
            "scenario_id": [
                "Legacy Overstaffed Team",
                "Lean Human + AMR Team",
                "Lean Human Team",
                "All-Humanoid Team",
            ],
            "npv_eur": [-1_700_000.0, -450_000.0, -650_000.0, -2_900_000.0],
            "total_capex_eur": [0.0, 195_000.0, 0.0, 2_050_000.0],
            "total_opex_5yr_eur_pv": [1_700_000.0, 255_000.0, 650_000.0, 850_000.0],
            "cost_per_order_eur": [1.44, 0.37, 0.54, 2.41],
        }
    ).write_parquet(processed / "tco_scenarios.parquet")
    pl.DataFrame(
        {
            "scenario_id": ["Legacy Overstaffed Team", "Lean Human + AMR Team"],
            "target_rho": [0.85, 0.85],
            "total_agents": [8, 4],
            "bottleneck_agent_type": ["human", "amr"],
            "bottleneck_cycle_time_seconds": [25.0, 87.5],
            "lambda_max_per_hour": [979.2, 140.0],
            "capacity_orders_per_shift": [7834.0, 1119.0],
            "observed_throughput_mean": [7780.0, 1103.0],
            "observed_throughput_std": [40.0, 32.0],
            "n_runs_at_ceiling": [5, 5],
        }
    ).write_parquet(processed / "simulation_capacity_ceiling.parquet")
    get_axes = _install_tick_spy(monkeypatch)

    try:
        generate_executive_charts(processed, tmp_path / "charts")
    except Exception as exc:  # pragma: no cover - fixture too thin for another chart
        if not (tmp_path / "charts" / "06_effect_decomposition.png").exists():
            pytest.skip(f"fixture too thin to reach chart 06: {exc}")

    _assert_ticks_match_positions(get_axes())
    assert (tmp_path / "charts" / "06_effect_decomposition.png").exists()


def test_chart_09_frontier_ticks_show_plotted_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shutil.copytree(REPO_ROOT / "config", tmp_path / "config")
    get_axes = _install_tick_spy(monkeypatch)

    result = generate_demand_frontier(tmp_path)

    assert result["chart"].exists()
    _assert_ticks_match_positions(get_axes())


EURO_K_LABEL = re.compile(r"^€(-?[\d,]+)K$")


def _load_tornado_module() -> object:
    spec = importlib.util.spec_from_file_location(
        "generate_tornado_chart", REPO_ROOT / "scripts" / "generate_tornado_chart.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tornado_project(tmp_path: Path) -> Path:
    """A scratch project holding the committed sensitivity report and an OAT table built from it."""
    report = json.loads((REPO_ROOT / "reports" / "sensitivity_analysis_report.json").read_text())
    base = -460_171.33
    rows: dict[str, list] = {"parameter": [], "npv_eur": [], "delta_vs_base": []}
    for item in report["oat_elasticity_ranking"]:
        for sign in (-1.0, 0.0, 1.0):
            delta = sign * item["peak_delta_vs_base_eur"]
            rows["parameter"].append(item["parameter"])
            rows["npv_eur"].append(base + delta)
            rows["delta_vs_base"].append(delta)
    (tmp_path / "data" / "processed").mkdir(parents=True)
    (tmp_path / "reports").mkdir()
    pl.DataFrame(rows).write_parquet(
        tmp_path / "data" / "processed" / "sensitivity_oat_results.parquet"
    )
    (tmp_path / "reports" / "sensitivity_analysis_report.json").write_text(json.dumps(report))
    return tmp_path


def test_chart_04_tornado_ticks_are_distinct_and_labels_readable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Chart 04 once labelled every tick €-0.5M or €-0.4M and showed raw config keys."""
    module = _load_tornado_module()
    seen: dict[str, list] = {}
    original = Figure.savefig

    def spy(self: Figure, *args: object, **kwargs: object) -> None:
        self.canvas.draw()
        ax = self.axes[0]
        low, high = sorted(ax.xaxis.get_view_interval())
        seen["x"] = [
            (tick.label1.get_text(), loc)
            for loc, tick in zip(
                ax.xaxis.get_majorticklocs(), ax.xaxis.get_major_ticks(), strict=True
            )
            if low <= loc <= high
        ]
        seen["y"] = [label.get_text() for label in ax.get_yticklabels()]
        original(self, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(Figure, "savefig", spy)
    out = module.main(_tornado_project(tmp_path))  # type: ignore[attr-defined]
    assert out.exists()

    labels = [text for text, _ in seen["x"]]
    assert len(labels) >= 3 and len(set(labels)) == len(labels), f"duplicate ticks: {labels}"
    for text, loc in seen["x"]:
        match = EURO_K_LABEL.match(text)
        assert match, f"unexpected tick label {text!r}"
        assert abs(float(match.group(1).replace(",", "")) * 1000 - loc) <= 500, (text, loc)

    report = json.loads((REPO_ROOT / "reports" / "sensitivity_analysis_report.json").read_text())
    parameters = report["oat_parameter_ranges"].keys()
    assert set(parameters) <= module.PARAM_LABELS.keys()  # type: ignore[attr-defined]
    assert len(seen["y"]) == len(parameters)
    for label in seen["y"]:
        assert "_" not in label, f"code name on the axis: {label!r}"
