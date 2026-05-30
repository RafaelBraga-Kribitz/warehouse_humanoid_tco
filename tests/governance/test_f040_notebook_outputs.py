"""F-040 — 01_data_profile_summary.ipynb must have committed cell outputs."""

from __future__ import annotations

import json

from _ratchet import REPO_ROOT, ratchet

NOTEBOOK = REPO_ROOT / "notebooks" / "01_data_profile_summary.ipynb"


def test_notebook_has_outputs() -> None:
    if not NOTEBOOK.exists():
        ratchet("F-040", fixed=True, gap_msg="notebook absent — vacuously fixed")
        return
    data = json.loads(NOTEBOOK.read_text())
    n_outputs = sum(
        1 for c in data.get("cells", []) if c.get("cell_type") == "code" and c.get("outputs")
    )
    ratchet(
        "F-040",
        fixed=n_outputs > 0,
        gap_msg="notebook has 0 code cells with outputs",
    )
