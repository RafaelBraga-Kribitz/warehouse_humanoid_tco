"""Language navigation and UK spelling preserve the decision evidence contract."""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))


def load_check(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("alter_recommendation, expected", [(False, 0), (True, 1)])
def test_trilingual_decision_statement_keeps_the_evidence_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, alter_recommendation: bool, expected: int
) -> None:
    for path in ["PROJECT_CHARTER.md", "README.md", "reports/module_03_tco_report.json"]:
        destination = tmp_path / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, destination)
    if alter_recommendation:
        readme = tmp_path / "README.md"
        readme.write_text(
            readme.read_text().replace(
                "deploy Lean Human + AMR Team now", "defer Lean Human + AMR Team now"
            )
        )
    check = load_check("check_decision_statement")
    monkeypatch.setattr(check, "REPO_ROOT", tmp_path)
    assert check.main() == expected


def test_navigation_does_not_hide_narrative_lines() -> None:
    from scripts._governance_check import readme_contract_text

    nav = "[PT-BR](README.pt-BR.md) · [EN-UK](README.md) · [DE-AT](README.de-AT.md)"
    body = "\n".join(["A substantive narrative line."] * 201)
    assert len(readme_contract_text(nav + "\n\n" + body).splitlines()) == 201
    prose = nav + " Important caveat: labour is modelled, not measured."
    assert readme_contract_text(prose).startswith(nav + " Important caveat:")


def test_markdown_allowlist_is_limited_to_supported_readme_locales() -> None:
    import re

    import yaml

    workflow = yaml.safe_load((ROOT / ".github/workflows/docs-ssot-check.yml").read_text())
    script = workflow["jobs"]["markdown-allowlist"]["steps"][1]["run"]
    pattern = re.search(r"allowed_pattern='([^']+)'", script).group(1)
    for path in ["./README.md", "./README.pt-BR.md", "./README.de-AT.md"]:
        assert re.fullmatch(pattern, path)
    assert not re.fullmatch(pattern, "./README.fr.md")
    assert not re.fullmatch(pattern, "./UNREGISTERED.md")
