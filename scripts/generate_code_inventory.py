"""Walk src/ via ast → emit governance/CODE_INVENTORY.yaml.

Supports --diff mode: exits 1 if the generated inventory differs from the
committed version (used in CI to detect undocumented public API changes).
"""

from __future__ import annotations

import ast
import sys
from datetime import date
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent
SRC = REPO_ROOT / "src"
OUT = REPO_ROOT / "governance" / "CODE_INVENTORY.yaml"


def _build_inventory() -> dict:
    modules: dict[str, dict] = {}
    for py_file in sorted(SRC.rglob("*.py")):
        rel = py_file.relative_to(REPO_ROOT)
        try:
            tree = ast.parse(py_file.read_text())
        except SyntaxError:
            continue
        module_key = str(rel).replace("/", ".").removesuffix(".py")
        classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        functions = [
            n.name
            for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")
        ]
        entry: dict = {"path": str(rel)}
        if classes:
            entry["classes"] = classes
        if functions:
            entry["public_functions"] = functions
        modules[module_key] = entry
    return {
        "generated_at": str(date.today()),
        "source": "src/",
        "modules": modules,
    }


def main() -> int:
    diff_mode = "--diff" in sys.argv
    inventory = _build_inventory()
    content = yaml.dump(inventory, default_flow_style=False, allow_unicode=True, sort_keys=False)

    if diff_mode:
        if not OUT.exists():
            print("[FAIL] generate_code_inventory.py: CODE_INVENTORY.yaml missing — run without --diff first")
            return 1
        existing = OUT.read_text()
        # Compare module keys and public symbols only (ignore generated_at date)
        existing_data = yaml.safe_load(existing) or {}
        new_data = yaml.safe_load(content) or {}
        existing_modules = {k: v for k, v in (existing_data.get("modules") or {}).items()}
        new_modules = {k: v for k, v in (new_data.get("modules") or {}).items()}
        diffs: list[str] = []
        for k in sorted(set(existing_modules) | set(new_modules)):
            old = existing_modules.get(k, {})
            new = new_modules.get(k, {})
            if old.get("public_functions") != new.get("public_functions") or old.get("classes") != new.get("classes"):
                diffs.append(k)
        if diffs:
            print(f"[FAIL] generate_code_inventory.py: API drift in {len(diffs)} module(s): {'; '.join(diffs[:5])}")
            return 1
        print(f"[PASS] generate_code_inventory.py: CODE_INVENTORY.yaml matches source ({len(new_modules)} modules)")
        return 0

    OUT.write_text(content)
    print(f"[PASS] generate_code_inventory.py: wrote {len(inventory['modules'])} modules → {OUT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
