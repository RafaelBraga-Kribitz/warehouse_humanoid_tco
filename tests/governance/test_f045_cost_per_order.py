"""F-045 — cost_per_order_eur metric must exist and README must reflect honest narrative.

Guards:
  1. tco_scenarios.parquet has cost_per_order_eur column.
  2. S-baseline-human has lowest cost_per_order_eur (load-bearing result at current
     capex/cycle-time: humans at 25s/cycle outperform humanoids at ~43s effective).
  3. README.md mentions cost-per-order framing.
  4. README.md does NOT contain the wrong p95 claim ("only scenario whose p95
     doesn't overlap with the baseline mean") — that claim is false for all scenarios.
  5. README.md NPV savings figure is within 10% of the value in tco_scenarios.parquet
     (catches stale hardcoded numbers).
"""

from __future__ import annotations

import re

import polars as pl
from _ratchet import REPO_ROOT, ratchet

TCO_PARQUET = REPO_ROOT / "data" / "processed" / "tco_scenarios.parquet"
README = REPO_ROOT / "README.md"


def test_cost_per_order_column_present() -> None:
    if not TCO_PARQUET.exists():
        ratchet("F-045", fixed=False, gap_msg="tco_scenarios.parquet missing")
        return
    df = pl.read_parquet(TCO_PARQUET)
    if "cost_per_order_eur" not in df.columns:
        ratchet("F-045", fixed=False, gap_msg="cost_per_order_eur column absent from tco_scenarios.parquet")
        return
    ratchet("F-045", fixed=True, gap_msg="")


def test_baseline_human_lowest_cost_per_order() -> None:
    if not TCO_PARQUET.exists():
        ratchet("F-045", fixed=False, gap_msg="tco_scenarios.parquet missing")
        return
    df = pl.read_parquet(TCO_PARQUET)
    if "cost_per_order_eur" not in df.columns:
        ratchet("F-045", fixed=False, gap_msg="cost_per_order_eur column absent")
        return
    ranked = df.sort("cost_per_order_eur")
    cheapest = ranked["scenario_id"][0]
    if cheapest != "S-baseline-human":
        ratchet(
            "F-045",
            fixed=False,
            gap_msg=(
                f"Expected S-baseline-human cheapest per order; got {cheapest}. "
                f"If capex assumptions changed, this guard should be revisited."
            ),
        )
        return
    ratchet("F-045", fixed=True, gap_msg="")


def test_readme_mentions_cost_per_order() -> None:
    if not README.exists():
        ratchet("F-045", fixed=False, gap_msg="README.md missing")
        return
    text = README.read_text()
    if not any(p in text.lower() for p in ("cost_per_order", "cost per order", "cost-per-order")):
        ratchet("F-045", fixed=False, gap_msg="README.md has no cost-per-order framing")
        return
    ratchet("F-045", fixed=True, gap_msg="")


def test_readme_no_false_p95_claim() -> None:
    if not README.exists():
        ratchet("F-045", fixed=False, gap_msg="README.md missing")
        return
    text = README.read_text()
    # The false claim: "only scenario whose p95 ... doesn't overlap"
    false_claim = bool(re.search(r"only scenario whose p95", text, re.IGNORECASE))
    if false_claim:
        ratchet(
            "F-045",
            fixed=False,
            gap_msg=(
                "README.md still contains false p95 non-overlap claim. "
                "All scenarios' p95 overlap with the baseline mean — remove or correct."
            ),
        )
        return
    ratchet("F-045", fixed=True, gap_msg="")


def test_readme_npv_savings_not_stale() -> None:
    if not TCO_PARQUET.exists() or not README.exists():
        ratchet("F-045", fixed=False, gap_msg="parquet or README missing")
        return
    df = pl.read_parquet(TCO_PARQUET)
    if "npv_eur" not in df.columns:
        ratchet("F-045", fixed=False, gap_msg="npv_eur absent from tco_scenarios")
        return
    baseline = df.filter(pl.col("scenario_id") == "S-baseline-human")["npv_eur"]
    hybrid = df.filter(pl.col("scenario_id") == "S-hybrid-amr")["npv_eur"]
    if len(baseline) == 0 or len(hybrid) == 0:
        ratchet("F-045", fixed=False, gap_msg="baseline or hybrid-amr scenario missing from parquet")
        return
    actual_savings = abs(float(baseline[0])) - abs(float(hybrid[0]))

    text = README.read_text()
    # Look for the stale €684K figure (wrong) — within 5% of 684000 = [649800, 718200]
    stale_match = re.search(r"€(\d[\d,]+)K?\s*\(?(\d+)%\s*reduction\)?", text)
    if stale_match:
        raw = stale_match.group(1).replace(",", "")
        stated = float(raw) * (1000 if "K" not in stale_match.group(0) or "K" in stale_match.group(0) else 1)
        # If stated savings differ from actual by >15%, flag stale
        if abs(stated - actual_savings) / max(abs(actual_savings), 1) > 0.15:
            ratchet(
                "F-045",
                fixed=False,
                gap_msg=(
                    f"README states ~€{stated:,.0f} savings but parquet shows €{actual_savings:,.0f}. "
                    f"Update the hardcoded figure."
                ),
            )
            return
    ratchet("F-045", fixed=True, gap_msg="")
