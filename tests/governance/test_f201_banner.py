"""F-201 — verification (ratchet while open)."""

from __future__ import annotations

from _ratchet import ratchet


def test_f_201_pending() -> None:
    ratchet("F-201", fixed=False, gap_msg="F-201 not yet remediated")
