"""F-043 — presentation-layer artifacts (charts, QMDs) regenerate via make target.

This contract requires a `make presentation` target that:
  1. Exists in the Makefile
  2. Runs module-04 + QMD rendering (when quarto available)
  3. Is explicitly called in CI or make all (so stale artifacts don't accumulate)

The test verifies the target exists and is documented.
"""

from __future__ import annotations

import re

from _ratchet import REPO_ROOT, ratchet

MAKEFILE = REPO_ROOT / "Makefile"


def test_presentation_target_exists() -> None:
    """Verify `make presentation` target is defined in Makefile."""
    content = MAKEFILE.read_text()

    # Check that the target is declared (line starts with 'presentation:')
    target_match = re.search(r"^presentation:", content, re.MULTILINE)
    fixed = target_match is not None

    ratchet(
        "F-043",
        fixed,
        "`make presentation` target not found in Makefile",
    )


def test_presentation_target_documented() -> None:
    """Verify `make presentation` appears in the help target's @echo lines."""
    content = MAKEFILE.read_text()

    # Match an @echo line that mentions `make presentation` — the convention
    # used by every other documented target in this Makefile.
    help_match = re.search(
        r"@echo\s+.*make presentation",
        content,
    )
    fixed = help_match is not None

    ratchet(
        "F-043",
        fixed,
        "`make presentation` target not documented in `make help` output",
    )
