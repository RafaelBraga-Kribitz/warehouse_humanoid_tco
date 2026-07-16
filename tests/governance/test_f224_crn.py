"""F-224 — common-random-number sensitivity verification."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from warehouse_humanoid_tco.analysis.sensitivity import run_sensitivity_analysis


def test_f_224_crn_rank_probabilities_and_diagnostics(tmp_path: Path) -> None:
    """Every scenario must receive an identical draw at each sample index."""
    (tmp_path / "data" / "processed").mkdir(parents=True)
    (tmp_path / "reports").mkdir(parents=True)

    paths = run_sensitivity_analysis(tmp_path, n_mc_samples=100)
    samples = pl.read_parquet(paths["mc_samples"])
    sampled_columns = [column for column in samples.columns if column.endswith("_sampled")]

    scenario_pair = samples.filter(
        pl.col("scenario_id").is_in(["S-baseline-human", "S-pure-humanoid"])
    )
    for column in sampled_columns:
        draws_by_sample = scenario_pair.group_by("sample_id").agg(
            pl.col(column).n_unique().alias("unique_draws")
        )
        assert draws_by_sample["unique_draws"].max() == 1, column

    report = json.loads(paths["report"].read_text())
    assert abs(sum(report["rank_probabilities"].values()) - 1.0) <= 1e-9
    assert set(report["convergence"]) == {"half1_mean", "half2_mean", "rel_delta"}
    assert "infeasible_sample_count" in report
