"""F-226 — fail when the committed assumption register is stale."""

from __future__ import annotations

import difflib
import subprocess
import sys
import tempfile
from pathlib import Path

from _governance_check import REPO_ROOT, gate

REGISTER = REPO_ROOT / "governance" / "ASSUMPTION_REGISTER.md"
GENERATOR = REPO_ROOT / "scripts" / "generate_assumption_register.py"


def main() -> int:
    with tempfile.TemporaryDirectory() as directory:
        generated = Path(directory) / "ASSUMPTION_REGISTER.md"
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--output", str(generated)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        committed = REGISTER.read_text(encoding="utf-8") if REGISTER.exists() else ""
        rendered = generated.read_text(encoding="utf-8") if generated.exists() else ""
        diff = "".join(
            difflib.unified_diff(
                committed.splitlines(keepends=True),
                rendered.splitlines(keepends=True),
                fromfile=str(REGISTER),
                tofile="generated",
            )
        )
        return gate(
            "check_assumption_register.py",
            "F-226",
            ok=result.returncode == 0 and not diff,
            ok_msg="committed assumption register is reproducible",
            gap_msg=(result.stderr.strip() or diff[:2000] or "generator produced no output"),
        )


if __name__ == "__main__":
    raise SystemExit(main())
