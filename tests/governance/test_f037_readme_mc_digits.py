"""F-037 — README MC 90% interval digits must match sensitivity_analysis_report.json."""

from __future__ import annotations

import json

from _ratchet import REPO_ROOT, ratchet

README = REPO_ROOT / "README.md"
REPORT = REPO_ROOT / "reports" / "sensitivity_analysis_report.json"


def _fmt(value: float) -> str:
    return f"{abs(int(round(value))):,}"


def test_readme_digits_match_report() -> None:
    if not README.exists() or not REPORT.exists():
        ratchet("F-037", fixed=True, gap_msg="README or report absent — vacuously fixed")
        return
    text = README.read_text()
    data = json.loads(REPORT.read_text())
    mc = data.get("mc_summary", {})
    p5, p95 = mc.get("npv_p5"), mc.get("npv_p95")
    if p5 is None or p95 is None:
        ratchet("F-037", fixed=True, gap_msg="mc_summary missing — vacuously fixed")
        return
    has_p5 = _fmt(p5) in text
    has_p95 = _fmt(p95) in text
    ratchet(
        "F-037",
        fixed=has_p5 and has_p95,
        gap_msg=f"README missing p5={_fmt(p5)} or p95={_fmt(p95)}",
    )
