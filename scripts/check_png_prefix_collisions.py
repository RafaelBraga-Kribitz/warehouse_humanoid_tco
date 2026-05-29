"""F-005 — no two executive-chart PNGs may share a numeric prefix.

reports/executive_charts/ uses an NN_*.png ordering convention. Two files with
the same NN prefix (e.g. a regenerated chart landing beside a stale one) make the
report ambiguous. Forward gate; currently 01..04 are unique.
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict

from _governance_check import REPO_ROOT, gate

CHARTS = REPO_ROOT / "reports" / "executive_charts"
_PREFIX = re.compile(r"^(\d+)_")


def main() -> int:
    by_prefix: dict[str, list[str]] = defaultdict(list)
    count = 0
    if CHARTS.exists():
        for png in sorted(CHARTS.glob("*.png")):
            count += 1
            m = _PREFIX.match(png.name)
            if m:
                by_prefix[m.group(1)].append(png.name)
    collisions = {k: v for k, v in by_prefix.items() if len(v) > 1}
    return gate(
        "check_png_prefix_collisions.py",
        "F-005",
        ok=not collisions,
        ok_msg=f"{count} PNG(s), all numeric prefixes unique",
        gap_msg=f"prefix collisions: {collisions}",
    )


if __name__ == "__main__":
    sys.exit(main())
