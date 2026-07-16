"""F-238 — Quarto typst recruiter PDFs replace ReportLab dumps."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIN_PDF_BYTES = 30_000
PDFS = (
    "Executive_Summary_DE.pdf",
    "Executive_Summary_EN.pdf",
    "exhibit_deck.pdf",
)


def test_f238_qmd_declares_typst_and_makefile_uses_it() -> None:
    for name in ("Executive_Summary_DE.qmd", "Executive_Summary_EN.qmd", "exhibit_deck.qmd"):
        text = (ROOT / "reports" / name).read_text(encoding="utf-8")
        assert "typst:" in text, f"{name} must declare format.typst"

    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "exec-summary:" in makefile
    for qmd in (
        "Executive_Summary_DE.qmd",
        "Executive_Summary_EN.qmd",
        "exhibit_deck.qmd",
    ):
        assert f"quarto render reports/{qmd} --to typst" in makefile

    script = (ROOT / "scripts" / "render_decision_pdfs.py").read_text(encoding="utf-8")
    assert "emergency" in script.lower()
    assert "EMERGENCY FALLBACK" in script or "emergency fallback" in script.lower()


def test_f238_committed_pdfs_are_quarto_quality() -> None:
    for name in PDFS:
        path = ROOT / "reports" / name
        data = path.read_bytes()
        assert data.startswith(b"%PDF"), f"{name} is not a PDF"
        assert path.stat().st_size >= MIN_PDF_BYTES, f"{name} too small ({path.stat().st_size})"
        assert b"ReportLab Generated PDF" not in data, f"{name} is still ReportLab"

    deck = (ROOT / "reports" / "exhibit_deck.pdf").read_bytes()
    assert b"/Subtype /Image" in deck or b"/Subtype/Image" in deck, (
        "exhibit_deck.pdf must embed at least one chart image"
    )
