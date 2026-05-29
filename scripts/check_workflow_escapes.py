"""F-007 — CI workflows must not contain test escape hatches.

Scans .github/workflows/ for `|| echo` and `2>/dev/null` patterns that swallow
non-zero exit codes (e.g. pipeline.yml's `pytest ... 2>/dev/null || echo "No tests"`),
which silently turn real test failures into green builds.
"""

from __future__ import annotations

import re
import sys

from _governance_check import REPO_ROOT, gate

WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
_ESCAPES = re.compile(r"\|\|\s*echo|2>/dev/null")


def main() -> int:
    hits: list[str] = []
    for path in sorted(WORKFLOWS_DIR.glob("*.yml")):
        for i, line in enumerate(path.read_text().splitlines(), 1):
            if _ESCAPES.search(line):
                hits.append(f"{path.name}:{i}")
    return gate(
        "check_workflow_escapes.py",
        "F-007",
        ok=not hits,
        ok_msg="no '|| echo' / '2>/dev/null' escape hatches in workflows",
        gap_msg=f"escape hatch(es) at: {', '.join(hits)}",
    )


if __name__ == "__main__":
    sys.exit(main())
