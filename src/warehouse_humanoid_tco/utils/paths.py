"""Portable path helpers for serialized project artifacts."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def repo_relative(p: Path) -> str:
    """Return ``p`` relative to this repository or its generated-artifact root."""
    resolved = p.resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        parts = resolved.parts
        for marker in ("config", "data", "reports", "exports"):
            if marker in parts:
                return "/".join(parts[parts.index(marker) :])
        return resolved.name
