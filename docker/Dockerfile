FROM python:3.12-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

COPY pyproject.toml .
RUN uv pip install -e ".[dev]" --system

FROM base AS runtime
COPY . .
ENTRYPOINT ["python", "-m", "warehouse_humanoid_tco"]
