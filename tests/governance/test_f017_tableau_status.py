"""F-017 — the README Tableau claim must be verifiable.

"publication pending" with no link or date is unverifiable. Closure (Phase 5)
either publishes and links the workbook or removes the claim. Until then this is
a tracked, open gap.
"""

from __future__ import annotations

import re

from _ratchet import REPO_ROOT, ratchet

README = REPO_ROOT / "README.md"
_PENDING = re.compile(r"publication pending", re.IGNORECASE)
_TABLEAU_LINK = re.compile(r"https?://public\.tableau\.com/\S+", re.IGNORECASE)


def test_tableau_claim_is_verifiable() -> None:
    text = README.read_text()
    has_pending = bool(_PENDING.search(text))
    has_link = bool(_TABLEAU_LINK.search(text))
    # Fixed = no vague "pending" claim, or a concrete published link is present.
    ratchet(
        "F-017",
        fixed=(not has_pending) or has_link,
        gap_msg="README claims 'publication pending' with no Tableau Public link",
    )
