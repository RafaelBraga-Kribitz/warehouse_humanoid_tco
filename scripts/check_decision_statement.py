"""F-210 — verify the canonical decision statement and README summary."""

from __future__ import annotations

import json
import sys

from _governance_check import REPO_ROOT, gate

START = "<!-- DECISION_STATEMENT_START -->"
END = "<!-- DECISION_STATEMENT_END -->"
LABOR_SCARCITY = (
    "In Austrian intralogistics the practical automation driver is unfillable "
    "vacancies, not wage arbitrage; this model conservatively assumes labor is "
    "available at KV rates, so robot value is understated wherever vacancies go unfilled."
)


def main() -> int:
    charter = (REPO_ROOT / "PROJECT_CHARTER.md").read_text(encoding="utf-8")
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    report = json.loads(
        (REPO_ROOT / "reports" / "module_03_tco_report.json").read_text(encoding="utf-8")
    )
    vs_lean = report["breakeven_thresholds"]["vs_lean_human"]
    expected_capex = vs_lean["capex_eur_per_unit"]
    # F-237 follow-up: when no breakeven exists in the searched range the
    # statement must say so instead of quoting a search-bound artifact.
    if expected_capex is None:
        trigger_ok_fragment = "no pure-humanoid capex in the searched"
    else:
        trigger_ok_fragment = f"€{expected_capex:,.0f}"
    start = charter.find(START)
    end = charter.find(END)
    statement = charter[start + len(START) : end] if start >= 0 and end > start else ""
    recommendation = next(
        (line.strip() for line in statement.splitlines() if line.startswith("**Recommendation:**")),
        "",
    )
    first_25_lines = "\n".join(readme.splitlines()[:25])
    required_terms = (
        "COO/site director",
        "Austrian AutoStore-class warehouse",
        "deploy humanoids now",
        "lean-human+AMR now",
        "wait, with a humanoid procurement trigger",
        "2026–2028",
        "0.50–0.90 transfer factor",
    )
    ok = (
        bool(statement)
        and all(term in statement for term in required_terms)
        and trigger_ok_fragment in statement
        and LABOR_SCARCITY in statement
        and len(recommendation) >= 120
        and recommendation in first_25_lines
        and LABOR_SCARCITY in first_25_lines
    )
    return gate(
        "check_decision_statement.py",
        "F-210",
        ok=ok,
        ok_msg="canonical decision statement, trigger, and README summary are aligned",
        gap_msg="decision statement, labor-scarcity disclosure, or README quote is incomplete",
    )


if __name__ == "__main__":
    sys.exit(main())
