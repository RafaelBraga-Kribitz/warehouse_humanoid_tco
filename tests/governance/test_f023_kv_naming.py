"""F-023 — no doc may cite "KV Handel" / "Kollektivvertrag Handel" for warehouse wages."""

from __future__ import annotations

from _ratchet import REPO_ROOT, ratchet

PATHS = (
    REPO_ROOT / "reports" / "Executive_Summary_DE.qmd",
    REPO_ROOT / "data" / "raw" / "MANIFEST.yaml",
)
PATTERNS = ("Kollektivvertrag Handel", "KV Handel")


def test_no_wrong_kv() -> None:
    hits: list[str] = []
    for path in PATHS:
        if not path.exists():
            continue
        text = path.read_text()
        for pat in PATTERNS:
            if pat in text:
                hits.append(f"{path.name}:{pat}")
    ratchet(
        "F-023",
        fixed=not hits,
        gap_msg=f"wrong KV cited: {hits}",
    )
