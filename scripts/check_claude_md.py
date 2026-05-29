"""F-015 — CLAUDE.md agent protocol contract.

When CLAUDE.md exists (created in Phase 3) it must reference `make session-start`
and must not contain the unverifiable navigation claims the meta-audit flagged
(`graphify-out` substring or a literal "(hook)" graph-rebuild claim). Until the
file exists, F-015 is an open gap (measured, not enforced).
"""

from __future__ import annotations

import sys

from _governance_check import REPO_ROOT, gate

CLAUDE_MD = REPO_ROOT / "CLAUDE.md"
BANNED = ("graphify-out", "(hook)")
REQUIRED = "make session-start"


def main() -> int:
    if not CLAUDE_MD.exists():
        return gate(
            "check_claude_md.py",
            "F-015",
            ok=False,
            ok_msg="",
            gap_msg="CLAUDE.md absent (created in Phase 3)",
        )
    text = CLAUDE_MD.read_text()
    banned_hits = [b for b in BANNED if b in text]
    has_required = REQUIRED in text
    ok = not banned_hits and has_required
    return gate(
        "check_claude_md.py",
        "F-015",
        ok=ok,
        ok_msg=f"references '{REQUIRED}'; no banned navigation claims",
        gap_msg=f"banned={banned_hits}; references_session_start={has_required}",
    )


if __name__ == "__main__":
    sys.exit(main())
