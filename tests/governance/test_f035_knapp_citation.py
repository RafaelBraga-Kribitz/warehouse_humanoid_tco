"""F-035 — KNAPP_AUTOSTORE_THROUGHPUT_REFERENCE must carry a verifiable citation."""

from __future__ import annotations

import re

from _ratchet import REPO_ROOT, ratchet

VALIDATION = REPO_ROOT / "src" / "warehouse_humanoid_tco" / "evaluation" / "validation.py"
CONSTANT = "KNAPP_AUTOSTORE_THROUGHPUT_REFERENCE"


def test_citation_present() -> None:
    if not VALIDATION.exists():
        ratchet("F-035", fixed=True, gap_msg="validation.py absent — vacuously fixed")
        return
    text = VALIDATION.read_text()
    if CONSTANT not in text:
        ratchet("F-035", fixed=True, gap_msg="constant removed")
        return
    idx = text.index(CONSTANT)
    window = text[max(0, idx - 800) : idx + 800]
    has_url = bool(re.search(r"https?://", window))
    has_adr = bool(re.search(r"ADR-\d{4}", window))
    ratchet(
        "F-035",
        fixed=has_url or has_adr,
        gap_msg=f"{CONSTANT} lacks URL or ADR-#### citation in surrounding 800 chars",
    )
