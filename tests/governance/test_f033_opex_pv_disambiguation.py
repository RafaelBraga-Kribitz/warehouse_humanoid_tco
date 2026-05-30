"""F-033 — module_03_tco.py must disambiguate nominal vs PV opex from NPV."""

from __future__ import annotations

from _ratchet import REPO_ROOT, ratchet

MODULE = REPO_ROOT / "src" / "warehouse_humanoid_tco" / "pipelines" / "module_03_tco.py"
SAFE_TOKENS = ("total_opex_5yr_eur_nominal", "total_opex_5yr_eur_pv", "opex_5yr_pv_eur")
NAIVE_TOKEN = '"total_opex_5yr_eur"'  # noqa: S105 — JSON field name, not a credential


def test_opex_disambiguated() -> None:
    if not MODULE.exists():
        ratchet("F-033", fixed=True, gap_msg="module_03_tco.py absent — vacuously fixed")
        return
    text = MODULE.read_text()
    is_safe = any(tok in text for tok in SAFE_TOKENS)
    is_naive = NAIVE_TOKEN in text
    ratchet(
        "F-033",
        fixed=is_safe or not is_naive,
        gap_msg='module_03_tco.py emits ambiguous "total_opex_5yr_eur" next to NPV',
    )
