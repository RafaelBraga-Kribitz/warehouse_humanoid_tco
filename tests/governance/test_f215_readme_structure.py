"""F-215 — README decision-first structure."""

from __future__ import annotations

from _ratchet import REPO_ROOT, ratchet

README = REPO_ROOT / "README.md"


def test_f215_readme_structure() -> None:
    text = README.read_text(encoding="utf-8")
    lines = text.splitlines()
    decision_idx = next((i for i, ln in enumerate(lines) if ln.strip() == "## Decision summary"), None)
    fixed = (
        len(lines) <= 200
        and decision_idx is not None
        and decision_idx < 30
        and "Data Analytics / Business Intelligence portfolio project" not in text
        and "## How this was built" in text
        and "Recruiter (2 min)" in text
        and "Hiring manager (10 min)" in text
        and "Auditor" in text
        and "When do humanoid robots beat human labor" in text
    )
    if "tableau-dashboard.png" in text:
        fixed = fixed and (REPO_ROOT / "docs" / "assets" / "tableau-dashboard.png").exists()
    ratchet("F-215", fixed=fixed, gap_msg="README structure does not meet F-215 acceptance")
