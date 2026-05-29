"""F-005 — report freshness umbrella contract.

No report QMD may pin `date: today`, and executive-chart PNG prefixes must be
unique. Phase 5 introduces deterministic ISO render dates.
"""

from __future__ import annotations

import re
from collections import defaultdict

from _ratchet import REPO_ROOT, ratchet

REPORTS = REPO_ROOT / "reports"
CHARTS = REPORTS / "executive_charts"
_DATE_TODAY = re.compile(r"^\s*date:\s*today\s*$")
_PREFIX = re.compile(r"^(\d+)_")


def test_no_date_today_in_qmds() -> None:
    offenders = [
        qmd.name
        for qmd in sorted(REPORTS.glob("*.qmd"))
        if any(_DATE_TODAY.match(line) for line in qmd.read_text().splitlines())
    ]
    ratchet("F-005", fixed=not offenders, gap_msg=f"QMDs using 'date: today': {offenders}")


def test_png_prefixes_unique() -> None:
    by_prefix: dict[str, list[str]] = defaultdict(list)
    if CHARTS.exists():
        for png in CHARTS.glob("*.png"):
            m = _PREFIX.match(png.name)
            if m:
                by_prefix[m.group(1)].append(png.name)
    collisions = {k: v for k, v in by_prefix.items() if len(v) > 1}
    # Prefix uniqueness already holds today; this guards against regression.
    assert not collisions, f"PNG prefix collisions: {collisions}"
