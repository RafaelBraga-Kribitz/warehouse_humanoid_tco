"""Print TCO scenarios in a readable format for the demo GIF (cheapest first)."""

import pyarrow.parquet as pq

t = pq.read_table("data/processed/tco_scenarios.parquet")
rows = sorted(t.to_pylist(), key=lambda r: r["npv_eur"], reverse=True)
print(f"{'scenario_id':<34} {'NPV (EUR)':>14}")
print("-" * 49)
for r in rows:
    print(f"{r['scenario_id']:<34} {r['npv_eur']:>14,.0f}")
