"""F-242 — scenarios carry business-readable names everywhere; the old codes stay retired.

The seven scenarios were once identified by developer codes (``S-lean-human``,
``S-hybrid-amr`` ...). Business readers could not decode them, so the readable name
is now the identifier itself: config, enum, JSON, CSV, charts, prose, and PDFs.

This module is the regression guard:

* ``ScenarioId`` is the single source of truth and must match the config, in order.
* Names must look like business English (no ``S-`` prefix, no kebab/snake case).
* No tracked text file (or rendered PDF, when ``pdftotext`` exists) may contain a
  retired code. The only allowlisted files are those that document the rename.
* Published artifacts only use names from ``ScenarioId``.
* Code must never infer scenario meaning from name fragments (the hidden coupling that
  silently dropped ``breakeven_thresholds`` during the rename).
"""

from __future__ import annotations

import csv
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from warehouse_humanoid_tco.data.enums import ScenarioId
from warehouse_humanoid_tco.pipelines.module_03_tco import _LEGACY_FRACTIONS

REPO_ROOT = Path(__file__).resolve().parents[2]

# Retired code -> current business name. Kept here (allowlisted) as the rename record.
RETIRED_TO_CURRENT = {
    "S-baseline-human": ScenarioId.LEGACY_OVERSTAFFED_TEAM,
    "S-lean-human": ScenarioId.LEAN_HUMAN_TEAM,
    "S-lean-hybrid-amr": ScenarioId.LEAN_HUMAN_AMR_TEAM,
    "S-pure-humanoid": ScenarioId.ALL_HUMANOID_TEAM,
    "S-hybrid-5050": ScenarioId.HALF_HUMAN_HALF_HUMANOID_TEAM,
    "S-hybrid-amr": ScenarioId.HUMAN_HUMANOID_AMR_TEAM,
    "S-future-2028": ScenarioId.FUTURE_2028_HUMANOID_TEAM,
}
RETIRED_CODE_RE = re.compile(r"\bS-(?:baseline|lean|pure|hybrid|future)-[A-Za-z0-9-]+")
ALLOWLIST = frozenset(
    {
        "tests/governance/test_f242_business_scenario_names.py",
        "governance/findings/F-242.yaml",
        "CHANGELOG.md",
    }
)
SKIP_PREFIXES = ("data/raw/", "uv.lock", ".git/")
NAMES = [member.value for member in ScenarioId]


def _tracked_files() -> list[str]:
    try:
        out = subprocess.run(  # noqa: S603
            [shutil.which("git") or "git", "ls-files"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("git metadata unavailable")
    return [f for f in out.splitlines() if f and not f.startswith(SKIP_PREFIXES)]


def test_every_retired_code_maps_to_exactly_one_current_name() -> None:
    assert len(RETIRED_TO_CURRENT) == len(set(RETIRED_TO_CURRENT.values())) == len(ScenarioId)
    assert set(RETIRED_TO_CURRENT.values()) == set(ScenarioId)


def test_config_scenarios_match_enum_in_order() -> None:
    config = yaml.safe_load((REPO_ROOT / "config" / "autostore_baseline.yaml").read_text())
    assert [s["id"] for s in config["scenarios"]] == NAMES


def test_names_are_business_readable() -> None:
    for name in NAMES:
        assert not name.startswith("S-"), name
        assert name[0].isupper(), name
        assert " " in name or "-" in name, name
        assert "_" not in name, name
        assert name == name.strip() and "  " not in name, name
        assert not re.search(r"\b[a-z]+-[a-z]+-[a-z0-9]+\b", name), f"kebab-case code: {name}"
        assert name.endswith("Team"), f"names end with 'Team' for consistency: {name}"
        assert len(name) <= 40, f"name too long for chart labels: {name}"
    assert len(set(NAMES)) == len(NAMES)


def test_no_retired_scenario_code_in_tracked_text() -> None:
    offenders: dict[str, list[str]] = {}
    for rel in _tracked_files():
        if rel in ALLOWLIST:
            continue
        try:
            text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        hits = sorted(set(RETIRED_CODE_RE.findall(text)))
        if hits:
            offenders[rel] = hits
    assert not offenders, f"Retired scenario codes reappeared: {offenders}"


@pytest.mark.skipif(shutil.which("pdftotext") is None, reason="pdftotext not installed")
def test_no_retired_scenario_code_in_rendered_pdfs() -> None:
    for pdf in sorted((REPO_ROOT / "reports").glob("*.pdf")):
        text = subprocess.run(  # noqa: S603
            [shutil.which("pdftotext") or "pdftotext", str(pdf), "-"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        assert not RETIRED_CODE_RE.search(text), f"{pdf.name} still shows a retired code"


def test_published_artifacts_use_business_names() -> None:
    allowed = set(NAMES)
    with (REPO_ROOT / "exports" / "tableau_public" / "tco_scenarios.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        assert {row["scenario_id"] for row in csv.DictReader(handle)} == allowed
    for csv_name in ("simulation_runs.csv", "simulation_capacity_ceiling.csv"):
        with (REPO_ROOT / "exports" / "tableau_public" / csv_name).open(
            encoding="utf-8", newline=""
        ) as handle:
            assert {row["scenario_id"] for row in csv.DictReader(handle)} == allowed

    tco = json.loads((REPO_ROOT / "reports" / "module_03_tco_report.json").read_text())
    assert {r["scenario_id"] for r in tco["scenario_results"]} == allowed
    assert "breakeven_thresholds" in tco  # lost once when name matching silently failed

    sens = json.loads((REPO_ROOT / "reports" / "sensitivity_analysis_report.json").read_text())
    assert not RETIRED_CODE_RE.search(json.dumps(sens))


def test_legacy_fraction_table_covers_every_scenario() -> None:
    assert set(_LEGACY_FRACTIONS) == set(ScenarioId)


def test_code_never_infers_scenario_meaning_from_name_fragments() -> None:
    """``"hybrid-amr" in scenario_id`` style checks break silently when names change."""
    pattern = re.compile(
        r"""["'][^"']+["']\s+in\s+(?:\w+\[["']scenario_id["']\]|\w*scenario_id)\b"""
    )
    offenders: list[str] = []
    for rel in _tracked_files():
        if not rel.endswith(".py") or not rel.startswith(("src/", "scripts/")):
            continue
        for number, line in enumerate((REPO_ROOT / rel).read_text().splitlines(), start=1):
            if pattern.search(line):
                offenders.append(f"{rel}:{number}: {line.strip()}")
    assert not offenders, "Match scenarios by ScenarioId equality, not substring:\n" + "\n".join(
        offenders
    )
