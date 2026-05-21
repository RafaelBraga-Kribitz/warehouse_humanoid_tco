"""Export processed data for Tableau Public and Power BI consumption.

Writes CSV and parquet exports to reports/ directory.
Both BI tools consume the same data layer — no logic divergence.
See ADR-0004 for dual-publish rationale.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl


def export_for_tableau(df: pl.DataFrame, output_dir: Path, filename: str) -> Path:
    """Write DataFrame to CSV for Tableau Public.

    Tableau Public requires all published data to be publicly visible.
    Never embed secrets or PII.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / filename
    df.write_csv(out_path)
    return out_path


def export_for_powerbi(df: pl.DataFrame, output_dir: Path, filename: str) -> Path:
    """Write DataFrame to parquet for Power BI Desktop consumption."""
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / filename
    df.write_parquet(out_path)
    return out_path
