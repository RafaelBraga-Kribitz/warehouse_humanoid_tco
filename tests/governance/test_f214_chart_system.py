"""F-214 — chart design system and data-manifest verification.

The locked palette is the Braga design system v2.1 (bk-viz, DECISIONS.md D-053): chart code
names colour *roles* and resolves them through ``bk_theme``; no generator carries a colour
literal of its own.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import bk_theme as bk
from _ratchet import ratchet

from warehouse_humanoid_tco.visualization import chart_style

ROOT = Path(__file__).resolve().parents[2]
GENERATORS = (
    ROOT / "src" / "warehouse_humanoid_tco" / "visualization" / "chart_style.py",
    ROOT / "src" / "warehouse_humanoid_tco" / "pipelines" / "module_04_dashboards.py",
    ROOT / "src" / "warehouse_humanoid_tco" / "analysis" / "crew_optimizer.py",
    ROOT / "scripts" / "generate_tornado_chart.py",
    ROOT / "scripts" / "generate_f225_frontiers.py",
)
HEX_LITERAL = re.compile(r"""["']#[0-9A-Fa-f]{3,8}["']""")
NAMED_COLOUR = re.compile(r"""color\s*=\s*["'](black|white|gr[ae]y|red|green|blue)["']""")


def test_f_214_chart_design_system_and_manifest() -> None:
    bk.apply("light")
    roles_ok = (
        chart_style.RECOMMENDED,
        chart_style.BASELINE,
        chart_style.OTHER,
        chart_style.ADVERSE,
    ) == ("hl", "sc-py", "ink-2", "var-neg") and all(
        chart_style.color(role) == bk.c(role)
        for role in (
            chart_style.RECOMMENDED,
            chart_style.BASELINE,
            chart_style.OTHER,
            chart_style.ADVERSE,
        )
    )
    sources = {path: path.read_text(encoding="utf-8") for path in GENERATORS}
    no_literals = all(
        not HEX_LITERAL.search(text) and not NAMED_COLOUR.search(text) for text in sources.values()
    )
    themed = all("chart_style" in text or "bk_theme" in text for text in sources.values())
    try:
        manifest = json.loads(
            (ROOT / "reports" / "executive_charts" / "chart_data_manifest.json").read_text(
                encoding="utf-8"
            )
        )
        manifest_ok = (
            manifest["hash_algorithm"] == "sha256"
            and {
                "01_tco_npv_ranking",
                "02_cost_breakdown",
                "03_simulation_throughput",
                "05_cost_per_order",
            }
            <= manifest["charts"].keys()
            and all(len(digest) == 64 for digest in manifest["charts"].values())
        )
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        manifest_ok = False
    ratchet(
        "F-214",
        fixed=roles_ok and no_literals and themed and manifest_ok,
        gap_msg=(
            f"chart design-system contract broken: roles_ok={roles_ok} "
            f"no_literals={no_literals} themed={themed} manifest_ok={manifest_ok}"
        ),
    )
