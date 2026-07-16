"""F-218 — verify every manifest dataset has a recognized license memo row."""

from __future__ import annotations

import re
import sys

import yaml
from _governance_check import REPO_ROOT, gate

RECOGNIZED_LICENSES = {"Apache-2.0", "MIT", "BSD-3-Clause", "CC-BY-4.0", "CC-BY-SA-4.0"}


def manifest_dataset_ids() -> set[str]:
    manifest = yaml.safe_load(
        (REPO_ROOT / "config" / "dataset_manifest.yaml").read_text(encoding="utf-8")
    )
    return {
        dataset["repo_id"]
        for group in ("wbt_datasets", "diversemanip_datasets")
        for dataset in manifest[group]
    }


def memo_rows(text: str) -> dict[str, str]:
    rows: dict[str, str] = {}
    for line in text.splitlines():
        cells = [cell.strip() for cell in line.split("|")]
        if len(cells) >= 3 and cells[1].startswith("`unitreerobotics/"):
            rows[cells[1].strip("`")] = cells[2]
    return rows


def main() -> int:
    memo_path = REPO_ROOT / "governance" / "LICENSE_COMPLIANCE.md"
    memo = memo_path.read_text(encoding="utf-8") if memo_path.exists() else ""
    rows = memo_rows(memo)
    expected_ids = manifest_dataset_ids()
    ok = (
        expected_ids == set(rows)
        and all(license_name in RECOGNIZED_LICENSES for license_name in rows.values())
        and not re.search(r"\bUNKNOWN\b", memo, flags=re.IGNORECASE)
    )
    return gate(
        "check_license_memo.py",
        "F-218",
        ok=ok,
        ok_msg="every manifest dataset has a recognized license memo row",
        gap_msg="license memo is incomplete, has an unrecognized license, or says UNKNOWN",
    )


if __name__ == "__main__":
    sys.exit(main())
