"""F-219 — DuckDB projections remain parity-checked against published data."""

from __future__ import annotations

from pathlib import Path

import duckdb
import polars as pl
from _ratchet import ratchet

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = (
    "humanoid_capabilities_summary",
    "simulation_runs",
    "tco_scenarios",
    "simulation_capacity_ceiling",
)


def _query_projection(artifact: str) -> pl.DataFrame:
    sql = (REPO_ROOT / "analytics" / "sql" / f"{artifact}.sql").read_text()
    parquet = REPO_ROOT / "data" / "processed" / f"{artifact}.parquet"
    csv = REPO_ROOT / "exports" / "tableau_public" / f"{artifact}.csv"
    source = (
        f"read_parquet('{parquet.resolve().as_posix()}')"
        if parquet.exists()
        else f"read_csv_auto('{csv.resolve().as_posix()}')"
    )
    return pl.from_arrow(duckdb.sql(sql.replace("{{source}}", source)).to_arrow_table())


def test_sql_projections_have_explicit_columns_and_data_parity() -> None:
    complete = True
    for artifact in ARTIFACTS:
        sql_path = REPO_ROOT / "analytics" / "sql" / f"{artifact}.sql"
        csv_path = REPO_ROOT / "exports" / "tableau_public" / f"{artifact}.csv"
        if not sql_path.exists() or not csv_path.exists():
            complete = False
            continue
        projected = _query_projection(artifact)
        published = pl.read_csv(csv_path)
        complete = (
            complete
            and projected.columns == published.columns
            and projected.height == published.height
        )
        if artifact == "tco_scenarios" and complete:
            assert projected["npv_eur"].sum() == published["npv_eur"].sum()
    ratchet(
        "F-219",
        fixed=complete,
        gap_msg="DuckDB SQL projections are missing or do not match published CSV shape",
    )


def test_dashboard_export_uses_duckdb_sql_layer() -> None:
    module = (
        REPO_ROOT / "src" / "warehouse_humanoid_tco" / "pipelines" / "module_04_dashboards.py"
    ).read_text()
    ratchet(
        "F-219",
        fixed="duckdb" in module and "_duckdb_export" in module and "analytics" in module,
        gap_msg="Module 4 no longer invokes the DuckDB SQL export path",
    )
