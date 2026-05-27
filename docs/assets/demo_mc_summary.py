"""Print the Monte Carlo summary for the demo GIF."""

import json

with open("reports/sensitivity_analysis_report.json") as f:
    s = json.load(f)["mc_summary"]
print(f"n_samples    {s['n_samples']:>14,}")
print(f"npv_mean     {s['npv_mean']:>14,.0f} EUR")
print(f"npv_std      {s['npv_std']:>14,.0f} EUR")
print(f"npv_p5       {s['npv_p5']:>14,.0f} EUR")
print(f"npv_p50      {s['npv_p50']:>14,.0f} EUR")
print(f"npv_p95      {s['npv_p95']:>14,.0f} EUR")
