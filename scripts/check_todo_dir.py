"""F-012 — docs/todo/ must be absent or empty (open work lives in finding YAMLs).

Forward gate against the audit-doc accumulation pattern: free-form audit journals
under docs/todo/ are banned; all open work belongs in governance/findings/.
"""

from __future__ import annotations

import sys

from _governance_check import REPO_ROOT, gate

TODO_DIR = REPO_ROOT / "docs" / "todo"


def main() -> int:
    contents: list[str] = []
    if TODO_DIR.exists():
        contents = [str(p.relative_to(REPO_ROOT)) for p in TODO_DIR.rglob("*") if p.is_file()]
    ok = not contents
    return gate(
        "check_todo_dir.py",
        "F-012",
        ok=ok,
        ok_msg="docs/todo/ absent or empty",
        gap_msg=f"docs/todo/ contains {len(contents)} file(s): {', '.join(contents[:5])}",
    )


if __name__ == "__main__":
    sys.exit(main())
