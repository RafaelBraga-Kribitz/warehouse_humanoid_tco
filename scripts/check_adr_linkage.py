"""ADR-linkage advisory — governance changes should be accompanied by an ADR.

Phase 1 runs this in advisory mode: it reports when the working tree changes a
governance finding/registry file without touching an ADR, but never fails the
build. Phase 4 promotes it to an enforced PR gate (diff against the PR base).
"""

from __future__ import annotations

import subprocess
import sys

from _governance_check import REPO_ROOT

ADR_DIRS = ("governance/adrs/",)
GOVERNANCE_PREFIXES = ("governance/findings/", "governance/SSOT_REGISTRY.yaml")


def _changed_files() -> list[str]:
    try:
        out = subprocess.check_output(
            ["git", "diff", "--name-only", "HEAD"],  # noqa: S607
            cwd=REPO_ROOT,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    return [line for line in out.splitlines() if line.strip()]


def main() -> int:
    changed = _changed_files()
    gov_changed = [c for c in changed if c.startswith(GOVERNANCE_PREFIXES)]
    adr_changed = [c for c in changed if c.startswith(ADR_DIRS)]
    if gov_changed and not adr_changed:
        print(
            "[INFO] check_adr_linkage.py: governance files changed without an ADR "
            f"({len(gov_changed)} file(s)); enforced as a PR gate in Phase 4."
        )
    else:
        print("[PASS] check_adr_linkage.py: advisory — no unlinked governance change")
    return 0


if __name__ == "__main__":
    sys.exit(main())
