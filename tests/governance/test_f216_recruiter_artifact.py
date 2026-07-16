"""F-216 — recruiter-facing rendered PDF verification."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIN_PDF_BYTES = 30_000


def test_f_216_recruiter_pdf_is_linked() -> None:
    pdf = ROOT / "reports" / "Executive_Summary_DE.pdf"
    data = pdf.read_bytes()
    assert data.startswith(b"%PDF")
    assert pdf.stat().st_size >= MIN_PDF_BYTES
    assert b"ReportLab Generated PDF" not in data
    assert "(./reports/Executive_Summary_DE.pdf)" in (ROOT / "README.md").read_text(
        encoding="utf-8"
    )
