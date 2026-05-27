"""Print TCO scenarios in a readable format for the demo GIF."""

import pyarrow.parquet as pq

t = pq.read_table("data/processed/tco_scenarios.parquet")
print(f"{'scenario_id':<22} {'NPV (EUR)':>16}")
print("-" * 40)
for r in t.to_pylist():
    print(f"{r['scenario_id']:<22} {r['npv_eur']:>16,.0f}")
