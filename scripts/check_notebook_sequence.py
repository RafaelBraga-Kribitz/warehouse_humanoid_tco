"""F-016 — notebook numeric prefixes must form a gap-free, collision-free sequence.

Notebooks use an NN_ ordering convention. Two notebooks may not share a prefix,
and the present prefixes must be contiguous from the lowest (no missing 02 when
03 exists). A single notebook trivially satisfies this; the gate activates as the
notebook set grows.
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict

from _governance_check import REPO_ROOT, gate

NOTEBOOKS = REPO_ROOT / "notebooks"
_PREFIX = re.compile(r"^(\d+)_")


def main() -> int:
    by_prefix: dict[int, list[str]] = defaultdict(list)
    for nb in sorted(NOTEBOOKS.glob("*.ipynb")):
        m = _PREFIX.match(nb.name)
        if m:
            by_prefix[int(m.group(1))].append(nb.name)
    prefixes = sorted(by_prefix)
    problems: list[str] = []
    for p, names in by_prefix.items():
        if len(names) > 1:
            problems.append(f"prefix {p:02d} collision: {names}")
    if prefixes:
        expected = list(range(prefixes[0], prefixes[-1] + 1))
        missing = [f"{n:02d}" for n in expected if n not in by_prefix]
        if missing:
            problems.append(f"missing prefixes: {', '.join(missing)}")
    return gate(
        "check_notebook_sequence.py",
        "F-016",
        ok=not problems,
        ok_msg=f"notebooks {[f'{p:02d}' for p in prefixes]} form a clean sequence",
        gap_msg="; ".join(problems),
    )


if __name__ == "__main__":
    sys.exit(main())
