"""F-244 — README images show current business scenario names and current numbers.

F-242 renamed the scenarios in every text file, but two README visuals are raster images
whose text is baked into pixels, so the text-only guard could not see them: the hero banner
and the terminal demo GIF. Both are now rebuilt by scripts from the committed reports and
pinned by lock files. This test fails when the reports, the scenario names, or the images
drift apart, and when the README embeds an image that no guard covers.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
from pathlib import Path
from types import ModuleType

from warehouse_humanoid_tco.data.enums import ScenarioId

REPO_ROOT = Path(__file__).resolve().parents[2]
ASSETS = REPO_ROOT / "docs" / "assets"
REPORT = json.loads((REPO_ROOT / "reports" / "module_03_tco_report.json").read_text())
ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
NAMES = {member.value for member in ScenarioId}
# Images the README may embed besides charts (manifest-guarded) and the two locked visuals.
UNGUARDED_OK = {"docs/assets/Author_MDS_Rafael_Braga-Kribitz_kroped.png"}


def _load(script: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(script, REPO_ROOT / "scripts" / f"{script}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cast_text() -> str:
    lines = (ASSETS / "demo.cast").read_text(encoding="utf-8").splitlines()[1:]
    return ANSI.sub(
        "", "".join(json.loads(line)[2] for line in lines if json.loads(line)[1] == "o")
    )


def test_hero_banner_text_matches_current_report() -> None:
    lock = json.loads((ASSETS / "hero-banner-v2.lock.json").read_text())
    fresh = _load("generate_hero_banner").build_spec(REPORT)
    assert lock["spec"] == fresh, (
        "hero banner is stale versus reports/module_03_tco_report.json; "
        "run: python scripts/generate_hero_banner.py"
    )


def test_hero_banner_png_is_the_generated_one() -> None:
    lock = json.loads((ASSETS / "hero-banner-v2.lock.json").read_text())
    assert _sha(ASSETS / "hero-banner-v2.png") == lock["png_sha256"], (
        "hero-banner-v2.png was changed without the generator; "
        "run: python scripts/generate_hero_banner.py"
    )


def test_hero_banner_uses_only_current_scenario_names() -> None:
    spec = json.loads((ASSETS / "hero-banner-v2.lock.json").read_text())["spec"]
    shown = {row["label"] for row in spec["rows"]}
    assert shown == {name.upper() for name in NAMES}
    for kpi in spec["kpis"][:2]:
        assert kpi["subtitle"].strip("()") in NAMES
    cheapest = max(REPORT["scenario_results"], key=lambda r: r["npv_eur"])["scenario_id"]
    assert spec["kpis"][0]["subtitle"] == f"({cheapest})"
    assert spec["rows"][0]["label"] == cheapest.upper()


def test_demo_cast_shows_current_ranking_and_headline() -> None:
    text = _cast_text()
    results = {r["scenario_id"]: round(r["npv_eur"]) for r in REPORT["scenario_results"]}
    shown: dict[str, int] = {}
    for line in text.splitlines():
        match = re.match(r"^(\S.*?\S)\s+(-[\d,]+)\s*$", line)
        if match and match.group(1) in NAMES:
            shown[match.group(1)] = int(match.group(2).replace(",", ""))
    assert shown == results, "demo.cast ranking table is stale; re-record docs/assets/demo_run.sh"
    cheapest = max(results, key=lambda name: results[name])
    assert f"{cheapest} is the cheapest of {len(results)} scenarios" in text

    sensitivity = json.loads(
        (REPO_ROOT / "reports" / "sensitivity_analysis_report.json").read_text()
    )
    mean = round(sensitivity["mc_summary"]["npv_mean"])
    assert f"npv_mean {mean:>14,} EUR".replace(" ", "") in text.replace(" ", "")


def test_demo_gif_is_rendered_from_the_committed_cast() -> None:
    lock = json.loads((ASSETS / "demo.lock.json").read_text())
    assert (
        _sha(ASSETS / "demo.cast") == lock["cast_sha256"]
    ), "demo.cast changed; run: python scripts/render_demo_gif.py"
    assert (
        _sha(ASSETS / "demo.gif") == lock["gif_sha256"]
    ), "demo.gif changed without the renderer; run: python scripts/render_demo_gif.py"


def test_every_readme_image_is_guarded() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    embedded = set(re.findall(r"\]\(\./([^)\s]+\.(?:png|gif|jpg|svg))\)", readme))
    embedded |= set(re.findall(r'src="([^"]+\.(?:png|gif|jpg|svg))"', readme))
    manifest = json.loads(
        (REPO_ROOT / "reports" / "executive_charts" / "chart_data_manifest.json").read_text()
    )
    guarded = {f"reports/executive_charts/{key}.png" for key in manifest["charts"]}
    guarded |= {"docs/assets/hero-banner-v2.png", "docs/assets/demo.gif"} | UNGUARDED_OK
    # The tornado's only scenario text is the sensitivity report's scenario_id (asserted below).
    guarded.add("reports/executive_charts/04_sensitivity_tornado.png")
    assert embedded, "README embeds no images?"
    assert embedded <= guarded, f"README images with no scenario-name guard: {embedded - guarded}"
    for image in embedded:
        assert (REPO_ROOT / image).exists(), image


def test_tornado_subtitle_comes_from_the_sensitivity_report() -> None:
    source = (REPO_ROOT / "scripts" / "generate_tornado_chart.py").read_text(encoding="utf-8")
    assert "report['scenario_id']" in source or 'report["scenario_id"]' in source
    for name in NAMES:
        assert name not in source, f"hard-coded scenario name in tornado script: {name}"
    sensitivity = json.loads(
        (REPO_ROOT / "reports" / "sensitivity_analysis_report.json").read_text()
    )
    assert sensitivity["scenario_id"] in NAMES
