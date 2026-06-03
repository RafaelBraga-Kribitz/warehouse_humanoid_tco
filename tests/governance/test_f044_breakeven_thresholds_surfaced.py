"""F-044 — cost-per-order break-even thresholds must be surfaced in a committed artifact.

Closure is satisfied by either:

  A. data/processed/tco_scenarios.parquet gains a `cost_per_order_eur` column
     AND reports/module_03_tco_report.json carries a `breakeven_thresholds`
     section with numeric values for at least `capex_eur_per_unit` and
     `effective_cycle_seconds` for the pure-humanoid scenario.

  B. The "breakeven sensitivity" phrase is removed from
     reports/module_03_tco_assumptions.qmd (narrative no longer claims it),
     in which case there is nothing for the artifact to back up.

Either path makes narrative and artifacts agree. The ratchet xfails while
the finding is open and fails on regression once closed.
"""

from __future__ import annotations

import json

from _ratchet import REPO_ROOT, ratchet

PARQUET = REPO_ROOT / "data" / "processed" / "tco_scenarios.parquet"
REPORT_JSON = REPO_ROOT / "reports" / "module_03_tco_report.json"
ASSUMPTIONS_QMD = REPO_ROOT / "reports" / "module_03_tco_assumptions.qmd"

NARRATIVE_CLAIM = "breakeven sensitivity"
REQUIRED_THRESHOLD_KEYS = ("capex_eur_per_unit", "effective_cycle_seconds")


def _parquet_has_cost_per_order() -> bool:
    if not PARQUET.exists():
        return False
    try:
        import polars as pl
    except ImportError:
        return False
    df = pl.read_parquet(PARQUET)
    return "cost_per_order_eur" in df.columns


def _report_has_breakeven_section() -> bool:
    if not REPORT_JSON.exists():
        return False
    payload = json.loads(REPORT_JSON.read_text())
    section = payload.get("breakeven_thresholds")
    if not isinstance(section, dict):
        return False
    # Accept either flat keys or nested under a scenario id.
    flat_ok = all(
        isinstance(section.get(k), (int, float)) for k in REQUIRED_THRESHOLD_KEYS
    )
    if flat_ok:
        return True
    for value in section.values():
        if isinstance(value, dict) and all(
            isinstance(value.get(k), (int, float)) for k in REQUIRED_THRESHOLD_KEYS
        ):
            return True
    return False


def _narrative_still_claims_breakeven() -> bool:
    if not ASSUMPTIONS_QMD.exists():
        return False
    return NARRATIVE_CLAIM in ASSUMPTIONS_QMD.read_text().lower()


def test_breakeven_thresholds_surfaced_or_claim_removed() -> None:
    artifact_complete = _parquet_has_cost_per_order() and _report_has_breakeven_section()
    claim_present = _narrative_still_claims_breakeven()

    if artifact_complete:
        ratchet("F-044", fixed=True, gap_msg="artifact thresholds present")
        return
    if not claim_present:
        ratchet("F-044", fixed=True, gap_msg="narrative claim removed")
        return

    ratchet(
        "F-044",
        fixed=False,
        gap_msg=(
            "narrative claims 'breakeven sensitivity' but tco_scenarios.parquet "
            "lacks cost_per_order_eur and module_03_tco_report.json lacks a "
            "breakeven_thresholds section"
        ),
    )
