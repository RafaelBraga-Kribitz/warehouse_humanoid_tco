"""F-022 — exec summary QMD must not cite the stale €9,25–€27,75 wage band."""

from __future__ import annotations

from _ratchet import REPO_ROOT, ratchet

QMD = REPO_ROOT / "reports" / "Executive_Summary_DE.qmd"
STALE_TOKENS = ("€9,25", "€27,75")


def test_no_stale_wage_band() -> None:
    if not QMD.exists():
        ratchet("F-022", fixed=True, gap_msg="QMD absent — vacuously fixed")
        return
    text = QMD.read_text()
    hits = [t for t in STALE_TOKENS if t in text]
    ratchet(
        "F-022",
        fixed=not hits,
        gap_msg=f"stale wage band tokens in QMD: {hits}",
    )
