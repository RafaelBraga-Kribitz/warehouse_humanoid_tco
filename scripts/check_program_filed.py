"""F-200 — Quality Transformation Program findings filed."""

from __future__ import annotations

import sys

import yaml
from _governance_check import REPO_ROOT, gate

REQUIRED = [
    "F-201",
    "F-202",
    "F-203",
    "F-204",
    "F-205",
    "F-206",
    "F-207",
    "F-210",
    "F-211",
    "F-212",
    "F-213",
    "F-214",
    "F-215",
    "F-216",
    "F-217",
    "F-218",
    "F-219",
    "F-220",
    "F-221",
    "F-222",
    "F-223",
    "F-224",
    "F-225",
    "F-226",
    "F-227",
    "F-228",
    "F-229",
    "F-230",
    "F-231",
    "F-232",
    "F-233",
    "F-234",
    "F-235",
    "F-236",
]
FINDINGS = REPO_ROOT / "governance" / "findings"
BLUEPRINT = REPO_ROOT / "governance" / "QUALITY_BLUEPRINT.md"


def main() -> int:
    problems: list[str] = []
    if not BLUEPRINT.exists() or BLUEPRINT.stat().st_size < 200:
        problems.append("QUALITY_BLUEPRINT.md missing or too short")
    for fid in REQUIRED:
        path = FINDINGS / f"{fid}.yaml"
        if not path.exists():
            problems.append(f"{fid}.yaml missing")
            continue
        data = yaml.safe_load(path.read_text()) or {}
        if not (data.get("evidence") or "").strip():
            problems.append(f"{fid}: empty evidence")
        if not data.get("verification_script"):
            problems.append(f"{fid}: empty verification_script")
    return gate(
        "check_program_filed.py",
        "F-200",
        ok=not problems,
        ok_msg=f"{len(REQUIRED)} program findings + blueprint present",
        gap_msg="; ".join(problems),
    )


if __name__ == "__main__":
    sys.exit(main())
