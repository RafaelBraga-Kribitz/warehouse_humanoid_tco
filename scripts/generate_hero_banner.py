"""Redraw the data-driven parts of docs/assets/hero-banner-v2.png (F-244).

The banner's photo and headline are the user-supplied design and are never touched. The two
data regions are repainted from ``reports/module_03_tco_report.json``:

* the KPI strip (cheapest option, best humanoid case, discount rate, horizon)
* the seven-row cost ranking table (scenario names, total cost, capex, cost per order)

Repainting is idempotent: each region is first wiped with the banner's flat background.

    python scripts/generate_hero_banner.py          # redraw the PNG in place
    python scripts/generate_hero_banner.py --spec   # print the text spec as JSON
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import matplotlib
import yaml
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BANNER = ROOT / "docs" / "assets" / "hero-banner-v2.png"
REPORT = ROOT / "reports" / "module_03_tco_report.json"
CONFIG = ROOT / "config" / "autostore_baseline.yaml"
TCO_CONFIG = ROOT / "config" / "tco_assumptions.yaml"
LOCK = ROOT / "docs" / "assets" / "hero-banner-v2.lock.json"

KPI_BG = (227, 227, 227)
TABLE_BG = (223, 223, 222)
INK = (0, 0, 0)
MUTED = (86, 87, 88)
ORANGE = (250, 100, 0)
SEPARATOR = (74, 74, 74)
KPI_BOX = (860, 40, 1774, 143)
TABLE_BOX = (800, 628, 1774, 782)
KPI_CENTERS = (935, 1185, 1430, 1660)
BAR_X0, BAR_X1 = 1135, 1467
ROW_Y0, ROW_PITCH, BAR_H = 640, 21, 15
SEPARATOR_XS = (1575, 1675)


def build_spec(report: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return every string the banner shows, derived from the committed TCO report."""
    report = report or json.loads(REPORT.read_text(encoding="utf-8"))
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    tco = yaml.safe_load(TCO_CONFIG.read_text(encoding="utf-8"))
    has_humanoids = {
        s["id"] for s in config["scenarios"] if s.get("agent_counts", {}).get("humanoid", 0) > 0
    }
    results = sorted(report["scenario_results"], key=lambda r: -float(r["npv_eur"]))
    cheapest = results[0]
    best_humanoid = next(r for r in results if r["scenario_id"] in has_humanoids)
    top_cost = max(-float(r["npv_eur"]) for r in results)
    rows = []
    for rank, row in enumerate(results, start=1):
        cost = -float(row["npv_eur"])
        capex = float(row["total_capex_eur"])
        rows.append(
            {
                "rank": f"{rank:02d}",
                "label": str(row["scenario_id"]).upper(),
                "total": f"{cost / 1e6:.2f} M€",
                "capex": "€0" if capex == 0 else f"€{capex / 1000:.0f}K",
                "per_order": f"€{float(row['cost_per_order_eur']):.2f}",
                "bar_fraction": round(cost / top_cost, 4),
            }
        )
    return {
        "kpis": [
            {
                "label": "Cheapest option",
                "subtitle": f"({cheapest['scenario_id']})",
                "value": f"€{-float(cheapest['npv_eur']) / 1e6:.3f}M",
            },
            {
                "label": "Best humanoid case",
                "subtitle": f"({best_humanoid['scenario_id']})",
                "value": f"€{-float(best_humanoid['npv_eur']) / 1e6:.3f}M",
            },
            {"label": "Discount rate", "subtitle": "", "value": f"{report['discount_rate']:.0%}"},
            {
                "label": "Horizon",
                "subtitle": "",
                "value": f"{int(tco['financial']['horizon_years'])} yr",
            },
        ],
        "rows": rows,
    }


def _font(name: str, size: int, fallback: str) -> ImageFont.FreeTypeFont:
    inter = Path("/usr/share/fonts/opentype/inter") / name
    path = inter if inter.exists() else Path(matplotlib.get_data_path()) / "fonts/ttf" / fallback
    return ImageFont.truetype(str(path), size)


def render(spec: dict[str, Any], src: Path = BANNER, out: Path = BANNER) -> None:
    image = Image.open(src).convert("RGB")
    draw = ImageDraw.Draw(image)
    draw.rectangle(KPI_BOX, fill=KPI_BG)
    draw.rectangle(TABLE_BOX, fill=TABLE_BG)

    label_font = _font("Inter-Bold.otf", 16, "DejaVuSans-Bold.ttf")
    value_font = _font("Inter-ExtraBold.otf", 23, "DejaVuSans-Bold.ttf")
    for centre, kpi in zip(KPI_CENTERS, spec["kpis"], strict=True):
        two_lines = bool(kpi["subtitle"])
        draw.text(
            (centre, 61 if two_lines else 72), kpi["label"], fill=INK, font=label_font, anchor="mm"
        )
        if two_lines:
            draw.text((centre, 84), kpi["subtitle"], fill=INK, font=label_font, anchor="mm")
        draw.text(
            (centre, 123 if two_lines else 108),
            kpi["value"],
            fill=ORANGE,
            font=value_font,
            anchor="mm",
        )

    mono = ImageFont.truetype(
        str(Path(matplotlib.get_data_path()) / "fonts/ttf/DejaVuSansMono-Bold.ttf"), 14
    )
    for x in SEPARATOR_XS:
        draw.line((x, 630, x, 777), fill=SEPARATOR, width=1)
    for i, row in enumerate(spec["rows"]):
        cy = ROW_Y0 + ROW_PITCH * i + 1
        draw.text((824, cy), row["rank"], fill=MUTED, font=mono, anchor="lm")
        draw.text((1115, cy), row["label"], fill=INK, font=mono, anchor="rm")
        width = max(int((BAR_X1 - BAR_X0) * row["bar_fraction"]), 6)
        draw.rounded_rectangle(
            (BAR_X0, cy - BAR_H // 2, BAR_X0 + width, cy + BAR_H // 2), radius=2, fill=ORANGE
        )
        draw.text((1557, cy), row["total"], fill=INK, font=mono, anchor="rm")
        draw.text((1627, cy), row["capex"], fill=INK, font=mono, anchor="mm")
        draw.text((1722, cy), row["per_order"], fill=INK, font=mono, anchor="mm")
    image.save(out, optimize=True)


if __name__ == "__main__":
    spec_ = build_spec()
    if "--spec" in sys.argv:
        print(json.dumps(spec_, indent=2, ensure_ascii=False))
    else:
        render(spec_)
        digest = hashlib.sha256(BANNER.read_bytes()).hexdigest()
        LOCK.write_text(
            json.dumps({"png_sha256": digest, "spec": spec_}, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"redrew {BANNER} and wrote {LOCK.name}")
