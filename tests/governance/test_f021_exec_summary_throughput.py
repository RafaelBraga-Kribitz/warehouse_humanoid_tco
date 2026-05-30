"""F-021 — exec summary QMD throughput claim must match pipeline output.

QMD line 60 asserts "alle Szenarien zeigen statistisch identische Durchsätze
(~NNN Bestellungen/Schicht)". The truth source is the per-scenario
`throughput_mean_orders_per_shift` column in exports/tableau_public/tco_scenarios.csv;
the mean across scenarios must match the "~NNN" claim within 50 orders.

The original test pointed at a `replication_summary` key that no longer exists
in the simulation report JSON; the CSV is the canonical aggregate today.
"""

from __future__ import annotations

import csv
import re

from _ratchet import REPO_ROOT, ratchet

QMD = REPO_ROOT / "reports" / "Executive_Summary_DE.qmd"
CSV_PATH = REPO_ROOT / "exports" / "tableau_public" / "tco_scenarios.csv"


def test_throughput_claim_matches_report() -> None:
    if not QMD.exists() or not CSV_PATH.exists():
        ratchet("F-021", fixed=True, gap_msg="QMD or CSV absent — vacuously fixed")
        return
    text = QMD.read_text()
    m = re.search(r"~(\d{3,4})\s*Bestellungen/Schicht", text)
    if not m:
        ratchet("F-021", fixed=True, gap_msg="no throughput claim in QMD — vacuously fixed")
        return
    claimed = int(m.group(1))
    means = [
        float(r["throughput_mean_orders_per_shift"])
        for r in csv.DictReader(CSV_PATH.open())
        if r.get("throughput_mean_orders_per_shift")
    ]
    if not means:
        ratchet("F-021", fixed=False, gap_msg="no throughput_mean column in CSV")
        return
    avg = sum(means) / len(means)
    delta = abs(claimed - avg)
    ratchet(
        "F-021",
        fixed=delta <= 50,
        gap_msg=f"QMD claims ~{claimed}/shift; CSV mean {avg:.0f} (Δ={delta:.0f})",
    )
