"""F-228 — exhibit deck source and Quarto typst PDF remain available."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MIN_PDF_BYTES = 30_000


def test_f_228_exhibit_deck_exists_and_is_pinned() -> None:
    source = (ROOT / "reports" / "exhibit_deck.qmd").read_text()
    assert source.count("\n## ") <= 12
    assert source.count("\n## ") >= 6
    assert "```{python}" in source
    assert "executive_charts/" in source

    pdf = ROOT / "reports" / "exhibit_deck.pdf"
    data = pdf.read_bytes()
    assert pdf.exists() and pdf.stat().st_size >= MIN_PDF_BYTES
    assert data.startswith(b"%PDF")
    assert b"ReportLab Generated PDF" not in data
    assert b"/Subtype /Image" in data or b"/Subtype/Image" in data

    readme = (ROOT / "README.md").read_text()
    assert "exhibit_deck.pdf" in readme
