"""TCO financial model — pure, assumption-explicit primitives.

All assumptions must be passed explicitly — no internal defaults.
See PROJECT_CHARTER.md §4 Module 3 and config/tco_assumptions.yaml.

Which primitives the pipeline actually uses:
  - `compute_npv` is the single canonical NPV implementation, called by BOTH
    `pipelines.module_03_tco.compute_tco_scenario` and
    `analysis.sensitivity.compute_tco_for_params`.
  - `compute_annual_labor_cost`, `compute_humanoid_capex`,
    `compute_annual_humanoid_opex` are used by the pipeline.
  - `compute_irr` and `compute_payback_years` are general-purpose cash-flow
    helpers retained as a tested public API. The TCO pipeline does NOT use them:
    it is a pure-cost model (all cash flows negative), so IRR is undefined and a
    cumulative-cashflow payback never turns positive. The pipeline instead
    reports a SIMPLE payback = capex / annual_opex_savings_vs_baseline. These
    two helpers are not "richer modeling" claims about the headline results.
"""

from __future__ import annotations

import numpy as np
import numpy_financial as npf


def compute_annual_labor_cost(
    n_humans: int,
    hourly_wage_eur: float,
    overhead_multiplier: float,
    operating_days: int = 252,
    shift_hours: float = 8.0,
) -> float:
    hours_per_year = operating_days * shift_hours
    return n_humans * hourly_wage_eur * overhead_multiplier * hours_per_year


def compute_humanoid_capex(
    n_humanoids: int,
    unit_capex_eur: float,
    installation_cost_per_unit_eur: float,
    training_cost_per_unit_eur: float,
) -> float:
    total_cost_per_unit = (
        unit_capex_eur + installation_cost_per_unit_eur + training_cost_per_unit_eur
    )
    return n_humanoids * total_cost_per_unit


def compute_annual_humanoid_opex(
    n_humanoids: int,
    unit_capex_eur: float,
    annual_maintenance_fraction: float,
    energy_kwh_per_shift: float,
    energy_cost_eur_per_kwh: float,
    operating_days: int = 252,
) -> float:
    maintenance = n_humanoids * unit_capex_eur * annual_maintenance_fraction
    energy = n_humanoids * energy_kwh_per_shift * energy_cost_eur_per_kwh * operating_days
    return maintenance + energy


def compute_npv(
    cash_flows: list[float],
    discount_rate: float,
) -> float:
    """NPV of cash_flows[0..N] where index 0 is year 0 (capex outflow)."""
    return float(npf.npv(discount_rate, cash_flows))


def compute_irr(cash_flows: list[float]) -> float | None:
    try:
        irr = npf.irr(cash_flows)
        return float(irr) if np.isfinite(irr) else None
    except Exception:
        return None


def compute_payback_years(cash_flows: list[float]) -> float | None:
    """Simple payback: first year cumulative cash flow turns positive.

    Note: Uses undiscounted sum of cash flows. For discounted payback, use NPV-based calculation.
    """
    cumulative = 0.0
    for year, cf in enumerate(cash_flows):
        cumulative += cf
        if cumulative >= 0:
            return float(year)
    return None
