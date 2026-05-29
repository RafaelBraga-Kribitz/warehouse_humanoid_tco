"""Every config/dataset_manifest.yaml entry has non-empty sha256 (Phase 1 stub).

Also flags the existing key-lookup bug in scripts/verify_data_integrity.py
(reads manifest.get('datasets', []) but the real keys are wbt_datasets +
diversemanip_datasets). Phase 1 fixes that script as part of this check.
"""

from _governance_stub import main_stub

if __name__ == "__main__":
    main_stub("check_manifest_sha256.py", finding_id="F-007")
