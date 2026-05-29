"""F-009 — the pre-commit ssot-check must cover every SSOT_REGISTRY canonical path.

The `.pre-commit-config.yaml` ssot-check hook has a `files:` regex that decides
which edits trigger the SSOT freshness check. Every `canonical` file path declared
in governance/SSOT_REGISTRY.yaml must match that regex; otherwise edits to a
canonical fact (CHARTER, config/, reports/) silently skip the check. Phase 4
widens the regex.
"""

from __future__ import annotations

import re
import sys

import yaml
from _governance_check import REPO_ROOT, gate

PRECOMMIT = REPO_ROOT / ".pre-commit-config.yaml"
REGISTRY = REPO_ROOT / "governance" / "SSOT_REGISTRY.yaml"


def _ssot_files_pattern() -> str | None:
    data = yaml.safe_load(PRECOMMIT.read_text()) or {}
    for repo in data.get("repos", []) or []:
        for hook in repo.get("hooks", []) or []:
            if hook.get("id") == "ssot-check":
                return hook.get("files")
    return None


def _canonical_paths() -> list[str]:
    """Canonical file/dir paths that a contributor could edit.

    Every canonical value in the registry is a repo path. We exclude `.git/`
    internals (not tracked, never staged) since a pre-commit `files:` regex
    cannot meaningfully cover them.
    """
    data = yaml.safe_load(REGISTRY.read_text()) or {}
    paths: list[str] = []
    for entry in (data.get("facts", {}) or {}).values():
        if not isinstance(entry, dict):
            continue
        canonical = entry.get("canonical")
        if isinstance(canonical, str) and not canonical.startswith(".git/"):
            paths.append(canonical)
    return sorted(set(paths))


def main() -> int:
    pattern = _ssot_files_pattern()
    if not pattern:
        return gate(
            "check_ssot_scope.py",
            "F-009",
            ok=False,
            ok_msg="",
            gap_msg="no ssot-check hook with a files: pattern found",
        )
    rx = re.compile(pattern)
    uncovered = [p for p in _canonical_paths() if not rx.match(p)]
    return gate(
        "check_ssot_scope.py",
        "F-009",
        ok=not uncovered,
        ok_msg="ssot-check files: covers every canonical path",
        gap_msg=f"{len(uncovered)} canonical path(s) not covered: {', '.join(uncovered)}",
    )


if __name__ == "__main__":
    sys.exit(main())
