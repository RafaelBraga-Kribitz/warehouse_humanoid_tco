"""F-044 — chart 03 must plot a capacity-discriminating metric, not demand-bound throughput.

Ratchet pattern: while F-044 is open the test xfails on a still-broken state.
Once `status: closed`, regression on any of the three guards below fails the
Adversary CI job and reopens the finding.

Guards:
  1. data/processed/simulation_capacity_ceiling.parquet exists and has one row
     per scenario declared in config/autostore_baseline.yaml.
  2. capacity_orders_per_shift spread (max - min) exceeds 500 — i.e. the metric
     actually discriminates scenarios. Below 500 we are back in Poisson(960)
     noise territory and the chart has no discriminative power.
  3. src/.../pipelines/module_04_dashboards.py reads
     simulation_capacity_ceiling.parquet (not simulation_runs.parquet) when
     building the file `03_simulation_throughput.png`. Catches future
     contributors who "refresh" the chart by reverting to the demand-bound
     metric without realising why F-044 closed it.
"""

from __future__ import annotations

import re

import polars as pl
import yaml
from _ratchet import REPO_ROOT, ratchet

CONFIG = REPO_ROOT / "config" / "autostore_baseline.yaml"
CAPACITY_PARQUET = REPO_ROOT / "data" / "processed" / "simulation_capacity_ceiling.parquet"
MODULE_04 = (
    REPO_ROOT / "src" / "warehouse_humanoid_tco" / "pipelines" / "module_04_dashboards.py"
)

MIN_CAPACITY_SPREAD_ORDERS = 500
REQUIRED_COLUMNS = {
    "scenario_id",
    "target_rho",
    "capacity_orders_per_shift",
    "observed_throughput_mean",
    "bottleneck_agent_type",
}


def _expected_scenarios() -> set[str]:
    cfg = yaml.safe_load(CONFIG.read_text()) or {}
    return {s["id"] for s in cfg.get("scenarios", []) if "id" in s}


def test_capacity_ceiling_parquet_present_and_complete() -> None:
    if not CAPACITY_PARQUET.exists():
        ratchet(
            "F-044",
            fixed=False,
            gap_msg=f"{CAPACITY_PARQUET.relative_to(REPO_ROOT)} missing — run module-02",
        )
        return
    df = pl.read_parquet(CAPACITY_PARQUET)
    missing_cols = REQUIRED_COLUMNS - set(df.columns)
    if missing_cols:
        ratchet(
            "F-044",
            fixed=False,
            gap_msg=f"capacity parquet missing columns: {sorted(missing_cols)}",
        )
        return
    expected = _expected_scenarios()
    actual = set(df["scenario_id"].to_list())
    if expected and expected != actual:
        ratchet(
            "F-044",
            fixed=False,
            gap_msg=(
                f"capacity parquet scenarios {sorted(actual)} != "
                f"config scenarios {sorted(expected)}"
            ),
        )
        return
    ratchet("F-044", fixed=True, gap_msg="")


def test_capacity_metric_discriminates_scenarios() -> None:
    if not CAPACITY_PARQUET.exists():
        ratchet("F-044", fixed=False, gap_msg="capacity parquet absent (see other guard)")
        return
    caps = pl.read_parquet(CAPACITY_PARQUET)["capacity_orders_per_shift"].to_list()
    if len(caps) < 2:
        ratchet("F-044", fixed=False, gap_msg="<2 scenarios; cannot measure spread")
        return
    spread = max(caps) - min(caps)
    if spread < MIN_CAPACITY_SPREAD_ORDERS:
        ratchet(
            "F-044",
            fixed=False,
            gap_msg=(
                f"capacity spread {spread:.0f} < {MIN_CAPACITY_SPREAD_ORDERS} — "
                f"chart is back in the demand-bound regime"
            ),
        )
        return
    ratchet("F-044", fixed=True, gap_msg="")


def test_module_04_reads_capacity_parquet() -> None:
    if not MODULE_04.exists():
        ratchet("F-044", fixed=True, gap_msg="module_04_dashboards.py absent — vacuously fixed")
        return
    text = MODULE_04.read_text()
    reads_capacity = bool(
        re.search(r"simulation_capacity_ceiling\.parquet", text)
    )
    chart_filename_present = "03_simulation_throughput.png" in text
    # Both signals required: the chart filename references the F-044 output AND
    # the new parquet is loaded. Either alone is insufficient — a contributor
    # could load capacity but plot from simulation_runs (regression), or rename
    # the chart file while still loading simulation_runs (also regression).
    ratchet(
        "F-044",
        fixed=reads_capacity and chart_filename_present,
        gap_msg=(
            f"module_04_dashboards.py: reads_capacity={reads_capacity} "
            f"chart_filename_present={chart_filename_present}"
        ),
    )
