"""F-227 — bilingual decision memos and challenge FAQ remain complete."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIN_PDF_BYTES = 30_000


def test_f_227_memos_and_faq_exist() -> None:
    de = (ROOT / "reports" / "Executive_Summary_DE.qmd").read_text()
    en = (ROOT / "reports" / "Executive_Summary_EN.qmd").read_text()
    assert "## Empfehlung" in de
    assert "## Recommendation" in en
    assert "S-lean-human" in de and "S-lean-human" in en
    assert "S-lean-hybrid-amr" in de and "S-lean-hybrid-amr" in en

    for filename in ("Executive_Summary_DE.pdf", "Executive_Summary_EN.pdf"):
        path = ROOT / "reports" / filename
        data = path.read_bytes()
        assert path.exists() and path.stat().st_size >= MIN_PDF_BYTES
        assert data.startswith(b"%PDF")
        assert b"ReportLab Generated PDF" not in data

    faq = (ROOT / "docs" / "challenge_this_analysis.md").read_text()
    assert faq.count("\n## Q") >= 8
    assert faq.count("](") >= 8

    lineage = (ROOT / "docs" / "data_lineage.md").read_text()
    assert lineage.count("```mermaid") >= 2
