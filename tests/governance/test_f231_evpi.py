"""F-231 — EVPI report verification."""
from __future__ import annotations

import json
from pathlib import Path

from _ratchet import ratchet


def test_f_231_evpi_is_present_and_nonnegative() -> None:
    report_path = Path(__file__).resolve().parents[2] / "reports" / "sensitivity_analysis_report.json"
    try:
        evpi = json.loads(report_path.read_text(encoding="utf-8"))["evpi_eur"]
        fixed = bool(evpi) and all(float(value) >= 0.0 for value in evpi.values())
    except (FileNotFoundError, KeyError, json.JSONDecodeError, TypeError, ValueError):
        fixed = False
    ratchet("F-231", fixed=fixed, gap_msg="evpi_eur is missing or contains a negative value")
