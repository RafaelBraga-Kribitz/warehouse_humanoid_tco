"""F-013 — pre-commit bootstrap must be wired and documented.

The `make bootstrap` target must run `pre-commit install`, and pre-commit must be
a declared dev dependency. Satisfied by Phase 0; guarded permanently here.
"""

from __future__ import annotations

import re

from _ratchet import REPO_ROOT

MAKEFILE = REPO_ROOT / "Makefile"
PYPROJECT = REPO_ROOT / "pyproject.toml"


def test_bootstrap_target_installs_precommit() -> None:
    makefile = MAKEFILE.read_text()
    assert re.search(r"^bootstrap:", makefile, re.MULTILINE), "Makefile needs a bootstrap target"
    assert "pre-commit install" in makefile, "bootstrap must run `pre-commit install`"


def test_precommit_is_dev_dependency() -> None:
    assert "pre-commit" in PYPROJECT.read_text(), "pre-commit must be a declared dependency"
