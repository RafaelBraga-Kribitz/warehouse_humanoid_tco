"""Export processed data for Tableau Public consumption.

Writes CSV exports to reports/ directory. See ADR-0004 (Tableau half) and
ADR-0008 (Power BI deprecation) for the dashboard-surface decision history.
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
