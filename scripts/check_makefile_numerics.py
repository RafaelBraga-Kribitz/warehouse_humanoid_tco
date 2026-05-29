"""F-014 — Makefile help text run-count must match module_02 n_runs default.

Forward gate: the "(N runs)" literal in `make help` and the `n_runs` default in
module_02_simulation.py drift independently across ADR-driven config bumps. This
asserts they agree until Phase 5 makes the help text read the value dynamically.
"""

from __future__ import annotations

import re
import sys

from _governance_check import REPO_ROOT, gate

MAKEFILE = REPO_ROOT / "Makefile"
MODULE_02 = REPO_ROOT / "src" / "warehouse_humanoid_tco" / "pipelines" / "module_02_simulation.py"

_MAKE_RUNS = re.compile(r"\((\d+)\s+runs\)")
_N_RUNS = re.compile(r"n_runs:\s*int\s*=\s*(\d+)")


def main() -> int:
    make_match = _MAKE_RUNS.search(MAKEFILE.read_text())
    code_match = _N_RUNS.search(MODULE_02.read_text())
    make_runs = int(make_match.group(1)) if make_match else None
    code_runs = int(code_match.group(1)) if code_match else None
    ok = make_runs is not None and make_runs == code_runs
    return gate(
        "check_makefile_numerics.py",
        "F-014",
        ok=ok,
        ok_msg=f"make help '{make_runs} runs' == n_runs default {code_runs}",
        gap_msg=f"make help runs={make_runs} vs n_runs default={code_runs}",
    )


if __name__ == "__main__":
    sys.exit(main())
