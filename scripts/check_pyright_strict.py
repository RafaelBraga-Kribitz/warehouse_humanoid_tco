"""F-235 — strict-module and coverage-ratchet verification."""

from __future__ import annotations

import subprocess
import sys

from _governance_check import REPO_ROOT, gate

STRICT_MODULES = (
    "src/warehouse_humanoid_tco/__init__.py",
    "src/warehouse_humanoid_tco/data/__init__.py",
    "src/warehouse_humanoid_tco/evaluation/__init__.py",
    "src/warehouse_humanoid_tco/features/__init__.py",
    "src/warehouse_humanoid_tco/models/__init__.py",
    "src/warehouse_humanoid_tco/pipelines/__init__.py",
    "src/warehouse_humanoid_tco/utils/__init__.py",
    "src/warehouse_humanoid_tco/visualization/__init__.py",
)


def main() -> int:
    strict_paths = [REPO_ROOT / path for path in STRICT_MODULES]
    headers_ok = all(
        path.exists() and path.read_text(encoding="utf-8").startswith("# pyright: strict")
        for path in strict_paths
    )
    pyright = subprocess.run(
        [sys.executable, "-m", "pyright", *map(str, strict_paths)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    ok = headers_ok and pyright.returncode == 0
    return gate(
        "check_pyright_strict.py",
        "F-235",
        ok=ok,
        ok_msg=f"{len(STRICT_MODULES)} strict modules pass Pyright",
        gap_msg=pyright.stdout.strip() or pyright.stderr.strip() or "strict module check failed",
    )


if __name__ == "__main__":
    sys.exit(main())
