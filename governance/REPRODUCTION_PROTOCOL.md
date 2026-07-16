# Reproduction protocol

This protocol lets an independent reviewer recreate the data products and
compare their SHA-256 hashes. Docker runs are intended to be bit-for-bit when
the image, Git revision, and input data are identical. Native runs should be
numerically identical, but package and platform differences can change file
bytes.

Expected cold-start time for `make all`: allow 20–40 minutes, depending on
Hugging Face download speed and whether the local cache is warm.

## Preconditions

```bash
git clone https://github.com/RafaelBraga-Kribitz/warehouse_humanoid_tco.git
cd warehouse_humanoid_tco
git lfs install
git lfs pull
```

Module 1 needs access to the public UnifoLM data. Set `HF_TOKEN` if the
environment requires an authenticated Hugging Face download.

## Docker path

Build the pinned environment:

```bash
docker build -f docker/Dockerfile -t warehouse-humanoid-tco:repro .
```

The image has a CLI entrypoint, so run the pipeline commands through `/bin/sh`
and mount the checkout to retain outputs:

```bash
docker run --rm --entrypoint /bin/sh -v "$PWD:/app" -w /app \
  -e HF_TOKEN warehouse-humanoid-tco:repro -lc '
  python -m warehouse_humanoid_tco.pipelines.module_01_capability_extraction &&
  python -m warehouse_humanoid_tco.pipelines.module_02_simulation &&
  python -m warehouse_humanoid_tco.pipelines.module_03_tco &&
  python -m warehouse_humanoid_tco.pipelines.module_04_dashboards'
```

## Native Unix path

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -e ".[dev,analytics]"
make all
make dbt
python scripts/check_repro_log.py
```

## Windows PowerShell path (no `make`)

```powershell
uv venv .venv
& .\.venv\Scripts\Activate.ps1
uv pip install -e ".[dev,analytics]"
python -m warehouse_humanoid_tco.pipelines.module_01_capability_extraction
python -m warehouse_humanoid_tco.pipelines.module_02_simulation
python -m warehouse_humanoid_tco.pipelines.module_03_tco
python -m warehouse_humanoid_tco.pipelines.module_04_dashboards
dbt build --project-dir analytics/dbt --profiles-dir analytics/dbt
python scripts/check_repro_log.py
```

For Docker from PowerShell, replace `$PWD` with `${PWD}` in the mount command:

```powershell
docker run --rm --entrypoint /bin/sh -v "${PWD}:/app" -w /app `
  -e HF_TOKEN warehouse-humanoid-tco:repro -lc "python -m warehouse_humanoid_tco.pipelines.module_01_capability_extraction && python -m warehouse_humanoid_tco.pipelines.module_02_simulation && python -m warehouse_humanoid_tco.pipelines.module_03_tco && python -m warehouse_humanoid_tco.pipelines.module_04_dashboards"
```

## Hash and log

After the pipeline completes, calculate hashes and copy them into
`governance/REPRODUCTION_LOG.md`:

```bash
sha256sum data/processed/*.parquet reports/*.json
```

```powershell
Get-FileHash data\processed\*.parquet,reports\*.json -Algorithm SHA256
```

The log must state the date, OS, command path, at least four artifact hashes,
and a `Discrepancies:` section. Do not call a reproduction successful if any
hash differs without recording and explaining the difference.
