"""F-006 — CONTRIBUTING.md "pyright strict" claim must match pyproject.toml.

If CONTRIBUTING.md claims pyright runs in strict mode, then
pyproject.toml [tool.pyright] typeCheckingMode must equal "strict".
"""

from __future__ import annotations

import re
import sys
import tomllib

from _governance_check import REPO_ROOT, gate

PYPROJECT = REPO_ROOT / "pyproject.toml"
CONTRIBUTING = REPO_ROOT / "CONTRIBUTING.md"

_STRICT_CLAIM = re.compile(r"pyright\s+strict", re.IGNORECASE)


def main() -> int:
    pp = tomllib.loads(PYPROJECT.read_text())
    mode = pp.get("tool", {}).get("pyright", {}).get("typeCheckingMode")
    claims_strict = bool(_STRICT_CLAIM.search(CONTRIBUTING.read_text()))
    ok = (not claims_strict) or (mode == "strict")
    return gate(
        "check_contributing_claims.py",
        "F-006",
        ok=ok,
        ok_msg=f"pyright mode='{mode}', claim consistent",
        gap_msg=f"CONTRIBUTING claims 'pyright strict' but typeCheckingMode='{mode}'",
    )


if __name__ == "__main__":
    sys.exit(main())
