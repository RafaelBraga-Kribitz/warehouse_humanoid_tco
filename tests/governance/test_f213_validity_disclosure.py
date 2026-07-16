"""F-213 — external-validity disclosure remains explicit."""

from __future__ import annotations

from pathlib import Path

from _ratchet import ratchet

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_f_213_validity_disclosure() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    limitations = (REPO_ROOT / "governance" / "LIMITATIONS.md").read_text(encoding="utf-8")
    section_start = readme.find("#### External validity — what the source data is and is not")
    section_end = readme.find("### Simulation", section_start)
    section = (
        readme[section_start:section_end]
        if section_start >= 0 and section_end > section_start
        else ""
    )
    required_terms = (
        "plates-into-dishwasher",
        "pillow",
        "clothes-into-washing-machine",
        "dual-arm",
        "single-arm",
        "No source episode is a warehouse task",
        "pick-move-place primitives",
        "0.50–0.90 transfer factor",
        "domain-transfer risk",
        "Warehouse-native task telemetry",
    )
    fixed = all(term in section for term in required_terms) and all(
        term in limitations
        for term in (
            "household demonstrations",
            "Domain-transfer risk",
            "0.50–0.90",
            "Warehouse-native task telemetry",
        )
    )
    ratchet(
        "F-213",
        fixed=fixed,
        gap_msg="README and limitations must disclose the household-to-warehouse transfer risk",
    )
