"""F-234 — package quickstart verification."""

from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

from _ratchet import ratchet


def test_f_234_packaging_surface_is_self_contained() -> None:
    root = Path(__file__).resolve().parents[2]
    quickstart = root / "examples" / "quickstart.py"
    try:
        version = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"][
            "version"
        ]
        run = subprocess.run(
            [sys.executable, str(quickstart)],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        fixed = (
            version == "1.0.0"
            and (root / "examples" / "synthetic_config.yaml").exists()
            and (root / "MAINTENANCE.md").exists()
            and len(quickstart.read_text(encoding="utf-8").splitlines()) <= 40
            and run.returncode == 0
        )
    except (FileNotFoundError, KeyError, tomllib.TOMLDecodeError, subprocess.TimeoutExpired):
        fixed = False
    ratchet(
        "F-234", fixed=fixed, gap_msg="quickstart, version, or maintenance policy is incomplete"
    )
