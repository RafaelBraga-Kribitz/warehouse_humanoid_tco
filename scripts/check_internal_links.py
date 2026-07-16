"""Verify that committed Markdown documentation does not contain dead links."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

from _governance_check import REPO_ROOT, gate

MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
CHARTER_PATH_RE = re.compile(r"`(governance/[^`]+\.md)`")


def check_links_in_text(text: str, base_dir: Path) -> list[str]:
    """Return unresolved relative Markdown links in *text*."""
    candidates = MARKDOWN_LINK_RE.findall(text)
    missing: list[str] = []

    for raw_target in candidates:
        target = raw_target.strip().strip("<>")
        target = target.split(maxsplit=1)[0].split("#", maxsplit=1)[0]
        if not target or target.startswith(("http://", "https://", "mailto:")):
            continue
        resolved = (base_dir / unquote(target)).resolve()
        if not resolved.exists():
            missing.append(raw_target)
    return missing


def _committed_markdown_files() -> list[Path]:
    """List tracked Markdown files, excluding the raw-data payloads."""
    result = subprocess.run(
        ["git", "ls-files", "--", "*.md"],  # noqa: S607
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [
        REPO_ROOT / line
        for line in result.stdout.splitlines()
        if line and not line.startswith("data/raw/") and (REPO_ROOT / line).exists()
    ]


def main() -> int:
    missing: list[str] = []
    for path in _committed_markdown_files():
        text = path.read_text(encoding="utf-8")
        targets = check_links_in_text(text, path.parent)
        if path == REPO_ROOT / "PROJECT_CHARTER.md":
            for target in CHARTER_PATH_RE.findall(text):
                targets.extend(check_links_in_text(f"[index]({target})", path.parent))
        missing.extend(f"{path.relative_to(REPO_ROOT)} -> {target}" for target in targets)
    ok = not missing
    return gate(
        "check_internal_links.py",
        "F-202",
        ok=ok,
        ok_msg="all committed internal Markdown links resolve",
        gap_msg="dead internal links: " + "; ".join(missing),
    )


if __name__ == "__main__":
    sys.exit(main())
