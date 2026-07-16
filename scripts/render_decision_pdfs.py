"""EMERGENCY FALLBACK ONLY — do not use for committed recruiter PDFs.

Canonical renders are Quarto typst via ``make exec-summary`` (F-238).
This ReportLab path exists solely when Quarto cannot run on a machine and a
local preview is needed. Never commit its output as
``reports/Executive_Summary_*.pdf`` or ``reports/exhibit_deck.pdf``.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parents[1]


def sections(path: Path) -> list[tuple[str, str]]:
    """Extract level-two QMD headings and their text, ignoring front matter/chunks."""
    output: list[tuple[str, str]] = []
    title = ""
    body: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            if title:
                output.append((title, " ".join(body)))
            title, body = line[3:], []
        elif not line.startswith(("```", "---")) and line.strip():
            body.append(line.replace("|", " · "))
    if title:
        output.append((title, " ".join(body)))
    return output


def render_memo(source: Path, output: Path) -> None:
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(output), pagesize=A4, rightMargin=1.8 * cm, leftMargin=1.8 * cm)
    story = [Paragraph(source.stem.replace("_", " "), styles["Title"]), Spacer(1, 12)]
    for heading, body in sections(source):
        story.extend([Paragraph(heading, styles["Heading2"]), Paragraph(body, styles["BodyText"]), Spacer(1, 10)])
    doc.build(story)


def render_deck(source: Path, output: Path) -> None:
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(
        str(output),
        pagesize=landscape(A4),
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
    )
    story: list = []
    for heading, body in sections(source):
        story.extend(
            [
                Paragraph(heading, styles["Heading1"]),
                Spacer(1, 12),
                Paragraph(body, styles["BodyText"]),
                PageBreak(),
            ]
        )
    if story:
        story.pop()  # drop trailing page break
    doc.build(story)


def main() -> None:
    reports = ROOT / "reports"
    print(
        "WARNING: emergency ReportLab fallback — committed PDFs must come from "
        "`make exec-summary` (Quarto typst)."
    )
    render_memo(reports / "Executive_Summary_DE.qmd", reports / "Executive_Summary_DE.pdf")
    render_memo(reports / "Executive_Summary_EN.qmd", reports / "Executive_Summary_EN.pdf")
    render_deck(reports / "exhibit_deck.qmd", reports / "exhibit_deck.pdf")
    print(f"Wrote emergency PDFs under {reports}")


if __name__ == "__main__":
    main()
