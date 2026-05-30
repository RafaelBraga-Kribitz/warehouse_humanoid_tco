"""F-021 — exec summary QMD throughput claim must match simulation report JSON.

QMD line 60 currently asserts "alle Szenarien zeigen statistisch identische
Durchsätze (~959 Bestellungen/Schicht)". The simulation report carries scenario-
level throughput_mean values; the rounded mean across scenarios must match the
"~NNN" claim in the QMD within 50 orders.
"""

from __future__ import annotations

import json
import re

from _ratchet import REPO_ROOT, ratchet

QMD = REPO_ROOT / "reports" / "Executive_Summary_DE.qmd"
REPORT = REPO_ROOT / "reports" / "module_02_simulation_report.json"


def test_throughput_claim_matches_report() -> None:
    if not QMD.exists() or not REPORT.exists():
        ratchet("F-021", fixed=True, gap_msg="QMD or report absent — vacuously fixed")
        return
    text = QMD.read_text()
    m = re.search(r"~(\d{3,4})\s*Bestellungen/Schicht", text)
    if not m:
        ratchet("F-021", fixed=True, gap_msg="no throughput claim in QMD — vacuously fixed")
        return
    claimed = int(m.group(1))
    data = json.loads(REPORT.read_text())
    rows = data.get("replication_summary", [])
    if not rows:
        ratchet("F-021", fixed=False, gap_msg="no replication_summary in simulation report")
        return
    means = [r.get("throughput_mean", 0) for r in rows]
    avg = sum(means) / len(means)
    delta = abs(claimed - avg)
    ratchet(
        "F-021",
        fixed=delta <= 50,
        gap_msg=f"QMD claims ~{claimed}/shift; report mean {avg:.0f} (Δ={delta:.0f})",
    )
