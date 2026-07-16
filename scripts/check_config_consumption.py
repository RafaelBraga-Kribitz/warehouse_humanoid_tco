"""F-205 — verify configuration leaves are consumed or declared unmodeled."""
from __future__ import annotations

import sys
from collections.abc import Iterable
from pathlib import Path

import yaml
from _governance_check import REPO_ROOT, gate


def _leaf_keys(value: object, prefix: str = "") -> set[str]:
    if isinstance(value, dict):
        keys: set[str] = set()
        for key, child in value.items():
            if key in {"unmodeled_parameters", "scenarios"}:
                continue
            child_prefix = f"{prefix}.{key}" if prefix else key
            keys.update(_leaf_keys(child, child_prefix))
        return keys
    if isinstance(value, list):
        return {prefix}
    return {prefix}


def _declared_unmodeled(value: object) -> set[str]:
    entries = value.get("unmodeled_parameters", []) if isinstance(value, dict) else []
    return {
        entry["key"]
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("key"), str)
    }


def _invalid_declarations(config_path: Path) -> set[str]:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    entries = config.get("unmodeled_parameters", []) if isinstance(config, dict) else []
    allowed_biases = {"favors_robots", "favors_humans", "neutral", "unknown"}
    invalid: set[str] = set()
    if not isinstance(entries, list):
        return {str(config_path)}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or set(entry) != {"key", "bias", "note", "planned"}:
            invalid.add(f"{config_path.name}[{index}]")
            continue
        if (
            not isinstance(entry["key"], str)
            or entry["bias"] not in allowed_biases
            or not isinstance(entry["note"], str)
            or entry["planned"] not in {"F-222", "none"}
        ):
            invalid.add(f"{config_path.name}[{index}]")
    return invalid


def uncovered_keys(configs: Iterable[Path], src_root: Path) -> set[str]:
    """Return config leaves absent from source strings and the declared triage."""
    source_text = "\n".join(path.read_text(encoding="utf-8") for path in src_root.rglob("*.py"))
    uncovered: set[str] = set()
    for config_path in configs:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        declared = _declared_unmodeled(config)
        for dotted_key in _leaf_keys(config):
            final_segment = dotted_key.rsplit(".", maxsplit=1)[-1]
            if final_segment not in source_text and dotted_key not in declared:
                uncovered.add(dotted_key)
    return uncovered


def main() -> int:
    configs = [
        REPO_ROOT / "config" / "tco_assumptions.yaml",
        REPO_ROOT / "config" / "autostore_baseline.yaml",
    ]
    missing = uncovered_keys(configs, REPO_ROOT / "src")
    invalid = set().union(*(_invalid_declarations(path) for path in configs))
    return gate(
        "check_config_consumption.py",
        "F-205",
        ok=not missing and not invalid,
        ok_msg="all config leaves are consumed or explicitly triaged",
        gap_msg=(
            f"uncovered config leaves: {', '.join(sorted(missing))}; "
            f"invalid declarations: {', '.join(sorted(invalid))}"
        ),
    )


if __name__ == "__main__":
    sys.exit(main())
