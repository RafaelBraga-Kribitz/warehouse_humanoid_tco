"""F-229 — dbt marts must rebuild the published Tableau surface."""

from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

import duckdb
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DBT_DIR = REPO_ROOT / "analytics" / "dbt"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
EXPORT_DIR = REPO_ROOT / "exports" / "tableau_public"
ARTIFACTS = (
    "humanoid_capabilities_summary",
    "simulation_runs",
    "simulation_capacity_ceiling",
    "tco_scenarios",
)


def _create_csv_backed_parquet_fixtures() -> list[Path]:
    """Supply ignored fixtures only when the pipeline outputs are unavailable."""
    created: list[Path] = []
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    with duckdb.connect() as connection:
        for artifact in ARTIFACTS:
            parquet_path = PROCESSED_DIR / f"{artifact}.parquet"
            if parquet_path.exists():
                continue
            csv_path = EXPORT_DIR / f"{artifact}.csv"
            assert csv_path.exists(), f"Missing published CSV fixture: {csv_path}"
            source = csv_path.as_posix().replace("'", "''")
            target = parquet_path.as_posix().replace("'", "''")
            connection.execute(
                f"COPY (SELECT * FROM read_csv_auto('{source}', header = true)) "  # noqa: S608
                f"TO '{target}' (FORMAT PARQUET)"
            )
            created.append(parquet_path)
    return created


def test_dbt_marts_match_tableau_csv_exports() -> None:
    """Build dbt without skips and compare its marts to published CSV data."""
    created = _create_csv_backed_parquet_fixtures()
    try:
        result = subprocess.run(  # noqa: S603 - invokes the current Python interpreter
            [
                sys.executable,
                "-m",
                "dbt.cli.main",
                "build",
                "--project-dir",
                str(DBT_DIR),
                "--profiles-dir",
                str(DBT_DIR),
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"dbt build failed:\n{result.stdout}\n{result.stderr}"

        with duckdb.connect(DBT_DIR / "target" / "whtco.duckdb", read_only=True) as connection:
            for artifact in ARTIFACTS:
                csv_path = EXPORT_DIR / f"{artifact}.csv"
                with csv_path.open(newline="", encoding="utf-8") as handle:
                    csv_columns = next(csv.reader(handle))
                table_name = f"mart_{artifact}"
                dbt_columns = [
                    row[1]
                    for row in connection.execute(f"PRAGMA table_info('{table_name}')").fetchall()
                ]
                assert dbt_columns == csv_columns

                dbt_count = connection.execute(  # noqa: S608 - table names derive from constants
                    f"SELECT count(*) FROM {table_name}"  # noqa: S608
                ).fetchone()[0]
                csv_count = connection.execute(
                    "SELECT count(*) FROM read_csv_auto(?, header = true)", [str(csv_path)]
                ).fetchone()[0]
                assert dbt_count == csv_count

            dbt_npv = connection.execute("SELECT sum(npv_eur) FROM mart_tco_scenarios").fetchone()[
                0
            ]
            csv_npv = connection.execute(
                "SELECT sum(npv_eur) FROM read_csv_auto(?, header = true)",
                [str(EXPORT_DIR / "tco_scenarios.csv")],
            ).fetchone()[0]
            assert dbt_npv == pytest.approx(csv_npv, rel=1e-6)
    finally:
        for parquet_path in created:
            parquet_path.unlink(missing_ok=True)
