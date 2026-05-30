"""F-023 — no source-of-truth file may name the wrong KV for warehouse wages.

Warehouse pickers fall under WKÖ Kollektivvertrag Spedition & Lagereibetriebe,
not Kollektivvertrag Handel. The repo previously mixed both names across QMD,
config, source comments, and the raw MANIFEST.

This test scans every canonical source file and bans the substrings
"Kollektivvertrag Handel" / "KV Handel". Generated HTML renders and the
finding YAMLs themselves (which legitimately quote the wrong term as evidence)
are excluded.
"""

from __future__ import annotations

from pathlib import Path

from _ratchet import REPO_ROOT, ratchet

SCAN_GLOBS = (
    "reports/*.qmd",
    "config/*.yaml",
    "data/raw/MANIFEST.yaml",
    "README.md",
    "PROJECT_CHARTER.md",
    "CONTRIBUTING.md",
    "CLAUDE.md",
    "docs/*.md",
    "src/**/*.py",
)
BANNED = ("Kollektivvertrag Handel", "KV Handel")


def _paths() -> list[Path]:
    out: list[Path] = []
    for pattern in SCAN_GLOBS:
        out.extend(REPO_ROOT.glob(pattern))
    return out


def test_no_wrong_kv() -> None:
    hits: list[str] = []
    for path in _paths():
        if not path.is_file():
            continue
        try:
            text = path.read_text()
        except OSError:
            continue
        for term in BANNED:
            if term in text:
                hits.append(f"{path.relative_to(REPO_ROOT)}:{term}")
                break
    ratchet(
        "F-023",
        fixed=not hits,
        gap_msg=f"wrong KV cited: {hits}",
    )
