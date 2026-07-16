# Reproduction log

- Date: 2026-07-16
- Reviewer: Cursor agent (stranger surrogate; not an independent third party)
- OS: Windows 11 (10.0.26200)
- Python: 3.12.10 (`.venv`)
- Revision: local working tree based on `d284a99c14f1`
- Path exercised: existing generated artifacts were hash-verified; the F-229
  dbt build and parity test passed locally.

## SHA-256 artifacts

| SHA-256 | Artifact |
| --- | --- |
| `00F6D3AD62DD712A1AE70A9D279EDD6642B44E97E870F2ED47D1E0BECE2CBCD4` | `data/processed/humanoid_capabilities_summary.parquet` |
| `96CB2FE4121CD984EB312662F738D43FDEE88163B934E6B3E5EB9A4256D4FE8B` | `data/processed/sensitivity_mc_samples.parquet` |
| `D1872F0C6AD9A7F3303F8223E698B4BF4805B7302739330825F6001841E88395` | `data/processed/sensitivity_oat_results.parquet` |
| `9344C9C20D4A3A9AFE89AA61DACAFAC85DEA2C7BD02F6E36CA05BEAC440B94C1` | `data/processed/simulation_capacity_ceiling.parquet` |
| `CFB86E949D0EC578AE28892D019601248F9C463B078CB92CC5CB7F4DEFC4F69F` | `data/processed/simulation_runs.parquet` |
| `6DF95552987FD731608D071B1B8056BC84FB1287D857195C53233AFE27D6401B` | `data/processed/tco_scenarios.parquet` |
| `18D804D99907323B797418F1663A320EDF8E5A9B99F25CF443AD3DA0C73C47F6` | `reports/module_01_capability_extraction_report.json` |
| `C60E5B81827425E75521D2B02B3F88E834698D6DC80C8C69B48E535A863CC659` | `reports/module_02_simulation_report.json` |
| `CEBEC2084407AF11D49FEA0D6741ECD6A478B76CDFE985BE0F579EE586D16722` | `reports/module_03_tco_report.json` |
| `F1E886B381BAC7619CFE6ACE44E75DE589FB41ABEF2A0F3E34EEC402EFBC3173` | `reports/module_04_dashboard_report.json` |
| `CF3AA96A7E2D10919E84B8F3701F7D6E83D207A6FD76C9C468EC3571B5FAAB7B` | `reports/sensitivity_analysis_report.json` |

## Discrepancies:

None observed for the hashes recorded above.

## Notes

`BLOCKED-ON-USER`: this is an agent-operated surrogate log, not the required
true third-party stranger-clone execution. An independent reviewer should run
the protocol from a fresh clone and replace or append to this log.
